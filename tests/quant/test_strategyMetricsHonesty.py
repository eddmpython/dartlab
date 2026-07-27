"""전략 지표의 정의 정확성 회귀.

두 지표가 그럴듯한 숫자를 내면서 실제로는 아무 말도 하지 않고 있었다.

Sortino 는 손실 구간만 골라 그 표준편차를 썼다. 그것은 손실이 자기 평균에서 얼마나
흩어졌는지를 잴 뿐 얼마나 아래인지는 재지 않는다. 그래서 매일 +2% 와 -1% 를 반복해
평균 +0.5% 를 내는 전략이 0.0 을 받았다. 손실 크기가 모두 같아 흩어짐이 0 이기 때문이다.
좋은 전략이 최악으로 보인다.

과적합 확률은 시행이 하나뿐일 때 "최고 시행" 이 자기 자신이라 순위가 언제나 1 이 되고
결과가 무조건 1.0 으로 고정됐다. OOS 성적이 정반대여도 같은 값이 나온다. 문서는
0.5 이상을 과적합 의심이라 적어 두었으므로 모든 정적 규칙이 최대 과적합으로 보고됐다.
"""

from __future__ import annotations

import numpy as np
import pytest

from dartlab.quant.strategy._metricsBasic import sharpe, sortino
from dartlab.quant.strategy._metricsOverfitting import pbo


def testProfitableStrategyWithUniformLossesIsNotScoredZero() -> None:
    """결함의 핵심 사례다. 손실 크기가 같다는 이유로 0 이 되면 안 된다."""

    returns = np.array([0.02, -0.01] * 126)

    assert sortino(returns) > 0
    assert sortino(returns) > sharpe(returns)


def testLosingStrategyIsNegative() -> None:
    """전부 손실인 전략이 양수나 0 이면 지표가 방향을 못 가린다."""

    assert sortino(np.array([-0.01] * 100)) < 0


def testBetterStrategyScoresHigher() -> None:
    """같은 하방 위험이면 수익이 큰 쪽이 높아야 한다."""

    modest = np.array([0.01, -0.01] * 126)
    strong = np.array([0.03, -0.01] * 126)

    assert sortino(strong) > sortino(modest)


def testUpsideVolatilityDoesNotPenalize() -> None:
    """상방 변동은 위험이 아니다. 그것이 Sharpe 와 다른 이유다."""

    steady = np.array([0.01, -0.01] * 126)
    spiky = np.array([0.05, -0.01] * 126)

    assert sortino(spiky) > sortino(steady)


def testTooFewObservationsReturnZero() -> None:
    """표본이 없으면 값을 만들지 않는다."""

    assert sortino(np.array([0.01])) == 0.0


def testOverfittingProbabilityIsUndecidableWithOneTrial() -> None:
    """시행이 하나면 자기 자신과 비교하는 셈이라 판정할 수 없다."""

    assert pbo([[0.1, 0.2, 0.3]], [[2.0, 3.0, 4.0]]) is None
    assert pbo([[0.1, 0.2, 0.3]], [[-2.0, -3.0, -4.0]]) is None


def testOverfittingProbabilityDistinguishesGoodAndBadOutOfSample() -> None:
    """시행이 여럿이면 OOS 성적에 따라 답이 갈려야 한다."""

    inSample = np.array([[0.3, 0.4], [0.2, 0.3], [0.1, 0.2]])
    goodOos = np.array([[0.3, 0.4], [0.2, 0.3], [0.1, 0.2]])
    badOos = np.array([[-0.3, -0.4], [0.2, 0.3], [0.1, 0.2]])

    assert pbo(inSample, goodOos) != pbo(inSample, badOos)


@pytest.mark.parametrize(
    ("inSample", "outOfSample"),
    [([[0.1]], [[0.2]]), ([[0.1, 0.2]], [[0.1]])],
)
def testDegenerateShapesDoNotProduceAConfidentAnswer(inSample: list, outOfSample: list) -> None:
    """구간이 부족하거나 모양이 안 맞으면 확신에 찬 값을 내면 안 된다."""

    result = pbo(inSample, outOfSample)

    assert result is None or result == 0.0
