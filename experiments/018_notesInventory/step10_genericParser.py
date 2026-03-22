"""범용 주석 테이블 파서.

재고자산에서 검증한 3가지 패턴을 일반화.
모든 후보(재고, 차입금, 매출채권, 충당부채 등)에 동일 파서 적용.
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


def _hasPeriodMarker(text: str) -> bool:
    return bool(re.search(r"(당기|전기|\(당\)|\(전\))", text))


def _detectPatternA(tables: list[dict]) -> list[dict] | None:
    """멀티레벨 헤더 (당기말/전기말 스팬)."""
    for table in tables:
        allRows = [table["headers"]] + table["rows"]
        headerText = " ".join(table["headers"])

        if "단위" in headerText:
            allRows = table["rows"]
            if not allRows:
                continue

        spanRowIdx = None
        for idx in range(min(3, len(allRows))):
            row = allRows[idx]
            rowText = " ".join(row)
            emptyCount = sum(1 for c in row if c == "")
            if _hasPeriodMarker(rowText) and emptyCount >= 2:
                spanRowIdx = idx
                break

        if spanRowIdx is None:
            continue

        spanRow = allRows[spanRowIdx]
        if spanRowIdx + 1 >= len(allRows):
            continue
        subHeaderRow = allRows[spanRowIdx + 1]
        dataRows = allRows[spanRowIdx + 2:]

        periods = []
        currentPeriod = None
        for ci, cell in enumerate(spanRow):
            if cell and _hasPeriodMarker(cell):
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

        results = []
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
                    "headers": subHeaders,
                    "items": items,
                })

        if results:
            return results
    return None


def _detectPatternB(tables: list[dict]) -> list[dict] | None:
    """당기/전기 분리 테이블 (세부내역 헤더 + 당기(단위) + 데이터 테이블)."""
    periodTables = []
    i = 0
    while i < len(tables):
        t = tables[i]
        headers = t["headers"]
        rows = t["rows"]

        if len(headers) <= 2 and rows:
            row0Text = " ".join(rows[0]) if rows else ""
            if _hasPeriodMarker(row0Text):
                periodName = rows[0][0].strip() if rows[0] else ""
                if i + 1 < len(tables):
                    dataTable = tables[i + 1]
                    filteredHeaders = [h for h in dataTable["headers"] if h]

                    if filteredHeaders and dataTable["rows"]:
                        items = []
                        for row in dataTable["rows"]:
                            name = row[0].strip() if row else ""
                            if not name:
                                continue
                            values = row[1:]
                            items.append({"name": name, "values": values})

                        if items:
                            periodTables.append({
                                "period": periodName,
                                "headers": filteredHeaders,
                                "items": items,
                            })
                    i += 2
                    continue
        i += 1
    return periodTables if periodTables else None


def _detectPatternC(tables: list[dict]) -> list[dict] | None:
    """단순 테이블 (당기/전기가 열, 또는 단일 기간)."""
    for table in tables:
        allRows = [table["headers"]] + table["rows"]
        headerText = " ".join(table["headers"])
        if "단위" in headerText:
            allRows = table["rows"]
            if not allRows:
                continue

        headerRow = None
        dataStartIdx = 0
        for idx, row in enumerate(allRows):
            if len(row) >= 2:
                rowText = " ".join(row)
                if _hasPeriodMarker(rowText) or "기" in rowText:
                    emptyCount = sum(1 for c in row if c == "")
                    if emptyCount < 2:
                        headerRow = row
                        dataStartIdx = idx + 1
                        break

        if headerRow is None:
            continue

        dataRows = allRows[dataStartIdx:]
        if not dataRows:
            continue

        cleanHeaders = [h for h in headerRow if h]
        if len(cleanHeaders) < 2:
            continue

        items = []
        for row in dataRows:
            name = row[0].strip() if row else ""
            if not name:
                continue
            values = row[1:]
            items.append({"name": name, "values": values})

        if items:
            return [{
                "period": "전체",
                "headers": cleanHeaders,
                "items": items,
            }]
    return None


def parseNotesTable(section: str) -> list[dict] | None:
    """범용 주석 테이블 파서. 3가지 패턴 순서대로 시도."""
    tables = extractRawTables(section)
    if not tables:
        return None

    result = _detectPatternA(tables)
    if result:
        return result

    result = _detectPatternB(tables)
    if result:
        return result

    result = _detectPatternC(tables)
    if result:
        return result

    return None


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

    print(f"{'키워드':<12s}  {'섹션있음':>6s}  {'파싱OK':>6s}  {'성공률':>6s}  {'섹션없음':>6s}")
    print("-" * 55)

    for keyword in CANDIDATES:
        hasSection = 0
        ok = 0
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
            result = parseNotesTable(section)
            if result:
                ok += 1

        rate = ok / hasSection * 100 if hasSection else 0
        print(f"{keyword:<12s}  {hasSection:6d}  {ok:6d}  {rate:5.1f}%  {noSection:6d}")
