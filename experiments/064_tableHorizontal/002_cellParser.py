"""
실험 ID: 064-002
실험명: Layer 1 cell parser — ParsedSubtable 구조 확립

목적:
- 단일 셀 마크다운을 서브테이블별로 독립 파싱하는 구조 확립
- ParsedSubtable 데이터클래스로 파싱 결과 표준화
- dividend, audit 등에서 서브테이블 경계가 유지되는지 검증

가설:
1. 서브테이블별 독립 파싱으로 항목 혼합 방지
2. multi_year에서 당기 값 + 전기/전전기 검증 값 분리 가능
3. dividend 5종목에서 서브테이블 구조 일관성 90%+

방법:
1. ParsedSubtable 데이터클래스 정의
2. parseCellSubtables() 함수: 마크다운 → list[ParsedSubtable]
3. dividend, audit에서 5종목 검증

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import re

from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.engines.dart.docs.sections.tableParser import (
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


@dataclass
class ParsedSubtable:
    """단일 서브테이블 파싱 결과."""

    subtableIdx: int
    tableType: str  # multi_year, key_value, matrix, skip
    unit: str | None = None
    headerNames: list[str] = field(default_factory=list)
    # (항목명, 값 리스트) — multi_year는 값이 1개(당기), matrix는 여러 개
    items: list[tuple[str, list[str]]] = field(default_factory=list)
    # multi_year 전용: 전기/전전기 검증용 {항목: {연도: 값}}
    priorValues: dict[str, dict[str, str]] = field(default_factory=dict)
    rowCount: int = 0


def parseCellSubtables(md: str, periodYear: int) -> list[ParsedSubtable]:
    """단일 기간 셀의 마크다운 → 서브테이블별 ParsedSubtable 리스트."""
    results = []
    for subIdx, sub in enumerate(splitSubtables(md)):
        hc = _headerCells(sub)
        if _isJunk(hc):
            continue
        dr = _dataRows(sub)
        if not dr:
            continue

        structType = _classifyStructure(hc)
        unit = _extractUnit(sub)

        if structType == "multi_year":
            triples, u = _parseMultiYear(sub, periodYear)
            if u:
                unit = u

            currentItems: list[tuple[str, list[str]]] = []
            priorValues: dict[str, dict[str, str]] = {}
            seenItems: list[str] = []

            for item, year, val in triples:
                if item not in seenItems:
                    seenItems.append(item)
                if year == str(periodYear):
                    currentItems.append((item, [val]))
                else:
                    if item not in priorValues:
                        priorValues[item] = {}
                    priorValues[item][year] = val

            results.append(ParsedSubtable(
                subtableIdx=subIdx,
                tableType="multi_year",
                unit=unit,
                headerNames=[],
                items=currentItems,
                priorValues=priorValues,
                rowCount=len(dr),
            ))

        elif structType in ("key_value", "matrix"):
            rows, headerNames, u = _parseKeyValueOrMatrix(sub)
            if u:
                unit = u

            items = []
            for item, vals in rows:
                items.append((item, [v for v in vals if v]))

            results.append(ParsedSubtable(
                subtableIdx=subIdx,
                tableType=structType,
                unit=unit,
                headerNames=headerNames,
                items=items,
                rowCount=len(dr),
            ))

    return results


def _printSubtable(st: ParsedSubtable, indent: str = "  ") -> None:
    print(f"{indent}[sub={st.subtableIdx}] {st.tableType} | {st.rowCount}행 | 단위={st.unit}")
    if st.headerNames:
        print(f"{indent}  헤더: {st.headerNames[:5]}")
    print(f"{indent}  항목 {len(st.items)}개:")
    for item, vals in st.items[:5]:
        print(f"{indent}    {item}: {vals[:3]}")
    if len(st.items) > 5:
        print(f"{indent}    ... +{len(st.items)-5}개")
    if st.priorValues:
        print(f"{indent}  검증용(전기 등): {len(st.priorValues)}개 항목")
        for item, yv in list(st.priorValues.items())[:3]:
            print(f"{indent}    {item}: {yv}")


if __name__ == "__main__":
    import polars as pl

    stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "네이버"),
        ("005380", "현대차"),
        ("068270", "셀트리온"),
    ]

    # ── dividend 검증 ──
    print("=" * 60)
    print("dividend 서브테이블 구조 검증")
    print("=" * 60)

    for code, name in stocks:
        sec = sections(code)
        if sec is None:
            print(f"\n{name}: sections None")
            continue

        topicFrame = sec.filter(pl.col("topic") == "dividend")
        if topicFrame.is_empty():
            print(f"\n{name}: dividend 없음")
            continue

        tableRows = topicFrame.filter(pl.col("blockType") == "table")
        print(f"\n{name} dividend: {tableRows.height} table 블록")

        for row in tableRows.iter_rows(named=True):
            bo = row["blockOrder"]
            # 2024 연간 보고서
            md = row.get("2024") or row.get("2023")
            if md is None:
                continue
            period = "2024" if row.get("2024") else "2023"
            pYear = int(period[:4])

            subs = parseCellSubtables(str(md), pYear)
            print(f"  blockOrder={bo}, period={period}: {len(subs)}개 서브테이블")
            for st in subs:
                _printSubtable(st, "    ")

    # ── audit 검증 ──
    print("\n" + "=" * 60)
    print("audit 서브테이블 구조 검증 (삼성전자)")
    print("=" * 60)

    sec = sections("005930")
    topicFrame = sec.filter(pl.col("topic") == "audit")
    tableRows = topicFrame.filter(pl.col("blockType") == "table")
    print(f"audit: {tableRows.height} table 블록")

    for row in tableRows.iter_rows(named=True):
        bo = row["blockOrder"]
        md = row.get("2024")
        if md is None:
            continue

        subs = parseCellSubtables(str(md), 2024)
        print(f"\n  blockOrder={bo}: {len(subs)}개 서브테이블")
        for st in subs:
            _printSubtable(st, "    ")

    # ── 서브테이블 수 일관성 ──
    print("\n" + "=" * 60)
    print("dividend blockOrder=1 서브테이블 수 일관성")
    print("=" * 60)

    for code, name in stocks:
        sec = sections(code)
        if sec is None:
            continue
        topicFrame = sec.filter(
            (pl.col("topic") == "dividend") & (pl.col("blockType") == "table") & (pl.col("blockOrder") == 1)
        )
        if topicFrame.is_empty():
            continue

        periodCols = [c for c in sec.columns if re.match(r"\d{4}$", c)]  # 연간만
        counts = []
        for p in periodCols:
            md = topicFrame[p][0]
            if md is None:
                continue
            subs = parseCellSubtables(str(md), int(p))
            counts.append((p, len(subs), [s.tableType for s in subs]))

        print(f"\n{name}:")
        for p, cnt, types in counts[-5:]:
            print(f"  {p}: {cnt}개 서브테이블 {types}")
