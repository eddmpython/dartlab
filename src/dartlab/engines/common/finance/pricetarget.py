"""확률 가중 주가 목표가 엔진.

5개 매크로 시나리오 × pro-forma → DCF → Monte Carlo → 투자 신호.

외부 의존성 제로 (random, math 모듈만 사용).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from dartlab.engines.common.finance.extract import getLatest, getTTM
from dartlab.engines.common.finance.prediction import (
    ContextSignals,
    adjust_probabilities,
    get_noise_sigma,
)
from dartlab.engines.common.finance.proforma import (
    ProFormaResult,
    build_proforma,
    compute_company_wacc,
    extract_historical_ratios,
)
from dartlab.engines.common.finance.simulation import (
    PRESET_SCENARIOS,
    MacroScenario,
    SectorElasticity,
    get_elasticity,
)

# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass
class ScenarioPriceTarget:
    """단일 시나리오의 주가 목표."""

    scenario_name: str
    probability: float
    proforma: ProFormaResult
    enterprise_value: float
    equity_value: float
    per_share_value: float
    wacc_used: float
    terminal_growth: float
    implied_per: float | None


@dataclass
class PriceTargetResult:
    """확률 가중 주가 목표가 전체 결과."""

    scenarios: list[ScenarioPriceTarget]
    weighted_target: float
    percentiles: dict[str, float]  # p10, p25, p50, p75, p90
    expected_value: float
    current_price: float | None
    upside_pct: float | None
    probability_above_current: float | None
    signal: str  # strong_buy / buy / hold / sell / strong_sell
    confidence: str  # high / medium / low
    wacc_details: dict[str, float]
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[확률 가중 주가 목표가]"]
        lines.append(f"  가중 목표가: {self.weighted_target:,.0f}원")
        if self.current_price:
            lines.append(f"  현재가: {self.current_price:,.0f}원")
            if self.upside_pct is not None:
                lines.append(f"  업사이드: {self.upside_pct:+.1f}%")
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
                f"  {s.scenario_name:<16s} | {s.probability * 100:4.0f}% "
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


def _derive_revenue_path_from_macro(
    base_growth: float,
    scenario: MacroScenario,
    elasticity: SectorElasticity,
    years: int = 5,
) -> list[float]:
    """매크로 시나리오 + 섹터 감응도 → 5년 매출 성장률 경로.

    baseline GDP 대비 시나리오 GDP 차이에 β를 곱해 성장률 조정.
    """
    baseline_gdp = PRESET_SCENARIOS["baseline"].gdp_growth
    path = []
    for i in range(years):
        gdp_idx = min(i, len(scenario.gdp_growth) - 1)
        base_gdp_idx = min(i, len(baseline_gdp) - 1)

        gdp_delta = scenario.gdp_growth[gdp_idx] - baseline_gdp[base_gdp_idx]
        fx_delta = 0.0
        if i < len(scenario.krw_usd) and scenario.krw_usd[0] > 0:
            fx_pct = (scenario.krw_usd[min(i, len(scenario.krw_usd) - 1)] / scenario.krw_usd[0] - 1) * 100
            fx_delta = fx_pct / 10 * elasticity.revenue_to_fx  # 환율 10% 변화당

        growth = base_growth + gdp_delta * elasticity.revenue_to_gdp + fx_delta
        # mean reversion: 극단 시나리오는 3~5년차에 baseline 복귀 경향
        if i >= 2:
            growth = growth * 0.7 + base_growth * 0.3
        if i >= 4:
            growth = growth * 0.5 + base_growth * 0.5

        path.append(round(growth, 2))
    return path


def _dcf_from_proforma(
    proforma: ProFormaResult,
    wacc: float,
    terminal_growth: float = 2.0,
    shares: int | None = None,
) -> tuple[float, float, float]:
    """Pro-forma FCF → Terminal Value → EV → Equity → 주당가치.

    Returns:
        (enterprise_value, equity_value, per_share_value)
    """
    if not proforma.projections:
        return 0.0, 0.0, 0.0

    discount_rate = wacc / 100
    tg = terminal_growth / 100

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
        per_share = equity_value  # 주식수 없으면 총 equity 반환

    return enterprise_value, equity_value, max(per_share, 0)


def _monte_carlo_price_distribution(
    series: dict,
    base_growth: float,
    elasticity: SectorElasticity,
    wacc: float,
    terminal_growth: float,
    shares: int | None,
    iterations: int = 5000,
    seed: int | None = None,
    size_class: str = "Mid",
) -> tuple[dict[str, float], float | None, list[float]]:
    """v2 Multi-Noise MC — 5변수 동시 noise + NWC + sizeClass σ.

    5개 변수: growth, margin, wacc, capex, tax
    sizeClass별 σ 차등: Small 1.5x, Mid 1.0x, Large 0.8x

    Returns:
        (percentiles, probability_above_current, all_values)
    """
    if seed is not None:
        random.seed(seed)

    ratios = extract_historical_ratios(series)
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
    tg = terminal_growth / 100
    values: list[float] = []

    # v2: sizeClass별 σ
    sigma_growth = get_noise_sigma("growth", size_class)
    sigma_margin = get_noise_sigma("margin", size_class)
    sigma_wacc = get_noise_sigma("wacc", size_class)
    sigma_capex = get_noise_sigma("capex", size_class)
    sigma_tax = get_noise_sigma("tax", size_class)

    for _ in range(iterations):
        # v2: 5변수 noise
        growth_noise = random.gauss(0, sigma_growth)
        margin_noise = random.gauss(0, sigma_margin)
        wacc_noise = random.gauss(0, sigma_wacc)
        capex_noise = random.gauss(0, sigma_capex)
        tax_noise = random.gauss(0, sigma_tax)

        noisy_growth = base_growth + growth_noise
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
                op_income = gross - rev * ratios.sga_ratio / 100
            else:
                op_income = gross - rev * ratios.sga_ratio / 100 - dep
            ebitda = op_income + dep
            ebt = max(op_income, 0)
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
        else:
            tv = 0
        pv_tv = tv / ((1 + noisy_wacc) ** 5)

        ev = fcf_pv + pv_tv
        eq = ev - base["total_debt"] + base["cash"]
        per_share = eq / shares if shares and shares > 0 else eq
        values.append(max(per_share, 0))

    if not values:
        return {}, None, []

    values.sort()
    n = len(values)

    def pct(p: float) -> float:
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


def _classify_signal(
    upside_pct: float | None,
    percentiles: dict[str, float],
    current_price: float | None,
) -> str:
    """upside와 분포로 투자 신호 판정."""
    if upside_pct is None:
        return "hold"

    p10 = percentiles.get("p10", 0)
    p90 = percentiles.get("p90", float("inf"))

    if upside_pct > 30 and current_price and p10 > current_price:
        return "strong_buy"
    if upside_pct > 15:
        return "buy"
    if upside_pct < -30 and current_price and p90 < current_price:
        return "strong_sell"
    if upside_pct < -15:
        return "sell"
    return "hold"


def compute_price_target(
    series: dict,
    sector_key: str | None = None,
    current_price: float | None = None,
    shares: int | None = None,
    market_cap: float | None = None,
    terminal_growth: float = 2.0,
    mc_iterations: int = 5000,
    mc_seed: int | None = None,
    scenario_probabilities: dict[str, float] | None = None,
    context_signals: ContextSignals | None = None,
) -> PriceTargetResult:
    """메인 — 5시나리오 × pro-forma → DCF → Monte Carlo → 확률 분포 → signal.

    v2: context_signals가 있으면 확률 동적 재가중 + sizeClass별 MC σ 차등.

    Args:
        series: 시계열 dict (unwrap 완료).
        sector_key: 업종 키 (SectorElasticity 조회).
        current_price: 현재 주가 (원).
        shares: 발행주식수.
        market_cap: 시가총액 (WACC의 equity weight 계산용).
        terminal_growth: 영구성장률 (%).
        mc_iterations: Monte Carlo 반복 횟수.
        mc_seed: 난수 시드 (재현용).
        scenario_probabilities: 시나리오별 확률 오버라이드.
        context_signals: v2 맥락 신호 (확률 재가중 + MC σ 차등).
    """
    warnings: list[str] = []
    probs = scenario_probabilities or dict(SCENARIO_PROBABILITIES)
    elasticity = get_elasticity(sector_key)

    # v2: context_signals가 있으면 확률 재가중
    size_class = "Mid"
    if context_signals:
        size_class = context_signals.size_class
        probs = adjust_probabilities(probs, context_signals)
        if context_signals.reasoning:
            warnings.append(f"맥락 기반 확률 재가중 ({len(context_signals.reasoning)}개 규칙 적용)")

    # WACC 계산 — v2: 업종 β 활용
    wacc, wacc_details = compute_company_wacc(
        series,
        sector_elasticity=elasticity,
        market_cap=market_cap,
    )

    # 기준 매출 성장률 (3년 CAGR)
    from dartlab.engines.common.finance.extract import getRevenueGrowth3Y

    base_growth = getRevenueGrowth3Y(series)
    if base_growth is None:
        base_growth = 3.0
        warnings.append("매출 성장률 데이터 부족 — 기본값 3% 사용")

    # 반도체 아닌 업종은 semiconductor_down 확률을 baseline에 재배분
    if sector_key and sector_key != "반도체" and "semiconductor_down" in probs:
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

        rev_path = _derive_revenue_path_from_macro(base_growth, scenario, elasticity)
        pf = build_proforma(
            series,
            revenue_growth_path=rev_path,
            sector_elasticity=elasticity,
            market_cap=market_cap,
            scenario_name=scenario.label,
        )
        ev, eq, per_share = _dcf_from_proforma(pf, wacc, terminal_growth, shares)

        # Implied P/E
        last_ni = pf.projections[-1].net_income if pf.projections else 0
        implied_per = eq / last_ni if last_ni and last_ni > 0 else None

        scenario_targets.append(
            ScenarioPriceTarget(
                scenario_name=name,
                probability=prob,
                proforma=pf,
                enterprise_value=ev,
                equity_value=eq,
                per_share_value=per_share,
                wacc_used=wacc,
                terminal_growth=terminal_growth,
                implied_per=implied_per,
            )
        )

    # 가중 목표가
    weighted_target = sum(s.per_share_value * s.probability for s in scenario_targets)

    # Monte Carlo 분포
    percentiles, _, mc_values = _monte_carlo_price_distribution(
        series,
        base_growth,
        elasticity,
        wacc,
        terminal_growth,
        shares,
        mc_iterations,
        mc_seed,
        size_class=size_class,
    )

    # upside
    upside_pct: float | None = None
    prob_above: float | None = None
    if current_price and current_price > 0:
        upside_pct = (weighted_target / current_price - 1) * 100
        if mc_values:
            above_count = sum(1 for v in mc_values if v > current_price)
            prob_above = above_count / len(mc_values) * 100

    # expected value (MC 평균)
    expected_value = sum(mc_values) / len(mc_values) if mc_values else weighted_target

    # signal
    signal = _classify_signal(upside_pct, percentiles, current_price)

    # 신뢰도
    ratios = extract_historical_ratios(series)
    confidence = ratios.confidence

    return PriceTargetResult(
        scenarios=scenario_targets,
        weighted_target=weighted_target,
        percentiles=percentiles,
        expected_value=expected_value,
        current_price=current_price,
        upside_pct=upside_pct,
        probability_above_current=prob_above,
        signal=signal,
        confidence=confidence,
        wacc_details=wacc_details,
        warnings=warnings,
    )
