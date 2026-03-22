"""엔씨소프트 변동표 블록 상세 확인."""

import sys

sys.path.insert(0, "src")

from step03_parser import splitPeriodBlocks

from dartlab.core.dataLoader import loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

df = loadData("036570")
years = sorted(df["year"].unique().to_list(), reverse=True)
for year in years[:2]:
    report = selectReport(df, year, reportKind="annual")
    if report is None:
        continue
    notes = extractNotesContent(report)
    if not notes:
        continue
    section = findNumberedSection(notes, "유형자산")
    if section:
        break

blocks = splitPeriodBlocks(section)
print(f"블록 수: {len(blocks)}")

if len(blocks) >= 3:
    period, block = blocks[2]
    print(f"\n3번째 블록 [{period}]:")
    lines = block.split("\n")
    for i, line in enumerate(lines):
        print(f"  {i}: {line[:150]}")
