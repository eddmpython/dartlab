"""Gather 글로벌 확장 테스트 — market_config, resilience, fallback, stale cache."""

from __future__ import annotations

import time

import pytest

from dartlab.engines.gather.cache import GatherCache
from dartlab.engines.gather.market_config import (
    MARKETS,
    get_market_config,
    resolve_ticker,
)
from dartlab.engines.gather.resilience import CircuitBreaker, SourceHealthTracker
from dartlab.engines.gather.types import CircuitOpenError, PriceSnapshot

pytestmark = pytest.mark.unit


# ══════════════════════════════════════
# MarketConfig 테스트
# ══════════════════════════════════════


class TestMarketConfig:
    """시장 설정 + ticker 변환."""

    def test_all_markets_defined(self):
        expected = {"KR", "US", "JP", "HK", "UK", "DE", "CN", "IN"}
        assert set(MARKETS.keys()) == expected

    def test_get_market_config_known(self):
        config = get_market_config("KR")
        assert config.code == "KR"
        assert config.currency == "KRW"
        assert "naver" in config.fallback_chain

    def test_get_market_config_unknown_returns_us(self):
        config = get_market_config("XX")
        assert config.code == "US"

    def test_get_market_config_case_insensitive(self):
        config = get_market_config("kr")
        assert config.code == "KR"

    # ticker 변환

    def test_resolve_ticker_kr_naver(self):
        assert resolve_ticker("005930", "KR", "naver") == "005930"

    def test_resolve_ticker_kr_yahoo(self):
        assert resolve_ticker("005930", "KR", "yahoo_direct") == "005930.KS"

    def test_resolve_ticker_us(self):
        assert resolve_ticker("AAPL", "US", "yahoo_direct") == "AAPL"
        assert resolve_ticker("AAPL", "US", "fmp") == "AAPL"

    def test_resolve_ticker_jp(self):
        assert resolve_ticker("7203", "JP", "yahoo_direct") == "7203.T"

    def test_resolve_ticker_hk_padding(self):
        # HK 4자리 패딩
        assert resolve_ticker("293", "HK", "yahoo_direct") == "0293.HK"
        assert resolve_ticker("9988", "HK", "yahoo_direct") == "9988.HK"

    def test_resolve_ticker_cn_shanghai(self):
        assert resolve_ticker("600519", "CN", "yahoo_direct") == "600519.SS"

    def test_resolve_ticker_cn_shenzhen(self):
        assert resolve_ticker("000858", "CN", "yahoo_direct") == "000858.SZ"
        assert resolve_ticker("300750", "CN", "yahoo_direct") == "300750.SZ"

    def test_resolve_ticker_uk(self):
        assert resolve_ticker("SHEL", "UK", "yahoo_direct") == "SHEL.L"

    def test_resolve_ticker_de(self):
        assert resolve_ticker("SAP", "DE", "fmp") == "SAP.DE"

    def test_fallback_chains_not_empty(self):
        for code, config in MARKETS.items():
            assert len(config.fallback_chain) >= 2, f"{code} fallback 체인이 너무 짧음"


# ══════════════════════════════════════
# CircuitBreaker 테스트
# ══════════════════════════════════════


class TestCircuitBreaker:
    """Circuit breaker 상태 전이."""

    def test_initially_closed(self):
        cb = CircuitBreaker()
        assert not cb.is_open("test_source")
        assert cb.state("test_source") == "closed"

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure("src")
        assert cb.is_open("src")
        assert cb.state("src") == "open"

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreaker(failure_threshold=5)
        for _ in range(4):
            cb.record_failure("src")
        assert not cb.is_open("src")

    def test_success_resets_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure("src")
        cb.record_failure("src")
        cb.record_success("src")
        cb.record_failure("src")
        cb.record_failure("src")
        assert not cb.is_open("src")  # 2 failures, not 3

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        cb.record_failure("src")
        cb.record_failure("src")
        assert cb.is_open("src")
        time.sleep(0.06)
        assert not cb.is_open("src")  # timeout 경과 → 1회 시도 허용
        # 허용 직후 다시 open (동시 통과 방지)
        assert cb.is_open("src")

    def test_half_open_success_closes(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        cb.record_failure("src")
        cb.record_failure("src")
        time.sleep(0.06)
        cb.is_open("src")  # 1회 허용
        cb.record_success("src")
        assert cb.state("src") == "closed"

    def test_half_open_failure_keeps_open(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        cb.record_failure("src")
        cb.record_failure("src")
        time.sleep(0.06)
        cb.is_open("src")  # 1회 허용
        cb.record_failure("src")
        assert cb.state("src") == "open"

    def test_independent_sources(self):
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure("a")
        cb.record_failure("a")
        assert cb.is_open("a")
        assert not cb.is_open("b")


# ══════════════════════════════════════
# SourceHealthTracker 테스트
# ══════════════════════════════════════


class TestSourceHealthTracker:
    """Source health scoring + reorder."""

    def test_default_score(self):
        ht = SourceHealthTracker()
        assert ht.score("unknown") == 0.5

    def test_all_success_high_score(self):
        ht = SourceHealthTracker()
        for _ in range(10):
            ht.record("src", success=True, latency=0.1)
        assert ht.score("src") > 0.9

    def test_all_failure_low_score(self):
        ht = SourceHealthTracker()
        for _ in range(10):
            ht.record("src", success=False)
        assert ht.score("src") < 0.2

    def test_reorder_keeps_original_when_similar(self):
        ht = SourceHealthTracker()
        # 두 소스 모두 신규 → score 0.5 동일 → 원래 순서
        result = ht.reorder(("a", "b", "c"))
        assert result == ["a", "b", "c"]

    def test_reorder_promotes_healthy(self):
        ht = SourceHealthTracker()
        for _ in range(20):
            ht.record("a", success=False)
            ht.record("b", success=True, latency=0.1)
        result = ht.reorder(("a", "b"))
        assert result[0] == "b"


# ══════════════════════════════════════
# Stale Cache 테스트
# ══════════════════════════════════════


class TestStaleCache:
    """stale-while-revalidate."""

    def test_get_typed_allow_stale(self):
        cache = GatherCache()
        cache.put_typed("005930", "price", PriceSnapshot(current=200000))
        # 정상 조회
        assert cache.get_typed("005930", "price") is not None

    def test_stale_returns_expired(self):
        cache = GatherCache()
        cache.put("key", "value", ttl=1)
        # 수동으로 expires_at을 과거로 설정
        cache._store["key"].expires_at = time.monotonic() - 1.0
        # 일반 조회는 None (만료 → stale store로 이동)
        assert cache.get("key") is None
        # stale 조회는 반환
        assert cache.get_stale("key") == "value"

    def test_get_typed_stale_fallback(self):
        cache = GatherCache()
        cache.put("005930:price", PriceSnapshot(current=100000), ttl=1)
        # 수동으로 만료
        cache._store["005930:price"].expires_at = time.monotonic() - 1.0
        # allow_stale=False → None (만료 데이터 stale로 이동)
        assert cache.get_typed("005930", "price", allow_stale=False) is None
        # allow_stale=True → stale 데이터
        result = cache.get_typed("005930", "price", allow_stale=True)
        assert result is not None
        assert result.current == 100000


# ══════════════════════════════════════
# CircuitOpenError 타입 체크
# ══════════════════════════════════════


class TestCircuitOpenError:
    def test_is_source_unavailable_subclass(self):
        from dartlab.engines.gather.types import SourceUnavailableError

        err = CircuitOpenError("test")
        assert isinstance(err, SourceUnavailableError)


# ══════════════════════════════════════
# Price Fallback 통합 테스트 (mock)
# ══════════════════════════════════════


class TestPriceFallback:
    """시장별 동적 fallback — mock 기반."""

    def test_kr_uses_naver_first(self):
        from unittest.mock import MagicMock

        from dartlab.engines.gather import price

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "closePrice": "200,000",
            "per": "12.50",
        }
        mock_client.get.return_value = mock_resp

        result = price.fetch("005930", market="KR", client=mock_client)
        assert result is not None
        assert result.current == 200000

    def test_domains_registry_loads_all(self):
        """모든 도메인이 load_domain으로 로드 가능."""
        from dartlab.engines.gather.domains import load_domain

        for name in ("naver", "yahoo", "yahoo_direct", "fmp"):
            module = load_domain(name)
            assert hasattr(module, "fetch_price")

    def test_domains_registry_invalid_raises(self):
        from dartlab.engines.gather.domains import load_domain

        with pytest.raises(ValueError, match="알 수 없는 도메인"):
            load_domain("nonexistent")
