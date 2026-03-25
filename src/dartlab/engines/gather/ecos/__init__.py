"""ECOS 경제지표 엔진 — 한국은행 경제통계시스템.

Usage::

    from dartlab.engines.gather.ecos import Ecos

    e = Ecos()                                   # ECOS_API_KEY 환경변수
    cpi = e.series("CPI")                        # CPI 시계열
    compare = e.compare(["CPI", "BASE_RATE"])    # 복수 비교
    cat = e.catalog()                            # 카탈로그
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from . import catalog as _catalog
from .client import EcosClient
from .series import fetchMulti, fetchSeries
from .types import CatalogEntry, EcosError

if TYPE_CHECKING:
    pass


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
    ) -> pl.DataFrame:
        """단일 시계열 조회 → DataFrame ``(date, value)``.

        Args:
            indicatorId: 카탈로그 지표 ID (예: "GDP", "CPI", "BASE_RATE").
            start: 시작일 (YYYY, YYYYMM, YYYYMMDD).
            end: 종료일.
        """
        return fetchSeries(self._client, indicatorId, start=start, end=end)

    def compare(
        self,
        indicatorIds: list[str],
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame:
        """복수 시계열 비교 → wide DataFrame ``(date, CPI, BASE_RATE, ...)``."""
        return fetchMulti(self._client, indicatorIds, start=start, end=end)

    # ── 카탈로그 ──

    def catalog(self, group: str | None = None) -> pl.DataFrame:
        """카탈로그 조회 → DataFrame ``(id, label, group, frequency, unit, description)``."""
        return _catalog.toDataframe(group)

    def search(self, keyword: str) -> list[CatalogEntry]:
        """키워드로 카탈로그 검색."""
        return _catalog.search(keyword)

    def group(self, name: str, *, start: str | None = None, end: str | None = None) -> pl.DataFrame:
        """카탈로그 그룹 일괄 조회.

        Args:
            name: 그룹명 (국민계정/물가/금리/환율/통화·금융/산업·생산/무역/경기·심리/부동산/고용).
        """
        ids = _catalog.getGroupIds(name)
        if not ids:
            available = ", ".join(_catalog.getGroups())
            raise ValueError(f"그룹 '{name}'을 찾을 수 없습니다. 사용 가능: {available}")
        return fetchMulti(self._client, ids, start=start, end=end)

    # ── 정리 ──

    def close(self) -> None:
        """HTTP 세션 종료."""
        self._client.close()

    def __repr__(self) -> str:
        n = len(_catalog.getAllIds())
        return f"Ecos(catalog={n} series, groups={_catalog.getGroups()})"


__all__ = ["Ecos", "EcosError", "CatalogEntry"]
