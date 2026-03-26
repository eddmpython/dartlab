"""ECOS 시계열 캐시 — BoundedCache 기반 메모리 안전."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from dartlab.core.memory import BoundedCache

# TTL (초)
_TTL_DAILY = 6 * 3600  # 일별 데이터: 6시간
_TTL_OTHER = 24 * 3600  # 월별/분기별: 24시간

_cache = BoundedCache(max_entries=256)


def _makeKey(*parts: Any) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()


def get(indicatorId: str, start: str | None, end: str | None) -> Any | None:
    """캐시 조회. TTL 만료 시 None."""
    key = _makeKey(indicatorId, start, end)
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, ttl, value = entry
    if time.monotonic() - ts > ttl:
        _cache.pop(key, None)
        return None
    return value


def put(
    indicatorId: str,
    start: str | None,
    end: str | None,
    value: Any,
    *,
    daily: bool = False,
) -> None:
    """캐시 저장."""
    key = _makeKey(indicatorId, start, end)
    ttl = _TTL_DAILY if daily else _TTL_OTHER
    _cache[key] = (time.monotonic(), ttl, value)


def clear() -> None:
    """캐시 전체 비우기."""
    _cache.clear()
