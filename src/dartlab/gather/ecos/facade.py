"""ECOS facade — Ecos 클래스 본체.

`__init__.py` thin facade 룰을 위해 클래스 정의 분리.
"""

from __future__ import annotations

import polars as pl

from dartlab.gather.catalogGroups import resolveGroupIds

from . import catalog as _catalog
from .client import EcosClient
from .series import fetchMulti, fetchSeries
from .types import CatalogEntry


class Ecos:
    """ECOS 경제지표 facade.

    Args:
        apiKey: ECOS API 키. None이면 ``ECOS_API_KEY`` 환경변수 사용.

    Example::

        e = Ecos()
        cpi = e.series("CPI")
        e.compare(["CPI", "BASE_RATE", "USDKRW"])
    """

    def __init__(self, apiKey: str | None = None) -> None:
        self._client = EcosClient(apiKey=apiKey)

    # ── 시계열 조회 ──

    def series(
        self,
        indicatorId: str,
        *,
        start: str | None = None,
        end: str | None = None,
        enrich: bool = False,
    ) -> pl.DataFrame:
        """단일 시계열 조회 → DataFrame ``(date, value)``.

        Parameters
        ----------
        indicatorId : str
            카탈로그 지표 ID (예: "GDP", "CPI", "BASE_RATE").
        start : str | None
            시작일 (YYYY, YYYYMM, YYYYMMDD). None이면 2000년부터.
        end : str | None
            종료일. None이면 최신까지.
        enrich : bool
            True이면 변화율 추가 + Parquet 영구 캐시.

        Returns
        -------
        pl.DataFrame
            컬럼: ``date`` (Date) — 관측일, ``value`` (Float64) — 지표값.
            enrich=True 시 변화율 컬럼 추가.

        Raises
        ------
        SeriesNotFoundError
            카탈로그에 없는 ``indicatorId``.

        Example
        -------
        >>> e = Ecos()
        >>> df = e.series("CPI", start="2020-01-01")

        Capabilities
        ------------
        series.fetchSeries 위임 — 캐시 hit / ECOS API / DataFrame 변환.
        AIContext: macro engine 의 한국 시계열 진입 facade — gather.macro(seriesId, market="KR") 와 짝.
        Guide: enrich=True 시 변화율 + Parquet 저장.
        When: 사용자가 한국 매크로 단일 시계열 분석 시.
        How: ``fetchSeries(self._client, indicatorId, start, end, enrich=enrich)``.

        Requires
        --------
        ``ECOS_API_KEY`` 환경변수.

        See Also
        --------
        compare : 복수 시리즈 wide.
        catalog : 사용 가능한 indicatorId 카탈로그.
        """
        return fetchSeries(self._client, indicatorId, start=start, end=end, enrich=enrich)

    def compare(
        self,
        indicatorIds: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame:
        """복수 시계열 비교 → wide DataFrame ``(date, CPI, BASE_RATE, ...)``.

        Parameters
        ----------
        indicatorIds : list[str]
            카탈로그 지표 ID 리스트 (예: ["CPI", "BASE_RATE", "USDKRW"]).
        start : str | None
            시작일 (YYYY, YYYYMM, YYYYMMDD). None이면 2000년부터.
        end : str | None
            종료일. None이면 최신까지.

        Returns
        -------
        pl.DataFrame
            컬럼: ``date`` (Date) — 관측일, 각 지표 ID (Float64) — 지표값.
            주기가 다른 지표는 outer join 후 forward-fill.

        Raises
        ------
        SeriesNotFoundError
            ``indicatorIds`` 중 하나라도 카탈로그에 없을 때.

        Example
        -------
        >>> e = Ecos()
        >>> df = e.compare(["CPI", "BASE_RATE"])

        Capabilities
        ------------
        series.fetchMulti 위임 — fan-out + outer join + forward_fill.
        AIContext: 한국 매크로 cross-series 분석 진입 (예: CPI vs 기준금리).
        Guide: 주기 다르면 outer join 후 forward_fill.
        When: 매크로 regime / correlation 분석 시.
        How: ``fetchMulti(self._client, indicatorIds, start, end)``.

        Requires
        --------
        ``ECOS_API_KEY`` 환경변수.

        See Also
        --------
        series : 단일 시리즈.
        group : 카탈로그 그룹 일괄.
        """
        return fetchMulti(self._client, indicatorIds, start=start, end=end)

    # ── 카탈로그 ──

    def catalog(self, group: str | None = None) -> pl.DataFrame:
        """카탈로그 조회.

        Parameters
        ----------
        group : str | None
            특정 그룹만 필터. None이면 전체.

        Returns
        -------
        pl.DataFrame
            컬럼: ``id`` (Utf8) — 지표 ID, ``label`` (Utf8) — 한글 라벨,
            ``group`` (Utf8) — 그룹명, ``frequency`` (Utf8) — 주기 코드,
            ``unit`` (Utf8) — 단위, ``description`` (Utf8) — 설명.

        Raises
        ------
        없음
            존재하지 않는 그룹명은 빈 DataFrame.

        Example
        -------
        >>> e = Ecos()
        >>> cat = e.catalog(group="물가")

        Capabilities
        ------------
        catalog.toDataframe 위임 — 정적 카탈로그 DataFrame.
        AIContext: 사용자 universe 탐색 진입 — API 호출 0 (정적).
        Guide: group 미명시 시 전체.
        When: 분석 시작 전 universe 확인 / UI dropdown.
        How: ``_catalog.toDataframe(group)``.

        Requires
        --------
        catalog._INDICATORS 정적 사전.

        See Also
        --------
        group · search.
        """
        return _catalog.toDataframe(group)

    def search(self, keyword: str, *, limit: int | None = None) -> list[CatalogEntry]:
        """키워드로 카탈로그 검색.

        Parameters
        ----------
        keyword : str
            검색 키워드 (ID, 라벨, 설명에서 매칭).
        limit : int | None
            반환 행수 상한. None이면 전체.

        Returns
        -------
        list[CatalogEntry]
            매칭된 카탈로그 엔트리 리스트. 각 엔트리에
            id, label, group, frequency, unit, description 포함.

        Raises
        ------
        없음
            매칭 0건은 빈 리스트.

        Example
        -------
        >>> e = Ecos()
        >>> hits = e.search("물가", limit=5)

        Capabilities
        ------------
        catalog.search 위임 — substring 매칭.
        AIContext: 사용자 자연어 키워드 탐색 진입.
        Guide: case-insensitive substring. 한글/영문 모두.
        When: 카탈로그에서 특정 키워드 탐색 시.
        How: ``_catalog.search(keyword, limit=limit)``.

        Requires
        --------
        catalog 정적 사전.

        See Also
        --------
        catalog : DataFrame 형식.
        """
        return _catalog.search(keyword, limit=limit)

    def group(self, name: str, *, start: str | None = None, end: str | None = None) -> pl.DataFrame:
        """카탈로그 그룹 일괄 조회.

        Parameters
        ----------
        name : str
            그룹명 (국민계정/물가/금리/환율/통화·금융/산업·생산/무역/경기·심리/부동산/고용).
        start : str | None
            시작일. None이면 2000년부터.
        end : str | None
            종료일. None이면 최신까지.

        Returns
        -------
        pl.DataFrame
            컬럼: ``date`` (Date) — 관측일, 각 지표 ID (Float64) — 지표값.
            그룹 내 모든 지표를 wide 형태로 조인.

        Raises
        ------
        ValueError
            존재하지 않는 그룹명.

        Example
        -------
        >>> e = Ecos()
        >>> df = e.group("물가")

        Capabilities
        ------------
        catalog.getGroupIds → fetchMulti 위임.
        AIContext: 그룹 단위 한국 매크로 분석 진입 (예: 물가 그룹 일괄).
        Guide: 미존재 그룹 ValueError + 가용 list.
        When: 카테고리 단위 매크로 dashboard / regime 분석 시.
        How: ``getGroupIds(name)`` → ``fetchMulti(self._client, ids, ...)``.

        Requires
        --------
        ``ECOS_API_KEY`` + ``name`` 이 등록된 그룹.

        See Also
        --------
        catalog · compare.
        """
        ids = resolveGroupIds(_catalog, name)
        return fetchMulti(self._client, ids, start=start, end=end)

    # ── 정리 ──

    def close(self) -> None:
        """HTTP 세션 종료.

        Capabilities: EcosClient.close 위임.
        AIContext: Ecos facade 리소스 정리 진입.
        Guide: idempotent.
        When: dartlab 종료 / context manager exit 시.
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
        ``self._client`` (EcosClient).

        Example
        -------
        >>> e = Ecos()
        >>> e.close()

        See Also
        --------
        client.EcosClient.close : 위임 대상.
        """
        self._client.close()

    def __repr__(self) -> str:
        n = len(_catalog.getAllIds())
        return f"Ecos(catalog={n} series, groups={_catalog.getGroups()})"


__all__ = ["Ecos"]
