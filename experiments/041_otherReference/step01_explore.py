"""
실험 041 · step01 — 기타 참고사항 탐색

목적: 기타 참고사항 섹션 구조 파악
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
            if "기타" in title and "참고" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 30:
                    continue

                noData = "해당사항" in content[:500] or "없습니다" in content[:300]
                hasTable = "|" in content

                return {
                    "corpName": corpName,
                    "year": year,
                    "contentLen": len(content),
                    "noData": noData,
                    "hasTable": hasTable,
                }
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])
    ok = fail = withTable = noData = 0

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                if r["noData"]:
                    noData += 1
                if r["hasTable"]:
                    withTable += 1
        except Exception:
            fail += 1

    total = len(files)
    print(f"\n=== 041 기타 참고사항 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"해당없음: {noData}건")
    print(f"테이블 포함: {withTable}건")
