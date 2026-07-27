"""Child process 와 worker thread 의 관측, 정지, zero-live 판정 primitive.

Owner page 와 eager seal 두 supervisor 가 같은 규칙으로 자식을 재우고 회수한다. 그
공통 규칙만 여기 모은다. Supervisor 본체는 어느 자식을 어떤 순서로 재울지만 정하고,
"살아 있는가"와 "어떻게 재우는가"는 이 모듈 하나에 둔다.
"""

from __future__ import annotations

import ctypes
import multiprocessing
import os
import time
from multiprocessing.connection import wait
from typing import Any

from dartlab.dataHub.isolation.ownerProcessModels import (
    _PROCESS_QUERY_LIMITED_INFORMATION,
    _STILL_ACTIVE,
    _TERMINATE_PROBE_SECONDS,
    _THREAD_QUERY_LIMITED_INFORMATION,
    _ProtocolViolation,
)
from dartlab.dataHub.isolation.ownerProcessWindows import _ControlTracker, _WindowsJob
from dartlab.dataHub.isolation.processLifecycle import (
    processGroupAlive,
    stopProcessGroup,
)
from dartlab.dataHub.paging.runtime import MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES


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


__all__: list[str] = []
