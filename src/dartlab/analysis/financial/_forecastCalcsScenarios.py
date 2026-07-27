"""forecastCalcs.py 의 시나리오/proforma — calcProFormaHighlights · calcScenarioImpact · calcScenarioSimulation."""

from __future__ import annotations

import logging
from typing import Any

from dartlab.analysis.financial._forecastCalcsInputs import (
    _getSectorParams,
    _getSeriesAndMeta,
    _getShares,
    _runForecastRevenue,
)
from dartlab.analysis.forecast.simulation import simulateAllScenarios
from dartlab.core.memory import memoizedCalc

log = logging.getLogger(__name__)


@memoizedCalc
def calcProFormaHighlights(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """Pro-Forma IS 주요 항목 전망.

    Returns
    -------
    dict
        isEstimate : bool — 추정치 여부
        currency : str — 통화 코드
        wacc : float — 가중평균자본비용 (%)
        revenueGrowthPath : list[float] — 연도별 매출 성장률 (%)
        years : list[dict] — 연도별 전망
            yearOffset : int — 기준연 대비 오프셋
            revenue : float — 매출 (원)
            operatingIncome : float — 영업이익 (원)
            netIncome : float — 순이익 (원)
            ebitda : float — EBITDA (원)
            fcf : float — 잉여현금흐름 (원)
        warnings : list[str] — 경고 메시지
        disclaimer : str — 면책 문구

    Capabilities:
        - 매출 성장 경로 + sector params 로 pro-forma IS/CF 전망 (revenue/op/net/EBITDA/FCF)
        - WACC + 연도별 yearOffset 메타

    Guide:
        DCF 입력의 표준. years 의 FCF 가 DCF intrinsicValue 산출에 사용.

    When:
        Story pro-forma 박스 + AI 전망 IS 답변.

    How:
        calcRevenueForecast → growthPath → buildProforma → projections 변환.

    Requires:
        매출 전망 + sector params.

    Raises:
        없음 — proforma 실패 시 None.

    Example:
        >>> calcProFormaHighlights(company)["years"][0]["revenue"]
        220000000000

    See Also:
        - calcRevenueForecast : 매출
        - calcScenarioImpact : 시나리오 영향

    AIContext:
        "내년 IS 전망" 답변 시 years 의 revenue/operatingIncome 인용.
    """
    result = _runForecastRevenue(company)
    if not result or not result.projected:
        return None

    series, _, sectorKey, _, currency = _getSeriesAndMeta(company)
    shares = _getShares(company)
    sp = _getSectorParams(company)

    growthPath = result.growthRates
    if not growthPath:
        return None

    from dartlab.analysis.financial.proforma import buildProforma

    try:
        pf = buildProforma(
            series,
            revenueGrowthPath=growthPath,
            sectorParams=sp,
            shares=shares,
            scenarioName="base",
        )
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as exc:
        log.debug("pro-forma 생성 실패: %s", exc)
        return None

    if not pf.projections:
        return None

    years = []
    for p in pf.projections:
        years.append(
            {
                "yearOffset": p.year_offset,
                "revenue": p.revenue,
                "operatingIncome": p.operating_income,
                "netIncome": p.net_income,
                "ebitda": p.ebitda,
                "fcf": p.fcf,
            }
        )

    return {
        "isEstimate": True,
        "currency": currency,
        "wacc": pf.wacc,
        "revenueGrowthPath": pf.revenueGrowthPath,
        "years": years,
        "warnings": pf.warnings,
        "disclaimer": pf.DISCLAIMER,
    }


@memoizedCalc
def calcScenarioImpact(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """매크로 시나리오별 매출/마진 영향.

    Returns
    -------
    dict
        isEstimate : bool — 추정치 여부
        currency : str — 통화 코드
        scenarios : dict — 시나리오별 (baseline/bull/bear)
            label : str — 시나리오 라벨
            revenueChangePct : float — 매출 변화율 (%)
            marginChangeBps : float — 마진 변화 (bps)
            revenuePath : list[float] — 매출 경로 (원)
            marginPath : list[float] — 마진 경로 (%)
            warnings : list[str] — 경고 메시지

    Capabilities:
        - baseline/bull/bear 3 시나리오 매크로 충격에 대한 매출/마진 영향 시뮬
        - revenuePath + marginPath 시계열

    Guide:
        Macro stress 테스트. spread (bull-bear) ≥ 50% = 시나리오 불확실성 ↑.

    When:
        Scenario stress + AI "매크로 시나리오" 답변.

    How:
        ``simulateAllScenarios`` → 각 시나리오 path → dict 변환.

    Requires:
        sector params + 시계열.

    Raises:
        없음.

    Example:
        >>> calcScenarioImpact(company)["scenarios"]["bull"]["revenueChangePct"]
        18

    See Also:
        - calcRevenueForecast : 기본 전망
        - calcScenarioSimulation : 시뮬레이션 본체

    AIContext:
        "매크로 시나리오 영향" 답변 시 scenarios 의 revenueChangePct 인용.
    """
    series, _, sectorKey, _, currency = _getSeriesAndMeta(company)
    shares = _getShares(company)
    sp = _getSectorParams(company)

    try:
        results = simulateAllScenarios(
            series,
            sectorKey=sectorKey,
            sectorParams=sp,
            shares=shares,
        )
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as exc:
        log.debug("시나리오 시뮬레이션 실패: %s", exc)
        return None

    if not results:
        return None

    scenarios = {}
    for name, sim in results.items():
        scenarios[name] = {
            "label": sim.scenarioLabel,
            "revenueChangePct": sim.revenueChangePct,
            "marginChangeBps": sim.marginChangeBps,
            "revenuePath": sim.revenuePath,
            "marginPath": sim.marginPath,
            "warnings": sim.warnings,
        }

    return {
        "isEstimate": True,
        "currency": currency,
        "scenarios": scenarios,
    }


@memoizedCalc
def calcScenarioSimulation(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """시나리오 시뮬레이션 — 과거 CAGR 기반 자동 3시나리오 ProForma + 분기 목표.

    과거 3년 매출 CAGR을 자동 계산하여 base 성장률로 사용하고,
    bull/base/bear 3개 시나리오의 ProForma IS/BS/CF + 분기 목표 + DCF를 생성한다.

    사용자 지정 성장률이 필요하면 scenarioSim.createSimulation()을 직접 호출.

    Returns
    -------
    dict
        isEstimate : bool — 추정치 여부
        currency : str — 통화 코드
        baseYear : str — 기준 연도
        targetYear : str — 목표 연도
        revenueGrowthCAGR : float — 기준 CAGR (%)
        scenarios : dict — 시나리오별 revenue/operatingIncome/netIncome/fcf/wacc (원)
        quarterlyRevTargets : dict — 시나리오별 분기 매출 목표 (원)
        quarterlyOITargets : dict — 시나리오별 분기 영업이익 목표 (원)
        dcfPerShare : dict — 시나리오별 주당 DCF 가치 (원)
        seasonality : dict — revenue/operatingIncome 분기 계절성 가중치

    Capabilities:
        - 과거 3 년 CAGR base → bull/base/bear 3 시나리오 ProForma + 분기 목표 + DCF
        - seasonality 가중치로 분기 분해

    Guide:
        자동 시나리오 생성. 사용자 정의 성장률은 scenarioSim.createSimulation 직접 호출.

    When:
        Scenario simulation + AI "3 시나리오 비교" 답변.

    How:
        과거 CAGR 계산 → createSimulation → 시나리오별 IS/BS/CF + 분기 목표.

    Requires:
        IS 시계열 ≥ 8 분기 (2 년).

    Raises:
        없음.

    Example:
        >>> calcScenarioSimulation(company)["scenarios"]["bull"]["revenue"]
        260000000000

    See Also:
        - calcScenarioImpact : 매크로 시나리오
        - calcProFormaHighlights : 단일 시나리오 IS

    AIContext:
        "3 시나리오 자동 시뮬" 답변 시 scenarios 각 항목 인용.
    """
    from dartlab.analysis.forecast.scenarioSim import createSimulation

    series, _, _, _, currency = _getSeriesAndMeta(company)
    shares = _getShares(company)

    revVals = []
    for sj_key in ("sales", "revenue"):
        vals = series.get("IS", {}).get(sj_key, [])
        if vals:
            annuals = []
            for end in range(len(vals), 3, -4):
                chunk = [v for v in vals[end - 4 : end] if v is not None]
                if len(chunk) == 4:
                    annuals.append(sum(chunk))
                if len(annuals) >= 4:
                    break
            annuals.reverse()
            if len(annuals) >= 2:
                revVals = annuals
                break

    if len(revVals) < 2:
        return None

    first, last = revVals[0], revVals[-1]
    nYears = len(revVals) - 1
    if first <= 0 or last <= 0:
        cagr = 0.0
    else:
        cagr = ((last / first) ** (1 / nYears) - 1) * 100

    cagr = max(-20.0, min(50.0, cagr))

    try:
        sim = createSimulation(
            company,
            "자동(CAGR기반)",
            revenueGrowth=round(cagr, 1),
            shares=shares,
        )
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as exc:
        log.debug("시나리오 시뮬레이션 실패: %s", exc)
        return None

    scenarios = {}
    for scName, pf in sim.proformaResults.items():
        if pf.projections:
            p = pf.projections[0]
            scenarios[scName] = {
                "revenue": p.revenue,
                "operatingIncome": p.operating_income,
                "netIncome": p.net_income,
                "fcf": p.fcf,
                "wacc": pf.wacc,
            }

    return {
        "isEstimate": True,
        "currency": currency,
        "baseYear": sim.baseYear,
        "targetYear": sim.targetYear,
        "revenueGrowthCAGR": round(cagr, 1),
        "scenarios": scenarios,
        "quarterlyRevTargets": {sc: [round(v) for v in vals] for sc, vals in sim.quarterlyRevTargets.items()},
        "quarterlyOITargets": {sc: [round(v) for v in vals] for sc, vals in sim.quarterlyOITargets.items()},
        "dcfPerShare": sim.dcfPerShare,
        "seasonality": {
            "revenue": [round(w, 3) for w in sim.revSeasonality],
            "operatingIncome": [round(w, 3) for w in sim.oiSeasonality],
        },
    }
