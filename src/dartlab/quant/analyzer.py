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

    return df.with_columns(
        [
            # 추세
            pl.Series("sma20", sma20),
            pl.Series("sma60", sma60),
            pl.Series("sma120", sma120),
            pl.Series("ema12", ema12),
            pl.Series("ema26", ema26),
            pl.Series("macd", macd_line),
            pl.Series("macdSignal", macd_signal),
            pl.Series("macdHist", macd_hist),
            pl.Series("adx", adx14),
            pl.Series("psar", psar),
            pl.Series("supertrend", st),
            pl.Series("stDirection", st_dir),
            # 모멘텀
            pl.Series("rsi", rsi14),
            pl.Series("stochK", stoch_k),
            pl.Series("stochD", stoch_d),
            pl.Series("roc", roc12),
            pl.Series("momentum", mom10),
            pl.Series("williamsR", willR),
            pl.Series("cci", cci20),
            pl.Series("cmo", cmo14),
            # 변동성
            pl.Series("bbUpper", bb_upper),
            pl.Series("bbLower", bb_lower),
            pl.Series("atr", atr14),
            pl.Series("keltUpper", kelt_upper),
            pl.Series("keltLower", kelt_lower),
            pl.Series("donchianUpper", don_upper),
            pl.Series("donchianLower", don_lower),
            # 거래량
            pl.Series("obv", obv),
            pl.Series("mfi", mfi14),
            pl.Series("forceIndex", force13),
            pl.Series("bullPower", bull),
            pl.Series("bearPower", bear),
        ]
    )


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

    result = {
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

    # 시장 대비 상대강도 + 베타 (가능하면)
    try:
        market = _fetchBenchmark()
        if market is not None and not market.is_empty():
            rs = _relativeStrength(df, market)
            beta = _calcBeta(df, market)
            result["relativeStrength"] = rs
            result["beta"] = beta
    except Exception:
        pass

    return result


def _fetchBenchmark(benchmark: str = "KOSPI") -> pl.DataFrame | None:
    """시장 지수 OHLCV 수집."""
    from dartlab.gather.entry import _INDEX_SYMBOLS, _fetchNaverIndex

    sym = _INDEX_SYMBOLS.get(benchmark, benchmark)
    df = _fetchNaverIndex(sym, 300)
    return df if not df.is_empty() else None


def _relativeStrength(stock_df: pl.DataFrame, market_df: pl.DataFrame) -> float | None:
    """종목 RSI - 시장 RSI → 상대강도."""
    s_close = stock_df["close"].to_numpy().astype(np.float64)
    m_close = market_df["close"].to_numpy().astype(np.float64)

    s_rsi = ind.vrsi(s_close, 14)
    m_rsi = ind.vrsi(m_close, 14)

    last_s = float(s_rsi[-1]) if not np.isnan(s_rsi[-1]) else None
    last_m = float(m_rsi[-1]) if not np.isnan(m_rsi[-1]) else None

    if last_s is not None and last_m is not None:
        return round(last_s - last_m, 1)
    return None


def _calcBeta(stock_df: pl.DataFrame, market_df: pl.DataFrame) -> dict | None:
    """종목 vs 시장 OLS 베타 + CAPM."""
    # 날짜 매칭 (str 변환)
    s_dates = set(str(d) for d in stock_df["date"].to_list())
    m_dates = set(str(d) for d in market_df["date"].to_list())
    common = sorted(s_dates & m_dates)

    if len(common) < 30:
        return None

    s_df = stock_df.with_columns(pl.col("date").cast(pl.Utf8).alias("_d")).filter(pl.col("_d").is_in(common)).sort("_d")
    m_df = (
        market_df.with_columns(pl.col("date").cast(pl.Utf8).alias("_d")).filter(pl.col("_d").is_in(common)).sort("_d")
    )

    sc = s_df["close"].to_numpy().astype(np.float64)
    mc = m_df["close"].to_numpy().astype(np.float64)
    sr = np.diff(sc) / sc[:-1]
    mr = np.diff(mc) / mc[:-1]

    mask = ~(np.isnan(sr) | np.isnan(mr))
    sr, mr = sr[mask], mr[mask]
    if len(sr) < 30:
        return None

    xm, ym = mr.mean(), sr.mean()
    cov = np.sum((mr - xm) * (sr - ym))
    var = np.sum((mr - xm) ** 2)
    beta = cov / var if var > 0 else 0
    alpha = ym - beta * xm

    yhat = alpha + beta * mr
    ss_res = np.sum((sr - yhat) ** 2)
    ss_tot = np.sum((sr - ym) ** 2)
    r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    # CAPM
    rf = 0.035
    mrp = 0.065
    capm = round((rf + beta * mrp) * 100, 1)

    return {
        "value": round(beta, 3),
        "alpha": round(alpha * 252 * 100, 2),
        "rSquared": round(r_sq, 4),
        "nObs": len(sr),
        "capm": capm,
    }
