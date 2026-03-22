"""차입금 주석 구조 탐색.

차입금 섹션의 일반적인 구조를 파악하여 파서 설계에 활용.
"""

import os
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import detectUnit, extractTables

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

SAMPLE_CODES = [
    "005930",
    "000660",
    "005380",
    "035420",
    "051910",
    "006800",
    "034730",
    "009150",
    "012330",
    "028260",
]

if __name__ == "__main__":
    for code in SAMPLE_CODES:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue
        contents = extractNotesContent(report)
        if not contents:
            continue
        section = findNumberedSection(contents, "차입금")
        if section is None:
            print(f"\n=== [{code}] {corpName} — 섹션 없음 ===")
            continue

        print(f"\n=== [{code}] {corpName} (길이: {len(section)}) ===")
        print(section[:600])
        print("...")
