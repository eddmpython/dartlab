"""원재료 및 생산설비 섹션 구조 탐색 — 삼성전자/SK하이닉스/NAVER."""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl
from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

STOCKS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
]

for code, name in STOCKS:
    print(f"\n{'='*80}")
    print(f"  {name} ({code})")
    print(f"{'='*80}")

    df = loadData(code)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        print("  보고서 없음")
        continue

    sections = report.filter(
        pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산설비")
        | pl.col("section_title").str.contains("생산능력")
        | pl.col("section_title").str.contains("생산실적")
        | pl.col("section_title").str.contains("설비")
    )

    if sections.height == 0:
        allSections = report["section_title"].unique().sort().to_list()
        print(f"  원재료/생산설비 섹션 없음")
        print(f"  전체 섹션: {allSections[:20]}")
        continue

    for i in range(sections.height):
        title = sections["section_title"][i]
        content = sections["section_content"][i]
        lines = content.split("\n")
        print(f"\n--- [{title}] ({len(lines)} lines) ---")
        for line in lines[:150]:
            print(f"  {line}")
        if len(lines) > 150:
            print(f"  ... ({len(lines) - 150} more lines)")
