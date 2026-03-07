"""회사의 개요 섹션 패턴 전수조사.

전 267종목에 대해:
- "I. 회사의 개요" / "I. 회사의 개황" 존재 여부
- "1. 회사의 개요" 하위 섹션 존재 여부
- 하위 섹션 타이틀 패턴 수집
- 연도별 패턴 변화
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

from dartlab.core import loadData, buildIndex
import polars as pl


idx = buildIndex()
codes = idx["stockCode"].to_list()

mainTitleCounts = {}
subTitleCounts = {}
results = []

for code in codes:
    df = loadData(code)
    annual = df.filter(df["report_type"].str.contains("사업보고서"))
    if annual.height == 0:
        results.append({"code": code, "hasAnnual": False})
        continue

    latestYear = annual["year"].unique().sort().to_list()[-1]
    latest = annual.filter(annual["year"] == latestYear)

    hasMain = latest.filter(
        latest["section_title"].str.contains("회사의 개요")
        | latest["section_title"].str.contains("회사의 개황")
    ).height > 0

    overviewTitles = latest.filter(
        latest["section_title"].str.starts_with("1.")
        | latest["section_title"].str.starts_with("2.")
        | latest["section_title"].str.starts_with("3.")
        | latest["section_title"].str.starts_with("4.")
        | latest["section_title"].str.starts_with("5.")
    ).filter(
        pl.col("section_title").str.contains("회사의 개요")
        | pl.col("section_title").str.contains("회사의 목적")
        | pl.col("section_title").str.contains("회사의 연혁")
        | pl.col("section_title").str.contains("자본금 변동")
        | pl.col("section_title").str.contains("주식의 총수")
        | pl.col("section_title").str.contains("정관에 관한")
        | pl.col("section_title").str.contains("주식사무")
        | pl.col("section_title").str.contains("주주의 분포")
        | pl.col("section_title").str.contains("주식의 분포")
    )

    subTitles = sorted(overviewTitles["section_title"].unique().to_list())

    for t in subTitles:
        subTitleCounts[t] = subTitleCounts.get(t, 0) + 1

    hasSubOverview = any("회사의 개요" in t for t in subTitles)

    results.append({
        "code": code,
        "hasAnnual": True,
        "year": latestYear,
        "hasMain": hasMain,
        "hasSubOverview": hasSubOverview,
        "subTitles": subTitles,
        "nSubs": len(subTitles),
    })


print("=" * 60)
print("전 종목 회사의 개요 섹션 패턴 조사")
print("=" * 60)

annualCount = sum(1 for r in results if r.get("hasAnnual"))
mainCount = sum(1 for r in results if r.get("hasMain"))
subCount = sum(1 for r in results if r.get("hasSubOverview"))

print(f"총 종목: {len(codes)}")
print(f"사업보고서 보유: {annualCount}")
print(f"I.회사의 개요 존재: {mainCount}")
print(f"1.회사의 개요 하위섹션: {subCount}")

print(f"\n하위 섹션 타이틀별 종목 수:")
for title, count in sorted(subTitleCounts.items(), key=lambda x: -x[1]):
    print(f"  {title}: {count}")

noMain = [r for r in results if r.get("hasAnnual") and not r.get("hasMain")]
if noMain:
    print(f"\nI.회사의 개요 없는 종목: {len(noMain)}")
    for r in noMain:
        print(f"  {r['code']} ({r.get('year', '?')})")

noSub = [r for r in results if r.get("hasMain") and not r.get("hasSubOverview")]
if noSub:
    print(f"\n1.회사의 개요 하위섹션 없는 종목: {len(noSub)}")
    for r in noSub[:20]:
        print(f"  {r['code']} ({r.get('year', '?')}): {r.get('subTitles', [])}")


print(f"\n{'=' * 60}")
print("삼성전자 연도별 하위 섹션 변화")
print("=" * 60)

df = loadData("005930")
annual = df.filter(df["report_type"].str.contains("사업보고서"))
years = sorted(annual["year"].unique().to_list())

for y in years:
    ydf = annual.filter(annual["year"] == y)
    subs = ydf.filter(
        ydf["section_title"].str.starts_with("1.")
        | ydf["section_title"].str.starts_with("2.")
        | ydf["section_title"].str.starts_with("3.")
        | ydf["section_title"].str.starts_with("4.")
        | ydf["section_title"].str.starts_with("5.")
    ).filter(
        pl.col("section_title").str.contains("회사")
        | pl.col("section_title").str.contains("자본금")
        | pl.col("section_title").str.contains("주식")
        | pl.col("section_title").str.contains("정관")
    )
    titles = sorted(subs["section_title"].unique().to_list())
    print(f"{y}: {titles}")
