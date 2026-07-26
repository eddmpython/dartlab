"""Owner child process의 Windows Job Object와 control tracker."""

from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from typing import Any

from dartlab.dataHub.isolation.ownerProcessArtifacts import _decodeControlFrame
from dartlab.dataHub.isolation.ownerProcessModels import (
    _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    _MAX_CONTROL_FRAMES,
    _PROCESS_QUERY_LIMITED_INFORMATION,
    _PROCESS_SET_QUOTA,
    _PROCESS_TERMINATE,
    _ProtocolViolation,
)
from dartlab.dataHub.pagingRuntime import MAX_OWNER_PROCESS_CONTROL_BYTES


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("readOperationCount", ctypes.c_ulonglong),
        ("writeOperationCount", ctypes.c_ulonglong),
        ("otherOperationCount", ctypes.c_ulonglong),
        ("readTransferCount", ctypes.c_ulonglong),
        ("writeTransferCount", ctypes.c_ulonglong),
        ("otherTransferCount", ctypes.c_ulonglong),
    ]


class _JobObjectBasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("perProcessUserTimeLimit", ctypes.c_longlong),
        ("perJobUserTimeLimit", ctypes.c_longlong),
        ("limitFlags", ctypes.c_ulong),
        ("minimumWorkingSetSize", ctypes.c_size_t),
        ("maximumWorkingSetSize", ctypes.c_size_t),
        ("activeProcessLimit", ctypes.c_ulong),
        ("affinity", ctypes.c_size_t),
        ("priorityClass", ctypes.c_ulong),
        ("schedulingClass", ctypes.c_ulong),
    ]


class _JobObjectExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("basicLimitInformation", _JobObjectBasicLimitInformation),
        ("ioInfo", _IoCounters),
        ("processMemoryLimit", ctypes.c_size_t),
        ("jobMemoryLimit", ctypes.c_size_t),
        ("peakProcessMemoryUsed", ctypes.c_size_t),
        ("peakJobMemoryUsed", ctypes.c_size_t),
    ]


class _WindowsJob:
    def __init__(self) -> None:
        self.handle: int | None = None
        self.attempted = os.name == "nt"
        self.assigned = False
        self.closedSuccessfully = False
        self.error: str | None = None

    def create(self) -> None:
        """Kill-on-close Windows Job Object를 만든다.

        Capabilities:
            Child process tree의 강제 회수 경계를 준비한다.

        Args:
            없음.

        Returns:
            없음. 성공 여부와 Windows error는 instance field에 남긴다.

        Raises:
            Windows API 예외를 외부로 전달하지 않는다.

        Example:
            ``job.create()``.

        Guide:
            Child spawn 전에 호출하고 handle을 parent에서만 소유한다.

        When:
            한 owner page의 process supervisor를 초기화할 때 사용한다.

        How:
            Extended limit에 kill-on-close flag를 설정한다.

        See Also:
            ``assign``과 ``close``.

        Requires:
            Windows에서는 kernel32 Job Object API가 필요하다.

        AI Context:
            Windows가 아니면 아무 handle도 만들지 않는 명시적 no-op이다.
        """

        if os.name != "nt":
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        kernel32.CreateJobObjectW.restype = ctypes.c_void_p
        kernel32.SetInformationJobObject.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_ulong,
        ]
        kernel32.SetInformationJobObject.restype = ctypes.c_int
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            self.error = _windowsError("OWNER_PROCESS_JOB_CREATE_FAILED")
            return
        information = _JobObjectExtendedLimitInformation()
        information.basicLimitInformation.limitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        configured = kernel32.SetInformationJobObject(
            handle,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(information),
            ctypes.sizeof(information),
        )
        if not configured:
            self.handle = int(handle)
            self.error = _windowsError("OWNER_PROCESS_JOB_CONFIGURE_FAILED")
            self.close()
            return
        self.handle = int(handle)

    def assign(self, pid: int) -> None:
        """Spawn한 child PID를 준비된 Job Object에 할당한다.

        Capabilities:
            Gate가 열리기 전에 child와 모든 후손의 kill 경계를 고정한다.

        Args:
            pid: 양수인 child process ID.

        Returns:
            없음. 할당 결과는 ``assigned``와 ``error``에 기록한다.

        Raises:
            Windows API 예외를 외부로 전달하지 않는다.

        Example:
            ``job.assign(process.pid)``.

        Guide:
            성공을 확인한 뒤에만 child start gate를 연다.

        When:
            ``Process.start`` 직후 child가 owner 작업을 시작하기 전에 사용한다.

        How:
            Process handle을 열어 Job Object에 한 번 할당한다.

        See Also:
            ``create``과 ``close``.

        Requires:
            유효한 Job handle과 아직 살아 있는 Windows PID가 필요하다.

        AI Context:
            할당 실패는 production에서 fail-closed한다.
        """

        if os.name != "nt" or self.handle is None:
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        kernel32.AssignProcessToJobObject.restype = ctypes.c_int
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        processHandle = kernel32.OpenProcess(
            _PROCESS_SET_QUOTA | _PROCESS_TERMINATE | _PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid,
        )
        if not processHandle:
            self.error = _windowsError("OWNER_PROCESS_JOB_OPEN_FAILED")
            return
        try:
            if not kernel32.AssignProcessToJobObject(self.handle, processHandle):
                self.error = _windowsError("OWNER_PROCESS_JOB_ASSIGN_FAILED")
                return
            self.assigned = True
        finally:
            kernel32.CloseHandle(processHandle)

    def close(self) -> bool:
        """Job Object handle을 닫아 남은 process tree를 회수한다.

        Capabilities:
            Kill-on-close를 실행하고 native handle을 정확히 한 번 해제한다.

        Args:
            없음.

        Returns:
            실제 handle을 닫았으면 ``True``를 반환한다.

        Raises:
            Windows API 예외를 외부로 전달하지 않는다.

        Example:
            ``closed = job.close()``.

        Guide:
            Timeout cleanup에서는 terminate와 kill 뒤, join 전에 호출한다.

        When:
            성공 또는 실패 child 정리 단계에서 항상 사용한다.

        How:
            ``CloseHandle``을 호출하고 instance handle을 ``None``으로 바꾼다.

        See Also:
            ``create``과 ``assign``.

        Requires:
            Windows Job handle이 있을 때만 실제 close를 수행한다.

        AI Context:
            반복 호출은 안전한 no-op이며 cleanup trace는 반환값으로 결정한다.
        """

        if os.name != "nt" or self.handle is None:
            return False
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        closed = bool(kernel32.CloseHandle(self.handle))
        if not closed:
            if self.error is None:
                self.error = _windowsError("OWNER_PROCESS_JOB_CLOSE_FAILED")
            return False
        self.handle = None
        self.closedSuccessfully = True
        return True


@dataclass(slots=True)
class _ControlTracker:
    frames: list[dict[str, Any]]
    byteCount: int = 0
    eof: bool = False

    @property
    def readyFrame(self) -> dict[str, Any] | None:
        """검증된 ready 제어 frame을 반환한다.

        Capabilities:
            Bounded frame 목록에서 child readiness 사실만 선택한다.

        Args:
            없음.

        Returns:
            Ready mapping 또는 아직 도착하지 않았으면 ``None``.

        Raises:
            예외를 발생시키지 않는다.

        Example:
            ``tracker.readyFrame``.

        Guide:
            PID와 worker native thread ID는 이 mapping에서만 읽는다.

        When:
            Parent가 IPC를 drain한 직후 readiness 시간을 기록할 때 사용한다.

        How:
            최대 두 frame의 validated 목록을 순서대로 탐색한다.

        See Also:
            ``resultFrame``과 ``consume``.

        Requires:
            Frame은 ``consume``을 통과한 값이어야 한다.

        AI Context:
            Raw pipe bytes를 직접 노출하지 않는다.
        """

        return next((frame for frame in self.frames if frame["kind"] == "ready"), None)

    @property
    def resultFrame(self) -> dict[str, Any] | None:
        """검증된 result 제어 frame을 반환한다.

        Capabilities:
            Bounded frame 목록에서 artifact claim만 선택한다.

        Args:
            없음.

        Returns:
            Result mapping 또는 아직 도착하지 않았으면 ``None``.

        Raises:
            예외를 발생시키지 않는다.

        Example:
            ``tracker.resultFrame``.

        Guide:
            Child process 종료 전에는 이 frame만으로 성공을 판정하지 않는다.

        When:
            Parent가 child sentinel과 artifact 검증을 결정할 때 사용한다.

        How:
            최대 두 frame의 validated 목록을 순서대로 탐색한다.

        See Also:
            ``readyFrame``과 ``consume``.

        Requires:
            Frame은 ``consume``을 통과한 값이어야 한다.

        AI Context:
            Locator가 아니라 parent-known artifact ID와 digest claim만 제공한다.
        """

        return next((frame for frame in self.frames if frame["kind"] == "result"), None)

    def consume(self, payload: bytes, *, artifactId: str) -> None:
        """한 bounded JSON control frame을 검증해 보존한다.

        Capabilities:
            Frame 수, 합계 bytes, schema, 순서, parent artifact ID를 강제한다.

        Args:
            payload: Pipe에서 maxlength 제한으로 읽은 한 frame bytes.
            artifactId: Parent가 미리 지정한 lowercase hex artifact ID.

        Returns:
            없음. 검증된 mapping을 내부 frame 목록에 추가한다.

        Raises:
            _ProtocolViolation: Size, schema, order 또는 identity가 다를 때.

        Example:
            ``tracker.consume(frame, artifactId=artifactId)``.

        Guide:
            Raw ``recv``가 아니라 ``recv_bytes(maxlength)`` 결과만 전달한다.

        When:
            Parent event loop가 pipe readability를 관측할 때마다 사용한다.

        How:
            Strict JSON decode 후 ready와 result 순서를 정확히 비교한다.

        See Also:
            ``readyFrame``과 ``resultFrame``.

        Requires:
            전체 IPC 합계가 고정된 control byte 상한 안에 있어야 한다.

        AI Context:
            Factor payload는 이 control frame으로 운반하지 않는다.
        """

        nextBytes = self.byteCount + len(payload)
        if len(self.frames) >= _MAX_CONTROL_FRAMES:
            raise _ProtocolViolation("OWNER_PROCESS_CONTROL_FRAME_COUNT")
        if nextBytes > MAX_OWNER_PROCESS_CONTROL_BYTES:
            raise _ProtocolViolation("OWNER_PROCESS_CONTROL_BYTE_BUDGET")
        frame = _decodeControlFrame(payload, artifactId=artifactId)
        expectedKind = "ready" if not self.frames else "result"
        if frame["kind"] != expectedKind:
            raise _ProtocolViolation("OWNER_PROCESS_CONTROL_ORDER")
        self.frames.append(frame)
        self.byteCount = nextBytes


def _windowsError(prefix: str) -> str:
    return f"{prefix}:{ctypes.get_last_error()}"
