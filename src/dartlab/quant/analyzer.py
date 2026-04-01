"""종합 기술적 분석 — 25개 지표 계산 + 판단(강세/중립/약세).

OHLCV DataFrame → 지표 DataFrame + 종합 판단 dict.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

from dartlab.quant import indicators as ind
from dartlab.quant import signals as sig


def enrichWithIndicators(df: pl.DataFrame) -> pl.DataFrame:
    """OHLCV DataFrame에 25개 기술적 지표를 추가.

    Args:
        df: date, open, high, low, close, volume 컬럼 필수.

    Returns:
        원본 + 지표 컬럼이 추가된 DataFrame.
    """
    close = df["close"].to_numpy().astype(np.float64)
    high = df["high"].to_numpy().astype(np.float64)
    low = df["low"].to_numpy().astype(np.float64)
    volume = df["volume"].to_numpy().astype(np.float64) if "volume" in df.columns else np.zeros(len(close))

    # 추세
    sma20 = ind.vsma(close, 20)
    sma60 = ind.vsma(close, 60)
    sma120 = ind.vsma(close, 120)
    ema12 = ind.vema(close, 12)
    ema26 = ind.vema(close, 26)
    macd_line, macd_signal, macd_hist = ind.vmacd(close)
    adx14 = ind.vadx(high, low, close, 14)
    psar = ind.vpsar(high, low)
    st, st_dir = ind.vsupertrend(high, low, close)

    # 모멘텀
    rsi14 = ind.vrsi(close, 14)
    stoch_k, stoch_d = ind.vstochastic(high, low, close)
    roc12 = ind.vroc(close, 12)
    mom10 = ind.vmomentum(close, 10)
    willR = ind.vwilliamsR(high, low, close, 14)
    cci20 = ind.vcci(high, low, close, 20)
    cmo14 = ind.vcmo(close, 14)

    # 변동성
    bb_upper, bb_middle, bb_lower = ind.vbollinger(close, 20, 2.0)
    atr14 = ind.vatr(high, low, close, 14)
    kelt_upper, kelt_middle, kelt_lower = ind.vkeltner(high, low, close)
    don_upper, don_middle, don_lower = ind.vdonchian(high, low, 20)

    # 거래량
    obv = ind.vobv(close, volume)
    mfi14 = ind.vmfi(high, low, close, volume, 14)
    force13 = ind.vforceIndex(close, volume, 13)
    bull, bear = ind.velderRay(high, low, close, 13)

    return df.with_columns([
        # 추세
        pl.Series("sma20", sma20), pl.Series("sma60", sma60), pl.Series("sma120", sma120),
        pl.Series("ema12", ema12), pl.Series("ema26", ema26),
        pl.Series("macd", macd_line), pl.Series("macdSignal", macd_signal), pl.Series("macdHist", macd_hist),
        pl.Series("adx", adx14), pl.Series("psar", psar),
        pl.Series("supertrend", st), pl.Series("stDirection", st_dir),
        # 모멘텀
        pl.Series("rsi", rsi14),
        pl.Series("stochK", stoch_k), pl.Series("stochD", stoch_d),
        pl.Series("roc", roc12), pl.Series("momentum", mom10),
        pl.Series("williamsR", willR), pl.Series("cci", cci20), pl.Series("cmo", cmo14),
        # 변동성
        pl.Series("bbUpper", bb_upper), pl.Series("bbLower", bb_lower),
        pl.Series("atr", atr14),
        pl.Series("keltUpper", kelt_upper), pl.Series("keltLower", kelt_lower),
        pl.Series("donchianUpper", don_upper), pl.Series("donchianLower", don_lower),
        # 거래량
        pl.Series("obv", obv), pl.Series("mfi", mfi14),
        pl.Series("forceIndex", force13),
        pl.Series("bullPower", bull), pl.Series("bearPower", bear),
    ])


def technicalVerdict(df: pl.DataFrame) -> dict[str, Any]:
    """OHLCV → 종합 기술적 판단.

    Returns:
        dict with keys: verdict(강세/중립/약세), score(-4~+4),
        rsi, aboveSma20, aboveSma60, bbPosition, signals, ...
    """
    close = df["close"].to_numpy().astype(np.float64)
    high = df["high"].to_numpy().astype(np.float64)
    low = df["low"].to_numpy().astype(np.float64)

    rsi = ind.vrsi(close, 14)
    sma20 = ind.vsma(close, 20)
    sma60 = ind.vsma(close, 60)
    bb_upper, _, bb_lower = ind.vbollinger(close)
    adx = ind.vadx(high, low, close)

    # 현재 값
    last_rsi = float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0
    last_close = float(close[-1])
    above20 = bool(last_close > sma20[-1]) if not np.isnan(sma20[-1]) else None
    above60 = bool(last_close > sma60[-1]) if not np.isnan(sma60[-1]) else None
    last_adx = float(adx[-1]) if not np.isnan(adx[-1]) else None

    # BB 위치
    bb_pos = None
    if not np.isnan(bb_upper[-1]) and not np.isnan(bb_lower[-1]):
        rng = bb_upper[-1] - bb_lower[-1]
        if rng > 0:
            bb_pos = round((last_close - bb_lower[-1]) / rng * 100, 1)

    # 점수 (-4 ~ +4)
    score = 0
    if last_rsi < 30:
        score += 2
    elif last_rsi < 40:
        score += 1
    elif last_rsi > 70:
        score -= 2
    elif last_rsi > 60:
        score -= 1
    if above20:
        score += 1
    elif above20 is not None:
        score -= 1
    if above60:
        score += 1
    elif above60 is not None:
        score -= 1

    if score >= 2:
        verdict = "강세"
    elif score <= -2:
        verdict = "약세"
    else:
        verdict = "중립"

    # 최근 20일 신호
    golden = sig.vgoldenCross(close, fast=20, slow=60)
    rsi_sig = sig.vrsiSignal(rsi)
    macd_sig = sig.vmacdSignal(close)
    recent = min(20, len(close))

    return {
        "verdict": verdict,
        "score": score,
        "rsi": round(last_rsi, 1),
        "adx": round(last_adx, 1) if last_adx else None,
        "aboveSma20": above20,
        "aboveSma60": above60,
        "bbPosition": bb_pos,
        "signals": {
            "goldenCross": int(golden[-recent:].sum()),
            "rsiSignal": int(rsi_sig[-recent:].sum()),
            "macdSignal": int(macd_sig[-recent:].sum()),
        },
    }
