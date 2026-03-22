"""삼성전자 원재료 + 생산설비 테이블 상세 디버깅."""

import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

df = loadData("005930")
years = sorted(df["year"].unique().to_list(), reverse=True)
report = selectReport(df, years[0], reportKind="annual")

sections = report.filter(
    pl.col("section_title").str.contains("원재료")
    | pl.col("section_title").str.contains("생산설비")
)

content = sections["section_content"][0]
lines = content.split("\n")

print("=== 원재료 테이블 raw lines ===")
inRaw = False
for i, line in enumerate(lines):
    s = line.strip()
    if "주요 원재료" in s and "현황" in s:
        inRaw = True
    if inRaw:
        print(f"  [{i:3d}] {s[:120]}")
        if s.startswith("|"):
            cells = [c.strip() for c in s.split("|") if c.strip()]
            print(f"        cells({len(cells)}): {cells[:8]}")
    if inRaw and ("가격" in s or "나." in s) and i > 10:
        break

print("\n\n=== 생산설비 테이블 raw lines ===")
inEq = False
for i, line in enumerate(lines):
    s = line.strip()
    if "시설 및 설비" in s or ("구 분" in s and "토지" in s):
        inEq = True
    if inEq:
        print(f"  [{i:3d}] {s[:120]}")
        if s.startswith("|"):
            cells = [c.strip() for c in s.split("|") if c.strip()]
            print(f"        cells({len(cells)}): {cells[:10]}")
    if inEq and i > 120:
        break
