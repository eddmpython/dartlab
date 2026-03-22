"""
실험 043 · step01 — 사업의 개요 탐색

목적: 사업의 개요 섹션 출현율, 내부 구조 파악
실험일: 2026-03-08
"""

import os
import re
import sys

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"
sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport


def pipeline(stockCode: str):
    try:
        df = loadData(stockCode)
    except FileNotFoundError:
        return None

    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if "사업의 개요" in title or "사업 의 개요" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                hasTable = "|" in content

                return {
                    "corpName": corpName,
                    "year": year,
                    "contentLen": len(content),
                    "hasTable": hasTable,
                }
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])
    ok = fail = withTable = 0
    totalLen = 0

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                totalLen += r["contentLen"]
                if r["hasTable"]:
                    withTable += 1
        except Exception:
            fail += 1

    total = len(files)
    print(f"\n=== 043 사업의 개요 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"평균 길이: {totalLen//max(ok,1)}자")
    print(f"테이블 포함: {withTable}건")
