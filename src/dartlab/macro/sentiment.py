"""매크로 심리 분석 — 공포탐욕 근사 + VIX 구간."""

from __future__ import annotations

from dartlab.core.finance.macroCycle import classifyVixRegime
from dartlab.core.finance.sentiment import calcFearGreedProxy


def _fetch_sentiment_data(market: str) -> dict[str, float | None]:
    """gather에서 심리 지표 수집."""
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    data: dict[str, float | None] = {}

    # VIX
    try:
        vix_df = g.macro("VIXCLS")
        if vix_df is not None and len(vix_df) > 0:
            vals = vix_df.get_column("value").drop_nulls()
            if len(vals) > 0:
                data["vix"] = float(vals[-1])
    except Exception:
        pass

    # S&P500 vs 125일 이동평균
    try:
        sp_df = g.macro("SP500")
        if sp_df is not None and len(sp_df) > 0:
            vals = sp_df.get_column("value").drop_nulls()
            if len(vals) >= 125:
                current = float(vals[-1])
                ma125 = sum(float(v) for v in vals[-125:]) / 125
                if ma125 > 0:
                    data["sp500_vs_ma125"] = current / ma125
    except Exception:
        pass

    # HY 스프레드
    try:
        hy_df = g.macro("BAMLH0A0HYM2")
        if hy_df is not None and len(hy_df) > 0:
            vals = hy_df.get_column("value").drop_nulls()
            if len(vals) > 0:
                data["hy_spread"] = float(vals[-1]) * 100  # % → bps
    except Exception:
        pass

    # 금/S&P500 비율
    try:
        gold_df = g.macro("GOLDAMGBD228NLBM")
        sp_df2 = g.macro("SP500")
        if gold_df is not None and sp_df2 is not None:
            gold_vals = gold_df.get_column("value").drop_nulls()
            sp_vals = sp_df2.get_column("value").drop_nulls()
            if len(gold_vals) > 0 and len(sp_vals) > 0:
                gold_price = float(gold_vals[-1])
                sp_price = float(sp_vals[-1])
                if sp_price > 0:
                    data["gold_equity_ratio"] = gold_price / sp_price
    except Exception:
        pass

    return data


def analyze_sentiment(*, market: str = "US", **kwargs) -> dict:
    """시장 심리 종합 분석.

    Returns:
        dict: fearGreed, vixRegime
    """
    data = _fetch_sentiment_data(market)
    result: dict = {"market": market.upper()}

    # 공포탐욕 근사
    vix = data.get("vix")
    sp_ratio = data.get("sp500_vs_ma125")
    hy = data.get("hy_spread")
    if vix is not None and sp_ratio is not None and hy is not None:
        fg = calcFearGreedProxy(vix, sp_ratio, hy, data.get("gold_equity_ratio"))
        result["fearGreed"] = {
            "score": fg.score,
            "zone": fg.zone,
            "zoneLabel": fg.zoneLabel,
            "components": fg.components,
        }
    else:
        result["fearGreed"] = None

    # VIX 구간 + 분할매수 신호
    if vix is not None:
        vr = classifyVixRegime(vix)
        result["vixRegime"] = {
            "level": vr.level,
            "zone": vr.zone,
            "zoneLabel": vr.zoneLabel,
            "buySignal": vr.buySignal,
        }
    else:
        result["vixRegime"] = None

    # 시계열
    from dartlab.macro._helpers import recent_timeseries

    ts: dict = {}
    try:
        from dartlab.gather import getDefaultGather

        g = getDefaultGather()
        for label, sid in [("vix", "VIXCLS"), ("sp500", "SP500"), ("hy_spread", "BAMLH0A0HYM2")]:
            ts[label] = recent_timeseries(g.macro(sid))
    except Exception:
        pass
    result["timeseries"] = ts

    return result
