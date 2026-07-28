"""FRED facade — Fred 클래스 본체.

`__init__.py` thin facade 룰을 위해 클래스 정의 분리.
"""

from __future__ import annotations

import polars as pl

from dartlab.gather.catalogGroups import resolveGroupIds

from . import catalog as _catalog
from . import transform as _transform
from .client import FredClient
from .series import fetchMeta, fetchMulti, fetchReleases, fetchSeries, searchSeries
from .types import CatalogEntry, SeriesMeta


class Fred:
    """FRED 경제지표 facade.

    Args:
        api_key: FRED API 키. None이면 ``FRED_API_KEY`` 환경변수 사용.

    Example::

        f = Fred()
        gdp = f.series("GDP")
        f.compare(["GDP", "UNRATE"], start="2020-01-01")
        f.correlation(["GDP", "UNRATE", "FEDFUNDS"])
    """

    def __init__(self, apiKey: str | None = None) -> None:
        self._client = FredClient(apiKey=apiKey)

    # ── 시계열 조회 ──

    def series(
        self,
        seriesId: str,
        *,
        start: str | None = None,
        end: str | None = None,
        freq: str | None = None,
        aggregation: str = "avg",
    ) -> pl.DataFrame:
        """단일 시계열 조회 → DataFrame ``(date, value)``.

        Capabilities: series.fetchSeries 위임 — 캐시 hit / FRED API GET / 리샘플.
        AIContext: macro engine 의 사용자 진입 facade — gather.macro(seriesId, market="US") 와 짝.
        Guide: freq 미명시 시 원본 frequency. aggregation 은 avg/sum/eop 셋.
        When: 사용자가 미국 매크로 단일 시계열 분석 시.
        How: ``fetchSeries(self._client, seriesId, ...)`` direct.

        Parameters
        ----------
        series_id : str
            FRED 시리즈 ID (예: "GDP", "UNRATE", "CPIAUCSL").
        start : str | None
            시작일 (YYYY-MM-DD). None이면 전체.
        end : str | None
            종료일. None이면 최신까지.
        freq : str | None
            리샘플 주파수 (d/w/bw/m/q/sa/a). None이면 원본.
        aggregation : str
            리샘플 집계 방법 (avg/sum/eop).

        Returns
        -------
        pl.DataFrame
            컬럼: ``date`` (Date) — 관측일, ``value`` (Float64) — 지표값.

        Raises
        ------
        FredError
            FRED API HTTP 오류 또는 인증 실패.

        Requires
        --------
        ``FRED_API_KEY`` 환경변수.

        Example
        -------
        >>> f = Fred()
        >>> df = f.series("GDP", start="2020-01-01")

        See Also
        --------
        compare : 복수 시리즈 wide pivot.
        yoy · mom · movingAverage : 본 함수 결과의 transform.
        """
        return fetchSeries(
            self._client,
            seriesId,
            start=start,
            end=end,
            freq=freq,
            aggregation=aggregation,
        )

    def search(self, query: str, *, limit: int = 20) -> pl.DataFrame:
        """키워드 검색.

        Capabilities: series.searchSeries 위임 — FRED /series/search endpoint.
        AIContext: 사용자가 카탈로그에 없는 시리즈 탐색 시 진입.
        Guide: 영문 키워드만. limit 기본 20.
        When: 카탈로그 외 시리즈 탐색 / fuzzy 검색 시.
        How: ``searchSeries(self._client, query, limit=limit)``.

        Parameters
        ----------
        query : str
            검색어 (영문).
        limit : int
            최대 결과 수.

        Returns
        -------
        pl.DataFrame
            컬럼: ``id`` (Utf8) — 시리즈 ID, ``title`` (Utf8) — 제목,
            ``frequency`` (Utf8) — 주기, ``units`` (Utf8) — 단위,
            ``popularity`` (Int64) — 인기도.

        Raises
        ------
        FredError
            FRED API HTTP 오류.

        Requires
        --------
        ``FRED_API_KEY`` 환경변수.

        Example
        -------
        >>> f = Fred()
        >>> hits = f.search("unemployment", limit=10)

        See Also
        --------
        catalog : 사전정의 13 그룹.
        meta : 단일 series 메타.
        """
        return searchSeries(self._client, query, limit=limit)

    def meta(self, seriesId: str) -> SeriesMeta:
        """시계열 메타데이터.

        Capabilities: series.fetchMeta 위임 — FRED /series endpoint.
        AIContext: fetch 전 series 의 frequency/units/freshness 확인 진입.
        Guide: 단건 SeriesMeta — 본문 시계열은 series() 별도 호출.
        When: 시리즈 단위 분석 전 메타 검증 / UI 표시 시.
        How: ``fetchMeta(self._client, seriesId)``.

        Parameters
        ----------
        series_id : str
            FRED 시리즈 ID.

        Returns
        -------
        SeriesMeta
            id, title, frequency, units, seasonal_adjustment,
            observation_start, observation_end, last_updated, notes 포함.

        Raises
        ------
        SeriesNotFoundError
            시리즈를 찾을 수 없을 때.

        Requires
        --------
        ``FRED_API_KEY`` 환경변수.

        Example
        -------
        >>> f = Fred()
        >>> m = f.meta("GDP")

        See Also
        --------
        series : 본문 시계열 fetch.
        catalog : 사전정의 카탈로그 + label.
        """
        return fetchMeta(self._client, seriesId)

    def compare(
        self,
        seriesIds: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
        freq: str | None = None,
    ) -> pl.DataFrame:
        """복수 시계열 비교 → wide DataFrame.

        Capabilities: series.fetchMulti 위임 — 시리즈별 fetch + outer join + forward-fill.
        AIContext: macro engine 의 cross-series 비교 (예: GDP vs UNRATE) 진입.
        Guide: 주파수 다르면 outer join 후 forward_fill — 표시 시 caller dropna 권장.
        When: correlation / regime 분석 입력 시계열 준비 시.
        How: ``fetchMulti(self._client, seriesIds, ...)``.

        Parameters
        ----------
        series_ids : list[str]
            FRED 시리즈 ID 리스트.
        start : str | None
            시작일 (YYYY-MM-DD). None이면 전체.
        end : str | None
            종료일. None이면 최신까지.
        freq : str | None
            리샘플 주파수. None이면 원본.

        Returns
        -------
        pl.DataFrame
            컬럼: ``date`` (Date) — 관측일, 각 시리즈 ID (Float64) — 지표값.
            주파수가 다른 시리즈는 outer join 후 forward-fill.

        Raises
        ------
        FredError
            FRED API HTTP 오류.

        Requires
        --------
        ``FRED_API_KEY`` 환경변수.

        Example
        -------
        >>> f = Fred()
        >>> df = f.compare(["GDP", "UNRATE"], start="2020-01-01")

        See Also
        --------
        series : 단일 시계열.
        correlation · leadLag : 본 함수 결과의 분석 transform.
        """
        return fetchMulti(
            self._client,
            seriesIds,
            start=start,
            end=end,
            freq=freq,
        )

    def releases(self, *, limit: int = 20) -> pl.DataFrame:
        """최근 데이터 릴리즈 일정.

        Capabilities: series.fetchReleases 위임 — FRED /releases endpoint.
        AIContext: 지표 발표 일정 추적 — 분석 결과의 staleness 진단 진입.
        Guide: limit 기본 20. 인기도 순.
        When: 매크로 분석 시 다음 발표 일정 / 신선도 확인 시.
        How: ``fetchReleases(self._client, limit=limit)``.

        Parameters
        ----------
        limit : int
            최대 결과 수.

        Returns
        -------
        pl.DataFrame
            컬럼: ``id`` (Int64) — 릴리즈 ID, ``name`` (Utf8) — 릴리즈명,
            ``press_release`` (Boolean) — 보도자료 여부, ``link`` (Utf8) — URL.

        Raises
        ------
        FredError
            FRED API HTTP 오류.

        Requires
        --------
        ``FRED_API_KEY`` 환경변수.

        Example
        -------
        >>> f = Fred()
        >>> rs = f.releases(limit=5)

        See Also
        --------
        meta : 단일 시리즈의 last_updated.
        """
        return fetchReleases(self._client, limit=limit)

    # ── 카탈로그 ──

    def group(self, name: str, *, start: str | None = None, end: str | None = None) -> pl.DataFrame:
        """카탈로그 그룹 일괄 조회.

        Capabilities: catalog.getGroupIds → series.fetchMulti 위임 → wide DataFrame.
        AIContext: 그룹 단위 매크로 분석 (예: 금리 그룹 전체 시계열) 진입.
        Guide: 미존재 그룹 ValueError + 가용 그룹 안내.
        When: 카테고리 단위 매크로 dashboard / regime 분석 시.
        How: ``getGroupIds(name)`` → ``fetchMulti(self._client, ids, start, end)``.

        Parameters
        ----------
        name : str
            그룹명 (growth/inflation/rates/employment/markets/housing/money).
        start : str | None
            시작일. None이면 전체.
        end : str | None
            종료일. None이면 최신까지.

        Returns
        -------
        pl.DataFrame
            컬럼: ``date`` (Date) — 관측일, 각 시리즈 ID (Float64) — 지표값.

        Raises
        ------
        ValueError
            존재하지 않는 그룹명.

        Requires
        --------
        ``FRED_API_KEY`` 환경변수 + ``name`` 이 CATALOG 에 등록된 그룹.

        Example
        -------
        >>> f = Fred()
        >>> df = f.group("rates")

        See Also
        --------
        catalog : 사전정의 그룹 카탈로그.
        compare : 임의 시리즈 list 비교.
        """
        ids = resolveGroupIds(_catalog, name)
        return fetchMulti(self._client, ids, start=start, end=end)

    def catalog(self, group: str | None = None) -> pl.DataFrame:
        """카탈로그 조회.

        Capabilities: catalog.toDataframe 위임 — 사전정의 카탈로그 DataFrame.
        AIContext: 사용자/AI 가 사용 가능 시리즈 universe 탐색 진입.
        Guide: group filter 없으면 전체. FRED API 호출 0 (정적).
        When: 분석 시작 전 universe 확인 / UI dropdown 빌드 시.
        How: ``_catalog.toDataframe(group)``.

        Parameters
        ----------
        group : str | None
            특정 그룹만 필터. None이면 전체.

        Returns
        -------
        pl.DataFrame
            컬럼: ``id`` (Utf8) — 시리즈 ID, ``label`` (Utf8) — 한글 라벨,
            ``group`` (Utf8) — 그룹명, ``frequency`` (Utf8) — 주기,
            ``unit`` (Utf8) — 단위, ``description`` (Utf8) — 설명.

        Raises
        ------
        없음
            미존재 그룹은 빈 DataFrame.

        Requires
        --------
        catalog.CATALOG 정적 사전.

        Example
        -------
        >>> f = Fred()
        >>> cat = f.catalog(group="rates")

        See Also
        --------
        group : 카탈로그 그룹 일괄 fetch.
        search : 카탈로그 외 fuzzy 검색.
        """
        return _catalog.toDataframe(group)

    # ── 변환 ──

    def yoy(self, seriesId: str, *, start: str | None = None, end: str | None = None) -> pl.DataFrame:
        """전년 동기 대비 변화율 (%).

        Capabilities: series + transform.yoy 위임 — 원본 + value_yoy 컬럼.
        AIContext: 인플레이션/생산 YoY 분석 진입 (CPI, IPI, PPI 등).
        Guide: frequency 자동 감지 (monthly→12 lag).
        When: 인플레이션 / 명목 증가율 분석 시.
        How: ``self.series(...)`` → ``_transform.yoy(df)``.

        Parameters
        ----------
        series_id : str
            FRED 시리즈 ID.
        start : str | None
            시작일. None이면 전체.
        end : str | None
            종료일. None이면 최신까지.

        Returns
        -------
        pl.DataFrame
            원본 컬럼 + ``value_yoy`` (Float64) — 전년 동기 대비 변화율 (%).

        Raises
        ------
        FredError
            series fetch 실패.

        Requires
        --------
        ``FRED_API_KEY`` + series 가 ≥ 8 row.

        Example
        -------
        >>> f = Fred()
        >>> df = f.yoy("CPIAUCSL")

        See Also
        --------
        mom : 전월 변화율.
        movingAverage : 이동평균.
        transform.yoy : 위임 대상.
        """
        df = self.series(seriesId, start=start, end=end)
        return _transform.yoy(df)

    def mom(self, seriesId: str, *, start: str | None = None, end: str | None = None) -> pl.DataFrame:
        """전월(전기) 대비 변화율 (%).

        Capabilities: series + transform.mom 위임 — 원본 + value_mom 컬럼.
        AIContext: 단기 모멘텀 분석 진입 (인플레이션 가속/감속 추적).
        Guide: frequency 무관 — shift(1).
        When: 단기 가속/감속 (한 기 단위 변화) 분석 시.
        How: ``self.series(...)`` → ``_transform.mom(df)``.

        Parameters
        ----------
        series_id : str
            FRED 시리즈 ID.
        start : str | None
            시작일. None이면 전체.
        end : str | None
            종료일. None이면 최신까지.

        Returns
        -------
        pl.DataFrame
            원본 컬럼 + ``value_mom`` (Float64) — 전월 대비 변화율 (%).

        Raises
        ------
        FredError
            series fetch 실패.

        Requires
        --------
        ``FRED_API_KEY`` + series 가 ≥ 2 row.

        Example
        -------
        >>> f = Fred()
        >>> df = f.mom("CPIAUCSL")

        See Also
        --------
        yoy : 전년 동기 변화율.
        transform.mom : 위임 대상.
        """
        df = self.series(seriesId, start=start, end=end)
        return _transform.mom(df)

    def movingAverage(
        self,
        seriesId: str,
        *,
        window: int = 12,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame:
        """이동평균.

        Capabilities: series + transform.movingAverage 위임 — value_ma{window} 컬럼.
        AIContext: 시계열 smoothing — short-term noise 제거 진입.
        Guide: window 기본 12 (1 년 월별 데이터 기준).
        When: trend 추출 / regime classifier 전처리 시.
        How: ``self.series(...)`` → ``_transform.movingAverage(df, window=window)``.

        Parameters
        ----------
        series_id : str
            FRED 시리즈 ID.
        window : int
            이동평균 윈도우 크기 (기).
        start : str | None
            시작일. None이면 전체.
        end : str | None
            종료일. None이면 최신까지.

        Returns
        -------
        pl.DataFrame
            원본 컬럼 + ``value_ma{window}`` (Float64) — 이동평균값.

        Raises
        ------
        FredError
            series fetch 실패.

        Requires
        --------
        ``FRED_API_KEY`` + series 가 ≥ window row.

        Example
        -------
        >>> f = Fred()
        >>> df = f.movingAverage("UNRATE", window=6)

        See Also
        --------
        yoy · mom : 변화율 transform 동행.
        transform.movingAverage : 위임 대상.
        """
        df = self.series(seriesId, start=start, end=end)
        return _transform.movingAverage(df, window=window)

    # ── 분석 ──

    def correlation(
        self,
        seriesIds: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame:
        """복수 시계열 간 상관행렬.

        Capabilities: compare + transform.correlation 위임 — N×N 상관 행렬.
        AIContext: 매크로 변수 간 통계적 관계 추출 — regime/portfolio 분석 진입.
        Guide: ≥ 2 시리즈 필요. 결측 row dropna 후 corr.
        When: 변수 다중공선성 확인 / regime 분류 입력 정의 시.
        How: ``self.compare(seriesIds, ...)`` → ``_transform.correlation(df)``.

        Parameters
        ----------
        series_ids : list[str]
            FRED 시리즈 ID 리스트 (2개 이상).
        start : str | None
            시작일. None이면 전체.
        end : str | None
            종료일. None이면 최신까지.

        Returns
        -------
        pl.DataFrame
            컬럼: ``column`` (Utf8) — 시리즈명, 각 시리즈 ID (Float64) — 상관계수.
            대각 = 1.0.

        Raises
        ------
        FredError
            compare fetch 실패.

        Requires
        --------
        ``FRED_API_KEY`` + ≥ 2 시리즈 시계열 가용.

        Example
        -------
        >>> f = Fred()
        >>> corr = f.correlation(["GDP", "UNRATE", "FEDFUNDS"])

        See Also
        --------
        compare : 본 함수의 source 시계열.
        leadLag : 동행 시차 분석.
        transform.correlation : 위임 대상.
        """
        df = self.compare(seriesIds, start=start, end=end)
        return _transform.correlation(df)

    def leadLag(
        self,
        idA: str,
        idB: str,
        *,
        maxLag: int = 12,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame:
        """선행/후행 상관분석.

        Capabilities: compare(idA, idB) + transform.leadLag 위임 — ±maxLag 시차별 corr.
        AIContext: 매크로 lead-lag 관계 추론 — 금리 → 실업률 시차 분석 진입.
        Guide: 양수 lag = idB 가 후행. 음수 lag = idA 가 후행.
        When: 정책 효과 시차 분석 (Fed funds → unemployment) 시.
        How: ``self.compare([idA, idB], ...)`` → ``_transform.leadLag(df, idA, idB, maxLag=maxLag)``.

        Parameters
        ----------
        idA, idB : str
            FRED 시리즈 ID 쌍.
        maxLag : int
            ± lag 최대 (기). 기본 12.
        start, end : str | None
            조회 범위.

        Returns:
            DataFrame ``(lag, correlation)``. 양수 lag = id_b가 후행.

        Raises
        ------
        FredError
            compare fetch 실패.

        Requires
        --------
        ``FRED_API_KEY`` + 양 시리즈 시계열 가용 + ≥ maxLag+1 row.

        Example
        -------
        >>> f = Fred()
        >>> df = f.leadLag("FEDFUNDS", "UNRATE", maxLag=6)

        See Also
        --------
        correlation : 동시점 상관 행렬.
        compare : source 시계열 wide.
        transform.leadLag : 위임 대상.
        """
        df = self.compare([idA, idB], start=start, end=end)
        return _transform.leadLag(df, idA, idB, maxLag=maxLag)

    # ── 정리 ──

    def close(self) -> None:
        """HTTP 세션 종료.

        Capabilities: FredClient.close 위임 — httpx 세션 정리.
        AIContext: dartlab 종료 / context manager exit 시 리소스 해제 진입.
        Guide: idempotent — 두 번 호출 graceful.
        When: 명시 cleanup / 테스트 fixture teardown 시.
        How: ``self._client.close()``.

        Returns
        -------
        None

        Raises
        ------
        없음
            세션이 이미 종료된 경우에도 graceful.

        Requires
        --------
        ``self._client`` (FredClient) 가용.

        Example
        -------
        >>> f = Fred()
        >>> f.close()

        See Also
        --------
        client.FredClient.close : 위임 대상.
        """
        self._client.close()

    def __repr__(self) -> str:
        n = len(_catalog.getAllIds())
        return f"Fred(catalog={n} series, groups={_catalog.getGroups()})"


__all__ = ["Fred"]
