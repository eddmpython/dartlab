"""Composite paging의 계획, 첫 page, continuation 공개 orchestration."""

from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.dataHub.compositePagingModels import (
    _CONTROL_BASE_BYTES,
    _CONTROL_PER_LANE_BYTES,
    _FORMAT_VERSION,
    _MAX_LANES,
    _MIN_CHILD_BYTES,
    _PAGE_KIND,
    CompositePagingPlan,
    _AdapterProtocol,
)
from dartlab.dataHub.compositePagingPayload import (
    _validateCompositePayload,
    materializationPageSchemaDigest,
)
from dartlab.dataHub.compositePagingResults import _failedResult, _resultFromComposite
from dartlab.dataHub.compositePagingSchedule import _materializeComposite, _outerPins
from dartlab.dataHub.compositePagingState import (
    _decodeSession,
    _encodeSession,
    _laneTree,
    _queryPayload,
    _validateQueryPayload,
)
from dartlab.dataHub.continuation import ContinuationError, ContinuationQueryState, canonicalDigest
from dartlab.dataHub.contracts import AssetRef, DataAssetDescriptor, DataQuery, DataResult
from dartlab.dataHub.pagingRuntime import (
    MAX_PAGE_BYTES,
    MAX_PAGE_ROWS,
    continuationStore,
    requireDeadline,
)
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

_log = dataHubLogger(__name__)


def _defaultAdapters() -> _AdapterProtocol:
    """호환 파사드에서 현재 production adapter seam을 가져온다."""

    import dartlab.dataHub.compositePaging as facade

    return facade._ProductionAdapters()


def prepareCompositePaging(
    assetIds: Sequence[str],
    query: DataQuery,
    *,
    requestedAssets: int,
    snapshotId: str,
    contractHash: str,
    resolved: Sequence[tuple[str, DataAssetDescriptor, DataQuery]],
    deadline: float,
    _adapters: _AdapterProtocol | None = None,
) -> CompositePagingPlan:
    """Owner 실행 없이 mixed outer session과 exact pins를 준비한다."""

    requireDeadline(deadline)
    adapters = _defaultAdapters() if _adapters is None else _adapters
    lanes = []
    for requestIndex, (requestId, descriptor, activeQuery) in enumerate(resolved):
        planned = adapters.plan(
            requestId,
            requestIndex,
            descriptor,
            activeQuery,
            snapshotId=snapshotId,
            contractHash=contractHash,
            deadline=deadline,
        )
        lanes.append(
            _laneTree(
                planned,
                requestId=requestId,
                requestIndex=requestIndex,
                descriptor=descriptor,
            )
        )
    if len(lanes) > _MAX_LANES:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    session = _decodeSession(
        _encodeSession(
            {
                "version": _FORMAT_VERSION,
                "pageKind": _PAGE_KIND,
                "snapshotId": snapshotId,
                "contractHash": contractHash,
                "requestedAssets": requestedAssets,
                "resolvedAssets": len(resolved),
                "pageMaxRows": min(query.budget.maxRows, MAX_PAGE_ROWS),
                "pageMaxBytes": min(query.budget.maxBytes, MAX_PAGE_BYTES),
                "pageTimeoutMs": query.budget.timeoutMs,
                "maxConcurrency": query.budget.maxConcurrency,
                "nextLaneIndex": 0,
                "lanes": lanes,
            }
        )
    )
    queryPayload = _queryPayload(assetIds, query)
    return CompositePagingPlan(
        session=session,
        queryPayload=queryPayload,
        pins=_outerPins(session, queryPayload),
        adapters=adapters,
    )


def compositeMaterializationIdentity(
    plan: CompositePagingPlan,
) -> dict[str, str]:
    """Prepared outer plan을 six-pin immutable generation identity로 바꾼다."""

    lanes = plan.session["lanes"]
    if not isinstance(lanes, list):
        raise ContinuationError("CONTINUATION_CORRUPT")
    assetDigest = canonicalDigest(
        {
            "catalogSnapshotId": plan.session["snapshotId"],
            "assets": [
                {
                    "requestId": lane["requestId"],
                    "requestIndex": lane["requestIndex"],
                    "assetId": lane["assetId"],
                    "assetVersionId": lane["assetVersionId"],
                    "layer": lane["layer"],
                    "laneKind": lane["laneKind"],
                }
                for lane in lanes
            ],
        }
    )
    universeDigest = canonicalDigest(
        {
            str(lane["requestId"]): {
                "laneKind": lane["laneKind"],
                "scopeDigest": canonicalDigest(lane["privateState"]),
            }
            for lane in lanes
        }
    )
    contractDigest = canonicalDigest(
        {
            "format": "materialized-composite-result-v1",
            "catalogSnapshotId": plan.session["snapshotId"],
            "contractHash": plan.session["contractHash"],
            "outerContractDigest": plan.pins.contractDigest,
            "pageSchemaDigest": materializationPageSchemaDigest(),
        }
    )
    return {
        "assetDigest": assetDigest,
        "sourceDigest": plan.pins.sourceDigest,
        "queryDigest": plan.pins.queryDigest,
        "universeDigest": universeDigest,
        "contractDigest": contractDigest,
        "schemaDigest": materializationPageSchemaDigest(),
    }


def executePreparedCompositePaging(
    plan: CompositePagingPlan,
    *,
    deadline: float,
) -> DataResult:
    """Prepared plan의 첫 outer page를 기존 continuation owner로 실행한다."""

    state = ContinuationQueryState(
        plan.queryPayload,
        _encodeSession(plan.session),
    )
    issueStore = continuationStore(
        deadline=deadline,
        payloadValidator=_validateCompositePayload,
    )
    issued = issueStore.issue(state, plan.pins)
    requireDeadline(deadline)
    redeemStore = continuationStore(
        deadline=deadline,
        payloadValidator=_validateCompositePayload,
        runMaintenance=False,
    )
    page = redeemStore.redeem(
        issued.token,
        plan.pins,
        materialize=lambda current: _materializeComposite(
            current,
            plan.adapters,
            deadline=deadline,
        ),
        waitSeconds=requireDeadline(deadline),
    )
    requireDeadline(deadline)
    return _resultFromComposite(plan.session, page, plan.adapters)


def executeInitialCompositePaging(
    assetIds: Sequence[str],
    query: DataQuery,
    *,
    requestedAssets: int,
    snapshotId: str,
    contractHash: str,
    resolved: Sequence[tuple[str, DataAssetDescriptor, DataQuery]],
    hasPlanningGaps: bool,
    deadline: float,
    _adapters: _AdapterProtocol | None = None,
) -> DataResult:
    """Mixed request 첫 page를 outer continuation 하나로 발급한다.

    Args:
        assetIds: 원 query의 legacy asset ID sequence.
        query: Request order와 총예산을 가진 원 DataQuery.
        requestedAssets: Catalog resolve 전 request 수.
        snapshotId: Catalog snapshot identity.
        contractHash: 원 query와 descriptor version의 결합 digest.
        resolved: Request ID, descriptor, active query plan.
        hasPlanningGaps: Catalog 또는 resolve 계획 gap 여부.
        deadline: 첫 page absolute monotonic deadline.
        _adapters: Production 비노출 deterministic test seam.

    Returns:
        Request-order partition과 outer continuation 하나를 가진 DataResult.

    Raises:
        없음. 계획과 continuation 실패는 fail-closed DataResult로 바뀐다.

    Example:
        ``executeInitialCompositePaging((), query, resolved=plan, ...)``.
    """

    refs = tuple(
        dict.fromkeys(
            AssetRef(descriptor.assetId, descriptor.assetVersionId) for _requestId, descriptor, _active in resolved
        )
    )
    if query.completeness == "requireComplete":
        return _failedResult(
            "PAGEABLE_REQUIRE_COMPLETE_UNSUPPORTED",
            "mixed pageable query는 requireComplete를 지원하지 않습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=refs,
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
            systemic=False,
        )
    if hasPlanningGaps or not resolved:
        return _failedResult(
            "PAGEABLE_PLAN_INCOMPLETE",
            "mixed pageable query 계획을 완전하게 고정할 수 없습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=refs,
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
            systemic=False,
        )
    minimumBytes = _CONTROL_BASE_BYTES + _CONTROL_PER_LANE_BYTES + _MIN_CHILD_BYTES
    if query.budget.maxBytes < minimumBytes:
        return _failedResult(
            "PAGEABLE_BYTE_BUDGET_TOO_SMALL",
            "mixed page control과 child payload를 담을 byte budget이 부족합니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=refs,
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
            systemic=False,
        )
    try:
        plan = prepareCompositePaging(
            assetIds,
            query,
            requestedAssets=requestedAssets,
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            deadline=deadline,
            _adapters=_adapters,
        )
        return executePreparedCompositePaging(plan, deadline=deadline)
    except ContinuationError as error:
        return _failedResult(
            error.code,
            str(error),
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=refs,
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
        )
    except Exception:
        recordFailure(_log, "COMPOSITE_PAGE_PLAN_FAILED")
        return _failedResult(
            "COMPOSITE_PAGE_PLAN_FAILED",
            "mixed page 계획을 고정하지 못했습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=refs,
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
        )


def resumeCompositePaging(
    token: str,
    *,
    deadline: float,
    startedAt: float | None = None,
    _adapters: _AdapterProtocol | None = None,
) -> DataResult:
    """저장된 mixed state를 catalog override 없이 다음 outer page로 교환한다.

    Args:
        token: 이전 DataResult가 반환한 유일한 opaque continuation.
        deadline: 현재 호출 absolute monotonic deadline.
        startedAt: 저장된 page timeout을 적용할 현재 호출 시작 시각.
        _adapters: Production 비노출 deterministic test seam.

    Returns:
        Replay되거나 새로 commit된 mixed DataResult page.

    Raises:
        없음. Token과 owner 실패는 비밀값 없는 failed result로 바뀐다.

    Example:
        ``resumeCompositePaging(token, deadline=deadline)``.
    """

    session: dict[str, Any] | None = None
    adapters = _defaultAdapters() if _adapters is None else _adapters
    try:
        requireDeadline(deadline)
        contextStore = continuationStore(
            deadline=deadline,
            payloadValidator=_validateCompositePayload,
        )
        context = contextStore.loadContext(token)
        _validateQueryPayload(context.state.queryPayload)
        session = _decodeSession(context.state.cursorPayload)
        if startedAt is not None:
            if type(startedAt) not in {int, float} or not math.isfinite(startedAt) or startedAt > time.perf_counter():
                raise ContinuationError("CONTINUATION_TIMEOUT")
            deadline = float(startedAt) + session["pageTimeoutMs"] / 1000
        requireDeadline(deadline)
        store = continuationStore(
            deadline=deadline,
            payloadValidator=_validateCompositePayload,
            runMaintenance=False,
        )
        page = store.redeem(
            token,
            context.pins,
            materialize=lambda current: _materializeComposite(
                current,
                adapters,
                deadline=deadline,
            ),
            waitSeconds=requireDeadline(deadline),
        )
        requireDeadline(deadline)
        return _resultFromComposite(session, page, adapters)
    except ContinuationError as error:
        return _failedResult(
            error.code,
            str(error),
            snapshotId=session["snapshotId"] if session is not None else "data-snapshot:continuation-unavailable",
            contractHash=session["contractHash"] if session is not None else "0" * 64,
            assets=(
                tuple(AssetRef(lane["assetId"], lane["assetVersionId"]) for lane in session["lanes"])
                if session is not None
                else ()
            ),
            requestedAssets=session["requestedAssets"] if session is not None else 0,
            resolvedAssets=session["resolvedAssets"] if session is not None else 0,
        )
    except Exception:
        recordFailure(_log, "CONTINUATION_OWNER_FAILED")
        return _failedResult(
            "CONTINUATION_OWNER_FAILED",
            "mixed continuation owner 실행에 실패했습니다",
            snapshotId=session["snapshotId"] if session is not None else "data-snapshot:continuation-unavailable",
            contractHash=session["contractHash"] if session is not None else "0" * 64,
            assets=(
                tuple(AssetRef(lane["assetId"], lane["assetVersionId"]) for lane in session["lanes"])
                if session is not None
                else ()
            ),
            requestedAssets=session["requestedAssets"] if session is not None else 0,
            resolvedAssets=session["resolvedAssets"] if session is not None else 0,
        )
