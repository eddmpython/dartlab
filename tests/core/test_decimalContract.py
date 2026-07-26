"""L0 십진 변환과 근접 판정의 실패 계약 회귀.

`isClose` 의 존재 이유는 자산 = 부채 + 자본 검증이다. 그런데 두 피연산자를 모두
`default=0` 으로 변환하고 있어서 값이 없는 대차대조표가 검증을 통과했다. NaN 도, None 도,
숫자가 아닌 문자열도 전부 True 였다.

`toDecimal` 은 문서가 ValueError 를 약속하면서 잘못된 문자열에는 `decimal.InvalidOperation`
을 새어 보냈다. ValueError 만 잡던 호출자는 그것을 놓친다.

두 계약을 값으로 못 박는다.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from dartlab.core.decimal import isClose, toDecimal


def testCloseComparisonStillWorksForRealNumbers() -> None:
    """정상 입력의 동작은 그대로다. 부동소수 오차를 흡수하는 것이 본래 목적이다."""

    assert isClose(0.1 + 0.2, 0.3) is True
    assert isClose("1000.00", "1000.01", absTol="0.05") is True
    assert isClose("1000.00", "1000.01", absTol="0.001") is False


@pytest.mark.parametrize("missing", [float("nan"), None, "abc", float("inf")])
def testCloseComparisonRefusesUnusableOperands(missing: object) -> None:
    """쓸 수 없는 값은 통과가 아니라 실패다.

    여기서 True 가 나오면 값이 빠진 재무제표가 항등식 검증을 통과한다. 검증기가
    검증하지 못했다는 사실 자체를 삼키는 것이 가장 나쁜 결과다.
    """

    with pytest.raises(ValueError):
        isClose(missing, 0.0)

    with pytest.raises(ValueError):
        isClose(0.0, missing)


def testConversionFailureIsAlwaysValueError() -> None:
    """문서가 약속한 예외 종류를 지킨다. 다른 예외가 새면 호출자가 못 잡는다."""

    with pytest.raises(ValueError):
        toDecimal("abc")

    with pytest.raises(ValueError):
        toDecimal(object())


@pytest.mark.parametrize("bad", [None, float("nan"), float("inf"), float("-inf"), "abc"])
def testDefaultStillAbsorbsBadInputWhenTheCallerAsksForIt(bad: object) -> None:
    """default 를 준 호출자는 예외 대신 그 값을 받는다. 그 길은 그대로 둔다."""

    assert toDecimal(bad, default=Decimal("7")) == Decimal("7")


def testGoodValuesConvertWithoutLosingPrecision() -> None:
    """정상 변환은 float 오차를 문자열 경유로 흡수한다."""

    assert toDecimal(0.1) == Decimal("0.1")
    assert toDecimal("1234.56") == Decimal("1234.56")
    assert toDecimal(42) == Decimal(42)
