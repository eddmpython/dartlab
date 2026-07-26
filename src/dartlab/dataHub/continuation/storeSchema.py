"""Continuation ledger DDL, 인덱스, 스키마 마이그레이션 계층.

분할 근거는 파일 크기 룰이다. 원본 단일 파일이 1,976 줄이라 SQLite 관심사별로
선형 mixin 체인으로 나눈다. 체인 순서는 base, schema, artifacts, gc, integrity 이고
구체 클래스는 `continuationStore.ContinuationStore` 하나뿐이다.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from collections.abc import Callable

from .contracts import (
    ArrowPayloadFacts,
    ContinuationError,
)

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_INITIALIZE_LOCK = threading.Lock()
_PayloadValidator = Callable[..., ArrowPayloadFacts]
_SCHEMA_VERSION = 3
_SWEEP_NAMES = frozenset({"artifacts", "cas", "roots"})


from .storeBase import _ContinuationStoreBase


class _ContinuationStoreSchema(_ContinuationStoreBase):
    """Continuation ledger DDL, 인덱스, 스키마 마이그레이션 계층."""

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
