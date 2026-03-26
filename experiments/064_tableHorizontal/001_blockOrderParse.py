"""
실험 ID: 064-001
실험명: blockOrder별 독립 테이블 파싱 → 기간 간 병합

목적:
- sections의 table 블록을 blockOrder별로 독립 파싱
- 같은 blockOrder의 마크다운 테이블을 기간별로 파싱 후 항목명 기준 outer join
- text-table 교차 순서로 최종 출력

가설:
1. 같은 blockOrder의 테이블은 기간별로 구조가 유사하여 항목명 정확 매칭률 80%+
2. multi_year 테이블에서 "당기" 값만 추출하면 기간 간 중복 없이 수평화 가능
3. blockOrder 순서로 text-table 교차 출력이 가능

방법:
1. 삼성전자 companyOverview topic에서 table 블록 추출
2. 각 blockOrder별, 각 기간별 마크다운을 독립 파싱
3. 항목명 기준 outer join → 항목×기간 매트릭스
4. text와 교차 배치하여 최종 DataFrame 구성

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import re

import polars as pl

from dartlab.providers.dart.docs.sections.pipeline import sections
from dartlab.providers.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _extractUnit,
    _headerCells,
    _isJunk,
    _normalizeItemName,
    _parseKeyValueOrMatrix,
    _parseMultiYear,
    splitSubtables,
)


def parseSingleCellTable(md: str, periodYear: int) -> list[dict]:
    """단일 기간 셀의 마크다운 테이블을 파싱.

    Returns:
        [{"항목": str, "값": str, "tableType": str, "subtableIdx": int}, ...]
    """
    results = []
    for subIdx, sub in enumerate(splitSubtables(md)):
        hc = _headerCells(sub)
        if _isJunk(hc):
            continue
        dr = _dataRows(sub)
        if not dr:
            continue

        structType = _classifyStructure(hc)
        unit = _extractUnit(sub) or ""

        if structType == "multi_year":
            triples, u = _parseMultiYear(sub, periodYear)
            if u:
                unit = u
            # "당기"(= periodYear) 값만 추출
            for item, year, val in triples:
                if year == str(periodYear):
                    results.append({
                        "항목": item,
                        "값": val,
                        "tableType": "multi_year",
                        "subtableIdx": subIdx,
                        "단위": unit,
                    })

        elif structType in ("key_value", "matrix"):
            rows, headerNames, u = _parseKeyValueOrMatrix(sub)
            if u:
                unit = u
            for item, vals in rows:
                val = " | ".join(v for v in vals if v).strip()
                if val:
                    results.append({
                        "항목": item,
                        "값": val,
                        "tableType": structType,
                        "subtableIdx": subIdx,
                        "단위": unit,
                    })

    return results


def horizontalizeTableBlock(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    periodCols: list[str],
) -> pl.DataFrame | None:
    """하나의 blockOrder table 행을 기간별로 파싱 → 항목×기간 매트릭스."""
    boRow = topicFrame.filter(pl.col("blockOrder") == blockOrder)
    if boRow.is_empty():
        return None

    # 각 기간별 파싱
    allItems: list[str] = []
    seenItems: set[str] = set()
    periodItemVal: dict[str, dict[str, str]] = {}

    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue

        pYear = int(re.match(r"\d{4}", p).group()) if re.match(r"\d{4}", p) else None
        if pYear is None:
            continue

        parsed = parseSingleCellTable(str(md), pYear)
        for entry in parsed:
            item = entry["항목"]
            if item not in seenItems:
                allItems.append(item)
                seenItems.add(item)
            if item not in periodItemVal:
                periodItemVal[item] = {}
            periodItemVal[item][p] = entry["값"]

    if not allItems:
        return None

    # 항목×기간 DataFrame 구성 (전부 str)
    usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
    schema = {"항목": pl.Utf8}
    for p in usedPeriods:
        schema[p] = pl.Utf8

    rows = []
    for item in allItems:
        row_data: dict[str, str | None] = {"항목": item}
        for p in usedPeriods:
            row_data[p] = periodItemVal.get(item, {}).get(p)
        rows.append(row_data)

    return pl.DataFrame(rows, schema=schema)


def buildInterleavedView(
    topicFrame: pl.DataFrame,
    periodCols: list[str],
) -> list[tuple[int, str, pl.DataFrame]]:
    """topic의 전체 블록을 blockOrder 순서로 text/table 교차 리스트 반환.

    Returns:
        [(blockOrder, "text"|"table", DataFrame), ...]
    """
    if "blockOrder" not in topicFrame.columns or "blockType" not in topicFrame.columns:
        return []

    blocks = []
    blockOrders = sorted(topicFrame["blockOrder"].unique().to_list())

    for bo in blockOrders:
        boRows = topicFrame.filter(pl.col("blockOrder") == bo)
        bt = boRows["blockType"][0]

        if bt == "text":
            # text: 기간 컬럼만 추출
            keepCols = [c for c in periodCols if c in boRows.columns]
            if keepCols:
                textDf = boRows.select(keepCols)
                # null만 있는 기간 제거
                keepCols2 = [c for c in keepCols if textDf[c].null_count() < textDf.height]
                if keepCols2:
                    blocks.append((bo, "text", textDf.select(keepCols2)))

        elif bt == "table":
            tableDf = horizontalizeTableBlock(topicFrame, bo, periodCols)
            if tableDf is not None:
                blocks.append((bo, "table", tableDf))

    return blocks


if __name__ == "__main__":
    sec = sections("005930")
    if sec is None:
        print("sections None")
        sys.exit(1)

    periodCols = [c for c in sec.columns if c not in ("chapter", "topic", "blockType", "blockOrder")]

    # companyOverview 테스트
    topic = "companyOverview"
    topicFrame = sec.filter(pl.col("topic") == topic)

    print(f"=== {topic} ===")
    print(f"전체 행: {topicFrame.height}")
    print(f"blockOrder 범위: {topicFrame['blockOrder'].min()} ~ {topicFrame['blockOrder'].max()}")
    print()

    blocks = buildInterleavedView(topicFrame, periodCols)

    for bo, bt, df in blocks:
        print(f"[blockOrder={bo}] {bt}")
        if bt == "text":
            # 최근 3기간만 미리보기
            recent = periodCols[-3:]
            for p in recent:
                if p in df.columns:
                    val = df[p][0]
                    if val:
                        print(f"  {p}: {str(val)[:80]}...")
        elif bt == "table":
            print(f"  항목 수: {df.height}")
            print(f"  컬럼: {df.columns}")
            # 최근 3기간으로 미리보기
            recent = ["항목"] + [c for c in periodCols[-3:] if c in df.columns]
            preview = df.select([c for c in recent if c in df.columns])
            print(preview)
        print()

    print(f"총 {len(blocks)}개 블록 (text/table 교차)")
    text_count = sum(1 for _, bt, _ in blocks if bt == "text")
    table_count = sum(1 for _, bt, _ in blocks if bt == "table")
    print(f"  text: {text_count}, table: {table_count}")
