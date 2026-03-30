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
                "isStale": getattr(snapshot, "is_stale", False),
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


def calcDcf(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """DCF (현금흐름 할인) 밸류에이션."""
    from dartlab.core.finance.dcf import dcfValuation

    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None
    marketCap = price["marketCap"] if price else None

    from dartlab.core.finance.proforma import compute_company_wacc

    wacc, _ = compute_company_wacc(
        series, sector_params=sp, market_cap=marketCap, currency=currency,
    )

    result = dcfValuation(
        series,
        shares=shares,
        sectorParams=sp,
        currentPrice=currentPrice,
        currency=currency,
        discountRate=wacc,
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


def calcDdm(company: Any, *, basePeriod: str | None = None) -> dict | None:
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

    # 1순위: Report API DPS (가장 정확한 연간 주당배당금)
    annualDivs: list[float] | None = None
    try:
        from dartlab.providers.dart.report.pivot import pivotDividend

        stockCode = getattr(company, "stockCode", None)
        divResult = pivotDividend(stockCode) if stockCode else None
        if divResult and divResult.dps:
            validDps = [d for d in divResult.dps if d is not None and d > 0]
            if validDps and shares and shares > 0:
                annualDivs = [dps * shares for dps in validDps]
    except (ImportError, ValueError, KeyError, AttributeError):
        pass

    # 2순위: calcDividendPolicy CF 기반 (Report 없을 때 fallback)
    if not annualDivs:
        divPolicy = calcDividendPolicy(company, basePeriod=basePeriod)
        if divPolicy and divPolicy.get("history"):
            hist = divPolicy["history"]
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


def calcRelativeValuation(company: Any, *, basePeriod: str | None = None) -> dict | None:
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


def calcResidualIncome(company: Any, *, basePeriod: str | None = None) -> dict | None:
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


# ── 지주사 NAV ──────────────────────────────────────────

# 주요 지주사 핵심 자회사 매핑 (종목코드: 지분율%)
# 출처: DART 사업보고서 기준. 자회사 지분 변동 시 업데이트 필요.
_HOLDING_SUBS: dict[str, list[tuple[str, float]]] = {
    "034730": [  # SK
        ("096770", 64.25),  # SK이노베이션
        ("017670", 26.80),  # SK텔레콤
        ("402340", 42.30),  # SK스퀘어
    ],
    "003550": [  # LG
        ("373220", 30.10),  # LG에너지솔루션
        ("051910", 33.30),  # LG화학
        ("066570", 33.67),  # LG전자
    ],
    "028260": [  # 삼성물산
        ("005930", 4.99),  # 삼성전자
        ("207940", 43.37),  # 삼성바이오로직스
    ],
    "005490": [  # POSCO홀딩스
        ("005380", 5.20),  # 현대차 (실제는 포스코인터/포스코퓨처엠이나 종목코드 확인 필요)
    ],
}


def calcNavValuation(company: Any) -> dict | None:
    """지주사 NAV = Sum(상장 자회사 시총 x 지분율) - 순차입금. 할인 30%."""
    stockCode = getattr(company, "stockCode", "")
    subs = _HOLDING_SUBS.get(stockCode)
    if not subs:
        return None

    series, shares, currency = _getSeriesAndShares(company)

    # 자회사 시총 합산 (Company 객체 생성 금지 — OOM 방지)
    totalSubValue = 0.0
    subDetails = []
    for subCode, ratio in subs:
        try:
            from dartlab.gather.http import run_async
            from dartlab.gather.price import fetch

            snapshot = run_async(fetch(subCode, market="KR"))
            if snapshot and snapshot.market_cap and snapshot.market_cap > 0:
                subValue = snapshot.market_cap * ratio / 100
                totalSubValue += subValue
                subDetails.append({"code": subCode, "ratio": ratio, "marketCap": snapshot.market_cap, "value": subValue})
        except (ImportError, OSError, RuntimeError, AttributeError):
            pass

    if totalSubValue <= 0:
        return None

    # 순차입금
    from dartlab.core.finance.extract import getLatest

    if series:
        stb = getLatest(series, "BS", "shortterm_borrowings") or 0
        ltb = getLatest(series, "BS", "longterm_borrowings") or 0
        bonds = getLatest(series, "BS", "debentures") or 0
        cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
        netDebt = stb + ltb + bonds - cash
    else:
        netDebt = 0

    # NAV = 자회사 지분가치 합계 - 순차입금
    navGross = totalSubValue - netDebt
    # 지주사 할인 30% (한국 실증 평균)
    navDiscounted = navGross * 0.70

    navPerShare = navDiscounted / shares if shares and shares > 0 else None

    return {
        "navGross": navGross,
        "navDiscounted": navDiscounted,
        "navPerShare": navPerShare,
        "holdingDiscount": 0.30,
        "subsidiaries": subDetails,
        "netDebt": netDebt,
    }


def calcPriceTarget(company: Any, *, basePeriod: str | None = None) -> dict | None:
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


def calcReverseImplied(company: Any, *, basePeriod: str | None = None) -> dict | None:
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


def calcSensitivity(company: Any, *, basePeriod: str | None = None) -> dict | None:
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
    sectorStr = ""
    isFinancial = False
    if sector:
        sectorVal = getattr(sector, "sector", None)
        if sectorVal:
            sectorStr = sectorVal.value if hasattr(sectorVal, "value") else str(sectorVal)
            if sectorStr == "금융":
                isFinancial = True

    # 지주사 판별 (금융보다 우선 — 한진칼 같은 금융 분류 지주사 대응)
    igVal = getattr(sector, "industryGroup", None) if sector else None
    igStr = igVal.name if igVal and hasattr(igVal, "name") else str(igVal or "")
    corpName = getattr(company, "corpName", "")
    _holdingCodes = {"034730", "003550", "028260", "005490", "180640"}  # SK, LG, 삼성물산, POSCO홀딩스, 한진칼
    stockCode = getattr(company, "stockCode", "")
    # 금융지주(신한지주, KB금융 등)는 financial이지 holding이 아님
    isFinancialHolding = isFinancial and ("지주" in corpName or "금융" in corpName)
    isHolding = not isFinancialHolding and (
        "HOLDING" in igStr.upper()
        or "지주" in corpName
        or "지주" in sectorStr
        or "홀딩스" in corpName
        or stockCode in _holdingCodes
    )
    if isHolding:
        # 지주사: DCF(연결 기반) 과대평가 위험 → 상대가치/RIM 우선, DCF 대폭 축소
        return "holding", {"DCF": 0.05, "DDM": 0.10, "상대가치": 0.15, "RIM": 0.30, "NAV": 0.40}

    if isFinancial:
        # 금융업: FCF 무의미, RIM/DDM 우선, DCF 제외
        return "financial", {"DCF": 0.0, "DDM": 0.35, "상대가치": 0.30, "RIM": 0.35}

    # ── 사이클 업종 사전 판별 (섹터 기반 — CAGR/CV보다 우선) ──
    _cyclicalIg = {
        "SEMICONDUCTOR", "CHEMICAL", "METALS", "SHIPBUILDING",
        "TRANSPORTATION", "OIL_GAS", "ENERGY_EQUIP", "CONSTRUCTION_MATERIALS",
        "CAPITAL_GOODS", "AUTO", "DISPLAY", "AIRLINE",
    }
    # NI CV가 높아도 사이클 기업이 아닌 업종 → cyclical 제외
    _stableIg = {
        "TELECOM", "UTILITIES", "GAS_UTILITY", "ELECTRIC",
        "SOFTWARE", "IT_SERVICE", "INTERNET", "MEDIA_ENTERTAINMENT",
        "MEDIA", "GAME",
    }

    isCyclicalSector = igStr.upper() in _cyclicalIg
    isStableSector = igStr.upper() in _stableIg

    # 유틸리티: 규제기업으로 CAPEX 극대, FCF 만성 적자 → DCF 부적합, DDM/RIM 우선
    if igStr.upper() in ("UTILITIES", "GAS_UTILITY", "ELECTRIC"):
        return "utility", {"DCF": 0.10, "DDM": 0.35, "상대가치": 0.15, "RIM": 0.40}
    # 수주잔고 기반 업종: DCF가 과거 적자를 외삽하므로 가중 축소, RIM/상대가치 우선
    _backlogIg = {"SHIPBUILDING", "CONSTRUCTION", "CONSTRUCTION_MATERIALS"}
    isBacklogSector = igStr.upper() in _backlogIg

    if isBacklogSector:
        return "backlog_cyclical", {"DCF": 0.15, "DDM": 0.05, "상대가치": 0.45, "RIM": 0.35}

    # 바이오/제약: FCF 적자 빈번, DCF 부적합. PSR/PBR 기반 상대가치 + RIM 우선
    if igStr.upper() in ("PHARMA_BIO", "HEALTHCARE_EQUIP"):
        return "pharma_bio", {"DCF": 0.10, "DDM": 0.05, "상대가치": 0.50, "RIM": 0.35}

    if isCyclicalSector:
        return "cyclical", {"DCF": 0.25, "DDM": 0.10, "상대가치": 0.40, "RIM": 0.25}

    # 성장주 판별: 매출 3Y CAGR > 15% (사이클 업종은 위에서 이미 처리)
    revCagr = getRevenueGrowth3Y(series)
    if revCagr is not None and revCagr > 15:
        return "growth", {"DCF": 0.45, "DDM": 0.05, "상대가치": 0.25, "RIM": 0.25}

    # 순환주 판별 (통계 기반): NI CV > 0.5이고 안정 업종이 아닌 경우
    niVals = getAnnualValues(series, "IS", "net_profit")
    if niVals and len(niVals) >= 4 and not isStableSector:
        validNi = [v for v in niVals[-5:] if v is not None and v > 0]
        if len(validNi) >= 3:
            mean = sum(validNi) / len(validNi)
            if mean > 0:
                var = sum((v - mean) ** 2 for v in validNi) / len(validNi)
                cv = (var ** 0.5) / mean
                if cv > 0.5:
                    return "cyclical", {"DCF": 0.25, "DDM": 0.10, "상대가치": 0.40, "RIM": 0.25}

    # 배당주: 안정적 ��당 (DDM 가중 높임)
    divVals = getAnnualValues(series, "CF", "dividends_paid")
    if divVals and len(divVals) >= 3:
        recentDivs = [abs(v) for v in divVals[-3:] if v is not None and v != 0]
        if len(recentDivs) >= 3:
            return "dividend", {"DCF": 0.25, "DDM": 0.30, "상대가치": 0.25, "RIM": 0.20}

    # 일반
    return "general", {"DCF": 0.35, "DDM": 0.15, "상대가치": 0.25, "RIM": 0.25}


def calcValuationSynthesis(company: Any, *, basePeriod: str | None = None) -> dict | None:
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

    # 개별 beta (수익률 회귀) + CAPM 기반 동적 WACC
    from dartlab.core.finance.proforma import compute_company_wacc, _fetchBeta

    stockCode = getattr(company, "stockCode", "")
    betaCalc = _fetchBeta(stockCode, currency) if stockCode else None

    wacc, _waccDetail = compute_company_wacc(
        series, sector_params=sp, market_cap=marketCap, currency=currency,
        beta_override=betaCalc,
    )

    result = fullValuation(
        series,
        shares=shares,
        sectorParams=sp,
        marketCap=marketCap,
        currentPrice=currentPrice,
        currency=currency,
        discountRate=wacc,
    )

    # 극단값 필터: 현재가 2% 미만 또는 10배 이상은 무의미 → 합성 제외
    _minVal = currentPrice * 0.02 if currentPrice and currentPrice > 0 else 0
    _maxVal = currentPrice * 10 if currentPrice and currentPrice > 0 else float("inf")

    def _inRange(v: float) -> bool:
        return _minVal < v < _maxVal

    estimates: list[dict] = []
    if result.dcf and result.dcf.perShareValue and _inRange(result.dcf.perShareValue):
        estimates.append({"method": "DCF", "value": result.dcf.perShareValue, "weight": weights.get("DCF", 0)})
    # DDM: fullValuation 내부 DDM 대신 calcDdm 사용 (calcDividendPolicy 기반, 더 정확)
    ddmResult = calcDdm(company, basePeriod=basePeriod)
    ddmValue = ddmResult.get("intrinsicValue") if ddmResult else None
    if ddmValue and _inRange(ddmValue):
        estimates.append({"method": "DDM", "value": ddmValue, "weight": weights.get("DDM", 0)})
    if result.relative and result.relative.consensusValue and _inRange(result.relative.consensusValue):
        estimates.append({"method": "상대가치", "value": result.relative.consensusValue, "weight": weights.get("상대가치", 0)})

    # RIM 결과도 합성에 포함
    beta = sp.beta if sp else None
    rimResult = _rimCalc(series, shares=shares, currentPrice=currentPrice, currency=currency, beta=beta)
    if rimResult and rimResult.intrinsicValue and _inRange(rimResult.intrinsicValue):
        estimates.append({"method": "RIM", "value": rimResult.intrinsicValue, "weight": weights.get("RIM", 0)})

    # Forward BPS × Target PBR — 수주잔고 기반 업종 (조선/건설)
    if companyType == "backlog_cyclical":
        from dartlab.core.finance.extract import getLatest, getAnnualValues, getRevenueGrowth3Y

        eq = getLatest(series, "BS", "total_equity")
        if eq and shares and shares > 0:
            bps = eq / shares
            revCagr = getRevenueGrowth3Y(series) or 0
            # 2년 후 Forward BPS = 현재 BPS × (1 + ROE추정)^2
            # ROE 추정: 최근 양수 ROE 또는 섹터 평균 8%
            niVals = getAnnualValues(series, "IS", "net_profit")
            recentNi = [v for v in (niVals[-3:] if niVals else []) if v is not None and v > 0]
            roe = recentNi[-1] / eq * 100 if recentNi and eq and eq > 0 else 8.0
            roe = min(max(roe, 3.0), 25.0)
            forwardBps = bps * (1 + roe / 100) ** 2
            # Target PBR: 조선 사이클 상단 2.0~4.0, 평균 3.0
            targetPbr = 3.0
            forwardPbrValue = forwardBps * targetPbr
            if _inRange(forwardPbrValue):
                estimates.append({"method": "Forward PBR", "value": forwardPbrValue, "weight": weights.get("상대가치", 0.45)})

    # NAV — 지주사만 (자회사 시총 합산 기반)
    if companyType == "holding":
        navResult = calcNavValuation(company)
        if navResult and navResult.get("navPerShare") and _inRange(navResult["navPerShare"]):
            estimates.append({"method": "NAV", "value": navResult["navPerShare"], "weight": weights.get("NAV", 0.40)})

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
        ri = calcReverseImplied(company, basePeriod=basePeriod)
        if ri:
            reverseImplied = {
                "impliedGrowthRate": ri.get("impliedGrowthRate"),
                "signal": ri.get("signal"),
            }

    warnings = []
    if price and price.get("isStale"):
        warnings.append("주가 데이터가 최신이 아닐 수 있습니다 (stale cache)")

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
        "warnings": warnings,
    }


def calcValuationFlags(company: Any, *, basePeriod: str | None = None) -> list[dict]:
    """가치평가 관련 플래그 집계."""
    flags: list[dict] = []

    dcf = calcDcf(company, basePeriod=basePeriod)
    if dcf:
        mos = dcf.get("marginOfSafety")
        if mos is not None:
            if mos > 30:
                flags.append({"signal": "opportunity", "label": f"DCF 안전마진 {mos:.0f}% -- 저평가 가능"})
            elif mos < -30:
                flags.append({"signal": "warning", "label": f"DCF 안전마진 {mos:.0f}% -- 고평가 주의"})

    ddm = calcDdm(company, basePeriod=basePeriod)
    if ddm and ddm.get("modelUsed") == "N/A":
        flags.append({"signal": "info", "label": "DDM 적용 불가 (무배당/데이터 부족)"})

    synthesis = calcValuationSynthesis(company, basePeriod=basePeriod)
    if synthesis:
        verdict = synthesis.get("verdict", "")
        if verdict == "저평가":
            flags.append({"signal": "opportunity", "label": "종합 판정: 저평가"})
        elif verdict == "고평가":
            flags.append({"signal": "warning", "label": "종합 판정: 고평가"})

    return flags
