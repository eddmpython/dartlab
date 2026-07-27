"""별도재무제표(OFS) + 금융업 전용 지표 — metrics.py 에서 분리."""

from __future__ import annotations

from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.credit.scoring._metricsArithmetic import _cv, _div, _getRatios, _isQuarterlyFallback, _ttmSum

_toDict = toDictBySnakeId
_annualCols = annualColsFromPeriods


# ═══════════════════════════════════════════════════════════
# 별도재무제표(OFS) 보조 지표 — 지주사/캡티브 금융 보정용
# ═══════════════════════════════════════════════════════════


def calcSeparateMetrics(company) -> dict | None:
    """별도재무제표(OFS) 기반 보조 지표.

    Capabilities:
        company 의 별도재무제표 (OFS) 에서 부채/차입금/EBITDA + 파생 비율 (separateDebtRatio /
        D-EBITDA / Net D-EBITDA / OCF/Sales 등) 산출. 지주사/캡티브 금융의 연결 (CFS) D-EBITDA
        왜곡 보정용.

    연결(CFS) 대비 별도(OFS)의 부채/차입금/EBITDA를 산출.
    지주사/캡티브 금융에서 연결 D/EBITDA 왜곡을 보정하는 데 사용.

    Parameters
    ----------
    company : Company
        DartCompany 또는 EdgarCompany 인스턴스.

    Returns
    -------
    dict | None
        period : str | None — 별도재무제표 기간
        totalAssets : float — 별도 자산총계 (원)
        totalBorrowing : float — 별도 총차입금 (원)
        ebitda : float — 별도 EBITDA (원)
        netDebt : float — 별도 순차입금 (원)
        revenue : float — 별도 매출 (원)
        ocf : float — 별도 영업현금흐름 (원)
        fcf : float | None — 별도 잉여현금흐름 (원)
        separateDebtRatio : float | None — 별도 부채비율 (%)
        separateDebtToEbitda : float | None — 별도 D/EBITDA (배)
        separateNetDebtToEbitda : float | None — 별도 순차입금/EBITDA (배)
        separateBorrowingDep : float | None — 별도 차입금의존도 (%)
        separateOcfToSales : float | None — 별도 OCF/매출 (%)
        separateOcfToDebt : float | None — 별도 OCF/총차입금 (%)

    Raises:
        없음 — OFS 데이터 부재 시 None 반환.

    Example:
        >>> from dartlab.credit.scoring._metricsTrackB import calcSeparateMetrics
        >>> sep = calcSeparateMetrics(Company("005380"))  # 현대차 (캡티브)
        >>> sep["separateDebtToEbitda"]

    Guide:
        지주사/캡티브 회사는 본 함수 결과의 ``separateDebtToEbitda`` 가 연결 대비 크게 우수.
        narrateRepayment / narrateCapitalStructure 가 본 값을 단서로 자동 첨부.

    When:
        ``credit.engine.evaluateCompany`` 가 captive/holding 회사 분기에 본 함수 호출. AI 가
        지주사 답변 시.

    How:
        company._getFinanceBuild("y", "OFS") 추출 → 최신 기간 BS/IS/CF 값 → 파생 비율 산출.

    Requires:
        - L1 raw: 별도재무제표 (OFS) 보유
        - company.companyFinanceBuild 호출 가능

    See Also:
        - ``dartlab.credit.scoring._metricsTrackB.calcFinancialMetrics`` : 금융업 Track B
        - ``dartlab.credit.features._narrativeAxesA.narrateCapitalStructure`` : 본 결과 사용자

    AIContext:
        AI 가 지주사 부채비율 답변 시 별도 vs 연결 차이 인용 필수. ``separateDebtRatio`` 단독
        인용 금지.
    """
    try:
        ofs = company._getFinanceBuild("y", "OFS")
    except (AttributeError, TypeError, FileNotFoundError):
        return None
    if ofs is None:
        return None

    series, periods = ofs
    if not periods:
        return None

    bs = series.get("BS", {})
    is_ = series.get("IS", {})
    cf = series.get("CF", {})
    idx = -1  # 최신 기간

    def _val(data: dict, key: str) -> float | None:
        vals = data.get(key)
        if vals is None or not isinstance(vals, list):
            return None
        return vals[idx] if abs(idx) <= len(vals) else None

    ta = _val(bs, "total_assets")
    tl = _val(bs, "total_liabilities")
    eq = _val(bs, "total_stockholders_equity")
    stb = _val(bs, "shortterm_borrowings") or 0
    ltb = _val(bs, "longterm_borrowings") or 0
    bonds = _val(bs, "bonds_payable") or _val(bs, "debentures") or 0
    cash = _val(bs, "cash_and_cash_equivalents") or 0
    oi = _val(is_, "operating_profit") or 0
    rev = _val(is_, "sales") or _val(is_, "revenue") or 0
    dep = _val(is_, "depreciation") or _val(is_, "depreciation_and_amortisation") or 0
    ocfVal = _val(cf, "operating_cashflow") or _val(cf, "cash_flows_from_operating_activities") or 0
    capexVal = abs(_val(cf, "purchase_of_property_plant_and_equipment") or 0)

    if ta is None or ta == 0:
        return None

    totalBorrowing = stb + ltb + bonds
    ebitda = oi + dep
    netDebt = totalBorrowing - cash if totalBorrowing > 0 else 0
    fcfVal = ocfVal - capexVal if ocfVal else None

    result = {
        "period": periods[idx] if abs(idx) <= len(periods) else None,
        "totalAssets": ta,
        "totalBorrowing": totalBorrowing,
        "ebitda": ebitda,
        "netDebt": netDebt,
        "revenue": rev,
        "ocf": ocfVal,
        "fcf": fcfVal,
        # 별도 지표
        "separateDebtRatio": _div(tl, eq, pct=True) if eq and eq > 0 else None,
        "separateDebtToEbitda": _div(totalBorrowing, ebitda) if ebitda and ebitda > 0 else None,
        "separateNetDebtToEbitda": _div(netDebt, ebitda) if ebitda and ebitda > 0 else None,
        "separateBorrowingDep": _div(totalBorrowing, ta, pct=True) if ta > 0 else None,
        "separateOcfToSales": _div(ocfVal, rev, pct=True) if rev and rev > 0 else None,
        "separateOcfToDebt": _div(ocfVal, totalBorrowing, pct=True) if totalBorrowing > 0 else None,
    }
    return result


# ═══════════════════════════════════════════════════════════
# Track B: 금융업 전용 지표 산출
# ═══════════════════════════════════════════════════════════


def calcFinancialMetrics(company, *, basePeriod: str | None = None) -> dict | None:
    """금융업(은행/보험/증권) 전용 5축 지표 산출.

    Capabilities:
        은행/보험/증권 회사용 5 축 지표 (자기자본비율, ROA, NIM proxy, 충당금비율, cash-to-asset)
        시계열 산출. 일반기업 D-EBITDA/FFO-Debt 미적용 Track B 핵심 함수.

    일반기업용 D/EBITDA, FFO/Debt 대신
    자본비율, ROA, NIM 대리, 충당금 비율 등 금융업 핵심 지표 사용.

    Parameters
    ----------
    company : Company
        DartCompany 또는 EdgarCompany 인스턴스 (금융업).
    basePeriod : str | None
        분석 기준 기간 (예: "2024"). None이면 최신 9개년.

    Returns
    -------
    dict | None
        history : list[dict] — 기간별 금융업 지표 시계열. 각 dict 포함 키:
            period : str — 기간
            totalAssets : float | None — 자산총계 (원)
            equity : float | None — 자본총계 (원)
            netIncome : float | None — 당기순이익 (원)
            operatingIncome : float | None — 영업이익 (원)
            ocf : float | None — 영업활동현금흐름 (원)
            equityRatio : float | None — 자기자본비율 (%)
            roa : float | None — 총자산이익률 (%)
            nimProxy : float | None — NIM 대리 (이자수익/자산) (%)
            provisionRatio : float | None — 충당금비율 (대손상각비/자산) (%)
            cashToAsset : float | None — 현금/자산 비율 (%)
            currentRatio : float | None — 유동비율 (%)
        businessStability : dict — 사업 안정성
            revenueCV : float | None — 영업이익 변동계수 (%)
            roaCV : float | None — ROA 변동계수 (%)
            totalAssets : float | None — 최신 자산총계 (원)
        track : str — "B" (금융업 트랙 식별자)

    Raises:
        없음 — BS/IS 데이터 부재 또는 연도 < 2 면 None.

    Example:
        >>> from dartlab.credit.scoring._metricsTrackB import calcFinancialMetrics
        >>> r = calcFinancialMetrics(Company("105560"))  # KB금융지주
        >>> r["history"][0]["equityRatio"]
        9.8

    Guide:
        BIS 자기자본비율 7~15% 정상. ROA 0.3~1.5% 정상. NIM proxy 1~3%. ``financialTrackBThresholds``
        가 본 함수 산출 metric 에 매핑.

    When:
        ``evaluateCompany`` 가 회사 sector 가 FINANCIALS 일 때 본 함수로 분기.

    How:
        company.select BS/IS/CF → 연간 컬럼 추출 → 자본/이자/충당금 row-wise 계산 → history list
        + businessStability 합성.

    Requires:
        - company.select BS/IS/CF 가능 (DART/EDGAR 금융업 재무제표)

    See Also:
        - ``dartlab.credit.scoring._metricsTrackB.calcSeparateMetrics`` : 별도 보조 지표
        - ``dartlab.credit.features.sectorThresholds.financialTrackBThresholds`` : 임계값

    AIContext:
        AI 답변 시 metric 단독 인용 금지 — BIS 8% 같은 규제 기준 함께 명시. 금융지주 vs 시중은행
        구분 단서 권장.
    """
    bsResult = company.select(
        "BS",
        ["자산총계", "부채총계", "자본총계", "유동자산", "유동부채", "현금및현금성자산", "현금및예치금"],
    )
    bsParsed = _toDict(bsResult)
    if bsParsed is None:
        return None
    bsData, bsPeriods = bsParsed

    isResult = company.select(
        "IS",
        ["이자수익", "금융이익", "금융비용", "4.금융비용", "당기순이익", "대손상각비", "영업이익"],
    )
    isParsed = _toDict(isResult)
    if isParsed is None:
        return None
    isData, _ = isParsed

    cfResult = company.select("CF", ["영업활동현금흐름", "4.금융비용", "금융비용"])
    cfParsed = _toDict(cfResult)
    cfData = cfParsed[0] if cfParsed else {}

    yCols = _annualCols(bsPeriods, basePeriod, 9)
    if len(yCols) < 2:
        return None

    _qMode = _isQuarterlyFallback(yCols)
    _allP = set(bsPeriods)

    # 금융업: 금융이익(순영업수익)을 우선. 이자수익은 부수 항목일 수 있음
    intIncome = isData.get("금융이익", {}) or isData.get("이자수익", {})
    intExpense = isData.get("금융비용", {}) or isData.get("4.금융비용", {})
    ni = isData.get("당기순이익", {})
    provision = isData.get("대손상각비", {})
    oi = isData.get("영업이익", {})
    ta = bsData.get("자산총계", {})
    eq = bsData.get("자본총계", {})
    cash = bsData.get("현금및현금성자산", {}) or bsData.get("현금및예치금", {})
    ca = bsData.get("유동자산", {})
    cl = bsData.get("유동부채", {})
    ocf = cfData.get("영업활동현금흐름", {})
    cfFinCost = cfData.get("4.금융비용", {}) or cfData.get("금융비용", {})

    history = []
    roaList = []
    revList = []

    for col in yCols[:-1]:
        totalAssets = ta.get(col)
        equity = eq.get(col)
        cashVal = cash.get(col)
        curAssets = ca.get(col)
        curLiab = cl.get(col)

        if _qMode:
            intInc = _ttmSum(intIncome, col, _allP)
            _ttmSum(intExpense, col, _allP) or _ttmSum(cfFinCost, col, _allP)
            netIncome = _ttmSum(ni, col, _allP)
            provCharge = _ttmSum(provision, col, _allP)
            opIncome = _ttmSum(oi, col, _allP)
            ocfVal = _ttmSum(ocf, col, _allP)
        else:
            intInc = intIncome.get(col)
            intExpense.get(col) or cfFinCost.get(col)
            netIncome = ni.get(col)
            provCharge = provision.get(col)
            opIncome = oi.get(col)
            ocfVal = ocf.get(col)

        if totalAssets is None or totalAssets == 0:
            continue

        # 축1: 자본적정성
        equityRatio = _div(equity, totalAssets, pct=True)

        # 축2: 수익성
        roa = _div(netIncome, totalAssets, pct=True)
        # NIM 대리: 이자수익/자산 (금융비용 차감 방식은 계정 불일치로 불안정)
        nim = _div(intInc, totalAssets, pct=True) if intInc else None

        # 축3: 자산건전성
        provRatio = _div(abs(provCharge) if provCharge else None, totalAssets, pct=True)

        # 축4: 유동성
        cashToAsset = _div(cashVal, totalAssets, pct=True)
        currentRatio = _div(curAssets, curLiab, pct=True) if curLiab and curLiab > 0 else None

        roaList.append(roa)
        revList.append(opIncome)

        history.append(
            {
                "period": col,
                "totalAssets": totalAssets,
                "equity": equity,
                "netIncome": netIncome,
                "operatingIncome": opIncome,
                "ocf": ocfVal,
                # 축1
                "equityRatio": equityRatio,
                # 축2
                "roa": roa,
                "nimProxy": nim,
                # 축3
                "provisionRatio": provRatio,
                # 축4
                "cashToAsset": cashToAsset,
                "currentRatio": currentRatio,
            }
        )

    if not history:
        return None

    # 축5: 사업안정성 (기존 로직 재사용)
    bizStability = {
        "revenueCV": _cv([r for r in revList if r is not None]),
        "roaCV": _cv([r for r in roaList if r is not None]),
        "totalAssets": history[0].get("totalAssets"),
    }

    return {
        "history": history,
        "businessStability": bizStability,
        "track": "B",
    }
