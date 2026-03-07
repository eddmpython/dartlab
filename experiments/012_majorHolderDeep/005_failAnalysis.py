"""
실험 ID: 012-005
실험명: 실패 종목 분석

목적:
- 5% 실패 5개 (스팩), 소액주주 실패 6개 원인 분석

결과:
(아래 실행 결과 참조)

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

from dartlab.core.dataLoader import loadData, extractCorpName
from dartlab.core.reportSelector import selectReport

FAIL_MIN = ["098070", "368030", "478560", "479960", "489500", "496320"]
FAIL_5 = ["482690", "489210", "489730", "492220", "498390"]


def showSection(code, keyword, sectionFilter):
    df = loadData(code)
    if df is None:
        print(f"  [{code}] 데이터 없음")
        return
    corpName = extractCorpName(df) or code
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        print(f"  [{corpName}] 보고서 없음")
        return

    sections = report.filter(pl.col("section_title").str.contains(sectionFilter))
    print(f"\n=== {corpName} ({code}) ===")

    for i in range(sections.height):
        content = sections["section_content"][i]
        lines = content.split("\n")
        found = False
        printed = 0
        for j, line in enumerate(lines):
            s = line.strip().replace("\xa0", " ")
            if keyword in s:
                found = True
                printed = 0
            if found and printed < 12:
                if s:
                    print(f"  [{j:3d}] {s[:130]}")
                    printed += 1


print("=" * 60)
print("소액주주 실패 종목")
print("=" * 60)

for code in FAIL_MIN:
    showSection(code, "소액주주", "주주에 관한 사항")

print("\n\n" + "=" * 60)
print("5% 이상 주주 실패 종목 (스팩)")
print("=" * 60)

for code in FAIL_5[:2]:
    showSection(code, "5%", "주주에 관한 사항")
