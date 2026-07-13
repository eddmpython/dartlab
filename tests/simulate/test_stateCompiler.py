from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    AdmissionVerifier,
    TrustedIssuer,
    initializeAdmissionRegistry,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)
from dartlab.simulate.stateCompiler import (
    StateCompilerError,
    StateCompileSpec,
    buildProviderObservationBatch,
    compilePointInTimeState,
    issuePointInTimeState,
    issueProviderObservationBatch,
    makeVariableObservation,
    validateCompiledPointInTimeState,
)
from dartlab.simulate.stateVariables import StateVariableSpec, buildStateVariableRegistry
from dartlab.simulate.vintage import VintageRef
from dartlab.simulate.world import (
    VariableSpec,
    WorldModel,
    initialStatePrimitives,
    worldStateFromCompiled,
)


def _context(tmp_path):
    registry = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(registry)
    private = Ed25519PrivateKey.generate()
    privateBytes = private.private_bytes_raw()
    trusted = {
        "pit-key": TrustedIssuer(
            issuerId="pit-issuer",
            issuerKeyId="pit-key",
            publicKey=private.public_key().public_bytes_raw(),
        )
    }
    return registry, artifacts, privateBytes, trusted


def _sourceReceipt(context, content: bytes, *, issuedAt: str = "20250102T000000Z"):
    registry, artifacts, privateBytes, trusted = context
    artifactHash = putAdmissionArtifact(artifacts, content)
    return issueAdmissionReceipt(
        registry,
        artifacts,
        privateKey=privateBytes,
        kind="dataVintage",
        subjectHash=artifactHash,
        artifactHash=artifactHash,
        parentReceiptIds=(),
        ruleId="provider-source-v1",
        ruleVersion="1",
        ruleHash=sha256(b"provider-source-v1").hexdigest(),
        issuerId="pit-issuer",
        issuerKeyId="pit-key",
        issuerExecutableHash=sha256(b"provider-source-issuer-v1").hexdigest(),
        knowledgeAsOf="20250102",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=0,
        status="verifiedVintage",
        issuedAt=issuedAt,
        trustedIssuers=trusted,
    )


def _variableSpec() -> StateVariableSpec:
    return StateVariableSpec(
        variableId="financial.revenue",
        signalId="financial.revenue",
        providerId="edgar",
        datasetId="quarterly-financial",
        unit="USD",
        role="state",
        evidenceRole="observed",
        frequency="quarter",
        timing="flow",
        transformId="level-v1",
        maxStalenessDays=400,
        lower=0.0,
    )


def _observation(
    sourceReceipt,
    *,
    value: float = 100.0,
    eventAt: str = "20241231",
    availableAt: str = "20250102",
    knowledgeAsOf: str = "20250102",
    revisionId: str = "original",
    revisionPolicy: str = "asKnown",
    coverage: str = "asOfExact",
):
    artifactHash = sourceReceipt.artifactHash if sourceReceipt is not None else sha256(b"unsigned").hexdigest()
    receiptId = sourceReceipt.receiptId if sourceReceipt is not None else ""
    vintage = VintageRef(
        artifactKind="providerObservation",
        provider="edgar",
        artifactId=f"revenue-{revisionId}",
        artifactHash=artifactHash,
        payloadHash=artifactHash,
        knowledgeAsOf=knowledgeAsOf,
        availableAt=availableAt,
        revisionPolicy=revisionPolicy,
        coverage=coverage,
        fiscalThrough=eventAt,
        receiptId=receiptId,
    )
    return makeVariableObservation(
        providerId="edgar",
        datasetId="quarterly-financial",
        entityId="AAPL",
        signalId="financial.revenue",
        value=value,
        unit="USD",
        frequency="quarter",
        timing="flow",
        transformId="level-v1",
        evidenceRole="observed",
        eventAt=eventAt,
        availableAt=availableAt,
        knowledgeAsOf=knowledgeAsOf,
        availabilityPrecision="date",
        revisionId=revisionId,
        vintage=vintage,
        normalizationRuleHash=sha256(b"edgar-quarterly-financial-v1").hexdigest(),
    )


def _compileSpec(decisionAsOf: str = "20250201", *, requireExact: bool = False) -> StateCompileSpec:
    return StateCompileSpec(
        entityId="AAPL",
        market="US",
        decisionAsOf=decisionAsOf,
        consumerId="quarterly-operating-world",
        consumerVersion="1",
        variableIds=("financial.revenue",),
        requireExact=requireExact,
    )


def _batch(observations, cutoffAsOf="20250201"):
    return buildProviderObservationBatch(
        tuple(observations),
        providerId="edgar",
        datasetId="quarterly-financial",
        entityId="AAPL",
        signalIds=("financial.revenue",),
        cutoffAsOf=cutoffAsOf,
    )


def testFutureRevisionCannotChangePastState(tmp_path) -> None:
    context = _context(tmp_path)
    originalReceipt = _sourceReceipt(context, b"original")
    amendedReceipt = _sourceReceipt(context, b"amended", issuedAt="20250402T000000Z")
    original = _observation(originalReceipt)
    amended = _observation(
        amendedReceipt,
        value=130.0,
        availableAt="20250402",
        knowledgeAsOf="20250402",
        revisionId="amended",
    )
    registry = buildStateVariableRegistry((_variableSpec(),))
    assert _batch((original,)) == _batch((original, amended))
    assert (
        compilePointInTimeState(registry, (_batch((original, amended)),), _compileSpec()).statePrimitives[0].value
        == 100.0
    )
    may = compilePointInTimeState(
        registry,
        (_batch((original, amended), "20250501"),),
        _compileSpec("20250501"),
    )
    assert may.statePrimitives[0].value == 130.0


def testConditionalAndSameDayEvidenceCannotBecomeExact(tmp_path) -> None:
    context = _context(tmp_path)
    source = _sourceReceipt(context, b"source")
    registry = buildStateVariableRegistry((_variableSpec(),))
    latest = _observation(None, revisionPolicy="latestRetained", coverage="periodOnly")
    conditional = compilePointInTimeState(registry, (_batch((latest,)),), _compileSpec())
    assert conditional.historyStatus == "conditional"
    with pytest.raises(StateCompilerError, match="requires exact"):
        compilePointInTimeState(registry, (_batch((latest,)),), _compileSpec(requireExact=True))
    sameDay = _observation(source, availableAt="20250201", knowledgeAsOf="20250201")
    assert compilePointInTimeState(registry, (_batch((sameDay,)),), _compileSpec()).historyStatus == "conditional"


def testMissingStaleAndMeaningDriftFailClosed(tmp_path) -> None:
    context = _context(tmp_path)
    source = _sourceReceipt(context, b"source")
    registry = buildStateVariableRegistry((_variableSpec(),))
    with pytest.raises(StateCompilerError, match="missing"):
        compilePointInTimeState(registry, (_batch(()),), _compileSpec())
    staleRegistry = buildStateVariableRegistry((replace(_variableSpec(), maxStalenessDays=1),))
    with pytest.raises(StateCompilerError, match="stale"):
        compilePointInTimeState(staleRegistry, (_batch((_observation(source),)),), _compileSpec())
    drifted = replace(_observation(source), timing="stock", observationId="")
    drifted = replace(drifted, observationId=sha256(b"wrong").hexdigest())
    with pytest.raises(StateCompilerError, match="content hash"):
        _batch((drifted,))


def testExactCompleteBatchAndStateReceiptRoundTrip(tmp_path) -> None:
    context = _context(tmp_path)
    registryPath, artifacts, privateBytes, trusted = context
    source = _sourceReceipt(context, b"source")
    signedBatch = issueProviderObservationBatch(
        _batch((_observation(source),)),
        registryPath,
        artifacts,
        privateKey=privateBytes,
        issuerId="pit-issuer",
        issuerKeyId="pit-key",
        issuedAt="20250201T000000Z",
        trustedIssuers=trusted,
    )
    verifier = AdmissionVerifier(registryPath, artifacts, trusted)
    registry = buildStateVariableRegistry((_variableSpec(),))
    compiled = compilePointInTimeState(
        registry,
        (signedBatch,),
        _compileSpec(requireExact=True),
        admissionVerifier=verifier,
    )
    assert compiled.historyStatus == "exact"
    assert compiled.admissionStatus == "documented"
    issued = issuePointInTimeState(
        compiled,
        registryPath,
        artifacts,
        privateKey=privateBytes,
        issuerId="pit-issuer",
        issuerKeyId="pit-key",
        issuedAt="20250201T000000Z",
        trustedIssuers=trusted,
    )
    assert issued.admissionStatus == "admitted"
    receipt = validateCompiledPointInTimeState(issued, verifier)
    assert receipt.parentReceiptIds == (signedBatch.batchReceiptId,)


def testWorldStateCanOnlyUseCompiledValuesAndMeaning(tmp_path) -> None:
    context = _context(tmp_path)
    registryPath, artifacts, privateBytes, trusted = context
    source = _sourceReceipt(context, b"source")
    batch = issueProviderObservationBatch(
        _batch((_observation(source),)),
        registryPath,
        artifacts,
        privateKey=privateBytes,
        issuerId="pit-issuer",
        issuerKeyId="pit-key",
        issuedAt="20250201T000000Z",
        trustedIssuers=trusted,
    )
    verifier = AdmissionVerifier(registryPath, artifacts, trusted)
    compiled = compilePointInTimeState(
        buildStateVariableRegistry((_variableSpec(),)),
        (batch,),
        _compileSpec(requireExact=True),
        admissionVerifier=verifier,
    )
    initial = worldStateFromCompiled(compiled)
    model = WorldModel(
        "pit-test-world",
        "1",
        (
            VariableSpec(
                "financial.revenue",
                "USD",
                "state",
                lower=0.0,
                frequency="quarter",
                timing="flow",
                transformId="level-v1",
                evidenceRole="observed",
            ),
        ),
        (),
        (),
        stepFrequency="quarter",
    )
    assert initialStatePrimitives(model, initial) == compiled.statePrimitives
    assert initial.stateCompilationContractHash == compiled.stateCompilationContractHash


def testManifestChangesWithValueRegistryAndCutoff(tmp_path) -> None:
    context = _context(tmp_path)
    source = _sourceReceipt(context, b"source")
    registry = buildStateVariableRegistry((_variableSpec(),))
    batch = _batch((_observation(source),))
    first = compilePointInTimeState(registry, (batch,), _compileSpec())
    changedValue = compilePointInTimeState(registry, (_batch((_observation(source, value=101.0),)),), _compileSpec())
    changedRegistry = compilePointInTimeState(
        buildStateVariableRegistry((replace(_variableSpec(), maxStalenessDays=401),)),
        (batch,),
        _compileSpec(),
    )
    nextDay = compilePointInTimeState(
        registry,
        (_batch((_observation(source),), "20250202"),),
        _compileSpec("20250202"),
    )
    assert len({first.manifestHash, changedValue.manifestHash, changedRegistry.manifestHash, nextDay.manifestHash}) == 4
    assert first.stateCompilationContractHash == nextDay.stateCompilationContractHash
    assert first.stateCompilationContractHash != changedRegistry.stateCompilationContractHash
