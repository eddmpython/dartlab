"""주식의 총수 테이블 파서."""

from dartlab.core.tableParser import parseAmount

FIELD_MAP = {
    "발행할 주식의 총수": "authorizedShares",
    "현재까지 발행한 주식의 총수": "issuedShares",
    "현재까지 감소한 주식의 총수": "retiredShares",
    "발행주식의 총수": "outstandingShares",
    "자기주식수": "treasuryShares",
    "유통주식수": "floatingShares",
    "자기주식 보유비율": "treasuryRatio",
}


def parseShareCapitalTable(content: str) -> dict | None:
    """주식의 총수 테이블 파싱.

    Ⅰ~Ⅶ 번호 체계에서 발행주식/자기주식/유통주식 추출.

    Returns:
        dict with keys: authorizedShares, issuedShares, retiredShares,
            outstandingShares, treasuryShares, floatingShares, treasuryRatio
        또는 발행주식 총수를 추출할 수 없으면 None
    """
    lines = content.split("\n")
    result = {}

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if len(cells) < 3:
            continue

        txt = " ".join(cells[:2])
        for keyword, field in FIELD_MAP.items():
            if keyword in txt:
                for ci in range(1, len(cells)):
                    v = parseAmount(cells[ci])
                    if v is not None:
                        result[field] = v
                        break
                break

    if not result.get("outstandingShares"):
        return None
    return result
