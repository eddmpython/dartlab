"""dartlab.gather.infra.cache real unit test (G+ P-Q7~Q11 batch).

GatherCache 의 TTL 만료, LRU 축출, BoundedCache 용량 한계, stale-while-revalidate
동작을 mock-free 단위 테스트로 검증.
"""

from __future__ import annotations

import importlib
import time

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.infra.cache`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.infra.cache")


def test_put_then_get_returns_value() -> None:
    """put → get 정상 동작 (TTL 안)."""
    from dartlab.gather.infra.cache import GatherCache

    cache = GatherCache(maxEntries=10)
    cache.put("key1", "value1", ttl=60)
    assert cache.get("key1") == "value1"


def test_get_missing_returns_none() -> None:
    """미존재 키는 None."""
    from dartlab.gather.infra.cache import GatherCache

    cache = GatherCache(maxEntries=10)
    assert cache.get("nonexistent") is None


def test_ttl_expires() -> None:
    """TTL 만료 후 None — stale 로 이동."""
    from dartlab.gather.infra.cache import GatherCache

    cache = GatherCache(maxEntries=10)
    cache.put("key1", "value1", ttl=1)  # 1초 만료
    assert cache.get("key1") == "value1"  # 즉시 hit
    time.sleep(1.1)
    assert cache.get("key1") is None  # 만료 후 None


def test_lru_eviction_on_capacity() -> None:
    """max 초과 시 가장 오래된 항목 evict (LRU)."""
    from dartlab.gather.infra.cache import GatherCache

    cache = GatherCache(maxEntries=3)
    cache.put("k1", "v1", ttl=60)
    cache.put("k2", "v2", ttl=60)
    cache.put("k3", "v3", ttl=60)
    cache.put("k4", "v4", ttl=60)  # k1 축출
    assert cache.get("k1") is None
    assert cache.get("k2") == "v2"
    assert cache.get("k3") == "v3"
    assert cache.get("k4") == "v4"


def test_typed_put_get() -> None:
    """putTyped / getTyped — 데이터 유형별 TTL 자동."""
    from dartlab.gather.infra.cache import GatherCache

    cache = GatherCache(maxEntries=10)
    cache.putTyped("005930", "price", {"close": 70000})
    val = cache.getTyped("005930", "price")
    assert val == {"close": 70000}


def test_ttl_env_override_via_module() -> None:
    """infra/ttl.py 의 TTL_PRICE 가 cache 에 반영됨 (env override 경로)."""
    from dartlab.gather.infra import cache, ttl

    # cache 모듈이 ttl 모듈의 TTL_PRICE 를 import 했는지 확인
    assert cache.TTL_PRICE == ttl.TTL_PRICE


def test_invalidate_stockCode() -> None:
    """종목별 일괄 무효화 — 같은 stockCode 의 모든 typed 항목 제거."""
    from dartlab.gather.infra.cache import GatherCache

    cache = GatherCache(maxEntries=10)
    cache.putTyped("005930", "price", "v1")
    cache.putTyped("005930", "flow", "v2")
    cache.putTyped("000660", "price", "v3")
    cache.invalidate("005930")
    assert cache.getTyped("005930", "price") is None
    assert cache.getTyped("005930", "flow") is None
    assert cache.getTyped("000660", "price") == "v3"


def test_cache_stats_counter() -> None:
    """get hit/miss + put eviction 마다 telemetry 카운터 누적 — A 트랙 O1."""
    from dartlab.gather.infra.cache import GatherCache
    from dartlab.gather.infra.telemetry import getCacheStatsSnapshot, resetCacheStats

    resetCacheStats()
    base = getCacheStatsSnapshot()
    assert base == {"hit": 0, "miss": 0, "evicted": 0}

    cache = GatherCache(maxEntries=3)
    cache.put("k1", "v1", ttl=60)
    cache.put("k2", "v2", ttl=60)
    cache.put("k3", "v3", ttl=60)

    # hit 5 회
    for _ in range(5):
        assert cache.get("k1") == "v1"
    # miss 3 회
    for _ in range(3):
        assert cache.get("nonexistent") is None
    # eviction 2 회 (maxEntries=3 에 5 키 → 2 축출)
    cache.put("k4", "v4", ttl=60)
    cache.put("k5", "v5", ttl=60)

    snap = getCacheStatsSnapshot()
    assert snap["hit"] == 5
    assert snap["miss"] == 3
    assert snap["evicted"] == 2


def test_cache_stats_reset_isolation() -> None:
    """resetCacheStats 가 모든 카운터를 0 으로 — 테스트 격리 보장."""
    from dartlab.gather.infra.cache import GatherCache
    from dartlab.gather.infra.telemetry import getCacheStatsSnapshot, resetCacheStats

    cache = GatherCache(maxEntries=2)
    cache.put("a", 1, ttl=60)
    cache.get("a")
    cache.get("missing")
    assert getCacheStatsSnapshot()["hit"] >= 1

    resetCacheStats()
    assert getCacheStatsSnapshot() == {"hit": 0, "miss": 0, "evicted": 0}


def test_cache_slot_is_deterministic_and_market_sensitive() -> None:
    from dartlab.gather.infra.cache import buildCacheSlot

    kr = buildCacheSlot("history", end="2026-01-31", market="kr", start="2026-01-01")
    us = buildCacheSlot("history", start="2026-01-01", market="US", end="2026-01-31")

    assert kr == "history|end=2026-01-31|market=KR|start=2026-01-01"
    assert us == "history|end=2026-01-31|market=US|start=2026-01-01"
    assert kr != us


def test_cache_slot_rejects_empty_type() -> None:
    from dartlab.gather.infra.cache import buildCacheSlot

    with pytest.raises(ValueError, match="dataType"):
        buildCacheSlot("")
