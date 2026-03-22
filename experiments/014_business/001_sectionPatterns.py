"""사업의 내용 섹션 패턴 전수조사.

전 종목에서:
- section_title 패턴 수집
- 하위 섹션 조합 분류
- 연도별 하위 섹션 유무 변화
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import polars as pl

from dartlab.core import buildIndex, loadData

idx = buildIndex()
codes = idx["stockCode"].to_list()

allTitles = set()
stats = []

for code in codes:
    try:
        df = loadData(code)
        name = df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code

        annual = df.filter(df["report_type"].str.contains("사업보고서"))
        if annual.height == 0:
            continue

        bizTitles = annual.filter(
            annual["section_title"].str.contains("사업의 내용")
            | annual["section_title"].str.contains("사업의 개요")
            | annual["section_title"].str.contains("주요 제품")
            | annual["section_title"].str.contains("원재료")
            | annual["section_title"].str.contains("생산 및 설비")
            | annual["section_title"].str.contains("매출")
            | annual["section_title"].str.contains("수주")
            | annual["section_title"].str.contains("위험관리")
            | annual["section_title"].str.contains("기타 참고")
            | annual["section_title"].str.contains("연구개발")
            | annual["section_title"].str.contains("주요계약")
            | annual["section_title"].str.contains("경영상")
            | annual["section_title"].str.contains("재무건전성")
        )["section_title"].unique().to_list()

        for t in bizTitles:
            allTitles.add(t)

        latestYear = annual["year"].unique().sort().to_list()[-1]
        latest = annual.filter(annual["year"] == latestYear)
        latestBiz = latest.filter(
            latest["section_title"].str.contains("사업의 내용")
            | latest["section_title"].str.contains("사업의 개요")
            | latest["section_title"].str.contains("주요 제품")
            | latest["section_title"].str.contains("원재료")
            | latest["section_title"].str.contains("생산 및 설비")
            | latest["section_title"].str.contains("매출")
            | latest["section_title"].str.contains("수주")
            | latest["section_title"].str.contains("위험관리")
            | latest["section_title"].str.contains("기타 참고")
            | latest["section_title"].str.contains("연구개발")
            | latest["section_title"].str.contains("주요계약")
            | latest["section_title"].str.contains("경영상")
            | latest["section_title"].str.contains("재무건전성")
        )["section_title"].unique().sort().to_list()

        hasSub = any(t[0].isdigit() for t in latestBiz if t)
        hasMain = any("II." in t for t in latestBiz)

        stats.append({
            "code": code,
            "name": name,
            "year": latestYear,
            "hasMain": hasMain,
            "hasSub": hasSub,
            "titles": latestBiz,
        })
    except Exception as e:
        print(f"[ERROR] {code}: {e}")

print("=" * 60)
print("전체 section_title 패턴 (정렬)")
print("=" * 60)
for t in sorted(allTitles):
    print(f"  {t}")

print(f"\n{'=' * 60}")
print(f"종목별 최신 연도 현황 ({len(stats)}종목)")
print("=" * 60)

both = [s for s in stats if s["hasMain"] and s["hasSub"]]
mainOnly = [s for s in stats if s["hasMain"] and not s["hasSub"]]
subOnly = [s for s in stats if s["hasSub"] and not s["hasMain"]]
neither = [s for s in stats if not s["hasMain"] and not s["hasSub"]]

print(f"  II.사업의내용 + 하위섹션: {len(both)}종목")
print(f"  II.사업의내용만 (하위 없음): {len(mainOnly)}종목")
print(f"  하위섹션만 (II. 없음): {len(subOnly)}종목")
print(f"  둘 다 없음: {len(neither)}종목")

if mainOnly:
    print(f"\n--- II.사업의내용만 (하위 없음) ---")
    for s in mainOnly:
        print(f"  {s['code']} {s['name']} ({s['year']}): {s['titles']}")

if neither:
    print(f"\n--- 둘 다 없음 ---")
    for s in neither:
        print(f"  {s['code']} {s['name']} ({s['year']}): {s['titles']}")


print(f"\n{'=' * 60}")
print("하위 섹션 조합 패턴 (빈도순)")
print("=" * 60)

combos = {}
for s in stats:
    key = tuple(t for t in s["titles"] if t[0].isdigit()) if s["hasSub"] else ("(없음)",)
    if key not in combos:
        combos[key] = []
    combos[key].append(s["code"])

for titles, codeList in sorted(combos.items(), key=lambda x: -len(x[1])):
    print(f"\n[{len(codeList)}종목] 예: {codeList[0]}")
    for t in titles:
        print(f"  {t}")


print(f"\n{'=' * 60}")
print("삼성전자 연도별 하위 섹션 변화")
print("=" * 60)

df = loadData("005930")
annual = df.filter(df["report_type"].str.contains("사업보고서"))
years = sorted(annual["year"].unique().to_list())

for y in years:
    ydf = annual.filter(annual["year"] == y)
    titles = ydf.filter(
        ydf["section_title"].str.contains("사업의 내용")
        | ydf["section_title"].str.contains("사업의 개요")
        | ydf["section_title"].str.contains("주요 제품")
        | ydf["section_title"].str.contains("원재료")
        | ydf["section_title"].str.contains("생산 및 설비")
        | ydf["section_title"].str.contains("매출")
        | ydf["section_title"].str.contains("수주")
        | ydf["section_title"].str.contains("위험관리")
        | ydf["section_title"].str.contains("기타 참고")
        | ydf["section_title"].str.contains("연구개발")
        | ydf["section_title"].str.contains("주요계약")
        | ydf["section_title"].str.contains("경영상")
    )["section_title"].unique().sort().to_list()
    print(f"{y}: {titles}")
