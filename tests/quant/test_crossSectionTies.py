"""횡단면 팩터 순위의 동률·결측 계약."""

from __future__ import annotations

import math

import pytest

from dartlab.quant.alphas.crossSection import percentileRank

pytestmark = pytest.mark.unit


def testEqualValuesReceiveTheSameAveragePercentile() -> None:
    assert percentileRank([1.0, 1.0, 1.0]) == [0.5, 0.5, 0.5]


def testTiesDoNotDependOnInputOrder() -> None:
    assert percentileRank([2.0, 1.0, 2.0, 3.0]) == pytest.approx([0.5, 0.0, 0.5, 1.0])


def testNonFiniteValuesRemainUnranked() -> None:
    result = percentileRank([1.0, float("nan"), 3.0])
    assert result[0] == 0.0
    assert math.isnan(result[1])
    assert result[2] == 1.0
