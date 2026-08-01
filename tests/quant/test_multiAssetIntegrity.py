from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl
import pytest

from dartlab.quant.strategy._backtestAdvanced import multiAssetBacktest
from dartlab.quant.strategy.backtest import vectorBacktest
from dartlab.quant.strategy.rule import Rule

pytestmark = pytest.mark.unit


def _bars(close: np.ndarray, *, start: date = date(2025, 1, 2)) -> pl.DataFrame:
    dates = [start + timedelta(days=idx) for idx in range(len(close))]
    return pl.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": np.full(len(close), 1_000_000.0),
        }
    )


def _buyAndHold(stub) -> Rule:
    close = stub._quant_arrays["close"]
    entries = np.zeros(len(close), dtype=np.bool_)
    exits = np.zeros(len(close), dtype=np.bool_)
    entries[0] = True
    return Rule(entries, exits)


def _patchFetch(monkeypatch, frames: dict[str, pl.DataFrame], calls: list[tuple[str, dict]] | None = None):
    import dartlab.quant.screen.dataAccess as data_access

    def fake_fetch(code, **kwargs):
        if calls is not None:
            calls.append((code, kwargs))
        return frames.get(code)

    monkeypatch.setattr(data_access, "fetchOhlcv", fake_fetch)


def test_equal_portfolio_is_initial_capital_sleeves_not_costless_daily_rebalancing(monkeypatch):
    first = np.linspace(100.0, 180.0, 80)
    second = np.linspace(100.0, 70.0, 80)
    frames = {"005930": _bars(first), "000660": _bars(second)}
    _patchFetch(monkeypatch, frames)

    result = multiAssetBacktest(
        ["005930", "000660"],
        _buyAndHold,
        weighting="equal",
        feeBps=0.0,
        slipBps=0.0,
    )

    dates = frames["005930"]["date"].to_list()
    individual = []
    for code in ("005930", "000660"):
        close = frames[code]["close"].to_numpy()
        individual.append(
            vectorBacktest(
                close,
                _buyAndHold(type("Stub", (), {"_quant_arrays": {"close": close}})()),
                open_=close,
                high=close + 1.0,
                low=close - 1.0,
                dates=dates,
                feeBps=0.0,
                slipBps=0.0,
            )
        )
    expected_equity = 0.5 * individual[0].equity + 0.5 * individual[1].equity

    assert result.status == "ok"
    np.testing.assert_allclose(result.equity, expected_equity)
    np.testing.assert_allclose(result.returns, result.equity / np.r_[1.0, result.equity[:-1]] - 1.0)
    assert result.period == (dates[0], dates[-1])
    assert result.validation["mode"] == "initial_equal_strategy_sleeves"
    assert result.validation["calendar_policy"] == "same_bounds_union_with_stale_internal_gaps"
    assert result.validation["universe_point_in_time"] is False
    assert result.oos is False
    assert result.dsr is None


def test_equal_portfolio_is_invariant_to_stock_code_order(monkeypatch):
    frames = {
        "005930": _bars(np.linspace(100.0, 160.0, 80)),
        "000660": _bars(np.linspace(100.0, 90.0, 80)),
    }
    _patchFetch(monkeypatch, frames)

    forward = multiAssetBacktest(["005930", "000660"], _buyAndHold, feeBps=0.0, slipBps=0.0)
    reverse = multiAssetBacktest(["000660", "005930"], _buyAndHold, feeBps=0.0, slipBps=0.0)

    assert forward.status == reverse.status == "ok"
    np.testing.assert_allclose(forward.returns, reverse.returns)
    np.testing.assert_allclose(forward.equity, reverse.equity)


def test_mismatched_trading_calendars_fail_instead_of_tail_aligning_rows(monkeypatch):
    frames = {
        "005930": _bars(np.linspace(100.0, 120.0, 80), start=date(2025, 1, 2)),
        "000660": _bars(np.linspace(100.0, 120.0, 80), start=date(2025, 1, 3)),
    }
    _patchFetch(monkeypatch, frames)

    result = multiAssetBacktest(["005930", "000660"], _buyAndHold)

    assert result.status == "error"
    assert result.reason == "trading calendar bounds mismatch"
    assert len(result.validation["failed_assets"]) == 2


def test_internal_same_market_calendar_gaps_keep_stale_sleeve_nav_instead_of_tail_alignment(monkeypatch):
    full = _bars(np.linspace(100.0, 140.0, 80))
    halted = _bars(np.linspace(100.0, 120.0, 80)).with_row_index("row").filter(~pl.col("row").is_in([20, 21, 22]))
    frames = {"005930": full, "000660": halted.drop("row")}
    _patchFetch(monkeypatch, frames)

    result = multiAssetBacktest(
        ["005930", "000660"],
        _buyAndHold,
        feeBps=0.0,
        slipBps=0.0,
    )

    assert result.status == "ok"
    assert len(result.returns) == 80
    assert result.validation["calendar_policy"] == "same_bounds_union_with_stale_internal_gaps"
    assert result.validation["calendar_gaps"]["005930"]["count"] == 0
    assert result.validation["calendar_gaps"]["000660"]["count"] == 3


@pytest.mark.parametrize("weighting", ["inv_vol", "risk_parity", "mystery"])
def test_unimplemented_or_unknown_weighting_fails_before_fetch(monkeypatch, weighting):
    calls: list[tuple[str, dict]] = []
    _patchFetch(monkeypatch, {}, calls)

    result = multiAssetBacktest(["005930", "000660"], _buyAndHold, weighting=weighting)

    assert result.status == "error"
    assert "unsupported weighting" in (result.reason or "")
    assert calls == []


def test_duplicate_and_mixed_market_universes_are_rejected(monkeypatch):
    calls: list[tuple[str, dict]] = []
    _patchFetch(monkeypatch, {}, calls)

    duplicate = multiAssetBacktest(["005930", "005930"], _buyAndHold)
    mixed = multiAssetBacktest(["005930", "AAPL"], _buyAndHold)

    assert duplicate.status == "error"
    assert "duplicate" in (duplicate.reason or "")
    assert mixed.status == "error"
    assert "mixed-market" in (mixed.reason or "")
    assert calls == []


def test_missing_requested_asset_fails_closed_with_the_exclusion_reason(monkeypatch):
    frames = {"005930": _bars(np.linspace(100.0, 120.0, 80))}
    _patchFetch(monkeypatch, frames)

    result = multiAssetBacktest(["005930", "000660"], _buyAndHold)

    assert result.status == "error"
    assert result.validation["requested_assets"] == ["005930", "000660"]
    assert result.validation["included_assets"] == ["005930"]
    assert result.validation["failed_assets"] == [{"stockCode": "000660", "reason": "OHLCV unavailable"}]


def test_start_is_forwarded_once_per_asset_and_rule_uses_the_same_snapshot(monkeypatch):
    frames = {
        "005930": _bars(np.linspace(100.0, 130.0, 80)),
        "000660": _bars(np.linspace(100.0, 110.0, 80)),
    }
    calls: list[tuple[str, dict]] = []
    seen_arrays: list[int] = []
    _patchFetch(monkeypatch, frames, calls)

    def builder(stub):
        seen_arrays.append(id(stub._quant_arrays))
        return _buyAndHold(stub)

    result = multiAssetBacktest(
        ["005930", "000660"],
        builder,
        start="2025-01-01",
        feeBps=0.0,
        slipBps=0.0,
    )

    assert result.status == "ok"
    assert calls == [
        ("005930", {"start": "2025-01-01"}),
        ("000660", {"start": "2025-01-01"}),
    ]
    assert len(seen_arrays) == 2
    assert result.validation["start"] == "2025-01-01"
