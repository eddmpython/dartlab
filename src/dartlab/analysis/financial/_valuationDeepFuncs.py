"""_valuationDeep 의 4 본체 함수 — calcPriceTarget · _classifyCompanyType · calcValuationSynthesis · calcValuationFlags."""

from __future__ import annotations

from typing import Any

from dartlab.analysis.financial._valuationDeepProxies import (
    _fetchPriceContext,
    _getSectorParams,
    _getSeriesAndShares,
    _resolveSectorKey,
    _rimCalc,
    calcDcf,
    calcDdm,
    calcNavValuation,
    calcResidualIncome,
    calcReverseImplied,
    computePriceTarget,
)
from dartlab.analysis.financial._valuationInputs import _historicalValuationBlock
from dartlab.core.memory import memoizedCalc


@memoizedCalc
def calcPriceTarget(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """확률 가중 주가 목표가 (5 시나리오 + Monte Carlo).

    Returns
    -------
    dict
        weightedTarget : float — 확률 가중 목표 주가 (원)
        percentiles : dict — 백분위별 주가 (원)
        expectedValue : float — 기대가치 (원)
        upside : float | None — 상승여력 (%)
        probabilityAboveCurrent : float — 현재가 초과 확률 (0.0-1.0)
        signal : str — 투자 신호 ("buy" | "hold" | "sell")
        confidence : str — 신뢰도 ("high" | "medium" | "low")
        scenarios : list[dict] — 시나리오별 상세 (name, probability, perShareValue(원), enterpriseValue(원))
        waccDetails : dict — WACC 상세
        warnings : list[str] — 경고 메시지
        currentPrice : float | None — 현재 주가 (원)
        currency : str — 통화 (KRW | USD)

    Capabilities:
        - 5 valuation 시나리오 (낙관/기본/보수/베어/베이스) 확률 가중 + Monte Carlo
        - 신호 (buy/hold/sell) + 확률 + waccDetails 종합

    Guide:
        analysis price target 표준 진입. confidence=high + signal=buy + |upside| > 20% 강력 매수.

    When:
        Story price target + AI 목표 주가 답변.

    How:
        5 시나리오 valuation + Monte Carlo distribution → 가중 평균 + 백분위.

    Requires:
        company 회계 + 현재 주가 + sector params.

    Raises:
        없음.

    Example:
        >>> calcPriceTarget(company)["weightedTarget"]
        80000

    See Also:
        - calcDcf / calcDdm / calcRelativeValuation : 단일 모델
        - calcValuationSynthesis : 모델 종합

    AIContext:
        "목표 주가" 답변 시 weightedTarget + signal + confidence 인용.
    """
    historicalBlock = _historicalValuationBlock(basePeriod, "priceTarget")
    if historicalBlock is not None:
        return historicalBlock

    series, shares, currency = _getSeriesAndShares(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None
    marketCap = price["marketCap"] if price else None
    sectorKey = _resolveSectorKey(company)

    result = computePriceTarget(
        series,
        sectorKey=sectorKey,
        currentPrice=currentPrice,
        shares=shares,
        marketCap=marketCap,
    )

    # 금융업 등 DCF 불가 시: 시나리오 전부 0이면 DDM/RIM으로 대체
    allZero = all(s.per_share_value == 0 for s in result.scenarios) if result.scenarios else True
    if allZero:
        ddmResult = calcDdm(company, basePeriod=basePeriod)
        rimResult = calcResidualIncome(company, basePeriod=basePeriod)
        fallbackValue = None
        if ddmResult and ddmResult.get("intrinsicValue") and ddmResult["intrinsicValue"] > 0:
            fallbackValue = ddmResult["intrinsicValue"]
        elif rimResult and rimResult.get("intrinsicValue") and rimResult["intrinsicValue"] > 0:
            fallbackValue = rimResult["intrinsicValue"]
        if fallbackValue:
            # DDM/RIM 기반 시나리오 생성 (±10%, ±20% 변동)
            from dartlab.analysis.valuation.pricetarget import ScenarioPriceTarget

            fallbackScenarios = [
                ScenarioPriceTarget("baseline", 0.55, None, 0, 0, fallbackValue, 0, 0, None),
                ScenarioPriceTarget("rate_hike", 0.20, None, 0, 0, fallbackValue * 0.9, 0, 0, None),
                ScenarioPriceTarget("china_slowdown", 0.15, None, 0, 0, fallbackValue * 0.85, 0, 0, None),
                ScenarioPriceTarget("adverse", 0.10, None, 0, 0, fallbackValue * 0.75, 0, 0, None),
            ]
            wt = sum(s.per_share_value * s.probability for s in fallbackScenarios)
            up = ((wt / currentPrice - 1) * 100) if currentPrice and currentPrice > 0 else None
            sig = "buy" if up and up > 10 else ("sell" if up and up < -10 else "hold")
            from dartlab.analysis.valuation.pricetarget import PriceTargetResult

            result = PriceTargetResult(
                scenarios=fallbackScenarios,
                weighted_target=wt,
                percentiles=result.percentiles,
                expected_value=fallbackValue,
                currentPrice=currentPrice,
                upsidePct=up,
                probability_above_current=result.probability_above_current,
                signal=sig,
                confidence="low",
                wacc_details=getattr(result, "wacc_details", {}),
                warnings=result.warnings + ["DCF 시나리오 불가 → DDM/RIM 기반 fallback"],
            )

    scenarios = []
    for s in result.scenarios:
        scenarios.append(
            {
                "name": s.scenarioName,
                "probability": s.probability,
                "perShareValue": s.per_share_value,
                "enterpriseValue": s.enterprise_value,
            }
        )

    return {
        "weightedTarget": result.weighted_target,
        "percentiles": result.percentiles,
        "expectedValue": result.expected_value,
        "upside": result.upsidePct,
        "probabilityAboveCurrent": result.probability_above_current,
        "signal": result.signal,
        "confidence": result.confidence,
        "scenarios": scenarios,
        "waccDetails": result.wacc_details,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }


def _classifyCompanyType(company: Any, series: dict) -> tuple[str, dict[str, float]]:
    """기업 특성 분류 -> 최적 모델 가중치 반환 (CFA 프레임워크 기반).

    Returns:
        (companyType, weights) where companyType is one of:
        "financial", "growth", "cyclical", "dividend", "general"
    """
    from dartlab.core.utils.extract import getAnnualValues, getRevenueGrowth3Y

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
        "SEMICONDUCTOR",
        "CHEMICAL",
        "METALS",
        "SHIPBUILDING",
        "TRANSPORTATION",
        "OIL_GAS",
        "ENERGY_EQUIP",
        "CONSTRUCTION_MATERIALS",
        "CAPITAL_GOODS",
        "AUTO",
        "DISPLAY",
        "AIRLINE",
    }
    # NI CV가 높아도 사이클 기업이 아닌 업종 → cyclical 제외
    _stableIg = {
        "TELECOM",
        "UTILITIES",
        "GAS_UTILITY",
        "ELECTRIC",
        "SOFTWARE",
        "IT_SERVICE",
        "INTERNET",
        "MEDIA_ENTERTAINMENT",
        "MEDIA",
        "GAME",
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
                cv = (var**0.5) / mean
                if cv > 0.5:
                    return "cyclical", {"DCF": 0.25, "DDM": 0.10, "상대가치": 0.40, "RIM": 0.25}

    # 배당주: 안정적 배당 (DDM 가중 높임)
    divVals = getAnnualValues(series, "CF", "dividends_paid")
    if divVals and len(divVals) >= 3:
        recentDivs = [abs(v) for v in divVals[-3:] if v is not None and v != 0]
        if len(recentDivs) >= 3:
            return "dividend", {"DCF": 0.25, "DDM": 0.30, "상대가치": 0.25, "RIM": 0.20}

    # 일반
    return "general", {"DCF": 0.35, "DDM": 0.15, "상대가치": 0.25, "RIM": 0.25}


@memoizedCalc
def calcValuationSynthesis(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """종합 밸류에이션 -- 기업 유형별 자동 모델 선택 + 가중 합성.

    Returns
    -------
    dict
        fairValueRange : dict — 적정가 범위 (원)
        verdict : str — 판정 ("저평가" | "적정" | "고평가")
        currentPrice : float | None — 현재 주가 (원)
        estimates : list[dict] — 모델별 추정 (method, value(원), weight)
        companyType : str — 기업 유형 ("financial" | "growth" | "cyclical" | "dividend" | "holding" | "general" 등)
        weightedFairValue : float | None — 가중 합성 적정가 (원)
        modelWeights : dict[str, float] — 모델별 가중치
        currency : str — 통화 (KRW | USD)
        reverseImplied : dict | None — 역내재성장률 (모델 실패 시 보충)
        warnings : list[str] — 경고 메시지
        technicalContext : dict | None — 기술적 분석 컨텍스트 (verdict, score, rsi)

    Capabilities:
        - 기업 유형 (financial/growth/cyclical 등) 자동 분류 → 모델별 가중치 → 가중 fair value
        - fairValueRange + verdict (저평가/적정/고평가)

    Guide:
        모델별 가중치는 기업 유형 따라 자동. dividend 형 = DDM 50%, growth = DCF 60%. weighted
        FairValue 대비 현재가로 verdict.

    When:
        Valuation 종합 + AI 적정가 답변.

    How:
        ``_classifyCompanyType`` → ``fullValuation`` 모델 5+ 호출 → 가중 합성.

    Requires:
        회계 시계열 + sector params + 현재 주가.

    Raises:
        없음 — 데이터 부재 시 None.

    Example:
        >>> calcValuationSynthesis(company)["verdict"]
        '저평가'

    See Also:
        - calcPriceTarget : 시나리오 기반
        - calcValuationFlags : 적정성 플래그

    AIContext:
        "이 종목 적정가" 답변 시 weightedFairValue + verdict 인용.
    """
    historicalBlock = _historicalValuationBlock(basePeriod, "valuationSynthesis")
    if historicalBlock is not None:
        return historicalBlock

    from dartlab.analysis.valuation.dcf import fullValuation

    series, shares, currency = _getSeriesAndShares(company)
    if series is None:
        return None

    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None
    marketCap = price["marketCap"] if price else None

    companyType, weights = _classifyCompanyType(company, series)

    # 개별 beta (수익률 회귀) + CAPM 기반 동적 WACC
    from dartlab.analysis.financial.proforma import _fetchBeta, computeCompanyWacc

    stockCode = getattr(company, "stockCode", "")
    betaCalc = _fetchBeta(stockCode, currency) if stockCode else None

    wacc, _waccDetail = computeCompanyWacc(
        series,
        sectorParams=sp,
        marketCap=marketCap,
        currency=currency,
        betaOverride=betaCalc,
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
        """적정가가 현재가 대비 합리적 범위(2%~10배) 내인지 검증."""
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
        estimates.append(
            {"method": "상대가치", "value": result.relative.consensusValue, "weight": weights.get("상대가치", 0)}
        )

    # RIM 결과도 합성에 포함
    beta = sp.beta if sp else None
    rimResult = _rimCalc(series, shares=shares, currentPrice=currentPrice, currency=currency, beta=beta)
    if rimResult and rimResult.intrinsicValue and _inRange(rimResult.intrinsicValue):
        estimates.append({"method": "RIM", "value": rimResult.intrinsicValue, "weight": weights.get("RIM", 0)})

    # Forward BPS × Target PBR — 수주잔고 기반 업종 (조선/건설)
    if companyType == "backlog_cyclical":
        from dartlab.core.utils.extract import getAnnualValues, getLatest, getRevenueGrowth3Y

        eq = getLatest(series, "BS", "total_equity")
        if eq and shares and shares > 0:
            bps = eq / shares
            getRevenueGrowth3Y(series) or 0
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
                estimates.append(
                    {"method": "Forward PBR", "value": forwardPbrValue, "weight": weights.get("상대가치", 0.45)}
                )

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

    # 모델 간 극단 괴리 경고
    if len(estimates) >= 2:
        vals = [e["value"] for e in estimates]
        maxVal, minVal = max(vals), min(vals)
        if minVal > 0 and maxVal / minVal > 10:
            warnings.append(f"모델 간 극단 괴리 ({maxVal / minVal:.0f}배) — 합성 신뢰도 낮음")

    # 기술적 분석 컨텍스트 — review가 주입 (analysis ↛ quant: L2↔L2 금지)
    # valuation은 순수 재무 데이터만으로 가치 산출. 기술적 컨텍스트가 필요한 경우
    # story 레이어에서 calcTechnicalVerdict 결과를 주입한다.
    technicalContext = None

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
        "technicalContext": technicalContext,
    }


@memoizedCalc
def calcValuationFlags(company: Any, *, basePeriod: str | None = None) -> list[dict]:
    """가치평가 관련 플래그 집계.

    Returns
    -------
    list[dict]
        signal : str — 신호 유형 ("opportunity" | "warning" | "info")
        label : str — 플래그 설명 메시지

    Capabilities:
        - DCF margin of safety + 상대 valuation + 다른 모델 결과 → opportunity/warning 플래그
        - 안전마진 30% 이상 = opportunity, -30% 이하 = warning

    Guide:
        story flag 박스의 valuation 영역 입력. signal == opportunity 수 ≥ 2 = 매수 후보 강함.

    When:
        Valuation 플래그 + AI 저평가/고평가 알림.

    How:
        calcDcf + calcRelativeValuation 등 호출 → 임계 비교 → 플래그 dict 누적.

    Requires:
        valuation sub-calc 가용.

    Raises:
        없음.

    Example:
        >>> calcValuationFlags(company)[0]["signal"]
        'opportunity'

    See Also:
        - calcValuationSynthesis : 가중 합성
        - calcPriceTarget : 시나리오

    AIContext:
        "valuation 경고/기회" 답변 시 signal=opportunity / warning 인용.
    """
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

        # 기술적 분석 교차 플래그
        tc = synthesis.get("technicalContext")
        if tc and verdict:
            techVerdict = tc.get("verdict", "")
            rsi = tc.get("rsi", 50)
            if verdict == "저평가" and techVerdict == "약세" and rsi <= 30:
                flags.append({"signal": "opportunity", "label": "저평가 + 과매도(RSI 30↓) — 역발상 매수 기회 가능성"})
            elif verdict == "고평가" and techVerdict == "강세" and rsi >= 70:
                flags.append({"signal": "warning", "label": "고평가 + 과매수(RSI 70↑) — 과열 경고"})
            elif verdict == "저평가" and techVerdict == "강세":
                flags.append({"signal": "opportunity", "label": "저평가 + 기술적 강세 — 시장 재평가 진행 중"})

    return flags
