"""매크로 예측 — LEI + 침체확률 + Hamilton RS + GDP Nowcasting.

투자전략 1: 금리 추이는 전기비 성장률에 의해 결정된다
투자전략 2: 주가지수는 명목 GDP증가율과 상관관계가 높다
투자전략 16: 전기비 성장률은 '선행지수 증가율+후행지수 증가율'이다

Hamilton (1989): Markov Regime Switching으로 확률적 경기국면 판별
Banbura et al. (2011): Dynamic Factor Model로 GDP 실시간 추정
"""

from __future__ import annotations

import numpy as np

from dartlab.core.finance.regimeSwitching import clevelandProbit, conferenceBoardLEI, hamiltonRegime
from dartlab.core.finance.nowcast import gdpNowcast


def _fetch_forecast_data(market: str) -> dict[str, float | list | None]:
    """gather에서 LEI 구성요소 + 프로빗 입력 수집."""
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    data: dict[str, float | list | None] = {}

    if market.upper() == "US":
        # T10Y3M (프로빗 입력)
        for label, sid in [
            ("t10y3m", "T10Y3M"),
            ("awhman", "AWHMAN"),
            ("icsa", "ICSA"),
            ("acogno", "ACOGNO"),
            ("napmnoi", "NAPMNOI"),
            ("acdgno", "ACDGNO"),
            ("permit", "PERMIT"),
            ("sp500", "SP500"),
            ("m2real", "M2REAL"),
            ("umcsent", "UMCSENT"),
            ("fedfunds", "FEDFUNDS"),
            ("dgs10", "DGS10"),
        ]:
            try:
                df = g.macro(sid)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls().to_list()
                    if vals:
                        data[label] = float(vals[-1])
                        if len(vals) > 1:
                            data[f"{label}_prev"] = float(vals[-2])
                        if len(vals) > 6:
                            data[f"{label}_6m"] = float(vals[-7])
            except Exception:
                pass

    elif market.upper() == "KR":
        # 한국: CLI + CCI + 후행
        for label, sid in [
            ("cli", "CLI"),
            ("cci", "CCI"),
            ("cli_lag", "CLI_LAG"),
        ]:
            try:
                df = g.macro(sid)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls().to_list()
                    if vals:
                        data[label] = float(vals[-1])
                        if len(vals) > 1:
                            data[f"{label}_prev"] = float(vals[-2])
                        if len(vals) > 6:
                            data[f"{label}_6m"] = float(vals[-7])
            except Exception:
                pass

    return data


def _pct_change(current: float | None, prev: float | None) -> float | None:
    """전기대비 변화율 (%)."""
    if current is None or prev is None or prev == 0:
        return None
    return ((current - prev) / abs(prev)) * 100


def analyze_forecast(*, market: str = "US", **kwargs) -> dict:
    """경제 예측 종합 분석.

    Returns:
        dict: recessionProb, lei, growthMomentum, timeseries
    """
    data = _fetch_forecast_data(market)
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

    # ── Hamilton Regime Switching ──
    # GDP 성장률 시계열이 있으면 확률적 국면 판별
    result["hamiltonRegime"] = None
    try:
        from dartlab.gather import getDefaultGather as _g2

        g2 = _g2()
        gdp_id = "A191RL1Q225SBEA" if market.upper() == "US" else "GROWTH"
        gdp_df = g2.macro(gdp_id)
        if gdp_df is not None and len(gdp_df) > 0:
            gdp_vals = gdp_df.get_column("value").drop_nulls().to_list()
            if len(gdp_vals) >= 20:
                hr = hamiltonRegime([float(v) for v in gdp_vals], maxIter=100)
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
    except Exception:
        pass

    # ── GDP Nowcasting (DFM) ──
    # 여러 거시지표의 공통 팩터로 GDP 실시간 추정
    result["nowcast"] = None
    if market.upper() == "US":
        try:
            from dartlab.gather import getDefaultGather as _g3

            g3 = _g3()
            # Nowcast 입력: 핵심 월간 지표 + GDP(분기)
            indicator_ids = ["INDPRO", "PAYEMS", "RSAFS", "ICSA", "PERMIT", "SP500"]
            series_list = []
            min_len = 999
            for sid in indicator_ids:
                df = g3.macro(sid)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls().to_list()
                    series_list.append([float(v) for v in vals])
                    min_len = min(min_len, len(vals))
                else:
                    series_list.append(None)

            # 최소 공통 길이로 정렬
            if min_len >= 30 and all(s is not None for s in series_list):
                indicators_arr = np.column_stack([s[-min_len:] for s in series_list])
                nc = gdpNowcast(indicators_arr, nFactors=1, arOrder=1, maxIter=30)
                result["nowcast"] = {
                    "gdpEstimate": nc.gdpEstimate,
                    "confidence": nc.confidence,
                    "factorCurrent": nc.factorCurrent,
                    "converged": nc.converged,
                    "description": nc.description,
                }
        except Exception:
            pass

    # 시계열
    from dartlab.macro._helpers import recent_timeseries

    ts: dict = {}
    try:
        from dartlab.gather import getDefaultGather

        g = getDefaultGather()
        if market.upper() == "US":
            for label, sid in [("t10y3m", "T10Y3M"), ("sp500", "SP500"), ("permit", "PERMIT")]:
                ts[label] = recent_timeseries(g.macro(sid))
        else:
            for label, sid in [("cli", "CLI"), ("cci", "CCI")]:
                ts[label] = recent_timeseries(g.macro(sid))
    except Exception:
        pass
    result["timeseries"] = ts

    return result
