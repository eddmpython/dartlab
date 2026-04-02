"""credit narrative 단위 테스트 — 합성 지표 사용.

coverage 대상:
- narrative.py: narrateRepayment, narrateCapitalStructure, narrateLiquidity,
                narrateCashFlow, narrateBusinessStability, narrateReliability,
                narrateDisclosureRisk, buildNarratives, narrateProfile,
                narrateTrend, narrateBorrowings, narrateCausalChain,
                buildOverallNarrative, AxisNarrative
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ═══════════════════════════════════════════════════════════
# AxisNarrative dataclass
# ═══════════════════════════════════════════════════════════


class TestAxisNarrative:
    def test_basic_creation(self):
        from dartlab.credit.narrative import AxisNarrative

        n = AxisNarrative("테스트", "요약 문장", ["상세1", "상세2"], "strong")
        assert n.axisName == "테스트"
        assert n.summary == "요약 문장"
        assert len(n.details) == 2
        assert n.severity == "strong"

    def test_to_paragraph(self):
        from dartlab.credit.narrative import AxisNarrative

        n = AxisNarrative("테스트", "요약.", ["상세1.", "상세2."], "adequate")
        paragraph = n.toParagraph()
        assert "요약." in paragraph
        assert "상세1." in paragraph
        assert "상세2." in paragraph

    def test_to_paragraph_no_details(self):
        from dartlab.credit.narrative import AxisNarrative

        n = AxisNarrative("테스트", "요약만.", [], "strong")
        assert n.toParagraph() == "요약만."

    def test_severity_kr(self):
        from dartlab.credit.narrative import AxisNarrative

        assert AxisNarrative("", "", [], "strong").severityKr == "우수"
        assert AxisNarrative("", "", [], "adequate").severityKr == "양호"
        assert AxisNarrative("", "", [], "weak").severityKr == "주의"
        assert AxisNarrative("", "", [], "critical").severityKr == "위험"

    def test_default_severity(self):
        from dartlab.credit.narrative import AxisNarrative

        n = AxisNarrative("x", "y")
        assert n.severity == "adequate"
        assert n.details == []


# ═══════════════════════════════════════════════════════════
# _severity helper
# ═══════════════════════════════════════════════════════════


class TestSeverityHelper:
    def test_severity_ranges(self):
        from dartlab.credit.narrative import _severity

        assert _severity(None) == "adequate"
        assert _severity(5) == "strong"
        assert _severity(15) == "adequate"
        assert _severity(35) == "weak"
        assert _severity(50) == "critical"

    def test_boundary_values(self):
        from dartlab.credit.narrative import _severity

        assert _severity(0) == "strong"
        assert _severity(9.99) == "strong"
        assert _severity(10) == "adequate"
        assert _severity(24.99) == "adequate"
        assert _severity(25) == "weak"
        assert _severity(44.99) == "weak"
        assert _severity(45) == "critical"


# ═══════════════════════════════════════════════════════════
# narrateRepayment
# ═══════════════════════════════════════════════════════════


class TestNarrateRepayment:
    def test_strong_repayment(self):
        from dartlab.credit.narrative import narrateRepayment

        latest = {
            "ebitda": 5e12,
            "totalBorrowing": 2e12,
            "revenue": 30e12,
            "ebitdaInterestCoverage": 150,
            "debtToEbitda": 0.4,
            "ffoToDebt": 50,
        }
        result = narrateRepayment(latest, 5, "제조")
        assert result.axisName == "채무상환능력"
        assert result.severity == "strong"
        assert "우수" in result.summary
        assert len(result.details) >= 1

    def test_weak_repayment(self):
        from dartlab.credit.narrative import narrateRepayment

        latest = {
            "ebitda": 1e9,
            "totalBorrowing": 5e12,
            "revenue": 10e12,
            "ebitdaInterestCoverage": 1.5,
            "debtToEbitda": 8,
            "ffoToDebt": 5,
        }
        result = narrateRepayment(latest, 40, "제조")
        assert result.severity == "weak"
        assert len(result.details) >= 1

    def test_critical_repayment(self):
        from dartlab.credit.narrative import narrateRepayment

        latest = {
            "ebitda": -1e9,
            "revenue": 5e12,
            "ebitdaInterestCoverage": 0.5,
            "debtToEbitda": 15,
        }
        result = narrateRepayment(latest, 50, "건설")
        assert result.severity == "critical"
        assert "취약" in result.summary

    def test_no_ebitda(self):
        from dartlab.credit.narrative import narrateRepayment

        result = narrateRepayment({}, None, "기타")
        assert result.axisName == "채무상환능력"
        assert result.severity == "adequate"

    def test_high_icr_no_debt(self):
        from dartlab.credit.narrative import narrateRepayment

        latest = {"ebitdaInterestCoverage": 200}
        result = narrateRepayment(latest, 3, "IT")
        assert result.severity == "strong"
        assert any("무차입" in d for d in result.details)


# ═══════════════════════════════════════════════════════════
# narrateCapitalStructure
# ═══════════════════════════════════════════════════════════


class TestNarrateCapitalStructure:
    def test_low_debt_ratio(self):
        from dartlab.credit.narrative import narrateCapitalStructure

        latest = {"debtRatio": 30, "borrowingDependency": 5}
        result = narrateCapitalStructure(latest, 5)
        assert result.severity == "strong"
        assert any("보수적" in d for d in result.details)

    def test_high_debt_ratio(self):
        from dartlab.credit.narrative import narrateCapitalStructure

        latest = {"debtRatio": 350, "borrowingDependency": 40}
        result = narrateCapitalStructure(latest, 50)
        assert result.severity == "critical"
        assert any("과도한" in d for d in result.details)

    def test_net_cash_position(self):
        from dartlab.credit.narrative import narrateCapitalStructure

        latest = {"debtRatio": 80, "netDebtToEbitda": -1.5}
        result = narrateCapitalStructure(latest, 8)
        assert any("순현금" in d for d in result.details)

    def test_empty_latest(self):
        from dartlab.credit.narrative import narrateCapitalStructure

        result = narrateCapitalStructure({}, None)
        assert result.axisName == "자본구조"


# ═══════════════════════════════════════════════════════════
# narrateLiquidity
# ═══════════════════════════════════════════════════════════


class TestNarrateLiquidity:
    def test_strong_liquidity(self):
        from dartlab.credit.narrative import narrateLiquidity

        latest = {"currentRatio": 250, "shortTermDebtRatio": 20, "cashRatio": 40}
        result = narrateLiquidity(latest, 3)
        assert result.severity == "strong"
        assert "충분" in result.summary

    def test_weak_liquidity(self):
        from dartlab.credit.narrative import narrateLiquidity

        latest = {"currentRatio": 80, "shortTermDebtRatio": 60}
        result = narrateLiquidity(latest, 30)
        assert result.severity == "weak"

    def test_contradiction_explained(self):
        from dartlab.credit.narrative import narrateLiquidity

        latest = {"currentRatio": 200, "shortTermDebtRatio": 55, "cashRatio": 35}
        result = narrateLiquidity(latest, 5)
        # High current ratio + high short-term debt → contradiction explanation
        assert any("차환" in d for d in result.details)

    def test_empty_latest(self):
        from dartlab.credit.narrative import narrateLiquidity

        result = narrateLiquidity({}, None)
        assert result.axisName == "유동성"


# ═══════════════════════════════════════════════════════════
# narrateCashFlow
# ═══════════════════════════════════════════════════════════


class TestNarrateCashFlow:
    def test_strong_cashflow(self):
        from dartlab.credit.narrative import narrateCashFlow

        latest = {"ocfToSales": 20, "fcf": 1e12}
        metrics = {
            "history": [
                {"ocf": 5e12},
                {"ocf": 4.5e12},
                {"ocf": 4e12},
            ]
        }
        result = narrateCashFlow(latest, 5, metrics)
        assert result.severity == "strong"
        assert any("우수" in d for d in result.details)

    def test_negative_fcf(self):
        from dartlab.credit.narrative import narrateCashFlow

        latest = {"ocfToSales": 8, "fcf": -5e11}
        result = narrateCashFlow(latest, 20, {"history": []})
        assert any("음수" in d for d in result.details)

    def test_holding_company_ocf(self):
        from dartlab.credit.narrative import narrateCashFlow

        latest = {"ocfToSales": 150}
        result = narrateCashFlow(latest, 8, {"history": []})
        assert any("자회사" in d or "매출 대비" in d for d in result.details)

    def test_empty_latest(self):
        from dartlab.credit.narrative import narrateCashFlow

        result = narrateCashFlow({}, None, {})
        assert result.axisName == "현금흐름"

    def test_three_consecutive_positive_ocf(self):
        from dartlab.credit.narrative import narrateCashFlow

        metrics = {
            "history": [
                {"ocf": 1e12},
                {"ocf": 2e12},
                {"ocf": 3e12},
            ]
        }
        result = narrateCashFlow({}, 5, metrics)
        assert any("3기 연속" in d for d in result.details)


# ═══════════════════════════════════════════════════════════
# narrateBusinessStability
# ═══════════════════════════════════════════════════════════


class TestNarrateBusinessStability:
    def test_stable_business(self):
        from dartlab.credit.narrative import narrateBusinessStability

        biz = {"revenueCV": 5, "latestRevenue": 15e12, "segmentHHI": 1200}
        result = narrateBusinessStability(biz, 3)
        assert result.severity == "strong"
        assert any("안정" in d for d in result.details)

    def test_volatile_business(self):
        from dartlab.credit.narrative import narrateBusinessStability

        biz = {"revenueCV": 30, "latestRevenue": 5e11, "segmentHHI": 8000}
        result = narrateBusinessStability(biz, 35)
        assert result.severity == "weak"

    def test_empty_biz(self):
        from dartlab.credit.narrative import narrateBusinessStability

        result = narrateBusinessStability({}, None)
        assert result.axisName == "사업안정성"


# ═══════════════════════════════════════════════════════════
# narrateReliability
# ═══════════════════════════════════════════════════════════


class TestNarrateReliability:
    def test_clean_audit(self):
        from dartlab.credit.narrative import narrateReliability

        rel = {"beneishMScore": -3.0, "piotroskiFScore": 8}
        result = narrateReliability(rel, "적정", 5)
        assert result.severity == "strong"
        assert any("적정" in d for d in result.details)
        assert any("강건" in d for d in result.details)

    def test_manipulator_warning(self):
        from dartlab.credit.narrative import narrateReliability

        rel = {"beneishMScore": -1.0, "piotroskiFScore": 2}
        result = narrateReliability(rel, "한정", 35)
        assert any("조작" in d for d in result.details)
        assert any("한정" in d for d in result.details)

    def test_adverse_audit(self):
        from dartlab.credit.narrative import narrateReliability

        result = narrateReliability({}, "부적정", 50)
        assert any("비적정" in d or "심각" in d for d in result.details)

    def test_empty_reliability(self):
        from dartlab.credit.narrative import narrateReliability

        result = narrateReliability({}, None, None)
        assert result.axisName == "재무신뢰성"


# ═══════════════════════════════════════════════════════════
# narrateDisclosureRisk
# ═══════════════════════════════════════════════════════════


class TestNarrateDisclosureRisk:
    def test_no_risk(self):
        from dartlab.credit.narrative import narrateDisclosureRisk

        result = narrateDisclosureRisk(None, 3)
        assert result.severity == "strong"
        assert "감지되지 않았다" in result.summary

    def test_chronic_contingent_liability(self):
        from dartlab.credit.narrative import narrateDisclosureRisk

        dr = {"chronicYears": 4, "riskKeyword": 2}
        result = narrateDisclosureRisk(dr, 35)
        assert result.severity == "weak"
        assert any("만성" in d for d in result.details)
        assert any("키워드" in d for d in result.details)

    def test_minor_risk(self):
        from dartlab.credit.narrative import narrateDisclosureRisk

        dr = {"chronicYears": 1, "riskKeyword": 0}
        result = narrateDisclosureRisk(dr, 15)
        assert any("증가 추세" in d for d in result.details)

    def test_empty_dr_dict(self):
        from dartlab.credit.narrative import narrateDisclosureRisk

        dr = {}
        result = narrateDisclosureRisk(dr, 5)
        assert result.axisName == "공시리스크"
        assert any("특이" in d for d in result.details)


# ═══════════════════════════════════════════════════════════
# buildNarratives
# ═══════════════════════════════════════════════════════════


class TestBuildNarratives:
    def test_returns_seven_narratives(self):
        from dartlab.credit.narrative import buildNarratives

        result = {
            "axes": [
                {"name": "채무상환능력", "score": 10},
                {"name": "자본구조", "score": 15},
                {"name": "유동성", "score": 5},
                {"name": "현금흐름", "score": 20},
                {"name": "사업안정성", "score": 12},
                {"name": "재무신뢰성", "score": 8},
                {"name": "공시리스크", "score": 3},
            ],
            "metricsHistory": [
                {
                    "ebitda": 5e12,
                    "totalBorrowing": 2e12,
                    "revenue": 30e12,
                    "ebitdaInterestCoverage": 20,
                    "debtRatio": 60,
                    "currentRatio": 180,
                    "ocfToSales": 15,
                    "ocf": 4e12,
                },
            ],
            "businessStability": {"revenueCV": 8},
            "reliability": {"piotroskiFScore": 7},
            "auditOpinion": "적정",
            "disclosureRisk": None,
            "sector": "제조",
        }
        narratives = buildNarratives(result)
        assert len(narratives) == 7
        axis_names = [n.axisName for n in narratives]
        assert "채무상환능력" in axis_names
        assert "자본구조" in axis_names
        assert "유동성" in axis_names
        assert "현금흐름" in axis_names
        assert "사업안정성" in axis_names
        assert "재무신뢰성" in axis_names
        assert "공시리스크" in axis_names

    def test_empty_result(self):
        from dartlab.credit.narrative import buildNarratives

        narratives = buildNarratives({})
        assert len(narratives) == 7  # Still returns 7 with defaults


# ═══════════════════════════════════════════════════════════
# narrateProfile
# ═══════════════════════════════════════════════════════════


class TestNarrateProfile:
    def test_with_profile(self):
        from dartlab.credit.narrative import narrateProfile

        profile = {"sector": "섹터: IT > 반도체", "products": "주요제품: 메모리반도체"}
        result = narrateProfile(profile, None, None)
        assert "IT" in result
        assert "반도체" in result

    def test_with_segments(self):
        from dartlab.credit.narrative import narrateProfile

        segments = {
            "segments": [
                {"name": "DX", "revenue": 60e12, "opMargin": 15.0},
                {"name": "DS", "revenue": 40e12, "opMargin": 30.0},
            ],
            "totalRevenue": 100e12,
        }
        result = narrateProfile(None, segments, None)
        assert "DX" in result

    def test_empty(self):
        from dartlab.credit.narrative import narrateProfile

        result = narrateProfile(None, None, None)
        assert result == ""


# ═══════════════════════════════════════════════════════════
# narrateTrend
# ═══════════════════════════════════════════════════════════


class TestNarrateTrend:
    def test_with_history(self):
        from dartlab.credit.narrative import narrateTrend

        history = [
            {"revenue": 100e12, "operatingIncome": 15e12, "debtToEbitda": 1.5, "debtRatio": 60, "period": "2024"},
            {"revenue": 90e12, "operatingIncome": 10e12, "debtToEbitda": 2.0, "debtRatio": 65, "period": "2023"},
        ]
        result = narrateTrend(history)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "매출" in result

    def test_too_short(self):
        from dartlab.credit.narrative import narrateTrend

        result = narrateTrend([{"revenue": 100}])
        assert result == ""

    def test_no_change(self):
        from dartlab.credit.narrative import narrateTrend

        history = [
            {"revenue": 100, "debtToEbitda": 2.0, "debtRatio": 60},
            {"revenue": 100, "debtToEbitda": 2.0, "debtRatio": 60},
        ]
        result = narrateTrend(history)
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════
# narrateBorrowings
# ═══════════════════════════════════════════════════════════


class TestNarrateBorrowings:
    def test_no_debt(self):
        from dartlab.credit.narrative import narrateBorrowings

        result = narrateBorrowings(None, {"totalBorrowing": 0})
        assert "불필요" in result

    def test_with_debt(self):
        from dartlab.credit.narrative import narrateBorrowings

        latest = {
            "totalBorrowing": 5e12,
            "shortTermDebtRatio": 40,
            "netDebt": 3e12,
        }
        result = narrateBorrowings(None, latest)
        assert "조원" in result

    def test_high_cash_coverage(self):
        from dartlab.credit.narrative import narrateBorrowings

        latest = {
            "totalBorrowing": 2e12,
            "shortTermDebtRatio": 30,
            "cash": 5e12,
        }
        result = narrateBorrowings(None, latest)
        assert "차환 위험" in result or "상회" in result

    def test_none_latest(self):
        from dartlab.credit.narrative import narrateBorrowings

        result = narrateBorrowings(None, None)
        assert result == ""


# ═══════════════════════════════════════════════════════════
# narrateCausalChain
# ═══════════════════════════════════════════════════════════


class TestNarrateCausalChain:
    def test_normal_company(self):
        from dartlab.credit.narrative import narrateCausalChain

        latest = {
            "revenue": 30e12,
            "operatingIncome": 5e12,
            "ebitda": 7e12,
            "ocf": 6e12,
            "netDebt": -1e12,
            "debtRatio": 50,
        }
        result_data = {"grade": "AA-", "holding": False}
        text = narrateCausalChain(latest, result_data)
        assert "인과 요약" in text
        assert "AA-" in text

    def test_holding_company(self):
        from dartlab.credit.narrative import narrateCausalChain

        latest = {
            "revenue": 1e12,
            "ocf": 2e12,
            "netDebt": -5e12,
            "debtRatio": 30,
        }
        result_data = {"grade": "A+", "holding": True}
        text = narrateCausalChain(latest, result_data)
        assert "지주사" in text

    def test_empty(self):
        from dartlab.credit.narrative import narrateCausalChain

        text = narrateCausalChain({}, {"grade": "BBB"})
        assert isinstance(text, str)


# ═══════════════════════════════════════════════════════════
# buildOverallNarrative
# ═══════════════════════════════════════════════════════════


class TestBuildOverallNarrative:
    def test_with_strengths_and_weaknesses(self):
        from dartlab.credit.narrative import AxisNarrative, buildOverallNarrative

        narratives = [
            AxisNarrative("채무상환능력", "우수", [], "strong"),
            AxisNarrative("자본구조", "양호", [], "adequate"),
            AxisNarrative("유동성", "주의", [], "weak"),
        ]
        result = {"grade": "A", "score": 75.0}
        text = buildOverallNarrative(result, narratives)
        assert "A" in text
        assert "75.0" in text
        assert "채무상환능력" in text
        assert "유동성" in text

    def test_captive_finance(self):
        from dartlab.credit.narrative import buildOverallNarrative

        result = {"grade": "BBB+", "score": 55.0, "captiveFinance": True}
        text = buildOverallNarrative(result, [])
        assert "캡티브" in text

    def test_holding(self):
        from dartlab.credit.narrative import buildOverallNarrative

        result = {"grade": "AA", "score": 80.0, "holding": True}
        text = buildOverallNarrative(result, [])
        assert "지주사" in text


# ═══════════════════════════════════════════════════════════
# _fmt helpers
# ═══════════════════════════════════════════════════════════


class TestFormatHelpers:
    def test_fmt(self):
        from dartlab.credit.narrative import _fmt

        assert _fmt(None) == "N/A"
        assert _fmt(3.14, "%") == "3.1%"
        assert _fmt(100, "배", 0) == "100배"  # int → no decimal formatting
        assert _fmt(100.0, "배", 0) == "100배"  # float with 0 decimals
        assert _fmt(5) == "5"  # int → no decimal

    def test_fmtTril(self):
        from dartlab.credit.narrative import _fmtTril

        assert _fmtTril(None) == "N/A"
        assert "조원" in _fmtTril(5e12)
        assert "억원" in _fmtTril(5e10)
        assert "원" in _fmtTril(5000)
        assert "-" in _fmtTril(-3e12)
