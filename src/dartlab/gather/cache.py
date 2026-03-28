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
TTL_NEWS = 1800  # 30분
TTL_DIVIDENDS = 24 * 3600  # 24시간
TTL_SPLITS = 24 * 3600  # 24시간
TTL_MACRO = 6 * 3600  # 6시간
TTL_DEFAULT = 3600  # 1시간

# 데이터 유형 → TTL 매핑
_TTL_MAP: dict[str, int] = {
    "price": TTL_PRICE,
    "consensus": TTL_CONSENSUS,
    "flow": TTL_FLOW,
    "sector_per": TTL_SECTOR,
    "history": TTL_HISTORY,
    "snapshot": TTL_SNAPSHOT,
    "news": TTL_NEWS,
    "dividends": TTL_DIVIDENDS,
    "splits": TTL_SPLITS,
    "macro": TTL_MACRO,
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
    - stale-while-revalidate: 만료 데이터를 별도 보관하여 최후 fallback 제공
    """

    def __init__(self, max_entries: int = 200) -> None:
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._stale: dict[str, object] = {}  # 만료 시 마지막 값 보존
        self._max = max_entries
        self._stale_max = max_entries  # stale도 용량 제한
        self._lock = threading.Lock()

    def get(self, key: str) -> object | None:
        """캐시 조회. 만료되었으면 stale로 이동 후 None 반환."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                # stale store에 보존 후 live에서 제거
                self._stale[key] = entry.value
                del self._store[key]
                self._trim_stale()
                return None
            self._store.move_to_end(key)
            return entry.value

    def put(self, key: str, value: object, ttl: int = TTL_DEFAULT) -> None:
        """캐시 저장."""
        with self._lock:
            if key in self._store:
                del self._store[key]
            self._stale.pop(key, None)  # 새 값 → stale 제거
            self._store[key] = _CacheEntry(
                value=value,
                expires_at=time.monotonic() + ttl,
            )
            while len(self._store) > self._max:
                self._store.popitem(last=False)

    def _trim_stale(self) -> None:
        """stale store 용량 제한 (lock 내에서 호출)."""
        while len(self._stale) > self._stale_max:
            # dict는 삽입순 — 가장 오래된 것 제거
            first_key = next(iter(self._stale))
            del self._stale[first_key]

    def get_stale(self, key: str) -> object | None:
        """만료된 데이터 반환 (stale-while-revalidate)."""
        with self._lock:
            return self._stale.get(key)

    def get_typed(self, stock_code: str, data_type: str, *, allow_stale: bool = False) -> object | None:
        """데이터 유형별 캐시 조회. allow_stale=True이면 만료 데이터도 반환."""
        key = f"{stock_code}:{data_type}"
        result = self.get(key)
        if result is not None:
            return result
        if allow_stale:
            return self.get_stale(key)
        return None

    def put_typed(self, stock_code: str, data_type: str, value: object) -> None:
        """데이터 유형에 맞는 TTL로 저장."""
        ttl = _TTL_MAP.get(data_type, TTL_DEFAULT)
        self.put(f"{stock_code}:{data_type}", value, ttl)

    def invalidate(self, stock_code: str) -> None:
        """특정 종목의 모든 캐시 제거 (live + stale)."""
        with self._lock:
            prefix = f"{stock_code}:"
            for store in (self._store, self._stale):
                keys = [k for k in store if k.startswith(prefix)]
                for k in keys:
                    del store[k]

    def clear(self) -> None:
        """전체 캐시 초기화 (live + stale)."""
        with self._lock:
            self._store.clear()
            self._stale.clear()

    @property
    def size(self) -> int:
        """캐시에 저장된 항목 수."""
        return len(self._store)

    def __repr__(self) -> str:
        return f"GatherCache(entries={self.size}, max={self._max})"
