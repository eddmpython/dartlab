"""Ordered Arrow page validation and atomic READY publication."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Sequence

from dartlab.data.continuation import (
    ContinuationError,
    canonicalJsonBytes,
    validateArrowIpcPayload,
)

from .contracts import (
    FORMAT_VERSION,
    BuildClaim,
    GenerationPins,
    MaterializationError,
    PageDraft,
    PageRecord,
    raiseFromContinuation,
    requireNonNegativeInt,
)
from .ledger import MaterializationLedger


class MaterializationPublication(MaterializationLedger):
    """BUILDING page를 검증하고 terminal root를 게시하는 계층."""

    def appendPage(
        self,
        claim: BuildClaim,
        *,
        ordinal: int,
        draft: PageDraft,
    ) -> PageRecord:
        """한 ordered Arrow page를 BUILDING generation에 추가한다.

        Capabilities:
            lease, row와 byte budget, Arrow schema, CAS digest를 검증한다.

        Args:
            claim: 현재 builder epoch의 live claim.
            ordinal: 0부터 연속하는 page 순번.
            draft: owner가 만든 Arrow IPC bytes와 row count.

        Returns:
            검증된 digest-only page facts.

        Example:
            ``store.appendPage(claim, ordinal=0, draft=page)``.

        Guide:
            existing composite outer page chain의 순서를 그대로 전달한다.

        SeeAlso:
            ``publishReady``.

        Requires:
            모든 page는 generation pins의 동일 schema를 사용해야 한다.

        AIContext:
            BUILDING page는 reader에게 보이지 않는다.
        """

        if (
            not isinstance(claim, BuildClaim)
            or not claim.acquired
            or type(ordinal) is not int
            or ordinal < 0
            or ordinal >= self.policy.maxPagesPerGeneration
            or not isinstance(draft, PageDraft)
        ):
            raise MaterializationError("MATERIALIZATION_INVALID")
        if draft.rowCount > self.policy.maxPageRows:
            raise MaterializationError("MATERIALIZATION_BUDGET")
        self.renewBuild(claim)
        try:
            facts = validateArrowIpcPayload(
                draft.payload,
                claimedRowCount=draft.rowCount,
                expectedSchemaDigest=claim.pins.schemaDigest,
                maxPageBytes=self.policy.maxPageBytes,
                maxLogicalBytes=self.policy.maxPageLogicalBytes,
            )
        except ContinuationError as error:
            raiseFromContinuation(error)
        digest = self._prepareArtifact(draft.payload)
        record = PageRecord(
            ordinal=ordinal,
            payloadDigest=digest,
            rowCount=facts.rowCount,
            byteCount=facts.byteCount,
            logicalByteCount=facts.logicalByteCount,
            schemaDigest=facts.schemaDigest,
        )
        now = self._now()
        with self._connection(immediate=True) as connection:
            self._assertLease(connection, claim, now=now)
            existing = connection.execute(
                "SELECT * FROM materialization_pages WHERE generation_key=? AND ordinal=?",
                (claim.generationKey, ordinal),
            ).fetchone()
            if existing is not None:
                if self._pageRecord(existing) != record:
                    raise MaterializationError("MATERIALIZATION_CORRUPT")
                return record
            countRow = connection.execute(
                "SELECT COUNT(*), COALESCE(SUM(row_count), 0), "
                "COALESCE(SUM(byte_count), 0) "
                "FROM materialization_pages WHERE generation_key=?",
                (claim.generationKey,),
            ).fetchone()
            if countRow is None:
                raise MaterializationError("MATERIALIZATION_CORRUPT")
            pageCount = requireNonNegativeInt(countRow[0])
            currentRows = requireNonNegativeInt(countRow[1])
            currentBytes = requireNonNegativeInt(countRow[2])
            if pageCount != ordinal:
                raise MaterializationError("MATERIALIZATION_INVALID")
            if currentRows + record.rowCount > self.policy.maxRowsPerGeneration:
                raise MaterializationError("MATERIALIZATION_BUDGET")
            if currentBytes + record.byteCount > self.policy.maxBytesPerGeneration:
                raise MaterializationError("MATERIALIZATION_BUDGET")
            self._referenceArtifact(
                connection,
                digest,
                byteCount=record.byteCount,
            )
            connection.execute(
                """
                INSERT INTO materialization_pages (
                    generation_key, ordinal, payload_digest, row_count,
                    byte_count, logical_byte_count, schema_digest
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim.generationKey,
                    record.ordinal,
                    record.payloadDigest,
                    record.rowCount,
                    record.byteCount,
                    record.logicalByteCount,
                    record.schemaDigest,
                ),
            )
            connection.execute(
                "UPDATE materialization_generations SET updated_at=? WHERE generation_key=?",
                (now, claim.generationKey),
            )
        return record

    @staticmethod
    def _manifestTree(
        key: str,
        pins: GenerationPins,
        pages: Sequence[PageRecord],
    ) -> dict[str, object]:
        return {
            "formatVersion": FORMAT_VERSION,
            "generationKey": key,
            "pins": pins.asTree(),
            "terminal": True,
            "pageCount": len(pages),
            "rowCount": sum(page.rowCount for page in pages),
            "byteCount": sum(page.byteCount for page in pages),
            "pages": [page.asTree() for page in pages],
        }

    def _loadBuildPages(
        self,
        claim: BuildClaim,
        *,
        now: float,
    ) -> tuple[PageRecord, ...]:
        with self._connection() as connection:
            self._assertLease(connection, claim, now=now)
            rows = connection.execute(
                "SELECT * FROM materialization_pages WHERE generation_key=? ORDER BY ordinal",
                (claim.generationKey,),
            ).fetchall()
        if not rows or len(rows) > self.policy.maxPagesPerGeneration:
            raise MaterializationError("MATERIALIZATION_INVALID")
        pages = tuple(self._pageRecord(row) for row in rows)
        if tuple(page.ordinal for page in pages) != tuple(range(len(pages))):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return pages

    def _verifyStoredPage(
        self,
        page: PageRecord,
        pins: GenerationPins,
    ) -> None:
        if not hmac.compare_digest(page.schemaDigest, pins.schemaDigest):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        try:
            payload = self.cas.readBytes(
                page.payloadDigest,
                maxBytes=self.policy.maxPageBytes,
                budgetCode="CONTINUATION_BYTE_BUDGET",
            )
            facts = validateArrowIpcPayload(
                payload,
                claimedRowCount=page.rowCount,
                expectedSchemaDigest=pins.schemaDigest,
                maxPageBytes=self.policy.maxPageBytes,
                maxLogicalBytes=self.policy.maxPageLogicalBytes,
            )
        except ContinuationError as error:
            raiseFromContinuation(error)
        if (
            facts.byteCount != page.byteCount
            or facts.logicalByteCount != page.logicalByteCount
            or not hmac.compare_digest(
                hashlib.sha256(payload).hexdigest(),
                page.payloadDigest,
            )
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")

    def _commitReady(
        self,
        claim: BuildClaim,
        pages: Sequence[PageRecord],
        manifestDigest: str,
        manifestByteCount: int,
    ) -> None:
        now = self._now()
        with self._connection(immediate=True) as connection:
            self._assertLease(connection, claim, now=now)
            rows = connection.execute(
                "SELECT * FROM materialization_pages WHERE generation_key=? ORDER BY ordinal",
                (claim.generationKey,),
            ).fetchall()
            if tuple(self._pageRecord(row) for row in rows) != tuple(pages):
                raise MaterializationError("MATERIALIZATION_CORRUPT")
            self._referenceArtifact(
                connection,
                manifestDigest,
                byteCount=manifestByteCount,
            )
            cursor = connection.execute(
                """
                UPDATE materialization_generations
                SET status='READY', build_owner_digest=NULL, lease_until=0,
                    updated_at=?, published_at=?, terminal_root_digest=?,
                    page_count=?, row_count=?, byte_count=?
                WHERE generation_key=? AND status='BUILDING'
                  AND build_owner_digest=? AND build_epoch=?
                """,
                (
                    now,
                    now,
                    manifestDigest,
                    len(pages),
                    sum(page.rowCount for page in pages),
                    sum(page.byteCount for page in pages),
                    claim.generationKey,
                    claim.ownerDigest,
                    claim.epoch,
                ),
            )
            if cursor.rowcount != 1:
                raise MaterializationError("MATERIALIZATION_LEASE_LOST")

    def publishReady(self, claim: BuildClaim) -> str:
        """모든 page를 재검증하고 terminal manifest를 원자적으로 게시한다.

        Capabilities:
            CAS manifest와 SQLite READY publication point를 결박한다.

        Args:
            claim: 현재 live builder epoch.

        Returns:
            terminal root SHA-256 digest.

        Example:
            ``root = store.publishReady(claim)``.

        Guide:
            마지막 outer page가 terminal임을 확인한 뒤에만 호출한다.

        SeeAlso:
            ``MaterializationStore.readReady``.

        Requires:
            generation에는 최소 한 page가 있어야 한다.

        AIContext:
            READY update 전 crash는 reader에게 계속 보이지 않는다.
        """

        if not isinstance(claim, BuildClaim) or not claim.acquired:
            raise MaterializationError("MATERIALIZATION_INVALID")
        self.renewBuild(claim)
        pages = self._loadBuildPages(claim, now=self._now())
        for page in pages:
            self._verifyStoredPage(page, claim.pins)
        manifestPayload = canonicalJsonBytes(self._manifestTree(claim.generationKey, claim.pins, pages))
        if len(manifestPayload) > self.policy.maxManifestBytes:
            raise MaterializationError("MATERIALIZATION_BUDGET")
        manifestDigest = self._prepareArtifact(manifestPayload)
        self._commitReady(
            claim,
            pages,
            manifestDigest,
            len(manifestPayload),
        )
        return manifestDigest
