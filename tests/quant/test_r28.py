"""R28 audit 회귀 테스트 — quant 엔진.

R28 audit: silent failure 0건. KeyError 로 명시적 처리 (ValueError 아니지만
사용자에게 명확함). 회귀 방지용.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_quant_no_args_returns_guide():
    """무인자 → DataFrame 가이드."""
    import polars as pl

    import dartlab

    c = dartlab.Company("005930")
    r = c.quant()
    assert isinstance(r, pl.DataFrame)
    assert "axis" in r.columns
    assert "label" in r.columns
    assert len(r) >= 20


def test_quant_unknown_metric_raises():
    """없는 metric 은 silent 가 아닌 명시적 에러 (KeyError)."""
    import dartlab

    c = dartlab.Company("005930")
    with pytest.raises((KeyError, ValueError), match="없는metric|찾을 수 없"):
        c.quant("없는metric")


def test_quant_empty_string_raises():
    """빈 문자열도 명시적 에러."""
    import dartlab

    c = dartlab.Company("005930")
    with pytest.raises((KeyError, ValueError)):
        c.quant("")


def test_quant_korean_alias(monkeypatch):
    """한글 alias 동작."""
    import polars as pl

    import dartlab
    import dartlab.quant.signal.momentum as momentumModule

    prices = pl.DataFrame({"close": [float(i) for i in range(1, 31)]})
    monkeypatch.setattr(momentumModule, "fetchOhlcv", lambda *args, **kwargs: prices)

    c = dartlab.Company("005930")
    r = c.quant("모멘텀")
    assert r is not None
    assert isinstance(r, dict)
