"""시계열 예측 + 시나리오 분석 + 민감도 분석 엔진."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from dartlab.engines.analysis.analyst.fmt import fmtBig, fmtPrice
from dartlab.engines.analysis.sector.types import SectorParams
from dartlab.engines.common.finance.extract import getAnnualValues

# ── 순수 Python OLS ──────────────────────────────────────


def _ols(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """단순 선형 회귀 (OLS)."""
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi**2 for xi in x)

    denom = n * sum_x2 - sum_x**2
    if abs(denom) < 1e-12:
        return 0.0, sum_y / n, 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    mean_y = sum_y / n
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))

    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, max(0.0, r_squared)


# ── 다변량 OLS (순수 Python — 외부 의존성 없음) ──────────


@dataclass
class MultiOlsResult:
    """다변량 OLS 결과."""

    coefficients: list[float]  # [intercept, β1, β2, ...]
    rSquared: float
    adjRSquared: float
    residuals: list[float]
    standardErrors: list[float]  # 계수별 표준오차
    tStats: list[float]  # 계수별 t-통계량
    nObs: int
    nFeatures: int


def _olsMulti(
    X: list[list[float]],
    y: list[float],
    *,
    addIntercept: bool = True,
) -> MultiOlsResult | None:
    """다변량 OLS — 순수 Python, (X'X)^-1 X'y.

    Parameters
    ----------
    X : 행 = 관측치, 열 = 독립변수
    y : 종속변수
    addIntercept : True이면 절편 열(1) 자동 추가

    Returns
    -------
    MultiOlsResult | None — 데이터 부족/특이행렬이면 None
    """
    n = len(y)
    if n < 2 or len(X) != n:
        return None

    k0 = len(X[0]) if X else 0
    if k0 == 0:
        return None

    # 절편 열 추가
    if addIntercept:
        Xa = [[1.0] + row for row in X]
    else:
        Xa = [list(row) for row in X]

    k = len(Xa[0])  # 총 변수 수 (절편 포함)
    if n <= k:
        return None

    # X'X 계산
    xtx = [[0.0] * k for _ in range(k)]
    for row in Xa:
        for i in range(k):
            for j in range(i, k):
                v = row[i] * row[j]
                xtx[i][j] += v
                if i != j:
                    xtx[j][i] += v

    # X'y 계산
    xty = [0.0] * k
    for idx in range(n):
        for j in range(k):
            xty[j] += Xa[idx][j] * y[idx]

    # (X'X)^-1 via Gauss-Jordan
    inv = _invertMatrix(xtx)
    if inv is None:
        return None

    # β = (X'X)^-1 X'y
    coeffs = [0.0] * k
    for i in range(k):
        for j in range(k):
            coeffs[i] += inv[i][j] * xty[j]

    # 잔차, R²
    meanY = sum(y) / n
    ssTot = sum((yi - meanY) ** 2 for yi in y)
    residuals = []
    ssRes = 0.0
    for idx in range(n):
        pred = sum(coeffs[j] * Xa[idx][j] for j in range(k))
        r = y[idx] - pred
        residuals.append(r)
        ssRes += r * r

    rSq = 1 - ssRes / ssTot if ssTot > 1e-15 else 0.0
    rSq = max(0.0, rSq)
    adjRSq = 1 - (1 - rSq) * (n - 1) / (n - k) if n > k else 0.0

    # 표준오차, t-통계량
    mse = ssRes / (n - k) if n > k else 0.0
    se = []
    tStats = []
    for i in range(k):
        vari = inv[i][i] * mse
        sei = math.sqrt(max(vari, 0.0))
        se.append(sei)
        tStats.append(coeffs[i] / sei if sei > 1e-15 else 0.0)

    return MultiOlsResult(
        coefficients=coeffs,
        rSquared=rSq,
        adjRSquared=adjRSq,
        residuals=residuals,
        standardErrors=se,
        tStats=tStats,
        nObs=n,
        nFeatures=k0,
    )


def _invertMatrix(m: list[list[float]]) -> list[list[float]] | None:
    """Gauss-Jordan 역행렬 (순수 Python)."""
    n = len(m)
    # augmented [M | I]
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]

    for col in range(n):
        # 피벗 선택 (부분 피벗)
        maxVal = abs(aug[col][col])
        maxRow = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > maxVal:
                maxVal = abs(aug[row][col])
                maxRow = row
        if maxVal < 1e-12:
            return None  # 특이행렬
        if maxRow != col:
            aug[col], aug[maxRow] = aug[maxRow], aug[col]

        pivot = aug[col][col]
        for j in range(2 * n):
            aug[col][j] /= pivot

        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    return [row[n:] for row in aug]


def _detectStructuralBreak(vals: list[float], minSegment: int = 4) -> int | None:
    """Chow Test 기반 구조적 변화점 감지."""
    n = len(vals)
    if n < minSegment * 2:
        return None

    xAll = list(range(n))
    _, _, r2Full = _ols([float(x) for x in xAll], vals)
    meanY = sum(vals) / n
    ssTot = sum((v - meanY) ** 2 for v in vals)
    ssrFull = ssTot * (1 - r2Full) if ssTot > 0 else 0

    bestBreak: int | None = None
    bestF = 0.0
    k = 2

    for bp in range(minSegment, n - minSegment + 1):
        x1 = [float(i) for i in range(bp)]
        y1 = vals[:bp]
        x2 = [float(i) for i in range(bp, n)]
        y2 = vals[bp:]

        _, _, r21 = _ols(x1, y1)
        _, _, r22 = _ols(x2, y2)

        ssTot1 = sum((v - sum(y1) / len(y1)) ** 2 for v in y1) if len(y1) > 0 else 0
        ssTot2 = sum((v - sum(y2) / len(y2)) ** 2 for v in y2) if len(y2) > 0 else 0

        ssr1 = ssTot1 * (1 - r21) if ssTot1 > 0 else 0
        ssr2 = ssTot2 * (1 - r22) if ssTot2 > 0 else 0

        ssrSplit = ssr1 + ssr2
        denom = ssrSplit / max(n - 2 * k, 1)
        if denom < 1e-12:
            continue

        fStat = ((ssrFull - ssrSplit) / k) / denom

        if fStat > bestF:
            bestF = fStat
            bestBreak = bp

    df = max(n - 2 * k, 1)
    fCritical = 3.0 + max(0, 10 - df) * 0.3

    if bestF > fCritical and bestBreak is not None:
        return bestBreak
    return None


def _coefficientOfVariation(values: list[float]) -> float:
    """변동계수 (CV = stdev / |mean|)."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if abs(mean) < 1e-12:
        return float("inf")
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance) / abs(mean)


# ── 결과 타입 ──────────────────────────────────────────────


@dataclass
class ForecastResult:
    """시계열 예측 결과."""

    metric: str
    metricLabel: str
    historical: list[Optional[float]]
    projected: list[float]
    horizon: int
    method: str
    confidence: str
    rSquared: float
    growthRate: float
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        c = self.currency
        lines = [
            f"[{self.metricLabel} 예측 — {self.method}]",
            f"  신뢰도: {self.confidence}  (R²={self.rSquared:.2f})",
            f"  성장률: {self.growthRate:.1f}%",
        ]
        validHist = [v for v in self.historical if v is not None]
        if validHist:
            lines.append(f"  최근 실적: {fmtBig(validHist[-1], c)}")
        if self.projected:
            for i, p in enumerate(self.projected, 1):
                lines.append(f"  +{i}년 예측: {fmtBig(p, c)}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class ScenarioResult:
    """시나리오 분석 결과."""

    base: dict[str, float]
    bull: dict[str, float]
    bear: dict[str, float]
    probability: dict[str, float]
    weightedValue: Optional[float]
    currentPrice: Optional[float]
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        c = self.currency
        lines = ["[시나리오 분석]"]
        for label, scenario, prob in [
            ("Bull", self.bull, self.probability.get("bull", 25)),
            ("Base", self.base, self.probability.get("base", 50)),
            ("Bear", self.bear, self.probability.get("bear", 25)),
        ]:
            growth = scenario.get("growth", 0)
            value = scenario.get("perShareValue", 0)
            lines.append(f"  {label} ({prob:.0f}%): 성장 {growth:+.1f}%, 적정가 {fmtPrice(value, c)}")
        if self.weightedValue is not None:
            lines.append(f"  확률가중 적정가: {fmtPrice(self.weightedValue, c)}")
        if self.currentPrice:
            lines.append(f"  현재가: {fmtPrice(self.currentPrice, c)}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class SensitivityResult:
    """민감도 분석 결과."""

    waccValues: list[float]
    growthValues: list[float]
    matrix: list[list[float]]
    baseWacc: float
    baseGrowth: float
    baseValue: float

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[민감도 분석 — WACC × 영구성장률]"]
        header = "WACC \\ g  " + "  ".join(f"{g:.1f}%" for g in self.growthValues)
        lines.append(f"  {header}")
        for i, wacc in enumerate(self.waccValues):
            row = f"  {wacc:.1f}%    " + "  ".join(
                f"{self.matrix[i][j] / 1e4:,.0f}만" if self.matrix[i][j] > 0 else "  N/A"
                for j in range(len(self.growthValues))
            )
            lines.append(row)
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ── 예측 메트릭 정의 ──────────────────────────────────────────

FORECAST_TARGETS: dict[str, tuple[str, str, str]] = {
    "revenue": ("IS", "sales", "매출"),
    "operating_income": ("IS", "operating_profit", "영업이익"),
    "net_income": ("IS", "net_profit", "순이익"),
    "operating_cashflow": ("CF", "operating_cashflow", "영업CF"),
}

_FALLBACKS: dict[str, list[str]] = {
    "sales": ["revenue"],
    "operating_profit": ["operating_income"],
    "net_profit": ["net_income"],
}


# ── 예측 엔진 ──────────────────────────────────────────────


def forecastMetric(
    series: dict,
    metric: str = "revenue",
    horizon: int = 3,
    sectorParams: Optional[SectorParams] = None,
) -> ForecastResult:
    """단일 메트릭 시계열 예측."""
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
        meanVal = sum(yVals) / n
        projected = []
        last = yVals[-1]
        for yr in range(1, horizon + 1):
            blend = yr / (horizon + 1)
            proj = last * (1 - blend) + meanVal * blend
            projected.append(proj)
        growthRate = 0.0
        warnings.append("높은 변동성 → 평균 회귀 모델 적용")
    elif r2 > 0.7 and abs(cagr) < 30:
        method = "linear"
        lastX = xVals[-1]
        projected = [slope * (lastX + yr) + intercept for yr in range(1, horizon + 1)]
        growthRate = cagr
        for i, p in enumerate(projected):
            if p < 0 and yVals[-1] > 0:
                projected[i] = yVals[-1] * 0.5
                warnings.append(f"+{i + 1}년 예측이 음수 → 최근값의 50%로 대체")
    else:
        method = "cagr_decay"
        growth = min(max(cagr, -10), 25)
        terminal = sectorGrowth
        projected = []
        last = yVals[-1]
        for yr in range(1, horizon + 1):
            blend = (yr - 1) / max(horizon - 1, 1)
            g = growth * (1 - blend) + terminal * blend
            proj = last * (1 + g / 100)
            projected.append(proj)
            last = proj
        growthRate = growth

    if r2 > 0.8 and n >= 5:
        confidence = "high"
    elif r2 > 0.5 and n >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    assumptions = []
    if method == "linear":
        assumptions.append(f"선형 추세 연장 (R²={r2:.2f})")
    elif method == "cagr_decay":
        assumptions.append(f"CAGR {cagr:.1f}% → 섹터평균 {sectorGrowth:.1f}%로 감속")
    elif method == "mean_revert":
        meanVal = sum(yVals) / n
        assumptions.append(f"평균 {meanVal / 1e8:,.0f}억으로 회귀")
    assumptions.append(f"과거 {n}개년 데이터 기반")

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


def forecastAll(
    series: dict,
    horizon: int = 3,
    sectorParams: Optional[SectorParams] = None,
) -> dict[str, ForecastResult]:
    """모든 주요 메트릭 예측."""
    return {
        key: forecastMetric(series, metric=key, horizon=horizon, sectorParams=sectorParams) for key in FORECAST_TARGETS
    }


# ── 시나리오 분석 ──────────────────────────────────────────


def scenarioAnalysis(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    currentPrice: Optional[float] = None,
) -> ScenarioResult:
    """3-Scenario DCF 분석."""
    from .valuation import DCFResult, dcfValuation

    warnings: list[str] = []
    sp = sectorParams or SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=15,
        pbrMultiple=1.2,
        evEbitdaMultiple=8,
        label="기타",
    )

    baseDcf = dcfValuation(series, shares=shares, sectorParams=sp, currentPrice=currentPrice)
    bullDcf = dcfValuation(
        series,
        shares=shares,
        sectorParams=sp,
        currentPrice=currentPrice,
        discountRate=max(sp.discountRate - 1.0, 5.0),
        terminalGrowth=min(sp.growthRate, 3.0) + 0.5,
    )
    bearDcf = dcfValuation(
        series,
        shares=shares,
        sectorParams=sp,
        currentPrice=currentPrice,
        discountRate=sp.discountRate + 1.0,
        terminalGrowth=max(min(sp.growthRate, 3.0) - 0.5, 0.5),
    )

    def _scenarioDict(dcf: DCFResult) -> dict[str, float]:
        return {
            "growth": dcf.growthRateInitial,
            "discountRate": dcf.discountRate,
            "terminalGrowth": dcf.terminalGrowth,
            "enterpriseValue": dcf.enterpriseValue,
            "equityValue": dcf.equityValue,
            "perShareValue": dcf.perShareValue or 0,
        }

    base = _scenarioDict(baseDcf)
    bull = _scenarioDict(bullDcf)
    bear = _scenarioDict(bearDcf)

    prob = {"base": 50, "bull": 25, "bear": 25}

    weighted = None
    baseV = base.get("perShareValue", 0)
    bullV = bull.get("perShareValue", 0)
    bearV = bear.get("perShareValue", 0)
    if baseV > 0 or bullV > 0 or bearV > 0:
        weighted = round(
            baseV * prob["base"] / 100 + bullV * prob["bull"] / 100 + bearV * prob["bear"] / 100,
            0,
        )

    if not baseDcf.fcfProjections:
        warnings.append("FCF 데이터 부족 → 시나리오 분석 신뢰도 낮음")

    return ScenarioResult(
        base=base,
        bull=bull,
        bear=bear,
        probability=prob,
        weightedValue=weighted,
        currentPrice=currentPrice,
        warnings=warnings,
    )


# ── 민감도 분석 ──────────────────────────────────────────


def sensitivityAnalysis(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    waccSteps: int = 5,
    waccRange: float = 2.0,
    growthSteps: int = 5,
    growthRange: float = 1.0,
) -> SensitivityResult:
    """WACC × Terminal Growth 민감도 테이블."""
    from .valuation import dcfValuation

    sp = sectorParams or SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=15,
        pbrMultiple=1.2,
        evEbitdaMultiple=8,
        label="기타",
    )

    baseWacc = sp.discountRate
    baseGrowth = min(sp.growthRate, 3.0)

    waccLo = max(baseWacc - waccRange, 4.0)
    waccHi = baseWacc + waccRange
    waccStep = (waccHi - waccLo) / max(waccSteps - 1, 1)
    waccValues = [round(waccLo + i * waccStep, 1) for i in range(waccSteps)]

    growthLo = max(baseGrowth - growthRange, 0.5)
    growthHi = baseGrowth + growthRange
    gStep = (growthHi - growthLo) / max(growthSteps - 1, 1)
    gValues = [round(growthLo + i * gStep, 1) for i in range(growthSteps)]

    matrix: list[list[float]] = []
    bValue = 0.0

    for wacc in waccValues:
        row: list[float] = []
        for tg in gValues:
            if wacc <= tg:
                row.append(0)
                continue
            dcf = dcfValuation(
                series,
                shares=shares,
                sectorParams=sp,
                discountRate=wacc,
                terminalGrowth=tg,
            )
            val = dcf.perShareValue or 0
            row.append(val)
            if abs(wacc - baseWacc) < 0.05 and abs(tg - baseGrowth) < 0.05:
                bValue = val
        matrix.append(row)

    return SensitivityResult(
        waccValues=waccValues,
        growthValues=gValues,
        matrix=matrix,
        baseWacc=baseWacc,
        baseGrowth=baseGrowth,
        baseValue=bValue,
    )
