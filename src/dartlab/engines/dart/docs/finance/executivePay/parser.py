"""임원 보수 테이블 파서."""

import re

# ──────────────────────────────────────────────
# 유틸리티
# ──────────────────────────────────────────────

def _cellsFromLine(line: str) -> list[str]:
    return [c.strip() for c in line.split("|")[1:-1]]


def _isSeparator(cells: list[str]) -> bool:
    return all(re.match(r"^-+$", c.strip()) or c.strip() == "" for c in cells)


def _parseFloat(text: str) -> float | None:
    if not text or text.strip() in ("-", "", "—", "해당없음"):
        return None
    text = text.replace(",", "").replace(" ", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


# ──────────────────────────────────────────────
# 테이블 블록 추출 + 분류
# ──────────────────────────────────────────────

def extractTableBlocks(content: str) -> list[list[str]]:
    """content에서 연속된 파이프라인 블록 추출."""
    lines = content.split("\n")
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip().startswith("|"):
            current.append(line)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def classifyBlock(block: list[str]) -> str:
    """테이블 블록 분류.

    Returns: "payByType" | "payIndividual" | "other"
    """
    allText = ""
    for line in block[:6]:
        cells = _cellsFromLine(line)
        if not _isSeparator(cells):
            allText += " " + " ".join(c for c in cells if c.strip())

    if re.search(r"구\s*분", allText) and re.search(r"보수총액|보수\s*총\s*액", allText):
        if re.search(r"등기이사|사외이사|감사위원|1인당", allText):
            return "payByType"
        if re.search(r"인원수", allText) and re.search(r"1인당|평균", allText):
            return "payByType"

    if re.search(r"이름", allText) and re.search(r"직위", allText) and re.search(r"보수총액", allText):
        return "payIndividual"

    return "other"


# ──────────────────────────────────────────────
# 유형별 보수 파서
# ──────────────────────────────────────────────

def parsePayByTypeBlock(block: list[str]) -> list[dict]:
    """유형별 보수 테이블 파싱.

    Returns: [{"category": str, "headcount": int, "totalPay": float, "avgPay": float}]
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 3:
        return []

    headerIdx = None
    for i, row in enumerate(rows):
        text = " ".join(row)
        if re.search(r"구\s*분", text) and re.search(r"인원|보수", text):
            headerIdx = i
            break

    if headerIdx is None:
        return []

    header = rows[headerIdx]
    nCols = len(header)

    colCategory = None
    colHeadcount = None
    colTotalPay = None
    colAvgPay = None

    for i, h in enumerate(header):
        h = h.replace(" ", "")
        if re.search(r"구분", h):
            colCategory = i
        elif re.search(r"인원", h):
            colHeadcount = i
        elif re.search(r"보수총액", h):
            colTotalPay = i
        elif re.search(r"1인당|평균보수", h):
            colAvgPay = i

    if colCategory is None:
        colCategory = 0
    if colHeadcount is None or colTotalPay is None:
        return []

    dataStart = headerIdx + 1

    result = []
    for row in rows[dataStart:]:
        if len(row) < 3:
            continue
        while len(row) < nCols:
            row.append("")

        category = row[colCategory].strip()
        if not category or re.search(r"비\s*고", category):
            continue
        # "계" 합계 행 제외
        if category in ("계", "합계", "합 계"):
            continue

        headcount = _parseFloat(row[colHeadcount])
        totalPay = _parseFloat(row[colTotalPay])
        avgPay = _parseFloat(row[colAvgPay]) if colAvgPay is not None else None

        if headcount is None and totalPay is None:
            continue

        result.append({
            "category": _normalizeCategory(category),
            "headcount": int(headcount) if headcount is not None else None,
            "totalPay": totalPay,
            "avgPay": avgPay,
        })

    return result


def _normalizeCategory(raw: str) -> str:
    """보수 카테고리 정규화."""
    raw = raw.strip()
    if re.search(r"등기이사.*사외.*제외|사내이사", raw):
        return "등기이사"
    if re.search(r"사외이사.*감사.*제외", raw):
        return "사외이사"
    if re.search(r"감사위원", raw):
        return "감사위원"
    if re.search(r"사외이사", raw):
        return "사외이사"
    if re.search(r"감사", raw):
        return "감사"
    if re.search(r"등기이사", raw):
        return "등기이사"
    return raw


# ──────────────────────────────────────────────
# 5억 초과 개인별 파서
# ──────────────────────────────────────────────

def parsePayIndividualBlock(block: list[str]) -> list[dict]:
    """5억 초과 개인별 보수 테이블 파싱.

    Returns: [{"name": str, "position": str, "totalPay": float}]
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 3:
        return []

    headerIdx = None
    for i, row in enumerate(rows):
        text = " ".join(row)
        if "이름" in text and "보수총액" in text:
            headerIdx = i
            break

    if headerIdx is None:
        return []

    header = rows[headerIdx]
    nCols = len(header)

    colName = None
    colPosition = None
    colTotalPay = None

    for i, h in enumerate(header):
        h = h.strip()
        if "이름" in h:
            colName = i
        elif "직위" in h:
            colPosition = i
        elif "보수총액" in h:
            colTotalPay = i

    if colName is None or colTotalPay is None:
        return []

    dataStart = headerIdx + 1

    result = []
    for row in rows[dataStart:]:
        while len(row) < nCols:
            row.append("")

        name = row[colName].strip()
        if not name:
            continue

        position = row[colPosition].strip() if colPosition is not None else ""
        totalPay = _parseFloat(row[colTotalPay])

        if totalPay is None:
            continue

        result.append({
            "name": name,
            "position": position,
            "totalPay": totalPay,
        })

    return result
