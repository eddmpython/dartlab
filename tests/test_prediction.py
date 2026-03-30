"""Context Signal Fusion 테스트.

ContextSignals, adjust_probabilities 검증.
"""

from __future__ import annotations

import pytest

from dartlab.analysis.forecast.prediction import (
    ContextSignals,
    _computeAdjustments,
)
from dartlab.analysis.forecast.prediction import (
    adjustProbabilities as adjust_probabilities,
)
from dartlab.analysis.valuation.pricetarget import SCENARIO_PROBABILITIES

# ── ContextSignals 기본 ─────────────────────────────────


class TestContextSignals:
    @pytest.mark.unit
    def test_default_values(self):
        signals = ContextSignals()
        assert signals.sizeClass == "Mid"
        assert signals.sectorCyclicality == "moderate"
        assert signals.growthRankPct == 50.0
        assert signals.diffChangeRate == 0.0
        assert signals.adjustments == {}
        assert signals.reasoning == []

    @pytest.mark.unit
    def test_repr(self):
        signals = ContextSignals(
            insightGrades={"profitability": "A", "health": "B"},
            sizeClass="Large",
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
            insightGrades={"profitability": "F", "health": "F", "cashflow": "D"},
            riskChangeRate=80.0,
            sectorCyclicality="high",
        )
        base = dict(SCENARIO_PROBABILITIES)
        result = adjust_probabilities(base, signals)
        total = sum(result.values())
        assert abs(total - 1.0) < 0.001

    @pytest.mark.unit
    def test_profitability_f_increases_adverse(self):
        """수익성 F → adverse 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(insightGrades={"profitability": "F"})
        result = adjust_probabilities(base, signals)
        assert result["adverse"] > base["adverse"]

    @pytest.mark.unit
    def test_health_d_increases_adverse(self):
        """건전성 D → adverse 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(insightGrades={"health": "D"})
        result = adjust_probabilities(base, signals)
        assert result["adverse"] > base["adverse"]

    @pytest.mark.unit
    def test_opportunity_a_increases_baseline(self):
        """기회 A → baseline 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(insightGrades={"opportunity": "A"})
        result = adjust_probabilities(base, signals)
        assert result["baseline"] > base["baseline"]

    @pytest.mark.unit
    def test_high_cyclicality_increases_rate_hike(self):
        """경기민감 → rate_hike 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(sectorCyclicality="high")
        result = adjust_probabilities(base, signals)
        assert result["rate_hike"] > base["rate_hike"]

    @pytest.mark.unit
    def test_defensive_increases_baseline(self):
        """방어적 → baseline 확률 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(sectorCyclicality="defensive")
        result = adjust_probabilities(base, signals)
        assert result["baseline"] > base["baseline"]

    @pytest.mark.unit
    def test_high_growth_rank_increases_baseline(self):
        """성장 상위 20% → baseline 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(growthRankPct=10.0)
        result = adjust_probabilities(base, signals)
        assert result["baseline"] > base["baseline"]

    @pytest.mark.unit
    def test_risk_change_high_increases_adverse(self):
        """리스크 변화율 80% → adverse 증가."""
        base = dict(SCENARIO_PROBABILITIES)
        signals = ContextSignals(riskChangeRate=80.0)
        result = adjust_probabilities(base, signals)
        assert result["adverse"] > base["adverse"]

    @pytest.mark.unit
    def test_no_negative_probabilities(self):
        """극단적 조정에도 음수 확률 없음."""
        signals = ContextSignals(
            insightGrades={
                "profitability": "F",
                "health": "F",
                "cashflow": "F",
                "opportunity": "A",
            },
            riskChangeRate=100.0,
            sectorCyclicality="high",
            growthRankPct=5.0,
        )
        base = dict(SCENARIO_PROBABILITIES)
        result = adjust_probabilities(base, signals)
        for v in result.values():
            assert v >= 0.01

    @pytest.mark.unit
    def test_reasoning_populated(self):
        """조정 발생 시 reasoning이 채워져야 함."""
        signals = ContextSignals(insightGrades={"profitability": "D"})
        adj, reasons = _computeAdjustments(signals)
        assert len(reasons) > 0
        assert "수익성" in reasons[0]

    @pytest.mark.unit
    def test_cashflow_d_increases_adverse(self):
        """현금흐름 D → adverse +3%p."""
        signals = ContextSignals(insightGrades={"cashflow": "D"})
        adj, _ = _computeAdjustments(signals)
        assert adj.get("adverse", 0) > 0
