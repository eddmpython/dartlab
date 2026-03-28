"""세션 레벨 Company + snapshot 캐시.

동일 종목 반복 질문 시 Company 객체 재생성/데이터 재로드를 스킵한다.
LRU 방식, 최대 MAX_SIZE 종목 유지.
적응형 TTL: 자주 접근되는 종목은 TTL 연장, 메모리 압박 시 캐시 축소.
"""

from __future__ import annotations

import time
from collections import OrderedDict

from dartlab import Company

MAX_SIZE = 5
BASE_TTL = 600
MAX_TTL = 3000
_MEMORY_THRESHOLD_MB = 1500


class _CacheEntry:
    __slots__ = ("company", "snapshot", "created_at", "access_count", "ttl")

    def __init__(self, company: Company, snapshot: dict | None):
        self.company = company
        self.snapshot = snapshot
        self.created_at = time.monotonic()
        self.access_count = 1
        self.ttl = BASE_TTL

    def touch(self) -> None:
        """접근 횟수 증가 및 TTL 연장."""
        self.access_count += 1
        self.ttl = min(BASE_TTL + self.access_count * 300, MAX_TTL)

    def is_expired(self) -> bool:
        """TTL 초과 여부를 반환한다."""
        return (time.monotonic() - self.created_at) > self.ttl


class CompanyCache:
    """스레드 안전은 불필요 (uvicorn single-worker, asyncio.to_thread 직렬)."""

    def __init__(self):
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._max_size = MAX_SIZE

    def _check_memory_pressure(self) -> None:
        """메모리 압박 시 캐시 크기 자동 축소."""
        try:
            from dartlab.core.memory import get_memory_mb

            mem = get_memory_mb()
            if mem <= 0:
                return
            if mem > _MEMORY_THRESHOLD_MB * 1.5:
                self._max_size = 1
            elif mem > _MEMORY_THRESHOLD_MB:
                self._max_size = 3
            else:
                self._max_size = MAX_SIZE
        except ImportError:
            pass

    def get(self, stock_code: str) -> tuple[Company, dict | None] | None:
        """캐시에서 Company와 snapshot을 조회한다."""
        entry = self._store.get(stock_code)
        if entry is None:
            return None
        if entry.is_expired():
            self._store.pop(stock_code, None)
            return None
        entry.touch()
        self._store.move_to_end(stock_code)
        return entry.company, entry.snapshot

    def put(self, stock_code: str, company: Company, snapshot: dict | None) -> None:
        """Company와 snapshot을 캐시에 저장한다."""
        self._check_memory_pressure()
        if stock_code in self._store:
            old = self._store[stock_code]
            new_entry = _CacheEntry(company, snapshot)
            new_entry.access_count = old.access_count + 1
            new_entry.ttl = min(BASE_TTL + new_entry.access_count * 300, MAX_TTL)
            self._store.move_to_end(stock_code)
            self._store[stock_code] = new_entry
        else:
            self._store[stock_code] = _CacheEntry(company, snapshot)
            while len(self._store) > self._max_size:
                self._store.popitem(last=False)

    def update_snapshot(self, stock_code: str, snapshot: dict | None) -> None:
        """기존 캐시 항목의 snapshot만 갱신한다."""
        entry = self._store.get(stock_code)
        if entry:
            entry.snapshot = snapshot

    def clear(self) -> None:
        """캐시 전체를 비우고 크기 제한을 초기화한다."""
        self._store.clear()
        self._max_size = MAX_SIZE

    def __len__(self) -> int:
        return len(self._store)


company_cache = CompanyCache()
