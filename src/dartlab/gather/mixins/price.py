"""Gather price/flow/history/revenueConsensus mixin — 가격·수급·시계열·컨센서스 6 메서드."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

from dartlab.core.polarsUtil import isEmptyDf

from ..infra.http import runAsync
from ..sources import flow as _flow
from ..sources import history as _history
from ..sources import intraday as _intraday
from ..sources import price as _price
from ..types import FlowData, PriceSnapshot, RevenueConsensus, SourceUnavailableError
from .context import GatherMixinContext

log = logging.getLogger(__name__)


def _intervalMinutes(interval: str | None) -> int | None:
    """interval 문자열을 분(int) 으로. 일봉("1d"/None)이면 None.

    ``"1m"``/``"3m"``/``"5m"`` 같은 분봉은 양의 정수, 그 외는 None (일봉 경로).
    """
    if interval in (None, "", "1d", "d", "day", "daily"):
        return None
    token = str(interval).strip().lower()
    if token.endswith("m"):
        token = token[:-1]
    return int(token) if token.isdigit() and int(token) > 0 else None


def _resampleMinutes(df: "pl.DataFrame", minutes: int) -> "pl.DataFrame":
    """1분봉 DataFrame 을 N분봉으로 리샘플 (OHLCV 집계). minutes<=1 이면 그대로."""
    import polars as pl

    if minutes <= 1 or "datetime" not in df.columns or df.height == 0:
        return df
    return (
        df.sort("datetime")
        .group_by_dynamic("datetime", every=f"{minutes}m")
        .agg(
            pl.col("open").first(),
            pl.col("high").max(),
            pl.col("low").min(),
            pl.col("close").last(),
            pl.col("volume").sum(),
        )
        .sort("datetime")
    )


class _GatherPriceMixin(GatherMixinContext):
    """가격·수급·히스토리·컨센서스 메서드 모음 — Gather 클래스 6 메서드."""

    def price(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        start: str | None = None,
        end: str | None = None,
        snapshot: bool = False,
        interval: str = "1d",
    ) -> "pl.DataFrame | PriceSnapshot | None":
        """OHLCV 주가 시계열 조회.

        Capabilities:
            - KR: Naver 금융 (기본 1년)
            - US: Yahoo Finance (기본 1년)
            - OHLCV + 거래량 DataFrame
            - snapshot=True 시 현재가 PriceSnapshot 반환
            - interval="1m"/"3m"/"5m" 시 분봉 (KR Naver, 당일 + 과거 세션 + 휴장일 폴백)
            - 자동 fallback 체인 (Naver -> Yahoo -> FMP)
            - TTL 캐시 (5분, DARTLAB_TTL_PRICE override 가능)

        AIContext:
            - quant/analysis 가 OHLCV 입력으로 소비 — gather → analysis 흐름의 데이터 원천

        Guide:
            ``Gather`` 클래스의 핵심 진입점. 단일 종목/티커의 OHLCV 시계열을
            한 호출로 fetch. snapshot=True 면 PriceSnapshot 단건 (현재가).

        When:
            "주가 추이 보여줘" 같은 사용자 의도 — 단일 종목 OHLCV 필요 시.

        How:
            stockCode + market → fallback chain → DataFrame.
            quant 의 indicator 추가는 별도 ``transforms.indicatorDispatch.addIndicators``.

        Args:
            stock_code: 종목코드 ("005930") 또는 티커 ("AAPL").
            market: "KR" 또는 "US". 기본 "KR".
            start: 시작일 (YYYY-MM-DD). None이면 1년 전. interval 이 분봉이면
                시작 시각 (``"2026-07-03"`` 등), None이면 당일.
            end: 종료일. None이면 오늘.
            snapshot: True면 PriceSnapshot (현재가) 반환.
            interval: ``"1d"`` (기본, 일봉) 또는 분봉 ``"1m"``/``"3m"``/``"5m"``.
                분봉은 KR Naver 전용 (당일 + 과거 세션 + 휴장일 폴백), datetime 컬럼.

        Returns:
            pl.DataFrame. 일봉은 date, 분봉은 datetime + open/high/low/close/volume 컬럼.
            snapshot=True 시 PriceSnapshot | None.

        Requires:
            없음 (공개 API).

        Raises:
            없음 — fallback 체인 내부 예외는 흡수.

        Example::

            g = getDefaultGather()
            g.price("005930")                    # 삼성전자 1년
            g.price("AAPL")                      # Apple 1년 (자동 US 판정)
            g.price("005930", snapshot=True)     # 현재가 스냅샷

        See Also:
            ``flow`` — 외국인/기관 수급 (같은 종목, 다른 axis).
            ``history`` — start/end 명시 시계열.
            ``dartlab.gather.transforms.indicatorDispatch.addIndicators`` — 보조지표.
        """
        # market 자동 감지 (core SSOT)
        from dartlab.core.market import resolveMarket

        market = resolveMarket(stockCode, market)

        if snapshot:
            return self._priceSnapshot(stockCode, market=market)
        if _intervalMinutes(interval) is not None:
            return self._intradayFrame(stockCode, market=market, interval=interval, start=start, end=end)
        from datetime import date, timedelta

        if start is None:
            end = end or date.today().isoformat()
            start = (date.today() - timedelta(days=365)).isoformat()
        elif end is None:
            end = date.today().isoformat()
        return self.history(stockCode, start=start, end=end, market=market)

    def _priceSnapshot(self, stockCode: str, *, market: str = "KR") -> PriceSnapshot | None:
        """현재가 스냅샷 — naver → naver_global fallback.

        Parameters
        ----------
        stock_code : str
            종목코드 ("005930") 또는 티커 ("AAPL").
        market : str
            "KR" 또는 "US". 기본 "KR".

        Returns
        -------
        PriceSnapshot | None
            price : float — 현재가 (원 또는 USD).
            change : float — 전일 대비 변동 (원 또는 USD).
            changePercent : float — 전일 대비 변동률 (%).
            volume : int — 거래량 (주).
            None — 데이터 수집 실패 시.
        """
        import time

        from dartlab.core.market import resolveMarket

        from ..infra.cache import buildCacheSlot
        from ..infra.telemetry import emitGatherFetch

        t0 = time.monotonic()
        cacheHit = False
        market = resolveMarket(stockCode, market)
        cacheSlot = buildCacheSlot("price", market=market)
        try:
            cached = self._cache.getTyped(stockCode, cacheSlot)
            if cached is not None:
                cacheHit = True
                return cached  # type: ignore[return-value]
            result = runAsync(_price.fetch(stockCode, market=market, client=self._client))
            if result:
                self._cache.putTyped(stockCode, cacheSlot, result)
            return result
        finally:
            emitGatherFetch("price", (time.monotonic() - t0) * 1000, cacheHit=cacheHit, market=market)

    def _intradayFrame(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        interval: str = "1m",
        start: str | None = None,
        end: str | None = None,
    ) -> "pl.DataFrame":
        """분봉 OHLCV DataFrame. KR Naver (당일 + 과거 세션 + 휴장일 폴백).

        price(interval="1m"/"3m"/"5m") 의 내부 경로. sources.intraday 로 1분봉을
        받아 datetime 을 파싱하고, 3m/5m 은 group_by_dynamic 로 리샘플한다.

        Parameters
        ----------
        stock_code : str
            종목코드 ("005930").
        market : str
            "KR" 만 지원. 외 시장은 빈 DataFrame.
        interval : str
            "1m"/"3m"/"5m" 등 분봉 단위.
        start : str | None
            시작 시각 ("2026-07-03" 등). None이면 당일.
        end : str | None
            종료 시각. None이면 start 부터 현재까지.

        Returns
        -------
        pl.DataFrame
            datetime, open, high, low, close, volume 컬럼. 없으면 빈 DataFrame.
        """
        import polars as pl

        from ..infra.cache import buildCacheSlot

        minutes = _intervalMinutes(interval) or 1
        cacheSlot = buildCacheSlot("price", market=market, interval=interval, start=start, end=end)
        cached = self._cache.getTyped(stockCode, cacheSlot)
        if cached is not None:
            return cached  # type: ignore[return-value]
        raw = runAsync(
            _intraday.fetch(
                stockCode,
                market=market,
                start=start or "",
                end=end or "",
                client=self._client,
            )
        )
        if not raw:
            return pl.DataFrame()
        df = pl.DataFrame(raw)
        if "datetime" in df.columns and df["datetime"].dtype == pl.Utf8:
            df = df.with_columns(pl.col("datetime").str.to_datetime("%Y-%m-%dT%H:%M:%S").alias("datetime"))
        if minutes > 1:
            df = _resampleMinutes(df, minutes)
        self._cache.putTyped(stockCode, cacheSlot, df)
        return df

    def flow(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        start: str | None = None,
        end: str | None = None,
        limit: int | None = None,
        pageSize: int | None = None,
        sleepSec: float = 0.0,
        marketType: str = "KRX",
        maxPages: int | None = None,
        all: bool = False,
        full: bool = False,
        proxy: str | None = None,
    ) -> "pl.DataFrame | None":
        """투자자별 수급 시계열 조회 (KR 전용).

        Capabilities:
            - KR 전용 (Naver 금융)
            - 외국인/기관/개인 순매수 + 외국인 보유비율
            - 일별 시계열 DataFrame
            - TTL 캐시 (DARTLAB_TTL_FLOW override 가능)

        AIContext:
            - 외국인/기관 매매 동향 — sentiment / 시장 압력 신호로 분석

        Guide:
            US 시장은 Naver 미지원 → None. KR 만 작동.

        When:
            "외국인 매매 동향" 같은 KR 종목 수급 분석 의도 시.

        How:
            stockCode → Naver fetch → date 파싱 → DataFrame.

        Args:
            stock_code: 종목코드 ("005930").
            market: "KR"만 지원. "US"이면 None 반환.
            start/end: 조회 기간. 지정 시 Naver trend 페이지를 과거로 순회.
            limit: 반환 행수 상한.
            pageSize: 호환용 고급 옵션. None이면 내부에서 자동 결정.
            sleepSec: 페이지 호출 사이 대기 시간.
            all/full: True면 가능한 전체 이력을 끝까지 자동 수집.
            proxy: 사용자 제공 HTTP(S) 프록시 URL.

        Returns:
            pl.DataFrame | None — date, foreignNet, institutionNet,
            individualNet, foreignHoldingRatio 컬럼. KR 외 None.

        Requires:
            없음 (공개 API).

        Raises:
            없음 — fallback 체인 내부 예외는 흡수.

        Example::

            import dartlab
            dartlab.gather("flow", "005930")              # 최근 5거래일
            dartlab.gather("flow", "005930", limit=30)    # 최근 30거래일
            dartlab.gather("flow", "005930", all=True)    # 가능한 전체 이력

        See Also:
            ``price`` — 같은 종목의 OHLCV.
            ``ownership`` — 누적 지분 보유 (스냅샷).
        """
        import time

        from dartlab.core.market import resolveMarket

        from ..infra.telemetry import emitGatherFetch

        t0 = time.monotonic()
        cacheHit = False
        market = resolveMarket(stockCode, market)
        import polars as pl

        fullHistory = bool(all or full)

        try:
            if market != "KR":
                return None
            cache_key = (
                f"{stockCode}:flow_series:"
                f"{start or ''}:{end or ''}:{limit or ''}:{pageSize}:{marketType}:{maxPages or ''}:{int(fullHistory)}"
            )
            cached = self._cache.getTyped(cache_key, "flow")
            if cached is not None:
                cacheHit = True
                return cached  # type: ignore[return-value]
            raw = runAsync(
                _flow.fetch(
                    stockCode,
                    market=market,
                    client=self._client,
                    start=start,
                    end=end,
                    limit=limit,
                    pageSize=pageSize,
                    sleepSec=sleepSec,
                    marketType=marketType,
                    maxPages=maxPages,
                    full=fullHistory,
                    proxy=proxy,
                )
            )
            if not raw:
                return None
            df = pl.DataFrame(raw)
            if "date" in df.columns and df["date"].dtype == pl.Utf8:
                df = df.with_columns(pl.col("date").str.to_date("%Y%m%d").alias("date"))
        finally:
            emitGatherFetch("flow", (time.monotonic() - t0) * 1000, cacheHit=cacheHit, market=market)
        self._cache.putTyped(cache_key, "flow", df)
        return df

    def _flowSnapshot(self, stockCode: str, *, market: str = "KR") -> FlowData | None:
        """수급 스냅샷 — flow() 시계열의 최신 행을 FlowData로 변환 (GatherSnapshot 내부용).

        Parameters
        ----------
        stock_code : str
            종목코드 ("005930").
        market : str
            "KR"만 지원. "US"이면 None 반환.

        Returns
        -------
        FlowData | None
            foreign_net : float — 외국인 순매수 (주).
            institution_net : float — 기관 순매수 (주).
            foreign_holding_ratio : float — 외국인 보유비율 (%).
            source : str — 데이터 출처 ("naver").
            None — KR 외 시장이거나 데이터 없을 때.
        """
        df = self.flow(stockCode, market=market)
        if isEmptyDf(df):
            return None
        row = df.row(0, named=True)
        return FlowData(
            foreign_net=row.get("foreignNet") or 0.0,
            institution_net=row.get("institutionNet") or 0.0,
            foreign_holding_ratio=row.get("foreignHoldingRatio") or 0.0,
            source="naver",
        )

    def revenueConsensus(
        self,
        stockCode: str,
        *,
        market: str = "KR",
    ) -> list[RevenueConsensus]:
        """매출/이익 컨센서스 (연간 추정치) 조회.

        Capabilities:
            - KR: 네이버 금융 (연간 매출/영업이익/순이익 추정)
            - US: Yahoo Finance quoteSummary
            - 연도별 RevenueConsensus 리스트
            - TTL 캐시

        AIContext:
            - 미래 컨센서스 fetch — story/analysis 가 future 매출 전망에 사용

        Guide:
            KR 만 본격 지원 (Naver). US 는 빈 리스트 (provider 미연결).

        When:
            매출/이익 컨센서스 시계열 (분석가 추정) 필요 시.

        How:
            stockCode + market → domain fetch → RevenueConsensus 리스트.

        Args:
            stock_code: 종목코드 ("005930") 또는 티커 ("AAPL").
            market: "KR" 또는 "US". 기본 "KR".

        Returns:
            list[RevenueConsensus] — 연도별 매출/이익 추정치. 실패 시 빈 리스트.

        Requires:
            없음 (공개 API).

        Raises:
            없음 — fallback 체인 내부 예외는 흡수.

        Example::

            g = getDefaultGather()
            g.revenue_consensus("005930")              # 삼성전자
            g.revenue_consensus("AAPL", market="US")   # Apple

        See Also:
            ``dartlab.analysis.revenueForecast`` — 컨센서스 + 분석.
        """
        from ..domains import loadDomain

        cache_key = f"{stockCode}_{market}"
        cached = self._cache.getTyped(cache_key, "revenue_consensus")
        if cached is not None:
            return cached  # type: ignore[return-value]
        try:
            if market == "KR":
                module = loadDomain("naver")
                result = runAsync(module.fetchRevenueConsensus(stockCode, self._client))
            else:
                # US/글로벌: revenue consensus 소스 없음 (네이버 KR 전용)
                result = []
        except (SourceUnavailableError, ImportError, OSError, AttributeError) as exc:
            log.warning("revenue_consensus 실패 (%s, %s): %s", stockCode, market, exc)
            result = []
        if result:
            self._cache.putTyped(cache_key, "revenue_consensus", result)
        return result

    def history(
        self,
        stockCode: str,
        *,
        start: str,
        end: str,
        market: str = "KR",
    ) -> "pl.DataFrame":
        """OHLCV 히스토리 DataFrame 조회 (기간 지정).

        Capabilities:
            - fallback 체인: Naver(KR) -> naver_global -> FMP -> Yahoo
            - date, open, high, low, close, volume 컬럼
            - 자동 날짜 파싱 (문자열 -> pl.Date)
            - TTL 캐시 (TTL_HISTORY, DARTLAB_TTL_HISTORY override)

        AIContext:
            - 백테스트/regime 분석의 시계열 입력 원천

        Guide:
            ``price()`` 가 기본 1년 자동 — start/end 명시 시 본 함수 호출.

        When:
            특정 기간 OHLCV 필요 시 (regime change date 분석 등).

        How:
            start/end ISO date → fallback chain → DataFrame.

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

        Raises:
            없음 — fallback 체인 내부 예외는 흡수.

        Example::

            g = getDefaultGather()
            g.history("005930", start="2025-01-01", end="2025-12-31")
            g.history("AAPL", start="2025-06-01", end="2025-12-31", market="US")

        See Also:
            ``price`` — 기본 1년 단축 호출.
        """
        # market 자동 감지 (core SSOT)
        from dartlab.core.market import resolveMarket

        market = resolveMarket(stockCode, market)

        import polars as pl

        from ..infra.cache import buildCacheSlot

        cacheSlot = buildCacheSlot("history", market=market, start=start, end=end)
        cached = self._cache.getTyped(stockCode, cacheSlot)
        if cached is not None:
            return cached  # type: ignore[return-value]
        raw = runAsync(
            _history.fetch(
                stockCode,
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
        self._cache.putTyped(stockCode, cacheSlot, df)
        return df
