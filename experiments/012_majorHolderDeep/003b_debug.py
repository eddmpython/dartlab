"""
실험 ID: 012-003b
실험명: 5% 이상 주주 파서 디버깅

목적:
- 003에서 실패한 7개 종목의 5% 이상 주주 테이블 실제 내용 확인
- 파서 로직 수정 방향 파악

실험일: 2026-03-07
"""

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

FAIL_STOCKS = ["005930", "005380", "051910", "006400", "003550", "034020", "000270"]


for code in FAIL_STOCKS:
    df = loadData(code)
    if df is None:
        continue
    corpName = df["corp_name"][0]
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        continue

    holderSections = report.filter(pl.col("section_title").str.contains("주주에 관한 사항"))

    print(f"\n{'='*60}")
    print(f"{corpName} ({code})")
    print(f"{'='*60}")

    for i in range(holderSections.height):
        content = holderSections["section_content"][i]
        lines = content.split("\n")

        inFive = False
        printed = 0
        for j, line in enumerate(lines):
            s = line.strip().replace("\xa0", " ")
            if "5% 이상" in s or "5%이상" in s:
                inFive = True
                print(f"  [{j:3d}] {s[:120]}")
                printed = 0
                continue

            if inFive and printed < 15:
                if s:
                    print(f"  [{j:3d}] {s[:120]}")
                    printed += 1
                    if "소액주주" in s:
                        break
                else:
                    printed += 1
