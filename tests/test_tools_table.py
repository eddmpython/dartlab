"""tools.table 모듈 테스트 — 데이터 의존 없음."""

import pytest

pytestmark = pytest.mark.unit

import polars as pl

from dartlab.tools.table import (
    format_korean,
    growth_matrix,
    pivot_accounts,
    ratio_table,
    summary_stats,
    yoy_change,
)

# ══════════════════════════════════════
# YoY 변동
# ══════════════════════════════════════


class TestYoyChange:
    def test_pct_change(self):
        df = pl.DataFrame({"year": [2021, 2022, 2023], "revenue": [100, 120, 150]})
        result = yoy_change(df, value_cols=["revenue"])
        yoy = result["revenue_YoY"].to_list()
        assert yoy[0] is None
        assert yoy[1] == 20.0
        assert yoy[2] == 25.0

    def test_absolute_change(self):
        df = pl.DataFrame({"year": [2021, 2022, 2023], "revenue": [100, 120, 150]})
        result = yoy_change(df, value_cols=["revenue"], pct=False)
        yoy = result["revenue_YoY"].to_list()
        assert yoy[0] is None
        assert yoy[1] == 20
        assert yoy[2] == 30

    def test_auto_detect_cols(self):
        df = pl.DataFrame(
            {
                "year": [2021, 2022],
                "revenue": [100, 120],
                "name": ["A", "B"],
            }
        )
        result = yoy_change(df)
        assert "revenue_YoY" in result.columns
        assert "name_YoY" not in result.columns

    def test_missing_year_col(self):
        df = pl.DataFrame({"x": [1, 2], "y": [10, 20]})
        result = yoy_change(df)
        assert result.columns == df.columns

    def test_none_values(self):
        df = pl.DataFrame({"year": [2021, 2022, 2023], "v": [100, None, 150]})
        result = yoy_change(df, value_cols=["v"])
        yoy = result["v_YoY"].to_list()
        assert yoy[0] is None
        assert yoy[1] is None  # prev=100, cur=None


# ══════════════════════════════════════
# 재무비율
# ══════════════════════════════════════


class TestRatioTable:
    def test_basic_ratios(self):
        bs = pl.DataFrame(
            {
                "계정명": ["부채총계", "자본총계", "자산총계", "유동자산", "유동부채"],
                "2023": [5000, 10000, 15000, 8000, 4000],
                "2022": [4000, 9000, 13000, 7000, 3500],
            }
        )
        is_ = pl.DataFrame(
            {
                "계정명": ["매출액", "영업이익", "당기순이익"],
                "2023": [20000, 3000, 2000],
                "2022": [18000, 2500, 1800],
            }
        )
        result = ratio_table(bs, is_)
        assert result.height == 2

        r2023 = result.filter(pl.col("year") == 2023).row(0, named=True)
        assert r2023["부채비율"] == 50.0  # 5000/10000*100
        assert r2023["유동비율"] == 200.0  # 8000/4000*100
        assert r2023["영업이익률"] == 15.0  # 3000/20000*100
        assert r2023["ROE"] == 20.0  # 2000/10000*100

    def test_no_year_cols(self):
        bs = pl.DataFrame({"계정명": ["부채총계"], "value": [100]})
        is_ = pl.DataFrame({"계정명": ["매출액"], "value": [200]})
        result = ratio_table(bs, is_)
        assert result.height == 0

    def test_division_by_zero(self):
        bs = pl.DataFrame(
            {
                "계정명": ["부채총계", "자본총계"],
                "2023": [5000, 0],
            }
        )
        is_ = pl.DataFrame(
            {
                "계정명": ["매출액", "영업이익"],
                "2023": [0, 100],
            }
        )
        result = ratio_table(bs, is_)
        r = result.row(0, named=True)
        assert r["부채비율"] is None  # equity=0
        assert r["영업이익률"] is None  # rev=0


# ══════════════════════════════════════
# 요약 통계
# ══════════════════════════════════════


class TestSummaryStats:
    def test_basic(self):
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023],
                "revenue": [100, 120, 140, 160],
            }
        )
        result = summary_stats(df)
        assert result.height == 1
        r = result.row(0, named=True)
        assert r["metric"] == "revenue"
        assert r["min"] == 100.0
        assert r["max"] == 160.0
        assert r["cagr"] is not None

    def test_trend_ascending(self):
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023],
                "v": [100, 110, 120, 130],
            }
        )
        result = summary_stats(df)
        assert result.row(0, named=True)["trend"] == "상승"

    def test_trend_descending(self):
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023],
                "v": [130, 120, 110, 100],
            }
        )
        result = summary_stats(df)
        assert result.row(0, named=True)["trend"] == "하락"

    def test_trend_mixed(self):
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023],
                "v": [100, 130, 110, 120],
            }
        )
        result = summary_stats(df)
        assert result.row(0, named=True)["trend"] == "변동"

    def test_insufficient_data(self):
        df = pl.DataFrame({"year": [2023], "v": [100]})
        result = summary_stats(df)
        # 1개 데이터: cagr 불가, trend="-"
        if result.height > 0:
            r = result.row(0, named=True)
            assert r["trend"] == "-"


# ══════════════════════════════════════
# 피벗
# ══════════════════════════════════════


class TestPivotAccounts:
    def test_basic(self):
        df = pl.DataFrame(
            {
                "계정명": ["매출액", "영업이익"],
                "2023": [20000, 3000],
                "2022": [18000, 2500],
            }
        )
        result = pivot_accounts(df)
        assert "year" in result.columns
        assert "매출액" in result.columns
        assert "영업이익" in result.columns
        assert result.height == 2

    def test_no_account_col(self):
        df = pl.DataFrame({"x": [1, 2], "y": [10, 20]})
        result = pivot_accounts(df)
        assert result.columns == df.columns


# ══════════════════════════════════════
# 한국어 포맷
# ══════════════════════════════════════


class TestFormatKorean:
    def test_million_to_billion(self):
        df = pl.DataFrame({"year": [2023], "revenue": [1500]})
        result = format_korean(df, cols=["revenue"])
        val = result["revenue"].to_list()[0]
        assert "억원" in val

    def test_million_to_trillion(self):
        df = pl.DataFrame({"year": [2023], "revenue": [1_500_000]})
        result = format_korean(df, cols=["revenue"])
        val = result["revenue"].to_list()[0]
        assert "조원" in val

    def test_none_value(self):
        """Polars null은 map_elements에 전달되지 않으므로 null 유지."""
        df = pl.DataFrame({"year": [2023], "revenue": [None]}, schema={"year": pl.Int64, "revenue": pl.Float64})
        result = format_korean(df, cols=["revenue"])
        val = result["revenue"].to_list()[0]
        assert val is None


# ══════════════════════════════════════
# 성장률 매트릭스
# ══════════════════════════════════════


class TestGrowthMatrix:
    def test_basic(self):
        df = pl.DataFrame(
            {
                "year": [2019, 2020, 2021, 2022, 2023],
                "revenue": [100, 110, 121, 133, 146],
            }
        )
        result = growth_matrix(df)
        assert result.height == 1
        r = result.row(0, named=True)
        assert r["1Y"] is not None
        assert r["3Y"] is not None

    def test_insufficient_data(self):
        df = pl.DataFrame({"year": [2023], "revenue": [100]})
        result = growth_matrix(df)
        assert result.height == 0
