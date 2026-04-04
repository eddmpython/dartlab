"""review builders.py 단위 테스트 — 합성 데이터로 빌더 함수 검증.

각 빌더 함수가 올바른 Block 타입을 반환하고,
빈 입력에 빈 리스트를 반환하는지 검증한다.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ── Block 타입 import ──


@pytest.fixture()
def block_types():
    from dartlab.review.blocks import (
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )

    return {
        "HeadingBlock": HeadingBlock,
        "TextBlock": TextBlock,
        "TableBlock": TableBlock,
        "FlagBlock": FlagBlock,
        "MetricBlock": MetricBlock,
    }


# ── 1. profileBlock ──


class TestProfileBlock:
    def test_empty_data(self):
        from dartlab.review.builders import profileBlock

        assert profileBlock({}) == []
        assert profileBlock(None) == []

    def test_with_sector_and_products(self, block_types):
        from dartlab.review.builders import profileBlock

        data = {"sector": "전자부품", "products": "반도체, 디스플레이"}
        blocks = profileBlock(data)
        assert len(blocks) == 1
        assert isinstance(blocks[0], block_types["TextBlock"])
        assert "전자부품" in blocks[0].text
        assert "반도체" in blocks[0].text

    def test_with_sector_only(self, block_types):
        from dartlab.review.builders import profileBlock

        data = {"sector": "IT"}
        blocks = profileBlock(data)
        assert len(blocks) == 1
        assert "IT" in blocks[0].text

    def test_no_relevant_keys(self):
        from dartlab.review.builders import profileBlock

        assert profileBlock({"other": "value"}) == []


# ── 2. marginTrendBlock ──


class TestMarginTrendBlock:
    def test_empty_data(self):
        from dartlab.review.builders import marginTrendBlock

        assert marginTrendBlock({}) == []
        assert marginTrendBlock(None) == []

    def test_with_history(self, block_types):
        from dartlab.review.builders import marginTrendBlock

        data = {
            "history": [
                {"period": "2022", "grossMargin": 35.0, "operatingMargin": 15.0, "netMargin": 10.0},
                {"period": "2023", "grossMargin": 37.0, "operatingMargin": 16.0, "netMargin": 11.0},
            ]
        }
        blocks = marginTrendBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert blocks[0].level == 2
        # TextBlock(해석 문장)이 삽입될 수 있음 — 마지막이 TableBlock
        assert isinstance(blocks[-1], block_types["TableBlock"])

    def test_single_period_still_works(self, block_types):
        from dartlab.review.builders import marginTrendBlock

        data = {
            "history": [
                {"period": "2023", "grossMargin": 30.0, "operatingMargin": 12.0, "netMargin": 8.0},
            ]
        }
        blocks = marginTrendBlock(data)
        assert len(blocks) == 2


# ── 3. returnTrendBlock ──


class TestReturnTrendBlock:
    def test_empty_data(self):
        from dartlab.review.builders import returnTrendBlock

        assert returnTrendBlock({}) == []

    def test_with_history(self, block_types):
        from dartlab.review.builders import returnTrendBlock

        data = {
            "history": [
                {"period": "2022", "roe": 12.0, "roa": 6.0, "leverage": 2.0},
                {"period": "2023", "roe": 14.0, "roa": 7.0, "leverage": 2.0},
            ]
        }
        blocks = returnTrendBlock(data)
        assert len(blocks) == 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["TableBlock"])


# ── 4. growthTrendBlock ──


class TestGrowthTrendBlock:
    def test_empty_data(self):
        from dartlab.review.builders import growthTrendBlock

        assert growthTrendBlock({}) == []

    def test_with_history(self, block_types):
        from dartlab.review.builders import growthTrendBlock

        data = {
            "history": [
                {
                    "period": "2022",
                    "revenueYoy": 10.0,
                    "operatingIncomeYoy": 15.0,
                    "netIncomeYoy": 12.0,
                    "totalAssetsYoy": 5.0,
                },
                {
                    "period": "2023",
                    "revenueYoy": 8.0,
                    "operatingIncomeYoy": 11.0,
                    "netIncomeYoy": 9.0,
                    "totalAssetsYoy": 4.0,
                },
            ]
        }
        blocks = growthTrendBlock(data)
        assert len(blocks) == 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["TableBlock"])


# ── 5. leverageTrendBlock ──


class TestLeverageTrendBlock:
    def test_empty_data(self):
        from dartlab.review.builders import leverageTrendBlock

        assert leverageTrendBlock({}) == []

    def test_with_history(self, block_types):
        from dartlab.review.builders import leverageTrendBlock

        data = {
            "history": [
                {"period": "2022", "debtRatio": 80.0, "netDebtRatio": 50.0, "equityRatio": 55.0},
                {"period": "2023", "debtRatio": 75.0, "netDebtRatio": 45.0, "equityRatio": 57.0},
            ]
        }
        blocks = leverageTrendBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert any(isinstance(b, block_types["TableBlock"]) for b in blocks)


# ── 6. cashFlowOverviewBlock ──


class TestCashFlowOverviewBlock:
    def test_empty_data(self):
        from dartlab.review.builders import cashFlowOverviewBlock

        assert cashFlowOverviewBlock({}) == []
        assert cashFlowOverviewBlock({"history": []}) == []

    def test_with_history(self, block_types):
        from dartlab.review.builders import cashFlowOverviewBlock

        data = {
            "history": [
                {
                    "period": "2023",
                    "ocf": 5_000_000_000_000,
                    "icf": -3_000_000_000_000,
                    "fcfFinancing": -1_000_000_000_000,
                    "capex": -2_000_000_000_000,
                    "fcf": 3_000_000_000_000,
                    "pattern": "건전형 — 영업CF로 투자+재무 커버",
                },
            ]
        }
        blocks = cashFlowOverviewBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        # CF 추이 + CF 패턴 추이
        table_blocks = [b for b in blocks if isinstance(b, block_types["TableBlock"])]
        assert len(table_blocks) == 2


# ── 7. dividendPolicyBlock ──


class TestDividendPolicyBlock:
    def test_empty_data(self):
        from dartlab.review.builders import dividendPolicyBlock

        assert dividendPolicyBlock({}) == []
        assert dividendPolicyBlock(None) == []

    def test_with_history(self, block_types):
        from dartlab.review.builders import dividendPolicyBlock

        data = {
            "history": [
                {"period": "2022", "dividendsPaid": 1_000_000_000, "payoutRatio": 30.0, "dividendGrowth": 5.0},
                {"period": "2023", "dividendsPaid": 1_200_000_000, "payoutRatio": 32.0, "dividendGrowth": 20.0},
            ],
            "consecutiveYears": 5,
        }
        blocks = dividendPolicyBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        # Should include a consecutive years metric
        metric_blocks = [b for b in blocks if isinstance(b, block_types["MetricBlock"])]
        assert len(metric_blocks) >= 1

    def test_no_consecutive_years(self, block_types):
        from dartlab.review.builders import dividendPolicyBlock

        data = {
            "history": [
                {"period": "2023", "dividendsPaid": 100, "payoutRatio": 20.0, "dividendGrowth": 10.0},
            ],
        }
        blocks = dividendPolicyBlock(data)
        assert len(blocks) >= 2


# ── 8. scorecardBlock ──


class TestScorecardBlock:
    def test_empty_data(self):
        from dartlab.review.builders import scorecardBlock

        assert scorecardBlock({}) == []
        assert scorecardBlock(None) == []

    def test_with_items(self, block_types):
        from dartlab.review.builders import scorecardBlock

        data = {
            "items": [
                {"area": "수익성", "grade": "A"},
                {"area": "성장성", "grade": "B"},
                {"area": "안정성", "grade": "A"},
                {"area": "효율성", "grade": "C"},
                {"area": "현금흐름", "grade": "A"},
            ],
            "profile": "수익성 우수, 성장성 양호",
        }
        blocks = scorecardBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["TableBlock"])
        # profile TextBlock
        text_blocks = [b for b in blocks if isinstance(b, block_types["TextBlock"])]
        assert len(text_blocks) == 1
        assert "수익성 우수" in text_blocks[0].text

    def test_empty_items(self):
        from dartlab.review.builders import scorecardBlock

        assert scorecardBlock({"items": []}) == []


# ── 9. creditMetricsBlock ──


class TestCreditMetricsBlock:
    def test_empty_data(self):
        from dartlab.review.builders import creditMetricsBlock

        assert creditMetricsBlock({}) == []
        assert creditMetricsBlock(None) == []

    def test_with_history(self, block_types):
        from dartlab.review.builders import creditMetricsBlock

        data = {
            "history": [
                {
                    "period": "2023",
                    "ebitdaInterestCoverage": 15.0,
                    "debtToEbitda": 1.2,
                    "ffoToDebt": 45.0,
                    "debtRatio": 80.0,
                    "currentRatio": 150.0,
                    "ocfToSales": 12.0,
                },
            ]
        }
        blocks = creditMetricsBlock(data)
        assert len(blocks) == 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["TableBlock"])

    def test_handles_none_values(self, block_types):
        from dartlab.review.builders import creditMetricsBlock

        data = {
            "history": [
                {
                    "period": "2023",
                    "ebitdaInterestCoverage": None,
                    "debtToEbitda": 2.0,
                    "ffoToDebt": None,
                    "debtRatio": 100.0,
                    "currentRatio": None,
                    "ocfToSales": None,
                },
            ]
        }
        blocks = creditMetricsBlock(data)
        assert len(blocks) == 2


# ── 10. technicalVerdictBlock ──


class TestTechnicalVerdictBlock:
    def test_empty_data(self):
        from dartlab.review.builders import technicalVerdictBlock

        assert technicalVerdictBlock({}) == []
        assert technicalVerdictBlock(None) == []

    def test_full_data(self, block_types):
        from dartlab.review.builders import technicalVerdictBlock

        data = {
            "verdict": "강세",
            "score": 5,
            "rsi": 55.0,
            "adx": 30.0,
            "aboveSma20": True,
            "aboveSma60": True,
            "bbPosition": 65.0,
        }
        blocks = technicalVerdictBlock(data)
        assert len(blocks) == 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["MetricBlock"])
        metrics = blocks[1].metrics
        assert any("종합 판단" in m[0] for m in metrics)
        assert any("RSI" in m[0] for m in metrics)
        assert any("ADX" in m[0] for m in metrics)

    def test_rsi_overbought(self, block_types):
        from dartlab.review.builders import technicalVerdictBlock

        data = {"verdict": "약세", "score": -3, "rsi": 75.0}
        blocks = technicalVerdictBlock(data)
        metric = blocks[1]
        rsi_text = [m[1] for m in metric.metrics if "RSI" in m[0]][0]
        assert "과매수" in rsi_text

    def test_rsi_oversold(self, block_types):
        from dartlab.review.builders import technicalVerdictBlock

        data = {"verdict": "약세", "score": -2, "rsi": 25.0}
        blocks = technicalVerdictBlock(data)
        metric = blocks[1]
        rsi_text = [m[1] for m in metric.metrics if "RSI" in m[0]][0]
        assert "과매도" in rsi_text

    def test_minimal_data(self, block_types):
        from dartlab.review.builders import technicalVerdictBlock

        data = {"verdict": "중립", "score": 0}
        blocks = technicalVerdictBlock(data)
        assert len(blocks) == 2


# ── 11. Flags 빌더 ──


class TestFlagsBuilders:
    def test_revenue_flags_empty(self):
        from dartlab.review.builders import revenueFlagsBlock

        assert revenueFlagsBlock([]) == []

    def test_revenue_flags_mixed(self, block_types):
        from dartlab.review.builders import revenueFlagsBlock

        flags = [("매출 편중 위험", "warning"), ("해외 매출 확대", "opportunity")]
        blocks = revenueFlagsBlock(flags)
        assert len(blocks) == 2
        warnings = [b for b in blocks if b.kind == "warning"]
        opps = [b for b in blocks if b.kind == "opportunity"]
        assert len(warnings) == 1
        assert len(opps) == 1

    def test_profitability_flags(self, block_types):
        from dartlab.review.builders import profitabilityFlagsBlock

        flags = ["마진 하락 추세 주의"]
        blocks = profitabilityFlagsBlock(flags)
        assert len(blocks) == 1
        assert isinstance(blocks[0], block_types["FlagBlock"])
        assert blocks[0].kind == "warning"

    def test_profitability_flags_positive(self, block_types):
        from dartlab.review.builders import profitabilityFlagsBlock

        flags = ["마진 안정적 유지"]
        blocks = profitabilityFlagsBlock(flags)
        assert len(blocks) == 1
        assert blocks[0].kind == "opportunity"

    def test_capital_flags_empty(self):
        from dartlab.review.builders import capitalFlagsBlock

        assert capitalFlagsBlock([]) == []

    def test_credit_flags_with_warnings_and_opportunities(self, block_types):
        from dartlab.review.builders import creditFlagsBlock

        data = {
            "flags": [
                {"signal": "ICR 하락", "detail": "이자보상 악화", "type": "warning"},
                {"signal": "순현금 충분", "detail": "재무 여력", "type": "opportunity"},
            ]
        }
        blocks = creditFlagsBlock(data)
        assert len(blocks) == 2

    def test_credit_flags_empty(self):
        from dartlab.review.builders import creditFlagsBlock

        assert creditFlagsBlock({}) == []
        assert creditFlagsBlock({"flags": []}) == []

    def test_growth_flags(self, block_types):
        from dartlab.review.builders import growthFlagsBlock

        blocks = growthFlagsBlock(["매출 고성장 지속"])
        assert len(blocks) == 1
        assert blocks[0].kind == "opportunity"

    def test_growth_flags_empty(self):
        from dartlab.review.builders import growthFlagsBlock

        assert growthFlagsBlock([]) == []

    def test_stability_flags(self, block_types):
        from dartlab.review.builders import stabilityFlagsBlock

        blocks = stabilityFlagsBlock(["부채비율 과다"])
        assert len(blocks) == 1
        assert blocks[0].kind == "warning"

    def test_efficiency_flags(self, block_types):
        from dartlab.review.builders import efficiencyFlagsBlock

        blocks = efficiencyFlagsBlock(["자산회전율 양호"])
        assert len(blocks) == 1
        assert blocks[0].kind == "opportunity"

    def test_asset_flags(self, block_types):
        from dartlab.review.builders import assetFlagsBlock

        blocks = assetFlagsBlock(["건설중인자산 급증"])
        assert len(blocks) == 1
        assert blocks[0].kind == "warning"

    def test_cost_structure_flags(self, block_types):
        from dartlab.review.builders import costStructureFlagsBlock

        blocks = costStructureFlagsBlock(["원가율 안정 유지"])
        assert len(blocks) == 1
        assert blocks[0].kind == "opportunity"

    def test_capital_allocation_flags(self, block_types):
        from dartlab.review.builders import capitalAllocationFlagsBlock

        blocks = capitalAllocationFlagsBlock(["배당 성향 낮음"])
        assert len(blocks) == 1
        assert blocks[0].kind == "warning"

    def test_investment_flags(self, block_types):
        from dartlab.review.builders import investmentFlagsBlock

        blocks = investmentFlagsBlock(["ROIC > WACC 우량"])
        assert len(blocks) == 1
        assert blocks[0].kind == "opportunity"

    def test_cross_statement_flags(self, block_types):
        from dartlab.review.builders import crossStatementFlagsBlock

        blocks = crossStatementFlagsBlock(["BS-CF 괴리 발견"])
        assert len(blocks) == 1
        assert blocks[0].kind == "warning"

    def test_summary_flags(self, block_types):
        from dartlab.review.builders import summaryFlagsBlock

        # summaryFlagsBlock always uses kind="warning" (no auto-classification)
        blocks = summaryFlagsBlock(["재무 건전성 양호"])
        assert len(blocks) == 1
        assert blocks[0].kind == "warning"

    def test_cash_flow_flags(self, block_types):
        from dartlab.review.builders import cashFlowFlagsBlock

        blocks = cashFlowFlagsBlock(["FCF 감소 추세"])
        assert len(blocks) == 1
        assert blocks[0].kind == "warning"

    def test_governance_flags_empty(self):
        from dartlab.review.builders import governanceFlagsBlock

        assert governanceFlagsBlock([]) == []

    def test_governance_flags_with_data(self, block_types):
        from dartlab.review.builders import governanceFlagsBlock

        flags = [("지배구조 위험", "warning"), ("사외이사 비중 양호", "opportunity")]
        blocks = governanceFlagsBlock(flags)
        assert len(blocks) == 2

    def test_disclosure_delta_flags(self, block_types):
        from dartlab.review.builders import disclosureDeltaFlagsBlock

        flags = [("공시 변화 감지", "warning")]
        blocks = disclosureDeltaFlagsBlock(flags)
        assert len(blocks) == 1

    def test_peer_benchmark_flags_empty(self):
        from dartlab.review.builders import peerBenchmarkFlagsBlock

        assert peerBenchmarkFlagsBlock([]) == []


# ── 12. 내부 헬퍼 함수 ──


class TestHelpers:
    def test_extractSeries_from_history(self):
        from dartlab.review.builders import _extractSeries

        data = {
            "history": [
                {"period": "2022", "roe": 10.0},
                {"period": "2023", "roe": 12.0},
            ]
        }
        series = _extractSeries(data, "roe")
        assert len(series) == 2
        assert series[0]["value"] == 10.0
        assert series[1]["period"] == "2023"

    def test_extractSeries_none_values_excluded(self):
        from dartlab.review.builders import _extractSeries

        data = {
            "history": [
                {"period": "2022", "roe": 10.0},
                {"period": "2023"},  # roe missing
            ]
        }
        series = _extractSeries(data, "roe")
        assert len(series) == 1

    def test_extractSeries_fallback_to_field_list(self):
        from dartlab.review.builders import _extractSeries

        data = {
            "roe": [{"period": "2022", "value": 10.0}],
        }
        series = _extractSeries(data, "roe")
        assert len(series) == 1
        assert series[0]["value"] == 10.0

    def test_extractSeries_empty_history(self):
        from dartlab.review.builders import _extractSeries

        data = {"history": []}
        series = _extractSeries(data, "roe")
        assert series == []

    def test_timelineTable_empty(self):
        from dartlab.review.builders import _timelineTable

        result = _timelineTable([], ["A"])
        assert result is None

    def test_timelineTable_with_data(self):
        from dartlab.review.builders import _timelineTable

        specs = [
            ([{"period": "2022", "value": 10.0}, {"period": "2023", "value": 12.0}], "{:.1f}%"),
        ]
        result = _timelineTable(specs, ["ROE"])
        assert result is not None
        assert "" in result
        assert "2022" in result
        assert "2023" in result
        assert result["2022"][0] == "10.0%"

    def test_timelineTable_none_values(self):
        from dartlab.review.builders import _timelineTable

        specs = [
            ([{"period": "2022", "value": None}, {"period": "2023", "value": 5.0}], "{:.1f}%"),
        ]
        result = _timelineTable(specs, ["X"])
        assert result is not None
        assert result["2022"][0] == "-"
        assert result["2023"][0] == "5.0%"

    def test_timelineTable_multiple_rows(self):
        from dartlab.review.builders import _timelineTable

        specs = [
            ([{"period": "2023", "value": 10.0}], "{:.1f}%"),
            ([{"period": "2023", "value": 5.0}], "{:.1f}%"),
        ]
        result = _timelineTable(specs, ["ROE", "ROA"])
        assert result is not None
        assert result["2023"][0] == "10.0%"
        assert result["2023"][1] == "5.0%"

    def test_flagsBlock_positive_keyword_classification(self, block_types):
        from dartlab.review.builders import _flagsBlock

        flags = ["재무구조 건전", "부채비율 과다"]
        blocks = _flagsBlock(flags)
        assert len(blocks) == 2
        opp = [b for b in blocks if b.kind == "opportunity"]
        warn = [b for b in blocks if b.kind == "warning"]
        assert len(opp) == 1
        assert len(warn) == 1
        assert "건전" in opp[0].flags[0]

    def test_flagsBlock_empty(self):
        from dartlab.review.builders import _flagsBlock

        assert _flagsBlock([]) == []

    def test_flagsBlock_all_positive(self, block_types):
        from dartlab.review.builders import _flagsBlock

        flags = ["현금흐름 안정", "순현금 보유"]
        blocks = _flagsBlock(flags)
        assert len(blocks) == 1
        assert blocks[0].kind == "opportunity"

    def test_fmtAmtShort_krw(self):
        from dartlab.review.builders import _fmtAmtShort

        assert "조" in _fmtAmtShort(15_0000_0000_0000)
        assert "억" in _fmtAmtShort(5000_0000_0000)
        assert _fmtAmtShort(0) == "-"
        assert _fmtAmtShort(None) == "-"

    def test_fmtAmtShort_negative_trillion(self):
        from dartlab.review.builders import _fmtAmtShort

        result = _fmtAmtShort(-5_0000_0000_0000)
        assert result.startswith("-")
        assert "조" in result

    def test_fmtAmtShort_negative_billion(self):
        from dartlab.review.builders import _fmtAmtShort

        result = _fmtAmtShort(-5000_0000_0000)
        assert result.startswith("-")
        assert "억" in result

    def test_fmtAmtShort_small_number(self):
        from dartlab.review.builders import _fmtAmtShort

        result = _fmtAmtShort(12345)
        assert result == "12,345"


# ── 13. 추가 빌더 ──


class TestAdditionalBuilders:
    def test_piotroskiBlock(self, block_types):
        from dartlab.review.builders import piotroskiBlock

        data = {
            "total": 7,
            "interpretation": "strong",
            "items": [
                {"signal": "ROA > 0", "pass": True},
                {"signal": "OCF > 0", "pass": True},
                {"signal": "ROA 증가", "pass": False},
            ],
        }
        blocks = piotroskiBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["MetricBlock"])
        assert "7/9" in blocks[1].metrics[0][1]
        assert "건전" in blocks[1].metrics[0][1]

    def test_piotroskiBlock_empty(self):
        from dartlab.review.builders import piotroskiBlock

        assert piotroskiBlock({}) == []

    def test_concentrationBlock(self, block_types):
        from dartlab.review.builders import concentrationBlock

        data = {"hhi": 3500, "hhiLabel": "중간 집중", "topPct": 60, "domesticPct": 40}
        blocks = concentrationBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert any(isinstance(b, block_types["MetricBlock"]) for b in blocks)

    def test_concentrationBlock_with_history(self, block_types):
        from dartlab.review.builders import concentrationBlock

        data = {
            "hhi": 4000,
            "hhiLabel": "고집중",
            "topPct": 70,
            "hhiHistory": [
                {"year": "2022", "hhi": 3800},
                {"year": "2023", "hhi": 4000},
            ],
            "hhiDirection": "집중도 상승",
        }
        blocks = concentrationBlock(data)
        table_blocks = [b for b in blocks if isinstance(b, block_types["TableBlock"])]
        assert len(table_blocks) >= 1

    def test_creditScoreBlock(self, block_types):
        from dartlab.review.builders import creditScoreBlock

        data = {
            "grade": "AA-",
            "gradeDescription": "우량",
            "score": 85.0,
            "pdEstimate": 0.05,
            "eCR": "eCR-2",
            "outlook": "안정적",
            "sector": "전자",
            "investmentGrade": True,
            "axes": [
                {"name": "채무상환", "score": 90.0, "weight": 30, "metrics": [1, 2, 3]},
                {"name": "레버리지", "score": 80.0, "weight": 25, "metrics": [1, 2]},
            ],
        }
        blocks = creditScoreBlock(data)
        assert len(blocks) >= 2
        heading = blocks[0]
        assert isinstance(heading, block_types["HeadingBlock"])
        assert "AA-" in heading.helper

    def test_creditHistoryBlock(self, block_types):
        from dartlab.review.builders import creditHistoryBlock

        data = {
            "history": [
                {"period": "2022", "grade": "A+", "score": 80.0, "pdEstimate": 0.1},
                {"period": "2023", "grade": "AA-", "score": 85.0, "pdEstimate": 0.05},
            ],
            "stable": True,
        }
        blocks = creditHistoryBlock(data)
        assert len(blocks) >= 2

    def test_segmentCompositionBlock(self, block_types):
        from dartlab.review.builders import segmentCompositionBlock

        data = {
            "totalRevenue": 100_000_000,
            "hasOpIncome": True,
            "segments": [
                {"name": "반도체", "revenue": 60_000_000, "opIncome": 15_000_000, "opMargin": 25.0},
                {"name": "디스플레이", "revenue": 40_000_000, "opIncome": 5_000_000, "opMargin": 12.5},
            ],
        }
        blocks = segmentCompositionBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])

    def test_segmentCompositionBlock_empty_segments(self):
        from dartlab.review.builders import segmentCompositionBlock

        assert segmentCompositionBlock({"totalRevenue": 100, "segments": []}) == []

    def test_distressScoreBlock(self, block_types):
        from dartlab.review.builders import distressScoreBlock

        data = {
            "latestScore": 3.5,
            "zone": "안전",
            "history": [
                {"period": "2022", "altmanZScore": 3.2},
                {"period": "2023", "altmanZScore": 3.5},
            ],
        }
        blocks = distressScoreBlock(data)
        assert len(blocks) >= 2


# ── 14. _enrichedFlagsBlock ──


class TestEnrichedFlagsBlock:
    def test_empty_flags(self):
        from dartlab.review.builders import _enrichedFlagsBlock

        assert _enrichedFlagsBlock([]) == []

    def test_with_enriched_metadata(self, block_types):
        from dartlab.review.builders import _enrichedFlagsBlock

        flags = ["Beneish M-Score 임계값 초과"]
        enriched = [
            {
                "code": "BENEISH_MANIPULATOR",
                "message": "Beneish M-Score 임계값 초과",
                "precision": 0.50,
                "reference": "Beneish 1999",
                "sectorNote": "건설업 주의",
            }
        ]
        blocks = _enrichedFlagsBlock(flags, enriched)
        assert len(blocks) >= 1
        assert isinstance(blocks[0], block_types["FlagBlock"])
        assert blocks[0].enrichedFlags is not None
        assert "정밀도 50%" in blocks[0].flags[0]

    def test_without_enriched_falls_back(self, block_types):
        from dartlab.review.builders import _enrichedFlagsBlock

        flags = ["경고 문구"]
        blocks = _enrichedFlagsBlock(flags, None)
        assert len(blocks) == 1
        assert isinstance(blocks[0], block_types["FlagBlock"])


# ── 15. notesDetailBlocks ──


class TestNotesDetailBlocks:
    def test_empty(self):
        from dartlab.review.builders import _notesDetailBlocks

        assert _notesDetailBlocks({}, {}) == []
        assert _notesDetailBlocks({"notesDetail": {}}, {}) == []
        assert _notesDetailBlocks({"notesDetail": None}, {}) == []

    def test_with_notes(self, block_types):
        from dartlab.review.builders import _notesDetailBlocks

        data = {
            "notesDetail": {
                "borrowings": [
                    {"항목": "단기차입금", "금액": 1000},
                    {"항목": "장기차입금", "금액": 5000},
                ],
            }
        }
        blocks = _notesDetailBlocks(data, {"borrowings": "차입금 상세"})
        assert len(blocks) == 2
        assert isinstance(blocks[0], block_types["TextBlock"])
        assert "차입금 상세" in blocks[0].text
        assert isinstance(blocks[1], block_types["TableBlock"])

    def test_with_empty_rows(self):
        from dartlab.review.builders import _notesDetailBlocks

        data = {"notesDetail": {"borrowings": []}}
        blocks = _notesDetailBlocks(data, {"borrowings": "차입금"})
        assert blocks == []


# ── 16. segmentTrendBlock ──


class TestSegmentTrendBlock:
    def test_empty_data(self):
        from dartlab.review.builders import segmentTrendBlock

        assert segmentTrendBlock({}) == []
        assert segmentTrendBlock(None) == []

    def test_with_data(self, block_types):
        from dartlab.review.builders import segmentTrendBlock

        data = {
            "yearCols": ["2022", "2023"],
            "rows": [
                {"name": "반도체", "values": {"2022": 50_000_000, "2023": 60_000_000}, "yoy": 20.0},
                {"name": "디스플레이", "values": {"2022": 30_000_000, "2023": 28_000_000}, "yoy": -6.7},
            ],
        }
        blocks = segmentTrendBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["TableBlock"])

    def test_missing_yoy(self, block_types):
        from dartlab.review.builders import segmentTrendBlock

        data = {
            "yearCols": ["2023"],
            "rows": [{"name": "A", "values": {"2023": 100}, "yoy": None}],
        }
        blocks = segmentTrendBlock(data)
        assert len(blocks) >= 2


# ── 17. breakdownBlock ──


class TestBreakdownBlock:
    def test_empty_data(self):
        from dartlab.review.builders import breakdownBlock

        assert breakdownBlock({}, "productBreakdown") == []
        assert breakdownBlock(None, "productBreakdown") == []

    def test_with_items(self, block_types):
        from dartlab.review.builders import breakdownBlock

        data = {
            "items": [
                {"name": "제품A", "value": 500_000_000, "pct": 60.0},
                {"name": "제품B", "value": 300_000_000, "pct": 36.0},
                {"name": "기타", "value": 30_000_000, "pct": 4.0},
            ],
        }
        blocks = breakdownBlock(data, "productBreakdown")
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["TableBlock"])


# ── 18. revenueGrowthBlock ──


class TestRevenueGrowthBlock:
    def test_empty_data(self):
        from dartlab.review.builders import revenueGrowthBlock

        assert revenueGrowthBlock({}) == []
        assert revenueGrowthBlock(None) == []

    def test_with_yoy_and_cagr(self, block_types):
        from dartlab.review.builders import revenueGrowthBlock

        data = {"yoy": 15.3, "cagr3y": 10.5}
        blocks = revenueGrowthBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        metricBlocks = [b for b in blocks if isinstance(b, block_types["MetricBlock"])]
        assert metricBlocks
        labels = [m[0] for m in metricBlocks[0].metrics]
        assert "매출 YoY" in labels
        assert "3Y CAGR" in labels


# ── 19. revenueQualityBlock ──


class TestRevenueQualityBlock:
    def test_empty_data(self):
        from dartlab.review.builders import revenueQualityBlock

        assert revenueQualityBlock({}) == []
        assert revenueQualityBlock(None) == []

    def test_with_full_data(self, block_types):
        from dartlab.review.builders import revenueQualityBlock

        data = {
            "cashConversion": 120.0,
            "cashConversionLabel": "양호",
            "grossMargin": 35.5,
            "grossMarginTrend": [33.0, 34.0, 35.5],
            "grossMarginDirection": "상승",
        }
        blocks = revenueQualityBlock(data)
        assert len(blocks) == 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        metric = blocks[1]
        assert isinstance(metric, block_types["MetricBlock"])
        assert len(metric.metrics) == 3


# ── 20. growthContributionBlock ──


class TestGrowthContributionBlock:
    def test_empty_data(self):
        from dartlab.review.builders import growthContributionBlock

        assert growthContributionBlock({}) == []
        assert growthContributionBlock(None) == []

    def test_with_contributions(self, block_types):
        from dartlab.review.builders import growthContributionBlock

        data = {
            "totalGrowthPct": 15.0,
            "contributions": [
                {"name": "반도체", "amount": 8_000_000, "pct": 80},
                {"name": "디스플레이", "amount": 2_000_000, "pct": 20},
            ],
            "driver": "반도체 부문이 전체 성장 주도",
            "period": "2023",
        }
        blocks = growthContributionBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert "(2023)" in blocks[0].title


# ── 21. 자금구조 빌더 ──


class TestFundingBuilders:
    def test_fundingSourcesBlock_empty(self):
        from dartlab.review.builders import fundingSourcesBlock

        assert fundingSourcesBlock({}) == []
        assert fundingSourcesBlock(None) == []

    def test_fundingSourcesBlock_with_data(self, block_types):
        from dartlab.review.builders import fundingSourcesBlock

        data = {
            "latest": {
                "totalAssets": 100_0000_0000_0000,
                "retained": 50_0000_0000_0000,
                "retainedPct": 50.0,
                "paidIn": 20_0000_0000_0000,
                "paidInPct": 20.0,
                "finDebt": 20_0000_0000_0000,
                "finDebtPct": 20.0,
                "opFunding": 10_0000_0000_0000,
                "opFundingPct": 10.0,
            },
            "diagnosis": "내부유보 중심 조달",
        }
        blocks = fundingSourcesBlock(data)
        assert len(blocks) >= 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])

    def test_capitalOverviewBlock_empty(self):
        from dartlab.review.builders import capitalOverviewBlock

        assert capitalOverviewBlock({}) == []

    def test_capitalOverviewBlock_with_data(self, block_types):
        from dartlab.review.builders import capitalOverviewBlock

        data = {"metrics": [("부채비율", "80.0%"), ("순차입금", "1.2조")]}
        blocks = capitalOverviewBlock(data)
        assert len(blocks) == 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["MetricBlock"])

    def test_interestBurdenBlock_empty(self):
        from dartlab.review.builders import interestBurdenBlock

        assert interestBurdenBlock({}) == []

    def test_interestBurdenBlock_with_data(self, block_types):
        from dartlab.review.builders import interestBurdenBlock

        data = {"metrics": [("이자보상배율", "15.0배"), ("금융비용", "1,200억")]}
        blocks = interestBurdenBlock(data)
        assert len(blocks) == 2

    def test_liquidityBlock_empty(self):
        from dartlab.review.builders import liquidityBlock

        assert liquidityBlock({}) == []

    def test_liquidityBlock_with_data(self, block_types):
        from dartlab.review.builders import liquidityBlock

        data = {"metrics": [("유동비율", "150.0%"), ("당좌비율", "120.0%")]}
        blocks = liquidityBlock(data)
        assert len(blocks) == 2

    def test_distressBlock_empty(self):
        from dartlab.review.builders import distressBlock

        assert distressBlock({}) == []

    def test_distressBlock_with_data(self, block_types):
        from dartlab.review.builders import distressBlock

        data = {"metrics": [("Altman Z", "3.5 (안전)"), ("Piotroski F", "7/9")]}
        blocks = distressBlock(data)
        assert len(blocks) == 2


# ── 22. cashFlowBlock ──


class TestCashFlowBlock:
    def test_empty_data(self):
        from dartlab.review.builders import cashFlowBlock

        assert cashFlowBlock({}) == []
        assert cashFlowBlock(None) == []

    def test_with_pattern_and_metrics(self, block_types):
        from dartlab.review.builders import cashFlowBlock

        data = {
            "tableRows": [
                {"": "영업CF", "2023": 5_0000_0000_0000},
                {"": "투자CF", "2023": -3_0000_0000_0000},
            ],
            "cols": ["2023"],
            "pattern": "건전형",
            "metrics": [("FCF", "2.0조")],
        }
        blocks = cashFlowBlock(data)
        assert len(blocks) >= 3
        has_pattern = any(isinstance(b, block_types["TextBlock"]) and "건전형" in b.text for b in blocks)
        assert has_pattern

    def test_heading_only_returns_empty(self):
        from dartlab.review.builders import cashFlowBlock

        data = {"tableRows": None, "cols": None}
        assert cashFlowBlock(data) == []


# ── 23. 이익품질 빌더 ──


class TestEarningsQualityBuilders:
    def test_accrualAnalysisBlock_empty(self):
        from dartlab.review.builders import accrualAnalysisBlock

        assert accrualAnalysisBlock({}) == []

    def test_accrualAnalysisBlock_with_data(self, block_types):
        from dartlab.review.builders import accrualAnalysisBlock

        data = {
            "history": [
                {"period": "2022", "sloanAccrualRatio": 0.05, "accrualToRevenue": 3.0, "ocfToNi": 120},
                {"period": "2023", "sloanAccrualRatio": 0.08, "accrualToRevenue": 5.0, "ocfToNi": 110},
            ]
        }
        blocks = accrualAnalysisBlock(data)
        assert len(blocks) >= 2

    def test_earningsPersistenceBlock_empty(self):
        from dartlab.review.builders import earningsPersistenceBlock

        assert earningsPersistenceBlock({}) == []

    def test_earningsPersistenceBlock_with_cv(self, block_types):
        from dartlab.review.builders import earningsPersistenceBlock

        data = {
            "history": [
                {
                    "period": "2023",
                    "operatingIncome": 10_0000_0000,
                    "nonOperatingIncome": 2_0000_0000,
                    "nonOpRatio": 16.7,
                },
            ],
            "earningsVolatility": 0.35,
        }
        blocks = earningsPersistenceBlock(data)
        assert len(blocks) >= 2
        metric_blocks = [b for b in blocks if isinstance(b, block_types["MetricBlock"])]
        assert len(metric_blocks) == 1

    def test_beneishMScoreBlock_empty(self):
        from dartlab.review.builders import beneishMScoreBlock

        assert beneishMScoreBlock({}) == []

    def test_beneishMScoreBlock_with_threshold(self, block_types):
        from dartlab.review.builders import beneishMScoreBlock

        data = {
            "history": [
                {"period": "2023", "mScore": -2.5},
            ],
            "threshold": -1.78,
        }
        blocks = beneishMScoreBlock(data)
        assert len(blocks) >= 2
        text_blocks = [b for b in blocks if isinstance(b, block_types["TextBlock"])]
        assert any("-1.78" in b.text for b in text_blocks)

    def test_earningsQualityFlagsBlock_dict_format(self, block_types):
        from dartlab.review.builders import earningsQualityFlagsBlock

        data = {"flags": ["발생액 과다"], "enrichedFlags": None}
        blocks = earningsQualityFlagsBlock(data)
        assert len(blocks) == 1

    def test_earningsQualityFlagsBlock_list_format(self, block_types):
        from dartlab.review.builders import earningsQualityFlagsBlock

        blocks = earningsQualityFlagsBlock(["이익품질 양호"])
        assert len(blocks) == 1
        assert blocks[0].kind == "opportunity"


# ── 24. 비용구조 빌더 ──


class TestCostStructureBuilders:
    def test_costBreakdownBlock_empty(self):
        from dartlab.review.builders import costBreakdownBlock

        assert costBreakdownBlock({}) == []

    def test_costBreakdownBlock_with_data(self, block_types):
        from dartlab.review.builders import costBreakdownBlock

        data = {
            "history": [
                {"period": "2023", "costOfSalesRatio": 65.0, "sgaRatio": 15.0, "operatingCostRatio": 80.0},
            ]
        }
        blocks = costBreakdownBlock(data)
        assert len(blocks) >= 2

    def test_operatingLeverageBlock_empty(self):
        from dartlab.review.builders import operatingLeverageBlock

        assert operatingLeverageBlock({}) == []

    def test_operatingLeverageBlock_with_data(self, block_types):
        from dartlab.review.builders import operatingLeverageBlock

        data = {
            "history": [
                {"period": "2023", "dol": 2.5, "contributionProxy": 3.0},
            ]
        }
        blocks = operatingLeverageBlock(data)
        assert len(blocks) >= 2


# ── 25. 가치평가 빌더 ──


class TestValuationBuilders:
    def test_dcfValuationBlock_empty(self):
        from dartlab.review.builders import dcfValuationBlock

        assert dcfValuationBlock({}) == []
        assert dcfValuationBlock(None) == []

    def test_dcfValuationBlock_with_data(self, block_types):
        from dartlab.review.builders import dcfValuationBlock

        data = {
            "perShareValue": 80000,
            "currentPrice": 70000,
            "marginOfSafety": 14.3,
            "discountRate": 8.5,
            "terminalGrowth": 2.0,
            "fcfProjections": [5_0000_0000, 5_5000_0000, 6_0000_0000],
        }
        blocks = dcfValuationBlock(data)
        assert len(blocks) >= 2
        metric = [b for b in blocks if isinstance(b, block_types["MetricBlock"])][0]
        labels = [m[0] for m in metric.metrics]
        assert "적정가" in labels

    def test_ddmValuationBlock_na(self, block_types):
        from dartlab.review.builders import ddmValuationBlock

        data = {"modelUsed": "N/A"}
        blocks = ddmValuationBlock(data)
        assert len(blocks) == 2
        text = [b for b in blocks if isinstance(b, block_types["TextBlock"])][0]
        assert "불가" in text.text

    def test_ddmValuationBlock_with_data(self, block_types):
        from dartlab.review.builders import ddmValuationBlock

        data = {
            "intrinsicValue": 50000,
            "dividendPerShare": 1500,
            "dividendGrowth": 5.0,
            "payoutRatio": 30.0,
        }
        blocks = ddmValuationBlock(data)
        assert len(blocks) >= 2

    def test_relativeValuationBlock_empty(self):
        from dartlab.review.builders import relativeValuationBlock

        assert relativeValuationBlock({}) == []

    def test_relativeValuationBlock_with_data(self, block_types):
        from dartlab.review.builders import relativeValuationBlock

        data = {
            "impliedValues": {"PER": 75000, "PBR": 80000},
            "sectorMultiples": {"PER": 15.0, "PBR": 1.5},
            "currentMultiples": {"PER": 12.0, "PBR": 1.2},
            "premiumDiscount": {"PER": -20.0, "PBR": -20.0},
            "consensusValue": 77500,
        }
        blocks = relativeValuationBlock(data)
        assert len(blocks) >= 2


# ── 26. Penman / ROIC Tree 빌더 ──


class TestResearchBuilders:
    def test_penmanDecompositionBlock_empty(self):
        from dartlab.review.builders import penmanDecompositionBlock

        assert penmanDecompositionBlock({}) == []
        assert penmanDecompositionBlock(None) == []

    def test_penmanDecompositionBlock_with_data(self, block_types):
        from dartlab.review.builders import penmanDecompositionBlock

        data = {
            "history": [
                {
                    "period": "2023",
                    "rnoa": 15.0,
                    "flev": 0.3,
                    "nbc": 3.0,
                    "spread": 12.0,
                    "leverageEffect": 3.6,
                    "roce": 18.6,
                },
            ]
        }
        blocks = penmanDecompositionBlock(data)
        assert len(blocks) == 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["TableBlock"])

    def test_roicTreeBlock_empty(self):
        from dartlab.review.builders import roicTreeBlock

        assert roicTreeBlock({}) == []

    def test_roicTreeBlock_with_drivers(self, block_types):
        from dartlab.review.builders import roicTreeBlock

        data = {
            "history": [
                {
                    "period": "2023",
                    "roic": 12.0,
                    "operatingMargin": 15.0,
                    "capitalTurnover": 0.80,
                    "grossMargin": 35.0,
                    "sgaRatio": 20.0,
                    "marginDriver": "원가 절감",
                    "turnoverDriver": "자산 경량화",
                },
            ]
        }
        blocks = roicTreeBlock(data)
        assert len(blocks) >= 2
        text_blocks = [b for b in blocks if isinstance(b, block_types["TextBlock"])]
        assert len(text_blocks) >= 1

    def test_ocfDecompositionBlock_empty(self):
        from dartlab.review.builders import ocfDecompositionBlock

        assert ocfDecompositionBlock({}) == []

    def test_ocfDecompositionBlock_with_data(self, block_types):
        from dartlab.review.builders import ocfDecompositionBlock

        data = {
            "history": [
                {
                    "period": "2023",
                    "ni": 10_0000_0000,
                    "depEstimate": 5_0000_0000,
                    "wcEffect": -2_0000_0000,
                    "ocf": 13_0000_0000,
                    "residual": 0,
                },
            ]
        }
        blocks = ocfDecompositionBlock(data)
        assert len(blocks) >= 2


# ── 27. assetStructureBlock ──


class TestAssetStructureBlock:
    def test_empty_data(self):
        from dartlab.review.builders import assetStructureBlock

        assert assetStructureBlock({}) == []
        assert assetStructureBlock(None) == []

    def test_with_history(self, block_types):
        from dartlab.review.builders import assetStructureBlock

        data = {
            "history": [
                {
                    "period": "2023",
                    "totalAssets": 100_0000_0000_0000,
                    "opAssets": 60_0000_0000_0000,
                    "opAssetsPct": 60.0,
                    "nonOpAssets": 40_0000_0000_0000,
                    "nonOpAssetsPct": 40.0,
                    "noa": 50_0000_0000_0000,
                    "wc": 15_0000_0000_0000,
                    "fixedOp": 35_0000_0000_0000,
                    "receivables": 10_0000_0000_0000,
                    "inventory": 8_0000_0000_0000,
                    "ppe": 30_0000_0000_0000,
                    "intangibles": 3_0000_0000_0000,
                    "goodwill": 2_0000_0000_0000,
                    "cip": 1_0000_0000_0000,
                    "cash": 20_0000_0000_0000,
                    "investments": 15_0000_0000_0000,
                },
            ],
            "diagnosis": "영업자산 중심 구조",
        }
        blocks = assetStructureBlock(data)
        assert len(blocks) >= 3  # heading + 2 tables + diagnosis text
        table_blocks = [b for b in blocks if isinstance(b, block_types["TableBlock"])]
        assert len(table_blocks) >= 2


# ── 28. workingCapitalBlock ──


class TestWorkingCapitalBlock:
    def test_empty_data(self):
        from dartlab.review.builders import workingCapitalBlock

        assert workingCapitalBlock({}) == []
        assert workingCapitalBlock(None) == []

    def test_with_latest(self, block_types):
        from dartlab.review.builders import workingCapitalBlock

        data = {
            "latest": {
                "wc": 5_0000_0000_0000,
                "receivableDays": 45.0,
                "inventoryDays": 60.0,
                "payableDays": 30.0,
                "ccc": 75.0,
            }
        }
        blocks = workingCapitalBlock(data)
        assert len(blocks) >= 2
        metric = [b for b in blocks if isinstance(b, block_types["MetricBlock"])][0]
        labels = [m[0] for m in metric.metrics]
        assert "CCC" in labels


# ── 29. dupontBlock ──


class TestDupontBlock:
    def test_empty_data(self):
        from dartlab.review.builders import dupontBlock

        assert dupontBlock({}) == []

    def test_with_history(self, block_types):
        from dartlab.review.builders import dupontBlock

        data = {
            "history": [
                {"period": "2023", "operatingMargin": 15.0, "assetTurnover": 0.8, "leverage": 1.5},
            ]
        }
        blocks = dupontBlock(data)
        assert len(blocks) == 2
        assert isinstance(blocks[0], block_types["HeadingBlock"])
        assert isinstance(blocks[1], block_types["TableBlock"])


# ── 30. 자본배분 빌더 ──


class TestCapitalAllocationBuilders:
    def test_shareholderReturnBlock_empty(self):
        from dartlab.review.builders import shareholderReturnBlock

        assert shareholderReturnBlock({}) == []

    def test_reinvestmentBlock_empty(self):
        from dartlab.review.builders import reinvestmentBlock

        assert reinvestmentBlock({}) == []

    def test_fcfUsageBlock_empty(self):
        from dartlab.review.builders import fcfUsageBlock

        assert fcfUsageBlock({}) == []


# ── 31. 투자효율 빌더 ──


class TestInvestmentEfficiencyBuilders:
    def test_roicTimelineBlock_empty(self):
        from dartlab.review.builders import roicTimelineBlock

        assert roicTimelineBlock({}) == []

    def test_investmentIntensityBlock_empty(self):
        from dartlab.review.builders import investmentIntensityBlock

        assert investmentIntensityBlock({}) == []

    def test_evaTimelineBlock_empty(self):
        from dartlab.review.builders import evaTimelineBlock

        assert evaTimelineBlock({}) == []


# ── 32. 재무정합성 빌더 ──


class TestFinancialConsistencyBuilders:
    def test_isCfDivergenceBlock_empty(self):
        from dartlab.review.builders import isCfDivergenceBlock

        assert isCfDivergenceBlock({}) == []

    def test_isBsDivergenceBlock_empty(self):
        from dartlab.review.builders import isBsDivergenceBlock

        assert isBsDivergenceBlock({}) == []

    def test_anomalyScoreBlock_empty(self):
        from dartlab.review.builders import anomalyScoreBlock

        assert anomalyScoreBlock({}) == []

    def test_effectiveTaxRateBlock_empty(self):
        from dartlab.review.builders import effectiveTaxRateBlock

        assert effectiveTaxRateBlock({}) == []

    def test_deferredTaxBlock_empty(self):
        from dartlab.review.builders import deferredTaxBlock

        assert deferredTaxBlock({}) == []


# ── 33. 지배구조/공시변화 빌더 ──


class TestGovernanceBuilders:
    def test_ownershipTrendBlock_empty(self):
        from dartlab.review.builders import ownershipTrendBlock

        assert ownershipTrendBlock({}) == []

    def test_boardCompositionBlock_empty(self):
        from dartlab.review.builders import boardCompositionBlock

        assert boardCompositionBlock({}) == []

    def test_auditOpinionTrendBlock_empty(self):
        from dartlab.review.builders import auditOpinionTrendBlock

        assert auditOpinionTrendBlock({}) == []

    def test_disclosureChangeSummaryBlock_empty(self):
        from dartlab.review.builders import disclosureChangeSummaryBlock

        assert disclosureChangeSummaryBlock({}) == []

    def test_keyTopicChangesBlock_empty(self):
        from dartlab.review.builders import keyTopicChangesBlock

        assert keyTopicChangesBlock({}) == []

    def test_changeIntensityBlock_empty(self):
        from dartlab.review.builders import changeIntensityBlock

        assert changeIntensityBlock({}) == []


# ── 34. 비교분석 빌더 ──


class TestPeerBenchmarkBuilders:
    def test_peerRankingBlock_empty(self):
        from dartlab.review.builders import peerRankingBlock

        assert peerRankingBlock({}) == []

    def test_riskReturnPositionBlock_empty(self):
        from dartlab.review.builders import riskReturnPositionBlock

        assert riskReturnPositionBlock({}) == []


# ── 35. 매출전망 빌더 ──


class TestForecastBuilders:
    def test_revenueForecastBlock_empty(self):
        from dartlab.review.builders import revenueForecastBlock

        assert revenueForecastBlock({}) == []

    def test_segmentForecastBlock_empty(self):
        from dartlab.review.builders import segmentForecastBlock

        assert segmentForecastBlock({}) == []

    def test_forecastMethodologyBlock_empty(self):
        from dartlab.review.builders import forecastMethodologyBlock

        assert forecastMethodologyBlock({}) == []

    def test_forecastFlagsBlock_empty(self):
        from dartlab.review.builders import forecastFlagsBlock

        assert forecastFlagsBlock({}) == []


# ── 36. 기술적 분석 빌더 ──


class TestMarketAnalysisBuilders:
    def test_technicalSignalsBlock_empty(self):
        from dartlab.review.builders import technicalSignalsBlock

        assert technicalSignalsBlock({}) == []

    def test_marketBetaBlock_empty(self):
        from dartlab.review.builders import marketBetaBlock

        assert marketBetaBlock({}) == []

    def test_fundamentalDivergenceBlock_empty(self):
        from dartlab.review.builders import fundamentalDivergenceBlock

        assert fundamentalDivergenceBlock({}) == []

    def test_marketRiskBlock_empty(self):
        from dartlab.review.builders import marketRiskBlock

        assert marketRiskBlock({}) == []

    def test_marketAnalysisFlagsBlock_empty(self):
        from dartlab.review.builders import marketAnalysisFlagsBlock

        assert marketAnalysisFlagsBlock([]) == []
        assert marketAnalysisFlagsBlock(None) == []
