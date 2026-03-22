"""step04 실패 케이스 분석.

1. 아무것도 추출 안 되는 3개: section_title 패턴 확인
2. 별도 추출됐지만 파싱 실패한 13개: splitStatements 결과 확인
"""

import os
import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import extractAccounts
from dartlab.finance.statements.extractor import splitStatements

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

# step04에서 확인된 실패 케이스
NO_EXTRACT = ["009150", "316140"]  # 삼성전기, 우리금융지주
PARSE_FAIL_SEP = [
    "393970", "403810", "482690", "484130", "487360",
    "487720", "489210", "489480", "489730", "492220",
    "493790", "495900", "496320", "498390",
]


def extractSeparateContent(report: pl.DataFrame) -> str | None:
    section = report.filter(
        pl.col("section_title").str.contains("재무제표")
        & ~pl.col("section_title").str.contains("연결")
        & ~pl.col("section_title").str.contains("주석")
    )
    if section.height == 0:
        return None
    return section["section_content"][0]


if __name__ == "__main__":
    # 1. 추출 실패 케이스: section_title 전체 확인
    print("=== 추출 실패 케이스 ===")
    for code in NO_EXTRACT:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            print(f"[{code}] {corpName}: 사업보고서 없음")
            continue

        titles = report["section_title"].unique().to_list()
        fsTitles = [t for t in titles if "재무" in t]
        print(f"[{code}] {corpName}")
        print(f"  재무 관련 section_title: {fsTitles}")

    # 2. 파싱 실패 케이스: splitStatements 결과 + 내용 일부
    print("\n=== 파싱 실패 케이스 (별도 추출은 성공) ===")
    for code in PARSE_FAIL_SEP[:5]:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue

        sep = extractSeparateContent(report)
        if sep is None:
            print(f"[{code}] {corpName}: 별도 추출 실패")
            continue

        parts = splitStatements(sep)
        print(f"\n[{code}] {corpName}")
        print(f"  splitStatements keys: {list(parts.keys())}")
        print(f"  content length: {len(sep)} chars")
        print(f"  content preview (first 500 chars):")
        print(f"  {sep[:500]}")
        print(f"  ---")
