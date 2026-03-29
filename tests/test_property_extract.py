"""Property-based tests for core/finance/extract.py.

Hypothesis로 무작위 시계열 입력에 대한 불변조건 검증.
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from dartlab.core.finance.extract import getLatest, getTTM, getAnnualValues, getRevenueGrowth3Y

pytestmark = pytest.mark.unit


# ── 전략 정의 ──

_float_or_none = st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False, min_value=-1e15, max_value=1e15))

_value_list = st.lists(_float_or_none, min_size=0, max_size=20)


def _makeSeries(sjDiv: str, snakeId: str, vals: list):
    """헬퍼: extract 함수가 기대하는 시계열 dict 구조."""
    return {sjDiv: {snakeId: vals}}


# ── getTTM 불변조건 ──


class TestGetTTMProperties:
    """getTTM의 property-based 불변조건."""

    @given(vals=_value_list)
    @settings(max_examples=200)
    def test_returnTypeIsFloatOrNone(self, vals):
        """반환값은 항상 float 또는 None."""
        result = getTTM(_makeSeries("IS", "sales", vals), "IS", "sales")
        assert result is None or isinstance(result, (int, float))

    @given(vals=_value_list)
    @settings(max_examples=200)
    def test_emptySeriesReturnsNone(self, vals):
        """빈 시계열 또는 존재하지 않는 키는 None."""
        assert getTTM({}, "IS", "sales") is None
        assert getTTM({"IS": {}}, "IS", "sales") is None
        assert getTTM({"IS": {"sales": []}}, "IS", "sales") is None

    @given(vals=st.lists(st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False), min_size=4, max_size=20))
    @settings(max_examples=200)
    def test_allPositiveFourOrMoreGivesResult(self, vals):
        """4개 이상의 양수값이면 반드시 결과를 반환."""
        result = getTTM(_makeSeries("IS", "sales", vals), "IS", "sales")
        assert result is not None
        assert result >= 0

    @given(vals=st.lists(st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False), min_size=4, max_size=4))
    @settings(max_examples=100)
    def test_exactFourValuesSumsAll(self, vals):
        """정확히 4개 값이면 합계와 동일."""
        result = getTTM(_makeSeries("IS", "sales", vals), "IS", "sales")
        assert result is not None
        assert abs(result - sum(vals)) < 1e-6

    @given(vals=_value_list)
    @settings(max_examples=200)
    def test_noCrashOnAnyInput(self, vals):
        """어떤 입력이든 크래시 없이 처리."""
        # strict=True
        getTTM(_makeSeries("IS", "sales", vals), "IS", "sales", strict=True)
        # strict=False
        getTTM(_makeSeries("IS", "sales", vals), "IS", "sales", strict=False)
        # annualize=True
        getTTM(_makeSeries("IS", "sales", vals), "IS", "sales", annualize=True)
        # maxTrailingNones=0
        getTTM(_makeSeries("IS", "sales", vals), "IS", "sales", maxTrailingNones=0)


# ── getLatest 불변조건 ──


class TestGetLatestProperties:
    """getLatest의 property-based 불변조건."""

    @given(vals=_value_list)
    @settings(max_examples=200)
    def test_returnTypeIsFloatOrNone(self, vals):
        """반환값은 항상 float 또는 None."""
        result = getLatest(_makeSeries("BS", "totalAssets", vals), "BS", "totalAssets")
        assert result is None or isinstance(result, (int, float))

    @given(vals=st.lists(st.floats(min_value=-1e15, max_value=1e15, allow_nan=False, allow_infinity=False), min_size=1, max_size=20))
    @settings(max_examples=200)
    def test_nonEmptyListAlwaysReturnsValue(self, vals):
        """non-null 값이 하나라도 있으면 반드시 결과 반환."""
        result = getLatest(_makeSeries("BS", "totalAssets", vals), "BS", "totalAssets")
        assert result is not None

    @given(vals=st.lists(st.floats(min_value=-1e15, max_value=1e15, allow_nan=False, allow_infinity=False), min_size=1, max_size=20))
    @settings(max_examples=200)
    def test_resultIsFromInputValues(self, vals):
        """반환값은 입력 리스트에 존재하는 값."""
        result = getLatest(_makeSeries("BS", "totalAssets", vals), "BS", "totalAssets")
        assert result in vals

    @given(n=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50)
    def test_allNoneReturnsNone(self, n):
        """모든 값이 None이면 None 반환."""
        vals = [None] * n
        result = getLatest(_makeSeries("BS", "totalAssets", vals), "BS", "totalAssets")
        assert result is None


# ── getAnnualValues 불변조건 ──


class TestGetAnnualValuesProperties:
    """getAnnualValues의 property-based 불변조건."""

    @given(vals=_value_list)
    @settings(max_examples=200)
    def test_returnsExactInputList(self, vals):
        """입력 리스트를 그대로 반환."""
        result = getAnnualValues(_makeSeries("IS", "sales", vals), "IS", "sales")
        assert result == vals

    def test_missingKeyReturnsEmptyList(self):
        """존재하지 않는 키는 빈 리스트."""
        assert getAnnualValues({}, "IS", "sales") == []
        assert getAnnualValues({"IS": {}}, "IS", "sales") == []


# ── getRevenueGrowth3Y 불변조건 ──


class TestRevenueGrowth3YProperties:
    """getRevenueGrowth3Y의 property-based 불변조건."""

    @given(vals=st.lists(st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False), min_size=4, max_size=20))
    @settings(max_examples=200)
    def test_allPositiveGivesFiniteResult(self, vals):
        """4개 이상의 양수값이면 유한한 결과."""
        result = getRevenueGrowth3Y({"IS": {"sales": vals}})
        assert result is None or (isinstance(result, float) and not (result != result))  # not NaN

    @given(vals=st.lists(_float_or_none, min_size=0, max_size=3))
    @settings(max_examples=100)
    def test_tooFewValuesReturnsNone(self, vals):
        """3개 이하 값은 None."""
        result = getRevenueGrowth3Y({"IS": {"sales": vals}})
        assert result is None

    @given(vals=_value_list)
    @settings(max_examples=200)
    def test_noCrashOnAnyInput(self, vals):
        """어떤 입력이든 크래시 없이 처리."""
        getRevenueGrowth3Y({"IS": {"sales": vals}})
