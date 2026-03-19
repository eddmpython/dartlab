"""show() 공통 헬퍼. DART/EDGAR Company.show()에서 공유."""

from __future__ import annotations

import re

import polars as pl

_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def isPeriodColumn(name: str) -> bool:
    """컬럼명이 기간 패턴(YYYY 또는 YYYYQ1~Q4)인지 판별."""
    return bool(_PERIOD_COLUMN_RE.fullmatch(name))


def transposeToVertical(wide: pl.DataFrame, periods: list[str]) -> pl.DataFrame | None:
    """수평화 DataFrame에서 요청 기간 컬럼만 추출.

    Args:
        wide: 항목(행) × 기간(열) 수평화 DataFrame.
        periods: 추출할 기간 목록.

    Returns:
        필터된 DataFrame 또는 None (매칭 기간 없을 때).
    """
    labelCol = wide.columns[0]
    periodCols = [c for c in wide.columns if isPeriodColumn(c)]
    matched: list[str] = []
    for p in periods:
        if p in periodCols:
            matched.append(p)
        elif "Q" not in p and f"{p}Q4" in periodCols:
            matched.append(f"{p}Q4")
    if not matched:
        return None
    return wide.select([labelCol] + matched)


def buildBlockIndex(topicRows: pl.DataFrame) -> pl.DataFrame:
    """topic의 블록 목차 DataFrame. DART/EDGAR Company._buildBlockIndex 공통 구현."""
    periodCols = [c for c in topicRows.columns if isPeriodColumn(c)]
    rows: list[dict[str, object]] = []
    seen: set[int] = set()
    hasBlockOrder = "blockOrder" in topicRows.columns

    for row in topicRows.iter_rows(named=True):
        bt = row.get("blockType", "text")
        source = row.get("source", "docs")

        if hasBlockOrder:
            bo = row.get("blockOrder", 0)
            if bo is None:
                bo = len(seen)
        else:
            bo = len(seen)

        if bo in seen:
            continue
        seen.add(bo)

        preview = ""
        if source in ("finance", "report"):
            preview = f"({source})"
        else:
            for p in reversed(periodCols):
                val = row.get(p)
                if val:
                    preview = str(val)[:50]
                    break
        rows.append({"block": bo, "type": bt, "source": source, "preview": preview})

    return pl.DataFrame(rows)
