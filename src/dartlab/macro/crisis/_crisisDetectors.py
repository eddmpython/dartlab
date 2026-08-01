"""매크로 위기 진단 헬퍼 16 종 — crisis.py 의 analyzeCrisis 가 호출.

각 ``_crisis*`` 헬퍼는 ``_fetchCrisisData`` 결과 dict + 보조 인자를 받아 도메인별 진단 dict
(또는 데이터 결손 시 None) 을 반환한다. analyzeCrisis 는 본 헬퍼들의 결과를 모아 종합 응답
구성. 본 모듈은 헬퍼 정의만 담는다.

도메인 분류:
- Credit/GDP gap + GHS 위기점수 + Capex 압력 + 달러 안전자산 (BIS · Greenwood-Hanson 표준)
- 역사적 맥락 (US 9 시계열 buildHistoricalContext)
- Minsky 5 단계 + Dalio 6 phase + 4 lever + 48 case + R&R 위기유형
- Koo Balance Sheet Recession + Fisher Debt-Deflation (US)
- KR 부동산 스트레스 + 신용위험 ↔ CPI (전략 35)
- Gilchrist-Zakrajšek EBP + Verdad Credit Cycle 4 단계
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

from dartlab.macro.crisis.detectors import (
    creditToGDPGap,
    dalioDebtCyclePhase,
    dalioPolicyLeverStatus,
    fisherDebtDeflation,
    ghsCrisisScore,
    kooBalanceSheetRecession,
    krHousingFinancialStress,
    minskyPhase,
)
from dartlab.macro.cycles.liquidity import capexPressure
from dartlab.macro.seriesFetch import getGather


def _frozenToDict(obj) -> dict | None:
    """frozen dataclass → dict 변환. None 이면 None 반환."""
    if obj is None:
        return None
    from dataclasses import asdict

    return asdict(obj)


def _crisisCreditGap(data: dict) -> tuple[dict | None, float | None]:
    """Credit-to-GDP Gap. 반환: (dict | None, gap_value | None)."""
    series = data.get("credit_gdp_series")
    if not (series and len(series) >= 4):
        return None, None
    gap_result = creditToGDPGap(series)
    return {
        "gap": gap_result.gap,
        "trend": gap_result.trend,
        "actual": gap_result.actual,
        "zone": gap_result.zone,
        "zoneLabel": gap_result.zoneLabel,
        "ccybBuffer": gap_result.ccybBuffer,
        "description": gap_result.description,
    }, gap_result.gap


def _crisisGhsScore(data: dict, creditGapVal, realRate) -> dict | None:
    """GHS 위기 점수. 반환: 구성요소/확률 포함 dict or None."""
    series = data.get("credit_gdp_series")
    sp500_3y = data.get("sp500_3y_return")
    if not (series and sp500_3y is not None):
        return None
    if len(series) >= 12:
        credit_3y = series[-1] - series[-12]
    elif len(series) >= 4:
        credit_3y = series[-1] - series[0]
    else:
        credit_3y = 0
    ghs = ghsCrisisScore(credit_3y, sp500_3y, realRate=realRate)
    return {
        "score": ghs.score,
        "zone": ghs.zone,
        "zoneLabel": ghs.zoneLabel,
        "components": ghs.components,
        "crisisProb": ghs.crisisProb,
        "description": ghs.description,
        "regime": ghs.regime,
        "regimeLabel": ghs.regimeLabel,
    }


def _crisisCapexPressure(data: dict) -> dict | None:
    """설비투자 압력 — HY 스프레드 수준 + 3개월 변화."""
    hy_series = data.get("hy_series")
    hyCurrent = data.get("hy_current")
    if hyCurrent is None or not (isinstance(hy_series, list) and len(hy_series) > 60):
        return None
    hy_change = hyCurrent - hy_series[-60]
    capex = capexPressure(hyCurrent, hy_change)
    return {
        "pressure": capex.pressure,
        "pressureLabel": capex.pressureLabel,
        "spreadLevel": capex.spreadLevel,
        "spreadChange": capex.spreadChange,
        "description": capex.description,
    }


def _crisisDollarSafeHaven(data: dict) -> dict | None:
    """VIX + 달러 3개월 변화 → 안전자산 효과 상태. 반환: 상태 dict or None."""
    vix = data.get("vix")
    dxyCurrent = data.get("dxy_current")
    dxy_3m = data.get("dxy_3m_ago")
    if not (vix is not None and dxyCurrent is not None and dxy_3m and dxy_3m > 0):
        return None
    dxy_change = ((dxyCurrent / dxy_3m) - 1) * 100
    if vix > 25 and dxy_change > 2:
        status, label = "active", "활성"
        desc = f"VIX {vix:.1f} + 달러 {dxy_change:+.1f}% — 안전자산 수요로 달러 강세"
    elif vix > 20:
        status, label = "mild", "경미"
        desc = f"VIX {vix:.1f} + 달러 {dxy_change:+.1f}% — 약한 안전자산 효과"
    else:
        status, label = "inactive", "비활성"
        desc = f"VIX {vix:.1f} — 금융위험 낮음, 달러 안전자산 효과 없음"
    return {
        "status": status,
        "statusLabel": label,
        "vix": round(vix, 1),
        "dxyChange3m": round(dxy_change, 1),
        "description": desc,
    }


def _crisisHistoricalContext(market: str, asOf: str | None) -> dict | None:
    """역사적 맥락 (US 전용) — 9 시계열 기반 buildHistoricalContext 호출."""
    if market.upper() != "US":
        return None
    try:
        from dartlab.macro.corporate.historicalContext import buildHistoricalContext
        from dartlab.macro.seriesFetch import fetchMonthlyDict

        g_hist = getGather(asOf)
        hist_data: dict = {}
        for key, sid in [
            ("hy_spread", "BAMLH0A0HYM2"),
            ("spread_10y3m", "T10Y3M"),
            ("spread_10y2y", "T10Y2Y"),
            ("unrate", "UNRATE"),
            ("cpi_raw", "CPIAUCSL"),
            ("indpro", "INDPRO"),
            ("vix", "VIXCLS"),
            ("nfci", "NFCI"),
            ("fedfunds", "FEDFUNDS"),
        ]:
            md = fetchMonthlyDict(g_hist, sid)
            if md:
                hist_data[key] = md
        if not hist_data:
            return None
        hc = buildHistoricalContext(hist_data)
        return {
            "hySpike": _frozenToDict(hc.hySpike),
            "yieldCurveInversion": _frozenToDict(hc.yieldCurveInversion),
            "unemploymentBounce": _frozenToDict(hc.unemploymentBounce),
            "cpiAcceleration": hc.cpiAcceleration,
            "simultaneousWarnings": _frozenToDict(hc.simultaneousWarnings),
            "bullishSignals": _frozenToDict(hc.bullishSignals),
            "hyCompression": _frozenToDict(hc.hyCompression),
            "historicalEvents": [_frozenToDict(e) for e in hc.historicalEvents] if hc.historicalEvents else None,
            "riskLevel": hc.riskLevel,
            "riskLabel": hc.riskLabel,
            "opportunityLevel": hc.opportunityLevel,
            "opportunityLabel": hc.opportunityLabel,
            "suggestedScenario": hc.suggestedScenario,
            "suggestedScenarioReason": hc.suggestedScenarioReason,
            "description": hc.description,
            "status": hc.status,
            "observedInputs": hc.observedInputs,
            "totalInputs": hc.totalInputs,
        }
    except (ImportError, KeyError, ValueError, TypeError) as e:
        log.debug("역사적 맥락 계산 실패: %s", e)
        return None


def _crisisMinsky(data: dict, creditGapVal, hyCurrent, vix, dxyCurrent) -> dict | None:
    """Minsky 5단계. 반환: phase/label/confidence/signals dict or None."""
    try:
        dxy_chg_val = None
        d3m = data.get("dxy_3m_ago")
        if dxyCurrent is not None and d3m and d3m > 0:
            dxy_chg_val = ((dxyCurrent / d3m) - 1) * 100
        mk = minskyPhase(
            creditGap=creditGapVal,
            assetReturn3y=data.get("sp500_3y_return"),
            hySpread=hyCurrent,
            vix=vix,
            dxyChange=dxy_chg_val,
        )
        return {
            "phase": mk.phase,
            "phaseLabel": mk.phaseLabel,
            "confidence": mk.confidence,
            "signals": mk.signals,
            "description": mk.description,
            "status": mk.status,
            "observedInputs": mk.observedInputs,
            "totalInputs": mk.totalInputs,
        }
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


def _crisisDalioCaseMatch(data: dict, creditGapVal) -> list | None:
    """Dalio Part 2 detail case matching (Weimar/GD/Subprime)."""
    try:
        from dartlab.macro.scenarios.dalioCaseMatch import matchDalioDetailCase

        case_state = {
            "totalDebtToGdp": data.get("total_debt_to_gdp"),
            "creditGap": creditGapVal,
            "realRate": data.get("real_rate"),
            "gdpGrowth": data.get("gdp_growth"),
            "debtServiceYoY": data.get("debt_service_yoy"),
        }
        if not any(v is not None for v in case_state.values()):
            return None
        return matchDalioDetailCase(case_state, topK=3)
    except (ImportError, KeyError, ValueError, TypeError):
        return None


def _crisisDalio48Match(data: dict, creditGapVal) -> list | None:
    """Dalio Part 3 — 48 case compendium matching."""
    try:
        from dartlab.macro.scenarios.dalio48Match import match48Cases

        state_48 = {
            "peakDebtToGdp": data.get("total_debt_to_gdp"),
            "peakCreditGap": creditGapVal,
            "troughRealRate": data.get("real_rate"),
            "troughGdpGrowth": data.get("gdp_growth"),
        }
        if not any(v is not None for v in state_48.values()):
            return None
        return match48Cases(state_48, topK=5)
    except (ImportError, KeyError, ValueError, TypeError):
        return None


def _crisisRRTypes(data: dict, hyCurrent, market: str, kwargs: dict) -> tuple[dict | None, list | None]:
    """R&R 위기 유형 분류 + 역사 매칭. 반환: (crisisType dict, rrMatch list)."""
    try:
        from dartlab.macro.crisis.rrCrisisDB import classifyCrisisType, matchRrHistorical

        ct = classifyCrisisType(
            hySpread=hyCurrent,
            npl=data.get("npl"),
            fxDepreciationYoy=kwargs.get("fxDepreciationYoy"),
            inflationYoy=(data.get("us_cpi_yoy") if data.get("us_cpi_yoy") is not None else data.get("cpi_yoy")),
            sovereignSpread=kwargs.get("sovereignSpread"),
            gdpGrowth=data.get("gdp_growth"),
        )
        crisisType = {
            "activeTypes": ct["activeTypes"],
            "dominantType": ct["dominantType"],
            "isTripleCrisis": ct["isTripleCrisis"],
            "signals": ct["signals"],
        }
        rrMatch = None
        if ct["activeTypes"]:
            rrMatch = matchRrHistorical(
                ct["activeTypes"],
                country=market.upper() if market.upper() in ("US", "KR") else None,
                topK=3,
            )
        return crisisType, rrMatch
    except (ImportError, KeyError, ValueError, TypeError):
        return None, None


def _crisisDalioDebtCycle(data: dict, creditGapVal, kwargs: dict) -> tuple[dict | None, dict | None]:
    """Dalio Part 1 — 6 phase + 4 lever 소진도. 반환: (debtCyclePhase, policyLeverStatus)."""

    def _input(name: str, dataName: str):
        override = kwargs.get(name)
        return override if override is not None else data.get(dataName)

    try:
        dp = dalioDebtCyclePhase(
            totalDebtToGdp=_input("totalDebtToGdp", "total_debt_to_gdp"),
            debtServiceYoY=_input("debtServiceYoY", "debt_service_yoy"),
            creditGap=creditGapVal,
            realRate=_input("realRate", "real_rate"),
            gdpGrowth=_input("gdpGrowth", "gdp_growth"),
        )
        dp_dict = {
            "phase": dp.phase,
            "phaseLabel": dp.phaseLabel,
            "signals": list(dp.signals),
            "description": dp.description,
            "status": dp.status,
            "observedInputs": dp.observedInputs,
            "totalInputs": dp.totalInputs,
        }
        pl = dalioPolicyLeverStatus(
            policyRate=_input("policyRate", "fed_funds"),
            publicDebtToGdp=_input("publicDebtToGdp", "public_debt_to_gdp"),
            creditGap=creditGapVal,
            fxFlexibility=kwargs.get("fxFlexibility"),
        )
        pl_dict = {
            "monetary": pl.monetary,
            "fiscal": pl.fiscal,
            "credit": pl.credit,
            "fx": pl.fx,
            "exhaustionScore": pl.exhaustionScore,
            "signals": list(pl.signals),
            "status": pl.status,
            "observedInputs": pl.observedInputs,
            "totalInputs": pl.totalInputs,
        }
        return dp_dict, pl_dict
    except (KeyError, ValueError, TypeError, AttributeError):
        return None, None


def _crisisKooBsr(data: dict) -> dict | None:
    """Koo Balance Sheet Recession (US). 반환: dict or None."""
    try:
        saving = data.get("private_saving")
        investment = data.get("private_investment")
        gdp_level = data.get("gdp_level")
        ff = data.get("fed_funds")
        if not all(v is not None for v in (saving, investment, gdp_level, ff)):
            return None
        koo = kooBalanceSheetRecession(saving, investment, gdp_level, ff)
        return {
            "privateSurplus": koo.privateSurplus,
            "policyRate": koo.policyRate,
            "isBSR": koo.isBSR,
            "description": koo.description,
        }
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


def _crisisFisherDeflation(data: dict) -> dict | None:
    """Fisher Debt-Deflation (US). 반환: dict or None."""
    try:
        dsr = data.get("dsr")
        us_cpi = data.get("us_cpi_yoy")
        npl = data.get("npl")
        if dsr is None or us_cpi is None:
            return None
        fisher = fisherDebtDeflation(dsr, us_cpi, npl)
        return {
            "dsr": fisher.dsr,
            "nplRate": fisher.nplRate,
            "cpiYoy": fisher.cpiYoy,
            "risk": fisher.risk,
            "riskLabel": fisher.riskLabel,
            "description": fisher.description,
        }
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


def _crisisKrHousingStress(data: dict) -> dict | None:
    """KR 부동산-금융 스트레스. 반환: dict or None."""
    try:
        apt_yoy = data.get("apt_yoy")
        if apt_yoy is None:
            return None
        hs = krHousingFinancialStress(apt_yoy)
        return {
            "housePriceYoy": hs.housePriceYoy,
            "stress": hs.stress,
            "stressLabel": hs.stressLabel,
            "description": hs.description,
        }
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


def _crisisKrCreditRisk(data: dict) -> dict | None:
    """KR 신용위험 ↔ CPI (전략 35). 반환: dict or None."""
    cpiYoy = data.get("cpi_yoy")
    if cpiYoy is None:
        return None
    if cpiYoy > 4:
        signal = "CPI 상승률 높음 → 신용위험 확대 경계"
    elif cpiYoy > 2:
        signal = "CPI 안정 → 신용위험 보통"
    else:
        signal = "CPI 둔화 → 신용위험 낮음"
    return {"cpiYoy": round(cpiYoy, 1), "signal": signal}


def _crisisExcessBondPremium(asOf: str | None) -> dict | None:
    """Gilchrist-Zakrajšek EBP. 반환: classifyEBP dict or None."""
    try:
        from dartlab.macro.crisis.excessBondPremium import approximateEBP, classifyEBP
        from dartlab.macro.seriesFetch import fetchLatest as _fl
        from dartlab.macro.seriesFetch import getGather as _gg

        _g = _gg(asOf)
        _hy = _fl(_g, "BAMLH0A0HYM2")
        _baa_aaa = _fl(_g, "BAA10Y")
        if _hy is None or _baa_aaa is None:
            return None
        hy_bp = _hy * 100
        default_proxy = _baa_aaa * 150
        ebp_val = approximateEBP(hy_bp, default_proxy)
        return classifyEBP(ebp_val)
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


def _crisisCreditCycle(asOf: str | None) -> dict | None:
    """Verdad Credit Cycle 4단계 (Greenwood-Hanson-Jin 2019). 반환: classifyCreditCycle dict."""
    try:
        from dartlab.macro.crisis.creditCycleDetect import classifyCreditCycle
        from dartlab.macro.seriesFetch import fetchLatest as _fl2
        from dartlab.macro.seriesFetch import getGather as _gg2

        _g2 = _gg2(asOf)
        _hy2 = _fl2(_g2, "BAMLH0A0HYM2")
        if _hy2 is None:
            return None
        hy_bp2 = _hy2 * 100
        hy_6m = None
        try:
            from dartlab.macro.seriesFetch import fetchSeriesList as _fsl

            hy_list = _fsl(_g2, "BAMLH0A0HYM2")
            if hy_list and len(hy_list) > 125:
                hy_6m = hy_list[-125] * 100
        except (KeyError, ValueError, TypeError):
            pass
        loan = _fl2(_g2, "DRTSCLCC")
        co = _fl2(_g2, "CORCCACBS")
        return classifyCreditCycle(hy_bp2, hySpread6mAgo=hy_6m, loanTightening=loan, chargeOff=co)
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


__all__ = [
    "_crisisCapexPressure",
    "_crisisCreditCycle",
    "_crisisCreditGap",
    "_crisisDalio48Match",
    "_crisisDalioCaseMatch",
    "_crisisDalioDebtCycle",
    "_crisisDollarSafeHaven",
    "_crisisExcessBondPremium",
    "_crisisFisherDeflation",
    "_crisisGhsScore",
    "_crisisHistoricalContext",
    "_crisisKooBsr",
    "_crisisKrCreditRisk",
    "_crisisKrHousingStress",
    "_crisisMinsky",
    "_crisisRRTypes",
    "_frozenToDict",
]
