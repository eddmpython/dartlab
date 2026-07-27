"""Composite paging의 canonical query, session, lane state codec."""

from __future__ import annotations

import base64
import binascii
import dataclasses
import hashlib
import hmac
import importlib
import json
import math
import zlib
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.dataHub.continuation import (
    ContinuationError,
    ContinuationPins,
    arrowSchemaDigest,
    canonicalDigest,
    canonicalJsonBytes,
)
from dartlab.dataHub.contracts import (
    DataAssetDescriptor,
    DataQuery,
    FactorProjection,
    GraphProjection,
    NarrativeProjection,
    NativeProjection,
    QueryBudget,
    RecordsProjection,
    ResourceProjection,
    TimeContext,
    UniverseSelection,
)
from dartlab.dataHub.paging.composite.models import (
    _EAGER_SCHEMA,
    _FORMAT_VERSION,
    _LOWER_SESSION_ENCODING,
    _MAX_LANES,
    _MAX_PACKED_SESSION_BYTES,
    _PAGE_KIND,
)
from dartlab.dataHub.paging.runtime import MAX_PAGE_BYTES, MAX_PAGE_ROWS, MAX_STATE_BYTES
from dartlab.dataHub.paging.stateCodec import rejectDuplicateKeys, requireDigest, requireText, strictTree


def _strictTree(value: Any, *, seen: set[int] | None = None) -> Any:
    """compositePagingState state tree를 공유 codec으로 canonical 변환한다."""

    return strictTree(value, context="composite state", seen=seen)


def _jsonLoad(payload: bytes) -> Any:
    """중복 key와 비정규 JSON을 거부하며 private state를 읽는다.

    중복 key 거부 규칙은 `stateCodec.rejectDuplicateKeys` 가 갖는다. 세 lane 이 같은 여섯
    줄을 각자 갖고 있었다. canonical 왕복 검사는 lane 마다 자리가 달라 여기 남긴다.
    """
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=rejectDuplicateKeys)
    except ContinuationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None
    if canonicalJsonBytes(value) != payload:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return value


_requireText = requireText


_requireDigest = requireDigest


def _packLowerSession(payload: bytes) -> dict[str, Any]:
    """Bounded lower JSON session을 canonical compressed tree로 바꾼다."""

    if not isinstance(payload, bytes) or not payload or len(payload) > MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    compressed = zlib.compress(payload, level=9)
    if not compressed or len(compressed) > _MAX_PACKED_SESSION_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    return {
        "encoding": _LOWER_SESSION_ENCODING,
        "rawSize": len(payload),
        "rawDigest": hashlib.sha256(payload).hexdigest(),
        "payload": base64.b64encode(compressed).decode("ascii"),
    }


def _unpackLowerSession(value: Any) -> bytes:
    """크기, stream 경계, digest를 확인하며 lower JSON session을 복원한다."""

    expected = {"encoding", "rawSize", "rawDigest", "payload"}
    if not isinstance(value, dict) or set(value) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    rawSize = value["rawSize"]
    encoded = value["payload"]
    if (
        value["encoding"] != _LOWER_SESSION_ENCODING
        or type(rawSize) is not int
        or not 0 < rawSize <= MAX_STATE_BYTES
        or type(encoded) is not str
        or not encoded
        or len(encoded) > 4 * ((_MAX_PACKED_SESSION_BYTES + 2) // 3)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    rawDigest = _requireDigest(value["rawDigest"])
    try:
        compressed = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None
    if (
        not compressed
        or len(compressed) > _MAX_PACKED_SESSION_BYTES
        or base64.b64encode(compressed).decode("ascii") != encoded
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    decoder = zlib.decompressobj()
    try:
        payload = decoder.decompress(compressed, MAX_STATE_BYTES + 1)
    except zlib.error:
        raise ContinuationError("CONTINUATION_CORRUPT") from None
    if len(payload) > MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    if decoder.unconsumed_tail or not decoder.eof:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    if decoder.unused_data or decoder.flush():
        raise ContinuationError("CONTINUATION_CORRUPT")
    if len(payload) != rawSize or not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), rawDigest):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return payload


def _pinsTree(pins: ContinuationPins) -> dict[str, str]:
    return {
        "sourceDigest": pins.sourceDigest,
        "queryDigest": pins.queryDigest,
        "contractDigest": pins.contractDigest,
        "schemaDigest": pins.schemaDigest,
    }


def _decodePins(value: Any) -> ContinuationPins:
    expected = {"sourceDigest", "queryDigest", "contractDigest", "schemaDigest"}
    if not isinstance(value, dict) or set(value) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    try:
        return ContinuationPins(**value)
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _samePins(expected: ContinuationPins, current: ContinuationPins) -> None:
    checks = (
        (expected.sourceDigest, current.sourceDigest, "CONTINUATION_SOURCE_STALE"),
        (expected.queryDigest, current.queryDigest, "CONTINUATION_QUERY_STALE"),
        (expected.contractDigest, current.contractDigest, "CONTINUATION_CONTRACT_STALE"),
        (expected.schemaDigest, current.schemaDigest, "CONTINUATION_SCHEMA_STALE"),
    )
    for expectedValue, currentValue, code in checks:
        if not hmac.compare_digest(expectedValue, currentValue):
            raise ContinuationError(code)


def _queryPayload(assetIds: Sequence[str], query: DataQuery) -> bytes:
    payload = canonicalJsonBytes(
        {
            "version": _FORMAT_VERSION,
            "pageKind": _PAGE_KIND,
            "assetIds": list(assetIds),
            "query": _strictTree(query),
        }
    )
    if len(payload) > MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    return payload


def _validateQueryPayload(payload: bytes) -> None:
    if not isinstance(payload, bytes) or len(payload) > MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    root = _jsonLoad(payload)
    if (
        not isinstance(root, dict)
        or set(root) != {"version", "pageKind", "assetIds", "query"}
        or root["version"] != _FORMAT_VERSION
        or root["pageKind"] != _PAGE_KIND
        or not isinstance(root["assetIds"], list)
        or any(type(item) is not str for item in root["assetIds"])
        or not isinstance(root["query"], dict)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")


def _laneTree(
    planned: Mapping[str, Any],
    *,
    requestId: str,
    requestIndex: int,
    descriptor: DataAssetDescriptor,
) -> dict[str, Any]:
    expected = {
        "laneKind",
        "privateState",
        "sourceDigest",
        "contractDigest",
        "schemaDigest",
    }
    if set(planned) != expected:
        raise ValueError("composite adapter plan schema가 다릅니다")
    laneKind = planned["laneKind"]
    if laneKind not in {"resource", "owner", "eager"}:
        raise ValueError("composite laneKind가 유효하지 않습니다")
    return {
        "requestId": requestId,
        "requestIndex": requestIndex,
        "assetId": descriptor.assetId,
        "assetVersionId": descriptor.assetVersionId,
        "layer": descriptor.layer,
        "laneKind": laneKind,
        "concurrencyGroup": descriptor.concurrencyGroup,
        "privateState": _strictTree(planned["privateState"]),
        "sourceDigest": _requireDigest(planned["sourceDigest"]),
        "contractDigest": _requireDigest(planned["contractDigest"]),
        "schemaDigest": _requireDigest(planned["schemaDigest"]),
        "done": False,
        "attempted": 0,
        "succeededRows": 0,
        "succeededPartitions": 0,
        "failedItems": 0,
        "gapCounts": {},
    }


def _decodeLane(value: Any, requestIndex: int) -> dict[str, Any]:
    expected = {
        "requestId",
        "requestIndex",
        "assetId",
        "assetVersionId",
        "layer",
        "laneKind",
        "concurrencyGroup",
        "privateState",
        "sourceDigest",
        "contractDigest",
        "schemaDigest",
        "done",
        "attempted",
        "succeededRows",
        "succeededPartitions",
        "failedItems",
        "gapCounts",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    if value["requestIndex"] != requestIndex or type(value["requestIndex"]) is not int:
        raise ContinuationError("CONTINUATION_CORRUPT")
    for name in ("requestId", "assetId", "assetVersionId", "layer"):
        _requireText(value[name])
    if value["laneKind"] not in {"resource", "owner", "eager"}:
        raise ContinuationError("CONTINUATION_CORRUPT")
    if value["concurrencyGroup"] is not None and type(value["concurrencyGroup"]) is not str:
        raise ContinuationError("CONTINUATION_CORRUPT")
    if not isinstance(value["privateState"], dict) or type(value["done"]) is not bool:
        raise ContinuationError("CONTINUATION_CORRUPT")
    for name in ("sourceDigest", "contractDigest", "schemaDigest"):
        _requireDigest(value[name])
    for name in ("attempted", "succeededRows", "succeededPartitions", "failedItems"):
        if type(value[name]) is not int or value[name] < 0:
            raise ContinuationError("CONTINUATION_CORRUPT")
    gapCounts = value["gapCounts"]
    if (
        not isinstance(gapCounts, dict)
        or any(type(code) is not str or not code for code in gapCounts)
        or any(type(count) is not int or count <= 0 for count in gapCounts.values())
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    copied = _strictTree(value)
    if not isinstance(copied, dict):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return copied


def _encodeSession(session: Mapping[str, Any]) -> bytes:
    payload = canonicalJsonBytes(_strictTree(session))
    if len(payload) > MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    return payload


def _decodeSession(payload: bytes) -> dict[str, Any]:
    if not isinstance(payload, bytes) or len(payload) > MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    root = _jsonLoad(payload)
    expected = {
        "version",
        "pageKind",
        "snapshotId",
        "contractHash",
        "requestedAssets",
        "resolvedAssets",
        "pageMaxRows",
        "pageMaxBytes",
        "pageTimeoutMs",
        "maxConcurrency",
        "nextLaneIndex",
        "lanes",
    }
    if (
        not isinstance(root, dict)
        or set(root) != expected
        or root["version"] != _FORMAT_VERSION
        or root["pageKind"] != _PAGE_KIND
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    _requireText(root["snapshotId"])
    _requireDigest(root["contractHash"])
    for name in (
        "requestedAssets",
        "resolvedAssets",
        "pageMaxRows",
        "pageMaxBytes",
        "pageTimeoutMs",
        "maxConcurrency",
        "nextLaneIndex",
    ):
        if type(root[name]) is not int or root[name] < 0:
            raise ContinuationError("CONTINUATION_CORRUPT")
    if (
        root["requestedAssets"] <= 0
        or root["resolvedAssets"] <= 0
        or root["pageMaxRows"] <= 0
        or root["pageMaxRows"] > MAX_PAGE_ROWS
        or root["pageMaxBytes"] <= 0
        or root["pageMaxBytes"] > MAX_PAGE_BYTES
        or root["pageTimeoutMs"] <= 0
        or root["maxConcurrency"] <= 0
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    laneValues = root["lanes"]
    if not isinstance(laneValues, list) or not 1 <= len(laneValues) <= _MAX_LANES:
        raise ContinuationError("CONTINUATION_CORRUPT")
    lanes = [_decodeLane(value, index) for index, value in enumerate(laneValues)]
    if len({lane["requestId"] for lane in lanes}) != len(lanes):
        raise ContinuationError("CONTINUATION_CORRUPT")
    if not 0 <= root["nextLaneIndex"] < len(lanes):
        raise ContinuationError("CONTINUATION_CORRUPT")
    root["lanes"] = lanes
    return root


def isCompositePagingState(payload: bytes) -> bool:
    """Private cursor가 composite outer state인지 보수적으로 판별한다.

    Args:
        payload: Continuation CAS에서 복원한 cursor bytes.

    Returns:
        Canonical composite marker가 있으면 ``True``.

    Raises:
        없음. 손상된 payload는 ``False``다.

    Example:
        ``isCompositePagingState(context.state.cursorPayload)``.
    """

    try:
        root = _jsonLoad(payload)
    except ContinuationError:
        return False
    return isinstance(root, dict) and root.get("pageKind") == _PAGE_KIND


def _descriptorCodec() -> tuple[Any, Any, Any, Any, Any]:
    module = importlib.import_module("dartlab.dataHub.paging.owner")
    return (
        getattr(module, "_descriptorTree"),
        getattr(module, "_decodeDescriptor"),
        getattr(module, "_queryTree"),
        getattr(module, "_decodeQuery"),
        getattr(module, "_ownerCodePin"),
    )


def _queryTree(query: DataQuery) -> dict[str, Any]:
    if query.requests or query.continuation is not None:
        raise ValueError("composite eager active query가 정규화되지 않았습니다")
    return {
        "subjects": list(query.subjects),
        "measures": list(query.measures),
        "universe": _strictTree(query.universe),
        "projection": _strictTree(query.projection),
        "time": _strictTree(query.time),
        "params": _strictTree(query.params),
        "budget": _strictTree(query.budget),
        "completeness": query.completeness,
        "lineage": query.lineage,
    }


def _decodeQuery(value: Any) -> DataQuery:
    expected = {
        "subjects",
        "measures",
        "universe",
        "projection",
        "time",
        "params",
        "budget",
        "completeness",
        "lineage",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    projectionValue = value["projection"]
    if not isinstance(projectionValue, dict):
        raise ContinuationError("CONTINUATION_CORRUPT")
    kind = projectionValue.get("kind")
    if not isinstance(kind, str):
        raise ContinuationError("CONTINUATION_CORRUPT")
    projectionTypes = {
        "native": NativeProjection,
        "records": RecordsProjection,
        "factor": FactorProjection,
        "graph": GraphProjection,
        "narrative": NarrativeProjection,
        "resource": ResourceProjection,
    }
    projectionType = projectionTypes.get(kind)
    if projectionType is None:
        raise ContinuationError("CONTINUATION_CORRUPT")
    projectionArguments = dict(projectionValue)
    if kind == "factor":
        measures = projectionArguments.get("measures")
        if not isinstance(measures, list):
            raise ContinuationError("CONTINUATION_CORRUPT")
        projectionArguments["measures"] = tuple(measures)
    try:
        projection = projectionType(**projectionArguments)
        universeValue = value["universe"]
        universe = None
        if universeValue is not None:
            if not isinstance(universeValue, dict):
                raise TypeError("universe")
            universeArguments = dict(universeValue)
            universeArguments["markets"] = tuple(universeArguments["markets"])
            universeArguments["explicitIds"] = tuple(universeArguments["explicitIds"])
            universe = UniverseSelection(**universeArguments)
        timeValue = value["time"]
        if timeValue is not None and not isinstance(timeValue, dict):
            raise TypeError("time")
        budgetValue = value["budget"]
        if not isinstance(budgetValue, dict) or not isinstance(value["params"], dict):
            raise TypeError("budget")
        return DataQuery(
            subjects=tuple(value["subjects"]),
            measures=tuple(value["measures"]),
            universe=universe,
            projection=projection,
            time=TimeContext(**timeValue) if timeValue is not None else None,
            params=value["params"],
            budget=QueryBudget(**budgetValue),
            completeness=value["completeness"],
            lineage=value["lineage"],
        )
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _lanePins(lane: Mapping[str, Any]) -> ContinuationPins:
    return ContinuationPins(
        sourceDigest=_requireDigest(lane["sourceDigest"]),
        queryDigest=canonicalDigest(
            {
                "requestId": lane["requestId"],
                "requestIndex": lane["requestIndex"],
                "assetId": lane["assetId"],
                "privateState": lane["privateState"],
            }
        ),
        contractDigest=_requireDigest(lane["contractDigest"]),
        schemaDigest=_requireDigest(lane["schemaDigest"]),
    )


def _isSafeEagerLane(descriptor: DataAssetDescriptor, query: DataQuery) -> bool:
    """Source payload를 읽거나 비격리 owner code를 실행하지 않는 eager locator인지 판정한다."""

    return (
        descriptor.executorKind == "resource"
        and isinstance(query.projection, ResourceProjection)
        and not query.projection.includePayload
    )
