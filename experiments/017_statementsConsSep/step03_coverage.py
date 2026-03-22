"""현재 statements() 모듈의 연결/별도 커버리지 검증.

1. 연결 있는 기업 → statements() 결과 확인
2. 연결 없는 기업 → statements() 결과 확인 (None 예상)
3. "4. 재무제표" 섹션으로 별도 추출 가능 여부
"""

import os
import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.finance.statements import statements
from dartlab.finance.statements.extractor import extractConsolidatedContent

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    hasResult = 0
    noResult = 0
    hasCons = 0
    noCons = 0

    noResultCodes = []

    for code in codes:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        # 연결 섹션 존재 여부
        consExists = False
        for year in years[:1]:
            report = selectReport(df, year, reportKind="annual")
            if report is None:
                continue
            cons = report.filter(
                pl.col("section_title").str.contains("연결재무제표")
                & ~pl.col("section_title").str.contains("주석")
            )
            consExists = cons.height > 0

        if consExists:
            hasCons += 1
        else:
            noCons += 1

        # statements() 결과
        result = statements(code, ifrsOnly=True, period="y")
        if result is not None and result.BS is not None:
            hasResult += 1
        else:
            noResult += 1
            noResultCodes.append((code, corpName, consExists))

    print(f"총 {len(codes)}개 기업")
    print(f"\n연결 섹션 존재: {hasCons}")
    print(f"연결 섹션 없음: {noCons}")
    print(f"\nstatements() 결과 있음: {hasResult}")
    print(f"statements() 결과 없음: {noResult}")

    if noResultCodes:
        print(f"\nstatements() 없는 기업 (처음 20개):")
        for code, name, hasCons in noResultCodes[:20]:
            tag = "연결O" if hasCons else "연결X"
            print(f"  [{code}] {name} ({tag})")
