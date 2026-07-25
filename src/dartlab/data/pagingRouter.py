"""Opaque continuation token을 pageable data owner adapter로 라우팅한다."""

from __future__ import annotations

from dartlab.data.continuation import ContinuationError, validateArrowIpcPayload
from dartlab.data.contracts import DataResult
from dartlab.data.pagingRuntime import continuationStore, requireDeadline


def resumeDataPaging(
    token: str,
    *,
    deadline: float,
    startedAt: float | None = None,
) -> DataResult:
    """Private cursor kind를 읽고 기존 resource 또는 계산형 owner page를 재개한다.

    Args:
        token: Public query가 받은 opaque continuation token.
        deadline: 현재 resume 호출의 monotonic deadline.
        startedAt: 최초 page timeout을 복원할 현재 호출 시작 시각.

    Returns:
        Resource 또는 계산형 owner adapter의 다음 ``DataResult``.

    Raises:
        ContinuationError: Router 진입 전에 deadline이 이미 만료됐을 때.

    Example:
        ``page = resumeDataPaging(token, deadline=deadline)``.
    """

    requireDeadline(deadline)
    try:
        context = continuationStore(
            deadline=deadline,
            payloadValidator=validateArrowIpcPayload,
            runMaintenance=False,
        ).loadContext(token)
    except ContinuationError:
        from dartlab.data.resourcePaging import resumeResourcePaging

        return resumeResourcePaging(token, deadline=deadline, startedAt=startedAt)
    from dartlab.data.materialization.paging import isMaterializedPagingState

    if isMaterializedPagingState(context.state.cursorPayload):
        from dartlab.data.materialization.paging import (
            resumeMaterializedPaging,
        )

        return resumeMaterializedPaging(
            token,
            deadline=deadline,
            startedAt=startedAt,
        )
    from dartlab.data.compositePaging import isCompositePagingState

    if isCompositePagingState(context.state.cursorPayload):
        from dartlab.data.compositePaging import resumeCompositePaging

        return resumeCompositePaging(token, deadline=deadline, startedAt=startedAt)
    from dartlab.data.ownerPaging import isOwnerPagingState

    if isOwnerPagingState(context.state.cursorPayload):
        from dartlab.data.ownerPaging import resumeOwnerPaging

        return resumeOwnerPaging(token, deadline=deadline, startedAt=startedAt)
    from dartlab.data.resourcePaging import resumeResourcePaging

    return resumeResourcePaging(token, deadline=deadline, startedAt=startedAt)


__all__ = ["resumeDataPaging"]
