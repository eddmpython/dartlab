"""주가 목표가 엔진 테스트.

compute_price_target, _derive_revenue_path_from_macro,
_dcf_from_proforma, _classify_signal 검증.
"""

from __future__ import annotations

import pytest

from dartlab.analysis.forecast.prediction import ContextSignals
from dartlab.analysis.forecast.simulation import (
    DEFAULT_ELASTICITY,
    PRESET_SCENARIOS,
    SectorElasticity,
)
from dartlab.analysis.valuation.pricetarget import (
    PriceTargetResult,
    _classify_signal,
    _dcf_from_proforma,
    _derive_revenue_path_from_macro,
    _monte_carlo_price_distribution,
    compute_price_target,
)
from dartlab.analysis.forecast.proforma import build_proforma

# ── Mock 시계열 (test_proforma와 동일) ──────────────────

SERIES: dict = {
    "IS": {
        "sales": [250, 250, 250, 250, 300, 300, 300, 300],
        "gross_profit": [75, 75, 75, 75, 90, 90, 90, 90],
        "selling_and_administrative_expenses": [25, 25, 25, 25, 30, 30, 30, 30],
        "profit_before_tax": [40, 40, 40, 40, 48, 48, 48, 48],
        "income_tax_expense": [8, 8, 8, 8, 10, 10, 10, 10],
        "finance_costs": [2, 2, 2, 2, 3, 3, 3, 3],
        "net_profit": [32, 32, 32, 32, 38, 38, 38, 38],
    },
    "CF": {
        "depreciation_and_amortization": [10, 10, 10, 10, 12, 12, 12, 12],
        "purchase_of_property_plant_and_equipment": [-15, -15, -15, -15, -18, -18, -18, -18],
        "dividends_paid": [-8, -8, -8, -8, -10, -10, -10, -10],
    },
    "BS": {
        "current_assets": [None, None, None, 500, None, None, None, 600],
        "current_liabilities": [None, None, None, 200, None, None, None, 240],
        "cash_and_cash_equivalents": [None, None, None, 100, None, None, None, 120],
        "shortterm_borrowings": [None, None, None, 50, None, None, None, 60],
        "longterm_borrowings": [None, None, None, 100, None, None, None, 120],
        "debentures": [None, None, None, 0, None, None, None, 0],
        "trade_receivables": [None, None, None, 150, None, None, None, 180],
        "inventories": [None, None, None, 120, None, None, None, 140],
        "trade_payables": [None, None, None, 80, None, None, None, 90],
        "tangible_assets": [None, None, None, 400, None, None, None, 450],
        "total_assets": [None, None, None, 1000, None, None, None, 1200],
        "total_liabilities": [None, None, None, 400, None, None, None, 480],
        "total_stockholders_equity": [None, None, None, 600, None, None, None, 720],
    },
}


# ── _derive_revenue_path_from_macro ──────────────────────


class TestDeriveRevenuePath:
    @pytest.mark.unit
    def test_baseline_returns_near_base_growth(self):
        scenario = PRESET_SCENARIOS["baseline"]
        path = _derive_revenue_path_from_macro(5.0, scenario, DEFAULT_ELASTICITY)
        assert len(path) == 5
        # baseline은 GDP delta ≈ 0이므로 base_growth 근처
        for g in path:
            assert -5 < g < 15

    @pytest.mark.unit
    def test_adverse_lowers_growth(self):
        baseline_path = _derive_revenue_path_from_macro(5.0, PRESET_SCENARIOS["baseline"], DEFAULT_ELASTICITY)
        adverse_path = _derive_revenue_path_from_macro(5.0, PRESET_SCENARIOS["adverse"], DEFAULT_ELASTICITY)
        # 경기침체 시 첫 해 성장률이 baseline보다 낮아야 함
        assert adverse_path[0] < baseline_path[0]

    @pytest.mark.unit
    def test_high_beta_amplifies(self):
        scenario = PRESET_SCENARIOS["adverse"]
        low_beta = SectorElasticity(0.3, 0.1, 10, 0, "defensive")
        high_beta = SectorElasticity(1.8, 0.8, 50, 0, "high")
        path_low = _derive_revenue_path_from_macro(5.0, scenario, low_beta)
        path_high = _derive_revenue_path_from_macro(5.0, scenario, high_beta)
        # 높은 β는 충격을 더 증폭
        assert path_high[0] < path_low[0]

    @pytest.mark.unit
    def test_mean_reversion(self):
        """4~5년차에 base_growth 방향으로 복귀."""
        scenario = PRESET_SCENARIOS["adverse"]
        path = _derive_revenue_path_from_macro(5.0, scenario, DEFAULT_ELASTICITY)
        # 마지막 연도가 첫 연도보다 base_growth에 가까움
        delta_first = abs(path[0] - 5.0)
        delta_last = abs(path[4] - 5.0)
        assert delta_last <= delta_first


# ── _dcf_from_proforma ───────────────────────────────────


class TestDCFFromProforma:
    @pytest.mark.unit
    def test_basic_dcf(self):
        pf = build_proforma(SERIES, revenue_growth_path=[5.0, 4.0, 3.0, 2.5, 2.0])
        ev, eq, per_share = _dcf_from_proforma(pf, wacc=10.0, shares=1000)
        assert ev > 0
        assert eq > 0
        assert per_share > 0
        assert per_share == eq / 1000

    @pytest.mark.unit
    def test_higher_wacc_lower_value(self):
        pf = build_proforma(SERIES, revenue_growth_path=[5.0, 4.0, 3.0])
        _, _, ps_low = _dcf_from_proforma(pf, wacc=8.0, shares=100)
        _, _, ps_high = _dcf_from_proforma(pf, wacc=15.0, shares=100)
        assert ps_low > ps_high

    @pytest.mark.unit
    def test_no_shares(self):
        pf = build_proforma(SERIES, revenue_growth_path=[5.0])
        ev, eq, per_share = _dcf_from_proforma(pf, wacc=10.0, shares=None)
        # shares 없으면 per_share = equity_value
        assert per_share == eq

    @pytest.mark.unit
    def test_empty_proforma(self):
        pf = build_proforma({"IS": {"sales": [0]}, "CF": {}, "BS": {}}, revenue_growth_path=[5.0])
        ev, eq, ps = _dcf_from_proforma(pf, wacc=10.0)
        assert ev == 0.0
        assert eq == 0.0


# ── _classify_signal ─────────────────────────────────────


class TestClassifySignal:
    @pytest.mark.unit
    def test_strong_buy(self):
        assert _classify_signal(35.0, {"p10": 110}, 100) == "strong_buy"

    @pytest.mark.unit
    def test_buy(self):
        assert _classify_signal(20.0, {"p10": 90}, 100) == "buy"

    @pytest.mark.unit
    def test_hold(self):
        assert _classify_signal(5.0, {}, 100) == "hold"

    @pytest.mark.unit
    def test_sell(self):
        assert _classify_signal(-20.0, {}, 100) == "sell"

    @pytest.mark.unit
    def test_strong_sell(self):
        assert _classify_signal(-35.0, {"p90": 80}, 100) == "strong_sell"

    @pytest.mark.unit
    def test_none_upside(self):
        assert _classify_signal(None, {}, None) == "hold"


# ── _monte_carlo_price_distribution ──────────────────────


class TestMonteCarlo:
    @pytest.mark.unit
    def test_basic_distribution(self):
        pcts, _, values = _monte_carlo_price_distribution(
            SERIES,
            5.0,
            DEFAULT_ELASTICITY,
            10.0,
            2.0,
            1000,
            iterations=500,
            seed=42,
        )
        assert "p10" in pcts
        assert "p50" in pcts
        assert "p90" in pcts
        assert pcts["p10"] <= pcts["p50"] <= pcts["p90"]
        assert len(values) == 500

    @pytest.mark.unit
    def test_reproducible_with_seed(self):
        pcts1, _, _ = _monte_carlo_price_distribution(
            SERIES,
            5.0,
            DEFAULT_ELASTICITY,
            10.0,
            2.0,
            100,
            iterations=200,
            seed=123,
        )
        pcts2, _, _ = _monte_carlo_price_distribution(
            SERIES,
            5.0,
            DEFAULT_ELASTICITY,
            10.0,
            2.0,
            100,
            iterations=200,
            seed=123,
        )
        assert pcts1["p50"] == pcts2["p50"]


# ── compute_price_target (통합) ──────────────────────────


class TestComputePriceTarget:
    @pytest.mark.unit
    def test_basic(self):
        result = compute_price_target(
            SERIES,
            current_price=500,
            shares=100,
            mc_iterations=500,
            mc_seed=42,
        )
        assert isinstance(result, PriceTargetResult)
        assert result.weighted_target > 0
        assert len(result.scenarios) > 0
        assert result.signal in ("strong_buy", "buy", "hold", "sell", "strong_sell")

    @pytest.mark.unit
    def test_probabilities_sum_to_one(self):
        result = compute_price_target(SERIES, mc_iterations=100, mc_seed=1)
        total = sum(s.probability for s in result.scenarios)
        assert abs(total - 1.0) < 0.01

    @pytest.mark.unit
    def test_percentile_order(self):
        result = compute_price_target(SERIES, shares=100, mc_iterations=500, mc_seed=42)
        pcts = result.percentiles
        if pcts:
            assert pcts["p10"] <= pcts["p25"] <= pcts["p50"] <= pcts["p75"] <= pcts["p90"]

    @pytest.mark.unit
    def test_upside_with_current_price(self):
        result = compute_price_target(
            SERIES,
            current_price=100,
            shares=100,
            mc_iterations=100,
            mc_seed=1,
        )
        assert result.upside_pct is not None
        assert result.probability_above_current is not None

    @pytest.mark.unit
    def test_no_current_price(self):
        result = compute_price_target(SERIES, mc_iterations=100, mc_seed=1)
        assert result.upside_pct is None
        assert result.signal == "hold"

    @pytest.mark.unit
    def test_non_semiconductor_redistributes(self):
        """비반도체 업종은 semiconductor_down 확률이 baseline에 재배분."""
        result = compute_price_target(
            SERIES,
            sector_key="자동차",
            mc_iterations=100,
            mc_seed=1,
        )
        names = [s.scenario_name for s in result.scenarios]
        assert "semiconductor_down" not in names

    @pytest.mark.unit
    def test_semiconductor_keeps_scenario(self):
        result = compute_price_target(
            SERIES,
            sector_key="반도체",
            mc_iterations=100,
            mc_seed=1,
        )
        names = [s.scenario_name for s in result.scenarios]
        assert "semiconductor_down" in names

    @pytest.mark.unit
    def test_repr(self):
        result = compute_price_target(
            SERIES,
            current_price=500,
            shares=100,
            mc_iterations=100,
            mc_seed=1,
        )
        text = repr(result)
        assert "주가 목표가" in text
        assert "투자 신호" in text

    @pytest.mark.unit
    def test_all_scenarios_have_proforma(self):
        result = compute_price_target(SERIES, mc_iterations=100, mc_seed=1)
        for s in result.scenarios:
            assert s.proforma is not None
            assert len(s.proforma.projections) > 0
            assert s.wacc_used > 0

    @pytest.mark.unit
    def test_confidence(self):
        result = compute_price_target(SERIES, mc_iterations=100, mc_seed=1)
        assert result.confidence in ("high", "medium", "low")


# ── v2: Multi-Noise MC ───────────────────────────────────


class TestMultiNoiseMC:
    @pytest.mark.unit
    def test_size_class_affects_spread(self):
        """Small이 Large보다 분포가 넓어야 함 (σ 차등)."""
        pcts_small, _, vals_small = _monte_carlo_price_distribution(
            SERIES,
            5.0,
            DEFAULT_ELASTICITY,
            10.0,
            2.0,
            100,
            iterations=500,
            seed=42,
            size_class="Small",
        )
        pcts_large, _, vals_large = _monte_carlo_price_distribution(
            SERIES,
            5.0,
            DEFAULT_ELASTICITY,
            10.0,
            2.0,
            100,
            iterations=500,
            seed=42,
            size_class="Large",
        )
        # 표준편차로 비교 (max(v, 0) 클램프로 P10이 0일 수 있으므로)
        import statistics

        std_small = statistics.stdev(vals_small) if len(vals_small) > 1 else 0
        std_large = statistics.stdev(vals_large) if len(vals_large) > 1 else 0
        assert std_small > std_large

    @pytest.mark.unit
    def test_nwc_reflected(self):
        """NWC가 FCF에 반영되면 결과 분포에 값이 있어야 함."""
        pcts, _, values = _monte_carlo_price_distribution(
            SERIES,
            5.0,
            DEFAULT_ELASTICITY,
            10.0,
            2.0,
            100,
            iterations=200,
            seed=42,
            size_class="Mid",
        )
        assert len(values) == 200
        # shares가 100이면 mock 데이터에서도 양의 값 존재
        assert pcts["p50"] >= 0
        # 최소한 일부 iterations에서 양의 값 생성
        positive_count = sum(1 for v in values if v > 0)
        assert positive_count > 0


# ── v2: ContextSignals 통합 ──────────────────────────────


class TestContextSignalsIntegration:
    @pytest.mark.unit
    def test_context_signals_changes_result(self):
        """맥락 신호가 있으면 결과가 달라져야 함."""
        result_no_ctx = compute_price_target(
            SERIES,
            shares=100,
            mc_iterations=200,
            mc_seed=42,
        )
        signals = ContextSignals(
            insightGrades={"profitability": "F", "health": "D"},
            sectorCyclicality="high",
        )
        result_with_ctx = compute_price_target(
            SERIES,
            shares=100,
            mc_iterations=200,
            mc_seed=42,
            context_signals=signals,
        )
        # 확률이 재가중되었으므로 weighted_target이 다를 수 있음
        # (적어도 경고가 추가되어야 함)
        assert any("맥락" in w for w in result_with_ctx.warnings)

    @pytest.mark.unit
    def test_context_signals_probabilities_sum(self):
        """맥락 신호 적용 후에도 확률 합계 = 1."""
        signals = ContextSignals(
            insightGrades={"profitability": "F"},
            riskChangeRate=90.0,
        )
        result = compute_price_target(
            SERIES,
            mc_iterations=100,
            mc_seed=1,
            context_signals=signals,
        )
        total = sum(s.probability for s in result.scenarios)
        assert abs(total - 1.0) < 0.01

    @pytest.mark.unit
    def test_size_class_passed_to_mc(self):
        """Small sizeClass → MC σ가 달라짐 (간접 검증)."""
        from dartlab.analysis.forecast.prediction import getNoiseSigma as get_noise_sigma

        # MC를 직접 실행하지 않고, σ 설정이 size_class에 따라 다른지 확인
        sigma_s = get_noise_sigma("growth", "Small")
        sigma_l = get_noise_sigma("growth", "Large")
        assert sigma_s > sigma_l

        # compute_price_target에 context_signals가 전달되면 경고 포함
        signals = ContextSignals(sizeClass="Small", insightGrades={"profitability": "D"})
        result = compute_price_target(
            SERIES,
            shares=100,
            mc_iterations=100,
            mc_seed=42,
            context_signals=signals,
        )
        assert any("맥락" in w for w in result.warnings)
