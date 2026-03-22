"""모든 후보의 extractTables 기반 성공률 측정.

단순히 "테이블이 있고 행이 있는가"로 판단.
"""

import os
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import extractTables

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

CANDIDATES = [
    "재고자산",
    "주당이익",
    "충당부채",
    "차입금",
    "매출채권",
    "리스",
    "투자부동산",
    "무형자산",
]


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    print(f"{'키워드':<12s}  {'섹션있음':>6s}  {'테이블OK':>6s}  {'성공률':>6s}  {'섹션없음':>6s}")
    print("-" * 50)

    for keyword in CANDIDATES:
        hasSection = 0
        tableOk = 0
        noSection = 0

        for code in codes:
            df = loadData(code)
            years = sorted(df["year"].unique().to_list(), reverse=True)

            report = selectReport(df, years[0], reportKind="annual")
            if report is None:
                continue

            contents = extractNotesContent(report)
            if not contents:
                continue

            section = findNumberedSection(contents, keyword)
            if section is None:
                noSection += 1
                continue

            hasSection += 1
            tables = extractTables(section)

            hasData = False
            for t in tables:
                if len(t["headers"]) >= 2 and len(t["rows"]) >= 2:
                    headerText = " ".join(t["headers"])
                    if "단위" not in headerText:
                        hasData = True
                        break

            if hasData:
                tableOk += 1

        rate = tableOk / hasSection * 100 if hasSection else 0
        print(f"{keyword:<12s}  {hasSection:6d}  {tableOk:6d}  {rate:5.1f}%  {noSection:6d}")
