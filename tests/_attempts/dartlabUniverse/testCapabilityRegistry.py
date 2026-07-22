from __future__ import annotations

from dataclasses import replace

import pytest

from .execution.admission import ExecutionBudget, ExecutionPolicy, ExecutionRequest, admitExecution
from .execution.registry import buildCapabilityRegistry
from .execution.schemaDescriptor import buildContractCorpus, validateSchemaDescriptor, validateValue
from .sources.capabilitySource import enumerateCapabilities
from .validation.g2 import validateG2


@pytest.fixture(scope="module")
def liveRegistry():
    return buildCapabilityRegistry(enumerateCapabilities())


def testLiveCandidateUnionIsClosed(liveRegistry):
    candidateIds = [item.candidateId for item in liveRegistry.capabilities]
    assert len(candidateIds) == len(set(candidateIds))
    assert liveRegistry.discoveredCandidateCount == liveRegistry.classifiedCandidateCount
    assert liveRegistry.catalogCoverage == 1.0
    assert all(item.eligible or item.gapReasons for item in liveRegistry.capabilities)


def testEligibleSchemaClosurePassesG2(liveRegistry):
    report = validateG2(liveRegistry)
    assert report.passed, report.failureCodes
    assert liveRegistry.eligibleCallableCount > 100
    assert liveRegistry.validatedSchemaCount == liveRegistry.eligibleCallableCount
    assert liveRegistry.executionReadiness == 1.0
    assert liveRegistry.blockedEligibleCount == 0


def testAnalysisRegistryMirrorStateIsVisibleNotHidden(liveRegistry):
    analysisOnly = [item for item in liveRegistry.capabilities if item.candidateId.startswith("analysis.")]
    assert analysisOnly
    assert {item.status for item in analysisOnly} <= {"ACTIVE", "CALLABLE_UNMIRRORED"}
    assert all(item.eligible and item.schemaDescriptor is not None for item in analysisOnly)
    assert all(
        item.gapReasons == (() if item.status == "ACTIVE" else ("CAPABILITY_MIRROR_MISSING",)) for item in analysisOnly
    )


def testRuntimeOnlyScanAxesAreBlockedAsRegistryDrift(liveRegistry):
    for candidateId in ("scan.industry", "scan.market"):
        capability = liveRegistry.byCandidate(candidateId)
        assert capability is not None
        assert capability.status == "MIRRORED_MISSING"
        assert not capability.eligible
        assert capability.gapReasons == ("AXIS_NOT_REGISTERED",)


def testPreviewAndCompanyDeferredAreNotExecutable(liveRegistry):
    preview = liveRegistry.byCandidate("simulate")
    assert preview is not None
    assert preview.status == "HIDDEN_PREVIEW"
    assert not preview.eligible
    companyDeferred = [item for item in liveRegistry.capabilities if item.status == "SCHEMA_INCOMPLETE"]
    assert companyDeferred
    assert all(not item.eligible for item in companyDeferred)


def testSchemaWideningMutationIsRejected(liveRegistry):
    capability = next(item for item in liveRegistry.capabilities if item.eligible)
    descriptor = capability.schemaDescriptor
    assert descriptor is not None
    corpus = buildContractCorpus(descriptor)
    widenedArgs = dict(descriptor.argsSchema)
    widenedArgs["additionalProperties"] = True
    widened = replace(descriptor, argsSchema=widenedArgs)
    report = validateSchemaDescriptor(widened, corpus)
    assert not report.valid
    assert "INVALID_ARGS_ACCEPTED" in {item.code for item in report.issues}


def testSourceDigestMutationMakesDescriptorStale(liveRegistry):
    capability = next(item for item in liveRegistry.capabilities if item.eligible)
    descriptor = capability.schemaDescriptor
    assert descriptor is not None
    corpus = replace(buildContractCorpus(descriptor), sourceDigest="0" * 64)
    report = validateSchemaDescriptor(descriptor, corpus)
    assert not report.valid
    assert "SOURCE_DIGEST_STALE" in {item.code for item in report.issues}


def testScanAccountSchemaClosesDartAndEdgarMarketDispatch(liveRegistry):
    capability = liveRegistry.byCandidate("scan.account")
    assert capability is not None and capability.schemaDescriptor is not None
    schema = capability.schemaDescriptor.argsSchema
    assert validateValue({"target": "sales", "freq": "Y", "market": "dart"}, schema).valid
    assert validateValue({"target": "sales", "freq": "Y", "market": "edgar"}, schema).valid
    assert not validateValue({"target": "sales", "freq": "Y", "market": "unknown"}, schema).valid
    assert any(
        "providers/edgar/finance/scanAccount.py" in item for item in capability.schemaDescriptor.extractionEvidenceRefs
    )


def testInventedAxisCannotBeAdmitted(liveRegistry, tmp_path):
    request = ExecutionRequest(
        requestId="invented-axis",
        capabilityId="du:v1:capability:" + "0" * 64,
        snapshotId="du:v1:snapshot:" + "1" * 64,
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
    policy = ExecutionPolicy(controlRoot=tmp_path.as_posix())
    decision = admitExecution(request, liveRegistry, policy)
    assert not decision.admitted
    assert "CAPABILITY_NOT_FOUND" in decision.reasonCodes


def testLiveRuntimeDriftRequiresRecensus(monkeypatch):
    from .execution import registry as registryModule

    census = enumerateCapabilities()
    monkeypatch.setattr(registryModule, "loadCapabilities", lambda: {"invented": {}})
    with pytest.raises(ValueError, match="재센서스"):
        buildCapabilityRegistry(census)
