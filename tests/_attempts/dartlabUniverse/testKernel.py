from __future__ import annotations

from dataclasses import replace

import pytest

from .contracts import Replayability
from .execution.admission import ExecutionBudget, ExecutionPolicy, ExecutionRequest
from .kernel import UniverseKernel
from .provenance import UniverseSnapshot
from .sources.capabilitySource import enumerateCapabilities


def _snapshot(capabilityDigest: str) -> UniverseSnapshot:
    return UniverseSnapshot(
        snapshotId="du:v1:snapshot:" + "1" * 64,
        schemaVersion="du-snapshot-v1",
        sourceRevisionSet=(("repo", "revision"),),
        sourceInputs=(),
        blogRevision="blog",
        dirtyCaptureRefs=(),
        nonreplayableSourceRefs=(),
        mediaCatalogDigest="media",
        capabilityCatalogDigest=capabilityDigest,
        identityLedgerVersion="identity",
        conceptMappingVersion="concept",
        relationTaxonomyVersion="relation",
        schemaDescriptorSetVersion="schema",
        controlPlaneHeadId="2" * 64,
        visibilityScope="LOCAL",
        previousSnapshotId=None,
        coverageLedgerDigest="coverage",
        replayability=Replayability.VERIFIED,
        rootInputsDigest="1" * 64,
        createdAt="2026-07-19T00:00:00+00:00",
    )


def testKernelBindsSnapshotCensusAndExecutionStore(tmp_path):
    census = enumerateCapabilities()
    kernel = UniverseKernel.build(census, _snapshot(census.digest), ExecutionPolicy(controlRoot=tmp_path.as_posix()))
    assert kernel.registry.censusDigest == census.digest
    assert kernel.registry.executionReadiness == 1.0
    assert kernel.executionStore.verifyIntegrity()


def testKernelRejectsCapabilityDigestDrift(tmp_path):
    census = enumerateCapabilities()
    snapshot = replace(_snapshot(census.digest), capabilityCatalogDigest="0" * 64)
    with pytest.raises(ValueError, match="capability digest"):
        UniverseKernel.build(census, snapshot, ExecutionPolicy(controlRoot=tmp_path.as_posix()))


def testKernelSnapshotMismatchProducesAdmissionRejection(tmp_path):
    census = enumerateCapabilities()
    kernel = UniverseKernel.build(census, _snapshot(census.digest), ExecutionPolicy(controlRoot=tmp_path.as_posix()))
    capability = next(item for item in kernel.registry.capabilities if item.eligible)
    request = ExecutionRequest(
        requestId="snapshot-mismatch",
        capabilityId=capability.capabilityId,
        snapshotId="du:v1:snapshot:" + "9" * 64,
        targetRefs=("du:v1:entity:test",),
        args={},
        assumptionRefs=(),
        visibilityScope="LOCAL",
        budget=ExecutionBudget(),
        priority=5,
        deadline=None,
        idempotencyKey=None,
        requestedBy="test",
    )
    decision = kernel.admit(request)
    assert not decision.admitted
    assert "SOURCE_SNAPSHOT_MISMATCH" in decision.reasonCodes
