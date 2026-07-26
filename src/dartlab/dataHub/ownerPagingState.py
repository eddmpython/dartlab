"""Owner paging query, descriptor, session의 canonical state codec."""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import importlib
import json
import marshal
import math
import types
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from dartlab.dataHub.continuation import ContinuationError, ContinuationPins, canonicalDigest, canonicalJsonBytes
from dartlab.dataHub.contracts import (
    DataAssetDescriptor,
    DataQuery,
    FactorProjection,
    QueryBudget,
    TimeContext,
    UniverseSelection,
)
from dartlab.dataHub.ownerPagingModels import (
    _FORMAT_VERSION,
    _MAX_ENTITY_PARAMS,
    _MAX_PAGE_ENTITIES,
    _PAGE_KIND,
    _EntityRef,
    _OwnerSession,
    _OwnerTask,
)
from dartlab.dataHub.pagingRuntime import MAX_PAGE_BYTES, MAX_PAGE_ROWS, MAX_STATE_BYTES
from dartlab.dataHub.pagingStateCodec import requireDigest, requireOptionalText, requireText, strictTree


def _strictTree(value: Any, *, seen: set[int] | None = None) -> Any:
    """owner paging query tree를 공유 codec으로 canonical 변환한다."""

    return strictTree(value, context="query", seen=seen)


def _jsonLoad(payload: bytes) -> Any:
    def pairsHook(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
        """중복 JSON key를 거부하며 mapping을 복원한다.

        Capabilities:
            중복 key가 private state의 앞선 값을 덮어쓰지 못하게 한다.

        Args:
            pairs: JSON decoder가 전달한 key와 value 순서쌍.

        Returns:
            중복 key가 없는 mapping.

        Raises:
            ContinuationError: 같은 key가 두 번 나타날 때.

        Example:
            ``pairsHook((("version", 1),))``.

        Guide:
            ``json.loads``의 ``object_pairs_hook``으로만 사용한다.

        When:
            Continuation query와 cursor JSON을 복원할 때 사용한다.

        How:
            입력 순서쌍을 한 번 순회하며 이미 본 key를 거부한다.

        See Also:
            ``_jsonLoad``.

        Requires:
            JSON decoder가 key와 value 순서쌍을 보존해야 한다.

        AI Context:
            중복 key는 일반 입력 오류가 아니라 continuation corruption이다.
        """

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


_requireText = requireText
_requireOptionalText = requireOptionalText
_requireDigest = requireDigest


def _queryTree(query: DataQuery) -> dict[str, Any]:
    projection = query.projection
    if not isinstance(projection, FactorProjection):
        raise ValueError("owner paging은 FactorProjection만 지원합니다")
    return {
        "measures": list(query.measures),
        "projection": {
            "measures": list(projection.measures),
            "unit": projection.unit,
            "frequency": projection.frequency,
        },
        "time": (
            None
            if query.time is None
            else {
                "validAt": query.time.validAt,
                "knownAt": query.time.knownAt,
            }
        ),
        "params": _strictTree(query.params),
        "budget": _strictTree(query.budget),
        "lineage": query.lineage,
    }


def _requestedMeasures(query: DataQuery) -> tuple[str, ...]:
    """Query override 또는 FactorProjection에 고정된 measure를 반환한다."""

    projection = query.projection
    if not isinstance(projection, FactorProjection):
        return tuple(query.measures)
    return tuple(query.measures or projection.measures)


def _sourcePin(
    ownerSourcePin: str,
    membershipDigest: str,
    requestedMeasures: Sequence[str] = (),
) -> str:
    """Source, universe membership, 요청 measure를 한 pin으로 결박한다."""

    return canonicalDigest(
        {
            "ownerSourcePin": ownerSourcePin,
            "membershipDigest": membershipDigest,
            "requestedMeasures": list(requestedMeasures),
        }
    )


def _decodeQuery(value: Any) -> DataQuery:
    expected = {"measures", "projection", "time", "params", "budget", "lineage"}
    if not isinstance(value, dict) or set(value) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    projection = value["projection"]
    budget = value["budget"]
    timeValue = value["time"]
    if (
        not isinstance(projection, dict)
        or set(projection) != {"measures", "unit", "frequency"}
        or not isinstance(budget, dict)
        or set(budget) != {field.name for field in dataclasses.fields(QueryBudget)}
        or (timeValue is not None and (not isinstance(timeValue, dict) or set(timeValue) != {"validAt", "knownAt"}))
        or not isinstance(value["measures"], list)
        or any(type(item) is not str for item in value["measures"])
        or not isinstance(projection["measures"], list)
        or any(type(item) is not str for item in projection["measures"])
        or not isinstance(value["params"], dict)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    try:
        return DataQuery(
            measures=tuple(value["measures"]),
            projection=FactorProjection(
                measures=tuple(projection["measures"]),
                unit=projection["unit"],
                frequency=projection["frequency"],
            ),
            time=TimeContext(**timeValue) if timeValue is not None else None,
            params=value["params"],
            budget=QueryBudget(**budget),
            lineage=value["lineage"],
        )
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _descriptorTree(descriptor: DataAssetDescriptor) -> dict[str, Any]:
    return _strictTree(descriptor)


def _callablePinValue(value: Any, *, seen: set[int] | None = None) -> Any:
    activeSeen = set() if seen is None else seen
    if value is None or type(value) in {str, bool, int}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("owner callable pin float는 유한해야 합니다")
        return value
    if type(value) is complex:
        return {"kind": "complex", "real": value.real, "imag": value.imag}
    if type(value) is bytes:
        return {
            "kind": "bytes",
            "byteCount": len(value),
            "digest": hashlib.sha256(value).hexdigest(),
        }
    if isinstance(value, types.CodeType):
        return _codePinTree(value)
    identity = id(value)
    if identity in activeSeen:
        raise ValueError("owner callable pin 값에 cycle이 있습니다")
    if isinstance(value, Mapping):
        activeSeen.add(identity)
        try:
            pairs = [
                (
                    _callablePinValue(key, seen=activeSeen),
                    _callablePinValue(item, seen=activeSeen),
                )
                for key, item in value.items()
            ]
            pairs.sort(key=lambda pair: canonicalJsonBytes(pair[0]))
            return {"kind": "mapping", "items": [[key, item] for key, item in pairs]}
        finally:
            activeSeen.remove(identity)
    if isinstance(value, (tuple, list, set, frozenset)):
        activeSeen.add(identity)
        try:
            items = [_callablePinValue(item, seen=activeSeen) for item in value]
            kind = type(value).__name__
            if isinstance(value, (set, frozenset)):
                items.sort(key=canonicalJsonBytes)
            return {"kind": kind, "items": items}
        finally:
            activeSeen.remove(identity)
    valueType = type(value)
    return {
        "kind": "typed-value",
        "type": f"{valueType.__module__}.{valueType.__qualname__}",
    }


def _codePinTree(code: types.CodeType) -> dict[str, Any]:
    marshalled = marshal.dumps(code)
    return {
        "kind": "code",
        "name": code.co_name,
        "qualname": code.co_qualname,
        "marshalDigest": hashlib.sha256(marshalled).hexdigest(),
        "bytecodeDigest": hashlib.sha256(code.co_code).hexdigest(),
        "constants": _callablePinValue(code.co_consts),
    }


def _ownerCodePin(
    descriptor: DataAssetDescriptor,
    requestedMeasures: Sequence[str] = (),
) -> str:
    moduleName = descriptor.executorModule
    attribute = descriptor.executorAttribute
    if not moduleName or not attribute:
        raise ValueError("owner callable 경로가 없습니다")
    module = importlib.import_module(moduleName)
    executor = getattr(module, attribute)
    if not callable(executor):
        raise TypeError("owner executor가 callable이 아닙니다")
    modulePath = getattr(module, "__file__", None)
    if not isinstance(modulePath, str) or not modulePath:
        raise ValueError("owner module payload 경로가 없습니다")
    try:
        modulePayload = Path(modulePath).read_bytes()
    except OSError:
        raise ValueError("owner module payload를 읽을 수 없습니다") from None
    code = getattr(executor, "__code__", None)
    if not isinstance(code, types.CodeType):
        call = getattr(type(executor), "__call__", None)
        code = getattr(call, "__code__", None)
    executorType = type(executor)
    return canonicalDigest(
        {
            "module": moduleName,
            "modulePayloadDigest": hashlib.sha256(modulePayload).hexdigest(),
            "attribute": attribute,
            "callableModule": getattr(executor, "__module__", executorType.__module__),
            "callableQualname": getattr(executor, "__qualname__", executorType.__qualname__),
            "callableType": f"{executorType.__module__}.{executorType.__qualname__}",
            "code": None if not isinstance(code, types.CodeType) else _codePinTree(code),
            "defaults": _callablePinValue(getattr(executor, "__defaults__", None)),
            "kwdefaults": _callablePinValue(getattr(executor, "__kwdefaults__", None)),
            "requestedMeasures": list(requestedMeasures),
        }
    )


def _decodeDescriptor(value: Any) -> DataAssetDescriptor:
    expected = {field.name for field in dataclasses.fields(DataAssetDescriptor)}
    if not isinstance(value, dict) or set(value) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    tree = dict(value)
    tupleFields = {"temporalSupport", "universeMarkets"}
    pairFields = {"marketUnits", "metadata"}
    try:
        for name in tupleFields:
            if not isinstance(tree[name], list):
                raise TypeError(name)
            tree[name] = tuple(tree[name])
        for name in pairFields:
            if not isinstance(tree[name], list) or any(
                not isinstance(item, list) or len(item) != 2 for item in tree[name]
            ):
                raise TypeError(name)
            tree[name] = tuple((item[0], item[1]) for item in tree[name])
        return DataAssetDescriptor(**tree)
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def _selectionTree(selection: UniverseSelection) -> dict[str, Any]:
    return _strictTree(selection)


def _decodeSelection(value: Any) -> UniverseSelection:
    expected = {field.name for field in dataclasses.fields(UniverseSelection)}
    if not isinstance(value, dict) or set(value) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    try:
        return UniverseSelection(
            markets=tuple(value["markets"]),
            membership=value["membership"],
            explicitIds=tuple(value["explicitIds"]),
            asOf=value["asOf"],
        )
    except (TypeError, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


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
        or canonicalJsonBytes(root) != payload
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")


def _taskTree(task: _OwnerTask) -> dict[str, Any]:
    return {
        "requestId": task.requestId,
        "descriptor": _descriptorTree(task.descriptor),
        "query": _queryTree(task.query),
        "selection": _selectionTree(task.selection),
        "market": task.market,
        "provider": task.provider,
        "universeSnapshotId": task.universeSnapshotId,
        "membershipDigest": task.membershipDigest,
        "sourceAssetId": task.sourceAssetId,
        "sourceCategory": task.sourceCategory,
        "ownerSourcePin": task.ownerSourcePin,
        "ownerCodePin": task.ownerCodePin,
        "sourcePin": task.sourcePin,
        "queryPin": task.queryPin,
        "entities": [
            {
                "entityId": entity.entityId,
                "sourceEntityId": entity.sourceEntityId,
                "params": [list(item) for item in entity.params],
            }
            for entity in task.entities
        ],
        "cursor": task.cursor,
        "succeededEntities": task.succeededEntities,
        "failedEntities": task.failedEntities,
        "failedSample": list(task.failedSample),
    }


def _encodeSession(session: _OwnerSession) -> bytes:
    payload = canonicalJsonBytes(
        {
            "version": _FORMAT_VERSION,
            "pageKind": _PAGE_KIND,
            "snapshotId": session.snapshotId,
            "contractHash": session.contractHash,
            "requestedAssets": session.requestedAssets,
            "universeSnapshotId": session.universeSnapshotId,
            "pageMaxRows": session.pageMaxRows,
            "pageMaxBytes": session.pageMaxBytes,
            "pageMaxLogicalBytes": session.pageMaxLogicalBytes,
            "pageMaxEntities": session.pageMaxEntities,
            "pageTimeoutMs": session.pageTimeoutMs,
            "maxConcurrency": session.maxConcurrency,
            "nextTaskIndex": session.nextTaskIndex,
            "tasks": [_taskTree(task) for task in session.tasks],
        }
    )
    if len(payload) > MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    return payload


def _decodeEntity(value: Any) -> _EntityRef:
    if not isinstance(value, dict) or set(value) != {"entityId", "sourceEntityId", "params"}:
        raise ContinuationError("CONTINUATION_CORRUPT")
    rawParams = value["params"]
    if (
        not isinstance(rawParams, list)
        or len(rawParams) > _MAX_ENTITY_PARAMS
        or any(not isinstance(item, list) or len(item) != 2 for item in rawParams)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    params = tuple((_requireText(item[0]), _requireText(item[1])) for item in rawParams)
    if params != tuple(sorted(params)) or len({name for name, _value in params}) != len(params):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return _EntityRef(
        _requireText(value["entityId"]),
        _requireOptionalText(value["sourceEntityId"]),
        params,
    )


def _decodeTask(value: Any) -> _OwnerTask:
    expected = {
        "requestId",
        "descriptor",
        "query",
        "selection",
        "market",
        "provider",
        "universeSnapshotId",
        "membershipDigest",
        "sourceAssetId",
        "sourceCategory",
        "ownerSourcePin",
        "ownerCodePin",
        "sourcePin",
        "queryPin",
        "entities",
        "cursor",
        "succeededEntities",
        "failedEntities",
        "failedSample",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    entitiesValue = value["entities"]
    failedSample = value["failedSample"]
    if (
        not isinstance(entitiesValue, list)
        or not entitiesValue
        or not isinstance(failedSample, list)
        or any(type(item) is not str for item in failedSample)
        or len(failedSample) > 32
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    entities = tuple(_decodeEntity(item) for item in entitiesValue)
    cursor = value["cursor"]
    succeeded = value["succeededEntities"]
    failed = value["failedEntities"]
    if (
        type(cursor) is not int
        or cursor < 0
        or cursor > len(entities)
        or type(succeeded) is not int
        or succeeded < 0
        or type(failed) is not int
        or failed < 0
        or succeeded + failed != cursor
        or len({entity.entityId for entity in entities}) != len(entities)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    descriptor = _decodeDescriptor(value["descriptor"])
    query = _decodeQuery(value["query"])
    selection = _decodeSelection(value["selection"])
    membershipDigest = _requireDigest(value["membershipDigest"])
    ownerSourcePin = _requireText(value["ownerSourcePin"])
    ownerCodePin = _requireDigest(value["ownerCodePin"])
    sourcePin = _requireDigest(value["sourcePin"])
    queryPin = _requireDigest(value["queryPin"])
    expectedSourcePin = _sourcePin(
        ownerSourcePin,
        membershipDigest,
        _requestedMeasures(query),
    )
    expectedQueryPin = canonicalDigest(
        {
            "descriptor": _descriptorTree(descriptor),
            "query": _queryTree(query),
            "selection": _selectionTree(selection),
        }
    )
    if not hmac.compare_digest(sourcePin, expectedSourcePin) or not hmac.compare_digest(queryPin, expectedQueryPin):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return _OwnerTask(
        requestId=_requireText(value["requestId"]),
        descriptor=descriptor,
        query=query,
        selection=selection,
        market=_requireText(value["market"]),
        provider=_requireText(value["provider"]),
        universeSnapshotId=_requireText(value["universeSnapshotId"]),
        membershipDigest=membershipDigest,
        sourceAssetId=_requireText(value["sourceAssetId"]),
        sourceCategory=_requireText(value["sourceCategory"]),
        ownerSourcePin=ownerSourcePin,
        ownerCodePin=ownerCodePin,
        sourcePin=sourcePin,
        queryPin=queryPin,
        entities=entities,
        cursor=cursor,
        succeededEntities=succeeded,
        failedEntities=failed,
        failedSample=tuple(failedSample),
    )


def _decodeSession(payload: bytes) -> _OwnerSession:
    expected = {
        "version",
        "pageKind",
        "snapshotId",
        "contractHash",
        "requestedAssets",
        "universeSnapshotId",
        "pageMaxRows",
        "pageMaxBytes",
        "pageMaxLogicalBytes",
        "pageMaxEntities",
        "pageTimeoutMs",
        "maxConcurrency",
        "nextTaskIndex",
        "tasks",
    }
    if not isinstance(payload, bytes) or len(payload) > MAX_STATE_BYTES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    root = _jsonLoad(payload)
    if (
        not isinstance(root, dict)
        or set(root) != expected
        or root["version"] != _FORMAT_VERSION
        or root["pageKind"] != _PAGE_KIND
        or canonicalJsonBytes(root) != payload
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    integerNames = (
        "requestedAssets",
        "pageMaxRows",
        "pageMaxBytes",
        "pageMaxLogicalBytes",
        "pageMaxEntities",
        "pageTimeoutMs",
        "maxConcurrency",
    )
    if any(type(root[name]) is not int or root[name] <= 0 for name in integerNames):
        raise ContinuationError("CONTINUATION_CORRUPT")
    if (
        root["pageMaxRows"] > MAX_PAGE_ROWS
        or root["pageMaxBytes"] > MAX_PAGE_BYTES
        or root["pageMaxLogicalBytes"] > MAX_PAGE_BYTES
        or root["pageMaxEntities"] > _MAX_PAGE_ENTITIES
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    tasksValue = root["tasks"]
    if not isinstance(tasksValue, list) or not tasksValue:
        raise ContinuationError("CONTINUATION_CORRUPT")
    tasks = tuple(_decodeTask(item) for item in tasksValue)
    nextTaskIndex = root["nextTaskIndex"]
    if (
        len({task.requestId for task in tasks}) != len(tasks)
        or type(nextTaskIndex) is not int
        or nextTaskIndex < 0
        or nextTaskIndex >= len(tasks)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return _OwnerSession(
        snapshotId=_requireText(root["snapshotId"]),
        contractHash=_requireDigest(root["contractHash"]),
        requestedAssets=root["requestedAssets"],
        universeSnapshotId=_requireText(root["universeSnapshotId"]),
        pageMaxRows=root["pageMaxRows"],
        pageMaxBytes=root["pageMaxBytes"],
        pageMaxLogicalBytes=root["pageMaxLogicalBytes"],
        pageMaxEntities=root["pageMaxEntities"],
        pageTimeoutMs=root["pageTimeoutMs"],
        maxConcurrency=root["maxConcurrency"],
        tasks=tasks,
        nextTaskIndex=nextTaskIndex,
    )


def isOwnerPagingState(payload: bytes) -> bool:
    """Private cursor payload가 계산형 owner page state인지 보수적으로 판별한다.

    Args:
        payload: Continuation store에서 복원한 private cursor bytes.

    Returns:
        현재 owner page kind가 명시된 canonical JSON이면 ``True``.

    Raises:
        없음. 손상된 payload는 ``False``로 판별한다.

    Example:
        ``isOwnerPagingState(context.state.cursorPayload)``.

    Requires:
        Payload는 private continuation state 후보 bytes여야 한다.
    """

    try:
        root = _jsonLoad(payload)
    except ContinuationError:
        return False
    return isinstance(root, dict) and root.get("pageKind") == _PAGE_KIND
