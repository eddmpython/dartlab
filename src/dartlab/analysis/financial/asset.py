"""1-3 자산 구조 분석 — 계산만 담당.

BS를 영업/비영업으로 재분류하여 자산 운영 구조를 본다.
블록 조립은 review/builders.py가 한다.
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.financial._helpers import annualColsFromPeriods, toDict
from dartlab.analysis.financial._memoize import memoized_calc

_MAX_YEARS = 8
_MAX_QUARTERS = 5


def _get(row: dict, col: str) -> float:
    """dict에서 안전하게 값 꺼내기 (None → 0)."""
    v = row.get(col) if row else None
    return v if v is not None else 0


def _getFirst(data: dict, keys: list[str], col: str) -> float:
    """여러 계정명 중 값이 있는 첫 번째를 반환 (fallback 체인)."""
    for k in keys:
        row = data.get(k, {})
        v = row.get(col) if row else None
        if v is not None and v != 0:
            return v
    return 0


def _pct(part: float, total: float) -> float:
    """퍼센트 계산 (0 division 안전)."""
    if total is None or total == 0:
        return 0.0
    return part / total * 100


# ── 영업/비영업 분류 매핑 ──

# 영업자산 — 이중 카운팅 방지를 위해 fallback 쌍 분리
# "매출채권" / "매출채권및기타채권" → 하나만 사용 (_getFirst)
# "매입채무" / "매입채무및기타채무" → 하나만 사용 (_getFirst)
_OP_ASSET_SIMPLE = [
    "기타유동금융자산",
    "재고자산",
    "선급금",
    "기타유동자산",
    # 고정영업자산
    "유형자산",
    "사용권자산",
    "무형자산",
    "영업권",
    "건설중인자산",
    "투자부동산",
]
_OP_ASSET_FALLBACK = [["매출채권", "매출채권및기타채권"]]

_NON_OP_ASSET_ACCOUNTS = [
    "현금및현금성자산",
    "단기금융자산",
    "장기금융자산",
    "관계기업등지분관련투자자산",
    "기타비유동금융자산",
]

# 관계기업 투자: 기업마다 다른 계정명 사용 → fallback 쌍
_ASSOCIATES_FALLBACK = ("관계기업등지분관련투자자산", "지분법적용투자지분")

_OP_LIAB_SIMPLE = [
    "선수금",
    "계약부채",
    "선수수익",
    "미지급비용",
    "미지급금",
    "충당부채",
    "기타유동부채",
]
_OP_LIAB_FALLBACK = [["매입채무", "매입채무및기타채무"]]

# 운전자본: fallback 체인 (매출채권 없으면 매출채권및기타채권 사용)
_WC_REC_KEYS = ["매출채권", "매출채권및기타채권"]
_WC_PAY_KEYS = ["매입채무", "매입채무및기타채무"]
_WC_ASSET_KEYS = ["재고자산", "선급금", "기타유동자산"]

_FIXED_OP_KEYS = ["유형자산", "사용권자산", "무형자산", "영업권", "건설중인자산"]


def _sumOp(data: dict, col: str, simpleKeys: list[str], fallbackPairs: list[list[str]]) -> float:
    """영업자산/부채 합산 (fallback 쌍은 하나만 선택)."""
    total = sum(_get(data.get(k, {}), col) for k in simpleKeys)
    for pair in fallbackPairs:
        total += _getFirst(data, pair, col)
    return total


# ── 메인: 자산 구조 ──


@memoized_calc
def calcAssetStructure(company, *, basePeriod: str | None = None) -> dict | None:
    """자산을 영업/비영업으로 재분류 — 시계열.

    반환::

        {
            "latest": {
                "totalAssets": float,
                "opAssets": float, "opAssetsPct": float,
                "nonOpAssets": float, "nonOpAssetsPct": float,
                "workingCapitalAssets": float,
                "fixedOpAssets": float,
                "noa": float,
                "netFinDebt": float,
            },
            "composition": {
                "receivables": float, "inventory": float,
                "ppe": float, "intangibles": float,
                "rou": float, "cip": float,
                "cash": float, "investments": float,
            },
            "history": [{period, opAssetsPct, nonOpAssetsPct, noa, ...}, ...],
            "diagnosis": str,
        }
    """
    _allFallback = [k for pair in _OP_ASSET_FALLBACK + _OP_LIAB_FALLBACK for k in pair]
    allAccounts = (
        ["자산총계", "부채총계"]
        + _OP_ASSET_SIMPLE
        + _allFallback
        + _NON_OP_ASSET_ACCOUNTS
        + list(_ASSOCIATES_FALLBACK)
        + _OP_LIAB_SIMPLE
    )
    result = company.select("BS", allAccounts)
    parsed = toDict(result)
    if parsed is None:
        return None

    data, allPeriods = parsed
    taRow = data.get("자산총계")
    if taRow is None:
        return None

    yCols = annualColsFromPeriods(allPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    history = []
    latest = None

    for col in yCols:
        ta = _get(taRow, col)
        if ta <= 0:
            continue

        # 영업자산 합산 (fallback 쌍은 하나만 선택)
        opAssets = _sumOp(data, col, _OP_ASSET_SIMPLE, _OP_ASSET_FALLBACK)
        # 비영업자산 합산 (관계기업 투자는 fallback 쌍)
        nonOpAssets = 0
        for k in _NON_OP_ASSET_ACCOUNTS:
            if k == _ASSOCIATES_FALLBACK[0]:
                v = _get(data.get(k, {}), col)
                if v == 0:
                    v = _get(data.get(_ASSOCIATES_FALLBACK[1], {}), col)
                nonOpAssets += v
            else:
                nonOpAssets += _get(data.get(k, {}), col)
        # 나머지 = 총자산 - 영업 - 비영업 (분류 안 된 것)
        otherAssets = ta - opAssets - nonOpAssets

        # 영업부채 (fallback 쌍은 하나만 선택)
        opLiab = _sumOp(data, col, _OP_LIAB_SIMPLE, _OP_LIAB_FALLBACK)

        # 순영업자산(NOA) = 영업자산 - 영업부채
        noa = opAssets - opLiab

        # 순운전자본 자산/부채 (fallback 체인)
        rec = _getFirst(data, _WC_REC_KEYS, col)
        wcAssets = rec + sum(_get(data.get(k, {}), col) for k in _WC_ASSET_KEYS)
        pay = _getFirst(data, _WC_PAY_KEYS, col)
        wcOtherLiab = sum(
            _get(data.get(k, {}), col) for k in ["선수금", "계약부채", "선수수익", "미지급비용", "미지급금"]
        )
        wcLiab = pay + wcOtherLiab
        wc = wcAssets - wcLiab

        # 고정영업자산
        fixedOp = sum(_get(data.get(k, {}), col) for k in _FIXED_OP_KEYS)

        # 순금융부채
        cash = _get(data.get("현금및현금성자산", {}), col)
        stFin = _get(data.get("단기금융자산", {}), col)
        finDebt = _get(data.get("부채총계", {}), col) - opLiab
        netFinDebt = max(0, finDebt - cash - stFin)

        # 세부 구성 (매 연도)
        recVal = _getFirst(data, _WC_REC_KEYS, col)
        invVal = _get(data.get("재고자산", {}), col)
        ppeVal = _get(data.get("유형자산", {}), col)
        intVal = _get(data.get("무형자산", {}), col)
        gwVal = _get(data.get("영업권", {}), col)
        rouVal = _get(data.get("사용권자산", {}), col)
        cipVal = _get(data.get("건설중인자산", {}), col)
        assocVal = _get(data.get(_ASSOCIATES_FALLBACK[0], {}), col)
        if assocVal == 0:
            assocVal = _get(data.get(_ASSOCIATES_FALLBACK[1], {}), col)
        invstVal = assocVal + _get(data.get("장기금융자산", {}), col)

        entry = {
            "period": col,
            "totalAssets": ta,
            "opAssets": opAssets,
            "opAssetsPct": _pct(opAssets, ta),
            "nonOpAssets": nonOpAssets,
            "nonOpAssetsPct": _pct(nonOpAssets, ta),
            "otherAssetsPct": _pct(otherAssets, ta),
            "noa": noa,
            "wc": wc,
            "fixedOp": fixedOp,
            # 세부 항목
            "receivables": recVal,
            "inventory": invVal,
            "ppe": ppeVal,
            "intangibles": intVal,
            "goodwill": gwVal,
            "rou": rouVal,
            "cip": cipVal,
            "cash": cash,
            "stFinancial": stFin,
            "investments": invstVal,
        }
        history.append(entry)

        if latest is None:
            latest = {
                "totalAssets": ta,
                "opAssets": opAssets,
                "opAssetsPct": _pct(opAssets, ta),
                "nonOpAssets": nonOpAssets,
                "nonOpAssetsPct": _pct(nonOpAssets, ta),
                "otherAssets": ta - opAssets - nonOpAssets,
                "otherAssetsPct": _pct(ta - opAssets - nonOpAssets, ta),
                "workingCapital": wc,
                "fixedOpAssets": fixedOp,
                "noa": noa,
                "netFinDebt": netFinDebt,
            }

    if latest is None:
        return None

    # 진단
    opPct = latest["opAssetsPct"]
    nonOpPct = latest["nonOpAssetsPct"]
    if opPct >= 70:
        diagnosis = "영업자산 중심 — 자산 대부분이 사업에 투입됨"
    elif nonOpPct >= 40:
        diagnosis = "비영업자산 과다 — 투자/금융자산 비중이 높음 (지주회사 성격)"
    elif opPct >= 50:
        diagnosis = "혼합 구조 — 영업자산과 비영업자산이 섞여 있음"
    else:
        diagnosis = "비영업 우위 — 영업 자산보다 비영업 자산이 많음"

    # notes enrichment — 주석에서 상세 분해 데이터 추가 (있으면)
    from dartlab.analysis.financial._helpers import fetchNotesDetail

    notesDetail = fetchNotesDetail(company, ["inventory", "tangibleAsset", "intangibleAsset", "investmentProperty"])

    result_dict: dict[str, Any] = {
        "latest": latest,
        "history": history,
        "diagnosis": diagnosis,
    }
    if notesDetail:
        result_dict["notesDetail"] = notesDetail

    return result_dict


# ── 운전자본 ──


@memoized_calc
def calcWorkingCapital(company, *, basePeriod: str | None = None) -> dict | None:
    """운전자본 상세 + CCC.

    반환::

        {
            "latest": {
                "wc": float,
                "receivables": float, "inventory": float,
                "payables": float,
                "receivableDays": float, "inventoryDays": float,
                "payableDays": float, "ccc": float,
            },
            "history": [{period, wc, receivableDays, inventoryDays, payableDays, ccc}, ...],
        }
    """
    bsAccounts = ["매출채권", "매출채권및기타채권", "재고자산", "매입채무", "매입채무및기타채무"]
    isAccounts = ["매출액", "매출원가"]

    bsResult = company.select("BS", bsAccounts)
    isResult = company.select("IS", isAccounts)
    bsParsed = toDict(bsResult)
    isParsed = toDict(isResult)
    if bsParsed is None or isParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    isData, isPeriods = isParsed

    invRow = bsData.get("재고자산", {})
    revRow = isData.get("매출액", {})
    cogsRow = isData.get("매출원가", {})

    yCols = annualColsFromPeriods(bsPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    history = []
    latest = None

    for col in yCols:
        rec = _getFirst(bsData, _WC_REC_KEYS, col)
        inv = _get(invRow, col)
        pay = _getFirst(bsData, _WC_PAY_KEYS, col)
        rev = _get(revRow, col)
        cogs = _get(cogsRow, col)
        wc = rec + inv - pay

        # 회전일수
        recDays = rec / rev * 365 if rev > 0 else None
        invDays = inv / cogs * 365 if cogs > 0 else None
        payDays = pay / cogs * 365 if cogs > 0 else None
        ccc = None
        if recDays is not None and invDays is not None and payDays is not None:
            ccc = recDays + invDays - payDays

        entry = {
            "period": col,
            "wc": wc,
            "receivableDays": recDays,
            "inventoryDays": invDays,
            "payableDays": payDays,
            "ccc": ccc,
        }
        history.append(entry)

        if latest is None:
            latest = {
                "wc": wc,
                "receivables": rec,
                "inventory": inv,
                "payables": pay,
                "receivableDays": recDays,
                "inventoryDays": invDays,
                "payableDays": payDays,
                "ccc": ccc,
            }

    if latest is None:
        return None
    return {"latest": latest, "history": history}


# ── CAPEX 패턴 ──


@memoized_calc
def calcCapexPattern(company, *, basePeriod: str | None = None) -> dict | None:
    """CAPEX vs 감가상각 + 건설중인자산 추이.

    반환::

        {
            "latest": {
                "capex": float, "depreciation": float,
                "capexToDepRatio": float,
                "cip": float, "cipPct": float,
                "investmentType": str,
            },
            "history": [{period, capex, depreciation, capexToDepRatio, cip}, ...],
        }
    """
    # CAPEX = 유형자산 취득(CF 투자활동에서)
    cfAccounts = ["유형자산의취득", "무형자산의취득", "감가상각비"]
    bsAccounts = ["건설중인자산", "유형자산", "자산총계"]
    isAccounts = ["감가상각비"]

    cfResult = company.select("CF", cfAccounts)
    bsResult = company.select("BS", bsAccounts)
    isResult = company.select("IS", isAccounts)

    bsParsed = toDict(bsResult)
    if bsParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    cfData = toDict(cfResult)
    isData = toDict(isResult)

    cfDict = cfData[0] if cfData else {}
    isDict = isData[0] if isData else {}

    cipRow = bsData.get("건설중인자산", {})
    ppeRow = bsData.get("유형자산", {})
    taRow = bsData.get("자산총계", {})
    capexRow = cfDict.get("유형자산의취득", {})
    intCapexRow = cfDict.get("무형자산의취득", {})
    # 감가상각 3-tier fallback:
    # 1순위: IS 감가상각비 (있는 기업은 직접 사용)
    # 2순위: CF 영업활동 감가상각비 (한국전력 등)
    # 3순위: 업종별 추정 (유형자산 / 추정내용연수 10년)
    depRow = isDict.get("감가상각비") or cfDict.get("감가상각비") or {}

    yCols = annualColsFromPeriods(bsPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    history = []
    latest = None

    # 감가상각 이상치 필터용 중앙값 사전 계산
    _rawDeps = [abs(_get(depRow, c)) for c in yCols]
    _validDeps = [d for d in _rawDeps if d > 0]
    _depMedian = sorted(_validDeps)[len(_validDeps) // 2] if _validDeps else 0

    for col in yCols:
        cip = _get(cipRow, col)
        ppe = _get(ppeRow, col)
        ta = _get(taRow, col)
        # CAPEX는 CF에서 음수로 나옴 → abs
        capex = abs(_get(capexRow, col)) + abs(_get(intCapexRow, col))
        dep = abs(_get(depRow, col))
        # 이상치 필터: 중앙값 대비 100배 이상 차이나면 스케일 오류로 판단
        if dep > 0 and _depMedian > 0:
            if dep / _depMedian > 100 or _depMedian / dep > 100:
                dep = 0  # 이상치 제거 → 아래 fallback으로 추정
        # 3순위 fallback: 감가상각 null이면 유형자산/10으로 추정
        if dep == 0 and ppe is not None and ppe > 0:
            dep = ppe / 10  # 평균 내용연수 10년 가정

        ratio = capex / dep if dep > 0 else None
        # CAPEX/감가상각 비율 상한: 10배 초과는 감가상각 추정 오류 가능성
        if ratio is not None and ratio > 10:
            ratio = None
        cipPct = _pct(cip, ta) if ta > 0 else 0

        entry = {
            "period": col,
            "capex": capex,
            "depreciation": dep,
            "capexToDepRatio": ratio,
            "cip": cip,
            "cipPct": cipPct,
        }
        history.append(entry)

        if latest is None:
            if ratio is not None and ratio > 1.5:
                investType = "적극 투자 — CAPEX가 감가상각의 1.5배 초과"
            elif ratio is not None and ratio > 1.0:
                investType = "성장 투자 — CAPEX > 감가상각"
            elif ratio is not None and ratio > 0:
                investType = "유지 투자 — CAPEX < 감가상각"
            else:
                investType = "투자 정보 부족"

            latest = {
                "capex": capex,
                "depreciation": dep,
                "capexToDepRatio": ratio,
                "cip": cip,
                "cipPct": cipPct,
                "investmentType": investType,
            }

    if latest is None:
        return None
    return {"latest": latest, "history": history}


# ── 투자부동산 추세 ──


@memoized_calc
def calcInvestmentPropertyTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """투자부동산 비중 + 공정가치 변동 추세.

    부동산 비중이 높은 기업(REIT, 건설사, 보험사)에서 자산 분석 정확도 향상.
    notes.investmentProperty에서 항목별 시계열을 추출하여 총자산 대비 비중 추적.

    반환::

        {
            "history": [
                {"period": str, "totalAssets": float, "ipValue": float, "ipPct": float},
                ...
            ],
            "trend": str | None,
            "notesDetail": list[dict] | None,
        }
    """
    bsResult = company.select("BS", ["자산총계", "투자부동산"])
    parsed = toDict(bsResult)
    if parsed is None:
        return None

    data, allPeriods = parsed
    taRow = data.get("자산총계", {})
    ipRow = data.get("투자부동산", {})

    # 투자부동산 계정이 아예 없거나 값이 전부 0이면 해당 없음
    if not ipRow or all(v is None or v == 0 for v in ipRow.values()):
        return None

    yCols = annualColsFromPeriods(allPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    history = []
    for col in yCols:
        ta = _get(taRow, col)
        ip = _get(ipRow, col)
        if ta <= 0:
            continue
        history.append({
            "period": col,
            "totalAssets": ta,
            "ipValue": ip,
            "ipPct": round(ip / ta * 100, 2) if ip > 0 else 0,
        })

    if not history:
        return None

    # 추세 판단
    trend = None
    pcts = [h["ipPct"] for h in history if h["ipPct"] > 0]
    if len(pcts) >= 2:
        diff = pcts[0] - pcts[-1]
        if diff > 2:
            trend = "비중 증가"
        elif diff < -2:
            trend = "비중 감소"
        else:
            trend = "안정"

    result_dict: dict[str, Any] = {"history": history, "trend": trend}

    # notes enrichment — 투자부동산 세부 항목 (공정가치, 취득/처분 등)
    from dartlab.analysis.financial._helpers import fetchNotesDetail

    notesData = fetchNotesDetail(company, ["investmentProperty"])
    if notesData.get("investmentProperty"):
        result_dict["notesDetail"] = notesData["investmentProperty"]

    return result_dict


# ── 무형자산 상세 ──


@memoized_calc
def calcIntangibleAssetDetail(company, *, basePeriod: str | None = None) -> dict | None:
    """무형자산 상세 분해 — 영업권/R&D/기타 비중 + 상각 추세.

    notes.intangibleAsset에서 항목별 시계열을 추출하여
    영업권 비중, R&D 자산화 추세, 손상차손 리스크를 분석.
    바이오/IT 등 IP 비중 높은 기업에서 이익품질 판단에 중요.

    반환::

        {
            "items": [{"name": str, "latestValue": float, "pct": float}, ...],
            "totalIntangible": float,
            "goodwillPct": float | None,
            "trend": str | None,
            "notesDetail": list[dict] | None,
        }
    """
    from dartlab.analysis.financial._helpers import fetchNotesDetail, parseNumStr

    notesData = fetchNotesDetail(company, ["intangibleAsset"])
    rawRows = notesData.get("intangibleAsset")

    # notes 없으면 BS에서 기본 분해
    bsResult = company.select("BS", ["무형자산", "영업권", "자산총계"])
    bsParsed = toDict(bsResult)
    if bsParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    intRow = bsData.get("무형자산", {})
    gwRow = bsData.get("영업권", {})
    taRow = bsData.get("자산총계", {})

    yCols = annualColsFromPeriods(bsPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    latestCol = yCols[0]
    totalInt = _get(intRow, latestCol) + _get(gwRow, latestCol)
    ta = _get(taRow, latestCol)

    if totalInt <= 0:
        return None

    # notes 상세가 있으면 항목별 분해
    items = []
    if rawRows:
        for row in rawRows:
            item = str(row.get("항목", "")).strip()
            if not item or any(kw in item for kw in ("합계", "총계", "소계")):
                continue
            v = parseNumStr(row.get(str(latestCol)))
            if v is not None and v > 0:
                items.append({"name": item, "latestValue": v, "pct": round(v / totalInt * 100, 1) if totalInt > 0 else 0})
        items.sort(key=lambda x: x["latestValue"], reverse=True)
        items = items[:8]

    # 영업권 비중
    gw = _get(gwRow, latestCol)
    goodwillPct = round(gw / totalInt * 100, 1) if totalInt > 0 and gw > 0 else None

    # 총자산 대비 무형자산 비중 추세
    trend = None
    intPcts = []
    for col in yCols:
        intVal = _get(intRow, col) + _get(gwRow, col)
        taVal = _get(taRow, col)
        if taVal > 0 and intVal > 0:
            intPcts.append(intVal / taVal * 100)
    if len(intPcts) >= 2:
        diff = intPcts[0] - intPcts[-1]
        if diff > 2:
            trend = "비중 증가"
        elif diff < -2:
            trend = "비중 감소"
        else:
            trend = "안정"

    result_dict: dict[str, Any] = {
        "items": items,
        "totalIntangible": totalInt,
        "totalAssets": ta,
        "intangiblePct": round(totalInt / ta * 100, 1) if ta > 0 else 0,
        "goodwillPct": goodwillPct,
        "trend": trend,
    }

    if rawRows:
        result_dict["notesDetail"] = rawRows

    return result_dict


# ── 자산 플래그 ──


@memoized_calc
def calcAssetFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """자산 구조 경고 신호."""
    flags = []

    structure = calcAssetStructure(company, basePeriod=basePeriod)
    if structure:
        lat = structure["latest"]
        if lat["nonOpAssetsPct"] >= 40:
            flags.append(f"비영업자산 {lat['nonOpAssetsPct']:.0f}% — 지주/투자 성격")
        hist0 = structure["history"][0] if structure["history"] else {}
        if hist0:
            ta = lat["totalAssets"]
            cipPct = _pct(hist0.get("cip", 0), ta)
            if cipPct >= 10:
                flags.append(f"건설중인자산 {cipPct:.0f}% — 대규모 투자 진행 중")
            invPct = _pct(hist0.get("inventory", 0), ta)
            if invPct >= 20:
                flags.append(f"재고자산 {invPct:.0f}% — 재고 비대화 주의")

    wc = calcWorkingCapital(company, basePeriod=basePeriod)
    if wc and wc["latest"]["ccc"] is not None:
        ccc = wc["latest"]["ccc"]
        if ccc > 2000:
            pass  # CCC > 2000일은 데이터 왜곡 가능성 → 경고 제외
        elif ccc > 120:
            flags.append(f"CCC {ccc:.0f}일 — 현금 회수 매우 느림")
        # CCC < 0은 선수금/매입채무 우위로 운전자본 효율적 → 경고 아닌 정보
        # efficiency.py의 "운전자본 유리 구조"로 충분

    capex = calcCapexPattern(company, basePeriod=basePeriod)
    if capex and capex["latest"]["capexToDepRatio"] is not None:
        ratio = capex["latest"]["capexToDepRatio"]
        if ratio < 0.5 and ratio > 0:
            flags.append(f"CAPEX/감가상각 {ratio:.1f}배 — 투자 부족 (자산 노후화 위험)")
        elif ratio > 3.0:
            flags.append(f"CAPEX/감가상각 {ratio:.1f}배 — 공격적 투자")

    from dartlab.analysis.financial.efficiency import calcTurnoverTrend

    turnover = calcTurnoverTrend(company, basePeriod=basePeriod)
    if turnover and turnover.get("totalAssetTurnover"):
        tat = turnover["totalAssetTurnover"]
        if len(tat) >= 2:
            newest = tat[0].get("value")
            oldest = tat[-1].get("value")
            if newest is not None and oldest is not None and oldest > 0:
                change = (newest - oldest) / oldest * 100
                if change < -20:
                    flags.append(f"총자산회전율 {change:.0f}% 하락 — 자산 효율 악화")

    return flags
