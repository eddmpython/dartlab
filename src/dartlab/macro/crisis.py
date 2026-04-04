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


def _fetch_crisis_data(market: str) -> dict[str, float | list | None]:
    """gather에서 위기 감지 지표 수집."""
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    data: dict[str, float | list | None] = {}

    if market.upper() == "US":
        # HY 스프레드 (시계열)
        try:
            hy_df = g.macro("BAMLH0A0HYM2")
            if hy_df is not None and len(hy_df) > 0:
                vals = hy_df.get_column("value").drop_nulls().to_list()
                if vals:
                    data["hy_series"] = [float(v) * 100 for v in vals]  # % → bps
                    data["hy_current"] = float(vals[-1]) * 100
        except Exception:
            pass

        # S&P500 (3년 수익률)
        try:
            sp_df = g.macro("SP500")
            if sp_df is not None and len(sp_df) > 0:
                vals = sp_df.get_column("value").drop_nulls().to_list()
                if vals and len(vals) > 750:  # ~3년 일간
                    current = float(vals[-1])
                    three_y_ago = float(vals[-750])
                    if three_y_ago > 0:
                        data["sp500_3y_return"] = ((current / three_y_ago) - 1) * 100
        except Exception:
            pass

        # VIX
        try:
            vix_df = g.macro("VIXCLS")
            if vix_df is not None and len(vix_df) > 0:
                vals = vix_df.get_column("value").drop_nulls()
                if len(vals) > 0:
                    data["vix"] = float(vals[-1])
        except Exception:
            pass

        # 달러인덱스 (위기 시 상승 — 전략 38)
        try:
            dxy_df = g.macro("DTWEXBGS")
            if dxy_df is not None and len(dxy_df) > 0:
                vals = dxy_df.get_column("value").drop_nulls().to_list()
                if vals and len(vals) > 60:
                    data["dxy_current"] = float(vals[-1])
                    data["dxy_3m_ago"] = float(vals[-60])
        except Exception:
            pass

        # Credit-to-GDP (TCMDO / GDP)
        try:
            credit_df = g.macro("TCMDO")
            gdp_df = g.macro("GDP")
            if credit_df is not None and gdp_df is not None:
                c_vals = credit_df.get_column("value").drop_nulls().to_list()
                g_vals = gdp_df.get_column("value").drop_nulls().to_list()
                if c_vals and g_vals:
                    # 두 시리즈 길이 맞추기 (분기)
                    min_len = min(len(c_vals), len(g_vals))
                    ratios = []
                    for i in range(min_len):
                        gdp_val = float(g_vals[i])
                        if gdp_val > 0:
                            ratios.append(float(c_vals[i]) / gdp_val * 100)
                    if ratios:
                        data["credit_gdp_series"] = ratios
        except Exception:
            pass

    elif market.upper() == "KR":
        # 한국 총국내신용/GDP
        try:
            credit_df = g.macro("CREDIT_TOTAL")
            gdp_df = g.macro("GDP")
            if credit_df is not None and gdp_df is not None:
                c_vals = credit_df.get_column("value").drop_nulls().to_list()
                g_vals = gdp_df.get_column("value").drop_nulls().to_list()
                if c_vals and g_vals:
                    min_len = min(len(c_vals), len(g_vals))
                    ratios = []
                    for i in range(min_len):
                        gdp_val = float(g_vals[i])
                        if gdp_val > 0:
                            ratios.append(float(c_vals[i]) / gdp_val * 100)
                    if ratios:
                        data["credit_gdp_series"] = ratios
        except Exception:
            pass

        # 한국 CPI (전략 35: 신용위험 ↔ CPI)
        try:
            cpi_df = g.macro("CPI")
            if cpi_df is not None and len(cpi_df) > 0:
                vals = cpi_df.get_column("value").drop_nulls().to_list()
                if vals and len(vals) > 12:
                    data["cpi_yoy"] = ((float(vals[-1]) / float(vals[-13])) - 1) * 100
        except Exception:
            pass

        # 한국 아파트가격 YoY (부동산 스트레스)
        try:
            apt_df = g.macro("APT_PRICE")
            if apt_df is not None and len(apt_df) > 0:
                vals = apt_df.get_column("value").drop_nulls().to_list()
                if vals and len(vals) > 12:
                    data["apt_yoy"] = ((float(vals[-1]) / float(vals[-13])) - 1) * 100
        except Exception:
            pass

    # ── Koo BSR 데이터 (US) ──
    if market.upper() == "US":
        for label, sid in [
            ("private_saving", "W987RC1Q027SBEA"),
            ("private_investment", "GPDI"),
            ("gdp_level", "GDP"),
            ("fed_funds", "FEDFUNDS"),
        ]:
            try:
                df = g.macro(sid)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls()
                    if len(vals) > 0:
                        data[label] = float(vals[-1])
            except Exception:
                pass

        # Fisher: DSR, NPL
        for label, sid in [("dsr", "TDSP"), ("npl", "DRSFRMACBS")]:
            try:
                df = g.macro(sid)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls()
                    if len(vals) > 0:
                        data[label] = float(vals[-1])
            except Exception:
                pass

        # CPI YoY for Fisher
        try:
            cpi_df = g.macro("CPIAUCSL")
            if cpi_df is not None and len(cpi_df) > 0:
                vals = cpi_df.get_column("value").drop_nulls().to_list()
                if vals and len(vals) > 12:
                    data["us_cpi_yoy"] = ((float(vals[-1]) / float(vals[-13])) - 1) * 100
        except Exception:
            pass

    return data


def analyze_crisis(*, market: str = "US", as_of: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """위기 감지 종합 분석.

    Returns:
        dict: creditGap, ghsScore, capexPressure, recessionDashboard,
              dollarSafeHaven, timeseries
    """
    data = _fetch_crisis_data(market)
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

    # 시계열
    from dartlab.macro._helpers import recent_timeseries

    ts: dict = {}
    try:
        from dartlab.gather import getDefaultGather

        g = getDefaultGather()
        for label, sid in [("hy_spread", "BAMLH0A0HYM2"), ("vix", "VIXCLS"), ("dxy", "DTWEXBGS")]:
            ts[label] = recent_timeseries(g.macro(sid))
    except Exception:
        pass
    result["timeseries"] = ts

    return result
