from __future__ import annotations

import os
import sqlite3
import time
from collections.abc import Mapping
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import polars as pl
import pytest

import dartlab
import dartlab.dataHub.execution as execution
import dartlab.dataHub.materialization.query as materializationQuery
import dartlab.dataHub.paging.composite as compositePaging
from dartlab.ai.tools.engineCall import _jsonableResult
from dartlab.dataHub.continuation import (
    ContinuationError,
    arrowSchemaDigest,
    canonicalDigest,
)
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataCatalogResult,
    DataPartition,
    DataQuery,
    DataResult,
)
from dartlab.dataHub.materialization.runtime import materializationStore
from dartlab.dataHub.paging.composite import (
    _EAGER_SCHEMA,
    _decodeEagerResult,
    _encodeEagerResult,
    _LaneAllocation,
    _LanePage,
)
from dartlab.webapi.browserApi import _json

pytestmark = pytest.mark.unit
dataCall: Any = getattr(dartlab, "data")


def processPublicOfflineReplay(
    home: str,
    receipt: dict[str, Any],
    resultQueue: Any,
) -> None:
    """Fresh process에서 public receipt replay의 CAS page read를 계측한다."""

    try:
        os.environ["DARTLAB_HOME"] = home
        databasePath = Path(home) / "dataHub" / "materializations" / "materializations.sqlite"
        with sqlite3.connect(databasePath) as connection:
            pageDigests = tuple(
                row[0]
                for row in connection.execute(
                    "SELECT payload_digest FROM materialization_pages WHERE generation_key=? ORDER BY ordinal",
                    (receipt["generationKey"],),
                ).fetchall()
            )
        materializationCas = Path(os.path.abspath(Path(home) / "dataHub" / "materializations" / "cas"))
        from dartlab.dataHub.continuation import ArtifactStore

        originalRead = ArtifactStore.readBytes
        pageReads: list[str] = []
        calls = {"catalog": 0, "owner": 0}

        def trackedRead(
            self: ArtifactStore,
            digest: str,
            *,
            maxBytes: int | None = None,
            budgetCode: str = "CONTINUATION_STATE_BUDGET",
        ) -> bytes:
            if self.root == materializationCas and digest in pageDigests:
                pageReads.append(digest)
            return originalRead(
                self,
                digest,
                maxBytes=maxBytes,
                budgetCode=budgetCode,
            )

        def forbiddenCatalog() -> Any:
            calls["catalog"] += 1
            raise AssertionError("offline replay가 catalog를 호출했습니다")

        def forbiddenAdapters() -> Any:
            calls["owner"] += 1
            raise AssertionError("offline replay가 owner를 호출했습니다")

        ArtifactStore.readBytes = trackedRead
        execution.buildCatalog = forbiddenCatalog
        compositePaging._ProductionAdapters = forbiddenAdapters
        try:
            publicData: Any = getattr(dartlab, "data")
            first = publicData(
                "query",
                query={
                    "materialization": {
                        "mode": "offline",
                        "receipt": receipt,
                    }
                },
            )
            firstReads = tuple(pageReads)
            pageReads.clear()
            if first.continuation is None:
                raise AssertionError("첫 replay page에 continuation이 없습니다")
            second = publicData(
                "query",
                query={"continuation": first.continuation},
            )
            secondReads = tuple(pageReads)
        finally:
            ArtifactStore.readBytes = originalRead
        resultQueue.put(
            (
                "ok",
                firstReads,
                secondReads,
                first.materializationReceipt,
                second.materializationReceipt,
                first.partitions[0].data["entityId"].to_list(),
                second.partitions[0].data["entityId"].to_list(),
                calls,
            )
        )
    except Exception as error:
        resultQueue.put(("error", type(error).__name__, str(error)))


class FakeAdapters:
    """두 outer page를 내는 deterministic composite owner."""

    def __init__(self):
        self.materializeCalls = 0

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
        return {
            "laneKind": "eager",
            "privateState": {"cursor": 0, "eventCount": 2},
            "sourceDigest": canonicalDigest({"requestId": requestId, "source": "v1"}),
            "contractDigest": canonicalDigest(
                {
                    "assetId": descriptor.assetId,
                    "assetVersionId": descriptor.assetVersionId,
                }
            ),
            "schemaDigest": arrowSchemaDigest(_EAGER_SCHEMA),
        }

    def validate(
        self,
        lane: Mapping[str, Any],
        *,
        deadline: float,
    ) -> None:
        del lane
        assert deadline > time.perf_counter()

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
        self.materializeCalls += 1
        private = lane["privateState"]
        cursor = int(private["cursor"])
        entityId = f"entity-{cursor}"
        frame = pl.DataFrame({"entityId": [entityId], "value": [cursor]})
        asset = AssetRef(str(lane["assetId"]), str(lane["assetVersionId"]))
        partition = DataPartition(
            asset=asset,
            projectionKind="factor",
            data=frame,
            schema=tuple((name, str(dtype)) for name, dtype in frame.schema.items()),
            rowCount=1,
            truncated=False,
            selector=(("subject", entityId),),
            temporalStatus="LATEST_ONLY",
            lineageRefs=("source:synthetic",),
            requestId=str(lane["requestId"]),
        )
        result = DataResult(
            status="ok",
            partitions=(partition,),
            assets=(asset,),
            snapshotId="catalog:test",
            contractHash="a" * 64,
            coverage=Coverage(1, 1, 1, 0),
            gaps=(),
            lineageRefs=("source:synthetic",),
            executionReceipts=(),
        )
        payload = _encodeEagerResult(result, maxBytes=allocation.maxBytes)
        nextCursor = cursor + 1
        done = nextCursor == 2
        return _LanePage(
            payload=payload,
            claimedRows=1,
            schemaDigest=arrowSchemaDigest(_EAGER_SCHEMA),
            nextPrivateState=(None if done else {"cursor": nextCursor, "eventCount": 2}),
            attempted=1,
            succeededRows=1,
            succeededPartitions=1,
            failedItems=0,
            gapCodes=(),
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


def descriptor() -> DataAssetDescriptor:
    return DataAssetDescriptor(
        assetId="synthetic.factor",
        assetVersionId="synthetic.factor:v1",
        owner="analysis",
        layer="L2",
        kind="factor",
        label="synthetic factor",
        description="materialization integration fixture",
        sourceRef="source:synthetic",
        queryable=True,
        executorKind="callable",
    )


def queryMapping(mode: str) -> dict[str, Any]:
    return {
        "requests": [
            {
                "assetId": "synthetic.factor",
                "requestId": "factor",
            }
        ],
        "budget": {
            "maxRows": 1,
            "maxBytes": 64 * 1024,
            "timeoutMs": 10_000,
            "maxAssets": 4,
            "maxSubjects": 100,
            "maxConcurrency": 1,
        },
        "materialization": mode,
    }


def installFixture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> FakeAdapters:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    asset = descriptor()
    catalog = DataCatalogResult(
        status="ok",
        assets=(asset,),
        snapshotId="catalog:test",
        coverage=Coverage(1, 1, 1, 0),
    )
    adapters = FakeAdapters()
    monkeypatch.setattr(execution, "buildCatalog", lambda: catalog)
    monkeypatch.setattr(
        compositePaging,
        "_ProductionAdapters",
        lambda: adapters,
    )
    return adapters


def testPublicMappingRefreshReuseOfflineAndStoredContinuation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = installFixture(monkeypatch, tmp_path)
    first = dataCall("query", query=queryMapping("refresh"))

    assert first.status == "partial"
    assert first.continuation is not None
    assert first.materializationReceipt is not None
    assert adapters.materializeCalls == 2
    receipt = first.materializationReceipt
    assert set(receipt) == {
        "generationKey",
        "terminalRootDigest",
        "pins",
    }

    second = dataCall(
        "query",
        query={"continuation": first.continuation},
    )
    assert second.continuation is None
    assert second.materializationReceipt == receipt
    assert second.partitions[0].data["entityId"].to_list() == ["entity-1"]
    assert adapters.materializeCalls == 2

    reused = dataCall("query", query=queryMapping("reuse"))
    assert reused.materializationReceipt == receipt
    assert adapters.materializeCalls == 2

    offline = dataCall(
        "query",
        query={
            "materialization": {
                "mode": "offline",
                "receipt": receipt,
            }
        },
    )
    assert offline.materializationReceipt == receipt
    assert adapters.materializeCalls == 2
    assert offline.partitions[0].data["entityId"].to_list() == ["entity-0"]


def testPublicMaterializedResumeMissingPageReturnsExactGap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installFixture(monkeypatch, tmp_path)
    built = dataCall("query", query=queryMapping("refresh"))
    assert built.continuation is not None
    receipt = built.materializationReceipt
    assert receipt is not None
    databasePath = tmp_path / "dataHub" / "materializations" / "materializations.sqlite"
    with sqlite3.connect(databasePath) as connection:
        digest = connection.execute(
            "SELECT payload_digest FROM materialization_pages WHERE generation_key=? AND ordinal=1",
            (receipt["generationKey"],),
        ).fetchone()[0]
    materializationStore().cas.pathForDigest(digest).unlink()

    resumed = dataCall(
        "query",
        query={"continuation": built.continuation},
    )

    assert resumed.status == "failed"
    assert resumed.gaps[0].code == "MATERIALIZATION_CORRUPT"
    assert built.continuation not in resumed.gaps[0].message
    retried = dataCall(
        "query",
        query={"continuation": built.continuation},
    )
    assert retried.status == "failed"
    assert retried.gaps[0].code == "MATERIALIZATION_CORRUPT"


@pytest.mark.parametrize("mode", ("reuse", "offline"))
def testPublicReuseOfflineCorruptFirstPageReturnsExactGap(
    mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installFixture(monkeypatch, tmp_path)
    built = dataCall("query", query=queryMapping("refresh"))
    receipt = built.materializationReceipt
    assert receipt is not None
    databasePath = tmp_path / "dataHub" / "materializations" / "materializations.sqlite"
    with sqlite3.connect(databasePath) as connection:
        digest = connection.execute(
            "SELECT payload_digest FROM materialization_pages WHERE generation_key=? AND ordinal=0",
            (receipt["generationKey"],),
        ).fetchone()[0]
    materializationStore().cas.pathForDigest(digest).write_bytes(b"corrupt")
    query = (
        queryMapping("reuse")
        if mode == "reuse"
        else {
            "materialization": {
                "mode": "offline",
                "receipt": receipt,
            }
        }
    )

    replayed = dataCall("query", query=query)

    assert replayed.status == "failed"
    assert replayed.gaps[0].code == "MATERIALIZATION_CORRUPT"


@pytest.mark.parametrize(
    ("mode", "methodName"),
    (
        ("reuse", "resultFromHandle"),
        ("offline", "resultFromReceipt"),
    ),
)
def testPublicReuseOfflineContinuationDeadlineReturnsExactGap(
    mode: str,
    methodName: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installFixture(monkeypatch, tmp_path)
    built = dataCall("query", query=queryMapping("refresh"))
    receipt = built.materializationReceipt
    assert receipt is not None

    def failDeadline(*_args: object, **_kwargs: object) -> None:
        raise ContinuationError("CONTINUATION_TIMEOUT")

    monkeypatch.setattr(materializationQuery, methodName, failDeadline)
    query = (
        queryMapping("reuse")
        if mode == "reuse"
        else {
            "materialization": {
                "mode": "offline",
                "receipt": receipt,
            }
        }
    )

    replayed = dataCall("query", query=query)

    assert replayed.status == "failed"
    assert replayed.gaps[0].code == "CONTINUATION_TIMEOUT"


def testPublicRefreshPreservesTypedProducerCauseAndAbortsBuilding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = installFixture(monkeypatch, tmp_path)

    def failMaterialize(*_args: object, **_kwargs: object) -> None:
        raise ContinuationError("CONTINUATION_SOURCE_STALE")

    monkeypatch.setattr(
        adapters,
        "materialize",
        failMaterialize,
    )
    result = dataCall("query", query=queryMapping("refresh"))

    assert result.status == "failed"
    assert result.gaps[0].code == "CONTINUATION_SOURCE_STALE"
    databasePath = tmp_path / "dataHub" / "materializations" / "materializations.sqlite"
    with sqlite3.connect(databasePath) as connection:
        assert (
            connection.execute("SELECT count(*) FROM materialization_generations WHERE status='BUILDING'").fetchone()[0]
            == 0
        )


@pytest.mark.parametrize(
    "failureCode",
    (
        "CONTINUATION_SOURCE_STALE",
        "OFFLINE_NETWORK_BLOCKED",
        "PAGEABLE_EAGER_WRITE_BLOCKED",
    ),
)
def testPublicRefreshPreservesTypedResumeCauseAndAbortsBuilding(
    failureCode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = installFixture(monkeypatch, tmp_path)
    originalMaterialize = adapters.materialize

    def failSecondPage(
        *args: object,
        **kwargs: object,
    ) -> _LanePage:
        if adapters.materializeCalls == 1:
            raise ContinuationError(failureCode)
        return originalMaterialize(*args, **kwargs)

    monkeypatch.setattr(adapters, "materialize", failSecondPage)
    result = dataCall("query", query=queryMapping("refresh"))

    assert result.status == "failed"
    assert result.gaps[0].code == failureCode
    assert adapters.materializeCalls == 1
    databasePath = tmp_path / "dataHub" / "materializations" / "materializations.sqlite"
    with sqlite3.connect(databasePath) as connection:
        assert (
            connection.execute("SELECT count(*) FROM materialization_generations WHERE status='BUILDING'").fetchone()[0]
            == 0
        )
        assert connection.execute("SELECT count(*) FROM materialization_pages").fetchone()[0] == 0


def testStructuredReceiptSurvivesEngineAndBrowserSerialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installFixture(monkeypatch, tmp_path)
    result = dataCall("query", query=queryMapping("refresh"))
    receipt = result.materializationReceipt
    assert receipt is not None

    enginePayload = _jsonableResult(result)
    browserPayload = _json(result)
    assert enginePayload["materializationReceipt"] == receipt
    assert browserPayload["materializationReceipt"] == receipt


def testFreshProcessReceiptReplayReadsOneMaterializedPagePerCall(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = installFixture(monkeypatch, tmp_path)
    built = dataCall("query", query=queryMapping("refresh"))
    receipt = built.materializationReceipt
    assert receipt is not None
    databasePath = tmp_path / "dataHub" / "materializations" / "materializations.sqlite"
    with sqlite3.connect(databasePath) as connection:
        pageDigests = tuple(
            row[0]
            for row in connection.execute(
                "SELECT payload_digest FROM materialization_pages WHERE generation_key=? ORDER BY ordinal",
                (receipt["generationKey"],),
            ).fetchall()
        )
    assert len(pageDigests) == 2

    context = get_context("spawn")
    resultQueue = context.Queue()
    process = context.Process(
        target=processPublicOfflineReplay,
        args=(str(tmp_path), receipt, resultQueue),
    )
    process.start()
    process.join(timeout=45.0)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5.0)
        pytest.fail("spawned public offline replay가 제한 시간 안에 종료되지 않았습니다")

    assert process.exitcode == 0
    assert resultQueue.get(timeout=5.0) == (
        "ok",
        (pageDigests[0],),
        (pageDigests[1],),
        receipt,
        receipt,
        ["entity-0"],
        ["entity-1"],
        {"catalog": 0, "owner": 0},
    )
    assert adapters.materializeCalls == 2
