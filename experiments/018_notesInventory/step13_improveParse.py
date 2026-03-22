"""parseNotesTable 개선 실험.

1. _hasPeriodMarker: 공백 포함 기간 마커 감지 (당 기 말 → 당기말)
2. Pattern D: 기간 마커 없는 단일 시점 테이블 지원
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


def _hasPeriodMarkerV2(text: str) -> bool:
    normalized = re.sub(r"\s+", "", text)
    return bool(re.search(r"(당기|전기|\(당\)|\(전\))", normalized))


def _detectPatternD(tables: list[dict]) -> list[dict] | None:
    """단일 시점 테이블 — 기간 마커 없는 일반 테이블.

    조건:
    - 2개 이상의 열
    - 2개 이상의 데이터 행
    - 적어도 1개 이상의 숫자 값
    """
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
            cleanCells = [c for c in row if c.strip()]
            if len(cleanCells) >= 2:
                hasNumber = any(re.search(r"\d", c) for c in cleanCells)
                if not hasNumber:
                    headerRow = row
                    dataStartIdx = idx + 1
                    break

        if headerRow is None:
            if len(allRows) >= 2:
                headerRow = allRows[0]
                dataStartIdx = 1
            else:
                continue

        dataRows = allRows[dataStartIdx:]
        if len(dataRows) < 1:
            continue

        cleanHeaders = [h for h in headerRow if h.strip()]
        if len(cleanHeaders) < 2:
            continue

        hasAnyNumber = False
        items = []
        for row in dataRows:
            name = row[0].strip() if row else ""
            if not name:
                continue
            values = row[1:]
            if any(re.search(r"\d", v) for v in values if v):
                hasAnyNumber = True
            items.append({"name": name, "values": values})

        if items and hasAnyNumber:
            return [{
                "pattern": "D",
                "period": "현재",
                "headers": cleanHeaders,
                "items": items,
            }]

    return None


def parseNotesTableV2(section: str) -> list[dict] | None:
    """개선된 parseNotesTable — 기존 A/B/C + D 패턴."""
    result = parseNotesTable(section)
    if result:
        return result

    tables = extractRawTables(section)
    if not tables:
        return None

    return _detectPatternD(tables)


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    ALL_KEYWORDS = [
        "재고자산", "주당이익", "충당부채", "차입금", "매출채권",
        "리스", "투자부동산", "무형자산",
        "법인세", "특수관계자", "약정사항", "금융자산", "공정가치",
        "이익잉여금", "금융부채", "기타포괄손익", "사채",
        "종업원급여", "퇴직급여", "확정급여", "재무위험", "우발부채", "담보",
    ]

    print("=== parseNotesTable (기존) vs V2 (D패턴 추가) ===\n")
    print(f"{'키워드':12s}  {'섹션':>4s}  {'기존':>4s}  {'V2':>4s}  {'기존%':>6s}  {'V2%':>6s}  {'개선':>4s}")
    print("-" * 60)

    for kw in ALL_KEYWORDS:
        found = 0
        parsedOld = 0
        parsedNew = 0

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
            found += 1

            oldResult = parseNotesTable(section)
            if oldResult:
                parsedOld += 1

            newResult = parseNotesTableV2(section)
            if newResult:
                parsedNew += 1

        if found == 0:
            continue

        oldRate = parsedOld / found * 100
        newRate = parsedNew / found * 100
        diff = parsedNew - parsedOld
        diffStr = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else ""
        print(f"{kw:12s}  {found:4d}  {parsedOld:4d}  {parsedNew:4d}  {oldRate:5.1f}%  {newRate:5.1f}%  {diffStr:>4s}")
