"""매크로 예측 — LEI + 침체확률 + Hamilton RS + GDP Nowcasting.

투자전략 1: 금리 추이는 전기비 성장률에 의해 결정된다
투자전략 2: 주가지수는 명목 GDP증가율과 상관관계가 높다
투자전략 16: 전기비 성장률은 '선행지수 증가율+후행지수 증가율'이다

Hamilton (1989): Markov Regime Switching으로 확률적 경기국면 판별
Banbura et al. (2011): Dynamic Factor Model로 GDP 실시간 추정
"""

from __future__ import annotations

import numpy as np

from dartlab.core.finance.nowcast import gdpNowcast
from dartlab.core.finance.regimeSwitching import clevelandProbit, conferenceBoardLEI, hamiltonRegime, sahmRule


def _fetch_forecast_data(market: str, as_of: str | None = None) -> dict[str, float | list | None]:
    """gather에서 LEI 구성요소 + 프로빗 입력 수집."""
    from dartlab.macro._helpers import fetch_with_history, get_gather

    g = get_gather(as_of)
    data: dict[str, float | list | None] = {}

    if market.upper() == "US":
        for label, sid in [
            ("t10y3m", "T10Y3M"), ("awhman", "AWHMAN"), ("icsa", "ICSA"), ("acogno", "ACOGNO"),
            ("napmnoi", "NAPMNOI"), ("acdgno", "ACDGNO"), ("permit", "PERMIT"), ("sp500", "SP500"),
            ("m2real", "M2REAL"), ("umcsent", "UMCSENT"), ("fedfunds", "FEDFUNDS"), ("dgs10", "DGS10"),
        ]:
            hist = fetch_with_history(g, sid)
            if "current" in hist:
                data[label] = hist["current"]
            if "prev" in hist:
                data[f"{label}_prev"] = hist["prev"]
            if "6m" in hist:
                data[f"{label}_6m"] = hist["6m"]

    elif market.upper() == "KR":
        for label, sid in [("cli", "CLI"), ("cci", "CCI"), ("cli_lag", "CLI_LAG")]:
            hist = fetch_with_history(g, sid)
            if "current" in hist:
                data[label] = hist["current"]
            if "prev" in hist:
                data[f"{label}_prev"] = hist["prev"]
            if "6m" in hist:
                data[f"{label}_6m"] = hist["6m"]

    return data


def _pct_change(current: float | None, prev: float | None) -> float | None:
    """전기대비 변화율 (%)."""
    if current is None or prev is None or prev == 0:
        return None
    return ((current - prev) / abs(prev)) * 100


def analyze_forecast(*, market: str = "US", as_of: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """경제 예측 종합 분석.

    Returns:
        dict: recessionProb, lei, growthMomentum, timeseries
    """
    data = _fetch_forecast_data(market, as_of=as_of)
    if overrides:
        from dartlab.macro._helpers import apply_overrides
        data = apply_overrides(data, overrides)
    result: dict = {"market": market.upper()}

    if market.upper() == "US":
        # Cleveland Fed 프로빗
        t10y3m = data.get("t10y3m")
        if t10y3m is not None:
            probit = clevelandProbit(t10y3m)
            result["recessionProb"] = {
                "probability": probit.probability,
                "zone": probit.zone,
                "zoneLabel": probit.zoneLabel,
                "spread": probit.spread,
                "description": probit.description,
            }
        else:
            result["recessionProb"] = None

        # LEI 복제
        components: dict[str, float | None] = {}

        # 각 구성요소 변화율 계산
        awhman = data.get("awhman")
        awhman_prev = data.get("awhman_prev")
        components["avg_weekly_hours"] = _pct_change(awhman, awhman_prev)

        icsa = data.get("icsa")
        icsa_prev = data.get("icsa_prev")
        if icsa is not None and icsa_prev is not None and icsa_prev > 0:
            components["initial_claims"] = -_pct_change(icsa, icsa_prev)  # 역수
        else:
            components["initial_claims"] = None

        components["new_orders_consumer"] = _pct_change(data.get("acogno"), data.get("acogno_prev"))

        # ISM 신규수주: 50 기준 편차
        napmnoi = data.get("napmnoi")
        components["ism_new_orders"] = napmnoi - 50 if napmnoi is not None else None

        components["new_orders_nondefense_cap"] = _pct_change(data.get("acdgno"), data.get("acdgno_prev"))
        components["building_permits"] = _pct_change(data.get("permit"), data.get("permit_prev"))
        components["sp500"] = _pct_change(data.get("sp500"), data.get("sp500_prev"))

        # leading credit: 간소화 (M2 실질 변화율로 근사)
        components["leading_credit"] = _pct_change(data.get("m2real"), data.get("m2real_prev"))

        # term spread: 10Y - FF 수준
        dgs10 = data.get("dgs10")
        ff = data.get("fedfunds")
        if dgs10 is not None and ff is not None:
            components["term_spread"] = dgs10 - ff
        else:
            components["term_spread"] = None

        components["consumer_expectations"] = _pct_change(data.get("umcsent"), data.get("umcsent_prev"))

        lei = conferenceBoardLEI(components)
        result["lei"] = {
            "level": lei.level,
            "mom": lei.mom,
            "mom6m": lei.mom6m,
            "signal": lei.signal,
            "signalLabel": lei.signalLabel,
            "availableComponents": sum(1 for v in components.values() if v is not None),
            "totalComponents": len(components),
            "description": lei.description,
        }

    elif market.upper() == "KR":
        result["recessionProb"] = None  # KR은 프로빗 미적용

        # 한국: 선행+동행+후행 조합 (전략 16)
        cli = data.get("cli")
        cli_prev = data.get("cli_prev")
        cci = data.get("cci")
        cci_prev = data.get("cci_prev")
        cli_lag = data.get("cli_lag")
        cli_lag_prev = data.get("cli_lag_prev")

        kr_forecast: dict = {}
        if cli is not None and cli_prev is not None:
            cli_mom = cli - cli_prev
            kr_forecast["cliMomentum"] = round(cli_mom, 2)
            kr_forecast["cliLevel"] = round(cli, 1)

        if cci is not None and cci_prev is not None:
            cci_mom = cci - cci_prev
            kr_forecast["cciMomentum"] = round(cci_mom, 2)

        if cli_lag is not None and cli_lag_prev is not None:
            lag_mom = cli_lag - cli_lag_prev
            kr_forecast["lagMomentum"] = round(lag_mom, 2)

        # 전략 16: 전기비 성장률 ≈ 선행 + 후행
        cli_m = kr_forecast.get("cliMomentum")
        lag_m = kr_forecast.get("lagMomentum")
        if cli_m is not None and lag_m is not None:
            growth_approx = cli_m + lag_m
            kr_forecast["growthApprox"] = round(growth_approx, 2)
            if growth_approx > 0.5:
                kr_forecast["growthSignal"] = "expanding"
                kr_forecast["growthLabel"] = "확장"
            elif growth_approx < -0.5:
                kr_forecast["growthSignal"] = "contracting"
                kr_forecast["growthLabel"] = "수축"
            else:
                kr_forecast["growthSignal"] = "stable"
                kr_forecast["growthLabel"] = "안정"

        result["lei"] = kr_forecast if kr_forecast else None

    # ── Sahm Rule ──
    from dartlab.macro._helpers import collect_timeseries, fetch_series_list, get_gather

    g = get_gather(as_of)
    result["sahmRule"] = None
    if market.upper() == "US":
        ur_vals = fetch_series_list(g, "UNRATE")
        if ur_vals and len(ur_vals) >= 15:
            sr = sahmRule(ur_vals)
            result["sahmRule"] = {
                "value": sr.value, "triggered": sr.triggered,
                "zone": sr.zone, "zoneLabel": sr.zoneLabel, "description": sr.description,
            }

    # ── Hamilton Regime Switching ──
    result["hamiltonRegime"] = None
    gdp_id = "A191RL1Q225SBEA" if market.upper() == "US" else "GROWTH"
    gdp_vals = fetch_series_list(g, gdp_id)
    if gdp_vals and len(gdp_vals) >= 20:
        hr = hamiltonRegime(gdp_vals, maxIter=100)
        result["hamiltonRegime"] = {
            "currentRegime": hr.regimeLabels[hr.currentRegime],
            "currentProb": hr.currentProb,
            "params": hr.params,
            "converged": hr.converged,
            "iterations": hr.iterations,
            "contractionProb": round(float(hr.smoothedProbs[-1, 1]), 4),
            "description": (
                f"Hamilton RS: {hr.regimeLabels[hr.currentRegime]} "
                f"({hr.currentProb:.1%}), "
                f"침체확률 {hr.smoothedProbs[-1, 1]:.1%}"
            ),
        }

    # ── GDP Nowcasting (DFM) ──
    result["nowcast"] = None
    if market.upper() == "US":
        indicator_ids = ["INDPRO", "PAYEMS", "RSAFS", "ICSA", "PERMIT", "SP500"]
        series_list = [fetch_series_list(g, sid) for sid in indicator_ids]
        valid = [s for s in series_list if s is not None]
        if len(valid) == len(indicator_ids):
            min_len = min(len(s) for s in valid)
            if min_len >= 30:
                indicators_arr = np.column_stack([s[-min_len:] for s in valid])
                nc = gdpNowcast(indicators_arr, nFactors=1, arOrder=1, maxIter=30)
                result["nowcast"] = {
                    "gdpEstimate": nc.gdpEstimate, "confidence": nc.confidence,
                    "factorCurrent": nc.factorCurrent, "converged": nc.converged,
                    "description": nc.description,
                }

    # 시계열
    if market.upper() == "US":
        result["timeseries"] = collect_timeseries(g, {"t10y3m": "T10Y3M", "sp500": "SP500", "permit": "PERMIT"})
    else:
        result["timeseries"] = collect_timeseries(g, {"cli": "CLI", "cci": "CCI"})

    return result
