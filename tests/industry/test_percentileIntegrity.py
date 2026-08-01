"""산업 백분위의 음수 꼬리·범위 계약."""

from __future__ import annotations

import pytest

from dartlab.industry.calcs.companyCalcs import _distribution, _percentile

pytestmark = pytest.mark.unit


def testSevereNegativeMetricCannotBecomeTopPercentile() -> None:
    distribution = _distribution([-1.0, 0.0, 1.0, 2.0, 3.0])
    assert distribution is not None
    assert _percentile(-100.0, distribution) == 0.0


def testPercentileAlwaysStaysInsidePublicRange() -> None:
    distribution = _distribution([-5.0, -1.0, 0.0, 2.0, 10.0])
    assert distribution is not None
    for value in (-1e9, -5.0, 0.0, 10.0, 1e9):
        result = _percentile(value, distribution)
        assert result is not None
        assert 0.0 <= result <= 100.0
