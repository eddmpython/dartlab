"""매크로 자산 분석 — 5대 자산 심층 해석."""

from __future__ import annotations

from dartlab.core.finance.macroCycle import (
    classifyVixRegime,
    copperGoldRatio,
    interpretAssets,
    interpretGoldDrivers,
)


def _fetch_asset_data(market: str) -> dict[str, float | None]:
    """gather에서 5대 자산 지표 수집."""
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    data: dict[str, float | None] = {}

    # US 자산 (글로벌 기준)
    series_pairs = [
        ("short_rate", "DGS2"),
        ("long_rate", "DGS10"),
        ("vix", "VIXCLS"),
        ("dfii10", "DFII10"),
    ]
    for key, series_id in series_pairs:
        try:
            df = g.macro(series_id)
            if df is not None and len(df) > 0:
                vals = df.get_column("value").drop_nulls()
                if len(vals) > 0:
                    data[key] = float(vals[-1])
                    # 변화율 (3개월 ≈ 63 거래일)
                    if len(vals) >= 63:
                        data[f"{key}_change"] = float(vals[-1]) - float(vals[-63])
        except Exception:
            pass

    # 환율
    fx_id = "USDKRW" if market.upper() == "KR" else "DTWEXBGS"
    try:
        fx_df = g.macro(fx_id)
        if fx_df is not None and len(fx_df) > 0:
            vals = fx_df.get_column("value").drop_nulls()
            if len(vals) > 0:
                data["fx_usdkrw"] = float(vals[-1])
                if len(vals) >= 63:
                    old = float(vals[-63])
                    if old > 0:
                        data["fx_change_pct"] = (float(vals[-1]) / old - 1) * 100
    except Exception:
        pass

    # 금
    try:
        gold_df = g.macro("GOLDAMGBD228NLBM")
        if gold_df is not None and len(gold_df) > 0:
            vals = gold_df.get_column("value").drop_nulls()
            if len(vals) > 0:
                data["gold"] = float(vals[-1])
                if len(vals) >= 252:
                    year_ago = float(vals[-252])
                    if year_ago > 0:
                        data["gold_yoy"] = (float(vals[-1]) / year_ago - 1) * 100
    except Exception:
        pass

    # 달러인덱스 변화율
    try:
        dxy_df = g.macro("DTWEXBGS")
        if dxy_df is not None and len(dxy_df) > 0:
            vals = dxy_df.get_column("value").drop_nulls()
            if len(vals) >= 63:
                old = float(vals[-63])
                if old > 0:
                    data["dxy_change_pct"] = (float(vals[-1]) / old - 1) * 100
    except Exception:
        pass

    return data


def analyze_assets(*, market: str = "US", as_of: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """5대 자산 종합 해석.

    Returns:
        dict: assets (기본 해석), goldDrivers, vixRegime
    """
    data = _fetch_asset_data(market)
    result: dict = {"market": market.upper()}

    # 기본 5대 자산 해석 — DKW 분해 + 금리차 교차 해석 포함
    asset_input: dict[str, float | None] = {}
    for k in (
        "short_rate",
        "short_rate_change",
        "long_rate",
        "long_rate_change",
        "fx_usdkrw",
        "fx_change_pct",
        "gold",
        "gold_yoy",
        "vix",
        "vix_change",
    ):
        if k in data:
            asset_input[k] = data[k]

    # 장기금리 "왜" 해석용: BEI/실질금리 변화
    if "dfii10_change" in data:
        asset_input["real_rate_change"] = data["dfii10_change"]
    # BEI 변화 (T10YIE 3개월 변화)
    try:
        from dartlab.gather import getDefaultGather

        bei_df = getDefaultGather().macro("T10YIE")
        if bei_df is not None and len(bei_df) > 0:
            vals = bei_df.get_column("value").drop_nulls()
            if len(vals) >= 63:
                asset_input["bei_change"] = float(vals[-1]) - float(vals[-63])
    except Exception:
        pass

    # 금리차-환율 교차 해석용: US 2Y - KR 기준금리
    if market.upper() == "KR":
        try:
            from dartlab.gather import getDefaultGather

            g = getDefaultGather()
            us2y = g.macro("DGS2")
            kr_rate = g.macro("기준금리")
            if us2y is not None and kr_rate is not None:
                us_vals = us2y.get_column("value").drop_nulls()
                kr_vals = kr_rate.get_column("value").drop_nulls()
                if len(us_vals) > 0 and len(kr_vals) > 0:
                    diff_now = float(us_vals[-1]) - float(kr_vals[-1])
                    asset_input["rate_diff"] = diff_now
                    if len(us_vals) >= 63 and len(kr_vals) >= 2:
                        diff_old = float(us_vals[-63]) - float(kr_vals[-2])
                        asset_input["rate_diff_change"] = diff_now - diff_old
        except Exception:
            pass

    signals = interpretAssets(asset_input)
    result["assets"] = [
        {
            "asset": s.asset,
            "label": s.label,
            "level": s.level,
            "change": s.change,
            "interpretation": s.interpretation,
            "implication": s.implication,
        }
        for s in signals
    ]

    # 금 3요인 심층 해석
    gold_yoy = data.get("gold_yoy")
    real_rate_chg = data.get("dfii10_change")
    dxy_chg = data.get("dxy_change_pct")
    vix = data.get("vix")
    if gold_yoy is not None and real_rate_chg is not None and dxy_chg is not None and vix is not None:
        gd = interpretGoldDrivers(gold_yoy, real_rate_chg, dxy_chg, vix)
        result["goldDrivers"] = {
            "realRateEffect": gd.realRateEffect,
            "dollarEffect": gd.dollarEffect,
            "safeHavenEffect": gd.safeHavenEffect,
            "dominant": gd.dominant,
        }
    else:
        result["goldDrivers"] = None

    # VIX 구간 판정
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

    # Copper/Gold Ratio
    result["copperGold"] = None
    try:
        from dartlab.gather import getDefaultGather

        g = getDefaultGather()
        cu_df = g.macro("PCOPPUSDM")
        gold_df = g.macro("GOLDAMGBD228NLBM")
        if cu_df is not None and gold_df is not None:
            cu_vals = cu_df.get_column("value").drop_nulls()
            au_vals = gold_df.get_column("value").drop_nulls()
            if len(cu_vals) > 1 and len(au_vals) > 1:
                cg = copperGoldRatio(
                    float(cu_vals[-1]),
                    float(au_vals[-1]),
                    float(cu_vals[-2]) if len(cu_vals) > 1 else None,
                    float(au_vals[-2]) if len(au_vals) > 1 else None,
                )
                result["copperGold"] = {
                    "ratio": cg.ratio,
                    "direction": cg.direction,
                    "directionLabel": cg.directionLabel,
                    "implication": cg.implication,
                    "description": cg.description,
                }
    except Exception:
        pass

    return result
