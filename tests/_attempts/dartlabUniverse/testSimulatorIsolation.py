from __future__ import annotations

import base64
import json
import sqlite3
from dataclasses import replace
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    artifactPath,
    initializeAdmissionRegistry,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)

from .canonical import canonicalJson
from .execution.simulatorArtifactSchema import (
    SimulatorArtifactSchemaRegistry,
    buildSimulatorArtifactDescriptor,
)
from .execution.simulatorDecoderRegistry import (
    decodeSimulatorReceiptTree,
    jsonDecoderContract,
    validateSimulatorSemanticBundle,
)
from .execution.simulatorReceiptSource import verifySimulatorAdmission

SNAPSHOT_ID = "du:v1:snapshot:" + "1" * 64
PARENT_RULE_HASH = "2" * 64
ROOT_RULE_HASH = "3" * 64
PARENT_EXECUTABLE_HASH = "4" * 64
ROOT_EXECUTABLE_HASH = "5" * 64


def _writeConfig(path: Path, private: Ed25519PrivateKey, *, issuerId="issuer", keyId="key") -> None:
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    path.write_text(
        json.dumps(
            {
                "issuers": [
                    {
                        "issuerId": issuerId,
                        "issuerKeyId": keyId,
                        "publicKeyBase64": base64.b64encode(public).decode("ascii"),
                        "status": "trusted",
                    }
                ]
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _fixture(tmp_path, rootChanges=None):
    private = Ed25519PrivateKey.generate()
    privateBytes = private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    config = tmp_path / "issuers.json"
    _writeConfig(config, private)
    database = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(database)
    parentPayload = {
        "schemaVersion": "source-v1",
        "asOf": "20250101",
        "sourceSnapshotId": SNAPSHOT_ID,
    }
    parentHash = putAdmissionArtifact(artifacts, canonicalJson(parentPayload))
    parent = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="fixtureSource",
        subjectHash=parentHash,
        artifactHash=parentHash,
        parentReceiptIds=(),
        ruleId="fixture-source-rule",
        ruleVersion="1",
        ruleHash=PARENT_RULE_HASH,
        issuerId="issuer",
        issuerKeyId="key",
        issuerExecutableHash=PARENT_EXECUTABLE_HASH,
        knowledgeAsOf="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="D",
        stepSpan=1,
        maxAdmittedStep=0,
        status="admitted",
        issuedAt="2025-01-02T00:00:00+00:00",
    )
    rootPayload = {
        "schemaVersion": "result-v1",
        "sourceSnapshotId": SNAPSHOT_ID,
        "targetRefs": ["du:v1:entity:test"],
        "assumptionRefs": ["du:v1:assumption:test"],
        "asOf": "20250101",
        "revisionPolicy": "asKnown",
        "coverage": "asOfExact",
        "frequency": "D",
        "stepSpan": 1,
        "maxAdmittedStep": 0,
        "seed": 7,
        "simulatorVersion": "fixture-simulator-v1",
        "codeRevision": "git:test",
        "dependencyFingerprint": "6" * 64,
        "outputSchema": {"type": "object"},
        "outputDigest": "7" * 64,
        "epistemicClass": "SIMULATED",
        "declaredSubject": "wrong",
    }
    rootPayload.update(rootChanges or {})
    rootHash = putAdmissionArtifact(artifacts, canonicalJson(rootPayload))
    root = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="fixtureResult",
        subjectHash=rootHash,
        artifactHash=rootHash,
        parentReceiptIds=(parent.receiptId,),
        ruleId="fixture-result-rule",
        ruleVersion="1",
        ruleHash=ROOT_RULE_HASH,
        issuerId="issuer",
        issuerKeyId="key",
        issuerExecutableHash=ROOT_EXECUTABLE_HASH,
        knowledgeAsOf="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="D",
        stepSpan=1,
        maxAdmittedStep=0,
        status="admitted",
        issuedAt="2025-01-02T00:00:00+00:00",
    )
    decoderId, decoderDigest = jsonDecoderContract()
    parentDescriptor = buildSimulatorArtifactDescriptor(
        receiptVersion=parent.receiptVersion,
        kind=parent.kind,
        ruleId=parent.ruleId,
        ruleVersion=parent.ruleVersion,
        ruleHash=parent.ruleHash,
        issuerExecutableHash=parent.issuerExecutableHash,
        artifactRole="SOURCE",
        mediaType="application/json",
        schemaVersion="source-v1",
        decoderId=decoderId,
        decoderDigest=decoderDigest,
        subjectHashRule="ARTIFACT_HASH",
        subjectBinding=None,
        parentRoles=(),
        fieldBindings=(("asOf", "asOf"), ("sourceSnapshotId", "sourceSnapshotId")),
        requiredSemanticFields=("asOf", "sourceSnapshotId"),
        seedPolicy="FORBIDDEN",
    )
    bindings = tuple((name, name) for name in rootPayload)
    rootDescriptor = buildSimulatorArtifactDescriptor(
        receiptVersion=root.receiptVersion,
        kind=root.kind,
        ruleId=root.ruleId,
        ruleVersion=root.ruleVersion,
        ruleHash=root.ruleHash,
        issuerExecutableHash=root.issuerExecutableHash,
        artifactRole="RESULT",
        mediaType="application/json",
        schemaVersion="result-v1",
        decoderId=decoderId,
        decoderDigest=decoderDigest,
        subjectHashRule="ARTIFACT_HASH",
        subjectBinding=None,
        parentRoles=("SOURCE",),
        fieldBindings=bindings,
        requiredSemanticFields=tuple(name for name, _ in bindings),
        seedPolicy="REQUIRED",
    )
    registry = SimulatorArtifactSchemaRegistry((parentDescriptor, rootDescriptor))
    return {
        "private": private,
        "config": config,
        "database": database,
        "artifacts": artifacts,
        "parent": parent,
        "root": root,
        "parentDescriptor": parentDescriptor,
        "rootDescriptor": rootDescriptor,
        "registry": registry,
    }


def _registration(fixture):
    return verifySimulatorAdmission(
        fixture["database"],
        fixture["artifacts"],
        fixture["root"].receiptId,
        fixture["config"],
    )


def testSignedReceiptTreeDecodesAndValidatesAsSimulated(tmp_path):
    fixture = _fixture(tmp_path)
    registration = _registration(fixture)
    assert registration.status == "VERIFIED_ADMISSION_RECEIPT", registration.issues
    assert len(registration.receiptTree) == 2
    bundle = decodeSimulatorReceiptTree(registration, fixture["registry"])
    assert bundle.status == "DECODED_SIMULATED", bundle.issues
    assert bundle.epistemicClass == "SIMULATED"
    report = validateSimulatorSemanticBundle(bundle, {"snapshotId": SNAPSHOT_ID})
    assert report.valid, report.issues


def testUnknownIssuerIsRejectedBeforeArtifactMeaning(tmp_path):
    fixture = _fixture(tmp_path)
    other = Ed25519PrivateKey.generate()
    _writeConfig(fixture["config"], other)
    registration = _registration(fixture)
    assert registration.status == "REJECTED_INVALID_ADMISSION_RECEIPT"
    assert registration.root is None


def testMissingArtifactRejectsAdmission(tmp_path):
    fixture = _fixture(tmp_path)
    artifactPath(fixture["artifacts"], fixture["root"].artifactHash).unlink()
    registration = _registration(fixture)
    assert registration.status == "REJECTED_INVALID_ADMISSION_RECEIPT"


def testBrokenParentChainRejectsAdmission(tmp_path):
    fixture = _fixture(tmp_path)
    with sqlite3.connect(fixture["database"]) as connection:
        connection.execute("DROP TRIGGER receipts_no_delete")
        connection.execute("DELETE FROM receipts WHERE receipt_id=?", (fixture["parent"].receiptId,))
    registration = _registration(fixture)
    assert registration.status == "REJECTED_INVALID_ADMISSION_RECEIPT"


def testUnknownSchemaRemainsUninterpretedAndCannotValidate(tmp_path):
    fixture = _fixture(tmp_path)
    registration = _registration(fixture)
    registry = SimulatorArtifactSchemaRegistry((fixture["parentDescriptor"],))
    bundle = decodeSimulatorReceiptTree(registration, registry)
    assert bundle.status == "VERIFIED_ARTIFACT_UNINTERPRETED"
    assert any("SIMULATOR_SCHEMA_DESCRIPTOR_MISSING" in issue for issue in bundle.issues)
    assert not validateSimulatorSemanticBundle(bundle, {"snapshotId": SNAPSHOT_ID}).valid


def testStaleDecoderRemainsUninterpreted(tmp_path):
    fixture = _fixture(tmp_path)
    stale = replace(fixture["rootDescriptor"], decoderDigest="0" * 64)
    registry = SimulatorArtifactSchemaRegistry((fixture["parentDescriptor"], stale))
    bundle = decodeSimulatorReceiptTree(_registration(fixture), registry)
    assert bundle.status == "VERIFIED_ARTIFACT_UNINTERPRETED"
    assert any("SIMULATOR_DECODER_STALE" in issue for issue in bundle.issues)


def testSubjectBindingMismatchIsRejected(tmp_path):
    fixture = _fixture(tmp_path)
    mismatched = replace(
        fixture["rootDescriptor"],
        subjectHashRule="FIELD_VALUE",
        subjectBinding="declaredSubject",
    )
    registry = SimulatorArtifactSchemaRegistry((fixture["parentDescriptor"], mismatched))
    bundle = decodeSimulatorReceiptTree(_registration(fixture), registry)
    assert bundle.status == "VERIFIED_ARTIFACT_UNINTERPRETED"
    assert any("SIMULATOR_SUBJECT_MISMATCH" in issue for issue in bundle.issues)


def testParentRoleMismatchIsRejected(tmp_path):
    fixture = _fixture(tmp_path)
    mismatched = replace(fixture["rootDescriptor"], parentRoles=("OTHER",))
    registry = SimulatorArtifactSchemaRegistry((fixture["parentDescriptor"], mismatched))
    bundle = decodeSimulatorReceiptTree(_registration(fixture), registry)
    assert bundle.status == "VERIFIED_ARTIFACT_UNINTERPRETED"
    assert any("SIMULATOR_PARENT_ROLE_MISMATCH" in issue for issue in bundle.issues)


def testArtifactSchemaVersionMismatchIsRejected(tmp_path):
    fixture = _fixture(tmp_path)
    mismatched = replace(fixture["rootDescriptor"], schemaVersion="result-v2")
    registry = SimulatorArtifactSchemaRegistry((fixture["parentDescriptor"], mismatched))
    bundle = decodeSimulatorReceiptTree(_registration(fixture), registry)
    assert bundle.status == "VERIFIED_ARTIFACT_UNINTERPRETED"
    assert any("schemaVersion" in issue for issue in bundle.issues)


def testMissingStochasticSeedFailsSemanticValidation(tmp_path):
    fixture = _fixture(tmp_path, {"seed": None})
    bundle = decodeSimulatorReceiptTree(_registration(fixture), fixture["registry"])
    report = validateSimulatorSemanticBundle(bundle, {"snapshotId": SNAPSHOT_ID})
    assert not report.valid
    assert "NONDETERMINISTIC_WITHOUT_SEED" in {item.code for item in report.issues}


def testSnapshotAndVintageMismatchFailSemanticValidation(tmp_path):
    fixture = _fixture(tmp_path, {"sourceSnapshotId": "du:v1:snapshot:" + "9" * 64, "asOf": "20241231"})
    bundle = decodeSimulatorReceiptTree(_registration(fixture), fixture["registry"])
    report = validateSimulatorSemanticBundle(bundle, {"snapshotId": SNAPSHOT_ID})
    codes = {item.code for item in report.issues}
    assert "SIMULATION_SNAPSHOT_MISMATCH" in codes
    assert "SIMULATOR_VINTAGE_MISMATCH" in codes


def testReceiptAndDecodedStepContractMismatchFails(tmp_path):
    fixture = _fixture(tmp_path, {"frequency": "M", "stepSpan": 2, "maxAdmittedStep": 3})
    bundle = decodeSimulatorReceiptTree(_registration(fixture), fixture["registry"])
    report = validateSimulatorSemanticBundle(bundle, {"snapshotId": SNAPSHOT_ID})
    assert not report.valid
    assert "SIMULATOR_RECEIPT_SEMANTIC_MISMATCH" in {item.code for item in report.issues}


def testObservedLeakageFailsSemanticValidation(tmp_path):
    fixture = _fixture(tmp_path, {"epistemicClass": "OBSERVED"})
    bundle = decodeSimulatorReceiptTree(_registration(fixture), fixture["registry"])
    report = validateSimulatorSemanticBundle(bundle, {"snapshotId": SNAPSHOT_ID})
    assert not report.valid
    assert "SIMULATED_CLASS_LEAKAGE" in {item.code for item in report.issues}
