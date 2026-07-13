"""Concept proof for an auditable multi-step strategy simulator.

This module deliberately contains no DartLab imports.  It proves the execution
contract before the capability can graduate into ``src/dartlab/simulate``.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Callable, Mapping

ROLE_SET = {"state", "metric", "shock"}
EVIDENCE_SET = {
    "accountingIdentity",
    "measuredAssociation",
    "identifiedIntervention",
    "explicitAssumption",
}
WEIGHT_KIND_SET = {"unweighted", "empirical", "calibrated", "subjective"}


class SimulationSpecError(ValueError):
    """Raised when a world, strategy, or objective contract is malformed."""


class SimulationBlocked(RuntimeError):
    """Raised when a required value is missing instead of silently using zero."""


@dataclass(frozen=True)
class VariableSpec:
    """상태, 충격, 결과 변수의 식별자와 단위 및 허용범위를 선언한다."""

    variableId: str
    unit: str
    role: str
    lower: float | None = None
    upper: float | None = None


@dataclass(frozen=True)
class ActionSpec:
    """행동의 범위, 지연, 직접비용, 효과 근거를 선언한다."""

    actionId: str
    unit: str
    lower: float
    upper: float
    leadSteps: int
    costPerUnit: float
    effectEvidence: str
    provenance: str


@dataclass(frozen=True)
class StepContext:
    """전이 법칙이 읽을 수 있는 현재와 과거 정보만 제공한다."""

    step: int
    prior: Mapping[str, float]
    current: Mapping[str, float]
    shocks: Mapping[str, float]
    issuedActions: Mapping[str, float]
    actions: Mapping[str, float]
    actionCost: float


LawFn = Callable[[StepContext], Mapping[str, float]]


@dataclass(frozen=True)
class LawSpec:
    """한 기간 전이 법칙의 입력, 출력, 근거, 버전을 선언한다."""

    lawId: str
    outputs: tuple[str, ...]
    priorInputs: tuple[str, ...] = ()
    currentInputs: tuple[str, ...] = ()
    shockInputs: tuple[str, ...] = ()
    actionInputs: tuple[str, ...] = ()
    usesActionCost: bool = False
    evidenceKind: str = "explicitAssumption"
    provenance: str = ""
    version: str = "1"
    status: str = "active"
    fn: LawFn = field(default=lambda _: {}, repr=False, compare=False)


@dataclass(frozen=True)
class WorldState:
    """특정 시점의 세계 값과 기준시점 및 근거를 보존한다."""

    values: Mapping[str, float | None]
    step: int = 0
    asOf: str = ""
    refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioPath:
    """기간별 외생 충격과 가중치 성격을 보존하는 세계 경로다."""

    pathId: str
    steps: tuple[Mapping[str, float | None], ...]
    weight: float | None = None
    weightKind: str = "unweighted"
    refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class StrategySpec:
    """미래 결과를 읽지 않는 기간별 행동 일정을 선언한다."""

    strategyId: str
    actionsByStep: tuple[Mapping[str, float], ...]
    refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConstraintSpec:
    """기간별 또는 최종 상태가 지켜야 할 명시적 임계조건을 선언한다."""

    metric: str
    operator: str
    threshold: float
    scope: str = "eachStep"


@dataclass(frozen=True)
class ObjectiveSpec:
    """전략 비교 지표와 집계 및 위험 선호를 명시한다."""

    metric: str
    reducer: str = "terminal"
    direction: str = "maximize"
    risk: str = "worst"
    tailFraction: float = 0.2


@dataclass(frozen=True)
class LawTrace:
    """한 법칙이 읽은 값과 만든 값 및 근거를 기록한다."""

    lawId: str
    inputs: Mapping[str, float]
    outputs: Mapping[str, float]
    evidenceKind: str
    provenance: str


@dataclass(frozen=True)
class StepTrace:
    """한 기간의 전이 전후 상태, 행동, 충격, 위반을 기록한다."""

    step: int
    before: Mapping[str, float]
    shocks: Mapping[str, float]
    issuedActions: Mapping[str, float]
    effectiveActions: Mapping[str, float]
    actionCost: float
    after: Mapping[str, float]
    laws: tuple[LawTrace, ...]
    breaches: tuple[str, ...]


@dataclass(frozen=True)
class PathTrace:
    """한 전략과 세계 경로 조합의 전체 기간 전이를 기록한다."""

    strategyId: str
    pathId: str
    initial: Mapping[str, float]
    steps: tuple[StepTrace, ...]
    status: str
    reason: str | None = None


@dataclass(frozen=True)
class StrategyEvaluation:
    """전략별 목적값, 경로값, 제약 위반 여부를 집계한다."""

    strategyId: str
    objectiveScores: tuple[float, ...]
    pathValues: tuple[tuple[float, ...], ...]
    breachCount: int
    feasible: bool


@dataclass(frozen=True)
class SimulationRun:
    """재현 해시와 전략 비교 결과 및 전체 감사 추적을 반환한다."""

    runHash: str
    status: str
    decisionStatus: str
    weightLabel: str
    recommendation: str | None
    paretoStrategies: tuple[str, ...]
    evaluations: tuple[StrategyEvaluation, ...]
    traces: tuple[PathTrace, ...]
    warnings: tuple[str, ...]


def _finite(value: float | None, label: str) -> float:
    if value is None:
        raise SimulationBlocked(f"{label} is missing")
    number = float(value)
    if not math.isfinite(number):
        raise SimulationBlocked(f"{label} is not finite")
    return number


def _canonical(value):
    if callable(value):
        return None
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items()) if k != "fn"}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    return value


def _stableHash(payload: Mapping) -> str:
    raw = json.dumps(_canonical(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class WorldModel:
    """변수와 행동 및 전이 법칙을 검증하고 실행 순서로 컴파일한다."""

    modelId: str
    version: str
    variables: tuple[VariableSpec, ...]
    actions: tuple[ActionSpec, ...]
    laws: tuple[LawSpec, ...]
    _orderedLaws: tuple[LawSpec, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        variables = {v.variableId: v for v in self.variables}
        if len(variables) != len(self.variables):
            raise SimulationSpecError("duplicate variableId")
        actions = {a.actionId: a for a in self.actions}
        if len(actions) != len(self.actions):
            raise SimulationSpecError("duplicate actionId")
        for variable in self.variables:
            if variable.role not in ROLE_SET:
                raise SimulationSpecError(f"unknown variable role: {variable.role}")
            if variable.lower is not None and variable.upper is not None and variable.lower > variable.upper:
                raise SimulationSpecError(f"invalid bounds: {variable.variableId}")
        for action in self.actions:
            if action.effectEvidence not in EVIDENCE_SET:
                raise SimulationSpecError(f"unknown action evidence: {action.effectEvidence}")
            if action.lower > action.upper or action.leadSteps < 0 or action.costPerUnit < 0:
                raise SimulationSpecError(f"invalid action contract: {action.actionId}")

        producer: dict[str, str] = {}
        byId: dict[str, LawSpec] = {}
        for law in self.laws:
            if law.lawId in byId:
                raise SimulationSpecError("duplicate lawId")
            byId[law.lawId] = law
            if law.evidenceKind not in EVIDENCE_SET or law.status not in {"active", "partial", "blocked"}:
                raise SimulationSpecError(f"invalid law certificate: {law.lawId}")
            declared = law.priorInputs + law.currentInputs + law.shockInputs
            if len(set(declared)) != len(declared):
                raise SimulationSpecError(f"ambiguous law input: {law.lawId}")
            for name in law.priorInputs + law.currentInputs + law.outputs:
                if name not in variables:
                    raise SimulationSpecError(f"unknown variable {name}: {law.lawId}")
            for name in law.shockInputs:
                if name not in variables or variables[name].role != "shock":
                    raise SimulationSpecError(f"unknown shock {name}: {law.lawId}")
            for name in law.actionInputs:
                if name not in actions:
                    raise SimulationSpecError(f"unknown action {name}: {law.lawId}")
            for output in law.outputs:
                if output in producer:
                    raise SimulationSpecError(f"duplicate output producer: {output}")
                if variables[output].role == "shock":
                    raise SimulationSpecError(f"law cannot produce shock: {output}")
                producer[output] = law.lawId

        if any(a.costPerUnit > 0 for a in self.actions) and not any(law.usesActionCost for law in self.laws):
            raise SimulationSpecError("action cost has no consuming law")

        dependencies: dict[str, set[str]] = {law.lawId: set() for law in self.laws}
        for law in self.laws:
            for name in law.currentInputs:
                parent = producer.get(name)
                if parent is None:
                    raise SimulationSpecError(f"current input has no producer: {name}")
                if parent == law.lawId:
                    raise SimulationSpecError(f"self cycle: {law.lawId}")
                dependencies[law.lawId].add(parent)

        ordered: list[LawSpec] = []
        ready = sorted(k for k, deps in dependencies.items() if not deps)
        while ready:
            lawId = ready.pop(0)
            ordered.append(byId[lawId])
            for child, deps in dependencies.items():
                if lawId in deps:
                    deps.remove(lawId)
                    if not deps and byId[child] not in ordered and child not in ready:
                        ready.append(child)
                        ready.sort()
        if len(ordered) != len(self.laws):
            raise SimulationSpecError("current-step law cycle")
        object.__setattr__(self, "_orderedLaws", tuple(ordered))


def _validateValue(model: WorldModel, variableId: str, value: float | None, label: str) -> float:
    number = _finite(value, label)
    spec = next(v for v in model.variables if v.variableId == variableId)
    if spec.lower is not None and number < spec.lower - 1e-12:
        raise SimulationBlocked(f"{label} below lower bound")
    if spec.upper is not None and number > spec.upper + 1e-12:
        raise SimulationBlocked(f"{label} above upper bound")
    return number


def _checkInputs(
    model: WorldModel,
    initial: WorldState,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
) -> int:
    if not paths or not strategies:
        raise SimulationSpecError("at least one path and strategy are required")
    horizon = len(paths[0].steps)
    if horizon < 1 or any(len(path.steps) != horizon for path in paths):
        raise SimulationSpecError("all paths must share a positive horizon")
    if any(len(strategy.actionsByStep) != horizon for strategy in strategies):
        raise SimulationSpecError("all strategies must share the path horizon")
    if len({p.pathId for p in paths}) != len(paths) or len({s.strategyId for s in strategies}) != len(strategies):
        raise SimulationSpecError("duplicate pathId or strategyId")
    actionIds = {a.actionId for a in model.actions}
    shockIds = {v.variableId for v in model.variables if v.role == "shock"}
    requiredInitial = {name for law in model.laws for name in law.priorInputs}
    for name in requiredInitial:
        _validateValue(model, name, initial.values.get(name), f"initial.{name}")
    for path in paths:
        if path.weightKind not in WEIGHT_KIND_SET:
            raise SimulationSpecError(f"unknown weight kind: {path.weightKind}")
        if path.weightKind == "unweighted" and path.weight is not None:
            raise SimulationSpecError("unweighted path cannot carry a weight")
        if path.weightKind != "unweighted" and (path.weight is None or path.weight <= 0):
            raise SimulationSpecError("weighted path needs a positive weight")
        for step, shocks in enumerate(path.steps):
            if set(shocks) != shockIds:
                missing = sorted(shockIds - set(shocks))
                raise SimulationBlocked(f"path {path.pathId} step {step} missing shocks: {missing}")
            for name, value in shocks.items():
                _validateValue(model, name, value, f"path.{path.pathId}.{step}.{name}")
    actionById = {a.actionId: a for a in model.actions}
    for strategy in strategies:
        for step, issued in enumerate(strategy.actionsByStep):
            if set(issued) != actionIds:
                missing = sorted(actionIds - set(issued))
                raise SimulationSpecError(f"strategy {strategy.strategyId} step {step} missing actions: {missing}")
            for name, value in issued.items():
                action = actionById[name]
                number = _finite(value, f"strategy.{strategy.strategyId}.{step}.{name}")
                if number < action.lower - 1e-12 or number > action.upper + 1e-12:
                    raise SimulationSpecError(f"action outside bounds: {name}")
    return horizon


def _constraintBreaches(
    constraints: tuple[ConstraintSpec, ...], values: Mapping[str, float], scope: str
) -> tuple[str, ...]:
    out: list[str] = []
    for spec in constraints:
        if spec.scope != scope:
            continue
        if spec.metric not in values:
            raise SimulationBlocked(f"constraint metric missing: {spec.metric}")
        value = values[spec.metric]
        if spec.operator == "ge":
            breached = value < spec.threshold
        elif spec.operator == "le":
            breached = value > spec.threshold
        else:
            raise SimulationSpecError(f"unknown constraint operator: {spec.operator}")
        if breached:
            out.append(f"{spec.metric}:{spec.operator}:{spec.threshold}")
    return tuple(out)


def _pathMetric(trace: PathTrace, objective: ObjectiveSpec) -> float:
    values = [step.after[objective.metric] for step in trace.steps]
    if objective.reducer == "terminal":
        value = values[-1]
    elif objective.reducer == "minimum":
        value = min(values)
    elif objective.reducer == "maximum":
        value = max(values)
    elif objective.reducer == "cumulative":
        value = sum(values)
    else:
        raise SimulationSpecError(f"unknown objective reducer: {objective.reducer}")
    if objective.direction == "maximize":
        return value
    if objective.direction == "minimize":
        return -value
    raise SimulationSpecError(f"unknown objective direction: {objective.direction}")


def _aggregate(values: list[float], weights: list[float], objective: ObjectiveSpec) -> float:
    if objective.risk == "worst":
        return min(values)
    if objective.risk == "average":
        total = sum(weights)
        return sum(value * weight for value, weight in zip(values, weights, strict=True)) / total
    if objective.risk == "cvar":
        if not 0 < objective.tailFraction <= 1:
            raise SimulationSpecError("tailFraction must be in (0, 1]")
        ordered = sorted(zip(values, weights, strict=True), key=lambda pair: pair[0])
        target = sum(weights) * objective.tailFraction
        used = 0.0
        total = 0.0
        for value, weight in ordered:
            take = min(weight, target - used)
            if take > 0:
                total += value * take
                used += take
            if used >= target - 1e-12:
                break
        return total / used
    raise SimulationSpecError(f"unknown objective risk: {objective.risk}")


def _pareto(evaluations: tuple[StrategyEvaluation, ...]) -> tuple[str, ...]:
    feasible = [evaluation for evaluation in evaluations if evaluation.feasible]
    frontier: list[str] = []
    for candidate in feasible:
        dominated = False
        for other in feasible:
            if other.strategyId == candidate.strategyId:
                continue
            noWorse = all(a >= b - 1e-12 for a, b in zip(other.objectiveScores, candidate.objectiveScores, strict=True))
            better = any(a > b + 1e-12 for a, b in zip(other.objectiveScores, candidate.objectiveScores, strict=True))
            if noWorse and better:
                dominated = True
                break
        if not dominated:
            frontier.append(candidate.strategyId)
    return tuple(sorted(frontier))


def simulateWorld(
    model: WorldModel,
    initial: WorldState,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
    *,
    constraints: tuple[ConstraintSpec, ...] = (),
    objectives: tuple[ObjectiveSpec, ...] = (),
) -> SimulationRun:
    """Evolve every strategy over the same explicit world paths.

    Strategies contain schedules only.  They receive no path object or future
    outcome, which makes look-ahead unavailable by construction in this slice.
    """

    horizon = _checkInputs(model, initial, paths, strategies)
    variableIds = {variable.variableId for variable in model.variables}
    for objective in objectives:
        if objective.metric not in variableIds:
            raise SimulationSpecError(f"unknown objective metric: {objective.metric}")
    for constraint in constraints:
        if constraint.metric not in variableIds or constraint.scope not in {"eachStep", "terminal"}:
            raise SimulationSpecError(f"invalid constraint: {constraint.metric}")

    actionById = {action.actionId: action for action in model.actions}
    traces: list[PathTrace] = []
    for strategy in strategies:
        for path in paths:
            prior = {name: _finite(value, f"initial.{name}") for name, value in initial.values.items()}
            stepTraces: list[StepTrace] = []
            for step in range(horizon):
                issued = {name: float(value) for name, value in strategy.actionsByStep[step].items()}
                effective: dict[str, float] = {}
                for actionId, action in actionById.items():
                    sourceStep = step - action.leadSteps
                    effective[actionId] = (
                        float(strategy.actionsByStep[sourceStep][actionId]) if sourceStep >= 0 else 0.0
                    )
                actionCost = sum(abs(issued[name]) * actionById[name].costPerUnit for name in issued)
                shocks = {
                    name: _finite(value, f"path.{path.pathId}.{step}.{name}")
                    for name, value in path.steps[step].items()
                }
                current: dict[str, float] = {}
                lawTraces: list[LawTrace] = []
                for law in model._orderedLaws:
                    if law.status == "blocked":
                        raise SimulationBlocked(f"law blocked: {law.lawId}")
                    inputValues: dict[str, float] = {}
                    for name in law.priorInputs:
                        inputValues[f"prior.{name}"] = _finite(prior.get(name), f"{law.lawId}.prior.{name}")
                    for name in law.currentInputs:
                        inputValues[f"current.{name}"] = _finite(current.get(name), f"{law.lawId}.current.{name}")
                    for name in law.shockInputs:
                        inputValues[f"shock.{name}"] = _finite(shocks.get(name), f"{law.lawId}.shock.{name}")
                    for name in law.actionInputs:
                        inputValues[f"action.{name}"] = _finite(effective.get(name), f"{law.lawId}.action.{name}")
                    if law.usesActionCost:
                        inputValues["actionCost"] = actionCost
                    ctx = StepContext(
                        step=step,
                        prior=prior,
                        current=current,
                        shocks=shocks,
                        issuedActions=issued,
                        actions=effective,
                        actionCost=actionCost,
                    )
                    produced = dict(law.fn(ctx))
                    if set(produced) != set(law.outputs):
                        raise SimulationBlocked(f"law output mismatch: {law.lawId}")
                    clean = {
                        name: _validateValue(model, name, value, f"{law.lawId}.output.{name}")
                        for name, value in produced.items()
                    }
                    current.update(clean)
                    lawTraces.append(
                        LawTrace(
                            lawId=law.lawId,
                            inputs=inputValues,
                            outputs=clean,
                            evidenceKind=law.evidenceKind,
                            provenance=law.provenance,
                        )
                    )
                after = dict(prior)
                after.update(current)
                breaches = _constraintBreaches(constraints, after, "eachStep")
                if step == horizon - 1:
                    breaches += _constraintBreaches(constraints, after, "terminal")
                stepTraces.append(
                    StepTrace(
                        step=step,
                        before=dict(prior),
                        shocks=shocks,
                        issuedActions=issued,
                        effectiveActions=effective,
                        actionCost=actionCost,
                        after=after,
                        laws=tuple(lawTraces),
                        breaches=breaches,
                    )
                )
                prior = after
            traces.append(
                PathTrace(
                    strategyId=strategy.strategyId,
                    pathId=path.pathId,
                    initial={name: _finite(value, f"initial.{name}") for name, value in initial.values.items()},
                    steps=tuple(stepTraces),
                    status="ok",
                )
            )

    weights = [1.0 if path.weight is None else float(path.weight) for path in paths]
    evaluations: list[StrategyEvaluation] = []
    for strategy in strategies:
        strategyTraces = [trace for trace in traces if trace.strategyId == strategy.strategyId]
        objectivePathValues: list[tuple[float, ...]] = []
        objectiveScores: list[float] = []
        for objective in objectives:
            values = tuple(_pathMetric(trace, objective) for trace in strategyTraces)
            objectivePathValues.append(values)
            objectiveScores.append(_aggregate(list(values), weights, objective))
        breachCount = sum(len(step.breaches) for trace in strategyTraces for step in trace.steps)
        evaluations.append(
            StrategyEvaluation(
                strategyId=strategy.strategyId,
                objectiveScores=tuple(objectiveScores),
                pathValues=tuple(objectivePathValues),
                breachCount=breachCount,
                feasible=breachCount == 0,
            )
        )

    unqualifiedLaws = [law.lawId for law in model.laws if law.status != "active"]
    actionLaws = [law for law in model.laws if law.actionInputs]
    assumedLaws = [law.lawId for law in model.laws if law.evidenceKind == "explicitAssumption"]
    assumedActions = [
        action.actionId
        for action in model.actions
        if action.effectEvidence not in {"identifiedIntervention", "accountingIdentity"}
    ]
    assumedActionLaws = [
        law.lawId for law in actionLaws if law.evidenceKind not in {"identifiedIntervention", "accountingIdentity"}
    ]
    warnings: list[str] = []
    if unqualifiedLaws:
        warnings.append(f"unqualified laws: {','.join(unqualifiedLaws)}")
    if assumedLaws or assumedActions or assumedActionLaws:
        warnings.append("unvalidated transition or intervention effects are conditional assumptions")
    if not objectives:
        decisionStatus = "abstain"
        warnings.append("no objective was declared")
    elif unqualifiedLaws or assumedLaws or assumedActions or assumedActionLaws:
        decisionStatus = "conditionalOnly"
    else:
        decisionStatus = "comparable"

    evaluationTuple = tuple(evaluations)
    pareto = _pareto(evaluationTuple) if objectives else ()
    recommendation: str | None = None
    if decisionStatus == "comparable" and objectives:
        feasible = [evaluation for evaluation in evaluations if evaluation.feasible]
        if feasible:
            best = max(evaluation.objectiveScores[0] for evaluation in feasible)
            winners = [
                evaluation.strategyId for evaluation in feasible if abs(evaluation.objectiveScores[0] - best) <= 1e-12
            ]
            if len(winners) == 1 and winners[0] in pareto:
                recommendation = winners[0]

    weightKinds = {path.weightKind for path in paths}
    if weightKinds == {"calibrated"}:
        weightLabel = "calibratedProbability"
    elif weightKinds == {"empirical"}:
        weightLabel = "empiricalFrequency"
    elif weightKinds == {"unweighted"}:
        weightLabel = "scenarioCoverage"
    else:
        weightLabel = "subjectiveScenarioWeight"
    payload = {
        "model": model,
        "initial": initial,
        "paths": paths,
        "strategies": strategies,
        "constraints": constraints,
        "objectives": objectives,
    }
    return SimulationRun(
        runHash=_stableHash(payload),
        status="partial" if unqualifiedLaws else "ok",
        decisionStatus=decisionStatus,
        weightLabel=weightLabel,
        recommendation=recommendation,
        paretoStrategies=pareto,
        evaluations=evaluationTuple,
        traces=tuple(traces),
        warnings=tuple(warnings),
    )
