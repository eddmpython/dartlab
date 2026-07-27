"""asset.py CAPEX + 투자부동산 + 무형자산 calc 분리.

분리 이유: asset.py 819 줄. 3 개 calc (calcCapexPattern · calcInvestmentPropertyTrend ·
calcIntangibleAssetDetail) 약 324 줄. asset.py 의 facade (자산구조 · 운전자본 · 플래그)
책임만 유지.

BC: asset 모듈에서 3 calc 모두 import 가능 (re-export).
"""

from __future__ import annotations

from typing import Any

from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safePct as _pct
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

_MAX_YEARS = 8


def _flowValue(row: dict, col: str) -> float:
    """CF/IS flow 행에서 값 추출. None 은 0.

    Parameters
    ----------
    row : dict
        기간 -> 값 행.
    col : str
        기간 컬럼.

    Returns
    -------
    float
        값 또는 0.
    """
    v = row.get(col)
    return v if v is not None else 0


def _capexEntry(col: str, rows: dict[str, dict], depMedian: float) -> dict:
    """한 연도의 CAPEX / 감가상각 / 건설중인자산 비중.

    Parameters
    ----------
    col : str
        연도 컬럼.
    rows : dict[str, dict]
        cip/ppe/ta/capex/intCapex/dep 행 dict.
    depMedian : float
        감가상각 중앙값 (이상치 필터 기준).

    Returns
    -------
    dict
        history 항목 한 장.
    """
    cip = _get(rows["cip"], col)
    ppe = _get(rows["ppe"], col)
    ta = _get(rows["ta"], col)
    # CAPEX 는 CF 에서 음수로 나오므로 abs
    capex = abs(_flowValue(rows["capex"], col)) + abs(_flowValue(rows["intCapex"], col))
    dep = abs(_flowValue(rows["dep"], col))
    # 이상치 필터: 중앙값 대비 100배 이상 차이나면 스케일 오류로 판단
    if dep > 0 and depMedian > 0:
        if dep / depMedian > 100 or depMedian / dep > 100:
            dep = 0  # 이상치 제거. 아래 fallback 으로 추정한다.
    # 3순위 fallback: 감가상각 null 이면 유형자산/10 으로 추정
    if dep == 0 and ppe is not None and ppe > 0:
        dep = ppe / 10  # 평균 내용연수 10년 가정

    ratio = capex / dep if dep > 0 else None
    # CAPEX/감가상각 비율 상한: 10배 초과는 감가상각 추정 오류 가능성
    if ratio is not None and ratio > 10:
        ratio = None

    return {
        "period": col,
        "capex": capex,
        "depreciation": dep,
        "capexToDepRatio": ratio,
        "cip": cip,
        "cipPct": _pct(cip, ta) if ta > 0 else 0,
    }


def _investmentType(ratio: float | None) -> str:
    """CAPEX/감가상각 배수를 투자 성격 문구로.

    Parameters
    ----------
    ratio : float | None
        CAPEX / 감가상각.

    Returns
    -------
    str
        투자 성격 문구.
    """
    if ratio is not None and ratio > 1.5:
        return "적극 투자. CAPEX가 감가상각의 1.5배 초과"
    if ratio is not None and ratio > 1.0:
        return "성장 투자. CAPEX > 감가상각"
    if ratio is not None and ratio > 0:
        return "유지 투자. CAPEX < 감가상각"
    return "투자 정보 부족"


@memoizedCalc
def calcCapexPattern(company, *, basePeriod: str | None = None) -> dict | None:
    """CAPEX vs 감가상각 + 건설중인자산 추이.

    Capabilities:
        - CAPEX/감가상각 비율과 건설중인자산 비중을 시계열로 정리.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        latest : dict
            capex : float — 자본적지출 (원)
            depreciation : float — 감가상각비 (원)
            capexToDepRatio : float — CAPEX/감가상각 비율 (배)
            cip : float — 건설중인자산 (원)
            cipPct : float — 건설중인자산 비중 (%)
            investmentType : str — 투자 유형 판단
        history : list[dict] — 연도별 CAPEX 패턴 시계열

    Guide:
        비율 1.5 초과 = 적극 투자, 1.0 이하 = 유지/축소.

    When:
        설비 사이클 진단, CAPEX 강도 평가 시점.

    How:
        CF 유형/무형 취득 합 vs IS·CF 감가상각 (3-tier fallback) 비교.

    Requires:
        BS/CF/IS 다년 + 유형자산·감가상각 항목.

    Raises:
        없음 — BS 결측 시 None.

    Example:
        >>> calcCapexPattern(company)
        {'latest': {'investmentType': '성장 투자 — CAPEX > 감가상각'}, ...}

    See Also:
        - calcInvestmentPropertyTrend : 투자부동산 추세.

    AIContext:
        ratio 가 None 이면 감가상각 추정 오차 가능성 명시.
    """
    # CAPEX = 유형자산 취득(CF 투자활동에서)
    cfAccounts = ["유형자산의취득", "무형자산의취득", "감가상각비"]
    bsAccounts = ["건설중인자산", "유형자산", "자산총계"]
    isAccounts = ["감가상각비"]

    cfResult = company.select("CF", cfAccounts, strict=False)
    bsResult = company.select("BS", bsAccounts, strict=False)
    isResult = company.select("IS", isAccounts, strict=False)

    bsParsed = toDictBySnakeId(bsResult)
    if bsParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    cfData = toDictBySnakeId(cfResult)
    isData = toDictBySnakeId(isResult)

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

    yCols = annualColsFromPeriods(bsPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    history = []
    latest = None

    # 감가상각 이상치 필터용 중앙값 사전 계산
    rawDeps = [abs(_flowValue(depRow, c)) for c in yCols]
    validDeps = [d for d in rawDeps if d > 0]
    depMedian = sorted(validDeps)[len(validDeps) // 2] if validDeps else 0

    rows = {"cip": cipRow, "ppe": ppeRow, "ta": taRow, "capex": capexRow, "intCapex": intCapexRow, "dep": depRow}
    for col in yCols:
        entry = _capexEntry(col, rows, depMedian)
        history.append(entry)

        if latest is None:
            latest = {
                "capex": entry["capex"],
                "depreciation": entry["depreciation"],
                "capexToDepRatio": entry["capexToDepRatio"],
                "cip": entry["cip"],
                "cipPct": entry["cipPct"],
                "investmentType": _investmentType(entry["capexToDepRatio"]),
            }

    if latest is None:
        return None
    return {"latest": latest, "history": history}


# ── 투자부동산 추세 ──


@memoizedCalc
def calcInvestmentPropertyTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """투자부동산 비중 + 공정가치 변동 추세.

    부동산 비중이 높은 기업(REIT, 건설사, 보험사)에서 자산 분석 정확도 향상.
    notes.investmentProperty에서 항목별 시계열을 추출하여 총자산 대비 비중 추적.

    Capabilities:
        - 투자부동산 시계열 비중 + 주석 enrichment 결합.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        history : list[dict]
            period : str — 기간
            totalAssets : float — 총자산 (원)
            ipValue : float — 투자부동산 금액 (원)
            ipPct : float — 총자산 대비 비중 (%)
        trend : str | None — 비중 추세 ("비중 증가"|"비중 감소"|"안정")
        notesDetail : list[dict] | None — 주석 상세 데이터

    Guide:
        REIT/건설사 외엔 비중 5% 미만이 일반.

    When:
        부동산 비중 큰 기업의 자산 구조 검토 시점.

    How:
        BS 투자부동산/자산총계 비중 + notes investmentProperty 결합.

    Requires:
        BS 다년 + 투자부동산 계정.

    Raises:
        없음 — 결측 시 None.

    Example:
        >>> calcInvestmentPropertyTrend(company)
        {'trend': '비중 증가', ...}

    See Also:
        - calcIntangibleAssetDetail : 무형자산 분해.

    AIContext:
        주석 detail 부재 시 history 비중만 인용.
    """
    bsResult = company.select("BS", ["자산총계", "투자부동산"])
    parsed = toDictBySnakeId(bsResult)
    if parsed is None:
        return None

    data, allPeriods = parsed
    taRow = data.get("자산총계", {})
    ipRow = data.get("투자부동산", {})

    # 투자부동산 계정이 아예 없거나 값이 전부 0이면 해당 없음
    if not ipRow or all(v is None or v == 0 for v in ipRow.values()):
        return None

    yCols = annualColsFromPeriods(allPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        ta = _get(taRow, col)
        ip = _get(ipRow, col)
        if ta <= 0:
            continue
        history.append(
            {
                "period": col,
                "totalAssets": ta,
                "ipValue": ip,
                "ipPct": round(ip / ta * 100, 2) if ip > 0 else 0,
            }
        )

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

    resultDict: dict[str, Any] = {"history": history, "trend": trend}

    # notes enrichment — 투자부동산 세부 항목 (공정가치, 취득/처분 등)
    from dartlab.analysis.financial.companyContext import fetchNotesDetail

    notesData = fetchNotesDetail(company, ["investmentProperty"])
    if notesData.get("investmentProperty"):
        resultDict["notesDetail"] = notesData["investmentProperty"]

    return resultDict


# ── 무형자산 상세 ──


@memoizedCalc
def calcIntangibleAssetDetail(company, *, basePeriod: str | None = None) -> dict | None:
    """무형자산 상세 분해 — 영업권/R&D/기타 비중 + 상각 추세.

    notes.intangibleAsset에서 항목별 시계열을 추출하여
    영업권 비중, R&D 자산화 추세, 손상차손 리스크를 분석.
    바이오/IT 등 IP 비중 높은 기업에서 이익품질 판단에 중요.

    Capabilities:
        - 무형자산 항목별 비중과 영업권 비중 추세 분석.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        items : list[dict]
            name : str — 항목명
            latestValue : float — 최근 금액 (원)
            pct : float — 무형자산 내 비중 (%)
        totalIntangible : float — 무형자산 합계 (원)
        totalAssets : float — 총자산 (원)
        intangiblePct : float — 총자산 대비 무형자산 비중 (%)
        goodwillPct : float | None — 영업권 비중 (%)
        trend : str | None — 비중 추세 ("비중 증가"|"비중 감소"|"안정")
        notesDetail : list[dict] | None — 주석 원본

    Guide:
        영업권 비중 50% 초과면 손상차손 리스크 우선 점검.

    When:
        무형자산 비중 큰 기업 (바이오·IT) 이익 질 점검 시점.

    How:
        notes intangibleAsset 항목별 합산 + BS 백업 → 비중·추세 산출.

    Requires:
        BS 다년 + notes intangibleAsset 또는 BS 무형자산·영업권.

    Raises:
        없음 — 결측 시 None.

    Example:
        >>> calcIntangibleAssetDetail(company)
        {'goodwillPct': 35.0, 'trend': '안정'}

    See Also:
        - calcInvestmentPropertyTrend : 투자부동산 추세.

    AIContext:
        영업권 손상은 회계 추정 — 단정 금지, 주석 detail 함께 확인.
    """
    from dartlab.analysis.financial.companyContext import fetchNotesDetail
    from dartlab.core.utils.helpers import parseNumStr

    notesData = fetchNotesDetail(company, ["intangibleAsset"])
    rawRows = notesData.get("intangibleAsset")

    # notes 없으면 BS에서 기본 분해
    bsResult = company.select("BS", ["무형자산", "영업권", "자산총계"])
    bsParsed = toDictBySnakeId(bsResult)
    if bsParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    intRow = bsData.get("무형자산", {})
    gwRow = bsData.get("영업권", {})
    taRow = bsData.get("자산총계", {})

    yCols = annualColsFromPeriods(bsPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
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
                items.append(
                    {"name": item, "latestValue": v, "pct": round(v / totalInt * 100, 1) if totalInt > 0 else 0}
                )
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

    resultDict: dict[str, Any] = {
        "items": items,
        "totalIntangible": totalInt,
        "totalAssets": ta,
        "intangiblePct": round(totalInt / ta * 100, 1) if ta > 0 else 0,
        "goodwillPct": goodwillPct,
        "trend": trend,
    }

    if rawRows:
        resultDict["notesDetail"] = rawRows

    return resultDict


# ── 자산 플래그 ──
