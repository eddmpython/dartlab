"""배당지표 테이블 파서."""

from dartlab.core.tableParser import parseAmount


def parseDividendTable(content: str) -> dict:
    """배당 섹션 텍스트에서 주요 배당지표 파싱.

    Returns:
        dict with keys: netIncome, eps, totalDividend, payoutRatio,
        dividendYieldCommon, dpsCommon, dpsPreferred.
        각 값은 [당기, 전기, 전전기] 3개 float|None 리스트.
    """
    lines = content.split("\n")
    tableRows: list[list[str]] = []
    inMainTable = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if not cells:
            continue
        if all(c.replace("-", "") == "" for c in cells):
            continue

        cellText = " ".join(cells)
        if "배당지표" in cellText or "단위" in cellText:
            inMainTable = True
            continue
        if "배당 이력" in cellText or "배당이력" in cellText:
            break
        if not inMainTable and "구" in cellText and "분" in cellText and "당기" in cellText:
            inMainTable = True
        if inMainTable or any(
            kw in cellText for kw in ["주당액면가액", "당기순이익", "현금배당금", "배당성향", "배당수익률"]
        ):
            inMainTable = True
            tableRows.append(cells)

    result = {
        "netIncome": [],
        "eps": [],
        "totalDividend": [],
        "payoutRatio": [],
        "dividendYieldCommon": [],
        "dpsCommon": [],
        "dpsPreferred": [],
    }

    prevLabel = ""
    for row in tableRows:
        if len(row) < 3:
            continue

        label = row[0].strip()
        if not label:
            label = prevLabel

        stockType = ""
        values = row[1:]
        if len(row) >= 4:
            second = row[1].strip()
            if second in ("보통주", "우선주", "종류주", "1우선주(주1)", "1우선주"):
                stockType = "우선주" if "우선" in second else ("종류주" if "종류" in second else "보통주")
                values = row[2:]
            elif label in ("보통주", "우선주", "종류주", "1우선주(주1)", "1우선주"):
                stockType = "우선주" if "우선" in label else ("종류주" if "종류" in label else "보통주")
                label = prevLabel
                values = row[1:]

        amounts = [parseAmount(v) for v in values[:3]]
        while len(amounts) < 3:
            amounts.append(None)

        if "당기순이익" in label and "연결" in label:
            result["netIncome"] = amounts
        elif "당기순이익" in label and (not result["netIncome"] or all(a is None for a in result["netIncome"])):
            result["netIncome"] = amounts
        elif "주당순이익" in label:
            result["eps"] = amounts
        elif "현금배당금총액" in label:
            result["totalDividend"] = amounts
        elif "현금배당성향" in label:
            result["payoutRatio"] = amounts
        elif "현금배당수익률" in label:
            if stockType == "우선주" or label == "우선주":
                pass
            elif stockType == "종류주" and all(a is None for a in amounts):
                pass
            else:
                result["dividendYieldCommon"] = amounts
        elif "주당" in label and "현금배당금" in label:
            if stockType == "우선주" or label == "우선주":
                result["dpsPreferred"] = amounts
            elif stockType == "종류주" and all(a is None for a in amounts):
                pass
            else:
                result["dpsCommon"] = amounts

        if label and label not in ("보통주", "우선주", "종류주"):
            prevLabel = label

    return result
