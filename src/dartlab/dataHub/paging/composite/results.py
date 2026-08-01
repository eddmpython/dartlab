"""Composite child 결과의 request-order DataResult 조립."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.dataHub.continuation import ContinuationError, canonicalDigest
from dartlab.dataHub.contracts import AssetRef, Coverage, DataGap, DataResult
from dartlab.dataHub.identity.contentSeal import resultSnapshotId
from dartlab.dataHub.paging.composite.models import _AdapterProtocol
from dartlab.dataHub.paging.composite.payload import _decodeComposite


def _resultFromComposite(
    session: Mapping[str, Any],
    page: Any,
    adapters: _AdapterProtocol,
) -> DataResult:
    decoded = _decodeComposite(
        page.payload,
        claimedRowCount=page.rowCount,
        maxPageBytes=session["pageMaxBytes"],
        maxLogicalBytes=session["pageMaxBytes"],
    )
    lanes = session["lanes"]
    if not isinstance(lanes, list):
        raise ContinuationError("CONTINUATION_CORRUPT")
    byRequest = {str(lane["requestId"]): lane for lane in lanes}
    childResults: list[tuple[int, DataResult]] = []
    for row in decoded.rows:
        lane = byRequest.get(row["requestId"])
        if (
            lane is None
            or lane["done"]
            or row["requestIndex"] != lane["requestIndex"]
            or row["laneKind"] != lane["laneKind"]
            or row["layer"] != lane["layer"]
            or row["childSchemaDigest"] != lane["schemaDigest"]
            or row["startStateDigest"] != canonicalDigest(lane["privateState"])
        ):
            raise ContinuationError("CONTINUATION_CORRUPT")
        result = adapters.result(lane, row, pageRef=page.pageRef)
        if result.continuation is not None:
            raise ContinuationError("CONTINUATION_CORRUPT")
        childResults.append((row["requestIndex"], result))
    childResults.sort(key=lambda item: item[0])
    partitions = tuple(partition for _requestIndex, result in childResults for partition in result.partitions)
    currentGaps = tuple(gap for _requestIndex, result in childResults for gap in result.gaps)
    historicalGaps = tuple(
        DataGap(
            str(code),
            f"이전 composite page에서 {count}회 발생했습니다",
            str(lane["assetId"]),
            requestId=str(lane["requestId"]),
        )
        for lane in lanes
        for code, count in sorted(lane["gapCounts"].items())
    )
    gaps = historicalGaps + currentGaps
    assets = tuple(dict.fromkeys(AssetRef(str(lane["assetId"]), str(lane["assetVersionId"])) for lane in lanes))
    lineageRefs = tuple(dict.fromkeys(ref for partition in partitions for ref in partition.lineageRefs))
    receipts = tuple(
        dict.fromkeys(
            (
                page.pageRef,
                *(receipt for _requestIndex, result in childResults for receipt in result.executionReceipts),
            )
        )
    )
    coverageRows = tuple(row for _requestIndex, result in childResults for row in result.universeCoverage)
    universeSnapshots = tuple(
        sorted(
            {
                result.universeSnapshotId
                for _requestIndex, result in childResults
                if result.universeSnapshotId is not None
            }
        )
    )
    if len(universeSnapshots) == 1:
        universeSnapshotId = universeSnapshots[0]
    elif universeSnapshots:
        universeSnapshotId = "universe-query:" + canonicalDigest(universeSnapshots)
    else:
        universeSnapshotId = None
    cumulativeSucceededPartitions = sum(int(lane["succeededPartitions"]) for lane in lanes) + sum(
        int(row["succeededPartitions"]) for row in decoded.rows
    )
    cumulativeFailedItems = sum(int(lane["failedItems"]) for lane in lanes) + sum(
        int(row["failedItems"]) for row in decoded.rows
    )
    if page.nextToken is not None:
        status = "partial"
    elif cumulativeSucceededPartitions == 0 and cumulativeFailedItems:
        status = "failed"
    elif cumulativeFailedItems:
        status = "partial"
    else:
        status = "ok"
    dataSnapshotId = resultSnapshotId(
        catalogSnapshotId=session["snapshotId"],
        contractHash=session["contractHash"],
        partitions=partitions,
        universeSnapshotId=universeSnapshotId,
    )
    return DataResult(
        status=status,
        partitions=partitions,
        assets=assets,
        snapshotId=session["snapshotId"],
        contractHash=session["contractHash"],
        coverage=Coverage(
            session["requestedAssets"],
            session["resolvedAssets"],
            cumulativeSucceededPartitions,
            cumulativeFailedItems,
        ),
        gaps=gaps,
        lineageRefs=lineageRefs,
        executionReceipts=receipts,
        continuation=page.nextToken,
        qualityAssertions=tuple(assertion for partition in partitions for assertion in partition.qualityAssertions),
        universeSnapshotId=universeSnapshotId,
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
