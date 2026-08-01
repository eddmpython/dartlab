"""analysis/valuation/dFV Two-Stage DCF resolver 헬퍼 분리.

dFV.py 가 853 줄 god module 이라 _tsd* 7 helper 분리.
identity 보존을 위해 dFV.py 가 본 모듈에서 re-export 한다.

함수 (Damodaran Multi-stage DCF resolver chain):
- _tsdResolveWacc: WACC override chain
- _tsdResolveHighGrowth: high-growth rate 해결
- _tsdBuildPhases: life phase → years/growth list 구성
- _tsdResolveTerminalGrowth: terminal growth (life phase + country)
- _tsdExtractBaseFcf: base FCF 추출
- _tsdMaybeNormalizeFcf: 정규화 (early-life 회사 음수 FCF 보정)
- _tsdExtractNetDebtShares: net debt + shares 추출
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.valuation._valuationInputAccess import _balanceValue


def _lazy(name):
    """dFV 본체 lazy lookup. 순환 import 회피."""
    import importlib

    return getattr(importlib.import_module("dartlab.analysis.valuation.dFV"), name)


def _inferShares(company, basePeriod: str | None = None):
    """dFV._inferShares lazy proxy. 본체로 위임."""
    return _lazy("_inferShares")(company, basePeriod=basePeriod)


def _tsdResolveWacc(company: Any, overrides: dict, basePeriod: str | None = None) -> float:
    """WACC 해결: override chain (forced/implied/bottomUp/country) → roic fallback → 9.0.

    Returns
    -------
    float
        Phase 4 G13 우선순위: forced wacc → Damodaran override path (compute_company_wacc)
        → calcRoicTimeline waccEstimate → 9.0 (최종 폴백).
    """
    try:
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline
        from dartlab.synth.overrides import applyOverride
    except ImportError:
        return 9.0

    forced_wacc = applyOverride(None, "wacc", overrides)
    implied_flag = applyOverride(False, "impliedERP", overrides)
    bottom_up_flag = applyOverride(False, "bottomUpBeta", overrides)
    country_code = applyOverride(None, "countryCode", overrides)

    if forced_wacc is not None:
        return float(forced_wacc)

    if implied_flag or bottom_up_flag or country_code:
        try:
            from dartlab.analysis.financial.proforma import computeCompanyWacc

            # 예전에는 company._series 를 먼저 봤는데 그 이름은 Company 에 없어 늘
            # 건너뛰었다. 실제 공급원은 재무 accessor 하나다.
            series = getattr(getattr(company, "_finance", None), "series", None)

            if series:
                wacc_val, _details = computeCompanyWacc(
                    series,
                    currency=getattr(company, "currency", "KRW"),
                    country=country_code,
                    impliedErp=bool(implied_flag),
                    bottomUpBeta=bool(bottom_up_flag),
                )
                return float(wacc_val)
        except (ImportError, AttributeError, ValueError, TypeError):
            pass

    try:
        roic = calcRoicTimeline(company, basePeriod=basePeriod)
        if roic and roic.get("history"):
            v = roic["history"][0].get("waccEstimate")
            if v is not None:
                return float(v)
    except (AttributeError, ValueError, TypeError):
        pass

    return 9.0


def _tsdResolveHighGrowth(company: Any, basePeriod: str | None = None) -> float:
    """매출 CAGR 기반 고성장률. 기본 8.0%, clamp [-5%, 25%].

    Returns
    -------
    float
        calcGrowthTrend cagr.revenue → 폴백 8.0 → 상·하한 clamp.
    """
    try:
        from dartlab.analysis.financial.growthAnalysis import calcGrowthTrend
    except ImportError:
        return 8.0
    highG: float | None = None
    try:
        g = calcGrowthTrend(company, basePeriod=basePeriod)
        if g:
            highG = (g.get("cagr") or {}).get("revenue")
    except (AttributeError, ValueError, TypeError):
        pass
    if highG is None:
        highG = 8.0
    return max(-5.0, min(highG, 25.0))


def _tsdBuildPhases(lifePhase: str | None, highG: float, overrides: dict) -> tuple[list[int], list[float]]:
    """lifeCycle 별 phase 구성 (Damodaran Ch.12) + growthRates override.

    Returns
    -------
    (years_vec, rates_vec)
        phase 별 연수 리스트 와 성장률 리스트. growthRates override 있으면 교체
        (연수 는 10년 을 len 으로 균등 분할).
    """
    try:
        from dartlab.synth.overrides import applyOverride
    except ImportError:
        return [5], [highG]

    phase_config: dict[str, tuple[list[int], list[float]]] = {
        "earlyGrowth": ([5, 3, 2], [highG, highG * 0.5, highG * 0.2]),
        "highGrowth": ([5, 3, 2], [highG, highG * 0.7, highG * 0.4]),
        "matureGrowth": ([4], [min(highG, 8.0)]),
        "matureStable": ([3], [min(highG, 3.0)]),
        "decline": ([2], [min(highG, -2.0) if highG < 0 else min(highG, 0.0)]),
        "turnaround": ([5], [highG]),
    }
    years_vec, rates_vec = phase_config.get(lifePhase or "", ([5], [highG]))

    rates_override = applyOverride(None, "growthRates", overrides)
    if isinstance(rates_override, list) and rates_override:
        rates_vec = rates_override
        if len(years_vec) != len(rates_vec):
            years_vec = [max(1, 10 // len(rates_vec))] * len(rates_vec)

    return years_vec, rates_vec


def _tsdResolveTerminalGrowth(lifePhase: str | None, company: Any, overrides: dict) -> float:
    """영구성장률. Phase 4 G12.3 phase 별 Rf 감쇠 매핑 + terminalGrowth override.

    Returns
    -------
    float
        Damodaran ERP riskFreeRate 기준 phase 별 감쇠값. override 있으면 우선.
    """
    try:
        from dartlab.synth.overrides import applyOverride
        from dartlab.synth.riskPremiums import loadDamodaranERP
    except ImportError:
        return 2.5

    currency = getattr(company, "currency", None)
    country = applyOverride(None, "countryCode", overrides)
    erp = loadDamodaranERP(countryCode=country, currency=currency)
    rf = erp["riskFreeRate"]
    tg_by_phase = {
        "earlyGrowth": max(2.0, rf - 0.5),
        "highGrowth": max(2.0, rf - 1.0),
        "matureGrowth": max(2.0, rf - 1.5),
        "matureStable": max(1.5, rf - 2.0),
        "decline": 0.5,
        "turnaround": max(2.0, rf - 1.0),
    }
    tg_default = tg_by_phase.get(lifePhase or "", max(1.0, rf - 1.0))
    return float(applyOverride(tg_default, "terminalGrowth", overrides))


def _tsdExtractBaseFcfInput(company: Any, basePeriod: str | None = None) -> dict | None:
    """기간 제한을 적용한 mid-cycle FCF 입력과 사용 기간을 반환한다."""
    try:
        from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
    except ImportError:
        return None
    try:
        cf = company.select("CF", ["영업활동현금흐름", "유형자산의취득"])
        parsed = toDictBySnakeId(cf)
        if not parsed:
            return None
        data, periods = parsed
        ocf_row = data.get("operating_cashflow") or {}
        capex_row = data.get("purchase_of_property_plant_and_equipment") or {}
        annual_years = annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=5)
        fcf_history: list[tuple[str, float]] = []
        for year in annual_years:
            ocf = ocf_row.get(year)
            capex = capex_row.get(year)
            if ocf:
                fcf_history.append((year, float(ocf) - abs(float(capex or 0))))
        positives = sorted(value for _, value in fcf_history if value > 0)
        if positives:
            return {
                "value": positives[len(positives) // 2],
                "periods": [period for period, _ in fcf_history],
                "source": "CF.operatingCashflow-capex.medianPositive",
            }
    except (AttributeError, KeyError, TypeError, ValueError):
        pass
    return None


def _tsdExtractBaseFcf(company: Any, basePeriod: str | None = None) -> float | None:
    """최근 5개년 양수 FCF (ocf - |capex|) 중앙값 (mid-cycle) 추출.

    Returns
    -------
    float | None
        positives 리스트 의 median. 양수 FCF 하나도 없으면 None.
    """
    resolved = _tsdExtractBaseFcfInput(company, basePeriod=basePeriod)
    return resolved["value"] if resolved else None


def _tsdMaybeNormalizeFcf(
    baseFcf: float,
    lifePhase: str | None,
    company: Any,
    basePeriod: str | None = None,
) -> float:
    """Phase 5 G16: 사이클/회복/적자 이력 기업은 Normalized FCF 로 교체 (Damodaran Ch.22).

    Returns
    -------
    float
        needsNormalized False 이면 base_fcf 그대로, True 면 calcNormalizedFcf 결과.
    """
    try:
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline
        from dartlab.analysis.financial.normalized import calcNormalizedFcf, needsNormalized
        from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
    except ImportError:
        return baseFcf

    roic_history_data: list[dict] = []
    try:
        roic = calcRoicTimeline(company, basePeriod=basePeriod)
        if roic and roic.get("history"):
            roic_history_data = roic["history"]
    except (AttributeError, ValueError, TypeError):
        pass

    if not needsNormalized(lifePhase, roic_history_data):
        return baseFcf

    rev_history: list[float] = []
    margin_history: list[float] = []
    try:
        is_rev = company.select("IS", ["매출액", "영업이익"])
        is_parsed = toDictBySnakeId(is_rev)
        if is_parsed:
            is_data, is_periods = is_parsed
            rev_row = is_data.get("sales") or {}
            op_row = is_data.get("operating_profit") or {}
            annual_ys = annualColsFromPeriods(is_periods, basePeriod=basePeriod, maxYears=5)
            for y in annual_ys:
                rv = rev_row.get(y)
                op = op_row.get(y)
                if rv and isinstance(rv, (int, float)) and rv > 0:
                    rev_history.append(float(rv))
                    margin_history.append(float(op) / float(rv) if op else 0.0)
    except (AttributeError, KeyError, TypeError, ValueError):
        return baseFcf

    try:
        norm = calcNormalizedFcf(rev_history, margin_history)
        if norm["method"] != "skip" and norm["normalizedFcf"]:
            return float(norm["normalizedFcf"])
    except (AttributeError, ValueError, TypeError):
        pass
    return baseFcf


def _tsdExtractNetDebtSharesInput(company: Any, basePeriod: str | None = None) -> dict | None:
    """기간 제한을 적용한 순차입금과 주식수 입력을 반환한다."""
    try:
        from dartlab.analysis.valuation._valuationInputAccess import _inferSharesInput
        from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
    except ImportError:
        return None
    try:
        bs = company.select("BS", ["단기차입금", "장기차입금", "사채", "현금및현금성자산"])
        parsed = toDictBySnakeId(bs)
        if not parsed:
            return None
        data, periods = parsed
        annual_periods = annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=1)
        if not annual_periods:
            return None
        balance_period = annual_periods[0]
        net_debt = (
            _balanceValue(data, balance_period, "shortterm_borrowings", "short_term_borrowings", "short_term_debt")
            + _balanceValue(data, balance_period, "longterm_borrowings", "long_term_borrowings", "long_term_debt")
            + _balanceValue(data, balance_period, "debentures", "corporate_bonds", "사채")
            - _balanceValue(data, balance_period, "cash_and_cash_equivalents", "cash_and_equivalents")
        )
        shares = _inferSharesInput(company, basePeriod=basePeriod)
        if not shares:
            return None
        return {
            "netDebt": net_debt,
            "shares": shares["value"],
            "balancePeriod": balance_period,
            "sharesPeriod": shares.get("period"),
            "sharesSource": shares.get("source"),
        }
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


def _tsdExtractNetDebtShares(company: Any, basePeriod: str | None = None) -> tuple[float, float] | None:
    """순차입금 (단기+장기+사채 - 현금) + 발행주식수 추출.

    Returns
    -------
    (net_debt, shares) | None
        BS periods 없거나 예외 시 None.
    """
    resolved = _tsdExtractNetDebtSharesInput(company, basePeriod=basePeriod)
    if not resolved:
        return None
    return resolved["netDebt"], resolved["shares"]


__all__ = [
    "_tsdBuildPhases",
    "_tsdExtractBaseFcf",
    "_tsdExtractBaseFcfInput",
    "_tsdExtractNetDebtShares",
    "_tsdExtractNetDebtSharesInput",
    "_tsdMaybeNormalizeFcf",
    "_tsdResolveHighGrowth",
    "_tsdResolveTerminalGrowth",
    "_tsdResolveWacc",
]
