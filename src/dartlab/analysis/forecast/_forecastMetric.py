"""forecast 의 forecastMetric + _marginLinkedForecast + forecastAll."""

from __future__ import annotations

import math

from dartlab.analysis.forecast._forecastTypes import (
    _FALLBACKS,
    FORECAST_TARGETS,
    ForecastResult,
)
from dartlab.core.utils.extract import getAnnualValues
from dartlab.core.utils.ols import (
    _coefficientOfVariation,
    _detectStructuralBreak,
    _ols,
)
from dartlab.frame.sector import SectorParams


def _meanRevertPath(yVals: list[float], horizon: int) -> list[float]:
    """평균 회귀 경로. 최근값에서 표본 평균으로 선형 blend.

    Parameters
    ----------
    yVals : list[float]
        과거 관측치.
    horizon : int
        예측 연수.

    Returns
    -------
    list[float]
        연도별 예측치.
    """
    meanVal = sum(yVals) / len(yVals)
    projected = []
    last = yVals[-1]
    for yr in range(1, horizon + 1):
        blend = yr / (horizon + 1)
        projected.append(last * (1 - blend) + meanVal * blend)
    return projected


def _linearPath(
    xVals: list[float],
    yVals: list[float],
    slope: float,
    intercept: float,
    horizon: int,
    warnings: list[str],
) -> list[float]:
    """선형 추세 연장. 음수 예측은 최근값의 50% 로 대체하고 경고를 남긴다.

    Parameters
    ----------
    xVals, yVals : list[float]
        회귀 입력.
    slope, intercept : float
        OLS 계수.
    horizon : int
        예측 연수.
    warnings : list[str]
        경고 누적. 제자리 변경.

    Returns
    -------
    list[float]
        연도별 예측치.
    """
    lastX = xVals[-1]
    projected = [slope * (lastX + yr) + intercept for yr in range(1, horizon + 1)]
    for i, p in enumerate(projected):
        if p < 0 and yVals[-1] > 0:
            projected[i] = yVals[-1] * 0.5
            warnings.append(f"+{i + 1}년 예측이 음수 → 최근값의 50%로 대체")
    return projected


def _cagrDecayPath(yVals: list[float], growth: float, sectorGrowth: float, horizon: int) -> list[float]:
    """지수 fade 성장 경로 (임의 선형감속 폐기).

    g(t)=gT+(g0-gT)*exp(-lambda*t). 초과성장 경쟁수렴 (Damodaran).
    lambda 는 고성장(g0>15)일 때 0.35 (완만 수렴), 그 외 0.5.

    Parameters
    ----------
    yVals : list[float]
        과거 관측치.
    growth : float
        시작 성장률 (%). -10 ~ 25 로 이미 clip 된 값.
    sectorGrowth : float
        수렴 목표 성장률 (%).
    horizon : int
        예측 연수.

    Returns
    -------
    list[float]
        연도별 예측치.
    """
    terminal = sectorGrowth
    fadeLambda = 0.35 if growth > 15 else 0.5
    projected = []
    last = yVals[-1]
    for yr in range(1, horizon + 1):
        g = terminal + (growth - terminal) * math.exp(-fadeLambda * yr)
        proj = last * (1 + g / 100)
        projected.append(proj)
        last = proj
    return projected


def _forecastAssumptions(
    method: str,
    r2: float,
    cagr: float,
    sectorGrowth: float,
    yVals: list[float],
    n: int,
) -> list[str]:
    """방법론별 가정 문장 목록.

    Parameters
    ----------
    method : str
        'linear' | 'cagr_decay' | 'mean_revert'.
    r2, cagr, sectorGrowth : float
        결정계수, CAGR(%), 섹터 성장률(%).
    yVals : list[float]
        과거 관측치.
    n : int
        관측 개수.

    Returns
    -------
    list[str]
        가정 문장. 마지막은 항상 데이터 개년 수.
    """
    assumptions = []
    if method == "linear":
        assumptions.append(f"선형 추세 연장 (R²={r2:.2f})")
    elif method == "cagr_decay":
        lam = 0.35 if min(max(cagr, -10), 25) > 15 else 0.5
        assumptions.append(f"CAGR {cagr:.1f}% → 섹터 {sectorGrowth:.1f}% 지수 fade (λ={lam}, 경쟁수렴)")
    elif method == "mean_revert":
        meanVal = sum(yVals) / n
        assumptions.append(f"평균 {meanVal / 1e8:,.0f}억으로 회귀")
    assumptions.append(f"과거 {n}개년 데이터 기반")
    return assumptions


def forecastMetric(
    series: dict,
    metric: str = "revenue",
    horizon: int = 3,
    sectorParams: SectorParams | None = None,
) -> ForecastResult:
    """단일 메트릭 시계열 예측.

    Capabilities:
        - OLS·CAGR decay·평균회귀 3 모델 자동 선택
        - 구조적 전환 감지 후 후행 구간만 학습

    Parameters
    ----------
    series : dict
        finance.timeseries 시계열 dict.
    metric : str
        예측 대상 ("revenue", "operating_income", "net_income", "operating_cashflow").
    horizon : int
        예측 기간 (년, 기본 3).
    sectorParams : SectorParams, optional
        업종별 파라미터 (성장률 등).

    Returns
    -------
    ForecastResult
        metric : str — 예측 대상 코드
        metricLabel : str — 한글 라벨
        historical : list[float | None] — 과거 연간 실적 (원)
        projected : list[float] — 예측값 시계열 (원)
        horizon : int — 예측 기간 (년)
        method : str — 사용 모델 ("linear" | "cagr_decay" | "mean_revert")
        confidence : str — 신뢰도 ("high" | "medium" | "low")
        rSquared : float — 결정계수 (0~1)
        growthRate : float — 적용 성장률 (%)

    Guide:
        finance.timeseries dict 한 개 + metric 키 하나로 단일 항목 예측.

    When:
        단일 재무 항목의 향후 3~5 년 예측이 필요할 때.

    How:
        forecastAll 내부에서 항목별 반복 호출되거나 단독 사용.

    Requires:
        timeseries 에 해당 metric annual 값 ≥ 3 개.

    Raises:
        없음. 데이터 부족 시 ForecastResult.warnings 에 사유 누적.

    Example:
        >>> r = forecastMetric(series, metric="revenue", horizon=3)
        >>> r.method in ("linear", "cagr_decay", "mean_revert", "N/A")
        True

    See Also:
        - forecastAll : 다중 메트릭 일괄 예측
        - scenarioAnalysis : optimistic/baseline/adverse 시나리오

    AIContext:
        AI 답변 시 method·confidence·rSquared 를 함께 인용해 신뢰도 표시.
    """
    warnings: list[str] = []
    target = FORECAST_TARGETS.get(metric)
    if target is None:
        return ForecastResult(
            metric=metric,
            metricLabel=metric,
            historical=[],
            projected=[],
            horizon=horizon,
            method="N/A",
            confidence="low",
            rSquared=0,
            growthRate=0,
            warnings=[f"미지원 예측 대상: {metric}"],
        )

    sjDiv, snakeId, label = target

    vals = getAnnualValues(series, sjDiv, snakeId)
    if not any(v is not None for v in vals):
        for fb in _FALLBACKS.get(snakeId, []):
            vals = getAnnualValues(series, sjDiv, fb)
            if any(v is not None for v in vals):
                break

    validPairs = [(i, v) for i, v in enumerate(vals) if v is not None]
    if len(validPairs) < 3:
        return ForecastResult(
            metric=metric,
            metricLabel=label,
            historical=vals,
            projected=[],
            horizon=horizon,
            method="N/A",
            confidence="low",
            rSquared=0,
            growthRate=0,
            warnings=["예측 불가: 유효 데이터 3년 미만"],
        )

    xVals = [float(p[0]) for p in validPairs]
    yVals = [p[1] for p in validPairs]

    breakIdx = _detectStructuralBreak(yVals, minSegment=4)
    if breakIdx is not None and breakIdx < len(yVals):
        nBefore = breakIdx
        nAfter = len(yVals) - breakIdx
        if nAfter >= 3:
            warnings.append(f"구조적 전환 감지 (데이터 {nBefore}→{nAfter}개 분할) — 전환 이후 데이터 기반 예측")
            xVals = xVals[breakIdx:]
            yVals = yVals[breakIdx:]

    cv = _coefficientOfVariation(yVals)
    slope, intercept, r2 = _ols(xVals, yVals)

    n = len(yVals)
    if yVals[0] > 0 and yVals[-1] > 0:
        cagr = ((yVals[-1] / yVals[0]) ** (1 / max(n - 1, 1)) - 1) * 100
    else:
        cagr = 0.0

    sectorGrowth = sectorParams.growthRate if sectorParams else 3.0

    if cv > 0.4:
        method = "mean_revert"
        projected = _meanRevertPath(yVals, horizon)
        growthRate = 0.0
        warnings.append("높은 변동성 → 평균 회귀 모델 적용")
    elif r2 > 0.7 and abs(cagr) < 30:
        method = "linear"
        projected = _linearPath(xVals, yVals, slope, intercept, horizon, warnings)
        growthRate = cagr
    else:
        method = "cagr_decay"
        growth = min(max(cagr, -10), 25)
        projected = _cagrDecayPath(yVals, growth, sectorGrowth, horizon)
        growthRate = growth

    if r2 > 0.8 and n >= 5:
        confidence = "high"
    elif r2 > 0.5 and n >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    assumptions = _forecastAssumptions(method, r2, cagr, sectorGrowth, yVals, n)

    return ForecastResult(
        metric=metric,
        metricLabel=label,
        historical=vals,
        projected=projected,
        horizon=horizon,
        method=method,
        confidence=confidence,
        rSquared=round(r2, 3),
        growthRate=round(growthRate, 1),
        assumptions=assumptions,
        warnings=warnings,
    )


def _revGrowthMarginPairs(revVals: list, metricVals: list) -> list[tuple[float, float]]:
    """(매출 성장률 %, 그 해 마진) 쌍 목록.

    Parameters
    ----------
    revVals, metricVals : list
        매출 / 대상 지표 연간 시계열.

    Returns
    -------
    list[tuple[float, float]]
        회귀 입력 쌍.
    """
    pairs = []
    for i in range(1, len(revVals)):
        r0, r1 = revVals[i - 1], revVals[i]
        m1 = metricVals[i] if i < len(metricVals) else None
        if r0 and r1 and m1 and r0 != 0 and r1 != 0:
            pairs.append(((r1 / r0 - 1) * 100, m1 / r1))
    return pairs


def _leverageBeta(revGrowthPairs: list[tuple[float, float]]) -> float | None:
    """영업레버리지 β. 점 4 개 미만이거나 회귀가 불안정하면 None.

    Parameters
    ----------
    revGrowthPairs : list[tuple[float, float]]
        _revGrowthMarginPairs 결과.

    Returns
    -------
    float | None
        β (%p/%p). r² 0.3 미만이거나 |β| 5.0 이상이면 None.
    """
    if len(revGrowthPairs) < 4:
        return None
    bslope, _bint, br2 = _ols([p[0] for p in revGrowthPairs], [p[1] * 100 for p in revGrowthPairs])
    if br2 >= 0.3 and abs(bslope) < 5.0:
        return bslope
    return None


def _leveragedMarginPath(
    revResult: ForecastResult,
    revVals: list,
    revGrowthPairs: list[tuple[float, float]],
    margins: list[float],
    avgMargin: float,
    leverageBeta: float,
) -> list[float]:
    """β 를 태운 마진으로 매출 전망을 이익 전망으로 옮긴다.

    Parameters
    ----------
    revResult : ForecastResult
        매출 전망.
    revVals : list
        과거 매출 시계열.
    revGrowthPairs : list[tuple[float, float]]
        회귀 입력 쌍 (정상 성장률 산출용).
    margins : list[float]
        과거 마진 (상·하한 산출용).
    avgMargin : float
        기준 마진.
    leverageBeta : float
        영업레버리지 β.

    Returns
    -------
    list[float]
        연도별 이익 예측치.
    """
    revGrowthNormal = sum(p[0] for p in revGrowthPairs) / len(revGrowthPairs)
    mlo, mhi = min(margins), max(margins)
    buf = 0.2 * (mhi - mlo) if mhi > mlo else 0.2 * abs(mhi or 0.05)
    mlo, mhi = mlo - buf, mhi + buf
    projected = []
    prevRev = float(revVals[-1])
    for rev in revResult.projected:
        rg = (rev / prevRev - 1) * 100 if prevRev else 0.0
        opm = max(mlo, min(avgMargin + (leverageBeta / 100.0) * (rg - revGrowthNormal), mhi))
        projected.append(rev * opm)
        prevRev = rev
    return projected


def _marginLinkedForecast(
    revResult: ForecastResult,
    series: dict,
    metric: str,
    horizon: int,
) -> ForecastResult | None:
    """매출 전망 × 마진 추세 → 영업이익/순이익 파생 예측.

    단순 OLS보다 정확: 매출 방향 예측(72~78%)을 이익에 전파.
    """
    if not revResult.projected or revResult.confidence == "low":
        return None

    target = FORECAST_TARGETS.get(metric)
    if target is None:
        return None
    sjDiv, snakeId, label = target

    # 과거 마진 계산
    revVals = getAnnualValues(series, "IS", "sales")
    if not any(v is not None for v in revVals):
        revVals = getAnnualValues(series, "IS", "revenue")
    metricVals = getAnnualValues(series, sjDiv, snakeId)
    for fb in _FALLBACKS.get(snakeId, []):
        if not any(v is not None for v in metricVals):
            metricVals = getAnnualValues(series, sjDiv, fb)

    margins = []
    for r, m in zip(revVals, metricVals):
        if r and m and r != 0:
            margins.append(m / r)

    if len(margins) < 2:
        return None

    # 최근 3년 마진 가중평균 (base + fallback)
    recent = margins[-3:] if len(margins) >= 3 else margins
    weights = list(range(1, len(recent) + 1))
    avgMargin = sum(w * m for w, m in zip(weights, recent)) / sum(weights)

    # 영업레버리지 마진 (고정 마진 폐기). OPM(t)=OPM_base+β·(revGrowth-normal), β=ΔOPM%/ΔRevGrowth%
    # 회귀(고정비 희석). 과거 OPM 범위 ±20% 상·하한. β 불안정(r²<0.3·<4점·폭주) 시 고정 fallback.
    revGrowthPairs = _revGrowthMarginPairs(revVals, metricVals)
    leverageBeta = _leverageBeta(revGrowthPairs)
    if leverageBeta is not None and revVals and revVals[-1]:
        projected = _leveragedMarginPath(revResult, revVals, revGrowthPairs, margins, avgMargin, leverageBeta)
        marginMethod = f"영업레버리지(β={leverageBeta:.2f}%p/%p)"
    else:
        projected = [rev * avgMargin for rev in revResult.projected]
        marginMethod = f"매출전망×고정마진({avgMargin:.1%})"
    validHist = [v for v in metricVals if v is not None]
    lastVal = validHist[-1] if validHist else 0
    growthRate = ((projected[-1] / lastVal) ** (1 / horizon) - 1) * 100 if lastVal and lastVal > 0 else 0

    return ForecastResult(
        metric=metric,
        metricLabel=label,
        historical=metricVals,
        projected=projected,
        horizon=horizon,
        method=marginMethod,
        confidence=revResult.confidence,
        rSquared=revResult.rSquared,
        growthRate=round(growthRate, 1),
        assumptions=[
            f"매출 전망 연동 (마진 {avgMargin:.1%} 적용)",
            f"최근 {len(recent)}년 가중평균 마진 사용",
        ],
        currency=revResult.currency,
    )


def forecastAll(
    series: dict,
    horizon: int = 3,
    sectorParams: SectorParams | None = None,
) -> dict[str, ForecastResult]:
    """모든 주요 메트릭 예측.

    매출은 정교한 앙상블, 영업이익/순이익은 매출x마진 연동.
    마진 연동 실패 시 단순 시계열 OLS fallback.

    Capabilities:
        - 매출·영업이익·순이익·OCF 4 메트릭 일괄 예측
        - 매출 기반 마진 연동 + OLS fallback 자동 전환

    Parameters
    ----------
    series : dict
        finance.timeseries 시계열 dict.
    horizon : int
        예측 기간 (년, 기본 3).
    sectorParams : SectorParams, optional
        업종별 파라미터.

    Returns
    -------
    dict[str, ForecastResult]
        메트릭 키 → ForecastResult 매핑.
        키: "revenue", "operating_income", "net_income", "operating_cashflow".

    Guide:
        forecastMetric 을 4 번 호출하는 진입점. DCF 사전 단계로 사용.

    When:
        예측 대시보드·DCF 입력·시나리오 분석 전 일괄 예측이 필요할 때.

    How:
        forecastMetric (revenue) → marginLinkedForecast 또는 forecastMetric 반복.

    Requires:
        finance.timeseries dict 1 개.

    Raises:
        없음. 항목별 실패는 ForecastResult.warnings 누적.

    Example:
        >>> r = forecastAll(series, horizon=3)
        >>> "revenue" in r
        True

    See Also:
        - forecastMetric : 단일 메트릭
        - scenarioAnalysis : 시나리오 가중

    AIContext:
        AI 답변 시 메트릭별 method + confidence 표로 인용.
    """
    results: dict[str, ForecastResult] = {}

    # 매출 먼저
    revResult = forecastMetric(series, metric="revenue", horizon=horizon, sectorParams=sectorParams)
    results["revenue"] = revResult

    # 영업이익/순이익: 매출×마진 연동 우선, fallback OLS
    for key in ("operating_income", "net_income"):
        linked = _marginLinkedForecast(revResult, series, key, horizon)
        if linked is not None:
            results[key] = linked
        else:
            results[key] = forecastMetric(series, metric=key, horizon=horizon, sectorParams=sectorParams)

    # OCF는 단독 예측
    results["operating_cashflow"] = forecastMetric(
        series, metric="operating_cashflow", horizon=horizon, sectorParams=sectorParams
    )

    return results


# ── 시나리오 분석 ──────────────────────────────────────────
