"""회사의 개요 파서."""

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


def parseCompanyInfo(content: str) -> dict:
    """회사 기본정보 테이블 파싱."""
    lines = content.split("\n")
    info: dict = {}

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        for i, c in enumerate(cells):
            c_clean = c.strip()
            if "설립일" in c_clean and i + 1 < len(cells):
                info["foundedDate"] = cells[i + 1].strip()
            elif "상장일" in c_clean and i + 1 < len(cells):
                info["listedDate"] = cells[i + 1].strip()
            elif "본점소재지" in c_clean and i + 1 < len(cells):
                info["address"] = cells[i + 1].strip()
            elif "대표이사" in c_clean and i + 1 < len(cells):
                info["ceo"] = cells[i + 1].strip()
            elif "주요사업" in c_clean and i + 1 < len(cells):
                info["mainBusiness"] = cells[i + 1].strip()
            elif "홈페이지" in c_clean and i + 1 < len(cells):
                info["website"] = cells[i + 1].strip()

    # 테이블에서 의미있는 값을 못 찾으면 산문형 fallback
    meaningful = {k: v for k, v in info.items() if v and v != "-"}
    if not meaningful:
        info = parseCompanyInfoFallback(content)

    return info


def parseCompanyInfoFallback(content: str) -> dict:
    """산문형 콘텐츠에서 regex 기반 회사정보 추출."""
    info: dict = {}
    text = content.replace("\xa0", " ")

    m = re.search(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일에?\s*[\S\s]{0,30}?설립", text)
    if not m:
        m = re.search(r"설립\s*일\s*자?\s*[:：\n]?\s*(\d{4})[\.\-/년]\s*(\d{1,2})[\.\-/월]\s*(\d{1,2})", text)
    if m:
        info["foundedDate"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    m = re.search(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*[\S\s]{0,30}?(?:공개|상장)", text)
    if not m:
        m = re.search(r"상장\s*일\s*자?\s*[:：\n]?\s*(\d{4})[\.\-/년]\s*(\d{1,2})[\.\-/월]\s*(\d{1,2})", text)
    if m:
        info["listedDate"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    m = re.search(r"주\s*소\s*[:：]\s*(.+?)(?:\n|$)", text)
    if not m:
        m = re.search(r"본점\s*소재지\s*[:：]?\s*(.+?)(?:\n|$)", text)
    if m:
        addr = m.group(1).strip().rstrip("|").strip()
        if len(addr) > 5:
            info["address"] = addr

    m = re.search(r"홈페이지\s*[:：]?\s*(https?://\S+|www\.\S+)", text)
    if m:
        info["website"] = m.group(1).strip()

    return info
