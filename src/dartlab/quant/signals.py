"""벡터화 신호 발생기 — 순수 NumPy 구현.

tradix에서 이식. int8 배열 반환: 1=매수, -1=매도, 0=신호없음.

신호 9개:
    vcrossover, vcrossunder, vcross,
    vgoldenCross, vrsiSignal, vmacdSignal,
    vbollingerSignal, vbreakoutSignal, vTrendFilter
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from dartlab.quant.indicators import vbollinger, vmacd, vsma


def vcrossover(fast: NDArray[np.float64], slow: NDArray[np.float64]) -> NDArray[np.int8]:
    """상향 돌파 감지. 1=크로스오버, 0=없음."""
    n = len(fast)
    signals = np.zeros(n, dtype=np.int8)
    prevFast = np.roll(fast, 1)
    prevSlow = np.roll(slow, 1)
    cross = (prevFast <= prevSlow) & (fast > slow)
    cross[0] = False
    cross = cross & ~np.isnan(fast) & ~np.isnan(slow) & ~np.isnan(prevFast) & ~np.isnan(prevSlow)
    signals[cross] = 1
    return signals


def vcrossunder(fast: NDArray[np.float64], slow: NDArray[np.float64]) -> NDArray[np.int8]:
    """하향 돌파 감지. -1=크로스언더, 0=없음."""
    n = len(fast)
    signals = np.zeros(n, dtype=np.int8)
    prevFast = np.roll(fast, 1)
    prevSlow = np.roll(slow, 1)
    cross = (prevFast >= prevSlow) & (fast < slow)
    cross[0] = False
    cross = cross & ~np.isnan(fast) & ~np.isnan(slow) & ~np.isnan(prevFast) & ~np.isnan(prevSlow)
    signals[cross] = -1
    return signals


def vcross(fast: NDArray[np.float64], slow: NDArray[np.float64]) -> NDArray[np.int8]:
    """양방향 돌파. +1=상향, -1=하향, 0=없음."""
    n = len(fast)
    signals = np.zeros(n, dtype=np.int8)
    prevFast = np.roll(fast, 1)
    prevSlow = np.roll(slow, 1)
    valid = ~np.isnan(fast) & ~np.isnan(slow) & ~np.isnan(prevFast) & ~np.isnan(prevSlow)
    valid[0] = False
    signals[(valid) & (prevFast <= prevSlow) & (fast > slow)] = 1
    signals[(valid) & (prevFast >= prevSlow) & (fast < slow)] = -1
    return signals


def vgoldenCross(close: NDArray[np.float64], fast: int = 10, slow: int = 30) -> NDArray[np.int8]:
    """골든크로스(+1) / 데스크로스(-1)."""
    return vcross(vsma(close, fast), vsma(close, slow))


def vrsiSignal(rsi: NDArray[np.float64], oversold: float = 30.0, overbought: float = 70.0) -> NDArray[np.int8]:
    """RSI 과매도 회복(+1) / 과매수 반전(-1)."""
    n = len(rsi)
    signals = np.zeros(n, dtype=np.int8)
    prevRsi = np.roll(rsi, 1)
    valid = ~np.isnan(rsi) & ~np.isnan(prevRsi)
    valid[0] = False
    signals[(valid) & (prevRsi <= oversold) & (rsi > oversold)] = 1
    signals[(valid) & (prevRsi >= overbought) & (rsi < overbought)] = -1
    return signals


def vmacdSignal(close: NDArray[np.float64], fast: int = 12, slow: int = 26, signal: int = 9) -> NDArray[np.int8]:
    """MACD/Signal 크로스."""
    macdLine, signalLine, _ = vmacd(close, fast, slow, signal)
    return vcross(macdLine, signalLine)


def vbollingerSignal(close: NDArray[np.float64], period: int = 20, std: float = 2.0) -> NDArray[np.int8]:
    """볼린저밴드 하단 반등(+1) / 상단 돌파(-1)."""
    upper, _, lower = vbollinger(close, period, std)
    n = len(close)
    signals = np.zeros(n, dtype=np.int8)
    prevClose = np.roll(close, 1)
    prevLower = np.roll(lower, 1)
    valid = ~np.isnan(upper) & ~np.isnan(lower)
    valid[0] = False
    signals[(valid) & (prevClose <= prevLower) & (close > lower)] = 1
    signals[(valid) & (close >= upper)] = -1
    return signals


def vbreakoutSignal(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 20,
) -> NDArray[np.int8]:
    """채널 돌파 (Turtle Trading). 상방(+1) / 하방(-1)."""
    n = len(close)
    signals = np.zeros(n, dtype=np.int8)
    for i in range(period, n):
        hh = np.max(high[i - period : i])
        ll = np.min(low[i - period : i])
        if close[i] > hh:
            signals[i] = 1
        elif close[i] < ll:
            signals[i] = -1
    return signals


def vTrendFilter(
    close: NDArray[np.float64],
    sma: NDArray[np.float64],
    adx: NDArray[np.float64],
    signals: NDArray[np.int8],
    adxThreshold: float = 25.0,
) -> NDArray[np.int8]:
    """ADX 추세 필터. 약한 추세 신호 제거."""
    n = len(close)
    filtered = np.zeros(n, dtype=np.int8)
    valid = ~np.isnan(sma) & ~np.isnan(adx)
    strong = valid & (adx >= adxThreshold)
    filtered[(strong) & (signals == 1) & (close > sma)] = 1
    filtered[(strong) & (signals == -1) & (close < sma)] = -1
    return filtered
