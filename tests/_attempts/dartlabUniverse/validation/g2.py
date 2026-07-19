"""Universe U2 capability와 execution readiness machine gate."""

from __future__ import annotations

from dataclasses import dataclass

from ..canonical import canonicalDigest
from ..execution.registry import UniverseCapabilityRegistry


@dataclass(frozen=True, slots=True)
class G2Report:
    passed: bool
    discoveredCandidateCount: int
    classifiedCandidateCount: int
    eligibleCallableCount: int
    validatedSchemaCount: int
    blockedEligibleCount: int
    catalogCoverage: float
    executionReadiness: float
    inventedAxisCount: int
    failureCodes: tuple[str, ...]
    digest: str


def validateG2(registry: UniverseCapabilityRegistry) -> G2Report:
    """Catalog closure와 eligible schema closure를 분리해 둘 다 100%인지 검증한다."""
    failures = []
    if registry.classifiedCandidateCount != registry.discoveredCandidateCount or registry.catalogCoverage != 1.0:
        failures.append("CATALOG_COVERAGE_INCOMPLETE")
    if registry.validatedSchemaCount != registry.eligibleCallableCount or registry.executionReadiness != 1.0:
        failures.append("EXECUTION_READINESS_INCOMPLETE")
    if registry.blockedEligibleCount:
        failures.append("BLOCKED_ELIGIBLE_CAPABILITY")
    if registry.inventedAxisCount:
        failures.append("INVENTED_AXIS")
    for capability in registry.capabilities:
        if not capability.eligible and not capability.gapReasons:
            failures.append(f"INELIGIBLE_REASON_MISSING:{capability.candidateId}")
        if capability.eligible and (
            capability.schemaDescriptor is None or capability.schemaDescriptor.status != "VALIDATED"
        ):
            failures.append(f"ELIGIBLE_SCHEMA_NOT_VALIDATED:{capability.candidateId}")
        if capability.status == "HIDDEN_PREVIEW" and capability.eligible:
            failures.append(f"PREVIEW_EXECUTION_LEAK:{capability.candidateId}")
    ordered = tuple(sorted(set(failures)))
    digest = canonicalDigest(
        {
            "registryDigest": registry.registryDigest,
            "failureCodes": ordered,
            "counts": (
                registry.discoveredCandidateCount,
                registry.classifiedCandidateCount,
                registry.eligibleCallableCount,
                registry.validatedSchemaCount,
            ),
        }
    )
    return G2Report(
        passed=not ordered,
        discoveredCandidateCount=registry.discoveredCandidateCount,
        classifiedCandidateCount=registry.classifiedCandidateCount,
        eligibleCallableCount=registry.eligibleCallableCount,
        validatedSchemaCount=registry.validatedSchemaCount,
        blockedEligibleCount=registry.blockedEligibleCount,
        catalogCoverage=registry.catalogCoverage,
        executionReadiness=registry.executionReadiness,
        inventedAxisCount=registry.inventedAxisCount,
        failureCodes=ordered,
        digest=digest,
    )
