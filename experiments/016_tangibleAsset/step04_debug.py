"""실패 케이스 디버깅."""

import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

FAILS = [
    ("105560", "KB금융"),
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
        print(f"[{code}] {corpName} — {year}년")
        print(f"{'=' * 80}")
        if section is None:
            print("  → 주석 없음")
            continue

        lines = section.split("\n")
        for line in lines[:60]:
            print(line)
        if len(lines) > 60:
            print(f"\n... ({len(lines) - 60}줄 생략, 총 {len(lines)}줄)")
