"""Universe U1 identity, temporal, provenance machine gate."""

from __future__ import annotations

from dataclasses import dataclass

from ..canonical import CensusResult, canonicalDigest
from ..contracts import ValidationReport
from ..identity.census import IdentityCensus
from ..provenance import SnapshotValidationReport, UniverseSnapshot


@dataclass(frozen=True, slots=True)
class G1Report:
    u0SnapshotDigest: str
    identityCensusDigest: str
    identityEntityCount: int
    identityCollisionCount: int
    universeSnapshotId: str
    replayValidationDigest: str
    contractValidationCount: int
    temporalFutureLeakCount: int
    falseMergeCount: int
    controlPlaneIntegrity: bool
    g1Passed: bool
    failureCodes: tuple[str, ...]
    digest: str


def buildG1Report(
    census: CensusResult,
    identityCensus: IdentityCensus,
    snapshot: UniverseSnapshot,
    replayValidation: SnapshotValidationReport,
    *,
    contractValidations: tuple[ValidationReport, ...] = (),
    temporalFutureLeakCount: int = 0,
    falseMergeCount: int = 0,
    controlPlaneIntegrity: bool,
    currentControlPlaneHeadId: str,
) -> G1Report:
    """U0, identity collision, replay, contract, temporal, control integrity를 fail-closed로 결합한다."""
    collisionCount = len(identityCensus.crossSourceEntityCollisions) + sum(
        len(source.duplicateEntityIds) + len(source.duplicateCanonicalKeys) for source in identityCensus.sources
    )
    failures = []
    if not census.coverage.g0Passed:
        failures.append("U0_REQUIRED")
    if identityCensus.totalEntityCount == 0 or any(not source.sourceRevisions for source in identityCensus.sources):
        failures.append("IDENTITY_AUTHORITY_EMPTY")
    if collisionCount:
        failures.append("IDENTITY_COLLISION")
    if not replayValidation.valid:
        failures.append("SNAPSHOT_REPLAY_FAILED")
    if replayValidation.snapshotId != snapshot.snapshotId:
        failures.append("REPLAY_SUBJECT_MISMATCH")
    if any(not report.valid for report in contractValidations):
        failures.append("CONTRACT_VALIDATION_FAILED")
    if temporalFutureLeakCount:
        failures.append("TEMPORAL_FUTURE_LEAK")
    if falseMergeCount:
        failures.append("IDENTITY_FALSE_MERGE")
    if not controlPlaneIntegrity:
        failures.append("CONTROL_PLANE_INVALID")
    if snapshot.controlPlaneHeadId != currentControlPlaneHeadId:
        failures.append("CONTROL_HEAD_MISMATCH")
    orderedFailures = tuple(sorted(failures))
    base = {
        "u0SnapshotDigest": census.snapshotDigest,
        "identityCensusDigest": identityCensus.digest,
        "identityEntityCount": identityCensus.totalEntityCount,
        "identityCollisionCount": collisionCount,
        "universeSnapshotId": snapshot.snapshotId,
        "replayValidationDigest": replayValidation.digest,
        "contractValidationCount": len(contractValidations),
        "temporalFutureLeakCount": temporalFutureLeakCount,
        "falseMergeCount": falseMergeCount,
        "controlPlaneIntegrity": controlPlaneIntegrity,
        "g1Passed": not orderedFailures,
        "failureCodes": orderedFailures,
    }
    return G1Report(**base, digest=canonicalDigest(base))
