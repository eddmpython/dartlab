"""core 유틸 함수 단위 테스트 — _helpers, SelectResult."""

import pytest

pytestmark = pytest.mark.unit

import polars as pl

from dartlab.analysis.financial._helpers import (
    annualColsFromPeriods,
    annualLabel,
    annualLabels,
    mergeRows,
    parseNumStr,
    quarterlyColsFromPeriods,
    toDict,
)
from dartlab.core.select import SelectResult

# ══════════════════════════════════════
# parseNumStr
# ══════════════════════════════════════


class TestParseNumStr:
    def test_plain_integer(self):
        assert parseNumStr("1234") == 1234.0

    def test_comma_separated(self):
        assert parseNumStr("1,234,567") == 1234567.0

    def test_float(self):
        assert parseNumStr("3.14") == 3.14

    def test_percentage(self):
        assert parseNumStr("12.5%") == 12.5

    def test_triangle_negative(self):
        """△ 기호는 마이너스를 의미한다."""
        assert parseNumStr("△500") == -500.0

    def test_filled_triangle_negative(self):
        """▲ 기호도 마이너스 처리."""
        assert parseNumStr("▲1,000") == -1000.0

    def test_none_input(self):
        assert parseNumStr(None) is None

    def test_empty_string(self):
        assert parseNumStr("") is None

    def test_dash(self):
        assert parseNumStr("-") is None

    def test_whitespace_only(self):
        assert parseNumStr("   ") is None

    def test_non_numeric(self):
        assert parseNumStr("abc") is None


# ══════════════════════════════════════
# annualColsFromPeriods
# ══════════════════════════════════════


class TestAnnualColsFromPeriods:
    def test_pure_annual(self):
        periods = ["2020", "2021", "2022", "2023", "2024"]
        result = annualColsFromPeriods(periods)
        assert result == ["2024", "2023", "2022", "2021", "2020"]

    def test_q4_fallback(self):
        """연도 컬럼이 없으면 Q4를 사용한다."""
        periods = ["2022Q1", "2022Q2", "2022Q3", "2022Q4", "2023Q1", "2023Q4"]
        result = annualColsFromPeriods(periods)
        assert result == ["2023Q4", "2022Q4"]

    def test_annual_preferred_over_q4(self):
        """연도 컬럼이 있으면 Q4보다 우선."""
        periods = ["2022", "2023", "2023Q4", "2024"]
        result = annualColsFromPeriods(periods)
        assert "2023Q4" not in result
        assert result == ["2024", "2023", "2022"]

    def test_basePeriod_filter_year(self):
        periods = ["2020", "2021", "2022", "2023", "2024"]
        result = annualColsFromPeriods(periods, basePeriod="2022")
        assert result == ["2022", "2021", "2020"]

    def test_basePeriod_filter_q4(self):
        """basePeriod="2022Q4"이면 "2022" 연도컬럼은 Q5로 변환되어 제외된다."""
        periods = ["2020", "2021", "2022", "2023", "2024"]
        result = annualColsFromPeriods(periods, basePeriod="2022Q4")
        # "2022" -> sortKey "2022Q5" > "2022Q4" -> 제외됨
        assert result == ["2021", "2020"]

    def test_maxYears_limit(self):
        periods = [str(y) for y in range(2015, 2025)]
        result = annualColsFromPeriods(periods, maxYears=3)
        assert len(result) == 3
        assert result[0] == "2024"

    def test_empty_periods(self):
        assert annualColsFromPeriods([]) == []

    def test_only_non_q4_quarters(self):
        """Q4가 아닌 분기만 있으면 빈 리스트."""
        periods = ["2023Q1", "2023Q2", "2023Q3"]
        assert annualColsFromPeriods(periods) == []


# ══════════════════════════════════════
# quarterlyColsFromPeriods
# ══════════════════════════════════════


class TestQuarterlyColsFromPeriods:
    def test_basic(self):
        periods = ["2023", "2023Q1", "2023Q2", "2023Q3", "2023Q4"]
        result = quarterlyColsFromPeriods(periods)
        assert result == ["2023Q4", "2023Q3", "2023Q2", "2023Q1"]

    def test_basePeriod_filter(self):
        periods = ["2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1"]
        result = quarterlyColsFromPeriods(periods, basePeriod="2023Q3")
        assert "2023Q4" not in result
        assert "2024Q1" not in result

    def test_maxQuarters(self):
        periods = [f"2023Q{i}" for i in range(1, 5)] + [f"2024Q{i}" for i in range(1, 5)]
        result = quarterlyColsFromPeriods(periods, maxQuarters=3)
        assert len(result) == 3


# ══════════════════════════════════════
# annualLabel / annualLabels
# ══════════════════════════════════════


class TestAnnualLabel:
    def test_q4_strip(self):
        assert annualLabel("2025Q4") == "2025"

    def test_year_passthrough(self):
        assert annualLabel("2025") == "2025"

    def test_non_q4_kept(self):
        assert annualLabel("2025Q3") == "2025Q3"

    def test_labels_dict(self):
        result = annualLabels(["2023", "2024Q4"])
        assert result == {"2023": "2023", "2024Q4": "2024"}


# ══════════════════════════════════════
# mergeRows
# ══════════════════════════════════════


class TestMergeRows:
    def test_both_none(self):
        assert mergeRows(None, None) == {}

    def test_primary_none(self):
        assert mergeRows(None, {"a": 1}) == {"a": 1}

    def test_fallback_none(self):
        assert mergeRows({"a": 1}, None) == {"a": 1}

    def test_primary_wins(self):
        result = mergeRows({"a": 10, "b": 20}, {"a": 99, "b": 88})
        assert result == {"a": 10, "b": 20}

    def test_fallback_fills_none(self):
        """primary의 None 값을 fallback으로 채운다."""
        result = mergeRows({"a": 10, "b": None}, {"a": 99, "b": 88, "c": 77})
        assert result["a"] == 10
        assert result["b"] == 88
        assert result["c"] == 77

    def test_fallback_does_not_overwrite(self):
        result = mergeRows({"x": 0}, {"x": 100})
        assert result["x"] == 0


# ══════════════════════════════════════
# toDict
# ══════════════════════════════════════


class TestToDict:
    def _make_select_result(self, df: pl.DataFrame) -> SelectResult:
        return SelectResult(df=df, topic="IS")

    def test_basic_conversion(self):
        df = pl.DataFrame(
            {
                "계정명": ["매출액", "영업이익"],
                "2023": [100, 20],
                "2024": [120, 25],
            }
        )
        sr = self._make_select_result(df)
        result = toDict(sr)
        assert result is not None
        data, periods = result
        assert "매출액" in data
        assert data["매출액"]["2024"] == 120
        assert periods == ["2024", "2023"]

    def test_none_input(self):
        assert toDict(None) is None

    def test_no_period_cols(self):
        df = pl.DataFrame({"계정명": ["a"], "note": ["x"]})
        sr = self._make_select_result(df)
        assert toDict(sr) is None

    def test_max_periods(self):
        df = pl.DataFrame(
            {
                "계정명": ["매출액"],
                "2020": [80],
                "2021": [90],
                "2022": [100],
                "2023": [110],
                "2024": [120],
            }
        )
        sr = self._make_select_result(df)
        result = toDict(sr, maxPeriods=2)
        assert result is not None
        data, periods = result
        assert len(periods) == 2
        assert periods[0] == "2024"


# ══════════════════════════════════════
# SelectResult basics
# ══════════════════════════════════════


class TestSelectResult:
    def test_properties(self):
        df = pl.DataFrame({"계정명": ["a"], "2024": [1]})
        sr = SelectResult(df=df, topic="BS", meta={"currency": "KRW"})
        assert sr.topic == "BS"
        assert sr.meta["currency"] == "KRW"
        assert sr.df is df

    def test_len(self):
        df = pl.DataFrame({"계정명": ["a", "b"], "2024": [1, 2]})
        sr = SelectResult(df=df, topic="IS")
        assert len(sr) == 2

    def test_is_numeric(self):
        df = pl.DataFrame({"계정명": ["a"], "2024": [100]})
        sr = SelectResult(df=df, topic="IS")
        assert sr.isNumeric is True

    def test_is_not_numeric(self):
        df = pl.DataFrame({"계정명": ["a"], "2024": ["text"]})
        sr = SelectResult(df=df, topic="IS")
        assert sr.isNumeric is False

    def test_default_meta(self):
        df = pl.DataFrame({"x": [1]})
        sr = SelectResult(df=df, topic="T")
        assert sr.meta == {}
