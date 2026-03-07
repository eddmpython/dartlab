"""삼성전자 생산설비 유형자산 테이블 상세 디버깅."""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl
from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

df = loadData("005930")
years = sorted(df["year"].unique().to_list(), reverse=True)
report = selectReport(df, years[0], reportKind="annual")
sections = report.filter(pl.col("section_title").str.contains("원재료"))
content = sections["section_content"][0]
lines = content.split("\n")

print("=== 유형자산 변동 테이블 (line 121~) ===")
for i in range(121, min(150, len(lines))):
    s = lines[i].strip()
    if s.startswith("|"):
        cells = [c.strip() for c in s.split("|")]
        nonEmpty = [c for c in cells if c]
        print(f"  [{i:3d}] raw cells: {cells[:10]}")
        print(f"        non-empty: {nonEmpty[:10]}")
    else:
        print(f"  [{i:3d}] {s[:100]}")
