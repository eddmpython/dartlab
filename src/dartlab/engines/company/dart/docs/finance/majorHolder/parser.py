"""최대주주 테이블 파서."""

import re

from dartlab.core.tableParser import parseAmount


def parseMajorHolderTable(content: str) -> dict:
    """최대주주 및 특수관계인 테이블 파싱.

    Returns:
        dict with keys:
            holders: list[dict] - {name, relation, stockType, sharesStart, ratioStart, sharesEnd, ratioEnd}
            majorHolder: str | None
            majorRatio: float | None
            totalRatio: float | None
    """
    lines = content.split("\n")
    result = {
        "holders": [],
        "majorHolder": None,
        "majorRatio": None,
        "totalRatio": None,
    }

    inTable = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if inTable and result["holders"]:
                break
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if len(cells) < 3:
            continue

        txt = " ".join(cells)

        if all(c.replace("-", "") == "" for c in cells):
            continue

        if ("성 명" in txt or "성명" in txt) and ("관 계" in txt or "관계" in txt) and ("주식" in txt or "지분" in txt):
            inTable = True
            continue

        if not inTable:
            continue

        if "기 초" in txt or ("주식수" in txt and "지분율" in txt):
            continue

        if "출자자수" in txt or "명 칭" in txt or "직위" in txt or "직책" in txt:
            break

        name = cells[0]
        if name in ("합 계", "합계", "계"):
            for ci in range(len(cells) - 1, 0, -1):
                v = parseAmount(cells[ci])
                if v is not None and 0 < v < 100:
                    result["totalRatio"] = v
                    break
            break

        if len(cells) < 7:
            continue

        if not name or name in ("기 초", "기초", "주식수", "지분율"):
            continue

        relation = cells[1]
        stockType = cells[2]
        sharesStart = parseAmount(cells[3])
        ratioStart = parseAmount(cells[4])
        sharesEnd = parseAmount(cells[5])
        ratioEnd = parseAmount(cells[6])

        holder = {
            "name": name,
            "relation": relation,
            "stockType": stockType,
            "sharesStart": sharesStart,
            "ratioStart": ratioStart,
            "sharesEnd": sharesEnd,
            "ratioEnd": ratioEnd,
        }
        result["holders"].append(holder)

        isMajor = "본인" in relation or ("최대주주" in relation and "특수" not in relation)
        isCommon = "보통주" in stockType or "의결권" in stockType
        if isMajor and isCommon and result["majorHolder"] is None:
            result["majorHolder"] = name
            if ratioEnd is not None and 0 < ratioEnd < 100:
                result["majorRatio"] = ratioEnd
            elif ratioStart is not None and 0 < ratioStart < 100:
                result["majorRatio"] = ratioStart

    if result["majorHolder"] is None and result["holders"]:
        first = result["holders"][0]
        if first["ratioEnd"] and 0 < first["ratioEnd"] < 100:
            result["majorHolder"] = first["name"]
            result["majorRatio"] = first["ratioEnd"]

    return result


def parseBigHolders(content: str) -> list[dict] | None:
    """5% 이상 주주 현황 파싱.

    Returns:
        [{"name": str, "shares": float|None, "ratio": float|None}] 또는 None
    """
    lines = content.split("\n")
    inSection = False
    holders = []

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "5% 이상 주주" in s or "5%이상 주주" in s or "5%이상주주" in s:
                inSection = True
                if not s.startswith("|"):
                    continue
            else:
                continue

        if "소액주주" in s:
            break

        if not s.startswith("|"):
            if s.startswith("※") or re.match(r"^주\d*\)", s):
                continue
            if holders and s:
                break
            continue

        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue

        cellJoined = " ".join(cells)

        if "기준일" in cellJoined or "단위" in cellJoined:
            continue
        if ("구분" in cells[0] or "구 분" in cells[0]) and ("주주명" in cellJoined or "소유" in cellJoined):
            continue
        if "지분율" in cellJoined and "소유주식수" in cellJoined:
            continue
        if "※" in cells[0] or re.match(r"^주\d*\)", cells[0]):
            break

        if "우리사주" in cellJoined:
            shares = ratio = None
            for c in cells:
                v = parseAmount(c)
                if v is not None:
                    if v > 100:
                        shares = v
                    elif 0 < v <= 100:
                        ratio = v
            if shares or ratio:
                holders.append({"name": "우리사주조합", "shares": shares, "ratio": ratio})
            continue

        hasFiveLabel = "5% 이상" in cells[0] or "5%이상" in cells[0]

        if hasFiveLabel:
            if len(cells) >= 4:
                name = cells[1]
                shares = parseAmount(cells[2])
                ratio = parseAmount(cells[3])
                if name and (shares or ratio):
                    holders.append({"name": name, "shares": shares, "ratio": ratio})
        else:
            if len(cells) >= 3:
                name = cells[0]
                shares = parseAmount(cells[1])
                ratio = parseAmount(cells[2])
                if name and (shares or ratio):
                    holders.append({"name": name, "shares": shares, "ratio": ratio})

    return holders if holders else None


def parseMinority(content: str) -> dict | None:
    """소액주주 현황 파싱.

    Returns:
        {"holders", "totalHolders", "holderPct",
         "shares", "totalShares", "sharePct"} 또는 None
    """
    lines = content.split("\n")
    inSection = False

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "소액주주" in s:
                inSection = True
            continue

        if not s.startswith("|"):
            continue
        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        cellJoined = " ".join(cells)

        if "소액주주수" in cellJoined or "구 분" in cellJoined:
            continue

        if "소액주주" not in cellJoined:
            continue

        numbers = []
        for c in cells:
            v = parseAmount(c)
            if v is not None:
                numbers.append(v)

        if len(numbers) >= 6:
            return {
                "holders": int(numbers[0]),
                "totalHolders": int(numbers[1]),
                "holderPct": numbers[2],
                "shares": int(numbers[3]),
                "totalShares": int(numbers[4]),
                "sharePct": numbers[5],
            }

    return None


def parseVoting(content: str) -> dict | None:
    """의결권 현황 파싱.

    Returns:
        {"issuedCommon", "noVoteCommon", "votableCommon",
         "issuedPref", ...} 또는 None
    """
    lines = content.split("\n")
    inSection = False
    inTable = False
    result = {}

    ITEM_MAP = [
        ("발행주식총수", "issued"),
        ("의결권없는", "noVote"),
        ("의결권 없는", "noVote"),
        ("정관에 의하여", "excluded"),
        ("기타 법률에 의하여", "restricted"),
        ("의결권이 부활된", "restored"),
        ("의결권을 행사할 수 있는", "votable"),
    ]

    lastKey = None

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "의결권 현황" in s or "의결권현황" in s:
                inSection = True
            continue

        if not s.startswith("|"):
            if inTable and result:
                if s and not s.startswith("※") and not s.startswith("(주"):
                    break
            continue

        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue

        if "구 분" in cells[0] or "구분" in cells[0]:
            inTable = True
            continue

        if not inTable:
            continue

        if "※" in cells[0]:
            break

        matched = False
        for keyword, key in ITEM_MAP:
            if keyword in cells[0]:
                lastKey = key
                matched = True

                stockType = "보통주"
                shares = None
                if len(cells) >= 3:
                    typeCell = cells[1]
                    if "우선주" in typeCell or "우선" in typeCell or "종류주" in typeCell:
                        stockType = "우선주"
                    shares = parseAmount(cells[2])
                elif len(cells) >= 2:
                    shares = parseAmount(cells[1])

                suffix = "Common" if stockType == "보통주" else "Pref"
                result[f"{key}{suffix}"] = shares
                break

        if not matched and lastKey and len(cells) >= 2:
            typeCell = cells[0].replace(" ", "")
            shares = parseAmount(cells[1])
            if "우선주" in typeCell or "우선" in typeCell or "종류주" in typeCell:
                result[f"{lastKey}Pref"] = shares

    return result if result else None
