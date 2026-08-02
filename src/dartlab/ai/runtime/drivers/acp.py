"""Agent Client Protocol v1 stdio 드라이버."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..contracts import AgentEvent, ProcessSpec, RuntimeDescriptor
from ..eventProjection import EventProjector
from ..mcpBootstrap import embeddedMcpServerSpec
from ..processSupervisor import JsonRpcChannel, ProcessSupervisor
from .base import DriverHandle, runtimeLaunchArgv


class AcpDriver:
    """ACP v1 세션과 양방향 권한 요청을 DartLab 이벤트로 연결한다."""

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

        Args: 런타임 설명, 실행 파일, DartLab 세션 ID, 작업공간이다.
        Returns: initialize와 session/new가 끝난 ACP handle이다.
        Raises: transport or JSON-RPC errors on handshake failure.
        Example: 엔진의 `openSession`에서 호출한다.
        """
        supervisor = ProcessSupervisor(ProcessSpec(runtimeLaunchArgv(descriptor, executable), cwd))
        supervisor.start()
        try:
            channel = JsonRpcChannel(supervisor)
            channel.request(
                "initialize",
                {
                    "protocolVersion": 1,
                    "clientCapabilities": {"fs": {"readTextFile": False, "writeTextFile": False}},
                    "clientInfo": {"name": "dartlab", "version": "1"},
                },
                timeout=20,
            )
            sessionParams = {
                "cwd": str(cwd.resolve()),
                "mcpServers": [embeddedMcpServerSpec()],
            }
            if nativeSessionId:
                result = channel.request(
                    "session/load",
                    {**sessionParams, "sessionId": nativeSessionId},
                    timeout=30,
                )
            else:
                result = channel.request("session/new", sessionParams, timeout=30)
        except Exception:
            supervisor.stop()
            raise
        resolvedNativeId = str(result.get("sessionId") or nativeSessionId or "")
        if not resolvedNativeId:
            supervisor.stop()
            raise RuntimeError("ACP session/new가 sessionId를 반환하지 않았습니다")
        return DriverHandle(
            descriptor=descriptor,
            executable=executable,
            sessionId=sessionId,
            nativeSessionId=resolvedNativeId,
            cwd=cwd,
            projector=EventProjector(descriptor.runtimeId, sessionId),
            supervisor=supervisor,
            channel=channel,
            metadata={"requestId": 1000},
        )

    def streamTurn(self, handle: DriverHandle, question: str, *, instructions: str) -> Iterator[AgentEvent]:
        """Sig: streamTurn(handle, question, *, instructions) -> Iterator[AgentEvent].

        Args: 열린 ACP handle, 질문, 분석 캡슐이다.
        Returns: session/update와 최종 응답을 투영한 iterator다.
        Raises: RuntimeError if another turn is active or channel is closed.
        Example: `driver.streamTurn(handle, "질문", instructions=capsule)`.
        """
        if handle.activeTurnId is not None or handle.channel is None or handle.supervisor is None:
            raise RuntimeError("세션에 이미 활성 턴이 있거나 채널이 닫혔습니다")
        turnId = uuid.uuid4().hex
        handle.activeTurnId = turnId
        requestId = int(handle.metadata.get("requestId") or 1000) + 1
        handle.metadata["requestId"] = requestId
        prompt = f"{instructions}\n\n사용자 요청:\n{question}"
        handle.supervisor.sendJson(
            {
                "jsonrpc": "2.0",
                "id": requestId,
                "method": "session/prompt",
                "params": {
                    "sessionId": handle.nativeSessionId,
                    "prompt": [{"type": "text", "text": prompt}],
                },
            }
        )
        yield handle.projector.event("turnStarted", turnId=turnId)
        try:
            while True:
                message = handle.channel.nextMessage(timeout=300)
                nativeType = str(message.get("method") or message.get("type") or "native")
                if "id" in message and nativeType in {"session/request_permission", "session/requestPermission"}:
                    approvalId = str(message["id"])
                    handle.pendingApprovals[approvalId] = (message["id"], nativeType)
                    handle.metadata.setdefault("approvalParams", {})[approvalId] = message.get("params") or {}
                for event in handle.projector.project(message, turnId=turnId):
                    if event.kind == "approvalRequested":
                        yield handle.projector.event(
                            "approvalRequested",
                            turnId=turnId,
                            payload={**event.payload, "approvalId": str(message.get("id"))},
                            nativeType=event.nativeType,
                        )
                    else:
                        yield event
                if message.get("id") == requestId:
                    if "error" in message:
                        yield handle.projector.event(
                            "runtimeError", turnId=turnId, payload={"error": str(message["error"])}
                        )
                    else:
                        result = message.get("result") if isinstance(message.get("result"), dict) else {}
                        yield handle.projector.event("turnCompleted", turnId=turnId, payload=result)
                    return
        finally:
            handle.activeTurnId = None

    def cancel(self, handle: DriverHandle) -> None:
        """Sig: cancel(handle) -> None.

        Args: 활성 세션 handle이다.
        Returns: None.
        Example: `driver.cancel(handle)`.
        """
        if handle.channel and handle.activeTurnId:
            handle.channel.notify("session/cancel", {"sessionId": handle.nativeSessionId})

    def approve(self, handle: DriverHandle, approvalId: str, *, allow: bool) -> None:
        """Sig: approve(handle, approvalId, *, allow) -> None.

        Args: handle, pending approval ID, 허용 여부다.
        Returns: None.
        Raises: KeyError if approval does not exist.
        Example: `driver.approve(handle, approvalId, allow=True)`.
        """
        requestId, _ = handle.pendingApprovals.pop(approvalId)
        if handle.channel is None:
            raise RuntimeError("runtime channel is closed")
        params = handle.metadata.get("approvalParams", {}).pop(approvalId, {})
        options = params.get("options") if isinstance(params, dict) else []
        optionId = None
        if allow:
            for option in options or []:
                if isinstance(option, dict) and option.get("optionId"):
                    optionId = str(option["optionId"])
                    break
        outcome = {"outcome": "selected", "optionId": optionId} if optionId else {"outcome": "cancelled"}
        handle.channel.respond(requestId, {"outcome": outcome})

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

        Args: ACP handle이다.
        Returns: 빈 목록이다. 모델 선택은 agent가 소유한다.
        Example: `driver.models(handle) == []`.
        """
        return []
