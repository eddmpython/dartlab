"""잔여수익 분석 — 팩터 제거 후 잔여 모멘텀.

학술 근거: Blitz, Huij, Martens (2011) — Residual Momentum.
"""

from __future__ import annotations

import numpy as np

from dartlab.quant._helpers import fetch_benchmark, fetch_ohlcv, ohlcv_to_arrays, resolve_market


def analyze_residual(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """팩터 제거 후 잔여 모멘텀/알파."""
    market = resolve_market(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}

    from dartlab.quant.factor import analyze_factor

    fr = analyze_factor(stockCode, market=market)
    if "error" in fr:
        return {**result, "error": fr["error"]}

    ohlcv = fetch_ohlcv(stockCode)
    if ohlcv is None or ohlcv.is_empty():
        return {**result, "error": "주가 데이터 없음"}

    close = ohlcv_to_arrays(ohlcv).get("close")
    if close is None or len(close) < 60:
        return {**result, "error": "데이터 부족"}

    sr = np.diff(np.log(close))

    bench = fetch_benchmark(market)
    if bench is None:
        return {**result, "error": "벤치마크 없음"}
    bc = ohlcv_to_arrays(bench).get("close")
    br = np.diff(np.log(bc))

    ml = min(len(sr), len(br))
    sr, br = sr[-ml:], br[-ml:]

    beta = fr.get("MKT", {}).get("loading", 1.0)
    alpha_d = fr.get("alpha", 0) / 252
    predicted = alpha_d + beta * br
    residuals = sr - predicted

    n = len(residuals)
    rm6 = float(np.mean(residuals[-min(126, n):]) * 252)
    rm1 = float(np.mean(residuals[-min(22, n):]) * 252)
    iv = float(np.std(residuals) * np.sqrt(252))
    ra = float(np.mean(residuals) * 252)
    rs = ra / iv if iv > 0 else 0

    result["residualMomentum6m"] = round(rm6, 4)
    result["residualMomentum1m"] = round(rm1, 4)
    result["idiosyncraticVol"] = round(iv, 4)
    result["residualAlpha"] = round(ra, 4)
    result["residualSharpe"] = round(float(rs), 4)
    result["factorRSquared"] = fr.get("rSquared", 0)
    result["residualVerdict"] = "positive_alpha" if ra > 0.05 else "negative_alpha" if ra < -0.05 else "neutral"
    return result
