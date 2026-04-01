"""신용평가(credit) 모듈 단위 테스트.

순수 함수 위주로 테스트 — Company/외부 데이터 의존 없음.
"""

from __future__ import annotations

import pytest

# ── metrics: _div, _cv, _calcSegmentHHI ──


class TestDiv:
    def test_basic(self):
        from dartlab.credit.metrics import _div

        assert _div(10, 2) == 5.0

    def test_pct(self):
        from dartlab.credit.metrics import _div

        assert _div(1, 4, pct=True) == 25.0

    def test_zero_denominator(self):
        from dartlab.credit.metrics import _div

        assert _div(10, 0) is None

    def test_none_inputs(self):
        from dartlab.credit.metrics import _div

        assert _div(None, 5) is None
        assert _div(5, None) is None

    def test_negative_denominator(self):
        from dartlab.credit.metrics import _div

        # abs(b) 사용
        assert _div(10, -2) == 5.0


class TestCV:
    def test_basic(self):
        from dartlab.credit.metrics import _cv

        result = _cv([100, 100, 100])
        assert result == 0.0

    def test_variation(self):
        from dartlab.credit.metrics import _cv

        result = _cv([10, 20, 30])
        assert result is not None
        assert result > 0

    def test_too_few(self):
        from dartlab.credit.metrics import _cv

        assert _cv([1, 2]) is None
        assert _cv([]) is None

    def test_none_filtered(self):
        from dartlab.credit.metrics import _cv

        assert _cv([1, None, 2]) is None  # only 2 valid

    def test_zero_mean(self):
        from dartlab.credit.metrics import _cv

        assert _cv([1, -1, 0]) is None  # mean = 0


class TestSegmentHHI:
    def test_none_input(self):
        from dartlab.credit.metrics import _calcSegmentHHI

        assert _calcSegmentHHI(None) is None
        assert _calcSegmentHHI([]) is None

    def test_single_segment(self):
        from dartlab.credit.metrics import _calcSegmentHHI

        # 1개 부문이면 다각화 의미 없음
        assert _calcSegmentHHI([{"매출액": 1000}]) is None

    def test_equal_split(self):
        from dartlab.credit.metrics import _calcSegmentHHI

        # 2개 균등 → 50²×2 = 5000
        result = _calcSegmentHHI([{"매출액": 500}, {"매출액": 500}])
        assert result == 5000.0

    def test_concentrated(self):
        from dartlab.credit.metrics import _calcSegmentHHI

        # 90:10 → 8100 + 100 = 8200
        result = _calcSegmentHHI([{"매출액": 900}, {"매출액": 100}])
        assert result == 8200.0


# ── __init__: _resolveAxis, _filterAxis, axes ──


class TestResolveAxis:
    def test_canonical(self):
        from dartlab.credit import _resolveAxis

        assert _resolveAxis("채무상환") == "채무상환"
        assert _resolveAxis("자본구조") == "자본구조"

    def test_alias(self):
        from dartlab.credit import _resolveAxis

        assert _resolveAxis("repayment") == "채무상환"
        assert _resolveAxis("leverage") == "자본구조"
        assert _resolveAxis("liquidity") == "유동성"

    def test_invalid(self):
        from dartlab.credit import _resolveAxis

        assert _resolveAxis("nonsense") is None

    def test_case_insensitive(self):
        from dartlab.credit import _resolveAxis

        assert _resolveAxis("Repayment") == "채무상환"


class TestFilterAxis:
    def test_valid(self):
        from dartlab.credit import _filterAxis

        result = {
            "grade": "dCR-A",
            "score": 20.0,
            "axes": [
                {"name": "채무상환능력", "score": 15.0, "weight": 25, "metrics": []},
                {"name": "자본구조", "score": 30.0, "weight": 15, "metrics": []},
            ],
        }
        filtered = _filterAxis(result, "채무상환")
        assert filtered is not None
        assert filtered["axis"] == "채무상환능력"
        assert filtered["score"] == 15.0

    def test_invalid_raises(self):
        from dartlab.credit import _filterAxis

        with pytest.raises(ValueError, match="알 수 없는 신용평가 축"):
            _filterAxis({"axes": []}, "garbage")


class TestAxes:
    def test_returns_7(self):
        from dartlab.credit import axes

        a = axes()
        assert len(a) == 7
        assert "채무상환" in a


# ── narrative: _severity, _fmt, _fmtTril ──


class TestSeverity:
    def test_thresholds(self):
        from dartlab.credit.narrative import _severity

        assert _severity(5) == "strong"
        assert _severity(10) == "adequate"
        assert _severity(24) == "adequate"
        assert _severity(25) == "weak"
        assert _severity(44) == "weak"
        assert _severity(45) == "critical"
        assert _severity(None) == "adequate"


class TestFmt:
    def test_none(self):
        from dartlab.credit.narrative import _fmt

        assert _fmt(None) == "N/A"

    def test_float(self):
        from dartlab.credit.narrative import _fmt

        assert _fmt(3.14159, "%", 1) == "3.1%"

    def test_int(self):
        from dartlab.credit.narrative import _fmt

        assert _fmt(42, "배") == "42배"


class TestFmtTril:
    def test_trillion(self):
        from dartlab.credit.narrative import _fmtTril

        assert _fmtTril(5e12) == "5.0조원"

    def test_billion(self):
        from dartlab.credit.narrative import _fmtTril

        assert _fmtTril(3e10) == "300억원"

    def test_small(self):
        from dartlab.credit.narrative import _fmtTril

        assert _fmtTril(50000) == "50,000원"

    def test_negative(self):
        from dartlab.credit.narrative import _fmtTril

        assert _fmtTril(-2e12) == "-2.0조원"

    def test_none(self):
        from dartlab.credit.narrative import _fmtTril

        assert _fmtTril(None) == "N/A"


# ── audit: _notchDiff ──


class TestNotchDiff:
    def test_same(self):
        from dartlab.credit.audit import _notchDiff

        assert _notchDiff("AAA", "AAA") == 0

    def test_adjacent(self):
        from dartlab.credit.audit import _notchDiff

        assert _notchDiff("AAA", "AA+") == 1

    def test_wide(self):
        from dartlab.credit.audit import _notchDiff

        assert _notchDiff("AAA", "D") == 19

    def test_invalid(self):
        from dartlab.credit.audit import _notchDiff

        assert _notchDiff("AAA", "INVALID") == 99
        assert _notchDiff("INVALID", "AAA") == 99


# ── engine: _isHolding, _isCaptiveFinance, _score* ──


class TestIsHolding:
    def test_holding(self):
        from dartlab.credit.engine import _isHolding

        class FakeCo:
            corpName = "LG지주"

        assert _isHolding(FakeCo()) is True

    def test_holdings_en(self):
        from dartlab.credit.engine import _isHolding

        class FakeCo:
            corpName = "SK Holdings"

        assert _isHolding(FakeCo()) is True

    def test_not_holding(self):
        from dartlab.credit.engine import _isHolding

        class FakeCo:
            corpName = "삼성전자"

        assert _isHolding(FakeCo()) is False

    def test_none_name(self):
        from dartlab.credit.engine import _isHolding

        class FakeCo:
            corpName = None

        assert _isHolding(FakeCo()) is False


class TestIsCaptiveFinance:
    def test_captive(self):
        from dartlab.credit.engine import _isCaptiveFinance

        assert _isCaptiveFinance(1600, 100, False) is True  # 16 > 15

    def test_not_captive(self):
        from dartlab.credit.engine import _isCaptiveFinance

        assert _isCaptiveFinance(100, 100, False) is False  # 1 < 15

    def test_financial_excluded(self):
        from dartlab.credit.engine import _isCaptiveFinance

        assert _isCaptiveFinance(1600, 100, True) is False

    def test_zero_ebitda(self):
        from dartlab.credit.engine import _isCaptiveFinance

        assert _isCaptiveFinance(1600, 0, False) is False
        assert _isCaptiveFinance(1600, None, False) is False


class TestScoreCashFlow:
    def test_strong(self):
        from dartlab.credit.engine import _scoreCashFlow

        latest = {"ocfToSales": 25, "fcfToSales": 15}
        metrics = {"history": [{"ocf": 100}, {"ocf": 80}, {"ocf": 60}]}
        scores = _scoreCashFlow(latest, metrics)
        score_dict = dict(scores)
        assert score_dict["OCF/매출"] == 0.0
        assert score_dict["FCF/매출"] == 0.0
        assert score_dict["OCF추세"] == 0.0

    def test_negative_ocf(self):
        from dartlab.credit.engine import _scoreCashFlow

        latest = {"ocfToSales": -5}
        metrics = {"history": [{"ocf": -10}, {"ocf": -5}, {"ocf": -1}]}
        scores = _scoreCashFlow(latest, metrics)
        score_dict = dict(scores)
        assert score_dict["OCF/매출"] >= 50  # penalty
        assert score_dict["OCF추세"] == 50.0  # latest negative


class TestScoreReliability:
    def test_clean(self):
        from dartlab.credit.engine import _scoreReliability

        rel = {"beneishMScore": -3.0, "piotroskiFScore": 8}
        scores = dict(_scoreReliability(rel, "적정"))
        assert scores["Beneish M"] == 0.0
        assert scores["Piotroski F"] == 0.0
        assert scores["감사의견"] == 0.0

    def test_warning(self):
        from dartlab.credit.engine import _scoreReliability

        rel = {"beneishMScore": -1.5, "piotroskiFScore": 2}
        scores = dict(_scoreReliability(rel, "한정"))
        assert scores["Beneish M"] == 45.0
        assert scores["Piotroski F"] == 45.0
        assert scores["감사의견"] == 50.0


class TestScoreDisclosureRisk:
    def test_none(self):
        from dartlab.credit.engine import _scoreDisclosureRisk

        assert _scoreDisclosureRisk(None) == []

    def test_clean(self):
        from dartlab.credit.engine import _scoreDisclosureRisk

        scores = dict(_scoreDisclosureRisk({"chronicYears": 0, "riskKeyword": 0}))
        assert scores["우발부채만성"] == 0.0
        assert scores["리스크키워드"] == 0.0

    def test_risky(self):
        from dartlab.credit.engine import _scoreDisclosureRisk

        scores = dict(_scoreDisclosureRisk({"chronicYears": 5, "riskKeyword": 3}))
        assert scores["우발부채만성"] == 60.0
        assert scores["리스크키워드"] == 60.0


class TestScoreBusinessStability:
    def test_stable_large(self):
        from dartlab.credit.engine import _scoreBusinessStability

        biz = {
            "revenueCV": 3,
            "opMarginCV": 5,
            "latestRevenue": 60e12,
            "segmentHHI": 1000,
        }
        scores = dict(_scoreBusinessStability(biz))
        assert scores["매출안정성"] == 0.0
        assert scores["이익안정성"] == 0.0
        assert scores["규모"] == 0.0
        assert scores["부문다각화"] == 0.0

    def test_volatile_small(self):
        from dartlab.credit.engine import _scoreBusinessStability

        biz = {
            "revenueCV": 35,
            "opMarginCV": 70,
            "latestRevenue": 5e9,
            "segmentHHI": 8000,
        }
        scores = dict(_scoreBusinessStability(biz))
        assert scores["매출안정성"] > 40
        assert scores["규모"] == 45.0
        assert scores["부문다각화"] == 40.0
