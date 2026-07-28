"""분기 계절성 코어 세 함수 단위 가드 (순수 계산, 데이터 불요)."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit

from dartlab.analysis.forecast.scenarioSim import (
    computeSeasonality,
    quarterlyValues,
    seasonalSharesFromYearQuarters,
)


class TestSeasonalSharesFromYearQuarters:
    def test_single_year_shares_sum_to_one(self):
        out = seasonalSharesFromYearQuarters({"2024": [1.0, 2.0, 3.0, 4.0]})
        assert out == pytest.approx([0.1, 0.2, 0.3, 0.4])
        assert sum(out) == pytest.approx(1.0)

    def test_partial_year_is_dropped(self):
        """분기 넷이 안 차는 연도는 표본에서 뺀다. 부분 연도가 비중을 왜곡한다."""
        out = seasonalSharesFromYearQuarters({"2024": [1.0, 1.0, 1.0], "2025": [1.0, 2.0, 3.0, 4.0]})
        assert out == pytest.approx([0.1, 0.2, 0.3, 0.4])

    def test_negative_quarter_uses_absolute_share(self):
        """적자 분기도 비중 표본이다. 절대값으로 센다."""
        out = seasonalSharesFromYearQuarters({"2024": [-1.0, 1.0, 1.0, 1.0]})
        assert out == pytest.approx([0.25] * 4)

    def test_no_sample_falls_back_to_even(self):
        assert seasonalSharesFromYearQuarters({}) == [0.25, 0.25, 0.25, 0.25]
        assert seasonalSharesFromYearQuarters({"2024": [0.0, 0.0, 0.0, 0.0]}) == [0.25] * 4

    def test_two_years_are_averaged(self):
        out = seasonalSharesFromYearQuarters({"2023": [1.0, 1.0, 1.0, 1.0], "2024": [4.0, 2.0, 2.0, 2.0]})
        assert sum(out) == pytest.approx(1.0)
        assert out[0] > out[1]  # 2024 의 1 분기 쏠림이 평균에 남는다


def _isPanel() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "snakeId": ["sales", "operating_profit"],
            "2024Q1": [100.0, 10.0],
            "2024Q2": [200.0, 20.0],
            "2024Q3": [300.0, 30.0],
            "2024Q4": [400.0, 40.0],
        }
    )


class TestQuarterlyValues:
    def test_collects_published_quarters(self):
        out = quarterlyValues(_isPanel(), "sales", "2024")
        assert out == {"2024Q1": 100.0, "2024Q2": 200.0, "2024Q3": 300.0, "2024Q4": 400.0}

    def test_missing_row_is_empty(self):
        assert quarterlyValues(_isPanel(), "does_not_exist", "2024") == {}

    def test_none_frame_is_empty(self):
        assert quarterlyValues(None, "sales", "2024") == {}

    def test_unpublished_quarter_has_no_key(self):
        """미발표 분기는 키 자체가 없다. 0 으로 채우면 미발표와 0 을 못 가린다."""
        out = quarterlyValues(_isPanel(), "sales", "2023")
        assert out == {}


class TestComputeSeasonality:
    def test_full_year_gives_quarter_weights(self):
        out = computeSeasonality(_isPanel(), "sales", ["2024"])
        assert out == pytest.approx([0.1, 0.2, 0.3, 0.4])

    def test_no_sample_falls_back_to_even(self):
        assert computeSeasonality(None, "sales", ["2024"]) == [0.25, 0.25, 0.25, 0.25]
        assert computeSeasonality(_isPanel(), "sales", ["2019"]) == [0.25] * 4
