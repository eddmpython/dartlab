"""우발부채·채무보증·소송 파서."""

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

    if "소제기일" in text or "소송 당사자" in text or "소송당사자" in text:
        return "lawsuit"
    if "사건명" in text and ("원고" in text or "피고" in text or "소송" in text):
        return "lawsuit"
    if "소송" in text and ("원고" in text or "피고" in text):
        return "lawsuit"
    if ("채무보증" in text or "보증금액" in text or "지급보증" in text) and "기초" in text and "기말" in text:
        return "guaranteeDetail"
    if "보증금액" in text or "채무보증" in text or "지급보증" in text or "보증내역" in text:
        return "guaranteeSummary"
    if "담보" in text and ("자산" in text or "금액" in text or "제공" in text):
        return "collateral"
    if "약정" in text and ("한도" in text or "실행" in text):
        return "commitment"
    if ("당기말" in text or "당 기 말" in text) and ("전기말" in text or "전 기 말" in text):
        if "보증" in text or "채무" in text:
            return "guaranteeSummary"

    return "other"


def parseGuaranteeSummary(block: list[str]) -> dict | None:
    """채무보증 요약 테이블에서 총 보증금액 추출."""
    dataRows = [line for line in block if not isSeparatorRow(line)]

    totalAmount = 0
    count = 0

    for row in dataRows:
        cells = splitCells(row)
        if any("단위" in c for c in cells):
            continue

        for cell in cells:
            c = cell.strip()
            if re.match(r"^[\d,]+$", c):
                val = parseAmount(c)
                if val and val > 0:
                    totalAmount += val
                    count += 1

    if count == 0:
        return None

    return {"totalGuaranteeAmount": totalAmount, "lineCount": count}


def parseGuaranteeDetail(block: list[str]) -> dict | None:
    """채무보증 상세 테이블에서 기말 보증금액 합계 추출."""
    dataRows = [line for line in block if not isSeparatorRow(line)]

    endColIdx = None
    for row in dataRows:
        cells = splitCells(row)
        for i, cell in enumerate(cells):
            if "기말" in cell:
                endColIdx = i
                break
        if endColIdx is not None:
            break

    if endColIdx is None:
        return None

    total = 0
    count = 0
    foundHeader = False

    for row in dataRows:
        cells = splitCells(row)
        if "기말" in " ".join(cells):
            foundHeader = True
            continue
        if not foundHeader:
            continue
        if len(cells) <= endColIdx:
            continue

        val = parseAmount(cells[endColIdx])
        if val and val > 0:
            total += val
            count += 1

    if count == 0:
        return None

    return {"totalGuaranteeAmount": total, "lineCount": count}


def parseLawsuit(block: list[str]) -> dict | None:
    """소송 정보 추출 (key-value 형태)."""
    result: dict = {}

    for line in block:
        if isSeparatorRow(line):
            continue
        cells = splitCells(line)
        if len(cells) < 2:
            continue

        key = cells[0].strip()
        value = cells[1].strip()

        if "소제기일" in key:
            result["filingDate"] = value
        elif "당사자" in key:
            result["parties"] = value
        elif "내용" in key and "소송" in key:
            result["description"] = value
        elif "사건명" in key:
            result["description"] = value
        elif "가액" in key or "금액" in key:
            result["amount"] = value
            m = re.search(r"([\d,]+)", value)
            if m:
                result["amountValue"] = parseAmount(m.group(1))
        elif "진행" in key:
            result["status"] = value

    if not result:
        return None

    return result
