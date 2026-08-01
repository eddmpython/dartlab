"""전략 스타일 임계값의 형성 시점 회귀 테스트."""

from __future__ import annotations

import numpy as np
import pytest

pytestmark = pytest.mark.unit


def test_rolling_statistics_use_only_prior_history():
    """각 봉의 분위와 z-score는 현재 봉과 미래 값을 표본에 넣지 않는다."""
    from dartlab.quant.strategy.styles._common import rollingQuantile, rollingZScore

    values = np.array([np.nan, 1.0, 2.0, 3.0, 4.0, 5.0])
    quantile = rollingQuantile(values, 0.5, window=3, minPeriods=2)
    zscore = rollingZScore(values, window=3, minPeriods=2)

    assert np.isnan(quantile[2])
    assert quantile[3] == pytest.approx(1.5)
    assert zscore[3] == pytest.approx((3.0 - 1.5) / np.std([1.0, 2.0], ddof=1))

    changed = values.copy()
    changed[3] = -1_000.0
    changed_q = rollingQuantile(changed, 0.5, window=3, minPeriods=2)
    assert changed_q[3] == quantile[3]
    assert changed_q[4] != quantile[4]

    boundary = np.arange(10.0)
    base_boundary = rollingQuantile(boundary, 0.0, window=5, minPeriods=5)
    outside = boundary.copy()
    outside[2] = -1_000.0
    inside = boundary.copy()
    inside[3] = 1_000.0
    assert rollingQuantile(outside, 0.0, window=5, minPeriods=5)[8] == base_boundary[8]
    assert rollingQuantile(inside, 0.0, window=5, minPeriods=5)[8] != base_boundary[8]


def test_rolling_statistics_reject_invalid_windows_and_constant_zscore():
    """표본 수가 window를 넘을 수 없고 상수 이력의 z-score는 결측이다."""
    from dartlab.quant.strategy.styles._common import rollingQuantile, rollingZScore

    with pytest.raises(ValueError, match="must not exceed"):
        rollingQuantile(np.arange(10.0), 0.5, window=5, minPeriods=6)
    with pytest.raises(ValueError, match="between 0 and 1"):
        rollingQuantile(np.arange(10.0), 1.1, window=5, minPeriods=3)
    constant = rollingZScore(np.ones(10), window=5, minPeriods=3)
    assert np.all(np.isnan(constant))


def test_rolling_statistics_are_invariant_to_future_tail():
    """미래 tail을 추가해도 기존 prefix 통계는 바뀌지 않는다."""
    from dartlab.quant.strategy.styles._common import rollingQuantile, rollingZScore

    rng = np.random.default_rng(20260801)
    prefix = rng.normal(size=400)
    extended = np.concatenate([prefix, np.full(80, 1_000.0)])

    base_q = rollingQuantile(prefix, 0.7, window=252, minPeriods=20)
    future_q = rollingQuantile(extended, 0.7, window=252, minPeriods=20)
    base_z = rollingZScore(prefix, window=252, minPeriods=20)
    future_z = rollingZScore(extended, window=252, minPeriods=20)

    np.testing.assert_allclose(base_q, future_q[: len(prefix)], equal_nan=True)
    np.testing.assert_allclose(base_z, future_z[: len(prefix)], equal_nan=True)


def test_mean_reversion_signals_are_invariant_to_future_tail(monkeypatch):
    """미래 변동성 분포를 붙여도 과거 mean-reversion 신호는 변하지 않는다."""
    from dartlab.quant.strategy.styles import meanReversion

    prefix = np.linspace(100.0, 120.0, 400)
    extended = np.concatenate([prefix, np.linspace(121.0, 180.0, 100)])

    monkeypatch.setattr(meanReversion, "getArrays", lambda company: {"close": company.close})

    def _zscore(close, window):
        values = np.full(len(close), -2.0)
        values[::50] = 0.0
        return values

    monkeypatch.setattr(meanReversion, "_residualZScore", _zscore)
    monkeypatch.setattr(meanReversion, "vrsi", lambda close, period: np.zeros(len(close)))
    monkeypatch.setattr(
        meanReversion,
        "_volatilitySeries",
        lambda close: {
            "realized_vol": np.concatenate(
                [1.0 + np.arange(min(len(close), 400)) % 100, np.full(max(0, len(close) - 400), 10_000.0)]
            )
        },
    )

    base_rule = meanReversion.build(type("Company", (), {"close": prefix})())
    future_rule = meanReversion.build(type("Company", (), {"close": extended})())

    np.testing.assert_array_equal(base_rule.entry_expr, future_rule.entry_expr[: len(prefix)])
    np.testing.assert_array_equal(base_rule.exit_expr, future_rule.exit_expr[: len(prefix)])
    assert np.any(base_rule.entry_expr)
    assert np.any(base_rule.exit_expr)
    assert base_rule.meta["formation"] == "prior_252d_min_60d"


def test_low_vol_signals_are_invariant_to_future_tail(monkeypatch):
    """미래 vol과 MDD 분포를 붙여도 과거 defensive 신호는 변하지 않는다."""
    from dartlab.quant.strategy.styles import lowVolDefensive

    prefix = np.linspace(100.0, 130.0, 700)
    extended = np.concatenate([prefix, np.linspace(131.0, 180.0, 100)])

    monkeypatch.setattr(lowVolDefensive, "getArrays", lambda company: {"close": company.close})
    monkeypatch.setattr(
        lowVolDefensive,
        "_volatilitySeries",
        lambda close: {
            "realized_vol": np.concatenate(
                [
                    1.0 + np.arange(min(len(close), 700)) % 100,
                    np.full(max(0, len(close) - 700), 10_000.0),
                ]
            )
        },
    )
    monkeypatch.setattr(
        lowVolDefensive,
        "_tailriskSeries",
        lambda close: {
            "rolling_mdd": np.concatenate(
                [
                    np.sin(np.arange(min(len(close), 700)) / 10.0),
                    np.full(max(0, len(close) - 700), 100.0),
                ]
            )
        },
    )

    base_rule = lowVolDefensive.build(type("Company", (), {"close": prefix})())
    future_rule = lowVolDefensive.build(type("Company", (), {"close": extended})())

    np.testing.assert_array_equal(base_rule.entry_expr, future_rule.entry_expr[: len(prefix)])
    np.testing.assert_array_equal(base_rule.exit_expr, future_rule.exit_expr[: len(prefix)])
    assert np.any(base_rule.entry_expr)
    assert np.any(base_rule.exit_expr)
    assert base_rule.meta["formation"] == "prior_up_to_5y_min_1y"


def test_real_indicator_styles_are_prefix_invariant_at_multiple_cut_points(monkeypatch):
    """실제 RSI, vol, MDD, residual 경로도 warm-up과 window 경계에서 인과적이다."""
    from dartlab.quant.strategy.styles import lowVolDefensive, meanReversion

    rng = np.random.default_rng(42)
    returns = rng.normal(0.0003, 0.015, size=1_600)
    close = 100.0 * np.exp(np.cumsum(returns))
    monkeypatch.setattr(meanReversion, "getArrays", lambda company: {"close": company.close})
    monkeypatch.setattr(lowVolDefensive, "getArrays", lambda company: {"close": company.close})

    full_mean = meanReversion.build(type("Company", (), {"close": close})())
    full_low = lowVolDefensive.build(type("Company", (), {"close": close})())

    for cut in (81, 252, 504, 505, 800, 1_260, 1_300):
        prefix = close[:cut]
        mean_prefix = meanReversion.build(type("Company", (), {"close": prefix})())
        low_prefix = lowVolDefensive.build(type("Company", (), {"close": prefix})())
        np.testing.assert_array_equal(mean_prefix.entry_expr, full_mean.entry_expr[:cut])
        np.testing.assert_array_equal(mean_prefix.exit_expr, full_mean.exit_expr[:cut])
        np.testing.assert_array_equal(low_prefix.entry_expr, full_low.entry_expr[:cut])
        np.testing.assert_array_equal(low_prefix.exit_expr, full_low.exit_expr[:cut])


def test_ohlcv_arrays_are_sorted_before_causal_signal_formation():
    """입력 행 순서와 무관하게 numpy 시계열은 날짜 오름차순이다."""
    import polars as pl

    from dartlab.quant.screen.dataAccess import ohlcvToArrays

    frame = pl.DataFrame(
        {
            "date": ["2024-01-03", "2024-01-01", "2024-01-02"],
            "close": [3.0, 1.0, 2.0],
        }
    )
    arrays = ohlcvToArrays(frame)

    assert arrays["date"] == ["2024-01-01", "2024-01-02", "2024-01-03"]
    np.testing.assert_array_equal(arrays["close"], [1.0, 2.0, 3.0])
