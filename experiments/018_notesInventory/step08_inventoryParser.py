"""재고자산 통합 파서 — 모든 패턴 처리.

패턴 A: 멀티레벨 헤더 (당기말/전기말 스팬)
  | 구분 | 당기말 |  |  | 전기말 |  |  |
  | 취득원가 | 평가충당금 | 장부금액 | 취득원가 | 평가충당금 | 장부금액 |  |

패턴 B: 당기/전기 분리 테이블
  | 재고자산 세부내역 |
  | 당기 | (단위: 천원) |
  |  | 평가전금액 | 평가충당금 | 장부금액 합계 |
  | 상품 | 100 | -10 | 90 |

패턴 C: 단순 2열 (당기/전기 컬럼)
  | 구분 | 당기 | 전기 |
  | 저장품 | 100 | 90 |
"""

import os
import re
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import detectUnit, parseAmount

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


def isPeriodLabel(text: str) -> bool:
    t = text.strip()
    return bool(re.search(r"(당기|전기|당\)|전\)|제\s*\d+\s*\(당\)|제\s*\d+\s*\(전\))", t))


def detectPatternA(tables: list[dict]) -> list[dict] | None:
    """멀티레벨 헤더 (당기말/전기말 스팬) 감지 및 파싱."""
    for table in tables:
        allRows = [table["headers"]] + table["rows"]
        headerText = " ".join(table["headers"])

        startIdx = 0
        if "단위" in headerText:
            startIdx = 0
            allRows = table["rows"]
            if not allRows:
                continue

        spanRowIdx = None
        for idx in range(min(3, len(allRows))):
            row = allRows[idx]
            rowText = " ".join(row)
            emptyCount = sum(1 for c in row if c == "")
            hasPeriod = "당기" in rowText or "전기" in rowText or "(당)" in rowText or "(전)" in rowText
            if hasPeriod and emptyCount >= 2:
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
            isPeriod = "당기" in cell or "전기" in cell or "(당)" in cell or "(전)" in cell
            if cell and isPeriod:
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


def detectPatternB(tables: list[dict]) -> list[dict] | None:
    """당기/전기 분리 테이블 패턴 (세부내역 + 당기(단위) + 헤더 + 데이터)."""
    periodTables = []

    i = 0
    while i < len(tables):
        t = tables[i]
        headers = t["headers"]
        rows = t["rows"]

        if len(headers) <= 2 and rows:
            row0Text = " ".join(rows[0]) if rows else ""
            if "당기" in row0Text or "전기" in row0Text:
                periodName = rows[0][0].strip() if rows[0] else ""
                if i + 1 < len(tables):
                    dataTable = tables[i + 1]
                    dataHeaders = dataTable["headers"]
                    dataRows = dataTable["rows"]
                    filteredHeaders = [h for h in dataHeaders if h]

                    if filteredHeaders and dataRows:
                        items = []
                        for row in dataRows:
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


def detectPatternC(tables: list[dict]) -> list[dict] | None:
    """단순 2열 테이블 (당기/전기가 열, 또는 단일 기간)."""
    for table in tables:
        allRows = [table["headers"]] + table["rows"]

        headerRow = None
        dataStartIdx = 0
        for idx, row in enumerate(allRows):
            if len(row) >= 2:
                rowText = " ".join(row)
                hasAnyPeriod = "당" in rowText or "전" in rowText or "기" in rowText
                if hasAnyPeriod:
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


def parseInventory(section: str) -> list[dict] | None:
    """재고자산 통합 파서."""
    tables = extractRawTables(section)
    if not tables:
        return None

    result = detectPatternA(tables)
    if result:
        return result

    result = detectPatternB(tables)
    if result:
        return result

    result = detectPatternC(tables)
    if result:
        return result

    return None


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    ok = 0
    fail = 0
    failCodes = []
    noSection = 0

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

        section = findNumberedSection(contents, "재고자산")
        if section is None:
            noSection += 1
            continue

        result = parseInventory(section)

        if result:
            ok += 1
        else:
            fail += 1
            failCodes.append((code, corpName))

    total = ok + fail
    print(f"=== 재고자산 통합 파서 결과 ===")
    print(f"섹션 있음: {total}, 없음: {noSection}")
    print(f"파싱 성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}")

    if failCodes:
        print(f"\n실패 목록:")
        for code, name in failCodes:
            print(f"  [{code}] {name}")
