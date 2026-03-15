"""자본금 변동사항 + 주식의 총수 파서."""

import re


def parseAmount(text: str) -> int | None:
    """숫자 문자열을 정수로 변환."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip().replace(",", "").replace(" ", "")
    if text in ("-", "−", "–", ""):
        return None
    neg = False
    if text.startswith("(") and text.endswith(")"):
        neg = True
        text = text[1:-1]
    elif text.startswith("-") or text.startswith("△") or text.startswith("▲"):
        neg = True
        text = text.lstrip("-△▲")
    text = re.sub(r"[^\d.]", "", text)
    if not text:
        return None
    try:
        val = int(float(text))
        return -val if neg else val
    except ValueError:
        return None


def extractTableBlocks(content: str) -> list[list[str]]:
    """content에서 |(pipe) 구분 테이블 블록들 추출."""
    lines = content.split("\n")
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if "|" in stripped:
            current.append(stripped)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def splitCells(line: str) -> list[str]:
    """파이프 라인을 셀 리스트로 분할."""
    cells = [c.strip() for c in line.split("|")]
    while cells and cells[0] == "":
        cells.pop(0)
    while cells and cells[-1] == "":
        cells.pop()
    return cells


def isSeparatorRow(line: str) -> bool:
    """--- 구분선 행인지 확인."""
    cells = splitCells(line)
    return all(re.match(r"^-+$", c.strip()) for c in cells if c.strip())


# ──────────────────────────────────────────────
# 1. 자본금 변동사항
# ──────────────────────────────────────────────


def parseCapitalChangeTable(block: list[str]) -> dict | None:
    """자본금 변동사항 테이블 파싱.

    Returns:
        {
            "periods": ["56기(2024년말)", ...],
            "common": {"발행주식총수": [v1, ...], "액면금액": [...], "자본금": [...]},
            "preferred": {"발행주식총수": [...], ...},
        }
    """
    dataRows = [line for line in block if not isSeparatorRow(line)]
    if len(dataRows) < 4:
        return None

    headerRow = None
    for row in dataRows:
        cells = splitCells(row)
        if any("기" in c and ("말" in c or "년" in c) for c in cells):
            headerRow = row
            break

    if headerRow is None:
        return None

    headerCells = splitCells(headerRow)
    periods: list[str] = []
    for cell in headerCells:
        if re.search(r"\d+기|\d{4}년", cell):
            periods.append(cell)

    if not periods:
        return None

    currentType = None
    result: dict = {"periods": periods, "common": {}, "preferred": {}}

    for row in dataRows:
        if row == headerRow:
            continue
        cells = splitCells(row)
        if len(cells) < 2:
            continue
        if any("단위" in c for c in cells):
            continue
        if cells[0].strip() == "합계":
            continue

        for cell in cells:
            c = cell.strip()
            if re.search(r"보통주", c):
                currentType = "common"
                break
            elif re.search(r"우선주", c):
                currentType = "preferred"
                break

        if currentType is None:
            continue

        label = None
        for cell in cells:
            c = cell.strip()
            if c and c not in ("보통주", "우선주", "-", ""):
                if re.search(r"발행주식|액면|자본금", c):
                    label = c
                    break

        if label is None:
            continue

        numericCells = []
        for cell in cells:
            c = cell.strip()
            if re.match(r"^[\d,]+$", c):
                numericCells.append(c)
            elif c in ("-", "−", "–"):
                numericCells.append(c)

        values = [parseAmount(c) for c in numericCells[: len(periods)]]

        if "발행주식" in label:
            label = "발행주식총수"
        elif "액면" in label:
            label = "액면금액"
        elif "자본금" in label:
            label = "자본금"

        target = result[currentType]
        if label not in target:
            target[label] = values

    if not result["common"] and not result["preferred"]:
        return None

    return result


# ──────────────────────────────────────────────
# 2. 주식의 총수
# ──────────────────────────────────────────────


def parseShareTotalTable(block: list[str]) -> dict | None:
    """주식의 총수 등 테이블 파싱.

    Returns:
        {
            "referenceDate": "2024년 12월 31일",
            "authorizedShares": {"common": int, "preferred": int, "total": int},
            "issuedShares": {"common": int, "preferred": int, "total": int},
            "reducedShares": {"common": int, "preferred": int, "total": int},
            "outstandingShares": {"common": int, "preferred": int, "total": int},
        }
    """
    dataRows = [line for line in block if not isSeparatorRow(line)]
    if len(dataRows) < 5:
        return None

    refDate = None
    for row in dataRows:
        m = re.search(r"(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)", row)
        if m:
            refDate = m.group(1)
            break

    hasPreferred = any("우선주" in row for row in dataRows)

    result: dict = {"referenceDate": refDate}
    labelMap = {
        "발행할": "authorizedShares",
        "현재까지 발행한": "issuedShares",
        "현재까지발행한": "issuedShares",
        "감소한": "reducedShares",
        "발행주식의 총수": "outstandingShares",
        "발행주식의총수": "outstandingShares",
        "유통주식": "floatingShares",
    }

    for row in dataRows:
        cells = splitCells(row)
        if len(cells) < 3:
            continue

        rowText = " ".join(cells)
        matchedKey = None
        for pattern, key in labelMap.items():
            if pattern in rowText:
                matchedKey = key
                break

        if matchedKey is None:
            continue

        numericValues = []
        for cell in cells:
            c = cell.strip()
            if re.match(r"^[\d,]+$", c):
                numericValues.append(parseAmount(c))
            elif c in ("-", "−", "–"):
                numericValues.append(None)

        if not numericValues:
            continue

        values = {}
        if hasPreferred:
            if len(numericValues) >= 3:
                values = {"common": numericValues[0], "preferred": numericValues[1], "total": numericValues[2]}
            elif len(numericValues) == 2:
                values = {"common": numericValues[0], "total": numericValues[1]}
            elif len(numericValues) == 1:
                values = {"total": numericValues[0]}
        else:
            if len(numericValues) >= 2:
                values = {"common": numericValues[0], "total": numericValues[1]}
            elif len(numericValues) == 1:
                values = {"common": numericValues[0], "total": numericValues[0]}

        if values:
            result[matchedKey] = values

    if len(result) <= 1:
        return None

    return result


# ──────────────────────────────────────────────
# 3. 자기주식 변동
# ──────────────────────────────────────────────


def parseTreasuryStockTable(block: list[str]) -> dict | None:
    """자기주식 변동 테이블 파싱.

    Returns:
        {
            "referenceDate": "2024년 12월 31일",
            "rows": [{"method": str, "stockType": str, "beginQty": int, ...}],
            "totalBegin": int,
            "totalEnd": int,
        }
    """
    dataRows = [line for line in block if not isSeparatorRow(line)]
    if len(dataRows) < 5:
        return None

    hasKeywords = False
    for row in dataRows:
        if "기초수량" in row and "기말수량" in row:
            hasKeywords = True
            break
    if not hasKeywords:
        return None

    refDate = None
    for row in dataRows:
        m = re.search(r"(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)", row)
        if m:
            refDate = m.group(1)
            break

    headerRow = None
    for row in dataRows:
        if "기초수량" in row:
            headerRow = row
            break
    if headerRow is None:
        return None

    headerCells = splitCells(headerRow)
    beginIdx = acquiredIdx = disposedIdx = cancelledIdx = endIdx = None
    for i, cell in enumerate(headerCells):
        if "기초" in cell:
            beginIdx = i
        elif "취득" in cell and "방법" not in cell:
            acquiredIdx = i
        elif "처분" in cell:
            disposedIdx = i
        elif "소각" in cell:
            cancelledIdx = i
        elif "기말" in cell:
            endIdx = i

    if beginIdx is None or endIdx is None:
        return None

    rows = []
    currentMethod = ""
    totalBegin = 0
    totalEnd = 0

    foundHeader = False
    for row in dataRows:
        if row == headerRow:
            foundHeader = True
            continue
        if not foundHeader:
            continue

        cells = splitCells(row)
        if len(cells) < max(beginIdx, endIdx) + 1:
            continue

        stockType = None
        for cell in cells:
            if "보통주" in cell:
                stockType = "보통주"
                break
            elif "우선주" in cell:
                stockType = "우선주"
                break

        if stockType is None:
            for cell in cells[:3]:
                if cell.strip() and cell.strip() not in ("-", ""):
                    if any(kw in cell for kw in ["취득", "처분", "이익", "직접", "간접", "신탁", "기타"]):
                        currentMethod = cell.strip()
            continue

        begin = parseAmount(cells[beginIdx]) if beginIdx < len(cells) else None
        acquired = parseAmount(cells[acquiredIdx]) if acquiredIdx and acquiredIdx < len(cells) else None
        disposed = parseAmount(cells[disposedIdx]) if disposedIdx and disposedIdx < len(cells) else None
        cancelled = parseAmount(cells[cancelledIdx]) if cancelledIdx and cancelledIdx < len(cells) else None
        end = parseAmount(cells[endIdx]) if endIdx < len(cells) else None

        rows.append(
            {
                "method": currentMethod,
                "stockType": stockType,
                "beginQty": begin,
                "acquired": acquired,
                "disposed": disposed,
                "cancelled": cancelled,
                "endQty": end,
            }
        )

        if begin:
            totalBegin += begin
        if end:
            totalEnd += end

    if not rows:
        return None

    return {
        "referenceDate": refDate,
        "rows": rows,
        "totalBegin": totalBegin,
        "totalEnd": totalEnd,
    }
