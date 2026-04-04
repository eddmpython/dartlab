"""매크로 심리 분석 — 공포탐욕 근사 + VIX 구간."""

from __future__ import annotations

from dartlab.core.finance.macroCycle import classifyVixRegime
from dartlab.core.finance.sentiment import calcFearGreedProxy
from dartlab.macro._helpers import (
    apply_overrides,
    collect_timeseries,
    fetch_latest,
    fetch_series_list,
    get_gather,
)


def _fetch_sentiment_data(market: str, as_of: str | None = None) -> dict[str, float | None]:
    """gather에서 심리 지표 수집."""
    g = get_gather(as_of)
    data: dict[str, float | None] = {}

    data["vix"] = fetch_latest(g, "VIXCLS")

    sp_list = fetch_series_list(g, "SP500")
    if sp_list and len(sp_list) >= 125:
        current = sp_list[-1]
        ma125 = sum(sp_list[-125:]) / 125
        if ma125 > 0:
            data["sp500_vs_ma125"] = current / ma125

    hy = fetch_latest(g, "BAMLH0A0HYM2")
    if hy is not None:
        data["hy_spread"] = hy * 100

    gold = fetch_latest(g, "GOLDAMGBD228NLBM")
    sp = fetch_latest(g, "SP500")
    if gold is not None and sp is not None and sp > 0:
        data["gold_equity_ratio"] = gold / sp

    return data


def analyze_sentiment(
    *, market: str = "US", as_of: str | None = None, overrides: dict | None = None, **kwargs
) -> dict:
    """시장 심리 종합 분석."""
    data = _fetch_sentiment_data(market, as_of=as_of)
    if overrides:
        data = apply_overrides(data, overrides)
    result: dict = {"market": market.upper()}

    vix = data.get("vix")
    sp_ratio = data.get("sp500_vs_ma125")
    hy = data.get("hy_spread")
    if vix is not None and sp_ratio is not None and hy is not None:
        fg = calcFearGreedProxy(vix, sp_ratio, hy, data.get("gold_equity_ratio"))
        result["fearGreed"] = {
            "score": fg.score, "zone": fg.zone, "zoneLabel": fg.zoneLabel, "components": fg.components,
        }
    else:
        result["fearGreed"] = None

    if vix is not None:
        vr = classifyVixRegime(vix)
        result["vixRegime"] = {"level": vr.level, "zone": vr.zone, "zoneLabel": vr.zoneLabel, "buySignal": vr.buySignal}
    else:
        result["vixRegime"] = None

    g = get_gather(as_of)
    result["timeseries"] = collect_timeseries(g, {"vix": "VIXCLS", "sp500": "SP500", "hy_spread": "BAMLH0A0HYM2"})

    return result
