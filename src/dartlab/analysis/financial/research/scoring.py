"""정량 스코어링 프레임워크.

Piotroski F-Score, Magic Formula, QMJ, Lynch Fair Value,
Buffett Owner Earnings, DuPont 3-factor.
모든 함수는 연간 시계열(buildAnnual 결과)을 입력으로 받는다.
"""

from __future__ import annotations

import math

from dartlab.analysis.financial.research.types import (
    DuPontResult,
    LynchFairValue,
    MagicFormulaScore,
    PiotroskiScore,
    QmjScore,
    QuantScores,
)


def _val(series: dict, sjDiv: str, snakeId: str, idx: int) -> float | None:
    """시계열에서 특정 인덱스 값."""
    vals = series.get(sjDiv, {}).get(snakeId, [])
    if 0 <= idx < len(vals):
        return vals[idx]
    return None


def _latest(series: dict, sjDiv: str, snakeId: str) -> float | None:
    """최신 non-null 값."""
    vals = series.get(sjDiv, {}).get(snakeId, [])
    for v in reversed(vals):
        if v is not None:
            return v
    return None


def _latestTwo(series: dict, sjDiv: str, snakeId: str) -> tuple[float | None, float | None]:
    """최근 2개 non-null (latest, prev)."""
    vals = series.get(sjDiv, {}).get(snakeId, [])
    found: list[float] = []
    for v in reversed(vals):
        if v is not None:
            found.append(v)
            if len(found) == 2:
                break
    if len(found) == 2:
        return found[0], found[1]
    if len(found) == 1:
        return found[0], None
    return None, None


# ══════════════════════════════════════
# Piotroski F-Score (0-9)
# ══════════════════════════════════════


def calcPiotroski(
    aSeries: dict[str, dict[str, list[float | None]]],
) -> PiotroskiScore:
    """Piotroski F-Score 9-signal."""
    components: dict[str, bool] = {}

    # --- 수익성 (4 signals) ---
    ni = _latest(aSeries, "IS", "net_profit")
    ta = _latest(aSeries, "BS", "total_assets")
    taPrev = _latestTwo(aSeries, "BS", "total_assets")[1]
    ocf = _latest(aSeries, "CF", "operating_cashflow")

    roa = ni / ta if ni is not None and ta and ta > 0 else None
    roaPrev = None
    niPrev = _latestTwo(aSeries, "IS", "net_profit")[1]
    if niPrev is not None and taPrev and taPrev > 0:
        roaPrev = niPrev / taPrev

    # F1: ROA > 0
    components["roaPositive"] = roa is not None and roa > 0
    # F2: Operating CF > 0
    components["ocfPositive"] = ocf is not None and ocf > 0
    # F3: ROA increasing
    components["roaIncreasing"] = roa is not None and roaPrev is not None and roa > roaPrev
    # F4: CF > NI (accrual quality)
    components["cfGtNi"] = ocf is not None and ni is not None and ocf > ni

    # --- 건전성 (3 signals) ---
    ltd = _latest(aSeries, "BS", "long_term_borrowings")
    ltdPrev = _latestTwo(aSeries, "BS", "long_term_borrowings")[1]
    # fallback: total_liabilities
    if ltd is None:
        ltd = _latest(aSeries, "BS", "total_liabilities")
        ltdPrev = _latestTwo(aSeries, "BS", "total_liabilities")[1]

    ca = _latest(aSeries, "BS", "current_assets")
    cl = _latest(aSeries, "BS", "current_liabilities")
    caPrev = _latestTwo(aSeries, "BS", "current_assets")[1]
    clPrev = _latestTwo(aSeries, "BS", "current_liabilities")[1]

    cr = ca / cl if ca is not None and cl and cl > 0 else None
    crPrev = caPrev / clPrev if caPrev is not None and clPrev and clPrev > 0 else None

    # F5: Long-term debt decreasing
    components["debtDecreasing"] = ltd is not None and ltdPrev is not None and ltd <= ltdPrev
    # F6: Current ratio increasing
    components["currentRatioUp"] = cr is not None and crPrev is not None and cr > crPrev
    # F7: No new shares issued (equity not diluted)
    eq = _latest(aSeries, "BS", "total_stockholders_equity")
    eqPrev = _latestTwo(aSeries, "BS", "total_stockholders_equity")[1]
    shares = _latest(aSeries, "BS", "issued_shares")
    sharesPrev = _latestTwo(aSeries, "BS", "issued_shares")[1]
    if shares is not None and sharesPrev is not None:
        components["noNewShares"] = shares <= sharesPrev
    elif eq is not None and eqPrev is not None:
        # 발행주식수 없으면 자본 변동으로 근사
        components["noNewShares"] = True  # conservative
    else:
        components["noNewShares"] = True

    # --- 효율성 (2 signals) ---
    gp = _latest(aSeries, "IS", "gross_profit")
    gpPrev = _latestTwo(aSeries, "IS", "gross_profit")[1]
    sales = _latest(aSeries, "IS", "sales")
    salesPrev = _latestTwo(aSeries, "IS", "sales")[1]

    gm = gp / sales if gp is not None and sales and sales > 0 else None
    gmPrev = gpPrev / salesPrev if gpPrev is not None and salesPrev and salesPrev > 0 else None

    # F8: Gross margin increasing
    components["grossMarginUp"] = gm is not None and gmPrev is not None and gm > gmPrev
    # F9: Asset turnover increasing
    at = sales / ta if sales is not None and ta and ta > 0 else None
    atPrev = salesPrev / taPrev if salesPrev is not None and taPrev and taPrev > 0 else None
    components["assetTurnoverUp"] = at is not None and atPrev is not None and at > atPrev

    total = sum(1 for v in components.values() if v)
    if total >= 7:
        interp = "strong"
    elif total >= 4:
        interp = "moderate"
    else:
        interp = "weak"

    return PiotroskiScore(total=total, components=components, interpretation=interp)


# ══════════════════════════════════════
# Magic Formula (Greenblatt)
# ══════════════════════════════════════


def calcMagicFormula(
    aSeries: dict[str, dict[str, list[float | None]]],
    currentPrice: float | None = None,
    sharesOutstanding: float | None = None,
) -> MagicFormulaScore:
    """ROIC + Earnings Yield."""
    op = _latest(aSeries, "IS", "operating_profit")
    ta = _latest(aSeries, "BS", "total_assets")
    ca = _latest(aSeries, "BS", "current_assets")
    cl = _latest(aSeries, "BS", "current_liabilities")
    cash = _latest(aSeries, "BS", "cash_and_cash_equivalents")

    # ROIC = EBIT / (Net Working Capital + Net Fixed Assets)
    # 근사: ROIC = operating_profit / (total_assets - current_liabilities - cash)
    roic = None
    if op is not None and ta is not None:
        investedCapital = ta - (cl or 0) - (cash or 0)
        if investedCapital > 0:
            roic = (op / investedCapital) * 100

    # Earnings Yield = EBIT / EV
    # 근사: EV = market_cap + debt - cash
    ey = None
    if op is not None and currentPrice and sharesOutstanding:
        marketCap = currentPrice * sharesOutstanding
        debt = _latest(aSeries, "BS", "total_liabilities") or 0
        ev = marketCap + debt - (cash or 0)
        if ev > 0:
            ey = (op / ev) * 100

    return MagicFormulaScore(roic=_round(roic), earningsYield=_round(ey))


# ══════════════════════════════════════
# QMJ (Quality Minus Junk)
# ══════════════════════════════════════


def calcQmj(
    aSeries: dict[str, dict[str, list[float | None]]],
    aYears: list[str],
) -> QmjScore:
    """AQR Quality Minus Junk 4-pillar."""
    # --- Profitability ---
    ni = _latest(aSeries, "IS", "net_profit")
    eq = _latest(aSeries, "BS", "total_stockholders_equity")
    ta = _latest(aSeries, "BS", "total_assets")
    sales = _latest(aSeries, "IS", "sales")
    gp = _latest(aSeries, "IS", "gross_profit")
    ocf = _latest(aSeries, "CF", "operating_cashflow")

    roe = ni / eq if ni is not None and eq and eq > 0 else None
    roa = ni / ta if ni is not None and ta and ta > 0 else None
    gm = gp / sales if gp is not None and sales and sales > 0 else None
    cfoa = ocf / ta if ocf is not None and ta and ta > 0 else None

    profScores = [x for x in [roe, roa, gm, cfoa] if x is not None]
    profitability = sum(profScores) / len(profScores) if profScores else None

    # --- Growth (5Y 성장률 평균) ---
    salesList = aSeries.get("IS", {}).get("sales", [])
    validSales = [v for v in salesList if v is not None and v > 0]
    growth = None
    if len(validSales) >= 3:
        n = len(validSales) - 1
        growth = ((validSales[-1] / validSales[0]) ** (1 / n) - 1) if n > 0 else None

    # --- Safety (부채비율 역수 + 유동비율) ---
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
    safety = sum(safetyScores) / len(safetyScores) if safetyScores else None

    # --- Payout ---
    div = _latest(aSeries, "CF", "dividends_paid")
    payout = None
    if div is not None and ni is not None and ni > 0:
        payout = abs(div) / ni

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
    """Peter Lynch: Fair Value = EPS Growth Rate × EPS."""
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
    """Buffett Owner Earnings = NI + D&A - maintenance CAPEX."""
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


def calcDuPont(
    aSeries: dict[str, dict[str, list[float | None]]],
    aYears: list[str],
) -> DuPontResult:
    """DuPont 5-factor 분해: ROE = 세금부담 × 이자부담 × OPM × 회전율 × 레버리지."""
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
        ni = niList[i]
        s = salesList[i]
        ta = taList[i]
        eq = eqList[i]
        op = opList[i] if i < len(opList) else None
        ebt = ebtList[i] if i < len(ebtList) else None
        cl = clList[i] if i < len(clList) else None
        cash = cashList[i] if i < len(cashList) else None

        margin = ni / s if ni is not None and s and s > 0 else None
        turnover = s / ta if s is not None and ta and ta > 0 else None
        lever = ta / eq if ta is not None and eq and eq > 0 else None
        roe = ni / eq if ni is not None and eq and eq > 0 else None

        # 5-factor: taxBurden = NI/EBT, interestBurden = EBT/EBIT(=OP)
        tb = ni / ebt if ni is not None and ebt is not None and ebt != 0 else None
        ib = ebt / op if ebt is not None and op is not None and op != 0 else None
        opm = op / s if op is not None and s and s > 0 else None

        # ROIC = NOPAT / IC, IC = TA - CL - Cash (근사)
        roic = None
        if op is not None and ta is not None:
            ic = ta - (cl or 0) - (cash or 0)
            if ic > 0:
                nopat = op * (1 - 0.22)  # 법인세율 22% 근사
                roic = nopat / ic

        margins.append(_round(margin))
        turnovers.append(_round(turnover))
        leverages.append(_round(lever))
        roes.append(_round(roe))
        taxBurdens.append(_round(tb))
        interestBurdens.append(_round(ib))
        opMargins.append(_round(opm))
        roicList.append(_round(roic))
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
    """ROE 변동의 주요 동인 식별."""

    def _cv(vals: list[float | None]) -> float:
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
    """모든 정량 스코어 한 번에 계산."""
    return QuantScores(
        piotroski=calcPiotroski(aSeries),
        magicFormula=calcMagicFormula(aSeries, currentPrice, sharesOutstanding),
        qmj=calcQmj(aSeries, aYears),
        lynchFairValue=calcLynchFairValue(aSeries, currentPrice, sharesOutstanding),
        buffettOwnerEarnings=calcBuffettOwnerEarnings(aSeries),
        dupont=calcDuPont(aSeries, aYears),
    )


def _round(v: float | None, ndigits: int = 4) -> float | None:
    """None-safe round."""
    if v is None:
        return None
    return round(v, ndigits)
