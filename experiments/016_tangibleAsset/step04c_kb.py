"""KB금융 디버깅."""

import sys

sys.path.insert(0, "src")

from step03_parser import isAssetCategory, isMovementRow, normalizeLabel, splitCells, splitPeriodBlocks

from dartlab.core.dataLoader import loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

df = loadData("105560")
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
for period, block in blocks:
    print(f"\n  [{period}] 블록 길이: {len(block)}")
    lines = block.split("\n")
    for i, line in enumerate(lines[:15]):
        s = line.strip()
        if s.startswith("|") and "---" not in s:
            cells = splitCells(s)
            mvCount = sum(1 for c in cells if isMovementRow(c))
            assetCount = sum(1 for c in cells if isAssetCategory(c))
            print(f"    L{i}: mv={mvCount} asset={assetCount} cells={cells[:8]}")
        else:
            print(f"    L{i}: {s[:80]}")
