"""Volatility and range-risk indicators.

Capabilities:
    - Average True Range and downside drawdown-risk volatility calculations.

Args:
    Functions accept aligned NumPy high/low/close arrays and lookback periods.

Returns:
    Volatility arrays aligned to the input series length.

Example:
    >>> atr = vatr(high, low, close, period=14)

Guide:
    Keep range-risk formulas here so channels and trend stops can depend on one
    volatility source.

SeeAlso:
    ``channels`` for band construction and ``trend.vsupertrend`` for ATR-based stops.

Requires:
    NumPy arrays with aligned OHLC observations.

AIContext:
    Higher layers use this module to price risk without importing scan or provider code.

LLM Specifications:
    AntiPatterns: Do not normalize data, fetch prices, or choose periods based on ticker.
    OutputSchema: NDArray[np.float64] with NaN warmup regions.
    Prerequisites: Caller handles missing values and period selection.
    Freshness: Pure calculation; no external freshness source.
    Dataflow: OHLC arrays -> volatility formula -> risk arrays.
    TargetMarkets: Any OHLC market series.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def vatr(
    high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], period: int = 14
) -> NDArray[np.float64]:
    """Compute Average True Range using Wilder smoothing."""
    n = len(close)
    atr = np.full(n, np.nan, dtype=np.float64)
    if period < 1:
        raise ValueError("period must be at least 1")
    if n < period:
        return atr
    tr = np.empty(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    hl = high[1:] - low[1:]
    hc = np.abs(high[1:] - close[:-1])
    lc = np.abs(low[1:] - close[:-1])
    tr[1:] = np.maximum(np.maximum(hl, hc), lc)
    atr[period - 1] = np.mean(tr[:period])
    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def vulcer(close: NDArray[np.float64], period: int = 14) -> NDArray[np.float64]:
    """Compute Ulcer Index for downside volatility."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(period - 1, n):
        window = close[i - period + 1 : i + 1]
        peak = np.maximum.accumulate(window)
        drawdown = ((window - peak) / peak * 100) ** 2
        result[i] = np.sqrt(np.mean(drawdown))
    return result
