"""Trend and moving-average technical indicators.

Capabilities:
    - Moving averages, trend strength, trend-following stops, and MACD/TRIX style
      direction indicators.

Args:
    Functions accept aligned NumPy price arrays plus period or smoothing parameters.

Returns:
    NumPy arrays, or tuples of arrays, aligned to the input series length.

Example:
    >>> trend = vema(close, period=20)

Guide:
    Keep trend primitives pure. If an indicator needs market data, fetch it before
    calling this module.

SeeAlso:
    ``momentum`` for oscillators and ``channels`` for bands derived from averages.

Requires:
    NumPy arrays with enough history for the requested period.

AIContext:
    Quant layers use this module as the stable L1.5 trend primitive catalog.

LLM Specifications:
    AntiPatterns: Do not import gather, providers, scan, frame, or Company facade here.
    OutputSchema: NDArray[np.float64] or tuple outputs with input-series length.
    Prerequisites: Caller validates data alignment and missing values.
    Freshness: Pure calculation; no time-sensitive data access.
    Dataflow: OHLCV arrays -> trend function -> vectorized indicator arrays.
    TargetMarkets: Any OHLCV market series.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from numpy.typing import NDArray


def vsma(close: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """Compute Simple Moving Average over a rolling window.

    누적합 방식은 NaN 하나가 이후 전부를 오염시킨다. 실제로 그 때문에 %K 로 시작하는
    입력을 받는 소비자가 통째로 죽어 있었다. %K 는 언제나 앞쪽 `kPeriod-1` 개가 NaN
    이므로 그것을 평활하는 %D, KDJ 세 출력이 전 구간 NaN 이었다. 창 단위 평균으로
    바꾸면 NaN 이 그 창에만 머문다.

    정상 입력에서 값은 사실상 같다. 5 만 봉에서 최대 차이가 1e-9 수준이고 부동소수
    오차가 누적되지 않는 쪽이 오히려 더 정확하다.
    """

    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    if period < 1:
        raise ValueError("period must be at least 1")
    if n < period:
        return result
    result[period - 1 :] = sliding_window_view(close, period).mean(axis=1)
    return result


def vema(close: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """Compute Exponential Moving Average."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    if period < 1:
        raise ValueError("period must be at least 1")
    if n < period:
        return result
    alpha = 2.0 / (period + 1)
    result[period - 1] = np.mean(close[:period])
    for i in range(period, n):
        result[i] = alpha * close[i] + (1 - alpha) * result[i - 1]
    return result


def vmacd(
    close: NDArray[np.float64], fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute MACD line, signal line, and histogram."""
    fastEma = vema(close, fast)
    slowEma = vema(close, slow)
    macdLine = fastEma - slowEma
    n = len(close)
    signalLine = np.full(n, np.nan, dtype=np.float64)
    alpha = 2.0 / (signal + 1)
    startIdx = slow - 1 + signal - 1
    if startIdx < n:
        validMacd = macdLine[slow - 1 : startIdx + 1]
        validMacd = validMacd[~np.isnan(validMacd)]
        if len(validMacd) > 0:
            signalLine[startIdx] = np.mean(validMacd)
        for i in range(startIdx + 1, n):
            if not np.isnan(macdLine[i]) and not np.isnan(signalLine[i - 1]):
                signalLine[i] = alpha * macdLine[i] + (1 - alpha) * signalLine[i - 1]
    histogram = macdLine - signalLine
    return macdLine, signalLine, histogram


def vadx(
    high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], period: int = 14
) -> NDArray[np.float64]:
    """Compute Average Directional Index."""
    n = len(close)
    adx = np.full(n, np.nan, dtype=np.float64)
    if period < 1:
        raise ValueError("period must be at least 1")
    if n < 2 * period:
        return adx
    upMove = np.diff(high, prepend=high[0])
    downMove = -np.diff(low, prepend=low[0])
    plusDm = np.where((upMove > downMove) & (upMove > 0), upMove, 0)
    minusDm = np.where((downMove > upMove) & (downMove > 0), downMove, 0)
    tr = np.empty(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    hl = high[1:] - low[1:]
    hc = np.abs(high[1:] - close[:-1])
    lc = np.abs(low[1:] - close[:-1])
    tr[1:] = np.maximum(np.maximum(hl, hc), lc)
    smoothedPlusDm = np.zeros(n, dtype=np.float64)
    smoothedMinusDm = np.zeros(n, dtype=np.float64)
    smoothedTr = np.zeros(n, dtype=np.float64)
    smoothedPlusDm[period] = np.sum(plusDm[1 : period + 1])
    smoothedMinusDm[period] = np.sum(minusDm[1 : period + 1])
    smoothedTr[period] = np.sum(tr[1 : period + 1])
    for i in range(period + 1, n):
        smoothedPlusDm[i] = smoothedPlusDm[i - 1] - smoothedPlusDm[i - 1] / period + plusDm[i]
        smoothedMinusDm[i] = smoothedMinusDm[i - 1] - smoothedMinusDm[i - 1] / period + minusDm[i]
        smoothedTr[i] = smoothedTr[i - 1] - smoothedTr[i - 1] / period + tr[i]
    plusDi = np.zeros(n, dtype=np.float64)
    minusDi = np.zeros(n, dtype=np.float64)
    dx = np.zeros(n, dtype=np.float64)
    mask = smoothedTr[period:] != 0
    plusDi[period:][mask] = 100.0 * smoothedPlusDm[period:][mask] / smoothedTr[period:][mask]
    minusDi[period:][mask] = 100.0 * smoothedMinusDm[period:][mask] / smoothedTr[period:][mask]
    diSum = plusDi + minusDi
    diSumMask = diSum != 0
    dx[diSumMask] = 100.0 * np.abs(plusDi[diSumMask] - minusDi[diSumMask]) / diSum[diSumMask]
    adx[2 * period - 1] = np.mean(dx[period : 2 * period])
    for i in range(2 * period, n):
        adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period
    return adx


def vpsar(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    afStart: float = 0.02,
    afStep: float = 0.02,
    afMax: float = 0.2,
) -> NDArray[np.float64]:
    """Compute Parabolic SAR."""
    n = len(high)
    psar = np.full(n, np.nan, dtype=np.float64)
    if n < 2:
        return psar
    bull = True
    af = afStart
    ep = high[0]
    psar[0] = low[0]
    for i in range(1, n):
        prev = psar[i - 1]
        psar[i] = prev + af * (ep - prev)
        if bull:
            if low[i] < psar[i]:
                bull = False
                psar[i] = ep
                af = afStart
                ep = low[i]
            else:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + afStep, afMax)
                psar[i] = min(psar[i], low[i - 1])
                if i >= 2:
                    psar[i] = min(psar[i], low[i - 2])
        else:
            if high[i] > psar[i]:
                bull = True
                psar[i] = ep
                af = afStart
                ep = high[i]
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + afStep, afMax)
                psar[i] = max(psar[i], high[i - 1])
                if i >= 2:
                    psar[i] = max(psar[i], high[i - 2])
    return psar


def vsupertrend(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 10,
    multiplier: float = 3.0,
) -> Tuple[NDArray[np.float64], NDArray[np.int8]]:
    """Compute SuperTrend and direction."""
    from dartlab.core.indicators.volatility import vatr

    atr = vatr(high, low, close, period)
    n = len(close)
    hl2 = (high + low) / 2
    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr
    st = np.full(n, np.nan, dtype=np.float64)
    direction = np.zeros(n, dtype=np.int8)
    if period < 1:
        raise ValueError("period must be at least 1")
    if n < period:
        return st, direction
    st[period - 1] = upper[period - 1]
    direction[period - 1] = -1
    for i in range(period, n):
        if np.isnan(upper[i]):
            continue
        if close[i - 1] <= st[i - 1]:
            st[i] = min(upper[i], st[i - 1]) if not np.isnan(st[i - 1]) else upper[i]
            direction[i] = -1
            if close[i] > st[i]:
                st[i] = lower[i]
                direction[i] = 1
        else:
            st[i] = max(lower[i], st[i - 1]) if not np.isnan(st[i - 1]) else lower[i]
            direction[i] = 1
            if close[i] < st[i]:
                st[i] = upper[i]
                direction[i] = -1
    return st, direction


def vwma(close: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Compute Weighted Moving Average."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    weights = np.arange(1, period + 1, dtype=np.float64)
    wsum = weights.sum()
    for i in range(period - 1, n):
        result[i] = np.dot(close[i - period + 1 : i + 1], weights) / wsum
    return result


def vdema(close: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Compute Double EMA."""
    e1 = vema(close, period)
    e2 = vema(e1[~np.isnan(e1)], period)
    result = np.full(len(close), np.nan, dtype=np.float64)
    valid = ~np.isnan(e1)
    idx = np.where(valid)[0]
    if len(e2) <= len(idx):
        offset = len(idx) - len(e2)
        for j in range(len(e2)):
            i = idx[offset + j]
            result[i] = 2 * e1[i] - e2[j]
    return result


def vtema(close: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Compute Triple EMA."""
    e1 = vema(close, period)
    v1 = e1[~np.isnan(e1)]
    e2 = vema(v1, period) if len(v1) >= period else np.array([])
    v2 = e2[~np.isnan(e2)]
    e3 = vema(v2, period) if len(v2) >= period else np.array([])
    result = np.full(len(close), np.nan, dtype=np.float64)
    idx1 = np.where(~np.isnan(e1))[0]
    if len(e3) > 0 and len(e2) > 0:
        off2 = len(idx1) - len(e2)
        off3 = len(idx1) - len(e2) + len(e2) - len(e3)
        for j in range(len(e3)):
            i = idx1[off3 + j]
            result[i] = 3 * e1[i] - 3 * e2[off2 + (off3 - off2) + j] + e3[j]
    return result


def vhma(close: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Compute Hull Moving Average."""
    half = vwma(close, period // 2) if period // 2 > 0 else close.copy()
    full = vwma(close, period)
    diff = 2 * half - full
    sqrt_p = max(int(np.sqrt(period)), 1)
    valid = diff[~np.isnan(diff)]
    if len(valid) < sqrt_p:
        return np.full(len(close), np.nan, dtype=np.float64)
    hma_valid = vwma(valid, sqrt_p)
    result = np.full(len(close), np.nan, dtype=np.float64)
    idx = np.where(~np.isnan(diff))[0]
    offset = len(idx) - len(hma_valid)
    for j in range(len(hma_valid)):
        result[idx[offset + j]] = hma_valid[j]
    return result


def vvwma(close: NDArray[np.float64], volume: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Compute Volume Weighted Moving Average."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(period - 1, n):
        w = close[i - period + 1 : i + 1]
        v = volume[i - period + 1 : i + 1]
        vs = v.sum()
        if vs > 0:
            result[i] = np.dot(w, v) / vs
    return result


def vtrix(
    close: NDArray[np.float64], period: int = 15, signalPeriod: int = 9
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Compute TRIX and signal line."""
    e1 = vema(close, period)
    v1 = e1[~np.isnan(e1)]
    e2 = vema(v1, period) if len(v1) >= period else np.full(len(v1), np.nan)
    v2 = e2[~np.isnan(e2)]
    e3 = vema(v2, period) if len(v2) >= period else np.full(len(v2), np.nan)
    n = len(close)
    trix = np.full(n, np.nan, dtype=np.float64)
    idx1 = np.where(~np.isnan(e1))[0]
    if len(e3) > 1:
        for j in range(1, len(e3)):
            if e3[j - 1] != 0:
                offset = len(idx1) - len(e2) + len(e2) - len(e3)
                i = idx1[offset + j] if offset + j < len(idx1) else n - 1
                trix[i] = (e3[j] - e3[j - 1]) / e3[j - 1] * 100
    sig = vema(trix[~np.isnan(trix)], signalPeriod) if np.any(~np.isnan(trix)) else np.array([])
    signal = np.full(n, np.nan, dtype=np.float64)
    trix_idx = np.where(~np.isnan(trix))[0]
    if len(sig) > 0 and len(trix_idx) > 0:
        offset = len(trix_idx) - len(sig)
        for j in range(len(sig)):
            if offset + j < len(trix_idx):
                signal[trix_idx[offset + j]] = sig[j]
    return trix, signal
