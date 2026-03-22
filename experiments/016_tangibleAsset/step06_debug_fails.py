"""실패 35개 중 대표 케이스 디버깅."""

import sys

sys.path.insert(0, "src")

from step03_parser import isAssetCategory, isMovementRow, splitCells, splitPeriodBlocks

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

SAMPLES = [
    ("000020", "동화약품"),
    ("010130", "고려아연"),
    ("035900", "JYP"),
    ("036570", "엔씨소프트"),
    ("282330", "BGF리테일"),
    ("307950", "현대오토에버"),
    ("339770", "교촌에프앤비"),
    ("344820", "케이씨씨글라스"),
    ("285130", "SK케미칼"),
]


def getSection(code):
    df = loadData(code)
    corpName = extractCorpName(df)
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
            return corpName, year, section
    return corpName, None, None


if __name__ == "__main__":
    for code, name in SAMPLES:
        corpName, year, section = getSection(code)
        print(f"\n{'=' * 80}")
        print(f"[{code}] {corpName} — {year}년")
        if section is None:
            print("  없음")
            continue

        blocks = splitPeriodBlocks(section)
        print(f"  블록 수: {len(blocks)}")

        if len(blocks) == 0:
            lines = section.split("\n")
            print(f"  섹션 {len(lines)}줄, 테이블 행들:")
            for i, line in enumerate(lines[:50]):
                s = line.strip()
                if s.startswith("|") and "---" not in s:
                    cells = splitCells(s)
                    mvCount = sum(1 for c in cells if isMovementRow(c))
                    assetCount = sum(1 for c in cells if isAssetCategory(c))
                    print(f"    L{i}: mv={mvCount} asset={assetCount} [{cells[0][:20]}] cells={len(cells)}")
                elif s and not s.startswith("|"):
                    print(f"    L{i}: TEXT: {s[:80]}")
        else:
            for period, block in blocks[:4]:
                lines = block.split("\n")
                tableLines = [l for l in lines if l.strip().startswith("|") and "---" not in l.strip()]
                print(f"  [{period}] {len(tableLines)}개 테이블행")
                for tl in tableLines[:5]:
                    cells = splitCells(tl.strip())
                    mvCount = sum(1 for c in cells if isMovementRow(c))
                    assetCount = sum(1 for c in cells if isAssetCategory(c))
                    print(f"    mv={mvCount} asset={assetCount} [{cells[0][:25]}] cells={len(cells)}")
