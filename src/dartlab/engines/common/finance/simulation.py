"""경제 시나리오 기반 시뮬레이션 예측 엔진.

3-Layer 구조:
1. MacroScenario — 거시경제 변수 경로 (GDP, 금리, 환율, CPI)
2. SectorElasticity — 업종별 거시경제 감응도 (β)
3. CompanySimulation — 기업 실적 시뮬레이션 (시나리오 + Monte Carlo + 스트레스)

외부 의존성 제로 (random 모듈만 사용).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from dartlab.engines.common.finance.extract import (
    getAnnualValues,
    getLatest,
    getTTM,
)
from dartlab.engines.analysis.sector.types import SectorParams

# ══════════════════════════════════════
# Layer 1: 거시경제 시나리오
# ══════════════════════════════════════


@dataclass
class MacroScenario:
    """거시경제 시나리오 정의."""

    name: str
    label: str
    gdp_growth: list[float]  # 3년 GDP 성장률 (%)
    interest_rate: list[float]  # 3년 기준금리 (%)
    krw_usd: list[float]  # 3년 환율
    cpi: list[float]  # 3년 CPI (%)
    description: str = ""

    def __repr__(self) -> str:
        lines = [f"[{self.label}]"]
        lines.append(f"  GDP: {' → '.join(f'{g:+.1f}%' for g in self.gdp_growth)}")
        lines.append(f"  금리: {' → '.join(f'{r:.1f}%' for r in self.interest_rate)}")
        lines.append(f"  환율: {' → '.join(f'{x:,.0f}' for x in self.krw_usd)}")
        if self.description:
            lines.append(f"  설명: {self.description}")
        return "\n".join(lines)


# 한국 기준 사전 정의 시나리오
BASELINE_RATE = 2.5  # 현재 BOK 기준금리
BASELINE_FX = 1470  # 현재 KRW/USD

PRESET_SCENARIOS: dict[str, MacroScenario] = {
    "baseline": MacroScenario(
        "baseline",
        "기준 시나리오",
        gdp_growth=[1.5, 2.0, 2.2],
        interest_rate=[2.5, 2.5, 2.5],
        krw_usd=[1470, 1470, 1470],
        cpi=[2.2, 2.1, 2.0],
        description="현재 추세 유지",
    ),
    "adverse": MacroScenario(
        "adverse",
        "경기침체",
        gdp_growth=[-3.0, -1.0, 0.5],
        interest_rate=[1.0, 1.5, 2.0],
        krw_usd=[1600, 1580, 1550],
        cpi=[1.2, 1.5, 2.0],
        description="CCAR 스타일 심각한 경기침체 + 원화 약세",
    ),
    "china_slowdown": MacroScenario(
        "china_slowdown",
        "중국 경기둔화",
        gdp_growth=[-1.5, -0.5, 1.0],
        interest_rate=[1.5, 1.5, 2.0],
        krw_usd=[1550, 1520, 1480],
        cpi=[1.8, 1.9, 2.0],
        description="중국 수요 감소 → 한국 수출 타격",
    ),
    "rate_hike": MacroScenario(
        "rate_hike",
        "금리 인상",
        gdp_growth=[1.0, 1.5, 2.0],
        interest_rate=[3.5, 4.0, 4.0],
        krw_usd=[1400, 1380, 1400],
        cpi=[3.0, 2.8, 2.5],
        description="인플레이션 대응 긴축 + 원화 강세",
    ),
    "semiconductor_down": MacroScenario(
        "semiconductor_down",
        "반도체 불황",
        gdp_growth=[-2.0, -0.5, 1.5],
        interest_rate=[2.0, 2.0, 2.5],
        krw_usd=[1550, 1520, 1500],
        cpi=[1.5, 1.8, 2.0],
        description="DRAM/NAND 가격 급락 + 글로벌 수요 감소",
    ),
}


# ══════════════════════════════════════
# Layer 2: 업종별 거시경제 감응도
# ══════════════════════════════════════


@dataclass
class SectorElasticity:
    """업종별 거시경제 감응도."""

    revenue_to_gdp: float  # GDP 1%p 변화 → 매출 변화 (배수, β)
    revenue_to_fx: float  # 환율 10% 약세 → 매출 변화 (%)
    margin_to_gdp: float  # GDP 1%p 변화 → 마진 변화 (bps)
    nim_to_rate: float  # 금리 100bps 변화 → NIM 변화 (bps, 금융업만)
    cyclicality: str  # "high" | "moderate" | "low" | "defensive"

    def __repr__(self) -> str:
        return f"β(GDP)={self.revenue_to_gdp:.1f}, β(FX)={self.revenue_to_fx:.1f}, {self.cyclicality}"


SECTOR_ELASTICITY: dict[str, SectorElasticity] = {
    "반도체": SectorElasticity(1.8, 0.8, 50, 0, "high"),
    "자동차": SectorElasticity(1.3, 0.6, 30, 0, "high"),
    "화학": SectorElasticity(1.2, 0.4, 25, 0, "high"),
    "철강": SectorElasticity(1.4, 0.3, 30, 0, "high"),
    "건설": SectorElasticity(1.5, 0.1, 40, 0, "high"),
    "금융/은행": SectorElasticity(1.0, 0.1, 20, 15, "moderate"),
    "금융/보험": SectorElasticity(0.8, 0.1, 15, 10, "moderate"),
    "금융/증권": SectorElasticity(1.5, 0.2, 40, 5, "high"),
    "IT/소프트웨어": SectorElasticity(1.0, 0.3, 20, 0, "moderate"),
    "통신": SectorElasticity(0.4, 0.05, 10, 0, "defensive"),
    "유통": SectorElasticity(0.8, 0.1, 15, 0, "moderate"),
    "식품": SectorElasticity(0.3, 0.05, 5, 0, "defensive"),
    "제약/바이오": SectorElasticity(0.5, 0.2, 10, 0, "low"),
    "전력/에너지": SectorElasticity(0.3, 0.15, 10, 0, "defensive"),
    "섬유/의류": SectorElasticity(0.9, 0.3, 20, 0, "moderate"),
}

DEFAULT_ELASTICITY = SectorElasticity(0.8, 0.2, 15, 0, "moderate")


def get_elasticity(sector_key: Optional[str]) -> SectorElasticity:
    """업종 키로 감응도 조회."""
    if sector_key is None:
        return DEFAULT_ELASTICITY
    return SECTOR_ELASTICITY.get(sector_key, DEFAULT_ELASTICITY)


# ══════════════════════════════════════
# Layer 3: 기업 시뮬레이션
# ══════════════════════════════════════

# ── 결과 타입 ──


@dataclass
class SimulationResult:
    """단일 시나리오 시뮬레이션 결과."""

    scenario_name: str
    scenario_label: str
    years: int
    revenue_path: list[float]
    operating_income_path: list[float]
    margin_path: list[float]
    fcf_path: list[float]
    dcf_value: float
    per_share_value: Optional[float]
    revenue_change_pct: float
    margin_change_bps: float
    elasticity_used: SectorElasticity
    assumptions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 시뮬레이션은 참고용이며 실제 경제 상황과 다를 수 있습니다."

    def __repr__(self) -> str:
        lines = [f"[{self.scenario_label} 시뮬레이션]"]
        lines.append(f"  경기감응도: {self.elasticity_used}")
        for i, (rev, oi, mg) in enumerate(
            zip(
                self.revenue_path,
                self.operating_income_path,
                self.margin_path,
            )
        ):
            lines.append(f"  +{i + 1}년: 매출 {rev / 1e8:,.0f}억, 영업이익 {oi / 1e8:,.0f}억, 마진 {mg:.1f}%")
        lines.append(f"  매출 변화: {self.revenue_change_pct:+.1f}%")
        lines.append(f"  마진 변화: {self.margin_change_bps:+.0f}bps")
        if self.per_share_value is not None:
            lines.append(f"  주당 가치: {self.per_share_value:,.0f}원")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class MonteCarloResult:
    """Monte Carlo 시뮬레이션 결과."""

    iterations: int
    scenario_name: str
    percentiles: dict[str, dict[str, float]]
    expected_value: float
    std_dev: float
    var_95: float
    upside_probability: float  # 현재 대비 상승 확률 (%)
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 시뮬레이션은 참고용이며 실제 경제 상황과 다를 수 있습니다."

    def __repr__(self) -> str:
        lines = [f"[Monte Carlo — {self.scenario_name} ({self.iterations:,}회)]"]
        for metric, pcts in self.percentiles.items():
            p5 = pcts.get("p5", 0)
            p50 = pcts.get("p50", 0)
            p95 = pcts.get("p95", 0)
            lines.append(f"  {metric}: P5={p5 / 1e8:,.0f}억  P50={p50 / 1e8:,.0f}억  P95={p95 / 1e8:,.0f}억")
        lines.append(f"  기대값: {self.expected_value / 1e8:,.0f}억")
        lines.append(f"  VaR(95%): {self.var_95 / 1e8:,.0f}억")
        lines.append(f"  상승 확률: {self.upside_probability:.0f}%")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class StressTestResult:
    """스트레스 테스트 결과."""

    scenario_name: str
    scenario_label: str
    year_3_revenue_change: float
    year_3_margin_change: float
    year_3_debt_ratio: Optional[float]
    year_3_current_ratio: Optional[float]
    year_3_interest_coverage: Optional[float]
    survival_risk: str  # "low" | "medium" | "high" | "critical"
    dividend_sustainable: bool
    recovery_timeline: str
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 시뮬레이션은 참고용이며 실제 경제 상황과 다를 수 있습니다."

    def __repr__(self) -> str:
        lines = [f"[스트레스 테스트 — {self.scenario_label}]"]
        lines.append(f"  3년 후 매출 변화: {self.year_3_revenue_change:+.1f}%")
        lines.append(f"  3년 후 마진 변화: {self.year_3_margin_change:+.0f}bps")
        if self.year_3_debt_ratio is not None:
            lines.append(f"  3년 후 부채비율: {self.year_3_debt_ratio:.0f}%")
        if self.year_3_current_ratio is not None:
            lines.append(f"  3년 후 유동비율: {self.year_3_current_ratio:.0f}%")
        if self.year_3_interest_coverage is not None:
            lines.append(f"  3년 후 이자보상배율: {self.year_3_interest_coverage:.1f}x")
        lines.append(f"  생존 위험도: {self.survival_risk}")
        lines.append(f"  배당 지속: {'가능' if self.dividend_sustainable else '불가능'}")
        lines.append(f"  회복 전망: {self.recovery_timeline}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ── 내부 유틸 ──


def _extract_base_metrics(series: dict) -> dict[str, Optional[float]]:
    """현재 기업 기본 지표 추출."""
    rev = getTTM(series, "IS", "sales") or getTTM(series, "IS", "revenue")
    oi = getTTM(series, "IS", "operating_profit") or getTTM(series, "IS", "operating_income")
    ni = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income")
    ocf = getTTM(series, "CF", "operating_cashflow")
    capex = getTTM(series, "CF", "purchase_of_property_plant_and_equipment")
    div = getTTM(series, "CF", "dividends_paid")

    margin = (oi / rev * 100) if rev and oi and rev > 0 else None
    fcf = (ocf - abs(capex or 0)) if ocf is not None else None

    total_assets = getLatest(series, "BS", "total_assets")
    total_equity = getLatest(series, "BS", "total_stockholders_equity") or getLatest(
        series, "BS", "owners_of_parent_equity"
    )
    total_liab = getLatest(series, "BS", "total_liabilities")
    current_assets = getLatest(series, "BS", "current_assets")
    current_liab = getLatest(series, "BS", "current_liabilities")
    cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
    stb = getLatest(series, "BS", "shortterm_borrowings") or 0
    ltb = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "debentures") or 0
    fin_costs = getTTM(series, "IS", "finance_costs") or getTTM(series, "IS", "interest_expense")

    debt_ratio = (total_liab / total_equity * 100) if total_liab and total_equity and total_equity > 0 else None
    current_ratio = (
        (current_assets / current_liab * 100) if current_assets and current_liab and current_liab > 0 else None
    )
    interest_cov = (oi / abs(fin_costs)) if oi and fin_costs and abs(fin_costs) > 0 else None
    net_debt = stb + ltb + bonds - cash

    return {
        "revenue": rev,
        "operating_income": oi,
        "net_income": ni,
        "margin": margin,
        "ocf": ocf,
        "fcf": fcf,
        "capex": capex,
        "dividends_paid": div,
        "total_assets": total_assets,
        "total_equity": total_equity,
        "total_liabilities": total_liab,
        "current_assets": current_assets,
        "current_liabilities": current_liab,
        "debt_ratio": debt_ratio,
        "current_ratio": current_ratio,
        "interest_coverage": interest_cov,
        "net_debt": net_debt,
        "finance_costs": fin_costs,
    }


def _extract_volatility(series: dict) -> dict[str, float]:
    """과거 시계열에서 변동성(σ) 추출.

    Returns:
        {"revenue_cv": X, "margin_std": Y, "fcf_cv": Z}
    """
    rev_vals = getAnnualValues(series, "IS", "sales") or getAnnualValues(series, "IS", "revenue")
    oi_vals = getAnnualValues(series, "IS", "operating_profit") or getAnnualValues(series, "IS", "operating_income")

    def _std(values: list) -> float:
        valid = [v for v in values if v is not None]
        if len(valid) < 3:
            return 0.1  # 기본값 10%
        mean = sum(valid) / len(valid)
        if abs(mean) < 1e-12:
            return 0.1
        variance = sum((v - mean) ** 2 for v in valid) / (len(valid) - 1)
        return math.sqrt(variance) / abs(mean)

    def _margin_std(rev_list: list, oi_list: list) -> float:
        margins = []
        for r, o in zip(rev_list, oi_list):
            if r is not None and o is not None and r > 0:
                margins.append(o / r * 100)
        if len(margins) < 3:
            return 2.0  # 기본 2%p
        mean = sum(margins) / len(margins)
        variance = sum((m - mean) ** 2 for m in margins) / (len(margins) - 1)
        return math.sqrt(variance)

    return {
        "revenue_cv": _std(rev_vals),
        "margin_std": _margin_std(rev_vals, oi_vals),
    }


def _apply_macro_shock(
    base_revenue: float,
    base_margin: float,
    scenario: MacroScenario,
    elasticity: SectorElasticity,
    year_idx: int,
    base_wacc: float,
) -> tuple[float, float, float]:
    """매크로 충격 적용 → (조정 매출, 조정 마진%, 조정 할인율).

    Revenue' = Revenue × (1 + β_gdp × ΔGDP/100 + β_fx × (ΔFX/FX_base)/10)
    Margin' = Margin + margin_to_gdp × ΔGDP / 100
    WACC' = base_wacc + (ΔRate × 0.5)  (금리 100bps → WACC 50bps 연동)
    """
    gdp = scenario.gdp_growth[year_idx]
    rate = scenario.interest_rate[year_idx]
    fx = scenario.krw_usd[year_idx]

    # GDP 충격
    rev_gdp_effect = elasticity.revenue_to_gdp * gdp / 100

    # 환율 충격 (baseline 대비 변화율)
    fx_change_pct = (fx - BASELINE_FX) / BASELINE_FX * 100
    rev_fx_effect = elasticity.revenue_to_fx * fx_change_pct / 1000  # 10%당 β 적용

    adjusted_revenue = base_revenue * (1 + rev_gdp_effect + rev_fx_effect)

    # 마진 충격
    margin_shock_bps = elasticity.margin_to_gdp * gdp / 100
    # NIM 충격 (금융업)
    rate_change = rate - BASELINE_RATE
    nim_shock_bps = elasticity.nim_to_rate * rate_change / 100
    adjusted_margin = base_margin + margin_shock_bps + nim_shock_bps

    # WACC 조정 (금리 변동의 50% 반영)
    adjusted_wacc = base_wacc + rate_change * 0.5

    return adjusted_revenue, max(adjusted_margin, -50), adjusted_wacc


# ── 시나리오 시뮬레이션 ──


def simulate_scenario(
    series: dict,
    scenario: MacroScenario | str,
    sector_key: Optional[str] = None,
    sector_params: Optional[SectorParams] = None,
    shares: Optional[int] = None,
) -> SimulationResult:
    """단일 거시경제 시나리오 하에서 3년 실적 경로 시뮬레이션.

    Args:
        series: finance timeseries dict.
        scenario: MacroScenario 또는 preset 이름.
        sector_key: 업종 키 (SECTOR_ELASTICITY 조회용).
        sector_params: 섹터 파라미터 (할인율).
        shares: 발행주식수.

    Returns:
        SimulationResult.
    """
    warnings: list[str] = []

    # 시나리오 로드
    if isinstance(scenario, str):
        sc = PRESET_SCENARIOS.get(scenario)
        if sc is None:
            return SimulationResult(
                scenario_name=scenario,
                scenario_label="알 수 없음",
                years=0,
                revenue_path=[],
                operating_income_path=[],
                margin_path=[],
                fcf_path=[],
                dcf_value=0,
                per_share_value=None,
                revenue_change_pct=0,
                margin_change_bps=0,
                elasticity_used=DEFAULT_ELASTICITY,
                warnings=[f"미지원 시나리오: {scenario}. 선택지: {', '.join(PRESET_SCENARIOS)}"],
            )
    else:
        sc = scenario

    elasticity = get_elasticity(sector_key)
    base = _extract_base_metrics(series)
    base_wacc = sector_params.discountRate if sector_params else 10.0

    rev = base["revenue"]
    margin = base["margin"]
    if rev is None or rev <= 0:
        return SimulationResult(
            scenario_name=sc.name,
            scenario_label=sc.label,
            years=0,
            revenue_path=[],
            operating_income_path=[],
            margin_path=[],
            fcf_path=[],
            dcf_value=0,
            per_share_value=None,
            revenue_change_pct=0,
            margin_change_bps=0,
            elasticity_used=elasticity,
            warnings=["매출 데이터 부족"],
        )

    if margin is None:
        margin = 10.0
        warnings.append("마진 데이터 미확인 → 10%로 가정")

    capex_ratio = abs(base["capex"] or 0) / rev if rev > 0 else 0.05
    tax_rate = 0.22  # 한국 법인세 기본

    # 3년 경로 시뮬레이션
    horizon = min(len(sc.gdp_growth), 3)
    revenue_path: list[float] = []
    oi_path: list[float] = []
    margin_path: list[float] = []
    fcf_path: list[float] = []
    wacc_path: list[float] = []

    prev_rev = rev
    prev_margin = margin

    for yr in range(horizon):
        adj_rev, adj_margin, adj_wacc = _apply_macro_shock(
            prev_rev,
            prev_margin,
            sc,
            elasticity,
            yr,
            base_wacc,
        )
        adj_oi = adj_rev * adj_margin / 100
        adj_fcf = adj_oi * (1 - tax_rate) - adj_rev * capex_ratio

        revenue_path.append(adj_rev)
        oi_path.append(adj_oi)
        margin_path.append(adj_margin)
        fcf_path.append(adj_fcf)
        wacc_path.append(adj_wacc)

        prev_rev = adj_rev
        prev_margin = adj_margin

    # DCF 가치 (시나리오 경로의 FCF 합산)
    terminal_growth = min(sector_params.growthRate if sector_params else 3.0, 3.0)
    last_wacc = wacc_path[-1] if wacc_path else base_wacc

    if last_wacc <= terminal_growth:
        terminal_growth = max(last_wacc - 2.0, 0.5)

    pv_sum = sum(fcf / (1 + last_wacc / 100) ** (yr + 1) for yr, fcf in enumerate(fcf_path))
    terminal_fcf = fcf_path[-1] if fcf_path else 0
    if terminal_fcf > 0:
        tv = terminal_fcf * (1 + terminal_growth / 100) / (last_wacc / 100 - terminal_growth / 100)
        pv_tv = tv / (1 + last_wacc / 100) ** horizon
    else:
        tv = 0
        pv_tv = 0
        warnings.append("FCF 음수 → Terminal Value 미적용")

    ev = pv_sum + pv_tv
    net_debt = base["net_debt"] or 0
    equity_value = ev - net_debt
    per_share = equity_value / shares if shares and shares > 0 else None

    # 변화율 계산
    final_rev = revenue_path[-1] if revenue_path else rev
    rev_change = (final_rev - rev) / rev * 100 if rev > 0 else 0
    margin_change = (margin_path[-1] - margin) * 100 if margin_path else 0  # bps

    return SimulationResult(
        scenario_name=sc.name,
        scenario_label=sc.label,
        years=horizon,
        revenue_path=revenue_path,
        operating_income_path=oi_path,
        margin_path=margin_path,
        fcf_path=fcf_path,
        dcf_value=ev,
        per_share_value=per_share,
        revenue_change_pct=round(rev_change, 1),
        margin_change_bps=round(margin_change, 0),
        elasticity_used=elasticity,
        assumptions={
            "경기감응도(β)": f"GDP {elasticity.revenue_to_gdp:.1f}, FX {elasticity.revenue_to_fx:.1f}",
            "업종 경기민감도": elasticity.cyclicality,
            "할인율": f"{base_wacc:.1f}% → {last_wacc:.1f}%",
            "CapEx 비율": f"{capex_ratio * 100:.1f}%",
        },
        warnings=warnings,
    )


def simulate_all_scenarios(
    series: dict,
    sector_key: Optional[str] = None,
    sector_params: Optional[SectorParams] = None,
    shares: Optional[int] = None,
    scenarios: Optional[list[str]] = None,
) -> dict[str, SimulationResult]:
    """모든 사전 정의 시나리오 일괄 시뮬레이션."""
    keys = scenarios or list(PRESET_SCENARIOS.keys())
    return {
        key: simulate_scenario(series, key, sector_key, sector_params, shares)
        for key in keys
        if key in PRESET_SCENARIOS
    }


# ── Monte Carlo 시뮬레이션 ──


def monte_carlo_forecast(
    series: dict,
    sector_key: Optional[str] = None,
    sector_params: Optional[SectorParams] = None,
    shares: Optional[int] = None,
    scenario: MacroScenario | str = "baseline",
    iterations: int = 10000,
    horizon: int = 3,
    seed: Optional[int] = None,
) -> MonteCarloResult:
    """Monte Carlo 시뮬레이션 (순수 Python).

    1. 과거 시계열에서 σ(매출), σ(마진) 추출
    2. 매크로 시나리오 기반 μ(평균 경로) 계산
    3. 각 iteration: 정규분포 노이즈 추가
    4. 백분위 산출

    Args:
        series: finance timeseries.
        sector_key: 업종 키.
        sector_params: 섹터 파라미터.
        shares: 발행주식수.
        scenario: 기준 시나리오.
        iterations: 반복 횟수 (기본 10,000).
        horizon: 예측 기간 (년).
        seed: 난수 시드 (재현성).

    Returns:
        MonteCarloResult.
    """
    if seed is not None:
        random.seed(seed)

    warnings: list[str] = []

    # 시나리오 로드
    if isinstance(scenario, str):
        sc = PRESET_SCENARIOS.get(scenario, PRESET_SCENARIOS["baseline"])
    else:
        sc = scenario

    elasticity = get_elasticity(sector_key)
    base = _extract_base_metrics(series)
    vol = _extract_volatility(series)
    base_wacc = sector_params.discountRate if sector_params else 10.0

    rev = base["revenue"]
    margin = base["margin"]
    if rev is None or rev <= 0:
        return MonteCarloResult(
            iterations=iterations,
            scenario_name=sc.name,
            percentiles={},
            expected_value=0,
            std_dev=0,
            var_95=0,
            upside_probability=0,
            warnings=["매출 데이터 부족"],
        )
    if margin is None:
        margin = 10.0

    rev_cv = min(vol["revenue_cv"], 0.5)  # 상한 50%
    margin_std = min(vol["margin_std"], 10.0)  # 상한 10%p

    # 평균 경로 계산 (시나리오 기반)
    mean_rev_path: list[float] = []
    mean_margin_path: list[float] = []
    prev_r, prev_m = rev, margin
    for yr in range(min(horizon, len(sc.gdp_growth))):
        ar, am, _ = _apply_macro_shock(prev_r, prev_m, sc, elasticity, yr, base_wacc)
        mean_rev_path.append(ar)
        mean_margin_path.append(am)
        prev_r, prev_m = ar, am

    # Monte Carlo 실행
    final_revenues: list[float] = []
    final_ois: list[float] = []
    final_fcfs: list[float] = []

    capex_ratio = abs(base["capex"] or 0) / rev if rev > 0 else 0.05
    tax_rate = 0.22

    for _ in range(iterations):
        sim_rev = rev
        sim_margin = margin
        for yr in range(len(mean_rev_path)):
            # 평균 경로에 노이즈 추가
            rev_noise = random.gauss(0, rev_cv)
            margin_noise = random.gauss(0, margin_std)

            sim_rev = mean_rev_path[yr] * (1 + rev_noise)
            sim_margin = mean_margin_path[yr] + margin_noise

        sim_oi = sim_rev * max(sim_margin, -50) / 100
        sim_fcf = sim_oi * (1 - tax_rate) - sim_rev * capex_ratio

        final_revenues.append(sim_rev)
        final_ois.append(sim_oi)
        final_fcfs.append(sim_fcf)

    # 백분위 산출
    def _percentiles(vals: list[float]) -> dict[str, float]:
        sorted_vals = sorted(vals)
        n = len(sorted_vals)
        return {
            "p5": sorted_vals[int(n * 0.05)],
            "p25": sorted_vals[int(n * 0.25)],
            "p50": sorted_vals[int(n * 0.50)],
            "p75": sorted_vals[int(n * 0.75)],
            "p95": sorted_vals[int(n * 0.95)],
        }

    percentiles = {
        "매출": _percentiles(final_revenues),
        "영업이익": _percentiles(final_ois),
        "FCF": _percentiles(final_fcfs),
    }

    # 통계
    mean_rev_final = sum(final_revenues) / iterations
    std_dev = math.sqrt(sum((r - mean_rev_final) ** 2 for r in final_revenues) / (iterations - 1))
    var_95 = sorted(final_revenues)[int(iterations * 0.05)]
    upside_prob = sum(1 for r in final_revenues if r > rev) / iterations * 100

    if rev_cv >= 0.4:
        warnings.append("과거 매출 변동성 높음 → 시뮬레이션 신뢰도 낮음")

    return MonteCarloResult(
        iterations=iterations,
        scenario_name=sc.label,
        percentiles=percentiles,
        expected_value=mean_rev_final,
        std_dev=std_dev,
        var_95=var_95,
        upside_probability=round(upside_prob, 1),
        warnings=warnings,
    )


# ── 스트레스 테스트 ──


def stress_test(
    series: dict,
    sector_key: Optional[str] = None,
    sector_params: Optional[SectorParams] = None,
    scenario: str = "adverse",
) -> StressTestResult:
    """CCAR 스타일 스트레스 테스트.

    3년 경기침체 시나리오 하에서:
    - 매출/이익 경로
    - 부채비율/유동비율 변화 추정
    - 배당 지속 가능성
    - 생존 위험도 판단

    Args:
        series: finance timeseries.
        sector_key: 업종 키.
        sector_params: 섹터 파라미터.
        scenario: 스트레스 시나리오 이름.

    Returns:
        StressTestResult.
    """
    warnings: list[str] = []

    sim = simulate_scenario(series, scenario, sector_key, sector_params)
    base = _extract_base_metrics(series)

    sc = PRESET_SCENARIOS.get(scenario, PRESET_SCENARIOS["adverse"])

    # 3년 후 재무 건전성 추정
    rev_change = sim.revenue_change_pct
    margin_change = sim.margin_change_bps

    # 부채비율 추정: 이익 감소 → 자본 감소 → 부채비율 상승
    debt_ratio_3y = None
    if base["debt_ratio"] is not None and base["total_equity"] and base["total_equity"] > 0:
        # 3년간 누적 이익 변화 반영
        cum_profit_loss = sum(sim.operating_income_path) * 0.78 if sim.operating_income_path else 0
        baseline_profit = (base["operating_income"] or 0) * 0.78 * 3
        equity_change = cum_profit_loss - baseline_profit
        new_equity = base["total_equity"] + equity_change
        if new_equity > 0:
            debt_ratio_3y = round((base["total_liabilities"] or 0) / new_equity * 100, 0)
        else:
            debt_ratio_3y = 9999
            warnings.append("스트레스 하 자본잠식 위험")

    # 유동비율 추정
    current_ratio_3y = base["current_ratio"]
    if current_ratio_3y is not None and rev_change < -10:
        current_ratio_3y = current_ratio_3y * (1 + rev_change / 100 * 0.3)  # 보수적 조정

    # 이자보상배율
    int_cov_3y = None
    if sim.operating_income_path and base["finance_costs"] and abs(base["finance_costs"]) > 0:
        int_cov_3y = round(sim.operating_income_path[-1] / abs(base["finance_costs"]), 1)

    # 배당 지속 가능성
    div_sustainable = True
    if base["dividends_paid"] and sim.fcf_path:
        final_fcf = sim.fcf_path[-1]
        div_amount = abs(base["dividends_paid"] or 0)
        if final_fcf < div_amount:
            div_sustainable = False

    # 생존 위험도 판단
    risk_score = 0
    if rev_change < -20:
        risk_score += 2
    elif rev_change < -10:
        risk_score += 1

    if debt_ratio_3y is not None and debt_ratio_3y > 300:
        risk_score += 2
    elif debt_ratio_3y is not None and debt_ratio_3y > 200:
        risk_score += 1

    if int_cov_3y is not None and int_cov_3y < 1:
        risk_score += 2
    elif int_cov_3y is not None and int_cov_3y < 2:
        risk_score += 1

    if not div_sustainable:
        risk_score += 1

    if risk_score >= 5:
        survival_risk = "critical"
    elif risk_score >= 3:
        survival_risk = "high"
    elif risk_score >= 1:
        survival_risk = "medium"
    else:
        survival_risk = "low"

    # 회복 전망
    elasticity = get_elasticity(sector_key)
    if elasticity.cyclicality == "high":
        recovery = "V자 반등 가능 (경기민감 업종)"
    elif elasticity.cyclicality == "defensive":
        recovery = "안정적 — 충격 자체가 제한적"
    else:
        recovery = "점진적 회복 (1~2년)"

    return StressTestResult(
        scenario_name=sc.name,
        scenario_label=sc.label,
        year_3_revenue_change=round(rev_change, 1),
        year_3_margin_change=round(margin_change, 0),
        year_3_debt_ratio=debt_ratio_3y,
        year_3_current_ratio=round(current_ratio_3y, 0) if current_ratio_3y else None,
        year_3_interest_coverage=int_cov_3y,
        survival_risk=survival_risk,
        dividend_sustainable=div_sustainable,
        recovery_timeline=recovery,
        warnings=warnings,
    )
