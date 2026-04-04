"""EDGAR report extractors — 10-K/XBRL에서 구조화 데이터 추출."""

from __future__ import annotations

from pathlib import Path


def edgarFinancePath(cik: str) -> Path:
    """EDGAR finance parquet 경로. 전체 report/notes에서 공용."""
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / "edgar" / "finance" / f"{cik}.parquet"
