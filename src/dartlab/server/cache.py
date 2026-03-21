"""세션 레벨 Company + snapshot 캐시.

동일 종목 반복 질문 시 Company 객체 재생성/데이터 재로드를 스킵한다.
LRU 방식, 최대 MAX_SIZE 종목 유지.
"""

from __future__ import annotations

import time
from collections import OrderedDict

from dartlab import Company

MAX_SIZE = 5
TTL_SECONDS = 600


class _CacheEntry:
    __slots__ = ("company", "snapshot", "created_at")

    def __init__(self, company: Company, snapshot: dict | None):
        self.company = company
        self.snapshot = snapshot
        self.created_at = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.created_at) > TTL_SECONDS


class CompanyCache:
    """스레드 안전은 불필요 (uvicorn single-worker, asyncio.to_thread 직렬)."""

    def __init__(self):
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()

    def get(self, stock_code: str) -> tuple[Company, dict | None] | None:
        entry = self._store.get(stock_code)
        if entry is None:
            return None
        if entry.is_expired():
            self._store.pop(stock_code, None)
            return None
        self._store.move_to_end(stock_code)
        return entry.company, entry.snapshot

    def put(self, stock_code: str, company: Company, snapshot: dict | None) -> None:
        if stock_code in self._store:
            self._store.move_to_end(stock_code)
            self._store[stock_code] = _CacheEntry(company, snapshot)
        else:
            self._store[stock_code] = _CacheEntry(company, snapshot)
            if len(self._store) > MAX_SIZE:
                self._store.popitem(last=False)

    def update_snapshot(self, stock_code: str, snapshot: dict | None) -> None:
        entry = self._store.get(stock_code)
        if entry:
            entry.snapshot = snapshot

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


company_cache = CompanyCache()
