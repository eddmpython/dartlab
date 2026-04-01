"""벡터화 기술적 지표 — 순수 NumPy 구현.

tradix에서 이식. 전체 가격 배열을 한 번에 처리하여 초고속 계산.

지표 45개:
    추세: vsma, vema, vwma, vdema, vtema, vhma, vvwma, vmacd, vadx, vpsar, vsupertrend
    모멘텀: vrsi, vstochastic, vstochasticRsi, vkdj, vroc, vmomentum, vwilliamsR, vcci, vcmo, vawesomeOscillator, vultimateOscillator
    변동성: vbollinger, vbollingerPercentB, vbollingerWidth, vatr, vkeltner, vdonchian, vulcer
    거래량: vobv, vmfi, vforceIndex, vadl, vchaikin, vemv, vnvi, vpvi, vpvt, vvwap, velderRay
    특수: vtrix, vdpo, vpivotPoints, vlinearRegression, vzigzag

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


# ── 이동평균 계열 확장 ──


def vwma(close: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Weighted Moving Average."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    weights = np.arange(1, period + 1, dtype=np.float64)
    wsum = weights.sum()
    for i in range(period - 1, n):
        result[i] = np.dot(close[i - period + 1 : i + 1], weights) / wsum
    return result


def vdema(close: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Double EMA."""
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
    """Triple EMA."""
    e1 = vema(close, period)
    v1 = e1[~np.isnan(e1)]
    e2 = vema(v1, period) if len(v1) >= period else np.array([])
    v2 = e2[~np.isnan(e2)]
    e3 = vema(v2, period) if len(v2) >= period else np.array([])
    result = np.full(len(close), np.nan, dtype=np.float64)
    # TEMA = 3*EMA1 - 3*EMA2 + EMA3 at matching indices
    idx1 = np.where(~np.isnan(e1))[0]
    if len(e3) > 0 and len(e2) > 0:
        off2 = len(idx1) - len(e2)
        off3 = len(idx1) - len(e2) + len(e2) - len(e3)
        for j in range(len(e3)):
            i = idx1[off3 + j]
            result[i] = 3 * e1[i] - 3 * e2[off2 + (off3 - off2) + j] + e3[j]
    return result


def vhma(close: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Hull Moving Average."""
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


def vvwma(
    close: NDArray[np.float64],
    volume: NDArray[np.float64],
    period: int = 20,
) -> NDArray[np.float64]:
    """Volume Weighted Moving Average."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(period - 1, n):
        w = close[i - period + 1 : i + 1]
        v = volume[i - period + 1 : i + 1]
        vs = v.sum()
        if vs > 0:
            result[i] = np.dot(w, v) / vs
    return result


# ── 오실레이터 확장 ──


def vvwap(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    volume: NDArray[np.float64],
) -> NDArray[np.float64]:
    """VWAP (Volume Weighted Average Price) — 누적."""
    tp = (high + low + close) / 3
    cumTPV = np.cumsum(tp * volume)
    cumV = np.cumsum(volume)
    result = np.where(cumV > 0, cumTPV / cumV, np.nan)
    return result.astype(np.float64)


def vstochasticRsi(
    close: NDArray[np.float64],
    rsiPeriod: int = 14,
    stochPeriod: int = 14,
    kPeriod: int = 3,
    dPeriod: int = 3,
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Stochastic RSI (%K, %D)."""
    rsi = vrsi(close, rsiPeriod)
    n = len(close)
    k = np.full(n, np.nan, dtype=np.float64)
    for i in range(rsiPeriod + stochPeriod - 1, n):
        window = rsi[i - stochPeriod + 1 : i + 1]
        valid = window[~np.isnan(window)]
        if len(valid) >= 2:
            hh = np.max(valid)
            ll = np.min(valid)
            if hh != ll:
                k[i] = 100 * (rsi[i] - ll) / (hh - ll)
            else:
                k[i] = 50
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
    """KDJ Indicator (K, D, J)."""
    rawK, _ = vstochastic(high, low, close, period, 1)
    k = vsma(rawK, kSmooth)
    d = vsma(k, dSmooth)
    j = 3 * k - 2 * d
    return k, d, j


def vawesomeOscillator(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    fastPeriod: int = 5,
    slowPeriod: int = 34,
) -> NDArray[np.float64]:
    """Awesome Oscillator."""
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
    """Ultimate Oscillator."""
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


# ── 변동성 확장 ──


def vulcer(close: NDArray[np.float64], period: int = 14) -> NDArray[np.float64]:
    """Ulcer Index — 하방 변동성."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(period - 1, n):
        window = close[i - period + 1 : i + 1]
        peak = np.maximum.accumulate(window)
        drawdown = ((window - peak) / peak * 100) ** 2
        result[i] = np.sqrt(np.mean(drawdown))
    return result


def vbollingerPercentB(
    close: NDArray[np.float64],
    period: int = 20,
    std: float = 2.0,
) -> NDArray[np.float64]:
    """Bollinger %B (0~1, 밴드 내 위치)."""
    upper, _, lower = vbollinger(close, period, std)
    rng = upper - lower
    result = np.where(rng > 0, (close - lower) / rng, np.nan)
    return result.astype(np.float64)


def vbollingerWidth(
    close: NDArray[np.float64],
    period: int = 20,
    std: float = 2.0,
) -> NDArray[np.float64]:
    """Bollinger Bandwidth (밴드 폭 / 중심)."""
    upper, middle, lower = vbollinger(close, period, std)
    result = np.where(middle > 0, (upper - lower) / middle, np.nan)
    return result.astype(np.float64)


# ── 거래량 확장 ──


def vadl(
    close: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], volume: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Accumulation/Distribution Line."""
    n = len(close)
    adl = np.zeros(n, dtype=np.float64)
    for i in range(n):
        hl = high[i] - low[i]
        if hl > 0:
            mfm = ((close[i] - low[i]) - (high[i] - close[i])) / hl
            adl[i] = (adl[i - 1] if i > 0 else 0) + mfm * volume[i]
        else:
            adl[i] = adl[i - 1] if i > 0 else 0
    return adl


def vchaikin(
    close: NDArray[np.float64],
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    volume: NDArray[np.float64],
    fastPeriod: int = 3,
    slowPeriod: int = 10,
) -> NDArray[np.float64]:
    """Chaikin Oscillator (ADL의 EMA 차이)."""
    adl = vadl(close, high, low, volume)
    return vema(adl, fastPeriod) - vema(adl, slowPeriod)


def vemv(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    volume: NDArray[np.float64],
    period: int = 14,
) -> NDArray[np.float64]:
    """Ease of Movement (EMA smoothed)."""
    n = len(high)
    raw = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        hl = high[i] - low[i]
        if hl > 0 and volume[i] > 0:
            dm = ((high[i] + low[i]) / 2) - ((high[i - 1] + low[i - 1]) / 2)
            box = volume[i] / hl
            raw[i] = dm / box if box > 0 else 0
    return vema(raw, period)


def vnvi(close: NDArray[np.float64], volume: NDArray[np.float64]) -> NDArray[np.float64]:
    """Negative Volume Index."""
    n = len(close)
    nvi = np.full(n, 1000.0, dtype=np.float64)
    for i in range(1, n):
        if volume[i] < volume[i - 1] and close[i - 1] > 0:
            nvi[i] = nvi[i - 1] * (1 + (close[i] - close[i - 1]) / close[i - 1])
        else:
            nvi[i] = nvi[i - 1]
    return nvi


def vpvi(close: NDArray[np.float64], volume: NDArray[np.float64]) -> NDArray[np.float64]:
    """Positive Volume Index."""
    n = len(close)
    pvi = np.full(n, 1000.0, dtype=np.float64)
    for i in range(1, n):
        if volume[i] > volume[i - 1] and close[i - 1] > 0:
            pvi[i] = pvi[i - 1] * (1 + (close[i] - close[i - 1]) / close[i - 1])
        else:
            pvi[i] = pvi[i - 1]
    return pvi


def vpvt(close: NDArray[np.float64], volume: NDArray[np.float64]) -> NDArray[np.float64]:
    """Price Volume Trend."""
    n = len(close)
    pvt = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        if close[i - 1] > 0:
            pvt[i] = pvt[i - 1] + volume[i] * (close[i] - close[i - 1]) / close[i - 1]
        else:
            pvt[i] = pvt[i - 1]
    return pvt


# ── 특수 지표 ──


def vtrix(
    close: NDArray[np.float64],
    period: int = 15,
    signalPeriod: int = 9,
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """TRIX + Signal."""
    e1 = vema(close, period)
    v1 = e1[~np.isnan(e1)]
    e2 = vema(v1, period) if len(v1) >= period else np.full(len(v1), np.nan)
    v2 = e2[~np.isnan(e2)]
    e3 = vema(v2, period) if len(v2) >= period else np.full(len(v2), np.nan)

    n = len(close)
    trix = np.full(n, np.nan, dtype=np.float64)
    # TRIX = pct change of triple EMA
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


def vdpo(close: NDArray[np.float64], period: int = 20) -> NDArray[np.float64]:
    """Detrended Price Oscillator."""
    sma = vsma(close, period)
    shift = period // 2 + 1
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    for i in range(shift + period - 1, n):
        if not np.isnan(sma[i - shift]):
            result[i] = close[i] - sma[i - shift]
    return result


def vpivotPoints(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
) -> Tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """Pivot Points (PP, R1, R2, R3, S1, S2, S3). 전일 기준."""
    n = len(close)
    pp = np.full(n, np.nan, dtype=np.float64)
    r1 = np.full(n, np.nan, dtype=np.float64)
    r2 = np.full(n, np.nan, dtype=np.float64)
    r3 = np.full(n, np.nan, dtype=np.float64)
    s1 = np.full(n, np.nan, dtype=np.float64)
    s2 = np.full(n, np.nan, dtype=np.float64)
    s3 = np.full(n, np.nan, dtype=np.float64)
    for i in range(1, n):
        p = (high[i - 1] + low[i - 1] + close[i - 1]) / 3
        pp[i] = p
        r1[i] = 2 * p - low[i - 1]
        s1[i] = 2 * p - high[i - 1]
        r2[i] = p + (high[i - 1] - low[i - 1])
        s2[i] = p - (high[i - 1] - low[i - 1])
        r3[i] = high[i - 1] + 2 * (p - low[i - 1])
        s3[i] = low[i - 1] - 2 * (high[i - 1] - p)
    return pp, r1, r2, r3, s1, s2, s3


def vlinearRegression(
    close: NDArray[np.float64],
    period: int = 20,
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Linear Regression (value, slope, r-squared)."""
    n = len(close)
    value = np.full(n, np.nan, dtype=np.float64)
    slope = np.full(n, np.nan, dtype=np.float64)
    rsq = np.full(n, np.nan, dtype=np.float64)
    x = np.arange(period, dtype=np.float64)
    xmean = x.mean()
    xvar = np.sum((x - xmean) ** 2)
    for i in range(period - 1, n):
        y = close[i - period + 1 : i + 1]
        ymean = y.mean()
        cov = np.sum((x - xmean) * (y - ymean))
        b = cov / xvar if xvar > 0 else 0
        a = ymean - b * xmean
        value[i] = a + b * (period - 1)
        slope[i] = b
        yhat = a + b * x
        ss_res = np.sum((y - yhat) ** 2)
        ss_tot = np.sum((y - ymean) ** 2)
        rsq[i] = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return value, slope, rsq


def vzigzag(
    close: NDArray[np.float64],
    threshold: float = 5.0,
) -> NDArray[np.float64]:
    """ZigZag (threshold % 이상 변화만 추적)."""
    n = len(close)
    result = np.full(n, np.nan, dtype=np.float64)
    result[0] = close[0]
    lastPivot = close[0]
    lastIdx = 0
    direction = 0  # 0=unknown, 1=up, -1=down
    for i in range(1, n):
        change = (close[i] - lastPivot) / lastPivot * 100 if lastPivot > 0 else 0
        if direction == 0:
            if abs(change) >= threshold:
                direction = 1 if change > 0 else -1
                result[i] = close[i]
                lastPivot = close[i]
                lastIdx = i
        elif direction == 1:
            if close[i] > lastPivot:
                result[lastIdx] = np.nan
                result[i] = close[i]
                lastPivot = close[i]
                lastIdx = i
            elif change <= -threshold:
                direction = -1
                result[i] = close[i]
                lastPivot = close[i]
                lastIdx = i
        else:
            if close[i] < lastPivot:
                result[lastIdx] = np.nan
                result[i] = close[i]
                lastPivot = close[i]
                lastIdx = i
            elif change >= threshold:
                direction = 1
                result[i] = close[i]
                lastPivot = close[i]
                lastIdx = i
    return result
