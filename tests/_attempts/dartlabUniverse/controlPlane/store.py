"""Universe U1 SQLite append-only control decision chain."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..canonical import canonicalDigest, canonicalJson
from .cas import CasIntegrityError, ContentAddressedStore

_GENESIS_HEAD = hashlib.sha256(b"dartlab-universe-control-plane-v1").hexdigest()
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class DecisionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class ControlDecision:
    decisionId: str
    decisionKind: str
    subjectRefs: tuple[str, ...]
    inputEvidenceRefs: tuple[str, ...]
    ruleVersion: str
    payloadDigest: str
    status: DecisionStatus
    reviewer: str
    reasonCode: str
    previousDecisionId: str | None
    createdAt: str
    approvedAt: str | None = None


@dataclass(frozen=True, slots=True)
class ControlHead:
    headId: str
    sequence: int


class ConcurrentHeadError(RuntimeError):
    pass


class ControlPlaneIntegrityError(RuntimeError):
    pass


def _decisionFromPayload(payload: bytes) -> ControlDecision:
    data = json.loads(payload)
    return ControlDecision(
        decisionId=data["decisionId"],
        decisionKind=data["decisionKind"],
        subjectRefs=tuple(data["subjectRefs"]),
        inputEvidenceRefs=tuple(data["inputEvidenceRefs"]),
        ruleVersion=data["ruleVersion"],
        payloadDigest=data["payloadDigest"],
        status=DecisionStatus(data["status"]),
        reviewer=data["reviewer"],
        reasonCode=data["reasonCode"],
        previousDecisionId=data.get("previousDecisionId"),
        createdAt=data["createdAt"],
        approvedAt=data.get("approvedAt"),
    )


def _validateDecision(record: ControlDecision) -> None:
    if not record.decisionId or not record.decisionKind or not record.subjectRefs:
        raise ValueError("control decision identity와 subject는 필수")
    if not _SHA256_RE.fullmatch(record.payloadDigest):
        raise ValueError("control decision payloadDigest는 SHA-256이어야 함")
    if record.status is DecisionStatus.APPROVED and not record.approvedAt:
        raise ValueError("APPROVED decision은 approvedAt이 필요")


class ControlPlaneStore:
    """Optimistic head와 hash chain을 가진 append-only SQLite store."""

    def __init__(
        self,
        databasePath: Path,
        artifactStore: ContentAddressedStore | None = None,
    ):
        self.databasePath = databasePath.resolve()
        self.artifactStore = artifactStore
        self.databasePath.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL UNIQUE,
                    previous_decision_id TEXT,
                    previous_head_id TEXT NOT NULL,
                    head_id TEXT NOT NULL UNIQUE,
                    record_digest TEXT NOT NULL,
                    record_json BLOB NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS decisions_no_update
                BEFORE UPDATE ON decisions BEGIN SELECT RAISE(ABORT, 'append-only'); END;
                CREATE TRIGGER IF NOT EXISTS decisions_no_delete
                BEFORE DELETE ON decisions BEGIN SELECT RAISE(ABORT, 'append-only'); END;
                """
            )

    def _verifyArtifactRefs(self, record: ControlDecision) -> None:
        for objectRef in (ref for ref in record.inputEvidenceRefs if ref.startswith("cas:")):
            if self.artifactStore is None:
                raise ControlPlaneIntegrityError(f"CAS store 없이 decision artifact 검증 불가: {objectRef}")
            try:
                self.artifactStore.verify(objectRef)
            except CasIntegrityError as exc:
                raise ControlPlaneIntegrityError(f"decision artifact 무결성 실패: {objectRef}") from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.databasePath, timeout=10.0)
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

    def currentHead(self) -> ControlHead:
        self.verifyIntegrity()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT sequence, head_id FROM decisions ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
        return ControlHead(_GENESIS_HEAD, 0) if row is None else ControlHead(str(row[1]), int(row[0]))

    def appendControlDecision(self, record: ControlDecision, expectedHead: str) -> ControlHead:
        """Expected head가 일치할 때만 decision을 한 transaction으로 append한다."""
        _validateDecision(record)
        self._verifyArtifactRefs(record)
        payload = canonicalJson(record)
        recordDigest = hashlib.sha256(payload).hexdigest()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT sequence, head_id FROM decisions ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            previousHead = _GENESIS_HEAD if row is None else str(row[1])
            sequence = 1 if row is None else int(row[0]) + 1
            if previousHead != expectedHead:
                raise ConcurrentHeadError(f"expected={expectedHead}, actual={previousHead}")
            latestForSubject = None
            for (candidatePayload,) in connection.execute(
                "SELECT record_json FROM decisions ORDER BY sequence DESC"
            ).fetchall():
                candidate = _decisionFromPayload(bytes(candidatePayload))
                if candidate.decisionKind == record.decisionKind and candidate.subjectRefs == record.subjectRefs:
                    latestForSubject = candidate
                    break
            if latestForSubject is not None and record.previousDecisionId != latestForSubject.decisionId:
                raise ValueError(f"successor가 최신 decision을 가리키지 않음: {latestForSubject.decisionId}")
            if latestForSubject is None and record.previousDecisionId is not None:
                raise ValueError("새 subject decision은 previousDecisionId를 가질 수 없음")
            if record.previousDecisionId is not None:
                previous = connection.execute(
                    "SELECT record_json FROM decisions WHERE decision_id=?",
                    (record.previousDecisionId,),
                ).fetchone()
                if previous is None:
                    raise ValueError(f"previous decision 누락: {record.previousDecisionId}")
                previousDecision = _decisionFromPayload(bytes(previous[0]))
                if (
                    previousDecision.decisionKind != record.decisionKind
                    or previousDecision.subjectRefs != record.subjectRefs
                ):
                    raise ValueError("successor decision kind 또는 subject 불일치")
            headId = canonicalDigest(
                {
                    "sequence": sequence,
                    "previousHeadId": previousHead,
                    "recordDigest": recordDigest,
                }
            )
            connection.execute(
                """
                INSERT INTO decisions (
                    decision_id, previous_decision_id, previous_head_id,
                    head_id, record_digest, record_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.decisionId,
                    record.previousDecisionId,
                    previousHead,
                    headId,
                    recordDigest,
                    payload,
                ),
            )
        return ControlHead(headId, sequence)

    def verifyIntegrity(self) -> bool:
        """SQLite integrity, canonical record byte, digest, head chain을 전부 재검증한다."""
        with self._connection() as connection:
            check = connection.execute("PRAGMA integrity_check").fetchone()
            if check is None or check[0] != "ok":
                raise ControlPlaneIntegrityError(f"sqlite integrity 실패: {check}")
            triggers = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='decisions'"
                ).fetchall()
            }
            if not {"decisions_no_update", "decisions_no_delete"} <= triggers:
                raise ControlPlaneIntegrityError("append-only trigger 누락")
            rows = connection.execute(
                """
                SELECT sequence, previous_head_id, head_id, record_digest, record_json
                FROM decisions ORDER BY sequence
                """
            ).fetchall()
        previousHead = _GENESIS_HEAD
        for sequence, storedPrevious, storedHead, storedDigest, payload in rows:
            payloadBytes = bytes(payload)
            try:
                decoded = json.loads(payloadBytes)
            except Exception as exc:
                raise ControlPlaneIntegrityError("control decision JSON 손상") from exc
            if canonicalJson(decoded) != payloadBytes:
                raise ControlPlaneIntegrityError("control decision canonical byte 불일치")
            self._verifyArtifactRefs(_decisionFromPayload(payloadBytes))
            recordDigest = hashlib.sha256(payloadBytes).hexdigest()
            expectedHead = canonicalDigest(
                {
                    "sequence": int(sequence),
                    "previousHeadId": previousHead,
                    "recordDigest": recordDigest,
                }
            )
            if storedPrevious != previousHead or storedDigest != recordDigest or storedHead != expectedHead:
                raise ControlPlaneIntegrityError(f"control head chain 손상: {sequence}")
            previousHead = str(storedHead)
        return True

    def approvedDecisions(self) -> tuple[ControlDecision, ...]:
        """Subject별 최신 decision이 APPROVED인 record만 query 입력으로 반환한다."""
        self.verifyIntegrity()
        with self._connection() as connection:
            rows = connection.execute("SELECT record_json FROM decisions ORDER BY sequence").fetchall()
        latest: dict[tuple[str, tuple[str, ...]], ControlDecision] = {}
        for (payload,) in rows:
            decision = _decisionFromPayload(bytes(payload))
            latest[(decision.decisionKind, decision.subjectRefs)] = decision
        return tuple(
            sorted(
                (decision for decision in latest.values() if decision.status is DecisionStatus.APPROVED),
                key=lambda item: item.decisionId,
            )
        )


def appendControlDecision(
    store: ControlPlaneStore,
    record: ControlDecision,
    expectedHead: str,
) -> ControlHead:
    return store.appendControlDecision(record, expectedHead)
