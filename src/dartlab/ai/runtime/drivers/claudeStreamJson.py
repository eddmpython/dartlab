"""Claude Code stream-json 드라이버."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..contracts import AgentEvent, ProcessSpec, RuntimeDescriptor
from ..eventProjection import EventProjector
from ..mcpBootstrap import claudeReadOnlyMcpTools
from ..processSupervisor import ProcessClosedError, ProcessSupervisor
from .base import DriverHandle


class ClaudeStreamJsonDriver:
    """Claude CLI가 소유한 세션을 턴별 stream-json 프로세스로 연결한다."""

    def open(
        self,
        descriptor: RuntimeDescriptor,
        executable: str,
        sessionId: str,
        cwd: Path,
        nativeSessionId: str | None = None,
    ) -> DriverHandle:
        """Sig: open(descriptor, executable, sessionId, cwd, nativeSessionId=None) -> DriverHandle.

        Args: 런타임 설명, 실행 파일, DartLab 세션 ID, 작업공간이다.
        Returns: 아직 모델 호출을 시작하지 않은 세션 handle이다.
        Example: 엔진의 `openSession`에서 호출한다.
        """
        return DriverHandle(
            descriptor=descriptor,
            executable=executable,
            sessionId=sessionId,
            nativeSessionId=nativeSessionId or str(uuid.uuid4()),
            cwd=cwd,
            projector=EventProjector(descriptor.runtimeId, sessionId),
            metadata={"hasRun": bool(nativeSessionId)},
        )

    def streamTurn(self, handle: DriverHandle, question: str, *, instructions: str) -> Iterator[AgentEvent]:
        """Sig: streamTurn(handle, question, *, instructions) -> Iterator[AgentEvent].

        Args: handle, 질문, 분석 캡슐이다.
        Returns: stream-json을 실시간 투영하는 iterator다.
        Raises: RuntimeError if another turn is active.
        Example: `driver.streamTurn(handle, "질문", instructions=capsule)`.
        """
        if handle.activeTurnId is not None:
            raise RuntimeError("세션에 이미 활성 턴이 있습니다")
        turnId = uuid.uuid4().hex
        handle.activeTurnId = turnId
        hasRun = bool(handle.metadata.get("hasRun"))
        sessionArgs = ("--resume", handle.nativeSessionId) if hasRun else ("--session-id", handle.nativeSessionId)
        argv = (
            handle.executable,
            *handle.descriptor.launchArgs,
            "--verbose",
            "--permission-mode",
            "dontAsk",
            "--allowedTools",
            ",".join(claudeReadOnlyMcpTools()),
            "--append-system-prompt",
            instructions,
            *sessionArgs,
            question,
        )
        supervisor = ProcessSupervisor(ProcessSpec(argv, handle.cwd))
        handle.supervisor = supervisor
        supervisor.start()
        completed = False
        try:
            yield handle.projector.event("turnStarted", turnId=turnId)
            while True:
                try:
                    message = supervisor.readJson(timeout=300)
                except ProcessClosedError:
                    break
                for event in handle.projector.project(message, turnId=turnId):
                    yield event
                if message.get("type") == "result":
                    nativeId = message.get("session_id")
                    if nativeId:
                        handle.nativeSessionId = str(nativeId)
                    handle.metadata["hasRun"] = True
                    completed = True
                    break
            if not completed:
                yield handle.projector.event(
                    "runtimeError",
                    turnId=turnId,
                    payload={"error": supervisor.stderrText() or "Claude stream ended without a result"},
                )
        finally:
            supervisor.stop()
            handle.supervisor = None
            handle.activeTurnId = None

    def cancel(self, handle: DriverHandle) -> None:
        """Sig: cancel(handle) -> None.

        Args: 실행 중인 handle이다.
        Returns: None.
        Example: `driver.cancel(handle)`.
        """
        if handle.supervisor:
            handle.supervisor.stop()

    def approve(self, handle: DriverHandle, approvalId: str, *, allow: bool) -> None:
        """Sig: approve(handle, approvalId, *, allow) -> None.

        Args: handle, approvalId, 허용 여부다.
        Returns: None.
        Raises: NotImplementedError because print mode owns its permission UI.
        Example: 이 드라이버는 호출하지 않는다.
        """
        raise NotImplementedError("Claude print mode approval은 CLI permission mode가 관리합니다")

    def close(self, handle: DriverHandle) -> None:
        """Sig: close(handle) -> None.

        Args: 닫을 handle이다.
        Returns: None.
        Example: `driver.close(handle)`.
        """
        if handle.supervisor:
            handle.supervisor.stop()

    def models(self, handle: DriverHandle) -> list[dict[str, Any]]:
        """Sig: models(handle) -> list[dict[str, Any]].

        Args: Claude handle이다.
        Returns: 빈 목록이다. 모델 선택은 CLI 계정 설정이 소유한다.
        Example: `driver.models(handle) == []`.
        """
        return []
