"""
실험 ID: 064-005
실험명: 개선된 cell parser — 4대 과제 해결

목적:
- 과제1: multi_year 빈 컬럼 스킵 → 당기 값 완전 추출
- 과제2: matrix 헤더별 컬럼 분리 (파이프 합침 제거)
- 과제3: 기수 포함 항목명 정규화 (제55기(당기) → 당기)
- 과제4: 서브테이블 매칭 — 헤더 유사도 기반

가설:
1. 빈 컬럼 스킵으로 dividend 당기 추출 10항목 → 4항목 문제 해결
2. matrix 헤더 분리로 majorHolder 등 구조 유지

방법:
1. _parseMultiYear 개선 — 빈 컬럼 필터
2. parseCellSubtables 개선 — matrix 헤더별 분리
3. 기수 항목명 정규화 함수
4. dividend/audit 재검증

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

from dartlab.engines.company.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _extractUnit,
    _headerCells,
    _isJunk,
    _normalizeItemName,
    _STOCK_TYPES,
    splitSubtables,
)


# ── 개선된 multi_year 파서 ──

def parseMultiYearImproved(sub: list[str], periodYear: int) -> tuple[list[tuple[str, str, str]], str | None]:
    """개선: 빈 컬럼 스킵 + 보통주/우선주 처리."""
    sepIdx = -1
    for i, line in enumerate(sub):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            sepIdx = i
            break

    if sepIdx < 0 or sepIdx + 1 >= len(sub):
        return [], None

    # 기수 행
    kisuCells = [c.strip() for c in sub[sepIdx + 1].strip("|").split("|")]
    kisuNums = []
    kisuPositions = []  # 기수가 있는 컬럼 인덱스
    for ci, cell in enumerate(kisuCells):
        m = re.search(r"제\s*(\d+)\s*기", cell)
        if m:
            kisuNums.append(int(m.group(1)))
            kisuPositions.append(ci)

    if not kisuNums:
        return [], None

    maxKisu = max(kisuNums)
    kisuToYear = {kn: str(periodYear - maxKisu + kn) for kn in kisuNums}

    unit = _extractUnit(sub)
    triples: list[tuple[str, str, str]] = []
    prevItem = ""

    for line in sub[sepIdx + 2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        if not cells or not cells[0].strip():
            continue

        first = cells[0].strip()
        if first.startswith("※"):
            continue

        # 보통주/우선주 연속행
        if first in _STOCK_TYPES and prevItem:
            itemName = _normalizeItemName(f"{prevItem}-{first}")
            # 보통주/우선주 행은 값이 1번 컬럼부터 시작
            valCells = cells[1:]
        elif len(cells) > 1 and cells[1].strip() in _STOCK_TYPES:
            stockType = cells[1].strip()
            itemName = _normalizeItemName(f"{first}-{stockType}")
            valCells = cells[2:]
            prevItem = first
        else:
            itemName = _normalizeItemName(first)
            # 핵심 개선: 빈 컬럼 스킵
            # 값은 행 끝에서 기수 개수만큼 역순으로 추출
            nonEmptyCells = [c.strip() for c in cells[1:] if c.strip() and c.strip() != "-"]
            # 전체 값 컬럼 = 빈 컬럼 제외하고 뒤에서 기수 개수만큼
            allValCells = [c.strip() for c in cells[1:]]
            # 실제 값은 뒤에서부터 기수 개수만큼
            valCells = allValCells[-len(kisuNums):] if len(allValCells) >= len(kisuNums) else allValCells
            prevItem = first

            # valCells와 kisuNums를 직접 매핑 (역순)
            sortedPairs = sorted(zip(kisuNums, valCells), key=lambda x: -x[0])
            for kn, val in sortedPairs:
                val = val.strip()
                if val and val != "-" and val not in _STOCK_TYPES:
                    triples.append((itemName, kisuToYear[kn], val))
            continue

        # 보통주/우선주 경로: 기존 로직
        sortedKisu = sorted(kisuNums, reverse=True)
        for i, kn in enumerate(sortedKisu):
            if i < len(valCells):
                val = valCells[i].strip()
                if val and val != "-" and val not in _STOCK_TYPES:
                    triples.append((itemName, kisuToYear[kn], val))

    return triples, unit


# ── 기수 항목명 정규화 ──

_KISU_ITEM_RE = re.compile(r"제\d+기\s*(?:\d*분기)?\s*\(?(당기|전기|전전기|당반기|전반기)\)?")

def normalizeKisuItem(item: str) -> str:
    """'제55기(당기)' → '당기', '제54기(전기)' → '전기'."""
    m = _KISU_ITEM_RE.search(item)
    if m:
        return m.group(1)
    # 제55기만 있고 (당기) 없는 경우
    m2 = re.match(r"^제(\d+)기\s*(?:(\d+)분기)?(?:말)?$", item.strip())
    if m2:
        return item  # 그대로 유지 (연도 변환은 호출측에서)
    return item


# ── 개선된 ParsedSubtable ──

@dataclass
class ParsedSubtable:
    subtableIdx: int
    tableType: str
    unit: str | None = None
    headerNames: list[str] = field(default_factory=list)
    items: list[tuple[str, list[str]]] = field(default_factory=list)
    priorValues: dict[str, dict[str, str]] = field(default_factory=dict)
    rowCount: int = 0


def parseCellSubtablesV2(md: str, periodYear: int) -> list[ParsedSubtable]:
    """개선된 셀 파서 — multi_year 빈컬럼 수정 + matrix 헤더 분리."""
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
            triples, u = parseMultiYearImproved(sub, periodYear)
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
                items=currentItems,
                priorValues=priorValues,
                rowCount=len(dr),
            ))

        elif structType in ("key_value", "matrix"):
            headerNames = [_normalizeItemName(h) for h in hc[1:]] if len(hc) > 1 else []

            items = []
            for row in dr:
                if not row or not row[0].strip():
                    continue
                first = row[0].strip()
                if first.startswith("※") or first.startswith("☞"):
                    continue

                item = normalizeKisuItem(_normalizeItemName(first))
                vals = [c.strip() for c in row[1:]]

                if structType == "matrix" and headerNames:
                    # 헤더별 분리: (항목_헤더, [값]) 쌍으로
                    for hi, hname in enumerate(headerNames):
                        val = vals[hi] if hi < len(vals) else ""
                        if val and val != "-":
                            items.append((f"{item}_{hname}" if hname else item, [val]))
                else:
                    # key_value: 그대로
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


if __name__ == "__main__":
    from dartlab.engines.company.dart.docs.sections.pipeline import sections
    import polars as pl

    # ── 과제1 검증: dividend 당기 추출 개선 ──
    print("=" * 70)
    print("과제1: dividend 당기 추출 — 기존 vs 개선")
    print("=" * 70)

    sec = sections("005930")
    topicFrame = sec.filter(
        (pl.col("topic") == "dividend") & (pl.col("blockType") == "table") & (pl.col("blockOrder") == 1)
    )
    md = topicFrame["2024"][0]

    # 기존
    from dartlab.engines.company.dart.docs.sections.tableParser import _parseMultiYear
    subs_old = splitSubtables(str(md))
    for sub in subs_old:
        hc = _headerCells(sub)
        if _classifyStructure(hc) == "multi_year":
            triples_old, _ = _parseMultiYear(sub, 2024)
            old_current = [(item, val) for item, year, val in triples_old if year == "2024"]
            print(f"기존: 당기(2024) 항목 {len(old_current)}개")
            for item, val in old_current:
                print(f"  {item} = {val}")

    # 개선
    subs_new = parseCellSubtablesV2(str(md), 2024)
    for sub in subs_new:
        if sub.tableType == "multi_year":
            print(f"\n개선: 당기(2024) 항목 {len(sub.items)}개")
            for item, vals in sub.items:
                print(f"  {item} = {vals}")
            print(f"\n검증용(전기): {len(sub.priorValues)}개 항목")

    # ── 과제2 검증: audit matrix 헤더 분리 ──
    print("\n" + "=" * 70)
    print("과제2: audit matrix 헤더별 분리")
    print("=" * 70)

    topicFrame = sec.filter(
        (pl.col("topic") == "audit") & (pl.col("blockType") == "table") & (pl.col("blockOrder") == 1)
    )
    md = topicFrame["2024"][0]
    subs = parseCellSubtablesV2(str(md), 2024)
    for sub in subs:
        print(f"\n  [sub={sub.subtableIdx}] {sub.tableType} | {sub.rowCount}행 | 헤더={sub.headerNames[:4]}")
        for item, vals in sub.items[:6]:
            print(f"    {item}: {vals}")
        if len(sub.items) > 6:
            print(f"    ... +{len(sub.items)-6}개")

    # ── 과제3 검증: 기수 항목명 정규화 ──
    print("\n" + "=" * 70)
    print("과제3: 기수 항목명 정규화")
    print("=" * 70)

    tests = [
        "제55기(당기)", "제54기(전기)", "제53기(전전기)",
        "제55기1분기(당기)", "제55기반기(당기)",
        "제55기", "제55기말",
        "삼성전자㈜", "미등기임원",
    ]
    for t in tests:
        print(f"  {t:30s} → {normalizeKisuItem(t)}")

    # ── 5종목 dividend 개선 결과 ──
    print("\n" + "=" * 70)
    print("5종목 dividend 당기 추출 (개선)")
    print("=" * 70)

    stocks = [("005930", "삼성전자"), ("000660", "SK하이닉스"), ("035420", "네이버"), ("005380", "현대차")]
    for code, name in stocks:
        sec = sections(code)
        if sec is None:
            continue
        topicFrame = sec.filter(
            (pl.col("topic") == "dividend") & (pl.col("blockType") == "table") & (pl.col("blockOrder") == 1)
        )
        if topicFrame.is_empty():
            continue
        md = topicFrame.get_column("2024")[0] if "2024" in topicFrame.columns else None
        if md is None:
            continue

        subs = parseCellSubtablesV2(str(md), 2024)
        for sub in subs:
            if sub.tableType == "multi_year":
                print(f"\n{name}: 당기 {len(sub.items)}항목, 전기 {len(sub.priorValues)}항목")
                for item, vals in sub.items:
                    print(f"  {item} = {vals[0]}")
