"""Owner paging 판정, 계획, 첫 page와 continuation orchestration."""

from __future__ import annotations

import dataclasses
import math
import time
from collections.abc import Sequence
from typing import Any

from dartlab.dataHub.continuation import (
    ContinuationError,
    ContinuationQueryState,
    PageEnvelope,
    canonicalDigest,
)
from dartlab.dataHub.contracts import AssetRef, DataAssetDescriptor, DataQuery, DataResult, FactorProjection
from dartlab.dataHub.ownerPagingEntity import _entityParamMap
from dartlab.dataHub.ownerPagingModels import _MAX_PAGE_ENTITIES, _OwnerSession, _OwnerTask
from dartlab.dataHub.ownerPagingPayload import _continuationStore
from dartlab.dataHub.ownerPagingResults import _failedResult, _planFailure, _resultFromPage
from dartlab.dataHub.ownerPagingSchedule import _materialize, _requireTaskContracts, _requireTaskSources
from dartlab.dataHub.ownerPagingSource import _entities, _pins, _requireCurrentPins, _sourcePin
from dartlab.dataHub.ownerPagingState import (
    _decodeSession,
    _descriptorTree,
    _encodeSession,
    _ownerCodePin,
    _queryPayload,
    _queryTree,
    _requestedMeasures,
    _selectionTree,
    _validateQueryPayload,
)
from dartlab.dataHub.pagingRuntime import MAX_PAGE_BYTES, MAX_PAGE_ROWS, requireDeadline


def _ownerFacade() -> Any:
    """현재 호환 파사드의 monkeypatch seam을 반환한다."""

    import dartlab.dataHub.ownerPaging as facade

    return facade


def isPageableOwner(descriptor: DataAssetDescriptor, query: DataQuery) -> bool:
    """Descriptor와 query가 계산형 listed-universe subject paging 계약인지 판별한다.

    Args:
        descriptor: Catalog가 검증한 owner asset 선언.
        query: Projection과 universe가 결박된 active request query.

    Returns:
        별도 owner continuation으로 실행해야 하면 ``True``.

    Raises:
        없음. 지원하지 않는 조합은 ``False``다.

    Example:
        ``isPageableOwner(descriptor, activeQuery)``.

    Requires:
        Descriptor와 query는 catalog resolve 이후의 immutable 계약이어야 한다.
    """

    metadata = dict(descriptor.metadata)
    try:
        _entityParamMap(descriptor)
    except ValueError:
        return False
    return (
        isinstance(query.projection, FactorProjection)
        and query.universe is not None
        and not query.subjects
        and descriptor.executorKind == "callable"
        and descriptor.executionMode == "subjectFanout"
        and descriptor.universeKind == "listedEquity"
        and bool(descriptor.subjectParam)
        and isinstance(metadata.get("continuationSourceAssetId"), str)
        and isinstance(metadata.get("continuationSourceCategory"), str)
        and isinstance(metadata.get("sourceEntityParam"), str)
        and isinstance(metadata.get("sourcePayloadParam"), str)
        and isinstance(metadata.get("sourceIntegrityParam"), str)
    )


def _plannedTask(
    requestId: str,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
) -> _OwnerTask:
    if query.universe is None:
        raise ValueError("owner paging universe가 없습니다")
    if query.universe.membership != "listed" or query.universe.asOf is not None:
        raise ValueError("owner paging은 현재 listed universe만 지원합니다")
    if set(query.universe.markets) != set(descriptor.universeMarkets):
        raise ValueError("owner paging market scope가 asset 선언과 다릅니다")
    from dartlab.dataHub.execution import _temporalGap

    gap = _temporalGap(descriptor, query)
    if gap is not None:
        raise ValueError(gap.code)
    resolved = _ownerFacade().resolveUniverse(query.universe)
    if resolved.gaps:
        raise ValueError(resolved.gaps[0].code)
    if len(resolved.markets) != 1:
        raise ValueError("owner paging request 하나는 market 하나만 지원합니다")
    membership = resolved.markets[0]
    if membership.market not in descriptor.universeMarkets or not membership.entityIds:
        raise ValueError("owner paging universe가 asset 범위 밖입니다")
    metadata = dict(descriptor.metadata)
    entityParamMap = _entityParamMap(descriptor)
    paramsByEntity = membership.paramsByEntity()
    if any(
        sourceName not in dict(paramsByEntity.get(entityId, ()))
        for entityId in membership.entityIds
        for sourceName, _target in entityParamMap
    ):
        raise ValueError("owner paging universe entity parameter가 없습니다")
    sourceAssetId = metadata.get("continuationSourceAssetId")
    sourceCategory = metadata.get("continuationSourceCategory")
    if (
        not isinstance(sourceAssetId, str)
        or not sourceAssetId
        or not isinstance(sourceCategory, str)
        or not sourceCategory
    ):
        raise ValueError("owner paging source 선언이 없습니다")
    reservedParams = tuple(
        value
        for value in (
            metadata.get("sourceEntityParam"),
            metadata.get("sourcePayloadParam"),
            metadata.get("sourceIntegrityParam"),
            *(target for _source, target in entityParamMap),
            descriptor.measureParam,
        )
        if isinstance(value, str) and value
    )
    expectedReservedParams = 3 + len(entityParamMap) + (1 if descriptor.measureParam is not None else 0)
    if (
        len(reservedParams) != expectedReservedParams
        or len(set(reservedParams)) != len(reservedParams)
        or any(name in query.params for name in reservedParams)
    ):
        raise ValueError("owner paging source parameter 선언이 유효하지 않습니다")
    ownerSourcePin = _ownerFacade()._resourceSourcePin(sourceAssetId, sourceCategory)
    requestedMeasures = _requestedMeasures(query)
    ownerCodePin = _ownerCodePin(descriptor, requestedMeasures)
    sourcePin = _sourcePin(
        ownerSourcePin,
        membership.membershipDigest,
        requestedMeasures,
    )
    pageQuery = dataclasses.replace(query, subjects=(), universe=None, requests=())
    queryPin = canonicalDigest(
        {
            "descriptor": _descriptorTree(descriptor),
            "query": _queryTree(pageQuery),
            "selection": _selectionTree(query.universe),
        }
    )
    return _OwnerTask(
        requestId=requestId,
        descriptor=descriptor,
        query=pageQuery,
        selection=query.universe,
        market=membership.market,
        provider=membership.provider,
        universeSnapshotId=resolved.snapshotId,
        membershipDigest=membership.membershipDigest,
        sourceAssetId=sourceAssetId,
        sourceCategory=sourceCategory,
        ownerSourcePin=ownerSourcePin,
        ownerCodePin=ownerCodePin,
        sourcePin=sourcePin,
        queryPin=queryPin,
        entities=_entities(
            membership,
            tuple(source for source, _target in entityParamMap),
        ),
    )


def executeInitialOwnerPaging(
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
    """첫 계산형 universe page를 발급하고 동일 continuation store에서 즉시 실행한다.

    Capabilities:
        전체 listed universe 계획을 고정하고 첫 process page와 token을 원자 발급한다.

    Args:
        assetIds: Legacy query가 직접 지정한 asset IDs.
        query: 원 public query.
        requestedAssets: Resolve 전 전체 request 수.
        snapshotId: Catalog snapshot identity.
        contractHash: 원 query와 asset version의 결합 hash.
        resolved: Request ID, descriptor, active query 실행 계획.
        hasPlanningGaps: Catalog resolve 단계에서 gap이 있었는지 여부.
        deadline: 첫 page의 monotonic deadline.

    Returns:
        첫 factor page 또는 fail-closed ``DataResult``.

    Raises:
        없음. 안전한 계획과 continuation 오류는 failed result로 변환한다.

    Example:
        ``first = executeInitialOwnerPaging(assetIds, query, ...)``.

    Guide:
        혼합 실행, historical universe, requireComplete는 process 시작 전에 거부한다.

    When:
        Public data query가 subject 없는 pageable computed owner로 해소될 때 사용한다.

    How:
        Session과 pin을 issue한 뒤 같은 store에서 첫 page를 즉시 redeem한다.

    See Also:
        ``resumeOwnerPaging``과 ``isPageableOwner``.

    Requires:
        Resolved plan의 모든 request가 같은 pageable owner 계약을 충족해야 한다.

    AI Context:
        Continuation cursor와 commit은 parent process의 store만 소유한다.
    """

    refs = tuple(
        AssetRef(descriptor.assetId, descriptor.assetVersionId) for _requestId, descriptor, _active in resolved
    )
    try:
        requireDeadline(deadline)
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
    if any(not isPageableOwner(descriptor, active) for _requestId, descriptor, active in resolved):
        return _planFailure(
            "PAGEABLE_MIXED_EXECUTION_UNSUPPORTED",
            "계산형 pageable owner와 다른 실행 방식은 한 query에서 아직 혼합할 수 없습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if query.completeness == "requireComplete":
        return _planFailure(
            "PAGEABLE_REQUIRE_COMPLETE_UNSUPPORTED",
            "계산형 universe paging은 requireComplete를 지원하지 않습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if any(
        active.universe is not None and (active.universe.membership != "listed" or active.universe.asOf is not None)
        for _requestId, _descriptor, active in resolved
    ):
        return _planFailure(
            "UNIVERSE_PIT_UNSUPPORTED",
            "계산형 owner paging은 현재 listed universe만 지원합니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    if hasPlanningGaps or not resolved:
        return _planFailure(
            "PAGEABLE_PLAN_INCOMPLETE",
            "계산형 universe page 계획을 완전하게 고정할 수 없습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            requestedAssets=requestedAssets,
        )
    try:
        tasks = tuple(_plannedTask(requestId, descriptor, active) for requestId, descriptor, active in resolved)
        if not tasks:
            raise ValueError("owner paging task가 없습니다")
        universeIds = tuple(sorted({task.universeSnapshotId for task in tasks}))
        universeSnapshotId = (
            universeIds[0] if len(universeIds) == 1 else "universe-query:" + canonicalDigest(universeIds)
        )
        declaredPageCaps = []
        for task in tasks:
            value = dict(task.descriptor.metadata).get("pageMaxEntities", 8)
            if type(value) is not int or value <= 0:
                raise ValueError("pageMaxEntities 선언이 유효하지 않습니다")
            declaredPageCaps.append(value)
        session = _OwnerSession(
            snapshotId=snapshotId,
            contractHash=contractHash,
            requestedAssets=requestedAssets,
            universeSnapshotId=universeSnapshotId,
            pageMaxRows=min(query.budget.maxRows, MAX_PAGE_ROWS),
            pageMaxBytes=min(query.budget.maxBytes, MAX_PAGE_BYTES),
            pageMaxLogicalBytes=min(query.budget.maxBytes, MAX_PAGE_BYTES),
            pageMaxEntities=min(*declaredPageCaps, _MAX_PAGE_ENTITIES),
            pageTimeoutMs=query.budget.timeoutMs,
            maxConcurrency=query.budget.maxConcurrency,
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
                deadline=deadline,
                sourcesPrevalidated=True,
            ),
            waitSeconds=requireDeadline(deadline),
        )
        requireDeadline(deadline)
        return _resultFromPage(session, page)
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
        return _failedResult(
            "OWNER_PAGE_PLAN_FAILED",
            "계산형 universe page 계획을 고정하지 못했습니다",
            snapshotId=snapshotId,
            contractHash=contractHash,
            assets=refs,
            requestedAssets=requestedAssets,
            resolvedAssets=len(resolved),
        )


def resumeOwnerPaging(
    token: str,
    *,
    deadline: float,
    startedAt: float | None = None,
) -> DataResult:
    """Token private state로 계산형 owner의 다음 bounded page를 반환한다.

    Args:
        token: 원 질의를 대체하는 opaque bearer continuation.
        deadline: 현재 public 호출의 임시 monotonic deadline.
        startedAt: 최초 page timeout을 다시 적용할 현재 호출 시작 시각.

    Returns:
        Replay되거나 새로 계산된 다음 ``DataResult`` page.

    Raises:
        없음. Token, pin, source, owner 오류는 비밀값 없는 failed result다.

    Example:
        ``nextPage = resumeOwnerPaging(token, deadline=deadline)``.

    Requires:
        Token은 같은 private continuation root와 TTL 정책에서 발급됐어야 한다.
    """

    session: _OwnerSession | None = None
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
            """현재 source와 contract pin을 재검증해 다음 page를 계산한다.

            Capabilities:
                Uncommitted token의 current pin을 확인하고 process page를 계산한다.

            Args:
                current: Store가 claim한 현재 private query state.

            Returns:
                Bounded Arrow outer page와 선택적인 다음 state.

            Raises:
                ContinuationError: Source 또는 continuation pin이 달라졌을 때.

            Example:
                ``store.redeem(token, pins, materialize=materialize)``.

            Guide:
                Source와 contract drift는 owner process를 시작하기 전에 차단한다.

            When:
                Store가 아직 commit되지 않은 continuation token의 claim을 획득할 때 사용한다.

            How:
                Current pin을 재구성해 비교한 뒤 공통 page materializer에 위임한다.

            See Also:
                ``_materialize``과 ``_requireCurrentPins``.

            Requires:
                복원한 session과 context pin이 같은 immutable query를 나타내야 한다.

            AI Context:
                이미 commit된 replay는 이 callback을 호출하지 않는다.
            """

            _requireTaskContracts(session, deadline=deadline)
            currentSources = _requireTaskSources(session, deadline=deadline)
            currentPins = _pins(session, context.state.queryPayload, currentSources)
            _requireCurrentPins(context.pins, currentPins)
            return _materialize(
                current,
                deadline=deadline,
                sourcesPrevalidated=True,
            )

        redeemStore = _continuationStore(deadline=deadline, runMaintenance=False)
        page = redeemStore.redeem(
            token,
            context.pins,
            materialize=materialize,
            waitSeconds=requireDeadline(deadline),
        )
        requireDeadline(deadline)
        return _resultFromPage(session, page)
    except ContinuationError as error:
        return _failedResult(
            error.code,
            str(error),
            snapshotId=session.snapshotId if session is not None else "data-snapshot:continuation-unavailable",
            contractHash=session.contractHash if session is not None else "0" * 64,
            assets=(
                tuple(AssetRef(task.descriptor.assetId, task.descriptor.assetVersionId) for task in session.tasks)
                if session is not None
                else ()
            ),
            requestedAssets=session.requestedAssets if session is not None else 0,
            resolvedAssets=len(session.tasks) if session is not None else 0,
        )
    except Exception:
        return _failedResult(
            "CONTINUATION_OWNER_FAILED",
            "계산형 continuation page owner 실행에 실패했습니다",
            snapshotId=session.snapshotId if session is not None else "data-snapshot:continuation-unavailable",
            contractHash=session.contractHash if session is not None else "0" * 64,
            assets=(
                tuple(AssetRef(task.descriptor.assetId, task.descriptor.assetVersionId) for task in session.tasks)
                if session is not None
                else ()
            ),
            requestedAssets=session.requestedAssets if session is not None else 0,
            resolvedAssets=len(session.tasks) if session is not None else 0,
        )
