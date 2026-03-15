"""위험관리 및 파생거래 테이블 파서."""

import re


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


def parseAmount(text: str) -> int | None:
    """숫자 문자열을 정수로 변환."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    if text in ("-", "−", "–", ""):
        return None

    negative = False
    if text.startswith("△") or text.startswith("(") or text.startswith("−"):
        negative = True
        text = text.lstrip("△(−").rstrip(")")

    text = text.replace(",", "").replace(" ", "")
    text = re.sub(r"[^\d.]", "", text)
    if not text:
        return None
    try:
        val = int(float(text))
        if abs(val) > 9_000_000_000_000_000_000:
            return None
        return -val if negative else val
    except (ValueError, OverflowError):
        return None


def detectUnit(content: str) -> str:
    """단위 감지."""
    m = re.search(r"단위\s*[:\s]*\s*(백만원|억원|천원|원)", content[:500])
    if m:
        return m.group(1)
    return "백만원"


def parseFxSensitivity(content: str) -> list[dict]:
    """환율 민감도 테이블 파싱."""
    lines = content.split("\n")
    results: list[dict] = []

    inSection = False
    headerFound = False

    for line in lines:
        stripped = line.strip()

        if not inSection:
            if re.search(r"환율.*변동|환율.*민감도|외화.*민감도", stripped):
                inSection = True
            continue

        if "|" not in stripped or isSeparatorRow(stripped):
            if headerFound and results:
                break
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        if any("단위" in c for c in cells):
            continue
        if any("※" in c for c in cells):
            break

        if any("상승" in c or "하락" in c for c in cells):
            headerFound = True
            continue

        if not headerFound:
            continue

        currency = cells[0].strip()
        if not currency or currency in ("-", "−", "–") or len(currency) > 10:
            continue

        nums = [parseAmount(c) for c in cells[1:]]
        validNums = [n for n in nums if n is not None]
        if not validNums:
            continue

        entry = {"currency": currency}
        if len(validNums) >= 1:
            entry["upImpact"] = validNums[0]
        if len(validNums) >= 2:
            entry["downImpact"] = validNums[1]
        results.append(entry)

    return results


def _extractValueHeaders(headerCols: list[str]) -> list[str]:
    """헤더 행에서 라벨 키워드를 제외한 값 컬럼 헤더 추출."""
    labelKeywords = {"종류", "구분", "거래상대방", "거래대상", "파생상품"}
    valueHeaders = []
    for c in headerCols:
        s = c.strip()
        if not s or s in labelKeywords:
            continue
        valueHeaders.append(s)
    return valueHeaders


def parseDerivativeContracts(content: str) -> tuple[list[dict], list[str]]:
    """파생상품 계약 현황 파싱.

    Returns:
        (rows, valueHeaders) 튜플.
    """
    lines = content.split("\n")
    results: list[dict] = []

    inSection = False
    headerCols: list[str] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()

        if not inSection:
            if re.search(r"파생상품.*계약|파생상품.*현황|파생상품.*거래", stripped):
                inSection = True
            continue

        if "|" not in stripped or isSeparatorRow(stripped):
            if headerFound and results:
                break
            continue

        cells = splitCells(stripped)
        if len(cells) < 3:
            continue

        if any("단위" in c or "기준일" in c for c in cells):
            continue

        if any("종류" in c or "구분" in c for c in cells) and any("금액" in c or "손익" in c for c in cells):
            headerCols = cells
            headerFound = True
            continue

        if not headerFound:
            continue

        label_parts = []
        values = []
        for c in cells:
            val = parseAmount(c)
            if val is not None:
                values.append(val)
            elif c.strip() and c.strip() not in ("-", "−", "–"):
                label_parts.append(c.strip())

        if not label_parts:
            continue

        results.append(
            {
                "label": " > ".join(label_parts),
                "values": values,
            }
        )

    valueHeaders = _extractValueHeaders(headerCols) if headerCols else []
    return results, valueHeaders
