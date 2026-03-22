"""Gather 엔진 단위 테스트 — cache, http, naver source, facade."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

from dartlab.engines.gather.cache import GatherCache
from dartlab.engines.gather.http import GatherHttpClient, _DomainRateLimiter, _DomainSemaphore
from dartlab.engines.gather.types import (
    ConsensusData,
    FlowData,
    GatherResult,
    GatherSnapshot,
    MarketSnapshot,
    PeerData,
    PriceSnapshot,
)

# ══════════════════════════════════════
# GatherCache 테스트
# ══════════════════════════════════════


class TestGatherCache:
    """GatherCache TTL + LRU 테스트."""

    def test_put_and_get(self):
        cache = GatherCache()
        cache.put("key1", "value1", ttl=60)
        assert cache.get("key1") == "value1"

    def test_get_missing_returns_none(self):
        cache = GatherCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        cache = GatherCache()
        cache.put("key1", "value1", ttl=0)
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_max_entries_eviction(self):
        cache = GatherCache(max_entries=3)
        cache.put("a", 1, ttl=60)
        cache.put("b", 2, ttl=60)
        cache.put("c", 3, ttl=60)
        cache.put("d", 4, ttl=60)  # a 제거됨
        assert cache.get("a") is None
        assert cache.get("d") == 4
        assert cache.size == 3

    def test_lru_access_order(self):
        cache = GatherCache(max_entries=3)
        cache.put("a", 1, ttl=60)
        cache.put("b", 2, ttl=60)
        cache.put("c", 3, ttl=60)
        cache.get("a")  # a 접근 → LRU 순서 갱신
        cache.put("d", 4, ttl=60)  # b 제거됨
        assert cache.get("a") == 1
        assert cache.get("b") is None

    def test_typed_put_and_get(self):
        cache = GatherCache()
        cache.put_typed("005930", "consensus", {"target": 300000})
        result = cache.get_typed("005930", "consensus")
        assert result == {"target": 300000}

    def test_invalidate(self):
        cache = GatherCache()
        cache.put_typed("005930", "consensus", {"target": 300000})
        cache.put_typed("005930", "price", {"current": 200000})
        cache.put_typed("000660", "consensus", {"target": 150000})
        cache.invalidate("005930")
        assert cache.get_typed("005930", "consensus") is None
        assert cache.get_typed("005930", "price") is None
        assert cache.get_typed("000660", "consensus") is not None

    def test_clear(self):
        cache = GatherCache()
        cache.put("a", 1, ttl=60)
        cache.put("b", 2, ttl=60)
        cache.clear()
        assert cache.size == 0

    def test_repr(self):
        cache = GatherCache(max_entries=100)
        assert "GatherCache" in repr(cache)


# ══════════════════════════════════════
# HTTP 클라이언트 테스트
# ══════════════════════════════════════


class TestDomainRateLimiter:
    """Rate limiter 기본 동작."""

    def test_acquire_within_limit(self):
        limiter = _DomainRateLimiter("test.com", rpm=60)
        for _ in range(5):
            limiter.acquire()

    def test_domain_stored(self):
        limiter = _DomainRateLimiter("example.com", rpm=30)
        assert limiter._domain == "example.com"
        assert limiter._rpm == 30


class TestDomainSemaphore:
    """동시 연결 제한."""

    def test_acquire_release(self):
        sem = _DomainSemaphore(max_concurrent=2)
        assert sem.acquire(timeout=1.0)
        assert sem.acquire(timeout=1.0)
        sem.release()
        sem.release()


class TestGatherHttpClient:
    """GatherHttpClient 기본 동작."""

    def test_close(self):
        client = GatherHttpClient()
        client.close()  # 에러 없이 종료


# ══════════════════════════════════════
# 데이터 타입 테스트
# ══════════════════════════════════════


class TestDataTypes:
    """데이터 타입 repr + 기본값."""

    def test_price_snapshot_repr(self):
        p = PriceSnapshot(current=200000, per=12.5, pbr=1.3, source="naver")
        r = repr(p)
        assert "200,000" in r
        assert "naver" in r

    def test_consensus_repr(self):
        c = ConsensusData(
            target_price=300000,
            analyst_count=15,
            buy_ratio=0.8,
            high=350000,
            low=250000,
            source="naver",
        )
        r = repr(c)
        assert "300,000" in r

    def test_flow_repr(self):
        f = FlowData(foreign_net=-2500000, institution_net=1200000, foreign_holding_ratio=55.3)
        r = repr(f)
        assert "외국인" in r

    def test_peer_data_repr(self):
        p = PeerData(ticker="TSMC", name="TSMC", per=15.3, pbr=3.2)
        r = repr(p)
        assert "TSMC" in r
        assert "PER=15.3" in r

    def test_peer_data_none_fields(self):
        p = PeerData(ticker="AAPL", name="Apple")
        r = repr(p)
        assert "PER" not in r

    def test_market_snapshot_repr(self):
        snap = MarketSnapshot(
            stock_code="005930",
            current_price=200000,
            consensus=ConsensusData(target_price=300000, analyst_count=10, source="naver"),
            multiples={"per": 12.5, "pbr": 1.3},
            sources_available=["naver"],
            collected_at="2026-03-22T00:00:00",
        )
        r = repr(snap)
        assert "005930" in r
        assert "200,000" in r

    def test_market_snapshot_defaults(self):
        snap = MarketSnapshot()
        assert snap.stock_code == ""
        assert snap.current_price == 0.0
        assert snap.consensus is None
        assert snap.multiples == {}

    def test_gather_snapshot_properties(self):
        snap = GatherSnapshot(
            stock_code="005930",
            results={
                "naver": GatherResult(
                    domain="naver",
                    price=PriceSnapshot(current=200000, source="naver"),
                    consensus=ConsensusData(target_price=300000, source="naver"),
                    flow=FlowData(foreign_net=-1000, source="naver"),
                    sector_per=15.0,
                ),
                "yahoo": GatherResult(domain="yahoo", error="yfinance 미설치"),
            },
        )
        assert snap.price is not None
        assert snap.price.current == 200000
        assert snap.consensus is not None
        assert snap.consensus.target_price == 300000
        assert snap.flow is not None
        assert snap.sources_available == ["naver"]
        assert snap.sources_failed == ["yahoo"]

    def test_gather_snapshot_to_market_snapshot(self):
        snap = GatherSnapshot(
            stock_code="005930",
            results={
                "naver": GatherResult(
                    domain="naver",
                    price=PriceSnapshot(
                        current=200000,
                        per=12.5,
                        pbr=1.3,
                        high_52w=250000,
                        low_52w=150000,
                        source="naver",
                    ),
                    consensus=ConsensusData(target_price=300000, analyst_count=10, source="naver"),
                    flow=FlowData(foreign_net=-2500000, institution_net=1200000, foreign_holding_ratio=55.3),
                    sector_per=15.0,
                ),
            },
            collected_at="2026-03-22T00:00:00",
        )
        ms = snap.to_market_snapshot()
        assert ms.stock_code == "005930"
        assert ms.current_price == 200000
        assert ms.consensus is not None
        assert ms.consensus.target_price == 300000
        assert ms.multiples["per"] == 12.5
        assert ms.multiples["sector_per"] == 15.0
        assert ms.price_range_52w == (150000, 250000)
        assert ms.supply_demand["foreign_net"] == -2500000


# ══════════════════════════════════════
# Naver Source 테스트 (mock)
# ══════════════════════════════════════


class TestNaverSource:
    """네이버 소스 — mock HTTP 응답."""

    def test_fetch_price_success(self):
        from dartlab.engines.gather.domains.naver import fetch_price

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "closePrice": "200,000",
            "per": "12.50",
            "pbr": "1.30",
            "dividendYield": "2.10",
            "marketCap": "3,564,000",
            "high52wPrice": "250,000",
            "low52wPrice": "150,000",
        }
        mock_client.get.return_value = mock_resp

        result = fetch_price("005930", mock_client)
        assert result is not None
        assert result.current == 200000
        assert result.per == 12.5
        assert result.pbr == 1.3
        assert result.high_52w == 250000

    def test_fetch_consensus_success(self):
        from dartlab.engines.gather.domains.naver import fetch_consensus

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "consensusInfo": {
                "targetPrice": "300,000",
                "analystCount": 15,
                "targetPriceHigh": "350,000",
                "targetPriceLow": "250,000",
                "investmentOpinion": [
                    {"opinion": "매수", "count": 10},
                    {"opinion": "중립", "count": 3},
                    {"opinion": "매도", "count": 2},
                ],
            }
        }
        mock_client.get.return_value = mock_resp

        result = fetch_consensus("005930", mock_client)
        assert result is not None
        assert result.target_price == 300000
        assert result.analyst_count == 15
        assert abs(result.buy_ratio - 10 / 15) < 0.01
        assert result.high == 350000
        assert result.low == 250000

    def test_fetch_consensus_no_data(self):
        from dartlab.engines.gather.domains.naver import fetch_consensus

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_client.get.return_value = mock_resp

        result = fetch_consensus("005930", mock_client)
        assert result is None

    def test_fetch_flow_success(self):
        from dartlab.engines.gather.domains.naver import fetch_flow

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "foreignSummary": {"foreignOwnershipRatio": "55.30"},
            "dealTrendByInvestor": [
                {"investorType": "외국인", "accumulatedNetBuyVolume": "-2,500,000"},
                {"investorType": "기관", "accumulatedNetBuyVolume": "1,200,000"},
            ],
        }
        mock_client.get.return_value = mock_resp

        result = fetch_flow("005930", mock_client)
        assert result is not None
        assert result.foreign_holding_ratio == 55.3
        assert result.foreign_net == -2500000
        assert result.institution_net == 1200000

    def test_clean_number_edge_cases(self):
        from dartlab.engines.gather.domains.naver import _clean_number

        assert _clean_number("1,234,567") == 1234567
        assert _clean_number("+500") == 500
        assert _clean_number("-100") == -100
        assert _clean_number("N/A") is None
        assert _clean_number("") is None
        assert _clean_number(None) is None


# ══════════════════════════════════════
# Gather Facade 테스트 (mock)
# ══════════════════════════════════════


class TestGatherFacade:
    """Gather facade — mock 기반 통합."""

    def test_collect_builds_snapshot(self):
        from dartlab.engines.gather import Gather

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "closePrice": "200,000",
            "per": "12.50",
            "pbr": "1.30",
            "high52wPrice": "250,000",
            "low52wPrice": "150,000",
        }
        mock_client.get.return_value = mock_resp

        g = Gather(client=mock_client)
        snapshot = g.collect("005930")

        assert snapshot.stock_code == "005930"
        assert len(snapshot.sources_available) > 0
        assert snapshot.collected_at != ""

    def test_collect_caches_result(self):
        from dartlab.engines.gather import Gather

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"closePrice": "100000"}
        mock_client.get.return_value = mock_resp

        g = Gather(client=mock_client)

        snap1 = g.collect("005930")
        snap2 = g.collect("005930")  # 캐시 히트

        assert snap1 is snap2

    def test_collect_graceful_degradation(self):
        """소스 실패 시 → 빈 결과지만 스냅샷은 정상 생성."""
        from dartlab.engines.gather import Gather
        from dartlab.engines.gather.types import SourceUnavailableError

        def mock_get(url, **kwargs):
            if "basic" in url:
                resp = MagicMock()
                resp.json.return_value = {"closePrice": "200000"}
                return resp
            raise SourceUnavailableError("mock failure")

        mock_client = MagicMock()
        mock_client.get.side_effect = mock_get

        g = Gather(client=mock_client)
        snapshot = g.collect("005930")

        assert snapshot.stock_code == "005930"
        # price는 성공, consensus는 None
        assert snapshot.price is not None
        assert snapshot.price.current == 200000
        assert snapshot.consensus is None

    def test_price_fallback(self):
        """price() — 개별 조회."""
        from dartlab.engines.gather import Gather

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "closePrice": "200,000",
            "per": "12.50",
        }
        mock_client.get.return_value = mock_resp

        g = Gather(client=mock_client)
        price = g.price("005930")

        assert price is not None
        assert price.current == 200000

    def test_invalidate(self):
        from dartlab.engines.gather import Gather

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"closePrice": "100000"}
        mock_client.get.return_value = mock_resp

        g = Gather(client=mock_client)
        g.collect("005930")
        g.invalidate("005930")
        # 캐시 무효화 후 재수집
        snap = g.collect("005930")
        assert snap.stock_code == "005930"
