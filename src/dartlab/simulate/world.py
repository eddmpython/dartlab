"""Auditable multi-step world evolution and strategy comparison contracts."""

from __future__ import annotations

import json
import marshal
import math
import sqlite3
from dataclasses import dataclass, field, fields, replace
from hashlib import sha256
from types import MappingProxyType
from typing import TYPE_CHECKING, Callable, Mapping

from dartlab.simulate.parameterDraws import (
    ParameterDrawSetReceipt,
    validateParameterDrawSetReceipt,
)
from dartlab.simulate.vintage import (
    VintageError,
    VintageRef,
    isExactAsKnown,
    validateVintageRef,
    worldStatePayloadHash,
)

if TYPE_CHECKING:
    from dartlab.simulate.admissionRegistry import AdmissionVerifier
    from dartlab.simulate.policyEvaluation import PolicyAdmissionEvidence

ROLE_SET = {"state", "metric", "shock"}
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


class _CvarSpill:
    """compact 실행의 경로값을 임시 SQLite 파일에 흘려 exact weighted CVaR을 집계한다."""

    def __init__(self) -> None:
        self._connection = sqlite3.connect("")
        self._connection.execute("PRAGMA journal_mode=OFF")
        self._connection.execute("PRAGMA synchronous=OFF")
        self._connection.execute(
            "CREATE TABLE score (strategyIndex INTEGER, objectiveIndex INTEGER, ordinal INTEGER, value REAL, weight REAL)"
        )
        self._prepared = False

    def add(self, strategyIndex: int, objectiveIndex: int, ordinal: int, value: float, weight: float) -> None:
        """경로 목적값과 가중치를 메모리 대신 임시 저장소에 추가한다."""

        self._connection.execute(
            "INSERT INTO score VALUES (?, ?, ?, ?, ?)",
            (strategyIndex, objectiveIndex, ordinal, value, weight),
        )

    def weightedCvar(self, strategyIndex: int, objectiveIndex: int, tailFraction: float) -> float:
        """낮은 목적값 꼬리를 value와 ordinal 순으로 읽어 exact weighted CVaR을 반환한다."""

        if not self._prepared:
            self._connection.execute(
                "CREATE INDEX score_order ON score (strategyIndex, objectiveIndex, value, ordinal)"
            )
            self._prepared = True
        totalWeight = float(
            self._connection.execute(
                "SELECT SUM(weight) FROM score WHERE strategyIndex=? AND objectiveIndex=?",
                (strategyIndex, objectiveIndex),
            ).fetchone()[0]
        )
        target = totalWeight * tailFraction
        used = 0.0
        total = 0.0
        rows = self._connection.execute(
            "SELECT value, weight FROM score WHERE strategyIndex=? AND objectiveIndex=? ORDER BY value, ordinal",
            (strategyIndex, objectiveIndex),
        )
        for value, weight in rows:
            take = min(float(weight), target - used)
            if take > 0:
                total += float(value) * take
                used += take
            if used >= target - 1e-12:
                break
        if used <= 0:
            raise SimulationSpecError("compact cvar spill has no positive weight")
        return total / used

    def close(self) -> None:
        """임시 SQLite 저장소를 닫고 운영체제가 파일을 회수하게 한다."""

        connection = getattr(self, "_connection", None)
        if connection is not None:
            connection.close()
            self._connection = None

    def __del__(self) -> None:
        self.close()


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
    fn: LawFn = field(default=lambda _: {}, repr=False, compare=False)

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
    pathAdmissionReceiptId: str
    policyEvaluationCertificateId: str
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


def strategyContractHash(strategy: StrategySpec) -> str:
    """행동 일정 또는 정책 실행물과 버전·근거를 하나의 전략 계약 hash로 묶는다."""

    return _stableHash({"strategy": strategy})


def objectiveContractHash(objective: ObjectiveSpec) -> str:
    """목적 지표, 기간 축약, 방향, 위험 계약을 재사용 가능한 hash로 묶는다."""

    return _stableHash({"objective": objective})


def constraintContractHash(constraints: tuple[ConstraintSpec, ...]) -> str:
    """모든 hard constraint의 순서와 임계 계약을 하나의 hash로 묶는다."""

    return _stableHash({"constraints": constraints})


def traceRootFor(traces: tuple[PathTrace, ...]) -> str:
    """보존된 전체 trace 순서에서 실행기와 동일한 chain root를 다시 계산한다."""

    traceChain = sha256()
    for trace in traces:
        traceChain.update(bytes.fromhex(_stableHash({"trace": trace})))
    return _stableHash({"traceCount": len(traces), "traceChain": traceChain.hexdigest()})


def _pathSetPayload(paths: tuple[ScenarioPath, ...]) -> dict:
    return {
        "paths": [
            {
                "pathId": path.pathId,
                "steps": [dict(step) for step in path.steps],
                "weight": path.weight,
                "weightKind": path.weightKind,
                "refs": path.refs,
                "frequency": path.frequency,
                "stepSpan": path.stepSpan,
                "certificateId": path.certificateId,
                "validationStatus": path.validationStatus,
                "maxAdmittedStep": path.maxAdmittedStep,
                "parameterDraws": path.parameterDraws,
                "parameterDrawReceipt": path.parameterDrawReceipt,
                "knowledgeAsOf": path.knowledgeAsOf,
                "historyStatus": path.historyStatus,
                "vintage": path.vintage,
            }
            for path in paths
        ]
    }


def pathSetAdmissionArtifact(paths: tuple[ScenarioPath, ...]) -> bytes:
    """서명 대상 경로 집합을 순서 보존 정규 JSON 아티팩트로 직렬화한다."""

    return json.dumps(
        _canonical(_pathSetPayload(paths)),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def pathSetAdmissionSubjectHash(paths: tuple[ScenarioPath, ...]) -> str:
    """경로 admission 영수증이 서명해야 할 정확한 subject hash를 반환한다."""

    return sha256(pathSetAdmissionArtifact(paths)).hexdigest()


def _pathSetContentHash(paths: tuple[ScenarioPath, ...]) -> str:
    return pathSetAdmissionSubjectHash(paths)


def bindAdmittedPathContent(paths: tuple[ScenarioPath, ...]) -> tuple[ScenarioPath, ...]:
    """admitted 경로 집합의 실제 내용과 순서를 하나의 공유 hash로 묶는다."""

    if not paths or any(path.validationStatus != "admitted" for path in paths):
        raise SimulationSpecError("only a nonempty admitted path set can be content-bound")
    if any(_comparableDate(path.knowledgeAsOf) is None for path in paths):
        raise SimulationSpecError("admitted paths need a comparable knowledge cutoff")
    if any(path.historyStatus != "asKnown" for path in paths):
        raise SimulationSpecError("admitted paths need as-known history")
    contentHash = _pathSetContentHash(paths)
    return tuple(replace(path, admissionContentHash=contentHash) for path in paths)


def bindPathAdmissionReceipt(paths: tuple[ScenarioPath, ...], receiptId: str) -> tuple[ScenarioPath, ...]:
    """내용 결속을 바꾸지 않고 경로 집합 전체에 하나의 서명 영수증을 연결한다."""

    if not _validDigest(receiptId):
        raise SimulationSpecError("path admission receipt identifier is invalid")
    if not paths or any(path.validationStatus != "admitted" for path in paths):
        raise SimulationSpecError("only admitted paths can bind an admission receipt")
    contentHashes = {path.admissionContentHash for path in paths}
    if len(contentHashes) != 1 or next(iter(contentHashes)) != _pathSetContentHash(paths):
        raise SimulationSpecError("path admission receipt needs exact content binding")
    return tuple(replace(path, admissionReceiptId=receiptId) for path in paths)


def _lawContractPayload(law: LawSpec) -> dict:
    return {
        "outputs": law.outputs,
        "priorInputs": law.priorInputs,
        "currentInputs": law.currentInputs,
        "shockInputs": law.shockInputs,
        "actionInputs": law.actionInputs,
        "pathParameterInputs": law.pathParameterInputs,
        "pathParameterUnits": law.pathParameterUnits,
        "usesActionCost": law.usesActionCost,
    }


def _lawCertificatePayload(certificate: LawCertificate) -> dict:
    return {
        "lawId": certificate.lawId,
        "lawVersion": certificate.lawVersion,
        "evidenceKind": certificate.evidenceKind,
        "contractHash": certificate.contractHash,
        "parameterHash": certificate.parameterHash,
        "executableHash": certificate.executableHash,
        "evidenceHash": certificate.evidenceHash,
        "knowledgeAsOf": certificate.knowledgeAsOf,
        "historyStatus": certificate.historyStatus,
        "frequency": certificate.frequency,
        "stepSpan": certificate.stepSpan,
        "maxAdmittedStep": certificate.maxAdmittedStep,
        "status": certificate.status,
        "rules": certificate.rules,
    }


def issueLawCertificate(
    law: LawSpec,
    *,
    evidenceRows: tuple[Mapping[str, object], ...],
    knowledgeAsOf: str,
    historyStatus: str,
    frequency: str,
    stepSpan: int = 1,
    rules: str,
) -> LawCertificate:
    """검증 행의 연속 통과 지평을 계산하고 법칙 실행물 전체에 바인딩한다."""

    if law.evidenceKind not in {"measuredAssociation", "identifiedIntervention"}:
        raise SimulationSpecError("only measured or identified laws can be certified")
    cutoff = str(knowledgeAsOf).replace("-", "")[:8]
    if len(cutoff) != 8 or not cutoff.isdigit() or not rules or not frequency or stepSpan < 1:
        raise SimulationSpecError("law certificate needs a valid cutoff and rules")
    normalized: list[dict] = []
    required = {"step", "metric", "estimate", "threshold", "operator"}
    for row in evidenceRows:
        if not required.issubset(row):
            raise SimulationSpecError("law evidence row is incomplete")
        step = int(row["step"])
        operator = str(row["operator"])
        if step < 1 or not str(row["metric"]) or operator not in {"gt", "ge", "lt", "le"}:
            raise SimulationSpecError("law evidence row is invalid")
        estimate = float(row["estimate"])
        threshold = float(row["threshold"])
        if not math.isfinite(estimate) or not math.isfinite(threshold):
            raise SimulationSpecError("law evidence row is not finite")
        passed = {
            "gt": estimate > threshold,
            "ge": estimate >= threshold,
            "lt": estimate < threshold,
            "le": estimate <= threshold,
        }[operator]
        normalized.append(
            {
                "step": step,
                "metric": str(row["metric"]),
                "estimate": estimate,
                "threshold": threshold,
                "operator": operator,
                "passed": passed,
            }
        )
    normalized.sort(key=lambda row: (row["step"], row["metric"]))
    maxObserved = max((int(row["step"]) for row in normalized), default=0)
    maxAdmittedStep = 0
    for step in range(1, maxObserved + 1):
        stepRows = [row for row in normalized if row["step"] == step]
        if not stepRows or not all(bool(row["passed"]) for row in stepRows):
            break
        maxAdmittedStep = step
    if maxAdmittedStep < 1:
        status = "rejected"
    elif historyStatus == "asKnown":
        status = "admitted"
    else:
        status = "retrospectiveOnly"
    provisional = LawCertificate(
        certificateId="",
        lawId=law.lawId,
        lawVersion=law.version,
        evidenceKind=law.evidenceKind,
        contractHash=_stableHash(_lawContractPayload(law)),
        parameterHash=_stableHash({"parameters": law.parameters}),
        executableHash=_stableHash({"fn": law.fn}),
        evidenceHash=_stableHash({"rows": normalized}),
        knowledgeAsOf=cutoff,
        historyStatus=historyStatus,
        frequency=frequency,
        stepSpan=stepSpan,
        maxAdmittedStep=maxAdmittedStep,
        status=status,
        rules=rules,
    )
    return LawCertificate(
        certificateId=_stableHash(_lawCertificatePayload(provisional)),
        **{name: getattr(provisional, name) for name in provisional.__dataclass_fields__ if name != "certificateId"},
    )


def _validateLawCertificate(law: LawSpec) -> None:
    certificate = law.certificate
    if certificate is None:
        raise SimulationSpecError(f"empirical law needs a certificate: {law.lawId}")
    if certificate.status not in LAW_CERTIFICATE_STATUS_SET:
        raise SimulationSpecError(f"invalid law certificate status: {law.lawId}")
    expectedDigest = _stableHash(_lawCertificatePayload(certificate))
    if certificate.certificateId != expectedDigest:
        raise SimulationSpecError(f"law certificate digest mismatch: {law.lawId}")
    expected = {
        "lawId": law.lawId,
        "lawVersion": law.version,
        "evidenceKind": law.evidenceKind,
        "contractHash": _stableHash(_lawContractPayload(law)),
        "parameterHash": _stableHash({"parameters": law.parameters}),
        "executableHash": _stableHash({"fn": law.fn}),
    }
    if any(getattr(certificate, name) != value for name, value in expected.items()):
        raise SimulationSpecError(f"law certificate binding mismatch: {law.lawId}")
    if law.status == "active" and certificate.status != "admitted":
        raise SimulationSpecError(f"active law needs admitted evidence: {law.lawId}")
    if law.evidenceKind == "identifiedIntervention" and certificate.status != "admitted":
        raise SimulationSpecError(f"identified law needs admitted evidence: {law.lawId}")
    if certificate.status == "retrospectiveOnly" and law.status != "partial":
        raise SimulationSpecError(f"retrospective law must be partial: {law.lawId}")
    if certificate.status == "rejected" and law.status != "blocked":
        raise SimulationSpecError(f"rejected law must be blocked: {law.lawId}")


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
        parameterUnitByName: dict[str, str] = {}
        for law in self.laws:
            if law.lawId in byId:
                raise SimulationSpecError("duplicate lawId")
            byId[law.lawId] = law
            if law.evidenceKind not in EVIDENCE_SET or law.status not in {"active", "partial", "blocked"}:
                raise SimulationSpecError(f"invalid law certificate: {law.lawId}")
            if law.evidenceKind in {"measuredAssociation", "identifiedIntervention"}:
                _validateLawCertificate(law)
                if law.certificate is not None and (
                    law.certificate.frequency != self.stepFrequency or law.certificate.stepSpan != self.stepSpan
                ):
                    raise SimulationSpecError(f"law certificate step contract mismatch: {law.lawId}")
            elif law.certificate is not None:
                raise SimulationSpecError(f"non-empirical law cannot carry a certificate: {law.lawId}")
            declared = law.priorInputs + law.currentInputs + law.shockInputs
            if len(set(declared)) != len(declared):
                raise SimulationSpecError(f"ambiguous law input: {law.lawId}")
            if len(set(law.pathParameterInputs)) != len(law.pathParameterInputs) or any(
                not name for name in law.pathParameterInputs
            ):
                raise SimulationSpecError(f"invalid path parameter input: {law.lawId}")
            if set(law.pathParameterUnits) != set(law.pathParameterInputs) or any(
                not unit for unit in law.pathParameterUnits.values()
            ):
                raise SimulationSpecError(f"path parameter inputs need explicit units: {law.lawId}")
            for name, unit in law.pathParameterUnits.items():
                if name in parameterUnitByName and parameterUnitByName[name] != unit:
                    raise SimulationSpecError(f"conflicting path parameter unit: {name}")
                parameterUnitByName[name] = unit
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


def _cleanIssuedActions(
    model: WorldModel,
    strategyId: str,
    step: int,
    issued: Mapping[str, float],
) -> dict[str, float]:
    """정책 또는 일정이 낸 행동 집합과 범위를 같은 계약으로 검증한다."""

    if not isinstance(issued, Mapping):
        raise SimulationSpecError(f"strategy {strategyId} step {step} must return an action mapping")
    actionById = {action.actionId: action for action in model.actions}
    if set(issued) != set(actionById):
        missing = sorted(set(actionById) - set(issued))
        unknown = sorted(set(issued) - set(actionById))
        raise SimulationSpecError(
            f"strategy {strategyId} step {step} action mismatch; missing={missing}, unknown={unknown}"
        )
    clean: dict[str, float] = {}
    for name, value in issued.items():
        action = actionById[name]
        number = _finite(value, f"strategy.{strategyId}.{step}.{name}")
        if number < action.lower - 1e-12 or number > action.upper + 1e-12:
            raise SimulationSpecError(f"action outside bounds: {name}")
        clean[name] = number
    return clean


def _checkInputs(
    model: WorldModel,
    initial: WorldState,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
    admissionVerifier: AdmissionVerifier | None,
) -> int:
    if not paths or not strategies:
        raise SimulationSpecError("at least one path and strategy are required")
    horizon = len(paths[0].steps)
    if horizon < 1 or any(len(path.steps) != horizon for path in paths):
        raise SimulationSpecError("all paths must share a positive horizon")
    if any(len(strategy.actionsByStep) != horizon for strategy in strategies):
        raise SimulationSpecError("all strategies must share the path horizon")
    if initial.knowledgeAsOf:
        initialKnowledgeDate = _comparableDate(initial.knowledgeAsOf)
        if initialKnowledgeDate is None:
            raise SimulationSpecError("initial state has an invalid knowledge cutoff")
    else:
        initialKnowledgeDate = _comparableDate(initial.asOf)
    if initial.decisionAsOf:
        decisionDate = _comparableDate(initial.decisionAsOf)
        if decisionDate is None:
            raise SimulationSpecError("initial state has an invalid decision cutoff")
    else:
        decisionDate = initialKnowledgeDate
    if initialKnowledgeDate is not None and decisionDate is not None and initialKnowledgeDate > decisionDate:
        raise SimulationSpecError("initial state knowledge is newer than its decision cutoff")
    if initial.vintage is not None:
        if decisionDate is None:
            raise SimulationSpecError("initial state vintage needs a decision cutoff")
        try:
            validateVintageRef(
                initial.vintage,
                decisionAsOf=decisionDate,
                expectedArtifactKind="worldState",
                expectedPayloadHash=worldStatePayloadHash(
                    initial.values,
                    step=initial.step,
                    asOf=initial.asOf,
                    refs=initial.refs,
                ),
            )
        except VintageError as error:
            raise SimulationSpecError(str(error)) from error
        if initial.knowledgeAsOf and initial.vintage.knowledgeAsOf != initialKnowledgeDate:
            raise SimulationSpecError("initial state vintage knowledge cutoff mismatch")
    for law in model.laws:
        certificate = law.certificate
        if law.evidenceKind in {"measuredAssociation", "identifiedIntervention"}:
            _validateLawCertificate(law)
        if certificate is not None and certificate.status == "admitted" and certificate.maxAdmittedStep < horizon:
            raise SimulationSpecError(f"law exceeds admitted horizon: {law.lawId}")
        if certificate is not None and certificate.status == "admitted":
            if initialKnowledgeDate is None:
                raise SimulationSpecError("certified laws need an initial-state knowledge cutoff")
            if certificate.knowledgeAsOf > initialKnowledgeDate:
                raise SimulationSpecError(f"law certificate is newer than initial state: {law.lawId}")
    if len({p.pathId for p in paths}) != len(paths) or len({s.strategyId for s in strategies}) != len(strategies):
        raise SimulationSpecError("duplicate pathId or strategyId")
    if sum(strategy.isBaseline for strategy in strategies) > 1:
        raise SimulationSpecError("at most one baseline strategy is allowed")
    weightKinds = {path.weightKind for path in paths}
    if len(weightKinds) != 1:
        raise SimulationSpecError("all paths must share one weight interpretation")
    shockIds = {v.variableId for v in model.variables if v.role == "shock"}
    pathParameterIds = {name for law in model.laws for name in law.pathParameterInputs}
    requiredInitial = {name for law in model.laws for name in law.priorInputs}
    for name in requiredInitial:
        _validateValue(model, name, initial.values.get(name), f"initial.{name}")
    parameterPaths = tuple(path for path in paths if path.parameterDraws)
    parameterReceipts = {path.parameterDrawReceipt for path in parameterPaths}
    if any(receipt is not None for receipt in parameterReceipts):
        if None in parameterReceipts or len(parameterReceipts) != 1 or len(parameterPaths) != len(paths):
            raise SimulationSpecError("parameter draw paths must share one provenance receipt")
        receipt = next(iter(parameterReceipts))
        validateParameterDrawSetReceipt(paths, receipt, decisionAsOf=decisionDate)
        expectedUnits = {
            name: unit
            for law in model.laws
            for name, unit in law.pathParameterUnits.items()
            if name in receipt.parameterNames
        }
        if tuple(sorted(expectedUnits.items())) != receipt.parameterUnits:
            raise SimulationSpecError("parameter draw units do not match their consuming laws")
    for path in paths:
        unknownPathParameters = set(path.parameterDraws) - pathParameterIds
        if unknownPathParameters:
            raise SimulationSpecError(f"unknown path parameters for {path.pathId}: {sorted(unknownPathParameters)}")
        for name, value in path.parameterDraws.items():
            _finite(value, f"path.{path.pathId}.parameter.{name}")
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
        if path.vintage is not None:
            if decisionDate is None:
                raise SimulationSpecError("path vintage needs an initial-state decision cutoff")
            try:
                validateVintageRef(path.vintage, decisionAsOf=decisionDate)
            except VintageError as error:
                raise SimulationSpecError(str(error)) from error
            if path.knowledgeAsOf and path.vintage.knowledgeAsOf != path.knowledgeAsOf:
                raise SimulationSpecError(f"path vintage knowledge cutoff mismatch: {path.pathId}")
        if path.validationStatus == "admitted":
            if not _validDigest(path.certificateId):
                raise SimulationSpecError(f"admitted path needs a certificate: {path.pathId}")
            if path.maxAdmittedStep < horizon:
                raise SimulationSpecError(f"path exceeds admitted horizon: {path.pathId}")
            pathDate = _comparableDate(path.knowledgeAsOf)
            if pathDate is None:
                raise SimulationSpecError(f"admitted path needs a knowledge cutoff: {path.pathId}")
            if path.historyStatus != "asKnown":
                raise SimulationSpecError(f"admitted path needs as-known history: {path.pathId}")
            if path.vintage is None or not isExactAsKnown(path.vintage):
                raise SimulationSpecError(f"admitted path needs an exact as-known vintage: {path.pathId}")
            if not _validDigest(path.vintage.receiptId):
                raise SimulationSpecError(f"admitted path needs a signed vintage receipt: {path.pathId}")
            if decisionDate is None:
                raise SimulationSpecError("admitted paths need an initial-state decision cutoff")
            if pathDate > decisionDate:
                raise SimulationSpecError(f"path is newer than decision state: {path.pathId}")
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
        knowledgeCutoffs = {path.knowledgeAsOf for path in paths}
        historyStatuses = {path.historyStatus for path in paths}
        if (
            len(certificates) != 1
            or len(admittedHorizons) != 1
            or len(knowledgeCutoffs) != 1
            or historyStatuses != {"asKnown"}
        ):
            raise SimulationSpecError("admitted paths must share one certificate, horizon, and vintage")
        contentHashes = {path.admissionContentHash for path in paths}
        if len(contentHashes) != 1 or not _validDigest(next(iter(contentHashes))):
            raise SimulationSpecError("admitted paths need one content binding")
        contentHash = next(iter(contentHashes))
        if contentHash != _pathSetContentHash(paths):
            raise SimulationSpecError("admitted path content binding mismatch")
        receiptIds = {path.admissionReceiptId for path in paths}
        vintages = {path.vintage for path in paths}
        if len(receiptIds) != 1 or not _validDigest(next(iter(receiptIds))):
            raise SimulationSpecError("admitted paths need one signed path-set receipt")
        if len(vintages) != 1:
            raise SimulationSpecError("admitted paths must share one typed vintage")
        if admissionVerifier is None:
            raise SimulationSpecError("admitted paths need a runtime admission verifier")
        receiptId = next(iter(receiptIds))
        vintage = next(iter(vintages))
        if vintage is None:
            raise SimulationSpecError("admitted paths need one typed vintage")
        try:
            receipt = admissionVerifier.verify(
                receiptId,
                expectedSubjectHash=contentHash,
                expectedKind="pathSet",
            )
            vintageReceipt = admissionVerifier.verify(
                vintage.receiptId,
                expectedSubjectHash=vintage.payloadHash,
                expectedKind="dataVintage",
            )
        except RuntimeError as error:
            raise SimulationSpecError(f"path admission verification failed: {error}") from error
        if receipt.status != "admitted":
            raise SimulationSpecError("path-set receipt is not admitted")
        if receipt.artifactHash != contentHash:
            raise SimulationSpecError("path-set receipt artifact binding mismatch")
        if vintage.receiptId not in receipt.parentReceiptIds:
            raise SimulationSpecError("path-set receipt does not inherit its vintage receipt")
        if (
            vintageReceipt.status != "verifiedVintage"
            or vintageReceipt.artifactHash != vintage.artifactHash
            or vintageReceipt.knowledgeAsOf != vintage.knowledgeAsOf
            or vintageReceipt.revisionPolicy != vintage.revisionPolicy
            or vintageReceipt.coverage != vintage.coverage
        ):
            raise SimulationSpecError("path vintage receipt contract mismatch")
        receiptIssued = _comparableDate(receipt.issuedAt)
        vintageIssued = _comparableDate(vintageReceipt.issuedAt)
        if (
            decisionDate is None
            or receiptIssued is None
            or vintageIssued is None
            or receiptIssued > decisionDate
            or vintageIssued > decisionDate
        ):
            raise SimulationSpecError("path admission was not available by decisionAsOf")
        if (
            receipt.knowledgeAsOf != next(iter(knowledgeCutoffs))
            or receipt.frequency != model.stepFrequency
            or receipt.stepSpan != model.stepSpan
            or receipt.maxAdmittedStep < horizon
            or receipt.revisionPolicy != "asKnown"
            or receipt.coverage != "asOfExact"
        ):
            raise SimulationSpecError("path-set receipt execution contract mismatch")
    if weightKinds == {"calibrated"}:
        totalWeight = sum(float(path.weight) for path in paths if path.weight is not None)
        if abs(totalWeight - 1.0) > 1e-9:
            raise SimulationSpecError("calibrated path weights must sum to one")
    for strategy in strategies:
        if strategy.policyFn is not None:
            if not callable(strategy.policyFn):
                raise SimulationSpecError(f"closed-loop policy must be callable: {strategy.strategyId}")
            if any(issued for issued in strategy.actionsByStep):
                raise SimulationSpecError(
                    f"closed-loop strategy cannot also carry an action schedule: {strategy.strategyId}"
                )
            if not strategy.policyVersion or not strategy.policyProvenance:
                raise SimulationSpecError(
                    f"closed-loop strategy needs policy version and provenance: {strategy.strategyId}"
                )
        else:
            for step, issued in enumerate(strategy.actionsByStep):
                _cleanIssuedActions(model, strategy.strategyId, step, issued)
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
    traceLimit: int | None = None,
    admissionVerifier: AdmissionVerifier | None = None,
    policyAdmissionEvidence: PolicyAdmissionEvidence | None = None,
) -> SimulationRun:
    """Evolve every strategy over the same explicit world paths.

    Static strategies contain schedules. Closed-loop policies receive only the
    state and action known before the current shock, never a path or future
    outcome.
    """

    horizon = _checkInputs(model, initial, paths, strategies, admissionVerifier)
    decisionAsOf = (
        _comparableDate(initial.decisionAsOf)
        or _comparableDate(initial.knowledgeAsOf)
        or _comparableDate(initial.asOf)
        or ""
    )
    pathAdmissionReceiptId = paths[0].admissionReceiptId if paths[0].validationStatus == "admitted" else ""
    if traceLimit is not None and (not isinstance(traceLimit, int) or traceLimit < 0):
        raise SimulationSpecError("traceLimit must be a nonnegative integer or None")
    variableIds = {variable.variableId for variable in model.variables}
    for objective in objectives:
        if objective.metric not in variableIds:
            raise SimulationSpecError(f"unknown objective metric: {objective.metric}")
        if (
            objective.reducer not in {"terminal", "minimum", "maximum", "cumulative"}
            or objective.direction not in {"maximize", "minimize"}
            or objective.risk not in {"worst", "average", "cvar"}
        ):
            raise SimulationSpecError(f"invalid objective contract: {objective.metric}")
        if not math.isfinite(float(objective.tailFraction)) or not 0 < objective.tailFraction <= 1:
            raise SimulationSpecError(f"non-finite objective contract: {objective.metric}")
    for constraint in constraints:
        if (
            constraint.metric not in variableIds
            or constraint.scope not in {"eachStep", "terminal"}
            or not math.isfinite(float(constraint.threshold))
        ):
            raise SimulationSpecError(f"invalid constraint: {constraint.metric}")

    executableHash = _stableHash(
        {
            "modelId": model.modelId,
            "modelVersion": model.version,
            "laws": tuple((law.lawId, law.version, law.fn) for law in model.laws),
            "policies": tuple(
                (strategy.strategyId, strategy.policyVersion, strategy.policyFn)
                for strategy in strategies
                if strategy.policyFn is not None
            ),
        }
    )
    policyAdmissionIssues = ["policyEvaluation"]
    policyEvaluationCertificateId = ""
    if policyAdmissionEvidence is not None:
        if admissionVerifier is None:
            raise SimulationSpecError("policy admission evidence needs a runtime admission verifier")
        baselineStrategies = tuple(strategy for strategy in strategies if strategy.isBaseline)
        candidateStrategies = tuple(strategy for strategy in strategies if not strategy.isBaseline)
        if len(strategies) != 2 or len(baselineStrategies) != 1 or len(candidateStrategies) != 1:
            raise SimulationSpecError("policy admission evidence needs exactly one baseline and one candidate")
        if len(objectives) != 1:
            raise SimulationSpecError("policy admission evidence needs exactly one objective")
        try:
            from dartlab.simulate.policyEvaluation import (
                parameterContractHashFor,
                validatePolicyEvaluationCertificate,
            )

            pathReceipt = admissionVerifier.verify(
                pathAdmissionReceiptId,
                expectedSubjectHash=pathSetAdmissionSubjectHash(paths),
                expectedKind="pathSet",
            )
            validatePolicyEvaluationCertificate(
                policyAdmissionEvidence.snapshot,
                policyAdmissionEvidence.batch,
                policyAdmissionEvidence.certificate,
                admissionVerifier,
                decisionAsOf=decisionAsOf,
                executableHash=executableHash,
                baselineStrategyContractHash=strategyContractHash(baselineStrategies[0]),
                candidateStrategyContractHash=strategyContractHash(candidateStrategies[0]),
                objectiveContractHash=objectiveContractHash(objectives[0]),
                constraintContractHash=constraintContractHash(constraints),
                pathRuleHash=pathReceipt.ruleHash,
                parameterContractHash=parameterContractHashFor(paths),
                pathFrequency=pathReceipt.frequency,
                pathStepSpan=pathReceipt.stepSpan,
                pathHorizon=horizon,
            )
        except (OSError, RuntimeError, ValueError) as error:
            raise SimulationSpecError(f"policy admission verification failed: {error}") from error
        policyAdmissionIssues = []
        policyEvaluationCertificateId = policyAdmissionEvidence.certificate.certificateId

    actionById = {action.actionId: action for action in model.actions}
    cvarSpill = _CvarSpill() if traceLimit is not None and any(item.risk == "cvar" for item in objectives) else None
    weights = [1.0 if path.weight is None else float(path.weight) for path in paths]
    traces: list[PathTrace] = []
    traceChain = sha256()
    traceCount = 0
    objectiveValues: dict[str, list[list[float]]] = {
        strategy.strategyId: [[] for _ in objectives] for strategy in strategies
    }
    objectiveNumerators: dict[str, list[float]] = {
        strategy.strategyId: [0.0 for _ in objectives] for strategy in strategies
    }
    objectiveDenominators: dict[str, list[float]] = {
        strategy.strategyId: [0.0 for _ in objectives] for strategy in strategies
    }
    objectiveWorst: dict[str, list[float]] = {
        strategy.strategyId: [math.inf for _ in objectives] for strategy in strategies
    }
    breachCounts = {strategy.strategyId: 0 for strategy in strategies}
    for strategyIndex, strategy in enumerate(strategies):
        for pathIndex, path in enumerate(paths):
            prior = {name: _finite(value, f"initial.{name}") for name, value in initial.values.items()}
            stepTraces: list[StepTrace] = []
            issuedHistory: list[dict[str, float]] = []
            for step in range(horizon):
                if strategy.policyFn is None:
                    rawIssued = strategy.actionsByStep[step]
                else:
                    priorActions = issuedHistory[-1] if issuedHistory else {name: 0.0 for name in actionById}
                    policyContext = PolicyContext(
                        step=step,
                        prior=_freezeMapping(prior),
                        priorActions=_freezeMapping(priorActions),
                    )
                    rawIssued = strategy.policyFn(policyContext)
                issued = _cleanIssuedActions(model, strategy.strategyId, step, rawIssued)
                issuedHistory.append(issued)
                effective: dict[str, float] = {}
                for actionId, action in actionById.items():
                    sourceStep = step - action.leadSteps
                    effective[actionId] = issuedHistory[sourceStep][actionId] if sourceStep >= 0 else 0.0
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
                    lawPathParameters = {
                        name: _finite(path.parameterDraws[name], f"{law.lawId}.pathParameter.{name}")
                        for name in law.pathParameterInputs
                        if name in path.parameterDraws
                    }
                    for name, value in lawPathParameters.items():
                        inputValues[f"pathParameter.{name}"] = value
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
                        pathParameters=_freezeMapping(lawPathParameters),
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
                            pathParameters=lawPathParameters,
                            certificateId=law.certificate.certificateId if law.certificate is not None else "",
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
            trace = PathTrace(
                strategyId=strategy.strategyId,
                pathId=path.pathId,
                initial={name: _finite(value, f"initial.{name}") for name, value in initial.values.items()},
                steps=tuple(stepTraces),
                policyVersion=strategy.policyVersion,
                policyProvenance=strategy.policyProvenance,
                status="ok",
            )
            traceCount += 1
            traceChain.update(bytes.fromhex(_stableHash({"trace": trace})))
            if traceLimit is None or len(traces) < traceLimit:
                traces.append(trace)
            breachCounts[strategy.strategyId] += sum(len(item.breaches) for item in trace.steps)
            for objectiveIndex, objective in enumerate(objectives):
                value = _pathMetric(trace, objective)
                weight = weights[pathIndex]
                if traceLimit is None:
                    objectiveValues[strategy.strategyId][objectiveIndex].append(value)
                if objective.risk == "average":
                    objectiveNumerators[strategy.strategyId][objectiveIndex] += value * weight
                    objectiveDenominators[strategy.strategyId][objectiveIndex] += weight
                elif objective.risk == "worst":
                    objectiveWorst[strategy.strategyId][objectiveIndex] = min(
                        objectiveWorst[strategy.strategyId][objectiveIndex], value
                    )
                elif objective.risk == "cvar" and traceLimit is not None:
                    if cvarSpill is None:
                        raise SimulationSpecError("compact cvar spill was not initialized")
                    cvarSpill.add(strategyIndex, objectiveIndex, pathIndex, value, weight)

    evaluations: list[StrategyEvaluation] = []
    for strategyIndex, strategy in enumerate(strategies):
        objectivePathValues: list[tuple[float, ...]] = []
        objectiveScores: list[float] = []
        for objectiveIndex, objective in enumerate(objectives):
            if traceLimit is None:
                values = tuple(objectiveValues[strategy.strategyId][objectiveIndex])
                objectivePathValues.append(values)
                objectiveScores.append(_aggregate(list(values), weights, objective))
            elif objective.risk == "average":
                numerator = objectiveNumerators[strategy.strategyId][objectiveIndex]
                denominator = objectiveDenominators[strategy.strategyId][objectiveIndex]
                objectiveScores.append(numerator / denominator)
            elif objective.risk == "worst":
                objectiveScores.append(objectiveWorst[strategy.strategyId][objectiveIndex])
            elif objective.risk == "cvar":
                if cvarSpill is None:
                    raise SimulationSpecError("compact cvar spill was not initialized")
                objectiveScores.append(cvarSpill.weightedCvar(strategyIndex, objectiveIndex, objective.tailFraction))
        breachCount = breachCounts[strategy.strategyId]
        evaluations.append(
            StrategyEvaluation(
                strategyId=strategy.strategyId,
                objectiveScores=tuple(objectiveScores),
                pathValues=tuple(objectivePathValues) if traceLimit is None else (),
                breachCount=breachCount,
                feasible=breachCount == 0,
            )
        )
    if cvarSpill is not None:
        cvarSpill.close()

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
    parameterPaths = tuple(path for path in paths if path.parameterDraws)
    parameterProvenanceIssues = [
        path.pathId
        for path in parameterPaths
        if path.parameterDrawReceipt is None or path.parameterDrawReceipt.status != "admitted"
    ]
    warnings: list[str] = list(inputWarnings)
    if traceLimit is not None:
        warnings.append(
            f"compact trace retention: retained {len(traces)} of {traceCount}; path-level objective values omitted"
        )
    if unqualifiedLaws:
        warnings.append(f"unqualified laws: {','.join(unqualifiedLaws)}")
    if assumedLaws or assumedActions or assumedActionLaws:
        warnings.append("unvalidated transition or intervention effects are conditional assumptions")
    if pathAdmissionIssues:
        warnings.append(f"paths are not admitted: {','.join(pathAdmissionIssues)}")
    undocumentedParameterPaths = [path.pathId for path in parameterPaths if path.parameterDrawReceipt is None]
    if undocumentedParameterPaths:
        warnings.append("parameterMeasure:undocumented:" + ",".join(undocumentedParameterPaths))
    elif parameterProvenanceIssues:
        warnings.append("parameterMeasure:documentedOnly")
    if policyAdmissionIssues:
        warnings.append("policy evaluation certificate is unavailable; automatic recommendation is disabled")
    baselineIds = [strategy.strategyId for strategy in strategies if strategy.isBaseline]
    if objectives and (len(strategies) < 2 or not baselineIds):
        warnings.append("recommendation needs one baseline and at least one candidate")
    if not objectives:
        decisionStatus = "abstain"
        warnings.append("no objective was declared")
    elif (
        unqualifiedLaws
        or assumedLaws
        or assumedActions
        or assumedActionLaws
        or pathAdmissionIssues
        or parameterProvenanceIssues
        or policyAdmissionIssues
    ):
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
        "traceLimit": traceLimit,
        "policyEvaluationCertificateId": policyEvaluationCertificateId,
    }
    runHash = _stableHash(payload)
    parameterHash = _stableHash(
        {
            "laws": tuple((law.lawId, law.parameters) for law in model.laws),
            "actions": model.actions,
            "pathParameterDraws": tuple((path.pathId, path.parameterDraws) for path in paths),
            "constraints": constraints,
            "objectives": objectives,
        }
    )
    dataVintageHash = _stableHash({"initial": initial, "paths": paths})
    traceRoot = _stableHash({"traceCount": traceCount, "traceChain": traceChain.hexdigest()})
    resultPayload = {
        "status": "partial" if unqualifiedLaws else "ok",
        "decisionStatus": decisionStatus,
        "weightLabel": weightLabel,
        "recommendation": recommendation,
        "paretoStrategies": pareto,
        "evaluations": evaluationTuple,
        "traceRoot": traceRoot,
        "traceCount": traceCount,
        "retainedTraceCount": len(traces),
        "decisionAsOf": decisionAsOf,
        "pathAdmissionReceiptId": pathAdmissionReceiptId,
        "policyEvaluationCertificateId": policyEvaluationCertificateId,
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
        traceCount=traceCount,
        retainedTraceCount=len(traces),
        decisionAsOf=decisionAsOf,
        pathAdmissionReceiptId=pathAdmissionReceiptId,
        policyEvaluationCertificateId=policyEvaluationCertificateId,
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
