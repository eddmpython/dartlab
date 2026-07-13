"""Kill tests for signed, append-only admission receipts."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    AdmissionRegistryError,
    AdmissionVerifier,
    TrustedIssuer,
    artifactPath,
    initializeAdmissionRegistry,
    issueAdmissionReceipt,
    putAdmissionArtifact,
    verifyDetachedAdmissionReceipt,
)


def _keys() -> tuple[bytes, bytes]:
    private = Ed25519PrivateKey.generate()
    return (
        private.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        ),
        private.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        ),
    )


def _setup(tmp_path):
    database = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(database)
    private, public = _keys()
    trusted = {"key-1": TrustedIssuer("issuer-1", "key-1", public, "trusted")}
    verifier = AdmissionVerifier(database, artifacts, trusted)
    return database, artifacts, private, trusted, verifier


def _issue(
    database,
    artifacts,
    private,
    *,
    content=b"evidence",
    parents=(),
    status="admitted",
    issuedAt="20250102T000000Z",
):
    artifactHash = putAdmissionArtifact(artifacts, content)
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=private,
        kind="vintage",
        subjectHash="a" * 64,
        artifactHash=artifactHash,
        parentReceiptIds=parents,
        ruleId="vintage-as-known",
        ruleVersion="1",
        ruleHash="b" * 64,
        issuerId="issuer-1",
        issuerKeyId="key-1",
        issuerExecutableHash="c" * 64,
        knowledgeAsOf="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=4,
        status=status,
        issuedAt=issuedAt,
    )


def test_signed_receipt_verifies_artifact_and_append_only_chain(tmp_path) -> None:
    database, artifacts, private, _trusted, verifier = _setup(tmp_path)
    first = _issue(database, artifacts, private)
    second = _issue(database, artifacts, private, content=b"second", parents=(first.receiptId,))
    assert verifier.verify(first.receiptId).receiptId == first.receiptId
    assert verifier.verify(second.receiptId).parentReceiptIds == (first.receiptId,)
    assert second.previousReceiptHash
    with sqlite3.connect(database) as connection:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM receipts WHERE receipt_id=?", (first.receiptId,))
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE receipts SET payload_json='{}' WHERE receipt_id=?", (first.receiptId,))


def test_unknown_revoked_or_copied_signature_is_rejected(tmp_path) -> None:
    database, artifacts, private, trusted, verifier = _setup(tmp_path)
    receipt = _issue(database, artifacts, private)
    with pytest.raises(AdmissionRegistryError, match="unknown issuer key"):
        AdmissionVerifier(database, artifacts, {}).verify(receipt.receiptId)
    revoked = {"key-1": replace(trusted["key-1"], status="revoked")}
    with pytest.raises(AdmissionRegistryError, match="revoked issuer key"):
        AdmissionVerifier(database, artifacts, revoked).verify(receipt.receiptId)
    with pytest.raises(AdmissionRegistryError, match="signature"):
        verifyDetachedAdmissionReceipt(replace(receipt, subjectHash="d" * 64), trusted)
    assert verifier.verify(receipt.receiptId).status == "admitted"


def test_artifact_tamper_and_parent_downgrade_fail_closed(tmp_path) -> None:
    database, artifacts, private, trusted, _verifier = _setup(tmp_path)
    parent = _issue(database, artifacts, private, status="documented")
    with pytest.raises(AdmissionRegistryError, match="parent is not admitted"):
        _issue(database, artifacts, private, content=b"child", parents=(parent.receiptId,))
    admitted = _issue(database, artifacts, private, content=b"good")
    artifactPath(artifacts, admitted.artifactHash).write_bytes(b"tampered")
    with pytest.raises(AdmissionRegistryError, match="artifact hash mismatch"):
        AdmissionVerifier(database, artifacts, trusted).verify(admitted.receiptId)
    with pytest.raises(AdmissionRegistryError, match="registry is unavailable"):
        AdmissionVerifier(database.with_name("missing.sqlite"), artifacts, trusted).verify(admitted.receiptId)


def test_receipt_subject_and_kind_are_exact_runtime_contracts(tmp_path) -> None:
    database, artifacts, private, _trusted, verifier = _setup(tmp_path)
    receipt = _issue(database, artifacts, private)
    with pytest.raises(AdmissionRegistryError, match="subject mismatch"):
        verifier.verify(receipt.receiptId, expectedSubjectHash="d" * 64)
    with pytest.raises(AdmissionRegistryError, match="kind mismatch"):
        verifier.verify(receipt.receiptId, expectedKind="pathSet")
    with pytest.raises(AdmissionRegistryError, match="issued before"):
        _issue(database, artifacts, private, content=b"past-issuer", issuedAt="20241231T000000Z")
