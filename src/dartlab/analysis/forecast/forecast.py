"""시계열 예측 + 시나리오 분석 + 민감도 분석 엔진."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from dartlab.core.sector.types import SectorParams
from dartlab.core.finance.fmt import fmtBig, fmtPrice
from dartlab.core.finance.extract import getAnnualValues
from dartlab.core.finance.ols import (
    MultiOlsResult,
    _coefficientOfVariation,
    _detectStructuralBreak,
    _ols,
    _olsMulti,
)


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
    from dartlab.core.finance.dcf import DCFResult, dcfValuation

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
    from dartlab.core.finance.dcf import dcfValuation

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
