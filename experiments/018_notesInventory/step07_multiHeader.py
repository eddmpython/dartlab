"""멀티레벨 헤더 재고자산 테이블 파싱 실험.

핵심 패턴:
| (단위:천원) |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| 구분 | 당기말 |  |  | 전기말 |  |  |
| 취득원가 | 평가충당금 | 장부금액 | 취득원가 | 평가충당금 | 장부금액 |  |
| 제품 | 100 | -10 | 90 | 80 | -5 | 75 |

빈 셀을 유지해야 올바르게 파싱 가능.
"""

import os
import re
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import detectUnit

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


def extractRawTables(content: str) -> list[dict]:
    """빈 셀을 유지하는 테이블 파싱."""
    tables = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            cells = [c.strip() for c in line.split("|")]
            if cells and cells[0] == "":
                cells = cells[1:]
            if cells and cells[-1] == "":
                cells = cells[:-1]
            headers = cells
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rowLine = lines[i].strip()
                if "---" in rowLine:
                    if rows:
                        newHeader = rows.pop()
                        if rows:
                            tables.append({"headers": headers, "rows": rows})
                        headers = newHeader
                        rows = []
                    i += 1
                    continue
                rowCells = [c.strip() for c in rowLine.split("|")]
                if rowCells and rowCells[0] == "":
                    rowCells = rowCells[1:]
                if rowCells and rowCells[-1] == "":
                    rowCells = rowCells[:-1]
                rows.append(rowCells)
                i += 1
            if headers and rows:
                tables.append({"headers": headers, "rows": rows})
        else:
            i += 1
    return tables


def isMultiLevelHeader(rows: list[list[str]]) -> bool:
    """당기말/전기말 스팬 형태 멀티레벨 헤더인지 판단."""
    if len(rows) < 1:
        return False
    for row in rows[:3]:
        rowText = " ".join(row)
        if ("당기" in rowText and "전기" in rowText) or ("당" in rowText and "전" in rowText):
            emptyCount = sum(1 for c in row if c == "")
            if emptyCount >= 2:
                return True
    return False


def parseMultiLevel(tables: list[dict]) -> list[dict]:
    """멀티레벨 헤더 테이블에서 당기/전기 구조 추출."""
    results = []
    for table in tables:
        headers = table["headers"]
        rows = table["rows"]
        allRows = [headers] + rows

        headerText = " ".join(headers)
        if "단위" in headerText:
            allRows = rows
            if not allRows:
                continue

        spanRow = None
        subHeaderRow = None
        dataStartIdx = 0

        for idx, row in enumerate(allRows):
            rowText = " ".join(row)
            emptyCount = sum(1 for c in row if c == "")
            if ("당기" in rowText or "전기" in rowText) and emptyCount >= 2:
                spanRow = row
                if idx + 1 < len(allRows):
                    subHeaderRow = allRows[idx + 1]
                    dataStartIdx = idx + 2
                break

        if spanRow is None or subHeaderRow is None:
            continue

        nCols = len(spanRow)
        periods = []
        currentPeriod = None
        for ci, cell in enumerate(spanRow):
            if cell:
                if "당기" in cell or "전기" in cell:
                    currentPeriod = {"name": cell.strip(), "startCol": ci, "endCol": ci}
                elif currentPeriod:
                    currentPeriod = None
            else:
                if currentPeriod:
                    currentPeriod["endCol"] = ci

        periods = []
        currentPeriod = None
        for ci, cell in enumerate(spanRow):
            if cell and ("당기" in cell or "전기" in cell or "당" in cell or "전" in cell):
                if currentPeriod:
                    periods.append(currentPeriod)
                currentPeriod = {"name": cell.strip(), "startCol": ci, "endCol": ci}
            elif cell == "" and currentPeriod:
                currentPeriod["endCol"] = ci
            elif cell and currentPeriod:
                periods.append(currentPeriod)
                currentPeriod = None
        if currentPeriod:
            periods.append(currentPeriod)

        if not periods:
            continue

        dataRows = allRows[dataStartIdx:]

        for period in periods:
            subHeaders = subHeaderRow[period["startCol"]:period["endCol"] + 1]
            subHeaders = [h for h in subHeaders if h]

            items = []
            for row in dataRows:
                if len(row) <= period["endCol"]:
                    continue
                name = row[0].strip() if row[0] else ""
                if not name:
                    continue
                values = row[period["startCol"]:period["endCol"] + 1]
                items.append({"name": name, "values": values})

            if items:
                results.append({
                    "period": period["name"],
                    "subHeaders": subHeaders,
                    "items": items,
                })

    return results


FAIL_CODES = [
    "000020", "001210", "009900", "022100", "036570",
    "089860", "126720", "188040", "307950", "465770",
]


if __name__ == "__main__":
    ok = 0
    fail = 0

    for code in FAIL_CODES:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue
        contents = extractNotesContent(report)
        if not contents:
            continue
        section = findNumberedSection(contents, "재고자산")
        if section is None:
            continue

        tables = extractRawTables(section)
        parsed = parseMultiLevel(tables)

        if parsed:
            ok += 1
            print(f"OK [{code}] {corpName}")
            for p in parsed:
                print(f"  {p['period']}: subHeaders={p['subHeaders']}")
                for item in p["items"][:3]:
                    print(f"    {item['name']}: {item['values']}")
        else:
            fail += 1
            print(f"FAIL [{code}] {corpName}")
            for i, t in enumerate(tables):
                print(f"  Table {i}: headers={t['headers'][:5]}")
                for row in t["rows"][:3]:
                    print(f"    {row[:5]}")

    print(f"\n결과: {ok}/{ok+fail}")
