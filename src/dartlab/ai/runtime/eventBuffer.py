"""재연결과 역압력을 위한 제한 이벤트 버퍼."""

from __future__ import annotations

import json
import threading
from collections import deque

from .contracts import AgentEvent


class EventBuffer:
    """개수와 바이트 상한을 동시에 지키는 ring buffer."""

    def __init__(self, maxEvents: int = 256, maxBytes: int = 4 * 1024 * 1024):
        self.maxEvents = maxEvents
        self.maxBytes = maxBytes
        self._events: deque[tuple[AgentEvent, int]] = deque()
        self._bytes = 0
        self._lock = threading.Lock()

    def append(self, event: AgentEvent) -> None:
        """Sig: append(event) -> None.

        Args: event는 보관할 정규 이벤트다.
        Returns: None.
        Example: `buffer.append(event)`.
        """
        size = len(json.dumps(event.toDict(), ensure_ascii=False, default=str).encode("utf-8"))
        with self._lock:
            self._events.append((event, size))
            self._bytes += size
            while self._events and (len(self._events) > self.maxEvents or self._bytes > self.maxBytes):
                _, removedSize = self._events.popleft()
                self._bytes -= removedSize

    def after(self, sequence: int) -> list[AgentEvent]:
        """Sig: after(sequence) -> list[AgentEvent].

        Args: sequence는 클라이언트가 마지막으로 받은 순번이다.
        Returns: 그 뒤에 남아 있는 이벤트를 오름차순으로 반환한다.
        Example: `replay = buffer.after(12)`.
        """
        with self._lock:
            return [event for event, _ in self._events if event.sequence > sequence]

    def bounds(self) -> tuple[int | None, int | None]:
        """Sig: bounds() -> tuple[int | None, int | None].

        Args: 없음.
        Returns: 버퍼의 처음과 마지막 sequence다.
        Example: `first, last = buffer.bounds()`.
        """
        with self._lock:
            if not self._events:
                return None, None
            return self._events[0][0].sequence, self._events[-1][0].sequence
