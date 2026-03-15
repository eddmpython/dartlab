"""타법인출자 현황 테이블 파서."""

from dartlab.core.tableParser import parseAmount


def parseSubsidiaryTable(content: str) -> list[dict]:
    """타법인출자 현황 16셀 테이블 파싱.

    Returns:
        list[dict] - 각 dict는 SubsidiaryInvestment 필드와 동일:
            name, listed, firstAcquired, purpose, firstAmount,
            beginShares, beginRatio, beginBook,
            acquiredShares, acquiredAmount, valuationGain,
            endShares, endRatio, endBook,
            totalAssets, netIncome
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

        if len(cells) < 10:
            continue

        txt = " ".join(cells)
        if all(c.replace("-", "") == "" for c in cells):
            continue

        if "법인명" in txt or "법 인 명" in txt:
            inTable = True
            continue

        if not inTable:
            continue

        if "수량" in cells[0] and ("지분율" in txt or "금액" in txt):
            continue

        name = cells[0]
        if name in ("합 계", "합계", "계"):
            break

        if len(cells) < 16:
            continue

        if not name or name in ("수량", "지분율", "장부가액"):
            continue

        record = {
            "name": name,
            "listed": cells[1],
            "firstAcquired": cells[2],
            "purpose": cells[3],
            "firstAmount": parseAmount(cells[4]),
            "beginShares": parseAmount(cells[5]),
            "beginRatio": parseAmount(cells[6]),
            "beginBook": parseAmount(cells[7]),
            "acquiredShares": parseAmount(cells[8]),
            "acquiredAmount": parseAmount(cells[9]),
            "valuationGain": parseAmount(cells[10]),
            "endShares": parseAmount(cells[11]),
            "endRatio": parseAmount(cells[12]),
            "endBook": parseAmount(cells[13]),
            "totalAssets": parseAmount(cells[14]),
            "netIncome": parseAmount(cells[15]),
        }
        results.append(record)

    return results
