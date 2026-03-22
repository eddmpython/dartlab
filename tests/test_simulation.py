"""경제 시나리오 시뮬레이션 엔진 단위 테스트.

순수 dict 기반 테스트 — Company 로딩 없이 실행 가능.
"""

from __future__ import annotations

import pytest

# ── 테스트용 mock 시계열 ──────────────────────────────────


def _make_series(
    revenue: list = None,
    operating_profit: list = None,
    net_profit: list = None,
    operating_cashflow: list = None,
    capex: list = None,
    dividends_paid: list = None,
    total_assets: list = None,
    total_equity: list = None,
    total_liabilities: list = None,
    current_assets: list = None,
    current_liabilities: list = None,
    cash: list = None,
    stb: list = None,
    ltb: list = None,
    debentures: list = None,
) -> dict:
    """테스트용 간이 시계열 dict 생성."""
    series = {"IS": {}, "BS": {}, "CF": {}}

    if revenue is not None:
        series["IS"]["sales"] = revenue
    if operating_profit is not None:
        series["IS"]["operating_profit"] = operating_profit
    if net_profit is not None:
        series["IS"]["net_profit"] = net_profit

    if operating_cashflow is not None:
        series["CF"]["operating_cashflow"] = operating_cashflow
    if capex is not None:
        series["CF"]["purchase_of_property_plant_and_equipment"] = capex
    if dividends_paid is not None:
        series["CF"]["dividends_paid"] = dividends_paid

    if total_assets is not None:
        series["BS"]["total_assets"] = total_assets
    if total_equity is not None:
        series["BS"]["total_stockholders_equity"] = total_equity
    if total_liabilities is not None:
        series["BS"]["total_liabilities"] = total_liabilities
    if current_assets is not None:
        series["BS"]["current_assets"] = current_assets
    if current_liabilities is not None:
        series["BS"]["current_liabilities"] = current_liabilities
    if cash is not None:
        series["BS"]["cash_and_cash_equivalents"] = cash
    if stb is not None:
        series["BS"]["shortterm_borrowings"] = stb
    if ltb is not None:
        series["BS"]["longterm_borrowings"] = ltb
    if debentures is not None:
        series["BS"]["debentures"] = debentures

    return series


# 정상 기업 시계열 (매출 성장, FCF 양수, 배당 있음)
HEALTHY_SERIES = _make_series(
    revenue=[100e8, 120e8, 140e8, 160e8, 180e8],
    operating_profit=[10e8, 14e8, 18e8, 22e8, 25e8],
    net_profit=[8e8, 11e8, 14e8, 17e8, 20e8],
    operating_cashflow=[12e8, 15e8, 18e8, 22e8, 26e8],
    capex=[-3e8, -4e8, -5e8, -6e8, -7e8],
    dividends_paid=[-3e8, -3.1e8, -3.2e8, -3.3e8, -3.5e8],
    total_assets=[200e8, 220e8, 250e8, 280e8, 310e8],
    total_equity=[120e8, 135e8, 150e8, 170e8, 190e8],
    total_liabilities=[80e8, 85e8, 100e8, 110e8, 120e8],
    current_assets=[60e8, 70e8, 80e8, 90e8, 100e8],
    current_liabilities=[40e8, 42e8, 48e8, 50e8, 55e8],
    cash=[30e8, 35e8, 40e8, 45e8, 50e8],
    stb=[10e8, 10e8, 12e8, 12e8, 15e8],
    ltb=[20e8, 20e8, 25e8, 25e8, 30e8],
    debentures=[5e8, 5e8, 5e8, 5e8, 5e8],
)


@pytest.fixture
def sector_params():
    from dartlab.engines.analysis.sector.types import SectorParams

    return SectorParams(
        discountRate=10.0,
        growthRate=4.0,
        perMultiple=15,
        pbrMultiple=1.5,
        evEbitdaMultiple=8,
        label="테스트업종",
    )


# ══════════════════════════════════════
# MacroScenario 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestMacroScenario:
    def test_preset_scenarios_exist(self):
        from dartlab.engines.common.finance.simulation import PRESET_SCENARIOS

        assert len(PRESET_SCENARIOS) == 5
        assert "baseline" in PRESET_SCENARIOS
        assert "adverse" in PRESET_SCENARIOS
        assert "china_slowdown" in PRESET_SCENARIOS
        assert "rate_hike" in PRESET_SCENARIOS
        assert "semiconductor_down" in PRESET_SCENARIOS

    def test_scenario_structure(self):
        from dartlab.engines.common.finance.simulation import PRESET_SCENARIOS

        for name, sc in PRESET_SCENARIOS.items():
            assert len(sc.gdp_growth) == 3
            assert len(sc.interest_rate) == 3
            assert len(sc.krw_usd) == 3
            assert len(sc.cpi) == 3
            assert sc.name == name
            assert sc.label  # 비어있지 않음

    def test_scenario_repr(self):
        from dartlab.engines.common.finance.simulation import PRESET_SCENARIOS

        text = repr(PRESET_SCENARIOS["adverse"])
        assert "경기침체" in text
        assert "GDP" in text


# ══════════════════════════════════════
# SectorElasticity 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestSectorElasticity:
    def test_get_elasticity_known(self):
        from dartlab.engines.common.finance.simulation import get_elasticity

        e = get_elasticity("반도체")
        assert e.revenue_to_gdp == 1.8
        assert e.cyclicality == "high"

    def test_get_elasticity_unknown(self):
        from dartlab.engines.common.finance.simulation import (
            DEFAULT_ELASTICITY,
            get_elasticity,
        )

        e = get_elasticity("존재하지않는업종")
        assert e == DEFAULT_ELASTICITY

    def test_get_elasticity_none(self):
        from dartlab.engines.common.finance.simulation import (
            DEFAULT_ELASTICITY,
            get_elasticity,
        )

        e = get_elasticity(None)
        assert e == DEFAULT_ELASTICITY

    def test_defensive_vs_cyclical(self):
        from dartlab.engines.common.finance.simulation import get_elasticity

        semi = get_elasticity("반도체")
        food = get_elasticity("식품")
        assert semi.revenue_to_gdp > food.revenue_to_gdp
        assert food.cyclicality == "defensive"


# ══════════════════════════════════════
# simulate_scenario 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestSimulateScenario:
    def test_baseline(self, sector_params):
        from dartlab.engines.common.finance.simulation import simulate_scenario

        result = simulate_scenario(
            HEALTHY_SERIES,
            scenario="baseline",
            sector_key="반도체",
            sector_params=sector_params,
            shares=1_000_000,
        )
        assert result.scenario_name == "baseline"
        assert len(result.revenue_path) == 3
        assert len(result.operating_income_path) == 3
        assert len(result.margin_path) == 3
        assert len(result.fcf_path) == 3
        assert result.per_share_value is not None
        assert result.dcf_value > 0

    def test_adverse(self, sector_params):
        from dartlab.engines.common.finance.simulation import simulate_scenario

        result = simulate_scenario(
            HEALTHY_SERIES,
            scenario="adverse",
            sector_key="반도체",
            sector_params=sector_params,
        )
        # 경기침체 → 매출 감소 (반도체 β=1.8이므로 큰 하락)
        assert result.revenue_change_pct < 0

    def test_adverse_vs_baseline_revenue(self, sector_params):
        from dartlab.engines.common.finance.simulation import simulate_scenario

        baseline = simulate_scenario(
            HEALTHY_SERIES,
            scenario="baseline",
            sector_key="반도체",
            sector_params=sector_params,
        )
        adverse = simulate_scenario(
            HEALTHY_SERIES,
            scenario="adverse",
            sector_key="반도체",
            sector_params=sector_params,
        )
        # 경기침체 매출이 기준 매출보다 낮아야 함
        assert adverse.revenue_path[-1] < baseline.revenue_path[-1]

    def test_defensive_sector_less_impact(self, sector_params):
        from dartlab.engines.common.finance.simulation import simulate_scenario

        semi = simulate_scenario(
            HEALTHY_SERIES,
            scenario="adverse",
            sector_key="반도체",
            sector_params=sector_params,
        )
        food = simulate_scenario(
            HEALTHY_SERIES,
            scenario="adverse",
            sector_key="식품",
            sector_params=sector_params,
        )
        # 식품(방어적)이 반도체보다 매출 타격 작아야 함
        assert abs(food.revenue_change_pct) < abs(semi.revenue_change_pct)

    def test_no_shares(self, sector_params):
        from dartlab.engines.common.finance.simulation import simulate_scenario

        result = simulate_scenario(
            HEALTHY_SERIES,
            scenario="baseline",
            sector_params=sector_params,
        )
        assert result.per_share_value is None
        assert result.dcf_value > 0

    def test_scenario_str_or_object(self, sector_params):
        from dartlab.engines.common.finance.simulation import (
            PRESET_SCENARIOS,
            simulate_scenario,
        )

        r1 = simulate_scenario(HEALTHY_SERIES, scenario="baseline", sector_params=sector_params)
        r2 = simulate_scenario(
            HEALTHY_SERIES,
            scenario=PRESET_SCENARIOS["baseline"],
            sector_params=sector_params,
        )
        assert r1.scenario_name == r2.scenario_name
        assert r1.revenue_path == r2.revenue_path

    def test_repr(self, sector_params):
        from dartlab.engines.common.finance.simulation import simulate_scenario

        result = simulate_scenario(
            HEALTHY_SERIES,
            scenario="baseline",
            sector_key="반도체",
            sector_params=sector_params,
        )
        text = repr(result)
        assert "시뮬레이션" in text
        assert "매출" in text
        assert "참고용" in text


# ══════════════════════════════════════
# simulate_all_scenarios 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestSimulateAll:
    def test_all_scenarios(self, sector_params):
        from dartlab.engines.common.finance.simulation import simulate_all_scenarios

        results = simulate_all_scenarios(
            HEALTHY_SERIES,
            sector_key="반도체",
            sector_params=sector_params,
        )
        assert len(results) == 5
        assert "baseline" in results
        assert "adverse" in results
        for name, r in results.items():
            assert len(r.revenue_path) == 3

    def test_selective_scenarios(self, sector_params):
        from dartlab.engines.common.finance.simulation import simulate_all_scenarios

        results = simulate_all_scenarios(
            HEALTHY_SERIES,
            sector_params=sector_params,
            scenarios=["baseline", "adverse"],
        )
        assert len(results) == 2


# ══════════════════════════════════════
# Monte Carlo 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestMonteCarlo:
    def test_basic(self, sector_params):
        from dartlab.engines.common.finance.simulation import monte_carlo_forecast

        result = monte_carlo_forecast(
            HEALTHY_SERIES,
            sector_key="반도체",
            sector_params=sector_params,
            shares=1_000_000,
            iterations=1000,  # 테스트용으로 줄임
        )
        assert result.iterations == 1000
        assert "매출" in result.percentiles
        rev_pcts = result.percentiles["매출"]
        assert rev_pcts["p5"] <= rev_pcts["p50"] <= rev_pcts["p95"]
        assert result.expected_value > 0
        assert result.std_dev > 0

    def test_percentile_ordering(self, sector_params):
        from dartlab.engines.common.finance.simulation import monte_carlo_forecast

        result = monte_carlo_forecast(
            HEALTHY_SERIES,
            sector_params=sector_params,
            iterations=500,
        )
        for metric, pcts in result.percentiles.items():
            assert pcts["p5"] <= pcts["p25"] <= pcts["p50"] <= pcts["p75"] <= pcts["p95"]

    def test_adverse_lower_than_baseline(self, sector_params):
        from dartlab.engines.common.finance.simulation import monte_carlo_forecast

        base = monte_carlo_forecast(
            HEALTHY_SERIES,
            sector_key="반도체",
            sector_params=sector_params,
            scenario="baseline",
            iterations=2000,
        )
        adv = monte_carlo_forecast(
            HEALTHY_SERIES,
            sector_key="반도체",
            sector_params=sector_params,
            scenario="adverse",
            iterations=2000,
        )
        # 경기침체 시 기대값이 기준보다 낮아야 함
        assert adv.expected_value < base.expected_value

    def test_repr(self, sector_params):
        from dartlab.engines.common.finance.simulation import monte_carlo_forecast

        result = monte_carlo_forecast(
            HEALTHY_SERIES,
            sector_params=sector_params,
            iterations=500,
        )
        text = repr(result)
        assert "Monte Carlo" in text
        assert "P5" in text
        assert "P50" in text
        assert "P95" in text


# ══════════════════════════════════════
# 스트레스 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestStressTest:
    def test_basic(self, sector_params):
        from dartlab.engines.common.finance.simulation import stress_test

        result = stress_test(
            HEALTHY_SERIES,
            sector_key="반도체",
            sector_params=sector_params,
        )
        assert result.scenario_name == "adverse"
        assert result.year_3_revenue_change < 0  # 경기침체 → 매출 감소
        assert result.survival_risk in ("low", "medium", "high", "critical")
        assert isinstance(result.dividend_sustainable, bool)

    def test_healthy_company_low_risk(self, sector_params):
        from dartlab.engines.common.finance.simulation import stress_test

        result = stress_test(
            HEALTHY_SERIES,
            sector_key="식품",  # 방어적 업종
            sector_params=sector_params,
        )
        # 건전한 기업 + 방어적 업종 → 생존 위험 낮음
        assert result.survival_risk in ("low", "medium")

    def test_debt_ratio_computed(self, sector_params):
        from dartlab.engines.common.finance.simulation import stress_test

        result = stress_test(
            HEALTHY_SERIES,
            sector_params=sector_params,
        )
        assert result.year_3_debt_ratio is not None
        assert result.year_3_debt_ratio > 0

    def test_repr(self, sector_params):
        from dartlab.engines.common.finance.simulation import stress_test

        result = stress_test(
            HEALTHY_SERIES,
            sector_params=sector_params,
        )
        text = repr(result)
        assert "스트레스 테스트" in text
        assert "생존 위험도" in text
        assert "배당" in text
        assert "참고용" in text

    def test_custom_scenario(self, sector_params):
        from dartlab.engines.common.finance.simulation import stress_test

        result = stress_test(
            HEALTHY_SERIES,
            sector_params=sector_params,
            scenario="semiconductor_down",
        )
        assert result.scenario_name == "semiconductor_down"


# ══════════════════════════════════════
# 내부 유틸 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestInternalUtils:
    def test_extract_base_metrics(self):
        from dartlab.engines.common.finance.simulation import _extract_base_metrics

        metrics = _extract_base_metrics(HEALTHY_SERIES)
        assert metrics["revenue"] is not None
        assert metrics["revenue"] > 0
        assert metrics["operating_income"] is not None
        assert metrics["margin"] is not None
        assert 0 < metrics["margin"] < 100

    def test_extract_volatility(self):
        from dartlab.engines.common.finance.simulation import _extract_volatility

        vol = _extract_volatility(HEALTHY_SERIES)
        assert "revenue_cv" in vol
        assert "margin_std" in vol
        assert vol["revenue_cv"] > 0
        assert vol["margin_std"] > 0

    def test_apply_macro_shock(self):
        from dartlab.engines.common.finance.simulation import (
            PRESET_SCENARIOS,
            _apply_macro_shock,
            get_elasticity,
        )

        elast = get_elasticity("반도체")
        sc = PRESET_SCENARIOS["adverse"]
        rev, margin, wacc = _apply_macro_shock(
            base_revenue=180e8,
            base_margin=13.9,
            scenario=sc,
            elasticity=elast,
            year_idx=0,
            base_wacc=10.0,
        )
        # 경기침체 + 반도체(고감응) → 매출 하락
        assert rev < 180e8
        # 마진도 하락
        assert margin < 13.9
        # 금리 인하 → WACC 하락
        assert wacc < 10.0

    def test_empty_series(self, sector_params):
        from dartlab.engines.common.finance.simulation import simulate_scenario

        result = simulate_scenario(
            {"IS": {}, "BS": {}, "CF": {}},
            scenario="baseline",
            sector_params=sector_params,
        )
        assert len(result.warnings) > 0
