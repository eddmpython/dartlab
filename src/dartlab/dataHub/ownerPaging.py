"""계산형 owner subject fanout의 호환 파사드.

State, source pin, Arrow payload, entity 실행, scheduler, result, API 책임은
각 전용 모듈이 소유한다. 기존 import와 private test seam은 이곳에 유지한다.
"""

from __future__ import annotations

from dartlab.dataHub.catalog.universe import resolveUniverse
from dartlab.dataHub.continuation import ContinuationError, canonicalDigest, inspectArrowIpcPayload
from dartlab.dataHub.ownerPagingApi import (
    _plannedTask,
    executeInitialOwnerPaging,
    isPageableOwner,
    resumeOwnerPaging,
)
from dartlab.dataHub.ownerPagingEntity import (
    _entityParamMap,
    _executeEntity,
    _failureEntry,
    _prepareEntitySources,
    _requestRef,
    _sourcePayloadParams,
)
from dartlab.dataHub.ownerPagingModels import (
    _DIGEST_RE,
    _FORMAT_VERSION,
    _MAX_ENTITY_PARAMS,
    _MAX_PAGE_ENTITIES,
    _OUTER_METADATA,
    _OUTER_SCHEMA,
    _PAGE_KIND,
    _DecodedPage,
    _EntityRef,
    _OwnerEntry,
    _OwnerSession,
    _OwnerTask,
    _VerifiedEntitySource,
)
from dartlab.dataHub.ownerPagingPayload import (
    _continuationStore,
    _decodePage,
    _encodePage,
    _entryClaim,
    _framePayload,
    _innerTable,
    _validateOwnerPayload,
)
from dartlab.dataHub.ownerPagingResults import (
    _failedResult,
    _planFailure,
    _progressSelector,
    _resultFromPage,
    _universeCoverage,
)
from dartlab.dataHub.ownerPagingSchedule import (
    _boundedEntries,
    _candidates,
    _executionWindows,
    _materialize,
    _nextTaskIndex,
    _requireDecodedPage,
    _requireTaskContracts,
    _requireTaskSources,
    _runOwnerPageProcess,
    _updatedTasks,
)
from dartlab.dataHub.ownerPagingSource import (
    _contractDigest,
    _currentTaskSourcePin,
    _entities,
    _pins,
    _requireCurrentPins,
    _resourceSourcePin,
    _sourcePin,
)
from dartlab.dataHub.ownerPagingState import (
    _callablePinValue,
    _codePinTree,
    _decodeDescriptor,
    _decodeEntity,
    _decodeProcessSession,
    _decodeQuery,
    _decodeSelection,
    _decodeSession,
    _decodeTask,
    _descriptorTree,
    _encodeProcessSession,
    _encodeSession,
    _jsonLoad,
    _ownerCodePin,
    _queryPayload,
    _queryTree,
    _requestedMeasures,
    _requireDigest,
    _requireOptionalText,
    _requireText,
    _selectionTree,
    _strictTree,
    _taskTree,
    _validateQueryPayload,
    isOwnerPagingState,
)
from dartlab.dataHub.pagingRuntime import requireDeadline

__all__ = [
    "executeInitialOwnerPaging",
    "isOwnerPagingState",
    "isPageableOwner",
    "resumeOwnerPaging",
]
