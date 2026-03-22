"""
실험 035 · step01 — 기타 재무에 관한 사항 탐색

목적:
- "기타 재무" 관련 섹션 내부 구조 파악
- 재평가, 합병, 자산유동화 등 테이블 유무 확인

실험일: 2026-03-08
"""

import os
import re
import sys

import polars as pl

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"
sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport


def explore(stockCode: str):
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
            if "기타 재무" in title or ("기타" in title and "재무" in title):
                content = row.get("section_content", "") or ""
                return {
                    "stockCode": stockCode,
                    "corpName": corpName,
                    "year": year,
                    "title": title,
                    "contentLen": len(content),
                    "preview": content[:1500],
                }
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])

    found = 0
    total = len(files)
    samples = []

    for code in files:
        result = explore(code)
        if result:
            found += 1
            if len(samples) < 5:
                samples.append(result)

    print(f"\n=== 기타 재무에 관한 사항 ===")
    print(f"출현율: {found}/{total} ({found/total*100:.1f}%)")
    print()

    for s in samples:
        print(f"--- {s['corpName']} ({s['stockCode']}) | {s['year']} ---")
        print(f"제목: {s['title']}")
        print(f"길이: {s['contentLen']}")
        print(s["preview"][:800])
        print()
