"""Restart-safe caller-bounded materialization garbage collection."""

from __future__ import annotations

from dartlab.data.continuation import ContinuationError

from .contracts import (
    MaintenanceBudget,
    MaintenanceReport,
    MaterializationError,
    raiseFromContinuation,
    requireDigest,
    requireNonNegativeInt,
)
from .replay import MaterializationReplay


class MaterializationMaintenance(MaterializationReplay):
    """Reader, generation, reference, CAS 순서로 bounded GC를 수행한다."""

    def maintain(
        self,
        budget: MaintenanceBudget | None = None,
    ) -> MaintenanceReport:
        """한 호출의 모든 작업량을 budget으로 제한해 GC를 진행한다.

        Capabilities:
            expired reader, stale BUILDING, retained READY, page reference,
            STAGED와 unreferenced CAS를 restart-safe하게 회수한다.

        Args:
            budget: 단계별 최대 처리 수.

        Returns:
            실제 처리된 단계별 count와 해제 byte 수.

        Example:
            ``report = store.maintain(MaintenanceBudget(maxArtifacts=10))``.

        Guide:
            작은 budget으로 반복 호출해 큰 generation을 점진적으로 회수한다.

        SeeAlso:
            ``MaterializationPolicy.readyRetentionSeconds``.

        Requires:
            live reader가 있는 READY generation은 전환하지 않는다.

        AIContext:
            한 요청이 무제한 GC 작업을 떠안지 않는다.
        """

        bounds = budget or MaintenanceBudget()
        now = self._now()
        readersDeleted = 0
        generationsMarked = 0
        pagesReleased = 0
        generationsDeleted = 0
        artifactsDeleted = 0
        bytesFreed = 0
        with self._connection(immediate=True) as connection:
            expiredReaders = connection.execute(
                "SELECT reader_digest FROM materialization_readers "
                "WHERE expires_at<=? ORDER BY expires_at, reader_digest LIMIT ?",
                (now, bounds.maxReaderLeases),
            ).fetchall()
            for row in expiredReaders:
                cursor = connection.execute(
                    "DELETE FROM materialization_readers WHERE reader_digest=?",
                    (requireDigest(row["reader_digest"]),),
                )
                readersDeleted += cursor.rowcount

            candidates = connection.execute(
                """
                SELECT generation_key
                FROM materialization_generations AS generation
                WHERE (
                    generation.status='BUILDING' AND generation.lease_until<=?
                ) OR (
                    generation.status='READY'
                    AND generation.published_at<=?
                    AND NOT EXISTS (
                        SELECT 1 FROM materialization_readers AS reader
                        WHERE reader.generation_key=generation.generation_key
                          AND reader.expires_at>?
                    )
                )
                ORDER BY generation.updated_at, generation.generation_key
                LIMIT ?
                """,
                (
                    now,
                    now - self.policy.readyRetentionSeconds,
                    now,
                    bounds.maxGenerationTransitions,
                ),
            ).fetchall()
            for row in candidates:
                cursor = connection.execute(
                    "UPDATE materialization_generations "
                    "SET status='GC_PENDING', updated_at=? "
                    "WHERE generation_key=? AND status IN ('BUILDING', 'READY')",
                    (now, requireDigest(row["generation_key"])),
                )
                generationsMarked += cursor.rowcount

            pageRows = connection.execute(
                """
                SELECT page.generation_key, page.ordinal, page.payload_digest
                FROM materialization_pages AS page
                JOIN materialization_generations AS generation
                  ON generation.generation_key=page.generation_key
                WHERE generation.status='GC_PENDING'
                ORDER BY page.generation_key, page.ordinal
                LIMIT ?
                """,
                (bounds.maxPageReferences,),
            ).fetchall()
            for row in pageRows:
                key = requireDigest(row["generation_key"])
                ordinal = requireNonNegativeInt(row["ordinal"])
                digest = requireDigest(row["payload_digest"])
                cursor = connection.execute(
                    "DELETE FROM materialization_pages WHERE generation_key=? AND ordinal=?",
                    (key, ordinal),
                )
                if cursor.rowcount != 1:
                    raise MaterializationError("MATERIALIZATION_CORRUPT")
                self._releaseArtifactReference(connection, digest, now=now)
                pagesReleased += 1

            completed = connection.execute(
                """
                SELECT generation_key, terminal_root_digest
                FROM materialization_generations AS generation
                WHERE generation.status='GC_PENDING'
                  AND NOT EXISTS (
                      SELECT 1 FROM materialization_pages AS page
                      WHERE page.generation_key=generation.generation_key
                  )
                ORDER BY generation.updated_at, generation.generation_key
                LIMIT ?
                """,
                (bounds.maxGenerationTransitions,),
            ).fetchall()
            for row in completed:
                key = requireDigest(row["generation_key"])
                terminalRoot = row["terminal_root_digest"]
                if terminalRoot is not None:
                    self._releaseArtifactReference(
                        connection,
                        requireDigest(terminalRoot),
                        now=now,
                    )
                cursor = connection.execute(
                    "DELETE FROM materialization_generations WHERE generation_key=?",
                    (key,),
                )
                generationsDeleted += cursor.rowcount

            staged = connection.execute(
                "SELECT digest FROM materialization_artifacts "
                "WHERE status='STAGED' AND reference_count=0 AND staged_at<=? "
                "ORDER BY staged_at, digest LIMIT ?",
                (
                    now - self.policy.artifactStageSeconds,
                    bounds.maxArtifacts,
                ),
            ).fetchall()
            for row in staged:
                connection.execute(
                    "UPDATE materialization_artifacts SET status='GC_PENDING' "
                    "WHERE digest=? AND status='STAGED' AND reference_count=0",
                    (requireDigest(row["digest"]),),
                )

            garbage = connection.execute(
                "SELECT digest, byte_count FROM materialization_artifacts "
                "WHERE status='GC_PENDING' AND reference_count=0 "
                "ORDER BY staged_at, digest LIMIT ?",
                (bounds.maxArtifacts,),
            ).fetchall()
            for row in garbage:
                digest = requireDigest(row["digest"])
                expectedBytes = requireNonNegativeInt(row["byte_count"])
                try:
                    deleted, freed = self.cas.deleteBytes(digest)
                except ContinuationError as error:
                    raiseFromContinuation(error)
                if deleted and freed != expectedBytes:
                    raise MaterializationError("MATERIALIZATION_CORRUPT")
                cursor = connection.execute(
                    "DELETE FROM materialization_artifacts "
                    "WHERE digest=? AND status='GC_PENDING' AND reference_count=0",
                    (digest,),
                )
                if cursor.rowcount != 1:
                    raise MaterializationError("MATERIALIZATION_CORRUPT")
                artifactsDeleted += 1
                bytesFreed += freed

        return MaintenanceReport(
            readerLeasesDeleted=readersDeleted,
            generationsMarked=generationsMarked,
            pageReferencesReleased=pagesReleased,
            generationsDeleted=generationsDeleted,
            artifactsDeleted=artifactsDeleted,
            bytesFreed=bytesFreed,
        )
