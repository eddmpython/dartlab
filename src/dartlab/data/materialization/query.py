"""Existing composite outer chain to immutable generation integration."""

from __future__ import annotations

import secrets
import time
from collections.abc import Sequence

from dartlab.data.compositePaging import (
    CompositePagingPlan,
    compositeMaterializationIdentity,
    compositeQueryDigest,
    encodeMaterializationPage,
    executePreparedCompositePaging,
)
from dartlab.data.continuation import ContinuationError
from dartlab.data.contracts import DataQuery, DataResult
from dartlab.data.pagingRouter import resumeDataPaging
from dartlab.data.pagingRuntime import MAX_PAGE_BYTES

from .contracts import (
    GenerationPins,
    MaterializationDirective,
    MaterializationError,
    PageDraft,
)
from .paging import resultFromHandle, resultFromReceipt
from .runtime import materializationStore


def _raiseProducerFailure(result: DataResult) -> None:
    """Systemic continuation 실패는 등록된 typed 원인으로 복원한다."""

    if result.status != "failed" or result.partitions:
        return
    if len(result.gaps) == 1 and result.gaps[0].systemic:
        try:
            error = ContinuationError(result.gaps[0].code)
        except ValueError:
            pass
        else:
            raise error
    raise MaterializationError("MATERIALIZATION_NOT_READY")


def replayMaterializedQuery(
    assetIds: Sequence[str],
    query: DataQuery,
    directive: MaterializationDirective,
    *,
    deadline: float,
) -> DataResult | None:
    """Receipt 또는 canonical query digest로 READY fast path를 실행한다."""

    store = materializationStore(pageTimeoutMs=query.budget.timeoutMs)
    if directive.mode == "offline":
        if directive.receipt is None:
            raise MaterializationError("MATERIALIZATION_INVALID")
        return resultFromReceipt(directive.receipt, deadline=deadline)
    if directive.mode != "reuse":
        return None
    if directive.receipt is not None:
        return resultFromReceipt(directive.receipt, deadline=deadline)
    generation = store.readLatestHandle(compositeQueryDigest(assetIds, query))
    if generation is None:
        return None
    return resultFromHandle(generation, deadline=deadline)


def materializeCompositeQuery(
    plan: CompositePagingPlan,
    query: DataQuery,
    *,
    deadline: float,
) -> DataResult:
    """Prepared composite chain을 terminal까지 순회해 READY로 게시한다."""

    identity = compositeMaterializationIdentity(plan)
    exactPins = GenerationPins(**identity)
    store = materializationStore(pageTimeoutMs=query.budget.timeoutMs)
    buildDeadline = time.perf_counter() + store.policy.maxBuildSeconds

    def ownerProducer():
        """Owner continuation을 끝까지 소비해 generation page를 생산한다."""
        if time.perf_counter() >= buildDeadline:
            raise MaterializationError("MATERIALIZATION_BUDGET")
        pageDeadline = min(buildDeadline, deadline)
        if time.perf_counter() >= pageDeadline:
            raise MaterializationError("MATERIALIZATION_BUDGET")
        result = executePreparedCompositePaging(plan, deadline=pageDeadline)
        pageCount = 0
        while True:
            if time.perf_counter() >= buildDeadline:
                raise MaterializationError("MATERIALIZATION_BUDGET")
            _raiseProducerFailure(result)
            payload = encodeMaterializationPage(
                result,
                maxBytes=MAX_PAGE_BYTES,
            )
            yield PageDraft(payload=payload, rowCount=1)
            pageCount += 1
            if pageCount >= store.policy.maxPagesPerGeneration:
                if result.continuation is not None:
                    raise MaterializationError("MATERIALIZATION_BUDGET")
            if result.continuation is None:
                break
            pageDeadline = min(
                buildDeadline,
                time.perf_counter() + query.budget.timeoutMs / 1000,
            )
            result = resumeDataPaging(
                result.continuation,
                deadline=pageDeadline,
            )
            if time.perf_counter() >= buildDeadline:
                raise MaterializationError("MATERIALIZATION_BUDGET")

    outcome = store.materializeOrReplayHandle(
        exactPins,
        builderId=secrets.token_hex(32),
        ownerProducer=ownerProducer,
    )
    replayDeadline = time.perf_counter() + query.budget.timeoutMs / 1000
    return resultFromHandle(
        outcome.generation,
        deadline=replayDeadline,
    )
