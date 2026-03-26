"""context 모듈 테스트 — 데이터 의존 없음."""

import pytest

pytestmark = pytest.mark.unit

import polars as pl

from dartlab.core.registry import ColumnMeta, DataEntry
from dartlab.ai.context import (
    _build_ratios_section,
    _compute_derived_metrics,
    _resolve_tables,
    df_to_markdown,
    scan_available_modules,
)
from dartlab.ai.metadata import ModuleMeta
from dartlab.analysis.comparative.sector.types import IndustryGroup, Sector, SectorInfo

# ══════════════════════════════════════
# df_to_markdown
# ══════════════════════════════════════


class TestDfToMarkdown:
    def test_basic(self):
        df = pl.DataFrame({"year": [2023, 2022], "revenue": [150, 120]})
        result = df_to_markdown(df)
        assert "year" in result
        assert "revenue" in result
        assert "150" in result
        assert "|" in result

    def test_empty_df(self):
        df = pl.DataFrame()
        result = df_to_markdown(df)
        assert result == "(데이터 없음)"

    def test_none_df(self):
        result = df_to_markdown(None)
        assert result == "(데이터 없음)"

    def test_truncation(self):
        df = pl.DataFrame({"year": list(range(2000, 2050)), "v": list(range(50))})
        result = df_to_markdown(df, max_rows=5)
        assert "상위 5행 표시" in result
        assert "전체 50행" in result

    def test_with_meta(self):
        df = pl.DataFrame({"year": [2023], "auditor": ["삼일"]})
        entry = DataEntry(
            name="test",
            label="감사의견",
            category="report",
            dataType="dataframe",
            description="감사의견 시계열",
            unit="",
            columns=(
                ColumnMeta("year", "사업연도"),
                ColumnMeta("auditor", "감사인명"),
            ),
        )
        meta = ModuleMeta(entry)
        result = df_to_markdown(df, meta=meta)
        assert "사업연도" in result
        assert "감사인명" in result

    def test_none_values(self):
        df = pl.DataFrame(
            {
                "year": [2023],
                "value": [None],
            },
            schema={"year": pl.Int64, "value": pl.Float64},
        )
        result = df_to_markdown(df)
        assert "| - |" in result

    def test_year_sorted_desc(self):
        """year 컬럼이 있으면 최신순 정렬."""
        df = pl.DataFrame({"year": [2020, 2023, 2021], "v": [1, 3, 2]})
        result = df_to_markdown(df)
        lines = [l for l in result.split("\n") if l.startswith("|") and "---" not in l]
        # 헤더 다음 첫 데이터 행이 2023이어야
        data_lines = lines[1:]  # 헤더 제외
        assert "2023" in data_lines[0]

    def test_float_formatting(self):
        """큰 float은 콤마, 작은 float은 소수점 4자리."""
        df = pl.DataFrame({"x": [1234567.0, 0.001234]})
        result = df_to_markdown(df)
        assert "1,234,567" in result
        assert "0.0012" in result


# ══════════════════════════════════════
# 파생 지표 자동계산
# ══════════════════════════════════════


class TestComputeDerivedMetrics:
    def test_is_yoy(self):
        """IS 매출액 YoY% 계산."""
        df = pl.DataFrame(
            {
                "계정명": ["매출액", "영업이익", "당기순이익"],
                "2023": [20000, 3000, 2000],
                "2022": [18000, 2500, 1800],
            }
        )
        result = _compute_derived_metrics("IS", df)
        assert result is not None
        assert "매출 성장률" in result
        assert "영업이익률" in result

    def test_bs_ratios(self):
        """BS 부채비율/유동비율 계산."""
        df = pl.DataFrame(
            {
                "계정명": ["부채총계", "자본총계", "유동자산", "유동부채", "자산총계"],
                "2023": [5000, 10000, 8000, 4000, 15000],
                "2022": [4000, 9000, 7000, 3500, 13000],
            }
        )
        result = _compute_derived_metrics("BS", df)
        assert result is not None
        assert "부채비율" in result
        assert "유동비율" in result

    def test_cf(self):
        """CF 영업활동CF 변동 계산."""
        df = pl.DataFrame(
            {
                "계정명": ["영업활동으로인한현금흐름"],
                "2023": [5000],
                "2022": [3000],
            }
        )
        result = _compute_derived_metrics("CF", df)
        assert result is not None
        assert "영업활동CF" in result

    def test_unknown_module(self):
        """BS/IS/CF가 아닌 모듈은 None."""
        df = pl.DataFrame({"계정명": ["항목"], "2023": [100]})
        result = _compute_derived_metrics("dividend", df)
        assert result is None

    def test_missing_accounts(self):
        """계정이 없으면 graceful하게 None 또는 부분 결과."""
        df = pl.DataFrame(
            {
                "계정명": ["기타항목"],
                "2023": [100],
                "2022": [90],
            }
        )
        result = _compute_derived_metrics("IS", df)
        # 매출액이 없으므로 결과 없음
        assert result is None

    def test_single_year(self):
        """연도 1개뿐이면 None."""
        df = pl.DataFrame(
            {
                "계정명": ["매출액"],
                "2023": [20000],
            }
        )
        result = _compute_derived_metrics("IS", df)
        assert result is None


class TestBuildRatiosSection:
    def test_financial_thresholds_are_relaxed(self):
        class DummyRatios:
            roe = 8.3
            roa = 0.6
            operatingMargin = None
            netMargin = None
            grossMargin = None
            ebitdaMargin = None
            roic = None
            debtRatio = None
            currentRatio = None
            quickRatio = None
            equityRatio = 8.1
            interestCoverage = None
            debtToEbitda = None
            netDebt = None
            netDebtRatio = None
            fcf = None
            operatingCfToNetIncome = None
            capexRatio = None
            dividendPayoutRatio = None
            revenueGrowth = None
            operatingProfitGrowth = None
            netProfitGrowth = None
            revenueGrowth3Y = None
            assetGrowth = None
            totalAssetTurnover = None
            inventoryTurnover = None
            receivablesTurnover = None
            revenueTTM = None
            operatingIncomeTTM = None
            netIncomeTTM = None
            dupontMargin = None
            dupontTurnover = None
            dupontLeverage = None
            piotroskiFScore = None
            altmanZScore = None
            ccc = None
            dso = None
            dio = None
            dpo = None
            warnings = []

        class DummyCompany:
            ratios = DummyRatios()
            sector = SectorInfo(Sector.FINANCIALS, IndustryGroup.BANK, 1.0, "test")

        result = _build_ratios_section(DummyCompany())
        assert result is not None
        assert "| ROE | 8.3% | 양호 |" in result
        assert "| ROA | 0.6% | 양호 |" in result


# ══════════════════════════════════════
# 토픽 매핑
# ══════════════════════════════════════


class TestResolveModules:
    def test_keyword_matching(self):
        """'배당' 질문 시 dividend 포함."""
        result = _resolve_tables("배당 정책을 분석해줘", None, None)
        assert "dividend" in result

    def test_default_modules(self):
        """키워드 매칭 없으면 BS, IS, CF 기본 포함."""
        result = _resolve_tables("xyz 분석해줘", None, None)
        assert "BS" in result
        assert "IS" in result
        assert "CF" in result

    def test_explicit_include(self):
        """include 지정 시 해당 모듈만 포함."""
        result = _resolve_tables("뭐든", ["audit", "dividend"], None)
        assert "audit" in result
        assert "dividend" in result

    def test_exclude(self):
        """exclude 지정 시 제외."""
        result = _resolve_tables("배당 분석", None, ["dividend"])
        assert "dividend" not in result

    def test_base_always_included(self):
        """fsSummary는 항상 포함."""
        result = _resolve_tables("아무 질문", None, None)
        assert "fsSummary" in result

    def test_multiple_keywords(self):
        """여러 키워드가 매칭되면 모두 포함."""
        result = _resolve_tables("배당과 감사의견을 분석해줘", None, None)
        assert "dividend" in result
        assert "audit" in result


class TestScanAvailableModules:
    def test_skips_broken_attribute_and_keeps_valid_module(self):
        class DummyCompany:
            BS = pl.DataFrame({"계정명": ["자산총계"], "2023": [100]})

            @property
            def IS(self):
                raise ValueError("broken module")

        result = scan_available_modules(DummyCompany())
        names = {item["name"] for item in result}

        assert "BS" in names
        assert "IS" not in names
