"""Gather 엔진 TTL 캐시 — 데이터 유형별 만료 + LRU 축출."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass

# TTL 기본값 (초)
TTL_PRICE = 300  # 5분
TTL_CONSENSUS = 24 * 3600  # 24시간
TTL_FLOW = 3600  # 1시간
TTL_SECTOR = 24 * 3600  # 24시간
TTL_HISTORY = 6 * 3600  # 6시간
TTL_SNAPSHOT = 300  # 5분 (전체 수집 결과)
TTL_DEFAULT = 3600  # 1시간

# 데이터 유형 → TTL 매핑
_TTL_MAP: dict[str, int] = {
    "price": TTL_PRICE,
    "consensus": TTL_CONSENSUS,
    "flow": TTL_FLOW,
    "sector_per": TTL_SECTOR,
    "history": TTL_HISTORY,
    "snapshot": TTL_SNAPSHOT,
}


@dataclass(slots=True)
class _CacheEntry:
    value: object
    expires_at: float


class GatherCache:
    """TTL 기반 LRU 캐시 — thread-safe + 용량 제한.

    - 데이터 유형별 TTL 자동 적용
    - max_entries 초과 시 가장 오래된 항목 축출
    - 종목별 일괄 무효화 지원
    """

    def __init__(self, max_entries: int = 200) -> None:
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._max = max_entries
        self._lock = threading.Lock()

    def get(self, key: str) -> object | None:
        """캐시 조회. 만료되었으면 제거 후 None 반환."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return entry.value

    def put(self, key: str, value: object, ttl: int = TTL_DEFAULT) -> None:
        """캐시 저장."""
        with self._lock:
            if key in self._store:
                del self._store[key]
            self._store[key] = _CacheEntry(
                value=value,
                expires_at=time.monotonic() + ttl,
            )
            while len(self._store) > self._max:
                self._store.popitem(last=False)

    def get_typed(self, stock_code: str, data_type: str) -> object | None:
        """데이터 유형별 캐시 조회."""
        return self.get(f"{stock_code}:{data_type}")

    def put_typed(self, stock_code: str, data_type: str, value: object) -> None:
        """데이터 유형에 맞는 TTL로 저장."""
        ttl = _TTL_MAP.get(data_type, TTL_DEFAULT)
        self.put(f"{stock_code}:{data_type}", value, ttl)

    def invalidate(self, stock_code: str) -> None:
        """특정 종목의 모든 캐시 제거."""
        with self._lock:
            keys = [k for k in self._store if k.startswith(f"{stock_code}:")]
            for k in keys:
                del self._store[k]

    def clear(self) -> None:
        """전체 캐시 초기화."""
        with self._lock:
            self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"GatherCache(entries={self.size}, max={self._max})"
