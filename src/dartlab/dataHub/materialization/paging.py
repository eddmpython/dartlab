"""Opaque continuation replay for immutable materialized result pages."""

from __future__ import annotations

import dataclasses
import hmac
import json
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.dataHub.continuation import (
    ArrowPayloadFacts,
    ContinuationError,
    ContinuationPins,
    ContinuationQueryState,
    PageEnvelope,
    bytesDigest,
    canonicalDigest,
    canonicalJsonBytes,
    validateArrowIpcPayload,
)
from dartlab.dataHub.contracts import DataResult
from dartlab.dataHub.paging.composite import (
    decodeMaterializationPage,
    materializationPageSchemaDigest,
)
from dartlab.dataHub.paging.runtime import (
    MAX_PAGE_BYTES,
    MAX_STATE_BYTES,
    continuationStore,
    requireDeadline,
)
from dartlab.dataHub.paging.stateCodec import rejectDuplicateKeys
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

from .contracts import (
    MaterializationError,
    MaterializationReceipt,
    MaterializedGeneration,
    MaterializedGenerationHandle,
)
from .runtime import materializationStore

FORMAT_VERSION = 1
PAGE_KIND = "materialization"


_log = dataHubLogger(__name__)


def jsonLoad(payload: bytes) -> Any:
    """중복 key와 비정규 JSON을 거부하며 replay state를 읽는다.

    중복 key 규칙은 `paging.stateCodec.rejectDuplicateKeys` 가 정본이다. 이 lane 은 실패를
    telemetry 에 남긴 뒤 훼손으로 끝내는 점이 달라 바깥 try 는 여기 남긴다.
    """
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=rejectDuplicateKeys)
    except ContinuationError:
        raise
    except Exception:
        recordFailure(_log, "CONTINUATION_CORRUPT")
        raise ContinuationError("CONTINUATION_CORRUPT") from None
    if canonicalJsonBytes(value) != payload:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return value


def queryPayload(receipt: MaterializationReceipt) -> bytes:
    """Digest-only receipt를 continuation query state로 봉인한다."""

    payload = canonicalJsonBytes(
        {
            "version": FORMAT_VERSION,
            "pageKind": PAGE_KIND,
            "receipt": receipt.asTree(),
        }
    )
    if len(payload) > MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    return payload


def decodeReceipt(payload: bytes) -> MaterializationReceipt:
    """Continuation query payload에서 exact receipt를 복원한다."""

    root = jsonLoad(payload)
    if (
        not isinstance(root, dict)
        or set(root) != {"version", "pageKind", "receipt"}
        or root["version"] != FORMAT_VERSION
        or root["pageKind"] != PAGE_KIND
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    try:
        return MaterializationReceipt.fromTree(root["receipt"])
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def cursorPayload(*, ordinal: int, pageCount: int) -> bytes:
    """다음 stored page ordinal을 private cursor로 봉인한다."""

    if type(ordinal) is not int or type(pageCount) is not int or ordinal < 0 or pageCount <= 0 or ordinal >= pageCount:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return canonicalJsonBytes(
        {
            "version": FORMAT_VERSION,
            "pageKind": PAGE_KIND,
            "ordinal": ordinal,
            "pageCount": pageCount,
        }
    )


def decodeCursor(payload: bytes) -> tuple[int, int]:
    """Private cursor에서 bounded ordinal과 page count를 읽는다."""

    root = jsonLoad(payload)
    if (
        not isinstance(root, dict)
        or set(root) != {"version", "pageKind", "ordinal", "pageCount"}
        or root["version"] != FORMAT_VERSION
        or root["pageKind"] != PAGE_KIND
        or type(root["ordinal"]) is not int
        or type(root["pageCount"]) is not int
        or root["ordinal"] < 0
        or root["pageCount"] <= 0
        or root["ordinal"] >= root["pageCount"]
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return root["ordinal"], root["pageCount"]


def isMaterializedPagingState(payload: bytes) -> bool:
    """Cursor가 materialized replay state인지 보수적으로 판정한다."""

    try:
        decodeCursor(payload)
        return True
    except Exception:
        return False


def replayPins(
    receipt: MaterializationReceipt,
    receiptPayload: bytes,
) -> ContinuationPins:
    """Materialized replay continuation의 exact control pins를 만든다."""

    return ContinuationPins(
        sourceDigest=receipt.pins.sourceDigest,
        queryDigest=bytesDigest(receiptPayload),
        contractDigest=canonicalDigest(
            {
                "format": "materialization-replay-v1",
                "generationKey": receipt.generationKey,
                "terminalRootDigest": receipt.terminalRootDigest,
                "contractDigest": receipt.pins.contractDigest,
            }
        ),
        schemaDigest=materializationPageSchemaDigest(),
    )


def validateMaterializedPayload(
    payload: bytes,
    *,
    claimedRowCount: int,
    expectedSchemaDigest: str,
    maxPageBytes: int,
    maxLogicalBytes: int,
) -> ArrowPayloadFacts:
    """Fixed-schema materialized result wrapper를 검증한다."""

    if not hmac.compare_digest(
        expectedSchemaDigest,
        materializationPageSchemaDigest(),
    ):
        raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
    return validateArrowIpcPayload(
        payload,
        claimedRowCount=claimedRowCount,
        expectedSchemaDigest=expectedSchemaDigest,
        maxPageBytes=maxPageBytes,
        maxLogicalBytes=maxLogicalBytes,
    )


def issueReplayToken(
    generation: MaterializedGenerationHandle,
    *,
    nextOrdinal: int,
    deadline: float,
) -> str:
    """다음 immutable page를 가리키는 opaque continuation을 발급한다."""

    receiptPayload = queryPayload(generation.receipt)
    state = ContinuationQueryState(
        receiptPayload,
        cursorPayload(
            ordinal=nextOrdinal,
            pageCount=generation.pageCount,
        ),
    )
    issued = continuationStore(
        deadline=deadline,
        payloadValidator=validateMaterializedPayload,
    ).issue(state, replayPins(generation.receipt, receiptPayload))
    return issued.token


def resultFromHandle(
    generation: MaterializedGenerationHandle,
    *,
    deadline: float,
) -> DataResult:
    """READY handle의 첫 CAS page 하나만 읽어 public result를 만든다."""

    if generation.pageCount <= 0:
        raise ContinuationError("CONTINUATION_CORRUPT")
    current, first = materializationStore().readReceiptPage(generation.receipt, 0)
    if current != generation:
        raise ContinuationError("CONTINUATION_CORRUPT")
    result = decodeMaterializationPage(first.payload)
    token = issueReplayToken(generation, nextOrdinal=1, deadline=deadline) if generation.pageCount > 1 else None
    return dataclasses.replace(
        result,
        continuation=token,
        materializationReceipt=generation.receipt.asTree(),
    )


def resultFromReceipt(
    receipt: MaterializationReceipt,
    *,
    deadline: float,
) -> DataResult:
    """한 reader lease에서 receipt metadata와 첫 page를 함께 읽는다."""

    generation, first = materializationStore().readReceiptPage(receipt, 0)
    result = decodeMaterializationPage(first.payload)
    token = issueReplayToken(generation, nextOrdinal=1, deadline=deadline) if generation.pageCount > 1 else None
    return dataclasses.replace(
        result,
        continuation=token,
        materializationReceipt=generation.receipt.asTree(),
    )


def resultFromGeneration(
    generation: MaterializedGeneration,
    *,
    deadline: float,
) -> DataResult:
    """READY generation의 첫 page와 replay token을 public result로 만든다."""

    if not generation.pages:
        raise ContinuationError("CONTINUATION_CORRUPT")
    first = generation.pages[0]
    result = decodeMaterializationPage(first.payload)
    handle = MaterializedGenerationHandle(
        generationKey=generation.generationKey,
        pins=generation.pins,
        terminalRootDigest=generation.terminalRootDigest,
        pageCount=len(generation.pages),
        rowCount=generation.rowCount,
        byteCount=generation.byteCount,
    )
    token = issueReplayToken(handle, nextOrdinal=1, deadline=deadline) if len(generation.pages) > 1 else None
    return dataclasses.replace(
        result,
        continuation=token,
        materializationReceipt=generation.receipt.asTree(),
    )


def resumeMaterializedPaging(
    token: str,
    *,
    deadline: float,
    startedAt: float | None = None,
) -> DataResult:
    """Opaque token을 다음 immutable result page로 교환한다."""

    del startedAt
    requireDeadline(deadline)
    contextStore = continuationStore(
        deadline=deadline,
        payloadValidator=validateMaterializedPayload,
    )
    context = contextStore.loadContext(token)
    receipt = decodeReceipt(context.state.queryPayload)
    ordinal, pageCount = decodeCursor(context.state.cursorPayload)
    expectedPins = replayPins(receipt, context.state.queryPayload)
    if context.pins != expectedPins:
        raise ContinuationError("CONTINUATION_CORRUPT")
    store = materializationStore()
    materializationFailure: MaterializationError | None = None

    def materialize(
        state: ContinuationQueryState,
    ) -> PageEnvelope:
        """Receipt가 고정한 generation에서 요청 page를 읽는다."""
        nonlocal materializationFailure
        currentReceipt = decodeReceipt(state.queryPayload)
        currentOrdinal, currentCount = decodeCursor(state.cursorPayload)
        if currentReceipt != receipt or currentCount != pageCount or currentOrdinal != ordinal:
            raise ContinuationError("CONTINUATION_CORRUPT")
        try:
            generation, page = store.readReceiptPage(
                currentReceipt,
                currentOrdinal,
            )
        except MaterializationError as error:
            materializationFailure = error
            raise
        if generation.pageCount != currentCount:
            raise ContinuationError("CONTINUATION_CORRUPT")
        nextOrdinal = currentOrdinal + 1
        nextState = (
            ContinuationQueryState(
                state.queryPayload,
                cursorPayload(
                    ordinal=nextOrdinal,
                    pageCount=currentCount,
                ),
            )
            if nextOrdinal < currentCount
            else None
        )
        return PageEnvelope(
            payload=page.payload,
            rowCount=page.rowCount,
            nextState=nextState,
        )

    try:
        page = continuationStore(
            deadline=deadline,
            payloadValidator=validateMaterializedPayload,
            runMaintenance=False,
        ).redeem(
            token,
            expectedPins,
            materialize=materialize,
            waitSeconds=requireDeadline(deadline),
        )
    except ContinuationError:
        if materializationFailure is not None:
            raise materializationFailure from None
        raise
    result = decodeMaterializationPage(page.payload)
    return dataclasses.replace(
        result,
        continuation=page.nextToken,
        materializationReceipt=receipt.asTree(),
    )


__all__ = [
    "isMaterializedPagingState",
    "resultFromHandle",
    "resultFromReceipt",
    "resultFromGeneration",
    "resumeMaterializedPaging",
]
