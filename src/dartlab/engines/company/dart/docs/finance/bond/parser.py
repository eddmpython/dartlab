"""채무증권 발행실적 테이블 파서."""

from dartlab.core.tableParser import parseAmount


def parseBondTable(content: str) -> list[dict]:
    """채무증권 발행실적 10셀 테이블 파싱.

    Returns:
        list[dict] - 각 dict는 BondIssuance 필드와 동일:
            issuer, bondType, method, issueDate, amount,
            interestRate, rating, maturityDate, redeemed, underwriter
    """
    lines = content.split("\n")
    results = []
    inTable = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if len(cells) < 8:
            continue

        txt = " ".join(cells)
        if all(c.replace("-", "") == "" for c in cells):
            continue

        if "발행회사" in txt and "증권종류" in txt:
            inTable = True
            continue

        if not inTable:
            continue

        name = cells[0]
        if name in ("합 계", "합계", "계"):
            break

        if len(cells) < 10:
            continue

        if not name:
            continue

        record = {
            "issuer": name,
            "bondType": cells[1],
            "method": cells[2],
            "issueDate": cells[3],
            "amount": parseAmount(cells[4]),
            "interestRate": cells[5],
            "rating": cells[6],
            "maturityDate": cells[7],
            "redeemed": cells[8],
            "underwriter": cells[9] if len(cells) > 9 else None,
        }
        results.append(record)

    return results
