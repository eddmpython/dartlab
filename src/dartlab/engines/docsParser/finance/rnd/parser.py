"""연구개발활동 파서."""

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
        return int(float(text))
    except ValueError:
        return None


def parseFloat(text: str) -> float | None:
    """퍼센트 등 소수 파싱."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip().replace(",", "").replace("%", "").replace(" ", "")
    if text in ("-", "−", "–", ""):
        return None
    try:
        return float(text)
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
    cells = [c.strip() for c in line.split("|")]
    while cells and cells[0] == "":
        cells.pop(0)
    while cells and cells[-1] == "":
        cells.pop()
    return cells


def isSeparatorRow(line: str) -> bool:
    cells = splitCells(line)
    return all(re.match(r"^-+$", c.strip()) for c in cells if c.strip())


def parseRndTable(block: list[str]) -> dict | None:
    """R&D 비용 테이블 파싱.

    구조 (삼성전자 등):
    | 과 목 | 제56기 | 제55기 | 제54기 |
    | 연구개발비용 계 | 35,021,531 | 28,352,769 | 24,929,171 |
    | (정부보조금) | ... | ... | ... |
    | 연구개발비/매출액 비율 | 11.45% | 10.88% | 9.67% |

    Returns:
        {"periods": [...], "rndExpense": [...], "revenueRatio": [...]}
    """
    dataRows = [line for line in block if not isSeparatorRow(line)]
    if len(dataRows) < 3:
        return None

    # R&D 관련 테이블인지 확인
    blockText = " ".join(dataRows)
    if "연구개발" not in blockText and "R&D" not in blockText:
        return None

    # 기간 헤더 찾기
    headerRow = None
    periods: list[str] = []
    for row in dataRows:
        cells = splitCells(row)
        periodCells = [c for c in cells if re.search(r"\d+기|당기|전기|\d{4}년", c)]
        if periodCells:
            headerRow = row
            periods = periodCells
            break

    if not periods:
        return None

    # 데이터 행 파싱
    rndExpense: list[int | None] = []
    revenueRatio: list[float | None] = []

    for row in dataRows:
        if row == headerRow:
            continue
        cells = splitCells(row)
        if len(cells) < 2:
            continue

        rowText = " ".join(cells[:3])

        # 연구개발비용 계
        if ("연구개발비용" in rowText and "계" in rowText) or ("합 계" in rowText and "연구" in blockText) or ("연구개발비 합계" in rowText):
            for cell in cells:
                if re.match(r"^[\d,]+$", cell.strip()):
                    rndExpense.append(parseAmount(cell))

        # 매출액 대비 비율
        if "매출액" in rowText and ("비율" in rowText or "%" in " ".join(cells)):
            for cell in cells:
                val = parseFloat(cell)
                if val is not None and 0 < val < 100:
                    revenueRatio.append(val)

    if not rndExpense:
        return None

    return {
        "periods": periods,
        "rndExpense": rndExpense[:len(periods)],
        "revenueRatio": revenueRatio[:len(periods)] if revenueRatio else [],
    }
