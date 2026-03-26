"""정관에 관한 사항 파서."""

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


def parseArticlesChanges(content: str) -> list[dict]:
    """정관 변경 이력 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            if headerFound and results:
                # 사업목적 테이블 시작시 중단
                pass
            continue

        cells = splitCells(stripped)
        if len(cells) < 3:
            continue

        # 헤더 감지
        if any("변경일" in c or "정관변경" in c for c in cells) and any(
            "주총" in c or "변경사항" in c or "변경이유" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 사업목적 테이블 시작시 중단
        if any("사업목적" in c for c in cells) and any("영위" in c for c in cells):
            break

        # 데이터 행
        date = cells[0].strip()
        if not date or len(date) < 4:
            continue

        # 날짜가 아닌 행 스킵 (숫자 시작이 아님)
        if not re.search(r"\d{4}", date):
            continue

        entry: dict = {"date": date}
        if len(cells) >= 2:
            entry["meetingName"] = cells[1].strip()
        if len(cells) >= 3:
            entry["changes"] = cells[2].strip()
        if len(cells) >= 4:
            entry["reason"] = cells[3].strip()

        results.append(entry)

    return results


def parseBusinessPurpose(content: str) -> list[dict]:
    """사업목적 현황 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            if headerFound and results:
                # 다른 섹션 시작시 중단 가능
                pass
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        # 헤더 감지
        if any("사업목적" in c for c in cells) and any("영위" in c or "구 분" in c or "구분" in c for c in cells):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 정관 변경 이력 테이블 만나면 중단 (순서가 바뀐 경우)
        if any("변경일" in c or "정관변경" in c for c in cells):
            break

        # 데이터 행
        purpose = ""
        status = ""

        # 첫 번째 셀이 숫자면 구분 번호
        if len(cells) >= 3:
            purpose = cells[1].strip()
            status = cells[2].strip()
        elif len(cells) == 2:
            purpose = cells[0].strip()
            status = cells[1].strip()

        if not purpose or len(purpose) < 2:
            continue

        # "※" 주석행 스킵
        if purpose.startswith("※") or purpose.startswith("*"):
            continue

        entry: dict = {"purpose": purpose}
        if status:
            entry["active"] = "영위" in status
        results.append(entry)

    return results
