"""경제 시나리오 기반 시뮬레이션 예측 엔진.

3-Layer 구조:
1. MacroScenario — 거시경제 변수 경로 (GDP, 금리, 환율, CPI)
2. SectorElasticity — 업종별 거시경제 감응도 (beta)
3. CompanySimulation — 기업 실적 시뮬레이션 (시나리오 + Monte Carlo + 스트레스)

외부 의존성 제로 (random 모듈만 사용).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from dartlab.core.sector.types import SectorParams
from dartlab.core.finance.fmt import fmtBig, fmtPrice
from dartlab.core.finance.extract import (
    getAnnualValues,
    getLatest,
    getTTM,
)
from dartlab.core.finance.scenario import (
    BASELINE_FX,
    BASELINE_RATE,
    DEFAULT_ELASTICITY,
    MacroScenario,
    PRESET_SCENARIOS,
    PRESET_SCENARIOS_KR,
    PRESET_SCENARIOS_US,
    SECTOR_ELASTICITY,
    SectorElasticity,
    getElasticity,
    getPresetScenarios,
)


# ══════════════════════════════════════
# Layer 3: 기업 시뮬레이션
# ══════════════════════════════════════

# ── 결과 타입 ──


@dataclass
class SimulationResult:
    """단일 시나리오 시뮬레이션 결과."""

    scenarioName: str
    scenarioLabel: str
    years: int
    revenuePath: list[float]
    operatingIncomePath: list[float]
    marginPath: list[float]
    fcfPath: list[float]
    dcfValue: float
    perShareValue: Optional[float]
    revenueChangePct: float
    marginChangeBps: float
    elasticityUsed: SectorElasticity
    assumptions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 시뮬레이션은 참고용이며 실제 경제 상황과 다를 수 있습니다."

    def __repr__(self) -> str:
        c = self.currency
        lines = [f"[{self.scenarioLabel} 시뮬레이션]"]
        lines.append(f"  경기감응도: {self.elasticityUsed}")
        for i, (rev, oi, mg) in enumerate(
            zip(
                self.revenuePath,
                self.operatingIncomePath,
                self.marginPath,
            )
        ):
            lines.append(f"  +{i + 1}년: 매출 {fmtBig(rev, c)}, 영업이익 {fmtBig(oi, c)}, 마진 {mg:.1f}%")
        lines.append(f"  매출 변화: {self.revenueChangePct:+.1f}%")
        lines.append(f"  마진 변화: {self.marginChangeBps:+.0f}bps")
        if self.perShareValue is not None:
            lines.append(f"  주당 가치: {fmtPrice(self.perShareValue, c)}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class MonteCarloResult:
    """Monte Carlo 시뮬레이션 결과."""

    iterations: int
    scenarioName: str
    percentiles: dict[str, dict[str, float]]
    expectedValue: float
    stdDev: float
    var95: float
    upsideProbability: float  # 현재 대비 상승 확률 (%)
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 시뮬레이션은 참고용이며 실제 경제 상황과 다를 수 있습니다."

    def __repr__(self) -> str:
        c = self.currency
        lines = [f"[Monte Carlo — {self.scenarioName} ({self.iterations:,}회)]"]
        for metric, pcts in self.percentiles.items():
            p5 = pcts.get("p5", 0)
            p50 = pcts.get("p50", 0)
            p95 = pcts.get("p95", 0)
            lines.append(f"  {metric}: P5={fmtBig(p5, c)}  P50={fmtBig(p50, c)}  P95={fmtBig(p95, c)}")
        lines.append(f"  기대값: {fmtBig(self.expectedValue, c)}")
        lines.append(f"  VaR(95%): {fmtBig(self.var95, c)}")
        lines.append(f"  상승 확률: {self.upsideProbability:.0f}%")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class StressTestResult:
    """스트레스 테스트 결과."""

    scenarioName: str
    scenarioLabel: str
    year3RevenueChange: float
    year3MarginChange: float
    year3DebtRatio: Optional[float]
    year3CurrentRatio: Optional[float]
    year3InterestCoverage: Optional[float]
    survivalRisk: str  # "low" | "medium" | "high" | "critical"
    dividendSustainable: bool
    recoveryTimeline: str
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 시뮬레이션은 참고용이며 실제 경제 상황과 다를 수 있습니다."

    def __repr__(self) -> str:
        lines = [f"[스트레스 테스트 — {self.scenarioLabel}]"]
        lines.append(f"  3년 후 매출 변화: {self.year3RevenueChange:+.1f}%")
        lines.append(f"  3년 후 마진 변화: {self.year3MarginChange:+.0f}bps")
        if self.year3DebtRatio is not None:
            lines.append(f"  3년 후 부채비율: {self.year3DebtRatio:.0f}%")
        if self.year3CurrentRatio is not None:
            lines.append(f"  3년 후 유동비율: {self.year3CurrentRatio:.0f}%")
        if self.year3InterestCoverage is not None:
            lines.append(f"  3년 후 이자보상배율: {self.year3InterestCoverage:.1f}x")
        lines.append(f"  생존 위험도: {self.survivalRisk}")
        lines.append(f"  배당 지속: {'가능' if self.dividendSustainable else '불가능'}")
        lines.append(f"  회복 전망: {self.recoveryTimeline}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ── 내부 유틸 ──


def _extractBaseMetrics(series: dict) -> dict[str, Optional[float]]:
    """현재 기업 기본 지표 추출."""
    rev = getTTM(series, "IS", "sales") or getTTM(series, "IS", "revenue")
    oi = getTTM(series, "IS", "operating_profit") or getTTM(series, "IS", "operating_income")
    ni = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income")
    ocf = getTTM(series, "CF", "operating_cashflow")
    capex = getTTM(series, "CF", "purchase_of_property_plant_and_equipment")
    div = getTTM(series, "CF", "dividends_paid")

    margin = (oi / rev * 100) if rev and oi and rev > 0 else None
    fcf = (ocf - abs(capex or 0)) if ocf is not None else None

    totalAssets = getLatest(series, "BS", "total_assets")
    totalEquity = getLatest(series, "BS", "total_stockholders_equity") or getLatest(
        series, "BS", "owners_of_parent_equity"
    )
    totalLiab = getLatest(series, "BS", "total_liabilities")
    currentAssets = getLatest(series, "BS", "current_assets")
    currentLiab = getLatest(series, "BS", "current_liabilities")
    cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
    stb = getLatest(series, "BS", "shortterm_borrowings") or 0
    ltb = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "debentures") or 0
    finCosts = getTTM(series, "IS", "finance_costs") or getTTM(series, "IS", "interest_expense")

    debtRatio = (totalLiab / totalEquity * 100) if totalLiab and totalEquity and totalEquity > 0 else None
    currentRatio = (currentAssets / currentLiab * 100) if currentAssets and currentLiab and currentLiab > 0 else None
    interestCov = (oi / abs(finCosts)) if oi and finCosts and abs(finCosts) > 0 else None
    netDebt = stb + ltb + bonds - cash

    return {
        "revenue": rev,
        "operatingIncome": oi,
        "netIncome": ni,
        "margin": margin,
        "ocf": ocf,
        "fcf": fcf,
        "capex": capex,
        "dividendsPaid": div,
        "totalAssets": totalAssets,
        "totalEquity": totalEquity,
        "totalLiabilities": totalLiab,
        "currentAssets": currentAssets,
        "currentLiabilities": currentLiab,
        "debtRatio": debtRatio,
        "currentRatio": currentRatio,
        "interestCoverage": interestCov,
        "netDebt": netDebt,
        "financeCosts": finCosts,
    }


def _extractVolatility(series: dict) -> dict[str, float]:
    """과거 시계열에서 변동성 추출."""
    revVals = getAnnualValues(series, "IS", "sales") or getAnnualValues(series, "IS", "revenue")
    oiVals = getAnnualValues(series, "IS", "operating_profit") or getAnnualValues(series, "IS", "operating_income")

    def _std(values: list) -> float:
        valid = [v for v in values if v is not None]
        if len(valid) < 3:
            return 0.1  # 기본값 10%
        mean = sum(valid) / len(valid)
        if abs(mean) < 1e-12:
            return 0.1
        variance = sum((v - mean) ** 2 for v in valid) / (len(valid) - 1)
        return math.sqrt(variance) / abs(mean)

    def _marginStd(revList: list, oiList: list) -> float:
        margins = []
        for r, o in zip(revList, oiList):
            if r is not None and o is not None and r > 0:
                margins.append(o / r * 100)
        if len(margins) < 3:
            return 2.0  # 기본 2%p
        mean = sum(margins) / len(margins)
        variance = sum((m - mean) ** 2 for m in margins) / (len(margins) - 1)
        return math.sqrt(variance)

    return {
        "revenueCv": _std(revVals),
        "marginStd": _marginStd(revVals, oiVals),
    }


def _applyMacroShock(
    baseRevenue: float,
    baseMargin: float,
    scenario: MacroScenario,
    elasticity: SectorElasticity,
    yearIdx: int,
    baseWacc: float,
) -> tuple[float, float, float]:
    """매크로 충격 적용 -> (조정 매출, 조정 마진%, 조정 할인율)."""
    gdp = scenario.gdpGrowth[yearIdx]
    rate = scenario.interestRate[yearIdx]
    fx = scenario.krwUsd[yearIdx]

    # GDP 충격
    revGdpEffect = elasticity.revenueToGdp * gdp / 100

    # 환율 충격 (baseline 대비 변화율)
    fxChangePct = (fx - BASELINE_FX) / BASELINE_FX * 100
    revFxEffect = elasticity.revenueToFx * fxChangePct / 1000  # 10%당 beta 적용

    adjustedRevenue = baseRevenue * (1 + revGdpEffect + revFxEffect)

    # 마진 충격
    marginShockBps = elasticity.marginToGdp * gdp / 100
    # NIM 충격 (금융업)
    rateChange = rate - BASELINE_RATE
    nimShockBps = elasticity.nimToRate * rateChange / 100
    adjustedMargin = baseMargin + marginShockBps + nimShockBps

    # WACC 조정 (금리 변동의 50% 반영)
    adjustedWacc = baseWacc + rateChange * 0.5

    return adjustedRevenue, max(adjustedMargin, -50), adjustedWacc


# ── 시나리오 시뮬레이션 ──


def simulateScenario(
    series: dict,
    scenario: MacroScenario | str,
    sectorKey: Optional[str] = None,
    sectorParams: Optional[SectorParams] = None,
    shares: Optional[int] = None,
) -> SimulationResult:
    """단일 거시경제 시나리오 하에서 3년 실적 경로 시뮬레이션."""
    warnings: list[str] = []

    # 시나리오 로드
    if isinstance(scenario, str):
        sc = PRESET_SCENARIOS.get(scenario)
        if sc is None:
            return SimulationResult(
                scenarioName=scenario,
                scenarioLabel="알 수 없음",
                years=0,
                revenuePath=[],
                operatingIncomePath=[],
                marginPath=[],
                fcfPath=[],
                dcfValue=0,
                perShareValue=None,
                revenueChangePct=0,
                marginChangeBps=0,
                elasticityUsed=DEFAULT_ELASTICITY,
                warnings=[f"미지원 시나리오: {scenario}. 선택지: {', '.join(PRESET_SCENARIOS)}"],
            )
    else:
        sc = scenario

    elasticity = getElasticity(sectorKey)
    base = _extractBaseMetrics(series)
    baseWacc = sectorParams.discountRate if sectorParams else 10.0

    rev = base["revenue"]
    margin = base["margin"]
    if rev is None or rev <= 0:
        return SimulationResult(
            scenarioName=sc.name,
            scenarioLabel=sc.label,
            years=0,
            revenuePath=[],
            operatingIncomePath=[],
            marginPath=[],
            fcfPath=[],
            dcfValue=0,
            perShareValue=None,
            revenueChangePct=0,
            marginChangeBps=0,
            elasticityUsed=elasticity,
            warnings=["매출 데이터 부족"],
        )

    if margin is None:
        margin = 10.0
        warnings.append("마진 데이터 미확인 -> 10%로 가정")

    capexRatio = abs(base["capex"] or 0) / rev if rev > 0 else 0.05
    taxRate = 0.22  # 한국 법인세 기본

    # 3년 경로 시뮬레이션
    horizon = min(len(sc.gdpGrowth), 3)
    revenuePath: list[float] = []
    oiPath: list[float] = []
    marginPath: list[float] = []
    fcfPath: list[float] = []
    waccPath: list[float] = []

    prevRev = rev
    prevMargin = margin

    for yr in range(horizon):
        adjRev, adjMargin, adjWacc = _applyMacroShock(
            prevRev,
            prevMargin,
            sc,
            elasticity,
            yr,
            baseWacc,
        )
        adjOi = adjRev * adjMargin / 100
        adjFcf = adjOi * (1 - taxRate) - adjRev * capexRatio

        revenuePath.append(adjRev)
        oiPath.append(adjOi)
        marginPath.append(adjMargin)
        fcfPath.append(adjFcf)
        waccPath.append(adjWacc)

        prevRev = adjRev
        prevMargin = adjMargin

    # DCF 가치 (시나리오 경로의 FCF 합산)
    terminalGrowth = min(sectorParams.growthRate if sectorParams else 3.0, 3.0)
    lastWacc = waccPath[-1] if waccPath else baseWacc

    if lastWacc <= terminalGrowth:
        terminalGrowth = max(lastWacc - 2.0, 0.5)

    pvSum = sum(fcf / (1 + lastWacc / 100) ** (yr + 1) for yr, fcf in enumerate(fcfPath))
    terminalFcf = fcfPath[-1] if fcfPath else 0
    if terminalFcf > 0:
        tv = terminalFcf * (1 + terminalGrowth / 100) / (lastWacc / 100 - terminalGrowth / 100)
        pvTv = tv / (1 + lastWacc / 100) ** horizon
    else:
        tv = 0
        pvTv = 0
        warnings.append("FCF 음수 -> Terminal Value 미적용")

    ev = pvSum + pvTv
    netDebt = base["netDebt"] or 0
    equityValue = ev - netDebt
    perShare = equityValue / shares if shares and shares > 0 else None

    # 변화율 계산
    finalRev = revenuePath[-1] if revenuePath else rev
    revChange = (finalRev - rev) / rev * 100 if rev > 0 else 0
    marginChange = (marginPath[-1] - margin) * 100 if marginPath else 0  # bps

    return SimulationResult(
        scenarioName=sc.name,
        scenarioLabel=sc.label,
        years=horizon,
        revenuePath=revenuePath,
        operatingIncomePath=oiPath,
        marginPath=marginPath,
        fcfPath=fcfPath,
        dcfValue=ev,
        perShareValue=perShare,
        revenueChangePct=round(revChange, 1),
        marginChangeBps=round(marginChange, 0),
        elasticityUsed=elasticity,
        assumptions={
            "경기감응도(beta)": f"GDP {elasticity.revenueToGdp:.1f}, FX {elasticity.revenueToFx:.1f}",
            "업종 경기민감도": elasticity.cyclicality,
            "할인율": f"{baseWacc:.1f}% -> {lastWacc:.1f}%",
            "CapEx 비율": f"{capexRatio * 100:.1f}%",
        },
        warnings=warnings,
    )


def simulateAllScenarios(
    series: dict,
    sectorKey: Optional[str] = None,
    sectorParams: Optional[SectorParams] = None,
    shares: Optional[int] = None,
    scenarios: Optional[list[str]] = None,
) -> dict[str, SimulationResult]:
    """모든 사전 정의 시나리오 일괄 시뮬레이션."""
    keys = scenarios or list(PRESET_SCENARIOS.keys())
    return {
        key: simulateScenario(series, key, sectorKey, sectorParams, shares) for key in keys if key in PRESET_SCENARIOS
    }


# ── Monte Carlo 시뮬레이션 ──


def monteCarloForecast(
    series: dict,
    sectorKey: Optional[str] = None,
    sectorParams: Optional[SectorParams] = None,
    shares: Optional[int] = None,
    scenario: MacroScenario | str = "baseline",
    iterations: int = 10000,
    horizon: int = 3,
    seed: Optional[int] = None,
) -> MonteCarloResult:
    """Monte Carlo 시뮬레이션 (순수 Python)."""
    if seed is not None:
        random.seed(seed)

    warnings: list[str] = []

    # 시나리오 로드
    if isinstance(scenario, str):
        sc = PRESET_SCENARIOS.get(scenario, PRESET_SCENARIOS["baseline"])
    else:
        sc = scenario

    elasticity = getElasticity(sectorKey)
    base = _extractBaseMetrics(series)
    vol = _extractVolatility(series)
    baseWacc = sectorParams.discountRate if sectorParams else 10.0

    rev = base["revenue"]
    margin = base["margin"]
    if rev is None or rev <= 0:
        return MonteCarloResult(
            iterations=iterations,
            scenarioName=sc.name,
            percentiles={},
            expectedValue=0,
            stdDev=0,
            var95=0,
            upsideProbability=0,
            warnings=["매출 데이터 부족"],
        )
    if margin is None:
        margin = 10.0

    revCv = min(vol["revenueCv"], 0.5)  # 상한 50%
    marginStd = min(vol["marginStd"], 10.0)  # 상한 10%p

    # 평균 경로 계산 (시나리오 기반)
    meanRevPath: list[float] = []
    meanMarginPath: list[float] = []
    prevR, prevM = rev, margin
    for yr in range(min(horizon, len(sc.gdpGrowth))):
        ar, am, _ = _applyMacroShock(prevR, prevM, sc, elasticity, yr, baseWacc)
        meanRevPath.append(ar)
        meanMarginPath.append(am)
        prevR, prevM = ar, am

    # Monte Carlo 실행
    finalRevenues: list[float] = []
    finalOis: list[float] = []
    finalFcfs: list[float] = []

    capexRatio = abs(base["capex"] or 0) / rev if rev > 0 else 0.05
    taxRate = 0.22

    for _ in range(iterations):
        simRev = rev
        simMargin = margin
        for yr in range(len(meanRevPath)):
            # 평균 경로에 노이즈 추가
            revNoise = random.gauss(0, revCv)
            marginNoise = random.gauss(0, marginStd)

            simRev = meanRevPath[yr] * (1 + revNoise)
            simMargin = meanMarginPath[yr] + marginNoise

        simOi = simRev * max(simMargin, -50) / 100
        simFcf = simOi * (1 - taxRate) - simRev * capexRatio

        finalRevenues.append(simRev)
        finalOis.append(simOi)
        finalFcfs.append(simFcf)

    # 백분위 산출
    def _percentiles(vals: list[float]) -> dict[str, float]:
        sortedVals = sorted(vals)
        n = len(sortedVals)
        return {
            "p5": sortedVals[int(n * 0.05)],
            "p25": sortedVals[int(n * 0.25)],
            "p50": sortedVals[int(n * 0.50)],
            "p75": sortedVals[int(n * 0.75)],
            "p95": sortedVals[int(n * 0.95)],
        }

    percentiles = {
        "매출": _percentiles(finalRevenues),
        "영업이익": _percentiles(finalOis),
        "FCF": _percentiles(finalFcfs),
    }

    # 통계
    meanRevFinal = sum(finalRevenues) / iterations
    stdDev = math.sqrt(sum((r - meanRevFinal) ** 2 for r in finalRevenues) / (iterations - 1))
    var95 = sorted(finalRevenues)[int(iterations * 0.05)]
    upsideProb = sum(1 for r in finalRevenues if r > rev) / iterations * 100

    if revCv >= 0.4:
        warnings.append("과거 매출 변동성 높음 -> 시뮬레이션 신뢰도 낮음")

    return MonteCarloResult(
        iterations=iterations,
        scenarioName=sc.label,
        percentiles=percentiles,
        expectedValue=meanRevFinal,
        stdDev=stdDev,
        var95=var95,
        upsideProbability=round(upsideProb, 1),
        warnings=warnings,
    )


# ── 스트레스 테스트 ──


def stressTest(
    series: dict,
    sectorKey: Optional[str] = None,
    sectorParams: Optional[SectorParams] = None,
    scenario: str = "adverse",
) -> StressTestResult:
    """CCAR 스타일 스트레스 테스트."""
    warnings: list[str] = []

    sim = simulateScenario(series, scenario, sectorKey, sectorParams)
    base = _extractBaseMetrics(series)

    sc = PRESET_SCENARIOS.get(scenario, PRESET_SCENARIOS["adverse"])

    # 3년 후 재무 건전성 추정
    revChange = sim.revenueChangePct
    marginChange = sim.marginChangeBps

    # 부채비율 추정: 이익 감소 -> 자본 감소 -> 부채비율 상승
    debtRatio3y = None
    if base["debtRatio"] is not None and base["totalEquity"] and base["totalEquity"] > 0:
        # 3년간 누적 이익 변화 반영
        cumProfitLoss = sum(sim.operatingIncomePath) * 0.78 if sim.operatingIncomePath else 0
        baselineProfit = (base["operatingIncome"] or 0) * 0.78 * 3
        equityChange = cumProfitLoss - baselineProfit
        newEquity = base["totalEquity"] + equityChange
        if newEquity > 0:
            debtRatio3y = round((base["totalLiabilities"] or 0) / newEquity * 100, 0)
        else:
            debtRatio3y = 9999
            warnings.append("스트레스 하 자본잠식 위험")

    # 유동비율 추정
    currentRatio3y = base["currentRatio"]
    if currentRatio3y is not None and revChange < -10:
        currentRatio3y = currentRatio3y * (1 + revChange / 100 * 0.3)  # 보수적 조정

    # 이자보상배율
    intCov3y = None
    if sim.operatingIncomePath and base["financeCosts"] and abs(base["financeCosts"]) > 0:
        intCov3y = round(sim.operatingIncomePath[-1] / abs(base["financeCosts"]), 1)

    # 배당 지속 가능성
    divSustainable = True
    if base["dividendsPaid"] and sim.fcfPath:
        finalFcf = sim.fcfPath[-1]
        divAmount = abs(base["dividendsPaid"] or 0)
        if finalFcf < divAmount:
            divSustainable = False

    # 생존 위험도 판단
    riskScore = 0
    if revChange < -20:
        riskScore += 2
    elif revChange < -10:
        riskScore += 1

    if debtRatio3y is not None and debtRatio3y > 300:
        riskScore += 2
    elif debtRatio3y is not None and debtRatio3y > 200:
        riskScore += 1

    if intCov3y is not None and intCov3y < 1:
        riskScore += 2
    elif intCov3y is not None and intCov3y < 2:
        riskScore += 1

    if not divSustainable:
        riskScore += 1

    if riskScore >= 5:
        survivalRisk = "critical"
    elif riskScore >= 3:
        survivalRisk = "high"
    elif riskScore >= 1:
        survivalRisk = "medium"
    else:
        survivalRisk = "low"

    # 회복 전망
    elasticity = getElasticity(sectorKey)
    if elasticity.cyclicality == "high":
        recovery = "V자 반등 가능 (경기민감 업종)"
    elif elasticity.cyclicality == "defensive":
        recovery = "안정적 — 충격 자체가 제한적"
    else:
        recovery = "점진적 회복 (1~2년)"

    return StressTestResult(
        scenarioName=sc.name,
        scenarioLabel=sc.label,
        year3RevenueChange=round(revChange, 1),
        year3MarginChange=round(marginChange, 0),
        year3DebtRatio=debtRatio3y,
        year3CurrentRatio=round(currentRatio3y, 0) if currentRatio3y else None,
        year3InterestCoverage=intCov3y,
        survivalRisk=survivalRisk,
        dividendSustainable=divSustainable,
        recoveryTimeline=recovery,
        warnings=warnings,
    )
