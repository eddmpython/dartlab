"""각 포맷 유형별 대표 기업의 raw 주석 내용 확인."""

import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

SAMPLES = {
    "MOVEMENT_FULL": ("005930", "삼성전자"),
    "MOVEMENT_SIMPLE": ("051910", "LG화학"),
    "GROSS_ACCUM": ("000660", "SK하이닉스"),
    "OTHER_금융": ("055550", "신한지주"),
    "OTHER_현대차": ("005380", "현대자동차"),
    "OTHER_셀트리온": ("068270", "셀트리온"),
    "OTHER_우리금융": ("316140", "우리금융지주"),
    "OTHER_대한항공": ("003490", "대한항공"),
}


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
    for label, (code, name) in SAMPLES.items():
        year, section = getSection(code)
        if section is None:
            print(f"\n{'=' * 80}")
            print(f"[{label}] {code} {name} — 없음")
            continue

        print(f"\n{'=' * 80}")
        print(f"[{label}] {code} {name} — {year}년")
        print(f"{'=' * 80}")
        lines = section.split("\n")
        for line in lines[:80]:
            print(line)
        if len(lines) > 80:
            print(f"\n... ({len(lines) - 80}줄 생략)")
