"""Owner entity 결과를 fixed-schema outer Arrow page로 봉인한다."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any

import polars as pl
import pyarrow as pa

from dartlab.dataHub.continuation import (
    ArrowPayloadFacts,
    ContinuationError,
    arrowSchemaDigest,
    inspectArrowIpcPayload,
)
from dartlab.dataHub.ownerPagingModels import (
    _OUTER_SCHEMA,
    _DecodedPage,
    _OwnerEntry,
)
from dartlab.dataHub.ownerPagingState import _requireDigest, _requireOptionalText, _requireText
from dartlab.dataHub.pagingRuntime import MAX_PAGE_ROWS, continuationStore
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

_log = dataHubLogger(__name__)


def _framePayload(frame: pl.DataFrame) -> bytes:
    table = frame.to_arrow().combine_chunks()
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema, options=pa.ipc.IpcWriteOptions(compression=None)) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()


def _innerTable(payload: bytes, *, logicalLimit: int) -> tuple[ArrowPayloadFacts, pa.Table]:
    facts = inspectArrowIpcPayload(payload, maxLogicalBytes=logicalLimit)
    if facts.containerKind != "stream":
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    try:
        reader = pa.ipc.open_stream(pa.BufferReader(payload))
        schema = reader.schema
        batches = tuple(reader)
        table = pa.Table.from_batches(batches, schema=schema)
    except Exception:
        recordFailure(_log, "CONTINUATION_PAYLOAD_INVALID")
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID") from None
    if not batches or table.num_rows != facts.rowCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    return facts, table


def _entryClaim(entry: _OwnerEntry, *, logicalLimit: int) -> dict[str, Any]:
    if (
        entry.status not in {"ok", "failed"}
        or type(entry.entityOrdinal) is not int
        or entry.entityOrdinal < 0
        or not entry.entityId
        or len(entry.gapCodes) != len(entry.gapMessages)
        or len(entry.gapCodes) > 64
        or any(not code or not message for code, message in zip(entry.gapCodes, entry.gapMessages, strict=True))
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    if entry.status == "failed":
        if any(
            value is not None
            for value in (
                entry.receiptRef,
                entry.contentHash,
                entry.temporalStatus,
                entry.payload,
            )
        ):
            raise ContinuationError("CONTINUATION_CORRUPT")
        return {
            "requestId": entry.requestId,
            "assetId": entry.assetId,
            "assetVersionId": entry.assetVersionId,
            "sourcePin": entry.sourcePin,
            "queryPin": entry.queryPin,
            "entityOrdinal": entry.entityOrdinal,
            "entityId": entry.entityId,
            "sourceEntityId": entry.sourceEntityId,
            "status": entry.status,
            "gapCodes": list(entry.gapCodes),
            "gapMessages": list(entry.gapMessages),
            "receiptRef": None,
            "contentHash": None,
            "temporalStatus": None,
            "innerPayload": None,
            "innerRowCount": 0,
            "innerEncodedByteCount": 0,
            "innerLogicalByteCount": 0,
            "innerSchemaDigest": None,
            "innerPayloadDigest": None,
        }
    if entry.payload is None or entry.receiptRef is None or entry.contentHash is None or entry.temporalStatus is None:
        raise ContinuationError("CONTINUATION_CORRUPT")
    facts, table = _innerTable(entry.payload, logicalLimit=logicalLimit)
    if table.num_rows <= 0:
        raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
    return {
        "requestId": entry.requestId,
        "assetId": entry.assetId,
        "assetVersionId": entry.assetVersionId,
        "sourcePin": entry.sourcePin,
        "queryPin": entry.queryPin,
        "entityOrdinal": entry.entityOrdinal,
        "entityId": entry.entityId,
        "sourceEntityId": entry.sourceEntityId,
        "status": entry.status,
        "gapCodes": list(entry.gapCodes),
        "gapMessages": list(entry.gapMessages),
        "receiptRef": entry.receiptRef,
        "contentHash": entry.contentHash,
        "temporalStatus": entry.temporalStatus,
        "innerPayload": entry.payload,
        "innerRowCount": facts.rowCount,
        "innerEncodedByteCount": facts.byteCount,
        "innerLogicalByteCount": facts.logicalByteCount,
        "innerSchemaDigest": facts.schemaDigest,
        "innerPayloadDigest": hashlib.sha256(entry.payload).hexdigest(),
    }


def _encodePage(
    entries: Sequence[_OwnerEntry],
    *,
    maxPageRows: int,
    maxPageBytes: int,
    maxLogicalBytes: int,
) -> bytes:
    if not entries:
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    claims = [_entryClaim(entry, logicalLimit=maxLogicalBytes) for entry in entries]
    totalRows = sum(claim["innerRowCount"] for claim in claims)
    if totalRows > maxPageRows:
        raise ContinuationError("CONTINUATION_ROW_BUDGET")
    arrays = [pa.array([row[field.name] for row in claims], type=field.type) for field in _OUTER_SCHEMA]
    batch = pa.RecordBatch.from_arrays(arrays, schema=_OUTER_SCHEMA)
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, _OUTER_SCHEMA, options=pa.ipc.IpcWriteOptions(compression=None)) as writer:
        writer.write_batch(batch)
    payload = sink.getvalue().to_pybytes()
    _decodePage(
        payload,
        claimedRowCount=totalRows,
        maxPageRows=maxPageRows,
        maxPageBytes=maxPageBytes,
        maxLogicalBytes=maxLogicalBytes,
    )
    return payload


def _decodePage(
    payload: bytes,
    *,
    claimedRowCount: int,
    maxPageRows: int,
    maxPageBytes: int,
    maxLogicalBytes: int,
) -> _DecodedPage:
    if len(payload) > maxPageBytes:
        raise ContinuationError("CONTINUATION_BYTE_BUDGET")
    outerFacts = inspectArrowIpcPayload(payload, maxLogicalBytes=maxLogicalBytes)
    if outerFacts.containerKind != "stream" or outerFacts.schemaDigest != arrowSchemaDigest(_OUTER_SCHEMA):
        raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
    try:
        reader = pa.ipc.open_stream(pa.BufferReader(payload))
        schema = reader.schema
        batches = tuple(reader)
        table = pa.Table.from_batches(batches, schema=schema)
    except Exception:
        recordFailure(_log, "CONTINUATION_PAYLOAD_INVALID")
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID") from None
    if len(batches) != 1 or not schema.equals(_OUTER_SCHEMA, check_metadata=True):
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    rows = table.to_pylist()
    if not rows or len(rows) != outerFacts.rowCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    entries: list[_OwnerEntry] = []
    tables: list[pa.Table | None] = []
    totalRows = 0
    totalLogicalBytes = outerFacts.logicalByteCount
    identities: set[tuple[str, int]] = set()
    for row in rows:
        requestId = _requireText(row["requestId"])
        entityOrdinal = row["entityOrdinal"]
        status = _requireText(row["status"])
        gapCodes = row["gapCodes"]
        gapMessages = row["gapMessages"]
        if (
            type(entityOrdinal) is not int
            or entityOrdinal < 0
            or (requestId, entityOrdinal) in identities
            or status not in {"ok", "failed"}
            or not isinstance(gapCodes, list)
            or not isinstance(gapMessages, list)
            or len(gapCodes) != len(gapMessages)
            or len(gapCodes) > 64
            or any(type(item) is not str or not item for item in (*gapCodes, *gapMessages))
        ):
            raise ContinuationError("CONTINUATION_CORRUPT")
        identities.add((requestId, entityOrdinal))
        payloadValue = row["innerPayload"]
        if status == "failed":
            if (
                payloadValue is not None
                or row["innerRowCount"] != 0
                or row["innerEncodedByteCount"] != 0
                or row["innerLogicalByteCount"] != 0
                or any(
                    row[name] is not None
                    for name in (
                        "receiptRef",
                        "contentHash",
                        "temporalStatus",
                        "innerSchemaDigest",
                        "innerPayloadDigest",
                    )
                )
            ):
                raise ContinuationError("CONTINUATION_CORRUPT")
            innerTable = None
        else:
            if (
                not isinstance(payloadValue, bytes)
                or row["innerEncodedByteCount"] != len(payloadValue)
                or row["innerPayloadDigest"] != hashlib.sha256(payloadValue).hexdigest()
            ):
                raise ContinuationError("CONTINUATION_CORRUPT")
            facts, innerTable = _innerTable(payloadValue, logicalLimit=maxLogicalBytes)
            if (
                row["innerRowCount"] != facts.rowCount
                or facts.rowCount <= 0
                or row["innerLogicalByteCount"] != facts.logicalByteCount
                or row["innerSchemaDigest"] != facts.schemaDigest
                or not row["receiptRef"]
                or not row["contentHash"]
                or not row["temporalStatus"]
            ):
                raise ContinuationError("CONTINUATION_CORRUPT")
            totalRows += facts.rowCount
            totalLogicalBytes += facts.logicalByteCount
        entries.append(
            _OwnerEntry(
                requestId=requestId,
                assetId=_requireText(row["assetId"]),
                assetVersionId=_requireText(row["assetVersionId"]),
                sourcePin=_requireDigest(row["sourcePin"]),
                queryPin=_requireDigest(row["queryPin"]),
                entityOrdinal=entityOrdinal,
                entityId=_requireText(row["entityId"]),
                sourceEntityId=_requireOptionalText(row["sourceEntityId"]),
                status=status,
                gapCodes=tuple(gapCodes),
                gapMessages=tuple(gapMessages),
                receiptRef=_requireOptionalText(row["receiptRef"]),
                contentHash=_requireOptionalText(row["contentHash"]),
                temporalStatus=_requireOptionalText(row["temporalStatus"]),
                payload=payloadValue,
            )
        )
        tables.append(innerTable)
    if totalRows != claimedRowCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
    if totalRows > maxPageRows:
        raise ContinuationError("CONTINUATION_ROW_BUDGET")
    if totalLogicalBytes > maxLogicalBytes:
        raise ContinuationError("CONTINUATION_LOGICAL_BYTE_BUDGET")
    return _DecodedPage(
        ArrowPayloadFacts(
            rowCount=totalRows,
            byteCount=len(payload),
            logicalByteCount=totalLogicalBytes,
            schemaDigest=outerFacts.schemaDigest,
            containerKind="stream",
        ),
        tuple(entries),
        tuple(tables),
    )


def _validateOwnerPayload(
    payload: bytes,
    *,
    claimedRowCount: int,
    expectedSchemaDigest: str,
    maxPageBytes: int,
    maxLogicalBytes: int,
) -> ArrowPayloadFacts:
    if expectedSchemaDigest != arrowSchemaDigest(_OUTER_SCHEMA):
        raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
    return _decodePage(
        payload,
        claimedRowCount=claimedRowCount,
        maxPageRows=MAX_PAGE_ROWS,
        maxPageBytes=maxPageBytes,
        maxLogicalBytes=maxLogicalBytes,
    ).facts


def _continuationStore(*, deadline: float, runMaintenance: bool = True):
    return continuationStore(
        deadline=deadline,
        payloadValidator=_validateOwnerPayload,
        runMaintenance=runMaintenance,
    )
