"""Signed append-only admission receipts over content-addressed artifacts.

The runtime verifier receives only allowlisted Ed25519 public keys. Issuance is
kept in a separate function that requires private-key bytes supplied by the
operator environment; the registry never stores private keys. SQLite triggers
make normal writes append-only, while the hash chain and artifact rehashing
detect row or evidence mutation during read-only verification.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import sqlite3
import tempfile
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

_DOMAIN = b"dartlab.admission.receipt.v1\0"
_RECEIPT_VERSION = "admission-receipt-v1"
_STATUS_SET = {
    "documented",
    "verifiedVintage",
    "retrospectiveOnly",
    "admitted",
    "policyAdmitted",
    "rejected",
}
_REVISION_POLICIES = {"asKnown", "latestRetained", "revisedHistory", "synthetic", "explicitAssumption"}
_COVERAGE_KINDS = {"asOfExact", "latestOnly", "periodOnly", "synthetic"}
_ADMITTED_PARENT_STATUSES = {"verifiedVintage", "admitted", "policyAdmitted"}


class AdmissionRegistryError(RuntimeError):
    """Raised when a registry, receipt, signature, chain, or artifact is invalid."""


@dataclass(frozen=True)
class TrustedIssuer:
    """A runtime trust anchor supplied by application configuration."""

    issuerId: str
    issuerKeyId: str
    publicKey: bytes
    status: str = "trusted"


@dataclass(frozen=True)
class AdmissionReceipt:
    """A signed relational claim over one immutable artifact and its parents."""

    receiptId: str
    receiptVersion: str
    kind: str
    subjectHash: str
    artifactHash: str
    parentReceiptIds: tuple[str, ...]
    ruleId: str
    ruleVersion: str
    ruleHash: str
    issuerId: str
    issuerKeyId: str
    issuerExecutableHash: str
    knowledgeAsOf: str
    revisionPolicy: str
    coverage: str
    frequency: str
    stepSpan: int
    maxAdmittedStep: int
    status: str
    previousReceiptHash: str
    issuedAt: str
    signature: str


def _hashBytes(content: bytes) -> str:
    return sha256(content).hexdigest()


def _hashFile(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _dateText(value: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise AdmissionRegistryError(f"invalid receipt knowledge cutoff: {value}")
    return text


def _receiptPayload(receipt: AdmissionReceipt) -> dict:
    return {
        "receiptVersion": receipt.receiptVersion,
        "kind": receipt.kind,
        "subjectHash": receipt.subjectHash,
        "artifactHash": receipt.artifactHash,
        "parentReceiptIds": receipt.parentReceiptIds,
        "ruleId": receipt.ruleId,
        "ruleVersion": receipt.ruleVersion,
        "ruleHash": receipt.ruleHash,
        "issuerId": receipt.issuerId,
        "issuerKeyId": receipt.issuerKeyId,
        "issuerExecutableHash": receipt.issuerExecutableHash,
        "knowledgeAsOf": receipt.knowledgeAsOf,
        "revisionPolicy": receipt.revisionPolicy,
        "coverage": receipt.coverage,
        "frequency": receipt.frequency,
        "stepSpan": receipt.stepSpan,
        "maxAdmittedStep": receipt.maxAdmittedStep,
        "status": receipt.status,
        "previousReceiptHash": receipt.previousReceiptHash,
        "issuedAt": receipt.issuedAt,
    }


def _payloadBytes(receipt: AdmissionReceipt) -> bytes:
    raw = json.dumps(
        _receiptPayload(receipt),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _DOMAIN + raw


def _rowHash(receipt: AdmissionReceipt) -> str:
    return _hashBytes(
        b"dartlab.admission.registry-row.v1\0"
        + receipt.previousReceiptHash.encode("ascii")
        + receipt.receiptId.encode("ascii")
        + base64.b64decode(receipt.signature, validate=True)
    )


def _validateReceiptContract(receipt: AdmissionReceipt) -> None:
    if receipt.receiptVersion != _RECEIPT_VERSION or not receipt.kind:
        raise AdmissionRegistryError("receipt protocol mismatch")
    for label, value in (
        ("subject", receipt.subjectHash),
        ("artifact", receipt.artifactHash),
        ("rule", receipt.ruleHash),
        ("issuer executable", receipt.issuerExecutableHash),
    ):
        if not _validDigest(value):
            raise AdmissionRegistryError(f"receipt {label} hash is invalid")
    if receipt.previousReceiptHash and not _validDigest(receipt.previousReceiptHash):
        raise AdmissionRegistryError("receipt previous hash is invalid")
    if (
        not receipt.ruleId
        or not receipt.ruleVersion
        or not receipt.issuerId
        or not receipt.issuerKeyId
        or not receipt.issuedAt
    ):
        raise AdmissionRegistryError("receipt identity fields are incomplete")
    if receipt.status not in _STATUS_SET:
        raise AdmissionRegistryError("receipt status is invalid")
    if receipt.revisionPolicy not in _REVISION_POLICIES or receipt.coverage not in _COVERAGE_KINDS:
        raise AdmissionRegistryError("receipt vintage contract is invalid")
    if receipt.stepSpan < 1 or receipt.maxAdmittedStep < 0 or not receipt.frequency:
        raise AdmissionRegistryError("receipt step contract is invalid")
    if len(set(receipt.parentReceiptIds)) != len(receipt.parentReceiptIds) or any(
        not _validDigest(receiptId) for receiptId in receipt.parentReceiptIds
    ):
        raise AdmissionRegistryError("receipt parent contract is invalid")
    knowledgeCutoff = _dateText(receipt.knowledgeAsOf)
    if knowledgeCutoff > _dateText(receipt.issuedAt):
        raise AdmissionRegistryError("receipt is issued before its knowledge cutoff")
    if receipt.status in {"verifiedVintage", "admitted", "policyAdmitted"} and (
        receipt.revisionPolicy != "asKnown" or receipt.coverage != "asOfExact"
    ):
        raise AdmissionRegistryError("admitted receipt needs exact as-known vintage")


def initializeAdmissionRegistry(databasePath: str | Path) -> None:
    """Create the append-only receipt table and mutation-blocking triggers."""

    path = Path(databasePath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL,
                signature BLOB NOT NULL,
                previous_receipt_hash TEXT NOT NULL,
                row_hash TEXT NOT NULL UNIQUE
            );
            CREATE TRIGGER IF NOT EXISTS receipts_no_update
            BEFORE UPDATE ON receipts
            BEGIN
                SELECT RAISE(ABORT, 'receipts are append-only');
            END;
            CREATE TRIGGER IF NOT EXISTS receipts_no_delete
            BEFORE DELETE ON receipts
            BEGIN
                SELECT RAISE(ABORT, 'receipts are append-only');
            END;
            """
        )


def artifactPath(artifactRoot: str | Path, artifactHash: str) -> Path:
    """Return the deterministic content-addressed location of an artifact."""

    if not _validDigest(artifactHash):
        raise AdmissionRegistryError("artifact hash is invalid")
    root = Path(artifactRoot)
    return root / artifactHash[:2] / artifactHash


def putAdmissionArtifact(artifactRoot: str | Path, content: bytes) -> str:
    """Atomically store immutable bytes under their SHA-256 content address."""

    artifactHash = _hashBytes(bytes(content))
    target = artifactPath(artifactRoot, artifactHash)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if _hashFile(target) != artifactHash:
            raise AdmissionRegistryError("existing admission artifact hash mismatch")
        return artifactHash
    descriptor, temporary = tempfile.mkstemp(prefix=f".{artifactHash}.", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return artifactHash


def verifyDetachedAdmissionReceipt(
    receipt: AdmissionReceipt,
    trustedIssuers: Mapping[str, TrustedIssuer],
) -> AdmissionReceipt:
    """Verify one receipt against an application-owned public-key allowlist."""

    _validateReceiptContract(receipt)
    trusted = trustedIssuers.get(receipt.issuerKeyId)
    if trusted is None or trusted.issuerId != receipt.issuerId:
        raise AdmissionRegistryError("unknown issuer key")
    if trusted.status != "trusted":
        raise AdmissionRegistryError("revoked issuer key")
    try:
        signature = base64.b64decode(receipt.signature, validate=True)
        Ed25519PublicKey.from_public_bytes(trusted.publicKey).verify(signature, _payloadBytes(receipt))
    except (InvalidSignature, ValueError, binascii.Error) as error:
        raise AdmissionRegistryError("admission receipt signature mismatch") from error
    expectedId = _hashBytes(_payloadBytes(receipt) + signature)
    if receipt.receiptId != expectedId:
        raise AdmissionRegistryError("admission receipt identifier mismatch")
    return receipt


def _receiptFromRow(receiptId: str, payloadJson: str, signature: bytes) -> AdmissionReceipt:
    try:
        payload = json.loads(payloadJson)
        payload["parentReceiptIds"] = tuple(payload["parentReceiptIds"])
        return AdmissionReceipt(
            receiptId=receiptId,
            signature=base64.b64encode(signature).decode("ascii"),
            **payload,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise AdmissionRegistryError("receipt row payload is malformed") from error


def issueAdmissionReceipt(
    databasePath: str | Path,
    artifactRoot: str | Path,
    *,
    privateKey: bytes,
    kind: str,
    subjectHash: str,
    artifactHash: str,
    parentReceiptIds: tuple[str, ...],
    ruleId: str,
    ruleVersion: str,
    ruleHash: str,
    issuerId: str,
    issuerKeyId: str,
    issuerExecutableHash: str,
    knowledgeAsOf: str,
    revisionPolicy: str,
    coverage: str,
    frequency: str,
    stepSpan: int,
    maxAdmittedStep: int,
    status: str,
    issuedAt: str,
    trustedIssuers: Mapping[str, TrustedIssuer] | None = None,
) -> AdmissionReceipt:
    """Sign and append one receipt after rehashing its artifact and parents."""

    database = Path(databasePath)
    if not database.exists():
        raise AdmissionRegistryError("admission registry is unavailable")
    target = artifactPath(artifactRoot, artifactHash)
    if not target.exists() or _hashFile(target) != artifactHash:
        raise AdmissionRegistryError("admission artifact hash mismatch")
    try:
        private = Ed25519PrivateKey.from_private_bytes(privateKey)
    except ValueError as error:
        raise AdmissionRegistryError("issuer private key is invalid") from error
    if trustedIssuers is None:
        public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        trustedIssuers = {
            issuerKeyId: TrustedIssuer(
                issuerId=issuerId,
                issuerKeyId=issuerKeyId,
                publicKey=public,
                status="trusted",
            )
        }
    verifier = AdmissionVerifier(database, artifactRoot, trustedIssuers)
    parents = tuple(verifier.verify(receiptId) for receiptId in parentReceiptIds)
    if status in _ADMITTED_PARENT_STATUSES and any(
        parent.status not in _ADMITTED_PARENT_STATUSES for parent in parents
    ):
        raise AdmissionRegistryError("parent is not admitted")
    with sqlite3.connect(database) as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT row_hash FROM receipts ORDER BY seq DESC LIMIT 1").fetchone()
        previousHash = str(row[0]) if row is not None else ""
        provisional = AdmissionReceipt(
            receiptId="",
            receiptVersion=_RECEIPT_VERSION,
            kind=kind,
            subjectHash=subjectHash.lower(),
            artifactHash=artifactHash.lower(),
            parentReceiptIds=tuple(parentReceiptIds),
            ruleId=ruleId,
            ruleVersion=ruleVersion,
            ruleHash=ruleHash.lower(),
            issuerId=issuerId,
            issuerKeyId=issuerKeyId,
            issuerExecutableHash=issuerExecutableHash.lower(),
            knowledgeAsOf=_dateText(knowledgeAsOf),
            revisionPolicy=revisionPolicy,
            coverage=coverage,
            frequency=frequency,
            stepSpan=int(stepSpan),
            maxAdmittedStep=int(maxAdmittedStep),
            status=status,
            previousReceiptHash=previousHash,
            issuedAt=issuedAt,
            signature="",
        )
        _validateReceiptContract(provisional)
        signature = private.sign(_payloadBytes(provisional))
        receipt = replace(
            provisional,
            receiptId=_hashBytes(_payloadBytes(provisional) + signature),
            signature=base64.b64encode(signature).decode("ascii"),
        )
        connection.execute(
            """
            INSERT INTO receipts (
                receipt_id, payload_json, signature, previous_receipt_hash, row_hash
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                receipt.receiptId,
                json.dumps(_receiptPayload(receipt), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                signature,
                receipt.previousReceiptHash,
                _rowHash(receipt),
            ),
        )
    return receipt


class AdmissionVerifier:
    """Read-only deep verifier for signatures, chain lineage, parents, and artifacts."""

    def __init__(
        self,
        databasePath: str | Path,
        artifactRoot: str | Path,
        trustedIssuers: Mapping[str, TrustedIssuer],
    ) -> None:
        self.databasePath = Path(databasePath)
        self.artifactRoot = Path(artifactRoot)
        self.trustedIssuers = dict(trustedIssuers)
        self._verifiedChainCache: dict[str, AdmissionReceipt] | None = None
        self._verifiedChainStamp: tuple[int, int] | None = None

    def _loadVerifiedChain(self) -> dict[str, AdmissionReceipt]:
        if not self.databasePath.exists():
            raise AdmissionRegistryError("admission registry is unavailable")
        stat = self.databasePath.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
        if self._verifiedChainCache is not None and self._verifiedChainStamp == stamp:
            return self._verifiedChainCache
        try:
            connection = sqlite3.connect(f"file:{self.databasePath.as_posix()}?mode=ro", uri=True)
            rows = connection.execute(
                "SELECT seq, receipt_id, payload_json, signature, previous_receipt_hash, row_hash "
                "FROM receipts ORDER BY seq"
            ).fetchall()
            connection.close()
        except sqlite3.Error as error:
            raise AdmissionRegistryError("admission registry is unavailable") from error
        receipts: dict[str, AdmissionReceipt] = {}
        previousHash = ""
        for expectedSequence, row in enumerate(rows, start=1):
            sequence, receiptId, payloadJson, signature, storedPrevious, storedRowHash = row
            if sequence != expectedSequence:
                raise AdmissionRegistryError("admission registry sequence gap")
            receipt = _receiptFromRow(str(receiptId), str(payloadJson), bytes(signature))
            verifyDetachedAdmissionReceipt(receipt, self.trustedIssuers)
            if storedPrevious != previousHash or receipt.previousReceiptHash != previousHash:
                raise AdmissionRegistryError("admission registry chain mismatch")
            computedRowHash = _rowHash(receipt)
            if storedRowHash != computedRowHash:
                raise AdmissionRegistryError("admission registry row hash mismatch")
            previousHash = computedRowHash
            receipts[receipt.receiptId] = receipt
        self._verifiedChainCache = receipts
        self._verifiedChainStamp = stamp
        return receipts

    def verify(
        self,
        receiptId: str,
        *,
        expectedSubjectHash: str | None = None,
        expectedKind: str | None = None,
    ) -> AdmissionReceipt:
        """Deep-verify one receipt and every reachable parent artifact."""

        receipts = self._loadVerifiedChain()
        receipt = receipts.get(receiptId)
        if receipt is None:
            raise AdmissionRegistryError("admission receipt is unknown")
        if expectedSubjectHash is not None and receipt.subjectHash != expectedSubjectHash:
            raise AdmissionRegistryError("admission receipt subject mismatch")
        if expectedKind is not None and receipt.kind != expectedKind:
            raise AdmissionRegistryError("admission receipt kind mismatch")
        visited: set[str] = set()

        def verifyTree(item: AdmissionReceipt) -> None:
            """영수증에서 도달 가능한 부모와 아티팩트 체인을 재귀 검증한다."""

            if item.receiptId in visited:
                return
            visited.add(item.receiptId)
            target = artifactPath(self.artifactRoot, item.artifactHash)
            if not target.exists() or _hashFile(target) != item.artifactHash:
                raise AdmissionRegistryError("admission artifact hash mismatch")
            for parentId in item.parentReceiptIds:
                parent = receipts.get(parentId)
                if parent is None:
                    raise AdmissionRegistryError("admission parent receipt is unknown")
                if item.status in _ADMITTED_PARENT_STATUSES and parent.status not in _ADMITTED_PARENT_STATUSES:
                    raise AdmissionRegistryError("admission parent is not admitted")
                verifyTree(parent)

        verifyTree(receipt)
        return receipt
