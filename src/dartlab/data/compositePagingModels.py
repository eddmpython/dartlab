"""Composite paging의 immutable schema와 내부 계약 type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

import pyarrow as pa

from dartlab.data.continuation import ArrowPayloadFacts, ContinuationPins
from dartlab.data.contracts import DataAssetDescriptor, DataQuery, DataResult
from dartlab.data.pagingRuntime import MAX_STATE_BYTES

_FORMAT_VERSION = 1
_PAGE_KIND = "composite"
_MIN_CHILD_BYTES = 4096
_CONTROL_BASE_BYTES = 8192
_CONTROL_PER_LANE_BYTES = 2048
_MAX_LANES = 32
_DIGEST_LENGTH = 64
_LOWER_SESSION_ENCODING = "zlib-base64-v1"
_MAX_PACKED_SESSION_BYTES = MAX_STATE_BYTES
_COMPOSITE_METADATA = {b"dartlab.data.composite-page": b"v1"}
_COMPOSITE_SCHEMA = pa.schema(
    [
        pa.field("requestIndex", pa.int32(), nullable=False),
        pa.field("requestId", pa.string(), nullable=False),
        pa.field("layer", pa.string(), nullable=False),
        pa.field("laneKind", pa.string(), nullable=False),
        pa.field("startStateDigest", pa.string(), nullable=False),
        pa.field("nextStateDigest", pa.string(), nullable=True),
        pa.field("done", pa.bool_(), nullable=False),
        pa.field("attempted", pa.int64(), nullable=False),
        pa.field("succeededRows", pa.int64(), nullable=False),
        pa.field("succeededPartitions", pa.int64(), nullable=False),
        pa.field("failedItems", pa.int64(), nullable=False),
        pa.field("gapCodes", pa.list_(pa.string()), nullable=False),
        pa.field("childMaxRows", pa.int64(), nullable=False),
        pa.field("childMaxBytes", pa.int64(), nullable=False),
        pa.field("childMaxConcurrency", pa.int64(), nullable=False),
        pa.field("childPayload", pa.binary(), nullable=False),
        pa.field("childClaimedRows", pa.int64(), nullable=False),
        pa.field("childSchemaDigest", pa.string(), nullable=False),
        pa.field("childPayloadDigest", pa.string(), nullable=False),
    ],
    metadata=_COMPOSITE_METADATA,
)
_EAGER_METADATA = {b"dartlab.data.composite-eager": b"v1"}
_EAGER_SCHEMA = pa.schema(
    [
        pa.field("resultMetadata", pa.binary(), nullable=False),
        pa.field("partitionMetadata", pa.list_(pa.binary()), nullable=False),
        pa.field("dataKinds", pa.list_(pa.string()), nullable=False),
        pa.field("dataPayloads", pa.list_(pa.binary()), nullable=False),
    ],
    metadata=_EAGER_METADATA,
)


@dataclass(frozen=True, slots=True)
class _LaneAllocation:
    """한 outer round에서 lane 하나가 소비할 상한."""

    maxRows: int
    maxBytes: int
    maxConcurrency: int


@dataclass(frozen=True, slots=True)
class _LanePage:
    """Child token 없이 outer page에 봉인할 lane 결과."""

    payload: bytes
    claimedRows: int
    schemaDigest: str
    nextPrivateState: Mapping[str, Any] | None
    attempted: int
    succeededRows: int
    succeededPartitions: int
    failedItems: int
    gapCodes: tuple[str, ...]
    done: bool


@dataclass(frozen=True, slots=True)
class _DecodedComposite:
    """검증된 outer Arrow page와 schedule rows."""

    facts: ArrowPayloadFacts
    rows: tuple[dict[str, Any], ...]


class _AdapterProtocol(Protocol):
    """Production adapter와 private test adapter가 공유하는 내부 계약."""

    def plan(
        self,
        requestId: str,
        requestIndex: int,
        descriptor: DataAssetDescriptor,
        query: DataQuery,
        *,
        snapshotId: str,
        contractHash: str,
        deadline: float,
    ) -> Mapping[str, Any]:
        """요청 하나를 고정된 lower lane 계획으로 변환한다."""
        ...

    def validate(self, lane: Mapping[str, Any], *, deadline: float) -> Any:
        """실행 직전 lower lane의 pin과 source를 검증한다."""
        ...

    def materialize(
        self,
        lane: Mapping[str, Any],
        allocation: _LaneAllocation,
        *,
        deadline: float,
        validation: Any,
    ) -> _LanePage:
        """할당된 예산 안에서 lower lane 한 page를 만든다."""
        ...

    def result(
        self,
        lane: Mapping[str, Any],
        row: Mapping[str, Any],
        *,
        pageRef: str,
    ) -> DataResult:
        """저장된 lower lane 행을 공개 DataResult로 복원한다."""
        ...


@dataclass(frozen=True, slots=True)
class CompositePagingPlan:
    """Owner 실행 전 exact source와 contract가 고정된 composite plan."""

    session: Mapping[str, Any]
    queryPayload: bytes = field(repr=False)
    pins: ContinuationPins
    adapters: _AdapterProtocol = field(repr=False, compare=False)
