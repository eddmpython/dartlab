"""dFV (dartlab Fair Value) 헬퍼 — override selector + early dispatch + apply 5종.

analysis/valuation/dFV.py 가 1047 줄 god module 이라 헬퍼 분리.
identity 보존을 위해 dFV.py 가 본 모듈에서 re-export 한다.

상수:
- _MODEL_SENSITIVITY — primary model × override 키 감응 매트릭스
- _SELECTOR_IGNORE — selector 무시 keys
- _DFV_OVERRIDE_ALLOWED_KEYS — override dict 허용 키 화이트리스트

함수:
- _selectPrimaryWithOverrides — override 감응 primary 자동 전환
- _dfvEarlyDispatch — 금융/지주 자동 분기 (Bank Excess Return / SOTP)
- _dfvCheckRelativeExtreme — primary=relative 이탈 시 secondary 교체
- _dfvApplyGoingConcern · _dfvApplyTwoStage · _dfvApplyRealOptions ·
  _dfvApplyLiquidation · _dfvApplyConsistency · _dfvApplyOverrideMeta —
  out dict 에 in-place 결과 추가
"""

from __future__ import annotations

from typing import Any

# Phase 12 A1: Smart Primary Selector — override 감응성 매트릭스.
# override 가 들어올 때 primary 가 무감각 모델이면 감응 모델로 자동 전환.
_MODEL_SENSITIVITY: dict[str, set[str]] = {
    "dcf": {"wacc", "terminalGrowth", "growthRates", "countryCode"},
    "dcf2stage": {
        "wacc",
        "terminalGrowth",
        "growthRates",
        "marginPath",
        "reinvestmentPath",
        "countryCode",
    },
    "ddm": {"terminalGrowth"},
    "rim": {"wacc", "countryCode"},
    "relative": set(),  # PER/PBR — override 무감각
    "relativeSurvival": set(),
    "liquidation": {"liquidationValue", "liquidationDiscount"},
}

_SELECTOR_IGNORE = {"primaryModel", "lifeCyclePhase", "companyType", "pSurvival", "impliedERP", "bottomUpBeta"}


def _selectPrimaryWithOverrides(
    selected: str,
    allMethods: dict,
    overrides: dict,
) -> tuple[str, str | None]:
    """override 가 실제 영향 주는 primary 자동 선택.

    Returns
    -------
    (primary_key, reason) — reason not None 이면 자동 전환됨.
    """
    if not overrides:
        return selected, None
    ov_keys = {k for k in overrides if k not in _SELECTOR_IGNORE and not k.startswith("_")}
    if not ov_keys:
        return selected, None

    sensitivities = _MODEL_SENSITIVITY.get(selected, set())
    if sensitivities & ov_keys:
        return selected, None  # 현재 primary 이미 감응

    # 감응 대안 모델 중 값 있는 것 선택
    for cand in ("dcf2stage", "dcf", "rim", "ddm"):
        if cand in allMethods and allMethods[cand] and allMethods[cand] > 0:
            cand_sens = _MODEL_SENSITIVITY.get(cand, set())
            if cand_sens & ov_keys:
                return cand, f"{selected}→{cand} (override {sorted(ov_keys)} 반영)"
    return selected, None


def _dfvEarlyDispatch(company: Any, basePeriod: str | None, ov: dict) -> dict | None:
    """금융업/지주사 자동 분기 — Bank Excess Return / SOTP NAV.

    Returns
    -------
    dict | None
        Bank DFV (isFinancialCompany) 또는 Holding SOTP (upside |≤100%|)
        valid result. 해당 없으면 None (일반 dispatch 진행).
    """
    try:
        from dartlab.analysis.valuation.bankDFV import calcBankDFV, isFinancialCompany

        if isFinancialCompany(company):
            bank_result = calcBankDFV(company, basePeriod=basePeriod, overrides=ov)
            if bank_result and bank_result.get("dFV"):
                return bank_result
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    try:
        from dartlab.analysis.financial.companyType import _checkHolding
        from dartlab.analysis.valuation.sotp import calcHoldingDFV

        if _checkHolding(company):
            sotp_result = calcHoldingDFV(company, basePeriod=basePeriod, overrides=ov)
            if sotp_result and sotp_result.get("dFV"):
                up = sotp_result.get("upside")
                if up is None or abs(up) <= 100:
                    return sotp_result
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    return None


def _dfvCheckRelativeExtreme(
    company: Any,
    primaryKey: str,
    primaryValue: float,
    secondaryKeys: list,
    allMethods: dict,
) -> tuple[str, float]:
    """primary=relative 가 현재가 ±150% 이탈 시 secondary 중 현재가 근접 모델로 교체.

    Returns
    -------
    tuple[str, float]
        (new_primary_key, new_primary_value). 정상 범위면 그대로 반환.
    """
    if primaryKey not in ("relative", "relativeSurvival"):
        return primaryKey, primaryValue
    try:
        import importlib

        _getCurrentPrice = importlib.import_module("dartlab.analysis.valuation.dFV")._getCurrentPrice
        cp = _getCurrentPrice(company)
        if not (cp and cp > 0):
            return primaryKey, primaryValue
        ratio = primaryValue / cp
        if not (ratio > 2.5 or ratio < 0.4):
            return primaryKey, primaryValue
        sec_candidates: list[tuple[str, float, float]] = []
        for sk in secondaryKeys:
            sv = allMethods.get(sk)
            if sv and sv > 0:
                sec_candidates.append((sk, sv, abs(sv / cp - 1.0)))
        if sec_candidates:
            sec_candidates.sort(key=lambda x: x[2])
            return sec_candidates[0][0], sec_candidates[0][1]
    except (AttributeError, ValueError, TypeError, ZeroDivisionError):
        pass
    return primaryKey, primaryValue


def _dfvApplyGoingConcern(out: dict, goingConcern: float | None, survival: dict | None) -> None:
    """Going concern + Survival 가중 결과를 out 에 in-place 추가."""
    if goingConcern is not None:
        out["goingConcernValue"] = round(goingConcern)
    if survival is not None:
        out["survival"] = {
            "pSurvival": survival.get("pSurvival"),
            "liquidationValue": round(survival["liquidationValue"]) if survival.get("liquidationValue") else None,
            "adjustedUplift": survival.get("uplift"),
        }


def _dfvApplyTwoStage(out: dict, twoStageDetail: dict | None) -> None:
    """Two-Stage DCF 상세를 out['twoStage'] 에 추가."""
    if not twoStageDetail:
        return
    out["twoStage"] = {
        "growthYears": twoStageDetail.get("growthYears"),
        "growthRates": twoStageDetail.get("growthRates"),
        "terminalGrowthRate": twoStageDetail.get("terminalGrowthRate"),
        "pvExplicit": twoStageDetail.get("pvExplicit"),
        "pvTerminal": twoStageDetail.get("pvTerminal"),
        "tvShare": twoStageDetail.get("tvShare"),
        "phases": twoStageDetail.get("phases") or [],
        "marginPath": twoStageDetail.get("marginPath"),
        "reinvestmentPath": twoStageDetail.get("reinvestmentPath"),
        "warnings": twoStageDetail.get("warnings") or [],
    }


def _dfvApplyRealOptions(out: dict, company: Any, basePeriod: str | None, ov: dict) -> None:
    """Real Options 값 — appliedAs 에 따라 uplift(bull) or floor 로 반영."""
    try:
        from dartlab.analysis.valuation.realOptions import calcRealOptionsValue

        ro = calcRealOptionsValue(company, basePeriod=basePeriod, overrides=ov)
        if ro and ro.get("optionValue") is not None:
            out["realOptions"] = ro
            if ro.get("appliedAs") == "uplift":
                out["scenarios"]["bull"] = round(out["scenarios"]["bull"] + ro["optionValue"])
            elif ro.get("appliedAs") == "floor":
                out["realOptionsFloor"] = ro.get("K")
    except (ImportError, AttributeError, ValueError, TypeError):
        pass


def _dfvApplyLiquidation(out: dict, liquidationDetail: dict | None) -> None:
    """Liquidation 상세를 out['liquidation'] 에 추가."""
    if not liquidationDetail:
        return
    out["liquidation"] = {
        "recoveries": liquidationDetail.get("recoveries"),
        "grossRecovery": liquidationDetail.get("grossRecovery"),
        "netToEquity": liquidationDetail.get("netToEquity"),
        "perShare": liquidationDetail.get("perShare"),
        "weightedRecoveryRate": liquidationDetail.get("weightedRecoveryRate"),
    }


def _dfvApplyConsistency(out: dict, consistency: dict | None) -> None:
    """Cash flow consistency 플래그를 out 에 평탄화 추가."""
    if not consistency:
        return
    out["consistencyFlags"] = consistency.get("flags", [])
    out["consistencyScore"] = consistency.get("score")
    out["consistencySeverity"] = consistency.get("severity")


_DFV_OVERRIDE_ALLOWED_KEYS = (
    "wacc",
    "terminalGrowth",
    "primaryModel",
    "lifeCyclePhase",
    "pSurvival",
    "liquidationValue",
    "liquidationDiscount",
    "countryCode",
    "countryRiskPremium",
)


def _dfvApplyOverrideMeta(out: dict, ov: dict, primarySwitchReason: str | None) -> None:
    """적용된 override + 자동 전환 메타데이터 기록."""
    if ov:
        out["overrideApplied"] = {k: v for k, v in ov.items() if k in _DFV_OVERRIDE_ALLOWED_KEYS}
    if primarySwitchReason:
        out.setdefault("overrideApplied", {})["primaryAutoSwitch"] = primarySwitchReason
