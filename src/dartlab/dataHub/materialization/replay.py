"""READY generation verification, offline replay, and cold build facade."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections.abc import Callable, Iterable, Mapping, Sequence
from functools import lru_cache
from typing import Any

from dartlab.dataHub.continuation import (
    ContinuationError,
    canonicalJsonBytes,
    validateArrowIpcPayload,
)
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

from .contracts import (
    FORMAT_VERSION,
    BuildClaim,
    BuildHandleOutcome,
    BuildOutcome,
    GenerationPins,
    MaterializationError,
    MaterializationReceipt,
    MaterializedGeneration,
    MaterializedGenerationHandle,
    MaterializedPage,
    PageDraft,
    PageRecord,
    generationKey,
    raiseFromContinuation,
    requireDigest,
    requireNonNegativeInt,
)
from .publication import MaterializationPublication

_log = dataHubLogger(__name__)


def decodeCanonicalJson(payload: bytes) -> Any:
    """중복 key와 비정규 JSON을 거부하며 CAS manifest를 decode한다."""

    def pairsHook(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
        """중복 JSON key를 거부하며 CAS mapping을 조립한다."""
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise MaterializationError("MATERIALIZATION_CORRUPT")
            result[key] = value
        return result

    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=pairsHook)
        if canonicalJsonBytes(value) != payload:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return value
    except MaterializationError:
        raise
    except Exception:
        recordFailure(_log, "MATERIALIZATION_CORRUPT")
        raise MaterializationError("MATERIALIZATION_CORRUPT") from None


def _pageRecordFromTree(value: Any) -> PageRecord:
    """Terminal manifest의 page mapping을 검증된 record로 복원한다."""

    expected = {
        "ordinal",
        "payloadDigest",
        "rowCount",
        "byteCount",
        "logicalByteCount",
        "schemaDigest",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise MaterializationError("MATERIALIZATION_CORRUPT")
    return PageRecord(
        ordinal=requireNonNegativeInt(value["ordinal"]),
        payloadDigest=requireDigest(value["payloadDigest"]),
        rowCount=requireNonNegativeInt(value["rowCount"]),
        byteCount=requireNonNegativeInt(value["byteCount"]),
        logicalByteCount=requireNonNegativeInt(value["logicalByteCount"]),
        schemaDigest=requireDigest(value["schemaDigest"]),
    )


class MaterializationReplay(MaterializationPublication):
    """READY generation을 owner와 source 없이 검증해 재생하는 계층."""

    @lru_cache(maxsize=16)
    def _cachedManifest(
        self,
        terminalRoot: str,
    ) -> tuple[str, GenerationPins, int, int, tuple[PageRecord, ...]]:
        """Immutable terminal root별 검증 manifest를 process 안에서 재사용한다."""

        try:
            manifestPayload = self.cas.readBytes(
                terminalRoot,
                maxBytes=self.policy.maxManifestBytes,
                budgetCode="CONTINUATION_STATE_BUDGET",
            )
        except ContinuationError as error:
            raiseFromContinuation(error)
        manifest = decodeCanonicalJson(manifestPayload)
        expected = {
            "formatVersion",
            "generationKey",
            "pins",
            "terminal",
            "pageCount",
            "rowCount",
            "byteCount",
            "pages",
        }
        if not isinstance(manifest, Mapping) or set(manifest) != expected:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        try:
            pins = GenerationPins.fromTree(manifest["pins"])
        except (TypeError, ValueError):
            raise MaterializationError("MATERIALIZATION_CORRUPT") from None
        rawPages = manifest["pages"]
        if (
            manifest["formatVersion"] != FORMAT_VERSION
            or manifest["terminal"] is not True
            or not isinstance(rawPages, list)
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        key = requireDigest(manifest["generationKey"])
        pageCount = requireNonNegativeInt(manifest["pageCount"])
        rowCount = requireNonNegativeInt(manifest["rowCount"])
        byteCount = requireNonNegativeInt(manifest["byteCount"])
        pages = tuple(_pageRecordFromTree(value) for value in rawPages)
        if (
            pageCount != len(pages)
            or pageCount == 0
            or pageCount > self.policy.maxPagesPerGeneration
            or tuple(page.ordinal for page in pages) != tuple(range(pageCount))
            or sum(page.rowCount for page in pages) != rowCount
            or sum(page.byteCount for page in pages) != byteCount
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return key, pins, rowCount, byteCount, pages

    def _consumeOwnerProducer(
        self,
        claim: BuildClaim,
        ownerProducer: Callable[[], Iterable[PageDraft]],
    ) -> None:
        """Owner page chain을 게시하고 실패 시 BUILDING을 즉시 abort한다."""

        produced = 0
        iterator: Any | None = None
        try:
            iterator = iter(ownerProducer())
            while True:
                self.renewBuild(claim)
                try:
                    draft = next(iterator)
                except StopIteration:
                    break
                produced += 1
                if produced > self.policy.maxPagesPerGeneration:
                    raise MaterializationError("MATERIALIZATION_BUDGET")
                self.appendPage(
                    claim,
                    ordinal=produced - 1,
                    draft=draft,
                )
            if produced == 0:
                raise MaterializationError("MATERIALIZATION_INVALID")
            self.publishReady(claim)
        except BaseException:
            try:
                self.abortBuild(claim)
            except BaseException:
                pass
            if iterator is not None:
                close = getattr(iterator, "close", None)
                if callable(close):
                    try:
                        close()
                    except BaseException:
                        pass
            raise

    def _validateReadyMetadata(
        self,
        row: Any,
        pages: Sequence[PageRecord],
    ) -> tuple[str, int, int]:
        terminalRoot = requireDigest(row["terminal_root_digest"])
        pageCount = requireNonNegativeInt(row["page_count"])
        rowCount = requireNonNegativeInt(row["row_count"])
        byteCount = requireNonNegativeInt(row["byte_count"])
        if (
            pageCount != len(pages)
            or pageCount == 0
            or pageCount > self.policy.maxPagesPerGeneration
            or tuple(page.ordinal for page in pages) != tuple(range(pageCount))
            or sum(page.rowCount for page in pages) != rowCount
            or sum(page.byteCount for page in pages) != byteCount
            or rowCount > self.policy.maxRowsPerGeneration
            or byteCount > self.policy.maxBytesPerGeneration
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return terminalRoot, rowCount, byteCount

    def _validateReadyManifestSummary(
        self,
        row: Any,
        *,
        key: str,
        pins: GenerationPins,
    ) -> tuple[str, int, int, tuple[PageRecord, ...]]:
        """READY row를 cached terminal manifest 전체와 결박한다."""

        terminalRoot = requireDigest(row["terminal_root_digest"])
        pageCount = requireNonNegativeInt(row["page_count"])
        rowCount = requireNonNegativeInt(row["row_count"])
        byteCount = requireNonNegativeInt(row["byte_count"])
        if (
            pageCount == 0
            or pageCount > self.policy.maxPagesPerGeneration
            or rowCount > self.policy.maxRowsPerGeneration
            or byteCount > self.policy.maxBytesPerGeneration
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        manifestKey, manifestPins, manifestRows, manifestBytes, manifestPages = self._cachedManifest(terminalRoot)
        if (
            not hmac.compare_digest(manifestKey, key)
            or manifestPins != pins
            or len(manifestPages) != pageCount
            or manifestRows != rowCount
            or manifestBytes != byteCount
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return terminalRoot, rowCount, byteCount, manifestPages

    def _validateReadyManifest(
        self,
        row: Any,
        pages: Sequence[PageRecord],
        *,
        key: str,
        pins: GenerationPins,
        readerDigest: str,
    ) -> tuple[str, int, int]:
        """Reader lease 안에서 READY metadata와 terminal manifest를 결박한다."""

        terminalRoot, rowCount, byteCount = self._validateReadyMetadata(
            row,
            pages,
        )
        manifestKey, manifestPins, manifestRows, manifestBytes, manifestPages = self._cachedManifest(terminalRoot)
        if (
            not hmac.compare_digest(manifestKey, key)
            or manifestPins != pins
            or manifestRows != rowCount
            or manifestBytes != byteCount
            or manifestPages != tuple(pages)
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return terminalRoot, rowCount, byteCount

    def _readValidatedPage(
        self,
        page: PageRecord,
        *,
        pins: GenerationPins,
        key: str,
        readerDigest: str,
        renewLease: bool = True,
    ) -> MaterializedPage:
        """Reader lease 안에서 CAS page 한 개만 읽고 검증한다."""

        if renewLease:
            self._renewReader(key, readerDigest)
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
            or not hmac.compare_digest(facts.schemaDigest, page.schemaDigest)
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return MaterializedPage(
            ordinal=page.ordinal,
            payloadDigest=page.payloadDigest,
            payload=payload,
            rowCount=page.rowCount,
            byteCount=page.byteCount,
            logicalByteCount=page.logicalByteCount,
            schemaDigest=page.schemaDigest,
        )

    def readReadyHandle(
        self,
        pins: GenerationPins,
    ) -> MaterializedGenerationHandle | None:
        """Payload를 읽지 않고 manifest 검증을 마친 READY handle을 반환한다."""

        readerDigest = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        acquired = self._acquireReaderPage(
            pins,
            readerDigest=readerDigest,
            ordinal=None,
        )
        if acquired is None:
            return None
        row, page = acquired
        if page is not None:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        key = generationKey(pins)
        completed = False
        try:
            terminalRoot, rowCount, byteCount, pages = self._validateReadyManifestSummary(
                row,
                key=key,
                pins=pins,
            )
            result = MaterializedGenerationHandle(
                generationKey=key,
                pins=pins,
                terminalRootDigest=terminalRoot,
                pageCount=len(pages),
                rowCount=rowCount,
                byteCount=byteCount,
            )
            self._completeReader(key, readerDigest)
            completed = True
            return result
        finally:
            if not completed:
                self._releaseReader(readerDigest)

    def readReceiptHandle(
        self,
        receipt: MaterializationReceipt,
    ) -> MaterializedGenerationHandle:
        """Receipt만으로 payload eager load 없는 exact READY handle을 읽는다."""

        if not isinstance(receipt, MaterializationReceipt):
            raise MaterializationError("MATERIALIZATION_INVALID")
        generation = self.readReadyHandle(receipt.pins)
        if generation is None:
            raise MaterializationError("MATERIALIZATION_NOT_READY")
        if not hmac.compare_digest(generation.generationKey, receipt.generationKey) or not hmac.compare_digest(
            generation.terminalRootDigest,
            receipt.terminalRootDigest,
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return generation

    def readReceiptPage(
        self,
        receipt: MaterializationReceipt,
        ordinal: int,
    ) -> tuple[MaterializedGenerationHandle, MaterializedPage]:
        """한 reader lease에서 READY handle과 요청 ordinal page를 함께 읽는다."""

        if not isinstance(receipt, MaterializationReceipt) or type(ordinal) is not int or ordinal < 0:
            raise MaterializationError("MATERIALIZATION_INVALID")
        readerDigest = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        acquired = self._acquireReaderPage(
            receipt.pins,
            readerDigest=readerDigest,
            ordinal=ordinal,
        )
        if acquired is None:
            raise MaterializationError("MATERIALIZATION_NOT_READY")
        row, selectedPage = acquired
        if selectedPage is None:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        key = generationKey(receipt.pins)
        completed = False
        try:
            terminalRoot, rowCount, byteCount, pages = self._validateReadyManifestSummary(
                row,
                key=key,
                pins=receipt.pins,
            )
            if (
                not hmac.compare_digest(key, receipt.generationKey)
                or not hmac.compare_digest(
                    terminalRoot,
                    receipt.terminalRootDigest,
                )
                or ordinal >= len(pages)
                or selectedPage != pages[ordinal]
            ):
                raise MaterializationError("MATERIALIZATION_CORRUPT")
            result = self._readValidatedPage(
                selectedPage,
                pins=receipt.pins,
                key=key,
                readerDigest=readerDigest,
                renewLease=False,
            )
            output = (
                MaterializedGenerationHandle(
                    generationKey=key,
                    pins=receipt.pins,
                    terminalRootDigest=terminalRoot,
                    pageCount=len(pages),
                    rowCount=rowCount,
                    byteCount=byteCount,
                ),
                result,
            )
            self._completeReader(key, readerDigest)
            completed = True
            return output
        finally:
            if not completed:
                self._releaseReader(readerDigest)

    def readLatestHandle(
        self,
        queryDigest: str,
    ) -> MaterializedGenerationHandle | None:
        """Canonical query의 최신 READY generation metadata를 읽는다."""

        requireDigest(queryDigest)
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM materialization_generations "
                "WHERE query_digest=? AND status='READY' "
                "ORDER BY published_at DESC, generation_key DESC LIMIT 32",
                (queryDigest,),
            ).fetchall()
        for row in rows:
            generation = self.readReadyHandle(self._pinsFromRow(row))
            if generation is not None:
                return generation
        return None

    def readReady(
        self,
        pins: GenerationPins,
    ) -> MaterializedGeneration | None:
        """완전한 READY generation을 source owner 호출 없이 읽는다.

        Capabilities:
            reader heartbeat, terminal manifest, ordered CAS page, Arrow schema를
            모두 재검증한다.

        Args:
            pins: 조회할 exact generation identity.

        Returns:
            READY generation 또는 BUILDING과 absent일 때 ``None``.

        Example:
            ``ready = store.readReady(pins)``.

        Guide:
            latest source를 해소할 필요가 없는 exact receipt replay에 사용한다.

        SeeAlso:
            ``readReceipt``, ``materializeOrReplay``.

        Requires:
            pins는 첫 query receipt 또는 현재 metadata에서 계산돼야 한다.

        AIContext:
            이 경로는 owner와 source를 호출하지 않는다.
        """

        readerDigest = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        acquired = self._acquireReader(pins, readerDigest=readerDigest)
        if acquired is None:
            return None
        row, pages = acquired
        key = generationKey(pins)
        completed = False
        try:
            terminalRoot, rowCount, byteCount = self._validateReadyManifest(
                row,
                pages,
                key=key,
                pins=pins,
                readerDigest=readerDigest,
            )
            materializedPages = []
            for page in pages:
                materializedPages.append(
                    self._readValidatedPage(
                        page,
                        pins=pins,
                        key=key,
                        readerDigest=readerDigest,
                    )
                )
            result = MaterializedGeneration(
                generationKey=key,
                pins=pins,
                terminalRootDigest=terminalRoot,
                pages=tuple(materializedPages),
                rowCount=rowCount,
                byteCount=byteCount,
            )
            self._completeReader(key, readerDigest)
            completed = True
            return result
        finally:
            if not completed:
                self._releaseReader(readerDigest)

    def readReceipt(
        self,
        receipt: MaterializationReceipt,
    ) -> MaterializedGeneration:
        """구조화된 receipt만으로 exact READY generation을 offline 재생한다."""

        if not isinstance(receipt, MaterializationReceipt):
            raise MaterializationError("MATERIALIZATION_INVALID")
        generation = self.readReady(receipt.pins)
        if generation is None:
            raise MaterializationError("MATERIALIZATION_NOT_READY")
        if not hmac.compare_digest(generation.generationKey, receipt.generationKey) or not hmac.compare_digest(
            generation.terminalRootDigest,
            receipt.terminalRootDigest,
        ):
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return generation

    def readLatest(self, queryDigest: str) -> MaterializedGeneration | None:
        """같은 canonical query의 가장 최근 READY generation을 재사용한다."""

        requireDigest(queryDigest)
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM materialization_generations "
                "WHERE query_digest=? AND status='READY' "
                "ORDER BY published_at DESC, generation_key DESC LIMIT 32",
                (queryDigest,),
            ).fetchall()
        for row in rows:
            generation = self.readReady(self._pinsFromRow(row))
            if generation is not None:
                return generation
        return None

    def materializeOrReplay(
        self,
        pins: GenerationPins,
        *,
        builderId: str,
        ownerProducer: Callable[[], Iterable[PageDraft]],
    ) -> BuildOutcome:
        """READY를 재생하거나 기존 outer page producer를 정확히 한 번 소비한다.

        Capabilities:
            READY fast path, single builder, ordered page publication을 제공한다.

        Args:
            pins: exact generation identity.
            builderId: ledger에는 digest로만 저장되는 process-local identity.
            ownerProducer: 기존 composite chain을 ordinal 순으로 내는 callable.

        Returns:
            generation과 warm replay 여부.

        Example:
            ``outcome = store.materializeOrReplay(pins, builderId=runId, ownerProducer=pages)``.

        Guide:
            producer 안에서 asset owner를 직접 반복하지 않는다.

        SeeAlso:
            ``readReady``.

        Requires:
            producer는 동일 schema의 terminal outer page chain을 반환해야 한다.

        AIContext:
            READY hit에서는 producer를 호출하기 전에 반환한다.
        """

        if not callable(ownerProducer):
            raise MaterializationError("MATERIALIZATION_INVALID")
        ready = self.readReady(pins)
        if ready is not None:
            return BuildOutcome(ready, True)
        claim = self.claimBuild(pins, builderId=builderId)
        if claim.ready:
            racedReady = self.readReady(pins)
            if racedReady is None:
                raise MaterializationError("MATERIALIZATION_CORRUPT")
            return BuildOutcome(racedReady, True)
        if not claim.acquired:
            raise MaterializationError("MATERIALIZATION_BUSY")
        self._consumeOwnerProducer(claim, ownerProducer)
        built = self.readReady(pins)
        if built is None:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return BuildOutcome(built, False)

    def materializeOrReplayHandle(
        self,
        pins: GenerationPins,
        *,
        builderId: str,
        ownerProducer: Callable[[], Iterable[PageDraft]],
    ) -> BuildHandleOutcome:
        """READY handle을 재생하거나 build한 뒤 payload 없는 handle을 반환한다."""

        if not callable(ownerProducer):
            raise MaterializationError("MATERIALIZATION_INVALID")
        ready = self.readReadyHandle(pins)
        if ready is not None:
            return BuildHandleOutcome(ready, True)
        claim = self.claimBuild(pins, builderId=builderId)
        if claim.ready:
            racedReady = self.readReadyHandle(pins)
            if racedReady is None:
                raise MaterializationError("MATERIALIZATION_CORRUPT")
            return BuildHandleOutcome(racedReady, True)
        if not claim.acquired:
            raise MaterializationError("MATERIALIZATION_BUSY")
        self._consumeOwnerProducer(claim, ownerProducer)
        built = self.readReadyHandle(pins)
        if built is None:
            raise MaterializationError("MATERIALIZATION_CORRUPT")
        return BuildHandleOutcome(built, False)
