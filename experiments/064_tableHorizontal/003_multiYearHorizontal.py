"""
실험 ID: 064-003
실험명: Layer 2 horizontalizer — 비교형 (multi_year) 수평화

목적:
- multi_year 테이블에서 당기 값 추출 → 기간 간 join → 항목×기간 매트릭스
- 전기/전전기 값으로 교차 검증
- dividend, salesOrder, rawMaterial에서 검증

가설:
1. 당기 값만 추출하면 기간 간 중복 없이 깨끗한 수평화
2. 전기 값 = 이전 보고서의 당기 값 일치율 90%+
3. 5종목 dividend에서 항목×기간 매트릭스 정상 생성

방법:
1. 002의 parseCellSubtables → multi_year만 필터
2. 기간별 당기 값 수집 → 항목명 기준 outer join
3. 전기/전전기 검증: 값 일치 확인

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

from dartlab.engines.company.dart.docs.sections.pipeline import sections

# 002에서 만든 parseCellSubtables 재사용
sys.path.insert(0, str(Path(__file__).parent))
from _002_cellParser import ParsedSubtable, parseCellSubtables


def horizontalizeMultiYear(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    subtableIdx: int,
    periodCols: list[str],
) -> tuple[pl.DataFrame | None, dict]:
    """multi_year 서브테이블의 기간 간 수평화.

    Returns:
        (항목×기간 DataFrame, 검증 결과 dict)
    """
    boRow = topicFrame.filter(pl.col("blockOrder") == blockOrder)
    if boRow.is_empty():
        return None, {}

    # 연간 기간만 (multi_year는 연간 보고서에서만 의미)
    annualPeriods = [p for p in periodCols if re.match(r"^\d{4}$", p)]

    allItems: list[str] = []
    seenItems: set[str] = set()
    periodItemVal: dict[str, dict[str, str]] = {}
    verification: dict[str, list[tuple[str, str, str, str, bool]]] = {}  # item → [(fromPeriod, year, priorVal, actualVal, match)]

    for p in annualPeriods:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue

        pYear = int(p)
        subs = parseCellSubtables(str(md), pYear)

        # 해당 subtableIdx의 multi_year만
        matching = [s for s in subs if s.subtableIdx == subtableIdx and s.tableType == "multi_year"]
        if not matching:
            # subtableIdx가 기간마다 다를 수 있음 → multi_year 중 첫 번째 사용
            matching = [s for s in subs if s.tableType == "multi_year"]

        if not matching:
            continue

        sub = matching[0]
        for item, vals in sub.items:
            if item not in seenItems:
                allItems.append(item)
                seenItems.add(item)
            if item not in periodItemVal:
                periodItemVal[item] = {}
            if vals:
                periodItemVal[item][p] = vals[0]

        # 전기/전전기 검증
        for item, priorYears in sub.priorValues.items():
            for year, priorVal in priorYears.items():
                actualVal = periodItemVal.get(item, {}).get(year)
                match = actualVal == priorVal if actualVal is not None else None
                if item not in verification:
                    verification[item] = []
                verification[item].append((p, year, priorVal, actualVal or "N/A", match is True if match is not None else None))

    if not allItems:
        return None, {}

    # DataFrame 구성
    usedPeriods = sorted(set(p for iv in periodItemVal.values() for p in iv.keys()))
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

    # 검증 요약
    totalChecks = sum(len(v) for v in verification.values())
    matches = sum(1 for v in verification.values() for _, _, _, _, m in v if m is True)
    mismatches = sum(1 for v in verification.values() for _, _, _, _, m in v if m is False)
    noData = sum(1 for v in verification.values() for _, _, _, _, m in v if m is None)

    verifyResult = {
        "totalChecks": totalChecks,
        "matches": matches,
        "mismatches": mismatches,
        "noData": noData,
        "matchRate": f"{matches/totalChecks*100:.1f}%" if totalChecks else "N/A",
        "details": verification,
    }

    return df, verifyResult


if __name__ == "__main__":
    stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "네이버"),
        ("005380", "현대차"),
        ("068270", "셀트리온"),
    ]

    # ── dividend multi_year 수평화 ──
    print("=" * 70)
    print("dividend multi_year 수평화")
    print("=" * 70)

    for code, name in stocks:
        sec = sections(code)
        if sec is None:
            continue

        periodCols = [c for c in sec.columns if c not in ("chapter", "topic", "blockType", "blockOrder")]
        topicFrame = sec.filter((pl.col("topic") == "dividend") & (pl.col("blockType") == "table"))

        if topicFrame.is_empty():
            print(f"\n{name}: dividend table 없음")
            continue

        # blockOrder=1이 보통 multi_year 배당 테이블
        df, verify = horizontalizeMultiYear(topicFrame, 1, 0, periodCols)

        if df is not None:
            print(f"\n{name}: {df.height}항목 × {len(df.columns)-1}기간")
            print(f"  검증: {verify['matchRate']} ({verify['matches']}/{verify['totalChecks']})")
            if verify['mismatches']:
                print(f"  ⚠ 불일치: {verify['mismatches']}건")
                for item, checks in verify['details'].items():
                    for fromP, year, prior, actual, match in checks:
                        if match is False:
                            print(f"    {item} {year}: {fromP}보고서={prior}, 실제={actual}")

            # 최근 5년 미리보기
            recentCols = ["항목"] + [c for c in df.columns if c != "항목"][-5:]
            print(df.select([c for c in recentCols if c in df.columns]))
        else:
            print(f"\n{name}: multi_year 수평화 실패")

    # ── salesOrder multi_year 수평화 (삼성전자) ──
    print("\n" + "=" * 70)
    print("salesOrder multi_year 수평화 (삼성전자)")
    print("=" * 70)

    sec = sections("005930")
    periodCols = [c for c in sec.columns if c not in ("chapter", "topic", "blockType", "blockOrder")]
    topicFrame = sec.filter((pl.col("topic") == "salesOrder") & (pl.col("blockType") == "table"))

    for row in topicFrame.iter_rows(named=True):
        bo = row["blockOrder"]
        # 2024 연간에서 구조 확인
        md = row.get("2024")
        if md is None:
            continue
        subs = parseCellSubtables(str(md), 2024)
        hasMultiYear = any(s.tableType == "multi_year" for s in subs)
        if not hasMultiYear:
            continue

        df, verify = horizontalizeMultiYear(topicFrame, bo, 0, periodCols)
        if df is not None:
            print(f"\n  blockOrder={bo}: {df.height}항목 × {len(df.columns)-1}기간")
            print(f"  검증: {verify['matchRate']} ({verify['matches']}/{verify['totalChecks']})")
            recentCols = ["항목"] + [c for c in df.columns if c != "항목"][-5:]
            print(df.select([c for c in recentCols if c in df.columns]))
