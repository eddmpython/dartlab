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

__all__ = [
    "BoundedBatchReader",
    "IntegrityMode",
    "ResourceManifest",
    "ResourcePredicate",
    "ResourceReadReceipt",
    "ResourceReadRequest",
    "ResourceShard",
    "canonicalJsonBytes",
    "loadResourceManifest",
    "openResourceBatchReader",
    "validateManifestSources",
]
