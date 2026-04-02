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

from dartlab.analysis.financial._helpers import annualColsFromPeriods, toDict
from dartlab.analysis.financial._memoize import memoized_calc

log = logging.getLogger(__name__)

_MAX_YEARS = 8

# ── 업종별 모멘텀 사전확률 (walk-forward 실측, 200기업 4800건+) ──
# 베이즈 사전확률: "전분기 방향 유지"가 맞을 확률. 업종마다 다르다.
# 식품(88%) vs 반도체(66%) vs 영화(60%) — 모멘텀 지속성이 업종 특성.
_INDUSTRY_PRIOR: dict[str, float] = {
    # 85%+ (안정 성장 — 모멘텀 매우 강)
    "동·식물성 유지 및 낙농제품 제조업": 0.886,
    "금속 주조업": 0.882,
    "섬유, 의복, 신발 및 가죽제품 소매업": 0.875,
    "도로 화물 운송업": 0.871,
    # 80~85%
    "1차 비철금속 제조업": 0.829,
    "음·식료품 및 담배 도매업": 0.824,
    "컴퓨터 프로그래밍, 시스템 통합 및 관리업": 0.824,
    "생활용품 도매업": 0.815,
    "일반 교습 학원": 0.812,
    "가정용 기기 제조업": 0.809,
    "곡물가공품, 전분 및 전분제품 제조업": 0.800,
    "유리 및 유리제품 제조업": 0.800,
    # 76~80%
    "상품 종합 도매업": 0.797,
    "알코올음료 제조업": 0.795,
    "사진장비 및 광학기기 제조업": 0.794,
    "화학섬유 제조업": 0.785,
    "기초 화학물질 제조업": 0.783,
    "종합 소매업": 0.776,
    "봉제의복 제조업": 0.771,
    "구조용 금속제품, 탱크 및 증기발생기 제조업": 0.765,
    # 73~76%
    "1차 철강 제조업": 0.755,
    "건물 건설업": 0.748,
    "자동차 신품 부품 제조업": 0.747,
    "자연과학 및 공학 연구개발업": 0.740,
    "의약품 제조업": 0.734,
    "기타 금속 가공제품 제조업": 0.732,
    # 70~73%
    "전자부품 제조업": 0.719,
    "소프트웨어 개발 및 공급업": 0.716,
    "의료용 기기 제조업": 0.713,
    "기초 의약물질 제조업": 0.707,
    "기타 전문 도매업": 0.701,
    # 65~70%
    "의료용품 및 기타 의약 관련제품 제조업": 0.689,
    "전기 통신업": 0.677,
    "선박 및 보트 건조업": 0.674,
    "기타 화학제품 제조업": 0.667,
    "반도체 제조업": 0.665,
    "특수 목적용 기계 제조업": 0.653,
    # 60% 미만 (모멘텀 약 — 예측 불확실)
    "통신 및 방송 장비 제조업": 0.606,
    "영화, 비디오물, 방송프로그램 제작 및 배급업": 0.596,
    "일반 목적용 기계 제조업": 0.590,
    "전동기, 발전기 및 전기 변환 · 공급 · 제어 장치 제조업": 0.579,
}
_DEFAULT_PRIOR = 0.721  # 전체 평균

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


@memoized_calc
def calcEarningsMomentum(company, *, basePeriod: str | None = None) -> dict | None:
    """이익 모멘텀 — Sloan 분해(현금 vs 발생액) + DuPont 추세.

    이익이 가속/감속 중인지, 현금 뒷받침이 있는지를 판단한다.
    """
    isResult = company.select("IS", ["당기순이익", "매출액", "영업이익"])
    cfResult = company.select("CF", ["영업활동현금흐름"])
    bsResult = company.select("BS", ["자산총계", "자본총계"])

    isParsed = toDict(isResult)
    cfParsed = toDict(cfResult)
    bsParsed = toDict(bsResult)
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

    yCols = annualColsFromPeriods(cfPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
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

        history.append(
            {
                "period": col,
                "netIncome": ni,
                "ocf": ocf,
                "accrual": accrual,
                "sloanAccrualRatio": _safe(accrual, ta) if ta > 0 else None,
                "ocfToNi": _safe(ocf, ni) if ni != 0 else None,
                "margin": margin,
                "turnover": turnover,
                "leverage": leverage,
            }
        )

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


@memoized_calc
def calcPeerPrediction(company, *, basePeriod: str | None = None) -> dict | None:
    """횡단면 피어 예측 — scan 데이터 기반 cross-section 회귀.

    사전 적합된 횡단면/패널 모델로 이 회사의 매출 성장률을 예측하고,
    실제 성장률과의 괴리를 측정한다.
    """
    stockCode = _getStockCode(company)
    if stockCode is None:
        return None

    # 횡단면 모델 로드 시도 (최신 연도부터 탐색)
    from datetime import datetime

    try:
        from dartlab.analysis.valuation.crossRegression import loadModel, loadPanelModel

        csModel = None
        for tryYear in range(datetime.now().year - 1, datetime.now().year - 4, -1):
            csModel = loadModel(tryYear)
            if csModel is not None:
                break
        panelModel = loadPanelModel()
    except (ImportError, FileNotFoundError, OSError, TypeError):
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
    parsed = toDict(isResult)
    if parsed is None:
        return None
    data, periods = parsed
    revRow = data.get("매출액", {})
    yCols = annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=3)
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


@memoized_calc
def calcStructuralBreak(company, *, basePeriod: str | None = None) -> dict | None:
    """구조변화 감지 — 매출/영업이익/마진/ROE 4대 지표.

    Chow Test 기반 구조적 변화점을 감지하여 추세 추정의 신뢰도를 판단한다.
    """
    from dartlab.core.finance.ols import detectStructuralBreak, ols

    isResult = company.select("IS", ["매출액", "영업이익"])
    isParsed = toDict(isResult)
    if isParsed is None:
        return None
    isData, isPeriods = isParsed

    revRow = isData.get("매출액", {})
    oiRow = isData.get("영업이익", {})
    yCols = annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if len(yCols) < 6:
        return None

    # ROE 시계열 (ratioSeries에서)
    roeVals = _getRatioValues(company, "roe", len(yCols))

    # 4대 지표 시계열 (오래된 → 최신 순서로 뒤집기)
    metrics = []

    revVals = [_get(revRow, c) for c in reversed(yCols)]
    oiVals = [_get(oiRow, c) for c in reversed(yCols)]
    marginVals = [
        _safe(oi, rev) * 100 if rev != 0 and _safe(oi, rev) is not None else None for rev, oi in zip(revVals, oiVals)
    ]

    for name, vals in [
        ("revenue", revVals),
        ("operatingIncome", oiVals),
        ("operatingMargin", marginVals),
        ("roe", roeVals),
    ]:
        clean = [v for v in vals if v is not None]
        if len(clean) < 6:
            metrics.append(
                {
                    "name": name,
                    "hasBreak": False,
                    "breakYear": None,
                    "preBreakGrowth": None,
                    "postBreakGrowth": None,
                    "trendReliability": "low",
                    "nObservations": len(clean),
                }
            )
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

            metrics.append(
                {
                    "name": name,
                    "hasBreak": True,
                    "breakYear": breakYear,
                    "preBreakGrowth": round(preGrowth, 2) if preGrowth is not None else None,
                    "postBreakGrowth": round(postGrowth, 2) if postGrowth is not None else None,
                    "trendReliability": "low",
                    "nObservations": len(clean),
                }
            )
        else:
            # 변화점 없음 — 추세 일관
            _, _, r2 = ols(list(range(len(clean))), clean)
            reliability = "high" if r2 > 0.7 else ("medium" if r2 > 0.4 else "low")
            metrics.append(
                {
                    "name": name,
                    "hasBreak": False,
                    "breakYear": None,
                    "preBreakGrowth": None,
                    "postBreakGrowth": None,
                    "trendReliability": reliability,
                    "nObservations": len(clean),
                }
            )

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


@memoized_calc
def calcMacroSensitivity(company, *, basePeriod: str | None = None) -> dict | None:
    """거시경제 민감도 — 섹터별 탄성치 + 관련 지표 매핑.

    라이브 매크로 데이터를 fetch하지 않는다.
    관련 지표명을 반환하여 AI가 gather.macro()로 조회할 수 있게 한다.
    """
    from dartlab.core.finance.scenario import getElasticity

    sectorKey = _getSectorKey(company)
    elasticity = getElasticity(sectorKey)

    # 민감도 분류
    fxExposure = (
        "high" if abs(elasticity.revenueToFx) >= 0.5 else ("moderate" if abs(elasticity.revenueToFx) >= 0.2 else "low")
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
            {
                "indicator": "BASE_RATE",
                "source": "ECOS",
                "direction": "direct",
                "description": "기준금리 → NIM 직접 영향",
            },
        ] + primaryDrivers

    # FX 민감 섹터 추가 지표
    if fxExposure == "high":
        secondaryDrivers.append(
            {
                "indicator": "KRW_USD",
                "source": "ECOS",
                "direction": "positive_for_export",
                "description": "원화 약세 → 수출 유리",
            }
        )

    # 관련 지표명 목록 (AI가 gather.macro()로 조회할 때 사용)
    allIndicators = list({d["indicator"] for d in primaryDrivers + secondaryDrivers})

    result = {
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

    # Prediction Space enrichment (라이브 축 상태, 캐시 있을 때만)
    try:
        from dartlab.analysis.forecast.predictionSpace import getPredictionSpace

        space = getPredictionSpace()
        if space is not None:
            result["predictionAxes"] = {
                name: {
                    "label": ax.label,
                    "level": ax.level,
                    "direction": ax.direction,
                    "momentum": ax.momentum,
                }
                for name, ax in space.axes.items()
            }
            result["axisImpact"] = space.impactOn(sectorKey)
            result["netMacroEffect"] = round(sum(space.impactOn(sectorKey).values()), 2)
    except (ImportError, TypeError):
        pass

    return result


# ══════════════════════════════════════
# calc 4b: 거시-재무 동적 회귀
# ══════════════════════════════════════


@memoized_calc
def calcMacroRegression(company, *, basePeriod: str | None = None) -> dict | None:
    """거시-재무 동적 회귀 — 기업별 거시 베타를 과거 데이터에서 학습.

    정적 상수(scenario.py의 revenueToGdp=1.8 등) 대신,
    실제 과거 매출/마진 성장률과 거시지표 변화율 간 OLS 회귀로
    기업 고유의 동적 베타를 추정한다.

    학술 근거:
    - Fama-MacBeth 1973: 횡단면 회귀로 팩터 프리미엄 추정
    - 시간차(lag) 효과: GDP t → 매출 t+1 (경기 전달 메커니즘)

    반환:
        dict with:
        - betas: {gdp: float, rate: float, fx: float} — OLS 기울기 (기업별)
        - staticBetas: {gdp: float, rate: float, fx: float} — 정적 탄성치 (비교용)
        - lagEffects: {variable: {lag0: corr, lag1: corr}} — 시간차별 상관도
        - rSquared: float — 설명력
        - nObs: int — 관측치 수
        - confidence: str — "high"/"medium"/"low"
        - table: list[dict] — 연도별 매출 성장률 vs 거시 변화율 시계열 테이블
    """
    isResult = company.select("IS", ["매출액", "영업이익"])
    isParsed = toDict(isResult)
    if isParsed is None:
        return None
    isData, isPeriods = isParsed
    revRow = isData.get("매출액", {})
    oiRow = isData.get("영업이익", {})

    # 분기 YoY 기반: 동일 분기 대비 성장률 (관측치 ~36개)
    qCols = sorted([p for p in isPeriods if "Q" in p], reverse=True)
    yoyCols: list[str] = []
    revGrowth: list[float | None] = []
    marginChange: list[float | None] = []

    for col in qCols:
        prevCol = f"{int(col[:4]) - 1}{col[-2:]}"
        if prevCol not in isPeriods:
            continue
        cur = _get(revRow, col) or None
        prev = _get(revRow, prevCol) or None
        if cur is not None and prev is not None and prev != 0:
            revGrowth.append((cur - prev) / abs(prev) * 100)
        else:
            revGrowth.append(None)

        curOi = _get(oiRow, col) or None
        prevOi = _get(oiRow, prevCol) or None
        curMargin = curOi / cur * 100 if cur and curOi and cur != 0 else None
        prevMargin = prevOi / prev * 100 if prev and prevOi and prev != 0 else None
        if curMargin is not None and prevMargin is not None:
            marginChange.append(curMargin - prevMargin)
        else:
            marginChange.append(None)

        yoyCols.append(col)

    cols = yoyCols
    if len(cols) < 6:
        return None

    # 적응형 변수 선택: 매핑 후보 + 범용 후보에서 상관도 기반 최적 3개
    stockCode = _getStockCode(company)
    macroData = _loadAdaptive(revGrowth, cols, stockCode=stockCode)
    if macroData is None:
        return None

    # OLS 회귀
    betas, rSquared, nObs = _fitOLS(revGrowth, macroData, cols)
    if betas is None:
        return None

    # 시간차(lag) 상관도 계산
    lagEffects = _calcLagCorrelation(revGrowth, macroData, cols)

    # 마진 회귀 (금리 → 마진 변화)
    marginBetas, marginR2, _ = _fitOLS(marginChange, macroData, cols)

    # 정적 탄성치 비교
    from dartlab.core.finance.scenario import getElasticity

    sectorKey = _getSectorKey(company)
    staticEl = getElasticity(sectorKey)

    confidence = "high" if nObs >= 8 and rSquared > 0.3 else ("medium" if nObs >= 5 else "low")

    # 테이블 (연도별 시계열)
    table = _buildMacroTable(cols, revGrowth, marginChange, macroData)

    # 사용된 지표 정보
    usedIndicators = macroData.get("_usedIndicators", {}) if isinstance(macroData.get("_usedIndicators"), dict) else {}

    return {
        "betas": betas,
        "staticBetas": {
            "gdp": staticEl.revenueToGdp,
            "rate": staticEl.marginToGdp,
            "fx": staticEl.revenueToFx,
        },
        "usedIndicators": usedIndicators,
        "marginBetas": marginBetas,
        "lagEffects": lagEffects,
        "rSquared": round(rSquared, 4),
        "marginR2": round(marginR2, 4) if marginR2 is not None else None,
        "nObs": nObs,
        "nVars": len(betas) if betas else 0,
        "degreesOfFreedom": nObs - len(betas) - 1 if betas else 0,
        "confidence": confidence,
        "sectorKey": sectorKey,
        "table": table,
        "_predictedDirection": _predictDirection(betas, macroData),
    }


def _predictDirection(betas: dict | None, macroData: dict) -> str | None:
    """OLS 베타 × 최신 외생변수 변화율 → 예측 방향."""
    if not betas:
        return None
    # macroData의 첫 번째 값(최신)을 사용
    predicted = 0.0
    for key, beta in betas.items():
        vals = macroData.get(key)
        if isinstance(vals, list) and vals and vals[0] is not None:
            predicted += beta * vals[0]
    return "up" if predicted > 0 else "down"


def _getFinanceSeries(company):
    """Company에서 finance series dict 추출."""
    try:
        return company.finance._series if hasattr(company.finance, "_series") else None
    except (AttributeError, TypeError):
        return None


def _loadAdaptive(
    revGrowth: list[float | None],
    periodCols: list[str],
    stockCode: str | None = None,
) -> dict[str, list[float | None]] | None:
    """적응형 변수 선택 — 매핑 후보 + 범용 후보에서 상관도 기반 최적 3개.

    1. exogenousAxes 매핑 3개 + 범용 후보 5개 = 총 8개 로드
    2. 각 변수와 revGrowth의 상관도 계산
    3. 상관도 상위 3개 선택
    """
    from dartlab.gather.macro import alignToFinancialPeriods, loadMacroParquet

    # 매핑 후보
    try:
        from dartlab.core.finance.exogenousAxes import getExogenousSeriesIds

        mapped = getExogenousSeriesIds(stockCode=stockCode)
    except (ImportError, KeyError):
        mapped = [("IPI", "ecos"), ("BASE_RATE", "ecos"), ("USDKRW", "ecos")]

    # 범용 후보 (전 시장에서 빈출 + 한국 PPI)
    universal = [
        ("PPI_MFG", "ecos"),  # 한국 공산품PPI — 가장 직접적 범용
        ("PCUOMFGOMFG", "fred"),  # 미국 제조업PPI
        ("EXPORT", "ecos"),  # 한국 수출
        ("PCOPPUSDM", "fred"),  # 구리 (글로벌 수요)
        ("INDPRO", "fred"),  # 미국 산업생산
        ("TCU", "fred"),  # 설비가동률
        ("DGORDER", "fred"),  # 내구재 주문
    ]

    # 중복 제거하며 합치기
    seen: set[str] = set()
    candidates: list[tuple[str, str]] = []
    for sid, src in mapped + universal:
        if sid not in seen:
            seen.add(sid)
            candidates.append((sid, src))

    # 전년동기 기간 생성
    prevCols = [f"{int(c[:4]) - 1}{c[4:]}" for c in periodCols]
    isRateVar = {"BASE_RATE", "BAMLH0A0HYM2", "CORP_BOND_3Y"}

    # 모든 후보 로드 + YoY 계산 + 상관도
    candidateData: list[tuple[str, str, list[float | None], float]] = []

    for sid, source in candidates:
        df = loadMacroParquet(sid, source=source)
        if df is None or df.is_empty():
            continue
        curVals = alignToFinancialPeriods(df, periodCols).get_column("value").to_list()
        prevVals = alignToFinancialPeriods(df, prevCols).get_column("value").to_list()

        changes: list[float | None] = []
        for cur, prev in zip(curVals, prevVals):
            if cur is not None and prev is not None and prev != 0:
                changes.append(cur - prev if sid in isRateVar else (cur - prev) / abs(prev) * 100)
            else:
                changes.append(None)

        # 상관도 계산
        corr = _quickCorr(revGrowth, changes)
        candidateData.append((sid, source, changes, abs(corr) if corr is not None else 0))

    if not candidateData:
        return None

    # 상관도 상위 3개 선택
    candidateData.sort(key=lambda x: x[3], reverse=True)
    selected = candidateData[:3]

    result: dict[str, list[float | None]] = {}
    usedIndicators: dict[str, str] = {}

    for i, (sid, source, changes, corr) in enumerate(selected):
        key = f"v{i}"
        result[key] = changes
        usedIndicators[key] = sid

    result["_usedIndicators"] = usedIndicators  # type: ignore[assignment]
    return result


def _quickCorr(y: list[float | None], x: list[float | None]) -> float | None:
    """빠른 피어슨 상관계수."""
    pairs = [(a, b) for a, b in zip(y, x) if a is not None and b is not None]
    if len(pairs) < 5:
        return None
    ys = [p[0] for p in pairs]
    xs = [p[1] for p in pairs]
    ym = sum(ys) / len(ys)
    xm = sum(xs) / len(xs)
    cov = sum((a - ym) * (b - xm) for a, b in pairs) / len(pairs)
    ystd = math.sqrt(sum((a - ym) ** 2 for a in ys) / len(ys))
    xstd = math.sqrt(sum((b - xm) ** 2 for b in xs) / len(xs))
    if ystd < 1e-12 or xstd < 1e-12:
        return None
    return cov / (ystd * xstd)


def _loadMacroAligned(
    periodCols: list[str],
    stockCode: str | None = None,
) -> dict[str, list[float | None]] | None:
    """Parquet 캐시에서 거시 지표를 로드 → YoY 변화율을 직접 계산.

    periodCols가 분기("2024Q3" 등)이면 전년동기 대비 YoY,
    연간이면 전년 대비 변화율.

    Returns:
        {"v0": [yoy_change, ...], "v1": [...], "_usedIndicators": {...}}
        또는 None (데이터 없음).
    """
    from dartlab.gather.macro import alignToFinancialPeriods, loadMacroParquet

    try:
        from dartlab.core.finance.exogenousAxes import getExogenousSeriesIds

        seriesPairs = getExogenousSeriesIds(stockCode=stockCode)
    except (ImportError, KeyError):
        seriesPairs = [("IPI", "ecos"), ("BASE_RATE", "ecos"), ("USDKRW", "ecos")]

    # 전년동기 기간 생성
    prevCols = [f"{int(c[:4]) - 1}{c[4:]}" for c in periodCols]

    result: dict[str, list[float | None]] = {}
    usedIndicators: dict[str, str] = {}
    isRateVar = {"BASE_RATE", "BAMLH0A0HYM2", "CORP_BOND_3Y"}

    for i, (seriesId, source) in enumerate(seriesPairs[:3]):
        key = f"v{i}"
        df = loadMacroParquet(seriesId, source=source)
        if df is not None and not df.is_empty():
            curVals = alignToFinancialPeriods(df, periodCols).get_column("value").to_list()
            prevVals = alignToFinancialPeriods(df, prevCols).get_column("value").to_list()

            # YoY 변화율 계산
            changes: list[float | None] = []
            for cur, prev in zip(curVals, prevVals):
                if cur is not None and prev is not None and prev != 0:
                    if seriesId in isRateVar:
                        changes.append(cur - prev)  # 금리: 절대 변화 (pp)
                    else:
                        changes.append((cur - prev) / abs(prev) * 100)  # %
                else:
                    changes.append(None)
            result[key] = changes
            usedIndicators[key] = seriesId
        else:
            result[key] = [None] * len(periodCols)
            usedIndicators[key] = seriesId

    result["_usedIndicators"] = usedIndicators  # type: ignore[assignment]

    hasData = any(
        any(v is not None for v in vals)
        for k, vals in result.items()
        if k != "_usedIndicators" and isinstance(vals, list)
    )
    return result if hasData else None


def _fitOLS(
    y: list[float | None],
    macroData: dict[str, list[float | None]],
    cols: list[str],
) -> tuple[dict[str, float] | None, float | None, int]:
    """OLS 회귀 — y ~ 거시변화율 + 산업지표변화율 (가변 변수).

    macroData의 키가 회귀 변수명이 된다.
    외부 의존성 없이 순수 Python으로 구현.

    Returns:
        (betas, r_squared, n_obs) 또는 (None, None, 0).
    """
    # macroData는 이미 YoY 변화율 (또는 level). _loadMacroAligned가 변화율 반환.
    varNames = [k for k in macroData.keys() if k != "_usedIndicators" and isinstance(macroData[k], list)]
    if not varNames:
        return None, None, 0

    n = min(len(y), *(len(macroData[v]) for v in varNames))

    validY: list[float] = []
    validX: list[list[float]] = []
    activeVars: list[str] = []

    # 데이터가 있는 변수만 사용
    for v in varNames:
        if any(x is not None for x in macroData[v][:n]):
            activeVars.append(v)

    for i in range(n):
        yVal = y[i]
        if yVal is None:
            continue
        xVals = []
        skip = False
        for v in activeVars:
            val = macroData[v][i] if i < len(macroData[v]) else None
            if val is None:
                skip = True
                break
            xVals.append(val)
        if not skip:
            validY.append(yVal)
            validX.append(xVals)

    if len(validY) < 3 or not activeVars:
        return None, None, 0

    # OLS: β = (X'X)^-1 X'y (절편 포함)
    nObs = len(validY)
    k = 1 + len(activeVars)  # 절편 + 변수 수

    X = [[1.0] + row for row in validX]

    XtX = [[sum(X[r][i] * X[r][j] for r in range(nObs)) for j in range(k)] for i in range(k)]
    Xty = [sum(X[r][i] * validY[r] for r in range(nObs)) for i in range(k)]

    inv = _invertMatrix(XtX)
    if inv is None:
        return None, None, 0

    beta = [sum(inv[i][j] * Xty[j] for j in range(k)) for i in range(k)]

    # R²
    yMean = sum(validY) / nObs
    ssTot = sum((y_ - yMean) ** 2 for y_ in validY)
    yPred = [sum(X[r][j] * beta[j] for j in range(k)) for r in range(nObs)]
    ssRes = sum((validY[r] - yPred[r]) ** 2 for r in range(nObs))
    rSquared = 1 - ssRes / ssTot if ssTot > 0 else 0.0

    betas = {activeVars[i]: round(beta[i + 1], 4) for i in range(len(activeVars))}

    return betas, rSquared, nObs


def _invertMatrix(m: list[list[float]]) -> list[list[float]] | None:
    """4x4 행렬 가우스-조르단 역행렬."""
    n = len(m)
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]

    for col in range(n):
        # 피벗 선택
        maxRow = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[maxRow][col]) < 1e-12:
            return None  # 특이 행렬
        aug[col], aug[maxRow] = aug[maxRow], aug[col]

        pivot = aug[col][col]
        aug[col] = [x / pivot for x in aug[col]]

        for row in range(n):
            if row != col:
                factor = aug[row][col]
                aug[row] = [aug[row][j] - factor * aug[col][j] for j in range(2 * n)]

    return [row[n:] for row in aug]


def _calcLagCorrelation(
    y: list[float | None],
    macroData: dict[str, list[float | None]],
    cols: list[str],
) -> dict[str, dict[str, float | None]]:
    """시간차(lag) 상관도 — lag 0, 1, 2."""
    result: dict[str, dict[str, float | None]] = {}

    for key in [k for k in macroData if k != "_usedIndicators" and isinstance(macroData[k], list)]:
        vals = macroData[key]
        lagCorrs: dict[str, float | None] = {}
        # 거시 변화율
        changes = []
        for i in range(len(vals) - 1):
            cur, prev = vals[i], vals[i + 1]
            if cur is not None and prev is not None and prev != 0:
                if key == "rate":
                    changes.append(cur - prev)
                else:
                    changes.append((cur - prev) / abs(prev) * 100)
            else:
                changes.append(None)

        for lag in range(3):
            corr = _pearsonCorrelation(y, changes, lag=lag)
            lagCorrs[f"lag{lag}"] = round(corr, 4) if corr is not None else None

        result[key] = lagCorrs

    return result


def _pearsonCorrelation(
    y: list[float | None],
    x: list[float | None],
    *,
    lag: int = 0,
) -> float | None:
    """피어슨 상관계수 (lag 적용)."""
    pairs: list[tuple[float, float]] = []
    for i in range(len(y)):
        xi = i + lag
        if xi < len(x):
            yVal, xVal = y[i], x[xi]
            if yVal is not None and xVal is not None:
                pairs.append((yVal, xVal))

    if len(pairs) < 3:
        return None

    yVals = [p[0] for p in pairs]
    xVals = [p[1] for p in pairs]
    yMean = sum(yVals) / len(yVals)
    xMean = sum(xVals) / len(xVals)

    cov = sum((y_ - yMean) * (x_ - xMean) for y_, x_ in pairs) / len(pairs)
    yStd = math.sqrt(sum((y_ - yMean) ** 2 for y_ in yVals) / len(yVals))
    xStd = math.sqrt(sum((x_ - xMean) ** 2 for x_ in xVals) / len(xVals))

    if yStd < 1e-12 or xStd < 1e-12:
        return None

    return cov / (yStd * xStd)


def _buildMacroTable(
    cols: list[str],
    revGrowth: list[float | None],
    marginChange: list[float | None],
    macroData: dict[str, list[float | None]],
) -> list[dict]:
    """연도별 매출 성장률 vs 거시 변화율 시계열 테이블."""
    table = []
    n = min(len(revGrowth), len(cols) - 1)

    for i in range(n):
        row: dict = {
            "period": cols[i],
            "revGrowthPct": round(revGrowth[i], 2) if revGrowth[i] is not None else None,
            "marginChangeBps": round(marginChange[i], 1)
            if i < len(marginChange) and marginChange[i] is not None
            else None,
        }
        for key, vals in macroData.items():
            if key == "_usedIndicators" or not isinstance(vals, list):
                continue
            row[f"{key}Value"] = round(vals[i], 2) if i < len(vals) and vals[i] is not None else None
        table.append(row)

    return table


# ══════════════════════════════════════
# calc 4c: 이벤트 충격 분석
# ══════════════════════════════════════


@memoized_calc
def calcEventImpact(company, *, basePeriod: str | None = None) -> dict | None:
    """이벤트 충격 분석 — 공시 급변/지배구조 변화 시점 전후 재무 패턴.

    과거에 공시 텍스트가 급변하거나 지배구조가 변한 시점을 식별하고,
    해당 시점 전후 매출/마진 변화 패턴을 추출한다.

    반환:
        dict with:
        - events: list[dict] — 감지된 이벤트 목록
          - period: str — 이벤트 발생 기간
          - type: str — "disclosureShock" / "governanceChange" / "structuralBreak"
          - magnitude: float — 변화 크기
          - preRevGrowth: float — 이벤트 전 매출 성장률 (%)
          - postRevGrowth: float — 이벤트 후 매출 성장률 (%)
          - preMargin: float — 이벤트 전 영업마진 (%)
          - postMargin: float — 이벤트 후 영업마진 (%)
          - recoveryYears: int | None — 회복까지 걸린 기간
        - averageImpact: dict — 이벤트 유형별 평균 충격
        - resilience: str — "high"/"medium"/"low" — 기업의 충격 회복력
    """
    isResult = company.select("IS", ["매출액", "영업이익"])
    isParsed = toDict(isResult)
    if isParsed is None:
        return None
    isData, isPeriods = isParsed
    revRow = isData.get("매출액", {})
    oiRow = isData.get("영업이익", {})

    cols = annualColsFromPeriods(isPeriods, basePeriod=basePeriod)
    if len(cols) < 4:
        return None

    revValues = [_get(revRow, c) or None for c in cols]
    oiValues = [_get(oiRow, c) or None for c in cols]

    # 매출 성장률 + 마진 계산
    revGrowth = _calcGrowthRates(revValues)
    margins = _calcMargins(revValues, oiValues)

    events: list[dict] = []

    # 1. 공시 텍스트 급변 감지 (disclosureDelta 활용)
    try:
        discDelta = calcDisclosureDelta(company, basePeriod=basePeriod)
        if discDelta and discDelta.get("changeIntensity"):
            intensity = discDelta["changeIntensity"]
            if intensity.get("totalChangeBytes", 0) > 50000:
                eventIdx = 0  # 최신 기간
                events.append(
                    _buildEvent(
                        period=cols[eventIdx] if eventIdx < len(cols) else "unknown",
                        eventType="disclosureShock",
                        magnitude=intensity.get("totalChangeBytes", 0) / 10000,
                        revGrowth=revGrowth,
                        margins=margins,
                        eventIdx=eventIdx,
                    )
                )
    except (AttributeError, TypeError, KeyError):
        pass

    # 2. 구조변화점 감지 (structuralBreak 재활용)
    try:
        breakResult = calcStructuralBreak(company, basePeriod=basePeriod)
        if breakResult:
            for metric, detail in breakResult.get("metrics", {}).items():
                if detail.get("breakDetected"):
                    breakYear = detail.get("breakYear")
                    if breakYear:
                        eventIdx = _findPeriodIdx(cols, breakYear)
                        if eventIdx is not None:
                            events.append(
                                _buildEvent(
                                    period=cols[eventIdx] if eventIdx < len(cols) else str(breakYear),
                                    eventType="structuralBreak",
                                    magnitude=abs(detail.get("postBreakGrowth", 0) - detail.get("preBreakGrowth", 0)),
                                    revGrowth=revGrowth,
                                    margins=margins,
                                    eventIdx=eventIdx,
                                )
                            )
    except (AttributeError, TypeError, KeyError):
        pass

    # 3. 매출 급변 감지 (|성장률| > 30% = 충격)
    for i, g in enumerate(revGrowth):
        if g is not None and abs(g) > 30:
            events.append(
                _buildEvent(
                    period=cols[i] if i < len(cols) else "unknown",
                    eventType="revenueShock",
                    magnitude=abs(g),
                    revGrowth=revGrowth,
                    margins=margins,
                    eventIdx=i,
                )
            )

    if not events:
        return {
            "events": [],
            "averageImpact": {},
            "resilience": "high",
            "summary": "최근 5년간 유의미한 충격 이벤트 없음",
        }

    # 회복력 판단
    recoveries = [e.get("recoveryYears") for e in events if e.get("recoveryYears") is not None]
    avgRecovery = sum(recoveries) / len(recoveries) if recoveries else None
    resilience = (
        "high"
        if avgRecovery is not None and avgRecovery <= 1
        else ("low" if avgRecovery and avgRecovery >= 3 else "medium")
    )

    # 유형별 평균 충격
    typeImpacts: dict[str, list[float]] = {}
    for e in events:
        t = e["type"]
        impact = (e.get("postRevGrowth") or 0) - (e.get("preRevGrowth") or 0)
        typeImpacts.setdefault(t, []).append(impact)

    averageImpact = {t: round(sum(v) / len(v), 2) for t, v in typeImpacts.items()}

    return {
        "events": events,
        "averageImpact": averageImpact,
        "resilience": resilience,
        "avgRecoveryYears": round(avgRecovery, 1) if avgRecovery else None,
    }


def _calcGrowthRates(values: list[float | None]) -> list[float | None]:
    """연간 성장률 계산."""
    rates = []
    for i in range(len(values) - 1):
        cur, prev = values[i], values[i + 1]
        if cur is not None and prev is not None and prev != 0:
            rates.append((cur - prev) / abs(prev) * 100)
        else:
            rates.append(None)
    return rates


def _calcMargins(revValues: list, oiValues: list | None) -> list[float | None]:
    """영업마진 시계열."""
    if oiValues is None:
        return [None] * len(revValues)
    margins = []
    for r, o in zip(revValues, oiValues):
        if r is not None and o is not None and r != 0:
            margins.append(o / r * 100)
        else:
            margins.append(None)
    return margins


def _buildEvent(
    *,
    period: str,
    eventType: str,
    magnitude: float,
    revGrowth: list[float | None],
    margins: list[float | None],
    eventIdx: int,
) -> dict:
    """이벤트 전후 재무 패턴 추출."""
    preRevGrowth = revGrowth[eventIdx + 1] if eventIdx + 1 < len(revGrowth) else None
    postRevGrowth = revGrowth[eventIdx] if eventIdx < len(revGrowth) else None
    preMargin = margins[eventIdx + 1] if eventIdx + 1 < len(margins) else None
    postMargin = margins[eventIdx] if eventIdx < len(margins) else None

    # 회복 시간: 이벤트 후 성장률이 양으로 돌아오는 기간
    recoveryYears = None
    if postRevGrowth is not None and postRevGrowth < 0:
        for j in range(eventIdx - 1, -1, -1):
            if j < len(revGrowth) and revGrowth[j] is not None and revGrowth[j] > 0:
                recoveryYears = eventIdx - j
                break

    return {
        "period": period,
        "type": eventType,
        "magnitude": round(magnitude, 2),
        "preRevGrowth": round(preRevGrowth, 2) if preRevGrowth is not None else None,
        "postRevGrowth": round(postRevGrowth, 2) if postRevGrowth is not None else None,
        "preMargin": round(preMargin, 1) if preMargin is not None else None,
        "postMargin": round(postMargin, 1) if postMargin is not None else None,
        "recoveryYears": recoveryYears,
    }


def _findPeriodIdx(cols: list[str], year: int) -> int | None:
    """연도로 기간 인덱스 찾기."""
    yearStr = str(year)
    for i, col in enumerate(cols):
        if col.startswith(yearStr):
            return i
    return None


# ══════════════════════════════════════
# calc 5: 공시 변화 신호
# ══════════════════════════════════════


@memoized_calc
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
# calc 8: 재고/매출채권 괴리 신호
# ══════════════════════════════════════


@memoized_calc
def calcInventoryDivergence(company, *, basePeriod: str | None = None) -> dict | None:
    """재고/매출채권 괴리 — 수요 둔화 선행 지표.

    재고 증가율 > 매출 증가율 = 수요 둔화 (NYU Stern).
    매출채권 증가율 > 매출 증가율 = 회수 악화.
    NOA 급증 = 이익 조작 가능성 (Oler 2024).
    """
    bsResult = company.select(
        "BS", ["재고자산", "매출채권및기타채권", "매출채권", "매입채무및기타채무", "매입채무", "자산총계"]
    )
    isResult = company.select("IS", ["매출액", "매출원가"])

    bsParsed = toDict(bsResult)
    isParsed = toDict(isResult)
    if bsParsed is None or isParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    isData, _ = isParsed

    invRow = bsData.get("재고자산", {})
    arRow = bsData.get("매출채권및기타채권", bsData.get("매출채권", {}))
    apRow = bsData.get("매입채무및기타채무", bsData.get("매입채무", {}))
    taRow = bsData.get("자산총계", {})
    revRow = isData.get("매출액", {})
    cogsRow = isData.get("매출원가", {})

    yCols = annualColsFromPeriods(bsPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if len(yCols) < 3:
        return None

    history = []
    for i, col in enumerate(yCols):
        inv = _get(invRow, col)
        ar = _get(arRow, col)
        ap = _get(apRow, col)
        ta = _get(taRow, col)
        rev = _get(revRow, col)
        cogs = _get(cogsRow, col)

        # DSO / DIO
        dso = (ar / rev * 365) if rev > 0 else None
        dio = (inv / cogs * 365) if cogs > 0 else None

        # YoY 성장률
        invGrowth = None
        revGrowth = None
        arGrowth = None
        if i + 1 < len(yCols):
            prevCol = yCols[i + 1]
            prevInv = _get(invRow, prevCol)
            prevRev = _get(revRow, prevCol)
            prevAr = _get(arRow, prevCol)
            if prevInv > 0:
                invGrowth = ((inv - prevInv) / prevInv) * 100
            if prevRev > 0:
                revGrowth = ((rev - prevRev) / prevRev) * 100
            if prevAr > 0:
                arGrowth = ((ar - prevAr) / prevAr) * 100

        divergence = None
        if invGrowth is not None and revGrowth is not None:
            divergence = invGrowth - revGrowth

        arDivergence = None
        if arGrowth is not None and revGrowth is not None:
            arDivergence = arGrowth - revGrowth

        # NOA = (자산 - 현금) - (부채 - 금융부채) ≈ 자산 - 매입채무 - 현금 (간이)
        noa = ta - ap if ta > 0 else None

        history.append(
            {
                "period": col,
                "inventory": inv,
                "receivables": ar,
                "revenue": rev,
                "inventoryGrowth": round(invGrowth, 1) if invGrowth is not None else None,
                "revenueGrowth": round(revGrowth, 1) if revGrowth is not None else None,
                "divergence": round(divergence, 1) if divergence is not None else None,
                "arDivergence": round(arDivergence, 1) if arDivergence is not None else None,
                "dso": round(dso, 1) if dso is not None else None,
                "dio": round(dio, 1) if dio is not None else None,
                "noa": noa,
            }
        )

    if not history:
        return None

    # 재고 신호 판단 (최근 2년)
    recentDiv = [h["divergence"] for h in history[:2] if h["divergence"] is not None]
    if recentDiv:
        avgDiv = sum(recentDiv) / len(recentDiv)
        if avgDiv > 5:
            inventorySignal = "building"
        elif avgDiv < -5:
            inventorySignal = "liquidating"
        else:
            inventorySignal = "stable"
    else:
        inventorySignal = "stable"

    # 매출채권 신호
    recentArDiv = [h["arDivergence"] for h in history[:2] if h["arDivergence"] is not None]
    if recentArDiv:
        avgArDiv = sum(recentArDiv) / len(recentArDiv)
        if avgArDiv > 5:
            receivableSignal = "deteriorating"
        elif avgArDiv < -5:
            receivableSignal = "improving"
        else:
            receivableSignal = "stable"
    else:
        receivableSignal = "stable"

    # NOA 성장률
    noaGrowth = None
    if len(history) >= 2 and history[0]["noa"] and history[1]["noa"] and history[1]["noa"] > 0:
        noaGrowth = ((history[0]["noa"] - history[1]["noa"]) / abs(history[1]["noa"])) * 100

    # 리스크 점수 (0-100)
    riskScore = 30  # 기본
    if inventorySignal == "building":
        riskScore += 25
    if receivableSignal == "deteriorating":
        riskScore += 20
    if noaGrowth is not None and noaGrowth > 20:
        riskScore += 25
    riskScore = min(100, riskScore)

    return {
        "history": history,
        "inventorySignal": inventorySignal,
        "receivableSignal": receivableSignal,
        "noaGrowth": round(noaGrowth, 1) if noaGrowth is not None else None,
        "riskScore": riskScore,
    }


# ══════════════════════════════════════
# calc 9: 동종업계 공시 타이밍
# ══════════════════════════════════════


@memoized_calc
def calcAnnouncementTiming(company, *, basePeriod: str | None = None) -> dict | None:
    """동종업계 공시 타이밍 — 선발 기업 실적으로 후발 예측.

    같은 업종에서 이미 실적을 발표한 기업들의 성장 방향을 집계한다.
    Ramnath 2002, Thomas & Zhang 2008 — 20년+ 검증된 anomaly.
    """
    stockCode = _getStockCode(company)
    if stockCode is None:
        return None

    # 업종 정보
    sectorKey = _getSectorKey(company)
    if sectorKey is None:
        return None

    # scan growth에서 동종 업종 성장률 로드
    try:
        from dartlab.scan import Scan

        scan = Scan()
        growthResult = scan("growth")
        if growthResult is None or not hasattr(growthResult, "df"):
            return None

        df = growthResult.df
    except (ImportError, ValueError, AttributeError):
        return None

    # 업종 필터 (sector 컬럼이 있으면 사용, 없으면 전체)
    sectorCol = None
    for col in ("sector", "industry", "industryGroup", "업종"):
        if col in df.columns:
            sectorCol = col
            break

    if sectorCol:
        peerDf = df.filter(df[sectorCol] == sectorKey)
    else:
        return None

    if peerDf.height < 3:
        return None

    # 성장률 방향 집계
    growthCol = None
    for col in ("revenueGrowth", "revenueCagr3y", "growth", "매출성장률"):
        if col in peerDf.columns:
            growthCol = col
            break

    if growthCol is None:
        return None

    codeCol = "stockCode" if "stockCode" in peerDf.columns else peerDf.columns[0]
    directions = {"up": 0, "down": 0, "flat": 0}
    totalPeers = peerDf.height
    selfExcluded = False

    for row in peerDf.iter_rows(named=True):
        code = str(row.get(codeCol, ""))
        if code == stockCode:
            selfExcluded = True
            continue
        g = row.get(growthCol)
        if g is None:
            continue
        g = float(g)
        if g > 2:
            directions["up"] += 1
        elif g < -2:
            directions["down"] += 1
        else:
            directions["flat"] += 1

    reported = sum(directions.values())
    if reported < 2:
        return None

    # 피어 합의 점수 (-1.0 ~ +1.0)
    peerConsensus = (directions["up"] - directions["down"]) / reported

    # 벨웨더 신호 (다수 방향)
    maxDir = max(directions, key=directions.get)
    if directions[maxDir] / reported >= 0.6:
        bellwetherSignal = "positive" if maxDir == "up" else ("negative" if maxDir == "down" else "neutral")
    else:
        bellwetherSignal = "neutral"

    confidence = "high" if reported >= 5 else ("medium" if reported >= 3 else "low")

    return {
        "sectorKey": sectorKey,
        "sectorPeersReported": reported,
        "sectorPeersTotal": totalPeers - (1 if selfExcluded else 0),
        "reportedDirection": directions,
        "bellwetherSignal": bellwetherSignal,
        "peerConsensus": round(peerConsensus, 3),
        "confidence": confidence,
    }


# ══════════════════════════════════════
# calc 10: 공급망 모멘텀
# ══════════════════════════════════════


@memoized_calc
def calcSupplyChainSignal(company, *, basePeriod: str | None = None) -> dict | None:
    """공급망 모멘텀 — 관계사 실적이 이 회사를 선행.

    Cohen & Frazzini 2008 (J. Finance) — 고객사 실적이 공급사를 1-2분기 선행.
    DART 투자관계 + 관계사 거래에서 연결 기업을 식별하고,
    상장 관계사의 성장률로 이 회사에 대한 전파 신호를 계산.
    """
    stockCode = _getStockCode(company)
    if stockCode is None:
        return None

    # 관계사 네트워크 추출
    linkedCompanies = _getLinkedCompanies(company, stockCode)
    if not linkedCompanies:
        return None

    # 상장 관계사의 성장률 조회 (scan growth)
    growthMap = _loadGrowthMap()
    if not growthMap:
        return None

    enriched = []
    for lc in linkedCompanies:
        code = lc.get("code", "")
        growth = growthMap.get(code)
        if growth is not None:
            enriched.append(
                {
                    "code": code,
                    "name": lc.get("name", ""),
                    "relationship": lc.get("relationship", ""),
                    "revenueGrowth": round(growth, 1),
                }
            )

    if not enriched:
        return None

    # 가중 평균 모멘텀
    growths = [e["revenueGrowth"] for e in enriched]
    networkMomentum = sum(growths) / len(growths)
    # 정규화 (-1 ~ +1)
    normalizedMomentum = _clamp(networkMomentum / 30)

    # 공급망 리스크
    negCount = sum(1 for g in growths if g < -5)
    if negCount / len(growths) > 0.5:
        supplyChainRisk = "high"
    elif negCount / len(growths) > 0.25:
        supplyChainRisk = "moderate"
    else:
        supplyChainRisk = "low"

    confidence = "high" if len(enriched) >= 5 else ("medium" if len(enriched) >= 2 else "low")

    return {
        "linkedCompanies": enriched[:10],
        "networkMomentum": round(normalizedMomentum, 3),
        "nLinkedListed": len(enriched),
        "supplyChainRisk": supplyChainRisk,
        "confidence": confidence,
    }


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _getLinkedCompanies(company, stockCode: str) -> list[dict]:
    """관계사/투자회사 목록 추출."""
    linked = []

    # 1. 투자관계 (network edges에서)
    try:
        from dartlab.scan.network.edges import build_invest_edges

        investDf = build_invest_edges(stockCode)
        if investDf is not None and hasattr(investDf, "height") and investDf.height > 0:
            for row in investDf.iter_rows(named=True):
                toCode = row.get("to_code", "")
                if toCode and row.get("is_listed"):
                    linked.append(
                        {
                            "code": toCode,
                            "name": row.get("to_name", ""),
                            "relationship": "투자",
                        }
                    )
    except (ImportError, ValueError, TypeError):
        pass

    # 2. 관계사 거래 (relatedPartyTx에서)
    try:
        rpt = getattr(company, "relatedPartyTx", None)
        if rpt and hasattr(rpt, "revenueTxDf") and rpt.revenueTxDf is not None:
            for row in rpt.revenueTxDf.iter_rows(named=True):
                entity = row.get("entity", "")
                if entity and entity not in {lc["name"] for lc in linked}:
                    linked.append(
                        {
                            "code": "",
                            "name": entity,
                            "relationship": "거래",
                        }
                    )
    except (AttributeError, TypeError):
        pass

    return linked


def _loadGrowthMap() -> dict[str, float]:
    """scan growth에서 전종목 매출 성장률 맵을 로드."""
    try:
        from dartlab.scan import Scan

        scan = Scan()
        result = scan("growth")
        if result is None or not hasattr(result, "df"):
            return {}

        df = result.df
        codeCol = "stockCode" if "stockCode" in df.columns else df.columns[0]
        growthCol = None
        for col in ("revenueGrowth", "revenueCagr3y", "growth"):
            if col in df.columns:
                growthCol = col
                break
        if growthCol is None:
            return {}

        gmap = {}
        for row in df.iter_rows(named=True):
            code = str(row.get(codeCol, ""))
            g = row.get(growthCol)
            if code and g is not None:
                gmap[code] = float(g)
        return gmap
    except (ImportError, ValueError, AttributeError):
        return {}


# ══════════════════════════════════════
# calc 6: 다중 신호 종합
# ══════════════════════════════════════


_DIRECTION_SCORES = {
    "up": 1.0,
    "accelerating": 1.0,
    "bullish": 1.0,
    "positive": 0.5,
    "flat": 0.0,
    "stable": 0.0,
    "neutral": 0.0,
    "down": -1.0,
    "decelerating": -0.5,
    "bearish": -1.0,
    "negative": -0.5,
    "reversing": 0.0,
    "transitioning": -0.2,
    "volatile": -0.5,
}


# ══════════════════════════════════════
# calc 10: 컨센서스 매출 방향
# ══════════════════════════════════════


@memoized_calc
def calcConsensusDirection(company, *, basePeriod: str | None = None) -> dict | None:
    """컨센서스 매출 방향 — 애널리스트 추정 매출 vs 직전 실적.

    네이버 finance/annual에서 isConsensus="Y" 기간의 매출 추정치를 가져와서
    직전 실적 대비 성장/하락 방향을 판단한다.

    Zacks 연구: 컨센서스 방향이 실적 방향의 가장 강력한 단일 예측자 (70%).
    """
    stockCode = _getStockCode(company)
    if not stockCode:
        return None

    try:
        import httpx

        resp = httpx.get(
            f"https://m.stock.naver.com/api/stock/{stockCode}/finance/annual",
            headers={"User-Agent": "dartlab/1.0"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        fi = data.get("financeInfo", {})
        titles = fi.get("trTitleList", [])
        rows = fi.get("rowList", [])

        # 컨센서스 기간 + 직전 실적 기간 찾기
        cnsKey = None
        realKeys: list[str] = []
        for t in titles:
            if t.get("isConsensus") == "Y" and cnsKey is None:
                cnsKey = t["key"]
            elif t.get("isConsensus") == "N":
                realKeys.append(t["key"])

        if not cnsKey or not realKeys:
            return None

        lastRealKey = realKeys[-1]  # 가장 최신 실적

        # 매출 행 찾기
        for row in rows:
            if row.get("title") != "매출액":
                continue

            cnsValStr = row.get("columns", {}).get(cnsKey, {}).get("value", "")
            realValStr = row.get("columns", {}).get(lastRealKey, {}).get("value", "")
            if not cnsValStr or not realValStr:
                return None

            cnsVal = float(cnsValStr.replace(",", ""))
            realVal = float(realValStr.replace(",", ""))
            if realVal == 0:
                return None

            growthPct = (cnsVal - realVal) / abs(realVal) * 100
            direction = "up" if growthPct > 2 else ("down" if growthPct < -2 else "flat")

            return {
                "consensusRevenue": cnsVal,
                "lastActualRevenue": realVal,
                "consensusPeriod": cnsKey,
                "actualPeriod": lastRealKey,
                "expectedGrowthPct": round(growthPct, 1),
                "direction": direction,
                "confidence": "high" if abs(growthPct) > 10 else ("medium" if abs(growthPct) > 3 else "low"),
            }

    except (ImportError, ValueError, KeyError, TypeError):
        return None

    return None


# ══════════════════════════════════════
# calc 11: 수급 누적 방향
# ══════════════════════════════════════


@memoized_calc
def calcFlowDirection(company, *, basePeriod: str | None = None) -> dict | None:
    """수급 누적 방향 — 기관/외국인 순매수 분기 집계.

    최근 60거래일 기관+외국인 순매수 합계가 양이면 실적 개선 기대.
    "스마트머니는 실적을 안다" (Park et al., MDPI 2020).
    """
    stockCode = _getStockCode(company)
    if not stockCode:
        return None

    try:
        import httpx

        resp = httpx.get(
            f"https://m.stock.naver.com/api/stock/{stockCode}/integration",
            headers={"User-Agent": "dartlab/1.0"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        deals = data.get("dealTrendInfos", [])
        if not deals or len(deals) < 3:
            return None

        # 최근 60거래일 집계
        recent = deals[:60]  # integration은 ~5일, 있는 만큼 사용
        foreignNet = 0
        instNet = 0
        for d in recent:
            fq = d.get("foreignerPureBuyQuant", "0")
            oq = d.get("organPureBuyQuant", "0")
            foreignNet += int(str(fq).replace(",", "").replace("+", ""))
            instNet += int(str(oq).replace(",", "").replace("+", ""))

        smartMoney = foreignNet + instNet
        direction = "up" if smartMoney > 0 else ("down" if smartMoney < 0 else "flat")

        return {
            "foreignNet60d": foreignNet,
            "institutionNet60d": instNet,
            "smartMoneyNet": smartMoney,
            "direction": direction,
            "days": len(recent),
            "confidence": "high" if abs(smartMoney) > 1000000 else ("medium" if abs(smartMoney) > 100000 else "low"),
        }

    except (ImportError, OSError, ValueError, KeyError, TypeError):
        return None


# ══════════════════════════════════════
# calc 12: 매출 모멘텀 (전분기 방향 유지)
# ══════════════════════════════════════


@memoized_calc
def calcRevenueDirection(company, *, basePeriod: str | None = None) -> dict | None:
    """매출 방향 예측 — 모멘텀 + 영업이익률 확인 + OLS 확인.

    검증 결과:
    - 모멘텀 단독: 72.1% (4825건, 172종목)
    - 모멘텀+영업이익률>0 일치: 76.1% (76% 시점)
    - 모멘텀+OLS 일치: 77.7% (68% 시점)
    - 2연속 모멘텀: 74.7%

    방법론:
    1. 기본: 전분기 YoY 방향 유지 (72.1%)
    2. 확인1: 영업이익률 > 0이면 신뢰도 상승 (76.1%) — API 불필요
    3. 확인2: OLS 외생변수와 일치하면 추가 상승 (77.7%)
    4. 2연속 같은 방향이면 74.7%

    학술 근거: M4/M5 Competition — 단순 방법이 최강.
    """
    isResult = company.select("IS", ["매출액", "영업이익"])
    isParsed = toDict(isResult)
    if isParsed is None:
        return None
    isData, isPeriods = isParsed
    revRow = isData.get("매출액", {})
    oiRow = isData.get("영업이익", {})

    qCols = sorted([p for p in isPeriods if "Q" in p], reverse=True)

    # 최근 분기 YoY
    directions: list[dict] = []
    for col in qCols[:6]:
        prevCol = f"{int(col[:4]) - 1}{col[-2:]}"
        if prevCol not in isPeriods:
            continue
        cur = _get(revRow, col) or None
        prev = _get(revRow, prevCol) or None
        if cur is not None and prev is not None and prev != 0:
            growth = (cur - prev) / abs(prev) * 100
            directions.append({"period": col, "yoyGrowth": round(growth, 1), "positive": growth > 0})

    if not directions:
        return None

    # 모멘텀 방향 (기본 예측: 전분기 방향 유지)
    latest = directions[0]
    direction = "up" if latest["positive"] else "down"

    # 2연속 모멘텀 (74.7%)
    streak = 1
    if len(directions) >= 2 and directions[0]["positive"] == directions[1]["positive"]:
        streak = 2
    if len(directions) >= 3 and streak == 2 and directions[1]["positive"] == directions[2]["positive"]:
        streak = 3

    # 확인1: 영업이익률 > 0 (76.1% — API 불필요, 가장 빠른 확인)
    latestRev = _get(revRow, directions[0]["period"]) or None
    latestOi = _get(oiRow, directions[0]["period"]) or None
    marginPositive = None
    margin = None
    if latestRev and latestOi and latestRev != 0:
        margin = latestOi / latestRev * 100
        marginPositive = margin > 0

    marginAgree = None
    if marginPositive is not None:
        # 매출 성장(+) + 영업이익률 양(+) → 일치
        # 매출 하락(-) + 영업이익률 음(-) → 일치
        marginAgree = latest["positive"] == marginPositive

    # 확인2: OLS 외생변수
    macroReg = calcMacroRegression(company, basePeriod=basePeriod)
    olsAgree = None
    if macroReg and macroReg.get("betas"):
        olsDirection = macroReg.get("_predictedDirection")
        if olsDirection is not None:
            olsAgree = (olsDirection == "up") == latest["positive"]

    # 베이즈 사후확률 갱신 — 업종별 사전확률에서 시작
    # 슈퍼예측가 원리: 사전확률이 정확할수록 사후확률도 정확
    sectorKey = _getSectorKey(company)
    industry = None
    try:
        from dartlab.core.finance.exogenousAxes import _lookupFromKindList

        industry, _ = _lookupFromKindList(_getStockCode(company) or "")
    except (ImportError, TypeError):
        pass
    posterior = _INDUSTRY_PRIOR.get(industry or "", _DEFAULT_PRIOR)

    # 신호 1: streak (2연속 → 74.7%, 3연속 → 더 강함)
    if streak >= 3:
        posterior = _bayesUpdate(posterior, 0.78)
    elif streak >= 2:
        posterior = _bayesUpdate(posterior, 0.747)

    # 신호 2: 영업이익률 (연속 값 — 크기 반영)
    if margin is not None:
        if latest["positive"]:
            # 매출 성장 + 마진 크기에 따라 차등 갱신
            marginEvidence = min(0.85, 0.72 + margin * 0.003) if margin > 0 else max(0.55, 0.72 - abs(margin) * 0.005)
        else:
            # 매출 하락 + 마진 부정이면 하락 확신 강화
            marginEvidence = max(0.55, 0.72 - margin * 0.003) if margin < 0 else min(0.85, 0.72 + abs(margin) * 0.003)
        posterior = _bayesUpdate(posterior, marginEvidence)

    # 신호 3: OLS 외생변수 (일치/불일치)
    if olsAgree is True:
        posterior = _bayesUpdate(posterior, 0.777)
    elif olsAgree is False:
        posterior = _bayesUpdate(posterior, 0.425)  # 불일치 시 하향 (OLS가 42.5%)

    # 보정: 원시 posterior를 실측 기반으로 재보정
    # 원시 78~85% → 실측 62~73%. 선형 보정으로 과신 제거.
    calibrated = _calibrate(posterior)

    # 신뢰도 등급 (보정된 확률 기준)
    if calibrated >= 0.78:
        confidence = "very_high"
    elif calibrated >= 0.73:
        confidence = "high"
    elif calibrated >= 0.65:
        confidence = "medium"
    else:
        confidence = "low"

    # 하위호환: confirms도 유지
    confirms = sum(1 for x in [marginAgree, olsAgree, streak >= 2] if x)

    return {
        "latestPeriod": latest["period"],
        "latestYoyGrowth": latest["yoyGrowth"],
        "direction": direction,
        "streak": streak,
        "margin": round(margin, 1) if margin is not None else None,
        "marginAgree": marginAgree,
        "olsAgree": olsAgree,
        "confirms": confirms,
        "probability": round(calibrated, 3),
        "rawPosterior": round(posterior, 3),
        "industryPrior": round(_INDUSTRY_PRIOR.get(industry or "", _DEFAULT_PRIOR), 3),
        "confidence": confidence,
        "history": directions[:4],
    }


def _calibrate(rawPosterior: float) -> float:
    """원시 베이즈 확률을 실측 기반으로 재보정.

    walk-forward 564건 캘리브레이션 결과:
    - 원시 78% → 실측 62%
    - 원시 83% → 실측 73%
    - 원시 86% → 실측 88%

    선형 보간으로 과신 제거. 원시 확률이 높을수록 실측에 가깝게 보정.
    """
    # 보정: posterior를 72% 기저 방향으로 수축 (shrinkage)
    # calibrated = base + (raw - base) * shrinkage_factor
    base = 0.72  # 모멘텀 기저 정확도
    shrinkage = 0.6  # 60%만 반영
    calibrated = base + (rawPosterior - base) * shrinkage
    return max(0.50, min(0.95, calibrated))


def _bayesUpdate(prior: float, evidence: float, damping: float = 0.3) -> float:
    """베이즈 사후확률 갱신 (감쇠 적용).

    Args:
        prior: 현재 P(매출↑)
        evidence: P(매출↑ | 이 신호)
        damping: 갱신 강도 감쇠 (0~1). 1.0 = 완전 갱신, 0.3 = 30% 갱신.
            신호 간 독립성 가정 위반을 보정. 0.3이 과신 방지 + 변별력 유지의 균형.

    나이브 베이즈 + 감쇠: lr^damping
    """
    if evidence <= 0 or evidence >= 1:
        return prior
    lr = evidence / (1 - evidence)
    # 감쇠: lr의 damping 거듭제곱
    lr_damped = lr**damping
    prior_odds = prior / (1 - prior)
    posterior_odds = prior_odds * lr_damped
    return posterior_odds / (1 + posterior_odds)


@memoized_calc
def calcPredictionSynthesis(company, *, basePeriod: str | None = None) -> dict | None:
    """다중 신호 종합 — 5개 신호의 단순 평균 앙상블.

    학술 근거: 32편 논문, 97개 비교에서 단순 평균이 최적 (Green & Armstrong 2015).
    """
    # 각 calc 독립 호출 (company._cache로 중복 방지는 호출자 레벨)
    momentum = calcEarningsMomentum(company, basePeriod=basePeriod)
    peer = calcPeerPrediction(company, basePeriod=basePeriod)
    structural = calcStructuralBreak(company, basePeriod=basePeriod)
    macro = calcMacroSensitivity(company, basePeriod=basePeriod)
    macroReg = calcMacroRegression(company, basePeriod=basePeriod)
    eventImp = calcEventImpact(company, basePeriod=basePeriod)
    disclosure = calcDisclosureDelta(company, basePeriod=basePeriod)
    inventory = calcInventoryDivergence(company, basePeriod=basePeriod)
    timing = calcAnnouncementTiming(company, basePeriod=basePeriod)
    supplyChain = calcSupplyChainSignal(company, basePeriod=basePeriod)

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

    # 5b. 거시-재무 동적 회귀 신호
    if macroReg is not None and macroReg.get("rSquared", 0) > 0.1:
        # netMacroEffect가 있으면 사용, 없으면 betas에서 추정
        netEffect = macro.get("netMacroEffect", 0) if macro else 0
        macroRegScore = _clamp(netEffect / 10)  # ±10% → ±1.0
        macroRegDir = "positive" if macroRegScore > 0.15 else ("negative" if macroRegScore < -0.15 else "neutral")
        signals["macroRegression"] = {
            "direction": macroRegDir,
            "strength": abs(macroRegScore),
            "rSquared": macroReg["rSquared"],
            "confidence": macroReg["confidence"],
            "nObs": macroReg["nObs"],
        }
        scores.append(macroRegScore)

    # 5c. 이벤트 충격 신호
    if eventImp is not None:
        resilience = eventImp.get("resilience", "medium")
        nEvents = len(eventImp.get("events", []))
        if resilience == "low" and nEvents > 0:
            eventScore = -0.5
            eventDir = "negative"
        elif resilience == "high":
            eventScore = 0.2
            eventDir = "positive"
        else:
            eventScore = 0.0
            eventDir = "neutral"
        signals["eventImpact"] = {
            "direction": eventDir,
            "strength": abs(eventScore),
            "resilience": resilience,
            "nEvents": nEvents,
            "avgRecoveryYears": eventImp.get("avgRecoveryYears"),
        }
        if nEvents > 0:
            scores.append(eventScore)

    # 6. 재고/매출채권 괴리 신호
    if inventory is not None:
        risk = inventory["riskScore"]
        invScore = -(risk - 50) / 50  # 50 이하=긍정, 50 이상=부정
        invDir = "negative" if risk > 60 else ("positive" if risk < 30 else "neutral")
        signals["inventoryDivergence"] = {
            "direction": invDir,
            "strength": abs(invScore),
            "riskScore": risk,
            "inventorySignal": inventory["inventorySignal"],
            "receivableSignal": inventory["receivableSignal"],
        }
        scores.append(invScore)

    # 7. 공시 타이밍 신호
    if timing is not None:
        timingScore = timing["peerConsensus"]
        timingDir = "positive" if timingScore > 0.2 else ("negative" if timingScore < -0.2 else "neutral")
        signals["announcementTiming"] = {
            "direction": timingDir,
            "strength": abs(timingScore),
            "peerConsensus": timing["peerConsensus"],
            "bellwether": timing["bellwetherSignal"],
            "peersReported": timing["sectorPeersReported"],
        }
        scores.append(timingScore)

    # 8. 공급망 모멘텀 신호
    if supplyChain is not None:
        scScore = supplyChain["networkMomentum"]
        scDir = "positive" if scScore > 0.15 else ("negative" if scScore < -0.15 else "neutral")
        signals["supplyChain"] = {
            "direction": scDir,
            "strength": abs(scScore),
            "networkMomentum": supplyChain["networkMomentum"],
            "nLinked": supplyChain["nLinkedListed"],
            "risk": supplyChain["supplyChainRisk"],
        }
        scores.append(scScore)

    # 9. 컨센서스 매출 방향
    consensus = calcConsensusDirection(company, basePeriod=basePeriod)
    if consensus is not None:
        cnsDir = consensus["direction"]
        cnsScore = _DIRECTION_SCORES.get(cnsDir, 0.0)
        signals["consensusDirection"] = {
            "direction": cnsDir,
            "strength": abs(cnsScore),
            "expectedGrowth": consensus["expectedGrowthPct"],
            "confidence": consensus["confidence"],
        }
        scores.append(cnsScore)

    # 10. 수급 누적 방향
    flowDir = calcFlowDirection(company, basePeriod=basePeriod)
    if flowDir is not None:
        fDir = flowDir["direction"]
        fScore = _DIRECTION_SCORES.get(fDir, 0.0)
        signals["flowDirection"] = {
            "direction": fDir,
            "strength": abs(fScore),
            "smartMoneyNet": flowDir["smartMoneyNet"],
            "confidence": flowDir["confidence"],
        }
        scores.append(fScore)

    # 11. 매출 모멘텀 (전분기 방향 유지)
    revDir = calcRevenueDirection(company, basePeriod=basePeriod)
    if revDir is not None:
        rDir = revDir["direction"]
        rScore = _DIRECTION_SCORES.get(rDir, 0.0)
        signals["revenueDirection"] = {
            "direction": rDir,
            "strength": abs(rScore),
            "latestYoyGrowth": revDir["latestYoyGrowth"],
            "streak": revDir["streak"],
            "confidence": revDir["confidence"],
        }
        scores.append(rScore)

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

    # 매출 방향 예측 (모멘텀 기반 — 검증 정확도 71.3%)
    revPrediction = None
    if revDir is not None:
        revPrediction = {
            "direction": revDir["direction"],
            "confidence": revDir["confidence"],
            "streak": revDir["streak"],
            "olsAgree": revDir.get("olsAgree"),
            "expectedAccuracy": (
                77.7
                if revDir.get("olsAgree") and revDir["streak"] >= 2
                else 74.7
                if revDir["streak"] >= 2
                else 77.7
                if revDir.get("olsAgree")
                else 71.3
            ),
        }

    return {
        "signals": signals,
        "consensus": consensus,
        "directionScore": round(avgScore, 3),
        "agreementScore": round(agreementScore, 3),
        "confidence": confidence,
        "nSignals": nSignals,
        "revenuePrediction": revPrediction,
        "aiContext": {
            "directionBias": round(avgScore, 3),
            "keyDrivers": keyDrivers,
            "keyRisks": keyRisks,
        },
    }


# ══════════════════════════════════════
# calc 7: 예측신호 플래그
# ══════════════════════════════════════


@memoized_calc
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

    # 거시-재무 회귀
    macroReg = calcMacroRegression(company, basePeriod=basePeriod)
    if macroReg:
        if macroReg["rSquared"] > 0.3 and macroReg["confidence"] in ("high", "medium"):
            betas = macroReg.get("betas", {})
            for indicator, beta in betas.items():
                if abs(beta) > 2.0:
                    flags.append(("MACRO_HIGH_BETA", f"거시 베타 높음: {indicator} β={beta:+.1f}"))

    # 이벤트 충격
    eventImp = calcEventImpact(company, basePeriod=basePeriod)
    if eventImp:
        if eventImp.get("resilience") == "low":
            flags.append(("LOW_RESILIENCE", f"충격 회복력 낮음 (평균 {eventImp.get('avgRecoveryYears', '?')}년)"))
        nEvents = len(eventImp.get("events", []))
        if nEvents >= 3:
            flags.append(("FREQUENT_EVENTS", f"최근 충격 이벤트 {nEvents}건"))

    # 재고/매출채권 괴리
    inventory = calcInventoryDivergence(company, basePeriod=basePeriod)
    if inventory:
        if inventory["riskScore"] > 70:
            flags.append(("INV_HIGH_RISK", f"재고/매출채권 위험 점수 {inventory['riskScore']}"))
        if inventory["inventorySignal"] == "building":
            h = inventory["history"]
            div = h[0]["divergence"] if h and h[0].get("divergence") is not None else 0
            flags.append(("INV_DIVERGE", f"재고 급증 vs 매출 (괴리 {div:+.1f}%p)"))
        if inventory["receivableSignal"] == "deteriorating":
            flags.append(("DSO_SPIKE", "매출채권 회수 악화 — 매출 대비 채권 급증"))
        if inventory["noaGrowth"] is not None and inventory["noaGrowth"] > 20:
            flags.append(("NOA_SURGE", f"순영업자산 급증 {inventory['noaGrowth']:+.1f}%"))

    # 업종 타이밍
    timing = calcAnnouncementTiming(company, basePeriod=basePeriod)
    if timing:
        dirs = timing["reportedDirection"]
        total = sum(dirs.values())
        if total >= 3 and dirs["down"] / total >= 0.7:
            flags.append(("SECTOR_DOWNTURN", f"업종 {dirs['down']}/{total} 기업 실적 하락"))

    # 공급망 리스크
    sc = calcSupplyChainSignal(company, basePeriod=basePeriod)
    if sc:
        if sc["supplyChainRisk"] == "high":
            flags.append(("NETWORK_RISK", f"관계사 {sc['nLinkedListed']}개 중 다수 실적 악화"))

    return flags if flags else None
