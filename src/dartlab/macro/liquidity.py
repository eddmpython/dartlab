"""매크로 유동성 분석 — M2 + 연준 B/S + 신용스프레드 + FCI."""

from __future__ import annotations

from dartlab.core.finance.liquidity import classifyLiquidityRegime
from dartlab.macro._helpers import (
    apply_overrides,
    collect_timeseries,
    fetch_change_pct,
    fetch_latest,
    fetch_series_list,
    fetch_yoy,
    get_gather,
)


def _fetch_liquidity_data(market: str, as_of: str | None = None) -> dict[str, float | None]:
    """gather에서 유동성 지표 수집."""
    g = get_gather(as_of)
    data: dict[str, float | None] = {}

    data["m2_yoy"] = fetch_yoy(g, "M2SL")
    data["fed_bs_change_pct"] = fetch_change_pct(g, "WALCL", 13)

    hy = fetch_latest(g, "BAMLH0A0HYM2")
    if hy is not None:
        data["hy_spread"] = hy * 100

    ig = fetch_latest(g, "BAMLC0A0CM")
    if ig is not None:
        data["ig_spread"] = ig * 100

    data["rrp_change_pct"] = fetch_change_pct(g, "RRPONTSYD", 63)

    return {k: v for k, v in data.items() if v is not None}


def analyze_liquidity(
    *, market: str = "US", as_of: str | None = None, overrides: dict | None = None, **kwargs
) -> dict:
    """유동성 환경 종합 분석."""
    data = _fetch_liquidity_data(market, as_of=as_of)
    if overrides:
        data = apply_overrides(data, overrides)

    regime = classifyLiquidityRegime(
        m2_yoy=data.get("m2_yoy"),
        fed_bs_change_pct=data.get("fed_bs_change_pct"),
        hy_spread=data.get("hy_spread"),
        ig_spread=data.get("ig_spread"),
        rrp_change_pct=data.get("rrp_change_pct"),
    )

    result = {
        "market": market.upper(),
        "regime": regime.regime,
        "regimeLabel": regime.regimeLabel,
        "score": regime.score,
        "signals": list(regime.signals),
    }

    # NFCI + 자체 FCI
    result["nfci"] = None
    result["fci"] = None
    g = get_gather(as_of)

    if market.upper() == "US":
        nfci_val = fetch_latest(g, "NFCI")
        if nfci_val is not None:
            result["nfci"] = {
                "value": round(nfci_val, 3),
                "regime": "tight" if nfci_val > 0 else "loose",
                "regimeLabel": "긴축" if nfci_val > 0 else "완화",
                "description": f"NFCI {nfci_val:+.3f} — {'긴축' if nfci_val > 0 else '완화'} (평균=0)",
            }

    # 자체 FCI
    from dartlab.core.finance.fci import calcFCI

    if market.upper() == "US":
        sid_map = {"policy_rate": "FEDFUNDS", "long_rate": "DGS10", "credit_spread": "BAMLH0A0HYM2", "equity": "SP500", "fx": "DTWEXBGS"}
    else:
        sid_map = {"policy_rate": "BASE_RATE", "long_rate": "TREASURY_3Y", "credit_spread": "CORP_BOND_3Y", "fx": "USDKRW"}

    fci_vars: dict[str, list[float]] = {}
    for key, sid in sid_map.items():
        series = fetch_series_list(g, sid)
        if series:
            fci_vars[key] = series

    if len(fci_vars) >= 3:
        fci_result = calcFCI(fci_vars, market=market)
        result["fci"] = {
            "value": fci_result.value, "regime": fci_result.regime,
            "regimeLabel": fci_result.regimeLabel, "components": fci_result.components,
            "description": fci_result.description,
        }

    result["timeseries"] = collect_timeseries(g, {"m2": "M2SL", "hy_spread": "BAMLH0A0HYM2", "ig_spread": "BAMLC0A0CM"})

    return result
