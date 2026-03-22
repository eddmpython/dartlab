"""원재료 및 생산설비 테이블 파서."""

import re

from dartlab.core.tableParser import parseAmount


def splitCells(line: str) -> list[str]:
    """파이프로 분리, 빈 셀 유지."""
    parts = line.strip().split("|")
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


# ── 원재료 파서 ──────────────────────────────────────────


def _findHeaderIndices(headerCells: list[str]) -> dict:
    """헤더 셀에서 각 컬럼의 인덱스를 찾는다."""
    idx: dict[str, int] = {}
    gubunIdx: int | None = None  # "구분" 위치를 임시 저장
    for i, c in enumerate(headerCells):
        clean = c.replace(" ", "")
        if "사업부문" in clean or clean == "부문" or "부 문" in c:
            idx["segment"] = i
        elif "매입유형" in clean:
            if "segment" in idx:
                idx["subType"] = i
            else:
                idx["segment"] = i
        elif clean in ("구분",):
            gubunIdx = i
        elif (
            "품목" in clean
            or "원재료명" in clean
            or "원부재료" in clean
            or "원,부재료" in clean
            or "원ㆍ부재료" in clean
        ):
            idx["item"] = i
        elif "주요원재료" in clean or "주요제품명" in clean:
            idx["item"] = i
        elif "용도" in clean:
            idx["usage"] = i
        elif "매입액" in clean or "투입액" in clean or "매입금액" in clean:
            idx["amount"] = i
        elif clean == "금액" or "원재료금액" in clean:
            idx["amount"] = i
        elif "비율" in clean or "비중" in clean:
            idx["ratio"] = i
        elif "비고" in clean or "매입처" in clean or "구매처" in clean:
            idx["supplier"] = i
        elif re.match(r"^제\d+", clean) or re.match(r"^20\d{2}", clean) or re.match(r"^제\s*\d+", c.strip()):
            if "amount" not in idx:
                idx["amount"] = i

    # "구분" 처리: item이 따로 있으면 segment, 없으면 item
    if gubunIdx is not None:
        if "item" in idx:
            if "segment" not in idx:
                idx["segment"] = gubunIdx
        else:
            idx["item"] = gubunIdx

    return idx


def parseRawMaterials(content: str) -> list[dict] | None:
    """주요 원재료 현황 파싱 — 헤더 직접 감지 방식.

    Returns:
        [{segment, item, usage, amount, ratio, supplier}] 또는 None
    """
    lines = content.split("\n")
    inTable = False
    results: list[dict] = []
    lastSegment = None
    headerIdx: dict[str, int] = {}
    headerCols = 0
    prevHeaderCandidate: list[str] | None = None  # 분할 헤더 1행째 후보

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not s.startswith("|"):
            if s.startswith("※") or s.startswith("주"):
                continue
            if inTable and results:
                if re.match(r"^[나다라][\.\)]", s) or "가격" in s or "생산" in s:
                    break
            continue

        if "---" in s:
            continue

        cells = splitCells(s)
        if not cells:
            continue

        joined = " ".join(cells)

        if "단위" in joined and ("억원" in joined or "백만원" in joined or "천원" in joined or "원)" in joined):
            continue

        # 헤더 감지
        joinedNoSpace = joined.replace(" ", "")
        hasAmtKw = (
            "매입액" in joinedNoSpace
            or "투입액" in joinedNoSpace
            or "매입금액" in joinedNoSpace
            or "원재료금액" in joinedNoSpace
        )
        hasItemKw = (
            "품목" in joinedNoSpace
            or "원재료" in joinedNoSpace
            or "원부재료" in joinedNoSpace
            or "원,부재료" in joinedNoSpace
            or "원ㆍ부재료" in joinedNoSpace
            or "부문" in joinedNoSpace
            or "제품명" in joinedNoSpace
        )
        hasTypeKw = "매입유형" in joinedNoSpace
        hasRatioKw = "비율" in joinedNoSpace or "비중" in joinedNoSpace
        hasYearCol = bool(re.search(r"제\s*\d+\s*(?:\([^)]*\)\s*)?기|20\d{2}\s*년", joined))
        hasStructKw = "구분" in joinedNoSpace and ("용도" in joinedNoSpace or hasAmtKw or hasRatioKw)

        # 분할 헤더 2행째 감지: 매입액|비율만 반복되는 행
        isSplitRow2 = hasAmtKw and all(
            c.replace(" ", "")
            in (
                "",
                "매입액",
                "비율",
                "비율(%)",
                "비중",
                "비중(%)",
            )
            or re.match(r"^제\s*\d+", c.strip())
            or re.match(r"^20\d{2}", c.strip())
            for c in cells
        )

        isHeader = not isSplitRow2 and (
            (hasAmtKw and (hasItemKw or hasRatioKw or hasStructKw))
            or (hasTypeKw and hasItemKw)
            or (hasAmtKw and hasYearCol)
            or (
                hasYearCol
                and hasItemKw
                and "구분" in joinedNoSpace
                and "생산" not in joinedNoSpace
                and "수량" not in joinedNoSpace
            )
        )

        if isSplitRow2 and prevHeaderCandidate is not None:
            # 1행째 + 2행째 합쳐서 헤더 구성
            inTable = True
            headerIdx = _findHeaderIndices(prevHeaderCandidate)
            subIdx = _findHeaderIndices(cells)
            for k, v in subIdx.items():
                if k not in headerIdx:
                    headerIdx[k] = v
            if "amount" in headerIdx and "ratio" not in headerIdx:
                amtCell = ""
                ai = headerIdx["amount"]
                if ai < len(prevHeaderCandidate):
                    amtCell = prevHeaderCandidate[ai]
                elif ai < len(cells):
                    amtCell = cells[ai]
                if "비율" not in amtCell.replace(" ", ""):
                    nextIdx = headerIdx["amount"] + 1
                    if nextIdx < max(len(prevHeaderCandidate), len(cells)):
                        headerIdx["ratio"] = nextIdx
            headerCols = max(len(prevHeaderCandidate), len(cells))
            prevHeaderCandidate = None
            continue

        if isSplitRow2 and inTable and headerIdx:
            # row1이 isHeader로 이미 처리된 후 row2가 오는 경우
            # 매입액|비율 패턴이고 비율 키워드가 있을 때만 ratio 설정
            if "amount" in headerIdx and "ratio" not in headerIdx:
                if hasRatioKw:
                    nextIdx = headerIdx["amount"] + 1
                    if nextIdx < headerCols:
                        headerIdx["ratio"] = nextIdx
            continue

        if isHeader:
            headerCols = len(cells)
            headerIdx = _findHeaderIndices(cells)
            if "amount" not in headerIdx:
                for ci, c in enumerate(cells):
                    if re.match(r"^(제\d+|20\d{2})", c.replace(" ", "")):
                        headerIdx["amount"] = ci
                        break
            if "amount" not in headerIdx:
                # amount 컬럼 없는 헤더 → 테이블 진입하지 않음
                prevHeaderCandidate = None
                continue
            inTable = True
            # amount 바로 다음 칸이 ratio인 경우 자동 설정
            # 제외: 매입액(비율) 합쳐진 헤더, 연도 컬럼 헤더, 다음 셀이 빈칸
            if "ratio" not in headerIdx:
                amtCell = cells[headerIdx["amount"]] if headerIdx["amount"] < len(cells) else ""
                amtIsYearCol = bool(re.match(r"^제\s*\d+|^20\d{2}", amtCell.replace(" ", "")))
                nextIdx = headerIdx["amount"] + 1
                nextCell = cells[nextIdx].strip() if nextIdx < len(cells) else ""
                if (
                    not amtIsYearCol
                    and "비율" not in amtCell.replace(" ", "")
                    and nextCell  # 다음 셀이 빈칸이면 연도 span → ratio 아님
                ):
                    headerIdx["ratio"] = nextIdx
            prevHeaderCandidate = None
            continue

        # 분할 헤더 1행째 후보 기억 (품목/구분 등이 있는 행)
        if not inTable and (hasItemKw or hasStructKw or hasTypeKw):
            prevHeaderCandidate = cells
            continue

        # 분할 헤더: 이전 행이 헤더로 인식됐지만 amount 미발견
        if inTable and not headerIdx.get("amount"):
            if "매입액" in joinedNoSpace or "비율" in joinedNoSpace:
                subIdx = _findHeaderIndices(cells)
                headerIdx.update(subIdx)
                continue

        if not inTable:
            continue

        if "※" in cells[0] or re.match(r"^주\d*\)", cells[0]):
            break

        nonEmpty = [c for c in cells if c]

        # 서브 헤더 스킵: 대부분 셀이 연도 패턴이면 (분할 헤더 2행째)
        yearCellCount = sum(
            1
            for c in nonEmpty
            if re.match(r"^(제\s*\d+|20\d{2})", c.replace(" ", ""))
            or "매입액" == c.replace(" ", "")
            or "비율" == c.replace(" ", "")
        )
        if yearCellCount >= len(nonEmpty) * 0.5 and len(nonEmpty) >= 2:
            continue

        first = cells[0].replace(" ", "")
        if first in ("소계", "합계", "총계", "부문계"):
            continue
        if len(nonEmpty) < 2:
            continue

        segment = None
        item = None
        usage = None
        amt = None
        ratio = None
        supplier = None

        if headerIdx and "amount" in headerIdx:
            amtIdx = headerIdx["amount"]
            segIdx = headerIdx.get("segment")
            itemIdx = headerIdx.get("item")
            usageIdx = headerIdx.get("usage")
            ratioIdx = headerIdx.get("ratio")
            suppIdx = headerIdx.get("supplier")

            # shifted 감지
            shifted = False
            if segIdx is not None and segIdx < len(cells) and cells[segIdx]:
                if ratioIdx is not None and ratioIdx < len(cells):
                    ratioText = cells[ratioIdx]
                    amtText = cells[amtIdx] if amtIdx < len(cells) else ""
                    amtVal = parseAmount(amtText)
                    ratioVal = parseAmount(ratioText)
                    if amtVal is not None and "%" in ratioText:
                        shifted = False
                    elif amtVal is not None and ratioVal is not None:
                        # 비율이 100 초과면 실제 비율이 아님 → shifted
                        if ratioVal > 100:
                            shifted = True
                        else:
                            shifted = False
                    elif amtVal is None:
                        shifted = True
                    elif "%" not in ratioText and ratioVal is None:
                        # shifted 위치(amtIdx - 1)에 숫자가 있어야 진짜 shifted
                        prevIdx = amtIdx - 1
                        if prevIdx >= 0 and prevIdx < len(cells):
                            prevVal = parseAmount(cells[prevIdx])
                            if prevVal is not None:
                                shifted = True
                elif amtIdx < len(cells):
                    if parseAmount(cells[amtIdx]) is None:
                        shifted = True

            # shifted이지만 행 전체에 숫자가 없으면 실제로는
            # 금액이 없는 정상 행 (segment만 존재)
            if shifted:
                hasAnyNum = any(parseAmount(c) is not None for c in cells)
                if not hasAnyNum:
                    # 금액 없는 행 — segment만 갱신
                    if segIdx is not None and segIdx < len(cells) and cells[segIdx]:
                        lastSegment = cells[segIdx]
                    continue

            if shifted:
                segment = lastSegment
                shift = 0
                for tryShift in range(1, amtIdx + 1):
                    testIdx = amtIdx - tryShift
                    if testIdx < len(cells):
                        testVal = parseAmount(cells[testIdx])
                        if testVal is not None and testVal > 100:
                            shift = tryShift
                            break
                if shift == 0:
                    shift = 1

                def si(idx: int | None, s: int = shift) -> int | None:
                    return idx - s if idx is not None and idx - s >= 0 else None

                if si(itemIdx) is not None and si(itemIdx) < len(cells):
                    item = cells[si(itemIdx)]
                if si(usageIdx) is not None and si(usageIdx) < len(cells):
                    usage = cells[si(usageIdx)]
                if si(amtIdx) is not None and si(amtIdx) < len(cells):
                    amtText = cells[si(amtIdx)]
                    m2 = re.match(r"^([\d,]+)\s*\(([\d.]+)%?\)", amtText)
                    if m2:
                        amt = parseAmount(m2.group(1))
                        ratio = parseAmount(m2.group(2))
                    else:
                        amt = parseAmount(amtText)
                if si(ratioIdx) is not None and si(ratioIdx) < len(cells) and ratio is None:
                    ratio = parseAmount(cells[si(ratioIdx)])
                if si(suppIdx) is not None and si(suppIdx) < len(cells):
                    supplier = cells[si(suppIdx)]
            else:
                if segIdx is not None and segIdx < len(cells) and cells[segIdx]:
                    segment = cells[segIdx]
                    lastSegment = segment
                else:
                    segment = lastSegment

                if itemIdx is not None and itemIdx < len(cells):
                    item = cells[itemIdx]
                if usageIdx is not None and usageIdx < len(cells):
                    usage = cells[usageIdx]
                if amtIdx < len(cells):
                    amtText = cells[amtIdx]
                    m = re.match(r"^([\d,]+)\s*\(([\d.]+)%?\)", amtText)
                    if m:
                        amt = parseAmount(m.group(1))
                        ratio = parseAmount(m.group(2))
                    else:
                        amt = parseAmount(amtText)
                if ratioIdx is not None and ratioIdx < len(cells) and ratio is None:
                    ratio = parseAmount(cells[ratioIdx])
                if suppIdx is not None and suppIdx < len(cells):
                    supplier = cells[suppIdx]
        else:
            segment = lastSegment
            item = nonEmpty[0] if len(nonEmpty) > 0 else None
            usage = nonEmpty[1] if len(nonEmpty) > 1 else None
            amt = parseAmount(nonEmpty[2]) if len(nonEmpty) > 2 else None
            ratio = parseAmount(nonEmpty[3]) if len(nonEmpty) > 3 else None
            supplier = nonEmpty[4] if len(nonEmpty) > 4 else None

        if item and item.replace(" ", "") in ("소계", "합계", "총계", "부문계"):
            continue

        # item이 순수 숫자면 shift된 데이터 → 제외
        if item and re.match(r"^[\d,. ]+$", item.strip()):
            continue

        if item and (amt is not None or ratio is not None):
            results.append(
                {
                    "segment": segment,
                    "item": item,
                    "usage": usage,
                    "amount": amt,
                    "ratio": ratio,
                    "supplier": supplier,
                }
            )

    return results if results else None


# ── 생산설비 파서 ──────────────────────────────────────────

COL_KEYS = {
    "토지": "land",
    "토 지": "land",
    "건물": "buildings",
    "건물및구축물": "buildings",
    "건물 및 구축물": "buildings",
    "건물및 구축물": "buildings",
    "구축물": "structures",
    "기계장치": "machinery",
    "건설중인자산": "construction",
    "건설중인자산등": "construction",
    "건설중인 자산": "construction",
    "기타유형자산": "other",
    "기타의유형자산": "other",
    "공구기구비품": "other",
    "공구기구비품등": "other",
    "공구와기구": "other",
    "공기구": "other",
    "사용권자산": "rou",
    "차량운반구": "vehicles",
    "비품": "fixtures",
    "미착기계": "undelivered",
    "계": "total",
    "합계": "total",
    "합 계": "total",
}


def _normalizeColKey(text: str) -> str | None:
    """컬럼명을 정규화된 키로 변환."""
    clean = text.strip().replace(" ", "")
    if clean in COL_KEYS:
        return COL_KEYS[clean]
    if text.strip() in COL_KEYS:
        return COL_KEYS[text.strip()]
    return None


def parseEquipment(content: str) -> dict | None:
    """유형자산 변동 테이블 파싱 — 기말장부금액 행.

    Returns:
        {land, buildings, machinery, ..., total, depreciation, capex} 또는 None
    """
    lines = content.split("\n")
    inTable = False
    colNames: list[str | None] = []
    result: dict[str, float] = {}

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not s.startswith("|"):
            if inTable and result:
                if s and not s.startswith("※") and not s.startswith("(") and not s.startswith("["):
                    if "시설투자" in s or "투자" in s:
                        continue
                    break
            continue

        if "---" in s:
            continue

        cells = splitCells(s)
        if not cells:
            continue
        joined = " ".join(cells)

        if "단위" in joined and ("억원" in joined or "백만원" in joined or "천원" in joined):
            continue

        # 헤더 감지
        assetCount = sum(1 for c in cells if _normalizeColKey(c) is not None)
        hasTotal = any(_normalizeColKey(c) == "total" for c in cells)

        if assetCount >= 3 and hasTotal:
            colNames = []

            firstClean = cells[0].replace(" ", "")
            if firstClean in ("구분", "계정과목", "과목"):
                colNames.append(None)
                for c in cells[1:]:
                    colNames.append(_normalizeColKey(c))
            elif _normalizeColKey(cells[0]) is not None:
                colNames.append(None)
                for c in cells:
                    colNames.append(_normalizeColKey(c))
            else:
                for c in cells:
                    colNames.append(_normalizeColKey(c))

            inTable = True
            result = {}
            continue

        if not inTable or not colNames:
            continue

        # 행 라벨
        label = cells[0].replace(" ", "")
        if len(cells) > 1 and parseAmount(cells[1]) is None:
            label += cells[1].replace(" ", "")

        # 기말 행
        isEndRow = False
        if "기말" in label:
            if "장부" in label or "순장부" in label:
                isEndRow = True
            elif "취득" in label or "원가" in label:
                isEndRow = False
            elif label.replace("기말", "").replace("금액", "") == "":
                isEndRow = True

        if isEndRow:
            for ci in range(len(colNames)):
                key = colNames[ci]
                if key and ci < len(cells):
                    val = parseAmount(cells[ci])
                    if val is not None and key not in result:
                        result[key] = val
            if result:
                break

        # 감가상각비
        if "감가상각" in label and "누계" not in label and "포함" not in label and "원가" not in label:
            for ci in range(len(colNames)):
                if colNames[ci] == "total" and ci < len(cells):
                    val = parseAmount(cells[ci])
                    if val is not None:
                        result["depreciation"] = abs(val)

        # CAPEX
        if "취득" in label and ("일반" in label or "자본적" in label):
            for ci in range(len(colNames)):
                if colNames[ci] == "total" and ci < len(cells):
                    val = parseAmount(cells[ci])
                    if val is not None:
                        result["capex"] = val

    return result if result else None


# ── 시설투자 파서 ──────────────────────────────────────────


def parseCapex(content: str) -> list[dict] | None:
    """시설투자 현황 파싱.

    Returns:
        [{segment, amount}] 또는 None
    """
    lines = content.split("\n")
    inSection = False
    inTable = False
    results: list[dict] = []

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "시설투자" in s or "투자계획" in s or "투자 현황" in s:
                inSection = True
            continue

        if not s.startswith("|"):
            if inTable and results:
                break
            continue
        if "---" in s:
            continue

        cells = splitCells(s)
        joined = " ".join(cells)

        if "단위" in joined:
            continue
        if ("구 분" in joined or "구분" in joined) and ("투자" in joined or "내 용" in joined):
            inTable = True
            continue
        if not inTable:
            continue

        nonEmpty = [c for c in cells if c]
        if len(nonEmpty) < 2:
            continue

        if nonEmpty[0].replace(" ", "") in ("합계", "총계"):
            for c in reversed(nonEmpty):
                v = parseAmount(c)
                if v is not None and v > 0:
                    results.append({"segment": "합계", "amount": v})
                    break
            break

        name = nonEmpty[0]
        amt = None
        for c in reversed(nonEmpty):
            v = parseAmount(c)
            if v is not None and v > 0:
                amt = v
                break

        if name and amt:
            results.append({"segment": name, "amount": amt})

    return results if results else None
