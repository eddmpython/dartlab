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

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.contracts import DataAssetDescriptor, DataQuery
from dartlab.dataHub.isolation.eagerProcess import (
    _MAX_BUNDLE_BYTES,
    EagerSeal,
)
from dartlab.dataHub.isolation.eagerSupervisorRequest import (
    _buildSealRequest,
    _validateSealArguments,
)
from dartlab.dataHub.isolation.eagerSupervisorRun import (
    EagerProcessStatus,
    _openSealLaunch,
    _pumpSealFrames,
    _releaseSealLaunch,
    _SealLaunch,
    _SealRun,
    _settleSealOutcome,
)
from dartlab.dataHub.isolation.ownerProcess import (
    _removeArtifact,
    _safeErrorCode,
    _stopProcess,
    _WindowsJob,
    _zeroLive,
)
from dartlab.dataHub.isolation.processLifecycle import (
    processGroupAlive,
    stopProcessGroup,
)
from dartlab.dataHub.paging.runtime import (
    MIN_OWNER_PROCESS_WORK_SECONDS,
    OWNER_PROCESS_CLEANUP_GRACE_SECONDS,
)
from dartlab.dataHub.telemetry import dataHubLogger

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

    _validateSealArguments(
        selectors,
        publicDeadline=publicDeadline,
        cleanupGraceSeconds=cleanupGraceSeconds,
        minimumWorkSeconds=minimumWorkSeconds,
        maxBundleBytes=maxBundleBytes,
    )
    startedAt = time.perf_counter()
    normalizedDeadline = float(publicDeadline)
    workDeadline = normalizedDeadline - float(cleanupGraceSeconds)
    if workDeadline - startedAt < float(minimumWorkSeconds):
        return _budgetOutcome(startedAt, normalizedDeadline)

    requestPayload = _buildSealRequest(
        descriptor,
        query,
        selectors,
        requestId=requestId,
        snapshotId=snapshotId,
        contractHash=contractHash,
        universeSnapshotId=universeSnapshotId,
        codePin=codePin,
        maxBundleBytes=maxBundleBytes,
        workDeadline=workDeadline,
    )

    launch = _SealLaunch()
    job = _WindowsJob()
    try:
        _openSealLaunch(launch, job, requestPayload)
    except BaseException as error:
        _releaseSealLaunch(launch, job)
        if not isinstance(error, Exception):
            raise
        return _setupFailure(
            error,
            startedAt=startedAt,
            publicDeadline=normalizedDeadline,
            job=job,
        )
    assert (
        launch.artifactRoot is not None
        and launch.artifactPath is not None
        and launch.receiveConnection is not None
        and launch.sendConnection is not None
        and launch.startGate is not None
        and launch.process is not None
    )
    if workDeadline - time.perf_counter() < float(minimumWorkSeconds):
        launch.startGate.set()
        launch.sendConnection.close()
        launch.receiveConnection.close()
        job.close()
        _removeArtifact(launch.artifactPath)
        return _budgetOutcome(startedAt, normalizedDeadline)
    run = _SealRun()
    try:
        launch.process.start()
        run.processStarted = True
        run.pid = launch.process.pid
        if run.pid is None:
            raise RuntimeError("EAGER_PROCESS_PID_UNAVAILABLE")
        launch.sendConnection.close()
        job.assign(run.pid)
        if job.attempted and not job.assigned:
            run.status = "jobFailed"
            run.errorCode = "EAGER_PROCESS_JOB_REQUIRED"
            run.cleanupTrace = _stopProcess(launch.process, job, normalizedDeadline)
        else:
            launch.startGate.set()
            _pumpSealFrames(run, launch, workDeadline=workDeadline)
            _settleSealOutcome(
                run,
                launch,
                job,
                selectors,
                workDeadline=workDeadline,
                publicDeadline=normalizedDeadline,
                maxBundleBytes=maxBundleBytes,
            )
    except ContinuationError as error:
        if run.processStarted:
            run.cleanupTrace = _stopProcess(launch.process, job, normalizedDeadline)
            run.cleanupTrace += stopProcessGroup(run.pid, normalizedDeadline)
        run.status = "artifactFailed"
        run.errorCode = error.code
    except Exception as error:
        if run.processStarted:
            run.cleanupTrace = _stopProcess(launch.process, job, normalizedDeadline)
            run.cleanupTrace += stopProcessGroup(run.pid, normalizedDeadline)
        run.status = "childFailed"
        run.errorCode = _safeErrorCode(error)
    except BaseException:
        if run.processStarted:
            _stopProcess(launch.process, job, normalizedDeadline)
            stopProcessGroup(run.pid, normalizedDeadline)
        _removeArtifact(launch.artifactPath)
        raise
    finally:
        launch.startGate.set()
        launch.sendConnection.close()
        launch.receiveConnection.close()
        job.close()

    zeroLive = (
        _zeroLive(launch.process, run.pid, run.threadNativeId, job) and not processGroupAlive(run.pid)
        if run.processStarted
        else True
    )
    try:
        _removeArtifact(launch.artifactPath)
    except ContinuationError as error:
        run.status = "cleanupFailed"
        run.seal = None
        run.errorCode = error.code
    if not zeroLive:
        run.status = "cleanupFailed"
        run.seal = None
        run.errorCode = "EAGER_PROCESS_LIVE_AFTER_CLEANUP"
    endedAt = time.perf_counter()
    outcome = EagerProcessOutcome(
        run.status,
        run.seal,
        run.processStarted,
        run.pid,
        run.threadNativeId,
        endedAt - startedAt,
        max(0.0, endedAt - normalizedDeadline),
        len(run.tracker.frames),
        run.tracker.byteCount,
        run.cleanupTrace,
        zeroLive,
        job.attempted,
        job.assigned,
        job.error,
        None if run.status == "ok" else _publicErrorCode(run.errorCode),
    )
    recordChildOutcome(outcome)
    return outcome


__all__ = [
    "EagerProcessOutcome",
    "EagerProcessStatus",
    "runEagerSeal",
]
