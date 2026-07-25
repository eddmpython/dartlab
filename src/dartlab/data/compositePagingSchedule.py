"""Composite outer scheduler의 budget 배분과 page materialization."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping, Sequence
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
from typing import Any

from dartlab.data.compositePagingModels import (
    _COMPOSITE_SCHEMA,
    _CONTROL_BASE_BYTES,
    _CONTROL_PER_LANE_BYTES,
    _FORMAT_VERSION,
    _MIN_CHILD_BYTES,
    _PAGE_KIND,
    _AdapterProtocol,
    _LaneAllocation,
    _LanePage,
)
from dartlab.data.compositePagingPayload import _encodeCompositeRows
from dartlab.data.compositePagingState import (
    _decodeSession,
    _encodeSession,
    _jsonLoad,
    _strictTree,
    _validateQueryPayload,
)
from dartlab.data.continuation import (
    ContinuationError,
    ContinuationPins,
    ContinuationQueryState,
    PageEnvelope,
    arrowSchemaDigest,
    bytesDigest,
    canonicalDigest,
    canonicalJsonBytes,
)
from dartlab.data.pagingRuntime import requireDeadline


def _outerPins(session: Mapping[str, Any], queryPayload: bytes) -> ContinuationPins:
    lanes = session["lanes"]
    if not isinstance(lanes, list):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return ContinuationPins(
        sourceDigest=canonicalDigest({str(lane["requestId"]): str(lane["sourceDigest"]) for lane in lanes}),
        queryDigest=bytesDigest(queryPayload),
        contractDigest=canonicalDigest(
            {
                "format": _PAGE_KIND,
                "version": _FORMAT_VERSION,
                "contractHash": session["contractHash"],
                "lanes": [
                    {
                        "requestId": lane["requestId"],
                        "requestIndex": lane["requestIndex"],
                        "assetId": lane["assetId"],
                        "assetVersionId": lane["assetVersionId"],
                        "laneKind": lane["laneKind"],
                        "contractDigest": lane["contractDigest"],
                        "schemaDigest": lane["schemaDigest"],
                    }
                    for lane in lanes
                ],
            }
        ),
        schemaDigest=arrowSchemaDigest(_COMPOSITE_SCHEMA),
    )


def _selectLaneIndexes(session: Mapping[str, Any]) -> tuple[int, ...]:
    lanes = session["lanes"]
    start = session["nextLaneIndex"]
    if not isinstance(lanes, list) or type(start) is not int:
        raise ContinuationError("CONTINUATION_CORRUPT")
    maxRows = int(session["pageMaxRows"])
    maxBytes = int(session["pageMaxBytes"])
    maxConcurrency = int(session["maxConcurrency"])
    maxByBytes = (maxBytes - _CONTROL_BASE_BYTES) // (_CONTROL_PER_LANE_BYTES + _MIN_CHILD_BYTES)
    target = min(
        sum(not bool(lane["done"]) for lane in lanes),
        maxRows,
        maxConcurrency,
        maxByBytes,
    )
    if target <= 0:
        raise ContinuationError("CONTINUATION_BYTE_BUDGET")
    selected: list[int] = []
    groups: set[str] = set()
    assetMarkets: set[tuple[str, str | None]] = set()
    for offset in range(len(lanes)):
        index = (start + offset) % len(lanes)
        lane = lanes[index]
        if lane["done"]:
            continue
        private = lane["privateState"]
        sealedEager = lane["laneKind"] == "eager" and isinstance(private, dict) and private.get("eagerMode") == "sealed"
        if sealedEager:
            if selected:
                break
            selected.append(index)
            break
        group = lane["concurrencyGroup"]
        market = None
        if isinstance(private, dict):
            queryValue = private.get("query")
            if isinstance(queryValue, dict):
                universe = queryValue.get("universe")
                if isinstance(universe, dict):
                    markets = universe.get("markets")
                    if isinstance(markets, list) and len(markets) == 1:
                        market = str(markets[0])
        assetMarket = (str(lane["assetId"]), market)
        if (group is not None and group in groups) or assetMarket in assetMarkets:
            if selected:
                break
            continue
        selected.append(index)
        assetMarkets.add(assetMarket)
        if group is not None:
            groups.add(group)
        if len(selected) >= target:
            break
    if not selected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return tuple(selected)


def _allocations(
    session: Mapping[str, Any],
    selected: Sequence[int],
) -> tuple[_LaneAllocation, ...]:
    count = len(selected)
    maxRows = int(session["pageMaxRows"])
    maxBytes = int(session["pageMaxBytes"])
    maxConcurrency = int(session["maxConcurrency"])
    controlBytes = _CONTROL_BASE_BYTES + _CONTROL_PER_LANE_BYTES * count
    distributable = maxBytes - controlBytes
    if distributable < _MIN_CHILD_BYTES * count:
        raise ContinuationError("CONTINUATION_BYTE_BUDGET")
    rowBase, rowExtra = divmod(maxRows, count)
    byteBase, byteExtra = divmod(distributable, count)
    concurrencyBase, concurrencyExtra = divmod(maxConcurrency, count)
    allocations = tuple(
        _LaneAllocation(
            maxRows=rowBase + (1 if index < rowExtra else 0),
            maxBytes=byteBase + (1 if index < byteExtra else 0),
            maxConcurrency=concurrencyBase + (1 if index < concurrencyExtra else 0),
        )
        for index in range(count)
    )
    if (
        any(item.maxRows <= 0 or item.maxBytes < _MIN_CHILD_BYTES or item.maxConcurrency <= 0 for item in allocations)
        or sum(item.maxRows for item in allocations) > maxRows
        or sum(item.maxBytes for item in allocations) + controlBytes > maxBytes
        or sum(item.maxConcurrency for item in allocations) > maxConcurrency
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return allocations


def _updatedSession(
    session: Mapping[str, Any],
    selected: Sequence[int],
    pages: Mapping[int, _LanePage],
) -> dict[str, Any]:
    copied = _jsonLoad(canonicalJsonBytes(session))
    if not isinstance(copied, dict) or not isinstance(copied["lanes"], list):
        raise ContinuationError("CONTINUATION_CORRUPT")
    lanes = copied["lanes"]
    for index in selected:
        lane = lanes[index]
        page = pages[index]
        if lane["done"]:
            raise ContinuationError("CONTINUATION_CORRUPT")
        if page.done != (page.nextPrivateState is None):
            raise ContinuationError("CONTINUATION_CORRUPT")
        if page.nextPrivateState is not None:
            lane["privateState"] = _strictTree(page.nextPrivateState)
        lane["done"] = page.done
        lane["attempted"] += page.attempted
        lane["succeededRows"] += page.succeededRows
        lane["succeededPartitions"] += page.succeededPartitions
        lane["failedItems"] += page.failedItems
        for code in page.gapCodes:
            lane["gapCounts"][code] = lane["gapCounts"].get(code, 0) + 1
    copied["nextLaneIndex"] = (selected[-1] + 1) % len(lanes)
    return _decodeSession(_encodeSession(copied))


def _materializeComposite(
    state: ContinuationQueryState,
    adapters: _AdapterProtocol,
    *,
    deadline: float,
) -> PageEnvelope:
    requireDeadline(deadline)
    _validateQueryPayload(state.queryPayload)
    session = _decodeSession(state.cursorPayload)
    lanes = session["lanes"]
    if not isinstance(lanes, list) or all(bool(lane["done"]) for lane in lanes):
        raise ContinuationError("CONTINUATION_CORRUPT")

    validations: dict[int, Any] = {}
    for index, lane in enumerate(lanes):
        if lane["done"]:
            continue
        requireDeadline(deadline)
        validations[index] = adapters.validate(lane, deadline=deadline)
    selected = _selectLaneIndexes(session)
    allocations = _allocations(session, selected)

    def execute(item: tuple[int, _LaneAllocation]) -> tuple[int, _LanePage]:
        """선택한 lane 하나를 배정 예산 안에서 실행한다."""
        index, allocation = item
        page = adapters.materialize(
            lanes[index],
            allocation,
            deadline=deadline,
            validation=validations[index],
        )
        if (
            not isinstance(page, _LanePage)
            or page.attempted > allocation.maxRows
            or len(page.payload) > allocation.maxBytes
            or page.succeededRows > allocation.maxRows
        ):
            raise ContinuationError("CONTINUATION_ROW_BUDGET")
        return index, page

    work = tuple(zip(selected, allocations, strict=True))
    pool = ThreadPoolExecutor(max_workers=len(work), thread_name_prefix="data-composite")
    futures = tuple(pool.submit(execute, item) for item in work)
    pending = set(futures)
    try:
        _done, pending = wait(
            futures,
            timeout=requireDeadline(deadline),
            return_when=ALL_COMPLETED,
        )
        if pending:
            raise ContinuationError("CONTINUATION_TIMEOUT")
        pages = dict(future.result() for future in futures)
    finally:
        for future in pending:
            future.cancel()
        pool.shutdown(wait=not pending, cancel_futures=bool(pending))
    requireDeadline(deadline)
    if sum(page.succeededRows for page in pages.values()) > session["pageMaxRows"]:
        raise ContinuationError("CONTINUATION_ROW_BUDGET")
    rows = []
    for index, allocation in zip(selected, allocations, strict=True):
        lane = lanes[index]
        page = pages[index]
        startDigest = canonicalDigest(lane["privateState"])
        nextDigest = canonicalDigest(page.nextPrivateState) if page.nextPrivateState is not None else None
        if not hmac.compare_digest(page.schemaDigest, lane["schemaDigest"]):
            raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
        rows.append(
            {
                "requestIndex": lane["requestIndex"],
                "requestId": lane["requestId"],
                "layer": lane["layer"],
                "laneKind": lane["laneKind"],
                "startStateDigest": startDigest,
                "nextStateDigest": nextDigest,
                "done": page.done,
                "attempted": page.attempted,
                "succeededRows": page.succeededRows,
                "succeededPartitions": page.succeededPartitions,
                "failedItems": page.failedItems,
                "gapCodes": page.gapCodes,
                "childMaxRows": allocation.maxRows,
                "childMaxBytes": allocation.maxBytes,
                "childMaxConcurrency": allocation.maxConcurrency,
                "childPayload": page.payload,
                "childClaimedRows": page.claimedRows,
                "childSchemaDigest": page.schemaDigest,
                "childPayloadDigest": hashlib.sha256(page.payload).hexdigest(),
            }
        )
    payload = _encodeCompositeRows(rows, maxBytes=session["pageMaxBytes"])
    updated = _updatedSession(session, selected, pages)
    nextState = None
    if any(not lane["done"] for lane in updated["lanes"]):
        nextState = ContinuationQueryState(state.queryPayload, _encodeSession(updated))
    return PageEnvelope(payload=payload, rowCount=len(rows), nextState=nextState)
