"""거시 국면 판정의 정규분포 CDF 회귀.

손으로 옮겨 적은 근사식에서 지수항의 1/sqrt(2*pi) 계수가 빠져 있었다. 문서는 오차가
7.5e-8 이라고 밝혔는데 실제 최대 오차는 0.037 로 50 만 배 컸다. Φ(1) 이 0.8703 으로
나와 참값 0.8413 과 3 퍼센트포인트 가까이 어긋났고, 그 값이 밸류에이션 백분위와 국면
판정에 그대로 들어갔다.

근사식은 값이 그럴듯해서 틀린 줄 모른다. 그래서 참값과 직접 대조한다.
"""

from __future__ import annotations

import math

import pytest

from dartlab.macro.cycles._macroCycleStats import _normCdf


@pytest.mark.parametrize("z", [-3.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0])
def testMatchesTheTrueDistributionFunction(z: float) -> None:
    """참값과 대조한다. 근사식은 그럴듯한 오답을 내기 쉽다."""

    expected = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

    assert _normCdf(z) == pytest.approx(expected, abs=1e-12)


def testKnownLandmarkValues() -> None:
    """교과서 값으로 한 번 더 못 박는다."""

    assert _normCdf(0.0) == pytest.approx(0.5)
    assert _normCdf(1.0) == pytest.approx(0.8413447, abs=1e-6)
    assert _normCdf(-1.0) == pytest.approx(0.1586553, abs=1e-6)
    assert _normCdf(1.96) == pytest.approx(0.9750021, abs=1e-6)


def testIsSymmetricAroundZero() -> None:
    """대칭이 깨지면 상방과 하방 판정이 서로 다른 기준을 쓰게 된다."""

    for z in (0.3, 1.1, 2.4):
        assert _normCdf(z) + _normCdf(-z) == pytest.approx(1.0, abs=1e-12)


def testStaysWithinBounds() -> None:
    """확률이 구간을 벗어나면 백분위 표기가 무너진다."""

    for z in (-8.0, -3.0, 0.0, 3.0, 8.0):
        assert 0.0 <= _normCdf(z) <= 1.0


def testIsMonotonic() -> None:
    """단조성이 깨지면 더 극단적인 값이 덜 극단적으로 읽힌다."""

    values = [_normCdf(z / 10) for z in range(-40, 41)]

    assert all(earlier <= later for earlier, later in zip(values, values[1:], strict=False))
