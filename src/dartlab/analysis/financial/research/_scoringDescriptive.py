"""scoring 의 Descriptive 점수 — Piotroski/Magic/QMJ + 시리즈 헬퍼."""

from __future__ import annotations

from dartlab.analysis.financial.research.types import (
    MagicFormulaScore,
    PiotroskiScore,
    QmjScore,
)


def _val(series: dict, sjDiv: str, snakeId: str, idx: int) -> float | None:
    """시계열에서 특정 인덱스 값.

    Returns
    -------
    float | None
        해당 인덱스의 값. 범위 밖이면 None.
    """
    vals = series.get(sjDiv, {}).get(snakeId, [])
    if 0 <= idx < len(vals):
        return vals[idx]
    return None


def _latest(series: dict, sjDiv: str, snakeId: str) -> float | None:
    """최신 non-null 값.

    Returns
    -------
    float | None
        시계열 끝에서부터 탐색한 첫 non-null 값. 없으면 None.
    """
    vals = series.get(sjDiv, {}).get(snakeId, [])
    for v in reversed(vals):
        if v is not None:
            return v
    return None


def _latestTwo(series: dict, sjDiv: str, snakeId: str) -> tuple[float | None, float | None]:
    """최근 2개 non-null (latest, prev).

    Returns
    -------
    tuple[float | None, float | None]
        ``(latest, prev)`` 쌍. 데이터 부족 시 해당 위치 None.
    """
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


def _piotroskiProfitability(aSeries: dict, ta: float | None, taPrev: float | None) -> dict[str, bool]:
    """F1~F4 수익성 신호 (ROA 양수 / OCF 양수 / ROA 개선 / CF > NI).

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.
    ta, taPrev : float | None
        총자산 최신값과 직전값.

    Returns
    -------
    dict[str, bool]
        4 신호. 삽입 순서 F1 ~ F4.
    """
    ni = _latest(aSeries, "IS", "net_profit")
    ocf = _latest(aSeries, "CF", "operating_cashflow")

    roa = ni / ta if ni is not None and ta and ta > 0 else None
    roaPrev = None
    niPrev = _latestTwo(aSeries, "IS", "net_profit")[1]
    if niPrev is not None and taPrev and taPrev > 0:
        roaPrev = niPrev / taPrev

    return {
        # F1: ROA > 0
        "roaPositive": roa is not None and roa > 0,
        # F2: Operating CF > 0
        "ocfPositive": ocf is not None and ocf > 0,
        # F3: ROA increasing
        "roaIncreasing": roa is not None and roaPrev is not None and roa > roaPrev,
        # F4: CF > NI (accrual quality)
        "cfGtNi": ocf is not None and ni is not None and ocf > ni,
    }


def _piotroskiHealth(aSeries: dict) -> dict[str, bool]:
    """F5~F7 건전성 신호 (차입금 감소 / 유동비율 상승 / 무희석).

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.

    Returns
    -------
    dict[str, bool]
        3 신호. 삽입 순서 F5 ~ F7.
    """
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

    out: dict[str, bool] = {
        # F5: Long-term debt decreasing
        "debtDecreasing": ltd is not None and ltdPrev is not None and ltd <= ltdPrev,
        # F6: Current ratio increasing
        "currentRatioUp": cr is not None and crPrev is not None and cr > crPrev,
    }
    # F7: No new shares issued (equity not diluted)
    shares = _latest(aSeries, "BS", "issued_shares")
    sharesPrev = _latestTwo(aSeries, "BS", "issued_shares")[1]
    if shares is not None and sharesPrev is not None:
        out["noNewShares"] = shares <= sharesPrev
    else:
        # 발행주식수 없으면 보수적으로 통과 (자본 변동으로 근사)
        out["noNewShares"] = True
    return out


def _piotroskiEfficiency(aSeries: dict, ta: float | None, taPrev: float | None) -> dict[str, bool]:
    """F8~F9 효율성 신호 (매출총이익률 상승 / 자산회전율 상승).

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.
    ta, taPrev : float | None
        총자산 최신값과 직전값.

    Returns
    -------
    dict[str, bool]
        2 신호. 삽입 순서 F8 ~ F9.
    """
    gp = _latest(aSeries, "IS", "gross_profit")
    gpPrev = _latestTwo(aSeries, "IS", "gross_profit")[1]
    sales = _latest(aSeries, "IS", "sales")
    salesPrev = _latestTwo(aSeries, "IS", "sales")[1]

    gm = gp / sales if gp is not None and sales and sales > 0 else None
    gmPrev = gpPrev / salesPrev if gpPrev is not None and salesPrev and salesPrev > 0 else None

    at = sales / ta if sales is not None and ta and ta > 0 else None
    atPrev = salesPrev / taPrev if salesPrev is not None and taPrev and taPrev > 0 else None

    return {
        # F8: Gross margin increasing
        "grossMarginUp": gm is not None and gmPrev is not None and gm > gmPrev,
        # F9: Asset turnover increasing
        "assetTurnoverUp": at is not None and atPrev is not None and at > atPrev,
    }


def calcPiotroski(
    aSeries: dict[str, dict[str, list[float | None]]],
) -> PiotroskiScore:
    """Piotroski F-Score 9-signal.

    Capabilities:
        - 9 신호 (수익성 4 + 건전성 3 + 효율성 2) 점수화 → 0~9 합산.

    Guide:
        ROA · OCF · ROA 증가 · CF>NI · 부채 감소 · 유동비 증가 · 무희석 · GM 증가 · 자산회전 증가.

    When:
        가치주 스크리닝·재무 건전성 1차 필터.

    How:
        각 신호 boolean → True 합계. >=7 strong, >=4 moderate, 이하 weak.

    Requires:
        aSeries 에 IS net_profit/sales/gross_profit · BS total_assets/equity/borrowings · CF operating_cashflow 시계열.

    Raises:
        없음. 데이터 결측 시 해당 신호 False.

    Parameters:
        aSeries : dict
            연간 재무 시계열 ``{sjDiv: {snakeId: [값, ...]}}``.

    Returns:
        PiotroskiScore
            total : int — F-Score 합계 (0~9점)
            components : dict[str, bool] — 9개 신호별 통과 여부
            interpretation : str — ``"strong"`` | ``"moderate"`` | ``"weak"``

    Example:
        >>> calcPiotroski(aSeries)
        PiotroskiScore(total=7, components={...}, interpretation="strong")

    See Also:
        - calcAllScores : 6 종 스코어 일괄 호출 진입점.

    AIContext:
        Piotroski 7점 이상 = 펀더멘털 강화 신호 인용.
    """
    components: dict[str, bool] = {}

    ta = _latest(aSeries, "BS", "total_assets")
    taPrev = _latestTwo(aSeries, "BS", "total_assets")[1]

    components.update(_piotroskiProfitability(aSeries, ta, taPrev))
    components.update(_piotroskiHealth(aSeries))
    components.update(_piotroskiEfficiency(aSeries, ta, taPrev))

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
    """Greenblatt Magic Formula — ROIC + Earnings Yield.

    Capabilities:
        - ROIC + Earnings Yield 2 인자 산출 (Greenblatt 1999).

    Guide:
        ROIC = EBIT / (TA - CL - cash). EY = EBIT / EV. EV = market_cap + debt - cash.

    When:
        가치 + 퀄리티 동시 충족 종목 스크리닝 시.

    How:
        2 지표 합산이 아니라 순위 합계로 종목 비교 (본 함수는 raw 값만).

    Requires:
        aSeries IS operating_profit + BS total_assets/current_liabilities/cash. currentPrice·sharesOutstanding 옵션.

    Raises:
        없음. invested capital ≤ 0 또는 EV ≤ 0 시 None.

    Parameters:
        aSeries : dict
            연간 재무 시계열.
        currentPrice : float | None
            현재 주가 (원 또는 달러).
        sharesOutstanding : float | None
            발행주식수 (주).

    Returns:
        MagicFormulaScore
            roic : float | None — 투하자본수익률 (%)
            earningsYield : float | None — 이익수익률 (%)

    Example:
        >>> calcMagicFormula(aSeries, currentPrice=50000, sharesOutstanding=1e8)
        MagicFormulaScore(roic=15.2, earningsYield=8.1)

    See Also:
        - calcAllScores : 통합 진입점.

    AIContext:
        ROIC > 15% + EY > 8% = 양호한 magic formula 후보.
    """
    op = _latest(aSeries, "IS", "operating_profit")
    ta = _latest(aSeries, "BS", "total_assets")
    _latest(aSeries, "BS", "current_assets")
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


def _round(v: float | None, ndigits: int = 4) -> float | None:
    """None-safe round.

    Returns
    -------
    float | None
        반올림된 값. None이면 None.
    """
    if v is None:
        return None
    return round(v, ndigits)
