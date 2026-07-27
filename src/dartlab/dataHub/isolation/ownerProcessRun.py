"""Owner page child 한 번의 검증, 취득, 관측, 판정 단계.

supervisor 본체가 들고 있던 지역 변수 묶음을 두 개의 가변 상태로 세운다. ``_OwnerLaunch``
는 부모가 잡은 자원(artifact, pipe, gate, child)이고 ``_OwnerRun``은 그 child 를 지켜본
관측치다. 둘 다 제자리에서 채워지므로 중간에 예외가 빠져나가도 그때까지 잡힌 자원과
관측치가 호출자에게 그대로 남는다. 반환값으로 넘기면 부분 취득분을 잃고 leak 이 된다.
"""

from __future__ import annotations

import hashlib
import math
import multiprocessing
import time
from dataclasses import dataclass, field
from multiprocessing.connection import wait
from pathlib import Path
from typing import Any, cast

from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.isolation.ownerProcessArtifacts import (
    _artifactPath,
    _buildRequest,
    _createArtifact,
    _ensureArtifactRoot,
    _readArtifact,
    _removeArtifact,
    _safeErrorCode,
)
from dartlab.dataHub.isolation.ownerProcessChild import _pageChildMain
from dartlab.dataHub.isolation.ownerProcessControl import (
    _awaitChildExit,
    _drainAvailable,
    _finishProcess,
    _sentinelReady,
    _stopProcess,
)
from dartlab.dataHub.isolation.ownerProcessModels import (
    OwnerProcessOutcome,
    OwnerProcessPage,
    OwnerProcessStatus,
    _ProtocolViolation,
)
from dartlab.dataHub.isolation.ownerProcessWindows import _ControlTracker, _WindowsJob
from dartlab.dataHub.paging.runtime import MAX_STATE_BYTES
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

_log = dataHubLogger(__name__)


@dataclass(slots=True)
class _OwnerLaunch:
    """부모가 자식 하나를 띄우려고 잡은 자원 묶음."""

    artifactId: str = ""
    artifactRoot: Path | None = None
    artifactPath: Path | None = None
    receiveConnection: Any = None
    sendConnection: Any = None
    startGate: Any = None
    process: Any = None


@dataclass(slots=True)
class _OwnerRun:
    """자식 한 번 실행에 대한 부모의 관측치."""

    status: OwnerProcessStatus = "childFailed"
    errorCode: str | None = None
    page: OwnerProcessPage | None = None
    cleanupTrace: tuple[str, ...] = ()
    pid: int | None = None
    threadNativeId: int | None = None
    readySeconds: float | None = None
    processStarted: bool = False
    protocolError: str | None = None
    childCompletedAt: float | None = None
    tracker: _ControlTracker = field(default_factory=lambda: _ControlTracker(frames=[]))


def _validateOwnerArguments(
    sessionPayload: bytes,
    *,
    publicDeadline: float,
    cleanupGraceSeconds: float,
    minimumWorkSeconds: float,
) -> None:
    """Spawn 전에 끝나야 하는 payload 크기와 deadline 계약을 검사한다.

    세 검사의 순서가 곧 오류 메시지의 순서다. 어느 하나라도 앞당기거나 미루면
    호출자가 받는 ``ValueError`` 문구가 달라진다.
    """

    # IPC payload 는 durable state 와 달리 엔티티 목록을 함께 싣는다. 한 page 실행
    # 동안만 존재하므로 durable state 상한이 아니라 request 상한을 적용한다.
    if not isinstance(sessionPayload, bytes) or not sessionPayload or len(sessionPayload) > MAX_STATE_BYTES:
        raise ValueError("owner session payload 크기가 유효하지 않습니다")
    numeric = (publicDeadline, cleanupGraceSeconds, minimumWorkSeconds)
    if any(type(value) not in {int, float} or not math.isfinite(value) for value in numeric):
        raise ValueError("owner process deadline 값은 유한한 숫자여야 합니다")
    if cleanupGraceSeconds <= 0 or minimumWorkSeconds <= 0:
        raise ValueError("owner process deadline 예약은 양수여야 합니다")


def _openArtifact(launch: _OwnerLaunch) -> None:
    """부모만 아는 빈 artifact 자리를 먼저 만든다."""

    launch.artifactRoot = _ensureArtifactRoot()
    launch.artifactPath = _artifactPath(launch.artifactRoot, launch.artifactId)
    _createArtifact(launch.artifactPath, launch.artifactRoot)


def _artifactFailureOutcome(
    error: ContinuationError,
    launch: _OwnerLaunch,
    *,
    startedAt: float,
    publicDeadline: float,
    workDeadline: float,
) -> OwnerProcessOutcome:
    """Artifact 자리를 잡다 실패했을 때, 남은 흔적을 지우고 typed outcome 을 만든다.

    Artifact 삭제 실패는 여기서 삼킨다. 돌려줄 ``errorCode``는 이미 원래의 취득 실패
    원인으로 고정돼 있어, 정리 실패로 그 원인을 덮으면 진단이 사라진다.
    """

    endedAt = time.perf_counter()
    if launch.artifactPath is not None:
        try:
            _removeArtifact(launch.artifactPath)
        except ContinuationError:
            pass
    return OwnerProcessOutcome(
        status="artifactFailed",
        page=None,
        spawned=False,
        pid=None,
        threadNativeId=None,
        publicDeadline=publicDeadline,
        workDeadline=workDeadline,
        readySeconds=None,
        elapsedSeconds=endedAt - startedAt,
        deadlineOvershootSeconds=max(0.0, endedAt - publicDeadline),
        ipcFrameCount=0,
        ipcByteCount=0,
        cleanupTrace=(),
        zeroLive=True,
        jobObjectAttempted=False,
        jobObjectAssigned=False,
        jobObjectError=None,
        errorCode=error.code,
    )


def _openOwnerLaunch(
    launch: _OwnerLaunch,
    job: _WindowsJob,
    sessionPayload: bytes,
    *,
    workDeadline: float,
) -> None:
    """Request, pipe, gate, child, Job 을 정해진 순서로 잡아 ``launch``에 채운다.

    한 줄씩 곧바로 ``launch``에 기록하는 것이 계약이다. 중간에 실패하면 호출자의
    release 단계가 그때까지 잡힌 것만 정확히 되돌릴 수 있어야 한다.
    """

    requestPayload = _buildRequest(
        sessionPayload,
        artifactId=launch.artifactId,
        workDeadline=workDeadline,
    )
    context = multiprocessing.get_context("spawn")
    launch.receiveConnection, launch.sendConnection = context.Pipe(duplex=False)
    launch.startGate = context.Event()
    launch.process = context.Process(
        target=_pageChildMain,
        args=(launch.sendConnection, launch.startGate, requestPayload, launch.artifactId),
        name="dartlab-owner-page",
        daemon=False,
    )
    job.create()


def _releaseOwnerLaunch(launch: _OwnerLaunch, job: _WindowsJob) -> None:
    """취득 도중 실패했을 때 잡힌 자원만 골라 되돌린다.

    Artifact 삭제 실패는 여기서 삼키지 않는다. 자식을 아직 띄우지 않았으므로 부모가
    지우지 못한 artifact 가 곧 유일한 잔여물이고, 그 실패는 호출자로 올라가야 한다.
    """

    if launch.sendConnection is not None:
        launch.sendConnection.close()
    if launch.receiveConnection is not None:
        launch.receiveConnection.close()
    job.close()
    assert launch.artifactPath is not None
    _removeArtifact(launch.artifactPath)


def _launchFailureOutcome(
    error: BaseException,
    job: _WindowsJob,
    *,
    startedAt: float,
    publicDeadline: float,
    workDeadline: float,
) -> OwnerProcessOutcome:
    """Spawn 준비가 깨졌을 때의 typed outcome 을 만든다."""

    endedAt = time.perf_counter()
    return OwnerProcessOutcome(
        status="childFailed",
        page=None,
        spawned=False,
        pid=None,
        threadNativeId=None,
        publicDeadline=publicDeadline,
        workDeadline=workDeadline,
        readySeconds=None,
        elapsedSeconds=endedAt - startedAt,
        deadlineOvershootSeconds=max(0.0, endedAt - publicDeadline),
        ipcFrameCount=0,
        ipcByteCount=0,
        cleanupTrace=(),
        zeroLive=True,
        jobObjectAttempted=job.attempted,
        jobObjectAssigned=job.assigned,
        jobObjectError=job.error,
        errorCode=_safeErrorCode(error),
    )


def _pumpOwnerFrames(
    run: _OwnerRun,
    launch: _OwnerLaunch,
    *,
    workDeadline: float,
    startedAt: float,
) -> None:
    """기한 안에서 control frame 과 child sentinel 을 번갈아 관측한다.

    관측치는 반환하지 않고 ``run``에 바로 쌓는다. ``_drainAvailable``이 protocol 위반이
    아닌 예외로 죽어도 그때까지 읽은 ready 정보가 살아남아야 zero-live 판정이 정확하다.
    """

    receiveConnection = launch.receiveConnection
    process = launch.process
    tracker = run.tracker
    while time.perf_counter() < workDeadline:
        remaining = max(0.0, workDeadline - time.perf_counter())
        readyItems = wait(
            cast(Any, [receiveConnection, process.sentinel]),
            timeout=min(0.05, remaining),
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
            if readyFrame is not None and run.readySeconds is None:
                if readyFrame["pid"] != run.pid:
                    run.protocolError = "OWNER_PROCESS_READY_PID_MISMATCH"
                    break
                run.readySeconds = time.perf_counter() - startedAt
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
        if tracker.resultFrame is not None and _sentinelReady(process, remaining):
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


def _ownerPageFromArtifact(
    launch: _OwnerLaunch,
    resultFrame: dict[str, Any],
    sessionPayload: bytes,
) -> OwnerProcessPage:
    """부모만 아는 artifact 를 직접 읽어 검증된 page 로 세운다.

    Raises:
        ContinuationError: Session, artifact, page 중 어느 하나가 계약을 벗어날 때.
    """

    from dartlab.dataHub.paging import owner as ownerPaging

    session = ownerPaging._decodeSession(sessionPayload)
    payload = _readArtifact(
        launch.artifactPath,
        launch.artifactRoot,
        byteCount=int(resultFrame["byteCount"]),
        digest=str(resultFrame["digest"]),
        maxBytes=session.pageMaxBytes,
    )
    decoded = ownerPaging._decodePage(
        payload,
        claimedRowCount=int(resultFrame["rowCount"]),
        maxPageRows=session.pageMaxRows,
        maxPageBytes=session.pageMaxBytes,
        maxLogicalBytes=session.pageMaxLogicalBytes,
    )
    return OwnerProcessPage(
        payload=payload,
        rowCount=decoded.facts.rowCount,
        byteCount=len(payload),
        payloadDigest=hashlib.sha256(payload).hexdigest(),
    )


def _settleOwnerOutcome(
    run: _OwnerRun,
    launch: _OwnerLaunch,
    job: _WindowsJob,
    sessionPayload: bytes,
    *,
    workDeadline: float,
    publicDeadline: float,
) -> None:
    """관측이 끝난 자식을 정리하고 하나의 status 로 판정한다.

    다섯 갈래는 배타적이고 순서가 계약이다. Protocol 위반, 기한 안의 정상 종료, 기한
    초과, 결과를 보내고도 빠져나가지 않은 자식, 그리고 그냥 죽은 자식 순으로 본다.
    정리 trace 는 판정 직후에 바로 ``run``에 적어, 뒤이어 artifact 읽기가 실패해도
    정리 증거가 남게 한다.
    """

    tracker = run.tracker
    process = launch.process
    if run.protocolError is not None:
        run.status = "protocolFailed"
        run.errorCode = run.protocolError
        run.cleanupTrace = _stopProcess(process, job, publicDeadline)
    elif (
        tracker.resultFrame is not None
        and run.childCompletedAt is not None
        and run.childCompletedAt <= workDeadline
        and _awaitChildExit(process, workDeadline)
    ):
        run.cleanupTrace = _finishProcess(process, job, publicDeadline)
        resultFrame = tracker.resultFrame
        assert resultFrame is not None
        if resultFrame["status"] == "failed":
            run.status = "childFailed"
            run.errorCode = str(resultFrame["errorCode"])
        else:
            assert launch.artifactRoot is not None and launch.artifactPath is not None
            try:
                run.page = _ownerPageFromArtifact(launch, resultFrame, sessionPayload)
                run.status = "ok"
            except ContinuationError as error:
                run.status = "artifactFailed"
                run.errorCode = error.code
    elif time.perf_counter() >= workDeadline or (
        run.childCompletedAt is not None and run.childCompletedAt > workDeadline
    ):
        run.status = "timedOut"
        run.errorCode = "CONTINUATION_TIMEOUT"
        run.cleanupTrace = _stopProcess(process, job, publicDeadline)
    elif tracker.resultFrame is not None:
        run.status = "childFailed"
        # 여유를 주고도 자식이 안 빠져나갔다. 자식이 typed 실패를 이미 보냈다면
        # 그것이 부모의 추정보다 정확하다 (eagerSupervisor 와 동형).
        reportedFrame = tracker.resultFrame
        reportedCode = str(reportedFrame["errorCode"]) if reportedFrame["status"] == "failed" else None
        run.errorCode = reportedCode or "OWNER_PROCESS_CHILD_DID_NOT_EXIT"
        recordFailure(
            _log,
            "OWNER_PROCESS_CHILD_LINGERED",
            context={
                "reportedCode": reportedCode,
                "childCompleted": run.childCompletedAt is not None,
                "processAlive": process.is_alive(),
            },
        )
        run.cleanupTrace = _stopProcess(process, job, publicDeadline)
    else:
        run.status = "childFailed"
        run.errorCode = f"OWNER_PROCESS_CHILD_EXIT_{process.exitcode}"
        run.cleanupTrace = _finishProcess(process, job, publicDeadline)


__all__: list[str] = []
