"""매크로 교역 분석 — 교역조건 + 대용치 + 수출이익 선행.

투자전략 5: 우리나라 종합주가는 미국의 소비와 유사한 흐름을 보인다
투자전략 10: 우리나라 주가 흐름은 수출기업이 좌우한다
투자전략 11: 선행지수 중에 가장 앞선 모습을 보이는 것은 교역조건이다
투자전략 12: 교역조건대용치는 환율상승률과 유가상승률의 차다
투자전략 14: 환율의 방향성은 양국 선행지수의 상대강도에 의해 결정된다
투자전략 31: 교역조건대용치는 수출기업의 이익에 선행한다
"""

from __future__ import annotations

from dartlab.core.finance.termsOfTrade import (
    calcToT,
    exportProfitLeading,
    leadingIndexRelativeStrength,
    totProxy,
)


def _yoy(series: list[float], idx: int = -1) -> float | None:
    """시계열에서 12개월 전 대비 YoY% 계산 (월간 데이터 가정)."""
    if len(series) < 13:
        return None
    current = series[idx]
    prev = series[idx - 12]
    if prev == 0:
        return None
    return ((current - prev) / abs(prev)) * 100


def _mom(series: list[float]) -> float | None:
    """최근 2개 값의 MoM 차이."""
    if len(series) < 2:
        return None
    return series[-1] - series[-2]


def _fetch_trade_data(market: str, as_of: str | None = None) -> dict[str, float | list | None]:
    """gather에서 교역/환율/유가 지표 수집."""
    from dartlab.macro._helpers import fetch_latest_with_prev, fetch_series_list, get_gather

    g = get_gather(as_of)
    data: dict[str, float | list | None] = {}

    if market.upper() == "KR":
        for label, sid in [
            ("export_price", "EXPORT_PRICE"), ("import_price", "IMPORT_PRICE"),
            ("export_vol", "EXPORT"), ("usdkrw", "USDKRW"), ("cli", "CLI"),
        ]:
            series = fetch_series_list(g, sid)
            if series:
                data[f"{label}_series"] = series
                data[label] = series[-1]
                if len(series) > 1:
                    data[f"{label}_prev"] = series[-2]

    data["oil_series"] = fetch_series_list(g, "DCOILWTICO")
    oil_list = data.get("oil_series")
    if oil_list:
        data["oil"] = oil_list[-1]

    data["us_retail_series"] = fetch_series_list(g, "RSAFS")

    return data


def analyze_trade(*, market: str = "US", as_of: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """교역 종합 분석.

    Returns:
        dict: termsOfTrade, totProxy, exportProfit, leadingRelativeStrength,
              usConsumptionLink, timeseries
    """
    data = _fetch_trade_data(market, as_of=as_of)
    if overrides:
        from dartlab.macro._helpers import apply_overrides
        data = apply_overrides(data, overrides)
    result: dict = {"market": market.upper()}

    if market.upper() == "KR":
        # 교역조건 직접 계산
        exp_price = data.get("export_price")
        imp_price = data.get("import_price")
        if exp_price is not None and imp_price is not None:
            exp_prev = data.get("export_price_prev")
            imp_prev = data.get("import_price_prev")
            tot = calcToT(exp_price, imp_price, exp_prev, imp_prev)
            result["termsOfTrade"] = {
                "level": tot.level,
                "momentum": tot.momentum,
                "direction": tot.direction,
                "directionLabel": tot.directionLabel,
                "earningsImplication": tot.earningsImplication,
                "earningsLabel": tot.earningsLabel,
                "description": tot.description,
            }
        else:
            result["termsOfTrade"] = None

        # 교역조건 대용치 (환율 - 유가)
        usdkrw_series = data.get("usdkrw_series")
        oil_series = data.get("oil_series")
        if usdkrw_series and oil_series:
            fx_yoy = _yoy(usdkrw_series)
            oil_yoy = _yoy(oil_series)
            if fx_yoy is not None and oil_yoy is not None:
                proxy = totProxy(fx_yoy, oil_yoy)
                result["totProxy"] = {
                    "value": proxy.value,
                    "direction": proxy.direction,
                    "directionLabel": proxy.directionLabel,
                    "components": proxy.components,
                    "description": proxy.description,
                }
            else:
                result["totProxy"] = None
        else:
            result["totProxy"] = None

        # 수출이익 선행 신호
        tot_data = result.get("termsOfTrade")
        export_series = data.get("export_vol_series")
        if tot_data and export_series:
            tot_mom = tot_data["momentum"]
            export_yoy = _yoy(export_series)
            if export_yoy is not None:
                profit = exportProfitLeading(tot_mom, export_yoy)
                result["exportProfit"] = {
                    "signal": profit.signal,
                    "signalLabel": profit.signalLabel,
                    "confidence": profit.confidence,
                    "components": profit.components,
                    "description": profit.description,
                }
            else:
                result["exportProfit"] = None
        else:
            result["exportProfit"] = None

        # 양국 선행지수 상대강도 (전략 14)
        cli_series = data.get("cli_series")
        us_retail = data.get("us_retail_series")
        if cli_series:
            kr_cli_mom = _mom(cli_series)
            # US LEI는 아직 구현 전이므로 US 소매판매 모멘텀으로 근사
            us_mom = _mom(us_retail) if us_retail and len(us_retail) >= 2 else None
            if kr_cli_mom is not None and us_mom is not None:
                leading = leadingIndexRelativeStrength(us_mom, kr_cli_mom)
                result["leadingRelativeStrength"] = {
                    "relativeStrength": leading.relativeStrength,
                    "fxDirection": leading.fxDirection,
                    "fxLabel": leading.fxLabel,
                    "description": leading.description,
                }
            else:
                result["leadingRelativeStrength"] = None
        else:
            result["leadingRelativeStrength"] = None

        # 한국 주가 ≈ 미국 소비 (전략 5)
        if us_retail:
            us_retail_yoy = _yoy(us_retail)
            if us_retail_yoy is not None:
                if us_retail_yoy > 5:
                    link = "미국 소비 강세 → 한국 수출 호조 → KOSPI 긍정"
                elif us_retail_yoy < -2:
                    link = "미국 소비 약세 → 한국 수출 부진 → KOSPI 부정"
                else:
                    link = "미국 소비 보합 → 한국 주가 중립"
                result["usConsumptionLink"] = {
                    "usRetailYoy": round(us_retail_yoy, 1),
                    "implication": link,
                }
            else:
                result["usConsumptionLink"] = None
        else:
            result["usConsumptionLink"] = None

    else:
        # US market: 교역조건은 KR 위주이므로 제한적
        result["termsOfTrade"] = None
        result["totProxy"] = None
        result["exportProfit"] = None
        result["leadingRelativeStrength"] = None
        result["usConsumptionLink"] = None

    from dartlab.macro._helpers import collect_timeseries, get_gather

    g_ts = get_gather(as_of)
    ts_map = {"oil": "DCOILWTICO"}
    if market.upper() == "KR":
        ts_map.update({"export_price": "EXPORT_PRICE", "import_price": "IMPORT_PRICE", "usdkrw": "USDKRW", "export": "EXPORT"})
    result["timeseries"] = collect_timeseries(g_ts, ts_map)

    return result
