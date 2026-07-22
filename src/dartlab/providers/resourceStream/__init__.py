"""Provider-owned pageable parquet resource reader."""

from .contracts import (
    IntegrityMode,
    ResourceManifest,
    ResourcePredicate,
    ResourceReadReceipt,
    ResourceReadRequest,
    ResourceShard,
    canonicalJsonBytes,
)
from .manifest import loadResourceManifest, validateManifestSources
from .reader import BoundedBatchReader, openResourceBatchReader
from .workbench import (
    ResourceDescription,
    ResourcePage,
    describeResource,
    readResourcePage,
)

__all__ = [
    "BoundedBatchReader",
    "IntegrityMode",
    "ResourceManifest",
    "ResourceDescription",
    "ResourcePage",
    "ResourcePredicate",
    "ResourceReadReceipt",
    "ResourceReadRequest",
    "ResourceShard",
    "canonicalJsonBytes",
    "describeResource",
    "loadResourceManifest",
    "openResourceBatchReader",
    "readResourcePage",
    "validateManifestSources",
]
