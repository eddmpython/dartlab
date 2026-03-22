"""연결/별도 재무제표 분포 조사.

목표: raw parquet에서 section_title에 연결/별도가 어떻게 표현되는지 실측.
- "연결재무제표" vs "재무제표" vs "별도재무제표" 패턴
- 연도별 존재 비율
- 연결만/별도만/둘다 있는 기업 비율
"""

import os
import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


def surveyReport(code):
    """한 종목의 최근 사업보고서에서 section_title 패턴 조사."""
    df = loadData(code)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    results = []
    for year in years[:3]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        titles = report["section_title"].unique().to_list()

        hasCons = any("연결재무제표" in t for t in titles)
        hasSep = any("별도재무제표" in t or "개별재무제표" in t for t in titles)
        hasConsNotes = any("연결재무제표" in t and "주석" in t for t in titles)
        hasSepNotes = any(
            ("별도재무제표" in t or "개별재무제표" in t) and "주석" in t
            for t in titles
        )

        # 연결/별도 구분 없는 "재무제표" 섹션
        hasPlain = any(
            t.strip() == "재무제표" or t.strip() == "III. 재무에 관한 사항"
            for t in titles
        )

        # 재무제표 관련 모든 타이틀 추출
        fsTitles = [t for t in titles if "재무" in t or "재무제표" in t]

        results.append({
            "year": year,
            "hasCons": hasCons,
            "hasSep": hasSep,
            "hasConsNotes": hasConsNotes,
            "hasSepNotes": hasSepNotes,
            "hasPlain": hasPlain,
            "fsTitles": fsTitles,
        })

    return corpName, results


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    consOnly = 0
    sepOnly = 0
    both = 0
    neither = 0
    total = 0

    titlePatterns = {}

    for code in codes:
        corpName, results = surveyReport(code)
        if not results:
            continue

        r = results[0]  # 최신 연도
        total += 1

        if r["hasCons"] and r["hasSep"]:
            both += 1
        elif r["hasCons"]:
            consOnly += 1
        elif r["hasSep"]:
            sepOnly += 1
        else:
            neither += 1
            if neither <= 10:
                print(f"  NEITHER [{code}] {corpName}: {r['fsTitles']}")

        for t in r["fsTitles"]:
            t = t.strip()
            titlePatterns[t] = titlePatterns.get(t, 0) + 1

    print(f"\n총 {total}개 기업 (최신 사업보고서 기준)")
    print(f"  연결만: {consOnly}")
    print(f"  별도만: {sepOnly}")
    print(f"  둘 다: {both}")
    print(f"  둘 다 없음: {neither}")

    print(f"\n재무 관련 section_title 패턴 (상위 30):")
    for title, count in sorted(titlePatterns.items(), key=lambda x: -x[1])[:30]:
        print(f"  {count:4d}개  {title}")
