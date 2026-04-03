"""매크로 금리 분석 — 금리 방향 + 고용/물가 + DKW 근사."""

from __future__ import annotations

from dartlab.core.finance.macroCycle import decomposeLongRate, rateOutlook
from dartlab.core.finance.sentiment import (
    estimateRateExpectation,
    interpretEmployment,
    interpretInflation,
)


def _fetch_rate_data(market: str) -> dict[str, float | None]:
    """gather에서 금리 관련 지표 수집."""
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    data: dict[str, float | None] = {}

    if market.upper() == "US":
        # 최신값 그대로 쓰는 시리즈 (금리/실업률 = 이미 % 단위)
        direct_series = {
            "fed_funds": "FEDFUNDS",
            "dgs2": "DGS2",
            "dgs10": "DGS10",
            "dfii10": "DFII10",
            "t10yie": "T10YIE",
            "unrate": "UNRATE",
            "t5yie": "T5YIE",
        }
        for key, series_id in direct_series.items():
            try:
                df = g.macro(series_id)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls()
                    if len(vals) > 0:
                        data[key] = float(vals[-1])
            except Exception:
                pass

        # YoY 변화율로 변환이 필요한 시리즈 (CPI는 인덱스값이므로)
        for key, series_id in [("cpi_yoy", "CPIAUCSL"), ("core_cpi", "CPILFESL")]:
            try:
                df = g.macro(series_id)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls()
                    if len(vals) >= 12:
                        current = float(vals[-1])
                        year_ago = float(vals[-12])
                        if year_ago > 0:
                            data[key] = (current / year_ago - 1) * 100
            except Exception:
                pass

    elif market.upper() == "KR":
        # 한국 금리 데이터 (ECOS)
        for key, series_id in [("base_rate", "기준금리"), ("cpi_yoy", "CPI")]:
            try:
                df = g.macro(series_id)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls()
                    if len(vals) > 0:
                        data[key] = float(vals[-1])
            except Exception:
                pass

    return data


def analyze_rates(*, market: str = "US", **kwargs) -> dict:
    """금리 종합 분석.

    Returns:
        dict: rateOutlook, rateExpectation, rateDecomposition, employment, inflation
    """
    data = _fetch_rate_data(market)
    result: dict = {"market": market.upper()}

    # 금리 방향 전망
    outlook_input: dict[str, float | None] = {}
    if "fed_funds" in data:
        outlook_input["fed_funds"] = data["fed_funds"]
    if "base_rate" in data:
        outlook_input["base_rate"] = data["base_rate"]
    if "cpi_yoy" in data:
        outlook_input["cpi_yoy"] = data["cpi_yoy"]
    if "core_cpi" in data:
        outlook_input["core_cpi_yoy"] = data["core_cpi"]
    if "unrate" in data:
        outlook_input["unemployment"] = data["unrate"]

    result["outlook"] = rateOutlook(outlook_input)

    # FedWatch 근사 (2Y-FF 스프레드)
    ff = data.get("fed_funds") or data.get("base_rate")
    dgs2 = data.get("dgs2")
    dgs10 = data.get("dgs10")
    if ff is not None and dgs2 is not None:
        result["expectation"] = {
            "spread2yFf": estimateRateExpectation(ff, dgs2, dgs10).spread2yFf,
            "direction": estimateRateExpectation(ff, dgs2, dgs10).direction,
            "directionLabel": estimateRateExpectation(ff, dgs2, dgs10).directionLabel,
            "strength": estimateRateExpectation(ff, dgs2, dgs10).strength,
        }
    else:
        result["expectation"] = None

    # DKW 근사 분해 (US만)
    if market.upper() == "US" and dgs10 and data.get("t10yie") and data.get("dfii10"):
        decomp = decomposeLongRate(
            dgs10, data["t10yie"], data["dfii10"], ff  # type: ignore[arg-type]
        )
        result["decomposition"] = {
            "nominal": decomp.nominal,
            "expectedInflation": decomp.expectedInflation,
            "realRate": decomp.realRate,
            "termPremium": decomp.termPremium,
        }
    else:
        result["decomposition"] = None

    # 고용 해석
    unrate = data.get("unrate")
    if unrate is not None:
        emp = interpretEmployment(unrate)
        result["employment"] = {
            "state": emp.state,
            "stateLabel": emp.stateLabel,
            "reasoning": list(emp.reasoning),
        }
    else:
        result["employment"] = None

    # 물가 해석
    cpi = data.get("cpi_yoy")
    if cpi is not None:
        inf = interpretInflation(
            cpi,
            data.get("core_cpi"),
            data.get("t5yie"),
            data.get("t10yie"),
        )
        result["inflation"] = {
            "state": inf.state,
            "stateLabel": inf.stateLabel,
            "reasoning": list(inf.reasoning),
        }
    else:
        result["inflation"] = None

    # 시계열
    from dartlab.macro._helpers import recent_timeseries

    ts: dict = {}
    try:
        from dartlab.gather import getDefaultGather
        g = getDefaultGather()
        for label, sid in [("fed_funds", "FEDFUNDS"), ("dgs2", "DGS2"), ("dgs10", "DGS10"), ("bei", "T10YIE"), ("cpi", "CPIAUCSL")]:
            ts[label] = recent_timeseries(g.macro(sid))
    except Exception:
        pass
    result["timeseries"] = ts

    return result
