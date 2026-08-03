"""dFV v2 (dartlab Fair Value) — DCF Anchor + 삼각검증 + Quality WACC.

학술 근거:
- McKinsey Valuation Ch.14: DCF를 primary, multiples를 triangulation
- Damodaran: "하나의 서사, 하나의 모델" — 가중 평균 경계
- Fernandez: 질적 조정은 WACC 입력에서 (사후 곱셈 금지)
- CFA Level II: 기업유형별 모델 선택 매트릭스

dFV = Primary Model(Quality-Adjusted WACC) + 삼각검증 + DDM floor
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.valuation._dFVCalcs import (
    _applySurvivalAdjustment,
    _buildConsistency,
    _calcLiquidationDetail,
    _calcLiquidationValue,
    _calcOpinion,
    _calcTwoStageDcf,
    _collectAllValues,
    _getCurrentPrice,
    _inferShares,
    _triangulate,
)

# ── 헬퍼 (분리: _dFVDispatch.py SSOT, re-export 으로 BC 보존) ──
from dartlab.analysis.valuation._dFVDispatch import (
    _DFV_OVERRIDE_ALLOWED_KEYS,
    _MODEL_SENSITIVITY,
    _SELECTOR_IGNORE,
    _dfvApplyConsistency,
    _dfvApplyGoingConcern,
    _dfvApplyLiquidation,
    _dfvApplyOverrideMeta,
    _dfvApplyRealOptions,
    _dfvApplyTwoStage,
    _dfvCheckRelativeExtreme,
    _dfvEarlyDispatch,
    _selectPrimaryWithOverrides,
)
from dartlab.analysis.valuation._dFVTsd import (
    _tsdBuildPhases,
    _tsdExtractBaseFcf,
    _tsdExtractNetDebtShares,
    _tsdMaybeNormalizeFcf,
    _tsdResolveHighGrowth,
    _tsdResolveTerminalGrowth,
    _tsdResolveWacc,
)


def calcDFV(
    company: Any,
    *,
    basePeriod: str | None = None,
    overrides: dict | None = None,
) -> dict | None:
    """dartlab Fair Value v2 — 기업유형 × 생애주기 × 다중 모델 삼각검증.

    Capabilities:
        Company 의 기업유형 (early/growth/mature/decline) × 생애주기 단계로
        primary 모델 (DCF/DDM/RIM/EV-EBITDA/PSR 등) 자동 선택, secondary 2 개
        cross-check + Damodaran qualityWACC 조정 + DDM dividend floor + 청산
        가치 안전망까지 결합한 단일 적정주가 산출.

    Args:
        company: Company 객체. ``finance``, ``stockCode``, ``currency``,
            ``benchmark`` (선택) 속성 필요.
        basePeriod: 재무 기준 기간 (예 ``"2024Q4"``). ``None`` 이면 최신.
            공시 가용일과 시장 입력 vintage를 고정하는 as-of 계약은 아니다.
        overrides: AI/사용자 가정 override dict. 지원 키:
            - ``wacc`` (float): 강제 WACC
            - ``terminalGrowth`` (float): 영구성장률 강제
            - ``primaryModel`` (str): primary 모델 강제
            - ``lifeCyclePhase`` (str): 생애주기 강제
            - ``impliedERP``/``bottomUpBeta``/``countryCode``: WACC 산출 chain

    Returns:
        dict | None:
            - ``dFV`` (float): 적정주가 base (원)
            - ``scenarios`` (dict): ``{bull, base, bear}`` 시나리오 적정가
            - ``currentPrice`` (float|None)
            - ``upside`` (float): 적정 대비 (%)
            - ``opinion`` (str): 의견 ("강력매수"/"매수"/"중립"/"매도"/"강력매도")
            - ``confidence`` (str): 신뢰도 ("high"/"medium"/"low")
            - ``primaryModel`` (str): 사용된 primary 모델명
            - ``companyType`` (str|None)
            - ``triangulation`` (dict): 삼각검증 결과 (3 방법론 일치도)
            - ``dividendFloor`` (dict|None): DDM 하한
            - ``qualityWACC`` (dict): WACC 조정 상세
            - ``twoStage.assumptions`` (dict): 실제 DCF 입력과 재무 기간 provenance
            - ``allMethods`` (dict): 모든 방법론 적정가 (참고용)
            - ``overrideApplied`` (dict|None): 적용된 override
            - ``survival`` (dict|None): 부도확률 기반 going-concern 가중
        데이터 부족 (BS/IS/CF 누락) 시 ``None``.

    Raises:
        없음 — 내부 catch.

    Example:
        >>> from dartlab import Company
        >>> r = calcDFV(Company("005930"), overrides={"wacc": 8.5})
        >>> r["dFV"], r["opinion"]
        (75000.0, '매수')

    Guide:
        primary 모델 선택 표 (fitness.selectModels): earlyGrowth/highGrowth →
        DCF (FCF 기반), mature → EV-EBITDA + DDM, decline → 청산가치 + DDM.
        secondary 2 개 cross-check 후 triangulation 일치도 ±25% 내면
        confidence=high.

    When:
        Company 분석 종료 시점에 단일 적정주가가 필요할 때. AI Q&A 의 dFV 슬롯
        에서 항상 본 함수 결과 인용.

    How:
        calcDFV(Company("005930")) 또는 overrides={"wacc": 8.5} 형식.
        금융업/지주사는 자동으로 calcBankDFV/calcHoldingDFV dispatch.

    SeeAlso:
        - ``dartlab.analysis.valuation.dcf.dcfValuation``: DCF 단독
        - ``dartlab.analysis.valuation.dcf.ddmValuation``: DDM 단독
        - ``dartlab.synth.distress.survival.applySurvivalWeight``: distress 가중
        - ``dartlab.synth.riskPremiums.loadDamodaranERP``: ERP 룩업

    Requires:
        Company.finance (BS/IS/CF 시계열) + 종가 + analysis.financial 의 다수
        헬퍼 (ratios, valuation, growth, investment, proforma).

    AIContext:
        ``upside`` 만 단독 인용 금지 — primaryModel + triangulation 일치도 +
        confidence 셋 함께 노출. ``opinion`` 라벨은 사용자 향 표시이지 시장
        actionable signal 이 아님 (전문가 검토 필수).

    LLM Specifications:
        AntiPatterns:
            - upside 30%+ 인데 confidence="low" 결과를 그대로 인용 — 단일
              모델 의존 신호. triangulation 일치도 확인 필수.
            - overrides 키 추측 — 위 5 키만 적용됨, 나머지는 무시.
            - companyType "financial" 인데 DCF 강제 (overrides=primaryModel)
              금지 — 금융업은 RIM/DDM 만 의미.
        OutputSchema:
            상기 13 키 dict 또는 None. scenarios dict 는 bull/base/bear 3 키.
        Prerequisites:
            Company.finance + 종가 (gather("price")) + analysis 헬퍼 모듈.
        Freshness:
            finance = 최신 분기 (마감 후 30~45 일). 종가 = T+1.
        Dataflow:
            company → fitness.selectModels → primary/secondary 호출 →
            qualityWACC 조정 → applySurvivalWeight → triangulate → opinion.
        TargetMarkets: KR (DART), US (EDGAR).
    """
    if basePeriod is not None:
        reason = (
            "과거 재무기간에 대응하는 공시 가용일·주가·시가총액·주식수·모델선택 "
            "vintage가 완전히 고정되지 않아 dFV와 의견을 발행할 수 없습니다."
        )
        return {
            "status": "blocked",
            "assessmentStatus": "blocked",
            "basePeriod": basePeriod,
            "blockedReason": reason,
            "pointInTime": False,
            "dFV": None,
            "scenarios": None,
            "currentPrice": None,
            "upside": None,
            "opinion": None,
            "confidence": "unavailable",
            "primaryModel": None,
            "allMethods": {},
        }

    from dartlab.synth.overrides import applyOverride

    ov = overrides or {}

    special = _dfvEarlyDispatch(company, basePeriod, ov)
    if special is not None:
        return special

    # 1. 기업유형 × 생애주기 → primary/secondary 선택
    from dartlab.analysis.valuation.fitness import selectModels

    forced_phase = applyOverride(None, "lifeCyclePhase", ov)
    models = selectModels(company, lifeCyclePhase=forced_phase)
    primaryKey = applyOverride(models["primary"], "primaryModel", ov)
    secondaryKeys = models["secondary"]
    survival_adj = bool(models.get("survivalAdj", False))
    lifePhase = models.get("lifeCyclePhase")

    # 2. 실제 DCF 에 적용할 Quality-Adjusted WACC 를 먼저 확정한다.
    baseWacc = _tsdResolveWacc(company, ov, basePeriod=basePeriod)
    from dartlab.analysis.valuation.qualityWACC import calcQualityWACC

    qw = calcQualityWACC(company, baseWacc, basePeriod=basePeriod)
    adjusted_wacc = qw["adjustedWACC"]

    # 3. 모든 방법론 적정가 수집 (+ liquidation 자산별 + dcf2stage 실로직)
    allMethods = _collectAllValues(company, basePeriod)

    # 2a. Liquidation — 자산별 회수율 (Damodaran Dark Side Ch.9)
    liquidationDetail = _calcLiquidationDetail(company, ov)
    if liquidationDetail and liquidationDetail.get("perShare"):
        allMethods["liquidation"] = liquidationDetail["perShare"]

    # 2b. Two-Stage DCF — 고성장 n년 명시적 + terminal 수렴 (Damodaran Ch.12)
    twoStageDetail = _calcTwoStageDcf(
        company,
        lifePhase,
        ov,
        basePeriod=basePeriod,
        wacc=adjusted_wacc,
    )
    if twoStageDetail and twoStageDetail.get("perShare"):
        allMethods["dcf2stage"] = twoStageDetail["perShare"]

    # 2c. relativeSurvival — relative 값 재사용 (survival 가중은 하단)
    if "relative" in allMethods and "relativeSurvival" not in allMethods:
        allMethods["relativeSurvival"] = allMethods["relative"]
    if not allMethods:
        return None

    # Phase 12 A1: Smart Primary Selector — override 가 있고 현재 primary 가 무감각이면 자동 전환
    primaryKey, _primary_switch_reason = _selectPrimaryWithOverrides(primaryKey, allMethods, ov)

    # 4. Primary 모델 값 = dFV (Base)
    primaryValue = allMethods.get(primaryKey)

    # primary가 없으면 fallback: 가장 적합도 높은 방법론 사용
    if primaryValue is None:
        from dartlab.analysis.valuation.fitness import calcMethodFitness

        fit = calcMethodFitness(company, basePeriod=basePeriod)
        candidates = {k: v for k, v in allMethods.items() if v and v > 0}
        best_key = max(candidates.keys(), key=lambda k: fit.get(k, {}).get("fitness", 0), default=None)
        if best_key:
            primaryKey = best_key
            primaryValue = allMethods[best_key]
        else:
            return None

    if primaryValue is None or primaryValue <= 0:
        return None

    primaryKey, primaryValue = _dfvCheckRelativeExtreme(
        company,
        primaryKey,
        primaryValue,
        secondaryKeys,
        allMethods,
        basePeriod=basePeriod,
    )

    # 5. Bull/Base/Bear 시나리오 — DCF primary 면 드라이버(g·WACC) 교란(±12% 산술밴드 폐기),
    #    비-DCF primary 는 ±12% 근사 fallback (P1a de-gate).
    driver_scen = twoStageDetail.get("driverScenarios") if (primaryKey == "dcf2stage" and twoStageDetail) else None
    if driver_scen and driver_scen.get("bull") and driver_scen.get("bear"):
        bull = driver_scen["bull"]
        bear = driver_scen["bear"]
        scenarioMethod = {
            "method": "driverSensitivity",
            "driverNames": ["growth", "wacc"],
            "drivers": driver_scen.get("drivers") or {},
        }
    else:
        wacc_effect = 0.12  # WACC 1%p 변화 ≈ 적정가 ±12% (비-DCF primary 경험칙)
        bull = primaryValue * (1 + wacc_effect)
        bear = primaryValue * (1 - wacc_effect)
        scenarioMethod = {"method": "arithmeticPercentBand", "percent": 12.0}

    # 6. 삼각검증
    triangulation = _triangulate(primaryKey, primaryValue, secondaryKeys, allMethods)

    # 7. DDM floor
    ddm_floor = None
    ddm_value = allMethods.get("ddm")
    if ddm_value and ddm_value > 0 and models["ddmRole"] == "floor":
        ddm_floor = {
            "value": round(ddm_value),
            "meaning": f"배당만으로도 최소 {ddm_value:,.0f}원의 가치",
            "coverageRatio": round(ddm_value / primaryValue, 2) if primaryValue > 0 else 0,
        }

    # 8. Survival 가중 (Dark Side of Valuation)
    survival = None
    adjusted_primary = primaryValue
    goingConcern = None
    if survival_adj:
        survival = _applySurvivalAdjustment(company, primaryValue, ov)
        if survival and survival.get("adjustedValue") is not None:
            goingConcern = primaryValue
            adjusted_primary = survival["adjustedValue"]

    # 9. 현재가 + upside (survival 반영한 adjusted_primary 기준)
    currentPrice = _getCurrentPrice(company, basePeriod=basePeriod)
    upside = (adjusted_primary - currentPrice) / currentPrice * 100 if currentPrice and currentPrice > 0 else None

    # 10. 신뢰도 + 의견
    confidence = triangulation.get("confidence", "low")
    opinion = _calcOpinion(upside)

    # 11. Cash Flow Consistency 검증
    consistency = _buildConsistency(company, primaryKey, primaryValue, triangulation, adjusted_wacc, ov)

    out = {
        "dFV": round(adjusted_primary),
        "scenarios": {"bull": round(bull), "base": round(adjusted_primary), "bear": round(bear)},
        "scenarioMethod": scenarioMethod,
        "currentPrice": round(currentPrice) if currentPrice else None,
        "upside": round(upside, 1) if upside is not None else None,
        "opinion": opinion,
        "confidence": confidence,
        "primaryModel": primaryKey,
        "companyType": models.get("companyType"),
        "lifeCyclePhase": lifePhase,
        "triangulation": triangulation,
        "dividendFloor": ddm_floor,
        "qualityWACC": qw,
        "allMethods": {k: round(v) for k, v in allMethods.items()},
    }
    # P1a: reverse-DCF 헤드라인 + 재투자 진단 (펀더멘털 path 일 때만, 전부 guarded)
    rdrivers = twoStageDetail.get("reinvestmentDrivers") if twoStageDetail else None
    if rdrivers:
        out["reinvestmentCheck"] = rdrivers
        try:
            from dartlab.analysis.valuation._dFVDrivers import reverseDcfExhibit

            _sh = _inferShares(company, basePeriod=basePeriod)
            if currentPrice and _sh and _sh > 0:
                rdcf = reverseDcfExhibit(
                    company,
                    waccPct=adjusted_wacc,
                    fundamentalGrowth=rdrivers.get("fundamentalGrowth"),
                    marketCap=currentPrice * _sh,
                )
                if rdcf:
                    out["reverseDcf"] = rdcf
        except (ImportError, AttributeError, ValueError, TypeError):
            pass

    _dfvApplyGoingConcern(out, goingConcern, survival)
    _dfvApplyTwoStage(out, twoStageDetail)
    _dfvApplyRealOptions(out, company, basePeriod, ov)
    _dfvApplyLiquidation(out, liquidationDetail)
    _dfvApplyConsistency(out, consistency)
    _dfvApplyOverrideMeta(out, ov, _primary_switch_reason)
    return out
