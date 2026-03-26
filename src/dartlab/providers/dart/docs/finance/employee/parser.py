"""직원 현황 테이블 파서."""

import re

from dartlab.core.tableParser import parseAmount


def parseTenure(text: str) -> float | None:
    """평균근속연수 문자열 -> float (년 단위).

    지원 포맷: "13.0", "3년9개월", "12년 10개월", "6개월", "20"
    """
    if not text or text.strip() in ("", "-"):
        return None
    s = text.strip()
    m = re.match(r"(\d+)\s*년\s*(\d+)\s*개월", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 12
    m = re.match(r"(\d+)\s*년", s)
    if m:
        return float(m.group(1))
    m = re.match(r"(\d+)\s*개월", s)
    if m:
        return int(m.group(1)) / 12
    val = parseAmount(s)
    if val is not None and 0 < val < 100:
        return val
    return None


def _tryExtract(cells: list[str], empIdx: int, tenureIdx: int, salaryIdx: int, avgIdx: int) -> dict | None:
    """지정 인덱스로 합계 행에서 직원 데이터 추출."""
    if empIdx >= len(cells):
        return None
    emp = parseAmount(cells[empIdx])
    if emp is None or emp < 1:
        return None
    result: dict = {"totalEmployees": emp}
    if tenureIdx < len(cells):
        tenure = parseTenure(cells[tenureIdx])
        if tenure is not None:
            result["avgTenure"] = round(tenure, 1)
    if salaryIdx < len(cells):
        salary = parseAmount(cells[salaryIdx])
        if salary is not None and salary >= emp:
            result["totalSalary"] = salary
    if avgIdx < len(cells):
        avg = parseAmount(cells[avgIdx])
        if avg is not None:
            result["avgSalary"] = avg
    return result


def parseEmployeeTable(content: str) -> dict:
    """직원 현황 섹션에서 합계 행 파싱.

    Returns:
        dict with keys: totalEmployees, avgTenure, totalSalary, avgSalary.
        파싱 실패 시 빈 dict.
    """
    lines = content.split("\n")

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if cells[0] not in ("합 계", "합계"):
            continue
        if len(cells) < 4:
            continue

        # 표준 구조: cells[6]=emp, [7]=tenure, [8]=salary, [9]=avg
        if len(cells) >= 10:
            r = _tryExtract(cells, 6, 7, 8, 9)
            if r and r.get("totalSalary"):
                return r

        # shifted 구조: cells[5]=emp, [6]=tenure, [7]=salary, [8]=avg
        if len(cells) >= 9:
            r = _tryExtract(cells, 5, 6, 7, 8)
            if r and r.get("totalSalary"):
                return r

        # 변형 구조: cells[2]=emp, [7]=tenure, [8]=salary, [9]=avg
        if len(cells) >= 10:
            r = _tryExtract(cells, 2, 7, 8, 9)
            if r and r.get("totalSalary"):
                return r

        # salary 없어도 emp만 추출 (한화비전, 스팩)
        if len(cells) >= 10:
            r = _tryExtract(cells, 6, 7, 8, 9)
            if r:
                return r

        # cells[2]에 emp (스팩 일부)
        if len(cells) >= 3:
            maxIdx = len(cells)
            r = _tryExtract(
                cells,
                2,
                7 if maxIdx > 7 else maxIdx,
                8 if maxIdx > 8 else maxIdx,
                9 if maxIdx > 9 else maxIdx,
            )
            if r:
                return r

    return {}
