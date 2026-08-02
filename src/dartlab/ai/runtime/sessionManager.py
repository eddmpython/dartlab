"""열린 에이전트 세션과 이벤트 재생을 관리한다."""

from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from .drivers.base import AgentRuntimeDriver, DriverHandle
from .eventBuffer import EventBuffer


@dataclass
class ManagedSession:
    """driver handle과 replay buffer를 한 생명주기로 묶는다."""

    driver: AgentRuntimeDriver
    handle: DriverHandle
    buffer: EventBuffer


class SessionManager:
    """최대 네 개의 hot session을 LRU로 유지한다."""

    def __init__(self, maxHotSessions: int = 4):
        self.maxHotSessions = maxHotSessions
        self._sessions: OrderedDict[str, ManagedSession] = OrderedDict()
        self._lock = threading.RLock()

    def put(self, sessionId: str, managed: ManagedSession) -> ManagedSession:
        """Sig: put(sessionId, managed) -> ManagedSession.

        Args: 세션 ID와 열린 관리 객체다.
        Returns: 입력 managed다.
        Example: `manager.put("s", managed)`.
        """
        with self._lock:
            old = self._sessions.pop(sessionId, None)
            if old:
                old.driver.close(old.handle)
            self._sessions[sessionId] = managed
            while len(self._sessions) > self.maxHotSessions:
                _, evicted = self._sessions.popitem(last=False)
                evicted.driver.close(evicted.handle)
        return managed

    def get(self, sessionId: str) -> ManagedSession | None:
        """Sig: get(sessionId) -> ManagedSession | None.

        Args: sessionId는 조회할 DartLab 세션이다.
        Returns: 열린 managed session 또는 None이다.
        Example: `managed = manager.get("s")`.
        """
        with self._lock:
            managed = self._sessions.pop(sessionId, None)
            if managed:
                self._sessions[sessionId] = managed
            return managed

    def close(self, sessionId: str) -> None:
        """Sig: close(sessionId) -> None.

        Args: 닫을 sessionId다.
        Returns: None.
        Example: `manager.close("s")`.
        """
        with self._lock:
            managed = self._sessions.pop(sessionId, None)
        if managed:
            managed.driver.close(managed.handle)

    def closeAll(self) -> None:
        """Sig: closeAll() -> None.

        Args: 없음.
        Returns: None.
        Example: 서버 lifespan 종료에서 `manager.closeAll()`을 호출한다.
        """
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for managed in sessions:
            managed.driver.close(managed.handle)

    def status(self) -> list[dict[str, Any]]:
        """Sig: status() -> list[dict[str, Any]].

        Args: 없음.
        Returns: hot session의 공개 상태다.
        Example: `active = manager.status()`.
        """
        with self._lock:
            return [
                {
                    "sessionId": sessionId,
                    "runtimeId": managed.handle.descriptor.runtimeId,
                    "activeTurnId": managed.handle.activeTurnId,
                    "pendingApprovals": list(managed.handle.pendingApprovals),
                }
                for sessionId, managed in self._sessions.items()
            ]
