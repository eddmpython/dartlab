"""World model compilation: contract validation and current-step law ordering.

`WorldModel` 은 자료형이 아니라 컴파일러다. 생성 한 번에 변수, 행동, 법칙 계약을 전부
검증하고 current-step 의존 그래프를 위상 정렬해 실행 순서를 굳힌다. 그 일곱 단계가 한
`__post_init__` 안에 붙어 있으면 어느 단계가 어떤 불변식을 세우는지 읽어낼 방법이 없다.

여기서는 단계마다 함수를 하나씩 준다. 검사 순서가 곧 에러 우선순위 계약이라 함수 호출
순서를 바꾸면 사용자가 받는 메시지가 달라진다. 그래서 순서는 그대로 두고 경계만 그었다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

from dartlab.simulate.admissionRegistry import AdmissionVerifier
from dartlab.simulate.worldContracts import _validateActionEvidenceReceipt, _validateLawCertificate
from dartlab.simulate.worldTypes import (
    EVIDENCE_SET,
    ROLE_SET,
    ActionSpec,
    LawSpec,
    SimulationSpecError,
    VariableSpec,
    _validDigest,
)


def _indexVariables(variables: tuple[VariableSpec, ...]) -> dict[str, VariableSpec]:
    """변수 id 색인을 만들면서 중복 선언을 같은 자리에서 잡는다."""

    byId = {variable.variableId: variable for variable in variables}
    if len(byId) != len(variables):
        raise SimulationSpecError("duplicate variableId")
    return byId


def _indexActions(actions: tuple[ActionSpec, ...]) -> dict[str, ActionSpec]:
    """행동 id 색인을 만들면서 중복 선언을 같은 자리에서 잡는다."""

    byId = {action.actionId: action for action in actions}
    if len(byId) != len(actions):
        raise SimulationSpecError("duplicate actionId")
    return byId


def _validateVariableContracts(variables: tuple[VariableSpec, ...]) -> None:
    """변수 하나가 홀로 만족해야 할 역할, 의미, 경계 계약을 검사한다."""

    for variable in variables:
        if variable.role not in ROLE_SET:
            raise SimulationSpecError(f"unknown variable role: {variable.role}")
        if (
            not variable.unit
            or not variable.frequency
            or not variable.timing
            or not variable.transformId
            or not variable.evidenceRole
        ):
            raise SimulationSpecError(f"incomplete variable meaning: {variable.variableId}")
        for bound in (variable.lower, variable.upper):
            if bound is not None and not math.isfinite(float(bound)):
                raise SimulationSpecError(f"non-finite bounds: {variable.variableId}")
        if variable.lower is not None and variable.upper is not None and variable.lower > variable.upper:
            raise SimulationSpecError(f"invalid bounds: {variable.variableId}")


def _downgradeNonAdmittedLaws(laws: tuple[LawSpec, ...]) -> tuple[LawSpec, ...]:
    """Keep unsigned or rejected empirical claims executable only as non-admitted laws."""

    statusByCertificate = {"documented": "partial", "rejected": "blocked"}
    return tuple(
        replace(law, status=statusByCertificate[law.certificate.status])
        if law.certificate is not None and law.certificate.status in statusByCertificate
        else law
        for law in laws
    )


def _validateActionContracts(
    actions: tuple[ActionSpec, ...],
    admissionVerifier: AdmissionVerifier | None,
    stepFrequency: str,
    stepSpan: int,
) -> None:
    """행동 하나가 홀로 만족해야 할 근거, 범위, 비용, 인증 계약을 검사한다."""

    for action in actions:
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
        if action.effectEvidence == "identifiedIntervention":
            if not _validDigest(action.certificateId):
                raise SimulationSpecError(f"identified action needs an evidence receipt: {action.actionId}")
            if admissionVerifier is None:
                raise SimulationSpecError(f"identified action needs an admission verifier: {action.actionId}")
            _validateActionEvidenceReceipt(
                action,
                admissionVerifier,
                frequency=stepFrequency,
                stepSpan=stepSpan,
            )
        elif action.certificateId:
            raise SimulationSpecError(f"non-identified action cannot carry an evidence receipt: {action.actionId}")


def _validateLawIdentity(
    law: LawSpec,
    byId: dict[str, LawSpec],
    stepFrequency: str,
    stepSpan: int,
    admissionVerifier: AdmissionVerifier | None,
) -> None:
    """법칙의 식별자, 근거 종류, 상태, 인증서 결속을 모델 격자와 함께 검사한다."""

    if law.lawId in byId:
        raise SimulationSpecError("duplicate lawId")
    byId[law.lawId] = law
    if law.evidenceKind not in EVIDENCE_SET or law.status not in {"active", "partial", "blocked"}:
        raise SimulationSpecError(f"invalid law certificate: {law.lawId}")
    if law.evidenceKind in {"measuredAssociation", "identifiedIntervention"}:
        if (
            law.certificate is not None
            and law.certificate.status in {"admitted", "retrospectiveOnly"}
            and admissionVerifier is None
        ):
            raise SimulationSpecError(f"empirical law needs an admission verifier: {law.lawId}")
        _validateLawCertificate(law, admissionVerifier)
        if law.certificate is not None and (
            law.certificate.frequency != stepFrequency or law.certificate.stepSpan != stepSpan
        ):
            raise SimulationSpecError(f"law certificate step contract mismatch: {law.lawId}")
    elif law.certificate is not None:
        raise SimulationSpecError(f"non-empirical law cannot carry a certificate: {law.lawId}")


def _validateLawInputContracts(law: LawSpec, parameterUnitByName: dict[str, str]) -> None:
    """입력 이름의 모호성과 경로 파라미터의 단위 선언 및 모델 전역 일관성을 검사한다."""

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


def _validateLawReferences(
    law: LawSpec,
    variables: dict[str, VariableSpec],
    actions: dict[str, ActionSpec],
) -> None:
    """법칙이 지목한 변수, 충격, 행동이 전부 모델 등록분인지 검사한다."""

    for name in law.priorInputs + law.currentInputs + law.outputs:
        if name not in variables:
            raise SimulationSpecError(f"unknown variable {name}: {law.lawId}")
    for name in law.shockInputs:
        if name not in variables or variables[name].role != "shock":
            raise SimulationSpecError(f"unknown shock {name}: {law.lawId}")
    for name in law.actionInputs:
        if name not in actions:
            raise SimulationSpecError(f"unknown action {name}: {law.lawId}")


def _registerLawOutputs(law: LawSpec, variables: dict[str, VariableSpec], producer: dict[str, str]) -> None:
    """출력 변수마다 유일 생산자를 등록해 외생 변수 침범과 중복 생산을 막는다."""

    for output in law.outputs:
        if output in producer:
            raise SimulationSpecError(f"duplicate output producer: {output}")
        if variables[output].role in {"shock", "observedFeature"}:
            raise SimulationSpecError(f"law cannot produce external variable: {output}")
        producer[output] = law.lawId


def _validateLawContracts(
    laws: tuple[LawSpec, ...],
    variables: dict[str, VariableSpec],
    actions: dict[str, ActionSpec],
    stepFrequency: str,
    stepSpan: int,
    admissionVerifier: AdmissionVerifier | None,
) -> tuple[dict[str, str], dict[str, LawSpec]]:
    """법칙을 선언 순서대로 검사하며 생산자 표와 법칙 색인을 함께 세운다."""

    producer: dict[str, str] = {}
    byId: dict[str, LawSpec] = {}
    parameterUnitByName: dict[str, str] = {}
    for law in laws:
        _validateLawIdentity(law, byId, stepFrequency, stepSpan, admissionVerifier)
        _validateLawInputContracts(law, parameterUnitByName)
        _validateLawReferences(law, variables, actions)
        _registerLawOutputs(law, variables, producer)
    return producer, byId


def _lawDependencies(laws: tuple[LawSpec, ...], producer: dict[str, str]) -> dict[str, set[str]]:
    """current-step 입력을 생산자 간선으로 바꾸면서 고아 입력과 자기순환을 걸러낸다."""

    dependencies: dict[str, set[str]] = {law.lawId: set() for law in laws}
    for law in laws:
        for name in law.currentInputs:
            parent = producer.get(name)
            if parent is None:
                raise SimulationSpecError(f"current input has no producer: {name}")
            if parent == law.lawId:
                raise SimulationSpecError(f"self cycle: {law.lawId}")
            dependencies[law.lawId].add(parent)
    return dependencies


def _orderLaws(
    laws: tuple[LawSpec, ...],
    byId: dict[str, LawSpec],
    dependencies: dict[str, set[str]],
) -> tuple[LawSpec, ...]:
    """준비된 법칙을 id 사전순으로 꺼내는 결정적 위상 정렬로 실행 순서를 굳힌다."""

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
    if len(ordered) != len(laws):
        raise SimulationSpecError("current-step law cycle")
    return tuple(ordered)


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
    admissionVerifier: AdmissionVerifier | None = field(
        default=None,
        repr=False,
        compare=False,
        metadata={"canonical": False},
    )
    _orderedLaws: tuple[LawSpec, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "actions", tuple(self.actions))
        object.__setattr__(self, "laws", _downgradeNonAdmittedLaws(tuple(self.laws)))
        if not self.stepFrequency or self.stepSpan < 1:
            raise SimulationSpecError("invalid model step contract")
        variables = _indexVariables(self.variables)
        actions = _indexActions(self.actions)
        _validateVariableContracts(self.variables)
        _validateActionContracts(self.actions, self.admissionVerifier, self.stepFrequency, self.stepSpan)
        producer, byId = _validateLawContracts(
            self.laws,
            variables,
            actions,
            self.stepFrequency,
            self.stepSpan,
            self.admissionVerifier,
        )
        if any(a.costPerUnit > 0 for a in self.actions) and not any(law.usesActionCost for law in self.laws):
            raise SimulationSpecError("action cost has no consuming law")
        dependencies = _lawDependencies(self.laws, producer)
        object.__setattr__(self, "_orderedLaws", _orderLaws(self.laws, byId, dependencies))
