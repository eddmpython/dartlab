"""Context Signal Fusion 테스트.

ContextSignals, adjust_probabilities, get_noise_sigma 검증.
"""

from __future__ import annotations

import pytest

from dartlab.engines.common.finance.prediction import (
    NOISE_CONFIG,
    ContextSignals,
    adjust_probabilities,
    get_noise_sigma,
)
from dartlab.engines.common.finance.pricetarget import SCENARIO_PROBABILITIES


# ── ContextSignals 기본 ─────────────────────────────────


class TestContextSignals:
    @pytest.mark.unit
    def test_default_values(self):
        signals = ContextSignals()
        assert signals.size_class == "Mid"
        assert signals.sector_cyclicality == "moderate"
        assert signals.growth_rank_pct == 50.0
        assert signals.diff_change_rate == 0.0
        assert signals.adjustments == {}
        assert signals.reasoning == []

    @pytest.mark.unit
    def test_repr(self):
        signals = ContextSignals(
            insight_grades={"profitability": "A", "health": "B"},
            size_class="Large",
        )
        text = repr(signals)
        assert "맥락 신호" in text
        assert "Large" in text


# ── adjust_probabilities ────────────────────────────────


class TestAdjustProbabilities:
    @pytest.mark.unit
    def test_no_signals_no_change(self):
        """신호 없으면 확률 변화 없음."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals()
        result = adjust_probabilities(base, signals)
        for k in base:
            assert abs(result[k] - base[k]) < 0.01

    @pytest.mark.unit
    def test_sum_to_one(self):
        """어떤 조정이든 합계 = 1.0."""
        signals = ContextSignals(
            insight_grades={"profitability": "F", "health": "F", "cashflow": "D"},
            risk_change_rate=80.0,
            sector_cyclicality="high",
        )
        base = dict(SCENARIO_PROBABILITIES)
        result = adjust_probabilities(base, signals)
        total = sum(result.values())
        assert abs(total - 1.0) < 0.001

    @pytest.mark.unit
    def test_profitability_f_increases_adverse(self):
        """수익성 F → adverse 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(insight_grades={"profitability": "F"})
        result = adjust_probabilities(base, signals)
        assert result["adverse"] > base["adverse"]

    @pytest.mark.unit
    def test_health_d_increases_adverse(self):
        """건전성 D → adverse 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(insight_grades={"health": "D"})
        result = adjust_probabilities(base, signals)
        assert result["adverse"] > base["adverse"]

    @pytest.mark.unit
    def test_opportunity_a_increases_baseline(self):
        """기회 A → baseline 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(insight_grades={"opportunity": "A"})
        result = adjust_probabilities(base, signals)
        assert result["baseline"] > base["baseline"]

    @pytest.mark.unit
    def test_high_cyclicality_increases_rate_hike(self):
        """경기민감 → rate_hike 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(sector_cyclicality="high")
        result = adjust_probabilities(base, signals)
        assert result["rate_hike"] > base["rate_hike"]

    @pytest.mark.unit
    def test_defensive_increases_baseline(self):
        """방어적 → baseline 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(sector_cyclicality="defensive")
        result = adjust_probabilities(base, signals)
        assert result["baseline"] > base["baseline"]

    @pytest.mark.unit
    def test_high_growth_rank_increases_baseline(self):
        """성장 상위 20% → baseline 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(growth_rank_pct=10.0)
        result = adjust_probabilities(base, signals)
        assert result["baseline"] > base["baseline"]

    @pytest.mark.unit
    def test_risk_change_high_increases_adverse(self):
        """리스크 변화율 80% → adverse 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(risk_change_rate=80.0)
        result = adjust_probabilities(base, signals)
        assert result["adverse"] > base["adverse"]

    @pytest.mark.unit
    def test_no_negative_probabilities(self):
        """극단적 조정에도 음수 확률 없음."""
        signals = ContextSignals(
            insight_grades={
                "profitability": "F",
                "health": "F",
                "cashflow": "F",
                "opportunity": "A",
            },
            risk_change_rate=100.0,
            sector_cyclicality="high",
            growth_rank_pct=5.0,
        )
        base = dict(SCENARIO_PROBABILITIES)
        result = adjust_probabilities(base, signals)
        for v in result.values():
            assert v >= 0.01

    @pytest.mark.unit
    def test_reasoning_populated(self):
        """조정 발생 시 reasoning이 채워져야 함."""
        signals = ContextSignals(insight_grades={"profitability": "D"})
        # _compute_adjustments는 ContextSignals 생성 시 직접 호출 안 됨
        # adjust_probabilities는 signals.adjustments를 사용
        from dartlab.engines.common.finance.prediction import _compute_adjustments

        adj, reasons = _compute_adjustments(signals)
        assert len(reasons) > 0
        assert "수익성" in reasons[0]

    @pytest.mark.unit
    def test_cashflow_d_increases_adverse(self):
        """현금흐름 D → adverse +3%p."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(insight_grades={"cashflow": "D"})
        from dartlab.engines.common.finance.prediction import _compute_adjustments

        adj, _ = _compute_adjustments(signals)
        assert adj.get("adverse", 0) > 0


# ── get_noise_sigma ─────────────────────────────────────


class TestNoiseSigma:
    @pytest.mark.unit
    def test_default_mid(self):
        sigma = get_noise_sigma("growth", "Mid")
        assert sigma == NOISE_CONFIG["growth"]["base_sigma"] * 1.0

    @pytest.mark.unit
    def test_small_amplifies(self):
        sigma_mid = get_noise_sigma("growth", "Mid")
        sigma_small = get_noise_sigma("growth", "Small")
        assert sigma_small > sigma_mid

    @pytest.mark.unit
    def test_large_dampens(self):
        sigma_mid = get_noise_sigma("growth", "Mid")
        sigma_large = get_noise_sigma("growth", "Large")
        assert sigma_large < sigma_mid

    @pytest.mark.unit
    def test_unknown_variable(self):
        sigma = get_noise_sigma("unknown", "Mid")
        assert sigma == 1.0

    @pytest.mark.unit
    def test_all_variables_have_config(self):
        for var in ["growth", "margin", "wacc", "capex", "tax"]:
            for size in ["Small", "Mid", "Large"]:
                sigma = get_noise_sigma(var, size)
                assert sigma > 0
