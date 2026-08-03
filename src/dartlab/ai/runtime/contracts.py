"""로컬 에이전트 런타임의 안정 계약."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

EventKind = Literal[
    "sessionStarted",
    "sessionResumed",
    "turnStarted",
    "messageDelta",
    "reasoningDelta",
    "toolStarted",
    "toolCompleted",
    "approvalRequested",
    "artifactProduced",
    "turnCompleted",
    "runtimeError",
    "eventGap",
    "native",
]

RuntimeState = Literal["ready", "missing", "unavailable", "authRequired", "unknown"]

PUBLIC_AGENT_EVENT_KINDS = (
    "TEXT_MESSAGE_START",
    "TEXT_MESSAGE_CONTENT",
    "TEXT_MESSAGE_END",
    "THINKING_DELTA",
    "TOOL_CALL_START",
    "TOOL_CALL_ARGS",
    "TOOL_CALL_END",
    "TOOL_CALL_RESULT",
    "STATE_SNAPSHOT",
    "STATE_DELTA",
    "MESSAGES_SNAPSHOT",
    "ACTIVITY_SNAPSHOT",
    "ACTIVITY_DELTA",
    "VIEW_SPEC",
    "APPROVAL_REQUESTED",
    "RUN_FINISHED",
    "RUN_ERROR",
)


def nowIso() -> str:
    """Sig: nowIso() -> str.

    Args: 없음.
    Returns: UTC ISO 8601 문자열이다.
    Example: `timestamp = nowIso()`.
    """
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RuntimeDescriptor:
    """매니페스트에서 읽은 설치형 런타임 설명."""

    runtimeId: str
    displayName: str
    driver: str
    protocol: str
    executableCandidates: tuple[str, ...]
    versionArgs: tuple[str, ...]
    launchArgs: tuple[str, ...]
    installArgs: tuple[str, ...]
    officialUrl: str
    windowsLaunch: tuple[str, ...] = ()
    embeddedGrounding: bool = True
    authProbeArgs: tuple[str, ...] = ()
    authSuccessPattern: str | None = None
    loginArgs: tuple[str, ...] = ()

    def toDict(self) -> dict[str, Any]:
        """Sig: toDict() -> dict[str, Any].

        Args: 없음.
        Returns: JSON 직렬화 가능한 런타임 설명이다.
        Example: `descriptor.toDict()["runtimeId"]`.
        """
        return asdict(self)


@dataclass(frozen=True)
class RuntimeProbe:
    """한 런타임의 발견 및 버전 점검 결과."""

    runtimeId: str
    state: RuntimeState
    executable: str | None = None
    version: str | None = None
    checkedAt: str = field(default_factory=nowIso)
    detail: str | None = None

    def toDict(self) -> dict[str, Any]:
        """Sig: toDict() -> dict[str, Any].

        Args: 없음.
        Returns: 공개 가능한 probe 정보다.
        Example: `probe.toDict()["state"]`.
        """
        return asdict(self)


@dataclass(frozen=True)
class RuntimeSession:
    """DartLab 세션과 CLI 네이티브 세션의 매핑."""

    sessionId: str
    runtimeId: str
    nativeSessionId: str
    cwd: str
    createdAt: str = field(default_factory=nowIso)
    updatedAt: str = field(default_factory=nowIso)

    def toDict(self) -> dict[str, str]:
        """Sig: toDict() -> dict[str, str].

        Args: 없음.
        Returns: 세션 매핑의 공개 필드다.
        Example: `session.toDict()["runtimeId"]`.
        """
        return asdict(self)


@dataclass(frozen=True)
class AgentEvent:
    """드라이버별 이벤트를 정규화한 단일 이벤트 봉투."""

    schemaVersion: str
    sessionId: str
    turnId: str
    eventId: str
    sequence: int
    runtimeId: str
    kind: EventKind
    timestamp: str
    payload: dict[str, Any] = field(default_factory=dict)
    nativeType: str | None = None

    def toDict(self) -> dict[str, Any]:
        """Sig: toDict() -> dict[str, Any].

        Args: 없음.
        Returns: 서버와 UI가 공유하는 이벤트 봉투다.
        Example: `event.toDict()["kind"]`.
        """
        return asdict(self)


@dataclass(frozen=True)
class ProcessSpec:
    """shell 문자열 없이 자식 프로세스를 시작하는 명세."""

    argv: tuple[str, ...]
    cwd: Path
    env: dict[str, str] = field(default_factory=dict)
    maxFrameBytes: int = 1024 * 1024
    outputLimitBytes: int = 256 * 1024
