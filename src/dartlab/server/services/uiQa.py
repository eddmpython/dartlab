"""로컬 UI 검수를 위한 메모리 전용 세션·명령 브로커."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from time import monotonic
from typing import Any

SESSION_TTL_SECONDS = 60.0
COMMAND_LEASE_SECONDS = 5.0
MAX_SESSIONS = 20
MAX_COMMANDS_PER_SESSION = 100

ALLOWED_ACTIONS = frozenset({"click", "fill", "key", "navigate", "scroll", "snapshot"})
ALLOWED_KEYS = frozenset({"Enter", "Escape", "Tab", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"})


def _utcNow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class _Command:
    commandId: str
    action: str
    targetQaId: str | None
    value: str | None
    key: str | None
    path: str | None
    behavior: str | None
    block: str | None
    status: str = "pending"
    createdAt: str = field(default_factory=_utcNow)
    deliveredAt: str | None = None
    deliveryMonotonic: float | None = None
    completedAt: str | None = None
    ok: bool | None = None
    message: str | None = None
    detail: dict[str, Any] | None = None

    def toDict(self) -> dict[str, Any]:
        """검수 명령의 실행 상태와 결과를 격리된 공개 사전으로 반환한다."""
        return {
            "commandId": self.commandId,
            "action": self.action,
            "targetQaId": self.targetQaId,
            "value": self.value,
            "key": self.key,
            "path": self.path,
            "behavior": self.behavior,
            "block": self.block,
            "status": self.status,
            "createdAt": self.createdAt,
            "deliveredAt": self.deliveredAt,
            "completedAt": self.completedAt,
            "ok": self.ok,
            "message": self.message,
            "detail": deepcopy(self.detail),
        }


@dataclass
class _Session:
    sessionId: str
    clientName: str
    capabilities: list[str]
    connectedAt: str = field(default_factory=_utcNow)
    lastSeenAt: str = field(default_factory=_utcNow)
    lastSeenMonotonic: float = field(default_factory=monotonic)
    snapshot: dict[str, Any] | None = None
    commands: list[_Command] = field(default_factory=list)
    visualAudits: list[dict[str, Any]] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        """검수 세션의 연결 상태와 대기 작업 수를 요약한다."""
        pending = sum(command.status in {"pending", "delivered"} for command in self.commands)
        return {
            "sessionId": self.sessionId,
            "clientName": self.clientName,
            "capabilities": list(self.capabilities),
            "connectedAt": self.connectedAt,
            "lastSeenAt": self.lastSeenAt,
            "route": (self.snapshot or {}).get("route"),
            "title": (self.snapshot or {}).get("title"),
            "pendingCommands": pending,
            "visualAuditCount": len(self.visualAudits),
        }


class UiQaBroker:
    """브라우저 검수 브리지와 에이전트 API 사이의 bounded in-memory broker."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[str, _Session] = {}

    def reset(self) -> None:
        """테스트와 서버 수명주기 정리를 위한 전체 메모리 초기화."""
        with self._lock:
            self._sessions.clear()

    def _cleanup(self) -> None:
        cutoff = monotonic() - SESSION_TTL_SECONDS
        expired = [key for key, value in self._sessions.items() if value.lastSeenMonotonic < cutoff]
        for key in expired:
            del self._sessions[key]

    def _session(self, sessionId: str) -> _Session:
        self._cleanup()
        try:
            return self._sessions[sessionId]
        except KeyError as exc:
            raise KeyError("UI 검수 세션을 찾을 수 없습니다") from exc

    @staticmethod
    def _touch(session: _Session) -> None:
        session.lastSeenAt = _utcNow()
        session.lastSeenMonotonic = monotonic()

    def register(self, sessionId: str, clientName: str, capabilities: list[str]) -> dict[str, Any]:
        """브라우저 검수 세션을 등록하거나 기존 세션 정보를 갱신한다."""
        with self._lock:
            self._cleanup()
            if sessionId not in self._sessions and len(self._sessions) >= MAX_SESSIONS:
                oldest = min(self._sessions.values(), key=lambda item: item.lastSeenMonotonic)
                del self._sessions[oldest.sessionId]
            existing = self._sessions.get(sessionId)
            if existing is None:
                existing = _Session(sessionId, clientName, list(capabilities))
                self._sessions[sessionId] = existing
            else:
                existing.clientName = clientName
                existing.capabilities = list(capabilities)
                self._touch(existing)
            return existing.summary()

    def updateSnapshot(self, sessionId: str, snapshot: dict[str, Any]) -> dict[str, Any]:
        """세션의 최신 화면 스냅숏을 복사해 저장하고 접속 시각을 갱신한다."""
        with self._lock:
            session = self._session(sessionId)
            session.snapshot = deepcopy(snapshot)
            self._touch(session)
            return session.summary()

    def listSessions(self) -> list[dict[str, Any]]:
        """만료 세션을 정리한 뒤 최근 활동 순으로 세션 요약을 반환한다."""
        with self._lock:
            self._cleanup()
            sessions = sorted(self._sessions.values(), key=lambda item: item.lastSeenMonotonic, reverse=True)
            return [session.summary() for session in sessions]

    def getSession(self, sessionId: str) -> dict[str, Any]:
        """세션 요약과 최근 스냅숏, 명령, 시각 검수 기록을 반환한다."""
        with self._lock:
            session = self._session(sessionId)
            return {
                **session.summary(),
                "snapshot": deepcopy(session.snapshot),
                "commands": [command.toDict() for command in session.commands[-20:]],
                "visualAudits": deepcopy(session.visualAudits[-20:]),
            }

    def deleteSession(self, sessionId: str) -> None:
        """지정한 UI 검수 세션과 메모리 내 기록을 제거한다."""
        with self._lock:
            if self._sessions.pop(sessionId, None) is None:
                raise KeyError("UI 검수 세션을 찾을 수 없습니다")

    def enqueue(self, sessionId: str, command: dict[str, Any]) -> dict[str, Any]:
        """검수 명령을 세션 대기열에 추가하고 공개 표현을 반환한다."""
        with self._lock:
            session = self._session(sessionId)
            item = _Command(**command)
            session.commands.append(item)
            if len(session.commands) > MAX_COMMANDS_PER_SESSION:
                session.commands = session.commands[-MAX_COMMANDS_PER_SESSION:]
            return item.toDict()

    def nextCommand(self, sessionId: str) -> dict[str, Any] | None:
        """대기 중이거나 임대가 만료된 다음 검수 명령을 전달한다."""
        with self._lock:
            session = self._session(sessionId)
            self._touch(session)
            now = monotonic()
            for command in session.commands:
                leaseExpired = (
                    command.status == "delivered"
                    and command.deliveryMonotonic is not None
                    and now - command.deliveryMonotonic >= COMMAND_LEASE_SECONDS
                )
                if command.status == "pending" or leaseExpired:
                    command.status = "delivered"
                    command.deliveredAt = _utcNow()
                    command.deliveryMonotonic = now
                    return command.toDict()
            return None

    def completeCommand(
        self,
        sessionId: str,
        commandId: str,
        *,
        ok: bool,
        message: str | None,
        detail: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """전달된 검수 명령의 성공 여부와 실행 결과를 기록한다."""
        with self._lock:
            session = self._session(sessionId)
            self._touch(session)
            for command in session.commands:
                if command.commandId == commandId:
                    command.status = "succeeded" if ok else "failed"
                    command.ok = ok
                    command.message = message
                    command.detail = deepcopy(detail)
                    command.completedAt = _utcNow()
                    return command.toDict()
            raise KeyError("UI 검수 명령을 찾을 수 없습니다")

    def getCommand(self, sessionId: str, commandId: str) -> dict[str, Any]:
        """세션에서 지정한 검수 명령의 현재 상태를 조회한다."""
        with self._lock:
            session = self._session(sessionId)
            for command in session.commands:
                if command.commandId == commandId:
                    return command.toDict()
            raise KeyError("UI 검수 명령을 찾을 수 없습니다")

    def recordVisualAudit(self, sessionId: str, audit: dict[str, Any]) -> dict[str, Any]:
        """시나리오별 시각 검수 결과를 세션의 제한된 이력에 저장한다."""
        with self._lock:
            session = self._session(sessionId)
            self._touch(session)
            item = {**deepcopy(audit), "recordedAt": _utcNow()}
            session.visualAudits.append(item)
            session.visualAudits = session.visualAudits[-50:]
            return deepcopy(item)


uiQaBroker = UiQaBroker()
