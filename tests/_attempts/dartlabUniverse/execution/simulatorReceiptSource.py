"""기존 simulator AdmissionVerifier만 사용해 signed receipt tree를 read-only 등록한다."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from dartlab.simulate.admissionRegistry import (
    AdmissionReceipt,
    AdmissionRegistryError,
    AdmissionVerifier,
    TrustedIssuer,
    artifactPath,
)

from ..canonical import canonicalDigest


@dataclass(frozen=True, slots=True)
class SimulatorReceiptNode:
    receipt: AdmissionReceipt
    artifactPath: str
    artifactDigest: str


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    status: str
    receiptId: str
    root: SimulatorReceiptNode | None
    receiptTree: tuple[SimulatorReceiptNode, ...]
    trustedIssuerConfigDigest: str
    issues: tuple[str, ...]
    digest: str


def _loadTrustedIssuers(configRef: str | Path) -> tuple[dict[str, TrustedIssuer], str]:
    path = Path(configRef).resolve()
    if not path.is_file() or path.is_symlink():
        raise ValueError("trusted issuer config는 regular local file이어야 함")
    raw = path.read_bytes()
    payload = json.loads(raw)
    issuers = {}
    for item in payload.get("issuers", []):
        publicKey = base64.b64decode(item["publicKeyBase64"], validate=True)
        if len(publicKey) != 32:
            raise ValueError("Ed25519 public key는 32 byte여야 함")
        trusted = TrustedIssuer(
            issuerId=str(item["issuerId"]),
            issuerKeyId=str(item["issuerKeyId"]),
            publicKey=publicKey,
            status=str(item.get("status", "trusted")),
        )
        if trusted.issuerKeyId in issuers:
            raise ValueError("trusted issuer key ID 중복")
        issuers[trusted.issuerKeyId] = trusted
    if not issuers:
        raise ValueError("trusted issuer config가 비어 있음")
    return issuers, hashlib.sha256(raw).hexdigest()


def verifySimulatorAdmission(
    databasePath: str | Path,
    artifactRoot: str | Path,
    receiptId: str,
    trustedIssuerConfigRef: str | Path,
) -> RegistrationResult:
    """서명, issuer, registry chain, parent tree와 artifact byte를 모두 재검증한다."""
    configDigest = ""
    try:
        issuers, configDigest = _loadTrustedIssuers(trustedIssuerConfigRef)
        verifier = AdmissionVerifier(databasePath, artifactRoot, issuers)
        rootReceipt = verifier.verify(receiptId)
        nodes = {}

        def visit(receipt: AdmissionReceipt) -> None:
            if receipt.receiptId in nodes:
                return
            verified = verifier.verify(receipt.receiptId)
            path = artifactPath(artifactRoot, verified.artifactHash).resolve()
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != verified.artifactHash:
                raise AdmissionRegistryError("admission artifact hash mismatch")
            nodes[verified.receiptId] = SimulatorReceiptNode(
                receipt=verified,
                artifactPath=path.as_posix(),
                artifactDigest=digest,
            )
            for parentId in verified.parentReceiptIds:
                visit(verifier.verify(parentId))

        visit(rootReceipt)
        ordered = tuple(sorted(nodes.values(), key=lambda item: item.receipt.receiptId))
        root = nodes[rootReceipt.receiptId]
        status = "VERIFIED_ADMISSION_RECEIPT"
        issues = ()
    except Exception as exc:
        root = None
        ordered = ()
        status = "REJECTED_INVALID_ADMISSION_RECEIPT"
        issues = (f"{type(exc).__name__}:{str(exc)[:300]}",)
    digest = canonicalDigest(
        {
            "status": status,
            "receiptId": receiptId,
            "receiptTree": tuple(
                (item.receipt.receiptId, item.receipt.artifactHash, item.artifactDigest) for item in ordered
            ),
            "trustedIssuerConfigDigest": configDigest,
            "issues": issues,
        }
    )
    return RegistrationResult(
        status=status,
        receiptId=receiptId,
        root=root,
        receiptTree=ordered,
        trustedIssuerConfigDigest=configDigest,
        issues=issues,
        digest=digest,
    )
