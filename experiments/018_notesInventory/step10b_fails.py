"""범용 파서 실패 케이스 확인."""

import os
import sys

sys.path.insert(0, "src")

from step10_genericParser import parseNotesTable

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

CHECK = {
    "재고자산": [],
    "차입금": [],
    "투자부동산": [],
}

if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    for keyword in CHECK:
        for code in codes:
            df = loadData(code)
            corpName = extractCorpName(df)
            years = sorted(df["year"].unique().to_list(), reverse=True)

            report = selectReport(df, years[0], reportKind="annual")
            if report is None:
                continue

            contents = extractNotesContent(report)
            if not contents:
                continue

            section = findNumberedSection(contents, keyword)
            if section is None:
                continue

            result = parseNotesTable(section)
            if result is None:
                CHECK[keyword].append((code, corpName, section[:300]))

    for keyword, fails in CHECK.items():
        print(f"\n=== {keyword} 실패 ({len(fails)}건) ===")
        for code, name, preview in fails:
            print(f"\n[{code}] {name}")
            print(preview)
