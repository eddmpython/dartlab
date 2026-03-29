"""show() 공통 헬퍼. DART/EDGAR Company.show()에서 공유."""

from __future__ import annotations

import html
import re
import unicodedata

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


def normalizeItemKey(name: str) -> str:
    """항목명 정규화: NFKC + 공백제거 + HTML entity + lower."""
    name = html.unescape(name)
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"\s+", "", name)
    name = re.sub(r"[&](cr|nbsp|amp);", "", name)
    return name.lower()


def _cascadeFilterRows(
    df: pl.DataFrame,
    mc: str,
    indList: list[str],
) -> pl.DataFrame | None:
    """4단계 cascade 매칭: exact → normalized → contains → fuzzy."""
    # 1) exact match
    hits = df.filter(pl.col(mc).is_in(indList))
    if not hits.is_empty():
        return hits

    # 2) normalized exact
    colVals = df[mc].to_list()
    normMap: dict[str, list[int]] = {}
    for i, v in enumerate(colVals):
        if v is not None:
            normMap.setdefault(normalizeItemKey(str(v)), []).append(i)

    normQueries = [normalizeItemKey(q) for q in indList]
    matchedIdx: list[int] = []
    for nq in normQueries:
        if nq in normMap:
            matchedIdx.extend(normMap[nq])
    if matchedIdx:
        return df[sorted(set(matchedIdx))]

    # 3) contains (substring 양방향)
    matchedIdx = []
    for nq in normQueries:
        for nk, idxList in normMap.items():
            if nq in nk or nk in nq:
                matchedIdx.extend(idxList)
    if matchedIdx:
        return df[sorted(set(matchedIdx))]

    # 4) fuzzy
    import difflib

    allNormKeys = list(normMap.keys())
    matchedIdx = []
    for nq in normQueries:
        close = difflib.get_close_matches(nq, allNormKeys, n=3, cutoff=0.7)
        for ck in close:
            matchedIdx.extend(normMap[ck])
    if matchedIdx:
        return df[sorted(set(matchedIdx))]

    return None


def selectFromShow(
    df: pl.DataFrame,
    indList: list[str] | None = None,
    colList: list[str] | None = None,
) -> pl.DataFrame | None:
    """show() 결과에서 indList(행) + colList(열) 필터."""
    if df.is_empty():
        return None

    result = df

    # 행 필터 — indList (cascade 매칭)
    if indList is not None:
        metaCols = [c for c in result.columns if not isPeriodColumn(c)]
        matched = None
        for mc in metaCols:
            matched = _cascadeFilterRows(result, mc, indList)
            if matched is not None:
                result = matched
                break
        if matched is None:
            return None

    # 열 필터 — colList
    if colList is not None:
        periodCols = [c for c in result.columns if isPeriodColumn(c)]
        metaCols = [c for c in result.columns if not isPeriodColumn(c)]
        matchedPeriods: list[str] = []
        for p in colList:
            if p in periodCols:
                matchedPeriods.append(p)
            elif "Q" not in p and f"{p}Q4" in periodCols:
                matchedPeriods.append(f"{p}Q4")
        if not matchedPeriods:
            return None
        result = result.select(metaCols + matchedPeriods)

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
