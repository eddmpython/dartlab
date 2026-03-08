import re

from dartlab.core.constants import DEFAULT_UNIT_SCALE, UNIT_SCALE


def extractTables(content: str) -> list[dict]:
    """마크다운 테이블 파싱. DART 중첩 테이블(단위행+본체) 처리."""
    tables = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c != ""]
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
                rowCells = [c for c in rowCells if c != ""]
                if rowCells:
                    rows.append(rowCells)
                i += 1
            if headers and rows and len(headers) >= 2:
                tables.append({"headers": headers, "rows": rows})
        else:
            i += 1
    return tables


def parseAmount(text: str) -> float | None:
    """금액/숫자 문자열 → float. 음수 마커(△, ▲, 괄호) 처리."""
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip().replace(",", "").replace(" ", "")
    if re.match(r"^\(주\d*\)$", cleaned):
        return None
    isNeg = "△" in cleaned or "▲" in cleaned or (
        cleaned.startswith("(") and cleaned.endswith(")")
    )
    cleaned = re.sub(r"[△▲\(\)]", "", cleaned)
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned or cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    val = float(cleaned)
    return -val if isNeg else val


def detectUnit(content: str) -> float:
    """content에서 단위를 감지. 백만원=1, 천원=0.001, 원=0.000001 반환."""
    m = re.search(r"단위\s*[：:]\s*(백만원|천원|원)", content)
    if m:
        return UNIT_SCALE.get(m.group(1), DEFAULT_UNIT_SCALE)
    return DEFAULT_UNIT_SCALE


def extractRawTables(content: str) -> list[dict]:
    """마크다운 테이블 파싱 (빈 셀 유지). 멀티레벨 헤더 처리에 필수."""
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
    normalized = re.sub(r"\s+", "", text)
    return bool(re.search(r"(당기|전기|\(당\)|\(전\))", normalized))


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
                    "pattern": "A",
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
                                "pattern": "B",
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
                "pattern": "C",
                "period": "전체",
                "headers": cleanHeaders,
                "items": items,
            }]
    return None


def _detectPatternD(tables: list[dict]) -> list[dict] | None:
    """단일 시점 테이블 — 기간 마커 없는 일반 테이블.

    약정사항, 담보, 우발부채 등 현재 상태만 나열하는 테이블.
    2개 이상 열, 1개 이상 데이터 행, 숫자 값 포함 시 추출.
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
        if not dataRows:
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


def parseNotesTable(section: str) -> list[dict] | None:
    """주석 섹션에서 테이블 데이터 추출. 4가지 패턴 자동 감지.

    패턴 A: 멀티레벨 헤더 (당기말/전기말 스팬)
    패턴 B: 당기/전기 분리 테이블 (XBRL 공시)
    패턴 C: 단순 테이블 (기간이 열)
    패턴 D: 단일 시점 테이블 (기간 마커 없음)

    반환: [{"pattern": "A"|"B"|"C"|"D", "period": str, "headers": list, "items": list}]
    """
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

    result = _detectPatternD(tables)
    if result:
        return result

    return None


def extractAccounts(content: str) -> tuple[dict[str, list[float | None]], list[str]]:
    """요약재무정보 테이블에서 {계정명: [당기, 전기, ...]} 추출. 단위 정규화 포함."""
    unit = detectUnit(content)
    tables = extractTables(content)

    if not tables:
        rows = []
        headers = None
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            if "---" in stripped:
                continue
            cells = [c.strip() for c in stripped.split("|")]
            cells = [c for c in cells if c != ""]
            if not cells:
                continue
            if any("단위" in c for c in cells):
                continue
            cellText = " ".join(cells)
            if headers is None and ("기" in cellText or "년" in cellText) and len(cells) >= 2:
                headers = cells
                continue
            if headers and len(cells) >= 2:
                rows.append(cells)
        if headers and rows:
            tables = [{"headers": headers, "rows": rows}]

    result = {}
    order = []
    for table in tables:
        headers = table["headers"]
        if len(headers) < 2:
            continue
        headerText = " ".join(headers)
        if "단위" in headerText or all(not h for h in headers[1:]):
            for ri in range(min(3, len(table["rows"]))):
                candidate = table["rows"][ri]
                candText = " ".join(candidate)
                if "기" in candText or "년" in candText:
                    headers = candidate
                    table["rows"] = table["rows"][ri + 1:]
                    break
            else:
                continue
        if not any("기" in h or "년" in h for h in headers[1:]):
            continue
        for row in table["rows"]:
            if len(row) < 2:
                continue
            name = row[0].strip()
            if not name or "※" in name or "월" in name:
                continue
            if re.match(r"^\d{4}년", name):
                continue
            name = re.sub(r"(?<=[\uAC00-\uD7A3])\s+(?=[\uAC00-\uD7A3])", "", name)
            name = re.sub(r"[\[\]ㆍ·]", "", name).strip()
            if not name:
                continue
            amounts = [parseAmount(cell) for cell in row[1:]]
            if all(a is None for a in amounts):
                continue
            if unit != 1.0:
                amounts = [a * unit if a is not None else None for a in amounts]
            if name in result:
                continue
            result[name] = amounts
            order.append(name)
    return result, order
