"""Resource multiplex Arrow envelope 인코딩과 검증.

형제 lane 인 `ownerPaging*` 과 `compositePaging*` 은 이미 같은 역할로 나뉘어 있다.
이 lane 만 한 파일에 전부 갖고 있어 파일 크기 룰의 800 줄 상한을 넘겼다.
의존 방향은 models, state, payload, source, schedule, results 순 단방향이다.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any

import pyarrow as pa

from dartlab.dataHub.continuation import (
    ArrowPayloadFacts,
    ContinuationError,
    arrowSchemaDigest,
    inspectArrowIpcPayload,
)
from dartlab.dataHub.pagingRuntime import (
    MAX_PAGE_ROWS as _MAX_PAGE_ROWS,
)
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

from .resourcePagingModels import (
    _MULTIPLEX_SCHEMA,
    _DecodedMultiplex,
    _MultiplexEntry,
)
from .resourcePagingState import (
    _cursorBytes,
    _cursorFromBytes,
    _cursorMapping,
    _cursorPosition,
    _requireDigest,
    _requireText,
)

_log = dataHubLogger(__name__)


def _innerTable(payload: bytes, *, logicalLimit: int) -> tuple[ArrowPayloadFacts, pa.Table, int]:
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
    if len(batches) != 1 or table.num_rows != facts.rowCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    return facts, table, len(batches)


def _encodeMultiplex(
    entries: Sequence[_MultiplexEntry],
    *,
    maxPageRows: int,
    maxPageBytes: int,
    maxLogicalBytes: int,
) -> bytes:
    if not entries:
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    claims: list[dict[str, Any]] = []
    totalRows = 0
    for entry in entries:
        innerFacts, _table, _batchCount = _innerTable(entry.payload, logicalLimit=maxLogicalBytes)
        startCursor = _cursorMapping(entry.startCursor)
        nextCursor = _cursorMapping(entry.nextCursor) if entry.nextCursor is not None else None
        if (
            entry.nextRow - entry.startRow != innerFacts.rowCount
            or type(entry.scannedShardCount) is not int
            or entry.scannedShardCount <= 0
            or entry.done != (nextCursor is None)
            or (nextCursor is not None and _cursorPosition(nextCursor) <= _cursorPosition(startCursor))
        ):
            raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
        totalRows += innerFacts.rowCount
        claims.append(
            {
                "requestId": entry.requestId,
                "assetId": entry.assetId,
                "assetVersionId": entry.assetVersionId,
                "sourcePin": entry.sourcePin,
                "queryPin": entry.queryPin,
                "startCursor": _cursorBytes(startCursor),
                "nextCursor": _cursorBytes(nextCursor) if nextCursor is not None else None,
                "scannedShardCount": entry.scannedShardCount,
                "startRow": entry.startRow,
                "nextRow": entry.nextRow,
                "done": entry.done,
                "innerPayload": entry.payload,
                "innerRowCount": innerFacts.rowCount,
                "innerEncodedByteCount": innerFacts.byteCount,
                "innerLogicalByteCount": innerFacts.logicalByteCount,
                "innerSchemaDigest": innerFacts.schemaDigest,
                "innerPayloadDigest": hashlib.sha256(entry.payload).hexdigest(),
            }
        )
    if totalRows > maxPageRows:
        raise ContinuationError("CONTINUATION_ROW_BUDGET")
    arrays = [pa.array([row[field.name] for row in claims], type=field.type) for field in _MULTIPLEX_SCHEMA]
    batch = pa.RecordBatch.from_arrays(arrays, schema=_MULTIPLEX_SCHEMA)
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, _MULTIPLEX_SCHEMA, options=pa.ipc.IpcWriteOptions(compression=None)) as writer:
        writer.write_batch(batch)
    payload = sink.getvalue().to_pybytes()
    _decodeMultiplex(
        payload,
        claimedRowCount=totalRows,
        maxPageRows=maxPageRows,
        maxPageBytes=maxPageBytes,
        maxLogicalBytes=maxLogicalBytes,
    )
    return payload


def _decodeMultiplex(
    payload: bytes,
    *,
    claimedRowCount: int,
    maxPageRows: int,
    maxPageBytes: int,
    maxLogicalBytes: int,
) -> _DecodedMultiplex:
    if len(payload) > maxPageBytes:
        raise ContinuationError("CONTINUATION_BYTE_BUDGET")
    outerFacts = inspectArrowIpcPayload(payload, maxLogicalBytes=maxLogicalBytes)
    if outerFacts.containerKind != "stream" or outerFacts.schemaDigest != arrowSchemaDigest(_MULTIPLEX_SCHEMA):
        raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
    try:
        reader = pa.ipc.open_stream(pa.BufferReader(payload))
        schema = reader.schema
        batches = tuple(reader)
        table = pa.Table.from_batches(batches, schema=schema)
    except Exception:
        recordFailure(_log, "CONTINUATION_PAYLOAD_INVALID")
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID") from None
    if len(batches) != 1 or not schema.equals(_MULTIPLEX_SCHEMA, check_metadata=True):
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    rows = table.to_pylist()
    if not rows or len(rows) != outerFacts.rowCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    entries: list[_MultiplexEntry] = []
    innerTables: list[pa.Table] = []
    totalRows = 0
    totalLogicalBytes = outerFacts.logicalByteCount
    usedRequestIds: set[str] = set()
    for row in rows:
        requestId = _requireText(row["requestId"])
        assetId = _requireText(row["assetId"])
        assetVersionId = _requireText(row["assetVersionId"])
        sourcePin = _requireDigest(row["sourcePin"])
        queryPin = _requireDigest(row["queryPin"])
        startCursor = _cursorFromBytes(row["startCursor"], nullable=False)
        nextCursor = _cursorFromBytes(row["nextCursor"], nullable=True)
        scannedShardCount = row["scannedShardCount"]
        startRow = row["startRow"]
        nextRow = row["nextRow"]
        done = row["done"]
        innerPayload = row["innerPayload"]
        if (
            requestId in usedRequestIds
            or type(startRow) is not int
            or type(nextRow) is not int
            or startRow < 0
            or nextRow < startRow
            or type(done) is not bool
            or startCursor is None
            or type(scannedShardCount) is not int
            or scannedShardCount <= 0
            or done != (nextCursor is None)
            or (nextCursor is not None and _cursorPosition(nextCursor) <= _cursorPosition(startCursor))
            or not isinstance(innerPayload, bytes)
        ):
            raise ContinuationError("CONTINUATION_CORRUPT")
        usedRequestIds.add(requestId)
        if row["innerEncodedByteCount"] != len(innerPayload):
            raise ContinuationError("CONTINUATION_CORRUPT")
        if row["innerPayloadDigest"] != hashlib.sha256(innerPayload).hexdigest():
            raise ContinuationError("CONTINUATION_CORRUPT")
        innerFacts, innerTable, _batchCount = _innerTable(innerPayload, logicalLimit=maxLogicalBytes)
        if row["innerRowCount"] != innerFacts.rowCount or nextRow - startRow != innerFacts.rowCount:
            raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
        if row["innerLogicalByteCount"] != innerFacts.logicalByteCount:
            raise ContinuationError("CONTINUATION_LOGICAL_BYTE_BUDGET")
        if row["innerSchemaDigest"] != innerFacts.schemaDigest:
            raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
        totalRows += innerFacts.rowCount
        totalLogicalBytes += innerFacts.logicalByteCount
        entries.append(
            _MultiplexEntry(
                requestId,
                assetId,
                assetVersionId,
                sourcePin,
                queryPin,
                startCursor,
                nextCursor,
                scannedShardCount,
                startRow,
                nextRow,
                done,
                innerPayload,
            )
        )
        innerTables.append(innerTable)
    if totalRows != claimedRowCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
    if totalRows > maxPageRows:
        raise ContinuationError("CONTINUATION_ROW_BUDGET")
    if totalLogicalBytes > maxLogicalBytes:
        raise ContinuationError("CONTINUATION_LOGICAL_BYTE_BUDGET")
    facts = ArrowPayloadFacts(
        rowCount=totalRows,
        byteCount=len(payload),
        logicalByteCount=totalLogicalBytes,
        schemaDigest=outerFacts.schemaDigest,
        containerKind="stream",
    )
    return _DecodedMultiplex(facts, tuple(entries), tuple(innerTables))


def _validateMultiplexPayload(
    payload: bytes,
    *,
    claimedRowCount: int,
    expectedSchemaDigest: str,
    maxPageBytes: int,
    maxLogicalBytes: int,
) -> ArrowPayloadFacts:
    if expectedSchemaDigest != arrowSchemaDigest(_MULTIPLEX_SCHEMA):
        raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
    return _decodeMultiplex(
        payload,
        claimedRowCount=claimedRowCount,
        maxPageRows=_MAX_PAGE_ROWS,
        maxPageBytes=maxPageBytes,
        maxLogicalBytes=maxLogicalBytes,
    ).facts
