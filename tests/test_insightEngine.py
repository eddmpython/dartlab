"""insightEngine 테스트."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.scan.screen.rank import RankInfo
from dartlab.analysis.comparative.sector.types import Sector
from dartlab.analysis.financial.insight.anomaly import (
    _yoyChange,
    detectBalanceSheetShift,
    detectCashBurn,
    detectEarningsQuality,
    runAnomalyDetection,
)
from dartlab.analysis.financial.insight.benchmark import (
    BENCHMARKS,
    DEFAULT_BENCHMARK,
    getBenchmark,
    sectorAdjustment,
)
from dartlab.analysis.financial.insight.detector import (
    detectIncompleteYear,
)
from dartlab.analysis.financial.insight.grading import (
    _getGrowthYoY,
    _scoreToGrade,
    analyzeOpportunitySummary,
    analyzeProfitability,
    analyzeRiskSummary,
)
from dartlab.analysis.financial.insight.summary import (
    _eunNeun,
    _iGa,
    classifyProfile,
    generateSummary,
)
from dartlab.analysis.financial.insight.types import (
    AnalysisResult,
    Anomaly,
    Flag,
    InsightResult,
)
from dartlab.core.finance.ratios import RatioResult


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
            "performance": InsightResult(
                "F",
                "",
                risks=[
                    Flag("danger", "finance", "매출 급감"),
                    Flag("danger", "finance", "영업이익 급감"),
                ],
            ),
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
            "performance": InsightResult(
                "A",
                "",
                opportunities=[
                    Flag("strong", "growth", "매출 성장"),
                    Flag("strong", "growth", "이익 성장"),
                    Flag("strong", "finance", "ROE"),
                    Flag("positive", "finance", "부채"),
                    Flag("positive", "finance", "유동비"),
                ],
            ),
        }
        result = analyzeOpportunitySummary(insights)
        assert result.grade == "A"


class TestBenchmark:
    def test_get_benchmark_it(self):
        bm = getBenchmark(Sector.IT)
        assert bm.omMedian == 2.7
        assert bm.roeMedian == 12.7
        assert bm.n == 466

    def test_get_benchmark_unknown(self):
        bm = getBenchmark(Sector.UNKNOWN)
        assert bm == DEFAULT_BENCHMARK

    def test_all_sectors_have_benchmark(self):
        for s in Sector:
            if s == Sector.UNKNOWN:
                continue
            assert s in BENCHMARKS, f"{s} 벤치마크 누락"

    def test_sector_adjustment_above_q3(self):
        assert sectorAdjustment(30.0, 2.7, -4.9, 7.3) == 1

    def test_sector_adjustment_below_q1(self):
        assert sectorAdjustment(-10.0, 2.7, -4.9, 7.3) == -1

    def test_sector_adjustment_middle(self):
        assert sectorAdjustment(3.0, 2.7, -4.9, 7.3) == 0

    def test_sector_adjustment_none(self):
        assert sectorAdjustment(None, 2.7, -4.9, 7.3) == 0

    def test_profitability_with_sector_boost(self):
        ratios = RatioResult(operatingMargin=10.0, roe=15.0)
        result = analyzeProfitability(ratios, {}, isFinancial=False, sector=Sector.COMMUNICATION)
        assert any("섹터 보정" in d for d in result.details)

    def test_profitability_no_sector_adjustment(self):
        ratios = RatioResult(operatingMargin=5.0, roe=12.0)
        result = analyzeProfitability(ratios, {}, isFinancial=False, sector=Sector.IT)
        sectorDetails = [d for d in result.details if "섹터 보정" in d]
        assert len(sectorDetails) == 0


class TestRank:
    def test_rank_info_repr(self):
        ri = RankInfo(
            stockCode="005930",
            corpName="삼성전자",
            sector="IT",
            industryGroup="반도체와반도체장비",
            revenue=11e12,
            totalAssets=5e12,
            revenueRank=2,
            revenueTotal=2192,
            revenueRankInSector=2,
            revenueSectorTotal=467,
            sizeClass="large",
        )
        r = repr(ri)
        assert "삼성전자" in r
        assert "2/2192" in r
        assert "large" in r

    def test_rank_info_defaults(self):
        ri = RankInfo(stockCode="999999", corpName="테스트", sector="기타", industryGroup="기타")
        assert ri.revenueRank is None
        assert ri.sizeClass == ""
        assert ri.revenue is None

    def test_rank_info_size_class(self):
        ri = RankInfo(
            stockCode="000001",
            corpName="대형사",
            sector="IT",
            industryGroup="반도체와반도체장비",
            revenueRank=10,
            revenueTotal=2000,
            sizeClass="large",
        )
        assert ri.sizeClass == "large"
        ri2 = RankInfo(
            stockCode="000002",
            corpName="소형사",
            sector="IT",
            industryGroup="반도체와반도체장비",
            revenueRank=1500,
            revenueTotal=2000,
            sizeClass="small",
        )
        assert ri2.sizeClass == "small"


class TestAnomaly:
    def test_yoy_change(self):
        assert _yoyChange([100, 150]) == pytest.approx(50.0)
        assert _yoyChange([200, 100]) == pytest.approx(-50.0)
        assert _yoyChange([None]) is None

    def test_earnings_quality_skip_financial(self):
        series = {
            "IS": {"operating_profit": [100, 200], "net_profit": [50, 100]},
            "CF": {"operating_cashflow": [80, 40]},
        }
        result = detectEarningsQuality(series, isFinancial=True)
        assert result == []

    def test_earnings_quality_detect(self):
        series = {
            "IS": {"operating_profit": [100, 200], "net_profit": [50, 100]},
            "CF": {"operating_cashflow": [80, 40]},
        }
        result = detectEarningsQuality(series, isFinancial=False)
        assert len(result) >= 1
        assert result[0].severity == "danger"

    def test_balance_sheet_capital_erosion(self):
        series = {
            "BS": {
                "owners_of_parent_equity": [100, -50],
                "total_liabilities": [200, 300],
                "shortterm_borrowings": [0, 0],
                "longterm_borrowings": [0, 0],
                "debentures": [0, 0],
            }
        }
        result = detectBalanceSheetShift(series)
        found = [a for a in result if "자본잠식" in a.text]
        assert len(found) == 1

    def test_cash_burn_skip_financial(self):
        series = {
            "BS": {"cash_and_cash_equivalents": [100, 100]},
            "CF": {"operating_cashflow": [-50], "cash_flows_from_financing_activities": [80]},
        }
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
        grades = {
            "performance": "A",
            "profitability": "A",
            "health": "A",
            "cashflow": "B",
            "governance": "B",
            "risk": "A",
            "opportunity": "A",
        }
        assert classifyProfile(grades) == "premium"

    def test_classify_profile_caution(self):
        grades = {
            "performance": "F",
            "profitability": "F",
            "health": "F",
            "cashflow": "B",
            "governance": "A",
            "risk": "D",
            "opportunity": "D",
        }
        assert classifyProfile(grades) == "caution"

    def test_classify_profile_mixed(self):
        grades = {
            "performance": "C",
            "profitability": "C",
            "health": "C",
            "cashflow": "C",
            "governance": "C",
            "risk": "C",
            "opportunity": "C",
        }
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
