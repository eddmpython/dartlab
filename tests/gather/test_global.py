"""Gather 글로벌 확장 테스트 — market_config, resilience, fallback, stale cache."""

from __future__ import annotations

import time

import pytest

from dartlab.gather.infra.cache import GatherCache
from dartlab.gather.infra.resilience import CircuitBreaker, SourceHealthTracker
from dartlab.gather.marketConfig import (
    MARKETS,
    getMarketConfig,
    resolveTicker,
)
from dartlab.gather.types import CircuitOpenError, PriceSnapshot

pytestmark = pytest.mark.unit


# ══════════════════════════════════════
# MarketConfig 테스트
# ══════════════════════════════════════


class TestMarketConfig:
    """시장 설정 + ticker 변환."""

    def test_all_markets_defined(self):
        # Sprint 3 PR2 — 8→15 시장 확장 (CA/AU/BR/ZA/MX/SG/TH 추가)
        expected = {
            "KR",
            "US",
            "JP",
            "HK",
            "UK",
            "DE",
            "CN",
            "IN",
            "CA",
            "AU",
            "BR",
            "ZA",
            "MX",
            "SG",
            "TH",
        }
        assert set(MARKETS.keys()) == expected

    def test_get_market_config_known(self):
        config = getMarketConfig("KR")
        assert config.code == "KR"
        assert config.currency == "KRW"
        assert "naver" in config.fallback_chain

    def test_get_market_config_unknown_raises(self):
        """신뢰성 원칙: 미등록 market 을 silent US fallback 하지 않고 ValueError."""
        import pytest

        with pytest.raises(ValueError, match="알 수 없는 시장"):
            getMarketConfig("XX")

    def test_get_market_config_case_strict(self):
        """consistency_no_alias: 정식 대문자만 인정. 'kr' 은 ValueError."""
        import pytest

        with pytest.raises(ValueError, match="정식 표기"):
            getMarketConfig("kr")

    # ticker 변환

    def test_resolve_ticker_kr_naver(self):
        assert resolveTicker("005930", "KR", "naver") == "005930"

    def test_resolve_ticker_kr_yahoo(self):
        assert resolveTicker("005930", "KR", "yahoo_chart") == "005930.KS"

    def test_resolve_ticker_us(self):
        assert resolveTicker("AAPL", "US", "yahoo_chart") == "AAPL"
        assert resolveTicker("AAPL", "US", "fmp") == "AAPL"

    def test_resolve_ticker_jp(self):
        assert resolveTicker("7203", "JP", "yahoo_chart") == "7203.T"

    def test_resolve_ticker_hk_padding(self):
        # HK 4자리 패딩
        assert resolveTicker("293", "HK", "yahoo_chart") == "0293.HK"
        assert resolveTicker("9988", "HK", "yahoo_chart") == "9988.HK"

    def test_resolve_ticker_cn_shanghai(self):
        assert resolveTicker("600519", "CN", "yahoo_chart") == "600519.SS"

    def test_resolve_ticker_cn_shenzhen(self):
        assert resolveTicker("000858", "CN", "yahoo_chart") == "000858.SZ"
        assert resolveTicker("300750", "CN", "yahoo_chart") == "300750.SZ"

    def test_resolve_ticker_uk(self):
        assert resolveTicker("SHEL", "UK", "yahoo_chart") == "SHEL.L"

    def test_resolve_ticker_de(self):
        assert resolveTicker("SAP", "DE", "fmp") == "SAP.DE"

    def test_fallback_chains_not_empty(self):
        # Sprint 3 PR2 — 신규 시장 (ZA/SG/TH) 는 Yahoo only (≥ 1 허용).
        # 기존 8 시장 + CA/AU/BR/MX 는 ≥ 2 유지.
        single_chain_markets = {"ZA", "SG", "TH"}
        for code, config in MARKETS.items():
            min_len = 1 if code in single_chain_markets else 2
            assert len(config.fallback_chain) >= min_len, f"{code} fallback 체인이 너무 짧음 (min {min_len})"


# ══════════════════════════════════════
# CircuitBreaker 테스트
# ══════════════════════════════════════


class TestCircuitBreaker:
    """Circuit breaker 상태 전이."""

    def test_initially_closed(self):
        cb = CircuitBreaker()
        assert not cb.isOpen("test_source")
        assert cb.state("test_source") == "closed"

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failureThreshold=3)
        for _ in range(3):
            cb.recordFailure("src")
        assert cb.isOpen("src")
        assert cb.state("src") == "open"

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreaker(failureThreshold=5)
        for _ in range(4):
            cb.recordFailure("src")
        assert not cb.isOpen("src")

    def test_success_resets_count(self):
        cb = CircuitBreaker(failureThreshold=3)
        cb.recordFailure("src")
        cb.recordFailure("src")
        cb.recordSuccess("src")
        cb.recordFailure("src")
        cb.recordFailure("src")
        assert not cb.isOpen("src")  # 2 failures, not 3

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failureThreshold=2, recoveryTimeout=0.05)
        cb.recordFailure("src")
        cb.recordFailure("src")
        assert cb.isOpen("src")
        time.sleep(0.1)
        assert not cb.isOpen("src")  # timeout 경과 → 1회 시도 허용
        # 허용 직후 다시 open (동시 통과 방지)
        assert cb.isOpen("src")

    def test_half_open_success_closes(self):
        cb = CircuitBreaker(failureThreshold=2, recoveryTimeout=0.05)
        cb.recordFailure("src")
        cb.recordFailure("src")
        time.sleep(0.1)
        cb.isOpen("src")  # 1회 허용
        cb.recordSuccess("src")
        assert cb.state("src") == "closed"

    def test_half_open_failure_keeps_open(self):
        cb = CircuitBreaker(failureThreshold=2, recoveryTimeout=0.05)
        cb.recordFailure("src")
        cb.recordFailure("src")
        time.sleep(0.1)
        cb.isOpen("src")  # 1회 허용
        cb.recordFailure("src")
        assert cb.state("src") == "open"

    def test_independent_sources(self):
        cb = CircuitBreaker(failureThreshold=2)
        cb.recordFailure("a")
        cb.recordFailure("a")
        assert cb.isOpen("a")
        assert not cb.isOpen("b")


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
        cache.putTyped("005930", "price", PriceSnapshot(current=200000))
        # 정상 조회
        assert cache.getTyped("005930", "price") is not None

    def test_stale_returns_expired(self):
        cache = GatherCache()
        cache.put("key", "value", ttl=1)
        # 수동으로 expires_at을 과거로 설정
        cache._store["key"].expires_at = time.monotonic() - 1.0
        # 일반 조회는 None (만료 → stale store로 이동)
        assert cache.get("key") is None
        # stale 조회는 반환
        assert cache.getStale("key") == "value"

    def test_get_typed_stale_fallback(self):
        cache = GatherCache()
        cache.put("005930:price", PriceSnapshot(current=100000), ttl=1)
        # 수동으로 만료
        cache._store["005930:price"].expires_at = time.monotonic() - 1.0
        # allow_stale=False → None (만료 데이터 stale로 이동)
        assert cache.getTyped("005930", "price", allowStale=False) is None
        # allow_stale=True → stale 데이터
        result = cache.getTyped("005930", "price", allowStale=True)
        assert result is not None
        assert result.current == 100000


# ══════════════════════════════════════
# CircuitOpenError 타입 체크
# ══════════════════════════════════════


class TestCircuitOpenError:
    def test_is_source_unavailable_subclass(self):
        from dartlab.gather.types import SourceUnavailableError

        err = CircuitOpenError("test")
        assert isinstance(err, SourceUnavailableError)


# ══════════════════════════════════════
# Price Fallback 통합 테스트 (mock)
# ══════════════════════════════════════


class TestPriceFallback:
    """시장별 동적 fallback — mock 기반."""

    def test_kr_uses_naver_first(self, monkeypatch: pytest.MonkeyPatch):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock

        from dartlab.gather.infra.resilience import CircuitBreaker, SourceHealthTracker
        from dartlab.gather.sources import price

        monkeypatch.setattr(price, "circuitBreaker", CircuitBreaker())
        monkeypatch.setattr(price, "healthTracker", SourceHealthTracker())
        price._staleCache.clear()

        mock_resp = MagicMock()
        mock_resp.json.side_effect = [
            {"closePrice": "200,000"},
            {"totalInfos": [{"code": "per", "value": "12.50배"}]},
        ]
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_resp)

        result = asyncio.run(price.fetch("005930", market="KR", client=mock_client))
        assert result is not None
        assert result.current == 200000

    def test_domains_registry_loads_all(self):
        """모든 도메인이 loadDomain 으로 로드 가능 (snake alias 포함)."""
        from dartlab.gather.domains import loadDomain

        for name in ("naver", "yahoo_chart", "fmp"):
            module = loadDomain(name)
            # codemod 로 fetch_price → fetchPrice (commit 452fbe3c6 ~)
            assert hasattr(module, "fetchPrice")

    def test_domains_registry_invalid_raises(self):
        from dartlab.gather.domains import loadDomain

        with pytest.raises(ValueError, match="알 수 없는 도메인"):
            loadDomain("nonexistent")
