"""parse_logic 실패 케이스 상세 분석.

기간 마커 없이 테이블만 있는 케이스 분석.
"""

import os
import re
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import extractRawTables, parseNotesTable

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

FAIL_KEYWORDS = ["약정사항", "담보", "우발부채", "금융자산", "공정가치"]


def hasPeriodText(text: str) -> bool:
    return bool(re.search(r"(당기|전기|당반기|전반기|당분기|전분기|\(당\)|\(전\))", text))


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    for kw in FAIL_KEYWORDS:
        parseLogicFails = []

        for code in codes:
            df = loadData(code)
            years = sorted(df["year"].unique().to_list(), reverse=True)
            report = selectReport(df, years[0], reportKind="annual")
            if report is None:
                continue
            contents = extractNotesContent(report)
            if not contents:
                continue
            section = findNumberedSection(contents, kw)
            if section is None:
                continue

            result = parseNotesTable(section)
            if result:
                continue

            rawTables = extractRawTables(section)
            if not rawTables:
                continue
            totalRows = sum(len(t["rows"]) for t in rawTables)
            if totalRows <= 1:
                continue

            corpName = extractCorpName(df)
            parseLogicFails.append((code, corpName, section, rawTables))

        if not parseLogicFails:
            continue

        print(f"\n{'='*70}")
        print(f"=== {kw} — parse_logic 실패 {len(parseLogicFails)}건 ===")

        for code, name, section, rawTables in parseLogicFails[:5]:
            print(f"\n  [{code}] {name}")
            print(f"    rawTables: {len(rawTables)}개")

            sectionText = section[:500]
            hasPeriod = hasPeriodText(sectionText)
            print(f"    섹션 전체에 기간 키워드: {hasPeriod}")

            for i, tbl in enumerate(rawTables):
                headers = tbl["headers"]
                rows = tbl["rows"]
                headerStr = " | ".join(str(h) for h in headers)
                print(f"\n    테이블{i}: headers={len(headers)}, rows={len(rows)}")
                print(f"      header: {headerStr[:120]}")

                hasPH = hasPeriodText(headerStr)
                print(f"      기간마커(header): {hasPH}")

                for j, row in enumerate(rows[:2]):
                    rowStr = " | ".join(str(c) for c in row)
                    hasPR = hasPeriodText(rowStr)
                    print(f"      row[{j}]: {rowStr[:120]}  period={hasPR}")

            allText = " ".join(str(c) for tbl in rawTables for c in tbl["headers"])
            allText += " " + " ".join(str(c) for tbl in rawTables for row in tbl["rows"] for c in row)
            if not hasPeriodText(allText):
                print(f"    >>> 테이블 전체에 기간 키워드 없음 — 단일 시점 테이블")
            else:
                print(f"    >>> 기간 키워드는 있으나 패턴 감지 실패")
