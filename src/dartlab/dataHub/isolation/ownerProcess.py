"""계산형 owner page를 spawn 자식 하나에서 hard deadline으로 실행한다.

Continuation cursor와 commit은 parent에 두고 child에는 bounded page 계산만 맡긴다.
성공과 실패 모두에서 private artifact, process, worker zero-live를 검증한다.
"""

from __future__ import annotations

import ctypes
import hashlib
import math
import multiprocessing
import os
import secrets
import time
from multiprocessing.connection import wait
from pathlib import Path
from typing import Any, cast

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
from dartlab.dataHub.isolation.ownerProcessModels import (
    _PROCESS_QUERY_LIMITED_INFORMATION,
    _STILL_ACTIVE,
    _TERMINATE_PROBE_SECONDS,
    _THREAD_QUERY_LIMITED_INFORMATION,
    OwnerProcessOutcome,
    OwnerProcessPage,
    OwnerProcessStatus,
    _ProtocolViolation,
)
from dartlab.dataHub.isolation.ownerProcessWindows import _ControlTracker, _WindowsJob
from dartlab.dataHub.isolation.processLifecycle import (
    processGroupAlive,
    stopProcessGroup,
)
from dartlab.dataHub.paging.runtime import (
    MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES,
    MAX_STATE_BYTES,
    MIN_OWNER_PROCESS_WORK_SECONDS,
    OWNER_PROCESS_CLEANUP_GRACE_SECONDS,
)
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

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


def _drainAvailable(
    receiveConnection: Any,
    tracker: _ControlTracker,
    *,
    artifactId: str,
) -> None:
    while not tracker.eof:
        try:
            available = receiveConnection.poll()
        except (BrokenPipeError, OSError):
            tracker.eof = True
            return
        if not available:
            return
        try:
            payload = receiveConnection.recv_bytes(MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES)
        except EOFError:
            tracker.eof = True
            return
        except OSError:
            raise _ProtocolViolation("OWNER_PROCESS_CONTROL_FRAME_SIZE") from None
        tracker.consume(payload, artifactId=artifactId)


def _sentinelReady(process: Any, timeoutSeconds: float) -> bool:
    if process.exitcode is not None:
        return True
    if timeoutSeconds <= 0:
        return not process.is_alive()
    return bool(wait([process.sentinel], timeout=timeoutSeconds))


# 결과 프레임 도착 후 자식이 실제로 빠져나가기까지 봐 주는 여유.
# 자식의 worker thread 는 non-daemon 이라 결과를 보낸 뒤에도 잠시 더 살아 있다.
# 기한(workDeadline)에 견줘 짧게 잡아 실제 정지 감지를 늦추지 않는다.
_CHILD_EXIT_GRACE_SECONDS = 5.0


def _awaitChildExit(process: Any, workDeadline: float) -> bool:
    """결과를 받은 자식이 실제로 종료했는지, 짧은 여유를 두고 판정한다.

    그 순간의 ``is_alive()`` 만 보면 결과를 정상으로 보낸 실행도 childFailed 로
    뒤집힌다. 자식은 결과 프레임을 보낸 직후 worker thread 를 정리하느라 수십 ms
    더 살아 있고, 부모가 그 창을 이기면 성공이 실패로 기록된다. 기한을 넘기지
    않는 선에서만 기다리므로 진짜로 멈춘 자식은 그대로 실패로 남는다.

    Args:
        process: 검사 대상 자식 프로세스.
        workDeadline: 작업 기한 (perf_counter 절대값).

    Returns:
        bool: 자식이 종료했으면 True.
    """
    remaining = max(0.0, workDeadline - time.perf_counter())
    return _sentinelReady(process, min(_CHILD_EXIT_GRACE_SECONDS, remaining))


def _stopProcess(
    process: Any,
    job: _WindowsJob,
    publicDeadline: float,
) -> tuple[str, ...]:
    trace: list[str] = []
    if process.is_alive():
        process.terminate()
        trace.append("terminate")
        remaining = max(0.0, publicDeadline - time.perf_counter())
        _sentinelReady(process, min(_TERMINATE_PROBE_SECONDS, remaining))
        if process.is_alive():
            process.kill()
            trace.append("kill")
    trace.extend(stopProcessGroup(process.pid, publicDeadline))
    if job.close():
        trace.append("jobClose")
    process.join(timeout=max(0.0, publicDeadline - time.perf_counter()))
    trace.append("join")
    return tuple(trace)


def _finishProcess(
    process: Any,
    job: _WindowsJob,
    publicDeadline: float,
) -> tuple[str, ...]:
    trace: list[str] = []
    if job.close():
        trace.append("jobClose")
    process.join(timeout=max(0.0, publicDeadline - time.perf_counter()))
    trace.append("join")
    return tuple(trace)


def _windowsProcessAlive(pid: int | None) -> bool:
    if pid is None:
        return False
    if os.name != "nt":
        return any(child.pid == pid and child.is_alive() for child in multiprocessing.active_children())
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.GetExitCodeProcess.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_ulong),
    ]
    kernel32.GetExitCodeProcess.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    processHandle = kernel32.OpenProcess(
        _PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid,
    )
    if not processHandle:
        return False
    try:
        exitCode = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(processHandle, ctypes.byref(exitCode)):
            return False
        return exitCode.value == _STILL_ACTIVE
    finally:
        kernel32.CloseHandle(processHandle)


def _windowsThreadAlive(nativeId: int | None) -> bool:
    if nativeId is None or os.name != "nt":
        return False
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenThread.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel32.OpenThread.restype = ctypes.c_void_p
    kernel32.GetExitCodeThread.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_ulong),
    ]
    kernel32.GetExitCodeThread.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    threadHandle = kernel32.OpenThread(
        _THREAD_QUERY_LIMITED_INFORMATION,
        False,
        nativeId,
    )
    if not threadHandle:
        return False
    try:
        exitCode = ctypes.c_ulong()
        if not kernel32.GetExitCodeThread(threadHandle, ctypes.byref(exitCode)):
            return False
        return exitCode.value == _STILL_ACTIVE
    finally:
        kernel32.CloseHandle(threadHandle)


def _zeroLive(
    process: Any,
    pid: int | None,
    threadNativeId: int | None,
    job: _WindowsJob,
) -> bool:
    activePids = {
        child.pid for child in multiprocessing.active_children() if child.pid is not None and child.is_alive()
    }
    directZeroLive = (
        not process.is_alive()
        and pid not in activePids
        and not _windowsProcessAlive(pid)
        and not _windowsThreadAlive(threadNativeId)
    )
    jobTreeReleased = not job.attempted or (job.assigned and job.closedSuccessfully and job.error is None)
    # POSIX 에서 `jobTreeReleased` 는 무조건 참이라 손자 프로세스를 놓친다. group 이
    # 비었는지 직접 확인해 Windows 와 같은 강도의 zero-live 판정을 만든다.
    groupReleased = not processGroupAlive(pid)
    return directZeroLive and jobTreeReleased and groupReleased


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

    # IPC payload 는 durable state 와 달리 엔티티 목록을 함께 싣는다. 한 page 실행
    # 동안만 존재하므로 durable state 상한이 아니라 request 상한을 적용한다.
    if not isinstance(sessionPayload, bytes) or not sessionPayload or len(sessionPayload) > MAX_STATE_BYTES:
        raise ValueError("owner session payload 크기가 유효하지 않습니다")
    numeric = (publicDeadline, cleanupGraceSeconds, minimumWorkSeconds)
    if any(type(value) not in {int, float} or not math.isfinite(value) for value in numeric):
        raise ValueError("owner process deadline 값은 유한한 숫자여야 합니다")
    if cleanupGraceSeconds <= 0 or minimumWorkSeconds <= 0:
        raise ValueError("owner process deadline 예약은 양수여야 합니다")

    startedAt = time.perf_counter()
    normalizedDeadline = float(publicDeadline)
    workDeadline = normalizedDeadline - float(cleanupGraceSeconds)
    if workDeadline - startedAt < float(minimumWorkSeconds):
        return _budgetOutcome(
            publicDeadline=normalizedDeadline,
            workDeadline=workDeadline,
            startedAt=startedAt,
        )

    artifactId = secrets.token_hex(32)
    artifactRoot: Path | None = None
    artifactPath: Path | None = None
    try:
        artifactRoot = _ensureArtifactRoot()
        artifactPath = _artifactPath(artifactRoot, artifactId)
        _createArtifact(artifactPath, artifactRoot)
    except ContinuationError as error:
        endedAt = time.perf_counter()
        if artifactPath is not None:
            try:
                _removeArtifact(artifactPath)
            except ContinuationError:
                pass
        return OwnerProcessOutcome(
            status="artifactFailed",
            page=None,
            spawned=False,
            pid=None,
            threadNativeId=None,
            publicDeadline=normalizedDeadline,
            workDeadline=workDeadline,
            readySeconds=None,
            elapsedSeconds=endedAt - startedAt,
            deadlineOvershootSeconds=max(0.0, endedAt - normalizedDeadline),
            ipcFrameCount=0,
            ipcByteCount=0,
            cleanupTrace=(),
            zeroLive=True,
            jobObjectAttempted=False,
            jobObjectAssigned=False,
            jobObjectError=None,
            errorCode=error.code,
        )
    if workDeadline - time.perf_counter() < float(minimumWorkSeconds):
        assert artifactPath is not None
        _removeArtifact(artifactPath)
        return _budgetOutcome(
            publicDeadline=normalizedDeadline,
            workDeadline=workDeadline,
            startedAt=startedAt,
        )

    job = _WindowsJob()
    receiveConnection: Any | None = None
    sendConnection: Any | None = None
    startGate: Any | None = None
    process: Any | None = None
    try:
        requestPayload = _buildRequest(
            sessionPayload,
            artifactId=artifactId,
            workDeadline=workDeadline,
        )
        context = multiprocessing.get_context("spawn")
        receiveConnection, sendConnection = context.Pipe(duplex=False)
        startGate = context.Event()
        process = context.Process(
            target=_pageChildMain,
            args=(sendConnection, startGate, requestPayload, artifactId),
            name="dartlab-owner-page",
            daemon=False,
        )
        job.create()
    except BaseException as error:
        if sendConnection is not None:
            sendConnection.close()
        if receiveConnection is not None:
            receiveConnection.close()
        job.close()
        assert artifactPath is not None
        _removeArtifact(artifactPath)
        if not isinstance(error, Exception):
            raise
        endedAt = time.perf_counter()
        return OwnerProcessOutcome(
            status="childFailed",
            page=None,
            spawned=False,
            pid=None,
            threadNativeId=None,
            publicDeadline=normalizedDeadline,
            workDeadline=workDeadline,
            readySeconds=None,
            elapsedSeconds=endedAt - startedAt,
            deadlineOvershootSeconds=max(0.0, endedAt - normalizedDeadline),
            ipcFrameCount=0,
            ipcByteCount=0,
            cleanupTrace=(),
            zeroLive=True,
            jobObjectAttempted=job.attempted,
            jobObjectAssigned=job.assigned,
            jobObjectError=job.error,
            errorCode=_safeErrorCode(error),
        )
    assert (
        receiveConnection is not None and sendConnection is not None and startGate is not None and process is not None
    )
    tracker = _ControlTracker(frames=[])
    status: OwnerProcessStatus = "childFailed"
    errorCode: str | None = None
    page: OwnerProcessPage | None = None
    cleanupTrace: tuple[str, ...] = ()
    pid: int | None = None
    threadNativeId: int | None = None
    readySeconds: float | None = None
    processStarted = False
    protocolError: str | None = None
    childCompletedAt: float | None = None

    try:
        process.start()
        processStarted = True
        pid = process.pid
        if pid is None:
            raise RuntimeError("OWNER_PROCESS_PID_UNAVAILABLE")
        sendConnection.close()
        job.assign(pid)
        if job.attempted and not job.assigned:
            status = "jobFailed"
            errorCode = "OWNER_PROCESS_JOB_REQUIRED"
            cleanupTrace = _stopProcess(process, job, normalizedDeadline)
        else:
            startGate.set()
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
                            artifactId=artifactId,
                        )
                    except _ProtocolViolation as error:
                        protocolError = str(error)
                        break
                    readyFrame = tracker.readyFrame
                    if readyFrame is not None and readySeconds is None:
                        if readyFrame["pid"] != pid:
                            protocolError = "OWNER_PROCESS_READY_PID_MISMATCH"
                            break
                        readySeconds = time.perf_counter() - startedAt
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
                if tracker.resultFrame is not None and _sentinelReady(process, remaining):
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

            if protocolError is not None:
                status = "protocolFailed"
                errorCode = protocolError
                cleanupTrace = _stopProcess(process, job, normalizedDeadline)
            elif (
                tracker.resultFrame is not None
                and childCompletedAt is not None
                and childCompletedAt <= workDeadline
                and _awaitChildExit(process, workDeadline)
            ):
                cleanupTrace = _finishProcess(process, job, normalizedDeadline)
                resultFrame = tracker.resultFrame
                assert resultFrame is not None
                if resultFrame["status"] == "failed":
                    status = "childFailed"
                    errorCode = str(resultFrame["errorCode"])
                else:
                    assert artifactRoot is not None and artifactPath is not None
                    try:
                        from dartlab.dataHub.paging import owner as ownerPaging

                        session = ownerPaging._decodeSession(sessionPayload)
                        payload = _readArtifact(
                            artifactPath,
                            artifactRoot,
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
                        page = OwnerProcessPage(
                            payload=payload,
                            rowCount=decoded.facts.rowCount,
                            byteCount=len(payload),
                            payloadDigest=hashlib.sha256(payload).hexdigest(),
                        )
                        status = "ok"
                    except ContinuationError as error:
                        status = "artifactFailed"
                        errorCode = error.code
            elif time.perf_counter() >= workDeadline or (
                childCompletedAt is not None and childCompletedAt > workDeadline
            ):
                status = "timedOut"
                errorCode = "CONTINUATION_TIMEOUT"
                cleanupTrace = _stopProcess(process, job, normalizedDeadline)
            elif tracker.resultFrame is not None:
                status = "childFailed"
                # 여유를 주고도 자식이 안 빠져나갔다. 자식이 typed 실패를 이미 보냈다면
                # 그것이 부모의 추정보다 정확하다 (eagerSupervisor 와 동형).
                reportedFrame = tracker.resultFrame
                reportedCode = str(reportedFrame["errorCode"]) if reportedFrame["status"] == "failed" else None
                errorCode = reportedCode or "OWNER_PROCESS_CHILD_DID_NOT_EXIT"
                recordFailure(
                    _log,
                    "OWNER_PROCESS_CHILD_LINGERED",
                    context={
                        "reportedCode": reportedCode,
                        "childCompleted": childCompletedAt is not None,
                        "processAlive": process.is_alive(),
                    },
                )
                cleanupTrace = _stopProcess(process, job, normalizedDeadline)
            else:
                status = "childFailed"
                errorCode = f"OWNER_PROCESS_CHILD_EXIT_{process.exitcode}"
                cleanupTrace = _finishProcess(process, job, normalizedDeadline)
    except Exception as error:
        if processStarted:
            cleanupTrace = _stopProcess(process, job, normalizedDeadline)
        status = "childFailed"
        errorCode = _safeErrorCode(error)
    except BaseException:
        if processStarted:
            _stopProcess(process, job, normalizedDeadline)
        assert artifactPath is not None
        _removeArtifact(artifactPath)
        raise
    finally:
        startGate.set()
        sendConnection.close()
        receiveConnection.close()
        job.close()

    zeroLive = _zeroLive(process, pid, threadNativeId, job) if processStarted else True
    cleanupError: str | None = None
    assert artifactPath is not None
    try:
        _removeArtifact(artifactPath)
    except ContinuationError as error:
        cleanupError = error.code
    if not zeroLive or cleanupError is not None:
        status = "cleanupFailed"
        page = None
        errorCode = _cleanupFailureCode(errorCode, cleanupError)
    endedAt = time.perf_counter()
    outcome = OwnerProcessOutcome(
        status=status,
        page=page,
        spawned=processStarted,
        pid=pid,
        threadNativeId=threadNativeId,
        publicDeadline=normalizedDeadline,
        workDeadline=workDeadline,
        readySeconds=readySeconds,
        elapsedSeconds=endedAt - startedAt,
        deadlineOvershootSeconds=max(0.0, endedAt - normalizedDeadline),
        ipcFrameCount=len(tracker.frames),
        ipcByteCount=tracker.byteCount,
        cleanupTrace=cleanupTrace,
        zeroLive=zeroLive,
        jobObjectAttempted=job.attempted,
        jobObjectAssigned=job.assigned,
        jobObjectError=job.error,
        errorCode=errorCode,
    )
    _recordOwnerOutcome(outcome)
    return outcome


__all__ = [
    "OwnerProcessOutcome",
    "OwnerProcessPage",
    "OwnerProcessStatus",
    "runOwnerPage",
]
