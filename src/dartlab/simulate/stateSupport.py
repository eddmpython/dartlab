"""Typed initial-state artifacts and empirical policy applicability support.

The module does not forecast outcomes. It binds every model-visible initial
value to an identifier, unit, and role, then measures whether a current state
is inside the historical OOS origin support used by a policy certificate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from hashlib import sha256

from dartlab.simulate.vintage import canonicalPayloadBytes, canonicalPayloadHash

STATE_SUPPORT_DISTANCE_RULE = "range-scaled-chebyshev-nearest-origin-v1"
STATE_SUPPORT_SCHEMA = "empirical-state-support-v1"
STATE_SUPPORT_QUANTILE = 0.95
INITIAL_STATE_RULE_ID = "typed-initial-state"
INITIAL_STATE_RULE_VERSION = "1"
INITIAL_STATE_RULE_HASH = sha256(b"dartlab.typed-initial-state.v1").hexdigest()


class StateSupportError(ValueError):
    """상태 primitive 또는 정책 적용 가능성 경계가 잘못되면 발생한다."""


@dataclass(frozen=True)
class StatePrimitive:
    """모델이 읽는 초기값 하나와 변수 의미 계약을 보존한다."""

    variableId: str
    unit: str
    role: str
    value: float


@dataclass(frozen=True)
class EmpiricalStateSupport:
    """동일 계약의 역사적 OOS origin으로 만든 상태 적용 가능성 경계다."""

    supportId: str
    stateContractHash: str
    nOrigins: int
    variableIds: tuple[str, ...]
    units: tuple[str, ...]
    roles: tuple[str, ...]
    minimums: tuple[float, ...]
    maximums: tuple[float, ...]
    neighborQuantile: float
    neighborDistanceLimit: float
    originStateHashes: tuple[str, ...]
    distanceRule: str = STATE_SUPPORT_DISTANCE_RULE
    schemaVersion: str = STATE_SUPPORT_SCHEMA


def _normalizeState(state: tuple[StatePrimitive, ...]) -> tuple[StatePrimitive, ...]:
    normalized = tuple(sorted(state, key=lambda item: item.variableId))
    if len({item.variableId for item in normalized}) != len(normalized):
        raise StateSupportError("state needs unique typed primitives")
    if any(not item.variableId or not item.unit or not item.role for item in normalized):
        raise StateSupportError("state primitive contract is incomplete")
    if any(not math.isfinite(float(item.value)) for item in normalized):
        raise StateSupportError("state primitive is not finite")
    return normalized


def stateContractHash(state: tuple[StatePrimitive, ...]) -> str:
    """Hash the ordered variable identity, unit, and role contract.

    Args:
        state: Model-visible initial values. Values are excluded from the hash.

    Returns:
        SHA-256 hex digest of the exact typed variable contract.

    Raises:
        StateSupportError: If identifiers are duplicated or metadata is empty.

    Example:
        ``stateContractHash((StatePrimitive("cash", "KRW", "state", 1.0),))``
    """

    normalized = _normalizeState(state)
    return canonicalPayloadHash(tuple((item.variableId, item.unit, item.role) for item in normalized))


def stateAdmissionArtifact(
    state: tuple[StatePrimitive, ...],
    *,
    asOf: str,
    knowledgeAsOf: str,
    decisionAsOf: str,
) -> bytes:
    """Serialize the exact model-visible initial state for typed admission.

    Args:
        state: Typed initial values actually visible to laws and policies.
        asOf: Fiscal or event state label.
        knowledgeAsOf: Latest knowledge cutoff used by the state.
        decisionAsOf: Decision cutoff at which the state is consumed.

    Returns:
        Canonical JSON bytes suitable for a content-addressed receipt.

    Raises:
        StateSupportError: If the state contract or a value is invalid.

    Example:
        ``stateAdmissionArtifact(state, asOf="2024Q4", knowledgeAsOf="20250301", decisionAsOf="20250302")``
    """

    normalized = _normalizeState(state)
    if not knowledgeAsOf or not decisionAsOf:
        raise StateSupportError("state admission needs knowledge and decision cutoffs")
    return canonicalPayloadBytes(
        {
            "schemaVersion": "typed-initial-state-v1",
            "stateContractHash": stateContractHash(normalized),
            "asOf": str(asOf),
            "knowledgeAsOf": str(knowledgeAsOf),
            "decisionAsOf": str(decisionAsOf),
            "state": normalized,
        }
    )


def stateAdmissionSubjectHash(
    state: tuple[StatePrimitive, ...],
    *,
    asOf: str,
    knowledgeAsOf: str,
    decisionAsOf: str,
) -> str:
    """Return the content hash that an initialState receipt must sign.

    Args:
        state: Typed initial values visible to the executable.
        asOf: Fiscal or event state label.
        knowledgeAsOf: State knowledge cutoff.
        decisionAsOf: State decision cutoff.

    Returns:
        SHA-256 hex digest of the canonical admission artifact.

    Raises:
        StateSupportError: If the artifact contract is invalid.

    Example:
        ``stateAdmissionSubjectHash(state, asOf="2024Q4", knowledgeAsOf="20250301", decisionAsOf="20250302")``
    """

    return canonicalPayloadHash(
        {
            "schemaVersion": "typed-initial-state-v1",
            "stateContractHash": stateContractHash(state),
            "asOf": str(asOf),
            "knowledgeAsOf": str(knowledgeAsOf),
            "decisionAsOf": str(decisionAsOf),
            "state": _normalizeState(state),
        }
    )


def _distance(
    left: tuple[float, ...],
    right: tuple[float, ...],
    minimums: tuple[float, ...],
    maximums: tuple[float, ...],
) -> float:
    distances = []
    for first, second, minimum, maximum in zip(left, right, minimums, maximums, strict=True):
        span = maximum - minimum
        if abs(span) <= 1e-12:
            distances.append(0.0 if abs(first - second) <= 1e-12 else math.inf)
        else:
            distances.append(abs(first - second) / span)
    return max(distances, default=0.0)


def buildEmpiricalStateSupport(
    origins: tuple[tuple[StatePrimitive, ...], ...],
) -> EmpiricalStateSupport:
    """Build a fixed leave-one-out joint support boundary.

    Args:
        origins: Typed initial states from ordered, unique historical OOS origins.

    Returns:
        Deterministic marginal ranges and 95% nearest-origin distance boundary.

    Raises:
        StateSupportError: If fewer than three origins exist or contracts drift.

    Example:
        ``support = buildEmpiricalStateSupport((origin1, origin2, origin3))``
    """

    if len(origins) < 3:
        raise StateSupportError("state support needs at least three historical origins")
    normalized = tuple(_normalizeState(state) for state in origins)
    contract = stateContractHash(normalized[0])
    if any(stateContractHash(state) != contract for state in normalized[1:]):
        raise StateSupportError("historical state contracts drifted")
    vectors = tuple(tuple(float(item.value) for item in state) for state in normalized)
    width = len(vectors[0])
    minimums = tuple(min(row[index] for row in vectors) for index in range(width))
    maximums = tuple(max(row[index] for row in vectors) for index in range(width))
    leaveOneOut = []
    for index, vector in enumerate(vectors):
        leaveOneOut.append(
            min(
                _distance(vector, other, minimums, maximums)
                for otherIndex, other in enumerate(vectors)
                if otherIndex != index
            )
        )
    ordered = sorted(leaveOneOut)
    quantileIndex = max(0, math.ceil(STATE_SUPPORT_QUANTILE * len(ordered)) - 1)
    firstState = normalized[0]
    provisional = EmpiricalStateSupport(
        supportId="",
        stateContractHash=contract,
        nOrigins=len(normalized),
        variableIds=tuple(item.variableId for item in firstState),
        units=tuple(item.unit for item in firstState),
        roles=tuple(item.role for item in firstState),
        minimums=minimums,
        maximums=maximums,
        neighborQuantile=STATE_SUPPORT_QUANTILE,
        neighborDistanceLimit=ordered[quantileIndex],
        originStateHashes=tuple(sorted(canonicalPayloadHash(state) for state in normalized)),
    )
    return replace(provisional, supportId=canonicalPayloadHash(provisional))


def validateEmpiricalStateSupport(
    current: tuple[StatePrimitive, ...],
    origins: tuple[tuple[StatePrimitive, ...], ...],
    support: EmpiricalStateSupport,
) -> float:
    """Rebuild support and validate a current state without extrapolation.

    Args:
        current: Current model-visible initial state.
        origins: Historical OOS origin states sealed by the policy batch.
        support: Sealed support artifact to reproduce from those origins.

    Returns:
        Current range-scaled Chebyshev distance to the nearest origin.

    Raises:
        StateSupportError: If the contract, artifact, marginal, or joint gate fails.

    Example:
        ``distance = validateEmpiricalStateSupport(current, origins, support)``
    """

    expected = buildEmpiricalStateSupport(origins)
    if support != expected:
        raise StateSupportError("state support artifact does not match historical origins")
    normalized = _normalizeState(current)
    if stateContractHash(normalized) != support.stateContractHash:
        raise StateSupportError("current state contract is outside policy support")
    vector = tuple(float(item.value) for item in normalized)
    for value, minimum, maximum in zip(vector, support.minimums, support.maximums, strict=True):
        if value < minimum - 1e-12 or value > maximum + 1e-12:
            raise StateSupportError("current state is outside a historical marginal range")
    originVectors = tuple(tuple(float(item.value) for item in _normalizeState(origin)) for origin in origins)
    distance = min(
        (_distance(vector, origin, support.minimums, support.maximums) for origin in originVectors),
        default=0.0,
    )
    if distance > support.neighborDistanceLimit + 1e-12:
        raise StateSupportError("current state is outside joint historical support")
    return distance
