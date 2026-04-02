"""Quant engine unit tests — vectorized indicators, signals, verdict.

Uses synthetic NumPy arrays (uptrend, downtrend, sideways).
No real data loading, no Company objects.
"""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ── imports ──

from dartlab.quant.indicators import vatr, vbollinger, vema, vmacd, vrsi, vsma
from dartlab.quant.signals import vcross, vcrossover, vcrossunder, vgoldenCross, vrsiSignal

# ── helpers: synthetic OHLCV ──


def _uptrend(n: int = 200, start: float = 100.0, step: float = 0.5) -> np.ndarray:
    """Steadily rising prices."""
    return np.arange(start, start + n * step, step, dtype=np.float64)[:n]


def _downtrend(n: int = 200, start: float = 200.0, step: float = 0.5) -> np.ndarray:
    """Steadily falling prices."""
    return np.arange(start, start - n * step, -step, dtype=np.float64)[:n]


def _sideways(n: int = 200, center: float = 100.0, amplitude: float = 2.0) -> np.ndarray:
    """Oscillating around center."""
    return center + amplitude * np.sin(np.linspace(0, 8 * np.pi, n))


def _make_ohlcv(close: np.ndarray, spread: float = 1.0):
    """Generate high/low/volume from close."""
    high = close + spread
    low = close - spread
    volume = np.full(len(close), 1_000_000, dtype=np.float64)
    return high, low, close, volume


# ═══════════════════════════════════════════════════════════
# vsma
# ═══════════════════════════════════════════════════════════


class TestVsma:
    def test_known_values(self):
        close = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = vsma(close, period=3)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        assert result[2] == pytest.approx(2.0)  # (1+2+3)/3
        assert result[3] == pytest.approx(3.0)  # (2+3+4)/3
        assert result[4] == pytest.approx(4.0)  # (3+4+5)/3

    def test_first_elements_are_nan(self):
        close = np.arange(1.0, 11.0)
        result = vsma(close, period=5)
        assert all(np.isnan(result[:4]))
        assert not np.isnan(result[4])

    def test_period_one_equals_close(self):
        close = np.array([10.0, 20.0, 30.0])
        result = vsma(close, period=1)
        np.testing.assert_array_almost_equal(result, close)

    def test_uptrend_sma_below_close(self):
        close = _uptrend(100)
        sma = vsma(close, 20)
        # In uptrend, SMA lags below current close
        valid = ~np.isnan(sma)
        assert np.all(close[valid][-10:] > sma[valid][-10:])


# ═══════════════════════════════════════════════════════════
# vema
# ═══════════════════════════════════════════════════════════


class TestVema:
    def test_first_ema_equals_sma_seed(self):
        close = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        result = vema(close, period=3)
        # Seed = mean(2,4,6) = 4.0
        assert result[2] == pytest.approx(4.0)

    def test_nan_before_period(self):
        close = np.arange(1.0, 11.0)
        result = vema(close, period=5)
        assert all(np.isnan(result[:4]))

    def test_ema_responds_faster_than_sma_accelerating(self):
        # Use accelerating (quadratic) uptrend where EMA tracks better
        t = np.arange(100, dtype=np.float64)
        close = 100.0 + 0.05 * t**2
        ema = vema(close, 20)
        sma = vsma(close, 20)
        valid = ~np.isnan(ema) & ~np.isnan(sma)
        ema_diff = np.abs(close[valid] - ema[valid])
        sma_diff = np.abs(close[valid] - sma[valid])
        assert np.mean(ema_diff[-20:]) < np.mean(sma_diff[-20:])


# ═══════════════════════════════════════════════════════════
# vrsi
# ═══════════════════════════════════════════════════════════


class TestVrsi:
    def test_pure_uptrend_rsi_high(self):
        close = _uptrend(100)
        rsi = vrsi(close, 14)
        last_rsi = rsi[-1]
        assert last_rsi > 70  # Strong uptrend -> overbought

    def test_pure_downtrend_rsi_low(self):
        close = _downtrend(100)
        rsi = vrsi(close, 14)
        last_rsi = rsi[-1]
        assert last_rsi < 30  # Strong downtrend -> oversold

    def test_rsi_range_0_to_100(self):
        close = _sideways(200)
        rsi = vrsi(close, 14)
        valid = rsi[~np.isnan(rsi)]
        assert np.all(valid >= 0)
        assert np.all(valid <= 100)

    def test_nan_before_period(self):
        close = _uptrend(50)
        rsi = vrsi(close, 14)
        assert all(np.isnan(rsi[:14]))
        assert not np.isnan(rsi[14])

    def test_constant_prices_rsi_at_boundary(self):
        # All same price -> no gains/losses -> avgLoss=0 -> RSI=100
        close = np.full(50, 100.0)
        rsi = vrsi(close, 14)
        assert rsi[14] == 100.0


# ═══════════════════════════════════════════════════════════
# vmacd
# ═══════════════════════════════════════════════════════════


class TestVmacd:
    def test_returns_three_arrays(self):
        close = _uptrend(100)
        macd_line, signal_line, histogram = vmacd(close)
        assert len(macd_line) == 100
        assert len(signal_line) == 100
        assert len(histogram) == 100

    def test_histogram_is_macd_minus_signal(self):
        close = _uptrend(100)
        macd_line, signal_line, histogram = vmacd(close)
        valid = ~np.isnan(macd_line) & ~np.isnan(signal_line)
        np.testing.assert_array_almost_equal(histogram[valid], (macd_line - signal_line)[valid])

    def test_uptrend_macd_positive(self):
        close = _uptrend(100)
        macd_line, _, _ = vmacd(close)
        # In steady uptrend, fast EMA > slow EMA -> MACD > 0
        last_valid = macd_line[~np.isnan(macd_line)]
        assert last_valid[-1] > 0

    def test_early_values_nan(self):
        close = _uptrend(50)
        macd_line, signal_line, _ = vmacd(close, fast=12, slow=26, signal=9)
        # MACD line needs slow-1 elements, signal needs slow-1+signal-1
        assert np.isnan(macd_line[0])
        assert np.isnan(signal_line[0])


# ═══════════════════════════════════════════════════════════
# vbollinger
# ═══════════════════════════════════════════════════════════


class TestVbollinger:
    def test_returns_upper_middle_lower(self):
        close = _sideways(100)
        upper, middle, lower = vbollinger(close, period=20, std=2.0)
        assert len(upper) == 100
        assert len(middle) == 100
        assert len(lower) == 100

    def test_upper_above_middle_above_lower(self):
        close = _sideways(100)
        upper, middle, lower = vbollinger(close, period=20, std=2.0)
        valid = ~np.isnan(upper)
        assert np.all(upper[valid] >= middle[valid])
        assert np.all(middle[valid] >= lower[valid])

    def test_middle_equals_sma(self):
        close = _sideways(100)
        _, middle, _ = vbollinger(close, period=20, std=2.0)
        sma = vsma(close, 20)
        valid = ~np.isnan(middle)
        np.testing.assert_array_almost_equal(middle[valid], sma[valid])

    def test_nan_before_period(self):
        close = _uptrend(50)
        upper, middle, lower = vbollinger(close, period=20)
        assert all(np.isnan(upper[:19]))
        assert not np.isnan(upper[19])

    def test_constant_prices_bands_collapse(self):
        close = np.full(50, 100.0)
        upper, middle, lower = vbollinger(close, period=20, std=2.0)
        # No variance -> upper == middle == lower
        valid = ~np.isnan(upper)
        np.testing.assert_array_almost_equal(upper[valid], middle[valid])
        np.testing.assert_array_almost_equal(lower[valid], middle[valid])


# ═══════════════════════════════════════════════════════════
# vatr
# ═══════════════════════════════════════════════════════════


class TestVatr:
    def test_nan_before_period(self):
        close = _uptrend(50)
        high, low, _, _ = _make_ohlcv(close)
        atr = vatr(high, low, close, period=14)
        assert all(np.isnan(atr[:13]))
        assert not np.isnan(atr[13])

    def test_constant_spread_atr(self):
        close = np.full(50, 100.0)
        high = close + 1.0
        low = close - 1.0
        atr = vatr(high, low, close, period=14)
        # True range = 2.0 for every bar -> ATR should be ~2.0
        assert atr[13] == pytest.approx(2.0, abs=0.01)

    def test_atr_positive(self):
        close = _sideways(100)
        high, low, _, _ = _make_ohlcv(close, spread=3.0)
        atr = vatr(high, low, close, period=14)
        valid = atr[~np.isnan(atr)]
        assert np.all(valid > 0)


# ═══════════════════════════════════════════════════════════
# technicalVerdict
# ═══════════════════════════════════════════════════════════


class TestTechnicalVerdict:
    def _make_df(self, close: np.ndarray):
        import polars as pl

        high, low, _, volume = _make_ohlcv(close)
        dates = [f"2024-01-{i + 1:02d}" for i in range(len(close))]
        # Pad dates if needed
        if len(dates) < len(close):
            dates = [f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}" for i in range(len(close))]
        return pl.DataFrame(
            {
                "date": dates[: len(close)],
                "open": close.tolist(),
                "high": high.tolist(),
                "low": low.tolist(),
                "close": close.tolist(),
                "volume": [1_000_000] * len(close),
            }
        )

    @patch("dartlab.quant.analyzer._fetchBenchmark", return_value=None)
    def test_uptrend_verdict(self, mock_bench):
        from dartlab.quant.analyzer import technicalVerdict

        close = _uptrend(200)
        df = self._make_df(close)
        result = technicalVerdict(df)
        assert result["verdict"] in ("강세", "중립")
        assert result["rsi"] > 50
        assert "score" in result

    @patch("dartlab.quant.analyzer._fetchBenchmark", return_value=None)
    def test_downtrend_verdict(self, mock_bench):
        from dartlab.quant.analyzer import technicalVerdict

        close = _downtrend(200)
        df = self._make_df(close)
        result = technicalVerdict(df)
        assert result["verdict"] in ("약세", "중립")
        assert result["rsi"] < 50

    @patch("dartlab.quant.analyzer._fetchBenchmark", return_value=None)
    def test_verdict_has_required_keys(self, mock_bench):
        from dartlab.quant.analyzer import technicalVerdict

        close = _sideways(200)
        df = self._make_df(close)
        result = technicalVerdict(df)
        for key in ("verdict", "score", "rsi", "aboveSma20", "aboveSma60", "bbPosition", "signals"):
            assert key in result

    @patch("dartlab.quant.analyzer._fetchBenchmark", return_value=None)
    def test_score_range(self, mock_bench):
        from dartlab.quant.analyzer import technicalVerdict

        close = _sideways(200)
        df = self._make_df(close)
        result = technicalVerdict(df)
        assert -4 <= result["score"] <= 4

    @patch("dartlab.quant.analyzer._fetchBenchmark", return_value=None)
    def test_signals_dict_structure(self, mock_bench):
        from dartlab.quant.analyzer import technicalVerdict

        close = _uptrend(200)
        df = self._make_df(close)
        result = technicalVerdict(df)
        signals = result["signals"]
        assert "goldenCross" in signals
        assert "rsiSignal" in signals
        assert "macdSignal" in signals


# ═══════════════════════════════════════════════════════════
# Signal generators
# ═══════════════════════════════════════════════════════════


class TestVcrossover:
    def test_detects_upward_cross(self):
        fast = np.array([1.0, 2.0, 4.0, 6.0], dtype=np.float64)
        slow = np.array([3.0, 3.0, 3.0, 3.0], dtype=np.float64)
        result = vcrossover(fast, slow)
        # Cross happens at index 2 (fast goes from 2<3 to 4>3)
        assert result[2] == 1

    def test_no_cross(self):
        fast = np.array([5.0, 6.0, 7.0], dtype=np.float64)
        slow = np.array([1.0, 1.0, 1.0], dtype=np.float64)
        result = vcrossover(fast, slow)
        # fast always above slow
        assert np.all(result == 0)

    def test_first_element_always_zero(self):
        fast = np.array([0.0, 5.0], dtype=np.float64)
        slow = np.array([10.0, 0.0], dtype=np.float64)
        result = vcrossover(fast, slow)
        assert result[0] == 0


class TestVcrossunder:
    def test_detects_downward_cross(self):
        fast = np.array([5.0, 4.0, 2.0, 1.0], dtype=np.float64)
        slow = np.array([3.0, 3.0, 3.0, 3.0], dtype=np.float64)
        result = vcrossunder(fast, slow)
        # Cross at index 2: fast goes from 4>3 to 2<3
        assert result[2] == -1


class TestVcross:
    def test_both_directions(self):
        fast = np.array([1.0, 2.0, 4.0, 5.0, 2.0, 1.0], dtype=np.float64)
        slow = np.array([3.0, 3.0, 3.0, 3.0, 3.0, 3.0], dtype=np.float64)
        result = vcross(fast, slow)
        # Up cross at idx 2 (prev 2<=3, now 4>3)
        assert result[2] == 1
        # Down cross at idx 4 (prev 5>=3, now 2<3)
        assert result[4] == -1


class TestVgoldenCross:
    def test_uptrend_generates_golden_cross(self):
        # Create prices that start flat then surge up
        flat = np.full(50, 100.0)
        rising = np.linspace(100, 200, 100)
        close = np.concatenate([flat, rising])
        result = vgoldenCross(close, fast=10, slow=30)
        # Should have at least one golden cross (+1)
        assert np.any(result == 1)

    def test_downtrend_generates_death_cross(self):
        flat = np.full(50, 200.0)
        falling = np.linspace(200, 100, 100)
        close = np.concatenate([flat, falling])
        result = vgoldenCross(close, fast=10, slow=30)
        # Should have at least one death cross (-1)
        assert np.any(result == -1)


class TestVrsiSignal:
    def test_oversold_recovery_signal(self):
        # RSI goes from 25 (oversold) to 35 (recovered)
        rsi = np.array([50.0, 40.0, 25.0, 35.0], dtype=np.float64)
        result = vrsiSignal(rsi, oversold=30.0, overbought=70.0)
        # At index 3, prev=25 <= 30 and current=35 > 30 -> +1
        assert result[3] == 1

    def test_overbought_reversal_signal(self):
        rsi = np.array([50.0, 65.0, 75.0, 65.0], dtype=np.float64)
        result = vrsiSignal(rsi, oversold=30.0, overbought=70.0)
        # At index 3, prev=75 >= 70 and current=65 < 70 -> -1
        assert result[3] == -1

    def test_no_signal_in_mid_range(self):
        rsi = np.array([45.0, 50.0, 55.0, 50.0], dtype=np.float64)
        result = vrsiSignal(rsi, oversold=30.0, overbought=70.0)
        assert np.all(result == 0)
