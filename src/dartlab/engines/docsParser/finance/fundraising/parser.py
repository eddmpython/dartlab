"""증권 발행(증자/감자) 테이블 파서."""

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
    text = text.strip().replace(",", "").replace(" ", "")
    if text in ("-", "−", "–", ""):
        return None
    text = re.sub(r"[^\d.]", "", text)
    if not text:
        return None
    try:
        val = int(float(text))
        if abs(val) > 9_000_000_000_000_000_000:
            return None
        return val
    except (ValueError, OverflowError):
        return None


def parseEquityIssuance(content: str) -> list[dict]:
    """증자(감자) 현황 테이블 파싱.

    | 주식발행(감소)일자 | 발행(감소)형태 | 종류 | 수량 | 주당액면가액 | 주당발행(감소)가액 | 비고 |
    | 2020.01.03 | 전환권행사 | 보통주 | 92,603 | 500 | 118,786 | 발행회차: 제 10회 |
    | 2010년 06월 15일 | 신주인수권행사 | 보통주 | 874,916 | 500 | 598 | - |
    """
    lines = content.split("\n")
    results: list[dict] = []

    # 증자(감자) 테이블 영역 찾기
    inSection = False
    headerFound = False

    for line in lines:
        stripped = line.strip()

        # 섹션 시작 감지
        if "증자" in stripped and ("감자" in stripped or "현황" in stripped):
            inSection = True
            continue

        # 채무증권 섹션이 시작되면 종료
        if "채무증권" in stripped:
            break

        if not inSection:
            continue

        if "|" not in stripped or isSeparatorRow(stripped):
            continue

        cells = splitCells(stripped)

        # 헤더 행 건너뛰기
        if any("발행" in c and ("일자" in c or "형태" in c) for c in cells):
            headerFound = True
            continue
        if any(c in ("종류", "수량", "주당액면가액") for c in cells):
            continue

        if not headerFound:
            continue

        # 기준일/단위 행 건너뛰기
        if any("기준일" in c or "단위" in c for c in cells):
            continue

        # 데이터 행: 최소 4열 이상, 첫 셀이 날짜 패턴
        if len(cells) < 4:
            continue

        dateStr = cells[0].strip()
        # 날짜 패턴: YYYY.MM.DD or YYYY-MM-DD or YYYY/MM/DD or YYYY년 MM월 DD일
        dateMatch = re.match(r"^(\d{4})[\.\-/](\d{2})[\.\-/](\d{2})$", dateStr)
        if not dateMatch:
            dateMatch = re.match(r"^(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일$", dateStr)
        if not dateMatch:
            continue

        # 날짜 정규화: YYYY.MM.DD
        normalizedDate = f"{dateMatch.group(1)}.{int(dateMatch.group(2)):02d}.{int(dateMatch.group(3)):02d}"

        # 파싱
        entry = {"date": normalizedDate}

        if len(cells) > 1:
            entry["issueType"] = cells[1].strip()
        if len(cells) > 2:
            entry["stockType"] = cells[2].strip()
        if len(cells) > 3:
            entry["quantity"] = parseAmount(cells[3])
        if len(cells) > 4:
            entry["parValue"] = parseAmount(cells[4])
        if len(cells) > 5:
            entry["issuePrice"] = parseAmount(cells[5])
        if len(cells) > 6:
            entry["note"] = cells[6].strip()

        results.append(entry)

    return results
