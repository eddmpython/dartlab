"""실패 케이스 변동표 위치 탐색."""

import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

FAILS = [
    ("207940", "삼성바이오로직스"),
    ("096770", "SK이노베이션"),
    ("034730", "SK"),
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
    for code, name in FAILS:
        corpName, year, section = getSection(code)
        print(f"\n{'=' * 80}")
        print(f"[{code}] {corpName}")
        if section is None:
            print("  없음")
            continue

        lines = section.split("\n")
        for i, line in enumerate(lines):
            if "변동" in line or "증감" in line:
                print(f"  LINE {i}: {line[:100]}")
            elif "기초" in line and ("기말" in line or "취득" in line):
                print(f"  LINE {i}: {line[:120]}")
            elif line.strip().startswith("|") and "기초" in line:
                print(f"  LINE {i}: {line[:120]}")
        print(f"  총 {len(lines)}줄")
