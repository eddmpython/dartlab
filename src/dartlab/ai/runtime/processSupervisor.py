"""에이전트 CLI 자식 프로세스와 NDJSON 전송을 감독한다."""

from __future__ import annotations

import ctypes
import json
import os
import queue
import signal
import subprocess
import threading
import time
from collections import deque
from typing import Any

from .contracts import ProcessSpec


class ProcessClosedError(RuntimeError):
    """자식 프로세스가 예상보다 일찍 종료되었을 때 발생한다."""


class ProcessSupervisor:
    """shell 없이 프로세스를 실행하고 출력 예산과 종료 트리를 관리한다."""

    def __init__(self, spec: ProcessSpec):
        self.spec = spec
        self.process: subprocess.Popen[bytes] | None = None
        self._stdout: queue.Queue[bytes | None] = queue.Queue(maxsize=512)
        self._stderr: deque[bytes] = deque()
        self._stderrBytes = 0
        self._jobHandle: int | None = None
        self._writeLock = threading.Lock()
        self._stderrLock = threading.Lock()

    def start(self) -> None:
        """Sig: start() -> None.

        Args: 없음.
        Returns: None.
        Raises: OSError if the executable cannot be launched.
        Example: `supervisor.start()`.
        """
        if self.process is not None:
            return
        environment = os.environ.copy()
        environment.update(self.spec.env)
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        self.process = subprocess.Popen(
            list(self.spec.argv),
            cwd=self.spec.cwd,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=os.name != "nt",
            creationflags=flags,
        )
        if os.name == "nt":
            self._jobHandle = _attachWindowsJob(self.process)
        threading.Thread(target=self._readStdout, name="dartlab-agent-stdout", daemon=True).start()
        threading.Thread(target=self._readStderr, name="dartlab-agent-stderr", daemon=True).start()

    def _readStdout(self) -> None:
        """Sig: _readStdout() -> None.

        Args: 없음.
        Returns: None after EOF.
        Example: 내부 reader thread에서만 호출한다.
        """
        assert self.process is not None and self.process.stdout is not None
        try:
            while True:
                line = self.process.stdout.readline(self.spec.maxFrameBytes + 1)
                if not line:
                    break
                self._stdout.put(line)
        finally:
            self._stdout.put(None)

    def _readStderr(self) -> None:
        """Sig: _readStderr() -> None.

        Args: 없음.
        Returns: None after EOF.
        Example: 내부 reader thread에서만 호출한다.
        """
        assert self.process is not None and self.process.stderr is not None
        while True:
            chunk = self.process.stderr.read(4096)
            if not chunk:
                return
            with self._stderrLock:
                self._stderr.append(chunk)
                self._stderrBytes += len(chunk)
                while self._stderr and self._stderrBytes > self.spec.outputLimitBytes:
                    self._stderrBytes -= len(self._stderr.popleft())

    def sendJson(self, value: dict[str, Any]) -> None:
        """Sig: sendJson(value) -> None.

        Args: value는 NDJSON 한 프레임이다.
        Returns: None.
        Raises: ProcessClosedError if stdin is unavailable.
        Example: `supervisor.sendJson({"jsonrpc": "2.0"})`.
        """
        if self.process is None or self.process.stdin is None or self.process.poll() is not None:
            raise ProcessClosedError("agent runtime process is not running")
        frame = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        if len(frame) > self.spec.maxFrameBytes:
            raise ValueError("runtime frame exceeds 1 MiB")
        with self._writeLock:
            self.process.stdin.write(frame)
            self.process.stdin.flush()

    def readJson(self, *, timeout: float = 30.0) -> dict[str, Any]:
        """Sig: readJson(*, timeout=30.0) -> dict[str, Any].

        Args: timeout은 한 프레임 대기 초다.
        Returns: 파싱된 NDJSON 객체다.
        Raises: TimeoutError, ValueError, ProcessClosedError on transport failure.
        Example: `message = supervisor.readJson(timeout=5)`.
        """
        try:
            line = self._stdout.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError("agent runtime response timeout") from exc
        if line is None:
            raise ProcessClosedError(self.stderrText() or "agent runtime process closed")
        if len(line) > self.spec.maxFrameBytes:
            raise ValueError("runtime frame exceeds 1 MiB")
        value = json.loads(line.decode("utf-8", errors="strict"))
        if not isinstance(value, dict):
            raise ValueError("runtime frame must be a JSON object")
        return value

    def stderrText(self) -> str:
        """Sig: stderrText() -> str.

        Args: 없음.
        Returns: 예산 안에서 보존한 stderr 문자열이다.
        Example: `detail = supervisor.stderrText()`.
        """
        with self._stderrLock:
            value = b"".join(self._stderr)
        return value.decode("utf-8", errors="replace")

    def stop(self, *, graceSeconds: float = 2.0) -> None:
        """Sig: stop(*, graceSeconds=2.0) -> None.

        Args: graceSeconds는 정상 종료 대기 시간이다.
        Returns: None.
        Example: `supervisor.stop()`.
        """
        process = self.process
        if process is None:
            return
        if process.poll() is None:
            try:
                if process.stdin:
                    process.stdin.close()
                process.wait(timeout=graceSeconds)
            except (OSError, subprocess.TimeoutExpired):
                if os.name == "nt" and self._jobHandle:
                    ctypes.windll.kernel32.CloseHandle(self._jobHandle)
                    self._jobHandle = None
                elif os.name != "nt":
                    os.killpg(process.pid, signal.SIGTERM)
                else:
                    process.terminate()
                try:
                    process.wait(timeout=graceSeconds)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=graceSeconds)
        if self._jobHandle:
            ctypes.windll.kernel32.CloseHandle(self._jobHandle)
            self._jobHandle = None
        self.process = None


class JsonRpcChannel:
    """한 번에 하나의 요청을 보장하는 JSON-RPC 2.0 채널."""

    def __init__(self, supervisor: ProcessSupervisor):
        self.supervisor = supervisor
        self._requestId = 0
        self._pending: deque[dict[str, Any]] = deque()
        self._lock = threading.Lock()

    def request(self, method: str, params: dict[str, Any], *, timeout: float = 30.0) -> dict[str, Any]:
        """Sig: request(method, params, *, timeout=30.0) -> dict[str, Any].

        Args: JSON-RPC method, params, timeout이다.
        Returns: response result dict다.
        Raises: RuntimeError for JSON-RPC error; TimeoutError on deadline.
        Example: `channel.request("initialize", {})`.
        """
        with self._lock:
            self._requestId += 1
            requestId = self._requestId
            self.supervisor.sendJson({"jsonrpc": "2.0", "id": requestId, "method": method, "params": params})
            deadline = time.monotonic() + timeout
            while True:
                message = self.supervisor.readJson(timeout=max(0.01, deadline - time.monotonic()))
                if message.get("id") != requestId:
                    self._pending.append(message)
                    continue
                if "error" in message:
                    raise RuntimeError(f"{method} failed: {message['error']}")
                result = message.get("result")
                return result if isinstance(result, dict) else {"value": result}

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Sig: notify(method, params=None) -> None.

        Args: method와 선택적 params다.
        Returns: None.
        Example: `channel.notify("initialized")`.
        """
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self.supervisor.sendJson(message)

    def nextMessage(self, *, timeout: float = 30.0) -> dict[str, Any]:
        """Sig: nextMessage(*, timeout=30.0) -> dict[str, Any].

        Args: timeout은 대기 초다.
        Returns: pending 또는 새 메시지다.
        Raises: transport errors from ProcessSupervisor.
        Example: `notification = channel.nextMessage()`.
        """
        if self._pending:
            return self._pending.popleft()
        return self.supervisor.readJson(timeout=timeout)

    def respond(self, requestId: int | str, result: dict[str, Any]) -> None:
        """Sig: respond(requestId, result) -> None.

        Args: 서버 요청 ID와 응답 result다.
        Returns: None.
        Example: `channel.respond(message["id"], {"outcome": "cancelled"})`.
        """
        self.supervisor.sendJson({"jsonrpc": "2.0", "id": requestId, "result": result})


def _attachWindowsJob(process: subprocess.Popen[bytes]) -> int | None:
    """Sig: _attachWindowsJob(process) -> int | None.

    Args: 막 시작한 Windows 자식 프로세스다.
    Returns: kill-on-close Job Object handle 또는 None이다.
    Example: Windows start 경계에서만 호출한다.
    """
    if os.name != "nt":
        return None

    class BasicLimitInformation(ctypes.Structure):
        """Windows Job Object 기본 제한 구조체다."""

        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class IoCounters(ctypes.Structure):
        """Windows Job Object I/O 누계 구조체다."""

        _fields_ = [
            (name, ctypes.c_uint64)
            for name in (
                "ReadOperationCount",
                "WriteOperationCount",
                "OtherOperationCount",
                "ReadTransferCount",
                "WriteTransferCount",
                "OtherTransferCount",
            )
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        """kill-on-close 플래그를 전달하는 확장 제한 구조체다."""

        _fields_ = [
            ("BasicLimitInformation", BasicLimitInformation),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel = ctypes.windll.kernel32
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        return None
    info = ExtendedLimitInformation()
    info.BasicLimitInformation.LimitFlags = 0x00002000
    configured = kernel.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info))
    assigned = configured and kernel.AssignProcessToJobObject(handle, int(process._handle))
    if not assigned:
        kernel.CloseHandle(handle)
        return None
    return int(handle)
