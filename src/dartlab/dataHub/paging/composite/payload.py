"""Composite outer page와 eager result의 fixed-schema Arrow codec."""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl
import pyarrow as pa

from dartlab.dataHub.continuation import (
    ArrowPayloadFacts,
    ContinuationError,
    arrowSchemaDigest,
    bytesDigest,
    canonicalJsonBytes,
    inspectArrowIpcPayload,
)
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataGap,
    DataLineage,
    DataPartition,
    DataQuery,
    DataResult,
    QualityAssertion,
    UniverseCoverage,
)
from dartlab.dataHub.paging.composite.models import (
    _COMPOSITE_SCHEMA,
    _EAGER_SCHEMA,
    _DecodedComposite,
)
from dartlab.dataHub.paging.composite.state import (
    _jsonLoad,
    _queryPayload,
    _requireDigest,
    _requireText,
    _strictTree,
)
from dartlab.dataHub.paging.runtime import MAX_PAGE_BYTES
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

_log = dataHubLogger(__name__)


def compositeQueryDigest(
    assetIds: Sequence[str],
    query: DataQuery,
) -> str:
    """Source 조회 없이 logical query의 stable reuse digest를 계산한다."""

    return bytesDigest(_queryPayload(assetIds, query))


def materializationPageSchemaDigest() -> str:
    """Materialized public result page wrapper의 Arrow schema digest를 반환한다."""

    return arrowSchemaDigest(_EAGER_SCHEMA)


def encodeMaterializationPage(
    result: DataResult,
    *,
    maxBytes: int = MAX_PAGE_BYTES,
) -> bytes:
    """Composite public page 하나를 fixed-schema Arrow IPC로 봉인한다."""

    return _encodeEagerResult(result, maxBytes=maxBytes)


def decodeMaterializationPage(payload: bytes) -> DataResult:
    """Materialized fixed-schema Arrow IPC를 public DataResult로 복원한다."""

    return _decodeEagerResult(payload)


def _arrowPayload(table: pa.Table) -> bytes:
    combined = table.combine_chunks()
    sink = pa.BufferOutputStream()
    options = pa.ipc.IpcWriteOptions(compression=None)
    with pa.ipc.new_stream(sink, combined.schema, options=options) as writer:
        writer.write_table(combined)
    return sink.getvalue().to_pybytes()


def _readArrowTable(payload: bytes, schema: pa.Schema, *, maxLogicalBytes: int) -> pa.Table:
    facts = inspectArrowIpcPayload(payload, maxLogicalBytes=maxLogicalBytes)
    if facts.containerKind != "stream":
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    try:
        reader = pa.ipc.open_stream(pa.BufferReader(payload))
        actualSchema = reader.schema
        batches = tuple(reader)
        table = pa.Table.from_batches(batches, schema=actualSchema)
    except Exception:
        recordFailure(_log, "CONTINUATION_PAYLOAD_INVALID")
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID") from None
    if actualSchema != schema or len(batches) != 1 or table.num_rows != facts.rowCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    return table


def _encodeCompositeRows(rows: Sequence[Mapping[str, Any]], *, maxBytes: int) -> bytes:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "requestIndex": row["requestIndex"],
                "requestId": row["requestId"],
                "layer": row["layer"],
                "laneKind": row["laneKind"],
                "startStateDigest": row["startStateDigest"],
                "nextStateDigest": row["nextStateDigest"],
                "done": row["done"],
                "attempted": row["attempted"],
                "succeededRows": row["succeededRows"],
                "succeededPartitions": row["succeededPartitions"],
                "failedItems": row["failedItems"],
                "gapCodes": list(row["gapCodes"]),
                "childMaxRows": row["childMaxRows"],
                "childMaxBytes": row["childMaxBytes"],
                "childMaxConcurrency": row["childMaxConcurrency"],
                "childPayload": row["childPayload"],
                "childClaimedRows": row["childClaimedRows"],
                "childSchemaDigest": row["childSchemaDigest"],
                "childPayloadDigest": row["childPayloadDigest"],
            }
        )
    payload = _arrowPayload(pa.Table.from_pylist(normalized, schema=_COMPOSITE_SCHEMA))
    if len(payload) > maxBytes:
        raise ContinuationError("CONTINUATION_BYTE_BUDGET")
    return payload


def _decodeComposite(
    payload: bytes,
    *,
    claimedRowCount: int,
    maxPageBytes: int,
    maxLogicalBytes: int,
) -> _DecodedComposite:
    if len(payload) > maxPageBytes:
        raise ContinuationError("CONTINUATION_BYTE_BUDGET")
    facts = inspectArrowIpcPayload(payload, maxLogicalBytes=maxLogicalBytes)
    table = _readArrowTable(payload, _COMPOSITE_SCHEMA, maxLogicalBytes=maxLogicalBytes)
    if facts.rowCount != claimedRowCount or table.num_rows != claimedRowCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
    rows = []
    seenRequests: set[str] = set()
    for value in table.to_pylist():
        requestId = _requireText(value["requestId"])
        if requestId in seenRequests:
            raise ContinuationError("CONTINUATION_CORRUPT")
        seenRequests.add(requestId)
        for name in (
            "requestIndex",
            "attempted",
            "succeededRows",
            "succeededPartitions",
            "failedItems",
            "childMaxRows",
            "childMaxBytes",
            "childMaxConcurrency",
            "childClaimedRows",
        ):
            if type(value[name]) is not int or value[name] < 0:
                raise ContinuationError("CONTINUATION_CORRUPT")
        if any(value[name] <= 0 for name in ("childMaxRows", "childMaxBytes", "childMaxConcurrency")):
            raise ContinuationError("CONTINUATION_CORRUPT")
        if type(value["done"]) is not bool or value["laneKind"] not in {"resource", "owner", "eager"}:
            raise ContinuationError("CONTINUATION_CORRUPT")
        startDigest = _requireDigest(value["startStateDigest"])
        nextDigest = value["nextStateDigest"]
        if nextDigest is not None:
            nextDigest = _requireDigest(nextDigest)
        if value["done"] != (nextDigest is None):
            raise ContinuationError("CONTINUATION_CORRUPT")
        childPayload = value["childPayload"]
        if not isinstance(childPayload, bytes):
            raise ContinuationError("CONTINUATION_CORRUPT")
        childPayloadDigest = _requireDigest(value["childPayloadDigest"])
        if not hmac.compare_digest(hashlib.sha256(childPayload).hexdigest(), childPayloadDigest):
            raise ContinuationError("CONTINUATION_CORRUPT")
        gapCodes = value["gapCodes"]
        if not isinstance(gapCodes, list) or any(type(code) is not str or not code for code in gapCodes):
            raise ContinuationError("CONTINUATION_CORRUPT")
        rows.append(
            {
                **value,
                "startStateDigest": startDigest,
                "nextStateDigest": nextDigest,
                "childSchemaDigest": _requireDigest(value["childSchemaDigest"]),
                "childPayloadDigest": childPayloadDigest,
                "gapCodes": tuple(gapCodes),
            }
        )
    return _DecodedComposite(facts=facts, rows=tuple(rows))


def _validateCompositePayload(
    payload: bytes,
    *,
    claimedRowCount: int,
    expectedSchemaDigest: str,
    maxPageBytes: int,
    maxLogicalBytes: int,
) -> ArrowPayloadFacts:
    if not hmac.compare_digest(expectedSchemaDigest, arrowSchemaDigest(_COMPOSITE_SCHEMA)):
        raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
    return _decodeComposite(
        payload,
        claimedRowCount=claimedRowCount,
        maxPageBytes=maxPageBytes,
        maxLogicalBytes=maxLogicalBytes,
    ).facts


def _assertionTree(assertion: QualityAssertion) -> dict[str, Any]:
    return _strictTree(assertion)


def _lineageTree(lineage: DataLineage | None) -> dict[str, Any] | None:
    tree = _strictTree(lineage)
    if tree is not None and not isinstance(tree, dict):
        raise TypeError("lineage tree가 mapping이 아닙니다")
    return tree


def _partitionMetadata(partition: DataPartition) -> bytes:
    return canonicalJsonBytes(
        {
            "asset": _strictTree(partition.asset),
            "projectionKind": partition.projectionKind,
            "schema": _strictTree(partition.schema),
            "rowCount": partition.rowCount,
            "truncated": partition.truncated,
            "selector": _strictTree(partition.selector),
            "temporalStatus": partition.temporalStatus,
            "lineageRefs": list(partition.lineageRefs),
            "requestId": partition.requestId,
            "lineage": _lineageTree(partition.lineage),
            "qualityAssertions": [_assertionTree(item) for item in partition.qualityAssertions],
            "contentHash": partition.contentHash,
        }
    )


def _partitionData(partition: DataPartition) -> tuple[str, bytes]:
    data = partition.data
    if isinstance(data, pl.DataFrame):
        return "polars", _arrowPayload(data.to_arrow())
    if data is None:
        return "scalar", canonicalJsonBytes({"type": "null", "value": None})
    if type(data) is bool:
        return "scalar", canonicalJsonBytes({"type": "bool", "value": data})
    if type(data) is int:
        return "scalar", canonicalJsonBytes({"type": "int", "value": data})
    if type(data) is float:
        return "scalar", canonicalJsonBytes({"type": "float", "value": _strictTree(data)})
    if type(data) is str:
        return "scalar", canonicalJsonBytes({"type": "str", "value": data})
    if type(data) is bytes:
        return "bytes", data
    if isinstance(data, Mapping):
        return "mapping", canonicalJsonBytes(_strictTree(data))
    if isinstance(data, tuple):
        return "tuple", canonicalJsonBytes(_strictTree(data))
    if isinstance(data, list):
        return "list", canonicalJsonBytes(_strictTree(data))
    try:
        return "arrow", _arrowPayload(partition.toArrow())
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID") from None


def _resultMetadata(result: DataResult) -> bytes:
    return canonicalJsonBytes(
        {
            "status": result.status,
            "assets": [_strictTree(item) for item in result.assets],
            "snapshotId": result.snapshotId,
            "contractHash": result.contractHash,
            "coverage": _strictTree(result.coverage),
            "gaps": [_strictTree(item) for item in result.gaps],
            "lineageRefs": list(result.lineageRefs),
            "executionReceipts": list(result.executionReceipts),
            "qualityAssertions": [_assertionTree(item) for item in result.qualityAssertions],
            "universeSnapshotId": result.universeSnapshotId,
            "universeCoverage": [_strictTree(item) for item in result.universeCoverage],
            "dataSnapshotId": result.dataSnapshotId,
        }
    )


def _encodeEagerResult(result: DataResult, *, maxBytes: int) -> bytes:
    partitionMetadata = []
    dataKinds = []
    dataPayloads = []
    for partition in result.partitions:
        kind, payload = _partitionData(partition)
        partitionMetadata.append(_partitionMetadata(partition))
        dataKinds.append(kind)
        dataPayloads.append(payload)
    table = pa.Table.from_pylist(
        [
            {
                "resultMetadata": _resultMetadata(result),
                "partitionMetadata": partitionMetadata,
                "dataKinds": dataKinds,
                "dataPayloads": dataPayloads,
            }
        ],
        schema=_EAGER_SCHEMA,
    )
    payload = _arrowPayload(table)
    if len(payload) > maxBytes:
        raise ContinuationError("CONTINUATION_BYTE_BUDGET")
    return payload


def _decodeAsset(value: Any) -> AssetRef:
    if not isinstance(value, dict) or set(value) != {"assetId", "assetVersionId"}:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return AssetRef(_requireText(value["assetId"]), _requireText(value["assetVersionId"]))


def _decodeAssertion(value: Any) -> QualityAssertion:
    if not isinstance(value, dict):
        raise ContinuationError("CONTINUATION_CORRUPT")
    try:
        return QualityAssertion(**value)
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _decodeLineage(value: Any) -> DataLineage | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ContinuationError("CONTINUATION_CORRUPT")
    tree = dict(value)
    for name in ("sourceRefs", "evidenceRefs"):
        if not isinstance(tree.get(name), list):
            raise ContinuationError("CONTINUATION_CORRUPT")
        tree[name] = tuple(tree[name])
    try:
        return DataLineage(**tree)
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _decodeGap(value: Any) -> DataGap:
    if not isinstance(value, dict):
        raise ContinuationError("CONTINUATION_CORRUPT")
    try:
        return DataGap(**value)
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _decodeUniverseCoverage(value: Any) -> UniverseCoverage:
    if not isinstance(value, dict):
        raise ContinuationError("CONTINUATION_CORRUPT")
    tree = dict(value)
    for name in ("selector",):
        if not isinstance(tree.get(name), list):
            raise ContinuationError("CONTINUATION_CORRUPT")
        tree[name] = tuple(tuple(item) for item in tree[name])
    for name in ("missingSample", "gapCodes"):
        if not isinstance(tree.get(name), list):
            raise ContinuationError("CONTINUATION_CORRUPT")
        tree[name] = tuple(tree[name])
    try:
        return UniverseCoverage(**tree)
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _decodePartitionData(kind: str, payload: bytes) -> Any:
    if kind in {"polars", "arrow"}:
        table = _readArrowTableAny(payload)
        return pl.from_arrow(table)
    if kind == "bytes":
        return payload
    value = _jsonLoad(payload)
    if kind == "scalar" and isinstance(value, dict) and set(value) == {"type", "value"}:
        scalarType = value["type"]
        scalar = value["value"]
        if scalarType == "null" and scalar is None:
            return None
        if scalarType == "bool" and type(scalar) is bool:
            return scalar
        if scalarType == "int" and type(scalar) is int:
            return scalar
        if scalarType == "float" and type(scalar) is float and math.isfinite(scalar):
            return scalar
        if scalarType == "str" and type(scalar) is str:
            return scalar
        raise ContinuationError("CONTINUATION_CORRUPT")
    if kind == "mapping" and isinstance(value, dict):
        return value
    if kind == "tuple" and isinstance(value, list):
        return tuple(value)
    if kind == "list" and isinstance(value, list):
        return value
    raise ContinuationError("CONTINUATION_CORRUPT")


def _readArrowTableAny(payload: bytes) -> pa.Table:
    facts = inspectArrowIpcPayload(payload)
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
    return table


def _decodePartition(metadataPayload: bytes, dataKind: str, dataPayload: bytes) -> DataPartition:
    metadata = _jsonLoad(metadataPayload)
    expected = {
        "asset",
        "projectionKind",
        "schema",
        "rowCount",
        "truncated",
        "selector",
        "temporalStatus",
        "lineageRefs",
        "requestId",
        "lineage",
        "qualityAssertions",
        "contentHash",
    }
    if not isinstance(metadata, dict) or set(metadata) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    schema = metadata["schema"]
    selector = metadata["selector"]
    lineageRefs = metadata["lineageRefs"]
    assertions = metadata["qualityAssertions"]
    if (
        not isinstance(schema, list)
        or any(not isinstance(item, list) or len(item) != 2 for item in schema)
        or not isinstance(selector, list)
        or any(not isinstance(item, list) or len(item) != 2 for item in selector)
        or not isinstance(lineageRefs, list)
        or not isinstance(assertions, list)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return DataPartition(
        asset=_decodeAsset(metadata["asset"]),
        projectionKind=_requireText(metadata["projectionKind"]),
        data=_decodePartitionData(dataKind, dataPayload),
        schema=tuple((str(name), str(dtype)) for name, dtype in schema),
        rowCount=metadata["rowCount"],
        truncated=metadata["truncated"],
        selector=tuple((str(key), str(value)) for key, value in selector),
        temporalStatus=_requireText(metadata["temporalStatus"]),
        lineageRefs=tuple(_requireText(item) for item in lineageRefs),
        requestId=metadata["requestId"],
        lineage=_decodeLineage(metadata["lineage"]),
        qualityAssertions=tuple(_decodeAssertion(item) for item in assertions),
        contentHash=metadata["contentHash"],
    )


def _decodeEagerResult(payload: bytes) -> DataResult:
    table = _readArrowTable(payload, _EAGER_SCHEMA, maxLogicalBytes=MAX_PAGE_BYTES)
    if table.num_rows != 1:
        raise ContinuationError("CONTINUATION_CORRUPT")
    row = table.to_pylist()[0]
    metadata = _jsonLoad(row["resultMetadata"])
    expected = {
        "status",
        "assets",
        "snapshotId",
        "contractHash",
        "coverage",
        "gaps",
        "lineageRefs",
        "executionReceipts",
        "qualityAssertions",
        "universeSnapshotId",
        "universeCoverage",
        "dataSnapshotId",
    }
    if not isinstance(metadata, dict) or set(metadata) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    partitionMetadata = row["partitionMetadata"]
    dataKinds = row["dataKinds"]
    dataPayloads = row["dataPayloads"]
    if not (
        isinstance(partitionMetadata, list)
        and isinstance(dataKinds, list)
        and isinstance(dataPayloads, list)
        and len(partitionMetadata) == len(dataKinds) == len(dataPayloads)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    partitions = tuple(
        _decodePartition(meta, kind, data)
        for meta, kind, data in zip(partitionMetadata, dataKinds, dataPayloads, strict=True)
    )
    coverageValue = metadata["coverage"]
    if not isinstance(coverageValue, dict):
        raise ContinuationError("CONTINUATION_CORRUPT")
    try:
        coverage = Coverage(**coverageValue)
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None
    return DataResult(
        status=_requireText(metadata["status"]),
        partitions=partitions,
        assets=tuple(_decodeAsset(item) for item in metadata["assets"]),
        snapshotId=_requireText(metadata["snapshotId"]),
        contractHash=_requireDigest(metadata["contractHash"]),
        coverage=coverage,
        gaps=tuple(_decodeGap(item) for item in metadata["gaps"]),
        lineageRefs=tuple(_requireText(item) for item in metadata["lineageRefs"]),
        executionReceipts=tuple(_requireText(item) for item in metadata["executionReceipts"]),
        continuation=None,
        qualityAssertions=tuple(_decodeAssertion(item) for item in metadata["qualityAssertions"]),
        universeSnapshotId=metadata["universeSnapshotId"],
        universeCoverage=tuple(_decodeUniverseCoverage(item) for item in metadata["universeCoverage"]),
        dataSnapshotId=metadata["dataSnapshotId"],
    )
