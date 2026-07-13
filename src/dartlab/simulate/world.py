"""Auditable multi-step world evolution and strategy comparison contracts."""

from __future__ import annotations

import json
import marshal
import math
from dataclasses import dataclass, field, fields
from hashlib import sha256
from types import MappingProxyType
from typing import Callable, Mapping

ROLE_SET = {"state", "metric", "shock"}
EVIDENCE_SET = {
    "accountingIdentity",
    "measuredAssociation",
    "identifiedIntervention",
    "explicitAssumption",
}
WEIGHT_KIND_SET = {"unweighted", "empirical", "resampled", "calibrated", "subjective"}
PATH_VALIDATION_SET = {"unvalidated", "retrospectiveOnly", "admitted", "rejected"}


class SimulationSpecError(ValueError):
    """Raised when a world, strategy, or objective contract is malformed."""


class SimulationBlocked(RuntimeError):
    """Raised when a required value is missing instead of silently using zero."""


def _freezeMapping(values: Mapping) -> Mapping:
    """Copy a mapping before exposing a read-only view of it."""

    return MappingProxyType(dict(values))


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value.lower())


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
    certificateId: str = ""


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
    certificateId: str = ""
    parameters: Mapping[str, float | str | bool] = field(default_factory=dict)
    fn: LawFn = field(default=lambda _: {}, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameters", _freezeMapping(self.parameters))


@dataclass(frozen=True)
class WorldState:
    """특정 시점의 세계 값과 기준시점 및 근거를 보존한다."""

    values: Mapping[str, float | None]
    step: int = 0
    asOf: str = ""
    refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _freezeMapping(self.values))
        object.__setattr__(self, "refs", tuple(self.refs))


@dataclass(frozen=True)
class ScenarioPath:
    """기간별 외생 충격과 가중치 성격을 보존하는 세계 경로다."""

    pathId: str
    steps: tuple[Mapping[str, float | None], ...]
    weight: float | None = None
    weightKind: str = "unweighted"
    refs: tuple[str, ...] = ()
    frequency: str = "step"
    stepSpan: int = 1
    certificateId: str = ""
    validationStatus: str = "unvalidated"
    maxAdmittedStep: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", tuple(_freezeMapping(step) for step in self.steps))
        object.__setattr__(self, "refs", tuple(self.refs))


@dataclass(frozen=True)
class StrategySpec:
    """미래 결과를 읽지 않는 기간별 행동 일정을 선언한다."""

    strategyId: str
    actionsByStep: tuple[Mapping[str, float], ...]
    refs: tuple[str, ...] = ()
    isBaseline: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "actionsByStep", tuple(_freezeMapping(step) for step in self.actionsByStep))
        object.__setattr__(self, "refs", tuple(self.refs))


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
    version: str
    parameters: Mapping[str, float | str | bool]

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", _freezeMapping(self.inputs))
        object.__setattr__(self, "outputs", _freezeMapping(self.outputs))
        object.__setattr__(self, "parameters", _freezeMapping(self.parameters))


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

    def __post_init__(self) -> None:
        for name in ("before", "shocks", "issuedActions", "effectiveActions", "after"):
            object.__setattr__(self, name, _freezeMapping(getattr(self, name)))
        object.__setattr__(self, "laws", tuple(self.laws))
        object.__setattr__(self, "breaches", tuple(self.breaches))


@dataclass(frozen=True)
class PathTrace:
    """한 전략과 세계 경로 조합의 전체 기간 전이를 기록한다."""

    strategyId: str
    pathId: str
    initial: Mapping[str, float]
    steps: tuple[StepTrace, ...]
    status: str
    reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial", _freezeMapping(self.initial))
        object.__setattr__(self, "steps", tuple(self.steps))


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
    executableHash: str
    parameterHash: str
    dataVintageHash: str
    resultHash: str
    traceRoot: str
    status: str
    decisionStatus: str
    weightLabel: str
    recommendation: str | None
    paretoStrategies: tuple[str, ...]
    evaluations: tuple[StrategyEvaluation, ...]
    traces: tuple[PathTrace, ...]
    constraints: tuple[ConstraintSpec, ...]
    objectives: tuple[ObjectiveSpec, ...]
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
        code = getattr(value, "__code__", None)
        closure = getattr(value, "__closure__", None) or ()
        closureNames = tuple(getattr(code, "co_freevars", ()))
        captured = {name: _canonical(cell.cell_contents) for name, cell in zip(closureNames, closure, strict=True)}
        return {
            "callable": f"{getattr(value, '__module__', '')}.{getattr(value, '__qualname__', '')}",
            "codeHash": sha256(marshal.dumps(code)).hexdigest() if code is not None else "",
            "defaults": _canonical(getattr(value, "__defaults__", None)),
            "kwdefaults": _canonical(getattr(value, "__kwdefaults__", None)),
            "closure": captured,
        }
    if hasattr(value, "__dataclass_fields__"):
        return {item.name: _canonical(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return {"bytesHash": sha256(value).hexdigest()}
    if hasattr(value, "__dict__"):
        return {
            "objectType": f"{type(value).__module__}.{type(value).__qualname__}",
            "state": _canonical(vars(value)),
        }
    return {"objectType": f"{type(value).__module__}.{type(value).__qualname__}"}


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
    stepFrequency: str = "step"
    stepSpan: int = 1
    _orderedLaws: tuple[LawSpec, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "actions", tuple(self.actions))
        object.__setattr__(self, "laws", tuple(self.laws))
        if not self.stepFrequency or self.stepSpan < 1:
            raise SimulationSpecError("invalid model step contract")
        variables = {v.variableId: v for v in self.variables}
        if len(variables) != len(self.variables):
            raise SimulationSpecError("duplicate variableId")
        actions = {a.actionId: a for a in self.actions}
        if len(actions) != len(self.actions):
            raise SimulationSpecError("duplicate actionId")
        for variable in self.variables:
            if variable.role not in ROLE_SET:
                raise SimulationSpecError(f"unknown variable role: {variable.role}")
            for bound in (variable.lower, variable.upper):
                if bound is not None and not math.isfinite(float(bound)):
                    raise SimulationSpecError(f"non-finite bounds: {variable.variableId}")
            if variable.lower is not None and variable.upper is not None and variable.lower > variable.upper:
                raise SimulationSpecError(f"invalid bounds: {variable.variableId}")
        for action in self.actions:
            if action.effectEvidence not in EVIDENCE_SET:
                raise SimulationSpecError(f"unknown action evidence: {action.effectEvidence}")
            numericContract = (action.lower, action.upper, action.costPerUnit)
            if (
                any(not math.isfinite(float(value)) for value in numericContract)
                or action.lower > action.upper
                or action.leadSteps < 0
                or action.costPerUnit < 0
            ):
                raise SimulationSpecError(f"invalid action contract: {action.actionId}")
            if action.effectEvidence == "identifiedIntervention" and not _validDigest(action.certificateId):
                raise SimulationSpecError(f"identified action needs a certificate: {action.actionId}")

        producer: dict[str, str] = {}
        byId: dict[str, LawSpec] = {}
        for law in self.laws:
            if law.lawId in byId:
                raise SimulationSpecError("duplicate lawId")
            byId[law.lawId] = law
            if law.evidenceKind not in EVIDENCE_SET or law.status not in {"active", "partial", "blocked"}:
                raise SimulationSpecError(f"invalid law certificate: {law.lawId}")
            if law.evidenceKind == "identifiedIntervention" and not _validDigest(law.certificateId):
                raise SimulationSpecError(f"identified law needs a certificate: {law.lawId}")
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
    if sum(strategy.isBaseline for strategy in strategies) > 1:
        raise SimulationSpecError("at most one baseline strategy is allowed")
    weightKinds = {path.weightKind for path in paths}
    if len(weightKinds) != 1:
        raise SimulationSpecError("all paths must share one weight interpretation")
    actionIds = {a.actionId for a in model.actions}
    shockIds = {v.variableId for v in model.variables if v.role == "shock"}
    requiredInitial = {name for law in model.laws for name in law.priorInputs}
    for name in requiredInitial:
        _validateValue(model, name, initial.values.get(name), f"initial.{name}")
    for path in paths:
        if path.weightKind not in WEIGHT_KIND_SET:
            raise SimulationSpecError(f"unknown weight kind: {path.weightKind}")
        if path.validationStatus not in PATH_VALIDATION_SET:
            raise SimulationSpecError(f"unknown path validation status: {path.validationStatus}")
        if path.validationStatus == "rejected":
            raise SimulationSpecError(f"rejected path cannot execute: {path.pathId}")
        if path.frequency != model.stepFrequency or path.stepSpan != model.stepSpan:
            raise SimulationSpecError(
                f"path step contract mismatch: {path.pathId} is {path.stepSpan} {path.frequency}, "
                f"model needs {model.stepSpan} {model.stepFrequency}"
            )
        if path.maxAdmittedStep < 0:
            raise SimulationSpecError(f"negative admitted horizon: {path.pathId}")
        if path.validationStatus == "admitted":
            if not _validDigest(path.certificateId):
                raise SimulationSpecError(f"admitted path needs a certificate: {path.pathId}")
            if path.maxAdmittedStep < horizon:
                raise SimulationSpecError(f"path exceeds admitted horizon: {path.pathId}")
        if path.weightKind == "unweighted" and path.weight is not None:
            raise SimulationSpecError("unweighted path cannot carry a weight")
        if path.weightKind != "unweighted":
            if path.weight is None or not math.isfinite(float(path.weight)) or path.weight <= 0:
                raise SimulationSpecError("weighted path needs a positive finite weight")
        if path.weightKind == "calibrated":
            if path.validationStatus != "admitted" or not _validDigest(path.certificateId):
                raise SimulationSpecError("calibrated paths need an admission certificate")
        for step, shocks in enumerate(path.steps):
            if set(shocks) != shockIds:
                missing = sorted(shockIds - set(shocks))
                raise SimulationBlocked(f"path {path.pathId} step {step} missing shocks: {missing}")
            for name, value in shocks.items():
                _validateValue(model, name, value, f"path.{path.pathId}.{step}.{name}")
    validationStatuses = {path.validationStatus for path in paths}
    if len(validationStatuses) != 1:
        raise SimulationSpecError("all paths must share one validation status")
    if validationStatuses == {"admitted"}:
        certificates = {path.certificateId for path in paths}
        admittedHorizons = {path.maxAdmittedStep for path in paths}
        if len(certificates) != 1 or len(admittedHorizons) != 1:
            raise SimulationSpecError("admitted paths must share one certificate and horizon")
    if weightKinds == {"calibrated"}:
        totalWeight = sum(float(path.weight) for path in paths if path.weight is not None)
        if abs(totalWeight - 1.0) > 1e-9:
            raise SimulationSpecError("calibrated path weights must sum to one")
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
    inputWarnings: tuple[str, ...] = (),
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
        if not math.isfinite(float(objective.tailFraction)):
            raise SimulationSpecError(f"non-finite objective contract: {objective.metric}")
    for constraint in constraints:
        if (
            constraint.metric not in variableIds
            or constraint.scope not in {"eachStep", "terminal"}
            or not math.isfinite(float(constraint.threshold))
        ):
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
                    lawPrior = {name: prior[name] for name in law.priorInputs}
                    lawCurrent = {name: current[name] for name in law.currentInputs}
                    lawShocks = {name: shocks[name] for name in law.shockInputs}
                    lawActions = {name: effective[name] for name in law.actionInputs}
                    ctx = StepContext(
                        step=step,
                        prior=_freezeMapping(lawPrior),
                        current=_freezeMapping(lawCurrent),
                        shocks=_freezeMapping(lawShocks),
                        issuedActions=_freezeMapping({}),
                        actions=_freezeMapping(lawActions),
                        actionCost=actionCost if law.usesActionCost else 0.0,
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
                            version=law.version,
                            parameters=law.parameters,
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
    pathAdmissionIssues = [path.pathId for path in paths if path.validationStatus != "admitted"]
    warnings: list[str] = list(inputWarnings)
    if unqualifiedLaws:
        warnings.append(f"unqualified laws: {','.join(unqualifiedLaws)}")
    if assumedLaws or assumedActions or assumedActionLaws:
        warnings.append("unvalidated transition or intervention effects are conditional assumptions")
    if pathAdmissionIssues:
        warnings.append(f"paths are not admitted: {','.join(pathAdmissionIssues)}")
    baselineIds = [strategy.strategyId for strategy in strategies if strategy.isBaseline]
    if objectives and (len(strategies) < 2 or not baselineIds):
        warnings.append("recommendation needs one baseline and at least one candidate")
    if not objectives:
        decisionStatus = "abstain"
        warnings.append("no objective was declared")
    elif unqualifiedLaws or assumedLaws or assumedActions or assumedActionLaws or pathAdmissionIssues:
        decisionStatus = "conditionalOnly"
    elif len(objectives) > 1:
        decisionStatus = "paretoOnly"
        warnings.append("multiple objectives have no declared scalarization")
    else:
        decisionStatus = "comparable"

    evaluationTuple = tuple(evaluations)
    pareto = _pareto(evaluationTuple) if objectives else ()
    recommendation: str | None = None
    if decisionStatus == "comparable" and len(objectives) == 1 and len(strategies) >= 2 and len(baselineIds) == 1:
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
        weightLabel = "calibratedScenarioMeasure"
    elif weightKinds == {"empirical"}:
        weightLabel = "historicalEpisodeMeasure"
    elif weightKinds == {"resampled"}:
        weightLabel = "empiricalResamplingMeasure"
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
        "inputWarnings": inputWarnings,
    }
    runHash = _stableHash(payload)
    executableHash = _stableHash(
        {
            "modelId": model.modelId,
            "modelVersion": model.version,
            "laws": tuple((law.lawId, law.version, law.fn) for law in model.laws),
        }
    )
    parameterHash = _stableHash(
        {
            "laws": tuple((law.lawId, law.parameters) for law in model.laws),
            "actions": model.actions,
            "constraints": constraints,
            "objectives": objectives,
        }
    )
    dataVintageHash = _stableHash({"initial": initial, "paths": paths})
    traceRoot = _stableHash({"traces": tuple(traces)})
    resultPayload = {
        "status": "partial" if unqualifiedLaws else "ok",
        "decisionStatus": decisionStatus,
        "weightLabel": weightLabel,
        "recommendation": recommendation,
        "paretoStrategies": pareto,
        "evaluations": evaluationTuple,
        "traceRoot": traceRoot,
        "constraints": constraints,
        "objectives": objectives,
        "warnings": tuple(warnings),
    }
    return SimulationRun(
        runHash=runHash,
        executableHash=executableHash,
        parameterHash=parameterHash,
        dataVintageHash=dataVintageHash,
        resultHash=_stableHash(resultPayload),
        traceRoot=traceRoot,
        status="partial" if unqualifiedLaws else "ok",
        decisionStatus=decisionStatus,
        weightLabel=weightLabel,
        recommendation=recommendation,
        paretoStrategies=pareto,
        evaluations=evaluationTuple,
        traces=tuple(traces),
        constraints=tuple(constraints),
        objectives=tuple(objectives),
        warnings=tuple(warnings),
    )
