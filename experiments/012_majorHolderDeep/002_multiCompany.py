"""
실험 ID: 012-002
실험명: 10개 종목 — 5% 이상 주주 + 소액주주 + 의결권 현황 패턴 비교

목적:
- 5% 이상 주주, 소액주주, 의결권 현황 테이블이 모든 종목에 존재하는지 확인
- 테이블 헤더/셀 구조 패턴 파악
- 파서 설계를 위한 공통/예외 패턴 분류

가설:
1. 5% 이상 주주 테이블은 90% 이상 종목에 존재
2. 소액주주 테이블도 90% 이상 존재
3. 의결권 현황 테이블은 "3. 주주총회" 섹션에 거의 모든 종목 존재

방법:
1. 10개 종목에서 해당 테이블 존재 여부 + 헤더 패턴 추출
2. 공통 구조 정리

결과:
(아래 실행 결과 참조)

실험일: 2026-03-07
"""

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

STOCKS = [
    "005930", "000660", "035420", "005380", "055550",
    "051910", "006400", "003550", "034020", "000270",
]


def findTable(content: str, keywords: list[str]) -> list[str] | None:
    lines = content.split("\n")
    found = False
    tableLines = []
    gapCount = 0

    for line in lines:
        s = line.strip().replace("\xa0", " ")
        if not found:
            if any(kw in s for kw in keywords):
                found = True
                tableLines.append(f">> {s[:120]}")
            continue

        if s.startswith("|") and "---" not in s:
            gapCount = 0
            tableLines.append(s[:150])
        elif not s:
            gapCount += 1
            if gapCount >= 2 and len(tableLines) > 1:
                break
        elif s.startswith("|") and "---" in s:
            continue
        else:
            if len(tableLines) > 1 and not any(kw in s for kw in ["※", "주1", "주2", "(주"]):
                break
            if "※" in s or "(주" in s:
                continue

    return tableLines if len(tableLines) > 1 else None


def analyze(stockCode: str):
    df = loadData(stockCode)
    if df is None:
        return {"code": stockCode, "name": stockCode, "error": "no data"}

    corpName = df["corp_name"][0] if "corp_name" in df.columns else stockCode
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        return {"code": stockCode, "name": corpName, "error": "no report"}

    result = {"code": stockCode, "name": corpName}

    holderSections = report.filter(pl.col("section_title").str.contains("주주에 관한 사항"))
    totalSections = report.filter(pl.col("section_title").str.contains("주주총회"))

    fivePercent = None
    minority = None
    voting = None
    majorChange = None

    for i in range(holderSections.height):
        content = holderSections["section_content"][i]

        if fivePercent is None:
            fivePercent = findTable(content, ["5% 이상 주주", "5%이상 주주", "5%이상주주"])

        if minority is None:
            minority = findTable(content, ["소액주주"])

        if majorChange is None:
            majorChange = findTable(content, ["최대주주 변동현황", "최대주주 변동내역"])

    for i in range(totalSections.height):
        content = totalSections["section_content"][i]
        if voting is None:
            voting = findTable(content, ["의결권 현황", "의결권현황"])

    result["fivePercent"] = fivePercent
    result["minority"] = minority
    result["voting"] = voting
    result["majorChange"] = majorChange

    return result


if __name__ == "__main__":
    results = []
    for code in STOCKS:
        r = analyze(code)
        results.append(r)

    print("=" * 80)
    print("5% 이상 주주 현황")
    print("=" * 80)
    for r in results:
        name = r["name"]
        status = "O" if r.get("fivePercent") else "X"
        print(f"\n[{status}] {name} ({r['code']})")
        if r.get("fivePercent"):
            for line in r["fivePercent"][:8]:
                print(f"    {line}")

    print("\n" + "=" * 80)
    print("소액주주 현황")
    print("=" * 80)
    for r in results:
        name = r["name"]
        status = "O" if r.get("minority") else "X"
        print(f"\n[{status}] {name} ({r['code']})")
        if r.get("minority"):
            for line in r["minority"][:8]:
                print(f"    {line}")

    print("\n" + "=" * 80)
    print("의결권 현황")
    print("=" * 80)
    for r in results:
        name = r["name"]
        status = "O" if r.get("voting") else "X"
        print(f"\n[{status}] {name} ({r['code']})")
        if r.get("voting"):
            for line in r["voting"][:15]:
                print(f"    {line}")

    print("\n" + "=" * 80)
    print("최대주주 변동현황")
    print("=" * 80)
    for r in results:
        name = r["name"]
        status = "O" if r.get("majorChange") else "X"
        print(f"\n[{status}] {name} ({r['code']})")
        if r.get("majorChange"):
            for line in r["majorChange"][:8]:
                print(f"    {line}")

    print("\n\n=== 요약 ===")
    for field, label in [("fivePercent", "5%이상"), ("minority", "소액주주"), ("voting", "의결권"), ("majorChange", "최대주주변동")]:
        found = sum(1 for r in results if r.get(field))
        print(f"  {label}: {found}/{len(results)}")
