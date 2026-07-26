"""Restart-safe caller-bounded continuation 회수 계층.

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
    ContinuationMaintenanceBudget,
    PruneReport,
)

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_INITIALIZE_LOCK = threading.Lock()
_PayloadValidator = Callable[..., ArrowPayloadFacts]
_SCHEMA_VERSION = 3
_SWEEP_NAMES = frozenset({"artifacts", "cas", "roots"})


from .storeArtifacts import _ContinuationStoreArtifacts
from .storeBase import _SweepCursor


class _ContinuationStoreGc(_ContinuationStoreArtifacts):
    """Restart-safe caller-bounded continuation 회수 계층."""

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
