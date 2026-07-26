"""Resource page를 DataResult로 투영하는 계층.

형제 lane 인 `ownerPaging*` 과 `compositePaging*` 은 이미 같은 역할로 나뉘어 있다.
이 lane 만 한 파일에 전부 갖고 있어 파일 크기 룰의 800 줄 상한을 넘겼다.
의존 방향은 models, state, payload, source, schedule, results 순 단방향이다.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl

from dartlab.dataHub.contentSeal import resultSnapshotId
from dartlab.dataHub.continuation import (
    ContinuationError,
    canonicalDigest,
)
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataGap,
    DataPartition,
    DataQuery,
    DataResult,
    QualityAssertion,
    UniverseCoverage,
)

from .resourcePagingModels import (
    _MultiplexEntry,
    _ResourceSession,
)
from .resourcePagingPayload import (
    _decodeMultiplex,
)
from .resourcePagingSchedule import (
    _progressSelector,
    _progressValues,
)
from .resourcePagingState import (
    _originCursor,
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
