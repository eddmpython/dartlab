"""pipeline 모듈 테스트 — LLM 불필요."""

import pytest

pytestmark = pytest.mark.unit

import polars as pl

import dartlab.engines.ai.runtime.pipeline as pipeline_module
from dartlab.engines.ai.runtime.pipeline import (
    _df_to_simple_md,
    _run_dividend_analysis,
    _run_growth_analysis,
    _run_health_analysis,
    _run_profitability_analysis,
    _run_risk_analysis,
    classify_question,
    run_pipeline,
)

# ══════════════════════════════════════
# Mock Company
# ══════════════════════════════════════


class MockCompany:
    """테스트용 가짜 Company."""

    def __init__(self, **attrs):
        for k, v in attrs.items():
            setattr(self, k, v)


def _make_bs():
    return pl.DataFrame(
        {
            "계정명": ["자산총계", "부채총계", "자본총계", "유동자산", "유동부채"],
            "2023": [15000, 5000, 10000, 8000, 4000],
            "2022": [13000, 4000, 9000, 7000, 3500],
        }
    )


def _make_is():
    return pl.DataFrame(
        {
            "계정명": ["매출액", "영업이익", "당기순이익"],
            "2023": [20000, 3000, 2000],
            "2022": [18000, 2500, 1800],
            "2021": [16000, 2200, 1600],
        }
    )


def _make_cf():
    return pl.DataFrame(
        {
            "계정명": ["영업활동으로인한현금흐름", "투자활동으로인한현금흐름"],
            "2023": [5000, -3000],
            "2022": [3000, -2000],
        }
    )


def _make_dividend():
    return pl.DataFrame(
        {
            "year": [2021, 2022, 2023],
            "dps": [1000, 1200, 1500],
            "totalDividend": [5000, 6000, 7500],
        }
    )


# ══════════════════════════════════════
# classify_question
# ══════════════════════════════════════


class TestClassifyQuestion:
    def test_health(self):
        assert classify_question("재무 건전성을 분석해줘") == "건전성"

    def test_profitability(self):
        assert classify_question("수익성은 어떤가요") == "수익성"

    def test_growth(self):
        assert classify_question("성장성을 분석해줘") == "성장성"

    def test_dividend(self):
        assert classify_question("배당 정책을 분석해줘") == "배당"

    def test_governance(self):
        assert classify_question("지배구조를 분석해줘") == "지배구조"

    def test_risk(self):
        assert classify_question("리스크를 분석해줘") == "리스크"

    def test_general(self):
        """매칭 안 되면 종합."""
        assert classify_question("xyz 뭔가 알려줘") == "종합"

    def test_combined(self):
        """종합 분석."""
        assert classify_question("종합 분석해줘") == "종합"


# ══════════════════════════════════════
# _df_to_simple_md
# ══════════════════════════════════════


class TestDfToSimpleMd:
    def test_basic(self):
        df = pl.DataFrame({"year": [2023], "v": [100]})
        result = _df_to_simple_md(df)
        assert "year" in result
        assert "100" in result
        assert "|" in result

    def test_empty(self):
        df = pl.DataFrame()
        assert _df_to_simple_md(df) == ""

    def test_none(self):
        assert _df_to_simple_md(None) == ""


# ══════════════════════════════════════
# 파이프라인 러너
# ══════════════════════════════════════


class TestRunHealthAnalysis:
    def test_basic(self):
        company = MockCompany(BS=_make_bs(), IS=_make_is())
        result = _run_health_analysis(company, ["BS", "IS"])
        assert result is not None
        assert "재무비율" in result

    def test_no_bs(self):
        company = MockCompany(BS=None, IS=_make_is())
        result = _run_health_analysis(company, ["BS", "IS"])
        assert result is None


class TestRunProfitabilityAnalysis:
    def test_basic(self):
        company = MockCompany(IS=_make_is())
        result = _run_profitability_analysis(company, ["IS"])
        assert result is not None
        assert "수익성" in result or "YoY" in result

    def test_no_is(self):
        company = MockCompany(IS=None)
        result = _run_profitability_analysis(company, ["IS"])
        assert result is None


class TestRunGrowthAnalysis:
    def test_basic(self):
        company = MockCompany(IS=_make_is())
        result = _run_growth_analysis(company, ["IS"])
        assert result is not None
        assert "성장률" in result or "CAGR" in result

    def test_no_is(self):
        company = MockCompany(IS=None)
        result = _run_growth_analysis(company, ["IS"])
        assert result is None


class TestRunDividendAnalysis:
    def test_basic(self):
        company = MockCompany(dividend=_make_dividend())
        result = _run_dividend_analysis(company, ["dividend"])
        assert result is not None
        assert "배당" in result

    def test_no_dividend(self):
        company = MockCompany(dividend=None)
        result = _run_dividend_analysis(company, ["dividend"])
        assert result is None


class TestRunRiskAnalysis:
    def test_with_anomalies(self):
        """급격한 변동이 있는 데이터."""
        is_ = pl.DataFrame(
            {
                "계정명": ["매출액", "영업이익"],
                "2023": [20000, 3000],
                "2022": [10000, 500],  # 2023에서 100% 증가
            }
        )
        company = MockCompany(BS=_make_bs(), IS=is_, CF=_make_cf())
        result = _run_risk_analysis(company, ["BS", "IS", "CF"])
        # anomalies가 있으면 결과가 있어야 함
        if result:
            assert "이상치" in result

    def test_no_data(self):
        company = MockCompany(BS=None, IS=None, CF=None)
        result = _run_risk_analysis(company, [])
        assert result is None


# ══════════════════════════════════════
# run_pipeline 통합
# ══════════════════════════════════════


class TestRunPipeline:
    def test_health_pipeline(self):
        company = MockCompany(BS=_make_bs(), IS=_make_is())
        result = run_pipeline(company, "재무 건전성 분석", ["BS", "IS"])
        assert "자동 분석" in result

    def test_no_matching(self):
        """해당 파이프라인이 없는 질문 유형."""
        company = MockCompany()
        result = run_pipeline(company, "지배구조를 분석해줘", [])
        # 지배구조는 _PIPELINE_MAP에 없으므로 빈 문자열
        assert result == ""

    def test_error_resilience(self):
        """파이프라인 러너가 에러 나도 계속 실행."""
        company = MockCompany(BS="not_a_dataframe", IS=_make_is())
        result = run_pipeline(company, "재무 건전성 분석", ["BS", "IS"])
        # BS가 DataFrame이 아니어서 health는 실패하지만 에러가 나지 않음
        assert isinstance(result, str)

    def test_runner_value_error_does_not_block_next_runner(self, monkeypatch):
        def broken_runner(company, included_tables):
            raise ValueError("broken runner")

        def healthy_runner(company, included_tables):
            return "### 정상 러너"

        monkeypatch.setitem(
            pipeline_module._PIPELINE_MAP,
            "건전성",
            [broken_runner, healthy_runner],
        )
        monkeypatch.setattr(pipeline_module, "_run_l2_engines", lambda company, q_type: None)

        result = run_pipeline(MockCompany(), "재무 건전성 분석", [])

        assert "정상 러너" in result
