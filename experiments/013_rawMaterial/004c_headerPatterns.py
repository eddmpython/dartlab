"""실패 종목의 테이블 헤더 패턴 수집."""

import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

dataDir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "docsData")
files = sorted(f for f in os.listdir(dataDir) if f.endswith(".parquet"))

# 모든 종목에서 원재료 섹션 내 테이블 헤더 수집
sectionTitles = {}  # 가. 나. 등 소제목
tableHeaders = {}   # 파이프 테이블 헤더 행

for f in files:
    code = f.replace(".parquet", "")
    try:
        df = loadData(code)
    except Exception:
        continue

    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        continue

    sections = report.filter(
        pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산설비")
    )

    if sections.height == 0:
        continue

    for si in range(sections.height):
        content = sections["section_content"][si]
        lines = content.split("\n")

        for line in lines:
            s = line.strip().replace("\xa0", " ")

            # 소제목 수집 (가. 나. 다. 또는 (1) 등)
            if not s.startswith("|"):
                if re.match(r"^[가나다라마]\.", s) or re.match(r"^\(\d\)", s) or re.match(r"^\d\.\s", s):
                    key = s[:50]
                    if key not in sectionTitles:
                        sectionTitles[key] = 0
                    sectionTitles[key] += 1

            # 테이블 헤더 수집 (매입/원재료/품목 관련)
            if s.startswith("|") and "---" not in s:
                cells = [c.strip() for c in s.split("|") if c.strip()]
                joined = " ".join(cells)
                if any(kw in joined for kw in ["품 목", "품목", "원부재료", "원재료명", "주요자재",
                                                 "매입", "투입", "금액"]):
                    key = joined[:80]
                    if key not in tableHeaders:
                        tableHeaders[key] = 0
                    tableHeaders[key] += 1

print("=== 소제목 빈도 (상위 30) ===")
for title, cnt in sorted(sectionTitles.items(), key=lambda x: -x[1])[:30]:
    print(f"  ({cnt:3d}) {title}")

print("\n=== 테이블 헤더 패턴 (상위 30) ===")
for header, cnt in sorted(tableHeaders.items(), key=lambda x: -x[1])[:30]:
    print(f"  ({cnt:3d}) {header}")
