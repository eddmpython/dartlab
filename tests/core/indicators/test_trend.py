"""L0 이동평균의 결측 처리 회귀.

`vsma` 는 누적합으로 계산해 NaN 하나가 이후 전 구간을 오염시켰다. 지표 하나의 문제로
끝나지 않았다. 스토캐스틱 %K 는 정의상 앞쪽 `kPeriod-1` 개가 NaN 인데, 그것을 `vsma` 로
평활하는 %D 와 KDJ 세 출력이 전 구간 NaN 이었다. 값이 없는 것이 아니라 계산이 죽어
있었고 아무도 실패를 보지 못했다.

여기서 고정하는 것은 결측이 그 창에만 머문다는 것, 그리고 그 위에 얹힌 지표가 실제
값을 낸다는 것이다.
"""

from __future__ import annotations

import numpy as np
import pytest

from dartlab.core.indicators.momentum import vkdj, vstochastic, vstochasticRsi
from dartlab.core.indicators.trend import vsma


def testMovingAverageKeepsMissingValuesLocalToTheirWindow() -> None:
    """앞쪽 결측 하나가 뒤 전부를 죽이면 안 된다."""

    result = vsma(np.array([np.nan, 1.0, 2.0, 3.0, 4.0, 5.0]), 2)

    assert np.isnan(result[0])
    assert np.isnan(result[1])
    assert result[2:].tolist() == [1.5, 2.5, 3.5, 4.5]


def testMovingAverageComputesTheWindowMean() -> None:
    """평균 자체가 맞아야 한다."""

    result = vsma(np.array([1.0, 2.0, 3.0, 4.0]), 2)

    assert np.isnan(result[0])
    assert result[1:].tolist() == [1.5, 2.5, 3.5]


def testMovingAverageLeavesTheWarmupUndefined() -> None:
    """period 만큼 쌓이기 전에는 값이 없다."""

    result = vsma(np.arange(1.0, 6.0), 3)

    assert np.isnan(result[:2]).all()
    assert not np.isnan(result[2:]).any()


def testMovingAverageReturnsAllMissingWhenHistoryIsShorterThanThePeriod() -> None:
    """자료가 창보다 짧으면 계산할 것이 없다."""

    result = vsma(np.array([1.0, 2.0]), 5)

    assert np.isnan(result).all()
    assert len(result) == 2


def testMovingAverageRejectsANonPositivePeriod() -> None:
    """창 길이가 0 이하이면 정의되지 않는다. 조용히 통과하면 안 된다."""

    with pytest.raises(ValueError):
        vsma(np.arange(5.0), 0)


def testStochasticSignalLineIsActuallyComputed() -> None:
    """%D 는 %K 를 평활한 값이다. 전 구간 NaN 이면 신호선이 죽은 것이다."""

    rng = np.random.default_rng(20260727)
    n = 60
    close = np.cumsum(rng.normal(0, 1, n)) + 100

    k, d = vstochastic(close + 1, close - 1, close)

    assert not np.isnan(k[-1])
    assert not np.isnan(d[-1])
    assert 0.0 <= d[-1] <= 100.0


def testKdjProducesAllThreeLines() -> None:
    """세 선 중 하나라도 죽으면 KDJ 자체가 쓸모없다."""

    rng = np.random.default_rng(11)
    n = 60
    close = np.cumsum(rng.normal(0, 1, n)) + 100

    kLine, dLine, jLine = vkdj(close + 1, close - 1, close)

    assert not np.isnan(kLine[-1])
    assert not np.isnan(dLine[-1])
    assert not np.isnan(jLine[-1])


def testStochasticRsiSignalLineIsActuallyComputed() -> None:
    """같은 평활을 쓰는 다른 소비자도 함께 살아나야 한다."""

    rng = np.random.default_rng(5)
    close = np.cumsum(rng.normal(0, 1, 120)) + 100

    _k, d = vstochasticRsi(close)

    assert not np.isnan(d[-1])
