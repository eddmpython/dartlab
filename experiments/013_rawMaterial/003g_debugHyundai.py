"""현대차 원재료 raw pipe 확인."""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl
from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

df = loadData("005380")
years = sorted(df["year"].unique().to_list(), reverse=True)
report = selectReport(df, years[0], reportKind="annual")
sections = report.filter(pl.col("section_title").str.contains("원재료"))
content = sections["section_content"][0]
lines = content.split("\n")

for i in range(0, min(30, len(lines))):
    s = lines[i].strip()
    if s.startswith("|"):
        print(f"[{i:3d}] {s}")
    else:
        print(f"[{i:3d}] (text) {s[:80]}")

# 현대차 유형자산도 확인
print("\n=== 유형자산 ===")
for i in range(90, min(102, len(lines))):
    s = lines[i].strip()
    if s.startswith("|"):
        print(f"[{i:3d}] {s}")
    else:
        print(f"[{i:3d}] (text) {s[:80]}")
