"""원격 job의 logical query와 완료 DataResult를 결박하는 계약."""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Any

from dartlab.dataHub.catalog import buildCatalog
from dartlab.dataHub.contracts import AssetRef, DataQuery, DataResult
from dartlab.dataHub.execution import _resolveAgainstCatalog, _resolvedIdentity
from dartlab.dataHub.executionSupport import _compiledRequests
from dartlab.dataHub.identity.contentSeal import contentHash, resultSnapshotId
from dartlab.dataHub.materialization import MaterializationReceipt
from dartlab.dataHub.paging.composite import compositeQueryDigest
from dartlab.dataHub.projection.output import _rowCount, _schema

from .errors import DataHubControlError
from .queryContract import logicalQuery


def _digest(value: Any) -> str:
    if type(value) is not str or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("digest")
    return value


@dataclass(frozen=True, slots=True)
class ExpectedResultContract:
    """완료 시 다시 확인할 catalog, asset, query identity."""

    logicalQueryDigest: str
    catalogSnapshotId: str
    assets: tuple[AssetRef, ...]
    contractHash: str
    requestedAssets: int
    resolvedAssets: int

    def __post_init__(self) -> None:
        _digest(self.logicalQueryDigest)
        _digest(self.contractHash)
        if type(self.catalogSnapshotId) is not str or not self.catalogSnapshotId:
            raise ValueError("catalogSnapshotId")
        if type(self.requestedAssets) is not int or type(self.resolvedAssets) is not int:
            raise TypeError("asset counts")
        if not 0 <= self.resolvedAssets <= self.requestedAssets:
            raise ValueError("asset counts")

    def asTree(self) -> dict[str, Any]:
        """예상 결과 계약을 strict JSON tree로 변환한다."""

        return {
            "logicalQueryDigest": self.logicalQueryDigest,
            "catalogSnapshotId": self.catalogSnapshotId,
            "assets": [{"assetId": asset.assetId, "assetVersionId": asset.assetVersionId} for asset in self.assets],
            "contractHash": self.contractHash,
            "requestedAssets": self.requestedAssets,
            "resolvedAssets": self.resolvedAssets,
        }

    @classmethod
    def fromTree(cls, value: Any) -> ExpectedResultContract:
        """Strict JSON tree에서 예상 결과 계약을 복원한다."""

        expected = {
            "logicalQueryDigest",
            "catalogSnapshotId",
            "assets",
            "contractHash",
            "requestedAssets",
            "resolvedAssets",
        }
        if not isinstance(value, dict) or set(value) != expected or not isinstance(value["assets"], list):
            raise ValueError("expected result contract")
        assets = []
        for item in value["assets"]:
            if not isinstance(item, dict) or set(item) != {"assetId", "assetVersionId"}:
                raise ValueError("expected result assets")
            assets.append(AssetRef(**item))
        return cls(
            logicalQueryDigest=value["logicalQueryDigest"],
            catalogSnapshotId=value["catalogSnapshotId"],
            assets=tuple(assets),
            contractHash=value["contractHash"],
            requestedAssets=value["requestedAssets"],
            resolvedAssets=value["resolvedAssets"],
        )


def buildExpectedResultContract(query: DataQuery) -> ExpectedResultContract:
    """현재 catalog에서 canonical query의 예상 결과 identity를 만든다."""

    normalized = logicalQuery(query)
    try:
        requested = _compiledRequests((), normalized)
    except (TypeError, ValueError):
        raise DataHubControlError("DATA_HUB_INVALID") from None
    catalog = buildCatalog()
    resolved, _gaps = _resolveAgainstCatalog(requested, catalog)
    assets, contractHash = _resolvedIdentity(resolved, normalized)
    return ExpectedResultContract(
        logicalQueryDigest=compositeQueryDigest((), normalized),
        catalogSnapshotId=catalog.snapshotId,
        assets=assets,
        contractHash=contractHash,
        requestedAssets=len(requested),
        resolvedAssets=len(resolved),
    )


def verifyCompletionResult(result: DataResult, expected: ExpectedResultContract) -> None:
    """Decoded result가 자기 job의 exact expected contract와 일치하는지 검증한다."""

    if not isinstance(result, DataResult) or not isinstance(expected, ExpectedResultContract):
        raise DataHubControlError("DATA_HUB_RESULT_UNBOUND")
    if (
        result.snapshotId != expected.catalogSnapshotId
        or result.assets != expected.assets
        or not hmac.compare_digest(result.contractHash, expected.contractHash)
        or result.coverage.requestedAssets != expected.requestedAssets
        or result.coverage.resolvedAssets != expected.resolvedAssets
    ):
        raise DataHubControlError("DATA_HUB_RESULT_UNBOUND")
    if result.continuation is not None:
        raise DataHubControlError("DATA_HUB_RESULT_INCOMPLETE")
    if result.status not in {"ok", "partial", "failed"}:
        raise DataHubControlError("DATA_HUB_RESULT_UNBOUND")
    if any(partition.asset not in expected.assets for partition in result.partitions):
        raise DataHubControlError("DATA_HUB_RESULT_UNBOUND")
    for partition in result.partitions:
        actualHash = contentHash(partition.data)
        if (
            actualHash is None
            or partition.contentHash != actualHash
            or partition.rowCount != _rowCount(partition.data)
            or partition.schema != _schema(partition.data)
        ):
            raise DataHubControlError("DATA_HUB_RESULT_UNBOUND")
    actualSnapshot = resultSnapshotId(
        catalogSnapshotId=result.snapshotId,
        contractHash=result.contractHash,
        partitions=result.partitions,
        universeSnapshotId=result.universeSnapshotId,
    )
    if result.dataSnapshotId != actualSnapshot:
        raise DataHubControlError("DATA_HUB_RESULT_UNBOUND")
    if result.materializationReceipt is not None:
        try:
            receipt = MaterializationReceipt.fromTree(dict(result.materializationReceipt))
        except (TypeError, ValueError):
            raise DataHubControlError("DATA_HUB_RESULT_UNBOUND") from None
        if not hmac.compare_digest(receipt.pins.queryDigest, expected.logicalQueryDigest):
            raise DataHubControlError("DATA_HUB_RESULT_UNBOUND")


__all__ = [
    "ExpectedResultContract",
    "buildExpectedResultContract",
    "verifyCompletionResult",
]
