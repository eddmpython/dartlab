"""Richardson 발생액 + 영업외 분해 — calcRichardsonAccrual · calcNonOperatingBreakdown."""

from __future__ import annotations

from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get
from dartlab.core.utils.safe import getFirst

_MAX_YEARS = 8

# 영업외손익 계정의 조회 순서. snakeId 가 먼저, 회사마다 다른 원문 계정명이 뒤다.
_NONOP_KEYS = {
    "op": ("operating_profit", "영업이익"),
    "finInc": ("finance_income", "금융이익", "금융수익"),
    "finCost": ("finance_costs", "금융비용", "금융원가"),
    "assoc": ("share_of_profit_of_associates", "지분법관련손익", "지분법이익", "지분법손익"),
    "otherInc": ("other_income", "기타수익"),
    "otherExp": ("other_expenses", "기타비용"),
    "pt": ("profit_before_tax", "법인세비용차감전순이익", "법인세차감전순이익"),
}


@memoizedCalc
def calcRichardsonAccrual(company, *, basePeriod: str | None = None) -> dict | None:
    """Richardson et al. (2005) 3계층 발생액 분해.

    BS 변동 기반으로 발생액을 운전자본/비유동영업/금융으로 분리.
    신뢰도가 낮은 LTOACC가 클수록 이익 지속성이 낮다.

    WCACC  = (delta_CA - delta_Cash) - (delta_CL - delta_STD)  신뢰도 높음
    LTOACC = delta_NCOA - delta_NCOL                            신뢰도 낮음
    FINACC = delta_STI + delta_LTI - delta_LTD - delta_PSTK    중간

    학술근거: Richardson, Sloan, Soliman, Tuna (2005).

    Returns
    -------
    dict
        history : list[dict] — 기간별 3계층 발생액 시계열
            period : str — 회계연도
            wcacc : float | None — 운전자본 발생액/총자산 (%)
            ltoacc : float | None — 비유동영업 발생액/총자산 (%)
            finacc : float | None — 금융 발생액/총자산 (%)
            totalAccrual : float | None — 총발생액/총자산 (%)
            reliabilityScore : str | None — 이익 신뢰도 (high/medium/low)

    Capabilities:
        - BS 변동 기반 3계층 발생액 분해 (WCACC/LTOACC/FINACC)
        - reliabilityScore (high/medium/low) 분류

    Guide:
        Richardson et al. 2005 표준. LTOACC 가 클수록 이익 지속성 낮음 → 이익 품질 우려.

    When:
        Earnings quality 정밀 진단 + AI 발생액 분해 답변.

    How:
        BS 시계열 → 운전자본/비유동영업/금융 발생액 차분.

    Requires:
        BS 시계열 ≥ 2 년.

    Raises:
        없음 — 데이터 부재 시 None.

    Example:
        >>> calcRichardsonAccrual(company)["history"][-1]["reliabilityScore"]
        'medium'

    See Also:
        - calcSloanAccruals : 단순 Sloan
        - calcBeneishTimeline : 8 변수 Beneish

    AIContext:
        "이익 품질 정밀 진단" 답변 시 LTOACC + reliabilityScore 인용.
    """
    bsResult = company.select(
        "BS",
        [
            "유동자산",
            "비유동자산",
            "유동부채",
            "비유동부채",
            "현금및현금성자산",
            "단기차입금",
            "장기차입금",
            "차입금단기",
            "long_term_borrowings",
            "short_term_borrowings",
            "차입부채",
            "장기차입부채",
            "유동성장기차입금",
            "사채",
            "자산총계",
        ],
    )

    bsParsed = toDictBySnakeId(bsResult)
    if bsParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    caRow = bsData.get("current_assets", {})
    ncaRow = bsData.get("noncurrent_assets", {})
    clRow = bsData.get("current_liabilities", {})
    nclRow = bsData.get("noncurrent_liabilities", {})
    cashRow = bsData.get("cash_and_cash_equivalents", {})
    stRow = bsData.get("shortterm_borrowings", {})
    ltRow = bsData.get("longterm_borrowings", {})
    unifiedBorrowRow = bsData.get("borrowings", {})
    bondRow = bsData.get("debentures", {})
    taRow = bsData.get("total_assets", {})

    if not stRow and not ltRow and unifiedBorrowRow:
        stRow = unifiedBorrowRow

    yCols = annualColsFromPeriods(bsPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    for i in range(len(yCols) - 1):
        col = yCols[i]
        prevCol = yCols[i + 1]

        dCA = _get(caRow, col) - _get(caRow, prevCol)
        dCash = _get(cashRow, col) - _get(cashRow, prevCol)
        dCL = _get(clRow, col) - _get(clRow, prevCol)
        dSTD = _get(stRow, col) - _get(stRow, prevCol)
        dNCA = _get(ncaRow, col) - _get(ncaRow, prevCol)
        dNCL = _get(nclRow, col) - _get(nclRow, prevCol)
        dLTD = (_get(ltRow, col) + _get(bondRow, col)) - (_get(ltRow, prevCol) + _get(bondRow, prevCol))

        wcacc = (dCA - dCash) - (dCL - dSTD)
        ltoacc = dNCA - dNCL
        finacc = -dCash + dSTD + dLTD

        totalAccrual = wcacc + ltoacc + finacc
        avgTA = (_get(taRow, col) + _get(taRow, prevCol)) / 2

        wcaccNorm = round(wcacc / avgTA * 100, 2) if avgTA > 0 else None
        ltoaccNorm = round(ltoacc / avgTA * 100, 2) if avgTA > 0 else None
        finaccNorm = round(finacc / avgTA * 100, 2) if avgTA > 0 else None
        totalNorm = round(totalAccrual / avgTA * 100, 2) if avgTA > 0 else None

        if totalAccrual != 0 and avgTA > 0:
            ltoShare = (
                abs(ltoacc) / (abs(wcacc) + abs(ltoacc) + abs(finacc))
                if (abs(wcacc) + abs(ltoacc) + abs(finacc)) > 0
                else 0
            )
            reliability = "low" if ltoShare > 0.5 else "high" if ltoShare < 0.2 else "medium"
        else:
            reliability = None

        history.append(
            {
                "period": col,
                "wcacc": wcaccNorm,
                "ltoacc": ltoaccNorm,
                "finacc": finaccNorm,
                "totalAccrual": totalNorm,
                "reliabilityScore": reliability,
            }
        )

    return {"history": history} if history else None


@memoizedCalc
def calcNonOperatingBreakdown(company, *, basePeriod: str | None = None) -> dict | None:
    """영업외손익 항목별 분해 — 영업이익과 세전이익 사이의 갭.

    금융이익/비용, 지분법손익, 기타수익/비용을 개별 추적.
    영업외가 영업이익의 30% 이상이면 영업만으로 기업 판단 불가.

    Returns
    -------
    dict
        history : list[dict] — 기간별 영업외손익 분해 시계열
            period : str — 회계연도
            opIncome : float — 영업이익 (원)
            finIncome : float — 금융이익 (원)
            finCost : float — 금융비용 (원)
            netFinance : float — 순금융손익 (원)
            associateIncome : float — 지분법손익 (원)
            otherIncome : float — 기타수익 (원)
            otherExpense : float — 기타비용 (원)
            nonOpTotal : float | None — 영업외손익 합계 (원)
            nonOpRatio : float | None — 영업외/영업이익 비율 (%)
        notesDetail : dict | None — 관계기업 투자 주석 (있는 경우)

    Capabilities:
        - IS 영업외 항목 (금융이익/비용/지분법/기타) 시계열 분해 + 영업외 비중 산출
        - notesDetail 로 관계기업 투자 주석 보강

    Guide:
        영업외 비중이 영업이익 대비 30% 이상 = 이익 품질 저하 (영업 본업 외 의존).

    When:
        영업외 비중 분석 + AI "이익이 영업에서 나왔나" 답변.

    How:
        IS snakeId 추출 → 금융/지분법/기타 계산.

    Requires:
        IS 시계열 가용.

    Raises:
        없음.

    Example:
        >>> calcNonOperatingBreakdown(company)["history"][-1]["nonOpRatio"]
        15.2

    See Also:
        - calcRichardsonAccrual : 발생액 분해
        - earningsQuality.calcSloanAccruals

    AIContext:
        "이익이 본업에서" 답변 시 nonOpRatio 인용.
    """
    isResult = company.select(
        "IS",
        ["영업이익", "금융이익", "금융비용", "지분법관련손익", "기타수익", "기타비용", "법인세차감전순이익"],
    )

    isParsed = toDictBySnakeId(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed

    yCols = annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    # select 결과는 snakeId 와 원문 계정명을 함께 key 로 준다. 계정명은 회사마다 달라
    # ('법인세비용차감전순이익' 과 '법인세차감전순이익') snakeId 를 먼저 본다. 세전이익을
    # 못 찾고 0 으로 두면 영업외 합계가 -영업이익, 비율이 100% 로 나온다.
    history = []
    for col in yCols:
        op = getFirst(isData, list(_NONOP_KEYS["op"]), col)
        finInc = getFirst(isData, list(_NONOP_KEYS["finInc"]), col)
        finCost = getFirst(isData, list(_NONOP_KEYS["finCost"]), col)
        assoc = getFirst(isData, list(_NONOP_KEYS["assoc"]), col)
        otherInc = getFirst(isData, list(_NONOP_KEYS["otherInc"]), col)
        otherExp = getFirst(isData, list(_NONOP_KEYS["otherExp"]), col)
        pt = getFirst(isData, list(_NONOP_KEYS["pt"]), col, default=None)

        netFinance = finInc - finCost
        nonOpTotal = pt - op if op != 0 and pt is not None else None
        nonOpRatio = round(abs(nonOpTotal) / abs(op) * 100, 1) if op != 0 and nonOpTotal is not None else None

        history.append(
            {
                "period": col,
                "opIncome": op,
                "finIncome": finInc,
                "finCost": finCost,
                "netFinance": netFinance,
                "associateIncome": assoc,
                "otherIncome": otherInc,
                "otherExpense": otherExp,
                "nonOpTotal": nonOpTotal,
                "nonOpRatio": nonOpRatio,
            }
        )

    if not history:
        return None

    result: dict = {"history": history}

    from dartlab.analysis.financial.companyContext import fetchNotesDetail

    notesDetail = fetchNotesDetail(company, ["affiliates"])
    if notesDetail:
        result["notesDetail"] = notesDetail

    return result
