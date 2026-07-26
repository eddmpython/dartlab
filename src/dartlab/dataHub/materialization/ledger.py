"""Private digest-only ledger and builder lease operations."""

from __future__ import annotations

import hashlib
import hmac
import math
import sqlite3
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from dartlab.dataHub.continuation import ArtifactStore, ContinuationError
from dartlab.dataHub.continuation.privateStorage import (
    _resolvePrivateRoot,
    securePrivatePath,
    verifyPrivatePath,
)
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

from .contracts import (
    BuildClaim,
    GenerationPins,
    MaterializationError,
    MaterializationPolicy,
    PageRecord,
    generationKey,
    identityDigest,
    isDigest,
    raiseFromContinuation,
    requireDigest,
    requireNonNegativeInt,
    requireNonNegativeNumber,
)
from .schema import createSchema, validateSchema

INITIALIZE_LOCK = threading.RLock()


_log = dataHubLogger(__name__)


class MaterializationLedger:
    """Private immutable generation ledger.

    Capabilities:
        private root 검증, digest-only SQLite, STAGED CAS 등록, builder epoch,
        reader lease를 제공한다.

    Args:
        root: 전용 private materialization root.
        policy: page, lease, generation, retention 상한.
        clock: Unix time supplier.

    Returns:
        하위 publication, replay, maintenance 계층이 공유하는 ledger.

    Example:
        ``ledger = MaterializationLedger(privateRoot)``.

    Guide:
        공개 query가 아니라 ``MaterializationStore``를 통해 사용한다.

    SeeAlso:
        ``dartlab.dataHub.materialization.MaterializationStore``.

    Requires:
        root와 모든 자식 경로가 symlink 또는 reparse point가 아니어야 한다.

    AIContext:
        SQLite에는 digest와 수치 metadata만 저장한다.
    """

    def __init__(
        self,
        root: Path,
        policy: MaterializationPolicy | None = None,
        clock: Callable[[], float] = time.time,
    ):
        if not callable(clock):
            raise MaterializationError("MATERIALIZATION_INVALID")
        try:
            self.root = _resolvePrivateRoot(Path(root))
            self.root.mkdir(parents=True, exist_ok=True)
            securePrivatePath(self.root)
            self.cas = ArtifactStore(
                self.root / "cas",
                registrationCheck=self._artifactRegisteredForPublish,
            )
        except ContinuationError as error:
            raiseFromContinuation(error)
        self.policy = policy or MaterializationPolicy()
        self.clock = clock
        self.databasePath = self.root / "materializations.sqlite"
        with INITIALIZE_LOCK:
            self._initialize()

    def _artifactRegisteredForPublish(self, digest: str, byteCount: int) -> bool:
        if not isDigest(digest) or type(byteCount) is not int or byteCount < 0:
            return False
        try:
            with self._connection() as connection:
                row = connection.execute(
                    "SELECT byte_count, status FROM materialization_artifacts WHERE digest=?",
                    (digest,),
                ).fetchone()
        except MaterializationError:
            return False
        return (
            row is not None
            and requireNonNegativeInt(row["byte_count"]) == byteCount
            and row["status"] in {"STAGED", "REFERENCED"}
        )

    def _now(self) -> float:
        try:
            now = float(self.clock())
        except Exception:
            recordFailure(_log, "MATERIALIZATION_INVALID")
            raise MaterializationError("MATERIALIZATION_INVALID") from None
        if not math.isfinite(now) or now < 0:
            raise MaterializationError("MATERIALIZATION_INVALID")
        return now

    def _assertPrivateStorage(self) -> None:
        try:
            if _resolvePrivateRoot(self.root) != self.root:
                raise MaterializationError("MATERIALIZATION_SECURITY")
            if _resolvePrivateRoot(self.cas.root) != self.cas.root:
                raise MaterializationError("MATERIALIZATION_SECURITY")
            verifyPrivatePath(self.root)
            verifyPrivatePath(self.cas.root)
            if self.databasePath.exists():
                if _resolvePrivateRoot(self.databasePath) != self.databasePath:
                    raise MaterializationError("MATERIALIZATION_SECURITY")
                verifyPrivatePath(self.databasePath)
        except MaterializationError:
            raise
        except ContinuationError as error:
            raiseFromContinuation(error)

    def _connect(self) -> sqlite3.Connection:
        self._assertPrivateStorage()
        try:
            connection = sqlite3.connect(
                self.databasePath,
                timeout=15.0,
                isolation_level=None,
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("PRAGMA busy_timeout=15000")
            securePrivatePath(self.databasePath)
            for suffix in ("-wal", "-shm"):
                sidecar = Path(f"{self.databasePath}{suffix}")
                if sidecar.exists():
                    securePrivatePath(sidecar)
            return connection
        except ContinuationError as error:
            raiseFromContinuation(error)
        except sqlite3.DatabaseError:
            raise MaterializationError("MATERIALIZATION_CORRUPT") from None

    @contextmanager
    def _connection(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.execute("COMMIT")
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.DatabaseError:
                pass
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            versionRow = connection.execute("PRAGMA user_version").fetchone()
            if versionRow is None:
                raise MaterializationError("MATERIALIZATION_SCHEMA_UNSUPPORTED")
            version = int(versionRow[0])
            objects = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table', 'trigger') AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            }
            if version == 0 and not objects:
                createSchema(connection)
            else:
                validateSchema(connection)
        except MaterializationError:
            raise
        except sqlite3.DatabaseError:
            raise MaterializationError("MATERIALIZATION_SCHEMA_UNSUPPORTED") from None
        finally:
            connection.close()
        try:
            securePrivatePath(self.databasePath)
        except ContinuationError as error:
            raiseFromContinuation(error)

    @staticmethod
    def _pinsFromRow(row: sqlite3.Row) -> GenerationPins:
        try:
            return GenerationPins(
                assetDigest=requireDigest(row["asset_digest"]),
                sourceDigest=requireDigest(row["source_digest"]),
                queryDigest=requireDigest(row["query_digest"]),
                universeDigest=requireDigest(row["universe_digest"]),
                contractDigest=requireDigest(row["contract_digest"]),
                schemaDigest=requireDigest(row["schema_digest"]),
            )
        except (KeyError, ValueError):
            raise MaterializationError("MATERIALIZATION_CORRUPT") from None

    @staticmethod
    def _samePins(expected: GenerationPins, current: GenerationPins) -> bool:
        return all(
            hmac.compare_digest(getattr(expected, name), getattr(current, name))
            for name in (
                "assetDigest",
                "sourceDigest",
                "queryDigest",
                "universeDigest",
                "contractDigest",
                "schemaDigest",
            )
        )

    @staticmethod
    def _pageRecord(row: sqlite3.Row) -> PageRecord:
        try:
            return PageRecord(
                ordinal=requireNonNegativeInt(row["ordinal"]),
                payloadDigest=requireDigest(row["payload_digest"]),
                rowCount=requireNonNegativeInt(row["row_count"]),
                byteCount=requireNonNegativeInt(row["byte_count"]),
                logicalByteCount=requireNonNegativeInt(row["logical_byte_count"]),
                schemaDigest=requireDigest(row["schema_digest"]),
            )
        except KeyError:
            raise MaterializationError("MATERIALIZATION_CORRUPT") from None

    def _assertGenerationRow(
        self,
        row: sqlite3.Row | None,
        *,
        key: str,
        pins: GenerationPins,
    ) -> sqlite3.Row:
        if row is None or not hmac.compare_digest(
            requireDigest(row["generation_key"]),
            key,
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        if not self._samePins(pins, self._pinsFromRow(row)):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return row

    def _assertLease(
        self,
        connection: sqlite3.Connection,
        claim: BuildClaim,
        *,
        now: float,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM materialization_generations WHERE generation_key=?",
            (claim.generationKey,),
        ).fetchone()
        row = self._assertGenerationRow(
            row,
            key=claim.generationKey,
            pins=claim.pins,
        )
        if (
            row["status"] != "BUILDING"
            or not hmac.compare_digest(
                requireDigest(row["build_owner_digest"]),
                claim.ownerDigest,
            )
            or requireNonNegativeInt(row["build_epoch"]) != claim.epoch
            or requireNonNegativeNumber(row["lease_until"]) <= now
        ):
            raise MaterializationError("MATERIALIZATION_LEASE_LOST")
        return row

    def _releaseArtifactReference(
        self,
        connection: sqlite3.Connection,
        digest: str,
        *,
        now: float,
    ) -> None:
        row = connection.execute(
            "SELECT status, reference_count FROM materialization_artifacts WHERE digest=?",
            (digest,),
        ).fetchone()
        if row is None:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        references = requireNonNegativeInt(row["reference_count"])
        if references <= 0:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        nextReferences = references - 1
        connection.execute(
            "UPDATE materialization_artifacts SET reference_count=?, status=?, staged_at=? WHERE digest=?",
            (
                nextReferences,
                "GC_PENDING" if nextReferences == 0 else "REFERENCED",
                now,
                digest,
            ),
        )

    def _discardBuildingPages(
        self,
        connection: sqlite3.Connection,
        key: str,
        *,
        now: float,
    ) -> None:
        rows = connection.execute(
            "SELECT ordinal, payload_digest FROM materialization_pages WHERE generation_key=? ORDER BY ordinal",
            (key,),
        ).fetchall()
        if len(rows) > self.policy.maxPagesPerGeneration:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        for row in rows:
            ordinal = requireNonNegativeInt(row["ordinal"])
            digest = requireDigest(row["payload_digest"])
            cursor = connection.execute(
                "DELETE FROM materialization_pages WHERE generation_key=? AND ordinal=?",
                (key, ordinal),
            )
            if cursor.rowcount != 1:
                raise MaterializationError("MATERIALIZATION_CORRUPT")
            self._releaseArtifactReference(connection, digest, now=now)

    def claimBuild(self, pins: GenerationPins, *, builderId: str) -> BuildClaim:
        """한 exact generation을 claim하거나 live builder를 관찰한다."""

        key = generationKey(pins)
        ownerDigest = identityDigest(builderId)
        now = self._now()
        leaseUntil = now + self.policy.builderLeaseSeconds
        with self._connection(immediate=True) as connection:
            row = connection.execute(
                "SELECT * FROM materialization_generations WHERE generation_key=?",
                (key,),
            ).fetchone()
            if row is None:
                connection.execute(
                    """
                    INSERT INTO materialization_generations (
                        generation_key, asset_digest, source_digest, query_digest,
                        universe_digest, contract_digest, schema_digest, status,
                        build_owner_digest, build_epoch, lease_until, created_at, updated_at,
                        published_at, terminal_root_digest, page_count, row_count, byte_count
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, 'BUILDING', ?, 1, ?, ?, ?,
                        NULL, NULL, NULL, NULL, NULL
                    )
                    """,
                    (
                        key,
                        pins.assetDigest,
                        pins.sourceDigest,
                        pins.queryDigest,
                        pins.universeDigest,
                        pins.contractDigest,
                        pins.schemaDigest,
                        ownerDigest,
                        leaseUntil,
                        now,
                        now,
                    ),
                )
                return BuildClaim(key, pins, ownerDigest, 1, True, False)

            row = self._assertGenerationRow(row, key=key, pins=pins)
            status = row["status"]
            epoch = requireNonNegativeInt(row["build_epoch"])
            if status == "READY":
                return BuildClaim(key, pins, ownerDigest, epoch, False, True)
            if status == "GC_PENDING":
                return BuildClaim(key, pins, ownerDigest, epoch, False, False)
            if status != "BUILDING":
                raise MaterializationError("MATERIALIZATION_CORRUPT")
            currentOwner = requireDigest(row["build_owner_digest"])
            currentLease = requireNonNegativeNumber(row["lease_until"])
            if currentLease > now and not hmac.compare_digest(
                currentOwner,
                ownerDigest,
            ):
                return BuildClaim(key, pins, ownerDigest, epoch, False, False)
            if currentLease > now:
                connection.execute(
                    "UPDATE materialization_generations SET lease_until=?, updated_at=? WHERE generation_key=?",
                    (leaseUntil, now, key),
                )
                return BuildClaim(key, pins, ownerDigest, epoch, True, False)

            self._discardBuildingPages(connection, key, now=now)
            nextEpoch = epoch + 1
            connection.execute(
                """
                UPDATE materialization_generations
                SET build_owner_digest=?, build_epoch=?, lease_until=?, updated_at=?,
                    published_at=NULL, terminal_root_digest=NULL,
                    page_count=NULL, row_count=NULL, byte_count=NULL
                WHERE generation_key=? AND status='BUILDING'
                """,
                (ownerDigest, nextEpoch, leaseUntil, now, key),
            )
            return BuildClaim(key, pins, ownerDigest, nextEpoch, True, False)

    def renewBuild(self, claim: BuildClaim) -> None:
        """만료된 epoch를 부활시키지 않고 live build lease를 갱신한다."""

        if not isinstance(claim, BuildClaim) or not claim.acquired:
            raise MaterializationError("MATERIALIZATION_INVALID")
        now = self._now()
        with self._connection(immediate=True) as connection:
            self._assertLease(connection, claim, now=now)
            connection.execute(
                "UPDATE materialization_generations SET lease_until=?, updated_at=? WHERE generation_key=?",
                (
                    now + self.policy.builderLeaseSeconds,
                    now,
                    claim.generationKey,
                ),
            )

    def abortBuild(self, claim: BuildClaim) -> None:
        """현재 builder epoch의 실패한 BUILDING과 page reference를 즉시 제거한다."""

        if not isinstance(claim, BuildClaim) or not claim.acquired:
            raise MaterializationError("MATERIALIZATION_INVALID")
        now = self._now()
        with self._connection(immediate=True) as connection:
            row = connection.execute(
                "SELECT * FROM materialization_generations WHERE generation_key=?",
                (claim.generationKey,),
            ).fetchone()
            row = self._assertGenerationRow(
                row,
                key=claim.generationKey,
                pins=claim.pins,
            )
            if (
                row["status"] != "BUILDING"
                or not hmac.compare_digest(
                    requireDigest(row["build_owner_digest"]),
                    claim.ownerDigest,
                )
                or requireNonNegativeInt(row["build_epoch"]) != claim.epoch
            ):
                raise MaterializationError("MATERIALIZATION_LEASE_LOST")
            self._discardBuildingPages(
                connection,
                claim.generationKey,
                now=now,
            )
            cursor = connection.execute(
                """
                DELETE FROM materialization_generations
                WHERE generation_key=? AND status='BUILDING'
                  AND build_owner_digest=? AND build_epoch=?
                """,
                (
                    claim.generationKey,
                    claim.ownerDigest,
                    claim.epoch,
                ),
            )
            if cursor.rowcount != 1:
                raise MaterializationError("MATERIALIZATION_LEASE_LOST")

    def _prepareArtifact(self, payload: bytes) -> str:
        if not isinstance(payload, bytes):
            raise MaterializationError("MATERIALIZATION_INVALID")
        digest = hashlib.sha256(payload).hexdigest()
        now = self._now()
        with self._connection(immediate=True) as connection:
            row = connection.execute(
                "SELECT byte_count, status, reference_count FROM materialization_artifacts WHERE digest=?",
                (digest,),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO materialization_artifacts "
                    "(digest, byte_count, status, reference_count, staged_at) "
                    "VALUES (?, ?, 'STAGED', 0, ?)",
                    (digest, len(payload), now),
                )
            else:
                if requireNonNegativeInt(row["byte_count"]) != len(payload):
                    raise MaterializationError("MATERIALIZATION_CORRUPT")
                references = requireNonNegativeInt(row["reference_count"])
                status = row["status"]
                if status not in {"STAGED", "REFERENCED", "GC_PENDING"}:
                    raise MaterializationError("MATERIALIZATION_CORRUPT")
                if status == "GC_PENDING":
                    if references != 0:
                        raise MaterializationError("MATERIALIZATION_CORRUPT")
                    connection.execute(
                        "UPDATE materialization_artifacts SET status='STAGED', staged_at=? WHERE digest=?",
                        (now, digest),
                    )
                elif status == "STAGED":
                    connection.execute(
                        "UPDATE materialization_artifacts SET staged_at=? WHERE digest=?",
                        (now, digest),
                    )

        # Keep the second write lock through CAS publication. Maintenance cannot
        # remove the STAGED registration between validation and hard-link publish.
        with self._connection(immediate=True) as connection:
            registered = connection.execute(
                "SELECT byte_count, status FROM materialization_artifacts WHERE digest=?",
                (digest,),
            ).fetchone()
            if (
                registered is None
                or requireNonNegativeInt(registered["byte_count"]) != len(payload)
                or registered["status"] not in {"STAGED", "REFERENCED"}
            ):
                raise MaterializationError("MATERIALIZATION_CORRUPT")
            try:
                self._assertPrivateStorage()
                actualDigest = self.cas.putBytes(payload)
            except ContinuationError as error:
                raiseFromContinuation(error)
            if not hmac.compare_digest(actualDigest, digest):
                raise MaterializationError("MATERIALIZATION_CORRUPT")
        return digest

    def _referenceArtifact(
        self,
        connection: sqlite3.Connection,
        digest: str,
        *,
        byteCount: int,
    ) -> None:
        row = connection.execute(
            "SELECT byte_count, status, reference_count FROM materialization_artifacts WHERE digest=?",
            (digest,),
        ).fetchone()
        if row is None or requireNonNegativeInt(row["byte_count"]) != byteCount:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        status = row["status"]
        references = requireNonNegativeInt(row["reference_count"])
        if status not in {"STAGED", "REFERENCED"}:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        try:
            payload = self.cas.readBytes(digest, maxBytes=byteCount)
        except ContinuationError as error:
            raiseFromContinuation(error)
        if len(payload) != byteCount:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        connection.execute(
            "UPDATE materialization_artifacts SET status='REFERENCED', reference_count=? WHERE digest=?",
            (references + 1, digest),
        )

    def _acquireReader(
        self,
        pins: GenerationPins,
        *,
        readerDigest: str,
    ) -> tuple[sqlite3.Row, tuple[PageRecord, ...]] | None:
        key = generationKey(pins)
        now = self._now()
        with self._connection(immediate=True) as connection:
            row = connection.execute(
                "SELECT * FROM materialization_generations WHERE generation_key=?",
                (key,),
            ).fetchone()
            if row is None or row["status"] != "READY":
                return None
            row = self._assertGenerationRow(row, key=key, pins=pins)
            pageRows = connection.execute(
                "SELECT * FROM materialization_pages WHERE generation_key=? ORDER BY ordinal",
                (key,),
            ).fetchall()
            pages = tuple(self._pageRecord(pageRow) for pageRow in pageRows)
            connection.execute(
                "INSERT INTO materialization_readers (generation_key, reader_digest, expires_at) VALUES (?, ?, ?)",
                (
                    key,
                    readerDigest,
                    now + self.policy.readerLeaseSeconds,
                ),
            )
            return row, pages

    def _acquireReaderPage(
        self,
        pins: GenerationPins,
        *,
        readerDigest: str,
        ordinal: int | None,
    ) -> tuple[sqlite3.Row, PageRecord | None] | None:
        """READY metadata와 선택 page 하나만 읽고 reader lease를 획득한다."""

        if ordinal is not None and (type(ordinal) is not int or ordinal < 0):
            raise MaterializationError("MATERIALIZATION_INVALID")
        key = generationKey(pins)
        now = self._now()
        with self._connection(immediate=True) as connection:
            row = connection.execute(
                "SELECT * FROM materialization_generations WHERE generation_key=?",
                (key,),
            ).fetchone()
            if row is None or row["status"] != "READY":
                return None
            row = self._assertGenerationRow(row, key=key, pins=pins)
            page = None
            if ordinal is not None:
                pageRow = connection.execute(
                    """
                    SELECT *
                    FROM materialization_pages
                    WHERE generation_key=? AND ordinal=?
                    """,
                    (key, ordinal),
                ).fetchone()
                if pageRow is None:
                    raise MaterializationError("MATERIALIZATION_CORRUPT")
                page = self._pageRecord(pageRow)
            connection.execute(
                "INSERT INTO materialization_readers (generation_key, reader_digest, expires_at) VALUES (?, ?, ?)",
                (
                    key,
                    readerDigest,
                    now + self.policy.readerLeaseSeconds,
                ),
            )
            return row, page

    def _renewReader(self, key: str, readerDigest: str) -> None:
        now = self._now()
        with self._connection(immediate=True) as connection:
            cursor = connection.execute(
                """
                UPDATE materialization_readers
                SET expires_at=?
                WHERE generation_key=? AND reader_digest=? AND expires_at>?
                  AND EXISTS (
                      SELECT 1 FROM materialization_generations
                      WHERE generation_key=? AND status='READY'
                  )
                """,
                (
                    now + self.policy.readerLeaseSeconds,
                    key,
                    readerDigest,
                    now,
                    key,
                ),
            )
            if cursor.rowcount != 1:
                raise MaterializationError("MATERIALIZATION_NOT_READY")

    def _releaseReader(self, readerDigest: str) -> None:
        with self._connection(immediate=True) as connection:
            connection.execute(
                "DELETE FROM materialization_readers WHERE reader_digest=?",
                (readerDigest,),
            )

    def _completeReader(self, key: str, readerDigest: str) -> None:
        """마지막 lease 검증과 reader 삭제를 한 transaction으로 완료한다."""

        now = self._now()
        with self._connection(immediate=True) as connection:
            row = connection.execute(
                """
                SELECT reader.expires_at
                FROM materialization_readers AS reader
                JOIN materialization_generations AS generation
                  ON generation.generation_key=reader.generation_key
                WHERE reader.generation_key=?
                  AND reader.reader_digest=?
                  AND generation.status='READY'
                """,
                (key, readerDigest),
            ).fetchone()
            if row is None or requireNonNegativeNumber(row["expires_at"]) <= now:
                connection.execute(
                    "DELETE FROM materialization_readers WHERE reader_digest=?",
                    (readerDigest,),
                )
                raise MaterializationError("MATERIALIZATION_NOT_READY")
            cursor = connection.execute(
                "DELETE FROM materialization_readers WHERE generation_key=? AND reader_digest=?",
                (key, readerDigest),
            )
            if cursor.rowcount != 1:
                raise MaterializationError("MATERIALIZATION_CORRUPT")
