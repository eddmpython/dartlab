"""에이전트 런타임 드라이버 공통 계약."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..contracts import AgentEvent, RuntimeDescriptor
from ..eventProjection import EventProjector
from ..processSupervisor import JsonRpcChannel, ProcessSupervisor


@dataclass
class DriverHandle:
    """열린 네이티브 세션의 프로세스 상태."""

    descriptor: RuntimeDescriptor
    executable: str
    sessionId: str
    nativeSessionId: str
    cwd: Path
    projector: EventProjector
    supervisor: ProcessSupervisor | None = None
    channel: JsonRpcChannel | None = None
    activeTurnId: str | None = None
    pendingApprovals: dict[str, tuple[int | str, str]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentRuntimeDriver(Protocol):
    """세 드라이버가 구현하는 최소 생명주기."""

    def open(
        self,
        descriptor: RuntimeDescriptor,
        executable: str,
        sessionId: str,
        cwd: Path,
        nativeSessionId: str | None = None,
    ) -> DriverHandle:
        """네이티브 런타임 세션을 열거나 저장된 세션을 재개한다."""
        ...

    def streamTurn(self, handle: DriverHandle, question: str, *, instructions: str) -> Iterator[AgentEvent]:
        """한 질문의 네이티브 이벤트를 표준 AgentEvent로 스트리밍한다."""
        ...

    def cancel(self, handle: DriverHandle) -> None:
        """현재 활성 턴을 네이티브 프로토콜로 취소한다."""
        ...

    def approve(self, handle: DriverHandle, approvalId: str, *, allow: bool) -> None:
        """대기 중인 네이티브 권한 요청에 사용자 결정을 전달한다."""
        ...

    def close(self, handle: DriverHandle) -> None:
        """세션 프로세스와 전송 채널을 닫는다."""
        ...

    def models(self, handle: DriverHandle) -> list[dict[str, Any]]:
        """런타임이 공개하는 네이티브 모델 카탈로그를 반환한다."""
        ...
