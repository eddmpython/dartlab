"""Owner outer page의 public DataResult와 universe coverage 조립."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import polars as pl

from dartlab.data.contentSeal import contentHash, resultSnapshotId
from dartlab.data.continuation import ContinuationError
from dartlab.data.contracts import (
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
from dartlab.data.ownerPagingModels import _OwnerSession, _OwnerTask
from dartlab.data.ownerPagingPayload import _decodePage
from dartlab.data.ownerPagingSchedule import _candidates, _requireDecodedPage, _updatedTasks


def _progressSelector(task: _OwnerTask) -> tuple[tuple[str, str], ...]:
    return (
        ("complete", str(task.cursor >= len(task.entities)).lower()),
        ("completedEntityCount", str(task.cursor)),
        ("failedEntityCount", str(task.failedEntities)),
        ("nextEntityOrdinal", str(task.cursor)),
        ("requestedEntityCount", str(len(task.entities))),
        ("succeededEntityCount", str(task.succeededEntities)),
    )


def _universeCoverage(tasks: Sequence[_OwnerTask]) -> tuple[UniverseCoverage, ...]:
    rows = []
    for task in tasks:
        complete = task.cursor >= len(task.entities)
        if complete and task.failedEntities == 0:
            status = "complete"
            gapCodes: tuple[str, ...] = ()
        elif complete and task.succeededEntities == 0:
            status = "failed"
            gapCodes = ("FEATURE_UNIVERSE_FAILED",)
        else:
            status = "partial"
            gapCodes = ("FEATURE_UNIVERSE_PARTIAL",) if complete else ("OWNER_ENTITY_SCAN_IN_PROGRESS",)
        rows.append(
            UniverseCoverage(
                requestId=task.requestId,
                assetId=task.descriptor.assetId,
                market=task.market,
                provider=task.provider,
                executionMode=task.descriptor.executionMode,
                snapshotId=task.universeSnapshotId,
                selector=_progressSelector(task),
                requestedEntities=len(task.entities),
                returnedEntities=task.succeededEntities,
                matchedEntities=task.succeededEntities,
                missingEntities=len(task.entities) - task.succeededEntities,
                extraEntities=0,
                status=status,
                missingSample=task.failedSample,
                gapCodes=gapCodes,
            )
        )
    return tuple(rows)


def _resultFromPage(session: _OwnerSession, page: Any) -> DataResult:
    decoded = _decodePage(
        page.payload,
        claimedRowCount=page.rowCount,
        maxPageRows=session.pageMaxRows,
        maxPageBytes=session.pageMaxBytes,
        maxLogicalBytes=session.pageMaxLogicalBytes,
    )
    _requireDecodedPage(session, _candidates(session), decoded)
    byRequest = {task.requestId: task for task in session.tasks}
    nextTasks = _updatedTasks(session, decoded.entries)
    complete = all(task.cursor >= len(task.entities) for task in nextTasks)
    if (page.nextToken is None) != complete:
        raise ContinuationError("CONTINUATION_CORRUPT")
    partitions: list[DataPartition] = []
    gaps: list[DataGap] = []
    receipts: list[str] = [page.pageRef]
    for entry, table in zip(decoded.entries, decoded.tables, strict=True):
        task = byRequest[entry.requestId]
        for code, message in zip(entry.gapCodes, entry.gapMessages, strict=True):
            gaps.append(
                DataGap(
                    code,
                    message,
                    task.descriptor.assetId,
                    entry.entityId,
                    requestId=task.requestId,
                )
            )
        if entry.status != "ok":
            continue
        if table is None or entry.contentHash is None or entry.receiptRef is None or entry.temporalStatus is None:
            raise ContinuationError("CONTINUATION_CORRUPT")
        frame = pl.from_arrow(table)
        semantic = (
            frame.drop("evidenceRef") if isinstance(frame, pl.DataFrame) and "evidenceRef" in frame.columns else frame
        )
        if not isinstance(frame, pl.DataFrame) or contentHash(semantic) != entry.contentHash:
            raise ContinuationError("CONTINUATION_CORRUPT")
        assertion = QualityAssertion(
            assertionId="contentSealed",
            success=True,
            severity="error",
            expected="verified feature content hash",
            observed=entry.contentHash,
            assetId=entry.assetId,
        )
        partitions.append(
            DataPartition(
                asset=AssetRef(entry.assetId, entry.assetVersionId),
                projectionKind="factor",
                data=frame,
                schema=tuple((name, str(dtype)) for name, dtype in frame.schema.items()),
                rowCount=frame.height,
                truncated=False,
                selector=(("market", task.market), ("subject", entry.entityId)),
                temporalStatus=entry.temporalStatus,
                lineageRefs=(task.descriptor.sourceRef, page.pageRef),
                requestId=entry.requestId,
                qualityAssertions=(assertion,),
                contentHash=entry.contentHash,
            )
        )
        receipts.append(entry.receiptRef)
    assets = tuple(
        dict.fromkeys(AssetRef(task.descriptor.assetId, task.descriptor.assetVersionId) for task in session.tasks)
    )
    lineageRefs = tuple(dict.fromkeys(ref for partition in partitions for ref in partition.lineageRefs))
    coverageRows = _universeCoverage(nextTasks)
    dataSnapshotId = resultSnapshotId(
        catalogSnapshotId=session.snapshotId,
        contractHash=session.contractHash,
        partitions=partitions,
        universeSnapshotId=session.universeSnapshotId,
    )
    status = (
        "partial"
        if page.nextToken is not None or gaps or any(row.status != "complete" for row in coverageRows)
        else "ok"
    )
    failedEntries = sum(entry.status == "failed" for entry in decoded.entries)
    return DataResult(
        status=status,
        partitions=tuple(partitions),
        assets=assets,
        snapshotId=session.snapshotId,
        contractHash=session.contractHash,
        coverage=Coverage(
            session.requestedAssets,
            len(session.tasks),
            len(partitions),
            failedEntries,
        ),
        gaps=tuple(gaps),
        lineageRefs=lineageRefs,
        executionReceipts=tuple(dict.fromkeys(receipts)),
        continuation=page.nextToken,
        qualityAssertions=tuple(assertion for partition in partitions for assertion in partition.qualityAssertions),
        universeSnapshotId=session.universeSnapshotId,
        universeCoverage=coverageRows,
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
