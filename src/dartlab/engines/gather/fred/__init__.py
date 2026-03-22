"""FRED 경제지표 엔진 — 미국 연방준비은행 경제 데이터.

Usage::

    from dartlab.engines.gather.fred import Fred

    f = Fred()                                       # FRED_API_KEY 환경변수
    gdp = f.series("GDP")                            # GDP 시계열
    compare = f.compare(["GDP", "UNRATE"])            # 복수 비교
    corr = f.correlation(["GDP", "UNRATE", "FEDFUNDS"])  # 상관행렬
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from . import catalog as _catalog
from . import transform as _transform
from .client import FredClient
from .series import fetch_meta, fetch_multi, fetch_releases, fetch_series, search_series
from .types import CatalogEntry, FredError, SeriesMeta

if TYPE_CHECKING:
    pass


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

    def __init__(self, api_key: str | None = None) -> None:
        self._client = FredClient(api_key=api_key)

    # ── 시계열 조회 ──

    def series(
        self,
        series_id: str,
        *,
        start: str | None = None,
        end: str | None = None,
        frequency: str | None = None,
        aggregation: str = "avg",
    ) -> pl.DataFrame:
        """단일 시계열 조회 → DataFrame ``(date, value)``.

        Args:
            series_id: FRED 시리즈 ID (예: "GDP", "UNRATE", "CPIAUCSL").
            start: 시작일 (YYYY-MM-DD).
            end: 종료일.
            frequency: 리샘플 (d/w/bw/m/q/sa/a).
            aggregation: 집계 (avg/sum/eop).
        """
        return fetch_series(
            self._client, series_id,
            start=start, end=end, frequency=frequency, aggregation=aggregation,
        )

    def search(self, query: str, *, limit: int = 20) -> pl.DataFrame:
        """키워드 검색 → DataFrame ``(id, title, frequency, units, popularity)``."""
        return search_series(self._client, query, limit=limit)

    def meta(self, series_id: str) -> SeriesMeta:
        """시계열 메타데이터."""
        return fetch_meta(self._client, series_id)

    def compare(
        self,
        series_ids: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
        frequency: str | None = None,
    ) -> pl.DataFrame:
        """복수 시계열 비교 → wide DataFrame ``(date, GDP, UNRATE, ...)``."""
        return fetch_multi(
            self._client, series_ids,
            start=start, end=end, frequency=frequency,
        )

    def releases(self, *, limit: int = 20) -> pl.DataFrame:
        """최근 데이터 릴리즈 일정."""
        return fetch_releases(self._client, limit=limit)

    # ── 카탈로그 ──

    def group(self, name: str, *, start: str | None = None, end: str | None = None) -> pl.DataFrame:
        """카탈로그 그룹 일괄 조회.

        Args:
            name: 그룹명 (growth/inflation/rates/employment/markets/housing/money).
        """
        ids = _catalog.get_group_ids(name)
        if not ids:
            available = ", ".join(_catalog.get_groups())
            raise ValueError(f"그룹 '{name}'을 찾을 수 없습니다. 사용 가능: {available}")
        return fetch_multi(self._client, ids, start=start, end=end)

    def catalog(self, group: str | None = None) -> pl.DataFrame:
        """카탈로그 조회 → DataFrame ``(id, label, group, frequency, unit, description)``."""
        return _catalog.to_dataframe(group)

    # ── 변환 ──

    def yoy(self, series_id: str, *, start: str | None = None, end: str | None = None) -> pl.DataFrame:
        """전년 동기 대비 변화율 (%)."""
        df = self.series(series_id, start=start, end=end)
        return _transform.yoy(df)

    def mom(self, series_id: str, *, start: str | None = None, end: str | None = None) -> pl.DataFrame:
        """전월(전기) 대비 변화율 (%)."""
        df = self.series(series_id, start=start, end=end)
        return _transform.mom(df)

    def movingAverage(
        self, series_id: str, *, window: int = 12,
        start: str | None = None, end: str | None = None,
    ) -> pl.DataFrame:
        """이동평균."""
        df = self.series(series_id, start=start, end=end)
        return _transform.moving_average(df, window=window)

    # ── 분석 ──

    def correlation(
        self,
        series_ids: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame:
        """복수 시계열 간 상관행렬."""
        df = self.compare(series_ids, start=start, end=end)
        return _transform.correlation(df)

    def leadLag(
        self,
        id_a: str,
        id_b: str,
        *,
        max_lag: int = 12,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame:
        """선행/후행 상관분석.

        Returns:
            DataFrame ``(lag, correlation)``. 양수 lag = id_b가 후행.
        """
        df = self.compare([id_a, id_b], start=start, end=end)
        return _transform.lead_lag(df, id_a, id_b, max_lag=max_lag)

    # ── 정리 ──

    def close(self) -> None:
        """HTTP 세션 종료."""
        self._client.close()

    def __repr__(self) -> str:
        n = len(_catalog.get_all_ids())
        return f"Fred(catalog={n} series, groups={_catalog.get_groups()})"


__all__ = ["Fred", "FredError", "SeriesMeta", "CatalogEntry"]
