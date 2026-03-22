"""남은 13개 실패 케이스 raw 확인."""

import sys

sys.path.insert(0, "src")

from step03_parser import isAssetCategory, isMovementRow, splitCells, splitPeriodBlocks

from dartlab.core.dataLoader import loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

SAMPLES = [
    ("010130", "고려아연", 6378),
    ("071970", "HD현대마린엔진", 4126),
    ("092780", "DYP", 3168),
    ("098070", "한텍", 2826),
    ("139990", "아주스틸", 480),
    ("285130", "SK케미칼", 297),
    ("332190", "오션스바이오", 644),
    ("334890", "이지스밸류플러스리츠", 654),
    ("372910", "한컴라이프케어", 3258),
    ("454910", "두산로보틱스", 1816),
    ("475830", "오름테라퓨틱", 1797),
    ("489500", "엘케이켐", 4219),
    ("499790", "GS피앤엘", 1231),
]


def getSection(code):
    df = loadData(code)
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
            return year, section
    return None, None


if __name__ == "__main__":
    for code, name, size in SAMPLES:
        year, section = getSection(code)
        print(f"\n{'=' * 80}")
        print(f"[{code}] {name} — {year}년, {size}자")
        if section is None:
            print("  없음")
            continue

        blocks = splitPeriodBlocks(section)
        print(f"  블록 수: {len(blocks)}")
        for period, block in blocks:
            print(f"  [{period}] {len(block)}자")

        lines = section.split("\n")
        for i, line in enumerate(lines[:60]):
            s = line.strip()
            if s.startswith("|") and "---" not in s:
                cells = splitCells(s)
                mvCount = sum(1 for c in cells if isMovementRow(c))
                assetCount = sum(1 for c in cells if isAssetCategory(c))
                marker = ""
                if mvCount >= 3:
                    marker = " ← MOVEMENT HEADER"
                elif assetCount >= 3:
                    marker = " ← ASSET HEADER"
                print(f"  L{i:02d}: cells={len(cells)} mv={mvCount} asset={assetCount} | {s[:120]}{marker}")
            elif s and not s.startswith("|"):
                print(f"  L{i:02d}: TEXT: {s[:120]}")
            elif not s:
                pass
