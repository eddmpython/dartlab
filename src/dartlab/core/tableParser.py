import re

from dartlab.core.constants import UNIT_SCALE, DEFAULT_UNIT_SCALE


def extractTables(content: str) -> list[dict]:
    """마크다운 테이블 파싱. DART 중첩 테이블(단위행+본체) 처리."""
    tables = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c != ""]
            headers = cells
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rowLine = lines[i].strip()
                if "---" in rowLine:
                    if rows:
                        newHeader = rows.pop()
                        if rows:
                            tables.append({"headers": headers, "rows": rows})
                        headers = newHeader
                        rows = []
                    i += 1
                    continue
                rowCells = [c.strip() for c in rowLine.split("|")]
                rowCells = [c for c in rowCells if c != ""]
                if rowCells:
                    rows.append(rowCells)
                i += 1
            if headers and rows and len(headers) >= 2:
                tables.append({"headers": headers, "rows": rows})
        else:
            i += 1
    return tables


def parseAmount(text: str) -> float | None:
    """금액/숫자 문자열 → float. 음수 마커(△, ▲, 괄호) 처리."""
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip().replace(",", "").replace(" ", "")
    if re.match(r"^\(주\d*\)$", cleaned):
        return None
    isNeg = "△" in cleaned or "▲" in cleaned or (
        cleaned.startswith("(") and cleaned.endswith(")")
    )
    cleaned = re.sub(r"[△▲\(\)]", "", cleaned)
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned or cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    val = float(cleaned)
    return -val if isNeg else val


def detectUnit(content: str) -> float:
    """content에서 단위를 감지. 백만원=1, 천원=0.001, 원=0.000001 반환."""
    m = re.search(r"단위\s*[：:]\s*(백만원|천원|원)", content)
    if m:
        return UNIT_SCALE.get(m.group(1), DEFAULT_UNIT_SCALE)
    return DEFAULT_UNIT_SCALE


def extractAccounts(content: str) -> tuple[dict[str, list[float | None]], list[str]]:
    """요약재무정보 테이블에서 {계정명: [당기, 전기, ...]} 추출. 단위 정규화 포함."""
    unit = detectUnit(content)
    tables = extractTables(content)

    if not tables:
        rows = []
        headers = None
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            if "---" in stripped:
                continue
            cells = [c.strip() for c in stripped.split("|")]
            cells = [c for c in cells if c != ""]
            if not cells:
                continue
            if any("단위" in c for c in cells):
                continue
            cellText = " ".join(cells)
            if headers is None and ("기" in cellText or "년" in cellText) and len(cells) >= 2:
                headers = cells
                continue
            if headers and len(cells) >= 2:
                rows.append(cells)
        if headers and rows:
            tables = [{"headers": headers, "rows": rows}]

    result = {}
    order = []
    for table in tables:
        headers = table["headers"]
        if len(headers) < 2:
            continue
        headerText = " ".join(headers)
        if "단위" in headerText or all(not h for h in headers[1:]):
            for ri in range(min(3, len(table["rows"]))):
                candidate = table["rows"][ri]
                candText = " ".join(candidate)
                if "기" in candText or "년" in candText:
                    headers = candidate
                    table["rows"] = table["rows"][ri + 1:]
                    break
            else:
                continue
        if not any("기" in h or "년" in h for h in headers[1:]):
            continue
        for row in table["rows"]:
            if len(row) < 2:
                continue
            name = row[0].strip()
            if not name or "※" in name or "월" in name:
                continue
            if re.match(r"^\d{4}년", name):
                continue
            name = re.sub(r"(?<=[\uAC00-\uD7A3])\s+(?=[\uAC00-\uD7A3])", "", name)
            amounts = [parseAmount(cell) for cell in row[1:]]
            if all(a is None for a in amounts):
                continue
            if unit != 1.0:
                amounts = [a * unit if a is not None else None for a in amounts]
            result[name] = amounts
            order.append(name)
    return result, order
