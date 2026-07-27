"""피어 예측 신호 — calcPeerPrediction + _extractPeerFeatures + _getHistoricalRevenueGrowth.

Cross-section + panel 회귀로 동종 업종 피어 기반의 매출 성장률 예측 + 본 회사 괴리.

predictionSignals.py 의 calc 2 분리.
"""

from __future__ import annotations

import logging
import math

from dartlab.analysis.financial._predictionMath import _fitOLS
from dartlab.analysis.financial._predictionProbability import _DIRECTION_SCORES, _clamp
from dartlab.core.memory import memoizedCalc
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.core.utils.calc import safeDiv as _safe
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

log = logging.getLogger(__name__)

_getF = _getF2 = _get
_MAX_YEARS = 8


def _getStockCode(company) -> str | None:
    return getattr(company, "stockCode", None)


def _getSectorKey(company) -> str | None:
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
# calc 2: 횡단면 피어 예측
# ══════════════════════════════════════


@memoizedCalc
def calcPeerPrediction(company, *, basePeriod: str | None = None) -> dict | None:
    """Cross-section + panel 회귀 → peer 기반 매출 성장률 예측 + 괴리.

    Capabilities:
        scan 의 사전 적합된 횡단면/패널 OLS 모델 (loadModel/loadPanelModel)
        로 이 회사의 향후 매출 성장률 (%) 을 예측. 실제 historical 성장률과
        의 괴리 (divergence) 를 측정해 outlier 시그널 산출. 5 신호 중 cross-
        section 기반 신호.

    Args:
        company: Company 객체. stockCode + 재무 시계열 필요.
        basePeriod: 기준 기간. None 이면 최신.

    Returns:
        dict | None: 다음 키 (모델/데이터 부족 시 ``None``):
            - ``crossSectionPredicted`` (float|None): 횡단면 OLS 예측 (%)
            - ``panelPredicted`` (float|None): 패널 모델 예측 (%)
            - ``ensemblePredicted`` (float): 두 모델 평균 (없으면 단일)
            - ``companyHistoricalGrowth`` (float|None): 실제 매출 성장률 (%)
            - ``divergence`` (float|None): 예측 - 실제 (%p)
            - ``modelR2`` (float|None): 횡단면 모델 R²

    Raises:
        없음.

    Example:
        >>> r = calcPeerPrediction(Company("005930"))
        >>> r["ensemblePredicted"], r["divergence"]
        (8.5, -2.3)  # 모델은 8.5% 예측, 실제는 10.8% (peer 대비 outperform)

    Guide:
        divergence > 0 → 모델보다 실제가 낮음 (peer 평균 하회). divergence
        < 0 → outperform. |divergence| > 5%p 면 outlier (peer 대비 크게
        다른 트랙). 모델 R² < 0.3 이면 예측 신뢰도 낮음.

    When:
        peer 평균 대비 outperform/underperform 신호 추출 시점.

    How:
        loadModel/loadPanelModel → 회사 features 적용 → ensemble 평균.

    SeeAlso:
        - ``loadModel``/``loadPanelModel``: 횡단면/패널 모델 로드
        - ``calcPredictionSynthesis``: 본 함수 + 4 신호 앙상블

    Requires:
        scan 사전 적합 모델 (year-1 ~ year-3 탐색) + Company 재무 시계열.

    AIContext:
        ensemblePredicted 단독 인용 금지 — modelR2 와 divergence 함께. R²
        낮은 (<0.3) 모델 예측은 informative 가 아니라 noise 신호.

    LLM Specifications:
        AntiPatterns:
            - 모델이 없는 신규 산업/IPO 종목 — None 반환, 호출자 fallback
              로직 필요.
            - divergence 부호 해석 오류 — divergence>0 = 실제가 낮음 (peer
              하회), <0 = outperform.
        OutputSchema:
            상기 6 키 dict.
        Prerequisites:
            scan/loadModel(year) 결과 존재 + Company 재무 ≥ 3 년.
        Freshness:
            모델 = 연 1 회 적합 (loadModel year 인자).
        Dataflow:
            stockCode → loadModel/loadPanelModel → company features →
            예측 → ensemble → historical 비교 → divergence.
        TargetMarkets: KR (scan SSOT). US 미적용 (모델 부재).
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
        ratios = company._getRatiosInternal()
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
    parsed = toDictBySnakeId(isResult)
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


__all__ = ["calcPeerPrediction"]
