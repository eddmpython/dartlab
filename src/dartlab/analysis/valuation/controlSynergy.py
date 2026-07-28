"""Value of Control vs Synergy. Damodaran Dark Side Ch.17.

Control Value = Restructured Value − Status Quo Value
  (최적 자본배분 시나리오에서 얻을 수 있는 추가 가치)

Synergy Value = Combined NPV − (A standalone + B standalone)
  (합병 시 발생하는 추가 가치: cost / revenue / financial)

이중계산 방지: Control 과 Synergy 는 독립 계산, 합산 시 storyValidation 이 경고.
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.valuation._valuationInputAccess import _balanceValue, _inferShares

_DEFAULT_TAX = 0.22


def calcControlValue(
    company: Any,
    *,
    basePeriod: str | None = None,
    overrides: dict | None = None,
) -> dict[str, Any] | None:
    """Status Quo vs Restructured: 최적 자본배분 시나리오의 추가 가치.

    Capabilities:
        - calcDFV (status quo) + multiStageDcf (restructured) 차이 = Control Value
        - 섹터 p75 ROIC 부재 시 현재 × 1.3 근사 + warning
        - Damodaran Growth Equation (g = ROIC × reinvestRate) 적용

    Parameters
    ----------
    company : Company
        대상 기업.
    basePeriod : str, optional
        기준 기간.
    overrides : dict, optional
        optimalROIC 등 가정 override.

    Restructured 가정:
    - ROIC → sector p75
    - Reinvestment rate → sector p75
    - Growth = ROIC × reinvestmentRate (Damodaran equation)

    Returns
    -------
    dict | None
        statusQuoValue : float - 현재 경영 시나리오 DCF perShare
        restructuredValue : float - 최적 시나리오 DCF perShare
        controlPremium : float - restructured - statusQuo
        premiumPct : float - % 기준
        optimalROIC : float - 가정 ROIC (%)
        optimalReinvestment : float - 가정 재투자율 (%)
        method : "sector_p75"
        warnings : list[str]

    Example:
        >>> calcControlValue(Company("005930"))
        {"controlPremium": 12000, "premiumPct": 18.5, ...}

    Guide:
        Synergy 와 동시 합산 금지 (이중계산). storyValidation 이 경고.

    When:
        M&A 시나리오 분석 또는 행동주의/지배구조 개선 가치 답변 시.

    How:
        calcControlValue(company) 또는 overrides={"optimalROIC": 15} 형식.

    Requires:
        calcDFV + multiStageDcf + calcRoicTimeline + synth.overrides + riskPremiums.

    Raises:
        없음. 데이터 부족 시 None 또는 controlPremium=0.

    See Also:
        - calcSynergyValue : M&A 시너지 (본 함수와 독립 계산)
        - multiStageDcf : 재구축 시나리오 DCF 본체
        - Damodaran *Dark Side of Valuation* Ch.17

    AIContext:
        지배구조 변경/행동주의 가치 답변 시 controlPremium + premiumPct 인용.
    """
    overrides = overrides or {}
    warnings: list[str] = []

    try:
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline
        from dartlab.analysis.valuation.dcf import multiStageDcf
        from dartlab.analysis.valuation.dFV import calcDFV
        from dartlab.synth.overrides import applyOverride
        from dartlab.synth.riskPremiums import loadDamodaranERP
    except ImportError:
        return None

    # Status Quo = 기존 dFV
    status_quo = calcDFV(company, basePeriod=basePeriod)
    if not status_quo or not status_quo.get("dFV"):
        return None
    status_quo_value = status_quo["dFV"]

    # 현재 ROIC
    current_roic: float | None = None
    current_wacc: float | None = None
    try:
        r = calcRoicTimeline(company)
        if r and r.get("history"):
            current_roic = r["history"][0].get("roic")
            current_wacc = r["history"][0].get("waccEstimate")
    except (AttributeError, ValueError, TypeError):
        pass

    if current_wacc is None:
        current_wacc = 9.0

    # Optimal ROIC = 섹터 p75 (scan 필요). 미구현 시 현재 × 1.3 근사
    optimal_roic_pct = applyOverride(None, "optimalROIC", overrides)
    if optimal_roic_pct is None:
        if current_roic and current_roic > 0:
            optimal_roic_pct = min(current_roic * 1.3, current_wacc * 2.5)
            warnings.append("섹터 p75 ROIC 미수집으로 현재 × 1.3 근사")
        else:
            optimal_roic_pct = current_wacc * 1.5  # default 50% spread

    # Optimal reinvestment rate (Damodaran: g = ROIC × rr)
    # 가정: 타겟 성장률 = current_roic × 0.6 (재투자율 60%)
    optimal_reinvest = 0.6
    optimal_g = optimal_roic_pct * optimal_reinvest / 100.0 * 100  # %

    # Restructured: multiStageDcf 재실행
    ts = status_quo.get("twoStage", {})
    baseFcf = _estimateBaseFcf(company)
    if not baseFcf or baseFcf <= 0:
        warnings.append("baseFcf 추출 실패로 기본 DCF 사용")
        return {
            "statusQuoValue": status_quo_value,
            "restructuredValue": status_quo_value,
            "controlPremium": 0,
            "premiumPct": 0,
            "optimalROIC": optimal_roic_pct,
            "optimalReinvestment": optimal_reinvest * 100,
            "method": "sector_p75",
            "warnings": warnings,
        }

    currency = getattr(company, "currency", None)
    erp = loadDamodaranERP(currency=currency)
    tg = max(1.0, erp["riskFreeRate"] - 1.0)

    # Restructured DCF: 더 높은 성장률로 multi-stage
    restructured = multiStageDcf(
        baseFcf=baseFcf,
        growthYears=[5, 5],
        growthRates=[optimal_g, optimal_g * 0.5],
        terminalGrowthRate=tg,
        wacc=current_wacc,
        netDebt=_estimateNetDebt(company) or 0,
        shares=_inferShares(company),
    )
    restructured_value = restructured.get("perShare")
    if restructured_value is None:
        restructured_value = status_quo_value
        warnings.append("Restructured DCF 계산 실패")

    control_premium = restructured_value - status_quo_value
    premium_pct = (control_premium / status_quo_value * 100) if status_quo_value > 0 else 0

    return {
        "statusQuoValue": round(status_quo_value),
        "restructuredValue": round(restructured_value),
        "controlPremium": round(control_premium),
        "premiumPct": round(premium_pct, 2),
        "optimalROIC": round(optimal_roic_pct, 2),
        "optimalReinvestment": round(optimal_reinvest * 100, 2),
        "method": "sector_p75",
        "warnings": warnings,
    }


def calcSynergyValue(
    acquirer: Any,
    target: Any,
    *,
    synergyType: str = "cost",
    overrides: dict | None = None,
) -> dict[str, Any] | None:
    """합병 시너지 계산: cost / revenue / financial.

    Capabilities:
        - standalone A + B 의 calcDFV 결과 합 대비 combined 가치 차이 = synergy
        - 유형별 multiplier (cost 5% / revenue 8% / financial 3%)
        - integration cost 10% 차감 후 netSynergy 산출

    Parameters
    ----------
    acquirer : Company
        인수자 회사.
    target : Company
        피인수 회사.
    synergyType :
        "cost": 합병 후 운영비 절감 (opex ×0.95)
        "revenue": 교차 판매 성장 (g +2%p)
        "financial": 자본 효율 (WACC -50bps)
    overrides : dict, optional
        가정 override.

    Returns
    -------
    dict
        standaloneA, standaloneB, combinedValue, synergy, synergyPct,
        integrationCost, netSynergy, synergyType, warnings

    Example:
        >>> calcSynergyValue(acq, tgt, synergyType="cost")
        {"synergy": 8e10, "netSynergy": 7.2e10, ...}

    Guide:
        Control Value 와 합산 금지 (이중계산). 시너지 multiplier 는 단순 휴리스틱.

    When:
        M&A 시나리오 분석 시 시너지 가치 인용.

    How:
        calcSynergyValue(acquirer, target, synergyType="cost"|"revenue"|"financial").

    Requires:
        calcDFV: acquirer/target 양쪽 dFV 산출 가능해야 함.

    Raises:
        없음. calcDFV 실패 시 None.

    See Also:
        - calcControlValue : 단일 기업 지배구조 가치
        - Damodaran *Dark Side of Valuation* Ch.17

    AIContext:
        M&A 시너지 가치 답변 시 synergyType + netSynergy + integrationCost 인용.
    """
    overrides = overrides or {}
    warnings: list[str] = []

    try:
        from dartlab.analysis.valuation.dFV import calcDFV
    except ImportError:
        return None

    a = calcDFV(acquirer)
    b = calcDFV(target)
    if not a or not b or not a.get("dFV") or not b.get("dFV"):
        return None

    standalone_a = a["dFV"]
    standalone_b = b["dFV"]
    standalone_total = standalone_a + standalone_b

    # Synergy multiplier: 유형별
    synergy_mult = {
        "cost": 0.05,  # 5% combined uplift
        "revenue": 0.08,  # 8%
        "financial": 0.03,  # 3%
    }.get(synergyType.lower(), 0.05)

    combined = standalone_total * (1 + synergy_mult)
    synergy = combined - standalone_total
    synergy_pct = synergy / standalone_total * 100 if standalone_total > 0 else 0

    # Integration cost: 관습 10% of synergy
    integration_cost = synergy * 0.10
    net_synergy = synergy - integration_cost

    return {
        "standaloneA": round(standalone_a),
        "standaloneB": round(standalone_b),
        "combinedValue": round(combined),
        "synergy": round(synergy),
        "synergyPct": round(synergy_pct, 2),
        "integrationCost": round(integration_cost),
        "netSynergy": round(net_synergy),
        "synergyType": synergyType,
        "warnings": warnings,
    }


def _estimateBaseFcf(company: Any) -> float | None:
    """최근 양수 FCF 중앙값."""
    try:
        from dartlab.core.utils.helpers import toDictBySnakeId

        cf = company.select("CF", ["영업활동현금흐름", "유형자산의취득"])
        parsed = toDictBySnakeId(cf)
        if not parsed:
            return None
        data, periods = parsed
        ocf = data.get("operating_cashflow") or {}
        capex = data.get("purchase_of_property_plant_and_equipment") or {}
        years = [p for p in periods if p.isdigit() and len(p) == 4][:5]
        fcfs = []
        for y in years:
            o = ocf.get(y)
            cx = capex.get(y)
            if o:
                v = float(o) - abs(float(cx or 0))
                fcfs.append(v)
        positives = sorted([f for f in fcfs if f > 0])
        return positives[len(positives) // 2] if positives else None
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        return None


def _estimateNetDebt(company: Any) -> float | None:
    """순차입금 추정: 단기+장기차입금+사채 - 현금.

    Returns
    -------
    float | None
        순차입금 (원). 추출 실패 시 None.
    """
    try:
        from dartlab.core.utils.helpers import toDictBySnakeId

        bs = company.select("BS", ["단기차입금", "장기차입금", "사채", "현금및현금성자산"])
        parsed = toDictBySnakeId(bs)
        if not parsed:
            return None
        data, periods = parsed
        if not periods:
            return None
        latest = periods[0]

        return (
            _balanceValue(data, latest, "shortterm_borrowings")
            + _balanceValue(data, latest, "longterm_borrowings")
            + _balanceValue(data, latest, "debentures")
            - _balanceValue(data, latest, "cash_and_cash_equivalents")
        )
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        return None
