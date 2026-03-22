"""step05 실패 65개 분류.

분류:
1. 섹션 자체가 없음 (section_title에 재무 관련 없음)
2. 섹션은 있지만 splitStatements 빈 결과
3. splitStatements 성공이지만 extractAccounts 빈 결과
4. 데이터(report) 자체가 없음
"""

import os
import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import extractAccounts, extractTables
from dartlab.finance.statements.extractor import splitStatements

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

FAIL_CODES = [
    "0009K0", "0015N0", "009150", "014950", "031210", "061090", "081180",
    "098070", "125020", "125490", "136150", "178920", "234030", "309710",
    "317450", "318060", "331740", "332190", "340450", "342870", "364950",
    "380550", "388210", "393970", "397810", "403810", "424870", "439260",
    "444530", "452450", "455180", "459510", "459550", "460850", "462310",
    "462860", "463020", "468530", "469610", "475150", "475230", "475430",
    "476040", "482690", "484120", "484130", "484590", "486990", "487360",
    "487570", "487720", "488280", "489210", "489460", "489480", "489730",
    "489790", "492220", "493790", "494120", "495900", "496070", "496320",
    "498390", "499790",
]


def extractContent(report):
    cons = report.filter(
        pl.col("section_title").str.contains("연결재무제표")
        & ~pl.col("section_title").str.contains("주석")
    )
    if cons.height > 0:
        return cons["section_content"][0], "consolidated"

    sep = report.filter(
        pl.col("section_title").str.contains("재무제표")
        & ~pl.col("section_title").str.contains("연결")
        & ~pl.col("section_title").str.contains("주석")
    )
    if sep.height > 0:
        return sep["section_content"][0], "separate"

    return None, "none"


if __name__ == "__main__":
    categories = {
        "no_report": [],      # 사업보고서 자체 없음
        "no_section": [],     # 재무 섹션 없음
        "no_split": [],       # splitStatements 빈 결과
        "no_accounts": [],    # extractAccounts 빈 결과
    }

    for code in FAIL_CODES:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        # 최근 3개년 시도
        found = False
        for year in years[:3]:
            report = selectReport(df, year, reportKind="annual")
            if report is None:
                continue

            content, scope = extractContent(report)
            if content is None:
                titles = report["section_title"].unique().to_list()
                fsTitles = [t for t in titles if "재무" in t]
                categories["no_section"].append((code, corpName, year, fsTitles))
                found = True
                break

            parts = splitStatements(content)
            if not parts:
                categories["no_split"].append((code, corpName, year, scope, content[:200]))
                found = True
                break

            # 각 제표 파싱 시도
            anyOk = False
            for stKey in ["BS", "PNL", "CF"]:
                stContent = parts.get(stKey)
                if stContent:
                    accounts, order = extractAccounts(stContent)
                    if accounts:
                        anyOk = True
                        break

            if not anyOk:
                categories["no_accounts"].append((code, corpName, year, scope, list(parts.keys())))
                found = True
                break

            # 사실 여기 오면 성공인데... 위의 statementsUnified에서 실패한 이유?
            found = True
            print(f"  [UNEXPECTED OK] [{code}] {corpName} year={year}")
            break

        if not found:
            categories["no_report"].append((code, corpName))

    for cat, items in categories.items():
        print(f"\n=== {cat} ({len(items)}개) ===")
        for item in items[:10]:
            if cat == "no_report":
                code, name = item
                print(f"  [{code}] {name}")
            elif cat == "no_section":
                code, name, year, titles = item
                print(f"  [{code}] {name} ({year}) titles={titles}")
            elif cat == "no_split":
                code, name, year, scope, preview = item
                print(f"  [{code}] {name} ({year}) scope={scope}")
                print(f"    preview: {preview[:100]}")
            elif cat == "no_accounts":
                code, name, year, scope, keys = item
                print(f"  [{code}] {name} ({year}) scope={scope} keys={keys}")
