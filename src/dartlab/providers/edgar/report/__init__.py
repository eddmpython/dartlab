"""EDGAR report extractors — 10-K/XBRL에서 구조화 데이터 추출."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


def edgarFinancePath(cik: str) -> Path:
    """EDGAR finance parquet 경로. 전체 report/notes에서 공용."""
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / "edgar" / "finance" / f"{cik}.parquet"


def loadXbrlTags(
    company: "Company",
    tagPattern: str,
    forms: list[str] | None = None,
    unitFilter: str | None = None,
) -> pl.DataFrame | None:
    """CIK parquet에서 태그 패턴으로 XBRL 데이터를 로드한다.

    Parameters
    ----------
    company : Company
        EdgarCompany 인스턴스 (cik 속성 필요).
    tagPattern : str
        ``pl.col("tag").str.contains()`` 에 전달할 정규식.
    forms : list[str] | None
        필터할 form 유형. 기본 ``["10-K", "20-F"]``.
    unitFilter : str | None
        unit 컬럼 정규식 필터. 예: ``"(?i)USD"``.

    Returns
    -------
    pl.DataFrame | None
        매칭된 행. 없으면 None.
    """
    cik = getattr(company, "cik", None)
    if not cik:
        return None

    path = edgarFinancePath(cik)
    if not path.exists():
        return None

    if forms is None:
        forms = ["10-K", "20-F"]

    try:
        expr = pl.col("tag").str.contains(tagPattern) & pl.col("form").is_in(forms)
        if unitFilter:
            expr = expr & pl.col("unit").str.contains(unitFilter)
        df = pl.scan_parquet(path).filter(expr).collect()
        return df if not df.is_empty() else None
    except (pl.exceptions.ComputeError, OSError):
        return None
