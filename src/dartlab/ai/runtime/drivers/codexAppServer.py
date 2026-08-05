"""Codex app-server JSON-RPC 드라이버."""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from typing import Any

from ..contracts import AgentEvent, ProcessSpec, RuntimeDescriptor
from ..eventProjection import EventProjector
from ..processSupervisor import JsonRpcChannel, ProcessSupervisor
from .base import DriverHandle, remainingTurnSeconds, runtimeLaunchArgv, runtimeTurnTimeoutSeconds

_DEFAULT_CODEX_REASONING_EFFORT = "high"
_CODEX_REASONING_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max", "ultra"})


def codexReasoningEffort() -> str:
    """DartLab 분석 턴의 품질·지연 균형을 위한 Codex reasoning effort다."""
    configured = os.environ.get("DARTLAB_CODEX_REASONING_EFFORT", _DEFAULT_CODEX_REASONING_EFFORT).strip().casefold()
    return configured if configured in _CODEX_REASONING_EFFORTS else _DEFAULT_CODEX_REASONING_EFFORT


class CodexAppServerDriver:
    """Codex 네이티브 thread와 turn을 DartLab 세션으로 연결한다."""

    def open(
        self,
        descriptor: RuntimeDescriptor,
        executable: str,
        sessionId: str,
        cwd: Path,
        nativeSessionId: str | None = None,
        instructions: str = "",
    ) -> DriverHandle:
        """Sig: open(descriptor, executable, sessionId, cwd, nativeSessionId=None) -> DriverHandle.

        Args: 런타임 설명, 실행 경로, DartLab 세션 ID, 작업공간이다.
        Returns: 초기화된 app-server thread handle이다.
        Raises: transport or JSON-RPC errors when initialization fails.
        Example: 엔진의 `openSession`에서 호출한다.
        """
        supervisor = ProcessSupervisor(ProcessSpec(runtimeLaunchArgv(descriptor, executable), cwd))
        supervisor.start()
        try:
            channel = JsonRpcChannel(supervisor)
            channel.request(
                "initialize",
                {"clientInfo": {"name": "dartlab", "version": "1"}, "capabilities": {}},
                timeout=15,
            )
            channel.notify("initialized", {})
            threadParams = {
                "cwd": str(cwd.resolve()),
                "approvalPolicy": "never",
                "sandbox": "read-only",
                "developerInstructions": instructions,
            }
            if nativeSessionId:
                result = channel.request(
                    "thread/resume",
                    {**threadParams, "threadId": nativeSessionId},
                    timeout=30,
                )
            else:
                result = channel.request(
                    "thread/start",
                    {**threadParams, "ephemeral": False},
                    timeout=30,
                )
        except Exception:
            supervisor.stop()
            raise
        thread = result.get("thread") if isinstance(result.get("thread"), dict) else {}
        resolvedNativeId = str(thread.get("id") or result.get("threadId") or nativeSessionId or "")
        if not resolvedNativeId:
            supervisor.stop()
            raise RuntimeError("Codex thread/start가 thread ID를 반환하지 않았습니다")
        return DriverHandle(
            descriptor=descriptor,
            executable=executable,
            sessionId=sessionId,
            nativeSessionId=resolvedNativeId,
            cwd=cwd,
            projector=EventProjector(descriptor.runtimeId, sessionId),
            supervisor=supervisor,
            channel=channel,
            metadata={"instructions": instructions},
        )

    def streamTurn(self, handle: DriverHandle, question: str, *, instructions: str) -> Iterator[AgentEvent]:
        """Sig: streamTurn(handle, question, *, instructions) -> Iterator[AgentEvent].

        Args: 열린 handle, 사용자 질문, 분석 캡슐이다.
        Returns: 턴 완료까지 실시간 정규 이벤트를 내는 iterator다.
        Raises: RuntimeError if another turn is active or transport fails.
        Example: `events = driver.streamTurn(handle, "질문", instructions=capsule)`.

        Codex 는 형제 런타임의 턴별 system prompt 에 해당하는 표면이 없고 캡슐을
        thread 수명 동안 `developerInstructions` 로 들고 있다. 그래서 보통은 다시 보낼
        것이 없지만, 캡슐이 실제로 달라졌는데 조용히 버리면 턴이 옛 지침으로 돈다.
        달라진 경우에만 데이터 블록으로 앞에 붙인다.
        """
        if handle.activeTurnId is not None or handle.channel is None:
            raise RuntimeError("세션에 이미 활성 턴이 있거나 채널이 닫혔습니다")
        timeoutSeconds = runtimeTurnTimeoutSeconds()
        deadline = time.monotonic() + timeoutSeconds
        turnInput = [{"type": "text", "text": question}]
        if instructions and instructions != handle.metadata.get("instructions"):
            handle.metadata["instructions"] = instructions
            turnInput.insert(0, {"type": "text", "text": f"[DartLab 런타임 지침 갱신]\n{instructions}"})
        result = handle.channel.request(
            "turn/start",
            {
                "threadId": handle.nativeSessionId,
                "input": turnInput,
                "effort": codexReasoningEffort(),
                "approvalPolicy": "never",
                "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
            },
            timeout=min(30.0, remainingTurnSeconds(deadline, timeoutSeconds)),
        )
        turn = result.get("turn") if isinstance(result.get("turn"), dict) else {}
        turnId = str(turn.get("id") or result.get("turnId") or uuid.uuid4().hex)
        handle.activeTurnId = turnId
        completed = False
        try:
            while True:
                try:
                    message = handle.channel.nextMessage(timeout=remainingTurnSeconds(deadline, timeoutSeconds))
                except TimeoutError as exc:
                    raise TimeoutError(f"에이전트 턴이 {timeoutSeconds:g}초 제한을 초과했습니다") from exc
                nativeType = str(message.get("method") or message.get("type") or "native")
                if "id" in message and nativeType.endswith("/requestApproval"):
                    approvalId = str(message.get("id"))
                    handle.pendingApprovals[approvalId] = (message["id"], nativeType)
                for event in handle.projector.project(message, turnId=turnId):
                    if event.kind == "approvalRequested" and "approvalId" not in event.payload:
                        payload = {**event.payload, "approvalId": str(message.get("id"))}
                        event = handle.projector.event(
                            "approvalRequested", turnId=turnId, payload=payload, nativeType=event.nativeType
                        )
                    yield event
                if nativeType == "turn/completed":
                    completed = True
                    return
        finally:
            if not completed and handle.activeTurnId:
                with suppress(Exception):
                    self.cancel(handle)
            handle.activeTurnId = None

    def cancel(self, handle: DriverHandle) -> None:
        """Sig: cancel(handle) -> None.

        Args: 활성 턴을 가진 handle이다.
        Returns: None.
        Example: `driver.cancel(handle)`.
        """
        if handle.channel and handle.activeTurnId:
            handle.channel.startRequest(
                "turn/interrupt",
                {"threadId": handle.nativeSessionId, "turnId": handle.activeTurnId},
            )

    def approve(self, handle: DriverHandle, approvalId: str, *, allow: bool) -> None:
        """Sig: approve(handle, approvalId, *, allow) -> None.

        Args: handle, 공개 approval ID, 허용 여부다.
        Returns: None.
        Raises: KeyError if approvalId is not pending.
        Example: `driver.approve(handle, approvalId, allow=False)`.
        """
        requestId, nativeType = handle.pendingApprovals.pop(approvalId)
        if handle.channel is None:
            raise RuntimeError("runtime channel is closed")
        if "commandExecution" in nativeType:
            decision = "accept" if allow else "decline"
        else:
            decision = "accept" if allow else "decline"
        handle.channel.respond(requestId, {"decision": decision})

    def close(self, handle: DriverHandle) -> None:
        """Sig: close(handle) -> None.

        Args: 닫을 handle이다.
        Returns: None.
        Example: `driver.close(handle)`.
        """
        if handle.supervisor:
            handle.supervisor.stop()
        handle.supervisor = None
        handle.channel = None

    def models(self, handle: DriverHandle) -> list[dict[str, Any]]:
        """Sig: models(handle) -> list[dict[str, Any]].

        Args: 열린 Codex handle이다.
        Returns: CLI가 보고한 모델 메타 목록이다.
        Raises: RuntimeError if channel is closed.
        Example: `models = driver.models(handle)`.
        """
        if handle.channel is None:
            raise RuntimeError("runtime channel is closed")
        if handle.activeTurnId is not None:
            raise RuntimeError("활성 턴 중에는 model catalog를 조회할 수 없습니다")
        result = handle.channel.request("model/list", {}, timeout=20)
        return [item for item in result.get("data") or [] if isinstance(item, dict)]
