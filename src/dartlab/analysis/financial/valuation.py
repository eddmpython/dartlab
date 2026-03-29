"""가치평가 축 -- 기존 밸류에이션 엔진을 analysis 14축 패턴으로 래핑.

calc 함수 9개: DCF, DDM, 상대가치, RIM, 목표주가, 역내재성장률,
민감도, 종합합성, 플래그.

모든 함수는 (company) -> dict | None 시그니처를 따른다.
"""

from __future__ import annotations

import logging
from typing import Any

from dartlab.analysis.valuation.pricetarget import compute_price_target
from dartlab.analysis.valuation.residualIncome import calcResidualIncome as _rimCalc

log = logging.getLogger(__name__)


# ── IndustryGroup → SECTOR_ELASTICITY 키 매핑 ──

_IG_TO_SECTOR_KEY: dict[str, str] = {
    "SEMICONDUCTOR": "반도체",
    "AUTO": "자동차",
    "CHEMICAL": "화학",
    "METALS": "철강",
    "CONSTRUCTION": "건설",
    "CONSTRUCTION_MATERIALS": "건설",
    "BANK": "금융/은행",
    "INSURANCE": "금융/보험",
    "DIVERSIFIED_FINANCIALS": "금융/증권",
    "SOFTWARE": "IT/소프트웨어",
    "IT_SERVICE": "IT/소프트웨어",
    "INTERNET": "IT/소프트웨어",
    "TECH_HARDWARE": "전자/하드웨어",
    "DISPLAY": "디스플레이",
    "TELECOM": "통신",
    "RETAIL": "유통",
    "FOOD_BEV_TOBACCO": "식품",
    "FOOD_STAPLES": "식품",
    "HOUSEHOLD": "식품",
    "PHARMA_BIO": "제약/바이오",
    "HEALTHCARE_EQUIP": "제약/바이오",
    "UTILITIES": "전력/에너지",
    "ELECTRIC": "전력/에너지",
    "GAS_UTILITY": "전력/에너지",
    "ENERGY_EQUIP": "에너지/자원",
    "OIL_GAS": "에너지/자원",
    "CAPITAL_GOODS": "산업재",
    "MACHINERY": "산업재",
    "TRANSPORTATION": "산업재",
    "COMMERCIAL_SERVICE": "산업재",
    "SHIPBUILDING": "조선",
    "CONSUMER_DURABLES": "섬유/의류",
    "CONSUMER_SERVICE": "유통",
    "MEDIA_ENTERTAINMENT": "미디어/엔터",
    "MEDIA": "미디어/엔터",
    "GAME": "게임",
    "REAL_ESTATE": "부동산",
    "REIT": "부동산",
    "AEROSPACE_DEFENSE": "산업재",
    "HOTEL_LEISURE": "유통",
}


def _resolveSectorKey(company: Any) -> str | None:
    """company.sector에서 SECTOR_ELASTICITY 키를 추출."""
    try:
        sectorInfo = company.sector
        if sectorInfo is None:
            return None
        igName = sectorInfo.industryGroup.name
        return _IG_TO_SECTOR_KEY.get(igName)
    except (AttributeError, ValueError):
        return None


# ── 시가 연동 헬퍼 ──


def _fetchPriceContext(company: Any) -> dict | None:
    """gather.price에서 현재가/시총 가져오기 (sync).

    같은 company에 대해 세션 내 1회만 네트워크 호출.
    실패 시 None 반환 -- 시가 의존 calc만 graceful skip.
    """
    # company._cache에 저장하여 동일 세션 내 재활용
    cache = getattr(company, "_cache", None)
    _KEY = "_priceContext"
    if cache is not None and _KEY in cache:
        return cache[_KEY]

    stockCode = getattr(company, "stockCode", None)
    if not stockCode:
        return None

    result = None
    try:
        from dartlab.gather.http import run_async
        from dartlab.gather.price import fetch

        snapshot = run_async(fetch(stockCode, market="KR"))
        if snapshot is not None:
            result = {
                "currentPrice": snapshot.current,
                "marketCap": snapshot.market_cap,
                "per": snapshot.per,
                "pbr": snapshot.pbr,
            }
    except (ImportError, OSError, RuntimeError, AttributeError):
        log.debug("price fetch 실패: %s", stockCode)

    if cache is not None:
        cache[_KEY] = result
    return result


def _getSeriesAndShares(company: Any) -> tuple[dict | None, int | None, str]:
    """company에서 annual series, shares, currency 추출."""
    try:
        ann = company.annual
        if ann is None:
            return None, None, getattr(company, "currency", "KRW") or "KRW"
        series = ann[0] if isinstance(ann, tuple) else ann
    except (ValueError, KeyError, AttributeError):
        return None, None, getattr(company, "currency", "KRW") or "KRW"

    shares = None
    profile = getattr(company, "profile", None)
    if profile:
        sharesVal = getattr(profile, "sharesOutstanding", None)
        if sharesVal:
            shares = int(sharesVal)

    # fallback: 시가총액/현재가에서 shares 추정
    if shares is None:
        price = _fetchPriceContext(company)
        if price and price.get("marketCap") and price.get("currentPrice"):
            mc = price["marketCap"]
            cp = price["currentPrice"]
            if mc > 0 and cp > 0:
                shares = int(mc / cp)

    currency = getattr(company, "currency", "KRW") or "KRW"
    return series, shares, currency


def _getSectorParams(company: Any):
    """company에서 sectorParams 추출."""
    try:
        return getattr(company, "sectorParams", None)
    except AttributeError:
        return None


# ── calc 함수 9개 ──


def calcDcf(company: Any) -> dict | None:
    """DCF (현금흐름 할인) 밸류에이션."""
    from dartlab.core.finance.dcf import dcfValuation

    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None

    result = dcfValuation(
        series,
        shares=shares,
        sectorParams=sp,
        currentPrice=currentPrice,
        currency=currency,
    )
    return {
        "perShareValue": result.perShareValue,
        "enterpriseValue": result.enterpriseValue,
        "equityValue": result.equityValue,
        "discountRate": result.discountRate,
        "growthRateInitial": result.growthRateInitial,
        "terminalGrowth": result.terminalGrowth,
        "marginOfSafety": result.marginOfSafety,
        "fcfProjections": result.fcfProjections,
        "fcfHistorical": result.fcfHistorical,
        "exitMultipleTv": result.exitMultipleTv,
        "exitMultipleEv": result.exitMultipleEv,
        "exitMultiplePerShare": result.exitMultiplePerShare,
        "assumptions": result.assumptions,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }


def calcDdm(company: Any) -> dict | None:
    """DDM (배당 할인) 밸류에이션.

    calcDividendPolicy의 연간 배당 데이터를 우선 사용하여
    분기 CF 합산 오류를 방지한다.
    """
    from dartlab.core.finance.dcf import ddmValuation
    from dartlab.analysis.financial.capitalAllocation import calcDividendPolicy

    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None

    # calcDividendPolicy에서 연간 배당 추출 (정확한 연간 합산)
    annualDivs: list[float] | None = None
    divPolicy = calcDividendPolicy(company)
    if divPolicy and divPolicy.get("history"):
        hist = divPolicy["history"]
        # 의미 있는 배당만 추출 (주당 100원 미만 잡액 제거)
        minDiv = shares * 100 if shares and shares > 0 else 1e9
        annualDivs = [
            h["dividendsPaid"]
            for h in reversed(hist)
            if h.get("dividendsPaid") and h["dividendsPaid"] > minDiv
        ]

    result = ddmValuation(
        series,
        shares=shares,
        sectorParams=sp,
        currentPrice=currentPrice,
        annualDividends=annualDivs,
    )
    if result.modelUsed == "N/A" and not result.warnings:
        return None

    return {
        "intrinsicValue": result.intrinsicValue,
        "dividendPerShare": result.dividendPerShare,
        "dividendYield": result.dividendYield,
        "payoutRatio": result.payoutRatio,
        "dividendGrowth": result.dividendGrowth,
        "modelUsed": result.modelUsed,
        "discountRate": result.discountRate,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }


def calcRelativeValuation(company: Any) -> dict | None:
    """상대가치 (PER/PBR/EV-EBITDA/PSR/PEG) 밸류에이션."""
    from dartlab.core.finance.dcf import relativeValuation

    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    marketCap = price["marketCap"] if price else None
    currentPrice = price["currentPrice"] if price else None

    result = relativeValuation(
        series,
        sectorParams=sp,
        marketCap=marketCap,
        shares=shares,
        currentPrice=currentPrice,
    )
    return {
        "sectorMultiples": result.sectorMultiples,
        "currentMultiples": result.currentMultiples,
        "impliedValues": result.impliedValues,
        "premiumDiscount": result.premiumDiscount,
        "consensusValue": result.consensusValue,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }


def calcResidualIncome(company: Any) -> dict | None:
    """RIM (잔여이익모델) 밸류에이션."""
    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None
    beta = sp.beta if sp else None

    result = _rimCalc(
        series,
        shares=shares,
        currentPrice=currentPrice,
        currency=currency,
        beta=beta,
    )
    if result is None:
        return None

    return {
        "bps": result.bps,
        "coe": result.coe,
        "riHistory": result.riHistory,
        "intrinsicValue": result.intrinsicValue,
        "upside": result.upside,
        "terminalValue": result.terminalValue,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }


def calcPriceTarget(company: Any) -> dict | None:
    """확률 가중 주가 목표가 (5 시나리오 + Monte Carlo)."""
    series, shares, currency = _getSeriesAndShares(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None
    marketCap = price["marketCap"] if price else None
    sectorKey = _resolveSectorKey(company)

    result = compute_price_target(
        series,
        sector_key=sectorKey,
        current_price=currentPrice,
        shares=shares,
        market_cap=marketCap,
    )
    scenarios = []
    for s in result.scenarios:
        scenarios.append(
            {
                "name": s.scenario_name,
                "probability": s.probability,
                "perShareValue": s.per_share_value,
                "enterpriseValue": s.enterprise_value,
            }
        )

    return {
        "weightedTarget": result.weighted_target,
        "percentiles": result.percentiles,
        "expectedValue": result.expected_value,
        "upside": result.upside_pct,
        "probabilityAboveCurrent": result.probability_above_current,
        "signal": result.signal,
        "confidence": result.confidence,
        "scenarios": scenarios,
        "waccDetails": result.wacc_details,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }


def calcReverseImplied(company: Any) -> dict | None:
    """역내재성장률 -- 시장이 내재하는 매출 성장률 역산."""
    from dartlab.core.finance.priceImplied import reverseImpliedGrowth

    series, shares, currency = _getSeriesAndShares(company)
    price = _fetchPriceContext(company)
    if not price or not price.get("marketCap"):
        return None

    result = reverseImpliedGrowth(series, marketCap=price["marketCap"])
    if result is None:
        return None

    return {
        "impliedGrowthRate": result.impliedGrowthRate,
        "impliedRevenue": result.impliedRevenue,
        "marketCap": result.marketCap,
        "latestRevenue": result.latestRevenue,
        "assumedMargin": result.assumedMargin,
        "assumedWacc": result.assumedWacc,
        "signal": result.signal,
        "warnings": result.warnings,
        "currentPrice": price.get("currentPrice"),
        "currency": currency,
    }


def calcSensitivity(company: Any) -> dict | None:
    """WACC x 영구성장률 민감도 그리드."""
    from dartlab.core.finance.dcf import sensitivityAnalysis

    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None

    result = sensitivityAnalysis(
        series,
        shares=shares,
        sectorParams=sp,
        currentPrice=currentPrice,
        currency=currency,
    )
    if result is None:
        return None

    return {
        "grid": result.grid,
        "baseWacc": result.baseWacc,
        "baseTerminalGrowth": result.baseTerminalGrowth,
        "baseValue": result.baseValue,
        "currentPrice": currentPrice,
        "currency": currency,
    }


def _classifyCompanyType(company: Any, series: dict) -> tuple[str, dict[str, float]]:
    """기업 특성 분류 -> 최적 모델 가중치 반환 (CFA 프레임워크 기반).

    Returns:
        (companyType, weights) where companyType is one of:
        "financial", "growth", "cyclical", "dividend", "general"
    """
    from dartlab.core.finance.extract import getAnnualValues, getRevenueGrowth3Y

    sector = getattr(company, "sector", None)
    isFinancial = False
    if sector:
        sectorVal = getattr(sector, "sector", None)
        if sectorVal and hasattr(sectorVal, "value") and sectorVal.value == "금융":
            isFinancial = True

    if isFinancial:
        # 금융업: FCF 무의미, RIM/DDM 우선, DCF 제외
        return "financial", {"DCF": 0.0, "DDM": 0.35, "상대가치": 0.30, "RIM": 0.35}

    # 성장주 판별: 매출 3Y CAGR > 15%
    revCagr = getRevenueGrowth3Y(series)
    if revCagr is not None and revCagr > 15:
        return "growth", {"DCF": 0.45, "DDM": 0.05, "상대가치": 0.25, "RIM": 0.25}

    # 순환주 판별: 이익 변동성 높은 기업 (NI 표준편차/평균 > 0.5)
    niVals = getAnnualValues(series, "IS", "net_profit")
    if niVals and len(niVals) >= 4:
        validNi = [v for v in niVals[-5:] if v is not None and v > 0]
        if len(validNi) >= 3:
            mean = sum(validNi) / len(validNi)
            if mean > 0:
                var = sum((v - mean) ** 2 for v in validNi) / len(validNi)
                cv = (var ** 0.5) / mean
                if cv > 0.5:
                    # 순환주: Normalized earnings 기반 상대가치 우선
                    return "cyclical", {"DCF": 0.25, "DDM": 0.10, "상대가치": 0.40, "RIM": 0.25}

    # 배당주: 안정적 ��당 (DDM 가중 높임)
    divVals = getAnnualValues(series, "CF", "dividends_paid")
    if divVals and len(divVals) >= 3:
        recentDivs = [abs(v) for v in divVals[-3:] if v is not None and v != 0]
        if len(recentDivs) >= 3:
            return "dividend", {"DCF": 0.25, "DDM": 0.30, "상대가치": 0.25, "RIM": 0.20}

    # 일반
    return "general", {"DCF": 0.35, "DDM": 0.15, "상대가치": 0.25, "RIM": 0.25}


def calcValuationSynthesis(company: Any) -> dict | None:
    """종합 밸류에이션 -- 기업 유형별 자동 모델 선택 + 가중 합성."""
    from dartlab.core.finance.dcf import fullValuation

    series, shares, currency = _getSeriesAndShares(company)
    if series is None:
        return None

    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None
    marketCap = price["marketCap"] if price else None

    companyType, weights = _classifyCompanyType(company, series)

    result = fullValuation(
        series,
        shares=shares,
        sectorParams=sp,
        marketCap=marketCap,
        currentPrice=currentPrice,
        currency=currency,
    )

    # 극단값 필터: 현재가 2% 미만 결과는 무의미 → 제외
    _minVal = currentPrice * 0.02 if currentPrice and currentPrice > 0 else 0

    estimates: list[dict] = []
    if result.dcf and result.dcf.perShareValue and result.dcf.perShareValue > _minVal:
        estimates.append({"method": "DCF", "value": result.dcf.perShareValue, "weight": weights.get("DCF", 0)})
    if result.ddm and result.ddm.intrinsicValue and result.ddm.intrinsicValue > _minVal:
        estimates.append({"method": "DDM", "value": result.ddm.intrinsicValue, "weight": weights.get("DDM", 0)})
    if result.relative and result.relative.consensusValue and result.relative.consensusValue > _minVal:
        estimates.append({"method": "상대가치", "value": result.relative.consensusValue, "weight": weights.get("상대가치", 0)})

    # RIM 결과도 합성에 포함
    beta = sp.beta if sp else None
    rimResult = _rimCalc(series, shares=shares, currentPrice=currentPrice, currency=currency, beta=beta)
    if rimResult and rimResult.intrinsicValue and rimResult.intrinsicValue > _minVal:
        estimates.append({"method": "RIM", "value": rimResult.intrinsicValue, "weight": weights.get("RIM", 0)})

    # 가중 합성 적정가
    weightedFairValue = None
    if estimates:
        totalW = sum(e["weight"] for e in estimates if e["weight"] > 0)
        if totalW > 0:
            # 미가용 모델의 가중치를 비례 재배분
            normFactor = 1.0 / totalW
            weightedFairValue = sum(e["value"] * e["weight"] * normFactor for e in estimates)
            weightedFairValue = round(weightedFairValue, 0)

    # 역내재성장률 — 모든 모델 실패 시 시장 기대 역산으로 보충
    reverseImplied = None
    if not estimates or weightedFairValue is None:
        ri = calcReverseImplied(company)
        if ri:
            reverseImplied = {
                "impliedGrowthRate": ri.get("impliedGrowthRate"),
                "signal": ri.get("signal"),
            }

    return {
        "fairValueRange": result.fairValueRange,
        "verdict": result.verdict,
        "currentPrice": currentPrice,
        "estimates": estimates,
        "companyType": companyType,
        "weightedFairValue": weightedFairValue,
        "modelWeights": weights,
        "currency": currency,
        "reverseImplied": reverseImplied,
    }


def calcValuationFlags(company: Any) -> list[dict]:
    """가치평가 관련 플래그 집계."""
    flags: list[dict] = []

    dcf = calcDcf(company)
    if dcf:
        mos = dcf.get("marginOfSafety")
        if mos is not None:
            if mos > 30:
                flags.append({"signal": "opportunity", "label": f"DCF 안전마진 {mos:.0f}% -- 저평가 가능"})
            elif mos < -30:
                flags.append({"signal": "warning", "label": f"DCF 안전마진 {mos:.0f}% -- 고평가 주의"})

    ddm = calcDdm(company)
    if ddm and ddm.get("modelUsed") == "N/A":
        flags.append({"signal": "info", "label": "DDM 적용 불가 (무배당/데이터 부족)"})

    synthesis = calcValuationSynthesis(company)
    if synthesis:
        verdict = synthesis.get("verdict", "")
        if verdict == "저평가":
            flags.append({"signal": "opportunity", "label": "종합 판정: 저평가"})
        elif verdict == "고평가":
            flags.append({"signal": "warning", "label": "종합 판정: 고평가"})

    return flags
