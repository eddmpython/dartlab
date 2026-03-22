"""
실험 ID: 064-004
실험명: Layer 2 horizontalizer — 현황형 (key_value/matrix) 수평화

목적:
- key_value/matrix 테이블의 기간 간 수평화
- 같은 blockOrder+subtableIdx의 항목명 매칭률 확인
- audit, majorHolder, employee에서 검증

가설:
1. key_value: 항목명이 기간 간 거의 동일 → 정확 매칭률 95%+
2. matrix: 헤더가 기간마다 다를 수 있음 → 값 직접 수평화
3. 목록형 (employee 임원목록)은 항목 수 변동이 큼 → 감지 가능

방법:
1. 002의 parseCellSubtables → key_value/matrix만 필터
2. 기간별 항목명 수집 → outer join
3. 항목 수 변동 분석으로 목록형 감지 기준 도출

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
from collections import defaultdict

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections

sys.path.insert(0, str(Path(__file__).parent))
from _002_cellParser import ParsedSubtable, parseCellSubtables


def horizontalizeKvMatrix(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    subtableIdx: int,
    periodCols: list[str],
) -> tuple[pl.DataFrame | None, dict]:
    """key_value/matrix 서브테이블의 기간 간 수평화."""
    boRow = topicFrame.filter(pl.col("blockOrder") == blockOrder)
    if boRow.is_empty():
        return None, {}

    allItems: list[str] = []
    seenItems: set[str] = set()
    periodItemVal: dict[str, dict[str, str]] = {}
    periodItemCounts: dict[str, int] = {}

    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue

        pYear = int(re.match(r"\d{4}", p).group()) if re.match(r"\d{4}", p) else None
        if pYear is None:
            continue

        subs = parseCellSubtables(str(md), pYear)

        # 해당 subtableIdx의 kv/matrix
        matching = [s for s in subs if s.subtableIdx == subtableIdx and s.tableType in ("key_value", "matrix")]
        if not matching:
            matching = [s for s in subs if s.tableType in ("key_value", "matrix")]
            if matching:
                matching = [matching[min(subtableIdx, len(matching) - 1)]]

        if not matching:
            continue

        sub = matching[0]
        periodItemCounts[p] = len(sub.items)

        for item, vals in sub.items:
            if item not in seenItems:
                allItems.append(item)
                seenItems.add(item)
            if item not in periodItemVal:
                periodItemVal[item] = {}
            val = " | ".join(vals) if vals else ""
            if val:
                periodItemVal[item][p] = val

    if not allItems:
        return None, {}

    # DataFrame 구성
    usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
    schema = {"항목": pl.Utf8}
    for p in usedPeriods:
        schema[p] = pl.Utf8

    rows = []
    for item in allItems:
        row: dict[str, str | None] = {"항목": item}
        for p in usedPeriods:
            row[p] = periodItemVal.get(item, {}).get(p)
        rows.append(row)

    df = pl.DataFrame(rows, schema=schema)

    # 분석 결과
    counts = list(periodItemCounts.values())
    avgCount = sum(counts) / len(counts) if counts else 0
    maxCount = max(counts) if counts else 0
    minCount = min(counts) if counts else 0
    variationRate = (maxCount - minCount) / avgCount if avgCount > 0 else 0

    analysis = {
        "totalItems": len(allItems),
        "periodCounts": periodItemCounts,
        "avgItemCount": f"{avgCount:.1f}",
        "minCount": minCount,
        "maxCount": maxCount,
        "variationRate": f"{variationRate:.1%}",
        "isListType": variationRate > 0.5 or maxCount > 50,
    }

    return df, analysis


if __name__ == "__main__":
    sec = sections("005930")
    periodCols = [c for c in sec.columns if c not in ("chapter", "topic", "blockType", "blockOrder")]

    # ── audit blockOrder=1 서브테이블별 수평화 ──
    print("=" * 70)
    print("audit blockOrder=1 서브테이블별 수평화 (삼성전자)")
    print("=" * 70)

    topicFrame = sec.filter((pl.col("topic") == "audit") & (pl.col("blockType") == "table"))

    # 2024 기준 서브테이블 수 확인
    md2024 = topicFrame.filter(pl.col("blockOrder") == 1)["2024"][0]
    subs = parseCellSubtables(str(md2024), 2024)
    print(f"2024 서브테이블 수: {len(subs)}")

    for si, sub in enumerate(subs):
        print(f"\n  --- subtable {si} ({sub.tableType}) ---")
        df, analysis = horizontalizeKvMatrix(topicFrame, 1, si, periodCols)
        if df is not None:
            print(f"  {df.height}항목 × {len(df.columns)-1}기간")
            print(f"  목록형: {analysis['isListType']} (변동률: {analysis['variationRate']})")
            recent = ["항목"] + [c for c in df.columns if c != "항목"][-3:]
            print(df.select([c for c in recent if c in df.columns]).head(8))
        else:
            print("  수평화 실패")

    # ── employee 목록형 감지 ──
    print("\n" + "=" * 70)
    print("employee blockOrder별 목록형 감지 (삼성전자)")
    print("=" * 70)

    topicFrame = sec.filter((pl.col("topic") == "employee") & (pl.col("blockType") == "table"))
    for row in topicFrame.iter_rows(named=True):
        bo = row["blockOrder"]
        md = row.get("2024")
        if md is None:
            continue
        subs = parseCellSubtables(str(md), 2024)
        if not subs:
            continue

        for si, sub in enumerate(subs):
            df, analysis = horizontalizeKvMatrix(topicFrame, bo, si, periodCols)
            if df is not None:
                print(f"\n  bo={bo}, sub={si} ({sub.tableType}): {df.height}항목, 변동률={analysis['variationRate']}, 목록형={analysis['isListType']}")
                if not analysis['isListType']:
                    recent = ["항목"] + [c for c in df.columns if c != "항목"][-3:]
                    print(df.select([c for c in recent if c in df.columns]).head(5))

    # ── majorHolder 수평화 ──
    print("\n" + "=" * 70)
    print("majorHolder blockOrder=1 수평화 (삼성전자)")
    print("=" * 70)

    topicFrame = sec.filter((pl.col("topic") == "majorHolder") & (pl.col("blockType") == "table"))
    df, analysis = horizontalizeKvMatrix(topicFrame, 1, 0, periodCols)
    if df is not None:
        print(f"{df.height}항목 × {len(df.columns)-1}기간")
        print(f"목록형: {analysis['isListType']} (변동률: {analysis['variationRate']})")
        recent = ["항목"] + [c for c in df.columns if c != "항목"][-3:]
        print(df.select([c for c in recent if c in df.columns]).head(10))

    # ── companyOverview blockOrder별 ──
    print("\n" + "=" * 70)
    print("companyOverview 전체 blockOrder 목록형 분석 (삼성전자)")
    print("=" * 70)

    topicFrame = sec.filter((pl.col("topic") == "companyOverview") & (pl.col("blockType") == "table"))
    for row in topicFrame.iter_rows(named=True):
        bo = row["blockOrder"]
        md = row.get("2024")
        if md is None:
            continue
        subs = parseCellSubtables(str(md), 2024)
        for si, sub in enumerate(subs):
            df, analysis = horizontalizeKvMatrix(topicFrame, bo, si, periodCols)
            if df is not None:
                label = "목록" if analysis["isListType"] else "현황"
                print(f"  bo={bo} sub={si}: [{label}] {df.height}항목, 변동률={analysis['variationRate']}, max={analysis['maxCount']}")
