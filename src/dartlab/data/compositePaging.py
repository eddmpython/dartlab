"""Mixed Data Workbench request를 단일 continuation chain으로 스케줄한다.

구현 책임은 state, payload, adapter, scheduler, result, API 모듈로 분리한다.
이 모듈은 기존 공개 import와 private test seam을 보존하는 호환 파사드다.
"""

from __future__ import annotations

from dartlab.data.compositePagingAdapters import _ProductionAdapters
from dartlab.data.compositePagingApi import (
    compositeMaterializationIdentity,
    executeInitialCompositePaging,
    executePreparedCompositePaging,
    prepareCompositePaging,
    resumeCompositePaging,
)
from dartlab.data.compositePagingModels import (
    _COMPOSITE_METADATA,
    _COMPOSITE_SCHEMA,
    _CONTROL_BASE_BYTES,
    _CONTROL_PER_LANE_BYTES,
    _DIGEST_LENGTH,
    _EAGER_METADATA,
    _EAGER_SCHEMA,
    _FORMAT_VERSION,
    _LOWER_SESSION_ENCODING,
    _MAX_LANES,
    _MAX_PACKED_SESSION_BYTES,
    _MIN_CHILD_BYTES,
    _PAGE_KIND,
    CompositePagingPlan,
    _AdapterProtocol,
    _DecodedComposite,
    _LaneAllocation,
    _LanePage,
)
from dartlab.data.compositePagingPayload import (
    _arrowPayload,
    _assertionTree,
    _decodeAssertion,
    _decodeAsset,
    _decodeComposite,
    _decodeEagerResult,
    _decodeGap,
    _decodeLineage,
    _decodePartition,
    _decodePartitionData,
    _decodeUniverseCoverage,
    _encodeCompositeRows,
    _encodeEagerResult,
    _lineageTree,
    _partitionData,
    _partitionMetadata,
    _readArrowTable,
    _readArrowTableAny,
    _resultMetadata,
    _validateCompositePayload,
    compositeQueryDigest,
    decodeMaterializationPage,
    encodeMaterializationPage,
    materializationPageSchemaDigest,
)
from dartlab.data.compositePagingResults import _failedResult, _resultFromComposite
from dartlab.data.compositePagingSchedule import (
    _allocations,
    _materializeComposite,
    _outerPins,
    _selectLaneIndexes,
    _updatedSession,
)
from dartlab.data.compositePagingState import (
    _decodeLane,
    _decodePins,
    _decodeQuery,
    _decodeSession,
    _descriptorCodec,
    _encodeSession,
    _isSafeEagerLane,
    _jsonLoad,
    _lanePins,
    _laneTree,
    _packLowerSession,
    _pinsTree,
    _queryPayload,
    _queryTree,
    _requireDigest,
    _requireText,
    _samePins,
    _strictTree,
    _unpackLowerSession,
    _validateQueryPayload,
    isCompositePagingState,
)

__all__ = [
    "CompositePagingPlan",
    "compositeMaterializationIdentity",
    "compositeQueryDigest",
    "decodeMaterializationPage",
    "encodeMaterializationPage",
    "executeInitialCompositePaging",
    "executePreparedCompositePaging",
    "isCompositePagingState",
    "materializationPageSchemaDigest",
    "prepareCompositePaging",
    "resumeCompositePaging",
]
