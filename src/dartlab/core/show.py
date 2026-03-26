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
    periodCols = [c for c in wide.columns if isPeriodColumn(c)]
    metaCols = [c for c in wide.columns if not isPeriodColumn(c)]
    matched: list[str] = []
    for p in periods:
        if p in periodCols:
            matched.append(p)
        elif "Q" not in p and f"{p}Q4" in periodCols:
            matched.append(f"{p}Q4")
    if not matched:
        return None
    return wide.select(metaCols + matched)


def selectFromShow(
    df: pl.DataFrame,
    indList: list[str] | None = None,
    colList: list[str] | None = None,
) -> pl.DataFrame | None:
    """show() 결과에서 indList(행) + colList(열) 필터."""
    if df.is_empty():
        return None

    result = df

    # 행 필터 — indList
    if indList is not None:
        metaCols = [c for c in result.columns if not isPeriodColumn(c)]
        matchCol = None
        for mc in metaCols:
            hits = result.filter(pl.col(mc).is_in(indList))
            if not hits.is_empty():
                matchCol = mc
                result = hits
                break
        if matchCol is None:
            return None

    # 열 필터 — colList
    if colList is not None:
        periodCols = [c for c in result.columns if isPeriodColumn(c)]
        metaCols = [c for c in result.columns if not isPeriodColumn(c)]
        matched: list[str] = []
        for p in colList:
            if p in periodCols:
                matched.append(p)
            elif "Q" not in p and f"{p}Q4" in periodCols:
                matched.append(f"{p}Q4")
        if not matched:
            return None
        result = result.select(metaCols + matched)

    return result if not result.is_empty() else None


def buildBlockIndex(topicRows: pl.DataFrame) -> pl.DataFrame:
    """topic의 블록 목차 DataFrame. DART/EDGAR Company._buildBlockIndex 공통 구현."""
    periodCols = [c for c in topicRows.columns if isPeriodColumn(c)]
    rows: list[dict[str, object]] = []
    seen: set[int] = set()
    hasBlockOrder = "blockOrder" in topicRows.columns

    # 컬럼 데이터 한 번에 추출
    btList = topicRows["blockType"].to_list() if "blockType" in topicRows.columns else None
    srcList = topicRows["source"].to_list() if "source" in topicRows.columns else None
    boList = topicRows["blockOrder"].to_list() if hasBlockOrder else None
    periodData = {p: topicRows[p].to_list() for p in periodCols}

    for i in range(topicRows.height):
        bt = btList[i] if btList else "text"
        source = srcList[i] if srcList else "docs"

        if hasBlockOrder:
            bo = boList[i]
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
                val = periodData[p][i]
                if val:
                    preview = str(val)[:50]
                    break
        rows.append({"block": bo, "type": bt, "source": source, "preview": preview})

    return pl.DataFrame(rows)
