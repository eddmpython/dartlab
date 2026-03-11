"""이사회 테이블 파서."""

import re

# ──────────────────────────────────────────────
# 유틸리티
# ──────────────────────────────────────────────

def _cellsFromLine(line: str) -> list[str]:
    return [c.strip() for c in line.split("|")[1:-1]]


def _isSeparator(cells: list[str]) -> bool:
    return all(re.match(r"^-+$", c.strip()) or c.strip() == "" for c in cells)


def _parseInt(text: str) -> int | None:
    if not text or text.strip() in ("-", "", "—", "해당없음"):
        return None
    text = text.replace(",", "").replace(" ", "").strip()
    try:
        return int(float(text))
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

    Returns: "directorCount" | "boardMeeting" | "committeeActivity" | "committee" | "education" | "independence" | "other"
    """
    allText = ""
    for line in block[:6]:
        cells = _cellsFromLine(line)
        if not _isSeparator(cells):
            allText += " " + " ".join(c for c in cells if c.strip())

    if re.search(r"이사의\s*수", allText) and re.search(r"사외이사\s*수", allText):
        return "directorCount"

    if re.search(r"개최일자", allText) and re.search(r"의\s*안|의안", allText) and re.search(r"가결", allText):
        if re.search(r"위원회명", allText):
            return "committeeActivity"
        return "boardMeeting"

    if re.search(r"위원회명", allText) and re.search(r"구\s*성|설치목적|권한", allText):
        return "committee"

    if re.search(r"교육일자", allText) and re.search(r"참석", allText):
        return "education"

    if re.search(r"추천인", allText) and re.search(r"선임배경|활동분야|임\s*기", allText):
        return "independence"

    return "other"


# ──────────────────────────────────────────────
# 이사 수 파서
# ──────────────────────────────────────────────

def parseDirectorCount(block: list[str]) -> dict | None:
    """이사 수 / 사외이사 수 파싱.

    Returns: {"totalDirectors": int, "outsideDirectors": int}
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 2:
        return None

    headerIdx = None
    for i, row in enumerate(rows):
        text = " ".join(row)
        if re.search(r"이사의\s*수", text) and re.search(r"사외이사\s*수", text):
            headerIdx = i
            break

    if headerIdx is None:
        return None

    header = rows[headerIdx]
    nCols = len(header)

    colTotal = None
    colOutside = None

    for i, h in enumerate(header):
        h = h.replace(" ", "")
        if re.search(r"이사의수", h):
            colTotal = i
        elif re.search(r"사외이사수", h):
            colOutside = i

    if colTotal is None or colOutside is None:
        return None

    dataRow = None
    for row in rows[headerIdx + 1:]:
        text = " ".join(row)
        if re.search(r"선임|해임|중도퇴임|단위", text) and not any(_parseInt(c) is not None for c in row):
            continue
        for cell in row:
            if _parseInt(cell) is not None:
                dataRow = row
                break
        if dataRow is not None:
            break

    if dataRow is None:
        return None

    while len(dataRow) < nCols:
        dataRow.append("")

    return {
        "totalDirectors": _parseInt(dataRow[colTotal]),
        "outsideDirectors": _parseInt(dataRow[colOutside]),
    }


def parseDirectorCountFromText(content: str) -> dict | None:
    """content에서 이사 수 직접 추출 (fallback)."""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if re.search(r"이사의\s*수", line) and re.search(r"사외이사\s*수", line):
            for j in range(i + 1, min(i + 5, len(lines))):
                cells = _cellsFromLine(lines[j]) if lines[j].strip().startswith("|") else []
                if not cells or _isSeparator(cells):
                    continue
                text = " ".join(cells)
                if re.search(r"선임|해임|중도퇴임|단위", text) and not any(_parseInt(c) is not None for c in cells):
                    continue
                nums = [_parseInt(c) for c in cells]
                validNums = [n for n in nums if n is not None]
                if len(validNums) >= 2:
                    return {
                        "totalDirectors": validNums[0],
                        "outsideDirectors": validNums[1],
                    }
    return None


# ──────────────────────────────────────────────
# 이사회 개최/참석률 파서
# ──────────────────────────────────────────────

def parseBoardMeeting(block: list[str]) -> dict | None:
    """이사회 개최 횟수 + 출석률 파싱.

    Returns: {"meetingCount": int, "attendanceRates": {이름: float}}
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 3:
        return None

    headerIdx = None
    for i, row in enumerate(rows):
        text = " ".join(row)
        if re.search(r"개최일자", text) and re.search(r"가결", text):
            headerIdx = i
            break

    if headerIdx is None:
        return None

    attendanceRates = {}
    for row in rows[:headerIdx + 2]:
        for cell in row:
            matches = re.findall(r"(\S+?)\s*\(출석률\s*:?\s*([\d.]+)\s*%\)", cell)
            for name, rate in matches:
                try:
                    attendanceRates[name] = float(rate)
                except ValueError:
                    pass

    datePattern = re.compile(r"(?:\d{4}|'\d{2})[.\-/]\d{1,2}[.\-/]\d{1,2}")
    meetingDates = set()
    for row in rows[headerIdx + 1:]:
        for cell in row:
            for d in datePattern.findall(cell):
                meetingDates.add(d)

    maxSession = 0
    sessionPattern = re.compile(r"^(\d+)$")
    sessionInText = re.compile(r"\((\d+)차\)")
    for row in rows[headerIdx + 1:]:
        if row:
            m = sessionPattern.match(row[0].strip())
            if m:
                maxSession = max(maxSession, int(m.group(1)))
        for cell in row:
            for sm in sessionInText.finditer(cell):
                maxSession = max(maxSession, int(sm.group(1)))

    meetingCount = max(len(meetingDates), maxSession)

    if meetingCount == 0 and not attendanceRates:
        return None

    return {
        "meetingCount": meetingCount,
        "attendanceRates": attendanceRates,
    }


# ──────────────────────────────────────────────
# 위원회 구성 파서
# ──────────────────────────────────────────────

def parseCommittee(block: list[str]) -> list[dict]:
    """위원회 구성 파싱.

    Returns: [{"name": str, "composition": str, "members": str}]
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 2:
        return []

    headerIdx = None
    for i, row in enumerate(rows):
        text = " ".join(row)
        if re.search(r"위원회명", text) and re.search(r"구\s*성|소속", text):
            headerIdx = i
            break

    if headerIdx is None:
        return []

    header = rows[headerIdx]
    nCols = len(header)

    colName = None
    colComp = None
    colMembers = None

    for i, h in enumerate(header):
        h = h.replace(" ", "")
        if re.search(r"위원회명", h):
            colName = i
        elif re.search(r"구성", h):
            colComp = i
        elif re.search(r"소속|성명", h):
            colMembers = i

    if colName is None:
        colName = 0

    result = []
    for row in rows[headerIdx + 1:]:
        while len(row) < nCols:
            row.append("")

        name = row[colName].strip()
        if not name:
            continue

        comp = row[colComp].strip() if colComp is not None else ""
        members = row[colMembers].strip() if colMembers is not None else ""

        result.append({
            "name": name,
            "composition": comp,
            "members": members,
        })

    return result
