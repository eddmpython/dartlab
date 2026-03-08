"""감사제도에 관한 사항 파서."""

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


def parseAuditCommittee(content: str) -> list[dict]:
    """감사위원회 위원 현황 파싱."""
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
        if any("성명" in c or "위원" in c for c in cells) and any(
            "직위" in c or "구분" in c or "경력" in c or "사외" in c or "재직" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 데이터 행
        name = cells[0].strip()
        if not name or len(name) < 2 or name in ("합계", "합 계", "소계"):
            continue

        entry: dict = {"name": name}
        if len(cells) >= 2:
            entry["role"] = cells[1].strip()
        if len(cells) >= 3:
            entry["detail"] = cells[2].strip()

        results.append(entry)

    return results


def parseAuditActivity(content: str) -> list[dict]:
    """감사 활동 내역 파싱."""
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

        if any("개최일자" in c or "일자" in c for c in cells) and any(
            "의안" in c or "안건" in c or "내용" in c or "보고" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        date = cells[0].strip()
        if not date or not re.search(r"\d{4}", date):
            continue

        agenda = cells[1].strip() if len(cells) >= 2 else ""
        entry: dict = {"date": date}
        if agenda:
            entry["agenda"] = agenda
        if len(cells) >= 3:
            entry["result"] = cells[2].strip()

        results.append(entry)

    return results
