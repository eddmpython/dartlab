"""Default Accessor 구현 — F3 Protocol DIP 의 gather 측 구현체.

L2 (analysis/quant/industry) 가 직접 gather 모듈을 import 하지 않도록,
core.protocols 의 4 Protocol 의 default 구현을 한 곳에 모아 둔다. caller
(story/Company) 가 `getXxxAccessor()` 로 인스턴스를 받아 L2 함수에 전달.

정공법 B (Protocol DIP): L2 ↔ gather 직접 의존 차단.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Iterator

import polars as pl

if TYPE_CHECKING:
    from dartlab.core.protocols import CompanyProtocol


def _iterDataFrameBatches(df: pl.DataFrame | None, batchSize: int) -> Iterator[pl.DataFrame]:
    """공통 헬퍼 — DataFrame 을 batchSize 행씩 yield (G+ P-Q6).

    df 가 None / empty 면 yield 없이 종료.

    Args:
        df: 분할 대상 DataFrame.
        batchSize: 한 batch 의 행 수 (1+).

    Yields:
        pl.DataFrame — 각 batch slice.
    """
    if df is None or df.height == 0:
        return
    for i in range(0, df.height, batchSize):
        yield df.slice(i, batchSize)


class DefaultFinanceAccessor:
    """FinanceDataAccessor 기본 구현 — gather/price + gather/macro + gather/exogenousAxes."""

    def fetchPriceSnapshot(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        start: str | None = None,
        end: str | None = None,
        limit: int | None = None,
    ) -> pl.DataFrame | None:
        """OHLCV 스냅샷 fetch — gather("price") 위임.

        Capabilities:
            - L2 (analysis/quant) 가 gather 직접 import 없이 OHLCV 접근
            - limit kwarg 로 행수 상한 (가장 위 N) 적용

        AIContext:
            - story/Company 가 본 accessor 를 L2 함수에 주입 — F3 DIP

        Guide:
            FinanceDataAccessor Protocol 의 default 구현. L2 코드는
            Protocol 만 의존, 본 구현은 gather 의존을 흡수.

        When:
            quant/screen/regime 같은 L2 함수가 OHLCV 데이터 필요 시.

        How:
            ``getFinanceAccessor()`` 로 인스턴스 얻기 → L2 함수에 인자로 전달.

        Args:
            stockCode: 종목코드/티커.
            market: 시장 코드 (기본 ``"KR"``).
            start: 시작일 (YYYY-MM-DD). None이면 자동.
            end: 종료일. None이면 자동.
            limit: 반환 행수 상한 (가장 위 N). None이면 전체.

        Returns:
            OHLCV DataFrame.

        Requires:
            네트워크 (gather("price") 가 외부 API 호출). API 키 불필요.

        Raises:
            ValueError / GatherError — 입력 또는 공급자 실패 그대로.

        Example:
            >>> a = DefaultFinanceAccessor()
            >>> df = a.fetchPriceSnapshot("005930", market="KR", limit=10)

        See Also:
            ``dartlab.gather.GatherEntry`` — 본 함수가 위임하는 진입점.
            ``dartlab.core.protocols.FinanceDataAccessor`` — Protocol.
        """
        from dartlab.gather.entry import GatherEntry

        g = GatherEntry()
        df = g("price", stockCode, market=market, start=start, end=end)
        if df is not None and limit is not None and limit > 0 and hasattr(df, "head"):
            return df.head(limit)
        return df

    def fetchMacroSeries(
        self,
        seriesId: str,
        *,
        source: str = "fred",
        start: str | None = None,
        limit: int | None = None,
    ) -> pl.DataFrame | None:
        """단일 macro 시계열 fetch — gather("macro") 위임.

        Capabilities:
            - FRED (US) / ECOS (KR) 단일 시리즈 조회
            - limit kwarg 로 최근 N 행

        AIContext:
            - L2 macro/quant 가 raw 시계열 데이터 필요 시 본 accessor 경유

        Guide:
            FRED 의 GDP / UNRATE / FEDFUNDS, ECOS 의 BASE_RATE 등 단일
            지표 ID 로 호출. 전체 macro 는 ``gather("macro")`` 직접 호출.

        When:
            특정 거시지표 시계열 필요 시 (회귀분석/regime/anomaly).

        How:
            seriesId + source 로 fetch → df.tail(limit) 으로 최근 N.

        Args:
            seriesId: macro 시리즈 ID (예: "GDP", "UNRATE").
            source: 데이터 소스 (``"fred"`` | ``"ecos"``). 기본 ``"fred"``.
            start: 시작일. None이면 자동.
            limit: 반환 행수 상한 (가장 최근 N). None이면 전체.

        Returns:
            ``(date, value)`` DataFrame. 정상 무데이터면 None.

        Requires:
            네트워크 (FRED / ECOS 호출). FRED_API_KEY / ECOS_API_KEY env 권장.

        Raises:
            ValueError / GatherError — source 계약 또는 공급자 실패 그대로.

        Example:
            >>> a = DefaultFinanceAccessor()
            >>> gdp = a.fetchMacroSeries("GDP", source="fred", limit=50)

        See Also:
            ``dartlab.gather.fred.facade.Fred`` — FRED 클라이언트.
            ``dartlab.gather.ecos.facade.Ecos`` — ECOS 클라이언트.
        """
        from dartlab.gather.entry import GatherEntry

        sourceMarket = {"fred": "US", "ecos": "KR"}
        sourceKey = source.strip().lower()
        if sourceKey not in sourceMarket:
            raise ValueError(f"source는 'fred' 또는 'ecos'여야 합니다: {source!r}")
        g = GatherEntry()
        df = g("macro", seriesId, market=sourceMarket[sourceKey], start=start)
        if df is not None and limit is not None and limit > 0 and hasattr(df, "tail"):
            return df.tail(limit)
        return df

    def fetchExogenousAxes(self, stockCode: str, *, limit: int | None = None) -> list[tuple[str, str]]:
        """종목별 매크로 축 매핑 — gather.mapping.exogenousAxes 위임.

        Capabilities:
            종목에 연결된 외생 지표 ID와 source를 호출 순서대로 반환한다.

        AIContext:
            재무 분석 도구가 임의의 거시지표를 고르지 않고 사전 정의된 종목 매핑을 사용하게 한다.

        Guide:
            시계열 값이 필요하면 반환된 매핑을 ``fetchMacroSeries`` 에 전달한다.

        When:
            종목별 거시 민감도 분석에 사용할 입력 축을 결정할 때 호출한다.

        How:
            ``getExogenousIndicators`` 결과를 ``(seriesId, source)`` 튜플로 투영하고 limit을 적용한다.

        Args:
            stockCode: 종목코드.
            limit: 반환 항목 상한. None이면 전체.

        Returns:
            ``[(seriesId, source), ...]`` 리스트.

        Requires:
            ``dartlab.gather.mapping.exogenousAxes`` 모듈 — 매핑 사전 (parquet).

        Raises:
            내부 매핑 계약 오류를 그대로 전달.

        Example:
            >>> a = DefaultFinanceAccessor()
            >>> axes = a.fetchExogenousAxes("005930", limit=5)

        SeeAlso:
            ``fetchAlignedMacro`` 는 이 매핑의 실제 시계열을 재무 기간에 맞춘다.
        """
        from dartlab.gather.mapping.exogenousAxes import getExogenousIndicators

        indicators = getExogenousIndicators(stockCode=stockCode)
        result = [(indicator.seriesId, indicator.source) for indicator in indicators]
        if limit is not None and limit > 0:
            return result[:limit]
        return result

    def fetchAlignedMacro(
        self,
        stockCode: str,
        periods: list[str],
        *,
        limit: int | None = None,
    ) -> pl.DataFrame | None:
        """period 기준 정렬된 매크로 패널 — transforms.macro.loadMacroParquet 위임.

        Capabilities:
            종목에 매핑된 여러 거시 시계열을 재무 period 기준 단일 패널로 결합한다.

        AIContext:
            분석 도구가 서로 다른 빈도와 날짜 축을 직접 정렬하지 않고 검증된 period 패널을 받게 한다.

        Guide:
            ``periods`` 는 재무제표 축과 같은 순서로 전달하고, 값이 전혀 없을 때는 ``None`` 을 처리한다.

        When:
            재무 시계열과 외생변수를 같은 관측 축에서 회귀·비교할 때 사용한다.

        How:
            종목 매핑 조회 후 각 parquet를 재무 period로 정렬하고 ``period`` 컬럼으로 full join한다.

        Args:
            stockCode: 종목코드.
            periods: 정렬 대상 period 리스트.
            limit: 반환 행수 상한 (가장 최근 N). None이면 전체.

        Returns:
            패널 DataFrame. 가용한 외생변수 캐시가 없으면 None.

        Requires:
            ``data/<provider>/macro/aligned/*.parquet`` 사전 빌드.

        Raises:
            parquet/period 계약 오류를 그대로 전달.

        Example:
            >>> a = DefaultFinanceAccessor()
            >>> panel = a.fetchAlignedMacro("005930", ["2024Q1", "2024Q2"], limit=10)

        SeeAlso:
            ``fetchExogenousAxes`` 는 결합할 지표 목록의 SSOT다.
        """
        from dartlab.gather.transforms.macro import alignToFinancialPeriods, loadMacroParquet

        frames: list[pl.DataFrame] = []
        for seriesId, source in self.fetchExogenousAxes(stockCode):
            series = loadMacroParquet(seriesId, source=source)
            if series is None or series.is_empty():
                continue
            frames.append(alignToFinancialPeriods(series, periods).rename({"value": seriesId}))
        if not frames:
            return None
        panel = frames[0]
        for frame in frames[1:]:
            panel = panel.join(frame, on="period", how="full", coalesce=True)
        periodOrder = pl.DataFrame(
            {
                "period": periods,
                "__periodOrder": range(len(periods)),
            }
        )
        panel = periodOrder.join(panel, on="period", how="left").sort("__periodOrder").drop("__periodOrder")
        if limit is not None and limit > 0:
            return panel.tail(limit)
        return panel

    def lookupCompany(self, stockCode: str) -> CompanyProtocol | None:
        """종목코드 → Company.

        Args:
            stockCode: 종목코드/티커.

        Returns:
            Company 인스턴스. dartlab.company import 실패 또는 생성 실패 시 None.

        Requires:
            ``dartlab.company`` 모듈 + 종목코드 ↔ corp_code 매핑.

        Raises:
            없음 — ImportError/ValueError/RuntimeError/KeyError 는 내부에서 흡수.

        Example:
            >>> a = DefaultFinanceAccessor()
            >>> c = a.lookupCompany("005930")
        """
        try:
            from dartlab.company import Company
        except ImportError:
            return None
        try:
            return Company(stockCode)
        except (ValueError, RuntimeError, KeyError):
            return None

    # ── iter pair (G+ P-Q6 — providers 룰 10 spirit) ──

    def iterPriceSnapshot(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        start: str | None = None,
        end: str | None = None,
        batchSize: int = 100,
    ) -> Iterator[pl.DataFrame]:
        """fetchPriceSnapshot 의 streaming pair — batchSize 행씩 yield (G+ P-Q6 룰 10 spirit).

        Args: stockCode/market/start/end (fetchPriceSnapshot 와 동일), batchSize.
        Yields: pl.DataFrame — 각 batch.
        Raises: 없음.
        Example::

            for batch in a.iterPriceSnapshot("005930", batchSize=50): process(batch)

        Requires: 네트워크 (fetchPriceSnapshot 위임).
        See Also: ``fetchPriceSnapshot`` — full DataFrame.
        """
        df = self.fetchPriceSnapshot(stockCode, market=market, start=start, end=end)
        yield from _iterDataFrameBatches(df, batchSize)

    def iterMacroSeries(
        self,
        seriesId: str,
        *,
        source: str = "fred",
        start: str | None = None,
        batchSize: int = 100,
    ) -> Iterator[pl.DataFrame]:
        """fetchMacroSeries 의 streaming pair — batch yield (G+ P-Q6).

        Args: seriesId/source/start (fetchMacroSeries 와 동일), batchSize.
        Yields: pl.DataFrame — 각 batch.
        Raises: 없음.
        Example::

            for batch in a.iterMacroSeries("FEDFUNDS", batchSize=50): analyze(batch)

        Requires: 네트워크.
        See Also: ``fetchMacroSeries``.
        """
        df = self.fetchMacroSeries(seriesId, source=source, start=start)
        yield from _iterDataFrameBatches(df, batchSize)

    def fetchInsiderTrades(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        limit: int | None = None,
    ) -> pl.DataFrame | None:
        """내부자 거래 내역 DataFrame — gather.insiderTrading 위임 (A 트랙 I1).

        Capabilities:
            - KR: DART 임원거래 공시
            - InsiderTrade dataclass list → pl.DataFrame 변환
            - 빈 결과는 None (caller 가 None 분기)

        AIContext:
            - informed trading 신호. 외부 listener 가 dataframe accessor 로 받음.

        Guide:
            ``gather.engine.Gather().insiderTrading(...)`` 결과 list 를 DataFrame 으로
            동형 변환. dataclass __dict__ 가 그대로 row.

        When:
            insider 흐름 시계열을 DataFrame 처리 (filter/group/aggregate) 필요 시.

        How:
            stockCode + market → mixin 위임 → list[InsiderTrade] → DataFrame.

        Args:
            stockCode: 종목코드 ("005930") 또는 티커 ("AAPL").
            market: 현재 "KR"만 지원.

        Returns:
            pl.DataFrame | None — 거래 내역. 없으면 None.

        Requires:
            DART_API_KEY.

        Raises:
            ValueError / RuntimeError / provider 오류를 그대로 전달.

        Example::

            a = DefaultFinanceAccessor()
            df = a.fetchInsiderTrades("005930")

        See Also:
            ``iterInsiderTrades`` — streaming pair.
            ``dartlab.gather.mixins.info.insiderTrading`` — 원본 list.
        """
        from dartlab.gather.engine import Gather

        trades = Gather().insiderTrading(stockCode, market=market)
        if not trades:
            return None
        rows = [asdict(trade) for trade in trades]
        df = pl.DataFrame(rows)
        return df.head(limit) if limit is not None else df

    def iterInsiderTrades(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        batchSize: int = 100,
    ) -> Iterator[pl.DataFrame]:
        """fetchInsiderTrades 의 streaming pair — batchSize 행씩 yield (A 트랙 I1).

        Args: stockCode/market (fetchInsiderTrades 와 동일), batchSize.
        Yields: pl.DataFrame — 각 batch.
        Raises: 없음.
        Example::

            for batch in a.iterInsiderTrades("005930", batchSize=50): process(batch)

        Requires: 네트워크 (fetchInsiderTrades 위임).
        See Also: ``fetchInsiderTrades`` — full DataFrame.
        """
        df = self.fetchInsiderTrades(stockCode, market=market)
        yield from _iterDataFrameBatches(df, batchSize)

    def fetchOwnership(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        limit: int | None = None,
    ) -> pl.DataFrame | None:
        """기관/외국인 지분 보유 DataFrame — gather.ownership 위임 (A 트랙 I1).

        Capabilities:
            - KR: Naver 외국인 비율 + 기관 보유
            - InstitutionOwnership list → pl.DataFrame
            - 빈 결과는 None

        AIContext:
            - 외국인/기관 보유 흐름 분석. flow() 일별 변동의 누적 형태.

        Guide:
            ``gather.engine.Gather().ownership(...)`` 결과 list 를 DataFrame 동형.

        When:
            institutional ownership 시계열 DataFrame 처리 필요 시.

        How:
            stockCode + market → mixin 위임 → DataFrame.

        Args:
            stockCode: 종목코드 또는 티커.
            market: 현재 "KR"만 지원.

        Returns:
            pl.DataFrame | None — 지분 보유. 없으면 None.

        Requires:
            네트워크.

        Raises:
            ValueError / SourceUnavailableError를 그대로 전달.

        Example::

            a = DefaultFinanceAccessor()
            df = a.fetchOwnership("005930")

        See Also:
            ``iterOwnership`` — streaming pair.
            ``dartlab.gather.mixins.info.ownership`` — 원본 list.
        """
        from dartlab.gather.engine import Gather

        owners = Gather().ownership(stockCode, market=market)
        if not owners:
            return None
        rows = [asdict(owner) for owner in owners]
        df = pl.DataFrame(rows)
        return df.head(limit) if limit is not None else df

    def iterOwnership(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        batchSize: int = 100,
    ) -> Iterator[pl.DataFrame]:
        """fetchOwnership 의 streaming pair — batchSize 행씩 yield (A 트랙 I1).

        Args: stockCode/market (fetchOwnership 와 동일), batchSize.
        Yields: pl.DataFrame — 각 batch.
        Raises: 없음.
        Example::

            for batch in a.iterOwnership("005930"): aggregate(batch)

        Requires: 네트워크.
        See Also: ``fetchOwnership``.
        """
        df = self.fetchOwnership(stockCode, market=market)
        yield from _iterDataFrameBatches(df, batchSize)

    def fetchNews(
        self,
        query: str,
        *,
        market: str = "KR",
        days: int = 30,
        limit: int | None = None,
    ) -> pl.DataFrame | None:
        """뉴스 검색 DataFrame — gather.news 위임 (A 트랙 I1).

        Capabilities:
            - Google News RSS — title/link/published/source 컬럼
            - KR/US 시장별 검색
            - 빈 결과는 None

        AIContext:
            - sentiment / event 분석의 외부 신호 원천. 본문은 untrusted external.

        Guide:
            ``gather.engine.Gather().news(...)`` 결과 DataFrame 을 그대로 반환
            (이미 DataFrame). is_empty() 시 None 으로 정규화.

        When:
            뉴스 시계열 batch 처리 / sentiment scoring 시.

        How:
            query + market + days → mixin 위임 → DataFrame.

        Args:
            query: 검색어 (종목명, 키워드).
            market: "KR" 또는 "US". 기본 "KR".
            days: 최근 N일. 기본 30.

        Returns:
            pl.DataFrame | None — 뉴스. 빈 결과면 None.

        Requires:
            네트워크 (Google News RSS).

        Raises:
            없음.

        Example::

            a = DefaultFinanceAccessor()
            df = a.fetchNews("삼성전자", days=7)

        See Also:
            ``iterNews`` — streaming pair.
            ``dartlab.gather.mixins.news.news`` — 원본 DataFrame.
        """
        from dartlab.gather.engine import Gather

        df = Gather().news(query, market=market, days=days)
        if df is None or df.is_empty():
            return None
        return df.head(limit) if limit is not None else df

    def iterNews(
        self,
        query: str,
        *,
        market: str = "KR",
        days: int = 30,
        batchSize: int = 100,
    ) -> Iterator[pl.DataFrame]:
        """fetchNews 의 streaming pair — batchSize 행씩 yield (A 트랙 I1).

        Args: query/market/days (fetchNews 와 동일), batchSize.
        Yields: pl.DataFrame — 각 batch.
        Raises: 없음.
        Example::

            for batch in a.iterNews("삼성전자", batchSize=20): score_sentiment(batch)

        Requires: 네트워크.
        See Also: ``fetchNews``.
        """
        df = self.fetchNews(query, market=market, days=days)
        yield from _iterDataFrameBatches(df, batchSize)


class DefaultQuantAccessor:
    """QuantDataAccessor 기본 구현."""

    def fetchOhlcv(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        start: str | None = None,
        limit: int | None = None,
    ) -> pl.DataFrame | None:
        """단일 종목 OHLCV — gather price axis 위임.

        Capabilities:
            - L2가 gather 직접 import 없이 OHLCV 접근
            - limit 으로 최근 N 일 슬라이스

        AIContext:
            - quant/screen/regime 같은 L2 가 OHLCV 데이터 접근 시

        Guide:
            QuantDataAccessor Protocol 의 default 구현. fetchOhlcv 는 gather 의
            raw price axis 만 호출하고 quant 계산 owner 로 역진입하지 않는다.

        When:
            quant 함수가 단일 종목 시계열 필요 시.

        How:
            stockCode + market → fetchOhlcv → df.tail(limit).

        Args:
            stockCode: 종목코드/티커.
            market: 시장 코드 (기본 ``"KR"``).
            start: 시작일. None이면 자동.
            limit: 반환 행수 상한 (가장 최근 N일). None이면 전체.

        Returns:
            OHLCV DataFrame. fetch 실패 시 None.

        Requires:
            네트워크 (gather price source). API 키 불필요.

        Raises:
            없음 — 위임 함수의 예외는 호출자가 처리.

        Example:
            >>> a = DefaultQuantAccessor()
            >>> df = a.fetchOhlcv("005930", market="KR", limit=20)

        See Also:
            ``dartlab.gather("price", ...)`` — 본 위임의 backend.
        """
        from dartlab.gather.entry import GatherEntry

        df = GatherEntry()("price", stockCode, market=market, start=start)
        if df is not None and limit is not None and limit > 0 and hasattr(df, "tail"):
            return df.tail(limit)
        return df

    def fetchBenchmarkOhlcv(
        self,
        stockCode: str,
        *,
        market: str = "KR",
        benchmark: str | None = None,
        limit: int | None = None,
    ) -> tuple[pl.DataFrame | None, dict | None]:
        """벤치마크 OHLCV + meta — gather 경계에서는 제공하지 않음.

        Args:
            stockCode: 종목코드/티커.
            market: 시장 코드 (기본 ``"KR"``).
            benchmark: 벤치마크 ID. None이면 시장별 기본.
            limit: 반환 행수 상한 (가장 최근 N일). None이면 전체.

        Returns:
            ``(None, None)``. benchmark 매핑과 계산 owner 는 L2 quant 이다.

        Requires:
            없음. caller 가 quant benchmark API 에서 수행해야 한다.

        Raises:
            없음 — ValueError/RuntimeError/KeyError 는 내부에서 흡수.

        Example:
            >>> a = DefaultQuantAccessor()
            >>> df, meta = a.fetchBenchmarkOhlcv("005930", limit=10)
        """
        return None, None

    def fetchUniverseBulk(
        self,
        stockCodes: list[str],
        *,
        columns: list[str],
        limit: int | None = None,
    ) -> pl.DataFrame | None:
        """다종목 bulk 패널 — bulkData.hfBulk.loadFiltered 위임.

        Capabilities:
            여러 종목과 필요한 컬럼만 한 번에 필터링해 bulk 패널을 반환한다.

        AIContext:
            스크리닝 도구가 종목별 파일을 반복 로드하지 않고 제한된 입력 집합을 읽게 한다.

        Guide:
            빈 종목 목록은 ``None`` 이며, ``columns`` 에 실제 분석에 필요한 필드만 명시한다.

        When:
            동일 컬럼을 여러 종목에 걸쳐 비교하거나 스크리닝할 때 호출한다.

        How:
            ``loadFiltered`` 에 종목과 컬럼을 전달한 뒤 선택적으로 선두 행 limit을 적용한다.

        Args:
            stockCodes: 대상 종목코드 리스트.
            columns: 추출 컬럼 리스트.
            limit: 반환 행수 상한 (가장 위 N). None이면 전체.

        Returns:
            bulk 패널 DataFrame. fetch 실패 시 None.

        Requires:
            ``data/<provider>/bulk/*.parquet`` (HF SSOT 미러).

        Raises:
            ValueError / KeyError — 잘못된 필터 또는 없는 컬럼.

        Example:
            >>> a = DefaultQuantAccessor()
            >>> df = a.fetchUniverseBulk(["005930", "000660"], columns=["close"], limit=100)

        SeeAlso:
            ``dartlab.gather.bulkData.hfBulk.loadFiltered`` 가 필터 실행을 소유한다.
        """
        if not stockCodes:
            return None
        from dartlab.gather.bulkData.hfBulk import loadFiltered

        df = loadFiltered(stockCodes=stockCodes, columns=columns)
        if df.is_empty():
            return None
        if limit is not None and limit > 0:
            return df.head(limit)
        return df

    def fetchTechnicalIndicators(
        self,
        stockCode: str,
        indicators: list[str],
        *,
        limit: int | None = None,
    ) -> dict[str, pl.DataFrame]:
        """지표 번들 — gather raw 경계 밖 계산은 호출 측으로 위임.

        Capabilities:
            - 다중 보조지표 한 번에 fetch (rsi/ma/macd 등)
            - limit 으로 지표 개수 상한 (앞쪽 N)

        AIContext:
            - quant 가 종목별 지표 패키지 필요 시 본 accessor 경유

        Guide:
            gather accessor 는 raw/collection fetch 만 소유한다. 기술지표 계산은
            caller 가 OHLCV 를 받은 뒤 ``dartlab.synth`` 또는 L2 quant 에서 수행한다.

        When:
            screen/regime 등이 ad-hoc 지표 조합 필요 시.

        How:
            indicators=["rsi14", "ma20"] → {"rsi14": df, "ma20": df}.

        Args:
            stockCode: 종목코드/티커.
            indicators: 호출할 지표 이름 리스트 (예: ``["rsi14", "ma20"]``).
            limit: 반환 지표 개수 상한 (앞쪽 N). None이면 전체.

        Returns:
            빈 딕셔너리. 기존 호출 표면은 유지하되 L1 → L1.5 lazy import 는 하지 않는다.

        Requires:
            없음. 계산 owner 는 synth/quant caller.

        Raises:
            없음 — ImportError/ValueError/RuntimeError/KeyError/TypeError 는 내부에서 흡수.

        Example:
            >>> a = DefaultQuantAccessor()
            >>> out = a.fetchTechnicalIndicators("005930", ["rsi14"], limit=1)

        See Also:
            ``dartlab.synth.indicators`` — caller 가 직접 사용할 지표 함수 카탈로그.
        """
        return {}

    # ── iter pair (G+ P-Q6) ──

    def iterUniverseBulk(
        self,
        stockCodes: list[str],
        *,
        columns: list[str],
        batchSize: int = 1000,
    ) -> Iterator[pl.DataFrame]:
        """fetchUniverseBulk 의 streaming pair — batch 별 yield (G+ P-Q6).

        Args: stockCodes/columns (fetchUniverseBulk 와 동일), batchSize.
        Yields: pl.DataFrame — 각 batch.
        Raises: 없음.
        Example::

            for batch in a.iterUniverseBulk(codes, columns=["close"]): handle(batch)

        Requires: ``data/<provider>/bulk/*.parquet``.
        See Also: ``fetchUniverseBulk``.
        """
        df = self.fetchUniverseBulk(stockCodes, columns=columns)
        yield from _iterDataFrameBatches(df, batchSize)


class DefaultIndustryAccessor:
    """IndustryDataAccessor 기본 구현."""

    def fetchListing(self, *, market: str = "KR", limit: int | None = None) -> pl.DataFrame | None:
        """전종목 listing snapshot — KRX 기준 (short_code/marketCode/marketEngName 컬럼).

        Args:
            market: 시장 코드 (현재 ``"KR"`` 만 지원).
            limit: 반환 행수 상한 (가장 위 N). None이면 전체.

        Returns:
            전종목 listing DataFrame. import 실패 또는 fetch 실패 시 None.

        Requires:
            ``dartlab.gather.krx.listing`` 모듈 + KRX API (또는 캐시).

        Raises:
            없음 — ImportError/ValueError/RuntimeError/KeyError/TypeError 는 내부에서 흡수.

        Example:
            >>> a = DefaultIndustryAccessor()
            >>> df = a.fetchListing(market="KR", limit=20)
        """
        try:
            from dartlab.gather.krx.listing import getKrxList
        except ImportError:
            return None
        try:
            df = getKrxList()
            if df is not None and limit is not None and limit > 0 and hasattr(df, "head"):
                return df.head(limit)
            return df
        except (ValueError, RuntimeError, KeyError, TypeError):
            return None

    def fetchScanProfitability(self, *, limit: int | None = None) -> pl.DataFrame | None:
        """scan profitability parquet — gather 경계에서는 제공하지 않음.

        Args:
            limit: 반환 행수 상한. None이면 전체 collect.

        Returns:
            None. scan parquet owner 는 L1.5 scan 이며 gather 는 직접 호출하지 않는다.

        Requires:
            없음. caller 가 L1.5 scan API 를 직접 호출해야 한다.

        Raises:
            없음 — ImportError/ValueError/RuntimeError/KeyError/AttributeError 는 내부에서 흡수.

        Example:
            >>> a = DefaultIndustryAccessor()
            >>> df = a.fetchScanProfitability(limit=100)
        """
        return None

    def fetchScanFinanceParquet(self, name: str = "finance", *, limit: int | None = None) -> pl.DataFrame | None:
        """scan finance parquet — gather 경계에서는 제공하지 않음.

        Args:
            name: parquet 카테고리 이름 (기본 ``"finance"``).
            limit: 반환 행수 상한. None이면 전체 collect.

        Returns:
            None. scan parquet owner 는 L1.5 scan 이며 gather 는 직접 호출하지 않는다.

        Requires:
            없음. caller 가 L1.5 scan API 를 직접 호출해야 한다.

        Raises:
            없음 — ImportError/ValueError/RuntimeError/KeyError/AttributeError 는 내부에서 흡수.

        Example:
            >>> a = DefaultIndustryAccessor()
            >>> df = a.fetchScanFinanceParquet("finance", limit=100)
        """
        return None

    # ── iter pair (G+ P-Q6) ──

    def iterListing(self, *, market: str = "KR", batchSize: int = 200) -> Iterator[pl.DataFrame]:
        """fetchListing 의 streaming pair — batch 별 yield (G+ P-Q6).

        Args: market (시장 코드), batchSize (한 batch 행 수).
        Yields: pl.DataFrame — 각 batch.
        Raises: 없음.
        Example::

            for batch in a.iterListing(batchSize=500): pass

        Requires: KRX API/캐시.
        See Also: ``fetchListing``.
        """
        df = self.fetchListing(market=market)
        yield from _iterDataFrameBatches(df, batchSize)

    def iterScanFinanceParquet(self, name: str = "finance", *, batchSize: int = 1000) -> Iterator[pl.DataFrame]:
        """fetchScanFinanceParquet 의 streaming pair — scan batch yield (G+ P-Q6).

        Args: name (parquet 카테고리), batchSize (한 batch 행 수).
        Yields: pl.DataFrame — 각 batch.
        Raises: 없음.
        Example::

            for batch in a.iterScanFinanceParquet("finance"): pass

        Requires: ``data/<provider>/scan/<name>.parquet``.
        See Also: ``fetchScanFinanceParquet``.
        """
        df = self.fetchScanFinanceParquet(name)
        yield from _iterDataFrameBatches(df, batchSize)
