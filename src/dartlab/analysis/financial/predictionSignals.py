"""6-2 예측신호 -- 이 회사의 실적은 어디로 향하는가.

다중 소스 예측 신호를 구조화된 데이터로 제공한다.
forecast 엔진(점 추정)과 달리, 방향성과 신뢰도에 집중한다.

학술 근거:
- Sloan 1996: 현금흐름 구성요소가 발생액보다 지속성 높음
- Cao & You 2024 (G&D Award): 횡단면 재무비율 → ML 이익 예측
- M Competition: 단순 앙상블이 복잡한 가중치를 이김
- M6: 방향 정확도가 점 정확도보다 투자에 유의미
"""

from __future__ import annotations

import logging
import math

log = logging.getLogger(__name__)

_MAX_YEARS = 8

# ── 매크로 지표 매핑 (섹터별 관련 지표) ──

_SECTOR_MACRO_MAP: dict[str, list[dict]] = {
    "high": [
        {"indicator": "BASE_RATE", "source": "ECOS", "direction": "inverse", "description": "기준금리 → 설비투자 위축"},
        {"indicator": "KRW_USD", "source": "ECOS", "direction": "mixed", "description": "원/달러 환율 → 수출 영향"},
        {"indicator": "PMI", "source": "FRED", "direction": "positive", "description": "제조업 PMI → 수주 선행"},
    ],
    "moderate": [
        {"indicator": "BASE_RATE", "source": "ECOS", "direction": "inverse", "description": "기준금리 → 소비 영향"},
        {"indicator": "CPI", "source": "ECOS", "direction": "negative", "description": "소비자물가 → 비용 압박"},
    ],
    "defensive": [
        {"indicator": "CPI", "source": "ECOS", "direction": "negative", "description": "물가 → 비용 전가 여부"},
    ],
    "low": [
        {"indicator": "BASE_RATE", "source": "ECOS", "direction": "weak_inverse", "description": "금리 → 간접 영향"},
    ],
}

_RATE_SENSITIVE_SECTORS = {"금융/은행", "금융/보험", "금융/증권", "Financials", "Real Estate", "부동산"}
_FX_SENSITIVE_SECTORS = {"반도체", "자동차", "디스플레이", "Semiconductors", "Technology"}
_COMMODITY_SECTORS = {"화학", "철강", "에너지/자원", "Energy", "Materials"}


# ── 공통 헬퍼 ──


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.financial._helpers import toDict

    return toDict(selectResult)


def _annualCols(periods: list[str], maxYears: int = _MAX_YEARS, *, basePeriod: str | None = None) -> list[str]:
    from dartlab.analysis.financial._helpers import annualColsFromPeriods

    return annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=maxYears)


def _get(row: dict, col: str) -> float:
    v = row.get(col) if row else None
    return v if v is not None else 0


def _safe(num: float, den: float) -> float | None:
    if den is None or den == 0:
        return None
    return num / den


def _getStockCode(company) -> str | None:
    return getattr(company, "stockCode", None)


def _getSectorKey(company) -> str | None:
    """업종 키 추출 (scenario.py와 동일 경로)."""
    try:
        from dartlab.analysis.financial.valuation import _IG_TO_SECTOR_KEY

        sectorInfo = company.sector
        if sectorInfo is not None:
            igName = sectorInfo.industryGroup.name
            return _IG_TO_SECTOR_KEY.get(igName)
    except (AttributeError, ValueError, ImportError):
        pass
    return None


# ══════════════════════════════════════
# calc 1: 이익 모멘텀/지속성
# ══════════════════════════════════════


def calcEarningsMomentum(company, *, basePeriod: str | None = None) -> dict | None:
    """이익 모멘텀 — Sloan 분해(현금 vs 발생액) + DuPont 추세.

    이익이 가속/감속 중인지, 현금 뒷받침이 있는지를 판단한다.
    """
    isResult = company.select("IS", ["당기순이익", "매출액", "영업이익"])
    cfResult = company.select("CF", ["영업활동현금흐름"])
    bsResult = company.select("BS", ["자산총계", "자본총계"])

    isParsed = _toDict(isResult)
    cfParsed = _toDict(cfResult)
    bsParsed = _toDict(bsResult)
    if isParsed is None or cfParsed is None or bsParsed is None:
        return None

    isData, _ = isParsed
    cfData, cfPeriods = cfParsed
    bsData, _ = bsParsed

    niRow = isData.get("당기순이익", {})
    revRow = isData.get("매출액", {})
    oiRow = isData.get("영업이익", {})
    ocfRow = cfData.get("영업활동현금흐름", {})
    taRow = bsData.get("자산총계", {})
    teRow = bsData.get("자본총계", {})

    yCols = _annualCols(cfPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if len(yCols) < 3:
        return None

    # Sloan 분해 시계열
    history = []
    for col in yCols:
        ni = _get(niRow, col)
        ocf = _get(ocfRow, col)
        ta = _get(taRow, col)
        rev = _get(revRow, col)
        oi = _get(oiRow, col)
        te = _get(teRow, col)
        accrual = ni - ocf

        margin = _safe(oi, rev) if rev != 0 else None
        turnover = _safe(rev, ta) if ta != 0 else None
        leverage = _safe(ta, te) if te != 0 else None

        history.append({
            "period": col,
            "netIncome": ni,
            "ocf": ocf,
            "accrual": accrual,
            "sloanAccrualRatio": _safe(accrual, ta) if ta > 0 else None,
            "ocfToNi": _safe(ocf, ni) if ni != 0 else None,
            "margin": margin,
            "turnover": turnover,
            "leverage": leverage,
        })

    if len(history) < 3:
        return None

    # 이익 방향성 판단 (최근 3년 추세)
    recentNi = [h["netIncome"] for h in history[:3]]
    niChanges = [recentNi[i] - recentNi[i + 1] for i in range(len(recentNi) - 1)]

    if all(d > 0 for d in niChanges):
        momentum = "accelerating"
        direction = "up"
    elif all(d < 0 for d in niChanges):
        momentum = "decelerating"
        direction = "down"
    elif len(niChanges) >= 2 and niChanges[0] > 0 and niChanges[1] < 0:
        momentum = "reversing"
        direction = "up"
    elif len(niChanges) >= 2 and niChanges[0] < 0 and niChanges[1] > 0:
        momentum = "reversing"
        direction = "down"
    else:
        momentum = "stable"
        direction = "flat"

    # 현금 지속성 점수 (OCF/NI 비율 기반)
    ocfToNiVals = [h["ocfToNi"] for h in history[:5] if h["ocfToNi"] is not None]
    if ocfToNiVals:
        avgOcfToNi = sum(ocfToNiVals) / len(ocfToNiVals)
        if avgOcfToNi >= 1.0:
            persistenceScore = min(90, 50 + avgOcfToNi * 20)
        elif avgOcfToNi >= 0.5:
            persistenceScore = 30 + avgOcfToNi * 40
        else:
            persistenceScore = max(10, avgOcfToNi * 60)
    else:
        persistenceScore = 50

    # 발생액 비율 기반 경고
    recentAccrual = [h["sloanAccrualRatio"] for h in history[:3] if h["sloanAccrualRatio"] is not None]
    highAccrual = any(abs(a) > 0.10 for a in recentAccrual) if recentAccrual else False

    # 신뢰도
    nYears = len(history)
    if nYears >= 5 and not highAccrual:
        confidence = "high"
    elif nYears >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "history": history,
        "momentum": momentum,
        "earningsDirection": direction,
        "persistenceScore": round(persistenceScore, 1),
        "highAccrualWarning": highAccrual,
        "confidence": confidence,
    }


# ══════════════════════════════════════
# calc 2: 횡단면 피어 예측
# ══════════════════════════════════════


def calcPeerPrediction(company, *, basePeriod: str | None = None) -> dict | None:
    """횡단면 피어 예측 — scan 데이터 기반 cross-section 회귀.

    사전 적합된 횡단면/패널 모델로 이 회사의 매출 성장률을 예측하고,
    실제 성장률과의 괴리를 측정한다.
    """
    stockCode = _getStockCode(company)
    if stockCode is None:
        return None

    # 횡단면 모델 로드 시도
    try:
        from dartlab.analysis.valuation.crossRegression import loadModel, loadPanelModel, FEATURES

        csModel = loadModel()
        panelModel = loadPanelModel()
    except (ImportError, FileNotFoundError, OSError):
        csModel = None
        panelModel = None

    if csModel is None and panelModel is None:
        return None

    # 이 회사 피처 추출 (scan ratio에서)
    features = _extractPeerFeatures(company)
    if features is None:
        return None

    sectorKey = _getSectorKey(company) or ""

    # 횡단면 예측
    csPredicted = None
    csR2 = None
    if csModel is not None:
        csPredicted = csModel.predict(features, sectorKey)
        csR2 = csModel.rSquared

    # 패널 예측
    panelPredicted = None
    if panelModel is not None:
        panelPredicted = panelModel.predict(stockCode, features)

    # 앙상블 (단순 평균 — 학술적 최적)
    preds = [p for p in [csPredicted, panelPredicted] if p is not None]
    if not preds:
        return None

    ensemblePredicted = sum(preds) / len(preds)

    # 실제 매출 성장률
    historicalGrowth = _getHistoricalRevenueGrowth(company, basePeriod=basePeriod)

    divergence = None
    if historicalGrowth is not None:
        divergence = ensemblePredicted - historicalGrowth

    return {
        "crossSectionPredicted": round(csPredicted, 2) if csPredicted is not None else None,
        "panelPredicted": round(panelPredicted, 2) if panelPredicted is not None else None,
        "ensemblePredicted": round(ensemblePredicted, 2),
        "companyHistoricalGrowth": round(historicalGrowth, 2) if historicalGrowth is not None else None,
        "divergence": round(divergence, 2) if divergence is not None else None,
        "modelR2": round(csR2, 3) if csR2 is not None else None,
    }


def _extractPeerFeatures(company) -> dict[str, float] | None:
    """company에서 횡단면 회귀 피처를 추출."""
    features: dict[str, float] = {}

    try:
        ratios = company.finance.ratios
        if ratios is None:
            return None

        per = getattr(ratios, "per", None)
        pbr = getattr(ratios, "pbr", None)
        opMargin = getattr(ratios, "operatingMargin", None)
        debtRatio = getattr(ratios, "debtRatio", None)

        if per is not None:
            features["per"] = per
        if pbr is not None:
            features["pbr"] = pbr
        if opMargin is not None:
            features["operatingMargin"] = opMargin
        if debtRatio is not None:
            features["debtRatio"] = debtRatio

        # lnMarketCap
        profile = getattr(company, "profile", None)
        if profile:
            mc = getattr(profile, "marketCap", None)
            if mc and mc > 0:
                features["lnMarketCap"] = math.log(mc)

        # capexRatio, foreignHoldingRatio, revenueGrowthLag — 없으면 기본값
        features.setdefault("capexRatio", 0.0)
        features.setdefault("foreignHoldingRatio", 0.0)
        features.setdefault("revenueGrowthLag", 0.0)

    except (AttributeError, TypeError, ValueError):
        return None

    # 최소 4개 피처 있어야 유의미
    if len(features) < 4:
        return None

    return features


def _getHistoricalRevenueGrowth(company, *, basePeriod: str | None = None) -> float | None:
    """최근 매출 성장률 (%) 계산."""
    isResult = company.select("IS", ["매출액"])
    parsed = _toDict(isResult)
    if parsed is None:
        return None
    data, periods = parsed
    revRow = data.get("매출액", {})
    yCols = _annualCols(periods, 3, basePeriod=basePeriod)
    if len(yCols) < 2:
        return None
    cur = _get(revRow, yCols[0])
    prev = _get(revRow, yCols[1])
    if prev == 0:
        return None
    return ((cur - prev) / abs(prev)) * 100


# ══════════════════════════════════════
# calc 3: 구조변화 감지
# ══════════════════════════════════════


def calcStructuralBreak(company, *, basePeriod: str | None = None) -> dict | None:
    """구조변화 감지 — 매출/영업이익/마진/ROE 4대 지표.

    Chow Test 기반 구조적 변화점을 감지하여 추세 추정의 신뢰도를 판단한다.
    """
    from dartlab.core.finance.ols import detectStructuralBreak, ols

    isResult = company.select("IS", ["매출액", "영업이익"])
    isParsed = _toDict(isResult)
    if isParsed is None:
        return None
    isData, isPeriods = isParsed

    revRow = isData.get("매출액", {})
    oiRow = isData.get("영업이익", {})
    yCols = _annualCols(isPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if len(yCols) < 6:
        return None

    # ROE 시계열 (ratioSeries에서)
    roeVals = _getRatioValues(company, "roe", len(yCols))

    # 4대 지표 시계열 (오래된 → 최신 순서로 뒤집기)
    metrics = []

    revVals = [_get(revRow, c) for c in reversed(yCols)]
    oiVals = [_get(oiRow, c) for c in reversed(yCols)]
    marginVals = [_safe(oi, rev) * 100 if rev != 0 and _safe(oi, rev) is not None else None
                  for rev, oi in zip(revVals, oiVals)]

    for name, vals in [("revenue", revVals), ("operatingIncome", oiVals),
                       ("operatingMargin", marginVals), ("roe", roeVals)]:
        clean = [v for v in vals if v is not None]
        if len(clean) < 6:
            metrics.append({
                "name": name,
                "hasBreak": False,
                "breakYear": None,
                "preBreakGrowth": None,
                "postBreakGrowth": None,
                "trendReliability": "low",
                "nObservations": len(clean),
            })
            continue

        breakIdx = detectStructuralBreak(clean)

        if breakIdx is not None:
            # 변화점 기준 전/후 성장률
            pre = clean[:breakIdx]
            post = clean[breakIdx:]
            preGrowth = _avgGrowth(pre)
            postGrowth = _avgGrowth(post)

            # 연도 매핑 (reversed yCols 기준)
            reversedCols = list(reversed(yCols))
            breakYear = reversedCols[breakIdx] if breakIdx < len(reversedCols) else None

            metrics.append({
                "name": name,
                "hasBreak": True,
                "breakYear": breakYear,
                "preBreakGrowth": round(preGrowth, 2) if preGrowth is not None else None,
                "postBreakGrowth": round(postGrowth, 2) if postGrowth is not None else None,
                "trendReliability": "low",
                "nObservations": len(clean),
            })
        else:
            # 변화점 없음 — 추세 일관
            _, _, r2 = ols(list(range(len(clean))), clean)
            reliability = "high" if r2 > 0.7 else ("medium" if r2 > 0.4 else "low")
            metrics.append({
                "name": name,
                "hasBreak": False,
                "breakYear": None,
                "preBreakGrowth": None,
                "postBreakGrowth": None,
                "trendReliability": reliability,
                "nObservations": len(clean),
            })

    # 전체 안정성 판단
    nBreaks = sum(1 for m in metrics if m["hasBreak"])
    if nBreaks == 0:
        overallStability = "stable"
    elif nBreaks <= 1:
        overallStability = "transitioning"
    else:
        overallStability = "volatile"

    return {
        "metrics": metrics,
        "overallStability": overallStability,
    }


def _getRatioValues(company, ratioName: str, maxYears: int) -> list[float | None]:
    """ratioSeries에서 특정 비율의 시계열을 추출."""
    try:
        from dartlab.analysis.financial._helpers import getRatioSeries

        result = getRatioSeries(company)
        if result is None:
            return []
        data, years = result
        vals = data.get("RATIO", {}).get(ratioName, [])
        # 최신 maxYears개, 오래된→최신 순서로
        if len(vals) > maxYears:
            vals = vals[-maxYears:]
        return vals
    except (AttributeError, TypeError, ValueError):
        return []


def _avgGrowth(vals: list[float]) -> float | None:
    """값 목록의 평균 성장률 (%)."""
    if len(vals) < 2:
        return None
    growths = []
    for i in range(1, len(vals)):
        if vals[i - 1] != 0:
            growths.append(((vals[i] - vals[i - 1]) / abs(vals[i - 1])) * 100)
    return sum(growths) / len(growths) if growths else None


# ══════════════════════════════════════
# calc 4: 거시경제 민감도
# ══════════════════════════════════════


def calcMacroSensitivity(company, *, basePeriod: str | None = None) -> dict | None:
    """거시경제 민감도 — 섹터별 탄성치 + 관련 지표 매핑.

    라이브 매크로 데이터를 fetch하지 않는다.
    관련 지표명을 반환하여 AI가 gather.macro()로 조회할 수 있게 한다.
    """
    from dartlab.core.finance.scenario import getElasticity

    sectorKey = _getSectorKey(company)
    elasticity = getElasticity(sectorKey)

    # 민감도 분류
    fxExposure = "high" if abs(elasticity.revenueToFx) >= 0.5 else (
        "moderate" if abs(elasticity.revenueToFx) >= 0.2 else "low"
    )
    commodityExposure = "high" if sectorKey in _COMMODITY_SECTORS else "low"
    rateSensitivity = "high" if (sectorKey in _RATE_SENSITIVE_SECTORS or elasticity.nimToRate > 0) else "low"

    # 관련 지표 매핑
    drivers = _SECTOR_MACRO_MAP.get(elasticity.cyclicality, _SECTOR_MACRO_MAP["moderate"])
    primaryDrivers = drivers[:2] if len(drivers) >= 2 else drivers
    secondaryDrivers = drivers[2:] if len(drivers) > 2 else []

    # 금리 민감 섹터 추가 지표
    if rateSensitivity == "high":
        primaryDrivers = [
            {"indicator": "BASE_RATE", "source": "ECOS", "direction": "direct", "description": "기준금리 → NIM 직접 영향"},
        ] + primaryDrivers

    # FX 민감 섹터 추가 지표
    if fxExposure == "high":
        secondaryDrivers.append(
            {"indicator": "KRW_USD", "source": "ECOS", "direction": "positive_for_export", "description": "원화 약세 → 수출 유리"}
        )

    # 관련 지표명 목록 (AI가 gather.macro()로 조회할 때 사용)
    allIndicators = list({d["indicator"] for d in primaryDrivers + secondaryDrivers})

    return {
        "sectorKey": sectorKey,
        "sectorCyclicality": elasticity.cyclicality,
        "revenueToGdp": elasticity.revenueToGdp,
        "revenueToFx": elasticity.revenueToFx,
        "marginToGdp": elasticity.marginToGdp,
        "fxExposure": fxExposure,
        "commodityExposure": commodityExposure,
        "rateSensitivity": rateSensitivity,
        "primaryDrivers": primaryDrivers,
        "secondaryDrivers": secondaryDrivers,
        "relevantIndicators": allIndicators,
    }


# ══════════════════════════════════════
# calc 5: 공시 변화 신호
# ══════════════════════════════════════


def calcDisclosureDelta(company, *, basePeriod: str | None = None) -> dict | None:
    """공시 변화 신호 — diff 결과를 예측 신호로 변환.

    공시 텍스트 변화량을 방향성 신호로 해석한다.
    FinBERT 등 톤 분석은 미적용 — 변화 크기만 사용.
    """
    try:
        diffResult = company.docs.diff()
    except (AttributeError, TypeError):
        return None

    if diffResult is None:
        return None

    overallChangeRate = getattr(diffResult, "changeRate", None) or 0.0

    # 토픽별 변화율 추출
    riskChangeRate = 0.0
    businessChangeRate = 0.0
    revenueChangeRate = 0.0
    topChangedTopics = []

    riskTopics = {"riskFactors", "riskDerivative", "contingentLiabilities"}
    businessTopics = {"businessOverview", "businessContent"}
    revenueTopics = {"revenue", "salesSegment", "productionStatus"}

    topicChanges = getattr(diffResult, "topicChanges", None) or []
    for tc in topicChanges:
        topic = getattr(tc, "topic", "")
        changeRate = getattr(tc, "changeRate", 0) or 0

        if topic in riskTopics:
            riskChangeRate = max(riskChangeRate, changeRate)
        elif topic in businessTopics:
            businessChangeRate = max(businessChangeRate, changeRate)
        elif topic in revenueTopics:
            revenueChangeRate = max(revenueChangeRate, changeRate)

        if changeRate > 20:
            topChangedTopics.append({"topic": topic, "changeRate": round(changeRate, 1)})

    # 방향성 신호 판단
    if riskChangeRate > 60:
        signalDirection = "negative"
        signalStrength = "strong"
    elif riskChangeRate > 30:
        signalDirection = "negative"
        signalStrength = "moderate"
    elif overallChangeRate < 10:
        signalDirection = "neutral"
        signalStrength = "weak"
    elif businessChangeRate > 40 and riskChangeRate < 20:
        signalDirection = "positive"
        signalStrength = "moderate"
    else:
        signalDirection = "neutral"
        signalStrength = "weak"

    # 변화 큰 토픽 정렬
    topChangedTopics.sort(key=lambda x: x["changeRate"], reverse=True)

    return {
        "overallChangeRate": round(overallChangeRate, 1),
        "riskChangeRate": round(riskChangeRate, 1),
        "businessChangeRate": round(businessChangeRate, 1),
        "revenueRelatedChange": round(revenueChangeRate, 1),
        "signalDirection": signalDirection,
        "signalStrength": signalStrength,
        "topChangedTopics": topChangedTopics[:5],
    }


# ══════════════════════════════════════
# calc 6: 다중 신호 종합
# ══════════════════════════════════════


_DIRECTION_SCORES = {
    "up": 1.0, "accelerating": 1.0, "bullish": 1.0, "positive": 0.5,
    "flat": 0.0, "stable": 0.0, "neutral": 0.0,
    "down": -1.0, "decelerating": -0.5, "bearish": -1.0, "negative": -0.5,
    "reversing": 0.0, "transitioning": -0.2, "volatile": -0.5,
}


def calcPredictionSynthesis(company, *, basePeriod: str | None = None) -> dict | None:
    """다중 신호 종합 — 5개 신호의 단순 평균 앙상블.

    학술 근거: 32편 논문, 97개 비교에서 단순 평균이 최적 (Green & Armstrong 2015).
    """
    # 각 calc 독립 호출 (company._cache로 중복 방지는 호출자 레벨)
    momentum = calcEarningsMomentum(company, basePeriod=basePeriod)
    peer = calcPeerPrediction(company, basePeriod=basePeriod)
    structural = calcStructuralBreak(company, basePeriod=basePeriod)
    macro = calcMacroSensitivity(company, basePeriod=basePeriod)
    disclosure = calcDisclosureDelta(company, basePeriod=basePeriod)

    signals = {}
    scores = []

    # 1. 이익 모멘텀 신호
    if momentum is not None:
        dirKey = momentum["earningsDirection"]
        score = _DIRECTION_SCORES.get(dirKey, 0.0)
        signals["earningsMomentum"] = {
            "direction": dirKey,
            "strength": abs(score),
            "detail": momentum["momentum"],
            "persistence": momentum["persistenceScore"],
        }
        scores.append(score)

    # 2. 피어 예측 신호
    if peer is not None and peer.get("divergence") is not None:
        div = peer["divergence"]
        if div > 5:
            peerDir = "positive"
            peerScore = min(1.0, div / 20)
        elif div < -5:
            peerDir = "negative"
            peerScore = max(-1.0, div / 20)
        else:
            peerDir = "neutral"
            peerScore = 0.0
        signals["peerPrediction"] = {
            "direction": peerDir,
            "strength": abs(peerScore),
            "divergence": peer["divergence"],
        }
        scores.append(peerScore)

    # 3. 구조변화 신호
    if structural is not None:
        stabDir = structural["overallStability"]
        stabScore = _DIRECTION_SCORES.get(stabDir, 0.0)
        signals["structuralBreak"] = {
            "direction": stabDir,
            "strength": abs(stabScore),
            "nBreaks": sum(1 for m in structural["metrics"] if m["hasBreak"]),
        }
        scores.append(stabScore)

    # 4. 거시경제 신호 (방향성은 중립 — 조건부 위험 지표)
    if macro is not None:
        cyclicality = macro["sectorCyclicality"]
        macroScore = _DIRECTION_SCORES.get(cyclicality, 0.0) if cyclicality == "defensive" else 0.0
        signals["macroSensitivity"] = {
            "direction": cyclicality,
            "strength": 0.0,
            "cyclicality": cyclicality,
            "relevantIndicators": macro.get("relevantIndicators", []),
        }
        # 매크로는 방향 점수에 포함하지 않음 (조건부 지표)

    # 5. 공시 변화 신호
    if disclosure is not None:
        discDir = disclosure["signalDirection"]
        discScore = _DIRECTION_SCORES.get(discDir, 0.0)
        signals["disclosureDelta"] = {
            "direction": discDir,
            "strength": abs(discScore),
            "overallChange": disclosure["overallChangeRate"],
        }
        scores.append(discScore)

    if not scores:
        return None

    # 단순 평균 (학술적 최적)
    avgScore = sum(scores) / len(scores)

    if avgScore > 0.25:
        consensus = "bullish"
    elif avgScore < -0.25:
        consensus = "bearish"
    else:
        consensus = "neutral"

    # 신호 합의도 (표준편차 기반)
    if len(scores) >= 2:
        mean = avgScore
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = math.sqrt(variance)
        agreementScore = max(0, 1.0 - std)
    else:
        agreementScore = 0.5

    # 신뢰도
    nSignals = len(scores)
    if nSignals >= 4 and agreementScore > 0.6:
        confidence = "high"
    elif nSignals >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    # AI/forecast 엔진 소비용 요약
    keyDrivers = []
    keyRisks = []
    for name, sig in signals.items():
        if sig.get("direction") in ("up", "positive", "accelerating"):
            keyDrivers.append(name)
        elif sig.get("direction") in ("down", "negative", "decelerating", "volatile"):
            keyRisks.append(name)

    return {
        "signals": signals,
        "consensus": consensus,
        "directionScore": round(avgScore, 3),
        "agreementScore": round(agreementScore, 3),
        "confidence": confidence,
        "nSignals": nSignals,
        "aiContext": {
            "directionBias": round(avgScore, 3),
            "keyDrivers": keyDrivers,
            "keyRisks": keyRisks,
        },
    }


# ══════════════════════════════════════
# calc 7: 예측신호 플래그
# ══════════════════════════════════════


def calcPredictionFlags(company, *, basePeriod: str | None = None) -> list[tuple[str, str]] | None:
    """예측신호 경고 플래그."""
    flags = []

    # 이익 모멘텀
    momentum = calcEarningsMomentum(company, basePeriod=basePeriod)
    if momentum:
        if momentum["momentum"] == "decelerating":
            flags.append(("EARN_DECEL", "이익 감속 추세 — 최근 3년 연속 감소"))
        if momentum["highAccrualWarning"]:
            flags.append(("HIGH_ACCRUAL", "높은 발생액 비율 — 이익의 현금 뒷받침 약함"))
        if momentum["persistenceScore"] < 30:
            flags.append(("LOW_PERSIST", "낮은 이익 지속성 — OCF/NI 비율 낮음"))

    # 구조변화
    structural = calcStructuralBreak(company, basePeriod=basePeriod)
    if structural:
        if structural["overallStability"] == "volatile":
            flags.append(("STRUCT_VOLATILE", "다수 지표에서 구조변화 감지 — 추세 추정 신뢰도 낮음"))
        for m in structural["metrics"]:
            if m["hasBreak"] and m["name"] == "revenue":
                flags.append(("REV_BREAK", f"매출 구조변화 감지 ({m['breakYear']})"))

    # 공시 변화
    disclosure = calcDisclosureDelta(company, basePeriod=basePeriod)
    if disclosure:
        if disclosure["riskChangeRate"] > 60:
            flags.append(("RISK_SURGE", f"리스크 공시 급변 ({disclosure['riskChangeRate']:.0f}%)"))
        if disclosure["signalDirection"] == "negative" and disclosure["signalStrength"] == "strong":
            flags.append(("DISC_NEGATIVE", "공시 변화 부정적 신호 — 리스크 섹션 대폭 확대"))

    # 피어 괴리
    peer = calcPeerPrediction(company, basePeriod=basePeriod)
    if peer and peer.get("divergence") is not None:
        if peer["divergence"] < -15:
            flags.append(("PEER_BELOW", f"피어 대비 {peer['divergence']:+.1f}%p 하회 예측"))
        elif peer["divergence"] > 15:
            flags.append(("PEER_ABOVE", f"피어 대비 {peer['divergence']:+.1f}%p 상회 예측"))

    return flags if flags else None
