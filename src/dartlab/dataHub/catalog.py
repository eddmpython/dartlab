"""Unified Data Workbench metadata control plane."""

from __future__ import annotations

from dartlab.dataHub.contracts import CatalogQuery, Coverage, DataAssetDescriptor, DataCatalogResult
from dartlab.dataHub.discovery import catalogSnapshotId, discoverAssets


def _matches(asset: DataAssetDescriptor, query: CatalogQuery) -> bool:
    if query.layers and asset.layer not in query.layers:
        return False
    if query.owners and asset.owner not in query.owners:
        return False
    if query.kinds and asset.kind not in query.kinds:
        return False
    if asset.hidden and not query.includeHidden:
        return False
    if asset.layer not in {"L1", "L1.5", "L2"} and not query.includeOutOfScope:
        return False
    if query.search:
        needle = query.search.casefold()
        haystack = f"{asset.assetId} {asset.label} {asset.description}".casefold()
        if needle not in haystack:
            return False
    return True


def buildCatalog(query: CatalogQuery | None = None) -> DataCatalogResult:
    """Owner descriptor, registry, resource, concept를 metadata-only catalog로 합친다.

    Capabilities:
        L1, L1.5, L2 owner provider를 자동 발견하고 registry axis, DATA_RELEASES, extraction
        concept, Company surface를 stable asset ID로 정규화한다. 값 실행과 network fetch는 하지 않는다.

    Args:
        query: layer, owner, kind, text, hidden filter. None이면 in-scope 전체.

    Returns:
        DataCatalogResult. discovery 오류는 gaps에 보존하고 systemic gap이면 status가 failed다.

    Raises:
        없음. provider 오류는 machine-readable gap으로 반환한다.
    """
    active = query or CatalogQuery()
    allAssets, gaps = discoverAssets()
    selected = tuple(asset for asset in allAssets if _matches(asset, active))
    systemic = any(gap.systemic for gap in gaps)
    coverage = Coverage(len(allAssets), len(selected), 0, len(gaps))
    return DataCatalogResult(
        status="failed" if systemic else "ok",
        assets=selected,
        snapshotId=catalogSnapshotId(allAssets),
        coverage=coverage,
        gaps=gaps,
    )
