"""Credit engine unit tests - scorecard pure functions.

Tests scoreMetric, axisScore, mapTo20Grade, weightedScore,
gradeCategory, isInvestmentGrade, cashFlowGrade, creditOutlook.
All mocked, no data loading.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ── imports ──

from dartlab.credit.scoring.creditScorecard import (
    axisScore,
    cashFlowGrade,
    creditOutlook,
    estimatePD,
    gradeCategory,
    isInvestmentGrade,
    mapTo20Grade,
    notchGrade,
    scoreMetric,
    weightedScore,
)

# ═══════════════════════════════════════════════════════════
# scoreMetric
# ═══════════════════════════════════════════════════════════


_LOWER_BETTER = {
    "lower_is_better": True,
    "breakpoints": [(0, 0), (50, 25), (100, 50), (200, 80), (400, 100)],
}

_HIGHER_BETTER = {
    "lower_is_better": False,
    "breakpoints": [(400, 0), (200, 20), (100, 50), (50, 80), (0, 100)],
}


class TestScoreMetric:
    def test_returns_none_for_none_input(self):
        assert scoreMetric(None, _LOWER_BETTER) is None

    def test_returns_none_for_empty_breakpoints(self):
        assert scoreMetric(10, {"lower_is_better": True, "breakpoints": []}) is None

    def test_exact_breakpoint_lower_is_better(self):
        result = scoreMetric(50, _LOWER_BETTER)
        assert result == 25

    def test_exact_first_breakpoint(self):
        result = scoreMetric(0, _LOWER_BETTER)
        assert result == 0

    def test_exact_last_breakpoint(self):
        result = scoreMetric(400, _LOWER_BETTER)
        assert result == 100

    def test_below_range_clamps_to_first(self):
        result = scoreMetric(-10, _LOWER_BETTER)
        assert result == 0

    def test_above_range_clamps_to_last(self):
        result = scoreMetric(999, _LOWER_BETTER)
        assert result == 100

    def test_linear_interpolation_midpoint(self):
        # Between (0, 0) and (50, 25) at value=25 -> score=12.5
        result = scoreMetric(25, _LOWER_BETTER)
        assert result == 12.5

    def test_higher_is_better_exact(self):
        # breakpoints reversed internally: (0,100),(50,80),(100,50),(200,20),(400,0)
        # value=400 -> at last breakpoint -> score=0
        result = scoreMetric(400, _HIGHER_BETTER)
        assert result == 0

    def test_higher_is_better_low_value(self):
        # value=0 -> clamped to first after reversal -> score=100
        result = scoreMetric(0, _HIGHER_BETTER)
        assert result == 100

    def test_higher_is_better_interpolation(self):
        # After reversal: (0,100),(50,80),(100,50),(200,20),(400,0)
        # value=150 midpoint between (100,50) and (200,20) -> 35
        result = scoreMetric(150, _HIGHER_BETTER)
        assert result == 35.0


# ═══════════════════════════════════════════════════════════
# axisScore
# ═══════════════════════════════════════════════════════════


class TestAxisScore:
    def test_average_of_valid_scores(self):
        metrics = [("m1", 10.0), ("m2", 30.0), ("m3", 20.0)]
        result = axisScore(metrics)
        assert result == 20.0

    def test_filters_none_values(self):
        metrics = [("m1", 10.0), ("m2", None), ("m3", 30.0)]
        result = axisScore(metrics)
        assert result == 20.0

    def test_all_none_returns_none(self):
        metrics = [("m1", None), ("m2", None)]
        result = axisScore(metrics)
        assert result is None

    def test_single_metric(self):
        metrics = [("m1", 42.5)]
        result = axisScore(metrics)
        assert result == 42.5

    def test_empty_list_returns_none(self):
        result = axisScore([])
        assert result is None


# ═══════════════════════════════════════════════════════════
# mapTo20Grade
# ═══════════════════════════════════════════════════════════


class TestMapTo20Grade:
    def test_zero_score_is_aaa(self):
        grade, desc, pd = mapTo20Grade(0)
        assert grade == "AAA"

    def test_score_100_is_d(self):
        grade, desc, pd = mapTo20Grade(100)
        assert grade == "D"
        assert pd == 100.0

    def test_negative_score_clamps_to_aaa(self):
        grade, _, _ = mapTo20Grade(-5)
        assert grade == "AAA"

    def test_score_above_100_clamps_to_d(self):
        grade, _, _ = mapTo20Grade(150)
        assert grade == "D"

    def test_boundary_bbb_minus(self):
        # BBB- threshold is 32, score 31 should be BBB-
        grade, _, _ = mapTo20Grade(31)
        assert grade == "BBB-"

    def test_boundary_bb_plus(self):
        # BB+ threshold is 37, score 33 should be BB+
        grade, _, _ = mapTo20Grade(33)
        assert grade == "BB+"

    def test_score_5_is_aa(self):
        # AA+ threshold is 5, AA threshold is 8
        # score=5 is >= AA+ threshold(5) -> falls to AA (next threshold 8)
        grade, _, _ = mapTo20Grade(5)
        assert grade == "AA"

    def test_returns_tuple_of_three(self):
        result = mapTo20Grade(50)
        assert len(result) == 3
        grade, desc, pd = result
        assert isinstance(grade, str)
        assert isinstance(desc, str)
        assert isinstance(pd, float)

    def test_health_score_inverse(self):
        """healthScore = 100 - score. Low score = high health."""
        score = 10
        health = 100 - score
        assert health == 90
        grade, _, _ = mapTo20Grade(score)
        assert grade in ("AA-", "A+")  # score 10 -> AA- threshold


# ═══════════════════════════════════════════════════════════
# weightedScore
# ═══════════════════════════════════════════════════════════


class TestWeightedScore:
    def test_equal_weights(self):
        axes = [
            {"name": "a", "score": 20, "weight": 1},
            {"name": "b", "score": 40, "weight": 1},
        ]
        result = weightedScore(axes)
        assert result == 30.0

    def test_unequal_weights(self):
        axes = [
            {"name": "a", "score": 10, "weight": 3},
            {"name": "b", "score": 50, "weight": 1},
        ]
        # (10*3 + 50*1) / 4 = 80/4 = 20
        result = weightedScore(axes)
        assert result == 20.0

    def test_none_score_excluded_and_weight_redistributed(self):
        axes = [
            {"name": "a", "score": 20, "weight": 1},
            {"name": "b", "score": None, "weight": 1},
            {"name": "c", "score": 40, "weight": 1},
        ]
        result = weightedScore(axes)
        assert result == 30.0

    def test_all_none_returns_none(self):
        axes = [
            {"name": "a", "score": None, "weight": 1},
            {"name": "b", "score": None, "weight": 1},
        ]
        result = weightedScore(axes)
        assert result is None

    def test_empty_list_returns_none(self):
        result = weightedScore([])
        assert result is None


# ═══════════════════════════════════════════════════════════
# gradeCategory
# ═══════════════════════════════════════════════════════════


class TestGradeCategory:
    def test_aaa_is_best(self):
        assert gradeCategory("AAA") == "최우량"

    def test_aa_plus_is_best(self):
        assert gradeCategory("AA+") == "최우량"

    def test_aa_minus_is_best(self):
        assert gradeCategory("AA-") == "최우량"

    def test_a_plus_is_excellent(self):
        assert gradeCategory("A+") == "우량"

    def test_a_is_excellent(self):
        assert gradeCategory("A") == "우량"

    def test_bbb_is_adequate(self):
        assert gradeCategory("BBB") == "적격"

    def test_bbb_minus_is_adequate(self):
        assert gradeCategory("BBB-") == "적격"

    def test_bb_plus_is_speculative(self):
        assert gradeCategory("BB+") == "투기"

    def test_b_is_high_risk(self):
        assert gradeCategory("B") == "고위험"

    def test_ccc_is_distressed(self):
        assert gradeCategory("CCC") == "부실"

    def test_d_is_distressed(self):
        assert gradeCategory("D") == "부실"

    def test_unknown_grade_falls_to_speculative(self):
        # Unknown grade -> isInvestmentGrade returns False, idx defaults to 10
        result = gradeCategory("XYZ")
        assert result == "투기"


# ═══════════════════════════════════════════════════════════
# isInvestmentGrade
# ═══════════════════════════════════════════════════════════


class TestIsInvestmentGrade:
    def test_aaa_is_investment(self):
        assert isInvestmentGrade("AAA") is True

    def test_bbb_minus_is_investment(self):
        assert isInvestmentGrade("BBB-") is True

    def test_bb_plus_is_not_investment(self):
        assert isInvestmentGrade("BB+") is False

    def test_d_is_not_investment(self):
        assert isInvestmentGrade("D") is False

    def test_unknown_grade_is_not_investment(self):
        assert isInvestmentGrade("XYZ") is False

    def test_boundary_between_bbb_minus_and_bb_plus(self):
        assert isInvestmentGrade("BBB-") is True
        assert isInvestmentGrade("BB+") is False


# ═══════════════════════════════════════════════════════════
# cashFlowGrade
# ═══════════════════════════════════════════════════════════


class TestCashFlowGrade:
    def test_none_ocf_returns_unknown(self):
        assert cashFlowGrade(None, True, 35) == "eCR-?"

    def test_ecr1_best_cash_flow(self):
        result = cashFlowGrade(ocfToSales=20, fcfPositive=True, ocfToDebt=35)
        assert result == "eCR-1"

    def test_ecr2_good_cash_flow(self):
        result = cashFlowGrade(ocfToSales=12, fcfPositive=False, ocfToDebt=25)
        assert result == "eCR-2"

    def test_ecr3_adequate(self):
        result = cashFlowGrade(ocfToSales=7, fcfPositive=False, ocfToDebt=10)
        assert result == "eCR-3"

    def test_ecr4_moderate(self):
        result = cashFlowGrade(ocfToSales=2, fcfPositive=False, ocfToDebt=5)
        assert result == "eCR-4"

    def test_ecr5_weak(self):
        result = cashFlowGrade(ocfToSales=-3, fcfPositive=False, ocfToDebt=0)
        assert result == "eCR-5"

    def test_ecr6_severe(self):
        result = cashFlowGrade(ocfToSales=-10, fcfPositive=False, ocfToDebt=-5)
        assert result == "eCR-6"

    def test_ecr3_with_unstable_trend_falls_to_ecr4(self):
        # ocf_to_sales=7 would be eCR-3 but trend_stable=False blocks it
        result = cashFlowGrade(ocfToSales=7, fcfPositive=False, ocfToDebt=10, ocfTrendStable=False)
        assert result == "eCR-4"

    def test_ecr1_requires_all_conditions(self):
        # High ocf_to_sales but fcf_positive=False -> falls to eCR-2
        result = cashFlowGrade(ocfToSales=20, fcfPositive=False, ocfToDebt=35)
        assert result == "eCR-2"


# ═══════════════════════════════════════════════════════════
# creditOutlook
# ═══════════════════════════════════════════════════════════


class TestCreditOutlook:
    def test_empty_history_returns_na(self):
        assert creditOutlook([]) == "N/A"

    def test_single_entry_returns_na(self):
        assert creditOutlook([30]) == "N/A"

    def test_improving_trend(self):
        # recent=20, oldest=30 -> delta=-10 < -5 -> "긍정적"
        # (lower score = better, so improvement)
        assert creditOutlook([20, 25, 30]) == "긍정적"

    def test_worsening_trend(self):
        # recent=40, oldest=30 -> delta=+10 > 5 -> "부정적"
        assert creditOutlook([40, 35, 30]) == "부정적"

    def test_stable_trend(self):
        # recent=30, oldest=28 -> delta=+2, abs < 5 -> "안정적"
        assert creditOutlook([30, 29, 28]) == "안정적"

    def test_exactly_minus_5_is_stable(self):
        # delta = -5, not < -5 -> "안정적"
        assert creditOutlook([25, 30]) == "안정적"

    def test_exactly_plus_5_is_stable(self):
        # delta = +5, not > 5 -> "안정적"
        assert creditOutlook([35, 30]) == "안정적"


# ═══════════════════════════════════════════════════════════
# healthScore = 100 - score
# ═══════════════════════════════════════════════════════════


class TestHealthScore:
    """healthScore is 100 - riskScore. Verify the relationship."""

    def test_zero_risk_means_perfect_health(self):
        risk = 0
        health = 100 - risk
        assert health == 100

    def test_max_risk_means_zero_health(self):
        risk = 100
        health = 100 - risk
        assert health == 0

    def test_mid_risk_mid_health(self):
        risk = 50
        health = 100 - risk
        assert health == 50
        grade, _, _ = mapTo20Grade(risk)
        assert grade == "B+"


# ═══════════════════════════════════════════════════════════
# estimatePD / notchGrade (additional pure functions)
# ═══════════════════════════════════════════════════════════


class TestEstimatePD:
    def test_aaa_pd(self):
        assert estimatePD("AAA") == 0.00

    def test_d_pd(self):
        assert estimatePD("D") == 100.0

    def test_unknown_grade_returns_default(self):
        assert estimatePD("XYZ") == 50.0


class TestNotchGrade:
    def test_upgrade_one_notch(self):
        # AA (idx=2) -> idx=3 = AA-
        assert notchGrade("AA", 1) == "AA-"

    def test_downgrade_one_notch(self):
        # AA (idx=2) -> idx=1 = AA+
        assert notchGrade("AA", -1) == "AA+"

    def test_clamp_at_top(self):
        assert notchGrade("AAA", -1) == "AAA"

    def test_clamp_at_bottom(self):
        assert notchGrade("D", 1) == "D"

    def test_unknown_grade_returns_same(self):
        assert notchGrade("XYZ", 2) == "XYZ"


class TestMarketGuard:
    """S1-L4.3 - credit 등급표는 KR(WICS) calibration 전용. 비-KR 은 등급 미산출(None).

    US(EDGAR) 회사를 그대로 태우면 sectorThresholds 가 KR 기본임계를 US-GAAP 숫자에 먹여
    non-None 가짜 등급을 내던 회귀(확신 오정렬)를 차단한다.
    """

    def test_us_market_returns_none_before_data(self):
        """market='US' 면 데이터 접근 전 None - 가짜 등급 차단."""
        from dartlab.credit.engine import evaluateCompany

        class _FakeUs:
            market = "US"

            def __getattr__(self, name):  # market 외 접근 = 가드 미작동 증거
                raise AssertionError(f"US 가드가 데이터 접근({name}) 전 None 반환해야 함")

        assert evaluateCompany(_FakeUs()) is None

    def test_kr_market_passes_guard(self, monkeypatch):
        """KR/KR하위시장(KOSPI·KOSDAQ)/미지정/비-str(mock) 은 가드 통과 - _getSectorInfo 진입.

        DartCompany.market 은 'KR' 상수지만 일부 mock 은 'KOSPI' 등 KR 하위시장 라벨을 쓴다
        (test_calcs CreditMockCompany). 이들·비-str mock 을 막으면 KR 평가가 깨진다(회귀).
        """
        from dartlab.credit import engine

        def _boom(company):
            raise RuntimeError("guard-passed")

        monkeypatch.setattr(engine, "_getSectorInfo", _boom)

        class _FakeKr:
            market = "KR"

        class _FakeKospi:  # KR 하위시장 라벨(test_calcs mock 형)
            market = "KOSPI"

        class _FakeKosdaq:
            market = "KOSDAQ"

        class _FakeDefault:  # market 미정의 → getattr 기본 'KR'
            pass

        class _FakeMock:  # 비-str market(MagicMock 류) → KR 로 통과
            market = object()

        for fake in (_FakeKr(), _FakeKospi(), _FakeKosdaq(), _FakeDefault(), _FakeMock()):
            with pytest.raises(RuntimeError, match="guard-passed"):
                engine.evaluateCompany(fake)


class TestNotchMonotonicGate:
    """위험점수가 gate를 넘은 뒤 notch 때문에 gate 이전보다 좋아지는 역전을 차단한다."""

    def test_large_company_notch_cannot_cross_gate_grade(self, monkeypatch):
        from dartlab.credit import _enginePostAdjust as post

        monkeypatch.setattr(post, "_calcCHSAdjustment", lambda company, score: {"status": "missing"})
        monkeypatch.setattr(
            post,
            "_calcNotchAdjustment",
            lambda *args, **kwargs: {"totalNotch": 4, "reasons": ["대형기업"]},
        )
        monkeypatch.setattr(post, "_explainDivergence", lambda *args, **kwargs: [])

        grade, _, _, _, _, notch, _ = post._applyPostAdjustments(
            object(),
            10.65,
            {"revenue": 100e12},
            {"history": []},
            [],
            False,
            False,
            None,
        )

        assert grade == "A+"
        assert notch["monotonicGate"] == "A+"
