"""Gather 엔진 — 통합 멀티소스 비동기 병렬 수집.

Usage::

    from dartlab.gather import Gather

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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

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
    """통합 멀티소스 비동기 병렬 수집 엔진.

    Capabilities:
        - 개별 조회: price(), flow(), history(), news(), macro() 등 — fallback 체인
        - 전체 수집: collect() — 도메인별 asyncio.gather 병렬
        - 캐시: TTL 기반 데이터 유형별 자동 만료 (GatherCache)
        - circuit breaker: 실패 도메인 자동 격리/복구
        - 시장 지원: KR (Naver/ECOS), US (Yahoo/FRED/FMP)

    Guide:
        - "주가 보여줘" -> g.price("005930")
        - "현재가 알려줘" -> g.price("005930", snapshot=True)
        - "외국인 매매 동향" -> g.flow("005930")
        - "거시지표 전체" -> g.macro() 또는 g.macro("US")
        - "금리 추이" -> g.macro("FEDFUNDS") (자동 US 감지)
        - "뉴스 검색" -> g.news("삼성전자")
        - "전부 한번에" -> g.collect("005930") (병렬 수집 스냅샷)
        - 공개 API 진입점은 dartlab.gather(). 내부 엔진은 이 클래스.

    SeeAlso:
        - GatherEntry: dartlab.gather() 공개 API (3단계 패턴)
        - scan: 재무 기반 전종목 횡단분석
        - Company: 개별 종목 공시/재무 데이터

    Args:
        client: GatherHttpClient 인스턴스. None이면 내부 생성.

    Returns:
        Gather 인스턴스.

    Requires:
        없음 (API 키는 macro() 호출 시 필요).

    Example::

        from dartlab.gather import Gather, getDefaultGather

        g = getDefaultGather()           # 싱글턴 (권장)
        g.price("005930")               # 삼성전자 1년 OHLCV
        g.flow("005930")                # 수급 시계열
        g.macro()                       # KR 거시지표 전체
        snap = g.collect("005930")      # 전체 병렬 수집
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
        """OHLCV 주가 시계열 조회.

        Capabilities:
            - KR: Naver 금융 (기본 1년)
            - US: Yahoo Finance (기본 1년)
            - OHLCV + 거래량 DataFrame
            - snapshot=True 시 현재가 PriceSnapshot 반환
            - 자동 fallback 체인 (Naver -> Yahoo -> FMP)
            - TTL 캐시 (5분)

        Args:
            stock_code: 종목코드 ("005930") 또는 티커 ("AAPL").
            market: "KR" 또는 "US". 기본 "KR".
            start: 시작일 (YYYY-MM-DD). None이면 1년 전.
            end: 종료일. None이면 오늘.
            snapshot: True면 PriceSnapshot (현재가) 반환.

        Returns:
            pl.DataFrame — date, open, high, low, close, volume 컬럼.
            snapshot=True 시 PriceSnapshot | None.

        Requires:
            없음 (공개 API).

        Example::

            g = getDefaultGather()
            g.price("005930")                    # 삼성전자 1년
            g.price("AAPL", market="US")         # Apple 1년
            g.price("005930", snapshot=True)     # 현재가 스냅샷
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
        """애널리스트 컨센서스 (목표가/투자의견) 조회.

        Capabilities:
            - KR: Naver -> Yahoo fallback
            - US: Yahoo Finance
            - 목표가, 투자의견, 애널리스트 수
            - TTL 캐시

        Args:
            stock_code: 종목코드 ("005930") 또는 티커 ("AAPL").
            market: "KR" 또는 "US". 기본 "KR".

        Returns:
            ConsensusData | None — 목표가/투자의견 데이터.

        Requires:
            없음 (공개 API).

        Example::

            g = getDefaultGather()
            g.consensus("005930")              # 삼성전자 컨센서스
            g.consensus("AAPL", market="US")   # Apple 컨센서스
        """
        cache_key = f"{stock_code}:{market}"
        cached = self._cache.get_typed(cache_key, "consensus")
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = run_async(_consensus.fetch(stock_code, market=market, client=self._client))
        if result:
            self._cache.put_typed(cache_key, "consensus", result)
        return result

    def flow(self, stock_code: str, *, market: str = "KR") -> "pl.DataFrame | None":
        """투자자별 수급 시계열 조회 (KR 전용).

        Capabilities:
            - KR 전용 (Naver 금융)
            - 외국인/기관/개인 순매수 + 외국인 보유비율
            - 일별 시계열 DataFrame
            - TTL 캐시

        Args:
            stock_code: 종목코드 ("005930").
            market: "KR"만 지원. "US"이면 None 반환.

        Returns:
            pl.DataFrame | None — date, foreignNet, institutionNet,
            individualNet, foreignHoldingRatio 컬럼. KR 외 None.

        Requires:
            없음 (공개 API).

        Example::

            g = getDefaultGather()
            g.flow("005930")   # 삼성전자 수급 시계열
        """
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
        """매출/이익 컨센서스 (연간 추정치) 조회.

        Capabilities:
            - KR: 네이버 금융 (연간 매출/영업이익/순이익 추정)
            - US: Yahoo Finance quoteSummary
            - 연도별 RevenueConsensus 리스트
            - TTL 캐시

        Args:
            stock_code: 종목코드 ("005930") 또는 티커 ("AAPL").
            market: "KR" 또는 "US". 기본 "KR".

        Returns:
            list[RevenueConsensus] — 연도별 매출/이익 추정치. 실패 시 빈 리스트.

        Requires:
            없음 (공개 API).

        Example::

            g = getDefaultGather()
            g.revenue_consensus("005930")              # 삼성전자
            g.revenue_consensus("AAPL", market="US")   # Apple
        """
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
        """OHLCV 히스토리 DataFrame 조회 (기간 지정).

        Capabilities:
            - fallback 체인: Naver(KR) -> yahoo_direct -> FMP -> Yahoo
            - date, open, high, low, close, volume 컬럼
            - 자동 날짜 파싱 (문자열 -> pl.Date)
            - TTL 캐시 (TTL_HISTORY)

        Args:
            stock_code: 종목코드 ("005930") 또는 티커 ("AAPL").
            start: 시작일 (YYYY-MM-DD). 필수.
            end: 종료일 (YYYY-MM-DD). 필수.
            market: "KR" 또는 "US". 기본 "KR".

        Returns:
            pl.DataFrame — date, open, high, low, close, volume 컬럼.
            데이터 없으면 빈 DataFrame.

        Requires:
            없음 (공개 API).

        Example::

            g = getDefaultGather()
            g.history("005930", start="2025-01-01", end="2025-12-31")
            g.history("AAPL", start="2025-06-01", end="2025-12-31", market="US")
        """
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
        """뉴스 검색 (Google News RSS).

        Capabilities:
            - Google News RSS 기반 뉴스 수집
            - KR/US 시장별 검색
            - 기간 제한 (기본 30일)
            - circuit breaker + TTL 캐시
            - DataFrame: title, link, published, source 컬럼

        Args:
            query: 검색어 (종목명, 키워드 등).
            market: "KR" 또는 "US". 기본 "KR".
            days: 최근 N일 뉴스. 기본 30.

        Returns:
            pl.DataFrame — title, link, published, source 컬럼.
            결과 없으면 빈 DataFrame.

        Requires:
            없음 (공개 API).

        Example::

            g = getDefaultGather()
            g.news("삼성전자")                # KR 뉴스 30일
            g.news("Apple", market="US")     # US 뉴스 30일
            g.news("반도체", days=7)          # 최근 7일
        """
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
        """배당 이력 조회.

        Capabilities:
            - fallback 체인: yahoo_direct -> FMP
            - 배당일, 배당금, 배당수익률 등
            - circuit breaker 적용
            - TTL 캐시

        Args:
            stock_code: 종목코드 ("005930") 또는 티커 ("AAPL").
            market: "KR" 또는 "US". 기본 "KR".

        Returns:
            list[dict] — 배당 이력 (date, dividend 등). 없으면 빈 리스트.

        Requires:
            없음 (공개 API).

        Example::

            g = getDefaultGather()
            g.dividends("005930")              # 삼성전자 배당 이력
            g.dividends("AAPL", market="US")   # Apple 배당 이력
        """
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
        """액면분할/병합 이력 조회.

        Capabilities:
            - fallback 체인: yahoo_direct -> FMP
            - 분할일, 분할비율 등
            - circuit breaker 적용
            - TTL 캐시

        Args:
            stock_code: 종목코드 ("005930") 또는 티커 ("AAPL").
            market: "KR" 또는 "US". 기본 "KR".

        Returns:
            list[dict] — 분할 이력 (date, ratio 등). 없으면 빈 리스트.

        Requires:
            없음 (공개 API).

        Example::

            g = getDefaultGather()
            g.splits("005930")              # 삼성전자 분할 이력
            g.splits("AAPL", market="US")   # Apple 분할 이력
        """
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
        "CPI",
        "BASE_RATE",
        "USDKRW",
        "M2",
        "CLI",
        "CCI",
        "CSI",
        "IPI",
        "MANUFACTURING",
        "TRADE",
        "HOUSE_PRICE",
        "APT_PRICE",
    ]

    # eddmpython fred/config.py INDICATORS (24개)
    _MACRO_US = [
        "GDP",
        "CPIAUCSL",
        "CPILFESL",
        "PCEPI",
        "PCEPILFE",
        "UNRATE",
        "FEDFUNDS",
        "DGS10",
        "M2SL",
        "TB3MS",
        "SP500",
        "VIXCLS",
        "AAA",
        "HOUST",
        "CSUSHPISA",
        "INDPRO",
        "PAYEMS",
        "RSAFS",
        "CES0500000003",
        "ICSA",
        "USSLIND",
        "UMCSENT",
        "DRTSCILM",
        "DTWEXBGS",
        "DCOILWTICO",
    ]

    def macro(
        self,
        market: str = "KR",
        indicator: str | None = None,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> "pl.DataFrame | None":
        """거시경제 지표 시계열 조회.

        Capabilities:
            - KR: ECOS (한국은행) — CPI, 기준금리, 환율 등 12개 핵심 지표
            - US: FRED — GDP, CPI, 실업률, 연방기금금리 등 24개 핵심 지표
            - 스마트 라우팅: 지표 코드만으로 KR/US 자동 감지
            - 전체 지표: wide DataFrame (date + 각 지표 컬럼)
            - 단일 지표: (date, value) DataFrame

        Args:
            market: "KR" 또는 "US". 지표 코드 직접 전달도 가능 (자동 감지).
            indicator: 지표 코드 ("CPI", "FEDFUNDS" 등). None이면 전체 지표.
            start: 시작일 (YYYY-MM-DD). None이면 기본 기간.
            end: 종료일. None이면 오늘.

        Returns:
            pl.DataFrame | None — wide DataFrame (전체) 또는 (date, value) (단일).

        Requires:
            KR: ECOS_API_KEY (한국은행 무료 발급).
            US: FRED_API_KEY (FRED 무료 발급).

        Example::

            g = getDefaultGather()
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
            from dartlab.gather.ecos.catalog import getEntry

            if getEntry(indicator):
                return "KR"
        except ImportError:
            pass
        return "US"

    def _macroKR(self, indicator: str | None, *, start: str | None, end: str | None):
        """KR 거시지표 — ECOS."""
        try:
            from dartlab.gather.ecos import Ecos
            from dartlab.gather.ecos.types import EcosError
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
                log.info("ECOS_API_KEY 미설정 — KR macro 조회 불가")
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
            from dartlab.gather.fred import Fred
            from dartlab.gather.fred.types import FredError
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
                log.info("FRED_API_KEY 미설정 — US macro 조회 불가")
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
        """전체 도메인 병렬 수집 -> GatherSnapshot.

        Capabilities:
            - asyncio.gather()로 모든 도메인(naver, yahoo, fmp 등) 동시 호출
            - 뉴스도 병렬 수집 (최근 7일)
            - 개별 도메인 실패 격리 — 나머지 결과로 스냅샷 생성
            - 10초 타임아웃 (부분 결과 반환)
            - TTL 캐시

        Args:
            stock_code: 종목코드 ("005930") 또는 티커 ("AAPL").
            market: "KR" 또는 "US". 기본 "KR".

        Returns:
            GatherSnapshot — 도메인별 결과 + 뉴스 + 수집 시각.

        Requires:
            없음 (공개 API).

        Example::

            g = getDefaultGather()
            snap = g.collect("005930")       # 삼성전자 전체 수집
            snap.price                       # PriceSnapshot
            snap.news                        # 뉴스 리스트
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
        """특정 종목의 캐시 무효화.

        Args:
            stock_code: 캐시를 삭제할 종목코드.

        Example::

            g = getDefaultGather()
            g.invalidate("005930")   # 삼성전자 캐시 제거
        """
        self._cache.invalidate(stock_code)

    def close(self) -> None:
        """HTTP 클라이언트 등 리소스 정리."""
        if self._owns_client:
            run_async(self._client.close())

    def __repr__(self) -> str:
        return f"Gather(cache={self._cache})"


# ── 모듈 레벨 싱글턴 — 캐시/클라이언트 재사용 ──

_defaultGather: Gather | None = None


def getDefaultGather() -> Gather:
    """Gather 싱글턴 반환 — 같은 세션 내 캐시/HTTP 클라이언트 재사용.

    Capabilities:
        - 모듈 레벨 싱글턴으로 Gather 인스턴스 관리
        - 캐시/HTTP 클라이언트 세션 간 재사용
        - 첫 호출 시 자동 생성

    Returns:
        Gather — 싱글턴 인스턴스.

    Requires:
        없음.

    Example::

        from dartlab.gather import getDefaultGather

        g = getDefaultGather()
        g.price("005930")
    """
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
