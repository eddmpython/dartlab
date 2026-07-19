"""Universe U3 recovery receipt와 derived artifact의 durable local control-plane."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

from ..canonical import canonicalDigest, canonicalJson
from ..controlPlane.cas import ContentAddressedStore
from .descriptorCrawler import ResourceDescriptor
from .models import CatalogResource, CatalogState
from .recovery import (
    RecoverySourceObject,
    ResourceRecovery,
    rebindResourceRecovery,
    validateRecoverySet,
)


class ResourceRecoveryStoreIntegrityError(RuntimeError):
    """Recovery SQLite receipt, current binding, CAS 중 하나가 일치하지 않는다."""


def defaultRecoveryRoot() -> Path:
    root = Path(os.getenv("LOCALAPPDATA") or (Path.home() / ".dartlab"))
    return root / "DartLab" / "universe" / "control" / "recovery-v1"


def _decodeRecovery(payload: bytes, expectedPayloadDigest: str) -> ResourceRecovery:
    if hashlib.sha256(payload).hexdigest() != expectedPayloadDigest:
        raise ResourceRecoveryStoreIntegrityError("recovery payload digest mismatch")
    try:
        value = json.loads(payload)
        value["inputSources"] = tuple(RecoverySourceObject(**item) for item in value["inputSources"])
        value["artifactMetadata"] = tuple(tuple(item) for item in value["artifactMetadata"])
        value["verificationCodes"] = tuple(value["verificationCodes"])
        recovery = ResourceRecovery(**value)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ResourceRecoveryStoreIntegrityError("recovery payload decode failure") from exc
    if recovery.digest != canonicalDigest(recovery.__class__(**{**value, "digest": ""})):
        raise ResourceRecoveryStoreIntegrityError("recovery receipt digest mismatch")
    return recovery


def _targetKey(resource: CatalogResource) -> tuple[str, str, str, int | None]:
    locator = dict(resource.locator)
    return resource.sourceRef, locator.get("path", ""), locator.get("oid", ""), resource.byteSize


def _storedTargetKey(recovery: ResourceRecovery) -> tuple[str, str, str, int]:
    return (
        recovery.targetSourceRef,
        recovery.targetPath,
        recovery.targetSourceObjectId,
        recovery.targetByteSize,
    )


class ResourceRecoveryStore:
    """Source repository를 수정하지 않고 검증된 recovery만 로컬에 원자 저장한다."""

    def __init__(self, root: Path, *, cas: ContentAddressedStore | None = None):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.cas = cas or ContentAddressedStore(self.root / "cas")
        self.path = self.root / "receipts.sqlite"
        self.connection = sqlite3.connect(self.path, timeout=30.0)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        integrity = self.connection.execute("PRAGMA quick_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            self.connection.close()
            raise ResourceRecoveryStoreIntegrityError(f"recovery store integrity failure: {integrity}")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recovery_receipts (
                recovery_id TEXT PRIMARY KEY,
                target_source_ref TEXT NOT NULL,
                target_path TEXT NOT NULL,
                target_source_object_id TEXT NOT NULL,
                target_byte_size INTEGER NOT NULL,
                payload_digest TEXT NOT NULL,
                payload BLOB NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS recovery_target_identity
            ON recovery_receipts (
                target_source_ref,
                target_path,
                target_source_object_id,
                target_byte_size
            )
            """
        )
        self.connection.commit()
        self.staleReceiptCount = 0

    def __enter__(self) -> ResourceRecoveryStore:
        return self

    def __exit__(self, _excType, _exc, _traceback) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def receiptCount(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM recovery_receipts").fetchone()
        return int(row[0]) if row else 0

    def _readStored(self, recoveryId: str) -> ResourceRecovery | None:
        row = self.connection.execute(
            "SELECT payload_digest, payload FROM recovery_receipts WHERE recovery_id = ?",
            (recoveryId,),
        ).fetchone()
        return None if row is None else _decodeRecovery(bytes(row[1]), str(row[0]))

    def put(
        self,
        recovery: ResourceRecovery,
        catalog: CatalogState,
        descriptors: tuple[ResourceDescriptor, ...],
    ) -> ResourceRecovery:
        report = validateRecoverySet(catalog, descriptors, (recovery,), cas=self.cas)
        if not report.valid:
            raise ResourceRecoveryStoreIntegrityError(f"invalid recovery receipt: {report.issueCodes}")
        existing = self._readStored(recovery.recoveryId)
        if existing is not None:
            target = next(
                (item for item in catalog.resources if _targetKey(item) == _storedTargetKey(existing)),
                None,
            )
            descriptorByVersion = {item.resourceVersionId: item for item in descriptors}
            if target is None or target.resourceVersionId not in descriptorByVersion:
                raise ResourceRecoveryStoreIntegrityError("stored recovery target binding missing")
            rebound = rebindResourceRecovery(existing, target, descriptorByVersion[target.resourceVersionId])
            if rebound.recoveryId != recovery.recoveryId:
                raise ResourceRecoveryStoreIntegrityError("immutable recovery receipt collision")
            return rebound
        payload = canonicalJson(recovery)
        payloadDigest = hashlib.sha256(payload).hexdigest()
        try:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO recovery_receipts (
                        recovery_id,
                        target_source_ref,
                        target_path,
                        target_source_object_id,
                        target_byte_size,
                        payload_digest,
                        payload,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        recovery.recoveryId,
                        recovery.targetSourceRef,
                        recovery.targetPath,
                        recovery.targetSourceObjectId,
                        recovery.targetByteSize,
                        payloadDigest,
                        payload,
                        recovery.createdAt,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ResourceRecoveryStoreIntegrityError("recovery target identity collision") from exc
        return recovery

    def load(
        self,
        catalog: CatalogState,
        descriptors: tuple[ResourceDescriptor, ...],
    ) -> tuple[ResourceRecovery, ...]:
        """Current catalog에서 같은 immutable object인 receipt만 exact version으로 재결박한다."""
        resourcesByTarget = {_targetKey(item): item for item in catalog.resources if item.resourceKind == "HF_FILE"}
        descriptorsByVersion = {item.resourceVersionId: item for item in descriptors}
        recoveries = []
        stale = 0
        rows = self.connection.execute(
            "SELECT payload_digest, payload FROM recovery_receipts ORDER BY recovery_id"
        ).fetchall()
        for payloadDigest, payload in rows:
            stored = _decodeRecovery(bytes(payload), str(payloadDigest))
            target = resourcesByTarget.get(_storedTargetKey(stored))
            if target is None or target.resourceVersionId not in descriptorsByVersion:
                stale += 1
                continue
            try:
                recovery = rebindResourceRecovery(stored, target, descriptorsByVersion[target.resourceVersionId])
            except ValueError as exc:
                raise ResourceRecoveryStoreIntegrityError("recovery current binding mismatch") from exc
            recoveries.append(recovery)
        result = tuple(sorted(recoveries, key=lambda item: item.recoveryId))
        report = validateRecoverySet(catalog, descriptors, result, cas=self.cas)
        if not report.valid:
            raise ResourceRecoveryStoreIntegrityError(f"stored recovery validation failed: {report.issueCodes}")
        self.staleReceiptCount = stale
        return result
