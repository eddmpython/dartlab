"""Resource multiplex paging 의 공개 진입점.

첫 page 발급과 continuation 재개 두 함수만 둔다. 계약 세부는 형제 모듈이 소유한다.
"""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import importlib
import json
import math
import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow as pa

from dartlab.dataHub.continuation import (
    ArrowPayloadFacts,
    ContinuationError,
    ContinuationPins,
    ContinuationQueryState,
    ContinuationStore,
    PageEnvelope,
    arrowSchemaDigest,
    bytesDigest,
    canonicalDigest,
    canonicalJsonBytes,
    inspectArrowIpcPayload,
)
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataGap,
    DataPartition,
    DataQuery,
    DataResult,
    NativeProjection,
    QualityAssertion,
    UniverseCoverage,
)
from dartlab.dataHub.identity.contentSeal import resultSnapshotId
from dartlab.dataHub.paging.runtime import (
    MAX_PAGE_BYTES as _MAX_PAGE_BYTES,
)
from dartlab.dataHub.paging.runtime import (
    MAX_PAGE_ROWS as _MAX_PAGE_ROWS,
)
from dartlab.dataHub.paging.runtime import (
    MAX_STATE_BYTES as _MAX_STATE_BYTES,
)
from dartlab.dataHub.paging.runtime import (
    continuationStore,
    dataHubRoot,
    manifestCachePath,
    requireDeadline,
)
from dartlab.dataHub.paging.stateCodec import requireDigest, requireText, strictTree
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

from .models import (
    _CURSOR_KEYS,
    _FORMAT_VERSION,
    _MAX_PAGE_SHARDS,
    _MULTIPLEX_METADATA,
    _MULTIPLEX_SCHEMA,
    _OWNER_CONTRACTS_MODULE,
    _OWNER_MODULE,
    _PAGEABLE_PARAM_KEYS,
    _REQUEST_MAPPING_KEYS,
    _SESSION_KEYS,
    _TASK_KEYS,
    _DecodedMultiplex,
    _MultiplexEntry,
    _OwnerBoundary,
    _ResourceSession,
    _ResourceTask,
    _textDigest,
)
from .payload import (
    _decodeMultiplex,
    _encodeMultiplex,
    _innerTable,
    _validateMultiplexPayload,
)
from .results import (
    _failedResult,
    _planFailure,
    _resultFromPage,
    _universeCoverage,
)
from .schedule import (
    _materialize,
    _materializeOnce,
    _progressSelector,
    _progressValues,
)
from .source import (
    _continuationStore,
    _contractDigest,
    _currentSourcePins,
    _descriptionTask,
    _normalizedRequestMapping,
    _ownerBoundary,
    _pins,
    _preparedDescriptionTask,
    _requireCurrentPins,
    _validateOwnerPage,
    isPageableResource,
)
from .state import (
    _cursorBytes,
    _cursorFromBytes,
    _cursorMapping,
    _cursorPosition,
    _decodeSession,
    _decodeTask,
    _decodeTaskCursor,
    _encodeSession,
    _jsonLoad,
    _originCursor,
    _queryPayload,
    _requireDigest,
    _requireText,
    _strictTree,
    _taskTree,
    _validateQueryPayload,
)

_log = dataHubLogger(__name__)


def executeInitialResourcePaging(
    assetIds: Sequence[str],
    query: DataQuery,
    *,
    requestedAssets: int,
    snapshotId: str,
    contractHash: str,
    resolved: Sequence[tuple[str, DataAssetDescriptor, DataQuery]],
    hasPlanningGaps: bool,
    deadline: float,
) -> DataResult:
    """첫 full-universe resource page를 발급하고 즉시 같은 store에서 redeem한다."""

    try:
        requireDeadline(deadline)
    except ContinuationError as error:
        return _failedResult(
            error.code,
            str(error),
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=tuple(
                AssetRef(descriptor.assetId, descriptor.assetVersionId) for _requestId, descriptor, _active in resolved
            ),
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
        )
    if any(not isPageableResource(descriptor, active) for _requestId, descriptor, active in resolved):
        return _planFailure(
            "PAGEABLE_MIXED_EXECUTION_UNSUPPORTED",
            "pageable resource와 eager asset은 한 query에서 함께 실행할 수 없습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if query.completeness == "requireComplete":
        return _planFailure(
            "PAGEABLE_REQUIRE_COMPLETE_UNSUPPORTED",
            "pageable resource query는 requireComplete를 지원하지 않습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if hasPlanningGaps or not resolved:
        return _planFailure(
            "PAGEABLE_PLAN_INCOMPLETE",
            "pageable resource query 계획을 완전하게 고정할 수 없습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if any(
        active.universe is not None or active.time is not None or active.measures for _rid, _desc, active in resolved
    ):
        return _planFailure(
            "PAGEABLE_SELECTOR_UNSUPPORTED",
            "pageable resource query는 columns, predicates, companyIds만 지원합니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if query.budget.maxRows < len(resolved):
        return _planFailure(
            "PAGEABLE_ROW_BUDGET_TOO_SMALL",
            "첫 page에 모든 resource를 포함할 row budget이 부족합니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    try:
        requireDeadline(deadline)
        boundary = _ownerBoundary()
        preparedTasks = tuple(
            _preparedDescriptionTask(boundary, requestId, descriptor, active)
            for requestId, descriptor, active in resolved
        )
        tasks = tuple(task for task, _prepared in preparedTasks)
        preparedReads = {task.requestId: prepared for task, prepared in preparedTasks if prepared is not None}
        requireDeadline(deadline)
        session = _ResourceSession(
            snapshotId=snapshotId,
            contractHash=contractHash,
            requestedAssets=requestedAssets,
            pageMaxRows=min(query.budget.maxRows, _MAX_PAGE_ROWS),
            pageMaxBytes=min(query.budget.maxBytes, _MAX_PAGE_BYTES),
            pageMaxLogicalBytes=min(query.budget.maxBytes, _MAX_PAGE_BYTES),
            pageMaxShards=_MAX_PAGE_SHARDS,
            pageTimeoutMs=query.budget.timeoutMs,
            tasks=tasks,
        )
        queryPayload = _queryPayload(assetIds, query)
        state = ContinuationQueryState(queryPayload, _encodeSession(session))
        sourcePins = {task.requestId: task.sourcePin for task in tasks}
        pins = _pins(session, queryPayload, sourcePins)
        issueStore = _continuationStore(deadline=deadline)
        issued = issueStore.issue(state, pins)
        requireDeadline(deadline)
        redeemStore = _continuationStore(deadline=deadline, runMaintenance=False)
        page = redeemStore.redeem(
            issued.token,
            pins,
            materialize=lambda current: _materialize(
                current,
                boundary,
                deadline=deadline,
                preparedReads=preparedReads,
            ),
            waitSeconds=requireDeadline(deadline),
        )
        requireDeadline(deadline)
        result = _resultFromPage(session, page)
        requireDeadline(deadline)
        return result
    except ContinuationError as error:
        return _failedResult(
            error.code,
            str(error),
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=tuple(
                AssetRef(descriptor.assetId, descriptor.assetVersionId) for _requestId, descriptor, _active in resolved
            ),
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
        )
    except Exception:
        recordFailure(_log, "RESOURCE_PAGE_PLAN_FAILED")
        return _failedResult(
            "RESOURCE_PAGE_PLAN_FAILED",
            "resource page 계획을 고정하지 못했습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=tuple(
                AssetRef(descriptor.assetId, descriptor.assetVersionId) for _requestId, descriptor, _active in resolved
            ),
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
        )


def resumeResourcePaging(token: str, *, deadline: float, startedAt: float | None = None) -> DataResult:
    """Token private state를 catalog lookup 없이 복원해 다음 multiplex page를 반환한다."""

    session: _ResourceSession | None = None
    try:
        requireDeadline(deadline)
        contextStore = _continuationStore(deadline=deadline)
        context = contextStore.loadContext(token)
        requireDeadline(deadline)
        _validateQueryPayload(context.state.queryPayload)
        session = _decodeSession(context.state.cursorPayload)
        if startedAt is not None:
            if type(startedAt) not in {int, float} or not math.isfinite(startedAt) or startedAt > time.perf_counter():
                raise ContinuationError("CONTINUATION_TIMEOUT")
            deadline = float(startedAt) + session.pageTimeoutMs / 1000
        requireDeadline(deadline)

        def materialize(current: ContinuationQueryState) -> PageEnvelope:
            """현재 원천 pin을 재검증한 뒤 이어질 resource page를 만든다."""

            requireDeadline(deadline)
            boundary = _ownerBoundary()
            currentSources, preparedReads = _currentSourcePins(boundary, session, deadline=deadline)
            currentPins = _pins(session, context.state.queryPayload, currentSources)
            _requireCurrentPins(context.pins, currentPins)
            return _materialize(
                current,
                boundary,
                deadline=deadline,
                preparedReads=preparedReads,
            )

        requireDeadline(deadline)
        redeemStore = _continuationStore(deadline=deadline, runMaintenance=False)
        page = redeemStore.redeem(
            token,
            context.pins,
            materialize=materialize,
            waitSeconds=requireDeadline(deadline),
        )
        requireDeadline(deadline)
        result = _resultFromPage(session, page)
        requireDeadline(deadline)
        return result
    except ContinuationError as error:
        return _failedResult(
            error.code,
            str(error),
            snapshotId=session.snapshotId if session is not None else "data-snapshot:continuation-unavailable",
            contractHash=session.contractHash if session is not None else "0" * 64,
            assets=(
                tuple(AssetRef(task.assetId, task.assetVersionId) for task in session.tasks)
                if session is not None
                else ()
            ),
            requestedAssets=session.requestedAssets if session is not None else 0,
            resolvedAssets=len(session.tasks) if session is not None else 0,
        )
    except Exception:
        recordFailure(_log, "CONTINUATION_OWNER_FAILED")
        return _failedResult(
            "CONTINUATION_OWNER_FAILED",
            "continuation page owner 실행에 실패했습니다",
            snapshotId=session.snapshotId if session is not None else "data-snapshot:continuation-unavailable",
            contractHash=session.contractHash if session is not None else "0" * 64,
            assets=(
                tuple(AssetRef(task.assetId, task.assetVersionId) for task in session.tasks)
                if session is not None
                else ()
            ),
            requestedAssets=session.requestedAssets if session is not None else 0,
            resolvedAssets=len(session.tasks) if session is not None else 0,
        )
