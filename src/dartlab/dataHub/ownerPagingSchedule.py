"""Owner page 후보 배분, process 실행, continuation 진척 갱신."""

from __future__ import annotations

import dataclasses
import hmac
from collections.abc import Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

import polars as pl

from dartlab.dataHub.contentSeal import contentHash
from dartlab.dataHub.continuation import (
    ContinuationError,
    ContinuationQueryState,
    PageEnvelope,
    canonicalJsonBytes,
)
from dartlab.dataHub.ownerPagingEntity import _failureEntry
from dartlab.dataHub.ownerPagingModels import (
    _DecodedPage,
    _OwnerEntry,
    _OwnerSession,
    _OwnerTask,
    _VerifiedEntitySource,
)
from dartlab.dataHub.ownerPagingPayload import _decodePage, _encodePage
from dartlab.dataHub.ownerPagingSource import _currentTaskSourcePin, _pins
from dartlab.dataHub.ownerPagingState import (
    _decodeSession,
    _descriptorTree,
    _encodeProcessSession,
    _encodeSession,
    _ownerCodePin,
    _requestedMeasures,
    _validateQueryPayload,
)
from dartlab.dataHub.pagingRuntime import MAX_STATE_BYTES, requireDeadline
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

_log = dataHubLogger(__name__)


def _ownerFacade() -> Any:
    """현재 호환 파사드의 monkeypatch seam을 반환한다."""

    import dartlab.dataHub.ownerPaging as facade

    return facade


def _candidates(session: _OwnerSession) -> tuple[tuple[_OwnerTask, int], ...]:
    offsets = {task.requestId: 0 for task in session.tasks}
    selected: list[tuple[_OwnerTask, int]] = []
    taskCount = len(session.tasks)
    taskIndex = session.nextTaskIndex
    consecutiveExhausted = 0
    while len(selected) < session.pageMaxEntities:
        task = session.tasks[taskIndex]
        ordinal = task.cursor + offsets[task.requestId]
        if ordinal < task.entityCount:
            selected.append((task, ordinal))
            offsets[task.requestId] += 1
            consecutiveExhausted = 0
        else:
            consecutiveExhausted += 1
        taskIndex = (taskIndex + 1) % taskCount
        if consecutiveExhausted >= taskCount:
            break
    return tuple(selected)


def _executionWindows(
    candidates: Sequence[tuple[_OwnerTask, int]],
    maxConcurrency: int,
) -> tuple[tuple[tuple[_OwnerTask, int], ...], ...]:
    pending = list(candidates)
    windows: list[tuple[tuple[_OwnerTask, int], ...]] = []
    while pending:
        selectedCount = 0
        groups: set[str] = set()
        for task, _ordinal in pending:
            group = task.descriptor.concurrencyGroup
            if group is not None and group in groups:
                break
            selectedCount += 1
            if group is not None:
                groups.add(group)
            if selectedCount >= maxConcurrency:
                break
        window = tuple(pending[:selectedCount])
        del pending[:selectedCount]
        windows.append(window)
    return tuple(windows)


def _boundedEntries(
    candidates: Sequence[tuple[_OwnerTask, int]],
    session: _OwnerSession,
    *,
    deadline: float,
    verifiedSources: Mapping[tuple[str, int], _VerifiedEntitySource] | None = None,
) -> tuple[_OwnerEntry, ...]:
    executor = ThreadPoolExecutor(
        max_workers=min(session.maxConcurrency, len(candidates)),
        thread_name_prefix="dartlab-owner-page",
    )
    futures: list[Future[_OwnerEntry]] = []
    entries: list[_OwnerEntry] = []
    abandoned = False
    try:
        for window in _executionWindows(candidates, session.maxConcurrency):
            windowFutures = []
            for task, ordinal in window:
                source = None if verifiedSources is None else verifiedSources.get((task.requestId, ordinal))
                if source is None:
                    windowFutures.append(executor.submit(_ownerFacade()._executeEntity, task, ordinal))
                else:
                    windowFutures.append(executor.submit(_ownerFacade()._executeEntity, task, ordinal, source))
            futures.extend(windowFutures)
            for future, (task, ordinal) in zip(windowFutures, window, strict=True):
                try:
                    entry = future.result(timeout=requireDeadline(deadline))
                except TimeoutError:
                    abandoned = True
                    if not entries:
                        raise ContinuationError("CONTINUATION_TIMEOUT") from None
                    break
                candidate = (*entries, entry)
                try:
                    _encodePage(
                        candidate,
                        maxPageRows=session.pageMaxRows,
                        maxPageBytes=session.pageMaxBytes,
                        maxLogicalBytes=session.pageMaxLogicalBytes,
                    )
                except ContinuationError as error:
                    if error.code not in {
                        "CONTINUATION_ROW_BUDGET",
                        "CONTINUATION_BYTE_BUDGET",
                        "CONTINUATION_LOGICAL_BYTE_BUDGET",
                    }:
                        raise
                    if entries:
                        abandoned = True
                        break
                    entity = task.entities[ordinal]
                    entry = _failureEntry(
                        task,
                        ordinal,
                        entity,
                        "FEATURE_ENTITY_OUTPUT_TOO_LARGE",
                        "entity factor 결과가 요청 page 예산을 초과했습니다",
                    )
                    _encodePage(
                        (entry,),
                        maxPageRows=session.pageMaxRows,
                        maxPageBytes=session.pageMaxBytes,
                        maxLogicalBytes=session.pageMaxLogicalBytes,
                    )
                entries.append(entry)
            if abandoned:
                break
    finally:
        if abandoned:
            for future in futures:
                future.cancel()
        executor.shutdown(wait=not abandoned, cancel_futures=abandoned)
    if not entries:
        raise ContinuationError("CONTINUATION_TIMEOUT")
    return tuple(entries)


def _updatedTasks(
    session: _OwnerSession,
    entries: Sequence[_OwnerEntry],
) -> tuple[_OwnerTask, ...]:
    byRequest: dict[str, list[_OwnerEntry]] = {}
    for entry in entries:
        byRequest.setdefault(entry.requestId, []).append(entry)
    updated = []
    for task in session.tasks:
        taskEntries = sorted(byRequest.get(task.requestId, ()), key=lambda entry: entry.entityOrdinal)
        expected = list(range(task.cursor, task.cursor + len(taskEntries)))
        if [entry.entityOrdinal for entry in taskEntries] != expected:
            raise ContinuationError("CONTINUATION_CORRUPT")
        succeeded = sum(entry.status == "ok" for entry in taskEntries)
        failedEntities = [entry.entityId for entry in taskEntries if entry.status == "failed"]
        updated.append(
            dataclasses.replace(
                task,
                cursor=task.cursor + len(taskEntries),
                succeededEntities=task.succeededEntities + succeeded,
                failedEntities=task.failedEntities + len(failedEntities),
                failedSample=tuple(dict.fromkeys((*task.failedSample, *failedEntities)))[:32],
            )
        )
    return tuple(updated)


def _nextTaskIndex(
    session: _OwnerSession,
    entries: Sequence[_OwnerEntry],
) -> int:
    if not entries:
        raise ContinuationError("CONTINUATION_CORRUPT")
    byRequest = {task.requestId: index for index, task in enumerate(session.tasks)}
    lastIndex = byRequest.get(entries[-1].requestId)
    if lastIndex is None:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return (lastIndex + 1) % len(session.tasks)


def _requireTaskSources(session: _OwnerSession, *, deadline: float) -> dict[str, str]:
    current: dict[str, str] = {}
    for task in session.tasks:
        requireDeadline(deadline)
        currentPin = _currentTaskSourcePin(task)
        requireDeadline(deadline)
        if not hmac.compare_digest(currentPin, task.sourcePin):
            raise ContinuationError("CONTINUATION_SOURCE_STALE")
        current[task.requestId] = currentPin
    return current


def _requireTaskContracts(session: _OwnerSession, *, deadline: float) -> None:
    try:
        from dartlab.dataHub.catalog import buildCatalog

        catalog = buildCatalog()
        if catalog.status != "ok":
            raise ValueError("현재 catalog를 완전하게 복원할 수 없습니다")
        byId = {descriptor.assetId: descriptor for descriptor in catalog.assets}
        for task in session.tasks:
            requireDeadline(deadline)
            current = byId.get(task.descriptor.assetId)
            if current is None or canonicalJsonBytes(_descriptorTree(current)) != canonicalJsonBytes(
                _descriptorTree(task.descriptor)
            ):
                raise ValueError("owner descriptor가 달라졌습니다")
            currentCodePin = _ownerCodePin(
                current,
                _requestedMeasures(task.query),
            )
            requireDeadline(deadline)
            if not hmac.compare_digest(currentCodePin, task.ownerCodePin):
                raise ValueError("owner code가 달라졌습니다")
    except ContinuationError:
        raise
    except Exception:
        recordFailure(_log, "CONTINUATION_CONTRACT_STALE")
        raise ContinuationError("CONTINUATION_CONTRACT_STALE") from None


def _requireDecodedPage(
    session: _OwnerSession,
    candidates: Sequence[tuple[_OwnerTask, int]],
    decoded: _DecodedPage,
) -> None:
    if not decoded.entries or len(decoded.entries) > len(candidates):
        raise ContinuationError("CONTINUATION_CORRUPT")
    for entry, table, expected in zip(
        decoded.entries,
        decoded.tables,
        candidates,
        strict=False,
    ):
        task, ordinal = expected
        entity = task.entities[ordinal]
        if (
            entry.requestId != task.requestId
            or entry.assetId != task.descriptor.assetId
            or entry.assetVersionId != task.descriptor.assetVersionId
            or entry.sourcePin != task.sourcePin
            or entry.queryPin != task.queryPin
            or entry.entityOrdinal != ordinal
            or entry.entityId != entity.entityId
            or entry.sourceEntityId != entity.sourceEntityId
        ):
            raise ContinuationError("CONTINUATION_CORRUPT")
        if entry.status != "ok":
            if table is not None:
                raise ContinuationError("CONTINUATION_CORRUPT")
            continue
        if table is None or entry.contentHash is None or entry.receiptRef is None or entry.temporalStatus is None:
            raise ContinuationError("CONTINUATION_CORRUPT")
        frame = pl.from_arrow(table)
        semantic = (
            frame.drop("evidenceRef") if isinstance(frame, pl.DataFrame) and "evidenceRef" in frame.columns else frame
        )
        if not isinstance(frame, pl.DataFrame) or contentHash(semantic) != entry.contentHash:
            raise ContinuationError("CONTINUATION_CORRUPT")


def _runOwnerPageProcess(
    session: _OwnerSession,
    *,
    deadline: float,
):
    from dartlab.dataHub.ownerProcess import runOwnerPage

    # IPC payload 는 durable state 상한 안에서 엔티티 목록을 함께 싣고, 넘치면 목록을
    # 빼고 보낸다. 목록이 실려 오면 자식은 universe 를 볼 필요가 없고, 빠지면 자식이
    # 재해소해 채운다. 덕분에 payload 는 universe 규모와 무관하게 상한 안에 머문다.
    try:
        requestPayload = _encodeProcessSession(session, maxBytes=MAX_STATE_BYTES)
    except ContinuationError:
        requestPayload = _encodeSession(session)
    outcome = runOwnerPage(
        requestPayload,
        publicDeadline=deadline,
    )
    if outcome.status == "ok" and outcome.page is not None and outcome.zeroLive:
        return outcome.page
    if outcome.status in {"budgetRejected", "timedOut"}:
        raise ContinuationError("CONTINUATION_TIMEOUT")
    if outcome.errorCode is not None and (
        outcome.errorCode.startswith("CONTINUATION_")
        or outcome.errorCode
        in {
            "OFFLINE_NETWORK_BLOCKED",
            "PAGEABLE_EAGER_WRITE_BLOCKED",
        }
    ):
        raise ContinuationError(outcome.errorCode)
    if outcome.status == "cleanupFailed":
        raise ContinuationError("CONTINUATION_OWNER_PROCESS_CLEANUP_FAILED")
    if outcome.status == "jobFailed":
        raise ContinuationError("CONTINUATION_OWNER_PROCESS_JOB_FAILED")
    raise ContinuationError("CONTINUATION_OWNER_PROCESS_FAILED")


def _materialize(
    state: ContinuationQueryState,
    *,
    deadline: float,
    sourcesPrevalidated: bool = False,
    hydratedSession: _OwnerSession | None = None,
) -> PageEnvelope:
    """다음 owner page 를 계산한다.

    `hydratedSession` 은 첫 page 전용이다. 호출자가 이미 엔티티가 채워진 세션을 들고
    있으면 durable state 를 다시 decode 해 universe 를 재해소하는 왕복을 건너뛴다.
    """

    requireDeadline(deadline)
    _validateQueryPayload(state.queryPayload)
    session = hydratedSession if hydratedSession is not None else _decodeSession(state.cursorPayload)
    if all(task.cursor >= task.entityCount for task in session.tasks):
        raise ContinuationError("CONTINUATION_CORRUPT")
    if not sourcesPrevalidated:
        _requireTaskSources(session, deadline=deadline)
    candidates = _candidates(session)
    if not candidates:
        raise ContinuationError("CONTINUATION_CORRUPT")
    processPage = _ownerFacade()._runOwnerPageProcess(
        session,
        deadline=deadline,
    )
    decoded = _decodePage(
        processPage.payload,
        claimedRowCount=processPage.rowCount,
        maxPageRows=session.pageMaxRows,
        maxPageBytes=session.pageMaxBytes,
        maxLogicalBytes=session.pageMaxLogicalBytes,
    )
    _requireDecodedPage(session, candidates, decoded)
    requireDeadline(deadline)
    _requireTaskContracts(session, deadline=deadline)
    _requireTaskSources(session, deadline=deadline)  # page 확정 직전 source 불변 재확인
    entries = decoded.entries
    nextTasks = _updatedTasks(session, entries)
    nextTaskIndex = _nextTaskIndex(session, entries)
    nextState = None
    if any(task.cursor < task.entityCount for task in nextTasks):
        nextState = ContinuationQueryState(
            state.queryPayload,
            _encodeSession(
                dataclasses.replace(
                    session,
                    tasks=nextTasks,
                    nextTaskIndex=nextTaskIndex,
                )
            ),
        )
    requireDeadline(deadline)
    return PageEnvelope(
        payload=processPage.payload,
        rowCount=decoded.facts.rowCount,
        nextState=nextState,
    )
