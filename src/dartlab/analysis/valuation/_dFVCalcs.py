"""dFV (dartlab Fair Value) 계산 헬퍼 11 종. calcDFV 가 호출한다.

_collectAllValues, _getBaseWACC, _triangulate, _getCurrentPrice, _calcOpinion,
_calcLiquidationValue, _inferShares, _calcLiquidationDetail, _calcTwoStageDcf,
_applySurvivalAdjustment, _buildConsistency. 모두 inline import 로 외부 함수 호출.

_inferShares 본체는 `_valuationInputAccess` 로 옮겼다 (controlSynergy 와 공유).
호출 경로 보존을 위해 여기서 re-export 한다.

dFV.py god module 분리 일환.
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.valuation._dFVTsd import (
    _tsdBuildPhases,
    _tsdExtractBaseFcf,
    _tsdExtractNetDebtShares,
    _tsdMaybeNormalizeFcf,
    _tsdResolveHighGrowth,
    _tsdResolveTerminalGrowth,
    _tsdResolveWacc,
)
from dartlab.analysis.valuation._valuationInputAccess import _inferShares
from dartlab.analysis.valuation.types import opinionFromUpside


def _collectAllValues(company: Any, basePeriod: str | None) -> dict:
    """모든 방법론 적정가 수집."""
    values: dict = {}
    try:
        from dartlab.analysis.financial.valuation import calcValuationSynthesis

        synth = calcValuationSynthesis(company, basePeriod=basePeriod)
        if synth:
            method_map = {"DCF": "dcf", "DDM": "ddm", "상대가치": "relative", "RIM": "rim"}
            for est in synth.get("estimates", []):
                key = method_map.get(est.get("method", ""))
                val = est.get("value")
                if key and val and val > 0:
                    values[key] = float(val)
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    return values


def _getBaseWACC(company: Any) -> float:
    """기본 WACC 추출. Phase 4 G12: CAPM 기반 우선, 섹터 fallback.

    기존은 sectorParams.discountRate (대기업 10% 고정) 만 사용 → 삼성 AA급에 과도.
    Phase 4: `_estimateWacc` (CAPM + 시총 감쇠 + country) 우선 → 하한 4% 경계 반영.
    """
    # 1순위: CAPM 기반 (compute_company_wacc 경유)
    try:
        from dartlab.analysis.financial.investmentAnalysis import _estimateWacc

        w = _estimateWacc(company)
        if w is not None and 3.0 <= w <= 25.0:
            return float(w)
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    # 2순위: sectorParams (기존 fallback)
    try:
        from dartlab.analysis.valuation.dcf import _getSectorParams

        si = getattr(company, "sector", None)
        params = _getSectorParams(si.sector if si else None, si.industryGroup if si else None) if si else None
        if params:
            return params.discountRate
    except (ImportError, AttributeError):
        pass
    return 10.0  # 최종 fallback


def _triangulate(primaryKey: str, primaryValue: float, secondaryKeys: list[str], allMethods: dict) -> dict:
    """삼각검증: primary와 secondary 괴리 체크."""
    checks = []
    for key in secondaryKeys:
        sec_value = allMethods.get(key)
        if sec_value is None or sec_value <= 0:
            continue
        divergence = abs(primaryValue - sec_value) / primaryValue
        if divergence < 0.20:
            verdict = "합의"
        elif divergence < 0.50:
            verdict = "부분 합의"
        else:
            verdict = "불일치"
        checks.append(
            {
                "method": key,
                "value": round(sec_value),
                "divergence": round(divergence * 100, 1),
                "verdict": verdict,
            }
        )

    # 종합 신뢰도
    if not checks:
        confidence = "low"
    elif all(c["verdict"] == "합의" for c in checks):
        confidence = "high"
    elif any(c["verdict"] == "불일치" for c in checks):
        confidence = "low"
    else:
        confidence = "medium"

    return {"checks": checks, "confidence": confidence}


def _getCurrentPrice(company: Any) -> float | None:
    """현재 주가 추출. currentPrice 속성 우선, 없으면 gather 경유.

    Returns
    -------
    float | None
        현재 주가 (원). 조회 실패 시 None.
    """
    # 두 갈래가 다 죽어 있었다. `currentPrice` 는 표면에서 빠진 이름이라 늘 None 이고,
    # `getDefaultGather()` 가 돌려주는 객체는 호출할 수 없어 TypeError 로 떨어졌다. 둘 다
    # except 가 삼켜서 이 함수는 어느 회사에서도 주가를 못 냈다. 공개 계약으로 부른다.
    code = getattr(company, "stockCode", "")
    if not code:
        return None
    try:
        import dartlab

        rows = dartlab.gather("price", code)
    except (ImportError, AttributeError, ValueError, TypeError, KeyError, OSError, RuntimeError):
        return None
    if rows is None or getattr(rows, "height", 0) == 0 or "close" not in getattr(rows, "columns", []):
        return None
    last = rows["close"][-1]
    return float(last) if last is not None else None


def _calcOpinion(upside: float | None) -> str:
    """상승여력을 투자의견 라벨로 바꾼다. 기준표는 `types.opinionFromUpside` 가 갖는다.

    예전에는 이 표를 세 파일이 글자까지 똑같이 복사해 갖고 있었다. 사용자에게 그대로
    보이는 판정이라 하나만 임계값을 옮기면 같은 회사가 화면마다 다른 의견을 받는다.
    """
    return opinionFromUpside(upside)


def _calcLiquidationValue(company: Any, overrides: dict) -> float | None:
    """Simple 청산가치. survival weighting 용 (book × (1-discount))."""
    from dartlab.synth.overrides import applyOverride

    explicit = applyOverride(None, "liquidationValue", overrides)
    if explicit is not None:
        return float(explicit)

    try:
        bs = company.select("BS", ["자본총계", "총발행주식수"])
        from dartlab.core.utils.helpers import toDictBySnakeId

        parsed = toDictBySnakeId(bs)
        if not parsed:
            return None
        data, periods = parsed
        if not periods:
            return None
        latest = periods[0]
        equity = (data.get("total_stockholders_equity") or {}).get(latest)
        shares = (data.get("outstanding_shares") or {}).get(latest)
        if not equity or not shares or shares <= 0:
            return None
        discount = applyOverride(0.25, "liquidationDiscount", overrides)
        discount = max(0.0, min(0.7, float(discount)))
        return (equity * (1 - discount)) / shares
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        return None


def _calcLiquidationDetail(company: Any, overrides: dict) -> dict | None:
    """Damodaran 자산별 회수율 청산가치 (Dark Side Ch.9)."""
    try:
        from dartlab.analysis.valuation.dcf import liquidationValuation
        from dartlab.core.utils.helpers import toDictBySnakeId
    except ImportError:
        return None

    try:
        bs = company.select(
            "BS",
            [
                "현금및현금성자산",
                "매출채권",
                "재고자산",
                "유형자산",
                "무형자산",
                "자산총계",
                "부채총계",
            ],
        )
        parsed = toDictBySnakeId(bs)
        if not parsed:
            return None
        data, periods = parsed
        if not periods:
            return None
        latest = periods[0]

        def _get(*keys: str) -> float:
            """BS 다중 키에서 첫 번째 유효 값 추출 (None → 0)."""
            for k in keys:
                v = (data.get(k) or {}).get(latest)
                if v:
                    return float(v)
            return 0.0

        cash = _get("cash_and_cash_equivalents", "cash_and_equivalents")
        receivables = _get("trade_receivables", "trade_and_other_receivables", "매출채권")
        inventory = _get("inventories", "재고자산")
        tangible = _get("tangible_assets", "유형자산")
        intangible = _get("intangible_assets", "무형자산")
        total_assets = _get("total_assets", "자산총계")
        total_liab = _get("total_liabilities", "부채총계")
        shares = _inferShares(company)

        other = max(0.0, total_assets - cash - receivables - inventory - tangible - intangible)

        return liquidationValuation(
            cash=cash,
            receivables=receivables,
            inventory=inventory,
            tangibleAssets=tangible,
            intangibleAssets=intangible,
            otherAssets=other,
            totalLiabilities=total_liab,
            shares=shares,
        )
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        return None


def _calcTwoStageDcf(
    company: Any, lifePhase: str | None, overrides: dict, basePeriod: str | None = None
) -> dict | None:
    """Damodaran Multi-stage DCF (Ch.12). lifeCycle 별 phase 자동 구성.

    - earlyGrowth → 3-phase: [5, 3, 2]년 × [g_high, g_high×0.5, g_high×0.2]
    - highGrowth → 3-phase: [5, 3, 2]년 × [g_high, g_high×0.7, g_high×0.4]
    - matureGrowth / matureStable / decline → 단일 phase

    Returns
    -------
    dict | None
        multiStageDcf(...) 결과. 필수 데이터 (positive FCF / BS periods) 없으면 None.
    """
    try:
        from dartlab.analysis.valuation.dcf import multiStageDcf
        from dartlab.synth.overrides import applyOverride
    except ImportError:
        return None

    wacc = _tsdResolveWacc(company, overrides)
    terminal_g = _tsdResolveTerminalGrowth(lifePhase, company, overrides)

    margin_path = applyOverride(None, "marginPath", overrides)
    reinvestment_path = applyOverride(None, "reinvestmentPath", overrides)
    rates_override = applyOverride(None, "growthRates", overrides)

    # de-gate (P1a): 성장을 매출 CAGR 외삽이 아니라 펀더멘털 anchor 로. g=reinvest×ROIC,
    # ROIC→WACC fade. growthRates override·ROIC 추정 실패 시 기존 phase 로 폴백(가정 명시).
    drivers = None
    if rates_override is None:
        try:
            from dartlab.analysis.valuation._dFVDrivers import buildReinvestmentPath

            drivers = buildReinvestmentPath(company, waccPct=wacc, basePeriod=basePeriod)
        except (ImportError, AttributeError, ValueError, TypeError):
            drivers = None
    if drivers and drivers.get("growthRates"):
        rates_vec = drivers["growthRates"]
        years_vec = [1] * len(rates_vec)
    else:
        highG = _tsdResolveHighGrowth(company)
        years_vec, rates_vec = _tsdBuildPhases(lifePhase, highG, overrides)

    baseFcf = _tsdExtractBaseFcf(company)
    if not baseFcf or baseFcf <= 0:
        return None
    baseFcf = _tsdMaybeNormalizeFcf(baseFcf, lifePhase, company)

    nd_shares = _tsdExtractNetDebtShares(company)
    if nd_shares is None:
        return None
    net_debt, shares = nd_shares

    result = multiStageDcf(
        baseFcf=baseFcf,
        growthYears=years_vec,
        growthRates=rates_vec,
        terminalGrowthRate=terminal_g,
        wacc=wacc,
        marginPath=margin_path,
        reinvestmentPath=reinvestment_path,
        netDebt=net_debt,
        shares=shares,
    )
    if result is None:
        return None
    # 드라이버 시나리오(±12% 산술밴드 폐기) + 펀더멘털 진단 부착. 펀더멘털 path 일 때만
    # (phase 폴백은 per-year 가 아니라 buildDriverScenarios 가정 위반).
    if drivers:
        result["reinvestmentDrivers"] = drivers
        try:
            from dartlab.analysis.valuation._dFVDrivers import buildDriverScenarios

            scen = buildDriverScenarios(
                baseFcf=baseFcf,
                growthRates=rates_vec,
                terminalGrowth=terminal_g,
                wacc=wacc,
                netDebt=net_debt,
                shares=shares,
            )
            if scen:
                result["driverScenarios"] = scen
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
    return result


def _applySurvivalAdjustment(company: Any, primaryValue: float, overrides: dict) -> dict | None:
    """Dark Side of Valuation: Going-Concern × pSurvival 가중.

    CHS 부도확률 (12M PD) 을 chsFeatures 경로로 실제 추출. 실패 시 safe_default 폴백.
    """
    try:
        from dartlab.synth.distress import applySurvivalWeight, calcSurvivalWeight, computeChsProbability
        from dartlab.synth.overrides import applyOverride
    except ImportError:
        return None

    forced_p = applyOverride(None, "pSurvival", overrides)
    discount_override = applyOverride(None, "liquidationDiscount", overrides)

    if forced_p is not None:
        survival_dict = calcSurvivalWeight(
            probability=max(0.0, min(1.0, float(forced_p))),
            liquidationDiscount=discount_override,
        )
    else:
        # CHS 실추출: chsFeatures SSOT 경유
        chs_result = computeChsProbability(company)
        if chs_result:
            survival_dict = calcSurvivalWeight(
                probability=chs_result["probability"],
                zone=chs_result["zone"],
                liquidationDiscount=discount_override,
            )
        else:
            # safe_default 폴백
            survival_dict = calcSurvivalWeight(
                probability=None,
                zone=None,
                liquidationDiscount=discount_override,
            )

    # liquidation 값: Damodaran 자산별 회수 detail 의 perShare 우선, 없으면 book × (1-discount)
    liq_detail = _calcLiquidationDetail(company, overrides)
    liq_per_share = None
    if liq_detail and liq_detail.get("perShare"):
        liq_per_share = liq_detail["perShare"]
    else:
        liq_per_share = _calcLiquidationValue(company, overrides)

    weighted = applySurvivalWeight(primaryValue, liq_per_share, survival_dict)
    if liq_per_share is not None:
        weighted["liquidationValue"] = liq_per_share
    weighted["pSurvival"] = survival_dict.get("pSurvival")
    weighted["source"] = survival_dict.get("source")
    weighted["annualHazard"] = survival_dict.get("annualHazard")
    return weighted


def _buildConsistency(
    company: Any,
    primaryKey: str,
    primaryValue: float,
    triangulation: dict,
    wacc: float | None,
    overrides: dict,
) -> dict | None:
    """Cash Flow Consistency 검증. dFV 결과에 consistencyFlags 주입용."""
    try:
        from dartlab.analysis.valuation.consistency import calcCashFlowConsistency
        from dartlab.synth.overrides import applyOverride
    except ImportError:
        return None

    # ROIC 추출
    roic_pct: float | None = None
    try:
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline

        roic_data = calcRoicTimeline(company)
        if roic_data and roic_data.get("history"):
            roic_pct = roic_data["history"][0].get("roic")
    except (ImportError, AttributeError, ValueError, TypeError):
        pass

    tg = applyOverride(None, "terminalGrowth", overrides)
    country = applyOverride(None, "countryCode", overrides)
    currency = getattr(company, "currency", None)

    models_used = 1 + len(triangulation.get("checks") or [])

    return calcCashFlowConsistency(
        roicPct=roic_pct,
        waccPct=wacc,
        terminalGrowthPct=tg,
        primaryModel=primaryKey,
        modelsUsed=models_used,
        country=country,
        currency=currency,
    )


__all__ = [
    "_applySurvivalAdjustment",
    "_buildConsistency",
    "_calcLiquidationDetail",
    "_calcLiquidationValue",
    "_calcOpinion",
    "_calcTwoStageDcf",
    "_collectAllValues",
    "_getBaseWACC",
    "_getCurrentPrice",
    "_inferShares",
    "_triangulate",
]
