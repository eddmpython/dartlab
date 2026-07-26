"""L0 거래량, 자금흐름 지표 회귀.

`core/indicators/volume.py` 는 공개 함수 열하나가 전부 테스트 참조 0 이었다. L0 이라
quant 와 viz 가 그대로 얹혀 있고, 여기서 부호 하나가 뒤집히면 위층 신호가 통째로
반대가 된다.

전부 순수 함수라 기댓값을 손으로 계산해 못 박는다. 회귀 방향이 아니라 값 자체를 본다.
"""

from __future__ import annotations

import numpy as np
import pytest

from dartlab.core.indicators.volume import (
    vadl,
    vchaikin,
    velderRay,
    vemv,
    vforceIndex,
    vmfi,
    vnvi,
    vobv,
    vpvi,
    vpvt,
    vvwap,
)


def testObvAddsOnUpDaysSubtractsOnDownDaysAndHoldsFlat() -> None:
    """OBV 는 종가 방향으로 거래량을 누적한다. 보합은 직전 값을 유지한다."""

    close = np.array([10.0, 11.0, 11.0, 9.0, 12.0])
    volume = np.array([100.0, 200.0, 300.0, 400.0, 500.0])

    result = vobv(close, volume)

    assert result.tolist() == [0.0, 200.0, 200.0, -200.0, 300.0]


def testObvFirstElementIsAlwaysZero() -> None:
    """첫 봉은 비교 대상이 없어 0 이다. 여기가 흔들리면 전체가 상수만큼 밀린다."""

    result = vobv(np.array([10.0, 20.0]), np.array([7.0, 9.0]))

    assert result[0] == 0.0


def testMoneyFlowIndexIsHundredWhenThereIsNoNegativeFlow() -> None:
    """음의 자금흐름이 0 이면 100 이다. 0 나눗셈으로 새면 안 된다."""

    n = 20
    close = np.arange(1.0, n + 1.0)
    result = vmfi(close, close, close, np.full(n, 100.0), period=14)

    assert result[-1] == 100.0


def testMoneyFlowIndexLeavesTheWarmupWindowUndefined() -> None:
    """period 이전 구간은 계산할 수 없다. 0 으로 채우면 과매도로 오독된다."""

    n = 20
    close = np.arange(1.0, n + 1.0)
    result = vmfi(close, close, close, np.full(n, 100.0), period=14)

    assert np.isnan(result[:14]).all()
    assert not np.isnan(result[14:]).any()


def testMoneyFlowIndexStaysWithinItsBounds() -> None:
    """지수는 0 과 100 사이다. 벗어나면 위층 임계 판정이 무너진다."""

    rng = np.random.default_rng(20260727)
    n = 60
    close = np.cumsum(rng.normal(0, 1, n)) + 100
    high = close + 1
    low = close - 1
    volume = rng.uniform(100, 1000, n)

    result = vmfi(high, low, close, volume, period=14)
    defined = result[~np.isnan(result)]

    assert defined.size > 0
    assert (defined >= 0).all() and (defined <= 100).all()


def testElderRayMeasuresHighAndLowAgainstTheSameEma() -> None:
    """황소, 곰 힘은 같은 EMA 를 기준으로 잰다. 기준선이 어긋나면 둘의 비교가 무의미해진다.

    EMA 워밍업 구간은 값이 없어 둘 다 NaN 이다. 정의된 구간에서만 차가 고저 폭과 같다.
    """

    n = 30
    close = np.linspace(10.0, 40.0, n)
    high = close + 2.0
    low = close - 2.0

    bull, bear = velderRay(high, low, close, period=13)
    defined = ~np.isnan(bull)

    assert defined.any()
    assert np.isnan(bear[~defined]).all()
    assert np.allclose((bull - bear)[defined], (high - low)[defined])


def testForceIndexLeavesTheEmaWarmupUndefined() -> None:
    """EMA 로 평활하므로 워밍업 구간은 값이 없다. 0 으로 채우면 무압력으로 오독된다."""

    close = np.array([10.0, 12.0, 11.0, 13.0, 12.0, 14.0])
    volume = np.array([100.0, 200.0, 300.0, 400.0, 500.0, 600.0])

    result = vforceIndex(close, volume, period=3)

    assert np.isnan(result[0])
    assert not np.isnan(result[-1])


def testForceIndexIsPositiveWhenPriceRisesOnVolume() -> None:
    """가격이 오르며 거래가 실리면 force 는 양수다. 부호가 뒤집히면 신호가 반대가 된다."""

    close = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    volume = np.full(6, 100.0)

    result = vforceIndex(close, volume, period=3)

    assert result[-1] > 0


def testVwapEqualsTypicalPriceWhenVolumeIsFlat() -> None:
    """거래량이 균일하면 VWAP 은 대표가격의 누적 평균이다."""

    high = np.array([11.0, 13.0, 15.0])
    low = np.array([9.0, 11.0, 13.0])
    close = np.array([10.0, 12.0, 14.0])
    volume = np.array([100.0, 100.0, 100.0])

    result = vvwap(high, low, close, volume)

    assert np.allclose(result, [10.0, 11.0, 12.0])


def testVwapIsUndefinedWhileCumulativeVolumeIsZero() -> None:
    """누적 거래량이 0 인 구간은 값이 없다. 0 으로 채우면 가격이 0 원으로 읽힌다."""

    high = np.array([11.0, 13.0])
    low = np.array([9.0, 11.0])
    close = np.array([10.0, 12.0])
    volume = np.array([0.0, 100.0])

    result = vvwap(high, low, close, volume)

    assert np.isnan(result[0])
    assert result[1] == pytest.approx(12.0)


def testAccumulationDistributionUsesFullMultiplierAtTheExtremes() -> None:
    """종가가 고가면 승수 +1, 저가면 -1 이다. 부호가 뒤집히면 매집과 분산이 바뀐다."""

    high = np.array([10.0, 10.0])
    low = np.array([8.0, 8.0])
    close = np.array([10.0, 8.0])
    volume = np.array([100.0, 100.0])

    result = vadl(close, high, low, volume)

    assert result.tolist() == [100.0, 0.0]


def testAccumulationDistributionHoldsWhenTheBarHasNoRange() -> None:
    """고가와 저가가 같으면 승수를 정의할 수 없어 직전 값을 유지한다."""

    high = np.array([10.0, 10.0])
    low = np.array([8.0, 10.0])
    close = np.array([10.0, 10.0])
    volume = np.array([100.0, 999.0])

    result = vadl(close, high, low, volume)

    assert result[1] == result[0]


def testChaikinIsTheGapBetweenTwoEmasOfTheSameLine() -> None:
    """차이킨은 같은 ADL 의 두 EMA 차다. 두 기간이 같으면 0 이어야 한다."""

    rng = np.random.default_rng(7)
    n = 40
    close = np.cumsum(rng.normal(0, 1, n)) + 100
    high = close + 1
    low = close - 1
    volume = rng.uniform(100, 500, n)

    result = vchaikin(close, high, low, volume, fastPeriod=5, slowPeriod=5)
    defined = ~np.isnan(result)

    assert defined.any()
    assert np.allclose(result[defined], 0.0)


def testEaseOfMovementIsZeroWhenTheBarHasNoRange() -> None:
    """범위가 없는 봉은 이동 난이도를 정의할 수 없다."""

    high = np.array([10.0, 10.0, 10.0])
    low = np.array([10.0, 10.0, 10.0])
    volume = np.array([100.0, 100.0, 100.0])

    result = vemv(high, low, volume, period=2)
    defined = ~np.isnan(result)

    assert defined.any()
    assert np.allclose(result[defined], 0.0)


def testNegativeVolumeIndexMovesOnlyWhenVolumeShrinks() -> None:
    """NVI 는 거래량이 줄어든 날만 반영한다. 늘어난 날 움직이면 지표가 뒤집힌다."""

    close = np.array([100.0, 110.0, 121.0])
    volume = np.array([500.0, 400.0, 900.0])

    result = vnvi(close, volume)

    assert result[0] == 1000.0
    assert result[1] == pytest.approx(1100.0)
    assert result[2] == pytest.approx(1100.0)


def testPositiveVolumeIndexMovesOnlyWhenVolumeGrows() -> None:
    """PVI 는 NVI 의 반대다. 늘어난 날만 반영한다."""

    close = np.array([100.0, 110.0, 121.0])
    volume = np.array([500.0, 900.0, 400.0])

    result = vpvi(close, volume)

    assert result[0] == 1000.0
    assert result[1] == pytest.approx(1100.0)
    assert result[2] == pytest.approx(1100.0)


def testVolumeIndicesStartAtTheSameBaseline() -> None:
    """둘 다 1000 에서 출발해야 서로 비교된다."""

    close = np.array([100.0, 100.0])
    volume = np.array([100.0, 100.0])

    assert vnvi(close, volume)[0] == 1000.0
    assert vpvi(close, volume)[0] == 1000.0


def testPriceVolumeTrendAccumulatesVolumeWeightedReturns() -> None:
    """PVT 는 수익률에 거래량을 곱해 누적한다."""

    close = np.array([100.0, 110.0, 99.0])
    volume = np.array([0.0, 200.0, 300.0])

    result = vpvt(close, volume)

    assert result[0] == 0.0
    assert result[1] == pytest.approx(20.0)
    assert result[2] == pytest.approx(20.0 + 300.0 * (99.0 - 110.0) / 110.0)


def testPriceVolumeTrendHoldsWhenThePreviousCloseIsNotPositive() -> None:
    """직전 종가가 0 이면 수익률을 정의할 수 없어 직전 값을 유지한다."""

    close = np.array([0.0, 110.0])
    volume = np.array([100.0, 200.0])

    result = vpvt(close, volume)

    assert result[1] == result[0]


@pytest.mark.parametrize(
    "call",
    [
        lambda a: vobv(a, a),
        lambda a: vnvi(a, a),
        lambda a: vpvi(a, a),
        lambda a: vpvt(a, a),
        lambda a: vadl(a, a, a, a),
    ],
)
def testIndicatorsPreserveInputLength(call) -> None:
    """지표 길이가 입력과 다르면 위층 정렬이 통째로 어긋난다."""

    series = np.array([10.0, 11.0, 12.0, 11.0, 13.0])

    assert len(call(series)) == len(series)
