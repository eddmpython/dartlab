"""Provider-owned full-universe resources를 한 continuation chain으로 multiplex한다."""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import importlib
import json
import math
import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow as pa

from dartlab.dataHub.contentSeal import resultSnapshotId
from dartlab.dataHub.continuation import (
    ArrowPayloadFacts,
    ContinuationError,
    ContinuationPins,
    ContinuationQueryState,
    ContinuationStore,
    PageEnvelope,
    arrowSchemaDigest,
    bytesDigest,
    canonicalDigest,
    canonicalJsonBytes,
    inspectArrowIpcPayload,
)
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataGap,
    DataPartition,
    DataQuery,
    DataResult,
    NativeProjection,
    QualityAssertion,
    UniverseCoverage,
)
from dartlab.dataHub.pagingRuntime import (
    MAX_PAGE_BYTES as _MAX_PAGE_BYTES,
)
from dartlab.dataHub.pagingRuntime import (
    MAX_PAGE_ROWS as _MAX_PAGE_ROWS,
)
from dartlab.dataHub.pagingRuntime import (
    MAX_STATE_BYTES as _MAX_STATE_BYTES,
)
from dartlab.dataHub.pagingRuntime import (
    continuationStore,
    dataHubRoot,
    manifestCachePath,
    requireDeadline,
)

_MAX_PAGE_SHARDS = 64
_FORMAT_VERSION = 2
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_OWNER_MODULE = "dartlab.providers.resourceStream.workbench"
_OWNER_CONTRACTS_MODULE = "dartlab.providers.resourceStream.contracts"
_MULTIPLEX_METADATA = {b"dartlab.dataHub.resource-multiplex": b"v2"}
_MULTIPLEX_SCHEMA = pa.schema(
    [
        pa.field("requestId", pa.string(), nullable=False),
        pa.field("assetId", pa.string(), nullable=False),
        pa.field("assetVersionId", pa.string(), nullable=False),
        pa.field("sourcePin", pa.string(), nullable=False),
        pa.field("queryPin", pa.string(), nullable=False),
        pa.field("startCursor", pa.binary(), nullable=False),
        pa.field("nextCursor", pa.binary(), nullable=True),
        pa.field("scannedShardCount", pa.int64(), nullable=False),
        pa.field("startRow", pa.int64(), nullable=False),
        pa.field("nextRow", pa.int64(), nullable=False),
        pa.field("done", pa.bool_(), nullable=False),
        pa.field("innerPayload", pa.binary(), nullable=False),
        pa.field("innerRowCount", pa.int64(), nullable=False),
        pa.field("innerEncodedByteCount", pa.int64(), nullable=False),
        pa.field("innerLogicalByteCount", pa.int64(), nullable=False),
        pa.field("innerSchemaDigest", pa.string(), nullable=False),
        pa.field("innerPayloadDigest", pa.string(), nullable=False),
    ],
    metadata=_MULTIPLEX_METADATA,
)


@dataclass(frozen=True, slots=True)
class _OwnerBoundary:
    describe: Callable[..., Any]
    read: Callable[..., Any]
    requestType: Any
    prepare: Callable[..., Any] | None = None


@dataclass(frozen=True, slots=True)
class _ResourceTask:
    requestId: str
    assetId: str
    assetVersionId: str
    category: str
    sourceRef: str
    sourcePin: str
    queryPin: str
    ownerSourcePin: str
    ownerQueryPin: str
    requestMapping: Mapping[str, Any]
    sourceShardCount: int
    selectedShardCount: int
    executionMode: str
    provider: str
    market: str
    startRow: int = 0
    cursor: Mapping[str, int] | None = None
    done: bool = False


@dataclass(frozen=True, slots=True)
class _ResourceSession:
    snapshotId: str
    contractHash: str
    requestedAssets: int
    pageMaxRows: int
    pageMaxBytes: int
    pageMaxLogicalBytes: int
    pageMaxShards: int
    pageTimeoutMs: int
    tasks: tuple[_ResourceTask, ...]


@dataclass(frozen=True, slots=True)
class _MultiplexEntry:
    requestId: str
    assetId: str
    assetVersionId: str
    sourcePin: str
    queryPin: str
    startCursor: Mapping[str, int]
    nextCursor: Mapping[str, int] | None
    scannedShardCount: int
    startRow: int
    nextRow: int
    done: bool
    payload: bytes


@dataclass(frozen=True, slots=True)
class _DecodedMultiplex:
    facts: ArrowPayloadFacts
    entries: tuple[_MultiplexEntry, ...]
    tables: tuple[pa.Table, ...]


_TASK_KEYS = frozenset(
    {
        "requestId",
        "assetId",
        "assetVersionId",
        "category",
        "sourceRef",
        "sourcePin",
        "queryPin",
        "ownerSourcePin",
        "ownerQueryPin",
        "requestMapping",
        "sourceShardCount",
        "selectedShardCount",
        "executionMode",
        "provider",
        "market",
        "startRow",
        "cursor",
        "done",
    }
)
_SESSION_KEYS = frozenset(
    {
        "version",
        "snapshotId",
        "contractHash",
        "requestedAssets",
        "pageMaxRows",
        "pageMaxBytes",
        "pageMaxLogicalBytes",
        "pageMaxShards",
        "pageTimeoutMs",
        "tasks",
    }
)
_REQUEST_MAPPING_KEYS = frozenset({"columns", "predicates", "companyIds", "includeSourcePath", "allowRawContent"})
_PAGEABLE_PARAM_KEYS = _REQUEST_MAPPING_KEYS
_CURSOR_KEYS = frozenset({"version", "shardOrdinal", "physicalRowInShard"})


def _ownerBoundary() -> _OwnerBoundary:
    """Provider adapter와 request contract를 정적 의존 없이 불러온다."""

    module = importlib.import_module(_OWNER_MODULE)
    contracts = importlib.import_module(_OWNER_CONTRACTS_MODULE)
    describe = getattr(module, "describeResource")
    read = getattr(module, "readResourcePage")
    prepare = getattr(module, "prepareResourceRead", None)
    requestType = getattr(contracts, "ResourceReadRequest")
    if (
        not callable(describe)
        or not callable(read)
        or (prepare is not None and not callable(prepare))
        or not hasattr(requestType, "fromMapping")
    ):
        raise RuntimeError("resource owner boundary가 유효하지 않습니다")
    return _OwnerBoundary(describe, read, requestType, prepare)


def _textDigest(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("owner pin이 비었습니다")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _strictTree(value: Any, *, seen: set[int] | None = None) -> Any:
    """Typed query를 fallback coercion 없는 strict JSON tree로 바꾼다."""

    activeSeen = set() if seen is None else seen
    if value is None or type(value) in {str, bool, int}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("query float는 유한해야 합니다")
        return value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        identity = id(value)
        if identity in activeSeen:
            raise ValueError("query tree에 cycle이 있습니다")
        activeSeen.add(identity)
        try:
            return {
                field.name: _strictTree(getattr(value, field.name), seen=activeSeen)
                for field in dataclasses.fields(value)
            }
        finally:
            activeSeen.remove(identity)
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in activeSeen:
            raise ValueError("query tree에 cycle이 있습니다")
        activeSeen.add(identity)
        try:
            result = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise TypeError("query mapping key는 str이어야 합니다")
                result[key] = _strictTree(item, seen=activeSeen)
            return result
        finally:
            activeSeen.remove(identity)
    if isinstance(value, (tuple, list)):
        identity = id(value)
        if identity in activeSeen:
            raise ValueError("query tree에 cycle이 있습니다")
        activeSeen.add(identity)
        try:
            return [_strictTree(item, seen=activeSeen) for item in value]
        finally:
            activeSeen.remove(identity)
    raise TypeError("query에는 strict JSON 값만 허용됩니다")


def _queryPayload(assetIds: Sequence[str], query: DataQuery) -> bytes:
    payload = canonicalJsonBytes(
        {
            "version": _FORMAT_VERSION,
            "assetIds": list(assetIds),
            "query": _strictTree(query),
        }
    )
    if len(payload) > _MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    return payload


def _jsonLoad(payload: bytes) -> Any:
    def pairsHook(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
        """중복 키를 거부하며 이어읽기 JSON 객체를 복원한다."""

        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContinuationError("CONTINUATION_CORRUPT")
            result[key] = value
        return result

    try:
        return json.loads(payload.decode("utf-8"), object_pairs_hook=pairsHook)
    except ContinuationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _cursorMapping(value: Any) -> dict[str, int]:
    """Provider object 또는 strict mapping을 canonical cursor mapping으로 바꾼다."""

    converter = getattr(value, "toMapping", None)
    if callable(converter):
        value = converter()
    if not isinstance(value, Mapping) or frozenset(value) != _CURSOR_KEYS:
        raise ValueError("resource cursor key가 유효하지 않습니다")
    version = value["version"]
    shardOrdinal = value["shardOrdinal"]
    physicalRowInShard = value["physicalRowInShard"]
    if (
        type(version) is not int
        or version != 2
        or type(shardOrdinal) is not int
        or shardOrdinal < 0
        or type(physicalRowInShard) is not int
        or physicalRowInShard < 0
    ):
        raise ValueError("resource cursor 값이 유효하지 않습니다")
    return {
        "version": 2,
        "shardOrdinal": shardOrdinal,
        "physicalRowInShard": physicalRowInShard,
    }


def _originCursor() -> dict[str, int]:
    return {"version": 2, "shardOrdinal": 0, "physicalRowInShard": 0}


def _cursorPosition(cursor: Mapping[str, int]) -> tuple[int, int]:
    normalized = _cursorMapping(cursor)
    return normalized["shardOrdinal"], normalized["physicalRowInShard"]


def _cursorBytes(cursor: Mapping[str, int]) -> bytes:
    return canonicalJsonBytes(_cursorMapping(cursor))


def _cursorFromBytes(payload: Any, *, nullable: bool) -> dict[str, int] | None:
    if payload is None and nullable:
        return None
    if not isinstance(payload, bytes):
        raise ContinuationError("CONTINUATION_CORRUPT")
    value = _jsonLoad(payload)
    try:
        cursor = _cursorMapping(value)
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None
    if canonicalJsonBytes(cursor) != payload:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return cursor


def _decodeTaskCursor(value: Any) -> dict[str, int] | None:
    if value is None:
        return None
    try:
        return _cursorMapping(value)
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _validateQueryPayload(payload: bytes) -> None:
    if not isinstance(payload, bytes) or len(payload) > _MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    root = _jsonLoad(payload)
    if not isinstance(root, dict) or frozenset(root) != {"version", "assetIds", "query"}:
        raise ContinuationError("CONTINUATION_CORRUPT")
    if root["version"] != _FORMAT_VERSION:
        raise ContinuationError("CONTINUATION_CORRUPT")
    if not isinstance(root["assetIds"], list) or any(type(item) is not str for item in root["assetIds"]):
        raise ContinuationError("CONTINUATION_CORRUPT")
    if not isinstance(root["query"], dict) or canonicalJsonBytes(root) != payload:
        raise ContinuationError("CONTINUATION_CORRUPT")


def _taskTree(task: _ResourceTask) -> dict[str, Any]:
    return {
        "requestId": task.requestId,
        "assetId": task.assetId,
        "assetVersionId": task.assetVersionId,
        "category": task.category,
        "sourceRef": task.sourceRef,
        "sourcePin": task.sourcePin,
        "queryPin": task.queryPin,
        "ownerSourcePin": task.ownerSourcePin,
        "ownerQueryPin": task.ownerQueryPin,
        "requestMapping": _strictTree(task.requestMapping),
        "sourceShardCount": task.sourceShardCount,
        "selectedShardCount": task.selectedShardCount,
        "executionMode": task.executionMode,
        "provider": task.provider,
        "market": task.market,
        "startRow": task.startRow,
        "cursor": _strictTree(task.cursor),
        "done": task.done,
    }


def _encodeSession(session: _ResourceSession) -> bytes:
    payload = canonicalJsonBytes(
        {
            "version": _FORMAT_VERSION,
            "snapshotId": session.snapshotId,
            "contractHash": session.contractHash,
            "requestedAssets": session.requestedAssets,
            "pageMaxRows": session.pageMaxRows,
            "pageMaxBytes": session.pageMaxBytes,
            "pageMaxLogicalBytes": session.pageMaxLogicalBytes,
            "pageMaxShards": session.pageMaxShards,
            "pageTimeoutMs": session.pageTimeoutMs,
            "tasks": [_taskTree(task) for task in session.tasks],
        }
    )
    if len(payload) > _MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    return payload


def _requireText(value: Any) -> str:
    if type(value) is not str or not value:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return value


def _requireDigest(value: Any) -> str:
    text = _requireText(value)
    if _DIGEST_RE.fullmatch(text) is None:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return text


def _decodeTask(value: Any) -> _ResourceTask:
    if not isinstance(value, dict) or frozenset(value) != _TASK_KEYS:
        raise ContinuationError("CONTINUATION_CORRUPT")
    mapping = value["requestMapping"]
    if not isinstance(mapping, dict) or frozenset(mapping) != _REQUEST_MAPPING_KEYS:
        raise ContinuationError("CONTINUATION_CORRUPT")
    startRow = value["startRow"]
    sourceShardCount = value["sourceShardCount"]
    selectedShardCount = value["selectedShardCount"]
    cursor = _decodeTaskCursor(value["cursor"])
    done = value["done"]
    if (
        type(startRow) is not int
        or startRow < 0
        or type(sourceShardCount) is not int
        or sourceShardCount <= 0
        or type(selectedShardCount) is not int
        or selectedShardCount <= 0
        or selectedShardCount > sourceShardCount
        or type(done) is not bool
        or (done and cursor is not None)
        or (not done and startRow > 0 and cursor is None)
        or (cursor is not None and cursor["shardOrdinal"] >= selectedShardCount)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    sourcePin = _requireDigest(value["sourcePin"])
    queryPin = _requireDigest(value["queryPin"])
    ownerSourcePin = _requireText(value["ownerSourcePin"])
    ownerQueryPin = _requireText(value["ownerQueryPin"])
    if _textDigest(ownerSourcePin) != sourcePin or _textDigest(ownerQueryPin) != queryPin:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return _ResourceTask(
        requestId=_requireText(value["requestId"]),
        assetId=_requireText(value["assetId"]),
        assetVersionId=_requireText(value["assetVersionId"]),
        category=_requireText(value["category"]),
        sourceRef=_requireText(value["sourceRef"]),
        sourcePin=sourcePin,
        queryPin=queryPin,
        ownerSourcePin=ownerSourcePin,
        ownerQueryPin=ownerQueryPin,
        requestMapping=mapping,
        sourceShardCount=sourceShardCount,
        selectedShardCount=selectedShardCount,
        executionMode=_requireText(value["executionMode"]),
        provider=_requireText(value["provider"]),
        market=_requireText(value["market"]),
        startRow=startRow,
        cursor=cursor,
        done=done,
    )


def _decodeSession(payload: bytes) -> _ResourceSession:
    if not isinstance(payload, bytes) or len(payload) > _MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    root = _jsonLoad(payload)
    if not isinstance(root, dict) or frozenset(root) != _SESSION_KEYS:
        raise ContinuationError("CONTINUATION_CORRUPT")
    if root["version"] != _FORMAT_VERSION or canonicalJsonBytes(root) != payload:
        raise ContinuationError("CONTINUATION_CORRUPT")
    integerNames = (
        "requestedAssets",
        "pageMaxRows",
        "pageMaxBytes",
        "pageMaxLogicalBytes",
        "pageMaxShards",
        "pageTimeoutMs",
    )
    if any(type(root[name]) is not int or root[name] <= 0 for name in integerNames):
        raise ContinuationError("CONTINUATION_CORRUPT")
    if (
        root["pageMaxRows"] > _MAX_PAGE_ROWS
        or root["pageMaxBytes"] > _MAX_PAGE_BYTES
        or root["pageMaxLogicalBytes"] > _MAX_PAGE_BYTES
        or root["pageMaxShards"] > _MAX_PAGE_SHARDS
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    taskValues = root["tasks"]
    if not isinstance(taskValues, list) or not taskValues:
        raise ContinuationError("CONTINUATION_CORRUPT")
    tasks = tuple(_decodeTask(item) for item in taskValues)
    if len({task.requestId for task in tasks}) != len(tasks):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return _ResourceSession(
        snapshotId=_requireText(root["snapshotId"]),
        contractHash=_requireDigest(root["contractHash"]),
        requestedAssets=root["requestedAssets"],
        pageMaxRows=root["pageMaxRows"],
        pageMaxBytes=root["pageMaxBytes"],
        pageMaxLogicalBytes=root["pageMaxLogicalBytes"],
        pageMaxShards=root["pageMaxShards"],
        pageTimeoutMs=root["pageTimeoutMs"],
        tasks=tasks,
    )


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


def _workbenchRoot() -> Path:
    return dataHubRoot()


def _manifestCachePath(assetId: str, category: str) -> Path:
    return manifestCachePath(assetId, category)


def _requireDeadline(deadline: float) -> float:
    return requireDeadline(deadline)


def _continuationStore(*, deadline: float, runMaintenance: bool = True) -> ContinuationStore:
    return continuationStore(
        deadline=deadline,
        payloadValidator=_validateMultiplexPayload,
        runMaintenance=runMaintenance,
    )


def _contractDigest(session: _ResourceSession) -> str:
    return canonicalDigest(
        {
            "format": "dartlab-resource-multiplex",
            "version": _FORMAT_VERSION,
            "contractHash": session.contractHash,
            "tasks": [
                {
                    "requestId": task.requestId,
                    "assetId": task.assetId,
                    "assetVersionId": task.assetVersionId,
                    "category": task.category,
                    "requestMapping": task.requestMapping,
                    "sourceShardCount": task.sourceShardCount,
                    "selectedShardCount": task.selectedShardCount,
                    "executionMode": task.executionMode,
                    "provider": task.provider,
                    "market": task.market,
                }
                for task in session.tasks
            ],
        }
    )


def _pins(session: _ResourceSession, queryPayload: bytes, sourcePins: Mapping[str, str]) -> ContinuationPins:
    return ContinuationPins(
        sourceDigest=canonicalDigest(dict(sourcePins)),
        queryDigest=bytesDigest(queryPayload),
        contractDigest=_contractDigest(session),
        schemaDigest=arrowSchemaDigest(_MULTIPLEX_SCHEMA),
    )


def _requireCurrentPins(expected: ContinuationPins, current: ContinuationPins) -> None:
    checks = (
        (expected.sourceDigest, current.sourceDigest, "CONTINUATION_SOURCE_STALE"),
        (expected.queryDigest, current.queryDigest, "CONTINUATION_QUERY_STALE"),
        (expected.contractDigest, current.contractDigest, "CONTINUATION_CONTRACT_STALE"),
        (expected.schemaDigest, current.schemaDigest, "CONTINUATION_SCHEMA_STALE"),
    )
    for expectedValue, currentValue, code in checks:
        if not hmac.compare_digest(expectedValue, currentValue):
            raise ContinuationError(code)


def isPageableResource(descriptor: DataAssetDescriptor, query: DataQuery) -> bool:
    """Descriptor와 projection이 full-universe pageable resource인지 판별한다."""

    return (
        isinstance(query.projection, NativeProjection)
        and not query.subjects
        and descriptor.kind == "resource"
        and descriptor.executorKind == "resource"
        and descriptor.assetId.startswith("resource.")
        and (descriptor.executionMode == "resourceCompanyShard" or descriptor.assetId == "resource.edgar")
    )


def _normalizedRequestMapping(
    boundary: _OwnerBoundary,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    description: Any,
) -> tuple[dict[str, Any], str]:
    params = dict(query.params)
    if any(type(key) is not str for key in params) or not set(params) <= _PAGEABLE_PARAM_KEYS:
        raise ValueError("pageable resource params가 유효하지 않습니다")
    schemaFields = getattr(description, "schemaFields", None)
    if not isinstance(schemaFields, tuple) or any(
        not isinstance(field, tuple) or len(field) != 2 or any(type(item) is not str for item in field)
        for field in schemaFields
    ):
        raise ValueError("resource description schema가 유효하지 않습니다")
    available = {name for name, _fieldType in schemaFields}
    rawColumns = params.get("columns")
    if rawColumns is None:
        columns = tuple(name for name, _fieldType in schemaFields if name != "contentRaw")
    elif isinstance(rawColumns, (tuple, list)) and all(type(item) is str for item in rawColumns):
        columns = tuple(rawColumns)
    else:
        raise ValueError("resource columns가 유효하지 않습니다")
    if not columns or not set(columns) <= available:
        raise ValueError("resource columns가 description 밖에 있습니다")
    base: dict[str, Any] = {
        "columns": list(columns),
        "predicates": params.get("predicates", []),
        "companyIds": params.get("companyIds", []),
        "includeSourcePath": params.get("includeSourcePath", True),
        "allowRawContent": params.get("allowRawContent", False),
    }
    probe = boundary.requestType.fromMapping(base | {"batchRows": 1, "maxRows": 1, "maxBytes": 1})
    normalized = probe.toMapping()
    semantic = {key: normalized[key] for key in _REQUEST_MAPPING_KEYS}
    ownerQueryPin = probe.queryPin(descriptor.assetId)
    if not isinstance(ownerQueryPin, str) or not ownerQueryPin:
        raise ValueError("resource owner query pin이 비었습니다")
    return semantic, ownerQueryPin


def _descriptionTask(
    boundary: _OwnerBoundary,
    requestId: str,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    *,
    description: Any | None = None,
) -> _ResourceTask:
    category = descriptor.executorAxis or descriptor.assetId.removeprefix("resource.")
    cachePath = _manifestCachePath(descriptor.assetId, category)
    if description is None:
        description = boundary.describe(descriptor.assetId, category, cachePath)
    if (
        getattr(description, "resourceId", None) != descriptor.assetId
        or getattr(description, "category", None) != category
    ):
        raise ValueError("resource description identity가 다릅니다")
    ownerSourcePin = getattr(description, "sourcePin", None)
    if not isinstance(ownerSourcePin, str) or not ownerSourcePin.startswith("resource-source-full:"):
        raise ValueError("resource source pin이 full identity가 아닙니다")
    mapping, ownerQueryPin = _normalizedRequestMapping(boundary, descriptor, query, description)
    sourceShardCount = getattr(description, "shardCount", None)
    if type(sourceShardCount) is not int or sourceShardCount <= 0:
        raise ValueError("resource description shard count가 유효하지 않습니다")
    selectedCompanyIds = mapping["companyIds"]
    if not isinstance(selectedCompanyIds, (tuple, list)):
        raise ValueError("resource selected shard가 유효하지 않습니다")
    selectedShardCount = len(selectedCompanyIds) if selectedCompanyIds else sourceShardCount
    if selectedShardCount <= 0 or selectedShardCount > sourceShardCount:
        raise ValueError("resource selected shard count가 유효하지 않습니다")
    metadata = dict(descriptor.metadata)
    provider = metadata.get("sourceProvider", descriptor.owner)
    market = descriptor.universeMarkets[0] if len(descriptor.universeMarkets) == 1 else "UNKNOWN"
    if not isinstance(provider, str) or not provider or not isinstance(market, str) or not market:
        raise ValueError("resource coverage contract가 유효하지 않습니다")
    return _ResourceTask(
        requestId=requestId,
        assetId=descriptor.assetId,
        assetVersionId=descriptor.assetVersionId,
        category=category,
        sourceRef=descriptor.sourceRef,
        sourcePin=_textDigest(ownerSourcePin),
        queryPin=_textDigest(ownerQueryPin),
        ownerSourcePin=ownerSourcePin,
        ownerQueryPin=ownerQueryPin,
        requestMapping=mapping,
        sourceShardCount=sourceShardCount,
        selectedShardCount=selectedShardCount,
        executionMode=descriptor.executionMode,
        provider=provider,
        market=market,
    )


def _preparedDescriptionTask(
    boundary: _OwnerBoundary,
    requestId: str,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
) -> tuple[_ResourceTask, Any | None]:
    """가능하면 description과 바로 이어질 page가 같은 owner manifest를 쓰게 한다."""

    if boundary.prepare is None:
        return _descriptionTask(boundary, requestId, descriptor, query), None
    category = descriptor.executorAxis or descriptor.assetId.removeprefix("resource.")
    prepared = boundary.prepare(
        descriptor.assetId,
        category,
        _manifestCachePath(descriptor.assetId, category),
    )
    description = getattr(prepared, "description", None)
    if description is None or not callable(getattr(prepared, "read", None)):
        raise ValueError("prepared resource owner 계약이 유효하지 않습니다")
    return (
        _descriptionTask(
            boundary,
            requestId,
            descriptor,
            query,
            description=description,
        ),
        prepared,
    )


def _currentSourcePins(
    boundary: _OwnerBoundary,
    session: _ResourceSession,
    *,
    deadline: float,
) -> tuple[dict[str, str], dict[str, Any]]:
    pins = {}
    preparedReads: dict[str, Any] = {}
    for task in session.tasks:
        _requireDeadline(deadline)
        if boundary.prepare is None:
            description = boundary.describe(
                task.assetId,
                task.category,
                _manifestCachePath(task.assetId, task.category),
            )
        else:
            prepared = boundary.prepare(
                task.assetId,
                task.category,
                _manifestCachePath(task.assetId, task.category),
            )
            description = getattr(prepared, "description", None)
            if description is None or not callable(getattr(prepared, "read", None)):
                raise ContinuationError("CONTINUATION_SOURCE_STALE")
            preparedReads[task.requestId] = prepared
        _requireDeadline(deadline)
        if (
            getattr(description, "resourceId", None) != task.assetId
            or getattr(description, "category", None) != task.category
            or getattr(description, "shardCount", None) != task.sourceShardCount
        ):
            raise ContinuationError("CONTINUATION_SOURCE_STALE")
        ownerPin = getattr(description, "sourcePin", None)
        if not isinstance(ownerPin, str):
            raise ContinuationError("CONTINUATION_SOURCE_STALE")
        pins[task.requestId] = _textDigest(ownerPin)
    return pins, preparedReads


def _validateOwnerPage(
    task: _ResourceTask,
    page: Any,
    request: Any,
) -> tuple[ArrowPayloadFacts, bytes, dict[str, int], dict[str, int] | None, int]:
    if getattr(page, "resourceId", None) != task.assetId or getattr(page, "category", None) != task.category:
        raise ValueError("owner page identity가 다릅니다")
    payload = getattr(page, "encodedBytes", None)
    encodedByteCount = getattr(page, "encodedByteCount", None)
    actualSchemaFields = getattr(page, "actualSchemaFields", None)
    receipt = getattr(page, "receipt", None)
    if not isinstance(payload, bytes) or encodedByteCount != len(payload) or receipt is None:
        raise ValueError("owner encoded payload claim이 다릅니다")
    integerClaims = ("startRow", "nextRow", "batchCount", "rowCount", "byteCount", "scannedShardCount")
    if (
        any(type(getattr(receipt, name, None)) is not int for name in integerClaims)
        or type(getattr(receipt, "truncated", None)) is not bool
    ):
        raise ValueError("owner receipt type이 다릅니다")
    facts, table, batchCount = _innerTable(payload, logicalLimit=request.maxBytes)
    try:
        startCursor = _cursorMapping(getattr(receipt, "startCursor", None))
        rawNextCursor = getattr(receipt, "nextCursor", None)
        nextCursor = _cursorMapping(rawNextCursor) if rawNextCursor is not None else None
    except (TypeError, ValueError):
        raise ValueError("owner receipt cursor가 다릅니다") from None
    expectedStartCursor = _cursorMapping(task.cursor) if task.cursor is not None else _originCursor()
    parsedSchema = tuple((field.name, str(field.type)) for field in table.schema)
    if actualSchemaFields != parsedSchema:
        raise ValueError("owner actual schema claim이 다릅니다")
    expectedBatchCount = 1 if facts.rowCount else 0
    checks = (
        getattr(receipt, "sourcePin", None) == task.ownerSourcePin,
        getattr(receipt, "queryPin", None) == task.ownerQueryPin,
        getattr(receipt, "integrityMode", None) == "full",
        getattr(receipt, "startRow", None) == task.startRow,
        getattr(receipt, "nextRow", None) == task.startRow + facts.rowCount,
        getattr(receipt, "batchCount", None) == expectedBatchCount,
        getattr(receipt, "rowCount", None) == facts.rowCount,
        startCursor == expectedStartCursor,
        getattr(receipt, "truncated", None) == (nextCursor is not None),
        0 < getattr(receipt, "scannedShardCount", 0) <= request.maxShards,
        getattr(receipt, "scannedShardCount", 0) <= task.selectedShardCount,
        startCursor["shardOrdinal"] < task.selectedShardCount,
        nextCursor is None or nextCursor["shardOrdinal"] < task.selectedShardCount,
        nextCursor is None or _cursorPosition(nextCursor) > _cursorPosition(startCursor),
        0 <= getattr(receipt, "byteCount", -1) <= request.maxBytes,
        facts.rowCount == 0 or getattr(receipt, "byteCount", 0) > 0,
        batchCount == 1,
        _textDigest(getattr(receipt, "sourcePin", "")) == task.sourcePin,
        _textDigest(getattr(receipt, "queryPin", "")) == task.queryPin,
    )
    if not all(checks):
        raise ValueError("owner receipt claim이 다릅니다")
    return facts, payload, startCursor, nextCursor, receipt.scannedShardCount


def _materializeOnce(
    state: ContinuationQueryState,
    boundary: _OwnerBoundary,
    *,
    rowLimit: int,
    byteLimit: int,
    logicalLimit: int,
    deadline: float,
    preparedReads: Mapping[str, Any] | None = None,
) -> PageEnvelope:
    _requireDeadline(deadline)
    _validateQueryPayload(state.queryPayload)
    session = _decodeSession(state.cursorPayload)
    _requireDeadline(deadline)
    unfinished = tuple(task for task in session.tasks if not task.done)
    if not unfinished:
        raise ContinuationError("CONTINUATION_CORRUPT")
    if rowLimit < len(unfinished):
        raise ContinuationError("CONTINUATION_ROW_BUDGET")
    innerCapacity = min(byteLimit // 3, logicalLimit // 3)
    if innerCapacity <= 0:
        raise ContinuationError("CONTINUATION_LOGICAL_BYTE_BUDGET")
    remainingRows = rowLimit
    remainingInner = innerCapacity
    entries: list[_MultiplexEntry] = []
    updated = {task.requestId: task for task in session.tasks}
    for index, task in enumerate(unfinished):
        _requireDeadline(deadline)
        remainingTasks = len(unfinished) - index
        shareRows = max(1, remainingRows // remainingTasks)
        shareBytes = max(1, remainingInner // remainingTasks)
        if task.requestMapping["allowRawContent"] is True:
            shareRows = min(shareRows, 256)
            shareBytes = min(shareBytes, 2 * 1024 * 1024)
        requestMapping = dict(task.requestMapping) | {
            "batchRows": shareRows,
            "maxRows": shareRows,
            "maxBytes": shareBytes,
            "startRow": task.startRow,
            "cursor": task.cursor,
            "maxShards": session.pageMaxShards,
            "expectedSourcePin": task.ownerSourcePin,
            "expectedQueryPin": task.ownerQueryPin,
        }
        request = boundary.requestType.fromMapping(requestMapping)
        prepared = preparedReads.get(task.requestId) if preparedReads is not None else None
        if prepared is not None:
            page = prepared.read(request.toMapping())
        else:
            page = boundary.read(
                task.assetId,
                task.category,
                request.toMapping(),
                _manifestCachePath(task.assetId, task.category),
            )
        _requireDeadline(deadline)
        facts, payload, startCursor, nextCursor, scannedShardCount = _validateOwnerPage(task, page, request)
        receipt = page.receipt
        done = nextCursor is None
        entries.append(
            _MultiplexEntry(
                requestId=task.requestId,
                assetId=task.assetId,
                assetVersionId=task.assetVersionId,
                sourcePin=task.sourcePin,
                queryPin=task.queryPin,
                startCursor=startCursor,
                nextCursor=nextCursor,
                scannedShardCount=scannedShardCount,
                startRow=task.startRow,
                nextRow=receipt.nextRow,
                done=done,
                payload=payload,
            )
        )
        updated[task.requestId] = dataclasses.replace(
            task,
            startRow=receipt.nextRow,
            cursor=nextCursor,
            done=done,
        )
        remainingRows -= facts.rowCount
        remainingInner -= max(facts.logicalByteCount, facts.byteCount)
        if remainingRows < 0 or remainingInner < 0:
            raise ContinuationError("CONTINUATION_LOGICAL_BYTE_BUDGET")
    payload = _encodeMultiplex(
        entries,
        maxPageRows=rowLimit,
        maxPageBytes=byteLimit,
        maxLogicalBytes=logicalLimit,
    )
    _requireDeadline(deadline)
    nextTasks = tuple(updated[task.requestId] for task in session.tasks)
    nextState = None
    if any(not task.done for task in nextTasks):
        nextSession = dataclasses.replace(session, tasks=nextTasks)
        nextState = ContinuationQueryState(state.queryPayload, _encodeSession(nextSession))
    return PageEnvelope(
        payload=payload, rowCount=sum(entry.nextRow - entry.startRow for entry in entries), nextState=nextState
    )


def _materialize(
    state: ContinuationQueryState,
    boundary: _OwnerBoundary,
    *,
    deadline: float,
    preparedReads: Mapping[str, Any] | None = None,
) -> PageEnvelope:
    session = _decodeSession(state.cursorPayload)
    rowLimit = session.pageMaxRows
    byteLimit = session.pageMaxBytes
    logicalLimit = session.pageMaxLogicalBytes
    for attempt in range(6):
        _requireDeadline(deadline)
        try:
            return _materializeOnce(
                state,
                boundary,
                rowLimit=rowLimit,
                byteLimit=byteLimit,
                logicalLimit=logicalLimit,
                deadline=deadline,
                preparedReads=preparedReads if attempt == 0 else None,
            )
        except ContinuationError as error:
            if error.code not in {"CONTINUATION_BYTE_BUDGET", "CONTINUATION_LOGICAL_BYTE_BUDGET"} or attempt == 5:
                raise
            unfinishedCount = sum(not task.done for task in session.tasks)
            rowLimit = max(unfinishedCount, rowLimit // 2)
            byteLimit = max(1, byteLimit // 2)
            logicalLimit = max(1, logicalLimit // 2)
    raise ContinuationError("CONTINUATION_BYTE_BUDGET")


def _progressValues(
    task: _ResourceTask,
    entry: _MultiplexEntry | None,
) -> tuple[int, int, int, bool, int, int]:
    if task.done:
        return task.selectedShardCount, task.selectedShardCount, 0, True, 0, task.startRow
    if entry is None:
        raise ContinuationError("CONTINUATION_CORRUPT")
    if entry.done:
        return task.selectedShardCount, task.selectedShardCount, 0, True, entry.scannedShardCount, entry.nextRow
    if entry.nextCursor is None:
        raise ContinuationError("CONTINUATION_CORRUPT")
    cursor = _cursorMapping(entry.nextCursor)
    return (
        cursor["shardOrdinal"],
        cursor["shardOrdinal"],
        cursor["physicalRowInShard"],
        False,
        entry.scannedShardCount,
        entry.nextRow,
    )


def _progressSelector(task: _ResourceTask, entry: _MultiplexEntry | None) -> tuple[tuple[str, str], ...]:
    completed, cursorShard, cursorRow, complete, scanned, nextRow = _progressValues(task, entry)
    startRow = entry.startRow if entry is not None else task.startRow
    return (
        ("complete", str(complete).lower()),
        ("completedShardCount", str(completed)),
        ("cursorPhysicalRowInShard", str(cursorRow)),
        ("cursorShardOrdinal", str(cursorShard)),
        ("nextRow", str(nextRow)),
        ("pageScannedShardCount", str(scanned)),
        ("queryPin", task.queryPin),
        ("selectedShardCount", str(task.selectedShardCount)),
        ("sourcePin", task.sourcePin),
        ("sourceShardCount", str(task.sourceShardCount)),
        ("startRow", str(startRow)),
    )


def _universeCoverage(
    session: _ResourceSession,
    entries: Mapping[str, _MultiplexEntry],
) -> tuple[UniverseCoverage, ...]:
    coverage = []
    for task in session.tasks:
        entry = entries.get(task.requestId)
        completed, _cursorShard, _cursorRow, complete, _scanned, _nextRow = _progressValues(task, entry)
        missing = task.selectedShardCount - completed
        coverage.append(
            UniverseCoverage(
                requestId=task.requestId,
                assetId=task.assetId,
                market=task.market,
                provider=task.provider,
                executionMode=task.executionMode,
                snapshotId=task.ownerSourcePin,
                selector=_progressSelector(task, entry),
                requestedEntities=task.selectedShardCount,
                returnedEntities=completed,
                matchedEntities=completed,
                missingEntities=missing,
                extraEntities=0,
                status="complete" if complete else "partial",
                gapCodes=() if complete else ("SOURCE_SHARD_SCAN_IN_PROGRESS",),
            )
        )
    return tuple(coverage)


def _resultFromPage(session: _ResourceSession, page: Any) -> DataResult:
    decoded = _decodeMultiplex(
        page.payload,
        claimedRowCount=page.rowCount,
        maxPageRows=session.pageMaxRows,
        maxPageBytes=session.pageMaxBytes,
        maxLogicalBytes=session.pageMaxLogicalBytes,
    )
    byRequest = {task.requestId: task for task in session.tasks}
    entryByRequest = {entry.requestId: entry for entry in decoded.entries}
    expectedRequestIds = {task.requestId for task in session.tasks if not task.done}
    if set(entryByRequest) != expectedRequestIds:
        raise ContinuationError("CONTINUATION_CORRUPT")
    pageComplete = all(task.done or entryByRequest[task.requestId].done for task in session.tasks)
    if (page.nextToken is None) != pageComplete:
        raise ContinuationError("CONTINUATION_CORRUPT")
    partitions = []
    for entry, table in zip(decoded.entries, decoded.tables, strict=True):
        task = byRequest.get(entry.requestId)
        if (
            task is None
            or task.assetId != entry.assetId
            or task.assetVersionId != entry.assetVersionId
            or task.sourcePin != entry.sourcePin
            or task.queryPin != entry.queryPin
            or entry.startRow != task.startRow
            or entry.startCursor != (task.cursor if task.cursor is not None else _originCursor())
            or entry.scannedShardCount > session.pageMaxShards
            or entry.scannedShardCount > task.selectedShardCount
            or (entry.nextCursor is not None and entry.nextCursor["shardOrdinal"] >= task.selectedShardCount)
        ):
            raise ContinuationError("CONTINUATION_CORRUPT")
        frame = pl.from_arrow(table)
        if not isinstance(frame, pl.DataFrame):
            raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
        contentHashRef = f"sha256:{hashlib.sha256(entry.payload).hexdigest()}"
        partitions.append(
            DataPartition(
                asset=AssetRef(task.assetId, task.assetVersionId),
                projectionKind="native",
                data=frame,
                schema=tuple((name, str(dtype)) for name, dtype in frame.schema.items()),
                rowCount=entry.nextRow - entry.startRow,
                truncated=not entry.done,
                selector=_progressSelector(task, entry),
                temporalStatus="LATEST_ONLY",
                lineageRefs=(task.sourceRef, page.pageRef),
                requestId=task.requestId,
                qualityAssertions=(
                    QualityAssertion(
                        assertionId="contentSealed",
                        success=True,
                        severity="error",
                        expected="verified Arrow IPC content hash",
                        observed=contentHashRef,
                        assetId=task.assetId,
                    ),
                ),
                contentHash=contentHashRef,
            )
        )
    assets = tuple(dict.fromkeys(AssetRef(task.assetId, task.assetVersionId) for task in session.tasks))
    lineageRefs = tuple(dict.fromkeys(ref for partition in partitions for ref in partition.lineageRefs))
    universeCoverage = _universeCoverage(session, entryByRequest)
    universeSnapshotId = "resource-universe:" + canonicalDigest(
        {task.requestId: task.ownerSourcePin for task in session.tasks}
    )
    dataSnapshotId = resultSnapshotId(
        catalogSnapshotId=session.snapshotId,
        contractHash=session.contractHash,
        partitions=partitions,
        universeSnapshotId=universeSnapshotId,
    )
    return DataResult(
        status="partial" if page.nextToken is not None else "ok",
        partitions=tuple(partitions),
        assets=assets,
        snapshotId=session.snapshotId,
        contractHash=session.contractHash,
        coverage=Coverage(session.requestedAssets, len(session.tasks), len(partitions), 0),
        gaps=(),
        lineageRefs=lineageRefs,
        executionReceipts=(page.pageRef,),
        continuation=page.nextToken,
        qualityAssertions=tuple(assertion for partition in partitions for assertion in partition.qualityAssertions),
        universeSnapshotId=universeSnapshotId,
        universeCoverage=universeCoverage,
        dataSnapshotId=dataSnapshotId,
    )


def _failedResult(
    code: str,
    message: str,
    *,
    snapshotId: str = "data-snapshot:continuation-unavailable",
    contractHash: str = "0" * 64,
    assets: Sequence[AssetRef] = (),
    requestedAssets: int = 0,
    resolvedAssets: int = 0,
    systemic: bool = True,
) -> DataResult:
    return DataResult(
        status="failed",
        partitions=(),
        assets=tuple(assets),
        snapshotId=snapshotId,
        contractHash=contractHash,
        coverage=Coverage(requestedAssets, resolvedAssets, 0, 1),
        gaps=(DataGap(code, message, systemic=systemic),),
        lineageRefs=(),
        executionReceipts=(),
        continuation=None,
    )


def _planFailure(
    code: str,
    message: str,
    *,
    snapshotId: str,
    contractHash: str,
    resolved: Sequence[tuple[str, DataAssetDescriptor, DataQuery]],
    requestedAssets: int,
) -> DataResult:
    refs = tuple(
        dict.fromkeys(
            AssetRef(descriptor.assetId, descriptor.assetVersionId) for _requestId, descriptor, _query in resolved
        )
    )
    return _failedResult(
        code,
        message,
        snapshotId=snapshotId,
        contractHash=contractHash,
        assets=refs,
        requestedAssets=requestedAssets,
        resolvedAssets=len(resolved),
        systemic=False,
    )


def executeInitialResourcePaging(
    assetIds: Sequence[str],
    query: DataQuery,
    *,
    requestedAssets: int,
    snapshotId: str,
    contractHash: str,
    resolved: Sequence[tuple[str, DataAssetDescriptor, DataQuery]],
    hasPlanningGaps: bool,
    deadline: float,
) -> DataResult:
    """첫 full-universe resource page를 발급하고 즉시 같은 store에서 redeem한다."""

    try:
        _requireDeadline(deadline)
    except ContinuationError as error:
        return _failedResult(
            error.code,
            str(error),
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=tuple(
                AssetRef(descriptor.assetId, descriptor.assetVersionId) for _requestId, descriptor, _active in resolved
            ),
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
        )
    if any(not isPageableResource(descriptor, active) for _requestId, descriptor, active in resolved):
        return _planFailure(
            "PAGEABLE_MIXED_EXECUTION_UNSUPPORTED",
            "pageable resource와 eager asset은 한 query에서 함께 실행할 수 없습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if query.completeness == "requireComplete":
        return _planFailure(
            "PAGEABLE_REQUIRE_COMPLETE_UNSUPPORTED",
            "pageable resource query는 requireComplete를 지원하지 않습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if hasPlanningGaps or not resolved:
        return _planFailure(
            "PAGEABLE_PLAN_INCOMPLETE",
            "pageable resource query 계획을 완전하게 고정할 수 없습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if any(
        active.universe is not None or active.time is not None or active.measures for _rid, _desc, active in resolved
    ):
        return _planFailure(
            "PAGEABLE_SELECTOR_UNSUPPORTED",
            "pageable resource query는 columns, predicates, companyIds만 지원합니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if query.budget.maxRows < len(resolved):
        return _planFailure(
            "PAGEABLE_ROW_BUDGET_TOO_SMALL",
            "첫 page에 모든 resource를 포함할 row budget이 부족합니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    try:
        _requireDeadline(deadline)
        boundary = _ownerBoundary()
        preparedTasks = tuple(
            _preparedDescriptionTask(boundary, requestId, descriptor, active)
            for requestId, descriptor, active in resolved
        )
        tasks = tuple(task for task, _prepared in preparedTasks)
        preparedReads = {task.requestId: prepared for task, prepared in preparedTasks if prepared is not None}
        _requireDeadline(deadline)
        session = _ResourceSession(
            snapshotId=snapshotId,
            contractHash=contractHash,
            requestedAssets=requestedAssets,
            pageMaxRows=min(query.budget.maxRows, _MAX_PAGE_ROWS),
            pageMaxBytes=min(query.budget.maxBytes, _MAX_PAGE_BYTES),
            pageMaxLogicalBytes=min(query.budget.maxBytes, _MAX_PAGE_BYTES),
            pageMaxShards=_MAX_PAGE_SHARDS,
            pageTimeoutMs=query.budget.timeoutMs,
            tasks=tasks,
        )
        queryPayload = _queryPayload(assetIds, query)
        state = ContinuationQueryState(queryPayload, _encodeSession(session))
        sourcePins = {task.requestId: task.sourcePin for task in tasks}
        pins = _pins(session, queryPayload, sourcePins)
        issueStore = _continuationStore(deadline=deadline)
        issued = issueStore.issue(state, pins)
        _requireDeadline(deadline)
        redeemStore = _continuationStore(deadline=deadline, runMaintenance=False)
        page = redeemStore.redeem(
            issued.token,
            pins,
            materialize=lambda current: _materialize(
                current,
                boundary,
                deadline=deadline,
                preparedReads=preparedReads,
            ),
            waitSeconds=_requireDeadline(deadline),
        )
        _requireDeadline(deadline)
        result = _resultFromPage(session, page)
        _requireDeadline(deadline)
        return result
    except ContinuationError as error:
        return _failedResult(
            error.code,
            str(error),
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=tuple(
                AssetRef(descriptor.assetId, descriptor.assetVersionId) for _requestId, descriptor, _active in resolved
            ),
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
        )
    except Exception:
        return _failedResult(
            "RESOURCE_PAGE_PLAN_FAILED",
            "resource page 계획을 고정하지 못했습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=tuple(
                AssetRef(descriptor.assetId, descriptor.assetVersionId) for _requestId, descriptor, _active in resolved
            ),
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
        )


def resumeResourcePaging(token: str, *, deadline: float, startedAt: float | None = None) -> DataResult:
    """Token private state를 catalog lookup 없이 복원해 다음 multiplex page를 반환한다."""

    session: _ResourceSession | None = None
    try:
        _requireDeadline(deadline)
        contextStore = _continuationStore(deadline=deadline)
        context = contextStore.loadContext(token)
        _requireDeadline(deadline)
        _validateQueryPayload(context.state.queryPayload)
        session = _decodeSession(context.state.cursorPayload)
        if startedAt is not None:
            if type(startedAt) not in {int, float} or not math.isfinite(startedAt) or startedAt > time.perf_counter():
                raise ContinuationError("CONTINUATION_TIMEOUT")
            deadline = float(startedAt) + session.pageTimeoutMs / 1000
        _requireDeadline(deadline)

        def materialize(current: ContinuationQueryState) -> PageEnvelope:
            """현재 원천 pin을 재검증한 뒤 이어질 resource page를 만든다."""

            _requireDeadline(deadline)
            boundary = _ownerBoundary()
            currentSources, preparedReads = _currentSourcePins(boundary, session, deadline=deadline)
            currentPins = _pins(session, context.state.queryPayload, currentSources)
            _requireCurrentPins(context.pins, currentPins)
            return _materialize(
                current,
                boundary,
                deadline=deadline,
                preparedReads=preparedReads,
            )

        _requireDeadline(deadline)
        redeemStore = _continuationStore(deadline=deadline, runMaintenance=False)
        page = redeemStore.redeem(
            token,
            context.pins,
            materialize=materialize,
            waitSeconds=_requireDeadline(deadline),
        )
        _requireDeadline(deadline)
        result = _resultFromPage(session, page)
        _requireDeadline(deadline)
        return result
    except ContinuationError as error:
        return _failedResult(
            error.code,
            str(error),
            snapshotId=session.snapshotId if session is not None else "data-snapshot:continuation-unavailable",
            contractHash=session.contractHash if session is not None else "0" * 64,
            assets=(
                tuple(AssetRef(task.assetId, task.assetVersionId) for task in session.tasks)
                if session is not None
                else ()
            ),
            requestedAssets=session.requestedAssets if session is not None else 0,
            resolvedAssets=len(session.tasks) if session is not None else 0,
        )
    except Exception:
        return _failedResult(
            "CONTINUATION_OWNER_FAILED",
            "continuation page owner 실행에 실패했습니다",
            snapshotId=session.snapshotId if session is not None else "data-snapshot:continuation-unavailable",
            contractHash=session.contractHash if session is not None else "0" * 64,
            assets=(
                tuple(AssetRef(task.assetId, task.assetVersionId) for task in session.tasks)
                if session is not None
                else ()
            ),
            requestedAssets=session.requestedAssets if session is not None else 0,
            resolvedAssets=len(session.tasks) if session is not None else 0,
        )
