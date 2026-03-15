"""주주총회 등에 관한 사항 파서."""

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
    text = text.strip().replace(",", "").replace(" ", "")
    text = re.sub(r"[^\d]", "", text)
    if not text:
        return None
    try:
        return int(text)
    except (ValueError, OverflowError):
        return None


def parseMeetingAgenda(content: str) -> list[dict]:
    """주주총회 안건 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            if headerFound and results:
                break
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        # 헤더 감지
        if any("안건" in c or "의안" in c or "부의안건" in c for c in cells) and any(
            "결과" in c or "가결" in c or "찬성" in c or "내용" in c for c in cells
        ):
            headerFound = True
            continue

        if any("구분" in c or "구 분" in c for c in cells) and any("안건" in c or "내용" in c for c in cells):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 데이터 행
        label = ""
        for c in cells:
            if len(c.strip()) >= 3 and parseAmount(c) is None:
                label = c.strip()
                break

        if not label:
            continue

        entry: dict = {"agenda": label}
        # 결과 찾기
        for c in cells:
            if "가결" in c or "승인" in c or "원안" in c:
                entry["result"] = c.strip()
                break
            elif "부결" in c:
                entry["result"] = c.strip()
                break

        results.append(entry)

    return results
