"""회사의 연혁 파서."""

import re


def splitCells(line: str) -> list[str]:
    """파이프 구분자로 셀 분리."""
    cells = [c.strip() for c in line.split("|")]
    while cells and cells[0] == "":
        cells.pop(0)
    while cells and cells[-1] == "":
        cells.pop()
    return cells


def isSeparatorRow(line: str) -> bool:
    """구분선 행 여부 확인."""
    cells = splitCells(line)
    return all(re.match(r"^-+$", c.strip()) for c in cells if c.strip())


def parseHistory(content: str) -> list[dict]:
    """연혁 테이블 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        # 헤더 감지
        if any("일자" in c or "연월" in c or "날짜" in c or "년월" in c for c in cells) and any(
            "내용" in c or "연혁" in c or "사항" in c or "내역" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            # 날짜 패턴이 있으면 헤더 없이도 파싱
            if re.search(r"\d{4}[년.]\s*\d{1,2}", cells[0]):
                headerFound = True
            else:
                continue

        date = cells[0].strip()
        if not date or not re.search(r"\d{4}", date):
            continue

        event = cells[1].strip() if len(cells) >= 2 else ""
        if not event or len(event) < 2:
            continue

        results.append({"date": date, "event": event})

    return results
