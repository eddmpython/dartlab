"""자본잠식 기업의 비율 계약 회귀.

분모가 음수면 백분율의 부호가 뒤집힌다. 순손실 100 억에 자본 마이너스 50 억인 회사가
ROE +200% 로 읽혔고, 수익성 랭킹에서 맨 위로 올라갔다. 값이 이상해서 걸러지지도 않는다.
-500 에서 500 사이라는 기존 범위 검사를 +200 은 그대로 통과한다.

같은 저장소가 다른 곳에서는 이미 분모 양수를 요구하고 있었다. scan 빌더의 ROE 와
부채비율, `roce`, `noncurrentRatio` 가 그렇다. L0 만 예외였다.
"""

from __future__ import annotations

import pytest

from dartlab.core.utils.calc import safePct, safePctPositive

pytestmark = pytest.mark.unit


def testNegativeDenominatorInvertsThePercentageSign() -> None:
    """왜 막아야 하는지부터 고정한다. 이 성질이 결함의 원인이다."""

    assert safePct(-10e9, -5e9) == 200.0


def testGuardedPercentRefusesANegativeDenominator() -> None:
    """자본잠식이면 값이 없다. 뒤집힌 숫자보다 없음이 정직하다."""

    assert safePctPositive(-10e9, -5e9) is None
    assert safePctPositive(1000e9, -100e9) is None


def testGuardedPercentKeepsNormalCasesUnchanged() -> None:
    """정상 기업의 값은 그대로여야 한다. 막느라 멀쩡한 값을 없애면 안 된다."""

    assert safePctPositive(10e9, 100e9) == 10.0
    assert safePctPositive(-10e9, 100e9) == -10.0


def testGuardedPercentTreatsZeroDenominatorAsUndefined() -> None:
    """분모가 0 이면 나눌 수 없다."""

    assert safePctPositive(10e9, 0) is None


@pytest.mark.parametrize("part", [None, 0])
def testGuardedPercentHandlesMissingNumerator(part: object) -> None:
    """분자가 없거나 0 인 경우의 동작이 분모 가드 때문에 바뀌면 안 된다."""

    assert safePctPositive(part, 100e9) == safePct(part, 100e9)


def _computeRatios(**fields: float | None):
    """비율 엔진의 수익성, 안정성 두 블록을 그대로 태운다."""

    from dartlab.core.ratios import RatioResult, _calcProfitability, _calcStability

    result = RatioResult(shortTermBorrowings=0, longTermBorrowings=0, bonds=0, **fields)
    _calcProfitability(result)
    _calcStability(result)
    return result


def testInsolventCompanyGetsNoProfitabilityOrLeverageRatio() -> None:
    """자본잠식 기업은 값이 없어야 한다. 헬퍼만 고치고 호출부가 옛것을 쓰면 소용없다."""

    result = _computeRatios(
        netIncomeTTM=-10e9,
        ownersEquity=-5e9,
        totalEquity=-5e9,
        totalAssets=200e9,
        totalLiabilities=1000e9,
        cash=0,
    )

    assert result.roe is None
    assert result.debtRatio is None
    assert result.netDebtRatio is None


def testHealthyCompanyKeepsItsRatios() -> None:
    """가드가 멀쩡한 기업의 값까지 없애면 안 된다."""

    result = _computeRatios(
        netIncomeTTM=10e9,
        ownersEquity=100e9,
        totalEquity=100e9,
        totalAssets=200e9,
        totalLiabilities=100e9,
        cash=10e9,
    )

    assert result.roe == 10.0
    assert result.debtRatio == 100.0
    assert result.equityRatio == 50.0


def testSeriesPathUsesTheSamePositiveDenominatorContract() -> None:
    """공개 ratio panel의 시계열 경로도 시점값과 같은 자본잠식 계약을 지킨다."""
    from dartlab.core.ratios import calcRatioSeries

    series = {
        "IS": {"net_profit": [-10.0]},
        "BS": {
            "total_assets": [100.0],
            "total_liabilities": [105.0],
            "total_stockholders_equity": [-5.0],
            "owners_of_parent_equity": [-5.0],
            "shortterm_borrowings": [0.0],
            "longterm_borrowings": [0.0],
            "debentures": [0.0],
            "cash_and_cash_equivalents": [0.0],
        },
        "CF": {},
    }

    result = calcRatioSeries(series, ["2024"], annual=True, yoyLag=1)

    assert result.roe == [None]
    assert result.debtRatio == [None]
    assert result.netDebtRatio == [None]
