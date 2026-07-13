"""Provider-neutral variable meaning contracts for point-in-time state compilation."""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.simulate.vintage import canonicalPayloadHash

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

    Args:
        specs: Direct executable-visible variables and their fixed sources.

    Returns:
        Variable-id sorted registry with a canonical content hash.

    Raises:
        StateVariableError: If identity, meaning, sources, or bounds are invalid.

    Example:
        ``registry = buildStateVariableRegistry((revenueSpec, cashSpec))``
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
