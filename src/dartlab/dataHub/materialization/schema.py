"""Digest-only SQLite schema for immutable materialization generations."""

from __future__ import annotations

import sqlite3

from .contracts import SCHEMA_VERSION, MaterializationError

EXPECTED_OBJECTS = {
    "materialization_artifacts",
    "materialization_generations",
    "materialization_pages",
    "materialization_readers",
    "materialization_generation_identity_immutable",
    "materialization_ready_result_immutable",
    "materialization_page_immutable",
    "materialization_ready_page_no_delete",
    "materialization_artifact_identity_immutable",
}

EXPECTED_COLUMNS = {
    "materialization_artifacts": {
        "digest",
        "byte_count",
        "status",
        "reference_count",
        "staged_at",
    },
    "materialization_generations": {
        "generation_key",
        "asset_digest",
        "source_digest",
        "query_digest",
        "universe_digest",
        "contract_digest",
        "schema_digest",
        "status",
        "build_owner_digest",
        "build_epoch",
        "lease_until",
        "created_at",
        "updated_at",
        "published_at",
        "terminal_root_digest",
        "page_count",
        "row_count",
        "byte_count",
    },
    "materialization_pages": {
        "generation_key",
        "ordinal",
        "payload_digest",
        "row_count",
        "byte_count",
        "logical_byte_count",
        "schema_digest",
    },
    "materialization_readers": {
        "generation_key",
        "reader_digest",
        "expires_at",
    },
}


def createSchema(connection: sqlite3.Connection) -> None:
    """새 private ledger에 지원하는 schema를 원자적으로 만든다."""

    connection.executescript(
        """
        BEGIN IMMEDIATE;
        CREATE TABLE materialization_artifacts (
            digest TEXT PRIMARY KEY,
            byte_count INTEGER NOT NULL CHECK(byte_count >= 0),
            status TEXT NOT NULL CHECK(status IN ('STAGED', 'REFERENCED', 'GC_PENDING')),
            reference_count INTEGER NOT NULL CHECK(reference_count >= 0),
            staged_at REAL NOT NULL CHECK(staged_at >= 0)
        );
        CREATE INDEX materialization_artifact_gc
        ON materialization_artifacts(status, staged_at, digest);

        CREATE TABLE materialization_generations (
            generation_key TEXT PRIMARY KEY,
            asset_digest TEXT NOT NULL,
            source_digest TEXT NOT NULL,
            query_digest TEXT NOT NULL,
            universe_digest TEXT NOT NULL,
            contract_digest TEXT NOT NULL,
            schema_digest TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('BUILDING', 'READY', 'GC_PENDING')),
            build_owner_digest TEXT,
            build_epoch INTEGER NOT NULL CHECK(build_epoch > 0),
            lease_until REAL NOT NULL CHECK(lease_until >= 0),
            created_at REAL NOT NULL CHECK(created_at >= 0),
            updated_at REAL NOT NULL CHECK(updated_at >= 0),
            published_at REAL,
            terminal_root_digest TEXT REFERENCES materialization_artifacts(digest),
            page_count INTEGER,
            row_count INTEGER,
            byte_count INTEGER
        );
        CREATE INDEX materialization_generation_status
        ON materialization_generations(status, lease_until, published_at, generation_key);

        CREATE TABLE materialization_pages (
            generation_key TEXT NOT NULL
                REFERENCES materialization_generations(generation_key) ON DELETE CASCADE,
            ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
            payload_digest TEXT NOT NULL REFERENCES materialization_artifacts(digest),
            row_count INTEGER NOT NULL CHECK(row_count >= 0),
            byte_count INTEGER NOT NULL CHECK(byte_count >= 0),
            logical_byte_count INTEGER NOT NULL CHECK(logical_byte_count >= 0),
            schema_digest TEXT NOT NULL,
            PRIMARY KEY(generation_key, ordinal)
        );

        CREATE TABLE materialization_readers (
            generation_key TEXT NOT NULL
                REFERENCES materialization_generations(generation_key) ON DELETE CASCADE,
            reader_digest TEXT PRIMARY KEY,
            expires_at REAL NOT NULL CHECK(expires_at >= 0)
        );
        CREATE INDEX materialization_reader_expiry
        ON materialization_readers(expires_at, generation_key);

        CREATE TRIGGER materialization_generation_identity_immutable
        BEFORE UPDATE ON materialization_generations
        WHEN OLD.generation_key != NEW.generation_key
          OR OLD.asset_digest != NEW.asset_digest
          OR OLD.source_digest != NEW.source_digest
          OR OLD.query_digest != NEW.query_digest
          OR OLD.universe_digest != NEW.universe_digest
          OR OLD.contract_digest != NEW.contract_digest
          OR OLD.schema_digest != NEW.schema_digest
          OR OLD.created_at != NEW.created_at
        BEGIN
            SELECT RAISE(ABORT, 'materialization generation identity is immutable');
        END;

        CREATE TRIGGER materialization_ready_result_immutable
        BEFORE UPDATE ON materialization_generations
        WHEN OLD.status='READY'
          AND (
              NEW.status != 'GC_PENDING'
              OR OLD.terminal_root_digest != NEW.terminal_root_digest
              OR OLD.page_count != NEW.page_count
              OR OLD.row_count != NEW.row_count
              OR OLD.byte_count != NEW.byte_count
              OR OLD.published_at != NEW.published_at
          )
        BEGIN
            SELECT RAISE(ABORT, 'materialization READY result is immutable');
        END;

        CREATE TRIGGER materialization_page_immutable
        BEFORE UPDATE ON materialization_pages
        BEGIN
            SELECT RAISE(ABORT, 'materialization page is immutable');
        END;

        CREATE TRIGGER materialization_ready_page_no_delete
        BEFORE DELETE ON materialization_pages
        WHEN (
            SELECT status FROM materialization_generations
            WHERE generation_key=OLD.generation_key
        )='READY'
        BEGIN
            SELECT RAISE(ABORT, 'materialization READY page is immutable');
        END;

        CREATE TRIGGER materialization_artifact_identity_immutable
        BEFORE UPDATE ON materialization_artifacts
        WHEN OLD.digest != NEW.digest OR OLD.byte_count != NEW.byte_count
        BEGIN
            SELECT RAISE(ABORT, 'materialization artifact identity is immutable');
        END;

        PRAGMA user_version=1;
        COMMIT;
        """
    )


def tableColumns(connection: sqlite3.Connection, table: str) -> set[str]:
    """지원 대상 table의 실제 column 집합을 읽는다."""

    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}


def validateSchema(connection: sqlite3.Connection) -> None:
    """기존 ledger가 정확한 production schema인지 검증한다."""

    versionRow = connection.execute("PRAGMA user_version").fetchone()
    if versionRow is None or int(versionRow[0]) != SCHEMA_VERSION:
        raise MaterializationError("MATERIALIZATION_SCHEMA_UNSUPPORTED")
    actualObjects = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'trigger') AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }
    if actualObjects != EXPECTED_OBJECTS:
        raise MaterializationError("MATERIALIZATION_SCHEMA_UNSUPPORTED")
    for table, columns in EXPECTED_COLUMNS.items():
        if tableColumns(connection, table) != columns:
            raise MaterializationError("MATERIALIZATION_SCHEMA_UNSUPPORTED")
