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
# 한 owner task 가 등록할 수 있는 universe 엔티티 상한. state 에 목록 대신 개수만
# 담으므로 복원 시 이 상한으로 비정상 값을 차단한다. 현재 최대 시장은 US 약 7,700 이다.
_MAX_UNIVERSE_ENTITIES = 100_000
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
    # `entities` 는 continuation state 에 저장하지 않는다. universe membership 에서
    # 결정적으로 도출되고 `membershipDigest`, `descriptor`, `ownerCodePin` 세 pin 이
    # 도출 동일성을 보장하기 때문이다. 저장하면 엔티티 수에 비례해 state 가 커져
    # 두 시장 혼합 등록이 state 예산을 넘긴다. resume 은 `_hydrateTask` 가 채운다.
    entities: tuple[_EntityRef, ...]
    entityCount: int = -1
    cursor: int = 0
    succeededEntities: int = 0
    failedEntities: int = 0
    failedSample: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """엔티티 개수를 목록에서 도출한다. 명시값이 있으면 그대로 둔다."""

        if self.entityCount < 0:
            object.__setattr__(self, "entityCount", len(self.entities))


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
