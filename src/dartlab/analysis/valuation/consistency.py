"""Cash Flow Consistency — Damodaran 가정 간 정합성 검증.

*Investment Valuation* 에서 Damodaran 이 가장 자주 지적하는 실수:
- 성장 가정 ≠ 재투자 필요량 매칭 실패
- FCFF 로 할인하면서 Ke 로 할인 (discount rate 섞음)
- Terminal Value 비중 과도
- 실패 위험을 할인율에 장착 (이중계산)
- Marginal tax rate 와 effective tax rate 의 혼동

`detectExtremeFlags` 와 역할 분담:
- detectExtremeFlags : **단일 가정의 극단값** (WACC 15% 초과 등)
- calcCashFlowConsistency : **가정 간 정합성** (g ≠ reinvestRate × ROIC)

반환은 순수 dict — 해석은 story narrate 층 담당.
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.valuation._consistencyRules import (
    _mergeValuation,
    _resolveFromCompany,
    _ruleDiscountRateMatch,
    _ruleGrowthEquation,
    _ruleGrowthOptimism,
    _ruleSingleModel,
    _ruleTaxConsistency,
    _ruleTerminalGrowthBounded,
    _ruleTerminalValueShare,
    _severityAndScore,
)
from dartlab.synth.riskPremiums import loadDamodaranERP


def calcCashFlowConsistency(
    company: Any = None,
    *,
    basePeriod: str | None = None,
    valuation: dict[str, Any] | None = None,
    roicPct: float | None = None,
    growthRatePct: float | None = None,
    reinvestmentRatePct: float | None = None,
    terminalGrowthPct: float | None = None,
    terminalValueShare: float | None = None,
    primaryModel: str | None = None,
    modelsUsed: int | None = None,
    effectiveTaxRatePct: float | None = None,
    waccPct: float | None = None,
    country: str | None = None,
    currency: str | None = None,
) -> dict[str, Any]:
    """Damodaran 가정 간 정합성 검증.

    Capabilities:
        - 7 규칙 (TG ≤ Rf, Growth Equation, 할인율 매칭, TV 비중, 단일 모델,
          세율 일치, 성장 과다 낙관) 검증 + 심각도/score 산출
        - company 지정 시 ROIC/WACC/growth 자동 추출
        - valuation dict 의 모든 필드 자동 매핑

    Parameters
    ----------
    valuation : dFV 결과 dict. 지정 시 내부에서 필요한 값 자동 추출.
    roicPct, growthRatePct, reinvestmentRatePct : Growth Equation 검증 (g = reinvest × ROIC)
    terminalGrowthPct : 영구성장률 (%)
    terminalValueShare : TV / EV (0.0~1.0)
    primaryModel : "dcf"/"dcf2stage"/"fcfe"/"ddm"/"rim"/... — 할인율 매칭 검증
    modelsUsed : 사용된 모델 개수 (단일 방법론 의존 감지)
    effectiveTaxRatePct : 유효세율 (%)
    waccPct : WACC (%)
    country : ISO2 (Rf / marginalTax 조회)
    currency : country 없을 때 추론

    Returns
    -------
    dict
        flags : list[dict{rule, severity, message, observed, expected}]
        severity : str — 전체 최고 심각도
        score : int — 0~100 (100 = 완전 정합)
        checks : dict — 개별 검증 결과

    Example:
        >>> calcCashFlowConsistency(valuation=dFV_result)
        {"score": 85, "severity": "warn", "flags": [...]}

    Guide:
        critical=-40, warn=-15, info=-5. dFV 결과 + ROIC + Growth 함께 주입.

    When:
        dFV 산출 직후 가정 검증 + story 단계 narrate 직전.

    How:
        calcCashFlowConsistency(company, valuation=dFV) 또는 individual 키 주입.

    Requires:
        synth.riskPremiums.loadDamodaranERP + core.utils.calc.reinvestmentIdentity.

    Raises:
        없음 — 누락 입력은 해당 규칙 skip.

    See Also:
        - detectExtremeFlags : 단일 가정의 극단값 검출 (역할 분담)
        - calcDFV : 본 검증의 입력 dict 생산자

    AIContext:
        Damodaran 7 sins 정합성 위반 인용 시 flags + score 함께 노출.
    """
    # company 지정 시 자동 추출
    if company is not None:
        (
            currency,
            valuation,
            roicPct,
            waccPct,
            effectiveTaxRatePct,
            growthRatePct,
        ) = _resolveFromCompany(
            company,
            basePeriod,
            currency,
            valuation,
            roicPct,
            waccPct,
            effectiveTaxRatePct,
            growthRatePct,
        )

    if valuation:
        (
            roicPct,
            growthRatePct,
            terminalGrowthPct,
            terminalValueShare,
            primaryModel,
            modelsUsed,
            waccPct,
        ) = _mergeValuation(
            valuation,
            roicPct,
            growthRatePct,
            terminalGrowthPct,
            terminalValueShare,
            primaryModel,
            modelsUsed,
            waccPct,
        )

    erp = loadDamodaranERP(countryCode=country, currency=currency)
    rfPct = erp["riskFreeRate"]
    marginalTax = erp["marginalTaxRate"]

    flags: list[dict] = []
    checks: dict[str, Any] = {}

    _ruleTerminalGrowthBounded(terminalGrowthPct, rfPct, flags, checks)
    _ruleGrowthEquation(growthRatePct, roicPct, reinvestmentRatePct, flags, checks)
    _ruleDiscountRateMatch(primaryModel, waccPct, checks)
    _ruleTerminalValueShare(terminalValueShare, flags, checks)
    _ruleSingleModel(modelsUsed, flags)
    _ruleTaxConsistency(effectiveTaxRatePct, marginalTax, flags, checks)
    _ruleGrowthOptimism(growthRatePct, terminalGrowthPct, rfPct, flags)

    severity, score = _severityAndScore(flags)

    return {
        "flags": flags,
        "severity": severity,
        "score": score,
        "checks": checks,
    }
