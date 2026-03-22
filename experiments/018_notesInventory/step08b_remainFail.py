"""남은 5개 실패 케이스 상세 분석."""

import os
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

FAIL_CODES = ["010400", "079900", "378850", "413390", "475150"]

if __name__ == "__main__":
    for code in FAIL_CODES:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = selectReport(df, years[0], reportKind="annual")
        contents = extractNotesContent(report)
        section = findNumberedSection(contents, "재고자산")

        print(f"\n=== [{code}] {corpName} ===")
        print(f"섹션 길이: {len(section)}")
        print(section[:500])
        print("---")
