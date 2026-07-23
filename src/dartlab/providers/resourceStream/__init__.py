"""Provider-owned pageable parquet resource reader."""

from .contracts import (
    IntegrityMode,
    ResourceCursorV2,
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
    ResourceReadSession,
    describeResource,
    prepareResourceRead,
    readResourcePage,
)

__all__ = [
    "BoundedBatchReader",
    "IntegrityMode",
    "ResourceCursorV2",
    "ResourceManifest",
    "ResourceDescription",
    "ResourcePage",
    "ResourceReadSession",
    "ResourcePredicate",
    "ResourceReadReceipt",
    "ResourceReadRequest",
    "ResourceShard",
    "canonicalJsonBytes",
    "describeResource",
    "loadResourceManifest",
    "openResourceBatchReader",
    "prepareResourceRead",
    "readResourcePage",
    "validateManifestSources",
]
