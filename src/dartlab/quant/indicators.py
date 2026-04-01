"""벡터화 기술적 지표 — 순수 NumPy 구현.

tradix에서 이식. 전체 가격 배열을 한 번에 처리하여 초고속 계산.

지표 25개:
    추세: vsma, vema, vmacd, vadx, vpsar, vsupertrend, vichimoku
    모멘텀: vrsi, vstochastic, vroc, vmomentum, vwilliamsR, vcci, vcmo
    변동성: vbollinger, vatr, vkeltner, vdonchian
    거래량: vobv, vmfi, vforceIndex

사용법::

    from dartlab.quant.indicators import vsma, vrsi, vmacd
    sma = vsma(close, period=20)
    rsi = vrsi(close, period=14)
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from numpy.typing import NDArray


def vsma(close: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """Compute Simple Moving Average using cumsum optimization.

    Args:
        close: Array of closing prices.
        period: Lookback window size.

    Returns:
        Array with SMA values. First (period-1) elements are NaN.
    """
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)

    cumsum = np.cumsum(close)
    result[period - 1 :] = (cumsum[period - 1 :] - np.concatenate([[0], cumsum[:-period]])) / period

    return result


def vema(close: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """Compute Exponential Moving Average.

    Args:
        close: Array of closing prices.
        period: Lookback window size. Smoothing factor = 2/(period+1).

    Returns:
        Array with EMA values. First (period-1) elements are NaN.
    """
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)

    alpha = 2.0 / (period + 1)
    result[period - 1] = np.mean(close[:period])

    for i in range(period, n):
        result[i] = alpha * close[i] + (1 - alpha) * result[i - 1]

    return result


def vrsi(close: NDArray[np.float64], period: int = 14) -> NDArray[np.float64]:
    """Compute Relative Strength Index using Wilder's smoothing.

    Args:
        close: Array of closing prices.
        period: RSI lookback period (default: 14).

    Returns:
        Array with RSI values (0-100). First `period` elements are NaN.
    """
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)

    deltas = np.diff(close, prepend=close[0])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avgGain = np.mean(gains[1 : period + 1])
    avgLoss = np.mean(losses[1 : period + 1])

    if avgLoss == 0:
        result[period] = 100.0
    else:
        rs = avgGain / avgLoss
        result[period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period + 1, n):
        avgGain = (avgGain * (period - 1) + gains[i]) / period
        avgLoss = (avgLoss * (period - 1) + losses[i]) / period

        if avgLoss == 0:
            result[i] = 100.0
        else:
            rs = avgGain / avgLoss
            result[i] = 100.0 - (100.0 / (1.0 + rs))

    return result


def vmacd(
    close: NDArray[np.float64], fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute MACD (Moving Average Convergence Divergence).

    Args:
        close: Array of closing prices.
        fast: Fast EMA period (default: 12).
        slow: Slow EMA period (default: 26).
        signal: Signal line EMA period (default: 9).

    Returns:
        Tuple of (macd_line, signal_line, histogram) arrays.
    """
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


def vbollinger(
    close: NDArray[np.float64], period: int = 20, std: float = 2.0
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute Bollinger Bands (upper, middle, lower).

    Args:
        close: Array of closing prices.
        period: SMA period for middle band (default: 20).
        std: Standard deviation multiplier (default: 2.0).

    Returns:
        Tuple of (upper_band, middle_band, lower_band) arrays.
    """
    n = len(close)
    middle = vsma(close, period)

    upper = np.full(n, np.nan, dtype=np.float64)
    lower = np.full(n, np.nan, dtype=np.float64)

    for i in range(period - 1, n):
        window = close[i - period + 1 : i + 1]
        stdDev = np.std(window, ddof=0)
        upper[i] = middle[i] + std * stdDev
        lower[i] = middle[i] - std * stdDev

    return upper, middle, lower


def vatr(
    high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], period: int = 14
) -> NDArray[np.float64]:
    """Compute Average True Range using Wilder's smoothing.

    Args:
        high: Array of high prices.
        low: Array of low prices.
        close: Array of closing prices.
        period: ATR lookback period (default: 14).

    Returns:
        Array with ATR values. First (period-1) elements are NaN.
    """
    n = len(close)

    tr = np.empty(n, dtype=np.float64)
    tr[0] = high[0] - low[0]

    hl = high[1:] - low[1:]
    hc = np.abs(high[1:] - close[:-1])
    lc = np.abs(low[1:] - close[:-1])
    tr[1:] = np.maximum(np.maximum(hl, hc), lc)

    atr = np.full(n, np.nan, dtype=np.float64)
    atr[period - 1] = np.mean(tr[:period])

    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    return atr


def vstochastic(
    high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], kPeriod: int = 14, dPeriod: int = 3
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Compute Stochastic Oscillator (%K and %D lines).

    Args:
        high: Array of high prices.
        low: Array of low prices.
        close: Array of closing prices.
        kPeriod: %K lookback period (default: 14).
        dPeriod: %D smoothing period (default: 3).

    Returns:
        Tuple of (%K, %D) arrays. Values range 0-100.
    """
    n = len(close)
    k = np.full(n, np.nan, dtype=np.float64)

    for i in range(kPeriod - 1, n):
        highestHigh = np.max(high[i - kPeriod + 1 : i + 1])
        lowestLow = np.min(low[i - kPeriod + 1 : i + 1])

        if highestHigh != lowestLow:
            k[i] = 100.0 * (close[i] - lowestLow) / (highestHigh - lowestLow)
        else:
            k[i] = 50.0

    d = vsma(k, dPeriod)

    return k, d


def vadx(
    high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], period: int = 14
) -> NDArray[np.float64]:
    """Compute Average Directional Index (ADX).

    Measures trend strength regardless of direction. Values above 25
    indicate a strong trend, below 20 indicate a weak/no trend.

    Args:
        high: Array of high prices.
        low: Array of low prices.
        close: Array of closing prices.
        period: ADX lookback period (default: 14).

    Returns:
        Array with ADX values (0-100). First (2*period-1) elements are NaN.
    """
    n = len(close)

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

    adx = np.full(n, np.nan, dtype=np.float64)
    adx[2 * period - 1] = np.mean(dx[period : 2 * period])

    for i in range(2 * period, n):
        adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period

    return adx


def vroc(close: NDArray[np.float64], period: int = 12) -> NDArray[np.float64]:
    """Compute Rate of Change (percentage price change over N periods).

    Args:
        close: Array of closing prices.
        period: Lookback period (default: 12).

    Returns:
        Array with ROC values in percentage. First `period` elements are NaN.
    """
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)

    prevClose = close[:-period]
    mask = prevClose != 0
    result[period:][mask] = ((close[period:][mask] - prevClose[mask]) / prevClose[mask]) * 100.0

    return result


def vmomentum(close: NDArray[np.float64], period: int = 10) -> NDArray[np.float64]:
    """Compute Price Momentum (absolute price change over N periods).

    Args:
        close: Array of closing prices.
        period: Lookback period (default: 10).

    Returns:
        Array with momentum values. First `period` elements are NaN.
    """
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    result[period:] = close[period:] - close[:-period]
    return result


# ── 추가 지표 (tradix strategy/indicators.py에서 벡터화 이식) ──


def vobv(close: NDArray[np.float64], volume: NDArray[np.float64]) -> NDArray[np.float64]:
    """On Balance Volume."""
    n = len(close)
    obv = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        if close[i] > close[i - 1]:
            obv[i] = obv[i - 1] + volume[i]
        elif close[i] < close[i - 1]:
            obv[i] = obv[i - 1] - volume[i]
        else:
            obv[i] = obv[i - 1]
    return obv


def vwilliamsR(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 14,
) -> NDArray[np.float64]:
    """Williams %R (-100~0)."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(period - 1, n):
        hh = np.max(high[i - period + 1 : i + 1])
        ll = np.min(low[i - period + 1 : i + 1])
        if hh != ll:
            result[i] = -100.0 * (hh - close[i]) / (hh - ll)
        else:
            result[i] = -50.0
    return result


def vcci(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 20,
) -> NDArray[np.float64]:
    """Commodity Channel Index."""
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


def vmfi(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    volume: NDArray[np.float64],
    period: int = 14,
) -> NDArray[np.float64]:
    """Money Flow Index (0~100)."""
    tp = (high + low + close) / 3
    mf = tp * volume
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(period, n):
        pos = 0.0
        neg = 0.0
        for j in range(i - period + 1, i + 1):
            if tp[j] > tp[j - 1]:
                pos += mf[j]
            elif tp[j] < tp[j - 1]:
                neg += mf[j]
        if neg == 0:
            result[i] = 100.0
        else:
            result[i] = 100.0 - 100.0 / (1.0 + pos / neg)
    return result


def vpsar(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    afStart: float = 0.02,
    afStep: float = 0.02,
    afMax: float = 0.2,
) -> NDArray[np.float64]:
    """Parabolic SAR."""
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
    """SuperTrend. Returns (supertrend, direction: +1=up, -1=down)."""
    atr = vatr(high, low, close, period)
    n = len(close)
    hl2 = (high + low) / 2
    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr
    st = np.full(n, np.nan, dtype=np.float64)
    direction = np.zeros(n, dtype=np.int8)
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


def vkeltner(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 20,
    atrPeriod: int = 10,
    multiplier: float = 2.0,
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Keltner Channel (upper, middle, lower)."""
    middle = vema(close, period)
    atr = vatr(high, low, close, atrPeriod)
    upper = middle + multiplier * atr
    lower = middle - multiplier * atr
    return upper, middle, lower


def vdonchian(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    period: int = 20,
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Donchian Channel (upper, middle, lower)."""
    n = len(high)
    upper = np.full(n, np.nan, dtype=np.float64)
    lower = np.full(n, np.nan, dtype=np.float64)
    for i in range(period - 1, n):
        upper[i] = np.max(high[i - period + 1 : i + 1])
        lower[i] = np.min(low[i - period + 1 : i + 1])
    middle = (upper + lower) / 2
    return upper, middle, lower


def vcmo(close: NDArray[np.float64], period: int = 14) -> NDArray[np.float64]:
    """Chande Momentum Oscillator (-100~+100)."""
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


def velderRay(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 13,
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Elder Ray (bull_power, bear_power)."""
    ema = vema(close, period)
    bull = high - ema
    bear = low - ema
    return bull, bear


def vforceIndex(
    close: NDArray[np.float64],
    volume: NDArray[np.float64],
    period: int = 13,
) -> NDArray[np.float64]:
    """Force Index (EMA smoothed)."""
    n = len(close)
    raw = np.zeros(n, dtype=np.float64)
    raw[1:] = (close[1:] - close[:-1]) * volume[1:]
    return vema(raw, period)
