"""타법인출자 현황 파서."""

import re


def splitCells(line: str) -> list[str]:
    """파이프(|)로 구분된 셀을 분리."""
    cells = [c.strip() for c in line.split("|")]
    while cells and cells[0] == "":
        cells.pop(0)
    while cells and cells[-1] == "":
        cells.pop()
    return cells


def isSeparatorRow(line: str) -> bool:
    """구분선 행인지 확인."""
    cells = splitCells(line)
    return all(re.match(r"^-+$", c.strip()) for c in cells if c.strip())


def parseAmount(text: str) -> int | None:
    """금액 문자열을 정수로 변환."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    if text in ("-", "\u2212", "\u2013", ""):
        return None
    negative = False
    if text.startswith("\u25b3") or text.startswith("(") or text.startswith("\u2212"):
        negative = True
        text = text.lstrip("\u25b3(\u2212").rstrip(")")
    text = text.replace(",", "").replace(" ", "")
    text = re.sub(r"[^\d.]", "", text)
    if not text:
        return None
    try:
        val = int(float(text))
        return -val if negative else val
    except (ValueError, OverflowError):
        return None


def parseInvestments(content: str) -> tuple[list[dict], list[str]]:
    """타법인출자 현황 파싱.

    Returns:
        (rows, headers) — rows: [{"name": str, "values": [int]}], headers: 숫자 컬럼 헤더
    """
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False
    numericHeaders: list[str] = []

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            continue

        cells = splitCells(stripped)
        if len(cells) < 3:
            continue

        # 단위 행 스킵
        if any("단위" in c for c in cells) and len(cells) <= 2:
            continue

        # 헤더 감지
        if any("법인명" in c or "회사명" in c or "종목명" in c for c in cells) and any(
            "지분" in c or "장부" in c or "취득" in c or "기초" in c or "기말" in c for c in cells
        ):
            headerFound = True
            # 헤더에서 숫자 컬럼명 추출 (법인명 이후의 셀들)
            nameIdx = 0
            for i, c in enumerate(cells):
                if "법인명" in c or "회사명" in c or "종목명" in c:
                    nameIdx = i
                    break
            numericHeaders = [c.strip().replace(" ", "") for c in cells[nameIdx + 1 :] if c.strip()]
            continue

        if not headerFound:
            continue

        # 합계 행 스킵
        if any(c.strip() in ("합계", "합 계", "소계", "소 계", "총계") for c in cells):
            continue

        # 데이터 행: 법인명 + 숫자
        name = ""
        nums = []
        for c in cells:
            val = parseAmount(c)
            if val is not None:
                nums.append(val)
            elif c.strip() and len(c.strip()) >= 2 and c.strip() not in ("-", "\u2212", "\u2013"):
                if not name:
                    name = c.strip()

        if not name or not nums:
            continue

        results.append({"name": name, "values": nums})

    return results, numericHeaders
