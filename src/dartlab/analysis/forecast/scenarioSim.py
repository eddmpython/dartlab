"""시나리오 시뮬레이터 — 분기별 모니터링 + 행동 추천.

예측하지 않는다. 시나리오를 설정하고, 분기마다 실적과 비교하여
어떤 경로 위에 있는지 판정하고, 행동을 추천한다.

흐름::

    1. createSimulation(company, "반도체 회복", revenueGrowth=15)
       → 3개 시나리오(bull/base/bear) × ProForma IS/BS/CF
       → 과거 계절성으로 Q1~Q4 분기 목표 분해
       → 시나리오별 DCF 적정가치

    2. judgeQuarter(sim, "2025Q1", revenue, operatingIncome)
       → 매출 + 영업이익 이중 판정
       → 연간 착지 재예측
       → 행동 추천

검증: experiments/107_scenarioSim (001~008, 8개 기업 사후 검증 완료).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from dartlab.core.finance.proforma import (
    ProFormaResult,
    ProFormaYear,
    build_proforma,
    extract_historical_ratios,
)

# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass
class QuarterJudgment:
    """한 분기 실적 판정 결과."""

    quarter: str
    actualRevenue: float
    actualOI: float
    targetRevBase: float
    targetOIBase: float
    revDeviation: float  # (actual - base) / base × 100
    oiDeviation: float
    revPath: str  # on_track | outperform | outperform_mild | underperform | underperform_severe
    oiPath: str
    action: str  # 보유 | 비중확대 검토 | 비중축소 검토 | 시나리오 재설정
    reason: str
    reforecastRevenue: float  # 연간 착지 재예측
    reforecastOI: float


@dataclass
class ScenarioSimulation:
    """시나리오 시뮬레이션 세션."""

    stockCode: str
    companyName: str
    scenarioName: str
    baseYear: str
    targetYear: str
    createdAt: str = field(default_factory=lambda: datetime.now().isoformat())

    # 시나리오 가정
    revenueGrowthPath: list[float] = field(default_factory=list)
    marginBlendWeight: float = 0.5

    # ProForma 결과 (bull/base/bear)
    proformaResults: dict[str, ProFormaResult] = field(default_factory=dict)

    # 분기 목표
    quarterlyRevTargets: dict[str, list[float]] = field(default_factory=dict)
    quarterlyOITargets: dict[str, list[float]] = field(default_factory=dict)

    # DCF 적정가치
    dcfPerShare: dict[str, int] = field(default_factory=dict)

    # 판정 이력
    judgments: list[QuarterJudgment] = field(default_factory=list)

    # 계절성 비중
    revSeasonality: list[float] = field(default_factory=list)
    oiSeasonality: list[float] = field(default_factory=list)


# ══════════════════════════════════════
# 내부 유틸
# ══════════════════════════════════════


def _quarterlyValues(is_df: Any, snakeId: str, year: str) -> list[float]:
    """IS DataFrame에서 특정 연도의 Q1~Q4 값 추출."""
    row = is_df.filter(is_df["snakeId"] == snakeId)
    if row.height == 0:
        return []
    vals = []
    for q in range(1, 5):
        col = f"{year}Q{q}"
        if col in row.columns:
            v = row[col].to_list()[0]
            vals.append(float(v) if v is not None else 0)
    return vals if len(vals) == 4 else []


def _computeSeasonality(is_df: Any, snakeId: str, years: list[str]) -> list[float]:
    """과거 N년 Q1~Q4 비중 평균."""
    all_w: list[list[float]] = []
    for y in years:
        qv = _quarterlyValues(is_df, snakeId, y)
        if len(qv) == 4:
            total = sum(abs(v) for v in qv)
            if total > 0:
                all_w.append([abs(v) / total for v in qv])
    if not all_w:
        return [0.25, 0.25, 0.25, 0.25]
    n = len(all_w)
    avg = [sum(w[q] for w in all_w) / n for q in range(4)]
    s = sum(avg)
    return [w / s for w in avg] if s > 0 else [0.25] * 4


def _blendWeight(baseOpMargin: float) -> float:
    """기준연도 영업이익률 → 과거 비율 가중치.

    저마진/적자 기업일수록 과거 비율(정상 수준)에 더 의존.
    """
    if baseOpMargin < 2.0:
        return 0.8
    elif baseOpMargin < 5.0:
        return 0.7
    else:
        return 0.5


def _judgePath(actual: float, bull: float, base: float, bear: float, tolerance: float = 0.05) -> str:
    """실적 vs 시나리오 목표 → 경로 판정."""
    if base == 0:
        return "unknown"
    dev = (actual - base) / abs(base)
    if abs(dev) <= tolerance:
        return "on_track"
    elif actual >= bull:
        return "outperform"
    elif actual <= bear:
        return "underperform_severe"
    elif dev > 0:
        return "outperform_mild"
    else:
        return "underperform"


def _decideAction(revPath: str, oiPath: str, history: list[QuarterJudgment]) -> tuple[str, str]:
    """매출 + 영업이익 이중 판정 → 행동 추천."""
    severity = {
        "outperform": 2,
        "outperform_mild": 1,
        "on_track": 0,
        "underperform": -1,
        "underperform_severe": -2,
        "unknown": 0,
    }
    combined = (severity.get(revPath, 0) + severity.get(oiPath, 0)) / 2

    prevScores = []
    for h in history[-2:]:
        ps = (severity.get(h.revPath, 0) + severity.get(h.oiPath, 0)) / 2
        prevScores.append(ps)
    consecutiveNeg = all(s < 0 for s in prevScores) if prevScores else False

    if combined >= 1.5:
        return "비중확대 검토", "매출+이익 모두 Bull 이상"
    elif combined >= 0.5:
        if prevScores and prevScores[-1] >= 0.5:
            return "비중확대 검토", "2분기 연속 상회"
        return "보유 (긍정)", "상회 관찰 중"
    elif combined >= -0.5:
        return "보유", "시나리오 경로 내"
    elif combined >= -1.5:
        if consecutiveNeg:
            return "비중축소 검토", "2분기 연속 하회"
        if oiPath == "underperform_severe" and "underperform" not in revPath:
            return "비중축소 검토", "매출은 괜찮으나 마진 붕괴"
        return "보유 (경계)", "1분기 하회, 추세 확인 필요"
    else:
        return "비중축소 검토", "Bear 시나리오 이탈"


def _scenarioDCF(
    projections: list[ProFormaYear],
    wacc_pct: float,
    netDebt: float = 0,
    shares: int = 1,
    terminalGrowth: float = 0.02,
) -> int:
    """3년 ProForma FCF → DCF 적정가 (per share)."""
    wacc = wacc_pct / 100
    if wacc <= terminalGrowth:
        wacc = terminalGrowth + 0.05

    pvFcf = sum(p.fcf / (1 + wacc) ** (i + 1) for i, p in enumerate(projections))

    lastP = projections[-1]
    normalizedFcf = lastP.ocf - lastP.depreciation
    if normalizedFcf <= 0:
        normalizedFcf = lastP.ocf * 0.3

    tv = normalizedFcf * (1 + terminalGrowth) / (wacc - terminalGrowth)
    pvTv = tv / (1 + wacc) ** len(projections)

    ev = pvFcf + pvTv
    equityValue = ev - netDebt
    return int(equityValue / shares) if shares > 0 else 0


# ══════════════════════════════════════
# 공개 API
# ══════════════════════════════════════


def createSimulation(
    company: Any,
    scenarioName: str,
    revenueGrowth: float | list[float],
    *,
    baseYear: str = "2024",
    targetYear: str = "2025",
    bullSpread: float = 1.5,
    bearSpread: float = 0.3,
    overrides: dict[str, float] | None = None,
    shares: int | None = None,
) -> ScenarioSimulation:
    """시나리오 시뮬레이션 생성.

    Args:
        company: Company 객체.
        scenarioName: 사용자 지정 이름 ("반도체 회복" 등).
        revenueGrowth: 연간 매출 성장률 (%). float이면 3년 수렴 자동 생성.
        baseYear: 기준 연도 (이 해까지의 데이터로 시나리오 설정).
        targetYear: 검증 대상 연도.
        bullSpread: Bull 성장률 = base × bullSpread.
        bearSpread: Bear 성장률 = base × bearSpread.
        overrides: ProForma 비율 오버라이드.
        shares: 발행주식수 (DCF per share 계산용).

    Returns:
        ScenarioSimulation — 3개 시나리오 ProForma + 분기 목표 + DCF.
    """
    # 성장률 경로 생성
    if isinstance(revenueGrowth, (int, float)):
        g = float(revenueGrowth)
        growthPath = [g, g * 0.7, g * 0.5]  # 3년 수렴
    else:
        growthPath = list(revenueGrowth)

    # series 추출 + 시간 필터
    ts = company.finance.timeseries
    fullSeries = ts[0] if isinstance(ts, tuple) else ts
    periods = ts[1] if isinstance(ts, tuple) else []

    cutoff = f"{baseYear}-Q4"
    cutIdx = periods.index(cutoff) + 1 if cutoff in periods else len(periods)
    series = {stmt: {k: v[:cutIdx] for k, v in fullSeries[stmt].items()} for stmt in ["IS", "BS", "CF"]}

    # 과거 비율 + 기준연도 비율
    ratios = extract_historical_ratios(series)
    is_df = company.IS

    rev_base = sum(_quarterlyValues(is_df, "sales", baseYear))
    gp_base = sum(_quarterlyValues(is_df, "gross_profit", baseYear))
    oi_base = sum(_quarterlyValues(is_df, "operating_profit", baseYear))

    baseGM = gp_base / rev_base * 100 if rev_base else ratios.gross_margin
    baseOpMargin = oi_base / rev_base * 100 if rev_base else 0

    # GM이 0인 경우 (서비스업 등 매출총이익 미보고) → 과거 비율 전적 의존
    if baseGM < 1.0 and ratios.gross_margin > 5.0:
        baseGM = ratios.gross_margin

    # 마진 블렌딩 가중치
    hw = _blendWeight(baseOpMargin)
    blendedGM = baseGM * (1 - hw) + ratios.gross_margin * hw

    # 3개 시나리오 ProForma
    scenarioDefs = [
        ("bull", [g * bullSpread if g > 0 else g * (1 / bullSpread) for g in growthPath], blendedGM + 2),
        ("base", growthPath, blendedGM),
        ("bear", [g * bearSpread if g > 0 else g * (1 / bearSpread) for g in growthPath], blendedGM - 2),
    ]

    pfResults: dict[str, ProFormaResult] = {}
    for scName, path, gm in scenarioDefs:
        combinedOverrides = {"gross_margin": gm}
        if overrides:
            combinedOverrides.update(overrides)
        try:
            pf = build_proforma(
                series,
                revenue_growth_path=path,
                scenario_name=scName,
                shares=shares,
                overrides=combinedOverrides,
            )
            if pf.projections:
                pfResults[scName] = pf
        except (KeyError, ValueError, ZeroDivisionError, TypeError):
            pass

    if "base" not in pfResults:
        msg = f"{baseYear} 데이터로 ProForma 생성 실패"
        raise ValueError(msg)

    # 계절성 분해
    seasonYears = [str(int(baseYear) - i) for i in range(3) if int(baseYear) - i >= 2019]
    revW = _computeSeasonality(is_df, "sales", seasonYears)
    oiW = _computeSeasonality(is_df, "operating_profit", seasonYears)

    # 분기 목표
    qRevTargets: dict[str, list[float]] = {}
    qOiTargets: dict[str, list[float]] = {}
    for sc, pf in pfResults.items():
        p = pf.projections[0]
        qRevTargets[sc] = [p.revenue * w for w in revW]
        qOiTargets[sc] = [p.operating_income * w for w in oiW]

    # DCF
    dcfValues: dict[str, int] = {}
    if shares and shares > 0:
        for sc, pf in pfResults.items():
            p1 = pf.projections[0]
            netDebt = (p1.short_term_debt + p1.long_term_debt) - p1.cash
            dcfValues[sc] = _scenarioDCF(pf.projections, pf.wacc, netDebt, shares)

    sim = ScenarioSimulation(
        stockCode=company.stockCode,
        companyName=getattr(company, "name", company.stockCode),
        scenarioName=scenarioName,
        baseYear=baseYear,
        targetYear=targetYear,
        revenueGrowthPath=growthPath,
        marginBlendWeight=hw,
        proformaResults=pfResults,
        quarterlyRevTargets=qRevTargets,
        quarterlyOITargets=qOiTargets,
        dcfPerShare=dcfValues,
        revSeasonality=revW,
        oiSeasonality=oiW,
    )

    return sim


def judgeQuarter(
    simulation: ScenarioSimulation,
    quarter: str,
    actualRevenue: float,
    actualOI: float,
) -> QuarterJudgment:
    """분기 실적 판정.

    Args:
        simulation: createSimulation()으로 생성한 시뮬레이션.
        quarter: 분기 식별자 ("2025Q1").
        actualRevenue: 실제 매출.
        actualOI: 실제 영업이익.

    Returns:
        QuarterJudgment — 판정 + 행동 + 재예측.
    """
    qIdx = int(quarter[-1]) - 1  # Q1=0, Q2=1, ...

    # 목표값
    bullRev = simulation.quarterlyRevTargets.get("bull", [0] * 4)[qIdx]
    baseRev = simulation.quarterlyRevTargets["base"][qIdx]
    bearRev = simulation.quarterlyRevTargets.get("bear", [0] * 4)[qIdx]

    bullOI = simulation.quarterlyOITargets.get("bull", [0] * 4)[qIdx]
    baseOI = simulation.quarterlyOITargets["base"][qIdx]
    bearOI = simulation.quarterlyOITargets.get("bear", [0] * 4)[qIdx]

    # 판정
    revPath = _judgePath(actualRevenue, bullRev, baseRev, bearRev)
    oiPath = _judgePath(actualOI, bullOI, baseOI, bearOI)

    revDev = (actualRevenue - baseRev) / abs(baseRev) * 100 if baseRev else 0
    oiDev = (actualOI - baseOI) / abs(baseOI) * 100 if baseOI else 0

    # 행동
    action, reason = _decideAction(revPath, oiPath, simulation.judgments)

    # 재예측 (단순: YTD 실적 + 남은 분기 원래 목표)
    allActualsRev = [j.actualRevenue for j in simulation.judgments] + [actualRevenue]
    allActualsOI = [j.actualOI for j in simulation.judgments] + [actualOI]
    remainRevTargets = simulation.quarterlyRevTargets["base"][qIdx + 1 :]
    remainOITargets = simulation.quarterlyOITargets["base"][qIdx + 1 :]
    reforecastRev = sum(allActualsRev) + sum(remainRevTargets)
    reforecastOI = sum(allActualsOI) + sum(remainOITargets)

    judgment = QuarterJudgment(
        quarter=quarter,
        actualRevenue=actualRevenue,
        actualOI=actualOI,
        targetRevBase=baseRev,
        targetOIBase=baseOI,
        revDeviation=round(revDev, 1),
        oiDeviation=round(oiDev, 1),
        revPath=revPath,
        oiPath=oiPath,
        action=action,
        reason=reason,
        reforecastRevenue=reforecastRev,
        reforecastOI=reforecastOI,
    )

    simulation.judgments.append(judgment)
    return judgment
