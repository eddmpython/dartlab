"""Eager result seal child의 hard-deadline process lifecycle을 관리한다.

Capabilities:
    Spawn, Job Object, POSIX process group, bounded IPC, artifact 검증과 zero-live를 제공한다.

Args:
    ``runEagerSeal``은 import 가능한 descriptor와 strict query 계약을 받는다.

Returns:
    검증된 EagerSeal 또는 구조화된 process outcome을 반환한다.

Raises:
    호출 인자나 strict JSON request가 유효하지 않으면 ``ValueError``를 발생시킨다.

Example:
    ``runEagerSeal(descriptor, query, ({},), requestId="x", ...)``.

Guide:
    결과 bytes는 pipe로 보내지 않고 parent-known private artifact에서만 읽는다.

When:
    Mixed continuation이 일반 eager executor를 첫 page 전에 봉인할 때 사용한다.

How:
    ``ownerProcess``의 검증된 Windows supervisor primitive를 재사용한다.

See Also:
    ``dartlab.dataHub.isolation.eagerProcess``과 ``dartlab.dataHub.isolation.ownerProcess``.

Requires:
    Parent와 child가 같은 private DARTLAB_HOME과 import path를 사용해야 한다.

AI Context:
    반환 전에 direct child, worker thread와 process tree가 모두 종료되어야 한다.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib
import math
import multiprocessing
import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from multiprocessing.connection import wait
from typing import Any, Literal, cast

from dartlab.dataHub.continuation import ContinuationError, arrowSchemaDigest
from dartlab.dataHub.contracts import DataAssetDescriptor, DataQuery
from dartlab.dataHub.isolation.eagerProcess import (
    _BUNDLE_OVERHEAD_BYTES,
    _EAGER_SCHEMA,
    _FORMAT_VERSION,
    _MAX_BUNDLE_BYTES,
    EagerSeal,
    _childMain,
    _decodeBundle,
    eagerCodePin,
)
from dartlab.dataHub.isolation.ownerProcess import (
    _artifactPath,
    _ControlTracker,
    _createArtifact,
    _drainAvailable,
    _ensureArtifactRoot,
    _finishProcess,
    _ProtocolViolation,
    _readArtifact,
    _removeArtifact,
    _safeErrorCode,
    _sentinelReady,
    _stopProcess,
    _strictJson,
    _WindowsJob,
    _zeroLive,
)
from dartlab.dataHub.isolation.processLifecycle import (
    processGroupAlive,
    stopProcessGroup,
)
from dartlab.dataHub.paging.runtime import (
    MAX_OWNER_PROCESS_REQUEST_BYTES,
    MIN_OWNER_PROCESS_WORK_SECONDS,
    OWNER_PROCESS_CLEANUP_GRACE_SECONDS,
)
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

_PUBLIC_ERROR_CODES = frozenset(
    {
        "CONTINUATION_BYTE_BUDGET",
        "CONTINUATION_CORRUPT",
        "CONTINUATION_PAYLOAD_INVALID",
        "CONTINUATION_PAYLOAD_ROW_MISMATCH",
        "CONTINUATION_PAYLOAD_SCHEMA_MISMATCH",
        "CONTINUATION_SECURITY_FAILED",
        "CONTINUATION_TIMEOUT",
        "OFFLINE_NETWORK_BLOCKED",
        "PAGEABLE_EAGER_CODE_PIN_FAILED",
        "PAGEABLE_EAGER_EXECUTOR_UNSUPPORTED",
        "PAGEABLE_EAGER_PROCESS_BUDGET",
        "PAGEABLE_EAGER_PROCESS_FAILED",
        "PAGEABLE_EAGER_SEAL_BUDGET",
        "PAGEABLE_EAGER_SEAL_RESULT_BUDGET",
        "PAGEABLE_EAGER_SEAL_ROW_BUDGET",
        "PAGEABLE_EAGER_SELECTOR_UNSUPPORTED",
        "PAGEABLE_EAGER_WRITE_BLOCKED",
    }
)


@dataclass(frozen=True, slots=True)
class EagerProcessOutcome:
    """Eager child 실행과 cleanup의 parent 관측 결과."""

    status: EagerProcessStatus
    seal: EagerSeal | None
    spawned: bool
    pid: int | None
    threadNativeId: int | None
    elapsedSeconds: float
    deadlineOvershootSeconds: float
    ipcFrameCount: int
    ipcByteCount: int
    cleanupTrace: tuple[str, ...]
    zeroLive: bool
    jobObjectAttempted: bool
    jobObjectAssigned: bool
    jobObjectError: str | None
    errorCode: str | None


def _publicErrorCode(code: str | None) -> str:
    """자식이 보고한 code 를 공개 목록으로 좁힌다.

    목록 밖 code 는 내부 사정을 노출할 수 있으므로 일반 실패로 뭉갠다. 다만 원래 code 를
    그냥 버리면 진단이 불가능해지므로 side channel 에 남긴다. 이 뭉갬이 Linux 전용
    실패를 오래 미궁에 두었던 직접 원인이다.
    """

    if code in _PUBLIC_ERROR_CODES:
        return code
    if code is not None:
        _log.warning(
            "eager child error code redacted rawCode=%s publicCode=%s",
            code,
            "PAGEABLE_EAGER_PROCESS_FAILED",
        )
    return "PAGEABLE_EAGER_PROCESS_FAILED"


def recordChildOutcome(outcome: EagerProcessOutcome) -> None:
    """자식 실행 관측치를 진단 채널에 남긴다.

    Capabilities:
        status 만 보고 버려지던 준비 시간, cleanup trace, zero-live, Job Object 상태를
        보존한다.

    Args:
        outcome: parent 가 관측한 자식 실행 결과.

    Returns:
        없음.

    Example:
        ``recordChildOutcome(outcome)``.

    Guide:
        성공 결과는 남기지 않는다. 실패만 기록해 잡음을 만들지 않는다.

    When:
        supervisor 가 outcome 을 공개 code 로 바꾸기 직전에 호출한다.

    How:
        관측 필드를 구조화 로그 한 줄로 내보낸다.

    See Also:
        ``_publicErrorCode``.

    Requires:
        공개 반환은 이 호출과 무관하게 축약 상태를 유지한다.

    AI Context:
        운영자가 자식 실패를 진단할 수 있는 유일한 통로다.
    """

    if outcome.status == "ok":
        return
    _log.warning(
        "eager child outcome status=%s errorCode=%s spawned=%s zeroLive=%s "
        "elapsed=%.3f overshoot=%.3f cleanup=%s jobObject=(attempted=%s assigned=%s error=%s)",
        outcome.status,
        outcome.errorCode,
        outcome.spawned,
        outcome.zeroLive,
        outcome.elapsedSeconds,
        outcome.deadlineOvershootSeconds,
        outcome.cleanupTrace,
        outcome.jobObjectAttempted,
        outcome.jobObjectAssigned,
        outcome.jobObjectError,
    )


def _budgetOutcome(startedAt: float, publicDeadline: float) -> EagerProcessOutcome:
    endedAt = time.perf_counter()
    return EagerProcessOutcome(
        "budgetRejected",
        None,
        False,
        None,
        None,
        endedAt - startedAt,
        max(0.0, endedAt - publicDeadline),
        0,
        0,
        (),
        True,
        False,
        False,
        None,
        "PAGEABLE_EAGER_PROCESS_BUDGET",
    )


def _setupFailure(
    error: BaseException,
    *,
    startedAt: float,
    publicDeadline: float,
    job: _WindowsJob,
) -> EagerProcessOutcome:
    endedAt = time.perf_counter()
    return EagerProcessOutcome(
        "childFailed",
        None,
        False,
        None,
        None,
        endedAt - startedAt,
        max(0.0, endedAt - publicDeadline),
        0,
        0,
        (),
        True,
        job.attempted,
        job.assigned,
        job.error,
        _publicErrorCode(_safeErrorCode(error)),
    )


def runEagerSeal(
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    selectors: Sequence[Mapping[str, str]],
    *,
    requestId: str,
    snapshotId: str,
    contractHash: str,
    universeSnapshotId: str | None,
    publicDeadline: float,
    codePin: str | None = None,
    maxBundleBytes: int = _MAX_BUNDLE_BYTES,
    cleanupGraceSeconds: float = OWNER_PROCESS_CLEANUP_GRACE_SECONDS,
    minimumWorkSeconds: float = MIN_OWNER_PROCESS_WORK_SECONDS,
) -> EagerProcessOutcome:
    """General eager lane을 fresh child에서 실행하고 content-sealed bundle로 회수한다."""

    numeric = (publicDeadline, cleanupGraceSeconds, minimumWorkSeconds)
    if any(type(value) not in {int, float} or not math.isfinite(value) for value in numeric):
        raise ValueError("eager process deadline 값은 유한한 숫자여야 합니다")
    if cleanupGraceSeconds <= 0 or minimumWorkSeconds <= 0:
        raise ValueError("eager process deadline 예약은 양수여야 합니다")
    if (
        not selectors
        or type(maxBundleBytes) is not int
        or not _BUNDLE_OVERHEAD_BYTES < maxBundleBytes <= _MAX_BUNDLE_BYTES
    ):
        raise ValueError("eager process seal 예산이 유효하지 않습니다")
    startedAt = time.perf_counter()
    normalizedDeadline = float(publicDeadline)
    workDeadline = normalizedDeadline - float(cleanupGraceSeconds)
    if workDeadline - startedAt < float(minimumWorkSeconds):
        return _budgetOutcome(startedAt, normalizedDeadline)

    composite = importlib.import_module("dartlab.dataHub.paging.composite")
    execution = importlib.import_module("dartlab.dataHub.execution")
    owner = importlib.import_module("dartlab.dataHub.paging.owner")
    requestedMeasures = execution._requestedMeasures(query)
    expectedCodePin = eagerCodePin(
        descriptor,
        requestedMeasures=requestedMeasures,
    )
    activeCodePin = expectedCodePin if codePin is None else codePin
    if (
        type(activeCodePin) is not str
        or len(activeCodePin) != 64
        or any(character not in "0123456789abcdef" for character in activeCodePin)
    ):
        raise ValueError("eager code pin이 유효하지 않습니다")
    if not hmac.compare_digest(activeCodePin, expectedCodePin):
        raise ContinuationError("PAGEABLE_EAGER_CODE_PIN_FAILED")
    requestPayload = _strictJson(
        {
            "artifactId": "0" * 64,
            "codePin": activeCodePin,
            "contractHash": contractHash,
            "descriptor": owner._descriptorTree(descriptor),
            "maxBytes": maxBundleBytes,
            "maxRows": query.budget.maxRows,
            "query": composite._queryTree(query),
            "requestId": requestId,
            "selectors": [dict(selector) for selector in selectors],
            "snapshotId": snapshotId,
            "universeSnapshotId": universeSnapshotId,
            "version": _FORMAT_VERSION,
            "workDeadlineNs": int(workDeadline * 1_000_000_000),
        }
    )
    if len(requestPayload) > MAX_OWNER_PROCESS_REQUEST_BYTES:
        raise ValueError("eager process input payload가 상한을 초과했습니다")

    artifactRoot = None
    artifactPath = None
    receiveConnection: Any | None = None
    sendConnection: Any | None = None
    startGate: Any | None = None
    process: Any | None = None
    job = _WindowsJob()
    try:
        artifactId = os.urandom(32).hex()
        request = importlib.import_module("json").loads(requestPayload.decode("ascii"))
        request["artifactId"] = artifactId
        requestPayload = _strictJson(request)
        artifactRoot = _ensureArtifactRoot()
        artifactPath = _artifactPath(artifactRoot, artifactId)
        _createArtifact(artifactPath, artifactRoot)
        context = multiprocessing.get_context("spawn")
        receiveConnection, sendConnection = context.Pipe(duplex=False)
        startGate = context.Event()
        process = context.Process(
            target=_childMain,
            args=(sendConnection, startGate, requestPayload, artifactId),
            name="dartlab-eager-seal",
            daemon=False,
        )
        job.create()
    except BaseException as error:
        if sendConnection is not None:
            sendConnection.close()
        if receiveConnection is not None:
            receiveConnection.close()
        job.close()
        if artifactPath is not None:
            try:
                _removeArtifact(artifactPath)
            except ContinuationError:
                pass
        if not isinstance(error, Exception):
            raise
        return _setupFailure(
            error,
            startedAt=startedAt,
            publicDeadline=normalizedDeadline,
            job=job,
        )
    assert (
        artifactRoot is not None
        and artifactPath is not None
        and receiveConnection is not None
        and sendConnection is not None
        and startGate is not None
        and process is not None
    )
    if workDeadline - time.perf_counter() < float(minimumWorkSeconds):
        startGate.set()
        sendConnection.close()
        receiveConnection.close()
        job.close()
        _removeArtifact(artifactPath)
        return _budgetOutcome(startedAt, normalizedDeadline)
    tracker = _ControlTracker(frames=[])
    status: EagerProcessStatus = "childFailed"
    seal: EagerSeal | None = None
    errorCode: str | None = None
    cleanupTrace: tuple[str, ...] = ()
    pid: int | None = None
    threadNativeId: int | None = None
    processStarted = False
    protocolError: str | None = None
    childCompletedAt: float | None = None
    try:
        process.start()
        processStarted = True
        pid = process.pid
        if pid is None:
            raise RuntimeError("EAGER_PROCESS_PID_UNAVAILABLE")
        sendConnection.close()
        job.assign(pid)
        if job.attempted and not job.assigned:
            status = "jobFailed"
            errorCode = "EAGER_PROCESS_JOB_REQUIRED"
            cleanupTrace = _stopProcess(process, job, normalizedDeadline)
        else:
            startGate.set()
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
                            artifactId=artifactId,
                        )
                    except _ProtocolViolation as error:
                        protocolError = str(error)
                        break
                    readyFrame = tracker.readyFrame
                    if readyFrame is not None:
                        if readyFrame["pid"] != pid:
                            protocolError = "EAGER_PROCESS_READY_PID_MISMATCH"
                            break
                        threadNativeId = int(readyFrame["threadNativeId"])
                if process.sentinel in readyItems:
                    childCompletedAt = time.perf_counter()
                    try:
                        _drainAvailable(
                            receiveConnection,
                            tracker,
                            artifactId=artifactId,
                        )
                    except _ProtocolViolation as error:
                        protocolError = str(error)
                    break
                if tracker.resultFrame is not None and _sentinelReady(
                    process,
                    max(0.0, workDeadline - time.perf_counter()),
                ):
                    childCompletedAt = time.perf_counter()
                    _drainAvailable(
                        receiveConnection,
                        tracker,
                        artifactId=artifactId,
                    )
                    break
            if protocolError is not None:
                status = "protocolFailed"
                errorCode = protocolError
                cleanupTrace = _stopProcess(process, job, normalizedDeadline)
                cleanupTrace += stopProcessGroup(pid, normalizedDeadline)
            elif (
                tracker.resultFrame is not None
                and not process.is_alive()
                and childCompletedAt is not None
                and childCompletedAt <= workDeadline
            ):
                cleanupTrace = _finishProcess(process, job, normalizedDeadline)
                cleanupTrace += stopProcessGroup(pid, normalizedDeadline)
                resultFrame = tracker.resultFrame
                assert resultFrame is not None
                if resultFrame["status"] == "failed":
                    status = "childFailed"
                    errorCode = str(resultFrame["errorCode"])
                else:
                    payload = _readArtifact(
                        artifactPath,
                        artifactRoot,
                        byteCount=int(resultFrame["byteCount"]),
                        digest=str(resultFrame["digest"]),
                        maxBytes=maxBundleBytes,
                    )
                    results = _decodeBundle(payload, selectors=selectors)
                    if len(results) != int(resultFrame["rowCount"]):
                        raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
                    seal = EagerSeal(
                        payload,
                        hashlib.sha256(payload).hexdigest(),
                        len(payload),
                        len(results),
                        arrowSchemaDigest(_EAGER_SCHEMA),
                    )
                    status = "ok"
            elif time.perf_counter() >= workDeadline or (
                childCompletedAt is not None and childCompletedAt > workDeadline
            ):
                status = "timedOut"
                errorCode = "CONTINUATION_TIMEOUT"
                cleanupTrace = _stopProcess(process, job, normalizedDeadline)
                cleanupTrace += stopProcessGroup(pid, normalizedDeadline)
            else:
                status = "childFailed"
                # 자식이 typed 실패를 이미 보냈다면 그것이 부모의 추정보다 정확하다.
                # 자식은 worker thread 가 non-daemon 이라 결과를 보낸 뒤에도 잠시 더
                # 살아 있을 수 있는데, 그 지연 때문에 진짜 원인을 지우면 안 된다.
                reportedFrame = tracker.resultFrame
                reportedCode = (
                    str(reportedFrame["errorCode"])
                    if reportedFrame is not None and reportedFrame["status"] == "failed"
                    else None
                )
                errorCode = reportedCode or "EAGER_PROCESS_CHILD_DID_NOT_EXIT"
                recordFailure(
                    _log,
                    "EAGER_PROCESS_CHILD_LINGERED",
                    context={
                        "hasResultFrame": reportedFrame is not None,
                        "reportedCode": reportedCode,
                        "childCompleted": childCompletedAt is not None,
                        "processAlive": process.is_alive(),
                    },
                )
                cleanupTrace = _stopProcess(process, job, normalizedDeadline)
                cleanupTrace += stopProcessGroup(pid, normalizedDeadline)
    except ContinuationError as error:
        if processStarted:
            cleanupTrace = _stopProcess(process, job, normalizedDeadline)
            cleanupTrace += stopProcessGroup(pid, normalizedDeadline)
        status = "artifactFailed"
        errorCode = error.code
    except Exception as error:
        if processStarted:
            cleanupTrace = _stopProcess(process, job, normalizedDeadline)
            cleanupTrace += stopProcessGroup(pid, normalizedDeadline)
        status = "childFailed"
        errorCode = _safeErrorCode(error)
    except BaseException:
        if processStarted:
            _stopProcess(process, job, normalizedDeadline)
            stopProcessGroup(pid, normalizedDeadline)
        _removeArtifact(artifactPath)
        raise
    finally:
        startGate.set()
        sendConnection.close()
        receiveConnection.close()
        job.close()

    zeroLive = _zeroLive(process, pid, threadNativeId, job) and not processGroupAlive(pid) if processStarted else True
    try:
        _removeArtifact(artifactPath)
    except ContinuationError as error:
        status = "cleanupFailed"
        seal = None
        errorCode = error.code
    if not zeroLive:
        status = "cleanupFailed"
        seal = None
        errorCode = "EAGER_PROCESS_LIVE_AFTER_CLEANUP"
    endedAt = time.perf_counter()
    outcome = EagerProcessOutcome(
        status,
        seal,
        processStarted,
        pid,
        threadNativeId,
        endedAt - startedAt,
        max(0.0, endedAt - normalizedDeadline),
        len(tracker.frames),
        tracker.byteCount,
        cleanupTrace,
        zeroLive,
        job.attempted,
        job.assigned,
        job.error,
        None if status == "ok" else _publicErrorCode(errorCode),
    )
    recordChildOutcome(outcome)
    return outcome


__all__ = [
    "EagerProcessOutcome",
    "EagerProcessStatus",
    "runEagerSeal",
]
