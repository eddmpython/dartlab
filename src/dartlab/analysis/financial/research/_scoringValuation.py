"""scoring 의 Valuation/DuPont 점수 — Lynch/Buffett/DuPont + AllScores."""

from __future__ import annotations

import math

from dartlab.analysis.financial.research._scoringDescriptive import (
    _latest,
    _latestTwo,
    _round,
    _val,
    calcMagicFormula,
    calcPiotroski,
)
from dartlab.analysis.financial.research.types import (
    DuPontResult,
    LynchFairValue,
    QmjScore,
    QuantScores,
)


def _qmjProfitability(aSeries: dict, ni: float | None, ta: float | None) -> float | None:
    """QMJ 수익성 축. ROE/ROA/GM/CFOA 중 산정 가능한 것의 평균.

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.
    ni, ta : float | None
        순이익, 총자산 최신값.

    Returns
    -------
    float | None
        평균 수익성. 산정 가능한 지표가 없으면 None.
    """
    eq = _latest(aSeries, "BS", "total_stockholders_equity")
    sales = _latest(aSeries, "IS", "sales")
    gp = _latest(aSeries, "IS", "gross_profit")
    ocf = _latest(aSeries, "CF", "operating_cashflow")

    roe = ni / eq if ni is not None and eq and eq > 0 else None
    roa = ni / ta if ni is not None and ta and ta > 0 else None
    gm = gp / sales if gp is not None and sales and sales > 0 else None
    cfoa = ocf / ta if ocf is not None and ta and ta > 0 else None

    profScores = [x for x in [roe, roa, gm, cfoa] if x is not None]
    return sum(profScores) / len(profScores) if profScores else None


def _qmjGrowth(aSeries: dict) -> float | None:
    """QMJ 성장 축. 유효 매출 시계열의 CAGR.

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.

    Returns
    -------
    float | None
        CAGR. 유효 매출이 3 개 미만이면 None.
    """
    salesList = aSeries.get("IS", {}).get("sales", [])
    validSales = [v for v in salesList if v is not None and v > 0]
    if len(validSales) < 3:
        return None
    n = len(validSales) - 1
    return ((validSales[-1] / validSales[0]) ** (1 / n) - 1) if n > 0 else None


def _qmjSafety(aSeries: dict, ta: float | None) -> float | None:
    """QMJ 안전성 축. 부채비율 역수와 정규화 유동비율의 평균.

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.
    ta : float | None
        총자산 최신값.

    Returns
    -------
    float | None
        안전성 점수. 산정 가능한 지표가 없으면 None.
    """
    tl = _latest(aSeries, "BS", "total_liabilities")
    cl = _latest(aSeries, "BS", "current_liabilities")
    ca = _latest(aSeries, "BS", "current_assets")
    debtRatio = tl / ta if tl is not None and ta and ta > 0 else None
    crRatio = ca / cl if ca is not None and cl and cl > 0 else None
    safetyScores = []
    if debtRatio is not None:
        safetyScores.append(1 - debtRatio)  # 낮을수록 안전
    if crRatio is not None:
        safetyScores.append(min(crRatio / 2, 1))  # 정규화
    return sum(safetyScores) / len(safetyScores) if safetyScores else None


def _qmjPayout(aSeries: dict, ni: float | None) -> float | None:
    """QMJ 배당 축. 배당지급액 절대값 / 순이익.

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.
    ni : float | None
        순이익 최신값.

    Returns
    -------
    float | None
        배당성향. 순이익이 양수가 아니면 None.
    """
    div = _latest(aSeries, "CF", "dividends_paid")
    if div is not None and ni is not None and ni > 0:
        return abs(div) / ni
    return None


def calcQmj(
    aSeries: dict[str, dict[str, list[float | None]]],
    aYears: list[str],
) -> QmjScore:
    """AQR Quality Minus Junk 4-pillar.

    Capabilities:
        - profitability/growth/safety/payout 4 축 통합 quality 점수.

    Guide:
        AQR 2013 Asness·Frazzini·Pedersen QMJ 단순화. composite = 4 축 평균.

    When:
        팩터 모델·smart-beta 노출 평가 시.

    How:
        profitability = ROE/ROA/GM/CFOA 평균. safety = 1-debtRatio + min(CR/2, 1) 평균. payout = abs(div)/NI.

    Requires:
        aSeries IS net_profit/sales/gross_profit · BS total_assets/equity/liabilities/current_assets/current_liabilities · CF operating_cashflow/dividends_paid.

    Raises:
        없음. 데이터 결측 시 해당 pillar None.

    Parameters:
        aSeries : dict
            연간 재무 시계열.
        aYears : list[str]
            연도 목록.

    Returns:
        QmjScore
            profitability : float | None — 수익성 평균 (비율)
            growth : float | None — 매출 CAGR (비율)
            safety : float | None — 안전성 점수 (0~1)
            payout : float | None — 배당성향 (비율)
            composite : float | None — 4-pillar 평균 (비율)

    Example:
        >>> calcQmj(aSeries, ["2022", "2023", "2024"])
        QmjScore(profitability=0.18, growth=0.07, safety=0.6, payout=0.3, composite=0.29)

    See Also:
        - calcAllScores : 통합 진입점.

    AIContext:
        QMJ composite 가 높은 종목은 quality 노출 강함.
    """
    ni = _latest(aSeries, "IS", "net_profit")
    ta = _latest(aSeries, "BS", "total_assets")

    profitability = _qmjProfitability(aSeries, ni, ta)
    growth = _qmjGrowth(aSeries)
    safety = _qmjSafety(aSeries, ta)
    payout = _qmjPayout(aSeries, ni)

    # composite
    pillars = [profitability, growth, safety, payout]
    validPillars = [p for p in pillars if p is not None]
    composite = sum(validPillars) / len(validPillars) if validPillars else None

    return QmjScore(
        profitability=_round(profitability),
        growth=_round(growth),
        safety=_round(safety),
        payout=_round(payout),
        composite=_round(composite),
    )


# ══════════════════════════════════════
# Lynch Fair Value
# ══════════════════════════════════════


def calcLynchFairValue(
    aSeries: dict[str, dict[str, list[float | None]]],
    currentPrice: float | None = None,
    sharesOutstanding: float | None = None,
) -> LynchFairValue:
    """Peter Lynch: Fair Value = EPS Growth Rate * EPS.

    Capabilities:
        - Lynch 적정가 + PEG + 저평가/적정/고평가 시그널.

    Guide:
        성장률(%) × EPS = fair value. PER/growth = PEG (1 미만 저평가 통상해석).

    When:
        성장주 합리적 가격대 판단 시.

    How:
        validNi 첫/끝 → CAGR(%) × latest EPS. currentPrice/fairValue ratio < 0.8 / > 1.2 시 신호.

    Requires:
        aSeries IS net_profit ≥ 3 시점 + sharesOutstanding > 0.

    Raises:
        없음. 데이터 부족 시 빈 LynchFairValue.

    Parameters:
        aSeries : dict
            연간 재무 시계열.
        currentPrice : float | None
            현재 주가 (원 또는 달러).
        sharesOutstanding : float | None
            발행주식수 (주).

    Returns:
        LynchFairValue
            earningsGrowthRate : float | None — EPS 성장률 (%)
            fairValue : float | None — Lynch 적정가 (원 또는 달러)
            currentPrice : float | None — 현재 주가
            pegRatio : float | None — PEG 비율 (배)
            signal : str | None — ``"undervalued"`` | ``"fair"`` | ``"overvalued"``

    Example:
        >>> calcLynchFairValue(aSeries, currentPrice=70000, sharesOutstanding=1e8)
        LynchFairValue(earningsGrowthRate=15, fairValue=90000, ...)

    See Also:
        - calcAllScores : 통합 진입점.

    AIContext:
        성장률 = fair PER 가정. 적자/마이너스 성장 시 적용 불가.
    """
    niList = aSeries.get("IS", {}).get("net_profit", [])
    validNi = [(i, v) for i, v in enumerate(niList) if v is not None and v > 0]

    if len(validNi) < 3 or not sharesOutstanding or sharesOutstanding <= 0:
        return LynchFairValue()

    latestNi = validNi[-1][1]
    oldestNi = validNi[0][1]
    nYears = validNi[-1][0] - validNi[0][0]
    if nYears <= 0 or oldestNi <= 0:
        return LynchFairValue()

    growthRate = ((latestNi / oldestNi) ** (1 / nYears) - 1) * 100
    eps = latestNi / sharesOutstanding
    fairValue = growthRate * eps if growthRate > 0 else None

    pegRatio = None
    if currentPrice and eps > 0 and growthRate > 0:
        per = currentPrice / eps
        pegRatio = per / growthRate

    signal = None
    if fairValue is not None and currentPrice:
        ratio = currentPrice / fairValue
        if ratio < 0.8:
            signal = "undervalued"
        elif ratio > 1.2:
            signal = "overvalued"
        else:
            signal = "fair"

    return LynchFairValue(
        earningsGrowthRate=_round(growthRate),
        fairValue=_round(fairValue),
        currentPrice=currentPrice,
        pegRatio=_round(pegRatio),
        signal=signal,
    )


# ══════════════════════════════════════
# Buffett Owner Earnings
# ══════════════════════════════════════


def calcBuffettOwnerEarnings(
    aSeries: dict[str, dict[str, list[float | None]]],
) -> float | None:
    """Buffett Owner Earnings = NI + D&A - maintenance CAPEX.

    Capabilities:
        - 회계 NI 보정 → 실제 주주에게 환원 가능한 현금흐름 산출.

    Guide:
        OCF - maintenance CAPEX (CAPEX 의 70% 가정). Berkshire Hathaway 1986 letter 정의 근사.

    When:
        밸류에이션 분모 (EV/OE) · DCF 자유현금흐름 대용.

    How:
        ocf - abs(capex) × 0.7. Maintenance vs growth CAPEX 분리 불가능해 휴리스틱.

    Requires:
        aSeries CF operating_cashflow + purchase_of_property_plant_and_equipment.

    Raises:
        없음. ni 또는 ocf None 시 None.

    Parameters:
        aSeries : dict
            연간 재무 시계열.

    Returns:
        float | None
            Owner Earnings (원 또는 달러). 데이터 부족 시 None.

    Example:
        >>> calcBuffettOwnerEarnings(aSeries)
        12300000000

    See Also:
        - calcAllScores : 통합 진입점.

    AIContext:
        OE > NI = 회계 보수적·CAPEX 적은 비즈니스.
    """
    ni = _latest(aSeries, "IS", "net_profit")
    # depreciation 근사: operating_profit - ebit가 아니라 CF에서 D&A 추출
    ocf = _latest(aSeries, "CF", "operating_cashflow")
    capex = _latest(aSeries, "CF", "purchase_of_property_plant_and_equipment")

    if ni is None or ocf is None:
        return None

    # Owner Earnings ≈ OCF - maintenance CAPEX
    # CAPEX는 음수일 수 있음
    capexAbs = abs(capex) if capex is not None else 0
    return _round(ocf - capexAbs * 0.7)  # 유지보수 CAPEX ≈ 70%


# ══════════════════════════════════════
# DuPont 3-Factor
# ══════════════════════════════════════


def _duPontFactors(
    ni: float | None,
    s: float | None,
    ta: float | None,
    eq: float | None,
    op: float | None,
    ebt: float | None,
    cl: float | None,
    cash: float | None,
) -> dict[str, float | None]:
    """한 해의 DuPont 3 요소 + 5-factor 확장 + ROIC.

    Parameters
    ----------
    ni, s, ta, eq : float | None
        순이익, 매출, 총자산, 자본.
    op, ebt : float | None
        영업이익, 세전이익.
    cl, cash : float | None
        유동부채, 현금 (ROIC 의 투하자본 근사용).

    Returns
    -------
    dict[str, float | None]
        margin / turnover / leverage / roe / taxBurden / interestBurden / opMargin / roic.
    """
    # ROIC = NOPAT / IC, IC = TA - CL - Cash (근사)
    roic = None
    if op is not None and ta is not None:
        ic = ta - (cl or 0) - (cash or 0)
        if ic > 0:
            nopat = op * (1 - 0.22)  # 법인세율 22% 근사
            roic = nopat / ic

    return {
        "margin": ni / s if ni is not None and s and s > 0 else None,
        "turnover": s / ta if s is not None and ta and ta > 0 else None,
        "leverage": ta / eq if ta is not None and eq and eq > 0 else None,
        "roe": ni / eq if ni is not None and eq and eq > 0 else None,
        # 5-factor: taxBurden = NI/EBT, interestBurden = EBT/EBIT(=OP)
        "taxBurden": ni / ebt if ni is not None and ebt is not None and ebt != 0 else None,
        "interestBurden": ebt / op if ebt is not None and op is not None and op != 0 else None,
        "opMargin": op / s if op is not None and s and s > 0 else None,
        "roic": roic,
    }


def calcDuPont(
    aSeries: dict[str, dict[str, list[float | None]]],
    aYears: list[str],
) -> DuPontResult:
    """DuPont 5-factor 분해: ROE = 세금부담 * 이자부담 * OPM * 회전율 * 레버리지.

    Capabilities:
        - 최근 5Y ROE 5 인자 분해 + driver (margin/turnover/leverage) 식별.

    Guide:
        3-factor (margin × turnover × leverage) + 5-factor (taxBurden × interestBurden × OPM × turnover × leverage) 동시 산출.

    When:
        ROE 변화 원인 분석·동종업계 비교 시.

    How:
        각 인자 변동계수(CV) 계산 → 최대 CV 가 driver. 모두 0 이면 balanced.

    Requires:
        aSeries IS net_profit/sales/operating_profit/income_before_tax · BS total_assets/equity/current_liabilities/cash.

    Raises:
        없음. 데이터 결측 시 해당 칸 None.

    Parameters:
        aSeries : dict
            연간 재무 시계열.
        aYears : list[str]
            연도 목록.

    Returns:
        DuPontResult
            netMargin : list[float | None] — 순이익률 (비율)
            assetTurnover : list[float | None] — 총자산회전율 (배)
            equityMultiplier : list[float | None] — 자기자본승수 (배)
            roe : list[float | None] — 자기자본이익률 (비율)
            periods : list[str] — 연도 목록
            driver : str — ROE 변동 주요 동인 (``"margin"`` | ``"turnover"`` | ``"leverage"`` | ``"balanced"``)
            taxBurden : list[float | None] — 세금부담률 (비율)
            interestBurden : list[float | None] — 이자부담률 (비율)
            operatingMargin : list[float | None] — 영업이익률 (비율)
            roic : list[float | None] — 투하자본수익률 (비율)

    Example:
        >>> calcDuPont(aSeries, ["2020", "2021", "2022", "2023", "2024"])
        DuPontResult(roe=[...], driver="margin", ...)

    See Also:
        - calcAllScores : 통합 진입점.

    AIContext:
        ROE 개선이 마진 vs 회전 vs 레버리지 어디서 왔는지 설명 인용.
    """
    niList = aSeries.get("IS", {}).get("net_profit", [])
    salesList = aSeries.get("IS", {}).get("sales", [])
    taList = aSeries.get("BS", {}).get("total_assets", [])
    eqList = aSeries.get("BS", {}).get("total_stockholders_equity", []) or aSeries.get("BS", {}).get("total_equity", [])
    opList = aSeries.get("IS", {}).get("operating_profit", [])
    ebtList = aSeries.get("IS", {}).get("income_before_tax", []) or aSeries.get("IS", {}).get("profit_before_tax", [])
    clList = aSeries.get("BS", {}).get("current_liabilities", [])
    cashList = aSeries.get("BS", {}).get("cash_and_cash_equivalents", [])

    margins: list[float | None] = []
    turnovers: list[float | None] = []
    leverages: list[float | None] = []
    roes: list[float | None] = []
    periods: list[str] = []
    # 5-factor 확장
    taxBurdens: list[float | None] = []
    interestBurdens: list[float | None] = []
    opMargins: list[float | None] = []
    roicList: list[float | None] = []

    n = min(len(niList), len(salesList), len(taList), len(eqList), len(aYears))
    start = max(0, n - 5)  # 최근 5년
    for i in range(start, n):
        op = opList[i] if i < len(opList) else None
        ebt = ebtList[i] if i < len(ebtList) else None
        cl = clList[i] if i < len(clList) else None
        cash = cashList[i] if i < len(cashList) else None

        f = _duPontFactors(niList[i], salesList[i], taList[i], eqList[i], op, ebt, cl, cash)

        margins.append(_round(f["margin"]))
        turnovers.append(_round(f["turnover"]))
        leverages.append(_round(f["leverage"]))
        roes.append(_round(f["roe"]))
        taxBurdens.append(_round(f["taxBurden"]))
        interestBurdens.append(_round(f["interestBurden"]))
        opMargins.append(_round(f["opMargin"]))
        roicList.append(_round(f["roic"]))
        periods.append(aYears[i])

    driver = _identifyDriver(margins, turnovers, leverages)

    return DuPontResult(
        netMargin=margins,
        assetTurnover=turnovers,
        equityMultiplier=leverages,
        roe=roes,
        periods=periods,
        driver=driver,
        taxBurden=taxBurdens,
        interestBurden=interestBurdens,
        operatingMargin=opMargins,
        roic=roicList,
    )


def _identifyDriver(
    margins: list[float | None],
    turnovers: list[float | None],
    leverages: list[float | None],
) -> str:
    """ROE 변동의 주요 동인 식별.

    Returns
    -------
    str
        ``"margin"`` | ``"turnover"`` | ``"leverage"`` | ``"balanced"``.
    """

    def _cv(vals: list[float | None]) -> float:
        """변동계수(CV) 산출 — 표준편차 / 평균."""
        valid = [v for v in vals if v is not None]
        if len(valid) < 2:
            return 0
        mean = sum(valid) / len(valid)
        if mean == 0:
            return 0
        variance = sum((v - mean) ** 2 for v in valid) / len(valid)
        return math.sqrt(variance) / abs(mean)

    cvMargin = _cv(margins)
    cvTurnover = _cv(turnovers)
    cvLeverage = _cv(leverages)

    maxCv = max(cvMargin, cvTurnover, cvLeverage)
    if maxCv == 0:
        return "balanced"
    if cvMargin == maxCv:
        return "margin"
    if cvTurnover == maxCv:
        return "turnover"
    return "leverage"


# ══════════════════════════════════════
# 종합
# ══════════════════════════════════════


def calcAllScores(
    aSeries: dict[str, dict[str, list[float | None]]],
    aYears: list[str],
    *,
    currentPrice: float | None = None,
    sharesOutstanding: float | None = None,
) -> QuantScores:
    """모든 정량 스코어 한 번에 계산.

    Requires:
        aSeries 가 IS/BS/CF snake_id 시계열 dict, aYears 연도 list.

    Raises:
        없음. 하위 계산자 결측 시 dataclass 필드 None.

    Returns:
        QuantScores
            piotroski : PiotroskiScore — F-Score (0~9점)
            magicFormula : MagicFormulaScore — ROIC + Earnings Yield
            qmj : QmjScore — Quality Minus Junk 4-pillar
            lynchFairValue : LynchFairValue — Lynch 적정가
            buffettOwnerEarnings : float | None — Owner Earnings (원 또는 달러)
            dupont : DuPontResult — DuPont 5-factor 분해

    Example:
        >>> calcAllScores(aSeries, aYears, currentPrice=70000, sharesOutstanding=1e8)
        QuantScores(piotroski=..., magicFormula=..., qmj=..., ...)
    """
    return QuantScores(
        piotroski=calcPiotroski(aSeries),
        magicFormula=calcMagicFormula(aSeries, currentPrice, sharesOutstanding),
        qmj=calcQmj(aSeries, aYears),
        lynchFairValue=calcLynchFairValue(aSeries, currentPrice, sharesOutstanding),
        buffettOwnerEarnings=calcBuffettOwnerEarnings(aSeries),
        dupont=calcDuPont(aSeries, aYears),
    )
