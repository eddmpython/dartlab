"""나머지 실패 케이스 raw 확인."""

import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

SAMPLES = [
    ("010130", "고려아연"),
    ("030190", "NICE평가정보"),
    ("064400", "LG씨엔에스"),
    ("071970", "HD현대마린엔진"),
    ("308170", "씨티알모빌리티"),
    ("448900", "한국피아이엠"),
    ("489500", "엘케이켐"),
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
    for code, name in SAMPLES:
        year, section = getSection(code)
        print(f"\n{'=' * 80}")
        print(f"[{code}] {name} — {year}년, {len(section) if section else 0}자")
        if section is None:
            continue

        lines = section.split("\n")
        for line in lines[:40]:
            print(line[:150])
        if len(lines) > 40:
            print(f"... ({len(lines) - 40}줄 생략)")
