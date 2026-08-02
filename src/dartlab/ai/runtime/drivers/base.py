"""에이전트 런타임 드라이버 공통 계약."""

from __future__ import annotations

import math
import os
import shutil
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..contracts import AgentEvent, RuntimeDescriptor
from ..eventProjection import EventProjector
from ..processSupervisor import JsonRpcChannel, ProcessSupervisor

_DEFAULT_TURN_TIMEOUT_SECONDS = 300.0
_MIN_TURN_TIMEOUT_SECONDS = 30.0
_MAX_TURN_TIMEOUT_SECONDS = 900.0


def runtimeTurnTimeoutSeconds() -> float:
    """환경 설정을 안전한 범위로 제한한 한 턴의 총 실행 시간이다."""
    raw = os.environ.get("DARTLAB_AGENT_TURN_TIMEOUT_SECONDS")
    if raw is None:
        return _DEFAULT_TURN_TIMEOUT_SECONDS
    try:
        configured = float(raw)
    except ValueError:
        return _DEFAULT_TURN_TIMEOUT_SECONDS
    if not math.isfinite(configured) or configured <= 0:
        return _DEFAULT_TURN_TIMEOUT_SECONDS
    return min(max(configured, _MIN_TURN_TIMEOUT_SECONDS), _MAX_TURN_TIMEOUT_SECONDS)


def remainingTurnSeconds(deadline: float, timeoutSeconds: float) -> float:
    """프레임마다 갱신되지 않는 총 턴 deadline의 남은 시간을 반환한다."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError(f"에이전트 턴이 {timeoutSeconds:g}초 제한을 초과했습니다")
    return max(0.01, remaining)


def runtimeLaunchArgv(descriptor: RuntimeDescriptor, executable: str) -> tuple[str, ...]:
    """Windows npm shim을 거치지 않는 매니페스트 선언형 실행 argv를 만든다."""
    return (*runtimeExecutableArgv(descriptor, executable), *descriptor.launchArgs)


def runtimeExecutableArgv(descriptor: RuntimeDescriptor, executable: str) -> tuple[str, ...]:
    """서브커맨드를 붙일 수 있는 런타임 실행 prefix만 반환한다."""
    if os.name != "nt" or not descriptor.windowsLaunch:
        return (executable,)

    shimDir = Path(executable).resolve().parent
    prefix: list[str] = []
    for token in descriptor.windowsLaunch:
        if token == "node":
            node = shutil.which("node")
            if node is None:
                raise FileNotFoundError("Windows 런타임 실행에 필요한 node를 찾을 수 없습니다")
            prefix.append(node)
            continue
        if "{shimDir}" not in token:
            raise ValueError(f"허용되지 않은 windowsLaunch 토큰: {token}")
        target = Path(token.replace("{shimDir}", str(shimDir))).resolve()
        try:
            target.relative_to(shimDir)
        except ValueError as exc:
            raise ValueError("windowsLaunch 경로가 npm shim 디렉터리를 벗어났습니다") from exc
        if not target.is_file():
            raise FileNotFoundError(f"Windows 런타임 실행 파일을 찾을 수 없습니다: {target}")
        prefix.append(str(target))
    return tuple(prefix)


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
        instructions: str = "",
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
