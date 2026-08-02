"""짧은 TTL의 런타임 probe 캐시."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .contracts import RuntimeProbe


@dataclass
class ProbeCacheEntry:
    """probe 값과 단조 시각을 묶는다."""

    probe: RuntimeProbe
    storedAt: float


class ProbeCache:
    """중복 CLI 실행을 막는 프로세스 로컬 캐시."""

    def __init__(self, ttlSeconds: float = 15.0):
        self.ttlSeconds = ttlSeconds
        self._values: dict[str, ProbeCacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, runtimeId: str) -> RuntimeProbe | None:
        """Sig: get(runtimeId) -> RuntimeProbe | None.

        Args: runtimeId는 캐시 키다.
        Returns: TTL 안의 probe 또는 None이다.
        Example: `cached = cache.get("codex")`.
        """
        with self._lock:
            entry = self._values.get(runtimeId)
            if entry is None or time.monotonic() - entry.storedAt > self.ttlSeconds:
                self._values.pop(runtimeId, None)
                return None
            return entry.probe

    def put(self, probe: RuntimeProbe) -> RuntimeProbe:
        """Sig: put(probe) -> RuntimeProbe.

        Args: probe는 저장할 점검 결과다.
        Returns: 입력 probe를 그대로 반환한다.
        Example: `cache.put(probe)`.
        """
        with self._lock:
            self._values[probe.runtimeId] = ProbeCacheEntry(probe, time.monotonic())
        return probe

    def clear(self, runtimeId: str | None = None) -> None:
        """Sig: clear(runtimeId=None) -> None.

        Args: runtimeId가 없으면 전체 캐시를 지운다.
        Returns: None.
        Example: `cache.clear("codex")`.
        """
        with self._lock:
            if runtimeId is None:
                self._values.clear()
            else:
                self._values.pop(runtimeId, None)
