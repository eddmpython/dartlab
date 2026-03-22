"""SPAC 파싱 실패 상세 분석.

splitStatements는 성공하는데 extractAccounts가 실패하는 이유.
"""

import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import extractAccounts
from dartlab.finance.statements.extractor import splitStatements


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
    code = "482690"  # 대신밸런스제19호스팩

    df = loadData(code)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    report = selectReport(df, years[0], reportKind="annual")
    sep = extractSeparateContent(report)
    parts = splitStatements(sep)

    print(f"[{code}] {corpName}")
    print(f"Keys: {list(parts.keys())}")

    for key in ["BS", "PNL", "CF"]:
        content = parts.get(key)
        if content is None:
            print(f"\n{key}: None")
            continue

        print(f"\n=== {key} ({len(content)} chars) ===")
        print(content[:800])
        print("---")

        accounts, order = extractAccounts(content)
        print(f"extractAccounts: {len(accounts)} accounts, {len(order)} order")
        if accounts:
            for name in order[:5]:
                print(f"  {name}: {accounts[name]}")
