from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from dartlab.quant.strategy.backtest import vectorBacktest
from dartlab.quant.strategy.rule import Rule

pytestmark = pytest.mark.unit


def _rule(n: int, *, entry: int = 0, exit_: int = 2, sizing: dict | None = None) -> Rule:
    entries = np.zeros(n, dtype=np.bool_)
    exits = np.zeros(n, dtype=np.bool_)
    entries[entry] = True
    exits[exit_] = True
    return Rule(entries, exits, sizing=sizing)


def test_fractional_kelly_sizes_the_same_trade_and_preserves_the_wealth_ledger():
    close = np.full(40, 120.0)
    close[:2] = 100.0
    sizing = {
        "method": "kelly",
        "kwargs": {"winProb": 0.60, "winLossRatio": 1.0},
    }

    result = vectorBacktest(
        close,
        _rule(len(close), sizing=sizing),
        feeBps=0.0,
        slipBps=0.0,
        execMode="close",
    )

    assert result.status == "ok"
    assert result.trades.height == 1
    assert result.trades["size"][0] == pytest.approx(0.20)
    assert result.trades["asset_pnl"][0] == pytest.approx(0.20)
    assert result.trades["pnl"][0] == pytest.approx(0.04)
    assert result.equity[-1] == pytest.approx(1.04)
    assert float(np.prod(1.0 + result.returns)) == pytest.approx(result.equity[-1])
    assert float(np.prod(1.0 + result.trades["pnl"].to_numpy())) == pytest.approx(result.equity[-1])
    # 진입 20% + 가격 상승 뒤 실제 청산 명목 24% / 당시 NAV 104%.
    assert result.turnover == pytest.approx(0.20 + 0.24 / 1.04)


def test_equal_sizing_is_the_explicit_form_of_the_default_full_notional_contract():
    close = np.linspace(100.0, 120.0, 40)
    default = vectorBacktest(close, _rule(len(close)), feeBps=0.0, slipBps=0.0, execMode="close")
    explicit = vectorBacktest(
        close,
        _rule(len(close), sizing={"method": "equal", "kwargs": {}}),
        feeBps=0.0,
        slipBps=0.0,
        execMode="close",
    )

    assert default.status == explicit.status == "ok"
    np.testing.assert_array_equal(default.returns, explicit.returns)
    np.testing.assert_array_equal(default.equity, explicit.equity)
    np.testing.assert_array_equal(default.positions, explicit.positions)
    assert default.trades.equals(explicit.trades)


def test_fixed_half_size_scales_flat_price_round_trip_cost_to_half_of_full_size():
    close = np.full(40, 100.0)
    full = vectorBacktest(close, _rule(len(close)), feeBps=100.0, slipBps=0.0, execMode="close")
    half = vectorBacktest(
        close,
        _rule(len(close), sizing={"method": "fixed", "kwargs": {"weight": 0.5}}),
        feeBps=100.0,
        slipBps=0.0,
        execMode="close",
    )

    full_loss = 1.0 - full.equity[-1]
    half_loss = 1.0 - half.equity[-1]
    assert half_loss == pytest.approx(full_loss * 0.5)
    assert half.trades["size"][0] == pytest.approx(0.5)
    assert half.positions.max() < 0.51
    assert half.exposure == full.exposure
    assert half.averageExposure == pytest.approx(full.averageExposure * 0.5, rel=5e-3)


def test_adv_impact_uses_actual_fractional_trade_exposure_on_both_sides():
    close = np.full(40, 100.0)
    full = vectorBacktest(
        close,
        _rule(len(close)),
        feeBps=0.0,
        slipBps=0.0,
        impactBpsPerPct=100.0,
        capitalPctOfAdv=10.0,
        execMode="close",
    )
    half = vectorBacktest(
        close,
        _rule(len(close), sizing={"method": "fixed", "kwargs": {"weight": 0.5}}),
        feeBps=0.0,
        slipBps=0.0,
        impactBpsPerPct=100.0,
        capitalPctOfAdv=10.0,
        execMode="close",
    )

    assert full.status == half.status == "ok"
    assert half.trades["cost_bps"][0] < full.trades["cost_bps"][0]
    assert half.equity[-1] > full.equity[-1]
    assert half.validation["impact_model"] == "explicit_adv_ratio_scaled_by_trade_exposure"


def test_dynamic_vol_target_name_is_rejected_in_favor_of_explicit_at_entry_contract():
    close = np.linspace(100.0, 110.0, 80)
    sizing = {"method": "vol_target", "kwargs": {"targetVol": 0.1}}

    result = vectorBacktest(close, _rule(len(close), entry=60, exit_=70, sizing=sizing))

    assert result.status == "error"
    assert "vol_target_at_entry" in (result.reason or "")


def test_vol_target_size_uses_only_information_available_at_the_signal_close():
    rng = np.random.default_rng(91)
    prefix_returns = rng.normal(0.0002, 0.01, 90)
    prefix = 100.0 * np.cumprod(1.0 + prefix_returns)
    calm_tail = np.r_[prefix, np.linspace(prefix[-1], prefix[-1] * 1.05, 30)]
    shock_tail = np.r_[prefix, np.linspace(prefix[-1], prefix[-1] * 0.40, 30)]
    entry = 80
    sizing = {
        "method": "vol_target_at_entry",
        "kwargs": {"targetVol": 0.10, "window": 60, "minPeriods": 30, "maxLeverage": 1.0},
    }

    calm = vectorBacktest(
        calm_tail,
        _rule(len(calm_tail), entry=entry, exit_=100, sizing=sizing),
        feeBps=0.0,
        slipBps=0.0,
        execMode="close",
    )
    shock = vectorBacktest(
        shock_tail,
        _rule(len(shock_tail), entry=entry, exit_=100, sizing=sizing),
        feeBps=0.0,
        slipBps=0.0,
        execMode="close",
    )

    assert calm.status == shock.status == "ok"
    assert calm.trades["size"][0] == pytest.approx(shock.trades["size"][0])
    assert 0.0 < calm.trades["size"][0] <= 1.0


@pytest.mark.parametrize(
    ("sizing", "reason"),
    [
        ({"method": "mystery", "kwargs": {}}, "unknown sizing"),
        ({"method": "kelly", "kwargs": {"winProb": 0.6}}, "kelly"),
        ({"method": "vol_target_at_entry", "kwargs": {"window": 10, "minPeriods": 20}}, "minPeriods"),
    ],
)
def test_invalid_sizing_contracts_fail_closed(sizing, reason):
    close = np.linspace(100.0, 110.0, 40)

    result = vectorBacktest(close, _rule(len(close), sizing=sizing))

    assert result.status == "error"
    assert reason in (result.reason or "")


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"execMode": "tomorrow_close"}, "execMode"),
        ({"feeBps": -1.0}, "cost"),
        ({"slipBps": float("nan")}, "cost"),
        ({"impactBpsPerPct": -1.0}, "cost"),
        ({"capitalPctOfAdv": -0.1}, "cost"),
        ({"open_": np.ones(39)}, "open_"),
        ({"high": np.ones(39)}, "high"),
        ({"low": np.ones(39)}, "low"),
        ({"volume": np.ones(39)}, "volume"),
        ({"dates": [date(2026, 1, 1)] * 39}, "dates"),
    ],
)
def test_invalid_execution_inputs_return_error_instead_of_crashing(kwargs, reason):
    close = np.linspace(100.0, 110.0, 40)

    result = vectorBacktest(close, _rule(len(close)), **kwargs)

    assert result.status == "error"
    assert reason in (result.reason or "")


@pytest.mark.parametrize(
    "bad_close",
    [
        np.r_[np.ones(39), np.nan],
        np.r_[np.ones(39), 0.0],
        np.ones((40, 1)),
    ],
)
def test_close_must_be_a_finite_positive_one_dimensional_series(bad_close):
    result = vectorBacktest(bad_close, _rule(40))

    assert result.status == "error"
    assert "close" in (result.reason or "")


def test_ohlc_bounds_and_strict_date_order_are_validated():
    close = np.linspace(100.0, 110.0, 40)
    bad_high = close.copy()
    bad_high[10] = close[10] - 1.0
    dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(40)]
    dates[20], dates[21] = dates[21], dates[20]

    bad_bar = vectorBacktest(close, _rule(len(close)), high=bad_high)
    bad_dates = vectorBacktest(close, _rule(len(close)), dates=dates)

    assert bad_bar.status == "error"
    assert "OHLC" in (bad_bar.reason or "")
    assert bad_dates.status == "error"
    assert "dates" in (bad_dates.reason or "")


def test_ohlc_validation_tolerates_sub_basis_point_adjusted_price_rounding():
    close = np.full(40, 28_000.0)
    high = close.copy()
    high[10] = 27_999.0

    result = vectorBacktest(close, _rule(len(close)), high=high)

    assert result.status == "ok"


def test_stop_contract_requires_intrabar_high_and_low_inputs():
    close = np.linspace(100.0, 110.0, 40)
    rule = _rule(len(close))
    rule = Rule(
        rule.entry_expr,
        rule.exit_expr,
        stop={"method": "fixed_pct", "kwargs": {"pct": 0.05}},
    )

    result = vectorBacktest(close, rule)

    assert result.status == "error"
    assert "stop" in (result.reason or "")


def test_close_fallback_and_trade_dates_are_explicit_in_the_result_ledger():
    close = np.linspace(100.0, 110.0, 40)
    dates = [date(2026, 1, 1) + timedelta(days=idx) for idx in range(40)]

    result = vectorBacktest(close, _rule(len(close)), dates=dates, feeBps=0.0, slipBps=0.0)

    assert result.status == "ok"
    assert result.validation["execution_mode_requested"] == "next_open"
    assert result.validation["execution_mode_effective"] == "close_fallback"
    assert result.validation["open_fallback"] is True
    assert result.trades["entry_date"][0] == str(dates[1])
    assert result.trades["exit_date"][0] == str(dates[3])
