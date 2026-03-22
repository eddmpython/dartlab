"""제재 현황 파서."""

import re


def parseAmount(text: str) -> int | None:
    """숫자 문자열을 정수로 변환."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip().replace(",", "").replace(" ", "")
    if text in ("-", "−", "–", ""):
        return None
    text = re.sub(r"[^\d.]", "", text)
    if not text:
        return None
    try:
        val = int(float(text))
        if abs(val) > 9_000_000_000_000_000_000:
            return None
        return val
    except (ValueError, OverflowError):
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
    cells = [c.strip() for c in line.split("|")]
    while cells and cells[0] == "":
        cells.pop(0)
    while cells and cells[-1] == "":
        cells.pop()
    return cells


def isSeparatorRow(line: str) -> bool:
    cells = splitCells(line)
    return all(re.match(r"^-+$", c.strip()) for c in cells if c.strip())


def parseSanctionTable(block: list[str]) -> list[dict]:
    """제재 테이블 파싱.

    구조:
    | 일자 | 제재기관 | 대상자 | 처벌/조치 내용 | 금전적 제재금액 | 사유 및 근거 법령 |

    Returns:
        [{date, agency, subject, action, amount, reason}, ...]
    """
    dataRows = [line for line in block if not isSeparatorRow(line)]
    if len(dataRows) < 3:
        return []

    # 헤더 컬럼 인덱스 찾기
    dateIdx = agencyIdx = subjectIdx = actionIdx = amountIdx = reasonIdx = None
    headerRow = None

    for row in dataRows:
        cells = splitCells(row)
        for i, cell in enumerate(cells):
            c = cell.strip()
            if "일자" in c and dateIdx is None:
                dateIdx = i
            if ("제재기관" in c or "처분기관" in c) and agencyIdx is None:
                agencyIdx = i
            if "대상" in c and subjectIdx is None:
                subjectIdx = i
            if ("처벌" in c or "조치" in c) and "내용" in c and actionIdx is None:
                actionIdx = i
            if ("금액" in c or "금전" in c) and amountIdx is None:
                amountIdx = i
            if ("사유" in c or "근거" in c) and reasonIdx is None:
                reasonIdx = i

        if dateIdx is not None:
            headerRow = row
            break

    if dateIdx is None:
        return []

    results = []
    foundHeader = False
    for row in dataRows:
        if row == headerRow:
            foundHeader = True
            continue
        if not foundHeader:
            continue

        cells = splitCells(row)
        if len(cells) < 3:
            continue
        # 단위 행 건너뛰기
        if any("단위" in c for c in cells):
            continue

        entry: dict = {}
        if dateIdx is not None and dateIdx < len(cells):
            entry["date"] = cells[dateIdx].strip()
        if agencyIdx is not None and agencyIdx < len(cells):
            entry["agency"] = cells[agencyIdx].strip()
        if subjectIdx is not None and subjectIdx < len(cells):
            entry["subject"] = cells[subjectIdx].strip()
        if actionIdx is not None and actionIdx < len(cells):
            entry["action"] = cells[actionIdx].strip()
        if amountIdx is not None and amountIdx < len(cells):
            entry["amount"] = cells[amountIdx].strip()
            entry["amountValue"] = parseAmount(cells[amountIdx])
        if reasonIdx is not None and reasonIdx < len(cells):
            entry["reason"] = cells[reasonIdx].strip()

        if entry.get("date") or entry.get("agency") or entry.get("action"):
            results.append(entry)

    return results
