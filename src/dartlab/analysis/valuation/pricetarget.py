"""확률 가중 주가 목표가 엔진.

5개 매크로 시나리오 × pro-forma → DCF → Monte Carlo → 투자 신호.

외부 의존성 제로 (random, math 모듈만 사용).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from dartlab.analysis.financial.proforma import (
    buildProforma,
    computeCompanyWacc,
    extractHistoricalRatios,
)
from dartlab.analysis.forecast.prediction import adjustProbabilities
from dartlab.core.utils.extract import getLatest, getTTM
from dartlab.synth.scenario import (
    PRESET_SCENARIOS,
    MacroScenario,
    SectorElasticity,
    getElasticity,
    getNoiseSigma,
)

if TYPE_CHECKING:
    from dartlab.analysis.financial.proforma import ProFormaResult
    from dartlab.analysis.forecast.prediction import ContextSignals


# ══════════════════════════════════════
# Cholesky 분해 (순수 Python -- numpy 의존 없음)
# ══════════════════════════════════════


def _choleskyDecompose(matrix: list[list[float]]) -> list[list[float]]:
    """상관행렬 → 하삼각 행렬 L (L × L^T = matrix)."""
    n = len(matrix)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                val = matrix[i][i] - s
                L[i][j] = math.sqrt(max(val, 0.0))
            else:
                L[i][j] = (matrix[i][j] - s) / L[j][j] if L[j][j] > 0 else 0.0
    return L


def _choleskyMultiply(L: list[list[float]], z: list[float]) -> list[float]:
    """L × z = 상관된 난수 벡터."""
    n = len(z)
    result = [0.0] * n
    for i in range(n):
        result[i] = sum(L[i][j] * z[j] for j in range(i + 1))
    return result


# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass
class ScenarioPriceTarget:
    """단일 시나리오의 주가 목표."""

    scenarioName: str
    probability: float
    proforma: ProFormaResult
    enterprise_value: float
    equity_value: float
    per_share_value: float | None
    wacc_used: float
    terminalGrowth: float
    implied_per: float | None


@dataclass
class PriceTargetResult:
    """확률 가중 주가 목표가 전체 결과."""

    scenarios: list[ScenarioPriceTarget]
    weighted_target: float | None
    percentiles: dict[str, float]  # p10, p25, p50, p75, p90
    expected_value: float | None
    currentPrice: float | None
    upsidePct: float | None
    probability_above_current: float | None
    signal: str | None  # strong_buy / buy / hold / sell / strong_sell
    confidence: str  # high / medium / low
    wacc_details: dict[str, float]
    warnings: list[str] = field(default_factory=list)
    status: str = "usable"
    blockedReason: str | None = None

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[확률 가중 주가 목표가]"]
        if self.weighted_target is not None:
            lines.append(f"  가중 목표가: {self.weighted_target:,.0f}원")
        else:
            lines.append("  가중 목표가: 미산출")
        if self.currentPrice:
            lines.append(f"  현재가: {self.currentPrice:,.0f}원")
            if self.upsidePct is not None:
                lines.append(f"  업사이드: {self.upsidePct:+.1f}%")
            if self.probability_above_current is not None:
                lines.append(f"  현재가 상회 확률: {self.probability_above_current:.0f}%")
        lines.append(f"  투자 신호: {self.signal}")
        lines.append(f"  신뢰도: {self.confidence}")
        lines.append("")

        # 시나리오별
        lines.append("  === 시나리오별 목표가 ===")
        lines.append("  시나리오         | 확률  | 목표가        | EV")
        lines.append("  -----------------|-------|--------------|----------")
        for s in self.scenarios:
            lines.append(
                f"  {s.scenarioName:<16s} | {s.probability * 100:4.0f}% "
                f"| {s.per_share_value:>12,.0f}원 | {s.enterprise_value / 1e8:>8,.0f}억"
            )

        # 분포
        lines.append("")
        lines.append("  === Monte Carlo 분포 ===")
        for k, v in sorted(self.percentiles.items()):
            lines.append(f"  {k}: {v:,.0f}원")

        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"\n  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ══════════════════════════════════════
# 시나리오 확률 가중치
# ══════════════════════════════════════

SCENARIO_PROBABILITIES: dict[str, float] = {
    "baseline": 0.40,
    "rate_hike": 0.20,
    "china_slowdown": 0.15,
    "semiconductor_down": 0.15,
    "adverse": 0.10,
}


# ══════════════════════════════════════
# 핵심 함수
# ══════════════════════════════════════


def _deriveRevenuePathFromMacro(
    baseGrowth: float,
    scenario: MacroScenario,
    elasticity: SectorElasticity,
    years: int = 5,
) -> list[float]:
    """매크로 시나리오 + 섹터 감응도 → 5년 매출 성장률 경로.

    baseline GDP 대비 시나리오 GDP 차이에 β를 곱해 성장률 조정.
    """
    baseline_gdp = PRESET_SCENARIOS["baseline"].gdpGrowth
    path = []
    for i in range(years):
        gdp_idx = min(i, len(scenario.gdpGrowth) - 1)
        base_gdp_idx = min(i, len(baseline_gdp) - 1)

        gdp_delta = scenario.gdpGrowth[gdp_idx] - baseline_gdp[base_gdp_idx]
        fx_delta = 0.0
        if i < len(scenario.krwUsd) and scenario.krwUsd[0] > 0:
            fx_pct = (scenario.krwUsd[min(i, len(scenario.krwUsd) - 1)] / scenario.krwUsd[0] - 1) * 100
            fx_delta = fx_pct / 10 * elasticity.revenueToFx  # 환율 10% 변화당

        growth = baseGrowth + gdp_delta * elasticity.revenueToGdp + fx_delta
        # mean reversion: 극단 시나리오는 3~5년차에 baseline 복귀 경향
        if i >= 2:
            growth = growth * 0.7 + baseGrowth * 0.3
        if i >= 4:
            growth = growth * 0.5 + baseGrowth * 0.5

        path.append(round(growth, 2))
    return path


def _dcfFromProforma(
    proforma: ProFormaResult,
    wacc: float,
    terminalGrowth: float = 2.0,
    shares: int | None = None,
) -> tuple[float, float, float]:
    """Pro-forma FCF → Terminal Value → EV → Equity → 주당가치.

    Returns:
        (enterprise_value, equity_value, per_share_value)
    """
    if not proforma.projections:
        return 0.0, 0.0, 0.0

    discount_rate = wacc / 100
    tg = terminalGrowth / 100

    # FCF 현가 합
    pv_fcf = 0.0
    for p in proforma.projections:
        df = (1 + discount_rate) ** p.year_offset
        pv_fcf += p.fcf / df

    last = proforma.projections[-1]
    last_year = last.year_offset

    # FCF 양수면 Gordon Growth, 음수면 EBITDA exit multiple fallback
    if last.fcf > 0:
        if discount_rate > tg:
            terminal_value = last.fcf * (1 + tg) / (discount_rate - tg)
        else:
            terminal_value = last.fcf * 20
        pv_tv = terminal_value / ((1 + discount_rate) ** last_year)
        enterprise_value = pv_fcf + pv_tv
    else:
        # CAPEX 집약 산업 — EBITDA exit multiple로 전체 EV 대체
        # FCF PV가 음수인 경우 누적 FCF를 사용하면 EBITDA TV를 압도하므로,
        # EBITDA 기반 순수 EV 계산으로 전환
        ebitda = last.ebitda if last.ebitda > 0 else last.operating_income
        if ebitda > 0:
            exit_multiple = max(6.0, min(1 / discount_rate, 15.0))
            terminal_value = ebitda * exit_multiple
            pv_tv = terminal_value / ((1 + discount_rate) ** last_year)
            enterprise_value = pv_tv  # FCF PV 무시, EBITDA exit만 사용
        elif last.revenue > 0:
            # EBITDA 음수 기업 — EV/Sales fallback (보수적)
            # 적자 지속 → 낮은 배수. 시나리오별 매출 차이는 반영
            sales_multiple = max(0.2, min(1 / discount_rate * 0.08, 0.8))
            terminal_value = last.revenue * sales_multiple
            pv_tv = terminal_value / ((1 + discount_rate) ** last_year)
            enterprise_value = pv_tv
        else:
            enterprise_value = 0

    # EV → Equity
    total_debt = proforma.base_year.get("total_debt", 0)
    cash = proforma.base_year.get("cash", 0)
    equity_value = enterprise_value - total_debt + cash

    # 주당가치
    if shares and shares > 0:
        per_share = equity_value / shares
    else:
        per_share = None

    return enterprise_value, equity_value, max(per_share, 0) if per_share is not None else None


def _monteCarloPriceDistribution(
    series: dict,
    baseGrowth: float,
    elasticity: SectorElasticity,
    wacc: float,
    terminalGrowth: float,
    shares: int | None,
    iterations: int = 5000,
    seed: int | None = None,
    sizeClass: str = "Mid",
) -> tuple[dict[str, float], float | None, list[float]]:
    """v2 Multi-Noise MC — 5변수 동시 noise + NWC + sizeClass σ.

    5개 변수: growth, margin, wacc, capex, tax
    sizeClass별 σ 차등: Small 1.5x, Mid 1.0x, Large 0.8x

    Returns:
        (percentiles, probability_above_current, all_values)
    """
    if shares is None or shares <= 0:
        return {}, None, []

    # 로컬 RNG 인스턴스 — 전역 random 상태 미오염 (동일 seed → 동일 시퀀스, 동작 무변경).
    rng = random.Random(seed)

    ratios = extractHistoricalRatios(series)
    base = {
        "revenue": getTTM(series, "IS", "sales") or 0,
        "cash": getLatest(series, "BS", "cash_and_cash_equivalents") or 0,
        "total_debt": (
            (getLatest(series, "BS", "shortterm_borrowings") or 0)
            + (getLatest(series, "BS", "longterm_borrowings") or 0)
            + (getLatest(series, "BS", "debentures") or 0)
        ),
    }
    if base["revenue"] <= 0:
        return {}, None, []

    discount_rate = wacc / 100
    tg = terminalGrowth / 100
    values: list[float] = []

    # v3: sizeClass별 sigma + Cholesky 상관
    sigma_growth = getNoiseSigma("growth", sizeClass)
    sigma_margin = getNoiseSigma("margin", sizeClass)
    sigma_wacc = getNoiseSigma("wacc", sizeClass)
    sigma_capex = getNoiseSigma("capex", sizeClass)
    sigma_tax = getNoiseSigma("tax", sizeClass)
    sigmas = [sigma_growth, sigma_margin, sigma_wacc, sigma_capex, sigma_tax]

    # 상관행렬: growth-margin 동조, wacc-growth 역상관
    # [growth, margin, wacc, capex, tax]
    corr = [
        [1.0, 0.4, -0.3, 0.2, 0.0],  # growth
        [0.4, 1.0, -0.2, 0.0, 0.0],  # margin (경기 좋으면 마진도 개선)
        [-0.3, -0.2, 1.0, 0.0, 0.1],  # wacc (금리 상승 시 성장 둔화)
        [0.2, 0.0, 0.0, 1.0, 0.0],  # capex
        [0.0, 0.0, 0.1, 0.0, 1.0],  # tax
    ]
    chol = _choleskyDecompose(corr)

    for _ in range(iterations):
        # v3: Cholesky 기반 상관 noise
        z = [rng.gauss(0, 1) for _ in range(5)]
        correlated = _choleskyMultiply(chol, z)
        growth_noise = correlated[0] * sigmas[0]
        margin_noise = correlated[1] * sigmas[1]
        wacc_noise = correlated[2] * sigmas[2]
        capex_noise = correlated[3] * sigmas[3]
        tax_noise = correlated[4] * sigmas[4]

        noisy_growth = baseGrowth + growth_noise
        noisy_margin = max(5.0, min(ratios.gross_margin + margin_noise, 80.0))
        noisy_wacc = max(0.03, min(discount_rate + wacc_noise / 100, 0.25))
        noisy_capex = max(0.5, ratios.capex_to_revenue + capex_noise)
        noisy_tax = max(5.0, min(ratios.effective_tax_rate + tax_noise, 50.0))

        # v2: IS + NWC 반영 5년 DCF
        rev = base["revenue"]
        fcf_pv = 0.0
        last_fcf = 0.0
        last_ebitda = 0.0
        prev_nwc = (
            rev * ratios.receivables_to_revenue / 100
            + rev * ratios.inventory_to_revenue / 100
            - rev * ratios.payables_to_revenue / 100
        )
        for yr in range(1, 6):
            rev = rev * (1 + noisy_growth / 100)
            gross = rev * noisy_margin / 100
            dep = rev * ratios.depreciation_ratio / 100
            # v3: IS 구조 분기 — D&A가 SGA에 포함된 경우 별도 차감하지 않음
            if ratios.dep_in_sga:
                opIncome = gross - rev * ratios.sga_ratio / 100
            else:
                opIncome = gross - rev * ratios.sga_ratio / 100 - dep
            ebitda = opIncome + dep
            ebt = max(opIncome, 0)
            ni = ebt * (1 - noisy_tax / 100)
            capex = rev * noisy_capex / 100
            # v2: NWC 변동 반영
            nwc = (
                rev * ratios.receivables_to_revenue / 100
                + rev * ratios.inventory_to_revenue / 100
                - rev * ratios.payables_to_revenue / 100
            )
            delta_nwc = nwc - prev_nwc
            fcf = ni + dep - delta_nwc - capex
            df = (1 + noisy_wacc) ** yr
            fcf_pv += fcf / df
            last_fcf = fcf
            last_ebitda = ebitda
            prev_nwc = nwc

        # Terminal Value — FCF 음수 시 EBITDA exit multiple fallback
        if last_fcf > 0:
            if noisy_wacc > tg:
                tv = last_fcf * (1 + tg) / (noisy_wacc - tg)
            else:
                tv = last_fcf * 20
        elif last_ebitda > 0:
            exit_mult = max(6.0, min(1 / noisy_wacc, 15.0))
            tv = last_ebitda * exit_mult
        elif rev > 0:
            # EBITDA 음수 — EV/Sales fallback (보수적)
            sales_mult = max(0.2, min(1 / noisy_wacc * 0.08, 0.8))
            tv = rev * sales_mult
        else:
            tv = 0
        pv_tv = tv / ((1 + noisy_wacc) ** 5)

        ev = fcf_pv + pv_tv
        eq = ev - base["total_debt"] + base["cash"]
        per_share = eq / shares
        values.append(max(per_share, 0))

    if not values:
        return {}, None, []

    values.sort()
    n = len(values)

    def pct(p: float) -> float:
        """백분위 값 추출.

        Capabilities:
            - 정렬된 values 리스트에서 p 백분위 인덱스 추출

        Parameters
        ----------
        p : float
            백분위 (0.0~1.0).

        Returns
        -------
        float
            해당 백분위의 값.

        Example:
            >>> pct(0.5)  # 중앙값
            12345.0

        Requires:
            상위 스코프 values (정렬됨) + n 변수.

        Raises:
            없음 — 인덱스는 n-1 로 clamp.
        """
        idx = int(n * p)
        return values[min(idx, n - 1)]

    percentiles = {
        "p10": pct(0.10),
        "p25": pct(0.25),
        "p50": pct(0.50),
        "p75": pct(0.75),
        "p90": pct(0.90),
    }

    return percentiles, None, values


def _classifySignal(
    upsidePct: float | None,
    percentiles: dict[str, float],
    currentPrice: float | None,
) -> str:
    """upside와 분포로 투자 신호 판정."""
    if upsidePct is None:
        return "hold"

    p10 = percentiles.get("p10", 0)
    p90 = percentiles.get("p90", float("inf"))

    if upsidePct > 30 and currentPrice and p10 > currentPrice:
        return "strong_buy"
    if upsidePct > 15:
        return "buy"
    if upsidePct < -30 and currentPrice and p90 < currentPrice:
        return "strong_sell"
    if upsidePct < -15:
        return "sell"
    return "hold"


def computePriceTarget(
    series: dict,
    sectorKey: str | None = None,
    currentPrice: float | None = None,
    shares: int | None = None,
    marketCap: float | None = None,
    terminalGrowth: float = 2.0,
    mcIterations: int = 5000,
    mcSeed: int | None = None,
    scenarioProbabilities: dict[str, float] | None = None,
    contextSignals: ContextSignals | None = None,
) -> PriceTargetResult:
    """메인 — 5시나리오 × pro-forma → DCF → Monte Carlo → 확률 분포 → signal.

    v2: context_signals가 있으면 확률 동적 재가중 + sizeClass별 MC σ 차등.

    Capabilities:
        - 5 시나리오 (baseline/optimistic/pessimistic/...) pro-forma DCF 가중평균
        - Monte Carlo 5000회 σ 시뮬레이션 → 백분위 분포 (p10~p90)
        - context_signals 기반 확률 동적 재가중 + sizeClass 별 σ 차등

    Parameters
    ----------
    series : dict
        시계열 dict (unwrap 완료).
    sectorKey : str, optional
        업종 키 (SectorElasticity 조회).
    currentPrice : float, optional
        현재 주가 (원).
    shares : int, optional
        발행주식수.
    marketCap : float, optional
        시가총액 (WACC의 equity weight 계산용) (원).
    terminalGrowth : float
        영구성장률 (%).
    mcIterations : int
        Monte Carlo 반복 횟수.
    mcSeed : int, optional
        난수 시드 (재현용).
    scenarioProbabilities : dict[str, float], optional
        시나리오별 확률 오버라이드.
    contextSignals : ContextSignals, optional
        v2 맥락 신호 (확률 재가중 + MC σ 차등).

    Returns
    -------
    PriceTargetResult
        target : float — 가중 평균 목표주가 (원)
        upsidePct : float — 현재가 대비 upside (%)
        signal : str — 투자 신호 ("strong_buy"|"buy"|"hold"|"sell"|"strong_sell")
        scenarios : dict — 시나리오별 DCF 결과
        percentiles : dict — Monte Carlo 백분위 분포

    Example:
        >>> r = computePriceTarget(series, sectorKey="반도체", currentPrice=75000,
        ...                         shares=5e9, marketCap=4.5e14)
        >>> r.target, r.signal

    Guide:
        v2 context_signals 미지정 시 default sizeClass="Mid" + 정적 확률.
        반도체 외 업종은 semiconductor_down 확률을 baseline 으로 재배분.

    When:
        Analyst.report 또는 단독 시나리오 기반 목표주가 산출 시.

    How:
        computePriceTarget(series, sectorKey="반도체", currentPrice=p, shares=s, ...).

    Requires:
        SectorElasticity + PRESET_SCENARIOS + buildProforma + computeCompanyWacc +
        getRevenueGrowth3Y.

    Raises:
        없음 — 결측은 warnings 누적.

    See Also:
        - Analyst.report : 본 결과를 dcf 채널로 흡수
        - calcDFV : 보다 종합적인 dFV 진입점

    AIContext:
        시나리오 기반 목표주가 답변 시 target + p10/p90 + signal 함께 인용.
    """
    warnings: list[str] = []
    blocked_reason = None
    if shares is None or shares <= 0:
        blocked_reason = "발행주식수 근거가 없어 총 주주가치를 주당 목표가로 변환할 수 없습니다."
        warnings.append(blocked_reason)
    probs = scenarioProbabilities or dict(SCENARIO_PROBABILITIES)
    elasticity = getElasticity(sectorKey)

    # v2: context_signals가 있으면 확률 재가중
    sizeClass = "Mid"
    if contextSignals:
        sizeClass = contextSignals.sizeClass
        probs = adjustProbabilities(probs, contextSignals)
        if contextSignals.reasoning:
            warnings.append(f"맥락 기반 확률 재가중 ({len(contextSignals.reasoning)}개 규칙 적용)")

    # WACC 계산 — v2: 업종 β 활용
    wacc, wacc_details = computeCompanyWacc(
        series,
        sectorElasticity=elasticity,
        marketCap=marketCap,
    )

    # 기준 매출 성장률 (3년 CAGR)
    from dartlab.core.utils.extract import getRevenueGrowth3Y

    baseGrowth = getRevenueGrowth3Y(series)
    if baseGrowth is None:
        baseGrowth = 3.0
        warnings.append("매출 성장률 데이터 부족 — 기본값 3% 사용")

    # 반도체 아닌 업종은 semiconductor_down 확률을 baseline에 재배분
    if sectorKey and sectorKey != "반도체" and "semiconductor_down" in probs:
        semi_prob = probs.pop("semiconductor_down")
        probs["baseline"] = probs.get("baseline", 0.4) + semi_prob

    # 확률 정규화
    total_prob = sum(probs.values())
    if total_prob > 0 and abs(total_prob - 1.0) > 0.001:
        probs = {k: v / total_prob for k, v in probs.items()}

    # 시나리오별 pro-forma + DCF
    scenario_targets: list[ScenarioPriceTarget] = []
    for name, prob in probs.items():
        scenario = PRESET_SCENARIOS.get(name)
        if not scenario:
            warnings.append(f"미지원 시나리오: {name}")
            continue

        rev_path = _deriveRevenuePathFromMacro(baseGrowth, scenario, elasticity)
        pf = buildProforma(
            series,
            revenueGrowthPath=rev_path,
            sectorElasticity=elasticity,
            marketCap=marketCap,
            scenarioName=scenario.label,
        )
        ev, eq, per_share = _dcfFromProforma(pf, wacc, terminalGrowth, shares)

        # Implied P/E
        last_ni = pf.projections[-1].net_income if pf.projections else 0
        implied_per = eq / last_ni if last_ni and last_ni > 0 else None

        scenario_targets.append(
            ScenarioPriceTarget(
                scenarioName=name,
                probability=prob,
                proforma=pf,
                enterprise_value=ev,
                equity_value=eq,
                per_share_value=per_share,
                wacc_used=wacc,
                terminalGrowth=terminalGrowth,
                implied_per=implied_per,
            )
        )

    # 가중 목표가
    per_share_targets = [s for s in scenario_targets if s.per_share_value is not None]
    weighted_target = sum(s.per_share_value * s.probability for s in per_share_targets) if per_share_targets else None

    # Monte Carlo 분포
    percentiles, _, mc_values = _monteCarloPriceDistribution(
        series,
        baseGrowth,
        elasticity,
        wacc,
        terminalGrowth,
        shares,
        mcIterations,
        mcSeed,
        sizeClass=sizeClass,
    )

    # upside
    upsidePct: float | None = None
    prob_above: float | None = None
    if weighted_target is not None and currentPrice and currentPrice > 0:
        upsidePct = (weighted_target / currentPrice - 1) * 100
        if mc_values:
            above_count = sum(1 for v in mc_values if v > currentPrice)
            prob_above = above_count / len(mc_values) * 100

    # expected value (MC 평균)
    expected_value = sum(mc_values) / len(mc_values) if mc_values else weighted_target

    # signal
    signal = _classifySignal(upsidePct, percentiles, currentPrice) if weighted_target is not None else None

    # 신뢰도
    ratios = extractHistoricalRatios(series)
    confidence = ratios.confidence if weighted_target is not None else "unavailable"

    return PriceTargetResult(
        scenarios=scenario_targets,
        weighted_target=weighted_target,
        percentiles=percentiles,
        expected_value=expected_value,
        currentPrice=currentPrice,
        upsidePct=upsidePct,
        probability_above_current=prob_above,
        signal=signal,
        confidence=confidence,
        wacc_details=wacc_details,
        warnings=warnings,
        status="usable" if weighted_target is not None else "blocked",
        blockedReason=blocked_reason,
    )
