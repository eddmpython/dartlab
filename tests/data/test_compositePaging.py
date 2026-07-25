"""Mixed Data Workbench outer continuation acceptance locks."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Literal

import polars as pl
import pytest

from dartlab.data.compositePaging import (
    _EAGER_SCHEMA,
    _decodeEagerResult,
    _decodeSession,
    _encodeEagerResult,
    _encodeSession,
    _LaneAllocation,
    _LanePage,
    _laneTree,
    _packLowerSession,
    _ProductionAdapters,
    _queryPayload,
    _unpackLowerSession,
    _validateCompositePayload,
    executeInitialCompositePaging,
    resumeCompositePaging,
)
from dartlab.data.continuation import (
    ContinuationError,
    ContinuationQueryState,
    arrowSchemaDigest,
    canonicalDigest,
    canonicalJsonBytes,
    encodeQueryState,
)
from dartlab.data.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataGap,
    DataPartition,
    DataQuery,
    DataRequest,
    DataResult,
    FactorProjection,
    QueryBudget,
    ResourceProjection,
    TimeContext,
    UniverseSelection,
)
from dartlab.data.pagingRuntime import MAX_STATE_BYTES, continuationStore


class _FakeAdapters:
    """Strict JSON cursor로 scheduler만 검증하는 private test adapter."""

    def __init__(
        self,
        events: Mapping[str, tuple[str, ...]],
        *,
        sourceVersion: str = "v1",
        delays: Mapping[str, float] | None = None,
    ):
        self.events = dict(events)
        self.sourceVersion = sourceVersion
        self.delays = {} if delays is None else dict(delays)
        self.validationCalls: list[str] = []
        self.materializeCalls: list[str] = []
        self.allocations: list[_LaneAllocation] = []

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
        del requestIndex, query, snapshotId, contractHash
        assert deadline > time.perf_counter()
        events = self.events[requestId]
        return {
            "laneKind": descriptor.owner,
            "privateState": {"cursor": 0, "eventCount": len(events)},
            "sourceDigest": self._sourceDigest(requestId),
            "contractDigest": canonicalDigest({"requestId": requestId, "assetVersionId": descriptor.assetVersionId}),
            "schemaDigest": arrowSchemaDigest(_EAGER_SCHEMA),
        }

    def validate(self, lane: Mapping[str, Any], *, deadline: float) -> None:
        assert deadline > time.perf_counter()
        requestId = str(lane["requestId"])
        self.validationCalls.append(requestId)
        if lane["sourceDigest"] != self._sourceDigest(requestId):
            from dartlab.data.continuation import ContinuationError

            raise ContinuationError("CONTINUATION_SOURCE_STALE")

    def materialize(
        self,
        lane: Mapping[str, Any],
        allocation: _LaneAllocation,
        *,
        deadline: float,
        validation: Any,
    ) -> _LanePage:
        del validation
        assert deadline > time.perf_counter()
        requestId = str(lane["requestId"])
        self.materializeCalls.append(requestId)
        self.allocations.append(allocation)
        delay = self.delays.get(requestId, 0.0)
        if delay:
            time.sleep(delay)
        private = lane["privateState"]
        cursor = int(private["cursor"])
        event = self.events[requestId][cursor]
        descriptor = AssetRef(str(lane["assetId"]), str(lane["assetVersionId"]))
        if event == "gap":
            partitions = ()
            gaps = (
                DataGap(
                    "SYNTHETIC_GAP",
                    "synthetic gap",
                    descriptor.assetId,
                    requestId=requestId,
                ),
            )
        else:
            frame = pl.DataFrame({"entityId": [event], "value": [cursor]})
            partitions = (
                DataPartition(
                    asset=descriptor,
                    projectionKind="factor",
                    data=frame,
                    schema=tuple((name, str(dtype)) for name, dtype in frame.schema.items()),
                    rowCount=1,
                    truncated=False,
                    selector=(("subject", event),),
                    temporalStatus="LATEST_ONLY",
                    lineageRefs=(f"source:{requestId}",),
                    requestId=requestId,
                ),
            )
            gaps = ()
        result = DataResult(
            status="failed" if gaps else "ok",
            partitions=partitions,
            assets=(descriptor,),
            snapshotId="catalog:test",
            contractHash="a" * 64,
            coverage=Coverage(1, 1, len(partitions), len(gaps)),
            gaps=gaps,
            lineageRefs=tuple(ref for partition in partitions for ref in partition.lineageRefs),
            executionReceipts=(),
            continuation=None,
        )
        payload = _encodeEagerResult(result, maxBytes=allocation.maxBytes)
        nextCursor = cursor + 1
        done = nextCursor == len(self.events[requestId])
        return _LanePage(
            payload=payload,
            claimedRows=1,
            schemaDigest=arrowSchemaDigest(_EAGER_SCHEMA),
            nextPrivateState=None if done else {"cursor": nextCursor, "eventCount": len(self.events[requestId])},
            attempted=1,
            succeededRows=len(partitions),
            succeededPartitions=len(partitions),
            failedItems=len(gaps),
            gapCodes=tuple(gap.code for gap in gaps),
            done=done,
        )

    def result(
        self,
        lane: Mapping[str, Any],
        row: Mapping[str, Any],
        *,
        pageRef: str,
    ) -> DataResult:
        del lane, pageRef
        return _decodeEagerResult(row["childPayload"])

    def _sourceDigest(self, requestId: str) -> str:
        return canonicalDigest({"requestId": requestId, "sourceVersion": self.sourceVersion})


def _descriptor(index: int, laneKind: str = "eager") -> DataAssetDescriptor:
    return DataAssetDescriptor(
        assetId=f"asset.{index}",
        assetVersionId=f"asset-version:{index}",
        owner=laneKind,
        layer=("L1", "L1.5", "L2")[index % 3],
        kind="factor",
        label=f"asset {index}",
        description="synthetic",
        sourceRef=f"source:{index}",
        queryable=True,
        executorKind="callable",
    )


def _resolved(count: int, query: DataQuery) -> tuple[tuple[str, DataAssetDescriptor, DataQuery], ...]:
    kinds = ("resource", "eager", "owner")
    return tuple((f"request{index}", _descriptor(index, kinds[index % len(kinds)]), query) for index in range(count))


def _query(
    *,
    rows: int = 1,
    concurrency: int = 1,
    completeness: Literal["allowPartial", "requireComplete"] = "allowPartial",
) -> DataQuery:
    return DataQuery(
        budget=QueryBudget(
            maxRows=rows,
            maxBytes=64 * 1024,
            timeoutMs=10_000,
            maxAssets=8,
            maxSubjects=100,
            maxConcurrency=concurrency,
        ),
        completeness=completeness,
    )


def _first(
    query: DataQuery,
    resolved: tuple[tuple[str, DataAssetDescriptor, DataQuery], ...],
    adapters: _FakeAdapters,
) -> DataResult:
    return executeInitialCompositePaging(
        (),
        query,
        requestedAssets=len(resolved),
        snapshotId="catalog:test",
        contractHash="a" * 64,
        resolved=resolved,
        hasPlanningGaps=False,
        deadline=time.perf_counter() + 10,
        _adapters=adapters,
    )


def _resumeInSpawn(
    home: str,
    token: str,
    events: Mapping[str, tuple[str, ...]],
) -> tuple[str | None, tuple[str | None, ...], tuple[str, ...], str]:
    os.environ["DARTLAB_HOME"] = home
    adapters = _FakeAdapters(events)
    page = resumeCompositePaging(
        token,
        deadline=time.perf_counter() + 10,
        _adapters=adapters,
    )
    return (
        page.continuation,
        tuple(partition.requestId for partition in page.partitions),
        tuple(adapters.materializeCalls),
        page.status,
    )


def testMixedKindsUseOneOuterTokenAndRoundRobinAcrossRestart(tmp_path, monkeypatch):
    """Resource, eager, owner lane이 outer token 하나로 공정 순회한다."""

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    query = _query()
    resolved = _resolved(3, query)
    events = {
        "request0": ("A0", "A1"),
        "request1": ("B0", "B1"),
        "request2": ("C0", "C1"),
    }
    firstAdapters = _FakeAdapters(events)
    first = _first(query, resolved, firstAdapters)
    assert first.status == "partial"
    assert first.continuation is not None
    assert [partition.requestId for partition in first.partitions] == ["request0"]

    token = first.continuation
    assert token is not None
    pages = [first]
    with ProcessPoolExecutor(max_workers=1, mp_context=get_context("spawn")) as pool:
        token, requestIds, spawnedCalls, spawnedStatus = pool.submit(
            _resumeInSpawn,
            str(tmp_path),
            token,
            events,
        ).result(timeout=30)
    assert requestIds == ("request1",)
    assert spawnedCalls == ("request1",)
    assert spawnedStatus == "partial"
    restarted = _FakeAdapters(events)
    while token is not None:
        page = resumeCompositePaging(
            token,
            deadline=time.perf_counter() + 10,
            _adapters=restarted,
        )
        pages.append(page)
        token = page.continuation

    assert firstAdapters.materializeCalls + list(spawnedCalls) + restarted.materializeCalls == [
        "request0",
        "request1",
        "request2",
        "request0",
        "request1",
        "request2",
    ]
    assert all(
        [partition.requestId for partition in page.partitions]
        == sorted(partition.requestId for partition in page.partitions if partition.requestId is not None)
        for page in pages
    )


def testCommittedOuterReplayTouchesNoAdapterAndPersistsNoBearer(tmp_path, monkeypatch):
    """Committed replay는 source와 owner를 다시 부르지 않고 token 원문을 저장하지 않는다."""

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    query = _query()
    resolved = _resolved(2, query)
    adapters = _FakeAdapters({"request0": ("A",), "request1": ("B",)})
    first = _first(query, resolved, adapters)
    token = first.continuation
    assert token is not None
    second = resumeCompositePaging(
        token,
        deadline=time.perf_counter() + 10,
        _adapters=adapters,
    )
    before = (len(adapters.validationCalls), len(adapters.materializeCalls))

    replay = resumeCompositePaging(
        token,
        deadline=time.perf_counter() + 10,
        _adapters=adapters,
    )

    assert (len(adapters.validationCalls), len(adapters.materializeCalls)) == before
    assert replay.partitions[0].toPolars().equals(second.partitions[0].toPolars())
    root = Path(tmp_path) / "data-workbench" / "continuations"
    stored = b"".join(path.read_bytes() for path in root.rglob("*") if path.is_file())
    assert token.encode("ascii") not in stored


def testEveryActiveSourceValidatesBeforeAnyLaneRuns(tmp_path, monkeypatch):
    """한 active lane source drift가 모든 materialize와 outer commit을 막는다."""

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    query = _query()
    resolved = _resolved(2, query)
    events = {"request0": ("A",), "request1": ("B",)}
    original = _FakeAdapters(events)
    first = _first(query, resolved, original)
    token = first.continuation
    assert token is not None
    stale = _FakeAdapters(events, sourceVersion="v2")

    failed = resumeCompositePaging(
        token,
        deadline=time.perf_counter() + 10,
        _adapters=stale,
    )

    assert failed.status == "failed"
    assert failed.gaps[0].code == "CONTINUATION_SOURCE_STALE"
    assert stale.materializeCalls == []
    recovered = resumeCompositePaging(
        token,
        deadline=time.perf_counter() + 10,
        _adapters=_FakeAdapters(events),
    )
    assert recovered.status == "ok"


def testFailureAdvancesCursorAndCumulativeGapCoverage(tmp_path, monkeypatch):
    """Structured gap도 cursor를 전진시키고 cumulative state에 보존한다."""

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    query = _query()
    resolved = _resolved(1, query)
    adapters = _FakeAdapters({"request0": ("gap", "A")})
    first = _first(query, resolved, adapters)
    assert first.gaps[0].code == "SYNTHETIC_GAP"
    token = first.continuation
    assert token is not None
    store = continuationStore(
        deadline=time.perf_counter() + 10,
        payloadValidator=_validateCompositePayload,
        runMaintenance=False,
    )
    context = store.loadContext(token)
    state = _decodeSession(context.state.cursorPayload)
    lane = state["lanes"][0]
    assert lane["attempted"] == 1
    assert lane["failedItems"] == 1
    assert lane["gapCounts"] == {"SYNTHETIC_GAP": 1}

    final = resumeCompositePaging(
        token,
        deadline=time.perf_counter() + 10,
        _adapters=adapters,
    )
    assert final.status == "partial"
    assert final.gaps == ()
    assert final.coverage.succeededPartitions == 1
    assert final.coverage.failedPartitions == 1
    assert final.partitions[0].toPolars()["entityId"].to_list() == ["A"]
    assert adapters.materializeCalls == ["request0", "request0"]


def testTotalBudgetsAndRequestOrderHoldUnderParallelCompletion(tmp_path, monkeypatch):
    """Lane allocation 합과 결과 순서가 outer budget과 request order를 지킨다."""

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    query = _query(rows=6, concurrency=3)
    resolved = _resolved(3, query)
    adapters = _FakeAdapters(
        {"request0": ("A",), "request1": ("B",), "request2": ("C",)},
        delays={"request0": 0.04, "request1": 0.02},
    )

    result = _first(query, resolved, adapters)

    assert result.status == "ok"
    assert [partition.requestId for partition in result.partitions] == [
        "request0",
        "request1",
        "request2",
    ]
    assert sum(item.maxRows for item in adapters.allocations) <= query.budget.maxRows
    assert sum(item.maxConcurrency for item in adapters.allocations) <= query.budget.maxConcurrency
    assert all(item.maxBytes > 0 for item in adapters.allocations)


def testHungLaneCannotCommitSuccessPastOuterDeadline(tmp_path, monkeypatch):
    """비협조 lane이 timeout 뒤 끝나도 outer page 성공으로 commit되지 않는다."""

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    query = _query()
    resolved = _resolved(1, query)
    adapters = _FakeAdapters({"request0": ("A",)}, delays={"request0": 2.0})
    started = time.perf_counter()

    result = executeInitialCompositePaging(
        (),
        query,
        requestedAssets=1,
        snapshotId="catalog:test",
        contractHash="a" * 64,
        resolved=resolved,
        hasPlanningGaps=False,
        deadline=started + 0.5,
        _adapters=adapters,
    )

    assert result.status == "failed"
    assert result.gaps[0].code == "CONTINUATION_TIMEOUT"
    assert time.perf_counter() - started < 1.25


def testLargeLowerSessionsUseBoundedExactCompressedState():
    """KR+US 규모 lower session 둘도 outer state budget 안에서 exact 복원된다."""

    raw = canonicalJsonBytes(
        {
            "entities": [
                {
                    "entityId": f"{index:010d}",
                    "sourceEntityId": f"{index:010d}",
                    "params": [["fiscalYearEndMonth", "12"]],
                }
                for index in range(5_500)
            ]
        }
    )
    assert 300_000 < len(raw) <= MAX_STATE_BYTES
    packed = _packLowerSession(raw)
    assert _unpackLowerSession(packed) == raw
    assert len(canonicalJsonBytes({"us": packed, "kr": packed})) < MAX_STATE_BYTES

    tampered = dict(packed) | {"rawDigest": "0" * 64}
    with pytest.raises(ContinuationError, match="무결성"):
        _unpackLowerSession(tampered)


def testActualKrUsOwnerPlansFitOneOuterState(monkeypatch):
    """현재 KR+US owner plan을 source 갱신 없이 한 outer state에 봉인한다."""

    import dartlab.core.dataLoader as dataLoader
    import dartlab.data.ownerPaging as ownerPaging
    from dartlab.data.catalog import buildCatalog

    monkeypatch.setattr(
        dataLoader,
        "updateEdgarListedUniverse",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("Data Workbench universe plan이 source를 갱신했습니다")),
    )
    monkeypatch.setattr(
        ownerPaging,
        "_resourceSourcePin",
        lambda _assetId, _category: "resource-source-full:" + "1" * 64,
    )
    catalog = buildCatalog()
    byId = {descriptor.assetId: descriptor for descriptor in catalog.assets}
    budget = QueryBudget(maxRows=100_000, maxBytes=64 * 1024 * 1024, maxAssets=3)
    plans = (
        (
            "us",
            byId["analysis.edgarFinancialFeatures"],
            DataQuery(
                universe=UniverseSelection(("US",)),
                projection=FactorProjection(),
                time=TimeContext(knownAt="20250201"),
                budget=budget,
            ),
        ),
        (
            "kr",
            byId["analysis.dartFinancialFeatures"],
            DataQuery(
                universe=UniverseSelection(("KR",)),
                projection=FactorProjection(),
                time=TimeContext(knownAt="20250201"),
                budget=budget,
            ),
        ),
        (
            "locator",
            byId["resource.finance"],
            DataQuery(
                subjects=("005930",),
                projection=ResourceProjection(),
                budget=budget,
            ),
        ),
    )
    adapters = _ProductionAdapters()
    lanes = []
    lowerSizes = {}
    entityCounts = {}
    for index, (requestId, descriptor, activeQuery) in enumerate(plans):
        lane = _laneTree(
            adapters.plan(
                requestId,
                index,
                descriptor,
                activeQuery,
                snapshotId=catalog.snapshotId,
                contractHash="a" * 64,
                deadline=time.perf_counter() + 30,
            ),
            requestId=requestId,
            requestIndex=index,
            descriptor=descriptor,
        )
        lanes.append(lane)
        if lane["laneKind"] == "owner":
            raw = _unpackLowerSession(lane["privateState"]["packedSession"])
            decoded = ownerPaging._decodeSession(raw)
            assert ownerPaging._encodeSession(decoded) == raw
            lowerSizes[requestId] = len(raw)
            entityCounts[requestId] = len(decoded.tasks[0].entities)
    outerQuery = DataQuery(
        requests=tuple(
            DataRequest(
                descriptor.assetId,
                requestId,
                subjects=activeQuery.subjects,
                universe=activeQuery.universe,
                projection=activeQuery.projection,
                time=activeQuery.time,
            )
            for requestId, descriptor, activeQuery in plans
        ),
        budget=budget,
    )
    cursorPayload = _encodeSession(
        {
            "version": 1,
            "pageKind": "composite",
            "snapshotId": catalog.snapshotId,
            "contractHash": "a" * 64,
            "requestedAssets": 3,
            "resolvedAssets": 3,
            "pageMaxRows": budget.maxRows,
            "pageMaxBytes": budget.maxBytes,
            "pageTimeoutMs": budget.timeoutMs,
            "maxConcurrency": budget.maxConcurrency,
            "nextLaneIndex": 0,
            "lanes": lanes,
        }
    )
    encodedState = encodeQueryState(
        ContinuationQueryState(_queryPayload((), outerQuery), cursorPayload),
        maxBytes=MAX_STATE_BYTES,
    )

    assert set(entityCounts) == {"us", "kr"}
    assert entityCounts["us"] >= 5_000
    assert entityCounts["kr"] >= 2_000
    assert lowerSizes["us"] > 450_000
    assert lowerSizes["kr"] > 150_000
    assert len(cursorPayload) < 120_000
    assert len(encodedState) < MAX_STATE_BYTES


def testEagerNativeScalarAndBytesRoundTripWithoutPickle():
    """Native scalar와 bytes는 type tag로 deterministic replay된다."""

    asset = AssetRef("asset.scalar", "asset-version:scalar")
    for value in (None, True, 42, 3.5, "hello", b"\x00\x01"):
        partition = DataPartition(
            asset=asset,
            projectionKind="native",
            data=value,
            schema=(("value", type(value).__name__),),
            rowCount=1,
            truncated=False,
            selector=(),
            temporalStatus="LATEST_ONLY",
            lineageRefs=(),
            requestId="scalar",
        )
        result = DataResult(
            status="ok",
            partitions=(partition,),
            assets=(asset,),
            snapshotId="catalog:test",
            contractHash="a" * 64,
            coverage=Coverage(1, 1, 1, 0),
            gaps=(),
            lineageRefs=(),
            executionReceipts=(),
        )

        decoded = _decodeEagerResult(_encodeEagerResult(result, maxBytes=64 * 1024))

        assert type(decoded.partitions[0].data) is type(value)
        assert decoded.partitions[0].data == value


def testRequireCompleteMixedPagingRemainsFailClosed(tmp_path, monkeypatch):
    """Pageable mixed query의 requireComplete는 실행 전 거부된다."""

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    query = _query(completeness="requireComplete")
    resolved = _resolved(2, query)
    adapters = _FakeAdapters({"request0": ("A",), "request1": ("B",)})

    result = _first(query, resolved, adapters)

    assert result.status == "failed"
    assert result.gaps[0].code == "PAGEABLE_REQUIRE_COMPLETE_UNSUPPORTED"
    assert adapters.materializeCalls == []
