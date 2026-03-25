"""Gather 엔진 — 통합 멀티소스 비동기 병렬 수집.

Usage::

    from dartlab.engines.gather import Gather

    g = Gather()
    g.price("005930")              # OHLCV 시계열 (기본 1년)
    g.price("005930", snapshot=True)  # PriceSnapshot (현재가)
    g.flow("005930")               # 수급 시계열
    g.macro()                      # 주요 거시지표 wide DataFrame
    g.macro("CPI")                 # 단일 지표 시계열

    snap = g.collect("005930")     # 전체 병렬 수집 → GatherSnapshot

모든 공개 API는 동기 시그니처 유지. 내부적으로 asyncio 병렬 실행.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from . import consensus as _consensus
from . import flow as _flow
from . import history as _history
from . import news as _news
from . import price as _price
from .cache import GatherCache
from .domains import load_domain
from .http import GatherHttpClient, run_async
from .market_config import get_market_config
from .types import (
    ConsensusData,
    FlowData,
    GatherResult,
    GatherSnapshot,
    MarketSnapshot,
    NewsItem,
    PeerData,
    PriceSnapshot,
    RevenueConsensus,
    SourceUnavailableError,
)

log = logging.getLogger(__name__)


class Gather:
    """통합 멀티소스 수집 엔진.

    - 개별 조회: price(), consensus(), flow() — fallback 체인
    - 전체 수집: collect() — 도메인별 asyncio.gather 병렬
    - 캐시: TTL 기반 데이터 유형별 자동 만료
    """

    def __init__(self, client: GatherHttpClient | None = None) -> None:
        self._client = client or GatherHttpClient()
        self._cache = GatherCache()
        self._owns_client = client is None

    # ── 개별 조회 (fallback 체인) ──

    def price(
        self,
        stock_code: str,
        *,
        market: str = "KR",
        start: str | None = None,
        end: str | None = None,
        snapshot: bool = False,
    ) -> "pl.DataFrame | PriceSnapshot | None":
        """주가 시계열 (기본) 또는 스냅샷.

        기본: 최근 1년 OHLCV DataFrame (date, open, high, low, close, volume).
        snapshot=True: 현재가 스냅샷 (PriceSnapshot).
        """
        if snapshot:
            return self._priceSnapshot(stock_code, market=market)
        from datetime import date, timedelta

        if start is None:
            end = end or date.today().isoformat()
            start = (date.today() - timedelta(days=365)).isoformat()
        elif end is None:
            end = date.today().isoformat()
        return self.history(stock_code, start=start, end=end, market=market)

    def _priceSnapshot(self, stock_code: str, *, market: str = "KR") -> PriceSnapshot | None:
        """현재가 스냅샷 — naver → yahoo_direct → yahoo fallback."""
        cached = self._cache.get_typed(stock_code, "price")
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = run_async(_price.fetch(stock_code, market=market, client=self._client))
        if result:
            self._cache.put_typed(stock_code, "price", result)
        return result

    def consensus(self, stock_code: str, *, market: str = "KR") -> ConsensusData | None:
        """컨센서스 — KR: naver→yahoo, US: yahoo."""
        cache_key = f"{stock_code}:{market}"
        cached = self._cache.get_typed(cache_key, "consensus")
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = run_async(_consensus.fetch(stock_code, market=market, client=self._client))
        if result:
            self._cache.put_typed(cache_key, "consensus", result)
        return result

    def flow(self, stock_code: str, *, market: str = "KR") -> "pl.DataFrame | None":
        """수급 시계열 — KR 전용 (naver). DataFrame (date, foreignNet, institutionNet, individualNet, foreignHoldingRatio)."""
        import polars as pl

        if market != "KR":
            return None
        cache_key = f"{stock_code}:flow_series"
        cached = self._cache.get_typed(cache_key, "flow")
        if cached is not None:
            return cached  # type: ignore[return-value]
        raw = run_async(_flow.fetch(stock_code, market=market, client=self._client))
        if not raw:
            return None
        df = pl.DataFrame(raw)
        if "date" in df.columns and df["date"].dtype == pl.Utf8:
            df = df.with_columns(pl.col("date").str.to_date("%Y%m%d").alias("date"))
        self._cache.put_typed(cache_key, "flow", df)
        return df

    def _flowSnapshot(self, stock_code: str, *, market: str = "KR") -> FlowData | None:
        """수급 스냅샷 (GatherSnapshot 내부용)."""
        df = self.flow(stock_code, market=market)
        if df is None or df.is_empty():
            return None
        row = df.row(0, named=True)
        return FlowData(
            foreign_net=row.get("foreignNet") or 0.0,
            institution_net=row.get("institutionNet") or 0.0,
            foreign_holding_ratio=row.get("foreignHoldingRatio") or 0.0,
            source="naver",
        )

    def revenue_consensus(
        self,
        stock_code: str,
        *,
        market: str = "KR",
    ) -> list[RevenueConsensus]:
        """매출/이익 컨센서스 — KR: 네이버, US: Yahoo quoteSummary."""
        cache_key = f"{stock_code}_{market}"
        cached = self._cache.get_typed(cache_key, "revenue_consensus")
        if cached is not None:
            return cached  # type: ignore[return-value]
        try:
            if market == "KR":
                module = load_domain("naver")
                result = run_async(module.fetch_revenue_consensus(stock_code, self._client))
            else:
                module = load_domain("yahoo_direct")
                result = run_async(
                    module.fetch_revenue_consensus(
                        stock_code,
                        self._client,
                        market=market,
                    )
                )
        except (SourceUnavailableError, ImportError, OSError, AttributeError) as exc:
            log.warning("revenue_consensus 실패 (%s, %s): %s", stock_code, market, exc)
            result = []
        if result:
            self._cache.put_typed(cache_key, "revenue_consensus", result)
        return result

    def history(
        self,
        stock_code: str,
        *,
        start: str,
        end: str,
        market: str = "KR",
    ) -> "pl.DataFrame":
        """히스토리 OHLCV DataFrame — fallback 체인 (naver(KR) → yahoo_direct → fmp → yahoo)."""
        import polars as pl

        cache_key = f"{stock_code}:history:{start}:{end}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        raw = run_async(
            _history.fetch(
                stock_code,
                start=start,
                end=end,
                market=market,
                client=self._client,
            )
        )
        if not raw:
            return pl.DataFrame()
        df = pl.DataFrame(raw)
        if "date" in df.columns and df["date"].dtype == pl.Utf8:
            df = df.with_columns(pl.col("date").str.to_date("%Y-%m-%d").alias("date"))
        from .cache import TTL_HISTORY

        self._cache.put(cache_key, df, TTL_HISTORY)
        return df

    def news(self, query: str, *, market: str = "KR", days: int = 30) -> "pl.DataFrame":
        """뉴스 — Google News RSS, 캐시/circuit breaker 적용."""
        import polars as pl

        cache_key = f"{query}:{market}:news"
        cached = self._cache.get_typed(cache_key, "news")
        if cached is not None:
            return cached  # type: ignore[return-value]
        items = run_async(_news._fetchAsync(query, market=market, days=days, client=self._client))
        df = _news.toDataFrame(items)
        if not df.is_empty():
            self._cache.put_typed(cache_key, "news", df)
        return df

    def dividends(self, stock_code: str, *, market: str = "KR") -> list[dict]:
        """배당 이력 — yahoo_direct → fmp fallback."""
        cache_key = f"{stock_code}:{market}:dividends"
        cached = self._cache.get_typed(cache_key, "dividends")
        if cached is not None:
            return cached  # type: ignore[return-value]
        from .domains import DIVIDENDS_FALLBACK
        from .resilience import circuit_breaker as _cb

        for source in DIVIDENDS_FALLBACK:
            if _cb.is_open(source):
                continue
            try:
                module = load_domain(source)
                if not hasattr(module, "fetchDividends"):
                    continue
                result = run_async(module.fetchDividends(stock_code, self._client, market=market))
                if result:
                    _cb.record_success(source)
                    self._cache.put_typed(cache_key, "dividends", result)
                    return result
            except (SourceUnavailableError, ImportError, OSError, AttributeError) as exc:
                _cb.record_failure(source)
                log.warning("dividends %s 실패 (%s): %s", source, stock_code, exc)
                continue
        return []

    def splits(self, stock_code: str, *, market: str = "KR") -> list[dict]:
        """분할 이력 — yahoo_direct → fmp fallback."""
        cache_key = f"{stock_code}:{market}:splits"
        cached = self._cache.get_typed(cache_key, "splits")
        if cached is not None:
            return cached  # type: ignore[return-value]
        from .domains import DIVIDENDS_FALLBACK
        from .resilience import circuit_breaker as _cb

        for source in DIVIDENDS_FALLBACK:
            if _cb.is_open(source):
                continue
            try:
                module = load_domain(source)
                if not hasattr(module, "fetchSplits"):
                    continue
                result = run_async(module.fetchSplits(stock_code, self._client, market=market))
                if result:
                    _cb.record_success(source)
                    self._cache.put_typed(cache_key, "splits", result)
                    return result
            except (SourceUnavailableError, ImportError, OSError, AttributeError) as exc:
                _cb.record_failure(source)
                log.warning("splits %s 실패 (%s): %s", source, stock_code, exc)
                continue
        return []

    # ── 거시지표 (eddmpython 검증 목록) ──

    _KNOWN_MARKETS = {"KR", "US"}

    # eddmpython PRIORITY_INDICATORS (12개)
    _MACRO_KR = [
        "CPI", "BASE_RATE", "USDKRW", "M2", "CLI", "CCI", "CSI",
        "IPI", "MANUFACTURING", "TRADE", "HOUSE_PRICE", "APT_PRICE",
    ]

    # eddmpython fred/config.py INDICATORS (24개)
    _MACRO_US = [
        "GDP", "CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE", "UNRATE",
        "FEDFUNDS", "DGS10", "M2SL", "TB3MS", "SP500", "VIXCLS", "AAA",
        "HOUST", "CSUSHPISA", "INDPRO", "PAYEMS", "RSAFS",
        "CES0500000003", "ICSA", "USSLIND", "UMCSENT",
        "DRTSCILM", "DTWEXBGS", "DCOILWTICO",
    ]

    def macro(
        self,
        market: str = "KR",
        indicator: str | None = None,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> "pl.DataFrame | None":
        """거시 지표 시계열.

        인자 없으면 주요 지표 전체를 wide DataFrame으로 반환.
        지표 지정 시 해당 지표만 (date, value) 반환.

        Example::

            g.macro()                 # KR 전체 지표 wide DF
            g.macro("US")             # US 전체 지표 wide DF
            g.macro("CPI")            # CPI (자동 KR 감지)
            g.macro("FEDFUNDS")       # 연방기금금리 (자동 US 감지)
            g.macro("KR", "CPI")      # 명시적 KR + CPI
            g.macro("US", "SP500")    # 명시적 US + S&P500
        """
        # 스마트 라우팅: market 위치에 지표 코드가 온 경우
        if market not in self._KNOWN_MARKETS:
            indicator = market
            market = self._detectMarket(indicator)
        if market == "KR":
            return self._macroKR(indicator, start=start, end=end)
        return self._macroUS(indicator, start=start, end=end)

    def _detectMarket(self, indicator: str) -> str:
        """지표 코드로 market 자동 감지."""
        try:
            from dartlab.engines.gather.ecos.catalog import getEntry
            if getEntry(indicator):
                return "KR"
        except ImportError:
            pass
        return "US"

    def _macroKR(self, indicator: str | None, *, start: str | None, end: str | None):
        """KR 거시지표 — ECOS."""
        try:
            from dartlab.engines.gather.ecos import Ecos
            from dartlab.engines.gather.ecos.types import EcosError
        except ImportError:
            log.debug("ecos 모듈 없음 — KR macro 수집 생략")
            return None
        try:
            ecos = Ecos()
        except EcosError:
            from dartlab.core.env import promptAndSave

            key = promptAndSave(
                "ECOS_API_KEY",
                label="한국은행 ECOS API 키가 필요합니다.",
                guide="무료 발급: https://ecos.bok.or.kr/api/#/",
            )
            if not key:
                return None
            ecos = Ecos(apiKey=key)
        kwargs: dict = {}
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end
        try:
            if indicator:
                return ecos.series(indicator, **kwargs)
            return ecos.compare(self._MACRO_KR, **kwargs)
        except (KeyError, ValueError, OSError, EcosError) as exc:
            log.warning("macro KR 실패: %s", exc)
            return None

    def _macroUS(self, indicator: str | None, *, start: str | None, end: str | None):
        """US 거시지표 — FRED."""
        try:
            from dartlab.engines.gather.fred import Fred
            from dartlab.engines.gather.fred.types import FredError
        except ImportError:
            log.debug("fred 모듈 없음 — US macro 수집 생략")
            return None
        try:
            fred = Fred()
        except FredError:
            from dartlab.core.env import promptAndSave

            key = promptAndSave(
                "FRED_API_KEY",
                label="FRED API 키가 필요합니다.",
                guide="무료 발급: https://fred.stlouisfed.org/docs/api/api_key.html",
            )
            if not key:
                return None
            fred = Fred(api_key=key)
        kwargs: dict = {}
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end
        try:
            if indicator:
                return fred.series(indicator, **kwargs)
            return fred.compare(self._MACRO_US, **kwargs)
        except (KeyError, ValueError, OSError, FredError) as exc:
            log.warning("macro US 실패: %s", exc)
            return None

    # ── 전체 병렬 수집 ──

    def collect(self, stock_code: str, *, market: str = "KR") -> GatherSnapshot:
        """모든 도메인에서 병렬 수집 → GatherSnapshot.

        각 도메인(naver, yahoo, fmp 등)을 asyncio.gather()로 동시 호출.
        개별 도메인 실패는 격리 — 나머지 결과로 스냅샷 생성.
        """
        cached = self._cache.get_typed(stock_code, "snapshot")
        if cached is not None:
            return cached  # type: ignore[return-value]

        snapshot = run_async(self._collect_async(stock_code, market))
        self._cache.put_typed(stock_code, "snapshot", snapshot)
        return snapshot

    async def _collect_async(self, stock_code: str, market: str) -> GatherSnapshot:
        """내부 async 수집 — 도메인별 + 뉴스 병렬, 10초 타임아웃."""
        config = get_market_config(market)
        domains = list(dict.fromkeys(config.fallback_chain))  # 순서 유지 중복 제거

        domainTasks = [self._fetch_domain_async(name, stock_code, market) for name in domains]
        newsTask = _news._fetchAsync(stock_code, market=market, days=7, client=self._client)

        try:
            allResults = await asyncio.wait_for(
                asyncio.gather(*domainTasks, newsTask, return_exceptions=True),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            log.warning("collect 10초 타임아웃 — 부분 결과 사용")
            allResults = [GatherResult(domain=d, error="timeout") for d in domains] + [[]]

        domainResults = allResults[: len(domains)]
        newsResult = allResults[len(domains)]

        results: dict[str, GatherResult] = {}
        for name, raw in zip(domains, domainResults):
            if isinstance(raw, BaseException):
                log.warning("도메인 %s 수집 실패: %s", name, raw)
                results[name] = GatherResult(domain=name, error=str(raw))
            else:
                results[name] = raw

        newsItems: list = []
        if isinstance(newsResult, list):
            newsItems = newsResult

        return GatherSnapshot(
            stock_code=stock_code,
            results=results,
            collected_at=datetime.now(timezone.utc).isoformat(),
            _news=newsItems,
        )

    async def _fetch_domain_async(self, domain_name: str, stock_code: str, market: str) -> GatherResult:
        """단일 도메인에서 모든 데이터 수집 (async)."""
        module = load_domain(domain_name)
        # fetch_all이 있는 도메인 (naver, yahoo)
        if hasattr(module, "fetch_all"):
            if domain_name == "naver":
                return await module.fetch_all(stock_code, self._client)
            return await module.fetch_all(stock_code, self._client, market=market)
        # fetch_price만 있는 도메인 (yahoo_direct, fmp)
        price = None
        if hasattr(module, "fetch_price"):
            price = await module.fetch_price(stock_code, self._client, market=market)
        return GatherResult(domain=domain_name, price=price)

    def invalidate(self, stock_code: str) -> None:
        """특정 종목의 캐시 무효화."""
        self._cache.invalidate(stock_code)

    def close(self) -> None:
        """리소스 정리."""
        if self._owns_client:
            run_async(self._client.close())

    def __repr__(self) -> str:
        return f"Gather(cache={self._cache})"


# ── 모듈 레벨 싱글턴 — 캐시/클라이언트 재사용 ──

_defaultGather: Gather | None = None


def getDefaultGather() -> Gather:
    """Gather 싱글턴 — 같은 세션 내 캐시/HTTP 클라이언트 재사용."""
    global _defaultGather
    if _defaultGather is None:
        _defaultGather = Gather()
    return _defaultGather


__all__ = [
    "Gather",
    "getDefaultGather",
    "GatherSnapshot",
    "MarketSnapshot",
    "NewsItem",
    "PeerData",
    "PriceSnapshot",
    "ConsensusData",
    "FlowData",
    "GatherResult",
    "RevenueConsensus",
]
