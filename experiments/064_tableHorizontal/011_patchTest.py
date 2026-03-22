"""
실험 ID: 064-011
실험명: 3가지 패치 검증

패치 내용:
1. _headerCells: 단위행 스킵 → 실제 헤더 반환
2. _dataRows: 단위행 이후의 실제 데이터 행 반환 (다중행 헤더 포함)
3. multi_year 분기(Q) 스킵 해제 — 분기에서도 당기값 추출

검증:
- 10종목 핵심 topic 수평화 테스트
- 기존 동작 깨지지 않는지 확인

실험일: 2026-03-17
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    _MULTI_YEAR_KW,
    _classifyStructure,
    _extractUnit,
    _isJunk,
    _normalizeItemName,
    _parseKeyValueOrMatrix,
    _parseMultiYear,
    splitSubtables,
)

_UNIT_ONLY_RE = re.compile(r"^\(?\s*단위\s*[:/]?\s*[^)]*\)?\s*$")


def _headerCellsPatched(lines: list[str]) -> list[str]:
    """단위행을 건너뛰고 실제 헤더 반환."""
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        # separator 스킵
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        # 비어있는 셀 제외
        nonEmpty = [c for c in cells if c.strip()]
        if not nonEmpty:
            continue
        # 단위행 스킵: 비어있지 않은 셀이 1개이고 단위 패턴
        if len(nonEmpty) == 1 and _UNIT_ONLY_RE.match(nonEmpty[0]):
            continue
        # 기준일행 스킵: (기준일 : ...)
        if len(nonEmpty) == 1 and re.match(r"^\(?\s*기준일\s*:", nonEmpty[0]):
            continue
        return [c for c in cells if c.strip()]
    return []


def _dataRowsPatched(lines: list[str]) -> list[list[str]]:
    """단위행/기준일행 뒤의 separator를 기준으로 데이터 행 반환."""
    rows = []
    # 마지막 separator 이후가 데이터
    lastSepIdx = -1
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            lastSepIdx = i

    if lastSepIdx < 0:
        return rows

    for line in lines[lastSepIdx + 1:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        rows.append(cells)
    return rows


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


def horizontalizePatched(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    periodCols: list[str],
) -> pl.DataFrame | None:
    """패치된 수평화 — 단위행 스킵 + Q multi_year 허용."""
    _SUFFIX_RE = re.compile(r"(사업)?부문$")
    _KISU_RE = re.compile(r"제\d+기\s*(?:\d*분기)?\s*\(?(당기|전기|전전기|당반기|전반기)\)?")

    def _normalizeItem(name: str) -> str:
        name = _SUFFIX_RE.sub("", name).strip()
        m = _KISU_RE.search(name)
        if m:
            return m.group(1)
        return name

    boRow = topicFrame.filter(
        (pl.col("blockOrder") == blockOrder) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return None

    allItems = []
    seenItems = set()
    periodItemVal = {}

    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue
        m = re.match(r"\d{4}", p)
        if m is None:
            continue
        pYear = int(m.group())

        for sub in splitSubtables(str(md)):
            # 패치: 단위행 스킵
            hc = _headerCellsPatched(sub)
            if _isJunk(hc):
                continue
            dr = _dataRowsPatched(sub)
            if not dr:
                continue

            structType = _classifyStructure(hc)

            # 패치: Q 기간에서도 multi_year 허용
            if structType == "multi_year":
                triples, _ = _parseMultiYear(sub, pYear)
                for rawItem, year, val in triples:
                    item = _normalizeItem(rawItem)
                    if year == str(pYear):
                        if item not in seenItems:
                            allItems.append(item)
                            seenItems.add(item)
                        if item not in periodItemVal:
                            periodItemVal[item] = {}
                        periodItemVal[item][p] = val

            elif structType in ("key_value", "matrix"):
                rows, _, _ = _parseKeyValueOrMatrix(sub)
                for rawItem, vals in rows:
                    item = _normalizeItem(rawItem)
                    val = " | ".join(v for v in vals if v).strip()
                    if val:
                        if item not in seenItems:
                            allItems.append(item)
                            seenItems.add(item)
                        if item not in periodItemVal:
                            periodItemVal[item] = {}
                        periodItemVal[item][p] = val

    # 품질 필터
    def _isJunkItem(name):
        stripped = re.sub(r"[,.\-\s]", "", name)
        return stripped.isdigit() or not stripped

    allItems = [item for item in allItems if not _isJunkItem(item)]
    if not allItems:
        return None

    # 이력형 감지
    periodItemSets = {}
    for item in allItems:
        for p in periodItemVal.get(item, {}):
            if p not in periodItemSets:
                periodItemSets[p] = set()
            periodItemSets[p].add(item)
    if len(periodItemSets) >= 2:
        sets = list(periodItemSets.values())
        totalOverlap = 0
        totalPairs = 0
        for i in range(len(sets)):
            for j in range(i + 1, min(i + 4, len(sets))):
                union = len(sets[i] | sets[j])
                inter = len(sets[i] & sets[j])
                if union > 0:
                    totalOverlap += inter / union
                    totalPairs += 1
        avgOverlap = totalOverlap / totalPairs if totalPairs else 0
        if avgOverlap < 0.3 and len(allItems) > 5:
            return None

    if len(allItems) > 50:
        return None

    usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
    if not usedPeriods:
        return None

    schema = {"항목": pl.Utf8}
    for p in usedPeriods:
        schema[p] = pl.Utf8

    rows = []
    for item in allItems:
        if not any(periodItemVal.get(item, {}).get(p) for p in usedPeriods):
            continue
        row = {"항목": item}
        for p in usedPeriods:
            row[p] = periodItemVal.get(item, {}).get(p)
        rows.append(row)

    if not rows:
        return None

    return pl.DataFrame(rows, schema=schema)


if __name__ == "__main__":
    # ── 패치1 검증: riskDerivative 000020 ──
    print("=" * 70)
    print("패치1 검증: riskDerivative 000020 bo=1 (단위행 스킵)")
    print("=" * 70)

    sec = sections("000020")
    periodCols = [c for c in sec.columns if _isPeriodCol(c)]
    topicFrame = sec.filter(pl.col("topic") == "riskDerivative")

    result = horizontalizePatched(topicFrame, 1, periodCols)
    if result is not None:
        print(f"성공: {result.height}행 × {len([c for c in result.columns if _isPeriodCol(c)])}기간")
        print(result.head(10))
    else:
        print("None — 여전히 실패")

    # ── 패치2 검증: salesOrder 000270 ──
    print("\n" + "=" * 70)
    print("패치2 검증: salesOrder 000270 bo=1 (단위행 스킵)")
    print("=" * 70)

    sec2 = sections("000270")
    periodCols2 = [c for c in sec2.columns if _isPeriodCol(c)]
    topicFrame2 = sec2.filter(pl.col("topic") == "salesOrder")

    result2 = horizontalizePatched(topicFrame2, 1, periodCols2)
    if result2 is not None:
        print(f"성공: {result2.height}행 × {len([c for c in result2.columns if _isPeriodCol(c)])}기간")
        print(result2.head(10))
    else:
        print("None — 여전히 실패")

    # ── 패치3 검증: employee 000720 Q기간 ──
    print("\n" + "=" * 70)
    print("패치3 검증: employee 000720 bo=9 (Q multi_year)")
    print("=" * 70)

    sec3 = sections("000720")
    periodCols3 = [c for c in sec3.columns if _isPeriodCol(c)]
    topicFrame3 = sec3.filter(pl.col("topic") == "employee")

    result3 = horizontalizePatched(topicFrame3, 9, periodCols3)
    if result3 is not None:
        print(f"성공: {result3.height}행 × {len([c for c in result3.columns if _isPeriodCol(c)])}기간")
        print(result3.head(10))
    else:
        print("None — 여전히 실패")

    # ── 10종목 핵심 5 topic 비교 ──
    print("\n" + "=" * 70)
    print("10종목 핵심 5 topic: 기존 vs 패치")
    print("=" * 70)

    stocks = [
        ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("035420", "네이버"),
        ("005380", "현대차"), ("068270", "셀트리온"), ("105560", "KB금융"),
        ("051910", "LG화학"), ("003550", "LG"), ("028260", "삼성물산"), ("034730", "SK"),
    ]
    topics = ["dividend", "audit", "companyOverview", "employee", "salesOrder"]

    from dartlab.engines.company.dart.docs.sections.tableParser import _dataRows as _drOld
    from dartlab.engines.company.dart.docs.sections.tableParser import _headerCells as _hcOld

    for code, name in stocks:
        try:
            sec = sections(code)
        except Exception:
            continue
        if sec is None:
            continue
        periodCols = [c for c in sec.columns if _isPeriodCol(c)]

        for topic in topics:
            topicFrame = sec.filter(pl.col("topic") == topic)
            tableRows = topicFrame.filter(pl.col("blockType") == "table")
            if tableRows.is_empty():
                continue

            blockOrders = sorted(tableRows["blockOrder"].unique().to_list())
            oldSuccess = 0
            newSuccess = 0

            for bo in blockOrders:
                # 기존 로직 (간략)
                boRow = topicFrame.filter(
                    (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
                )
                # old
                oldItems = set()
                for p in periodCols:
                    md = boRow[p][0] if p in boRow.columns else None
                    if md is None:
                        continue
                    m = re.match(r"\d{4}", p)
                    if m is None:
                        continue
                    pYear = int(m.group())
                    for sub in splitSubtables(str(md)):
                        hc = _hcOld(sub)
                        if _isJunk(hc):
                            continue
                        dr = _drOld(sub)
                        if not dr:
                            continue
                        st = _classifyStructure(hc)
                        if st == "multi_year" and "Q" not in p:
                            triples, _ = _parseMultiYear(sub, pYear)
                            for item, year, val in triples:
                                if year == str(pYear):
                                    oldItems.add(item)
                        elif st in ("key_value", "matrix"):
                            rows, _, _ = _parseKeyValueOrMatrix(sub)
                            for item, vals in rows:
                                if vals:
                                    oldItems.add(item)
                if oldItems:
                    oldSuccess += 1

                # new
                result = horizontalizePatched(topicFrame, bo, periodCols)
                if result is not None:
                    newSuccess += 1

            total = len(blockOrders)
            if newSuccess > oldSuccess:
                print(f"  {name} {topic}: {oldSuccess}/{total} → {newSuccess}/{total} (+{newSuccess-oldSuccess})")
            elif newSuccess < oldSuccess:
                print(f"  {name} {topic}: {oldSuccess}/{total} → {newSuccess}/{total} (REGRESSION -{oldSuccess-newSuccess})")
