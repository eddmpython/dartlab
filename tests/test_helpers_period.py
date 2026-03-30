"""_helpers basePeriod 인프라 단위 테스트."""

import pytest

from dartlab.analysis.financial._helpers import (
    PeriodRange,
    annualColsFromPeriods,
    quarterlyColsFromPeriods,
)

pytestmark = pytest.mark.unit

# ── 테스트 데이터 ──

_PERIODS = [
    "2020Q1", "2020Q2", "2020Q3", "2020Q4",
    "2021Q1", "2021Q2", "2021Q3", "2021Q4",
    "2022Q1", "2022Q2", "2022Q3", "2022Q4",
    "2023Q1", "2023Q2", "2023Q3", "2023Q4",
    "2024Q1", "2024Q2", "2024Q3", "2024Q4",
    "2025Q1", "2025Q2",
]


# ── annualColsFromPeriods ──

_YEAR_PERIODS = ["2020", "2021", "2022", "2023", "2024"]


class TestAnnualColsFromPeriods:
    def test_q4_fallback_when_no_years(self):
        """연도 형식 없으면 Q4 fallback."""
        result = annualColsFromPeriods(_PERIODS, basePeriod=None, maxYears=5)
        assert result == ["2024Q4", "2023Q4", "2022Q4", "2021Q4", "2020Q4"]

    def test_year_format_preferred(self):
        """연도 형식이 있으면 우선 사용."""
        result = annualColsFromPeriods(_YEAR_PERIODS, basePeriod=None, maxYears=5)
        assert result == ["2024", "2023", "2022", "2021", "2020"]

    def test_basePeriod_filters_q4(self):
        result = annualColsFromPeriods(_PERIODS, basePeriod="2022Q4", maxYears=5)
        assert result == ["2022Q4", "2021Q4", "2020Q4"]

    def test_basePeriod_filters_years(self):
        result = annualColsFromPeriods(_YEAR_PERIODS, basePeriod="2022", maxYears=5)
        assert result == ["2022", "2021", "2020"]

    def test_basePeriod_year_on_q4_periods(self):
        """basePeriod="2022"이면 2022Q4 이하."""
        result = annualColsFromPeriods(_PERIODS, basePeriod="2022", maxYears=5)
        assert result == ["2022Q4", "2021Q4", "2020Q4"]

    def test_basePeriod_mid_year(self):
        """basePeriod="2023Q2"이면 2022Q4 이하 (Q2 < Q4)."""
        result = annualColsFromPeriods(_PERIODS, basePeriod="2023Q2", maxYears=5)
        assert result == ["2022Q4", "2021Q4", "2020Q4"]

    def test_maxYears_limits(self):
        result = annualColsFromPeriods(_PERIODS, basePeriod=None, maxYears=3)
        assert len(result) == 3

    def test_empty_periods(self):
        assert annualColsFromPeriods([], basePeriod=None) == []

    def test_no_q4(self):
        periods = ["2024Q1", "2024Q2", "2024Q3"]
        assert annualColsFromPeriods(periods, basePeriod=None) == []

    def test_default_max_is_8(self):
        """기본 maxYears=8."""
        periods = [f"{y}Q4" for y in range(2015, 2025)]
        result = annualColsFromPeriods(periods, basePeriod=None)
        assert len(result) == 8


# ── quarterlyColsFromPeriods ──

class TestQuarterlyColsFromPeriods:
    def test_no_basePeriod(self):
        result = quarterlyColsFromPeriods(_PERIODS, basePeriod=None, maxQuarters=8)
        assert result[0] == "2025Q2"
        assert len(result) == 8

    def test_basePeriod_filters(self):
        result = quarterlyColsFromPeriods(_PERIODS, basePeriod="2021Q4", maxQuarters=8)
        assert result[0] == "2021Q4"
        assert all(p <= "2021Q4" for p in result)

    def test_maxQuarters_limits(self):
        result = quarterlyColsFromPeriods(_PERIODS, basePeriod=None, maxQuarters=4)
        assert len(result) == 4

    def test_empty(self):
        assert quarterlyColsFromPeriods([], basePeriod=None) == []


# ── PeriodRange ──

class TestPeriodRange:
    def test_frozen(self):
        pr = PeriodRange(basePeriod="2024Q4", annualCols=["2024Q4"], quarterlyCols=["2024Q4"])
        with pytest.raises(AttributeError):
            pr.basePeriod = "2025Q1"
