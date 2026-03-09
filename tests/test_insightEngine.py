"""insightEngine 테스트."""

import pytest

from dartlab.engines.insightEngine.types import (
    Flag,
    InsightResult,
    Anomaly,
    AnalysisResult,
)
from dartlab.engines.insightEngine.detector import (
    detectIncompleteYear,
    detectFinancialSector,
)
from dartlab.engines.insightEngine.grading import (
    _scoreToGrade,
    _getGrowthYoY,
    analyzeRiskSummary,
    analyzeOpportunitySummary,
)
from dartlab.engines.insightEngine.anomaly import (
    _yoyChange,
    detectEarningsQuality,
    detectBalanceSheetShift,
    detectCashBurn,
    runAnomalyDetection,
)
from dartlab.engines.insightEngine.summary import (
    _eunNeun,
    _iGa,
    classifyProfile,
    generateSummary,
)


class TestTypes:
    def test_flag(self):
        f = Flag("danger", "finance", "영업이익 급감")
        assert f.level == "danger"
        assert f.category == "finance"

    def test_insight_result_defaults(self):
        r = InsightResult("A", "우수")
        assert r.grade == "A"
        assert r.details == []
        assert r.risks == []
        assert r.opportunities == []

    def test_anomaly(self):
        a = Anomaly("warning", "cashBurn", "현금 급감", -50.0)
        assert a.severity == "warning"
        assert a.value == -50.0

    def test_analysis_result_grades(self):
        r = AnalysisResult(
            corpName="테스트",
            stockCode="000000",
            isFinancial=False,
            performance=InsightResult("A", ""),
            profitability=InsightResult("B", ""),
            health=InsightResult("C", ""),
            cashflow=InsightResult("D", ""),
            governance=InsightResult("F", ""),
            risk=InsightResult("A", ""),
            opportunity=InsightResult("B", ""),
        )
        g = r.grades()
        assert g["performance"] == "A"
        assert g["governance"] == "F"
        assert len(g) == 7


class TestDetector:
    def test_incomplete_year_full(self):
        periods = ["2022_Q1", "2022_Q2", "2022_Q3", "2022_Q4", "2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4"]
        year, count = detectIncompleteYear(periods)
        assert year == "2023"
        assert count == 4

    def test_incomplete_year_partial(self):
        periods = ["2022_Q1", "2022_Q2", "2022_Q3", "2022_Q4", "2023_Q1", "2023_Q2"]
        year, count = detectIncompleteYear(periods)
        assert year == "2023"
        assert count == 2


class TestGrading:
    def test_score_to_grade(self):
        assert _scoreToGrade(5, 6) == "A"
        assert _scoreToGrade(3, 6) == "B"
        assert _scoreToGrade(2, 6) == "C"
        assert _scoreToGrade(0, 6) == "D"
        assert _scoreToGrade(-1, 6) == "F"

    def test_growth_yoy(self):
        assert _getGrowthYoY([100, 120]) == pytest.approx(20.0)
        assert _getGrowthYoY([100, 80]) == pytest.approx(-20.0)
        assert _getGrowthYoY([None]) is None
        assert _getGrowthYoY([100]) is None

    def test_growth_yoy_with_none(self):
        assert _getGrowthYoY([None, 100, None, 200]) == pytest.approx(100.0)

    def test_risk_summary_no_risks(self):
        insights = {
            "performance": InsightResult("A", "", risks=[]),
            "profitability": InsightResult("B", "", risks=[]),
        }
        result = analyzeRiskSummary(insights)
        assert result.grade == "A"

    def test_risk_summary_danger(self):
        insights = {
            "performance": InsightResult("F", "", risks=[
                Flag("danger", "finance", "매출 급감"),
                Flag("danger", "finance", "영업이익 급감"),
            ]),
        }
        result = analyzeRiskSummary(insights)
        assert result.grade == "F"

    def test_opportunity_none(self):
        insights = {
            "performance": InsightResult("D", "", opportunities=[]),
        }
        result = analyzeOpportunitySummary(insights)
        assert result.grade == "D"

    def test_opportunity_strong(self):
        insights = {
            "performance": InsightResult("A", "", opportunities=[
                Flag("strong", "growth", "매출 성장"),
                Flag("strong", "growth", "이익 성장"),
                Flag("strong", "finance", "ROE"),
                Flag("positive", "finance", "부채"),
                Flag("positive", "finance", "유동비"),
            ]),
        }
        result = analyzeOpportunitySummary(insights)
        assert result.grade == "A"


class TestAnomaly:
    def test_yoy_change(self):
        assert _yoyChange([100, 150]) == pytest.approx(50.0)
        assert _yoyChange([200, 100]) == pytest.approx(-50.0)
        assert _yoyChange([None]) is None

    def test_earnings_quality_skip_financial(self):
        series = {"IS": {"operating_income": [100, 200], "net_income": [50, 100]}, "CF": {"operating_cashflow": [80, 40]}}
        result = detectEarningsQuality(series, isFinancial=True)
        assert result == []

    def test_earnings_quality_detect(self):
        series = {"IS": {"operating_income": [100, 200], "net_income": [50, 100]}, "CF": {"operating_cashflow": [80, 40]}}
        result = detectEarningsQuality(series, isFinancial=False)
        assert len(result) >= 1
        assert result[0].severity == "danger"

    def test_balance_sheet_capital_erosion(self):
        series = {"BS": {"total_equity": [100, -50], "total_liabilities": [200, 300], "short_term_borrowings": [0, 0], "long_term_borrowings": [0, 0], "bonds": [0, 0]}}
        result = detectBalanceSheetShift(series)
        found = [a for a in result if "자본잠식" in a.text]
        assert len(found) == 1

    def test_cash_burn_skip_financial(self):
        series = {"BS": {"cash_and_equivalents": [100, 100]}, "CF": {"operating_cashflow": [-50], "financing_cashflow": [80]}}
        result = detectCashBurn(series, isFinancial=True)
        cashBurnItems = [a for a in result if "차입으로" in a.text]
        assert len(cashBurnItems) == 0

    def test_run_anomaly_detection(self):
        series = {"IS": {}, "BS": {}, "CF": {}}
        result = runAnomalyDetection(series, isFinancial=False)
        assert isinstance(result, list)


class TestSummary:
    def test_eun_neun_hangul(self):
        assert _eunNeun("삼성전자") == "삼성전자는"
        assert _eunNeun("카카오") == "카카오는"
        assert _eunNeun("한국전력") == "한국전력은"

    def test_i_ga_hangul(self):
        assert _iGa("수익성") == "수익성이"
        assert _iGa("지배구조") == "지배구조가"
        assert _iGa("현금흐름") == "현금흐름이"

    def test_classify_profile_premium(self):
        grades = {"performance": "A", "profitability": "A", "health": "A", "cashflow": "B", "governance": "B", "risk": "A", "opportunity": "A"}
        assert classifyProfile(grades) == "premium"

    def test_classify_profile_caution(self):
        grades = {"performance": "F", "profitability": "F", "health": "F", "cashflow": "B", "governance": "A", "risk": "D", "opportunity": "D"}
        assert classifyProfile(grades) == "caution"

    def test_classify_profile_mixed(self):
        grades = {"performance": "C", "profitability": "C", "health": "C", "cashflow": "C", "governance": "C", "risk": "C", "opportunity": "C"}
        assert classifyProfile(grades) == "mixed"

    def test_generate_summary_premium(self):
        insights = {
            "performance": InsightResult("A", "", details=["매출 고성장 (+50%)"]),
            "profitability": InsightResult("A", ""),
            "health": InsightResult("A", ""),
        }
        summary = generateSummary("삼성전자", insights, [], "premium")
        assert "삼성전자는" in summary
        assert "우량" in summary

    def test_generate_summary_with_anomaly(self):
        insights = {"performance": InsightResult("F", "", details=["매출 급감"])}
        anomalies = [Anomaly("danger", "earningsQuality", "이익↑ but CF↓ — 의심")]
        summary = generateSummary("테스트", insights, anomalies, "caution")
        assert "유의" in summary
