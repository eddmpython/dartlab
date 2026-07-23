"""Durable continuation ledger, claim coordinator, replay, and expiry GC."""

from __future__ import annotations

import hashlib
import hmac
import math
import re
import secrets
import sqlite3
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .arrowPayload import validateArrowIpcPayload
from .artifactStore import ArtifactStore
from .contracts import (
    ArrowPayloadFacts,
    ContinuationError,
    ContinuationMaintenanceBudget,
    ContinuationPage,
    ContinuationPins,
    ContinuationPolicy,
    ContinuationQueryState,
    IssuedContinuation,
    LoadedContinuationContext,
    PageEnvelope,
    PruneReport,
    bytesDigest,
    canonicalDigest,
)
from .privateStorage import _resolvePrivateRoot, securePrivatePath, verifyPrivatePath
from .queryState import decodeQueryState, encodeQueryState
from .tokens import childToken, encodeToken, tokenDigest

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_INITIALIZE_LOCK = threading.Lock()
_PayloadValidator = Callable[..., ArrowPayloadFacts]
_SCHEMA_VERSION = 3
_SWEEP_NAMES = frozenset({"artifacts", "cas", "roots"})


@dataclass(frozen=True, slots=True)
class _StagedArtifact:
    digest: str
    byteCount: int
    ownerId: str


@dataclass(frozen=True, slots=True)
class _SweepCursor:
    name: str
    digest: str
    value: float
    cycle: int


def _resultDigest(
    tokenDigestValue: str,
    pins: ContinuationPins,
    pageDigest: str,
    rowCount: int,
    byteCount: int,
    nextTokenDigest: str | None,
) -> str:
    return canonicalDigest(
        {
            "tokenDigest": tokenDigestValue,
            "sourceDigest": pins.sourceDigest,
            "queryDigest": pins.queryDigest,
            "contractDigest": pins.contractDigest,
            "schemaDigest": pins.schemaDigest,
            "pageDigest": pageDigest,
            "rowCount": rowCount,
            "byteCount": byteCount,
            "nextTokenDigest": nextTokenDigest,
        }
    )


class _LeaseHeartbeat:
    """Live owner의 SQLite lease를 별도 connection에서 갱신한다."""

    def __init__(self, store: ContinuationStore, tokenDigestValue: str, ownerId: str):
        self.store = store
        self.tokenDigestValue = tokenDigestValue
        self.ownerId = ownerId
        self.stopEvent = threading.Event()
        self.lost = False
        self.thread = threading.Thread(target=self._run, name="continuation-heartbeat", daemon=True)

    def _run(self) -> None:
        interval = max(0.01, self.store.policy.leaseSeconds / 3.0)
        while not self.stopEvent.wait(interval):
            try:
                renewed = self.store._renew(self.tokenDigestValue, self.ownerId)
            except Exception:
                renewed = False
            if not renewed:
                self.lost = True
                return

    def __enter__(self) -> _LeaseHeartbeat:
        self.thread.start()
        return self

    def __exit__(self, excType: object, exc: object, traceback: object) -> None:
        self.stopEvent.set()
        self.thread.join(timeout=max(1.0, self.store.policy.leaseSeconds))


class ContinuationStore:
    """단일 host의 thread와 process가 공유하는 continuation control plane.

    Args:
        root: private ledger와 CAS 전용 directory.
        policy: page, state, lifetime, claim, GC bounds.
        clock: Unix time supplier.
        payloadValidator: Arrow IPC actual-facts validator seam.

    Returns:
        durable issue, load, redeem, replay, prune 기능을 가진 store.

    Raises:
        ContinuationError: ledger, CAS, pin, payload 검증 실패 시.

    Example:
        ``store = ContinuationStore(controlRoot)``.

    Guide:
        기존 data query 축 내부에서만 사용하고 별도 public axis로 노출하지 않는다.

    SeeAlso:
        ``ContinuationQueryState``, ``PageEnvelope``.

    Requires:
        materialize callback은 pinned source를 읽는 결정적 read여야 한다.

    AIContext:
        SQLite에는 digest와 bounded metadata만, private 원문은 CAS에만 둔다.
    """

    def __init__(
        self,
        root: Path,
        policy: ContinuationPolicy | None = None,
        clock: Callable[[], float] = time.time,
        payloadValidator: _PayloadValidator = validateArrowIpcPayload,
    ):
        self.root = _resolvePrivateRoot(root)
        self.root.mkdir(parents=True, exist_ok=True)
        securePrivatePath(self.root)
        self.policy = policy or ContinuationPolicy()
        if not callable(clock):
            raise ContinuationError("CONTINUATION_CLOCK_INVALID")
        self.clock = clock
        self.payloadValidator = payloadValidator
        self.databasePath = self.root / "continuations.sqlite"
        self.cas = ArtifactStore(
            self.root / "cas",
            registrationCheck=self._artifactRegisteredForPublish,
        )
        with _INITIALIZE_LOCK:
            self._initialize()
        securePrivatePath(self.databasePath)

    def _connect(self, *, busySeconds: float | None = None) -> sqlite3.Connection:
        timeout = 15.0 if busySeconds is None else min(15.0, max(0.0, busySeconds))
        connection = sqlite3.connect(self.databasePath, timeout=timeout)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute(f"PRAGMA busy_timeout={int(timeout * 1000)}")
            securePrivatePath(self.databasePath)
            for suffix in ("-wal", "-shm"):
                sidecar = Path(f"{self.databasePath}{suffix}")
                if sidecar.exists():
                    securePrivatePath(sidecar)
        except Exception:
            connection.close()
            raise
        return connection

    def _artifactRegisteredForPublish(self, digest: str, byteCount: int) -> bool:
        if _DIGEST_RE.fullmatch(digest) is None or type(byteCount) is not int or byteCount < 0:
            return False
        with self._connection() as connection:
            row = connection.execute(
                "SELECT byte_count, status FROM continuation_artifacts WHERE digest=?",
                (digest,),
            ).fetchone()
            if row is None:
                return False
            if self._storedInt(row["byte_count"]) != byteCount:
                return False
            return row["status"] in {"STAGED", "REFERENCED"}

    @contextmanager
    def _connection(self, *, busySeconds: float | None = None) -> Iterator[sqlite3.Connection]:
        connection = self._connect(busySeconds=busySeconds)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            versionRow = connection.execute("PRAGMA user_version").fetchone()
            if versionRow is None:
                raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
            version = int(versionRow[0])
            objects = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                ).fetchall()
            }
            if version == 0:
                if objects:
                    raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
                self._createSchemaV3(connection)
            elif version == 1:
                self._migrateV1ToV3(connection)
            elif version == 2:
                self._migrateV2ToV3(connection)
            elif version == _SCHEMA_VERSION:
                self._validateSchemaV3(connection)
            else:
                raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")

    @staticmethod
    def _tableColumns(connection: sqlite3.Connection, table: str) -> set[str]:
        return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}

    @staticmethod
    def _continuationColumns() -> set[str]:
        return {
            "token_digest",
            "chain_root_digest",
            "parent_token_digest",
            "state_digest",
            "source_digest",
            "query_digest",
            "contract_digest",
            "schema_digest",
            "issued_at",
            "expires_at",
            "status",
            "owner_id",
            "lease_until",
            "page_digest",
            "row_count",
            "byte_count",
            "next_token_digest",
            "next_state_digest",
            "result_digest",
            "completed_at",
        }

    @staticmethod
    def _artifactColumns() -> set[str]:
        return {"digest", "byte_count", "status", "stage_owner", "staged_at", "referenced_at"}

    @staticmethod
    def _sweepColumns() -> set[str]:
        return {"sweep_name", "cursor_digest", "cursor_value", "cycle", "updated_at"}

    @staticmethod
    def _pruneWorkColumns() -> set[str]:
        return {"root_digest", "phase", "cursor_digest", "expires_at", "updated_at"}

    @staticmethod
    def _sweepTableSql() -> str:
        return """
            CREATE TABLE continuation_sweeps (
                sweep_name TEXT PRIMARY KEY,
                cursor_digest TEXT NOT NULL,
                cursor_value REAL NOT NULL CHECK(cursor_value >= 0),
                cycle INTEGER NOT NULL CHECK(cycle >= 0),
                updated_at REAL NOT NULL
            )
        """

    @staticmethod
    def _pruneWorkTableSql() -> str:
        return """
            CREATE TABLE continuation_prune_work (
                root_digest TEXT PRIMARY KEY,
                phase TEXT NOT NULL CHECK(phase IN ('SCAN', 'DELETE')),
                cursor_digest TEXT NOT NULL,
                expires_at REAL NOT NULL CHECK(expires_at >= 0),
                updated_at REAL NOT NULL
            )
        """

    @staticmethod
    def _seedSweeps(connection: sqlite3.Connection, now: float) -> None:
        connection.executemany(
            "INSERT INTO continuation_sweeps "
            "(sweep_name, cursor_digest, cursor_value, cycle, updated_at) VALUES (?, '', 0, 0, ?)",
            ((name, now) for name in sorted(_SWEEP_NAMES)),
        )

    @staticmethod
    def _rebuildV3Indexes(connection: sqlite3.Connection) -> None:
        for name in (
            "continuation_state_artifact",
            "continuation_page_artifact",
            "continuation_next_state_artifact",
            "continuation_root_sweep",
        ):
            connection.execute(f"DROP INDEX IF EXISTS {name}")
        connection.execute("CREATE INDEX continuation_state_artifact ON continuations(state_digest)")
        connection.execute("CREATE INDEX continuation_page_artifact ON continuations(page_digest)")
        connection.execute("CREATE INDEX continuation_next_state_artifact ON continuations(next_state_digest)")
        connection.execute(
            "CREATE INDEX continuation_root_sweep ON continuations(expires_at, token_digest) "
            "WHERE parent_token_digest IS NULL"
        )

    def _createSchemaV3(self, connection: sqlite3.Connection) -> None:
        now = 0.0
        connection.executescript(
            """
            BEGIN IMMEDIATE;
            CREATE TABLE continuations (
                token_digest TEXT PRIMARY KEY,
                chain_root_digest TEXT NOT NULL,
                parent_token_digest TEXT REFERENCES continuations(token_digest) ON DELETE CASCADE,
                state_digest TEXT NOT NULL,
                source_digest TEXT NOT NULL,
                query_digest TEXT NOT NULL,
                contract_digest TEXT NOT NULL,
                schema_digest TEXT NOT NULL,
                issued_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('PENDING', 'RUNNING', 'SUCCEEDED')),
                owner_id TEXT,
                lease_until REAL NOT NULL DEFAULT 0,
                page_digest TEXT,
                row_count INTEGER,
                byte_count INTEGER,
                next_token_digest TEXT,
                next_state_digest TEXT,
                result_digest TEXT,
                completed_at REAL
            );
            CREATE INDEX continuation_parent ON continuations(parent_token_digest);
            CREATE INDEX continuation_root_expiry ON continuations(chain_root_digest, expires_at);
            CREATE INDEX continuation_state_artifact ON continuations(state_digest);
            CREATE INDEX continuation_page_artifact ON continuations(page_digest);
            CREATE INDEX continuation_next_state_artifact ON continuations(next_state_digest);
            CREATE INDEX continuation_root_sweep ON continuations(expires_at, token_digest)
            WHERE parent_token_digest IS NULL;
            CREATE TABLE continuation_artifacts (
                digest TEXT PRIMARY KEY,
                byte_count INTEGER NOT NULL CHECK(byte_count >= 0),
                status TEXT NOT NULL CHECK(status IN ('STAGED', 'REFERENCED', 'GC_PENDING')),
                stage_owner TEXT,
                staged_at REAL NOT NULL,
                referenced_at REAL
            );
            CREATE INDEX continuation_artifact_status
            ON continuation_artifacts(status, staged_at);
            CREATE TRIGGER continuation_identity_immutable
            BEFORE UPDATE ON continuations
            WHEN OLD.token_digest != NEW.token_digest
              OR OLD.chain_root_digest != NEW.chain_root_digest
              OR OLD.parent_token_digest IS NOT NEW.parent_token_digest
              OR OLD.state_digest != NEW.state_digest
              OR OLD.source_digest != NEW.source_digest
              OR OLD.query_digest != NEW.query_digest
              OR OLD.contract_digest != NEW.contract_digest
              OR OLD.schema_digest != NEW.schema_digest
              OR OLD.issued_at != NEW.issued_at
              OR OLD.expires_at != NEW.expires_at
            BEGIN SELECT RAISE(ABORT, 'continuation identity is immutable'); END;
            CREATE TRIGGER continuation_success_immutable
            BEFORE UPDATE ON continuations WHEN OLD.status='SUCCEEDED'
            BEGIN SELECT RAISE(ABORT, 'continuation result is immutable'); END;
            CREATE TRIGGER continuation_artifact_identity_immutable
            BEFORE UPDATE ON continuation_artifacts
            WHEN OLD.digest != NEW.digest OR OLD.byte_count != NEW.byte_count
            BEGIN SELECT RAISE(ABORT, 'continuation artifact identity is immutable'); END;
            """
        )
        connection.execute(self._sweepTableSql())
        self._seedSweeps(connection, now)
        connection.execute(self._pruneWorkTableSql())
        connection.execute("PRAGMA user_version=3")

    def _migrateV1ToV3(self, connection: sqlite3.Connection) -> None:
        if self._tableColumns(connection, "continuations") != self._continuationColumns():
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        if self._tableColumns(connection, "continuation_gc_artifacts") != {"digest", "enqueued_at"}:
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            CREATE TABLE continuation_artifacts (
                digest TEXT PRIMARY KEY,
                byte_count INTEGER NOT NULL CHECK(byte_count >= 0),
                status TEXT NOT NULL CHECK(status IN ('STAGED', 'REFERENCED', 'GC_PENDING')),
                stage_owner TEXT,
                staged_at REAL NOT NULL,
                referenced_at REAL
            )
            """
        )
        connection.execute("CREATE INDEX continuation_artifact_status ON continuation_artifacts(status, staged_at)")
        self._rebuildV3Indexes(connection)
        connection.execute(
            """
            CREATE TRIGGER continuation_artifact_identity_immutable
            BEFORE UPDATE ON continuation_artifacts
            WHEN OLD.digest != NEW.digest OR OLD.byte_count != NEW.byte_count
            BEGIN SELECT RAISE(ABORT, 'continuation artifact identity is immutable'); END
            """
        )
        now = 0.0
        referenced = {
            self._storedDigest(value)
            for row in connection.execute(
                "SELECT state_digest, page_digest, next_state_digest FROM continuations"
            ).fetchall()
            for value in row
            if value is not None
        }
        for digest in referenced:
            payload = self.cas.readBytes(digest)
            connection.execute(
                "INSERT INTO continuation_artifacts "
                "(digest, byte_count, status, stage_owner, staged_at, referenced_at) "
                "VALUES (?, ?, 'REFERENCED', NULL, ?, ?)",
                (digest, len(payload), now, now),
            )
        oldPending = {
            self._storedDigest(row[0])
            for row in connection.execute("SELECT digest FROM continuation_gc_artifacts").fetchall()
        }
        # Do not enumerate the legacy CAS during startup migration. Explicit v1
        # tombstones are cheap to carry forward; any other legacy orphan is
        # discovered later by the persistent, caller-bounded prefix sweep.
        for digest in oldPending:
            if digest in referenced:
                continue
            path = self.cas.pathForDigest(digest)
            byteCount = len(self.cas.readBytes(digest)) if path.is_file() else 0
            connection.execute(
                "INSERT INTO continuation_artifacts "
                "(digest, byte_count, status, stage_owner, staged_at, referenced_at) "
                "VALUES (?, ?, 'GC_PENDING', NULL, ?, NULL)",
                (digest, byteCount, now),
            )
        connection.execute("DROP TABLE continuation_gc_artifacts")
        connection.execute(self._sweepTableSql())
        self._seedSweeps(connection, now)
        connection.execute("DROP TABLE IF EXISTS continuation_prune_work")
        connection.execute(self._pruneWorkTableSql())
        connection.execute("PRAGMA user_version=3")
        self._validateSchemaV3(connection)

    def _migrateV2ToV3(self, connection: sqlite3.Connection) -> None:
        self._validateSchemaV2(connection)
        connection.execute("BEGIN IMMEDIATE")
        now = 0.0
        self._rebuildV3Indexes(connection)
        connection.execute(self._sweepTableSql())
        self._seedSweeps(connection, now)
        connection.execute("DROP TABLE IF EXISTS continuation_prune_work")
        connection.execute(self._pruneWorkTableSql())
        connection.execute("PRAGMA user_version=3")
        self._validateSchemaV3(connection)

    def _validateSchemaV2(self, connection: sqlite3.Connection) -> None:
        if self._tableColumns(connection, "continuations") != self._continuationColumns():
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        if self._tableColumns(connection, "continuation_artifacts") != self._artifactColumns():
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        triggers = {
            str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall()
        }
        required = {
            "continuation_identity_immutable",
            "continuation_success_immutable",
            "continuation_artifact_identity_immutable",
        }
        if not required <= triggers:
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        indexes = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'"
            ).fetchall()
        }
        requiredIndexes = {
            "continuation_parent",
            "continuation_root_expiry",
            "continuation_artifact_status",
        }
        if not requiredIndexes <= indexes:
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        obsolete = connection.execute("SELECT 1 FROM sqlite_master WHERE name='continuation_gc_artifacts'").fetchone()
        if obsolete is not None:
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")

    def _validateSchemaV3(self, connection: sqlite3.Connection) -> None:
        self._validateSchemaV2(connection)
        if self._tableColumns(connection, "continuation_sweeps") != self._sweepColumns():
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        if self._tableColumns(connection, "continuation_prune_work") != self._pruneWorkColumns():
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        indexes = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'"
            ).fetchall()
        }
        requiredIndexes = {
            "continuation_state_artifact",
            "continuation_page_artifact",
            "continuation_next_state_artifact",
            "continuation_root_sweep",
        }
        if not requiredIndexes <= indexes:
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        rows = connection.execute(
            "SELECT sweep_name, cursor_digest, cursor_value, cycle, updated_at FROM continuation_sweeps"
        ).fetchall()
        if {str(row["sweep_name"]) for row in rows} != _SWEEP_NAMES:
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        for row in rows:
            self._decodeSweepRow(row)
        workRows = connection.execute(
            "SELECT root_digest, phase, cursor_digest, expires_at, updated_at FROM continuation_prune_work"
        ).fetchall()
        if len(workRows) > 1:
            raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")
        for row in workRows:
            self._storedDigest(row["root_digest"])
            self._storedDigest(row["cursor_digest"])
            self._storedFloat(row["expires_at"])
            self._storedFloat(row["updated_at"])
            if row["phase"] not in {"SCAN", "DELETE"}:
                raise ContinuationError("CONTINUATION_SCHEMA_VERSION_UNSUPPORTED")

    def _now(self) -> float:
        try:
            value = self.clock()
            if type(value) not in (int, float):
                raise ValueError
            number = float(value)
        except Exception:
            raise ContinuationError("CONTINUATION_CLOCK_INVALID") from None
        if not math.isfinite(number) or number < 0:
            raise ContinuationError("CONTINUATION_CLOCK_INVALID")
        return number

    @staticmethod
    def _storedFloat(value: Any) -> float:
        if type(value) not in (int, float):
            raise ContinuationError("CONTINUATION_CORRUPT")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ContinuationError("CONTINUATION_CORRUPT") from None
        if not math.isfinite(number) or number < 0:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return number

    @staticmethod
    def _storedInt(value: Any, *, minimum: int = 0) -> int:
        if type(value) is not int or value < minimum:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return value

    @staticmethod
    def _isTokenCollision(error: sqlite3.IntegrityError) -> bool:
        codes = {
            getattr(sqlite3, "SQLITE_CONSTRAINT_PRIMARYKEY", -1),
            getattr(sqlite3, "SQLITE_CONSTRAINT_UNIQUE", -1),
        }
        return (
            getattr(error, "sqlite_errorcode", None) in codes
            and str(error) == "UNIQUE constraint failed: continuations.token_digest"
        )

    @staticmethod
    def _isSqliteBusy(error: sqlite3.OperationalError) -> bool:
        code = getattr(error, "sqlite_errorcode", None)
        if type(code) is int and (code & 0xFF) in {
            getattr(sqlite3, "SQLITE_BUSY", 5),
            getattr(sqlite3, "SQLITE_LOCKED", 6),
        }:
            return True
        return str(error) in {"database is locked", "database table is locked"}

    @staticmethod
    def _storedDigest(value: Any) -> str:
        if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return value

    @staticmethod
    def _decodeSweepRow(row: sqlite3.Row | None) -> _SweepCursor:
        if row is None:
            raise ContinuationError("CONTINUATION_CORRUPT")
        name = row["sweep_name"]
        digest = row["cursor_digest"]
        if type(name) is not str or name not in _SWEEP_NAMES:
            raise ContinuationError("CONTINUATION_CORRUPT")
        if type(digest) is not str or (digest and _DIGEST_RE.fullmatch(digest) is None):
            raise ContinuationError("CONTINUATION_CORRUPT")
        value = ContinuationStore._storedFloat(row["cursor_value"])
        cycle = ContinuationStore._storedInt(row["cycle"])
        ContinuationStore._storedFloat(row["updated_at"])
        if name == "cas":
            prefix = int(value)
            if value != prefix or not 0 <= prefix <= 0xFF:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if digest:
                raise ContinuationError("CONTINUATION_CORRUPT")
        elif name == "artifacts" and value != 0:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return _SweepCursor(name, digest, value, cycle)

    @staticmethod
    def _loadSweep(connection: sqlite3.Connection, name: str) -> _SweepCursor:
        if name not in _SWEEP_NAMES:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return ContinuationStore._decodeSweepRow(
            connection.execute(
                "SELECT sweep_name, cursor_digest, cursor_value, cycle, updated_at "
                "FROM continuation_sweeps WHERE sweep_name=?",
                (name,),
            ).fetchone()
        )

    @staticmethod
    def _saveSweep(
        connection: sqlite3.Connection,
        cursor: _SweepCursor,
        *,
        now: float,
    ) -> None:
        if cursor.name not in _SWEEP_NAMES:
            raise ContinuationError("CONTINUATION_CORRUPT")
        changed = connection.execute(
            "UPDATE continuation_sweeps SET cursor_digest=?, cursor_value=?, cycle=?, updated_at=? WHERE sweep_name=?",
            (cursor.digest, cursor.value, cursor.cycle, now, cursor.name),
        ).rowcount
        if changed != 1:
            raise ContinuationError("CONTINUATION_CORRUPT")

    @staticmethod
    def _pinsFromRow(row: sqlite3.Row) -> ContinuationPins:
        return ContinuationPins(
            sourceDigest=ContinuationStore._storedDigest(row["source_digest"]),
            queryDigest=ContinuationStore._storedDigest(row["query_digest"]),
            contractDigest=ContinuationStore._storedDigest(row["contract_digest"]),
            schemaDigest=ContinuationStore._storedDigest(row["schema_digest"]),
        )

    @staticmethod
    def _validatePins(stored: ContinuationPins, current: ContinuationPins) -> None:
        mismatches = (
            (stored.sourceDigest, current.sourceDigest, "CONTINUATION_SOURCE_STALE"),
            (stored.queryDigest, current.queryDigest, "CONTINUATION_QUERY_STALE"),
            (stored.contractDigest, current.contractDigest, "CONTINUATION_CONTRACT_STALE"),
            (stored.schemaDigest, current.schemaDigest, "CONTINUATION_SCHEMA_STALE"),
        )
        for storedValue, currentValue, code in mismatches:
            if not hmac.compare_digest(storedValue, currentValue):
                raise ContinuationError(code)

    @staticmethod
    def _validateQueryState(state: ContinuationQueryState, pins: ContinuationPins) -> None:
        if not hmac.compare_digest(bytesDigest(state.queryPayload), pins.queryDigest):
            raise ContinuationError("CONTINUATION_QUERY_STALE")

    @staticmethod
    def _requireLiveRow(row: sqlite3.Row | None, now: float) -> sqlite3.Row:
        if row is None:
            raise ContinuationError("CONTINUATION_INVALID")
        expired = ContinuationStore._storedFloat(row["expires_at"]) <= now
        if expired:
            raise ContinuationError("CONTINUATION_EXPIRED")
        return row

    def _stageArtifact(self, payload: bytes, *, now: float) -> _StagedArtifact:
        digest = hashlib.sha256(payload).hexdigest()
        ownerId = uuid.uuid4().hex
        byteCount = len(payload)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM continuation_artifacts WHERE digest=?",
                (digest,),
            ).fetchone()
            if row is not None and self._storedInt(row["byte_count"]) != byteCount:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if row is not None and row["status"] == "REFERENCED":
                existing = self.cas.readBytes(digest)
                if len(existing) != byteCount:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                return _StagedArtifact(digest, byteCount, ownerId)
            if row is None:
                connection.execute(
                    "INSERT INTO continuation_artifacts "
                    "(digest, byte_count, status, stage_owner, staged_at, referenced_at) "
                    "VALUES (?, ?, 'STAGED', ?, ?, NULL)",
                    (digest, byteCount, ownerId, now),
                )
            else:
                connection.execute(
                    "UPDATE continuation_artifacts SET status='STAGED', stage_owner=?, staged_at=?, "
                    "referenced_at=NULL WHERE digest=?",
                    (ownerId, now, digest),
                )
        # The durable STAGED row makes a crash before publication collectable.
        # A second write transaction closes the registration-check/publication
        # race: maintenance cannot tombstone the row after the check but before
        # the hard-link becomes visible.
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            registered = connection.execute(
                "SELECT byte_count, status FROM continuation_artifacts WHERE digest=?",
                (digest,),
            ).fetchone()
            if (
                registered is None
                or self._storedInt(registered["byte_count"]) != byteCount
                or registered["status"] not in {"STAGED", "REFERENCED"}
            ):
                raise ContinuationError("CONTINUATION_CORRUPT")
            committedDigest = self.cas.putBytes(payload)
            if committedDigest != digest:
                raise ContinuationError("CONTINUATION_CORRUPT")
        return _StagedArtifact(digest, byteCount, ownerId)

    def _referenceArtifact(
        self,
        connection: sqlite3.Connection,
        artifact: _StagedArtifact,
        *,
        now: float,
    ) -> None:
        row = connection.execute(
            "SELECT * FROM continuation_artifacts WHERE digest=?",
            (artifact.digest,),
        ).fetchone()
        if row is None or self._storedInt(row["byte_count"]) != artifact.byteCount:
            raise ContinuationError("CONTINUATION_CORRUPT")
        payload = self.cas.readBytes(artifact.digest)
        if len(payload) != artifact.byteCount:
            raise ContinuationError("CONTINUATION_CORRUPT")
        connection.execute(
            "UPDATE continuation_artifacts SET status='REFERENCED', stage_owner=NULL, referenced_at=? WHERE digest=?",
            (now, artifact.digest),
        )

    @staticmethod
    def _requireReferencedArtifact(
        connection: sqlite3.Connection,
        digest: str,
        *,
        expectedBytes: int | None = None,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM continuation_artifacts WHERE digest=?",
            (digest,),
        ).fetchone()
        if row is None or row["status"] != "REFERENCED":
            raise ContinuationError("CONTINUATION_CORRUPT")
        byteCount = ContinuationStore._storedInt(row["byte_count"])
        if byteCount < 0 or (expectedBytes is not None and byteCount != expectedBytes):
            raise ContinuationError("CONTINUATION_CORRUPT")
        return row

    def issue(
        self,
        state: ContinuationQueryState,
        pins: ContinuationPins,
        *,
        ttlSeconds: float | None = None,
    ) -> IssuedContinuation:
        """Private state를 CAS에 넣고 random bearer token을 발급한다.

        Capabilities:
            bounded state CAS registration과 random token issuance를 원자 조정한다.

        Args:
            state: canonical query와 initial owner cursor.
            pins: source, query, contract, Arrow schema pins.
            ttlSeconds: optional absolute chain lifetime override.

        Returns:
            plaintext token을 1회 담은 repr-safe issuance result.

        Raises:
            ContinuationError: state budget 또는 query pin이 다를 때.

        Example:
            ``issued = store.issue(state, pins)``.

        Guide:
            token 원문은 caller만 보관하고 lineage에는 tokenDigest만 쓴다.

        When:
            bounded 첫 page 이후 다음 owner cursor를 외부 caller에게 넘길 때 호출한다.

        How:
            query pin을 검증하고 SQLite write lock 안에서 CAS와 root row를 등록한다.

        SeeAlso:
            ``loadContext``, ``redeem``.

        Requires:
            state.queryPayload는 pins.queryDigest의 정확한 preimage여야 한다.

        AIContext:
            state CAS write와 ledger registration은 같은 SQLite write lock 안에서 수행한다.
        """
        encodedState = encodeQueryState(state, maxBytes=self.policy.maxStateBytes)
        self._validateQueryState(state, pins)
        ttl = self.policy.tokenTtlSeconds if ttlSeconds is None else ttlSeconds
        try:
            if type(ttl) not in (int, float):
                raise ValueError
            ttlValue = float(ttl)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("ttlSeconds는 유한한 양수여야 합니다") from None
        if not math.isfinite(ttlValue) or ttlValue <= 0:
            raise ValueError("ttlSeconds는 유한한 양수여야 합니다")
        now = self._now()
        expiresAt = now + ttlValue
        if not math.isfinite(expiresAt):
            raise ValueError("ttlSeconds가 유효한 만료 시각을 만들 수 없습니다")
        stagedState = self._stageArtifact(encodedState, now=now)
        for _attempt in range(self.policy.maxTokenIssueAttempts):
            token = encodeToken(secrets.token_bytes(32))
            tokenDigestValue = tokenDigest(token)
            try:
                with self._connection() as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute(
                        "INSERT INTO continuations (token_digest, chain_root_digest, parent_token_digest, "
                        "state_digest, source_digest, query_digest, contract_digest, schema_digest, "
                        "issued_at, expires_at, status) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 'PENDING')",
                        (
                            tokenDigestValue,
                            tokenDigestValue,
                            stagedState.digest,
                            pins.sourceDigest,
                            pins.queryDigest,
                            pins.contractDigest,
                            pins.schemaDigest,
                            now,
                            expiresAt,
                        ),
                    )
                    self._referenceArtifact(connection, stagedState, now=now)
                return IssuedContinuation(token, tokenDigestValue, expiresAt)
            except sqlite3.IntegrityError as error:
                if self._isTokenCollision(error):
                    continue
                raise ContinuationError("CONTINUATION_CORRUPT") from None
        raise ContinuationError("CONTINUATION_TOKEN_COLLISION")

    def loadContext(self, token: str) -> LoadedContinuationContext:
        """token을 검증하고 private CAS state와 stored pins를 복원한다.

        Capabilities:
            token 형식, 존재, 만료, state digest, query pin을 한 경로에서 검증한다.

        Args:
            token: issue 또는 이전 page가 반환한 opaque bearer token.

        Returns:
            token 원문이 없는 private state, pins, lifetime context.

        Raises:
            ContinuationError: 형식, 존재, 만료, CAS, state 검증 실패 시.

        Example:
            ``context = store.loadContext(token)``.

        Guide:
            상위 query 복원은 context.state.queryPayload를 내부에서만 decode한다.

        When:
            continuation-only query가 원래 query와 owner cursor를 복원해야 할 때 호출한다.

        How:
            SQLite write lock으로 prune을 막고 bounded CAS state를 읽어 decode한다.

        SeeAlso:
            ``issue``, ``redeem``.

        Requires:
            private state는 repr, gap, SQLite에 복사하지 않는다.

        AIContext:
            BEGIN IMMEDIATE 동안 CAS를 읽어 prune과 registration race를 차단한다.
        """
        return self._loadContext(token, busySeconds=None)

    def _loadContext(self, token: str, *, busySeconds: float | None) -> LoadedContinuationContext:
        tokenDigestValue = tokenDigest(token)
        now = self._now()
        try:
            with self._connection(busySeconds=busySeconds) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = self._requireLiveRow(
                    connection.execute(
                        "SELECT * FROM continuations WHERE token_digest=?",
                        (tokenDigestValue,),
                    ).fetchone(),
                    now,
                )
                pins = self._pinsFromRow(row)
                stateDigest = self._storedDigest(row["state_digest"])
                artifact = self._requireReferencedArtifact(connection, stateDigest)
                encodedState = self.cas.readBytes(stateDigest, maxBytes=self.policy.maxStateBytes)
                if len(encodedState) != self._storedInt(artifact["byte_count"]):
                    raise ContinuationError("CONTINUATION_CORRUPT")
                state = decodeQueryState(encodedState, maxBytes=self.policy.maxStateBytes)
                self._validateQueryState(state, pins)
                return LoadedContinuationContext(
                    tokenDigest=tokenDigestValue,
                    state=state,
                    pins=pins,
                    issuedAt=self._storedFloat(row["issued_at"]),
                    expiresAt=self._storedFloat(row["expires_at"]),
                )
        except sqlite3.OperationalError as error:
            if self._isSqliteBusy(error):
                raise ContinuationError("CONTINUATION_BUSY") from None
            raise ContinuationError("CONTINUATION_CORRUPT") from None

    def _claim(
        self,
        tokenDigestValue: str,
        pins: ContinuationPins,
        ownerId: str,
        *,
        busySeconds: float | None = None,
    ) -> tuple[str, sqlite3.Row]:
        now = self._now()
        try:
            with self._connection(busySeconds=busySeconds) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = self._requireLiveRow(
                    connection.execute(
                        "SELECT * FROM continuations WHERE token_digest=?",
                        (tokenDigestValue,),
                    ).fetchone(),
                    now,
                )
                self._validatePins(self._pinsFromRow(row), pins)
                status = row["status"]
                if type(status) is not str or status not in {"PENDING", "RUNNING", "SUCCEEDED"}:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                if status == "SUCCEEDED":
                    return "REPLAY", row
                if status == "PENDING" or self._storedFloat(row["lease_until"]) <= now:
                    changed = connection.execute(
                        "UPDATE continuations SET status='RUNNING', owner_id=?, lease_until=? "
                        "WHERE token_digest=? AND status!='SUCCEEDED'",
                        (ownerId, now + self.policy.leaseSeconds, tokenDigestValue),
                    ).rowcount
                    if changed != 1:
                        raise ContinuationError("CONTINUATION_BUSY")
                    claimed = connection.execute(
                        "SELECT * FROM continuations WHERE token_digest=?",
                        (tokenDigestValue,),
                    ).fetchone()
                    if claimed is None:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    return "ACQUIRED", claimed
                return "BUSY", row
        except sqlite3.OperationalError as error:
            if self._isSqliteBusy(error):
                raise ContinuationError("CONTINUATION_BUSY") from None
            raise ContinuationError("CONTINUATION_CORRUPT") from None

    def _renew(self, tokenDigestValue: str, ownerId: str) -> bool:
        now = self._now()
        with self._connection() as connection:
            changed = connection.execute(
                "UPDATE continuations SET lease_until=? WHERE token_digest=? AND status='RUNNING' "
                "AND owner_id=? AND expires_at>?",
                (now + self.policy.leaseSeconds, tokenDigestValue, ownerId, now),
            ).rowcount
        return changed == 1

    def _release(self, tokenDigestValue: str, ownerId: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE continuations SET status='PENDING', owner_id=NULL, lease_until=0 "
                "WHERE token_digest=? AND status='RUNNING' AND owner_id=?",
                (tokenDigestValue, ownerId),
            )

    def _validatePage(self, envelope: PageEnvelope, pins: ContinuationPins) -> ArrowPayloadFacts:
        if envelope.rowCount > self.policy.maxPageRows:
            raise ContinuationError("CONTINUATION_ROW_BUDGET")
        return self.payloadValidator(
            envelope.payload,
            claimedRowCount=envelope.rowCount,
            expectedSchemaDigest=pins.schemaDigest,
            maxPageBytes=self.policy.maxPageBytes,
            maxLogicalBytes=self.policy.maxPageLogicalBytes,
        )

    def _pageFromRow(
        self,
        connection: sqlite3.Connection,
        token: str,
        row: sqlite3.Row,
        *,
        replayed: bool,
    ) -> ContinuationPage:
        required = ("page_digest", "row_count", "byte_count", "result_digest")
        if any(row[name] is None for name in required):
            raise ContinuationError("CONTINUATION_CORRUPT")
        pageDigest = self._storedDigest(row["page_digest"])
        byteCount = self._storedInt(row["byte_count"])
        self._requireReferencedArtifact(connection, pageDigest, expectedBytes=byteCount)
        payload = self.cas.readBytes(
            pageDigest,
            maxBytes=self.policy.maxPageBytes,
            budgetCode="CONTINUATION_BYTE_BUDGET",
        )
        rowCount = self._storedInt(row["row_count"])
        if rowCount < 0 or rowCount > self.policy.maxPageRows or byteCount != len(payload):
            raise ContinuationError("CONTINUATION_CORRUPT")
        pins = self._pinsFromRow(row)
        facts = self.payloadValidator(
            payload,
            claimedRowCount=rowCount,
            expectedSchemaDigest=pins.schemaDigest,
            maxPageBytes=self.policy.maxPageBytes,
            maxLogicalBytes=self.policy.maxPageLogicalBytes,
        )
        nextToken = None
        nextTokenDigestValue = row["next_token_digest"]
        nextStateDigest = row["next_state_digest"]
        if (nextTokenDigestValue is None) != (nextStateDigest is None):
            raise ContinuationError("CONTINUATION_CORRUPT")
        if nextTokenDigestValue is not None and nextStateDigest is not None:
            nextTokenDigestValue = self._storedDigest(nextTokenDigestValue)
            nextStateDigest = self._storedDigest(nextStateDigest)
            nextToken = childToken(token, pageDigest, nextStateDigest)
            if not hmac.compare_digest(tokenDigest(nextToken), nextTokenDigestValue):
                raise ContinuationError("CONTINUATION_CORRUPT")
            child = connection.execute(
                "SELECT * FROM continuations WHERE token_digest=?",
                (nextTokenDigestValue,),
            ).fetchone()
            if child is None:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._storedDigest(child["state_digest"]) != nextStateDigest:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._storedDigest(child["parent_token_digest"]) != self._storedDigest(row["token_digest"]):
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._storedDigest(child["chain_root_digest"]) != self._storedDigest(row["chain_root_digest"]):
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._pinsFromRow(child) != pins or self._storedFloat(child["expires_at"]) != self._storedFloat(
                row["expires_at"]
            ):
                raise ContinuationError("CONTINUATION_CORRUPT")
        expectedResultDigest = _resultDigest(
            self._storedDigest(row["token_digest"]),
            pins,
            pageDigest,
            rowCount,
            byteCount,
            nextTokenDigestValue,
        )
        if not hmac.compare_digest(expectedResultDigest, self._storedDigest(row["result_digest"])):
            raise ContinuationError("CONTINUATION_CORRUPT")
        return ContinuationPage(
            pageRef=f"cas:sha256:{pageDigest}",
            pageDigest=pageDigest,
            payload=payload,
            rowCount=facts.rowCount,
            byteCount=facts.byteCount,
            schemaDigest=facts.schemaDigest,
            nextToken=nextToken,
            replayed=replayed,
            resultDigest=expectedResultDigest,
        )

    def _replay(
        self,
        token: str,
        pins: ContinuationPins,
        *,
        busySeconds: float | None = None,
    ) -> ContinuationPage:
        tokenDigestValue = tokenDigest(token)
        try:
            with self._connection(busySeconds=busySeconds) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = self._requireLiveRow(
                    connection.execute(
                        "SELECT * FROM continuations WHERE token_digest=?",
                        (tokenDigestValue,),
                    ).fetchone(),
                    self._now(),
                )
                self._validatePins(self._pinsFromRow(row), pins)
                if row["status"] != "SUCCEEDED":
                    raise ContinuationError("CONTINUATION_BUSY")
                return self._pageFromRow(connection, token, row, replayed=True)
        except sqlite3.OperationalError as error:
            if self._isSqliteBusy(error):
                raise ContinuationError("CONTINUATION_BUSY") from None
            raise ContinuationError("CONTINUATION_CORRUPT") from None

    def _commit(
        self,
        token: str,
        context: LoadedContinuationContext,
        ownerId: str,
        envelope: PageEnvelope,
    ) -> ContinuationPage:
        facts = self._validatePage(envelope, context.pins)
        pageDigest = hashlib.sha256(envelope.payload).hexdigest()
        encodedNextState = None
        nextStateDigest = None
        nextToken = None
        nextTokenDigestValue = None
        if envelope.nextState is not None:
            self._validateQueryState(envelope.nextState, context.pins)
            encodedNextState = encodeQueryState(envelope.nextState, maxBytes=self.policy.maxStateBytes)
            nextStateDigest = hashlib.sha256(encodedNextState).hexdigest()
            nextToken = childToken(token, pageDigest, nextStateDigest)
            nextTokenDigestValue = tokenDigest(nextToken)
        resultDigest = _resultDigest(
            context.tokenDigest,
            context.pins,
            pageDigest,
            facts.rowCount,
            facts.byteCount,
            nextTokenDigestValue,
        )
        now = self._now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT * FROM continuations WHERE token_digest=?",
                (context.tokenDigest,),
            ).fetchone()
            if current is None:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            if current["status"] == "SUCCEEDED":
                return self._pageFromRow(connection, token, current, replayed=True)
            if current["status"] != "RUNNING" or current["owner_id"] != ownerId:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            self._requireLiveRow(current, self._now())
            self._validatePins(self._pinsFromRow(current), context.pins)
        stagedPage = self._stageArtifact(envelope.payload, now=now)
        stagedNextState = None
        if encodedNextState is not None:
            stagedNextState = self._stageArtifact(encodedNextState, now=now)
            if stagedNextState.digest != nextStateDigest:
                raise ContinuationError("CONTINUATION_CORRUPT")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT * FROM continuations WHERE token_digest=?",
                (context.tokenDigest,),
            ).fetchone()
            if current is None:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            if current["status"] == "SUCCEEDED":
                return self._pageFromRow(connection, token, current, replayed=True)
            if current["status"] != "RUNNING" or current["owner_id"] != ownerId:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            commitNow = self._now()
            self._requireLiveRow(current, commitNow)
            self._validatePins(self._pinsFromRow(current), context.pins)
            if stagedPage.digest != pageDigest:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if stagedNextState is not None and nextStateDigest is not None and nextTokenDigestValue is not None:
                try:
                    connection.execute(
                        "INSERT INTO continuations (token_digest, chain_root_digest, parent_token_digest, "
                        "state_digest, source_digest, query_digest, contract_digest, schema_digest, "
                        "issued_at, expires_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')",
                        (
                            nextTokenDigestValue,
                            str(current["chain_root_digest"]),
                            context.tokenDigest,
                            nextStateDigest,
                            context.pins.sourceDigest,
                            context.pins.queryDigest,
                            context.pins.contractDigest,
                            context.pins.schemaDigest,
                            commitNow,
                            self._storedFloat(current["expires_at"]),
                        ),
                    )
                except sqlite3.IntegrityError as error:
                    if self._isTokenCollision(error):
                        raise ContinuationError("CONTINUATION_TOKEN_COLLISION") from None
                    raise ContinuationError("CONTINUATION_CORRUPT") from None
            changed = connection.execute(
                "UPDATE continuations SET status='SUCCEEDED', owner_id=NULL, lease_until=0, "
                "page_digest=?, row_count=?, byte_count=?, next_token_digest=?, next_state_digest=?, "
                "result_digest=?, completed_at=? WHERE token_digest=? AND status='RUNNING' AND owner_id=?",
                (
                    pageDigest,
                    facts.rowCount,
                    facts.byteCount,
                    nextTokenDigestValue,
                    nextStateDigest,
                    resultDigest,
                    commitNow,
                    context.tokenDigest,
                    ownerId,
                ),
            ).rowcount
            if changed != 1:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            self._referenceArtifact(connection, stagedPage, now=commitNow)
            if stagedNextState is not None:
                self._referenceArtifact(connection, stagedNextState, now=commitNow)
            committed = connection.execute(
                "SELECT * FROM continuations WHERE token_digest=?",
                (context.tokenDigest,),
            ).fetchone()
            if committed is None:
                raise ContinuationError("CONTINUATION_CORRUPT")
            page = self._pageFromRow(connection, token, committed, replayed=False)
            if page.nextToken != nextToken:
                raise ContinuationError("CONTINUATION_CORRUPT")
            return page

    def redeem(
        self,
        token: str,
        pins: ContinuationPins,
        *,
        materialize: Callable[[ContinuationQueryState], PageEnvelope],
        waitSeconds: float | None = None,
    ) -> ContinuationPage:
        """동일 token에 owner 1회와 immutable page replay를 제공한다.

        Capabilities:
            thread와 process 경합에서 active owner 한 명과 committed page 하나를 보장한다.

        Args:
            token: opaque bearer token.
            pins: 현재 실행이 기대하는 exact pins.
            materialize: private state에서 Arrow IPC page를 만드는 pure callback.
            waitSeconds: caller가 허용한 owner 대기 상한. 정책 상한보다 길어질 수 없다.

        Returns:
            검증된 bounded page와 optional deterministic child token.

        Raises:
            ContinuationError: validation, owner, claim, payload 실패 시.

        Example:
            ``page = store.redeem(token, pins, materialize=owner)``.

        Guide:
            같은 token 재호출은 callback 없이 같은 CAS page를 반환한다.

        When:
            기존 data query 축이 token 하나를 실제 다음 page로 교환할 때 호출한다.

        How:
            context load, atomic claim, heartbeat, Arrow validation, CAS commit 순서로 실행한다.

        SeeAlso:
            ``loadContext``, ``pruneExpired``.

        Requires:
            callback은 side-effect free이고 sourceDigest가 고정한 source만 읽는다.

        AIContext:
            crash recovery는 callback 재실행 가능성이 있어 external side effect exactly-once가 아니다.
        """
        selectedWait = self.policy.waitSeconds
        if waitSeconds is not None:
            if type(waitSeconds) not in (int, float):
                raise ValueError("waitSeconds는 유한한 음수 아닌 수여야 합니다")
            try:
                callerWait = float(waitSeconds)
            except (OverflowError, TypeError, ValueError):
                raise ValueError("waitSeconds는 유한한 음수 아닌 수여야 합니다") from None
            if not math.isfinite(callerWait) or callerWait < 0:
                raise ValueError("waitSeconds는 유한한 음수 아닌 수여야 합니다")
            selectedWait = min(selectedWait, callerWait)
        deadline = time.monotonic() + selectedWait
        context = self._loadContext(
            token,
            busySeconds=max(0.0, deadline - time.monotonic()),
        )
        self._validatePins(context.pins, pins)
        ownerId = uuid.uuid4().hex
        while True:
            remaining = max(0.0, deadline - time.monotonic())
            try:
                status, _ = self._claim(
                    context.tokenDigest,
                    pins,
                    ownerId,
                    busySeconds=remaining,
                )
            except ContinuationError as error:
                if error.code != "CONTINUATION_BUSY":
                    raise
                status = "BUSY"
            if status == "REPLAY":
                return self._replay(
                    token,
                    pins,
                    busySeconds=max(0.0, deadline - time.monotonic()),
                )
            if status == "ACQUIRED":
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ContinuationError("CONTINUATION_BUSY")
            time.sleep(min(self.policy.pollSeconds, remaining))
        try:
            with _LeaseHeartbeat(self, context.tokenDigest, ownerId) as heartbeat:
                try:
                    envelope = materialize(context.state)
                except ContinuationError:
                    raise
                except Exception:
                    raise ContinuationError("CONTINUATION_OWNER_FAILED") from None
                if not isinstance(envelope, PageEnvelope):
                    raise ContinuationError("CONTINUATION_OWNER_FAILED")
                if heartbeat.lost:
                    raise ContinuationError("CONTINUATION_CLAIM_LOST")
                return self._commit(token, context, ownerId, envelope)
        except Exception:
            self._release(context.tokenDigest, ownerId)
            raise

    @staticmethod
    def _artifactReferenced(connection: sqlite3.Connection, digest: str) -> bool:
        return (
            connection.execute(
                "SELECT 1 FROM continuations WHERE state_digest=? OR page_digest=? OR next_state_digest=? LIMIT 1",
                (digest, digest, digest),
            ).fetchone()
            is not None
        )

    def _advancePruneWork(
        self,
        connection: sqlite3.Connection,
        *,
        now: float,
        maxRows: int,
    ) -> tuple[int, int, int, bool, str, float]:
        workRows = connection.execute("SELECT * FROM continuation_prune_work LIMIT 2").fetchall()
        if len(workRows) != 1:
            raise ContinuationError("CONTINUATION_CORRUPT")
        work = workRows[0]
        rootDigest = self._storedDigest(work["root_digest"])
        rootExpiry = self._storedFloat(work["expires_at"])
        cursorDigest = self._storedDigest(work["cursor_digest"])
        phase = work["phase"]
        if phase not in {"SCAN", "DELETE"}:
            raise ContinuationError("CONTINUATION_CORRUPT")

        rowsExamined = 0
        rowsDeleted = 0
        while rowsExamined < maxRows:
            row = connection.execute(
                "SELECT * FROM continuations WHERE token_digest=?",
                (cursorDigest,),
            ).fetchone()
            if row is None:
                raise ContinuationError("CONTINUATION_CORRUPT")
            tokenDigestValue = self._storedDigest(row["token_digest"])
            if self._storedDigest(row["chain_root_digest"]) != rootDigest:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._storedFloat(row["expires_at"]) != rootExpiry:
                raise ContinuationError("CONTINUATION_CORRUPT")
            rowsExamined += 1

            if phase == "SCAN":
                if row["status"] == "RUNNING" and self._storedFloat(row["lease_until"]) > now:
                    connection.execute("DELETE FROM continuation_prune_work WHERE root_digest=?", (rootDigest,))
                    return 0, 0, rowsExamined, True, rootDigest, rootExpiry
                childRows = connection.execute(
                    "SELECT token_digest FROM continuations WHERE parent_token_digest=? LIMIT 2",
                    (tokenDigestValue,),
                ).fetchall()
                nextDigestValue = row["next_token_digest"]
                if nextDigestValue is None:
                    if childRows:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    phase = "DELETE"
                    connection.execute(
                        "UPDATE continuation_prune_work SET phase='DELETE', updated_at=? WHERE root_digest=?",
                        (now, rootDigest),
                    )
                else:
                    nextDigest = self._storedDigest(nextDigestValue)
                    if len(childRows) != 1 or self._storedDigest(childRows[0]["token_digest"]) != nextDigest:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    cursorDigest = nextDigest
                    connection.execute(
                        "UPDATE continuation_prune_work SET cursor_digest=?, updated_at=? WHERE root_digest=?",
                        (cursorDigest, now, rootDigest),
                    )
                    continue

            child = connection.execute(
                "SELECT 1 FROM continuations WHERE parent_token_digest=? LIMIT 1",
                (tokenDigestValue,),
            ).fetchone()
            if child is not None:
                raise ContinuationError("CONTINUATION_CORRUPT")
            parentDigestValue = row["parent_token_digest"]
            artifacts = {
                self._storedDigest(value)
                for value in (row["state_digest"], row["page_digest"], row["next_state_digest"])
                if value is not None
            }
            connection.execute("DELETE FROM continuations WHERE token_digest=?", (tokenDigestValue,))
            for digest in artifacts:
                artifact = connection.execute(
                    "SELECT 1 FROM continuation_artifacts WHERE digest=?",
                    (digest,),
                ).fetchone()
                if artifact is None:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                status = "REFERENCED" if self._artifactReferenced(connection, digest) else "GC_PENDING"
                connection.execute(
                    "UPDATE continuation_artifacts SET status=?, stage_owner=NULL, "
                    "referenced_at=CASE WHEN ?='REFERENCED' THEN referenced_at ELSE NULL END "
                    "WHERE digest=?",
                    (status, status, digest),
                )
            rowsDeleted += 1
            if parentDigestValue is None:
                if tokenDigestValue != rootDigest:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                connection.execute("DELETE FROM continuation_prune_work WHERE root_digest=?", (rootDigest,))
                return 1, rowsDeleted, rowsExamined, True, rootDigest, rootExpiry
            cursorDigest = self._storedDigest(parentDigestValue)
            connection.execute(
                "UPDATE continuation_prune_work SET cursor_digest=?, updated_at=? WHERE root_digest=?",
                (cursorDigest, now, rootDigest),
            )

        return 0, rowsDeleted, rowsExamined, False, rootDigest, rootExpiry

    def _sweepExpiredRoots(
        self,
        connection: sqlite3.Connection,
        budget: ContinuationMaintenanceBudget,
        *,
        now: float,
        cutoff: float,
    ) -> tuple[int, int, int, int, int]:
        cursor = self._loadSweep(connection, "roots")
        existingWork = connection.execute("SELECT 1 FROM continuation_prune_work LIMIT 1").fetchone()
        if existingWork is not None:
            deletedChains, deletedRows, rowsExamined, finished, rootDigest, rootExpiry = self._advancePruneWork(
                connection,
                now=now,
                maxRows=budget.maxContinuationRows,
            )
            nextCursor = _SweepCursor(
                "roots",
                rootDigest if finished else cursor.digest,
                rootExpiry if finished else cursor.value,
                cursor.cycle,
            )
            self._saveSweep(connection, nextCursor, now=now)
            return deletedChains, deletedRows, 0, rowsExamined, 0

        rows = connection.execute(
            "SELECT token_digest, expires_at FROM continuations "
            "WHERE parent_token_digest IS NULL AND expires_at<=? "
            "AND (expires_at>? OR (expires_at=? AND token_digest>?)) "
            "ORDER BY expires_at, token_digest LIMIT ?",
            (cutoff, cursor.value, cursor.value, cursor.digest, budget.maxRootScans),
        ).fetchall()
        if not rows:
            self._saveSweep(connection, _SweepCursor("roots", "", 0.0, cursor.cycle + 1), now=now)
            return 0, 0, 0, 0, 1

        rootDigest = self._storedDigest(rows[0]["token_digest"])
        rootExpiry = self._storedFloat(rows[0]["expires_at"])
        connection.execute(
            "INSERT INTO continuation_prune_work "
            "(root_digest, phase, cursor_digest, expires_at, updated_at) VALUES (?, 'SCAN', ?, ?, ?)",
            (rootDigest, rootDigest, rootExpiry, now),
        )
        deletedChains, deletedRows, rowsExamined, finished, _, _ = self._advancePruneWork(
            connection,
            now=now,
            maxRows=budget.maxContinuationRows,
        )
        completedCycle = int(finished and len(rows) == 1 and len(rows) < budget.maxRootScans)
        nextCursor = (
            _SweepCursor("roots", "", 0.0, cursor.cycle + 1)
            if completedCycle
            else _SweepCursor(
                "roots",
                rootDigest if finished else cursor.digest,
                rootExpiry if finished else cursor.value,
                cursor.cycle,
            )
        )
        self._saveSweep(connection, nextCursor, now=now)
        return deletedChains, deletedRows, len(rows), rowsExamined, completedCycle

    def _sweepArtifactLedger(
        self,
        connection: sqlite3.Connection,
        budget: ContinuationMaintenanceBudget,
        *,
        now: float,
        stageCutoff: float,
    ) -> tuple[int, int]:
        cursor = self._loadSweep(connection, "artifacts")
        rows = connection.execute(
            "SELECT * FROM continuation_artifacts WHERE digest>? ORDER BY digest LIMIT ?",
            (cursor.digest, budget.maxLedgerScans),
        ).fetchall()
        lastDigest = cursor.digest
        for row in rows:
            digest = self._storedDigest(row["digest"])
            self._storedInt(row["byte_count"])
            stagedAt = self._storedFloat(row["staged_at"])
            status = row["status"]
            if status == "STAGED":
                if stagedAt <= stageCutoff:
                    if self._artifactReferenced(connection, digest):
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    connection.execute(
                        "UPDATE continuation_artifacts SET status='GC_PENDING', stage_owner=NULL WHERE digest=?",
                        (digest,),
                    )
            elif status == "REFERENCED":
                if not self._artifactReferenced(connection, digest):
                    connection.execute(
                        "UPDATE continuation_artifacts SET status='GC_PENDING', referenced_at=NULL WHERE digest=?",
                        (digest,),
                    )
            elif status != "GC_PENDING":
                raise ContinuationError("CONTINUATION_CORRUPT")
            lastDigest = digest

        completedCycle = int(len(rows) < budget.maxLedgerScans)
        nextCursor = _SweepCursor(
            "artifacts",
            "" if completedCycle else lastDigest,
            0.0,
            cursor.cycle + completedCycle,
        )
        self._saveSweep(connection, nextCursor, now=now)
        return len(rows), completedCycle

    def _sweepCasOrphans(
        self,
        connection: sqlite3.Connection,
        budget: ContinuationMaintenanceBudget,
        *,
        now: float,
    ) -> tuple[int, int, int]:
        cursor = self._loadSweep(connection, "cas")
        prefix = int(cursor.value)
        prefixesScanned = 0
        entriesExamined = 0
        completedCycles = 0
        while prefixesScanned < budget.maxCasPrefixes and entriesExamined < budget.maxCasEntries:
            page = self.cas.scanLegacyPrefix(
                prefix,
                limit=budget.maxCasEntries - entriesExamined,
            )
            prefixesScanned += 1
            entriesExamined += page.entriesExamined
            allRemoved = True
            for digest in page.digests:
                artifact = connection.execute(
                    "SELECT * FROM continuation_artifacts WHERE digest=?",
                    (digest,),
                ).fetchone()
                if artifact is None:
                    connection.execute(
                        "INSERT INTO continuation_artifacts "
                        "(digest, byte_count, status, stage_owner, staged_at, referenced_at) "
                        "VALUES (?, ?, 'GC_PENDING', NULL, ?, NULL)",
                        (digest, self.cas.byteCount(digest), now),
                    )
                    allRemoved = False
                else:
                    expectedBytes = self._storedInt(artifact["byte_count"])
                    if self.cas.byteCount(digest) != expectedBytes:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    status = artifact["status"]
                    if status == "REFERENCED" and not self._artifactReferenced(connection, digest):
                        connection.execute(
                            "UPDATE continuation_artifacts SET status='GC_PENDING', referenced_at=NULL WHERE digest=?",
                            (digest,),
                        )
                        allRemoved = False
                    elif status == "GC_PENDING":
                        allRemoved = False
                    elif status in {"REFERENCED", "STAGED"}:
                        self.cas.migrateLegacyDigest(digest)
                    else:
                        raise ContinuationError("CONTINUATION_CORRUPT")

            if not page.complete or not allRemoved:
                break
            if prefix == 0xFF:
                prefix = 0
                completedCycles += 1
            else:
                prefix += 1

        nextCursor = _SweepCursor("cas", "", float(prefix), cursor.cycle + completedCycles)
        self._saveSweep(connection, nextCursor, now=now)
        return prefixesScanned, entriesExamined, completedCycles

    def _deletePendingArtifacts(
        self,
        connection: sqlite3.Connection,
        budget: ContinuationMaintenanceBudget,
        *,
        now: float,
    ) -> tuple[int, int]:
        artifactsDeleted = 0
        bytesFreed = 0
        tombstones = connection.execute(
            "SELECT digest, byte_count FROM continuation_artifacts "
            "WHERE status='GC_PENDING' ORDER BY staged_at, digest LIMIT ?",
            (budget.maxArtifactDeletes,),
        ).fetchall()
        for tombstone in tombstones:
            digest = self._storedDigest(tombstone["digest"])
            expectedBytes = self._storedInt(tombstone["byte_count"])
            if self._artifactReferenced(connection, digest):
                connection.execute(
                    "UPDATE continuation_artifacts SET status='REFERENCED', referenced_at=? WHERE digest=?",
                    (now, digest),
                )
                continue
            deleted, byteCount = self.cas.deleteBytes(digest)
            if deleted and byteCount != expectedBytes:
                raise ContinuationError("CONTINUATION_CORRUPT")
            connection.execute("DELETE FROM continuation_artifacts WHERE digest=?", (digest,))
            artifactsDeleted += int(deleted)
            bytesFreed += byteCount
        return artifactsDeleted, bytesFreed

    def maintain(self, budget: ContinuationMaintenanceBudget | None = None) -> PruneReport:
        """Persistent sweep cursor로 continuation control plane을 bounded 정리한다.

        Capabilities:
            expired chain, dangling ledger, CAS orphan, tombstone을 독립 budget 안에서 정리한다.

        Args:
            budget: 호출당 root, ledger, CAS prefix, artifact 처리 상한.

        Returns:
            삭제량과 안전한 scan telemetry만 담은 report.

        Raises:
            ContinuationError: ledger, cursor, CAS 무결성 또는 보안 검증 실패 시.
            TypeError: budget 타입이 잘못됐을 때.

        Example:
            ``report = store.maintain(ContinuationMaintenanceBudget(maxCasPrefixes=4))``.

        Guide:
            짧은 cadence로 반복 호출하면 restart를 거쳐서도 모든 sweep이 wrap한다.

        When:
            data query runtime이 request latency를 예측 가능하게 유지하며 cleanup할 때 호출한다.

        How:
            SQLite cursor와 mutation을 한 transaction에 commit하고 CAS delete는 tombstone 뒤 수행한다.

        SeeAlso:
            ``pruneExpired``, ``verifyIntegrity``.

        Requires:
            issue와 commit CAS registration은 같은 SQLite ledger를 사용해야 한다.

        AIContext:
            report에는 digest, path, token, query, cursor 원문을 넣지 않는다.
        """
        selected = budget or ContinuationMaintenanceBudget()
        if not isinstance(selected, ContinuationMaintenanceBudget):
            raise TypeError("budget은 ContinuationMaintenanceBudget이어야 합니다")
        now = self._now()
        cutoff = now - self.policy.pruneGraceSeconds
        stageCutoff = now - self.policy.artifactStageSeconds
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            deletedChains, deletedRows, rootsScanned, continuationRows, rootCycles = self._sweepExpiredRoots(
                connection,
                selected,
                now=now,
                cutoff=cutoff,
            )
            ledgerScanned, ledgerCycles = self._sweepArtifactLedger(
                connection,
                selected,
                now=now,
                stageCutoff=stageCutoff,
            )
            casPrefixes, casEntries, casCycles = self._sweepCasOrphans(
                connection,
                selected,
                now=now,
            )

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            artifactsDeleted, bytesFreed = self._deletePendingArtifacts(connection, selected, now=now)
        return PruneReport(
            chainsDeleted=deletedChains,
            rowsDeleted=deletedRows,
            artifactsDeleted=artifactsDeleted,
            bytesFreed=bytesFreed,
            rootsScanned=rootsScanned,
            continuationRowsExamined=continuationRows,
            ledgerArtifactsScanned=ledgerScanned,
            casPrefixesScanned=casPrefixes,
            casEntriesExamined=casEntries,
            sweepCyclesCompleted=rootCycles + ledgerCycles + casCycles,
        )

    def pruneExpired(self, *, maxChains: int = 100, maxArtifacts: int = 10_000) -> PruneReport:
        """기존 bounds를 persistent bounded maintenance budget으로 변환한다."""
        if type(maxChains) is not int or type(maxArtifacts) is not int or maxChains <= 0 or maxArtifacts <= 0:
            raise ValueError("prune bounds는 양의 int여야 합니다")
        return self.maintain(
            ContinuationMaintenanceBudget(
                maxChains=maxChains,
                maxRootScans=maxChains * 4,
                maxContinuationRows=maxArtifacts,
                maxLedgerScans=maxArtifacts,
                maxCasPrefixes=16,
                maxCasEntries=maxArtifacts,
                maxArtifactDeletes=maxArtifacts,
            )
        )

    def _verifySucceededRow(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        rowsByDigest: dict[str, sqlite3.Row],
    ) -> None:
        required = ("page_digest", "row_count", "byte_count", "result_digest")
        if any(row[name] is None for name in required):
            raise ContinuationError("CONTINUATION_CORRUPT")
        pageDigest = self._storedDigest(row["page_digest"])
        byteCount = self._storedInt(row["byte_count"])
        self._requireReferencedArtifact(connection, pageDigest, expectedBytes=byteCount)
        payload = self.cas.readBytes(
            pageDigest,
            maxBytes=self.policy.maxPageBytes,
            budgetCode="CONTINUATION_BYTE_BUDGET",
        )
        rowCount = self._storedInt(row["row_count"])
        if byteCount != len(payload) or rowCount < 0 or rowCount > self.policy.maxPageRows:
            raise ContinuationError("CONTINUATION_CORRUPT")
        pins = self._pinsFromRow(row)
        self.payloadValidator(
            payload,
            claimedRowCount=rowCount,
            expectedSchemaDigest=pins.schemaDigest,
            maxPageBytes=self.policy.maxPageBytes,
            maxLogicalBytes=self.policy.maxPageLogicalBytes,
        )
        childDigest = row["next_token_digest"]
        nextStateDigest = row["next_state_digest"]
        if (childDigest is None) != (nextStateDigest is None):
            raise ContinuationError("CONTINUATION_CORRUPT")
        if childDigest is not None:
            childDigest = self._storedDigest(childDigest)
            nextStateDigest = self._storedDigest(nextStateDigest)
            child = rowsByDigest.get(childDigest)
            if child is None or child["state_digest"] != nextStateDigest:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if child["parent_token_digest"] != row["token_digest"]:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if child["chain_root_digest"] != row["chain_root_digest"]:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._pinsFromRow(child) != pins:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._storedFloat(child["expires_at"]) != self._storedFloat(row["expires_at"]):
                raise ContinuationError("CONTINUATION_CORRUPT")
        expected = _resultDigest(
            self._storedDigest(row["token_digest"]),
            pins,
            pageDigest,
            rowCount,
            byteCount,
            childDigest,
        )
        if not hmac.compare_digest(expected, self._storedDigest(row["result_digest"])):
            raise ContinuationError("CONTINUATION_CORRUPT")

    def verifyIntegrity(self) -> bool:
        """SQLite graph, private state, pins, Arrow pages, CAS를 전수 검증한다.

        Args:
            없음.

        Returns:
            모든 검증을 통과하면 True.

        Raises:
            ContinuationError: ledger 또는 artifact가 불완전할 때.

        Example:
            ``assert store.verifyIntegrity()``.

        Guide:
            owner callback을 호출하지 않으며 bearer token 원문도 요구하지 않는다.

        SeeAlso:
            ``pruneExpired``.

        Requires:
            같은 root를 다른 코드가 직접 수정하지 않는다.

        AIContext:
            actual Arrow rows와 schema까지 읽어 promotion evidence를 만든다.
        """
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            check = connection.execute("PRAGMA integrity_check").fetchone()
            foreignKeyErrors = connection.execute("PRAGMA foreign_key_check").fetchall()
            version = connection.execute("PRAGMA user_version").fetchone()
            rows = connection.execute("SELECT * FROM continuations ORDER BY token_digest").fetchall()
            artifacts = connection.execute("SELECT * FROM continuation_artifacts ORDER BY digest").fetchall()
            if check is None or check[0] != "ok" or foreignKeyErrors:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if version is None or self._storedInt(version[0]) != _SCHEMA_VERSION:
                raise ContinuationError("CONTINUATION_CORRUPT")
            try:
                self._validateSchemaV3(connection)
            except ContinuationError:
                raise ContinuationError("CONTINUATION_CORRUPT") from None

            for path in (
                self.root,
                self.databasePath,
                self.cas.root,
                self.cas.root / "objects",
                self.cas.legacyObjectRoot,
                self.cas.objectRoot,
            ):
                verifyPrivatePath(path)
            for suffix in ("-wal", "-shm"):
                sidecar = Path(f"{self.databasePath}{suffix}")
                if sidecar.exists():
                    verifyPrivatePath(sidecar)

            artifactDigests = {self._storedDigest(row["digest"]) for row in artifacts}
            casDigests = set(self.cas.iterDigests())
            if artifactDigests != casDigests:
                raise ContinuationError("CONTINUATION_CORRUPT")
            for artifact in artifacts:
                digest = self._storedDigest(artifact["digest"])
                byteCount = self._storedInt(artifact["byte_count"])
                if artifact["status"] != "REFERENCED":
                    raise ContinuationError("CONTINUATION_CORRUPT")
                if artifact["stage_owner"] is not None or artifact["referenced_at"] is None:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                self._storedFloat(artifact["staged_at"])
                self._storedFloat(artifact["referenced_at"])
                if not self._artifactReferenced(connection, digest):
                    raise ContinuationError("CONTINUATION_CORRUPT")
                payload = self.cas.readBytes(digest)
                if len(payload) != byteCount:
                    raise ContinuationError("CONTINUATION_CORRUPT")

            rowsByDigest = {self._storedDigest(row["token_digest"]): row for row in rows}
            for row in rows:
                tokenDigestValue = self._storedDigest(row["token_digest"])
                rootDigest = self._storedDigest(row["chain_root_digest"])
                stateDigest = self._storedDigest(row["state_digest"])
                issuedAt = self._storedFloat(row["issued_at"])
                expiresAt = self._storedFloat(row["expires_at"])
                leaseUntil = self._storedFloat(row["lease_until"])
                if expiresAt <= issuedAt:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                if row["completed_at"] is not None:
                    completedAt = self._storedFloat(row["completed_at"])
                    if completedAt < issuedAt:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                root = rowsByDigest.get(rootDigest)
                if root is None or root["parent_token_digest"] is not None:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                if self._storedFloat(root["expires_at"]) != expiresAt:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                pins = self._pinsFromRow(row)
                artifact = self._requireReferencedArtifact(connection, stateDigest)
                stateBytes = self.cas.readBytes(stateDigest, maxBytes=self.policy.maxStateBytes)
                if self._storedInt(artifact["byte_count"]) != len(stateBytes):
                    raise ContinuationError("CONTINUATION_CORRUPT")
                state = decodeQueryState(stateBytes, maxBytes=self.policy.maxStateBytes)
                self._validateQueryState(state, pins)
                parentDigest = row["parent_token_digest"]
                if parentDigest is not None:
                    parentDigest = self._storedDigest(parentDigest)
                    parent = rowsByDigest.get(parentDigest)
                    if parent is None or str(parent["chain_root_digest"]) != rootDigest:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    if parent["status"] != "SUCCEEDED" or parent["next_token_digest"] != tokenDigestValue:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                status = row["status"]
                if status == "PENDING":
                    if row["owner_id"] is not None or leaseUntil != 0:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    if any(
                        row[name] is not None
                        for name in (
                            "page_digest",
                            "row_count",
                            "byte_count",
                            "next_token_digest",
                            "next_state_digest",
                            "result_digest",
                            "completed_at",
                        )
                    ):
                        raise ContinuationError("CONTINUATION_CORRUPT")
                elif status == "RUNNING":
                    if type(row["owner_id"]) is not str or not row["owner_id"] or leaseUntil <= 0:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    if any(
                        row[name] is not None
                        for name in (
                            "page_digest",
                            "row_count",
                            "byte_count",
                            "next_token_digest",
                            "next_state_digest",
                            "result_digest",
                            "completed_at",
                        )
                    ):
                        raise ContinuationError("CONTINUATION_CORRUPT")
                elif status == "SUCCEEDED":
                    if row["owner_id"] is not None or leaseUntil != 0 or row["completed_at"] is None:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    self._verifySucceededRow(connection, row, rowsByDigest)
                else:
                    raise ContinuationError("CONTINUATION_CORRUPT")
        return True
