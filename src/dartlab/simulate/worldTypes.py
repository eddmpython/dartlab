"""World runtime contract types and the canonical hashing primitives they share.

여기 있는 것은 전부 "값"이다. 검증기, 컴파일러, 실행기가 모두 이 자료형을 읽지만
반대로 이 모듈은 그 어느 것도 알지 못한다. 그래서 world 계열 모듈의 import 그래프가
한 방향으로 정리되고, 계약 자료형만 필요한 소비자는 실행기를 끌어들이지 않는다.

정규화(`_canonical`)와 안정 해시(`_stableHash`)도 같은 자리에 둔다. 재현 해시가
자료형의 필드 구조 자체에 붙어 있는 계약이라, 자료형과 떨어지면 둘이 따로 바뀔 수 있다.
"""

from __future__ import annotations

import json
import marshal
import math
from dataclasses import dataclass, field, fields
from hashlib import sha256
from types import MappingProxyType
from typing import Callable, Mapping

from dartlab.simulate.parameterDraws import ParameterDrawSetReceipt
from dartlab.simulate.vintage import VintageRef

ROLE_SET = {"state", "observedFeature", "metric", "shock"}
EVIDENCE_SET = {
    "accountingIdentity",
    "measuredAssociation",
    "identifiedIntervention",
    "explicitAssumption",
}
WEIGHT_KIND_SET = {"unweighted", "empirical", "resampled", "calibrated", "subjective"}
PATH_VALIDATION_SET = {"unvalidated", "retrospectiveOnly", "admitted", "rejected"}
LAW_CERTIFICATE_STATUS_SET = {"retrospectiveOnly", "admitted", "rejected"}


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
    frequency: str = "step"
    timing: str = "level"
    transformId: str = "identity-v1"
    evidenceRole: str = "model"


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
    pathParameters: Mapping[str, float]
    actionCost: float


LawFn = Callable[[StepContext], Mapping[str, float]]


@dataclass(frozen=True)
class PolicyContext:
    """폐루프 정책에 현재 결정시점까지 관측된 상태와 직전 발행 행동만 제공한다."""

    step: int
    prior: Mapping[str, float]
    priorActions: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(self, "prior", _freezeMapping(self.prior))
        object.__setattr__(self, "priorActions", _freezeMapping(self.priorActions))


PolicyFn = Callable[[PolicyContext], Mapping[str, float]]


@dataclass(frozen=True)
class LawCertificate:
    """법칙 실행물, 계약, 파라미터, 검증 증거를 하나의 digest로 묶는다."""

    certificateId: str
    lawId: str
    lawVersion: str
    evidenceKind: str
    contractHash: str
    parameterHash: str
    executableHash: str
    evidenceHash: str
    knowledgeAsOf: str
    historyStatus: str
    frequency: str
    stepSpan: int
    maxAdmittedStep: int
    status: str
    rules: str


def _noOpLaw(_state) -> dict:
    """아무 것도 내지 않는 기본 법칙.

    이름을 붙여 두는 이유가 있다. 예전에는 여기 익명 람다가 있었는데, `_canonical` 이
    callable 을 해싱할 때 코드 객체를 marshal 하므로 파일 이름과 첫 줄 번호가 해시에
    들어간다. 그래서 이 람다 위에 빈 줄 하나만 넣어도 `executableHash` 와 `runHash` 가
    바뀌었다. 재현성을 재려고 만든 해시가 소스 편집에 흔들리면 그 해시는 아무 것도 재지
    못한다. 아래 `_canonical` 이 이 함수만 위치와 무관한 고정 표식으로 봉인한다.
    """
    return {}


@dataclass(frozen=True)
class LawSpec:
    """한 기간 전이 법칙의 입력, 출력, 근거, 버전을 선언한다."""

    lawId: str
    outputs: tuple[str, ...]
    priorInputs: tuple[str, ...] = ()
    currentInputs: tuple[str, ...] = ()
    shockInputs: tuple[str, ...] = ()
    actionInputs: tuple[str, ...] = ()
    pathParameterInputs: tuple[str, ...] = ()
    usesActionCost: bool = False
    evidenceKind: str = "explicitAssumption"
    provenance: str = ""
    version: str = "1"
    status: str = "active"
    certificate: LawCertificate | None = None
    parameters: Mapping[str, float | str | bool] = field(default_factory=dict)
    pathParameterUnits: Mapping[str, str] = field(default_factory=dict)
    fn: LawFn = field(default=_noOpLaw, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameters", _freezeMapping(self.parameters))
        object.__setattr__(self, "pathParameterUnits", _freezeMapping(self.pathParameterUnits))


@dataclass(frozen=True)
class WorldState:
    """특정 시점의 세계 값과 기준시점 및 근거를 보존한다."""

    values: Mapping[str, float | None]
    step: int = 0
    asOf: str = ""
    refs: tuple[str, ...] = ()
    knowledgeAsOf: str = ""
    decisionAsOf: str = ""
    vintage: VintageRef | None = None
    admissionReceiptId: str = ""
    stateCompilationContractHash: str = ""
    stateManifestHash: str = ""

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
    admissionContentHash: str = ""
    parameterDraws: Mapping[str, float] = field(default_factory=dict)
    parameterDrawReceipt: ParameterDrawSetReceipt | None = None
    knowledgeAsOf: str = ""
    historyStatus: str = ""
    vintage: VintageRef | None = None
    admissionReceiptId: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", tuple(_freezeMapping(step) for step in self.steps))
        object.__setattr__(self, "refs", tuple(self.refs))
        object.__setattr__(self, "parameterDraws", _freezeMapping(self.parameterDraws))


@dataclass(frozen=True)
class StrategySpec:
    """미래를 읽지 않는 행동 일정 또는 관측 상태 기반 폐루프 정책을 선언한다."""

    strategyId: str
    actionsByStep: tuple[Mapping[str, float], ...]
    refs: tuple[str, ...] = ()
    isBaseline: bool = False
    policyVersion: str = ""
    policyProvenance: str = ""
    policyFn: PolicyFn | None = field(default=None, repr=False, compare=False)

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
    pathParameters: Mapping[str, float]
    certificateId: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", _freezeMapping(self.inputs))
        object.__setattr__(self, "outputs", _freezeMapping(self.outputs))
        object.__setattr__(self, "parameters", _freezeMapping(self.parameters))
        object.__setattr__(self, "pathParameters", _freezeMapping(self.pathParameters))


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
    policyVersion: str
    policyProvenance: str
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
    traceCount: int
    retainedTraceCount: int
    decisionAsOf: str
    initialStateAdmissionReceiptId: str
    pathAdmissionReceiptId: str
    policyEvaluationCertificateId: str
    stateSupportId: str
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


def _comparableDate(value: str) -> str | None:
    text = str(value).replace("-", "")[:8]
    return text if len(text) == 8 and text.isdigit() else None


def _canonical(value):
    if value is _noOpLaw:
        # 기본 법칙은 소스 위치와 무관한 고정 표식으로 봉인한다. 코드 객체를 해싱하면
        # 파일을 옮기거나 줄만 밀려도 재현성 해시가 달라진다.
        return {"callable": "dartlab.simulate.worldTypes._noOpLaw", "codeHash": "noOpLaw"}
    if callable(value):
        code = getattr(value, "__code__", None)
        closure = getattr(value, "__closure__", None) or ()
        closureNames = tuple(getattr(code, "co_freevars", ()))
        captured = {name: _canonical(cell.cell_contents) for name, cell in zip(closureNames, closure, strict=True)}
        referencedGlobals = {}
        globalScope = getattr(value, "__globals__", {})
        for name in sorted(set(getattr(code, "co_names", ()))):
            if name not in globalScope:
                continue
            item = globalScope[name]
            if isinstance(item, (str, int, float, bool, bytes, tuple, list, dict)) or item is None:
                referencedGlobals[name] = _canonical(item)
            elif callable(item) and item is not value:
                itemCode = getattr(item, "__code__", None)
                referencedGlobals[name] = {
                    "callable": f"{getattr(item, '__module__', '')}.{getattr(item, '__qualname__', '')}",
                    "codeHash": sha256(marshal.dumps(itemCode)).hexdigest() if itemCode is not None else "",
                }
            else:
                referencedGlobals[name] = {"objectType": f"{type(item).__module__}.{type(item).__qualname__}"}
        return {
            "callable": f"{getattr(value, '__module__', '')}.{getattr(value, '__qualname__', '')}",
            "codeHash": sha256(marshal.dumps(code)).hexdigest() if code is not None else "",
            "defaults": _canonical(getattr(value, "__defaults__", None)),
            "kwdefaults": _canonical(getattr(value, "__kwdefaults__", None)),
            "closure": captured,
            "referencedGlobals": referencedGlobals,
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
