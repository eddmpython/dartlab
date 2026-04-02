"""tools/ + viz 패키지 테스트 — table, text, viz 모듈."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit

from dartlab.tools import table, text
from dartlab import viz

# ── table ──


def test_yoy_change():
    df = pl.DataFrame({"year": [2022, 2023, 2024], "dps": [1000, 1200, 1500]})
    result = table.yoy_change(df, value_cols=["dps"])

    assert "dps_YoY" in result.columns
    assert result["dps_YoY"][1] == pytest.approx(20.0, abs=0.1)
    assert result["dps_YoY"][2] == pytest.approx(25.0, abs=0.1)


def test_yoy_change_absolute():
    df = pl.DataFrame({"year": [2022, 2023], "value": [100, 150]})
    result = table.yoy_change(df, value_cols=["value"], pct=False)

    assert result["value_YoY"][1] == pytest.approx(50.0, abs=1)


def test_summary_stats():
    df = pl.DataFrame({"year": [2022, 2023, 2024], "dps": [1000, 1200, 1500]})
    result = table.summary_stats(df, value_cols=["dps"])

    assert result.height == 1
    assert result["metric"][0] == "dps"
    assert result["trend"][0] == "상승"
    assert result["cagr"][0] is not None


def test_growth_matrix():
    df = pl.DataFrame({"year": [2020, 2021, 2022, 2023, 2024], "rev": [100, 110, 121, 133, 146]})
    result = table.growth_matrix(df, value_cols=["rev"])

    assert result.height == 1
    assert "1Y" in result.columns
    assert "2Y" in result.columns


def test_format_korean():
    df = pl.DataFrame({"year": [2024], "amount": [150000000]})
    result = table.format_korean(df, unit="원", cols=["amount"])

    assert "억원" in result["amount"][0]


def test_pivot_accounts():
    df = pl.DataFrame({"계정명": ["매출액", "영업이익"], "2023": [1000, 200], "2024": [1200, 250]})
    result = table.pivot_accounts(df)

    assert "year" in result.columns
    assert "매출액" in result.columns
    assert result.height == 2


def test_yoy_missing_year_col():
    df = pl.DataFrame({"value": [1, 2, 3]})
    result = table.yoy_change(df)

    assert result.shape == df.shape  # 변경 없이 반환


# ── text ──


def test_extract_keywords():
    sample = "매출액이 증가하였고 영업이익도 개선되었습니다"
    kw = text.extract_keywords(sample, top_n=5)

    assert len(kw) > 0
    assert all(isinstance(k, tuple) and len(k) == 2 for k in kw)


def test_sentiment_indicators():
    sample = "매출 증가, 이익 성장, 부채 감소"
    result = text.sentiment_indicators(sample)

    assert result["positive_count"] > 0
    assert "증가" in result["positive_keywords"]
    assert isinstance(result["score"], float)


def test_sentiment_empty():
    result = text.sentiment_indicators("")

    assert result["score"] == 0.0
    assert result["positive_count"] == 0


def test_extract_numbers():
    sample = "매출액 1,500억원, 영업이익률 15.3%"
    nums = text.extract_numbers(sample)

    assert len(nums) >= 2
    assert any(n["unit"] == "억원" for n in nums)
    assert any(n["unit"] == "%" for n in nums)


def test_extract_numbers_empty():
    assert text.extract_numbers("") == []


def test_section_diff():
    class Sec:
        def __init__(self, key, txt):
            self.key = key
            self.text = txt

    a = [Sec("개요", "회사는 반도체를 생산합니다."), Sec("위험", "소송 위험이 있습니다.")]
    b = [Sec("개요", "회사는 반도체를 생산합니다."), Sec("신규", "AI 사업을 추진합니다.")]
    result = text.section_diff(a, b)

    assert "위험" in result["removed"]
    assert "신규" in result["added"]
    assert "개요" in result["unchanged"]


# ── viz (spec 생성, plotly 불필요) ──


def test_viz_spec_generators_registered():
    assert "revenue_trend" in viz.SPEC_GENERATORS
    assert "insight_radar" in viz.SPEC_GENERATORS
    assert len(viz.SPEC_GENERATORS) == 8


def test_auto_chart_callable():
    assert callable(viz.auto_chart)
    assert callable(viz.chart_from_spec)


def test_safe_val():
    from dartlab.viz.generators import _safe_val

    assert _safe_val(None) == 0.0
    assert _safe_val(42) == 42.0
    assert _safe_val("abc") == 0.0


def test_hex_to_rgba():
    from dartlab.viz.plotly import _hex_to_rgba

    assert "rgba" in _hex_to_rgba("#ea4647", 0.3)
    assert "234" in _hex_to_rgba("#ea4647", 0.3)
