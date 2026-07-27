"""Eager seal child 한 번의 취득, 관측, 판정 단계.

supervisor 본체가 소유하던 지역 변수 묶음을 두 개의 가변 상태로 세운다. ``_SealLaunch``
는 부모가 잡은 자원(artifact, pipe, gate, child)이고 ``_SealRun``은 그 child 를 지켜본
관측치다. 둘 다 제자리에서 채워지므로, 중간에 예외가 빠져나가도 그때까지 잡힌 자원과
관측치가 호출자에게 그대로 남는다. 반환값으로 넘기면 부분 취득분을 잃고 leak 이 된다.
"""

from __future__ import annotations

import hashlib
import importlib
import multiprocessing
import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from multiprocessing.connection import wait
from typing import Any, Literal, cast

from dartlab.dataHub.continuation import ContinuationError, arrowSchemaDigest
from dartlab.dataHub.isolation.eagerProcess import (
    _EAGER_SCHEMA,
    EagerSeal,
    _childMain,
    _decodeBundle,
)
from dartlab.dataHub.isolation.ownerProcess import (
    _artifactPath,
    _awaitChildExit,
    _ControlTracker,
    _createArtifact,
    _drainAvailable,
    _ensureArtifactRoot,
    _finishProcess,
    _ProtocolViolation,
    _readArtifact,
    _removeArtifact,
    _sentinelReady,
    _stopProcess,
    _strictJson,
    _WindowsJob,
)
from dartlab.dataHub.isolation.processLifecycle import stopProcessGroup
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

EagerProcessStatus = Literal[
    "ok",
    "budgetRejected",
    "timedOut",
    "protocolFailed",
    "childFailed",
    "artifactFailed",
    "jobFailed",
    "cleanupFailed",
]

_log = dataHubLogger(__name__)


@dataclass(slots=True)
class _SealLaunch:
    """부모가 자식 하나를 띄우려고 잡은 자원 묶음."""

    artifactId: str = ""
    artifactRoot: Any = None
    artifactPath: Any = None
    receiveConnection: Any = None
    sendConnection: Any = None
    startGate: Any = None
    process: Any = None


@dataclass(slots=True)
class _SealRun:
    """자식 한 번 실행에 대한 부모의 관측치."""

    status: EagerProcessStatus = "childFailed"
    seal: EagerSeal | None = None
    errorCode: str | None = None
    cleanupTrace: tuple[str, ...] = ()
    pid: int | None = None
    threadNativeId: int | None = None
    processStarted: bool = False
    protocolError: str | None = None
    childCompletedAt: float | None = None
    tracker: _ControlTracker = field(default_factory=lambda: _ControlTracker(frames=[]))


def _openSealLaunch(launch: _SealLaunch, job: _WindowsJob, requestPayload: bytes) -> None:
    """artifact, pipe, gate, child, Job 을 정해진 순서로 잡아 ``launch``에 채운다.

    한 줄씩 곧바로 ``launch``에 기록하는 것이 계약이다. 중간에 실패하면 호출자의
    release 단계가 그때까지 잡힌 것만 정확히 되돌릴 수 있어야 한다.
    """

    launch.artifactId = os.urandom(32).hex()
    request = importlib.import_module("json").loads(requestPayload.decode("ascii"))
    request["artifactId"] = launch.artifactId
    requestPayload = _strictJson(request)
    launch.artifactRoot = _ensureArtifactRoot()
    launch.artifactPath = _artifactPath(launch.artifactRoot, launch.artifactId)
    _createArtifact(launch.artifactPath, launch.artifactRoot)
    context = multiprocessing.get_context("spawn")
    launch.receiveConnection, launch.sendConnection = context.Pipe(duplex=False)
    launch.startGate = context.Event()
    launch.process = context.Process(
        target=_childMain,
        args=(launch.sendConnection, launch.startGate, requestPayload, launch.artifactId),
        name="dartlab-eager-seal",
        daemon=False,
    )
    job.create()


def _releaseSealLaunch(launch: _SealLaunch, job: _WindowsJob) -> None:
    """취득 도중 실패했을 때 잡힌 자원만 골라 되돌린다.

    Artifact 삭제 실패는 여기서 삼킨다. 호출자가 곧바로 원래의 취득 실패 원인을
    outcome 으로 돌려주므로, 정리 실패로 그 원인을 덮으면 진단이 사라진다.
    """

    if launch.sendConnection is not None:
        launch.sendConnection.close()
    if launch.receiveConnection is not None:
        launch.receiveConnection.close()
    job.close()
    if launch.artifactPath is not None:
        try:
            _removeArtifact(launch.artifactPath)
        except ContinuationError:
            pass


def _pumpSealFrames(run: _SealRun, launch: _SealLaunch, *, workDeadline: float) -> None:
    """기한 안에서 control frame 과 child sentinel 을 번갈아 관측한다.

    관측치는 반환하지 않고 ``run``에 바로 쌓는다. ``_drainAvailable``이 protocol 위반이
    아닌 예외로 죽어도 그때까지 읽은 ready 정보가 살아남아야 zero-live 판정이 정확하다.
    """

    receiveConnection = launch.receiveConnection
    process = launch.process
    tracker = run.tracker
    while time.perf_counter() < workDeadline:
        readyItems = wait(
            cast(Any, [receiveConnection, process.sentinel]),
            timeout=min(
                0.05,
                max(0.0, workDeadline - time.perf_counter()),
            ),
        )
        if receiveConnection in readyItems:
            try:
                _drainAvailable(
                    receiveConnection,
                    tracker,
                    artifactId=launch.artifactId,
                )
            except _ProtocolViolation as error:
                run.protocolError = str(error)
                break
            readyFrame = tracker.readyFrame
            if readyFrame is not None:
                if readyFrame["pid"] != run.pid:
                    run.protocolError = "EAGER_PROCESS_READY_PID_MISMATCH"
                    break
                run.threadNativeId = int(readyFrame["threadNativeId"])
        if process.sentinel in readyItems:
            run.childCompletedAt = time.perf_counter()
            try:
                _drainAvailable(
                    receiveConnection,
                    tracker,
                    artifactId=launch.artifactId,
                )
            except _ProtocolViolation as error:
                run.protocolError = str(error)
            break
        if tracker.resultFrame is not None and _sentinelReady(
            process,
            max(0.0, workDeadline - time.perf_counter()),
        ):
            run.childCompletedAt = time.perf_counter()
            _drainAvailable(
                receiveConnection,
                tracker,
                artifactId=launch.artifactId,
            )
            break


def _sealFromArtifact(
    launch: _SealLaunch,
    resultFrame: Mapping[str, Any],
    selectors: Sequence[Mapping[str, str]],
    *,
    maxBundleBytes: int,
) -> EagerSeal:
    """부모만 아는 artifact 를 직접 읽어 content-sealed bundle 로 봉인한다.

    Raises:
        ContinuationError: Artifact 가 claim 과 다르거나 bundle 이 깨졌을 때.
    """

    payload = _readArtifact(
        launch.artifactPath,
        launch.artifactRoot,
        byteCount=int(resultFrame["byteCount"]),
        digest=str(resultFrame["digest"]),
        maxBytes=maxBundleBytes,
    )
    results = _decodeBundle(payload, selectors=selectors)
    if len(results) != int(resultFrame["rowCount"]):
        raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
    return EagerSeal(
        payload,
        hashlib.sha256(payload).hexdigest(),
        len(payload),
        len(results),
        arrowSchemaDigest(_EAGER_SCHEMA),
    )


def _settleSealOutcome(
    run: _SealRun,
    launch: _SealLaunch,
    job: _WindowsJob,
    selectors: Sequence[Mapping[str, str]],
    *,
    workDeadline: float,
    publicDeadline: float,
    maxBundleBytes: int,
) -> None:
    """관측이 끝난 자식을 정리하고 하나의 status 로 판정한다.

    네 갈래는 배타적이고 순서가 계약이다. Protocol 위반, 기한 안의 정상 종료, 기한 초과,
    그리고 결과를 보내고도 빠져나가지 않은 자식 순으로 본다. 정리 trace 는 판정 직후에
    바로 ``run``에 적어, 뒤이어 artifact 읽기가 실패해도 정리 증거가 남게 한다.
    """

    tracker = run.tracker
    process = launch.process
    if run.protocolError is not None:
        run.status = "protocolFailed"
        run.errorCode = run.protocolError
        run.cleanupTrace = _stopProcess(process, job, publicDeadline)
        run.cleanupTrace += stopProcessGroup(run.pid, publicDeadline)
    elif (
        tracker.resultFrame is not None
        and run.childCompletedAt is not None
        and run.childCompletedAt <= workDeadline
        and _awaitChildExit(process, workDeadline)
    ):
        run.cleanupTrace = _finishProcess(process, job, publicDeadline)
        run.cleanupTrace += stopProcessGroup(run.pid, publicDeadline)
        resultFrame = tracker.resultFrame
        assert resultFrame is not None
        if resultFrame["status"] == "failed":
            run.status = "childFailed"
            run.errorCode = str(resultFrame["errorCode"])
        else:
            run.seal = _sealFromArtifact(
                launch,
                resultFrame,
                selectors,
                maxBundleBytes=maxBundleBytes,
            )
            run.status = "ok"
    elif time.perf_counter() >= workDeadline or (
        run.childCompletedAt is not None and run.childCompletedAt > workDeadline
    ):
        run.status = "timedOut"
        run.errorCode = "CONTINUATION_TIMEOUT"
        run.cleanupTrace = _stopProcess(process, job, publicDeadline)
        run.cleanupTrace += stopProcessGroup(run.pid, publicDeadline)
    else:
        run.status = "childFailed"
        # 자식이 typed 실패를 이미 보냈다면 그것이 부모의 추정보다 정확하다.
        # 자식은 worker thread 가 non-daemon 이라 결과를 보낸 뒤에도 잠시 더
        # 살아 있을 수 있는데, 그 지연 때문에 진짜 원인을 지우면 안 된다.
        reportedFrame = tracker.resultFrame
        reportedCode = (
            str(reportedFrame["errorCode"])
            if reportedFrame is not None and reportedFrame["status"] == "failed"
            else None
        )
        run.errorCode = reportedCode or "EAGER_PROCESS_CHILD_DID_NOT_EXIT"
        recordFailure(
            _log,
            "EAGER_PROCESS_CHILD_LINGERED",
            context={
                "hasResultFrame": reportedFrame is not None,
                "reportedCode": reportedCode,
                "childCompleted": run.childCompletedAt is not None,
                "processAlive": process.is_alive(),
            },
        )
        run.cleanupTrace = _stopProcess(process, job, publicDeadline)
        run.cleanupTrace += stopProcessGroup(run.pid, publicDeadline)


__all__: list[str] = []
