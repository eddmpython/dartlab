"""Gather 엔진 단위 테스트 — cache, http, naver source, facade."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from dartlab.gather.infra.cache import GatherCache
from dartlab.gather.infra.http import GatherHttpClient, _AsyncRateLimiter
from dartlab.gather.types import (
    FlowData,
    GatherResult,
    GatherSnapshot,
    MarketSnapshot,
    PeerData,
    PriceSnapshot,
)

pytestmark = pytest.mark.integration

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
        cache.put("key1", "value1", ttl=1)
        # 수동으로 만료시킴 (sleep 대신 정확한 제어)
        cache._store["key1"].expires_at = time.monotonic() - 1.0
        assert cache.get("key1") is None

    def test_max_entries_eviction(self):
        cache = GatherCache(maxEntries=3)
        cache.put("a", 1, ttl=60)
        cache.put("b", 2, ttl=60)
        cache.put("c", 3, ttl=60)
        cache.put("d", 4, ttl=60)  # a 제거됨
        assert cache.get("a") is None
        assert cache.get("d") == 4
        assert cache.size == 3

    def test_lru_access_order(self):
        cache = GatherCache(maxEntries=3)
        cache.put("a", 1, ttl=60)
        cache.put("b", 2, ttl=60)
        cache.put("c", 3, ttl=60)
        cache.get("a")  # a 접근 → LRU 순서 갱신
        cache.put("d", 4, ttl=60)  # b 제거됨
        assert cache.get("a") == 1
        assert cache.get("b") is None

    def test_typed_put_and_get(self):
        cache = GatherCache()
        cache.putTyped("005930", "flow", {"foreign_net": -2500000})
        result = cache.getTyped("005930", "flow")
        assert result == {"foreign_net": -2500000}

    def test_invalidate(self):
        cache = GatherCache()
        cache.putTyped("005930", "flow", {"foreign_net": -2500000})
        cache.putTyped("005930", "price", {"current": 200000})
        cache.putTyped("000660", "flow", {"foreign_net": 1200000})
        cache.invalidate("005930")
        assert cache.getTyped("005930", "flow") is None
        assert cache.getTyped("005930", "price") is None
        assert cache.getTyped("000660", "flow") is not None

    def test_clear(self):
        cache = GatherCache()
        cache.put("a", 1, ttl=60)
        cache.put("b", 2, ttl=60)
        cache.clear()
        assert cache.size == 0

    def test_repr(self):
        cache = GatherCache(maxEntries=100)
        assert "GatherCache" in repr(cache)


# ══════════════════════════════════════
# HTTP 클라이언트 테스트
# ══════════════════════════════════════


class TestAsyncRateLimiter:
    """Async rate limiter 기본 동작."""

    def test_acquire_within_limit(self):
        limiter = _AsyncRateLimiter("test.com", rpm=60)

        async def run():
            for _ in range(5):
                await limiter.acquire()

        asyncio.run(run())

    def test_domain_stored(self):
        limiter = _AsyncRateLimiter("example.com", rpm=30)
        assert limiter._domain == "example.com"
        assert limiter._rpm == 30


class TestGatherHttpClient:
    """GatherHttpClient 기본 동작."""

    def test_close(self):
        from dartlab.gather.infra.http import runAsync

        client = GatherHttpClient()
        runAsync(client.close())  # 에러 없이 종료


# ══════════════════════════════════════
# 데이터 타입 테스트
# ══════════════════════════════════════


class TestDataTypes:
    """데이터 타입 repr + 기본값."""

    def test_gather_result_has_data_distinguishes_error_only_result(self):
        """오류 문자열만 있는 결과는 실제 데이터가 아니고, 값 하나가 있으면 데이터다."""
        assert not GatherResult(domain="naver", error="source down").hasData
        assert GatherResult(domain="naver", sector_per=0.0).hasData

    def test_partial_source_is_both_available_and_failed(self):
        """일부 축 성공과 일부 축 실패를 서로 지우지 않고 양쪽 진단에 보존한다."""
        snap = GatherSnapshot(
            results={
                "naver": GatherResult(
                    domain="naver",
                    price=PriceSnapshot(current=100.0),
                    error="flow source down",
                )
            }
        )

        assert snap.sourcesAvailable == ["naver"]
        assert snap.sourcesFailed == ["naver"]

    def test_price_snapshot_repr(self):
        p = PriceSnapshot(current=200000, per=12.5, pbr=1.3, source="naver")
        r = repr(p)
        assert "200,000" in r
        assert "naver" in r

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
            stockCode="005930",
            currentPrice=200000,
            multiples={"per": 12.5, "pbr": 1.3},
            sourcesAvailable=["naver"],
            collected_at="2026-03-22T00:00:00",
        )
        r = repr(snap)
        assert "005930" in r
        assert "200,000" in r

    def test_market_snapshot_defaults(self):
        snap = MarketSnapshot()
        assert snap.stockCode == ""
        assert snap.currentPrice == 0.0
        assert snap.multiples == {}

    def test_gather_snapshot_properties(self):
        snap = GatherSnapshot(
            stockCode="005930",
            results={
                "naver": GatherResult(
                    domain="naver",
                    price=PriceSnapshot(current=200000, source="naver"),
                    flow=FlowData(foreign_net=-1000, source="naver"),
                    sector_per=15.0,
                ),
            },
        )
        assert snap.price is not None
        assert snap.price.current == 200000
        assert snap.flow is not None
        assert snap.sourcesAvailable == ["naver"]

    def test_gather_snapshot_to_market_snapshot(self):
        snap = GatherSnapshot(
            stockCode="005930",
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
                    flow=FlowData(foreign_net=-2500000, institution_net=1200000, foreign_holding_ratio=55.3),
                    sector_per=15.0,
                ),
            },
            collected_at="2026-03-22T00:00:00",
        )
        ms = snap.toMarketSnapshot()
        assert ms.stockCode == "005930"
        assert ms.currentPrice == 200000
        assert ms.multiples["per"] == 12.5
        assert ms.multiples["sector_per"] == 15.0
        assert ms.price_range_52w == (150000, 250000)
        assert ms.supply_demand["foreign_net"] == -2500000


# ══════════════════════════════════════
# Naver Source 테스트 (mock) — async
# ══════════════════════════════════════


def _make_async_client(json_data):
    """async mock client 생성 — client.get()이 코루틴 반환."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = json_data
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    return mock_client


class TestNaverSource:
    """네이버 소스 — mock HTTP 응답 (async)."""

    def test_fetch_price_success(self):
        from dartlab.gather.domains.naver import fetchPrice

        mock_client = _make_async_client(
            {
                "closePrice": "200,000",
                "totalInfos": [
                    {"code": "per", "value": "12.50배"},
                    {"code": "pbr", "value": "1.30배"},
                    {"code": "marketValue", "value": "3,564,000"},
                    {"code": "highPriceOf52Weeks", "value": "250,000원"},
                    {"code": "lowPriceOf52Weeks", "value": "150,000원"},
                    {"code": "dividendYieldRatio", "value": "2.10%"},
                ],
            }
        )

        result = asyncio.run(fetchPrice("005930", mock_client))
        assert result is not None
        assert result.current == 200000
        assert result.per == 12.5
        assert result.pbr == 1.3
        assert result.high_52w == 250000

    def test_fetch_flow_success(self):
        from dartlab.gather.domains.naver import fetchFlow

        mock_client = _make_async_client(
            {
                "dealTrendInfos": [
                    {
                        "bizdate": "20260326",
                        "foreignerPureBuyQuant": "-2,500,000",
                        "organPureBuyQuant": "1,200,000",
                        "individualPureBuyQuant": "300,000",
                        "foreignerHoldRatio": "55.30",
                    },
                ],
            }
        )

        result = asyncio.run(fetchFlow("005930", mock_client))
        assert result is not None
        assert isinstance(result, list)
        assert result[0]["foreignHoldingRatio"] == 55.3
        assert result[0]["foreignNet"] == -2500000.0
        assert result[0]["institutionNet"] == 1200000.0

    def test_clean_number_edge_cases(self):
        from dartlab.gather.domains.naver import _cleanNumber

        assert _cleanNumber("1,234,567") == 1234567
        assert _cleanNumber("+500") == 500
        assert _cleanNumber("-100") == -100
        assert _cleanNumber("N/A") is None
        assert _cleanNumber("") is None
        assert _cleanNumber(None) is None


# ══════════════════════════════════════
# Gather Facade 테스트 (mock) — async client
# ══════════════════════════════════════


def _make_facade_client(json_data):
    """Gather facade용 async mock client."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = json_data
    mock_client = MagicMock(spec=GatherHttpClient)
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.close = AsyncMock()
    return mock_client


class TestGatherFacade:
    """Gather facade — mock 기반 통합."""

    def test_collect_builds_snapshot(self):
        from dartlab.gather import Gather

        mock_client = _make_facade_client(
            {
                "closePrice": "200,000",
                "totalInfos": [
                    {"code": "per", "value": "12.50배"},
                    {"code": "pbr", "value": "1.30배"},
                    {"code": "highPriceOf52Weeks", "value": "250,000원"},
                    {"code": "lowPriceOf52Weeks", "value": "150,000원"},
                ],
            }
        )

        g = Gather(client=mock_client)

        # naver fetch_all만 mock — yahoo 등 실제 네트워크 차단
        async def _mock_domain(self_inner, domainName, stockCode, market):
            if domainName == "naver":
                from dartlab.gather.domains import naver

                return await naver.fetchAll(stockCode, self_inner._client)
            return GatherResult(domain=domainName)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(Gather, "_fetchDomainAsync", _mock_domain)
            snapshot = g.collect("005930")

        assert snapshot.stockCode == "005930"
        assert len(snapshot.sourcesAvailable) > 0
        assert snapshot.collected_at != ""

    def test_collect_caches_result(self):
        from dartlab.gather import Gather

        mock_client = _make_facade_client({"closePrice": "100000"})

        g = Gather(client=mock_client)

        snap1 = g.collect("005930")
        snap2 = g.collect("005930")  # 캐시 히트

        assert snap1 is snap2

    def test_collect_graceful_degradation(self):
        """소스 실패 시 → 빈 결과지만 스냅샷은 정상 생성."""
        from dartlab.gather import Gather
        from dartlab.gather.types import SourceUnavailableError

        async def mock_get(url, **kwargs):
            if "basic" in url:
                resp = MagicMock()
                resp.json.return_value = {"closePrice": "200000"}
                return resp
            if "integration" in url:
                resp = MagicMock()
                resp.json.return_value = {"totalInfos": []}
                return resp
            raise SourceUnavailableError("mock failure")

        mock_client = MagicMock(spec=GatherHttpClient)
        mock_client.get = AsyncMock(side_effect=mock_get)
        mock_client.close = AsyncMock()

        g = Gather(client=mock_client)

        # naver fetch_all만 mock — yahoo 등 실제 네트워크 차단
        async def _mock_domain(self_inner, domainName, stockCode, market):
            if domainName == "naver":
                from dartlab.gather.domains import naver

                return await naver.fetchAll(stockCode, self_inner._client)
            return GatherResult(domain=domainName)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(Gather, "_fetchDomainAsync", _mock_domain)
            snapshot = g.collect("005930")

        assert snapshot.stockCode == "005930"
        # price는 성공 (naver basic URL), 다른 도메인은 mock_get 에러로 빈 결과
        assert snapshot.price is not None
        assert snapshot.price.current == 200000

    def test_price_fallback(self):
        """price(snapshot=True) — 스냅샷 개별 조회."""
        from dartlab.gather import Gather

        mock_client = _make_facade_client(
            {
                "closePrice": "200,000",
                "totalInfos": [{"code": "per", "value": "12.50배"}],
            }
        )

        g = Gather(client=mock_client)
        price = g.price("005930", snapshot=True)

        assert price is not None
        assert price.current == 200000

    def test_invalidate(self):
        from dartlab.gather import Gather

        mock_client = _make_facade_client({"closePrice": "100000"})

        g = Gather(client=mock_client)
        g.collect("005930")
        g.invalidate("005930")
        # 캐시 무효화 후 재수집
        snap = g.collect("005930")
        assert snap.stockCode == "005930"
