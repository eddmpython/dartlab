"""One-company conditional strategy comparison across the KR macro presets (the `strategies` axis).

The public simulate verb has two axes. `scenario` evaluates the deterministic driver sheet for one
preset. `strategies` asks a different question: given the company's current financial state, which
of a few financial strategies holds up best under each preset, where does the leader flip, and
which preset leaves the decision closest to flipping.

It reuses the audited internals instead of adding a parallel model:

    buildSnapshot (read once)
      -> financialInputsFromSnapshot   company state + historical ratios
      -> preset GDP / rate / FX path   one annual macro path per KR preset
      -> bridgeFinancialPaths          demand growth, margin change and debt rate per year, using
                                       the same sector elasticities as the scenario axis
      -> runFinancialStrategies        every strategy on the same path, accounting closed each year

Nothing here is a recommendation. The bridge coefficients and the strategies are explicit
assumptions and no policy evaluation certificate exists, so every result is ``conditionalOnly`` with
``recommendation`` None and the blocked reasons say why. The case leader is the feasible strategy
with the highest terminal net cash; the Pareto set over net cash and debt is reported next to it.

Layer: L3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from dartlab.analysis.financial.proforma import extractHistoricalRatios
from dartlab.simulate.financialBridge import bridgeFinancialPaths, buildFinancialBridgeLaw
from dartlab.simulate.financialWorld import (
    FinancialWorldInputs,
    buildFinancialStrategy,
    financialInputsFromSnapshot,
    runFinancialStrategies,
)
from dartlab.simulate.registry import buildSnapshot, validateScenarioSpec
from dartlab.simulate.world import ScenarioPath, SimulationBlocked, SimulationRun, StrategySpec
from dartlab.synth.scenario import BASELINE_FX, BASELINE_RATE, getPresetScenarios

STRATEGY_COMPARISON_VERSION = "company-strategy-comparison-v1"
# The presets and elasticities are KR baselines, and the public verb is KR-only.
_PRESET_MARKET = "KR"
# Explicit capacity slack over observed revenue. Without it latent demand could never exceed capacity.
_CAPACITY_HEADROOM = 0.20
# The expansion strategy invests this multiple of maintenance capex.
_EXPANSION_MULTIPLE = 1.5
# The deleverage strategy repays this share of today's debt, spread evenly over the horizon.
_DELEVERAGE_SHARE = 0.5
_BLOCKED_REASONS = (
    "bridgeCoefficientsAreExplicitAssumptions",
    "strategiesAreExplicitAssumptions",
    "policyEvaluationCertificateMissing",
    "caseLeaderIsNotRecommendation",
)


@dataclass(frozen=True)
class StrategyDefinition:
    """비교에 쓴 전략 하나의 행동 계획. 모든 값은 회사의 현재 상태에서 정한 명시 가정이다."""

    strategyId: str
    description: str
    capexRatio: float
    inventoryRatio: float
    repayPerStep: float
    isBaseline: bool


@dataclass(frozen=True)
class StrategyOutcome:
    """시나리오 하나에서 전략 하나의 마지막 해 상태와 제약 위반. 값이 없으면 None 이다."""

    strategyId: str
    terminalNetCash: float | None
    terminalDebt: float | None
    terminalRevenue: float | None
    breachCount: int
    feasible: bool


@dataclass(frozen=True)
class StrategyCase:
    """시나리오 하나의 공통 경로 위에서 모든 전략을 굴린 결과."""

    scenarioName: str
    leaderStrategyId: str | None
    leaderMargin: float | None
    leaderMarginRatio: float | None
    paretoStrategies: tuple[str, ...]
    outcomes: tuple[StrategyOutcome, ...]
    shockPath: tuple[dict[str, float], ...]
    decisionStatus: str
    runHash: str


@dataclass(frozen=True)
class StrategyComparison:
    """한 회사의 조건부 전략 비교 결과. 추천이 아니라 명시 가정 아래의 비교다.

    Fields:
        stockCode         : 비교한 회사.
        horizon           : 연 단위 전개 기간.
        asOf / latestAsOf : 초기 상태의 재무 기준 기간과 최신 가용 기간.
        strategies        : 비교한 전략 정의.
        cases             : 프리셋마다 하나. 리더, 리더 격차, Pareto 집합, 전략별 결과.
        leaderByCase      : 프리셋 이름 -> 리더 전략 (없으면 None).
        leaderReversal    : 프리셋에 따라 리더가 달라지면 True.
        stableLeader      : 모든 프리셋에서 같은 전략이 리더일 때 그 전략.
        reversalCases     : baseline 과 리더가 다른 프리셋.
        fragileCase       : 리더 격차가 매출 대비 가장 작은 프리셋. 결정이 가장 쉽게 뒤집히는 곳.
        quality           : 데이터 결손이나 기권 없이 모든 프리셋이 리더를 냈으면 ``ok``.
        assumptions       : 결과를 조건 짓는 명시 가정.
        warnings          : 입력과 실행이 남긴 한계.
        gaps              : 비교를 할 수 없었던 사유. 있으면 cases 는 비어 있다.
        blockedReasons    : 추천이 닫혀 있는 이유.
        decisionStatus    : 항상 ``conditionalOnly``.
        recommendation    : 항상 None.
    """

    stockCode: str
    horizon: int
    asOf: str
    latestAsOf: str
    strategies: tuple[StrategyDefinition, ...]
    cases: tuple[StrategyCase, ...]
    leaderByCase: dict[str, str | None]
    leaderReversal: bool
    stableLeader: str | None
    reversalCases: tuple[str, ...]
    fragileCase: str | None
    quality: str
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
    gaps: tuple[str, ...]
    blockedReasons: tuple[str, ...] = _BLOCKED_REASONS
    decisionStatus: str = "conditionalOnly"
    recommendation: None = None
    schemaVersion: str = STRATEGY_COMPARISON_VERSION


def _dedupe(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _macroShockPath(name: str, horizon: int) -> ScenarioPath:
    """프리셋 하나를 연간 거시 혁신 경로로 바꾼다. 금리는 변화분과 기준 대비 편차를 함께 싣는다."""
    preset = getPresetScenarios(_PRESET_MARKET)[name]
    steps: list[dict[str, float]] = []
    previousRate = float(BASELINE_RATE)
    for year in range(horizon):
        rate = float(preset.interestRate[year])
        fx = float(preset.krwUsd[year])
        steps.append(
            {
                "gdpChange": float(preset.gdpGrowth[year]) / 100.0,
                "fxDeviation": (fx - BASELINE_FX) / BASELINE_FX,
                "rateChange": (rate - previousRate) / 100.0,
                "rateDeviation": (rate - BASELINE_RATE) / 100.0,
            }
        )
        previousRate = rate
    refs = (f"synth.scenario:PRESET_SCENARIOS_{_PRESET_MARKET}/{preset.name}",)
    return ScenarioPath(name, tuple(steps), refs=refs, frequency="year")


def _bridgeLaw(snapshot: dict, baseDebtRate: float):
    """시나리오 축과 같은 업종 탄성을 연간 재무 충격 계수로 옮긴 명시 가정 법칙."""
    elasticity = snapshot["elasticity"]
    return buildFinancialBridgeLaw(
        factorUnits={
            "gdpChange": "ratioChangePerYear",
            "fxDeviation": "ratioDeviationFromBaseline",
            "rateChange": "ratioChangePerYear",
            "rateDeviation": "ratioDeviationFromBaseline",
        },
        # revenueToGdp is a revenue multiplier per GDP point; revenueToFx is revenue % per 10% FX.
        demandLogCoefficients={
            "gdpChange": float(elasticity.revenueToGdp),
            "fxDeviation": float(elasticity.revenueToFx) / 10.0,
        },
        # marginToGdp and nimToRate are margin bps per point, so /100 turns them into ratio points.
        marginChangeCoefficients={
            "gdpChange": float(elasticity.marginToGdp) / 100.0,
            "rateDeviation": float(elasticity.nimToRate) / 100.0,
        },
        debtRateChangeCoefficients={"rateChange": 1.0},
        baseDebtRate=baseDebtRate,
        evidenceKind="explicitAssumption",
    )


def _baseDebtRate(series: dict) -> float:
    """과거 비율의 차입 이자율. [0, 1] 밖이면 추정이 깨진 것이라 계산 전에 막는다."""
    rate = float(extractHistoricalRatios(series).interest_rate_on_debt) / 100.0
    if not math.isfinite(rate) or rate < 0.0 or rate > 1.0:
        raise SimulationBlocked(f"historical debt rate is outside [0, 1]: {rate}")
    return rate


def _strategies(
    inputs: FinancialWorldInputs,
    horizon: int,
    maxFinancing: float,
) -> tuple[tuple[StrategyDefinition, ...], tuple[StrategySpec, ...]]:
    """현재 상태에서 유지, 증설, 부채 축소 세 전략을 정한다. 부채가 없으면 부채 축소는 뺀다."""
    state, params = inputs.state, inputs.parameters
    maintenance = min(0.25, max(0.01, params.depreciationRate * state.ppe / state.revenue))
    expansion = min(0.40, maintenance * _EXPANSION_MULTIPLE)
    inventoryRatio = state.inventories / state.revenue
    definitions = [
        StrategyDefinition(
            "hold",
            "유지 투자(감가상각만큼 capex), 재고 비율 유지, 차입과 상환 없음",
            maintenance,
            inventoryRatio,
            0.0,
            True,
        ),
        StrategyDefinition(
            "expand",
            f"증설 투자(유지 capex 의 {_EXPANSION_MULTIPLE:g}배), 재고 비율 유지, 차입과 상환 없음",
            expansion,
            inventoryRatio,
            0.0,
            False,
        ),
    ]
    if state.debt > 0:
        # Half the current debt over the horizon. Repaying all of it would put the last step's
        # repayment within rounding of the remaining balance, which the step leaf rejects.
        definitions.append(
            StrategyDefinition(
                "deleverage",
                f"유지 투자, 재고 비율 유지, 현재 부채의 {_DELEVERAGE_SHARE:.0%}를 기간에 나눠 상환",
                maintenance,
                inventoryRatio,
                min(state.debt * _DELEVERAGE_SHARE / horizon, maxFinancing),
                False,
            )
        )
    specs = tuple(
        buildFinancialStrategy(
            item.strategyId,
            capexRatio=(item.capexRatio,) * horizon,
            inventoryRatio=(item.inventoryRatio,) * horizon,
            borrow=(0.0,) * horizon,
            repay=(item.repayPerStep,) * horizon,
            refs=(f"strategyAssumption:{item.strategyId}",),
            isBaseline=item.isBaseline,
        )
        for item in definitions
    )
    return tuple(definitions), specs


def _outcomes(run: SimulationRun, order: tuple[str, ...]) -> tuple[StrategyOutcome, ...]:
    """전략별 마지막 해 상태. 경로가 중간에 막혀 기록이 없으면 값은 None, 실행 불가로 둔다."""
    evaluations = {item.strategyId: item for item in run.evaluations}
    traces = {trace.strategyId: trace for trace in run.traces}
    rows: list[StrategyOutcome] = []
    for strategyId in order:
        evaluation = evaluations[strategyId]
        trace = traces.get(strategyId)
        last = trace.steps[-1].after if trace is not None and trace.steps else None
        rows.append(
            StrategyOutcome(
                strategyId=strategyId,
                terminalNetCash=float(last["netCash"]) if last is not None else None,
                terminalDebt=float(last["debt"]) if last is not None else None,
                terminalRevenue=float(last["revenue"]) if last is not None else None,
                breachCount=int(evaluation.breachCount),
                feasible=bool(evaluation.feasible) and last is not None,
            )
        )
    return tuple(rows)


def _case(
    name: str,
    run: SimulationRun,
    path: ScenarioPath,
    order: tuple[str, ...],
    baseRevenue: float,
) -> StrategyCase:
    """한 프리셋의 리더와 리더 격차. 실행 가능한 전략이 둘 미만이면 격차는 None 이다."""
    outcomes = _outcomes(run, order)
    ranked = sorted(
        (item for item in outcomes if item.feasible and item.terminalNetCash is not None),
        key=lambda item: (-item.terminalNetCash, item.strategyId),
    )
    leader = ranked[0].strategyId if ranked else None
    margin = ranked[0].terminalNetCash - ranked[1].terminalNetCash if len(ranked) > 1 else None
    ratio = margin / baseRevenue if margin is not None and baseRevenue > 0 else None
    return StrategyCase(
        scenarioName=name,
        leaderStrategyId=leader,
        leaderMargin=margin,
        leaderMarginRatio=ratio,
        paretoStrategies=tuple(run.paretoStrategies),
        outcomes=outcomes,
        shockPath=tuple(dict(step) for step in path.steps),
        decisionStatus=run.decisionStatus,
        runHash=run.runHash,
    )


def _gapComparison(
    stockCode: str,
    horizon: int,
    snapshot: dict,
    assumptions: list[str],
    warnings: list[str],
    gap: str,
) -> StrategyComparison:
    return StrategyComparison(
        stockCode=stockCode,
        horizon=horizon,
        asOf=str(snapshot.get("asOf", "")),
        latestAsOf=str(snapshot.get("latestAsOf", "")),
        strategies=(),
        cases=(),
        leaderByCase={},
        leaderReversal=False,
        stableLeader=None,
        reversalCases=(),
        fragileCase=None,
        quality="partial",
        assumptions=_dedupe(assumptions),
        warnings=_dedupe(warnings),
        gaps=(gap,),
    )


def compareStrategies(company: Any, *, horizon: int = 3, asOf: str | None = None) -> StrategyComparison:
    """Compare a fixed set of financial strategies for one company across every KR macro preset.

    Capabilities:
        Compiles the company's current financial state once, bridges each KR preset into an annual
        demand / margin / debt-rate shock path with the scenario axis's sector elasticities, and
        runs hold, expand and deleverage on the same path per preset. Reports each preset's leader
        on terminal net cash, the margin to the runner-up, the Pareto set over net cash and debt,
        where the leader flips, and the preset closest to flipping.

    Args:
        company: a KR `Company`. Read once through `buildSnapshot`.
        horizon: annual steps. It cannot exceed the shortest preset path.
        asOf: optional fiscal period for the initial state (period-scoped PIT, as on the scenario
            axis). A historical period has no parameter vintage, so the comparison abstains.

    Returns:
        StrategyComparison: always ``conditionalOnly`` with ``recommendation`` None. When the
        state cannot be compiled the cases are empty and ``gaps`` names the reason.

    Raises:
        TypeError: if horizon has the wrong type.
        ValueError: if horizon is outside the preset paths or asOf is outside the data.

    Example:
        >>> comparison = compareStrategies(Company("005930"))  # doctest: +SKIP
        >>> comparison.leaderByCase["baseline"], comparison.fragileCase  # doctest: +SKIP
        ('hold', 'rate_hike')

    Guide:
        Read ``fragileCase`` and ``reversalCases`` before any leader: they say how much the answer
        depends on the macro assumption. The leader is a comparison under explicit assumptions.

    AIContext:
        Never present a case leader as advice. Quote the preset, the assumptions and the blocked
        reasons with it, and treat an empty ``cases`` as an honest gap, not as zero.
    """
    names = tuple(sorted(getPresetScenarios(_PRESET_MARKET)))
    for name in names:
        validateScenarioSpec(name, horizon)
    snapshot = buildSnapshot(company, asOf=asOf)
    stockCode = str(getattr(company, "stockCode", "") or "")
    assumptions = [f"snapshot:{item}" for item in snapshot.get("assumptions", ())]
    assumptions.extend(
        (
            f"capacityHeadroom:{_CAPACITY_HEADROOM:g}",
            "bridgeCoefficients:sectorElasticity",
            f"strategies:hold,expand{_EXPANSION_MULTIPLE:g}x,deleverage{_DELEVERAGE_SHARE:g}",
            "caseLeaderObjective:terminalNetCash",
        )
    )
    warnings = [f"snapshot:{item}" for item in snapshot.get("warnings", ())]
    if snapshot.get("parameterVintageStatus", "available") != "available":
        return _gapComparison(
            stockCode, horizon, snapshot, assumptions, warnings, "historical_parameter_vintage_absent"
        )
    try:
        inputs = financialInputsFromSnapshot(snapshot, capacityHeadroom=_CAPACITY_HEADROOM)
        baseDebtRate = _baseDebtRate(snapshot["series"])
    except SimulationBlocked as error:
        return _gapComparison(stockCode, horizon, snapshot, assumptions, warnings, str(error))
    assumptions.append(f"baseDebtRate:{baseDebtRate:.6g}")
    warnings.extend(inputs.warnings)

    law = _bridgeLaw(snapshot, baseDebtRate)
    maxFinancing = max(inputs.state.revenue * 0.2, 1.0)
    debtLimit = max(inputs.state.debt * 2.0, 1.0)
    definitions, specs = _strategies(inputs, horizon, maxFinancing)
    order = tuple(item.strategyId for item in definitions)
    cases: list[StrategyCase] = []
    for name in names:
        bridged = bridgeFinancialPaths((_macroShockPath(name, horizon),), law)
        warnings.extend(bridged.audit.warnings)
        path = bridged.paths[0]
        run = runFinancialStrategies(inputs, (path,), specs, debtLimit=debtLimit, maxFinancing=maxFinancing)
        warnings.extend(run.warnings)
        cases.append(_case(name, run, path, order, inputs.state.revenue))

    summary = summarizeCases(tuple(cases))
    dataLimited = any(item.startswith("snapshot:") for item in warnings)
    return StrategyComparison(
        stockCode=stockCode,
        horizon=horizon,
        asOf=str(snapshot.get("asOf", "")),
        latestAsOf=str(snapshot.get("latestAsOf", "")),
        strategies=definitions,
        cases=tuple(cases),
        leaderByCase=summary["leaderByCase"],
        leaderReversal=summary["leaderReversal"],
        stableLeader=summary["stableLeader"],
        reversalCases=summary["reversalCases"],
        fragileCase=summary["fragileCase"],
        quality="ok" if summary["allLed"] and not dataLimited else "partial",
        assumptions=_dedupe(assumptions),
        warnings=_dedupe(warnings),
        gaps=(),
    )


def summarizeCases(cases: tuple[StrategyCase, ...]) -> dict[str, Any]:
    """Summarize where the case leader holds, where it flips, and which case is closest to flipping.

    Args:
        cases: one `StrategyCase` per preset.

    Returns:
        dict: ``leaderByCase``, ``leaderReversal`` (more than one leader), ``stableLeader`` (the only
        leader when every case has one), ``reversalCases`` (cases whose leader differs from the
        ``baseline`` case), ``fragileCase`` (smallest leader margin relative to revenue, ties by
        name) and ``allLed``.

    Raises:
        None.

    Example:
        >>> summarizeCases(())["leaderReversal"]
        False
    """
    leaderByCase = {case.scenarioName: case.leaderStrategyId for case in cases}
    leaders = {leader for leader in leaderByCase.values() if leader is not None}
    allLed = bool(cases) and all(leader is not None for leader in leaderByCase.values())
    reversalCases: tuple[str, ...] = ()
    if "baseline" in leaderByCase:
        baselineLeader = leaderByCase["baseline"]
        reversalCases = tuple(name for name, leader in leaderByCase.items() if leader != baselineLeader)
    measured = [case for case in cases if case.leaderMarginRatio is not None]
    fragile = min(measured, key=lambda case: (case.leaderMarginRatio, case.scenarioName)) if measured else None
    return {
        "leaderByCase": leaderByCase,
        "leaderReversal": len(leaders) > 1,
        "stableLeader": next(iter(leaders)) if len(leaders) == 1 and allLed else None,
        "reversalCases": reversalCases,
        "fragileCase": fragile.scenarioName if fragile is not None else None,
        "allLed": allLed,
    }
