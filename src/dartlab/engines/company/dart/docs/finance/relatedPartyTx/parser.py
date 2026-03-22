"""대주주 거래 파서."""

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
        # Polars Int64 범위 초과 방지
        if abs(val) > 9_000_000_000_000_000_000:
            return None
        return -val if neg else val
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


def classifyBlock(block: list[str]) -> str:
    """블록 타입 분류."""
    text = " ".join(block[:8])

    if "채무보증" in text or "지급보증" in text or "보증금액" in text:
        return "guarantee"
    if "자산" in text and ("양수" in text or "양도" in text or "매각" in text or "매입" in text):
        return "assetTx"
    if "매출" in text and ("매입" in text or "매출입" in text):
        return "revenueTx"
    if "대여금" in text or "차입금" in text:
        return "loan"
    if "출자" in text or "출자지분" in text:
        return "investment"

    return "other"


def parseGuaranteeBlock(block: list[str]) -> list[dict]:
    """채무보증 블록에서 보증 건별 데이터 추출."""
    dataRows = [line for line in block if not isSeparatorRow(line)]
    results = []

    for row in dataRows:
        cells = splitCells(row)
        if len(cells) < 4:
            continue
        if any("단위" in c for c in cells):
            continue
        # 헤더 행 건너뛰기
        if any(c in ("법인명", "성명", "채무자", "보증내역") for c in cells[:2]):
            continue

        # 첫 번째 셀이 엔티티명
        entity = cells[0].strip()
        if not entity or entity in ("-", ""):
            continue

        # 숫자 셀 추출
        amounts = []
        for cell in cells[1:]:
            val = parseAmount(cell)
            if val is not None:
                amounts.append(val)

        if amounts:
            results.append(
                {
                    "entity": entity,
                    "amount": max(amounts),
                }
            )

    return results


def parseRevenueTxBlock(block: list[str]) -> list[dict]:
    """매출입 블록에서 거래 데이터 추출."""
    dataRows = [line for line in block if not isSeparatorRow(line)]
    results = []

    for row in dataRows:
        cells = splitCells(row)
        if len(cells) < 3:
            continue
        if any("단위" in c for c in cells):
            continue
        if any(c in ("회사명", "법인명", "거래상대방", "구분") for c in cells[:2]):
            continue

        entity = cells[0].strip()
        if not entity or entity in ("-", ""):
            continue

        amounts = []
        for cell in cells[1:]:
            val = parseAmount(cell)
            if val is not None:
                amounts.append(val)

        if amounts:
            results.append(
                {
                    "entity": entity,
                    "sales": amounts[0] if len(amounts) >= 1 else None,
                    "purchases": amounts[1] if len(amounts) >= 2 else None,
                }
            )

    return results
