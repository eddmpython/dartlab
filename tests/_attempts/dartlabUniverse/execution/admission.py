"""ExecutionRequest를 schema, snapshot, 권한, budget, idempotency 순으로 admission한다."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..canonical import canonicalDigest
from .registry import CapabilityRef, UniverseCapabilityRegistry
from .schemaDescriptor import validateValue

_SNAPSHOT_RE = re.compile(r"^du:v1:snapshot:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ExecutionBudget:
    maxWallMs: int = 120_000
    maxCpuMs: int = 120_000
    maxRssBytes: int = 2_147_483_648
    maxNetworkBytes: int = 0
    maxRows: int = 100_000
    maxOutputBytes: int = 64 * 1024 * 1024
    maxToolCalls: int = 1
    maxRetries: int = 1


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    requestId: str
    capabilityId: str
    snapshotId: str
    targetRefs: tuple[str, ...]
    args: dict[str, Any]
    assumptionRefs: tuple[str, ...]
    visibilityScope: str
    budget: ExecutionBudget
    priority: int
    deadline: str | None
    idempotencyKey: str | None
    requestedBy: str
    seed: int | None = None


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    controlRoot: str
    readDataRoot: str | None = None
    expectedSnapshotId: str | None = None
    allowedRuntimeBoundaries: tuple[str, ...] = ("LOCAL_PYTHON",)
    allowedVisibilityScopes: tuple[str, ...] = ("LOCAL",)
    allowedExecutorPrefixes: tuple[str, ...] = ("dartlab",)
    maxWallMs: int = 120_000
    maxCpuMs: int = 120_000
    maxRssBytes: int = 2_147_483_648
    maxNetworkBytes: int = 0
    maxRows: int = 100_000
    maxOutputBytes: int = 64 * 1024 * 1024
    maxRetries: int = 1
    workerPollMs: int = 20
    idempotencyWaitMs: int = 120_000
    protectedPaths: tuple[str, ...] = ()
    workerExecutable: str | None = None


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    admitted: bool
    decisionId: str
    request: ExecutionRequest
    capability: CapabilityRef | None
    normalizedArgs: dict[str, Any]
    idempotencyKey: str
    policy: ExecutionPolicy
    reasonCodes: tuple[str, ...]


def _bounded(request: ExecutionRequest, policy: ExecutionPolicy) -> tuple[str, ...]:
    checks = (
        ("maxWallMs", request.budget.maxWallMs, policy.maxWallMs),
        ("maxCpuMs", request.budget.maxCpuMs, policy.maxCpuMs),
        ("maxRssBytes", request.budget.maxRssBytes, policy.maxRssBytes),
        ("maxNetworkBytes", request.budget.maxNetworkBytes, policy.maxNetworkBytes),
        ("maxRows", request.budget.maxRows, policy.maxRows),
        ("maxOutputBytes", request.budget.maxOutputBytes, policy.maxOutputBytes),
        ("maxRetries", request.budget.maxRetries, policy.maxRetries),
    )
    return tuple(f"BUDGET_EXCEEDED:{name}" for name, actual, maximum in checks if actual < 0 or actual > maximum)


def _idempotencyKey(request: ExecutionRequest, capability: CapabilityRef | None, normalizedArgs: dict[str, Any]) -> str:
    engineVersion = capability.sourceDigest if capability is not None else "missing"
    computed = canonicalDigest(
        {
            "capabilityId": request.capabilityId,
            "snapshotId": request.snapshotId,
            "targetRefs": request.targetRefs,
            "normalizedArgs": normalizedArgs,
            "assumptionRefs": request.assumptionRefs,
            "seed": request.seed,
            "engineVersion": engineVersion,
        }
    )
    if request.idempotencyKey is not None and request.idempotencyKey != computed:
        return ""
    return computed


def _executorAllowed(apiRef: str, prefixes: tuple[str, ...]) -> bool:
    target = apiRef.split(":", 2)[1] if apiRef.startswith("python:") else apiRef
    return any(target == prefix or target.startswith(prefix + ".") for prefix in prefixes)


def admitExecution(
    request: ExecutionRequest,
    registry: UniverseCapabilityRegistry,
    policy: ExecutionPolicy,
) -> AdmissionDecision:
    """요청을 fail-closed 순서로 검사하고 불변 admission decision을 반환한다."""
    reasons = []
    capability = registry.get(request.capabilityId)
    normalizedArgs = dict(sorted(request.args.items()))
    if capability is None:
        reasons.append("CAPABILITY_NOT_FOUND")
    else:
        if not capability.eligible or capability.status not in {"ACTIVE", "CALLABLE_UNMIRRORED"}:
            reasons.append("CAPABILITY_NOT_EXECUTABLE")
        if capability.runtimeBoundary not in policy.allowedRuntimeBoundaries:
            reasons.append("ACCESS_DENIED_RUNTIME_BOUNDARY")
        if capability.visibility not in policy.allowedVisibilityScopes:
            reasons.append("ACCESS_DENIED_VISIBILITY")
        if not _executorAllowed(capability.apiRef, policy.allowedExecutorPrefixes):
            reasons.append("EXECUTOR_NOT_ALLOWLISTED")
        descriptor = capability.schemaDescriptor
        if descriptor is None or descriptor.status != "VALIDATED":
            reasons.append("SCHEMA_INCOMPLETE")
        elif not validateValue(normalizedArgs, descriptor.argsSchema).valid:
            reasons.append("INVALID_ARGS")
        if capability.seedPolicy == "REQUIRED" and request.seed is None:
            reasons.append("NONDETERMINISTIC_WITHOUT_SEED")
        if capability.seedPolicy == "FORBIDDEN" and request.seed is not None:
            reasons.append("UNEXPECTED_SEED")
    if not request.requestId or not request.requestedBy:
        reasons.append("REQUEST_IDENTITY_MISSING")
    if not _SNAPSHOT_RE.fullmatch(request.snapshotId):
        reasons.append("SOURCE_SNAPSHOT_INVALID")
    if policy.expectedSnapshotId is not None and request.snapshotId != policy.expectedSnapshotId:
        reasons.append("SOURCE_SNAPSHOT_MISMATCH")
    if not request.targetRefs or any(not item for item in request.targetRefs):
        reasons.append("TARGET_UNRESOLVED")
    if request.visibilityScope not in policy.allowedVisibilityScopes:
        reasons.append("ACCESS_DENIED_REQUEST_VISIBILITY")
    if request.priority < 0 or request.priority > 9:
        reasons.append("PRIORITY_INVALID")
    controlRoot = Path(policy.controlRoot).resolve()
    if not controlRoot.is_absolute():
        reasons.append("CONTROL_ROOT_INVALID")
    for protectedPath in policy.protectedPaths:
        protected = Path(protectedPath).resolve()
        if controlRoot == protected or controlRoot.is_relative_to(protected) or protected.is_relative_to(controlRoot):
            reasons.append("CONTROL_ROOT_OVERLAPS_PROTECTED_PATH")
    if policy.readDataRoot is not None:
        readDataRoot = Path(policy.readDataRoot).resolve()
        if not readDataRoot.is_dir():
            reasons.append("READ_DATA_ROOT_INVALID")
        if (
            controlRoot == readDataRoot
            or controlRoot.is_relative_to(readDataRoot)
            or readDataRoot.is_relative_to(controlRoot)
        ):
            reasons.append("CONTROL_ROOT_OVERLAPS_READ_DATA_ROOT")
    reasons.extend(_bounded(request, policy))
    key = _idempotencyKey(request, capability, normalizedArgs)
    if not key:
        reasons.append("IDEMPOTENCY_KEY_MISMATCH")
        key = canonicalDigest({"requestId": request.requestId, "invalidIdempotencyKey": request.idempotencyKey})
    orderedReasons = tuple(sorted(set(reasons)))
    decisionId = f"du:v1:execution-admission:{canonicalDigest({'request': request, 'reasons': orderedReasons})}"
    return AdmissionDecision(
        admitted=not orderedReasons,
        decisionId=decisionId,
        request=request,
        capability=capability,
        normalizedArgs=normalizedArgs,
        idempotencyKey=key,
        policy=policy,
        reasonCodes=orderedReasons,
    )
