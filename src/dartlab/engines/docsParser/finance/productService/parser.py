"""주요 제품 및 서비스 테이블 파서."""

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


def parseRatio(text: str) -> float | None:
    """비중(%) 문자열을 float로 변환."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip().replace("%", "").replace(",", "").replace(" ", "")
    if text in ("-", "−", "–", ""):
        return None

    negative = False
    if text.startswith("△") or text.startswith("(") or text.startswith("−"):
        negative = True
        text = text.lstrip("△(−").rstrip(")")

    try:
        val = float(text)
        return -val if negative else val
    except ValueError:
        return None


def detectUnit(content: str) -> str:
    """단위 감지."""
    m = re.search(r"단위\s*[:\s]*\s*(백만원|억원|천원|원)", content[:500])
    if m:
        return m.group(1)
    return "백만원"


def parseProductService(content: str) -> list[dict]:
    """주요 제품/서비스 테이블 파싱."""
    lines = content.split("\n")
    results: list[dict] = []

    headerFound = False
    inTable = False
    nonTableGap = 0

    for line in lines:
        stripped = line.strip()

        if "|" not in stripped or isSeparatorRow(stripped):
            if inTable:
                nonTableGap += 1
                if nonTableGap > 2:
                    break
            continue

        nonTableGap = 0
        cells = splitCells(stripped)
        if len(cells) < 3:
            continue

        if any("단위" in c for c in cells):
            continue

        if any("※" in c or "참고" in c or "참조" in c for c in cells):
            if inTable and results:
                break
            continue

        if any("가격" in c and "변동" in c for c in cells):
            break

        if not headerFound:
            hasProduct = any(
                k in c for c in cells
                for k in (
                    "제품", "서비스", "품목", "품 목", "구분", "부문", "부 문",
                    "사업부문", "상품명", "사업영역",
                )
            )
            hasMoney = any(
                k in c for c in cells
                for k in ("매출", "금액", "비중", "비율")
            )
            if hasProduct and hasMoney:
                headerFound = True
                continue
            if hasProduct or hasMoney:
                headerFound = True
                continue

        if not headerFound:
            continue

        if all(c.strip() in ("매출액", "비중", "비율", "금액", "") for c in cells):
            continue

        inTable = True

        label_parts = []
        amount = None
        ratio = None

        for c in cells:
            c_stripped = c.strip()
            if not c_stripped:
                continue

            if "%" in c_stripped:
                if ratio is None:
                    ratio = parseRatio(c_stripped)
                continue

            parsed = parseAmount(c_stripped)
            if parsed is not None and abs(parsed) > 10:
                if amount is None:
                    amount = parsed
                continue

            try:
                fval = float(c_stripped.replace(",", ""))
                if 0 < abs(fval) <= 100 and "." in c_stripped:
                    if ratio is None:
                        ratio = fval
                    continue
            except ValueError:
                pass

            label_parts.append(c_stripped)

        if not label_parts:
            continue

        label = " > ".join(label_parts)

        entry = {"label": label}
        if amount is not None:
            entry["amount"] = amount
        if ratio is not None:
            entry["ratio"] = ratio
        results.append(entry)

    return results
