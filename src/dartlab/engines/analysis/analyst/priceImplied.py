"""주가 내재 매출 역산 엔진 — 시장이 합의한 미래 매출을 현재 시가총액에서 역산."""

from __future__ import annotations

from dataclasses import dataclass, field

from dartlab.engines.common.finance.extract import getTTM


@dataclass
class PriceImpliedRevenue:
    """주가 내재 매출 역산 결과."""

    impliedGrowthRate: float  # 시장이 내재하는 매출 성장률 (%, 연간)
    impliedRevenue: list[float]  # 내재 향후 N년 매출
    currentPrice: float
    marketCap: float  # 시가총액 (원)
    latestRevenue: float  # 최근 TTM 매출
    assumedMargin: float  # 가정한 영업이익률 (%)
    assumedWacc: float  # 가정한 WACC (%)
    assumedTerminalGrowth: float  # 가정한 영구성장률 (%)
    gapVsForecast: float | None = None  # 엔진예측 - 시장내재 (%, 양수=시장이 보수적)
    signal: str | None = None  # "underpriced" | "overpriced" | "fair"
    warnings: list[str] = field(default_factory=list)


def reverseImpliedGrowth(
    series: dict,
    marketCap: float,
    *,
    wacc: float = 10.0,
    terminalGrowth: float = 2.0,
    horizon: int = 3,
    netDebt: float | None = None,
) -> PriceImpliedRevenue | None:
    """시가총액에서 시장이 내재하는 매출 성장률을 역산.

    원리: marketCap = PV(미래 FCF) + PV(TV)
    FCF = Revenue × margin × (1 - taxRate) + DA - CAPEX - ΔNWC ≈ Revenue × fcfMargin
    이를 g에 대해 역산하면 시장이 가정하는 매출 성장률이 나온다.
    """
    if marketCap is None or marketCap <= 0:
        return None

    revenue = getTTM(series, "IS", "sales") or getTTM(series, "IS", "revenue")
    if revenue is None or revenue <= 0:
        return None

    # 영업이익률 (최근 TTM)
    opIncome = getTTM(series, "IS", "operating_profit") or getTTM(series, "IS", "operating_income")
    margin = opIncome / revenue if opIncome and revenue else 0.0
    if margin <= 0:
        margin = 0.05  # 최소 5% 가정

    # FCF margin 추정: 영업이익률 × (1 - effective tax) - capex/revenue + da/revenue
    # 단순화: FCF margin ≈ 영업이익률 × 0.65 (세금·운전자본·capex 반영)
    fcfMargin = _estimateFcfMargin(series, margin)

    # equity value = marketCap (순부채 조정 생략 or 반영)
    ev = marketCap
    if netDebt is not None:
        ev = marketCap + netDebt

    # 이진 탐색으로 implied growth 역산
    impliedG = _bisectImpliedGrowth(
        ev=ev,
        baseRevenue=revenue,
        fcfMargin=fcfMargin,
        wacc=wacc / 100,
        terminalGrowth=terminalGrowth / 100,
        horizon=horizon,
    )

    warnings: list[str] = []
    if impliedG is None:
        warnings.append("역산 수렴 실패 — 시가총액이 FCF 기반 합리 범위 밖")
        return PriceImpliedRevenue(
            impliedGrowthRate=0.0,
            impliedRevenue=[],
            currentPrice=0.0,
            marketCap=marketCap,
            latestRevenue=revenue,
            assumedMargin=margin * 100,
            assumedWacc=wacc,
            assumedTerminalGrowth=terminalGrowth,
            warnings=warnings,
        )

    # implied revenue path
    impliedRevPath = []
    rev = revenue
    for _ in range(horizon):
        rev = rev * (1 + impliedG)
        impliedRevPath.append(rev)

    return PriceImpliedRevenue(
        impliedGrowthRate=impliedG * 100,
        impliedRevenue=impliedRevPath,
        currentPrice=0.0,  # 호출자가 설정
        marketCap=marketCap,
        latestRevenue=revenue,
        assumedMargin=margin * 100,
        assumedWacc=wacc,
        assumedTerminalGrowth=terminalGrowth,
        warnings=warnings,
    )


def computeGap(
    implied: PriceImpliedRevenue,
    forecastGrowthRate: float,
) -> None:
    """엔진 예측 성장률 vs 시장 내재 성장률 갭 계산 + 신호 부여."""
    gap = forecastGrowthRate - implied.impliedGrowthRate
    implied.gapVsForecast = round(gap, 2)

    # 갭 5%p 이상이면 신호
    if gap > 5.0:
        implied.signal = "underpriced"
    elif gap < -5.0:
        implied.signal = "overpriced"
    else:
        implied.signal = "fair"


# ── 내부 유틸 ──────────────────────────────────────────────


def _estimateFcfMargin(series: dict, opMargin: float) -> float:
    """FCF margin 추정 (실제 데이터 기반, fallback 단순화)."""
    revenue = getTTM(series, "IS", "sales") or getTTM(series, "IS", "revenue")
    ocf = getTTM(series, "CF", "operating_cashflow")
    capex = getTTM(series, "CF", "capital_expenditure") or getTTM(
        series, "CF", "purchase_of_property_plant_and_equipment"
    )

    if revenue and revenue > 0 and ocf is not None:
        capexVal = abs(capex) if capex else 0
        fcf = ocf - capexVal
        fcfMargin = fcf / revenue
        # 음수면 영업이익률 기반 fallback (음수 FCF는 일시적일 수 있음)
        if fcfMargin < 0:
            return max(opMargin * 0.50, 0.02)
        # 범위 제한 (0% ~ 40%)
        return max(0.02, min(fcfMargin, 0.40))

    # fallback: 영업이익률 × 65%
    return max(opMargin * 0.65, 0.02)


def _bisectImpliedGrowth(
    ev: float,
    baseRevenue: float,
    fcfMargin: float,
    wacc: float,
    terminalGrowth: float,
    horizon: int,
    *,
    lo: float = -0.50,
    hi: float = 0.60,
    tol: float = 1e-6,
    maxIter: int = 100,
) -> float | None:
    """이진 탐색으로 EV = DCF(g)를 만족하는 g 역산."""
    if wacc <= terminalGrowth:
        return None

    for _ in range(maxIter):
        mid = (lo + hi) / 2
        evCalc = _dcfFromGrowth(baseRevenue, fcfMargin, mid, wacc, terminalGrowth, horizon)

        if abs(evCalc - ev) / max(ev, 1) < tol:
            return mid

        if evCalc < ev:
            lo = mid
        else:
            hi = mid

    # 수렴 못하면 가장 가까운 값 반환
    mid = (lo + hi) / 2
    evCalc = _dcfFromGrowth(baseRevenue, fcfMargin, mid, wacc, terminalGrowth, horizon)
    if abs(evCalc - ev) / max(ev, 1) < 0.05:  # 5% 이내면 허용
        return mid
    return None


def _dcfFromGrowth(
    baseRevenue: float,
    fcfMargin: float,
    growth: float,
    wacc: float,
    terminalGrowth: float,
    horizon: int,
) -> float:
    """주어진 성장률로 DCF 기업가치 계산."""
    rev = baseRevenue
    pvFcf = 0.0
    for yr in range(1, horizon + 1):
        rev = rev * (1 + growth)
        fcf = rev * fcfMargin
        pvFcf += fcf / (1 + wacc) ** yr

    # terminal value
    terminalFcf = rev * (1 + growth) * fcfMargin
    tv = terminalFcf * (1 + terminalGrowth) / (wacc - terminalGrowth)
    pvTv = tv / (1 + wacc) ** horizon

    return pvFcf + pvTv
