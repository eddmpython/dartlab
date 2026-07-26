"""Provider-neutral feature meaning registry의 공용 data 계층 정본."""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.dataHub.vintage import canonicalPayloadHash

STATE_VARIABLE_ROLES = {"state", "observedFeature"}
STATE_EVIDENCE_ROLES = {
    "observed",
    "deterministicDerived",
    "admittedEstimate",
    "explicitAssumption",
    "derivedFromAssumption",
}
STATE_TIMINGS = {"flow", "stock", "boundaryIndex", "ratio"}
STATE_VARIABLE_SPEC_SCHEMA = "state-variable-spec-v1"
STATE_VARIABLE_REGISTRY_SCHEMA = "state-variable-registry-v1"


class StateVariableError(ValueError):
    """변수 의미, 공급자, 시간 단위 또는 경계 계약이 잘못되면 발생한다."""


@dataclass(frozen=True)
class StateVariableSpec:
    """실행 변수가 요구하는 의미와 공급자 신호 계약을 보존한다."""

    variableId: str
    signalId: str
    providerId: str
    datasetId: str
    unit: str
    role: str
    evidenceRole: str
    frequency: str
    timing: str
    transformId: str
    maxStalenessDays: int
    lower: float | None = None
    upper: float | None = None
    schemaVersion: str = STATE_VARIABLE_SPEC_SCHEMA


@dataclass(frozen=True)
class StateVariableRegistry:
    """정렬된 변수 의미와 그 전체 내용 해시를 보존한다."""

    specs: tuple[StateVariableSpec, ...]
    registryHash: str
    schemaVersion: str = STATE_VARIABLE_REGISTRY_SCHEMA


def _registryPayload(specs: tuple[StateVariableSpec, ...]) -> dict:
    return {"schemaVersion": STATE_VARIABLE_REGISTRY_SCHEMA, "specs": specs}


def buildStateVariableRegistry(specs: tuple[StateVariableSpec, ...]) -> StateVariableRegistry:
    """Validate and hash an order-independent state variable registry.

    Capabilities:
        Provider-neutral feature 의미, 증거 역할, 시간 timing과 bounds를 검증하고 정렬된 registry를 만든다.

    Args:
        specs: Direct executable-visible variables and their fixed sources.

    Returns:
        Variable-id sorted registry with a canonical content hash.

    Raises:
        StateVariableError: If identity, meaning, sources, or bounds are invalid.

    Example:
        ``registry = buildStateVariableRegistry((revenueSpec, cashSpec))``

    Guide:
        Data owner는 공급자 관측값과 별도로 실행에 노출할 feature 의미를 이 registry에 고정한다.

    When:
        Point-in-time state compile 또는 factor consumer가 feature contract를 실행 전에 결박할 때 호출한다.

    How:
        variableId로 정렬하고 각 의미 invariant를 검사한 뒤 canonical payload hash를 계산한다.

    Requires:
        specs는 현재 schema version을 쓰는 고유하고 완전한 ``StateVariableSpec`` tuple이어야 한다.

    SeeAlso:
        ``stateVariableContractHash``와 ``StateVariableRegistry``.

    AIContext:
        Provider 이름과 실행 의미를 분리해 simulator 밖의 공용 data consumer도 같은 feature contract를 쓴다.
    """

    ordered = tuple(sorted(specs, key=lambda item: item.variableId))
    if not ordered or len({item.variableId for item in ordered}) != len(ordered):
        raise StateVariableError("state registry needs unique variables")
    for item in ordered:
        if item.schemaVersion != STATE_VARIABLE_SPEC_SCHEMA:
            raise StateVariableError("state variable protocol mismatch")
        if (
            not item.variableId
            or not item.signalId
            or not item.providerId
            or not item.datasetId
            or not item.unit
            or not item.frequency
            or not item.transformId
        ):
            raise StateVariableError("state variable contract is incomplete")
        if (
            item.role not in STATE_VARIABLE_ROLES
            or item.evidenceRole not in STATE_EVIDENCE_ROLES
            or item.timing not in STATE_TIMINGS
        ):
            raise StateVariableError(f"state variable meaning is invalid: {item.variableId}")
        if item.maxStalenessDays < 0:
            raise StateVariableError("state variable staleness must be nonnegative")
        if item.lower is not None and item.upper is not None and item.lower > item.upper:
            raise StateVariableError("state variable bounds are inverted")
    return StateVariableRegistry(ordered, canonicalPayloadHash(_registryPayload(ordered)))


def stateVariableContractHash(specs: tuple[StateVariableSpec, ...]) -> str:
    """Hash executable meaning without values or provider observation identity.

    Args:
        specs: Variable specifications participating in one compiled state.

    Returns:
        Canonical hash of identifier, unit, execution role, evidence role,
        frequency, timing, and transform.

    Raises:
        StateVariableError: If the supplied specifications are invalid.

    Example:
        ``contractHash = stateVariableContractHash(registry.specs)``

    Requires:
        ``buildStateVariableRegistry`` 검증을 통과하는 specification tuple이어야 한다.
    """

    registry = buildStateVariableRegistry(specs)
    return canonicalPayloadHash(
        tuple(
            (
                item.variableId,
                item.unit,
                item.role,
                item.frequency,
                item.timing,
                item.transformId,
                item.evidenceRole,
            )
            for item in registry.specs
        )
    )


__all__ = [
    "STATE_EVIDENCE_ROLES",
    "STATE_TIMINGS",
    "STATE_VARIABLE_REGISTRY_SCHEMA",
    "STATE_VARIABLE_ROLES",
    "STATE_VARIABLE_SPEC_SCHEMA",
    "StateVariableError",
    "StateVariableRegistry",
    "StateVariableSpec",
    "buildStateVariableRegistry",
    "stateVariableContractHash",
]
