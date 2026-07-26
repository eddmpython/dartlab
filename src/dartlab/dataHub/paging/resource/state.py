"""Resource paging query와 session의 canonical state codec.

형제 lane 인 `ownerPaging*` 과 `compositePaging*` 은 이미 같은 역할로 나뉘어 있다.
이 lane 만 한 파일에 전부 갖고 있어 파일 크기 룰의 800 줄 상한을 넘겼다.
의존 방향은 models, state, payload, source, schedule, results 순 단방향이다.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.dataHub.continuation import (
    ContinuationError,
    canonicalJsonBytes,
)
from dartlab.dataHub.contracts import (
    DataQuery,
)
from dartlab.dataHub.paging.runtime import (
    MAX_PAGE_BYTES as _MAX_PAGE_BYTES,
)
from dartlab.dataHub.paging.runtime import (
    MAX_PAGE_ROWS as _MAX_PAGE_ROWS,
)
from dartlab.dataHub.paging.runtime import (
    MAX_STATE_BYTES as _MAX_STATE_BYTES,
)
from dartlab.dataHub.paging.stateCodec import requireDigest, requireText, strictTree

from .models import (
    _CURSOR_KEYS,
    _FORMAT_VERSION,
    _MAX_PAGE_SHARDS,
    _REQUEST_MAPPING_KEYS,
    _SESSION_KEYS,
    _TASK_KEYS,
    _ResourceSession,
    _ResourceTask,
    _textDigest,
)


def _strictTree(value: Any, *, seen: set[int] | None = None) -> Any:
    """resourcePaging state tree를 공유 codec으로 canonical 변환한다."""

    return strictTree(value, context="resource state", seen=seen)


_requireText = requireText

_requireDigest = requireDigest


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
