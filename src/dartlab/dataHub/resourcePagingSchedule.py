"""Resource page 실현과 진행 상태 계산.

형제 lane 인 `ownerPaging*` 과 `compositePaging*` 은 이미 같은 역할로 나뉘어 있다.
이 lane 만 한 파일에 전부 갖고 있어 파일 크기 룰의 800 줄 상한을 넘겼다.
의존 방향은 models, state, payload, source, schedule, results 순 단방향이다.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any

from dartlab.dataHub.continuation import (
    ContinuationError,
    ContinuationQueryState,
    PageEnvelope,
)
from dartlab.dataHub.pagingRuntime import (
    manifestCachePath,
    requireDeadline,
)

from .resourcePagingModels import (
    _MultiplexEntry,
    _OwnerBoundary,
    _ResourceTask,
)
from .resourcePagingPayload import (
    _encodeMultiplex,
)
from .resourcePagingSource import (
    _validateOwnerPage,
)
from .resourcePagingState import (
    _cursorMapping,
    _decodeSession,
    _encodeSession,
    _validateQueryPayload,
)


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
    requireDeadline(deadline)
    _validateQueryPayload(state.queryPayload)
    session = _decodeSession(state.cursorPayload)
    requireDeadline(deadline)
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
        requireDeadline(deadline)
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
                manifestCachePath(task.assetId, task.category),
            )
        requireDeadline(deadline)
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
    requireDeadline(deadline)
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
        requireDeadline(deadline)
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
