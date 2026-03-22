"""삼성전자 재고자산 파싱 디버그."""

import sys

sys.path.insert(0, "src")

from step08_inventoryParser import extractRawTables

from dartlab.core.dataLoader import loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

if __name__ == "__main__":
    df = loadData("005930")
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    contents = extractNotesContent(report)
    section = findNumberedSection(contents, "재고자산")

    print("=== 섹션 시작 200자 ===")
    print(section[:500])
    print("\n=== Raw Tables ===")
    tables = extractRawTables(section)
    for i, t in enumerate(tables):
        print(f"\nTable {i}:")
        print(f"  headers: {t['headers']}")
        for j, row in enumerate(t["rows"][:5]):
            print(f"  row {j}: {row}")
