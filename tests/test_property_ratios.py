"""Property-based tests for core/finance/ratios.py.

Hypothesis로 비율 계산의 불변조건 검증:
- 0으로 나누기 안전
- None 입력 처리
- 비율 범위 합리성
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from dartlab.core.finance.ratios import _safeDiv, _safePct

pytestmark = pytest.mark.unit


# ── _safeDiv 불변조건 ──

_fin_float = st.floats(min_value=-1e15, max_value=1e15, allow_nan=False, allow_infinity=False)
_fin_float_or_none = st.one_of(st.none(), _fin_float)


class TestSafeDivProperties:
    """_safeDiv의 property-based 불변조건."""

    @given(num=_fin_float_or_none, den=_fin_float_or_none)
    @settings(max_examples=500)
    def test_neverRaisesOnAnyInput(self, num, den):
        """어떤 입력이든 예외 없이 처리."""
        result = _safeDiv(num, den)
        assert result is None or isinstance(result, float)

    @given(num=_fin_float)
    @settings(max_examples=200)
    def test_zeroDenominatorReturnsNone(self, num):
        """분모가 0이면 항상 None."""
        assert _safeDiv(num, 0.0) is None

    @given(den=_fin_float_or_none)
    @settings(max_examples=200)
    def test_noneNumeratorReturnsNone(self, den):
        """분자가 None이면 항상 None."""
        assert _safeDiv(None, den) is None

    @given(num=_fin_float)
    @settings(max_examples=200)
    def test_noneDenominatorReturnsNone(self, num):
        """분모가 None이면 항상 None."""
        assert _safeDiv(num, None) is None

    @given(num=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
           den=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def test_positiveInputsGivePositiveResult(self, num, den):
        """양수/양수는 항상 양수 결과."""
        result = _safeDiv(num, den)
        assert result is not None
        assert result > 0


class TestSafePctProperties:
    """_safePct의 property-based 불변조건."""

    @given(num=_fin_float_or_none, den=_fin_float_or_none)
    @settings(max_examples=500)
    def test_neverRaisesOnAnyInput(self, num, den):
        """어떤 입력이든 예외 없이 처리."""
        result = _safePct(num, den)
        assert result is None or isinstance(result, float)

    @given(num=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
           den=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def test_resultIsRoundedHundredTimesDiv(self, num, den):
        """_safePct는 round(_safeDiv * 100, 2)."""
        divResult = _safeDiv(num, den)
        pctResult = _safePct(num, den)
        if divResult is not None and pctResult is not None:
            expected = round(divResult * 100, 2)
            assert abs(pctResult - expected) < 1e-9
