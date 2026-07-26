"""L0 가격 형태 지표 회귀.

`core/indicators/price.py` 는 공개 함수 셋이 전부 테스트 참조 0 이었다. 피벗과 회귀선은
위층 차트와 스크리너가 직접 얹는 값이라, 기준선이 한 칸 밀리면 지지 저항이 통째로
어긋난다.

전부 순수 함수라 손계산 기댓값으로 값 자체를 못 박는다.
"""

from __future__ import annotations

import numpy as np
import pytest

from dartlab.core.indicators.price import vlinearRegression, vpivotPoints, vzigzag


def testPivotPointsUseThePreviousBarNotTheCurrentOne() -> None:
    """피벗은 직전 봉으로 계산한다. 당일 봉을 쓰면 미래를 보는 값이 된다."""

    high = np.array([12.0, 99.0])
    low = np.array([6.0, 1.0])
    close = np.array([9.0, 50.0])

    pp, r1, r2, r3, s1, s2, s3 = vpivotPoints(high, low, close)

    assert pp[1] == pytest.approx(9.0)
    assert r1[1] == pytest.approx(12.0)
    assert s1[1] == pytest.approx(6.0)
    assert r2[1] == pytest.approx(15.0)
    assert s2[1] == pytest.approx(3.0)
    assert r3[1] == pytest.approx(18.0)
    assert s3[1] == pytest.approx(0.0)


def testPivotPointsLeaveTheFirstBarUndefined() -> None:
    """직전 봉이 없으면 값이 없다. 0 으로 채우면 첫 봉이 지지선 0 원으로 읽힌다."""

    high = np.array([12.0, 13.0])
    low = np.array([6.0, 7.0])
    close = np.array([9.0, 10.0])

    for series in vpivotPoints(high, low, close):
        assert np.isnan(series[0])


def testPivotLevelsKeepTheirOrdering() -> None:
    """지지와 저항은 s3 < s2 < s1 < pp < r1 < r2 < r3 순서를 지켜야 한다."""

    rng = np.random.default_rng(20260727)
    n = 40
    close = np.cumsum(rng.normal(0, 1, n)) + 100
    high = close + rng.uniform(0.5, 2.0, n)
    low = close - rng.uniform(0.5, 2.0, n)

    pp, r1, r2, r3, s1, s2, s3 = vpivotPoints(high, low, close)
    defined = ~np.isnan(pp)

    assert defined.any()
    assert (s3[defined] <= s2[defined]).all()
    assert (s2[defined] <= s1[defined]).all()
    assert (s1[defined] <= pp[defined]).all()
    assert (pp[defined] <= r1[defined]).all()
    assert (r1[defined] <= r2[defined]).all()
    assert (r2[defined] <= r3[defined]).all()


def testLinearRegressionRecoversAPerfectLine() -> None:
    """직선 입력이면 기울기를 정확히 되찾고 설명력은 1 이다."""

    close = np.arange(0.0, 20.0) * 3.0 + 5.0

    value, slope, rsq = vlinearRegression(close, period=10)

    assert slope[-1] == pytest.approx(3.0)
    assert value[-1] == pytest.approx(close[-1])
    assert rsq[-1] == pytest.approx(1.0)


def testLinearRegressionLeavesTheWarmupUndefined() -> None:
    """period 만큼 쌓이기 전에는 회귀선을 그릴 수 없다."""

    close = np.arange(0.0, 20.0)

    value, slope, rsq = vlinearRegression(close, period=10)

    assert np.isnan(value[:9]).all()
    assert np.isnan(slope[:9]).all()
    assert np.isnan(rsq[:9]).all()
    assert not np.isnan(value[9:]).any()


def testLinearRegressionOnFlatSeriesHasZeroSlope() -> None:
    """값이 변하지 않으면 기울기는 0 이고 설명할 분산이 없어 0 이다."""

    close = np.full(20, 7.0)

    _value, slope, rsq = vlinearRegression(close, period=10)

    assert slope[-1] == pytest.approx(0.0)
    assert rsq[-1] == pytest.approx(0.0)


def testLinearRegressionExplanatoryPowerStaysWithinBounds() -> None:
    """설명력은 0 과 1 사이다. 벗어나면 위층 신뢰도 가중이 무너진다."""

    rng = np.random.default_rng(11)
    close = np.cumsum(rng.normal(0, 1, 80)) + 100

    _value, _slope, rsq = vlinearRegression(close, period=20)
    defined = rsq[~np.isnan(rsq)]

    assert defined.size > 0
    assert (defined >= 0).all() and (defined <= 1).all()


def testZigzagAnchorsAtTheFirstBar() -> None:
    """첫 봉은 언제나 기준점이다. 여기가 비면 이후 변화율 계산이 성립하지 않는다."""

    close = np.array([100.0, 101.0, 102.0])

    result = vzigzag(close, threshold=5.0)

    assert result[0] == 100.0


def testZigzagIgnoresMovesBelowTheThreshold() -> None:
    """임계 미만 흔들림은 꼭지점이 아니다. 잡으면 노이즈가 추세로 보인다."""

    close = np.array([100.0, 101.0, 100.5, 101.5, 100.0])

    result = vzigzag(close, threshold=5.0)

    assert not np.isnan(result[0])
    assert np.isnan(result[1:]).all()


def testZigzagMarksThePivotOnceTheMoveClearsTheThreshold() -> None:
    """임계를 넘으면 그 지점을 꼭지점으로 잡는다."""

    close = np.array([100.0, 103.0, 110.0])

    result = vzigzag(close, threshold=5.0)

    assert np.isnan(result[1])
    assert result[2] == pytest.approx(110.0)


def testZigzagMovesThePivotForwardWhileTheTrendExtends() -> None:
    """추세가 이어지면 꼭지점은 앞선 자리를 비우고 최신 극값으로 옮겨간다."""

    close = np.array([100.0, 110.0, 120.0])

    result = vzigzag(close, threshold=5.0)

    assert np.isnan(result[1])
    assert result[2] == pytest.approx(120.0)


def testZigzagPreservesInputLength() -> None:
    """길이가 달라지면 위층 정렬이 어긋난다."""

    close = np.array([100.0, 106.0, 99.0, 120.0])

    assert len(vzigzag(close, threshold=5.0)) == len(close)
