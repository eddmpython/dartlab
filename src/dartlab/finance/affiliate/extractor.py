"""관계기업 주석 테이블 파싱 유틸."""

import re


def parseTableRows(text: str) -> list[list[str]]:
    """마크다운 테이블 행 추출. XBRL 패딩 제거."""
    rows = []
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        # 후행 빈 셀 제거 (XBRL 패딩)
        while cells and not cells[-1]:
            cells.pop()
        if not cells:
            continue
        if all(re.match(r"^-+$", c) for c in cells if c):
            continue
        if not any(c.strip() for c in cells):
            continue
        rows.append(cells)
    return rows
