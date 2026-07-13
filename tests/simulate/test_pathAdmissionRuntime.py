"""Kill tests for signed path-set admission and provider-neutral vintages."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    AdmissionVerifier,
    TrustedIssuer,
    artifactPath,
    initializeAdmissionRegistry,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)
from dartlab.simulate.vintage import VintageRef, canonicalPayloadHash, worldStatePayloadHash
from dartlab.simulate.world import (
    LawSpec,
    ScenarioPath,
    SimulationSpecError,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    bindAdmittedPathContent,
    bindPathAdmissionReceipt,
    pathSetAdmissionArtifact,
    pathSetAdmissionSubjectHash,
    simulateWorld,
)


def _model() -> WorldModel:
    return WorldModel(
        "signed-path-world",
        "1",
        (VariableSpec("shock", "ratio", "shock"), VariableSpec("value", "ratio", "metric")),
        (),
        (
            LawSpec(
                "identity",
                outputs=("value",),
                shockInputs=("shock",),
                fn=lambda ctx: {"value": ctx.shocks["shock"]},
            ),
        ),
    )


def _strategy() -> tuple[StrategySpec, ...]:
    return (StrategySpec("baseline", ({},), isBaseline=True),)


def _trust(tmp_path):
    database = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(database)
    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    trusted = {"test-key": TrustedIssuer("test-issuer", "test-key", public)}
    verifier = AdmissionVerifier(database, artifacts, trusted)
    return database, artifacts, private.private_bytes_raw(), trusted, verifier


def _issueVintage(database, artifacts, private, trusted, *, policy="asKnown", coverage="asOfExact"):
    normalized = {"provider": "test", "observations": [["20241231", 0.1]]}
    rawHash = putAdmissionArtifact(artifacts, b"immutable source bytes")
    payloadHash = canonicalPayloadHash(normalized)
    status = "verifiedVintage" if (policy, coverage) == ("asKnown", "asOfExact") else "documented"
    receipt = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=private,
        kind="dataVintage",
        subjectHash=payloadHash,
        artifactHash=rawHash,
        parentReceiptIds=(),
        ruleId="pit-vintage",
        ruleVersion="1",
        ruleHash=sha256(b"pit-vintage-v1").hexdigest(),
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"issuer-v1").hexdigest(),
        knowledgeAsOf="20250101",
        revisionPolicy=policy,
        coverage=coverage,
        frequency="step",
        stepSpan=1,
        maxAdmittedStep=1,
        status=status,
        issuedAt="20250102T000000Z",
        trustedIssuers=trusted,
    )
    return VintageRef(
        artifactKind="shockPanel",
        provider="test",
        artifactId="panel-20250101",
        artifactHash=rawHash,
        payloadHash=payloadHash,
        knowledgeAsOf="20250101",
        availableAt="20250101",
        revisionPolicy=policy,
        coverage=coverage,
        eventThrough="20241231",
        receiptId=receipt.receiptId,
    )


def _issuePath(tmp_path):
    database, artifacts, private, trusted, verifier = _trust(tmp_path)
    vintage = _issueVintage(database, artifacts, private, trusted)
    path = ScenarioPath(
        "signed",
        ({"shock": 0.1},),
        certificateId="a" * 64,
        validationStatus="admitted",
        maxAdmittedStep=1,
        knowledgeAsOf="20250101",
        historyStatus="asKnown",
        vintage=vintage,
    )
    paths = bindAdmittedPathContent((path,))
    artifactHash = putAdmissionArtifact(artifacts, pathSetAdmissionArtifact(paths))
    assert artifactHash == pathSetAdmissionSubjectHash(paths)
    receipt = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=private,
        kind="pathSet",
        subjectHash=artifactHash,
        artifactHash=artifactHash,
        parentReceiptIds=(vintage.receiptId,),
        ruleId="path-admission",
        ruleVersion="1",
        ruleHash=sha256(b"path-admission-v1").hexdigest(),
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"path-issuer-v1").hexdigest(),
        knowledgeAsOf="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="step",
        stepSpan=1,
        maxAdmittedStep=1,
        status="admitted",
        issuedAt="20250102T000000Z",
        trustedIssuers=trusted,
    )
    return bindPathAdmissionReceipt(paths, receipt.receiptId), verifier, artifacts


def _run(paths, verifier=None, *, decisionAsOf="20250102"):
    return simulateWorld(
        _model(),
        WorldState({}, asOf="20250101", knowledgeAsOf="20250101", decisionAsOf=decisionAsOf),
        paths,
        _strategy(),
        admissionVerifier=verifier,
    )


def testSignedPathSetExecutesButDigestOnlyClaimDoesNot(tmp_path) -> None:
    paths, verifier, _ = _issuePath(tmp_path)
    assert _run(paths, verifier).traces[0].steps[0].after["value"] == pytest.approx(0.1)
    with pytest.raises(SimulationSpecError, match="runtime admission verifier"):
        _run(paths)
    fake = tuple(replace(path, admissionReceiptId="b" * 64) for path in paths)
    with pytest.raises(SimulationSpecError, match="admission verification failed"):
        _run(fake, verifier)
    with pytest.raises(SimulationSpecError, match="not available by decisionAsOf"):
        _run(paths, verifier, decisionAsOf="20250101")


def testSignedPathArtifactIsRehashedAtExecution(tmp_path) -> None:
    paths, verifier, artifacts = _issuePath(tmp_path)
    artifactPath(artifacts, paths[0].admissionContentHash).write_bytes(b"tampered path-set artifact")
    with pytest.raises(SimulationSpecError, match="artifact hash mismatch"):
        _run(paths, verifier)


def testLatestRetainedPeriodOnlyVintageCannotBeAdmitted(tmp_path) -> None:
    database, artifacts, private, trusted, verifier = _trust(tmp_path)
    vintage = _issueVintage(database, artifacts, private, trusted, policy="latestRetained", coverage="periodOnly")
    path = ScenarioPath(
        "dart-latest",
        ({"shock": 0.1},),
        certificateId="a" * 64,
        validationStatus="admitted",
        maxAdmittedStep=1,
        knowledgeAsOf="20250101",
        historyStatus="asKnown",
        vintage=vintage,
    )
    with pytest.raises(SimulationSpecError, match="exact as-known vintage"):
        _run(bindAdmittedPathContent((path,)), verifier)


def testWorldStateVintageBindsActualValues() -> None:
    values = {"unused": 1.0}
    vintage = VintageRef(
        artifactKind="worldState",
        provider="test",
        artifactId="state-1",
        artifactHash="a" * 64,
        payloadHash=worldStatePayloadHash(values, step=0, asOf="20250101", refs=("source",)),
        knowledgeAsOf="20250101",
        availableAt="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
    )
    state = WorldState(
        {"unused": 2.0},
        asOf="20250101",
        refs=("source",),
        knowledgeAsOf="20250101",
        decisionAsOf="20250101",
        vintage=vintage,
    )
    path = ScenarioPath("plain", ({"shock": 0.1},))
    with pytest.raises(SimulationSpecError, match="payload hash mismatch"):
        simulateWorld(_model(), state, (path,), _strategy())
