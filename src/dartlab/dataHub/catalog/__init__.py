"""Asset 발견과 universe 해소 계층.

owner 가 선언한 metadata provider 를 훑어 descriptor 를 만들고, 시장별 상장 universe 를
local-only snapshot 에서 해소한다. 값은 물질화하지 않는다.
"""

from __future__ import annotations

from dartlab.dataHub.catalog.assets import buildCatalog
from dartlab.dataHub.catalog.discovery import (
    catalogSnapshotId,
    discoverAssets,
    discoverOwnerProviders,
)
from dartlab.dataHub.catalog.universe import (
    ResolvedMarket,
    ResolvedUniverse,
    entityIds,
    resolveUniverse,
)

__all__ = [
    "ResolvedMarket",
    "ResolvedUniverse",
    "buildCatalog",
    "catalogSnapshotId",
    "discoverAssets",
    "discoverOwnerProviders",
    "entityIds",
    "resolveUniverse",
]
