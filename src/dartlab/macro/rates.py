"""매크로 금리 분석 — 금리 방향 + 고용/물가 + DKW + Nelson-Siegel."""

from __future__ import annotations

from dartlab.core.finance.macroCycle import decomposeLongRate, rateOutlook, realRateRegime
from dartlab.core.finance.sentiment import (
    estimateRateExpectation,
    interpretEmployment,
    interpretInflation,
)
from dartlab.core.finance.yieldCurve import nelsonSiegel
from dartlab.macro._helpers import (
    apply_overrides,
    collect_timeseries,
    fetch_latest,
    fetch_yoy,
    get_gather,
)


def _fetch_rate_data(market: str, as_of: str | None = None) -> dict[str, float | None]:
    """gather에서 금리 관련 지표 수집."""
    g = get_gather(as_of)
    data: dict[str, float | None] = {}

    if market.upper() == "US":
        for key, sid in [
            ("fed_funds", "FEDFUNDS"), ("dgs2", "DGS2"), ("dgs10", "DGS10"),
            ("dfii10", "DFII10"), ("t10yie", "T10YIE"), ("unrate", "UNRATE"), ("t5yie", "T5YIE"),
        ]:
            data[key] = fetch_latest(g, sid)

        data["cpi_yoy"] = fetch_yoy(g, "CPIAUCSL")
        data["core_cpi"] = fetch_yoy(g, "CPILFESL")

    elif market.upper() == "KR":
        data["base_rate"] = fetch_latest(g, "BASE_RATE")
        data["cpi_yoy"] = fetch_yoy(g, "CPI")

    return {k: v for k, v in data.items() if v is not None}


def analyze_rates(
    *, market: str = "US", as_of: str | None = None, overrides: dict | None = None, **kwargs
) -> dict:
    """금리 종합 분석."""
    data = _fetch_rate_data(market, as_of=as_of)
    if overrides:
        data = apply_overrides(data, overrides)
    result: dict = {"market": market.upper()}

    # 금리 방향 전망
    outlook_input: dict[str, float | None] = {}
    for src, dst in [("fed_funds", "fed_funds"), ("base_rate", "base_rate"),
                     ("cpi_yoy", "cpi_yoy"), ("core_cpi", "core_cpi_yoy"), ("unrate", "unemployment")]:
        if src in data:
            outlook_input[dst] = data[src]
    result["outlook"] = rateOutlook(outlook_input)

    # FedWatch 근사
    ff = data.get("fed_funds") or data.get("base_rate")
    dgs2 = data.get("dgs2")
    dgs10 = data.get("dgs10")
    if ff is not None and dgs2 is not None:
        exp = estimateRateExpectation(ff, dgs2, dgs10)
        result["expectation"] = {
            "spread2yFf": exp.spread2yFf, "direction": exp.direction,
            "directionLabel": exp.directionLabel, "strength": exp.strength,
        }
    else:
        result["expectation"] = None

    # DKW 분해 (US만)
    result["decomposition"] = None
    if market.upper() == "US" and dgs10 and data.get("t10yie") and data.get("dfii10"):
        decomp = decomposeLongRate(dgs10, data["t10yie"], data["dfii10"], ff)
        result["decomposition"] = {
            "nominal": decomp.nominal, "expectedInflation": decomp.expectedInflation,
            "realRate": decomp.realRate, "termPremium": decomp.termPremium,
        }

    # 고용 해석
    unrate = data.get("unrate")
    if unrate is not None:
        emp = interpretEmployment(unrate)
        result["employment"] = {"state": emp.state, "stateLabel": emp.stateLabel, "reasoning": list(emp.reasoning)}
    else:
        result["employment"] = None

    # 물가 해석
    cpi = data.get("cpi_yoy")
    if cpi is not None:
        inf = interpretInflation(cpi, data.get("core_cpi"), data.get("t5yie"), data.get("t10yie"))
        result["inflation"] = {"state": inf.state, "stateLabel": inf.stateLabel, "reasoning": list(inf.reasoning)}
    else:
        result["inflation"] = None

    # Nelson-Siegel 수익률곡선 분해 (US만)
    result["yieldCurve"] = None
    if market.upper() == "US":
        g = get_gather(as_of)
        maturities = [1, 2, 3, 5, 7, 10, 20, 30]
        series_ids = ["DGS1", "DGS2", "DGS3", "DGS5", "DGS7", "DGS10", "DGS20", "DGS30"]
        yields_list, valid_mats = [], []
        for mat, sid in zip(maturities, series_ids):
            val = fetch_latest(g, sid)
            if val is not None:
                yields_list.append(val)
                valid_mats.append(mat)
        if len(valid_mats) >= 4:
            ns = nelsonSiegel(valid_mats, yields_list)
            result["yieldCurve"] = {
                "beta0": ns.beta0, "beta1": ns.beta1, "beta2": ns.beta2,
                "lambda": ns.lamb, "rmse": ns.rmse,
                "interpretation": ns.interpretation, "description": ns.description,
            }

    # BEI/실질금리 4분면 (US만)
    result["realRateRegime"] = None
    if market.upper() == "US" and data.get("dfii10") is not None and data.get("t10yie") is not None:
        rr = realRateRegime(data["dfii10"], data["t10yie"])
        result["realRateRegime"] = {
            "realRate": rr.realRate, "bei": rr.bei, "regime": rr.regime,
            "regimeLabel": rr.regimeLabel, "description": rr.description,
        }

    # 시계열
    g = get_gather(as_of)
    result["timeseries"] = collect_timeseries(g, {
        "fed_funds": "FEDFUNDS", "dgs2": "DGS2", "dgs10": "DGS10", "bei": "T10YIE", "cpi": "CPIAUCSL",
    })

    return result
