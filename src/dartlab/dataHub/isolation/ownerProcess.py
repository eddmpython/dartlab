"""계산형 owner page를 spawn 자식 하나에서 hard deadline으로 실행한다.

Continuation cursor와 commit은 parent에 두고 child에는 bounded page 계산만 맡긴다.
성공과 실패 모두에서 private artifact, process, worker zero-live를 검증한다.
"""

from __future__ import annotations

import multiprocessing
import secrets
import time
from pathlib import Path
from typing import Any

from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.isolation.ownerProcessArtifacts import (
    _artifactPath,
    _buildRequest,
    _createArtifact,
    _decodeControlFrame,
    _decodeRequest,
    _ensureArtifactRoot,
    _isReparse,
    _loadStrictJson,
    _readArtifact,
    _rejectDuplicatePairs,
    _removeArtifact,
    _requireArtifactFile,
    _safeErrorCode,
    _strictJson,
    _writeArtifact,
)
from dartlab.dataHub.isolation.ownerProcessChild import _pageChildMain
from dartlab.dataHub.isolation.ownerProcessControl import (
    _awaitChildExit,
    _drainAvailable,
    _finishProcess,
    _sentinelReady,
    _stopProcess,
    _windowsProcessAlive,
    _windowsThreadAlive,
    _zeroLive,
)
from dartlab.dataHub.isolation.ownerProcessModels import (
    OwnerProcessOutcome,
    OwnerProcessPage,
    OwnerProcessStatus,
    _ProtocolViolation,
)
from dartlab.dataHub.isolation.ownerProcessRun import (
    _artifactFailureOutcome,
    _launchFailureOutcome,
    _openArtifact,
    _openOwnerLaunch,
    _OwnerLaunch,
    _OwnerRun,
    _pumpOwnerFrames,
    _releaseOwnerLaunch,
    _settleOwnerOutcome,
    _validateOwnerArguments,
)
from dartlab.dataHub.isolation.ownerProcessWindows import _ControlTracker, _WindowsJob
from dartlab.dataHub.isolation.processLifecycle import (
    processGroupAlive,
    stopProcessGroup,
)
from dartlab.dataHub.paging.runtime import (
    MAX_STATE_BYTES,
    MIN_OWNER_PROCESS_WORK_SECONDS,
    OWNER_PROCESS_CLEANUP_GRACE_SECONDS,
)
from dartlab.dataHub.telemetry import dataHubLogger

_log = dataHubLogger(__name__)


def _recordOwnerOutcome(outcome: OwnerProcessOutcome) -> None:
    """자식 실행 관측치를 진단 채널에 남긴다.

    준비 시간, cleanup trace, zero-live, Job Object 상태는 status 만 보고 버려졌다.
    자식이 왜 실패했는지 알 수 있는 유일한 통로이므로 실패 결과만 기록한다.
    """

    if outcome.status == "ok":
        return
    _log.warning(
        "owner child outcome status=%s errorCode=%s spawned=%s zeroLive=%s "
        "ready=%.3f elapsed=%.3f overshoot=%.3f cleanup=%s jobObject=(attempted=%s assigned=%s error=%s)",
        outcome.status,
        outcome.errorCode,
        outcome.spawned,
        outcome.zeroLive,
        outcome.readySeconds or 0.0,
        outcome.elapsedSeconds,
        outcome.deadlineOvershootSeconds,
        outcome.cleanupTrace,
        outcome.jobObjectAttempted,
        outcome.jobObjectAssigned,
        outcome.jobObjectError,
    )


def _cleanupFailureCode(
    primaryErrorCode: str | None,
    cleanupErrorCode: str | None,
) -> str:
    """Cleanup 실패가 이미 고정된 owner root cause를 덮어쓰지 않게 한다."""

    return primaryErrorCode or cleanupErrorCode or "OWNER_PROCESS_LIVE_AFTER_CLEANUP"


def _budgetOutcome(
    *,
    publicDeadline: float,
    workDeadline: float,
    startedAt: float,
) -> OwnerProcessOutcome:
    endedAt = time.perf_counter()
    return OwnerProcessOutcome(
        status="budgetRejected",
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
        errorCode="OWNER_PROCESS_INSUFFICIENT_WORK_BUDGET",
    )


def runOwnerPage(
    sessionPayload: bytes,
    *,
    publicDeadline: float,
    cleanupGraceSeconds: float = OWNER_PROCESS_CLEANUP_GRACE_SECONDS,
    minimumWorkSeconds: float = MIN_OWNER_PROCESS_WORK_SECONDS,
) -> OwnerProcessOutcome:
    """한 owner page를 fresh spawn child에서 deadline 안에 계산하고 회수한다.

    Capabilities:
        Spawn 전 budget 거부, Windows Job Object, bounded control IPC, sealed
        Arrow artifact 검증, deterministic cleanup과 zero-live 확인을 수행한다.

    Args:
        sessionPayload: ``ownerPaging``의 bounded canonical private session bytes.
        publicDeadline: Parent ``time.perf_counter`` 기준 절대 deadline.
        cleanupGraceSeconds: Terminate, kill, Job close, join에 예약할 초.
        minimumWorkSeconds: Spawn과 유효 작업에 필요한 최소 work window 초.

    Returns:
        성공 page 또는 실패 code와 process 정리 증거를 담은 outcome.

    Raises:
        ValueError: Payload나 deadline 설정이 유효하지 않을 때.

    Example:
        ``runOwnerPage(payload, publicDeadline=time.perf_counter() + 30)``.

    Guide:
        ``workDeadline``은 항상 ``publicDeadline - cleanupGraceSeconds``다.

    When:
        Continuation store의 materializer가 아직 commit하지 않은 page를 계산할 때 사용한다.

    How:
        Parent가 temp artifact를 먼저 만들고 gate 뒤 child 하나를 spawn한다.

    See Also:
        ``OwnerProcessOutcome``과 ``ownerProcessArtifactRoot``.
    Requires:
        Session payload는 ``MAX_STATE_BYTES`` 이하이며 child에서 다시 decode되어야 한다.

    AI Context:
        Timeout과 partial child 결과는 page 전체를 미커밋으로 남긴다.
    """

    _validateOwnerArguments(
        sessionPayload,
        publicDeadline=publicDeadline,
        cleanupGraceSeconds=cleanupGraceSeconds,
        minimumWorkSeconds=minimumWorkSeconds,
    )

    startedAt = time.perf_counter()
    normalizedDeadline = float(publicDeadline)
    workDeadline = normalizedDeadline - float(cleanupGraceSeconds)
    if workDeadline - startedAt < float(minimumWorkSeconds):
        return _budgetOutcome(
            publicDeadline=normalizedDeadline,
            workDeadline=workDeadline,
            startedAt=startedAt,
        )

    launch = _OwnerLaunch(artifactId=secrets.token_hex(32))
    try:
        _openArtifact(launch)
    except ContinuationError as error:
        return _artifactFailureOutcome(
            error,
            launch,
            startedAt=startedAt,
            publicDeadline=normalizedDeadline,
            workDeadline=workDeadline,
        )
    if workDeadline - time.perf_counter() < float(minimumWorkSeconds):
        assert launch.artifactPath is not None
        _removeArtifact(launch.artifactPath)
        return _budgetOutcome(
            publicDeadline=normalizedDeadline,
            workDeadline=workDeadline,
            startedAt=startedAt,
        )

    job = _WindowsJob()
    try:
        _openOwnerLaunch(launch, job, sessionPayload, workDeadline=workDeadline)
    except BaseException as error:
        _releaseOwnerLaunch(launch, job)
        if not isinstance(error, Exception):
            raise
        return _launchFailureOutcome(
            error,
            job,
            startedAt=startedAt,
            publicDeadline=normalizedDeadline,
            workDeadline=workDeadline,
        )
    assert (
        launch.receiveConnection is not None
        and launch.sendConnection is not None
        and launch.startGate is not None
        and launch.process is not None
    )
    run = _OwnerRun()

    try:
        launch.process.start()
        run.processStarted = True
        run.pid = launch.process.pid
        if run.pid is None:
            raise RuntimeError("OWNER_PROCESS_PID_UNAVAILABLE")
        launch.sendConnection.close()
        job.assign(run.pid)
        if job.attempted and not job.assigned:
            run.status = "jobFailed"
            run.errorCode = "OWNER_PROCESS_JOB_REQUIRED"
            run.cleanupTrace = _stopProcess(launch.process, job, normalizedDeadline)
        else:
            launch.startGate.set()
            _pumpOwnerFrames(run, launch, workDeadline=workDeadline, startedAt=startedAt)
            _settleOwnerOutcome(
                run,
                launch,
                job,
                sessionPayload,
                workDeadline=workDeadline,
                publicDeadline=normalizedDeadline,
            )
    except Exception as error:
        if run.processStarted:
            run.cleanupTrace = _stopProcess(launch.process, job, normalizedDeadline)
        run.status = "childFailed"
        run.errorCode = _safeErrorCode(error)
    except BaseException:
        if run.processStarted:
            _stopProcess(launch.process, job, normalizedDeadline)
        assert launch.artifactPath is not None
        _removeArtifact(launch.artifactPath)
        raise
    finally:
        launch.startGate.set()
        launch.sendConnection.close()
        launch.receiveConnection.close()
        job.close()

    zeroLive = _zeroLive(launch.process, run.pid, run.threadNativeId, job) if run.processStarted else True
    cleanupError: str | None = None
    assert launch.artifactPath is not None
    try:
        _removeArtifact(launch.artifactPath)
    except ContinuationError as error:
        cleanupError = error.code
    if not zeroLive or cleanupError is not None:
        run.status = "cleanupFailed"
        run.page = None
        run.errorCode = _cleanupFailureCode(run.errorCode, cleanupError)
    endedAt = time.perf_counter()
    outcome = OwnerProcessOutcome(
        status=run.status,
        page=run.page,
        spawned=run.processStarted,
        pid=run.pid,
        threadNativeId=run.threadNativeId,
        publicDeadline=normalizedDeadline,
        workDeadline=workDeadline,
        readySeconds=run.readySeconds,
        elapsedSeconds=endedAt - startedAt,
        deadlineOvershootSeconds=max(0.0, endedAt - normalizedDeadline),
        ipcFrameCount=len(run.tracker.frames),
        ipcByteCount=run.tracker.byteCount,
        cleanupTrace=run.cleanupTrace,
        zeroLive=zeroLive,
        jobObjectAttempted=job.attempted,
        jobObjectAssigned=job.assigned,
        jobObjectError=job.error,
        errorCode=run.errorCode,
    )
    _recordOwnerOutcome(outcome)
    return outcome


__all__ = [
    "OwnerProcessOutcome",
    "OwnerProcessPage",
    "OwnerProcessStatus",
    "runOwnerPage",
]
