"""매크로 위기 감지 — Credit-to-GDP Gap + GHS 위기예측 + 침체 대시보드.

투자전략 32: 신용스프레드는 곧 설비투자조정압력이다
투자전략 33: 공급과잉은 대부분 도산을 수반한다
투자전략 35: 국내 신용위험은 소비자물가상승률과 상관관계가 높다
투자전략 38: 금융시장 위험이 커지면 달러화는 상승한다
"""

from __future__ import annotations

from dartlab.core.finance.crisisDetector import (
    creditToGDPGap,
    fisherDebtDeflation,
    ghsCrisisScore,
    kooBalanceSheetRecession,
    krHousingFinancialStress,
    minskyPhase,
    recessionDashboard,
)
from dartlab.core.finance.liquidity import capexPressure


def _fetch_crisis_data(market: str, as_of: str | None = None) -> dict[str, float | list | None]:
    """gather에서 위기 감지 지표 수집."""
    from dartlab.macro._helpers import fetch_change_pct, fetch_latest, fetch_series_list, fetch_yoy, get_gather

    g = get_gather(as_of)
    data: dict[str, float | list | None] = {}

    if market.upper() == "US":
        # HY 시계열 (bps 변환)
        hy_list = fetch_series_list(g, "BAMLH0A0HYM2")
        if hy_list:
            data["hy_series"] = [v * 100 for v in hy_list]
            data["hy_current"] = hy_list[-1] * 100

        # S&P500 3년 수익률
        sp_list = fetch_series_list(g, "SP500")
        if sp_list and len(sp_list) > 750:
            if sp_list[-750] > 0:
                data["sp500_3y_return"] = ((sp_list[-1] / sp_list[-750]) - 1) * 100

        data["vix"] = fetch_latest(g, "VIXCLS")

        # 달러인덱스
        dxy_list = fetch_series_list(g, "DTWEXBGS")
        if dxy_list and len(dxy_list) > 60:
            data["dxy_current"] = dxy_list[-1]
            data["dxy_3m_ago"] = dxy_list[-60]

        # Credit-to-GDP
        credit_list = fetch_series_list(g, "TCMDO")
        gdp_list = fetch_series_list(g, "GDP")
        if credit_list and gdp_list:
            min_len = min(len(credit_list), len(gdp_list))
            ratios = [credit_list[i] / gdp_list[i] * 100 for i in range(min_len) if gdp_list[i] > 0]
            if ratios:
                data["credit_gdp_series"] = ratios

    elif market.upper() == "KR":
        credit_list = fetch_series_list(g, "CREDIT_TOTAL")
        gdp_list = fetch_series_list(g, "GDP")
        if credit_list and gdp_list:
            min_len = min(len(credit_list), len(gdp_list))
            ratios = [credit_list[i] / gdp_list[i] * 100 for i in range(min_len) if gdp_list[i] > 0]
            if ratios:
                data["credit_gdp_series"] = ratios

        data["cpi_yoy"] = fetch_yoy(g, "CPI")
        data["apt_yoy"] = fetch_yoy(g, "APT_PRICE")

    # Koo BSR (US)
    if market.upper() == "US":
        for label, sid in [
            ("private_saving", "W987RC1Q027SBEA"), ("private_investment", "GPDI"),
            ("gdp_level", "GDP"), ("fed_funds", "FEDFUNDS"),
            ("dsr", "TDSP"), ("npl", "DRSFRMACBS"),
        ]:
            data[label] = fetch_latest(g, sid)
        data["us_cpi_yoy"] = fetch_yoy(g, "CPIAUCSL")

    return {k: v for k, v in data.items() if v is not None}


def analyze_crisis(*, market: str = "US", as_of: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """위기 감지 종합 분석.

    Returns:
        dict: creditGap, ghsScore, capexPressure, recessionDashboard,
              dollarSafeHaven, timeseries
    """
    data = _fetch_crisis_data(market, as_of=as_of)
    if overrides:
        from dartlab.macro._helpers import apply_overrides
        data = apply_overrides(data, overrides)
    result: dict = {"market": market.upper()}

    # Credit-to-GDP Gap
    credit_gdp_series = data.get("credit_gdp_series")
    if credit_gdp_series and len(credit_gdp_series) >= 4:
        gap_result = creditToGDPGap(credit_gdp_series)
        result["creditGap"] = {
            "gap": gap_result.gap,
            "trend": gap_result.trend,
            "actual": gap_result.actual,
            "zone": gap_result.zone,
            "zoneLabel": gap_result.zoneLabel,
            "ccybBuffer": gap_result.ccybBuffer,
            "description": gap_result.description,
        }
        credit_gap_val = gap_result.gap
    else:
        result["creditGap"] = None
        credit_gap_val = None

    # GHS 위기 점수
    sp500_3y = data.get("sp500_3y_return")
    if credit_gdp_series and sp500_3y is not None:
        # 3년 신용 변화
        if len(credit_gdp_series) >= 12:  # 분기 데이터 3년
            credit_3y = credit_gdp_series[-1] - credit_gdp_series[-12]
        elif len(credit_gdp_series) >= 4:
            credit_3y = credit_gdp_series[-1] - credit_gdp_series[0]
        else:
            credit_3y = 0

        ghs = ghsCrisisScore(credit_3y, sp500_3y)
        result["ghsScore"] = {
            "score": ghs.score,
            "zone": ghs.zone,
            "zoneLabel": ghs.zoneLabel,
            "components": ghs.components,
            "crisisProb": ghs.crisisProb,
            "description": ghs.description,
        }
    else:
        result["ghsScore"] = None

    # 설비투자 압력 (전략 32)
    hy_series = data.get("hy_series")
    hy_current = data.get("hy_current")
    if hy_current is not None and hy_series and len(hy_series) > 60:
        hy_3m_ago = hy_series[-60]
        hy_change = hy_current - hy_3m_ago
        capex = capexPressure(hy_current, hy_change)
        result["capexPressure"] = {
            "pressure": capex.pressure,
            "pressureLabel": capex.pressureLabel,
            "spreadLevel": capex.spreadLevel,
            "spreadChange": capex.spreadChange,
            "description": capex.description,
        }
    else:
        result["capexPressure"] = None

    # 달러 안전자산 효과 (전략 38)
    vix = data.get("vix")
    dxy_current = data.get("dxy_current")
    dxy_3m = data.get("dxy_3m_ago")
    if vix is not None and dxy_current is not None and dxy_3m is not None and dxy_3m > 0:
        dxy_change = ((dxy_current / dxy_3m) - 1) * 100
        if vix > 25 and dxy_change > 2:
            safe_haven = "active"
            safe_label = "활성"
            desc = f"VIX {vix:.1f} + 달러 {dxy_change:+.1f}% — 안전자산 수요로 달러 강세"
        elif vix > 20:
            safe_haven = "mild"
            safe_label = "경미"
            desc = f"VIX {vix:.1f} + 달러 {dxy_change:+.1f}% — 약한 안전자산 효과"
        else:
            safe_haven = "inactive"
            safe_label = "비활성"
            desc = f"VIX {vix:.1f} — 금융위험 낮음, 달러 안전자산 효과 없음"
        result["dollarSafeHaven"] = {
            "status": safe_haven,
            "statusLabel": safe_label,
            "vix": round(vix, 1),
            "dxyChange3m": round(dxy_change, 1),
            "description": desc,
        }
    else:
        result["dollarSafeHaven"] = None

    # 침체 대시보드 (다른 축 결과 필요 — 독립 실행 시 가용 데이터만 사용)
    probit_prob = kwargs.get("probitProb")
    lei_signal = kwargs.get("leiSignal")
    ism_level = kwargs.get("ismLevel")

    dashboard = recessionDashboard(
        probitProb=probit_prob,
        leiSignal=lei_signal,
        ismLevel=ism_level,
        creditGap=credit_gap_val,
        hySpread=hy_current,
    )
    result["recessionDashboard"] = {
        "composite": dashboard.composite,
        "zone": dashboard.zone,
        "zoneLabel": dashboard.zoneLabel,
        "components": dashboard.components,
        "historicalMatch": dashboard.historicalMatch,
        "description": dashboard.description,
    }

    # ── Minsky 5단계 ──
    result["minskyPhase"] = None
    try:
        dxy_chg_val = None
        if dxy_current is not None and data.get("dxy_3m_ago") is not None:
            d3m = data["dxy_3m_ago"]
            if d3m > 0:
                dxy_chg_val = ((dxy_current / d3m) - 1) * 100
        mk = minskyPhase(
            creditGap=credit_gap_val,
            assetReturn3y=data.get("sp500_3y_return"),
            hySpread=hy_current,
            vix=vix,
            dxyChange=dxy_chg_val,
        )
        result["minskyPhase"] = {
            "phase": mk.phase,
            "phaseLabel": mk.phaseLabel,
            "confidence": mk.confidence,
            "signals": mk.signals,
            "description": mk.description,
        }
    except Exception:
        pass

    # ── Koo Balance Sheet Recession (US) ──
    result["kooRecession"] = None
    if market.upper() == "US":
        try:
            saving = data.get("private_saving")
            investment = data.get("private_investment")
            gdp_level = data.get("gdp_level")
            ff = data.get("fed_funds")
            if saving is not None and investment is not None and gdp_level is not None and ff is not None:
                koo = kooBalanceSheetRecession(saving, investment, gdp_level, ff)
                result["kooRecession"] = {
                    "privateSurplus": koo.privateSurplus,
                    "policyRate": koo.policyRate,
                    "isBSR": koo.isBSR,
                    "description": koo.description,
                }
        except Exception:
            pass

    # ── Fisher Debt-Deflation (US) ──
    result["fisherDeflation"] = None
    if market.upper() == "US":
        try:
            dsr = data.get("dsr")
            us_cpi = data.get("us_cpi_yoy")
            npl = data.get("npl")
            if dsr is not None and us_cpi is not None:
                fisher = fisherDebtDeflation(dsr, us_cpi, npl)
                result["fisherDeflation"] = {
                    "dsr": fisher.dsr,
                    "nplRate": fisher.nplRate,
                    "cpiYoy": fisher.cpiYoy,
                    "risk": fisher.risk,
                    "riskLabel": fisher.riskLabel,
                    "description": fisher.description,
                }
        except Exception:
            pass

    # ── KR 부동산-금융 스트레스 ──
    if market.upper() == "KR":
        try:
            apt_yoy = data.get("apt_yoy")
            if apt_yoy is not None:
                hs = krHousingFinancialStress(apt_yoy)
                result["krHousingStress"] = {
                    "housePriceYoy": hs.housePriceYoy,
                    "stress": hs.stress,
                    "stressLabel": hs.stressLabel,
                    "description": hs.description,
                }
        except Exception:
            pass

    # 한국 신용위험 ↔ CPI (전략 35)
    if market.upper() == "KR":
        cpi_yoy = data.get("cpi_yoy")
        if cpi_yoy is not None:
            if cpi_yoy > 4:
                cr_signal = "CPI 상승률 높음 → 신용위험 확대 경계"
            elif cpi_yoy > 2:
                cr_signal = "CPI 안정 → 신용위험 보통"
            else:
                cr_signal = "CPI 둔화 → 신용위험 낮음"
            result["krCreditRisk"] = {
                "cpiYoy": round(cpi_yoy, 1),
                "signal": cr_signal,
            }

    from dartlab.macro._helpers import collect_timeseries, get_gather

    g_ts = get_gather(as_of)
    result["timeseries"] = collect_timeseries(g_ts, {"hy_spread": "BAMLH0A0HYM2", "vix": "VIXCLS", "dxy": "DTWEXBGS"})

    return result
