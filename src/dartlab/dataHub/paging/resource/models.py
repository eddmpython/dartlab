"""Resource multiplex의 값 타입, 스키마, 키 집합.

형제 lane 인 `ownerPaging*` 과 `compositePaging*` 은 이미 같은 역할로 나뉘어 있다.
이 lane 만 한 파일에 전부 갖고 있어 파일 크기 룰의 800 줄 상한을 넘겼다.
의존 방향은 models, state, payload, source, schedule, results 순 단방향이다.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import pyarrow as pa

from dartlab.dataHub.continuation import (
    ArrowPayloadFacts,
)

_MAX_PAGE_SHARDS = 64

_FORMAT_VERSION = 2

_OWNER_MODULE = "dartlab.providers.resourceStream.workbench"

_OWNER_CONTRACTS_MODULE = "dartlab.providers.resourceStream.contracts"

_MULTIPLEX_METADATA = {b"dartlab.dataHub.resource-multiplex": b"v2"}

_MULTIPLEX_SCHEMA = pa.schema(
    [
        pa.field("requestId", pa.string(), nullable=False),
        pa.field("assetId", pa.string(), nullable=False),
        pa.field("assetVersionId", pa.string(), nullable=False),
        pa.field("sourcePin", pa.string(), nullable=False),
        pa.field("queryPin", pa.string(), nullable=False),
        pa.field("startCursor", pa.binary(), nullable=False),
        pa.field("nextCursor", pa.binary(), nullable=True),
        pa.field("scannedShardCount", pa.int64(), nullable=False),
        pa.field("startRow", pa.int64(), nullable=False),
        pa.field("nextRow", pa.int64(), nullable=False),
        pa.field("done", pa.bool_(), nullable=False),
        pa.field("innerPayload", pa.binary(), nullable=False),
        pa.field("innerRowCount", pa.int64(), nullable=False),
        pa.field("innerEncodedByteCount", pa.int64(), nullable=False),
        pa.field("innerLogicalByteCount", pa.int64(), nullable=False),
        pa.field("innerSchemaDigest", pa.string(), nullable=False),
        pa.field("innerPayloadDigest", pa.string(), nullable=False),
    ],
    metadata=_MULTIPLEX_METADATA,
)


@dataclass(frozen=True, slots=True)
class _OwnerBoundary:
    describe: Callable[..., Any]
    read: Callable[..., Any]
    requestType: Any
    prepare: Callable[..., Any] | None = None


@dataclass(frozen=True, slots=True)
class _ResourceTask:
    requestId: str
    assetId: str
    assetVersionId: str
    category: str
    sourceRef: str
    sourcePin: str
    queryPin: str
    ownerSourcePin: str
    ownerQueryPin: str
    requestMapping: Mapping[str, Any]
    sourceShardCount: int
    selectedShardCount: int
    executionMode: str
    provider: str
    market: str
    startRow: int = 0
    cursor: Mapping[str, int] | None = None
    done: bool = False


@dataclass(frozen=True, slots=True)
class _ResourceSession:
    snapshotId: str
    contractHash: str
    requestedAssets: int
    pageMaxRows: int
    pageMaxBytes: int
    pageMaxLogicalBytes: int
    pageMaxShards: int
    pageTimeoutMs: int
    tasks: tuple[_ResourceTask, ...]


@dataclass(frozen=True, slots=True)
class _MultiplexEntry:
    requestId: str
    assetId: str
    assetVersionId: str
    sourcePin: str
    queryPin: str
    startCursor: Mapping[str, int]
    nextCursor: Mapping[str, int] | None
    scannedShardCount: int
    startRow: int
    nextRow: int
    done: bool
    payload: bytes


@dataclass(frozen=True, slots=True)
class _DecodedMultiplex:
    facts: ArrowPayloadFacts
    entries: tuple[_MultiplexEntry, ...]
    tables: tuple[pa.Table, ...]


_TASK_KEYS = frozenset(
    {
        "requestId",
        "assetId",
        "assetVersionId",
        "category",
        "sourceRef",
        "sourcePin",
        "queryPin",
        "ownerSourcePin",
        "ownerQueryPin",
        "requestMapping",
        "sourceShardCount",
        "selectedShardCount",
        "executionMode",
        "provider",
        "market",
        "startRow",
        "cursor",
        "done",
    }
)

_SESSION_KEYS = frozenset(
    {
        "version",
        "snapshotId",
        "contractHash",
        "requestedAssets",
        "pageMaxRows",
        "pageMaxBytes",
        "pageMaxLogicalBytes",
        "pageMaxShards",
        "pageTimeoutMs",
        "tasks",
    }
)

_REQUEST_MAPPING_KEYS = frozenset({"columns", "predicates", "companyIds", "includeSourcePath", "allowRawContent"})

_PAGEABLE_PARAM_KEYS = _REQUEST_MAPPING_KEYS

_CURSOR_KEYS = frozenset({"version", "shardOrdinal", "physicalRowInShard"})


def _textDigest(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("owner pin이 비었습니다")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
