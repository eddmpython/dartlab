"""Durable execution receipt, CAS output commit, idempotency claim과 orphan 복구."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..canonical import canonicalDigest, canonicalJson
from ..controlPlane.cas import CasIntegrityError, ContentAddressedStore

_INITIALIZE_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class ExecutionError:
    code: str
    phase: str
    retryable: bool
    sourceRefs: tuple[str, ...]
    messageSafe: str
    debugRefLocal: str | None
    observedAt: str


@dataclass(frozen=True, slots=True)
class BudgetUsed:
    wallMs: int
    cpuMs: int
    peakRssBytes: int
    networkBytes: int
    returnedRows: int
    outputBytes: int
    toolCalls: int
    retries: int


@dataclass(frozen=True, slots=True)
class OutputEnvelope:
    mediaType: str
    payload: bytes
    schemaDigest: str
    rowCount: int
    truncated: bool
    estimatedTotalRows: int | None
    continuation: str | None


@dataclass(frozen=True, slots=True)
class StagedOutput:
    objectRef: str
    outputDigest: str
    byteSize: int
    mediaType: str
    schemaDigest: str
    rowCount: int
    truncated: bool
    estimatedTotalRows: int | None
    continuation: str | None


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    executionId: str
    requestId: str
    parentExecutionId: str | None
    capabilityId: str
    snapshotId: str
    targetRefs: tuple[str, ...]
    normalizedArgs: dict[str, Any]
    argsDigest: str
    inputRefs: tuple[str, ...]
    assumptionRefs: tuple[str, ...]
    engineVersion: str
    codeRevision: str
    dependencyFingerprint: str
    seed: int | None
    startedAt: str
    finishedAt: str
    status: str
    attempt: int
    budgetUsed: BudgetUsed
    sourceReadStats: tuple[tuple[str, int], ...]
    outputRefs: tuple[str, ...]
    outputSchemaRef: str
    outputDigest: str | None
    gapReasons: tuple[str, ...]
    error: ExecutionError | None
    idempotencyKey: str


@dataclass(frozen=True, slots=True)
class ClaimResult:
    status: str
    ownerId: str
    receipt: ExecutionReceipt | None


@dataclass(frozen=True, slots=True)
class ReplayResult:
    valid: bool
    receipt: ExecutionReceipt
    payloads: tuple[bytes, ...]
    digest: str
    issues: tuple[str, ...]


def _errorFromDict(value: dict[str, Any] | None) -> ExecutionError | None:
    if value is None:
        return None
    return ExecutionError(
        code=value["code"],
        phase=value["phase"],
        retryable=bool(value["retryable"]),
        sourceRefs=tuple(value["sourceRefs"]),
        messageSafe=value["messageSafe"],
        debugRefLocal=value.get("debugRefLocal"),
        observedAt=value["observedAt"],
    )


def _receiptFromBytes(payload: bytes) -> ExecutionReceipt:
    value = json.loads(payload)
    value["targetRefs"] = tuple(value["targetRefs"])
    value["inputRefs"] = tuple(value["inputRefs"])
    value["assumptionRefs"] = tuple(value["assumptionRefs"])
    value["sourceReadStats"] = tuple(tuple(item) for item in value["sourceReadStats"])
    value["outputRefs"] = tuple(value["outputRefs"])
    value["gapReasons"] = tuple(value["gapReasons"])
    value["budgetUsed"] = BudgetUsed(**value["budgetUsed"])
    value["error"] = _errorFromDict(value.get("error"))
    return ExecutionReceipt(**value)


class ExecutionStore:
    """Receipt append 원장과 execution 전용 CAS를 한 root에 둔다."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.databasePath = self.root / "execution.sqlite"
        self.cas = ContentAddressedStore(self.root / "cas")
        self.quarantineRoot = self.root / "quarantine" / "sha256"
        with _INITIALIZE_LOCK:
            with self._connection() as connection:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.executescript(
                    """
                CREATE TABLE IF NOT EXISTS receipts (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL UNIQUE,
                    request_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    record_digest TEXT NOT NULL,
                    record_json BLOB NOT NULL,
                    UNIQUE(idempotency_key, attempt)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_success_per_idempotency
                ON receipts(idempotency_key) WHERE status='SUCCEEDED';
                CREATE TABLE IF NOT EXISTS claims (
                    idempotency_key TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_id TEXT,
                    lease_until REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS pending_outputs (
                    object_ref TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    byte_size INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    execution_id TEXT,
                    created_at REAL NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS execution_receipts_no_update
                BEFORE UPDATE ON receipts BEGIN SELECT RAISE(ABORT, 'execution receipts are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS execution_receipts_no_delete
                BEFORE DELETE ON receipts BEGIN SELECT RAISE(ABORT, 'execution receipts are append-only'); END;
                """
                )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.databasePath, timeout=15.0)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def loadSuccess(self, idempotencyKey: str) -> ExecutionReceipt | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT record_json FROM receipts WHERE idempotency_key=? AND status='SUCCEEDED'",
                (idempotencyKey,),
            ).fetchone()
        return None if row is None else _receiptFromBytes(bytes(row[0]))

    def loadReceipt(self, executionId: str) -> ExecutionReceipt | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT record_json FROM receipts WHERE execution_id=?",
                (executionId,),
            ).fetchone()
        return None if row is None else _receiptFromBytes(bytes(row[0]))

    def claim(self, idempotencyKey: str, *, ownerId: str | None = None, leaseSeconds: float = 180.0) -> ClaimResult:
        owner = ownerId or uuid.uuid4().hex
        now = time.time()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            success = connection.execute(
                "SELECT record_json FROM receipts WHERE idempotency_key=? AND status='SUCCEEDED'",
                (idempotencyKey,),
            ).fetchone()
            if success is not None:
                return ClaimResult("REPLAY", owner, _receiptFromBytes(bytes(success[0])))
            row = connection.execute(
                "SELECT owner_id, status, execution_id, lease_until FROM claims WHERE idempotency_key=?",
                (idempotencyKey,),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO claims VALUES (?, ?, 'RUNNING', NULL, ?, ?)",
                    (idempotencyKey, owner, now + leaseSeconds, now),
                )
                return ClaimResult("ACQUIRED", owner, None)
            priorOwner, status, executionId, leaseUntil = row
            if status == "SUCCEEDED" and executionId:
                receipt = self.loadReceipt(str(executionId))
                if receipt is not None:
                    return ClaimResult("REPLAY", owner, receipt)
            if float(leaseUntil) < now:
                connection.execute(
                    "UPDATE claims SET owner_id=?, status='RUNNING', execution_id=NULL, lease_until=?, updated_at=? "
                    "WHERE idempotency_key=?",
                    (owner, now + leaseSeconds, now, idempotencyKey),
                )
                return ClaimResult("RECOVERED", owner, None)
            return ClaimResult("BUSY", str(priorOwner), None)

    def renewClaim(self, idempotencyKey: str, ownerId: str, leaseSeconds: float = 180.0) -> bool:
        now = time.time()
        with self._connection() as connection:
            changed = connection.execute(
                "UPDATE claims SET lease_until=?, updated_at=? WHERE idempotency_key=? AND owner_id=? AND status='RUNNING'",
                (now + leaseSeconds, now, idempotencyKey, ownerId),
            ).rowcount
        return changed == 1

    def stageOutput(self, envelope: OutputEnvelope, ownerId: str) -> StagedOutput:
        digest = hashlib.sha256(envelope.payload).hexdigest()
        objectRef = self.cas.objectRef(digest)
        with self._connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO pending_outputs VALUES (?, ?, ?, 'STAGING', NULL, ?)",
                (objectRef, ownerId, len(envelope.payload), time.time()),
            )
        committedRef = self.cas.putBytes(envelope.payload)
        if committedRef != objectRef:
            raise RuntimeError("CAS output ref drift")
        with self._connection() as connection:
            connection.execute(
                "UPDATE pending_outputs SET state='STAGED' WHERE object_ref=? AND owner_id=?",
                (objectRef, ownerId),
            )
        return StagedOutput(
            objectRef=objectRef,
            outputDigest=digest,
            byteSize=len(envelope.payload),
            mediaType=envelope.mediaType,
            schemaDigest=envelope.schemaDigest,
            rowCount=envelope.rowCount,
            truncated=envelope.truncated,
            estimatedTotalRows=envelope.estimatedTotalRows,
            continuation=envelope.continuation,
        )

    def appendReceipt(
        self,
        receipt: ExecutionReceipt,
        *,
        ownerId: str | None = None,
        stagedOutputs: tuple[StagedOutput, ...] = (),
    ) -> ExecutionReceipt:
        payload = canonicalJson(receipt)
        digest = hashlib.sha256(payload).hexdigest()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            sameAttempt = connection.execute(
                "SELECT record_json FROM receipts WHERE idempotency_key=? AND attempt=?",
                (receipt.idempotencyKey, receipt.attempt),
            ).fetchone()
            if sameAttempt is not None:
                return _receiptFromBytes(bytes(sameAttempt[0]))
            if receipt.status == "SUCCEEDED":
                existing = connection.execute(
                    "SELECT record_json FROM receipts WHERE idempotency_key=? AND status='SUCCEEDED'",
                    (receipt.idempotencyKey,),
                ).fetchone()
                if existing is not None:
                    return _receiptFromBytes(bytes(existing[0]))
            connection.execute(
                "INSERT INTO receipts (execution_id, request_id, idempotency_key, attempt, status, record_digest, record_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    receipt.executionId,
                    receipt.requestId,
                    receipt.idempotencyKey,
                    receipt.attempt,
                    receipt.status,
                    digest,
                    payload,
                ),
            )
            for output in stagedOutputs:
                updated = connection.execute(
                    "UPDATE pending_outputs SET state='COMMITTED', execution_id=? WHERE object_ref=? AND state='STAGED'",
                    (receipt.executionId, output.objectRef),
                ).rowcount
                if updated != 1:
                    raise RuntimeError(f"staged output 원장 누락: {output.objectRef}")
            if ownerId is not None:
                claimStatus = "SUCCEEDED" if receipt.status == "SUCCEEDED" else "CLOSED"
                changed = connection.execute(
                    "UPDATE claims SET status=?, execution_id=?, lease_until=0, updated_at=? "
                    "WHERE idempotency_key=? AND owner_id=?",
                    (claimStatus, receipt.executionId, time.time(), receipt.idempotencyKey, ownerId),
                ).rowcount
                if changed != 1:
                    raise RuntimeError("idempotency claim owner 불일치")
        return receipt

    def verifyIntegrity(self) -> bool:
        with self._connection() as connection:
            check = connection.execute("PRAGMA integrity_check").fetchone()
            triggers = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='receipts'"
                ).fetchall()
            }
            rows = connection.execute("SELECT record_digest, record_json FROM receipts ORDER BY sequence").fetchall()
        if check is None or check[0] != "ok":
            raise RuntimeError("execution sqlite integrity 실패")
        if not {"execution_receipts_no_update", "execution_receipts_no_delete"} <= triggers:
            raise RuntimeError("execution receipt append-only trigger 누락")
        for storedDigest, payload in rows:
            payloadBytes = bytes(payload)
            if hashlib.sha256(payloadBytes).hexdigest() != storedDigest:
                raise RuntimeError("execution receipt digest mismatch")
            if canonicalJson(json.loads(payloadBytes)) != payloadBytes:
                raise RuntimeError("execution receipt canonical byte mismatch")
            receipt = _receiptFromBytes(payloadBytes)
            for objectRef in receipt.outputRefs:
                self.cas.verify(objectRef)
        return True

    def recoverOrphans(self) -> tuple[str, ...]:
        """Receipt commit 전에 멈춘 pending object를 quarantine으로 이동한다."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT object_ref FROM pending_outputs WHERE state!='COMMITTED' ORDER BY object_ref"
            ).fetchall()
        quarantined = []
        for (objectRef,) in rows:
            digest = self.cas.digestFromRef(str(objectRef))
            source = self.cas.pathForDigest(digest)
            if source.exists():
                target = self.quarantineRoot / digest[:2] / digest
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                        raise RuntimeError("quarantine digest mismatch")
                    source.unlink()
                else:
                    os.replace(source, target)
                quarantined.append(str(objectRef))
            with self._connection() as connection:
                connection.execute(
                    "UPDATE pending_outputs SET state='QUARANTINED' WHERE object_ref=? AND state!='COMMITTED'",
                    (objectRef,),
                )
        return tuple(quarantined)


def replayExecution(receipt: ExecutionReceipt, store: ExecutionStore | None = None) -> ReplayResult:
    """Receipt가 가리키는 CAS byte와 output digest를 재검증한다."""
    issues = []
    payloads = []
    if store is None:
        issues.append("EXECUTION_STORE_REQUIRED")
    else:
        for objectRef in receipt.outputRefs:
            try:
                payloads.append(store.cas.readBytes(objectRef))
            except CasIntegrityError:
                issues.append(f"OUTPUT_UNAVAILABLE:{objectRef}")
        if receipt.outputDigest and payloads:
            aggregate = hashlib.sha256(b"".join(payloads)).hexdigest()
            if aggregate != receipt.outputDigest:
                issues.append("OUTPUT_DIGEST_MISMATCH")
    digest = canonicalDigest(
        {
            "executionId": receipt.executionId,
            "receiptDigest": canonicalDigest(receipt),
            "payloadDigests": tuple(hashlib.sha256(item).hexdigest() for item in payloads),
            "issues": tuple(sorted(issues)),
        }
    )
    return ReplayResult(
        valid=not issues,
        receipt=receipt,
        payloads=tuple(payloads),
        digest=digest,
        issues=tuple(sorted(issues)),
    )
