"""_signalsMacro 의 calcMacroSensitivity + calcMacroRegression + 헬퍼."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path as _Path

from dartlab.analysis.financial._constants import (
    FX_SENSITIVITY_HIGH,
    FX_SENSITIVITY_MODERATE,
    TREND_RSQUARED_HIGH,
    TREND_RSQUARED_MEDIUM,
)
from dartlab.analysis.financial._predictionMath import (
    _calcLagCorrelation,
    _fitOLS,
    _invertMatrix,
    _pearsonCorrelation,
    _quickCorr,
)
from dartlab.analysis.financial._predictionProbability import (
    _DIRECTION_SCORES,
    _bayesUpdate,
    _calibrate,
    _clamp,
)
from dartlab.analysis.financial._signalsMacroBreak import _getStockCode
from dartlab.core.logger import getLogger
from dartlab.core.memory import memoizedCalc
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.core.utils.calc import safeDiv as _safe
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

_log = getLogger(__name__)

log = logging.getLogger(__name__)
_getF = _getF2 = _getF3 = _getF4 = _get
_MAX_YEARS = 8

_SECTOR_DATA = json.loads(
    (
        _Path(__file__).resolve().parents[2]
        / "providers"
        / "mappers"
        / "mapperData"
        / "parserMappings"
        / "sectorPriors.json"
    ).read_text(encoding="utf-8")
)
_SECTOR_MACRO_MAP: dict[str, list[dict]] = _SECTOR_DATA.get("sectorMacroMap", {})
_sensitivity = _SECTOR_DATA.get("sectorSensitivity", {})
_RATE_SENSITIVE_SECTORS = set(_sensitivity.get("rate", []))
_FX_SENSITIVE_SECTORS = set(_sensitivity.get("fx", []))
_COMMODITY_SECTORS = set(_sensitivity.get("commodity", []))


def _getSectorKey(company) -> str | None:
    try:
        sector = getattr(company, "sector", None)
        if sector is None:
            return None
        igName = sector.industryGroup.name
        from dartlab.analysis.financial.valuation import _IG_TO_SECTOR_KEY

        return _IG_TO_SECTOR_KEY.get(igName)
    except (AttributeError, ValueError):
        return None


def _getRatioValues(company, ratioName: str, maxYears: int) -> list[float | None]:
    """ratioSeries에서 특정 비율의 시계열을 추출."""
    try:
        from dartlab.analysis.financial.companyContext import getRatioSeries

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


@memoizedCalc
def calcMacroSensitivity(company, *, basePeriod: str | None = None) -> dict | None:
    """거시경제 민감도 — 섹터별 탄성치 + 관련 지표 매핑.

    라이브 매크로 데이터를 fetch하지 않는다.
    관련 지표명을 반환하여 AI가 gather.macro()로 조회할 수 있게 한다.

    Capabilities:
        - 섹터 탄성치와 거시 동인 지표명을 매핑해 노출도 산출.

    Returns
    -------
    dict
        sectorKey : str | None — 업종 키
        sectorCyclicality : str — 경기순환 민감도 ("high" | "moderate" | "low")
        revenueToGdp : float — 매출-GDP 탄성치 (배수)
        revenueToFx : float — 매출-환율 탄성치 (배수)
        marginToGdp : float — 마진-GDP 탄성치 (배수)
        fxExposure : str — 환율 노출 ("high" | "moderate" | "low")
        commodityExposure : str — 원자재 노출 ("high" | "low")
        rateSensitivity : str — 금리 민감도 ("high" | "low")
        primaryDrivers : list[dict] — 1차 거시 동인 (indicator, source, direction, description)
        secondaryDrivers : list[dict] — 2차 거시 동인
        relevantIndicators : list[str] — 관련 지표 ID 목록
        predictionAxes : dict | None — 라이브 축 상태 (PredictionSpace 캐시 있을 때)
        axisImpact : dict | None — 업종별 축 영향도
        netMacroEffect : float | None — 순 매크로 효과 합산

    Guide:
        relevantIndicators 를 gather.macro() 로 조회해 라이브 결합.

    When:
        업종별 거시 노출 점검 + 시나리오 가정 정의 직전.

    How:
        getElasticity(sectorKey) + 섹터→지표 매핑 결합.

    Requires:
        sectorKey 매핑, synth.scenario.getElasticity 사용 가능.

    Raises:
        없음 — sectorKey 결측 시 기본값.

    Example:
        >>> calcMacroSensitivity(company)
        {'fxExposure': 'high', ...}

    See Also:
        - calcMacroRegression : 동적 베타 회귀.

    AIContext:
        탄성치는 섹터 기본값 — 기업별 베타는 calcMacroRegression 우선.
    """
    from dartlab.synth.scenario import getElasticity

    sectorKey = _getSectorKey(company)
    elasticity = getElasticity(sectorKey)

    # 민감도 분류
    fxExposure = (
        "high"
        if abs(elasticity.revenueToFx) >= FX_SENSITIVITY_HIGH
        else ("moderate" if abs(elasticity.revenueToFx) >= FX_SENSITIVITY_MODERATE else "low")
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


def _sectorPriorFallback(company, reason: str) -> dict | None:
    """회사 고유 회귀가 불가할 때 섹터 탄성치로 위계 폴백 (02e Part 2 방법 C).

    스킵(None) 대신 섹터 prior 를 정직 라벨과 함께 낸다. ``betas=None`` · ``rSquared=0.0``
    이라 기존 소비자의 수치 게이트(rSquared > 0.1 / > 0.3)를 통과하지 못하므로, 섹터 평균이
    기업 고유 베타로 오독될 수 없다. 섹터 미해소면 ``None`` (기본 탄성치 날조 금지).

    Args:
        company: dartlab Company 인스턴스.
        reason: 폴백 사유 (관측치 부족·지표 로드 실패 등).

    Returns:
        dict | None: 성공 반환과 동일 스키마 + ``evidenceLevel="sectorPrior"`` ·
        ``fallbackReason``. 섹터 키 미해소 시 None.
    """
    sectorKey = _getSectorKey(company)
    if sectorKey is None:
        return None
    from dartlab.synth.scenario import getElasticity

    staticEl = getElasticity(sectorKey)
    return {
        "betas": None,
        "staticBetas": {
            "gdp": staticEl.revenueToGdp,
            "rate": staticEl.marginToGdp,
            "fx": staticEl.revenueToFx,
        },
        "usedIndicators": {},
        "marginBetas": None,
        "lagEffects": {},
        "rSquared": 0.0,
        "marginR2": None,
        "nObs": 0,
        "nVars": 0,
        "degreesOfFreedom": 0,
        "confidence": "low",
        "sectorKey": sectorKey,
        "table": [],
        "_predictedDirection": None,
        "evidenceLevel": "sectorPrior",
        "fallbackReason": reason,
    }


@memoizedCalc
def calcMacroRegression(company, *, basePeriod: str | None = None) -> dict | None:
    """거시-재무 동적 회귀 — 기업별 거시 베타를 과거 데이터에서 학습.

    정적 상수(scenario.py의 revenueToGdp=1.8 등) 대신,
    실제 과거 매출/마진 성장률과 거시지표 변화율 간 OLS 회귀로
    기업 고유의 동적 베타를 추정한다.

    학술 근거:
    - Fama-MacBeth 1973: 횡단면 회귀로 팩터 프리미엄 추정
    - 시간차(lag) 효과: GDP t → 매출 t+1 (경기 전달 메커니즘)

    Capabilities:
        - 기업 고유 거시 베타와 lag 효과를 OLS 로 추정.

    Returns
    -------
    dict
        betas : dict[str, float] — OLS 기울기 (기업 고유 동적 베타, 변수별)
        staticBetas : dict[str, float] — 정적 탄성치 (gdp, rate, fx) (배수)
        usedIndicators : dict[str, str] — 사용된 지표 매핑 (v0→seriesId)
        marginBetas : dict[str, float] | None — 마진 회귀 OLS 기울기
        lagEffects : dict[str, dict] — 시간차별 상관도 (lag0, lag1, lag2)
        rSquared : float — 매출 회귀 R-squared
        marginR2 : float | None — 마진 회귀 R-squared
        nObs : int — 관측치 수
        nVars : int — 변수 수
        degreesOfFreedom : int — 자유도
        confidence : str — 신뢰도 ("high" | "medium" | "low")
        sectorKey : str | None — 업종 키
        table : list[dict] . 기간별 매출 성장률 vs 거시 변화율 시계열
        evidenceLevel : str . "observed" (기업 고유 OLS) 또는 "sectorPrior" (섹터 탄성치 폴백)
        fallbackReason : str . sectorPrior 일 때만 존재. 폴백 사유

    Guide:
        nObs ≥ 10 + R² ≥ 0.3 일 때 동적 베타 채택 권장. 회귀가 불가하면 None 이 아니라
        섹터 prior 로 위계 폴백한다 (evidenceLevel="sectorPrior", betas=None, rSquared=0.0).
        기존 수치 게이트(rSquared > 0.1 / > 0.3)가 자동으로 걸러내므로 오독 위험은 없다.

    When:
        섹터 평균 탄성치보다 기업 고유 베타가 필요한 분석.

    How:
        IS 시계열 vs 매크로 시계열 OLS, lag 0/1/2 별 R² 비교.

    Requires:
        매출 다년 + 매크로 시계열, ols 모듈.

    Raises:
        없음 — 자료 부족 시 None.

    Example:
        >>> calcMacroRegression(company)
        {'rSquared': 0.45, 'confidence': 'medium'}

    See Also:
        - calcMacroSensitivity : 정적 탄성치 매핑.

    AIContext:
        R² 낮으면 (< 0.2) staticBetas 를 본다. 회귀 자체가 불가한 회사는 evidenceLevel
        ="sectorPrior" 로 내려오므로 "데이터 없음" 과 "섹터 평균" 을 구분해 답하라.
    """
    isResult = company.select("IS", ["매출액", "영업이익"])
    isParsed = toDictBySnakeId(isResult)
    if isParsed is None:
        return _sectorPriorFallback(company, "IS 시계열 파싱 불가")
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
        return _sectorPriorFallback(company, f"YoY 관측치 부족 ({len(cols)} < 6)")

    # 적응형 변수 선택: 매핑 후보 + 범용 후보에서 상관도 기반 최적 3개
    stockCode = _getStockCode(company)
    macroData = _loadAdaptive(revGrowth, cols, stockCode=stockCode)
    if macroData is None:
        return _sectorPriorFallback(company, "매크로 지표 로드 실패")

    # OLS 회귀
    betas, rSquared, nObs = _fitOLS(revGrowth, macroData, cols)
    if betas is None:
        return _sectorPriorFallback(company, "OLS 적합 실패")

    # 시간차(lag) 상관도 계산
    lagEffects = _calcLagCorrelation(revGrowth, macroData, cols)

    # 마진 회귀 (금리 → 마진 변화)
    marginBetas, marginR2, _ = _fitOLS(marginChange, macroData, cols)

    # 정적 탄성치 비교
    from dartlab.synth.scenario import getElasticity

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
        "evidenceLevel": "observed",
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
    """Company 에서 finance series-tuple 추출 (private internal)."""
    try:
        result = company._buildFinanceSeries(freq="Q")
        return result[0] if result else None
    except (AttributeError, TypeError):
        return None


def _materializeFromHf(seriesId: str, source: str):
    """로컬 캐시 miss 인 macro 시리즈를 HF 벌크에서 받아 캐시에 적재.

    Capabilities: ``~/.dartlab/cache/macro/`` miss → ``macroHf`` fetch → enrichAndCache
        적재 → DataFrame. 미materialize 소스(관세청 customs 등) 신호 손실 방지.
    AIContext: 회귀 macro 후보 로딩의 self-healing — un-cronned 캐시 의존 제거.
    Guide: 영구 캐시 부수효과(디스크 write). 네트워크/카탈로그 부재는 None 흡수.
    When: ``_loadAdaptive`` 후보 루프에서 ``loadMacroParquet`` 이 캐시 miss 반환 직후.
    How: macroHf.fetchSeries → enrichAndCache(addChangeRate + saveMacroParquet).

    Args:
        seriesId: 지표 ID 또는 HS 코드 (예 ``"8542"``).
        source: ``"fred"`` | ``"ecos"`` | ``"customs"``.

    Returns:
        pl.DataFrame | None — date/value(+변화율). HF 에도 없으면 None.

    Raises:
        없음 — 모든 예외를 None 으로 흡수 (회귀가 해당 후보 조용히 skip).

    Requires:
        ``macroHf`` HF 네트워크 접근 + ``~/.dartlab/cache/macro/`` write 권한.

    Example:
        >>> _materializeFromHf("8542", "customs")  # doctest: +SKIP

    SeeAlso:
        gather.bulkData.macroHf.fetchSeries : HF 벌크 시계열 read.
        gather.transforms.macro.enrichAndCache : 변화율 + 캐시 적재.
    """
    try:
        from dartlab.gather.bulkData import macroHf
        from dartlab.gather.transforms.macro import enrichAndCache

        df = macroHf.fetchSeries(source, seriesId)
        if df is None or df.is_empty():
            return None
        return enrichAndCache(seriesId, df, source=source)
    except Exception as exc:
        _log.warning("HF 시계열 구성 실패로 None 반환 (%s): %s: %s", seriesId, type(exc).__name__, exc)
        return None


def _loadAdaptive(
    revGrowth: list[float | None], periodCols: list[str], stockCode: str | None = None
) -> dict[str, list[float | None]] | None:
    """적응형 변수 선택 — 매핑 후보 + 범용 후보에서 상관도 기반 최적 3개.

    1. exogenousAxes 매핑 3개 + 범용 후보 5개 = 총 8개 로드
    2. 각 변수와 revGrowth의 상관도 계산
    3. 상관도 상위 3개 선택
    """
    from dartlab.gather.transforms.macro import alignToFinancialPeriods, loadMacroParquet

    # 매핑 후보
    try:
        from dartlab.gather.mapping.exogenousAxes import getExogenousSeriesIds

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

    # 관세청 수출 후보 — productIndicators 가 회사→HS 매핑(수출업종만, 비수출업종은 빈 list).
    # greedy 선택이 HS 집중 수출기업(반도체·자동차 등)에서만 채택, 분산형은 자기보호로 배제.
    customs: list[tuple[str, str]] = []
    if stockCode:
        try:
            from dartlab.gather.mapping.productIndicators import getProductIndicators

            for ind in getProductIndicators(stockCode):
                if ind.get("source") == "customs":
                    customs.append((ind["seriesId"], "customs"))
        except (ImportError, KeyError):
            pass

    # 중복 제거하며 합치기
    seen: set[str] = set()
    candidates: list[tuple[str, str]] = []
    for sid, src in mapped + universal + customs:
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
        if isEmptyDf(df):
            df = _materializeFromHf(sid, source)  # 캐시 miss → HF 벌크 폴백 + 적재
        if isEmptyDf(df):
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


def _loadMacroAligned(periodCols: list[str], stockCode: str | None = None) -> dict[str, list[float | None]] | None:
    """Parquet 캐시에서 거시 지표를 로드 → YoY 변화율을 직접 계산.

    periodCols가 분기("2024Q3" 등)이면 전년동기 대비 YoY,
    연간이면 전년 대비 변화율.

    Returns:
        {"v0": [yoy_change, ...], "v1": [...], "_usedIndicators": {...}}
        또는 None (데이터 없음).
    """
    from dartlab.gather.transforms.macro import alignToFinancialPeriods, loadMacroParquet

    try:
        from dartlab.gather.mapping.exogenousAxes import getExogenousSeriesIds

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


__all__ = ["calcMacroRegression", "calcMacroSensitivity"]
