"""Momentum and oscillator indicators.

Capabilities:
    - RSI, stochastic, ROC, Williams %R, CCI, CMO, KDJ, AO, UO, and DPO calculations.

Args:
    Functions accept aligned NumPy price arrays and lookback/smoothing parameters.

Returns:
    Momentum indicator arrays or tuples of arrays aligned to the input length.

Example:
    >>> rsi = vrsi(close, period=14)

Guide:
    Use this module for price-speed and oscillator signals. Trend averages live in
    ``trend`` and are imported only as pure math dependencies.

SeeAlso:
    ``trend.vsma`` for smoothing and ``volume`` for volume-confirmed momentum.

Requires:
    NumPy arrays with sufficient lookback history.

AIContext:
    Quant screeners and signal generators use these functions as deterministic L1.5
    momentum primitives.

LLM Specifications:
    AntiPatterns: Do not fetch OHLCV, infer ticker metadata, or call scan APIs here.
    OutputSchema: NDArray[np.float64] or tuple outputs with input-series length.
    Prerequisites: Caller supplies cleaned close/high/low arrays.
    Freshness: Pure calculation; output freshness equals input freshness.
    Dataflow: OHLC arrays -> oscillator formula -> vectorized signal arrays.
    TargetMarkets: Any liquid price series with OHLC data.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from dartlab.core.indicators.trend import vsma


def vrsi(close: NDArray[np.float64], period: int = 14) -> NDArray[np.float64]:
    """Compute Relative Strength Index using Wilder smoothing."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    if period < 1:
        raise ValueError("period must be at least 1")
    if n <= period:
        return result
    deltas = np.diff(close, prepend=close[0])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avgGain = np.mean(gains[1 : period + 1])
    avgLoss = np.mean(losses[1 : period + 1])
    result[period] = 100.0 if avgLoss == 0 else 100.0 - (100.0 / (1.0 + avgGain / avgLoss))
    for i in range(period + 1, n):
        avgGain = (avgGain * (period - 1) + gains[i]) / period
        avgLoss = (avgLoss * (period - 1) + losses[i]) / period
        result[i] = 100.0 if avgLoss == 0 else 100.0 - (100.0 / (1.0 + avgGain / avgLoss))
    return result


def vstochastic(
    high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], kPeriod: int = 14, dPeriod: int = 3
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Compute Stochastic Oscillator K and D lines."""
    n = len(close)
    k = np.full(n, np.nan, dtype=np.float64)
    for i in range(kPeriod - 1, n):
        highestHigh = np.max(high[i - kPeriod + 1 : i + 1])
        lowestLow = np.min(low[i - kPeriod + 1 : i + 1])
        k[i] = 100.0 * (close[i] - lowestLow) / (highestHigh - lowestLow) if highestHigh != lowestLow else 50.0
    d = vsma(k, dPeriod)
    return k, d


def vroc(close: NDArray[np.float64], period: int = 12) -> NDArray[np.float64]:
    """Compute Rate of Change."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    prevClose = close[:-period]
    mask = prevClose != 0
    result[period:][mask] = ((close[period:][mask] - prevClose[mask]) / prevClose[mask]) * 100.0
    return result


def vmomentum(close: NDArray[np.float64], period: int = 10) -> NDArray[np.float64]:
    """Compute price momentum."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    result[period:] = close[period:] - close[:-period]
    return result


def vwilliamsR(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 14,
) -> NDArray[np.float64]:
    """Compute Williams %R."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(period - 1, n):
        hh = np.max(high[i - period + 1 : i + 1])
        ll = np.min(low[i - period + 1 : i + 1])
        result[i] = -100.0 * (hh - close[i]) / (hh - ll) if hh != ll else -50.0
    return result


def vcci(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 20,
) -> NDArray[np.float64]:
    """Compute Commodity Channel Index."""
    tp = (high + low + close) / 3
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(period - 1, n):
        window = tp[i - period + 1 : i + 1]
        mean = np.mean(window)
        mad = np.mean(np.abs(window - mean))
        if mad != 0:
            result[i] = (tp[i] - mean) / (0.015 * mad)
    return result


def vcmo(close: NDArray[np.float64], period: int = 14) -> NDArray[np.float64]:
    """Compute Chande Momentum Oscillator."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(period, n):
        gains = 0.0
        losses = 0.0
        for j in range(i - period + 1, i + 1):
            diff = close[j] - close[j - 1]
            if diff > 0:
                gains += diff
            else:
                losses += abs(diff)
        total = gains + losses
        if total != 0:
            result[i] = 100.0 * (gains - losses) / total
    return result


def vstochasticRsi(
    close: NDArray[np.float64],
    rsiPeriod: int = 14,
    stochPeriod: int = 14,
    kPeriod: int = 3,
    dPeriod: int = 3,
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Compute Stochastic RSI K and D lines."""
    rsi = vrsi(close, rsiPeriod)
    n = len(close)
    k = np.full(n, np.nan, dtype=np.float64)
    for i in range(rsiPeriod + stochPeriod - 1, n):
        window = rsi[i - stochPeriod + 1 : i + 1]
        valid = window[~np.isnan(window)]
        if len(valid) >= 2:
            hh = np.max(valid)
            ll = np.min(valid)
            k[i] = 100 * (rsi[i] - ll) / (hh - ll) if hh != ll else 50
    d = vsma(k, dPeriod)
    return k, d


def vkdj(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 9,
    kSmooth: int = 3,
    dSmooth: int = 3,
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute KDJ indicator."""
    rawK, _ = vstochastic(high, low, close, period, 1)
    k = vsma(rawK, kSmooth)
    d = vsma(k, dSmooth)
    j = 3 * k - 2 * d
    return k, d, j


def vawesomeOscillator(
    high: NDArray[np.float64], low: NDArray[np.float64], fastPeriod: int = 5, slowPeriod: int = 34
) -> NDArray[np.float64]:
    """Compute Awesome Oscillator."""
    midpoint = (high + low) / 2
    return vsma(midpoint, fastPeriod) - vsma(midpoint, slowPeriod)


def vultimateOscillator(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    short: int = 7,
    medium: int = 14,
    long: int = 28,
) -> NDArray[np.float64]:
    """Compute Ultimate Oscillator."""
    n = len(close)
    bp = np.zeros(n, dtype=np.float64)
    tr = np.zeros(n, dtype=np.float64)
    bp[0] = close[0] - low[0]
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        bp[i] = close[i] - min(low[i], close[i - 1])
        tr[i] = max(high[i], close[i - 1]) - min(low[i], close[i - 1])
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(long - 1, n):
        s_tr = tr[i - short + 1 : i + 1].sum()
        m_tr = tr[i - medium + 1 : i + 1].sum()
        l_tr = tr[i - long + 1 : i + 1].sum()
        if s_tr > 0 and m_tr > 0 and l_tr > 0:
            a1 = bp[i - short + 1 : i + 1].sum() / s_tr
            a2 = bp[i - medium + 1 : i + 1].sum() / m_tr
            a3 = bp[i - long + 1 : i + 1].sum() / l_tr
            result[i] = 100 * (4 * a1 + 2 * a2 + a3) / 7
    return result


def vdpo(close: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Compute Detrended Price Oscillator."""
    sma = vsma(close, period)
    shift = period // 2 + 1
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(shift + period - 1, n):
        if not np.isnan(sma[i - shift]):
            result[i] = close[i] - sma[i - shift]
    return result
