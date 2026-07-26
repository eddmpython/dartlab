"""Owner paging의 immutable schema와 session type."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pyarrow as pa

from dartlab.dataHub.continuation import ArrowPayloadFacts
from dartlab.dataHub.contracts import DataAssetDescriptor, DataQuery, UniverseSelection

_FORMAT_VERSION = 2
_PAGE_KIND = "owner-subject-fanout"
_MAX_PAGE_ENTITIES = 64
_MAX_ENTITY_PARAMS = 16
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_OUTER_METADATA = {b"dartlab.dataHub.owner-page": b"v1"}
_OUTER_SCHEMA = pa.schema(
    [
        pa.field("requestId", pa.string(), nullable=False),
        pa.field("assetId", pa.string(), nullable=False),
        pa.field("assetVersionId", pa.string(), nullable=False),
        pa.field("sourcePin", pa.string(), nullable=False),
        pa.field("queryPin", pa.string(), nullable=False),
        pa.field("entityOrdinal", pa.int64(), nullable=False),
        pa.field("entityId", pa.string(), nullable=False),
        pa.field("sourceEntityId", pa.string(), nullable=True),
        pa.field("status", pa.string(), nullable=False),
        pa.field("gapCodes", pa.list_(pa.string()), nullable=False),
        pa.field("gapMessages", pa.list_(pa.string()), nullable=False),
        pa.field("receiptRef", pa.string(), nullable=True),
        pa.field("contentHash", pa.string(), nullable=True),
        pa.field("temporalStatus", pa.string(), nullable=True),
        pa.field("innerPayload", pa.binary(), nullable=True),
        pa.field("innerRowCount", pa.int64(), nullable=False),
        pa.field("innerEncodedByteCount", pa.int64(), nullable=False),
        pa.field("innerLogicalByteCount", pa.int64(), nullable=False),
        pa.field("innerSchemaDigest", pa.string(), nullable=True),
        pa.field("innerPayloadDigest", pa.string(), nullable=True),
    ],
    metadata=_OUTER_METADATA,
)


@dataclass(frozen=True, slots=True)
class _EntityRef:
    entityId: str
    sourceEntityId: str | None
    params: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class _OwnerTask:
    requestId: str
    descriptor: DataAssetDescriptor
    query: DataQuery
    selection: UniverseSelection
    market: str
    provider: str
    universeSnapshotId: str
    membershipDigest: str
    sourceAssetId: str
    sourceCategory: str
    ownerSourcePin: str
    ownerCodePin: str
    sourcePin: str
    queryPin: str
    entities: tuple[_EntityRef, ...]
    cursor: int = 0
    succeededEntities: int = 0
    failedEntities: int = 0
    failedSample: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _OwnerSession:
    snapshotId: str
    contractHash: str
    requestedAssets: int
    universeSnapshotId: str
    pageMaxRows: int
    pageMaxBytes: int
    pageMaxLogicalBytes: int
    pageMaxEntities: int
    pageTimeoutMs: int
    maxConcurrency: int
    tasks: tuple[_OwnerTask, ...]
    nextTaskIndex: int = 0


@dataclass(frozen=True, slots=True)
class _OwnerEntry:
    requestId: str
    assetId: str
    assetVersionId: str
    sourcePin: str
    queryPin: str
    entityOrdinal: int
    entityId: str
    sourceEntityId: str | None
    status: str
    gapCodes: tuple[str, ...]
    gapMessages: tuple[str, ...]
    receiptRef: str | None = None
    contentHash: str | None = None
    temporalStatus: str | None = None
    payload: bytes | None = None


@dataclass(frozen=True, slots=True)
class _VerifiedEntitySource:
    payload: bytes
    integrityDigest: str


@dataclass(frozen=True, slots=True)
class _DecodedPage:
    facts: ArrowPayloadFacts
    entries: tuple[_OwnerEntry, ...]
    tables: tuple[pa.Table | None, ...]
