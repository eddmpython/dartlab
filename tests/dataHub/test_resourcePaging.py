"""Public Data Workbench resource multiplex paging regression tests."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal, cast

import polars as pl
import pyarrow as pa
import pytest

from dartlab.dataHub.contracts import (
    Coverage,
    DataAssetDescriptor,
    DataCatalogResult,
    DataQuery,
    DataRequest,
    NativeProjection,
    QueryBudget,
    ResourceProjection,
)
from dartlab.providers.resourceStream import ResourceCursorV2, ResourceReadReceipt, ResourceReadRequest

pytestmark = pytest.mark.unit


def _descriptor(
    assetId: str,
    *,
    executionMode: Literal["resourceCompanyShard", "resourceBulk"],
) -> DataAssetDescriptor:
    category = assetId.removeprefix("resource.")
    return DataAssetDescriptor(
        assetId=assetId,
        assetVersionId=f"asset:{hashlib.sha256(assetId.encode()).hexdigest()}",
        owner="providers",
        layer="L1",
        kind="resource",
        label=assetId,
        description=assetId,
        sourceRef=f"dataRelease:{category}",
        queryable=True,
        visibility="PUBLIC",
        executorKind="resource",
        executorAxis=category,
        subjectParam="subject",
        selectorKind="subject",
        executionMode=executionMode,
        universeMarkets=("US",) if assetId == "resource.edgar" else ("KR",),
        metadata=(
            ("shardKind", "company" if executionMode == "resourceCompanyShard" else "bulk"),
            ("sourceProvider", "edgar" if assetId == "resource.edgar" else "dart"),
        ),
    )


def _catalog(*assets: DataAssetDescriptor) -> DataCatalogResult:
    return DataCatalogResult(
        status="ok",
        assets=assets,
        snapshotId="data-snapshot:" + "a" * 64,
        coverage=Coverage(len(assets), len(assets), 0, 0),
    )


@dataclass
class _SyntheticOwner:
    tables: dict[str, pa.Table]
    sourcePins: dict[str, str]
    calls: list[tuple[str, int, int]]
    tamper: str | None = None

    @staticmethod
    def _matches(row: dict[str, object], request: ResourceReadRequest) -> bool:
        for predicate in request.predicates:
            current = cast(Any, row.get(predicate.column))
            expected = cast(Any, predicate.value)
            if predicate.operator == "eq":
                matches = current == expected
            elif predicate.operator == "ne":
                matches = current != expected
            elif predicate.operator == "gt":
                matches = current is not None and current > expected
            elif predicate.operator == "ge":
                matches = current is not None and current >= expected
            elif predicate.operator == "lt":
                matches = current is not None and current < expected
            elif predicate.operator == "le":
                matches = current is not None and current <= expected
            else:
                matches = current in expected
            if not matches:
                return False
        return True

    @classmethod
    def create(cls) -> _SyntheticOwner:
        tables = {
            "resource.finance": pa.table({"companyId": ["K1", "K2", "K3", "K4", "K5"], "value": [1, 2, 3, 4, 5]}),
            "resource.edgar": pa.table({"cik": [10, 20, 30, 40], "valueUsd": [1.5, 2.5, 3.5, 4.5]}),
        }
        sourcePins = {
            assetId: f"resource-source-full:{hashlib.sha256(assetId.encode()).hexdigest()}" for assetId in tables
        }
        return cls(tables, sourcePins, [])

    def describe(self, resourceId: str, category: str, cachePath: Path):
        del cachePath
        table = self.tables[resourceId]
        return SimpleNamespace(
            resourceId=resourceId,
            category=category,
            sourcePin=self.sourcePins[resourceId],
            schemaFields=tuple((field.name, str(field.type)) for field in table.schema),
            commonSchemaFields=tuple((field.name, str(field.type)) for field in table.schema),
            shardCount=table.num_rows,
            totalBytes=table.nbytes,
            cacheHit=True,
        )

    def read(self, resourceId: str, category: str, requestMapping: dict[str, object], cachePath: Path):
        del cachePath
        request = ResourceReadRequest.fromMapping(requestMapping)
        table = self.tables[resourceId]
        projected = table.select(request.columns)
        startCursor = request.cursor or ResourceCursorV2(0, 0)
        cursor = startCursor
        sourceRows = table.to_pylist()
        selectedRows: list[dict[str, object]] = []
        selectedOrdinals: list[int] = []
        scannedShardCount = 0
        while cursor.shardOrdinal < table.num_rows and scannedShardCount < request.maxShards:
            scannedShardCount += 1
            if cursor.physicalRowInShard not in {0, 1}:
                raise ValueError("synthetic physical cursor가 유효하지 않습니다")
            if cursor.physicalRowInShard == 0 and self._matches(sourceRows[cursor.shardOrdinal], request):
                selectedRows.append({column: sourceRows[cursor.shardOrdinal][column] for column in request.columns})
                selectedOrdinals.append(cursor.shardOrdinal)
            cursor = ResourceCursorV2(cursor.shardOrdinal + 1, 0)
            if len(selectedRows) >= request.maxRows:
                break
        if scannedShardCount == 0:
            raise ValueError("synthetic cursor가 source 끝을 넘었습니다")
        selected = pa.Table.from_pylist(selectedRows, schema=projected.schema)
        if request.includeSourcePath:
            selected = selected.append_column(
                "sourcePath",
                pa.array([f"{category}-{index}" for index in selectedOrdinals]),
            )
        sink = pa.BufferOutputStream()
        with pa.ipc.new_stream(sink, selected.schema, options=pa.ipc.IpcWriteOptions(compression=None)) as writer:
            batches = selected.to_batches(max_chunksize=max(1, request.maxRows))
            if batches:
                writer.write_batch(batches[0])
            else:
                writer.write_batch(
                    pa.RecordBatch.from_arrays(
                        [pa.array([], type=field.type) for field in selected.schema],
                        schema=selected.schema,
                    )
                )
        payload = sink.getvalue().to_pybytes()
        nextCursor = None if cursor.shardOrdinal >= table.num_rows else cursor
        receipt = ResourceReadReceipt(
            sourcePin=self.sourcePins[resourceId],
            queryPin=request.queryPin(resourceId),
            integrityMode="full",
            startRow=request.startRow,
            nextRow=request.startRow + selected.num_rows,
            batchCount=1 if selected.num_rows else 0,
            rowCount=selected.num_rows,
            byteCount=selected.nbytes,
            truncated=nextCursor is not None,
            startCursor=startCursor,
            nextCursor=nextCursor,
            scannedShardCount=scannedShardCount,
        )
        actualSchema = tuple((field.name, str(field.type)) for field in selected.schema)
        encodedCount = len(payload)
        receiptOverrides: dict[str, object] = {}
        if self.tamper == "rowCount":
            receiptOverrides["rowCount"] = receipt.rowCount + 1
        elif self.tamper == "sourcePin":
            receiptOverrides["sourcePin"] = "resource-source-full:" + "f" * 64
        elif self.tamper == "schema":
            actualSchema = (("wrong", "string"),)
        elif self.tamper == "encodedByteCount":
            encodedCount += 1
        elif self.tamper == "byteCount":
            receiptOverrides["byteCount"] = request.maxBytes + 1
        elif self.tamper == "rowCountBool":
            receiptOverrides["rowCount"] = cast(Any, True)
        elif self.tamper == "truncatedType":
            receiptOverrides["truncated"] = cast(Any, "yes")
        elif self.tamper == "cursorNoProgress":
            receiptOverrides["nextCursor"] = receipt.startCursor
            receiptOverrides["truncated"] = True
        elif self.tamper == "cursorBackward":
            receiptOverrides["nextCursor"] = ResourceCursorV2(0, 0).toMapping()
            receiptOverrides["truncated"] = True
        elif self.tamper == "scannedShardCount":
            receiptOverrides["scannedShardCount"] = request.maxShards + 1
        if receiptOverrides:
            receipt = cast(
                Any,
                SimpleNamespace(**(receipt.toMapping() | receiptOverrides)),
            )
        self.calls.append((resourceId, request.startRow, selected.num_rows))
        return SimpleNamespace(
            resourceId=resourceId,
            category=category,
            receipt=receipt,
            actualSchemaFields=actualSchema,
            encodedBytes=payload,
            encodedByteCount=encodedCount,
        )


@pytest.fixture
def owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _SyntheticOwner:
    import dartlab.dataHub.execution as executionModule
    import dartlab.providers.resourceStream.workbench as workbenchModule

    value = _SyntheticOwner.create()
    assets = (
        _descriptor("resource.finance", executionMode="resourceCompanyShard"),
        _descriptor("resource.edgar", executionMode="resourceBulk"),
        _descriptor("resource.scan", executionMode="resourceBulk"),
        DataAssetDescriptor(
            assetId="scan.governance",
            assetVersionId="asset:" + "b" * 64,
            owner="scan",
            layer="L1.5",
            kind="native",
            label="governance",
            description="governance",
            sourceRef="python:scan",
            queryable=True,
            executorKind="engineAxis",
            executorAxis="governance",
            executionMode="ownerBulk",
        ),
    )
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path / "dartlab-home"))
    monkeypatch.setattr(executionModule, "buildCatalog", lambda: _catalog(*assets))
    monkeypatch.setattr(workbenchModule, "describeResource", value.describe)
    monkeypatch.setattr(workbenchModule, "readResourcePage", value.read)

    def prepare(resourceId: str, category: str, cachePath: Path):
        return SimpleNamespace(
            description=value.describe(resourceId, category, cachePath),
            read=lambda requestMapping: value.read(resourceId, category, requestMapping, cachePath),
        )

    monkeypatch.setattr(workbenchModule, "prepareResourceRead", prepare)
    return value


def _pageQuery(
    *,
    completeness: Literal["allowPartial", "requireComplete"] = "allowPartial",
) -> DataQuery:
    return DataQuery(
        requests=(
            DataRequest(
                "resource.finance",
                requestId="dartAll",
                projection=NativeProjection(),
                params={"columns": ["companyId", "value"]},
            ),
            DataRequest(
                "resource.edgar",
                requestId="edgarAll",
                projection=NativeProjection(),
                params={"columns": ["cik", "valueUsd"]},
            ),
        ),
        budget=QueryBudget(maxRows=4, maxBytes=1024 * 1024, maxAssets=8),
        completeness=completeness,
    )


def _publicData(*args: Any, **kwargs: Any) -> Any:
    import dartlab

    return getattr(dartlab, "data")(*args, **kwargs)


def testPublicQueryMultiplexesDartAndEdgarAcrossOneTokenChain(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dartlab.dataHub.execution as executionModule
    import dartlab.providers.resourceStream.workbench as workbenchModule

    result = _publicData("query", query=_pageQuery())
    assert result.status == "partial", result.gaps
    assert [partition.requestId for partition in result.partitions] == ["dartAll", "edgarAll"]
    assert result.continuation is not None
    assert len(result.executionReceipts) == 1
    assert result.executionReceipts[0].startswith("cas:sha256:")
    assert result.dataSnapshotId is not None
    assert result.dataSnapshotId.startswith("data-content-snapshot:")
    assert all(partition.contentHash is not None for partition in result.partitions)
    assert tuple(asset.assetId for asset in result.assets) == ("resource.finance", "resource.edgar")
    dartSelector = dict(result.partitions[0].selector)
    edgarSelector = dict(result.partitions[1].selector)
    assert dartSelector["startRow"] == "0"
    assert dartSelector["nextRow"] == "2"
    assert dartSelector["sourceShardCount"] == "5"
    assert dartSelector["selectedShardCount"] == "5"
    assert dartSelector["completedShardCount"] == "2"
    assert dartSelector["pageScannedShardCount"] == "2"
    assert dartSelector["cursorShardOrdinal"] == "2"
    assert dartSelector["cursorPhysicalRowInShard"] == "0"
    assert dartSelector["complete"] == "false"
    assert edgarSelector["sourceShardCount"] == "4"
    assert edgarSelector["completedShardCount"] == "2"
    firstCoverage = {coverage.requestId: coverage for coverage in result.universeCoverage}
    assert firstCoverage["dartAll"].market == "KR"
    assert firstCoverage["edgarAll"].market == "US"
    assert firstCoverage["dartAll"].provider == "dart"
    assert firstCoverage["edgarAll"].provider == "edgar"
    assert firstCoverage["dartAll"].requestedEntities == 5
    assert firstCoverage["dartAll"].matchedEntities == 2
    assert firstCoverage["dartAll"].missingEntities == 3
    assert firstCoverage["dartAll"].status == "partial"
    assert firstCoverage["edgarAll"].requestedEntities == 4
    assert firstCoverage["edgarAll"].matchedEntities == 2
    assert result.universeSnapshotId is not None

    firstToken = result.continuation
    firstContinuationReceipts = None
    collected = {partition.requestId: partition.data.to_dicts() for partition in result.partitions}
    monkeypatch.setattr(
        executionModule,
        "buildCatalog",
        lambda: (_ for _ in ()).throw(AssertionError("resume이 catalog를 호출함")),
    )
    monkeypatch.setattr(
        executionModule,
        "_compiledRequests",
        lambda *_args: (_ for _ in ()).throw(AssertionError("resume이 request compile을 호출함")),
    )
    while result.continuation is not None:
        activeToken = result.continuation
        result = _publicData("query", query=DataQuery(continuation=activeToken))
        if activeToken == firstToken:
            firstContinuationReceipts = result.executionReceipts
        for partition in result.partitions:
            collected.setdefault(partition.requestId, []).extend(partition.data.to_dicts())

    assert result.status == "ok"
    finalCoverage = {coverage.requestId: coverage for coverage in result.universeCoverage}
    assert set(finalCoverage) == {"dartAll", "edgarAll"}
    assert finalCoverage["dartAll"].matchedEntities == 5
    assert finalCoverage["dartAll"].missingEntities == 0
    assert finalCoverage["dartAll"].status == "complete"
    assert finalCoverage["edgarAll"].matchedEntities == 4
    assert finalCoverage["edgarAll"].missingEntities == 0
    assert finalCoverage["edgarAll"].status == "complete"
    expectedDart = pl.DataFrame(owner.tables["resource.finance"].to_pydict()).with_columns(
        pl.Series("sourcePath", [f"finance-{index}" for index in range(5)])
    )
    expectedEdgar = pl.DataFrame(owner.tables["resource.edgar"].to_pydict()).with_columns(
        pl.Series("sourcePath", [f"edgar-{index}" for index in range(4)])
    )
    assert collected["dartAll"] == expectedDart.to_dicts()
    assert collected["edgarAll"] == expectedEdgar.to_dicts()
    assert len({row["sourcePath"] for row in collected["dartAll"]}) == 5
    assert len({row["sourcePath"] for row in collected["edgarAll"]}) == 4
    assert owner.calls == [
        ("resource.finance", 0, 2),
        ("resource.edgar", 0, 2),
        ("resource.finance", 2, 2),
        ("resource.edgar", 2, 2),
        ("resource.finance", 4, 1),
    ]

    callsBeforeReplay = len(owner.calls)
    monkeypatch.setattr(
        workbenchModule,
        "describeResource",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("replay가 provider를 호출함")),
    )
    monkeypatch.setattr(
        workbenchModule,
        "readResourcePage",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("replay가 owner를 호출함")),
    )
    replay = _publicData("query", query=DataQuery(continuation=firstToken))
    assert replay.status == "partial"
    assert firstContinuationReceipts is not None
    assert replay.executionReceipts == firstContinuationReceipts
    assert len(owner.calls) == callsBeforeReplay


def testOneMappingCallEntersBothDartAndEdgarResources(owner: _SyntheticOwner) -> None:
    result = _publicData(
        "query",
        query={
            "requests": [
                {
                    "assetId": "resource.finance",
                    "requestId": "dartAll",
                    "params": {"columns": ["companyId", "value"]},
                },
                {
                    "assetId": "resource.edgar",
                    "requestId": "edgarAll",
                    "params": {"columns": ["cik", "valueUsd"]},
                },
            ],
            "budget": {"maxRows": 4, "maxBytes": 1024 * 1024, "maxAssets": 8},
        },
    )

    assert result.status == "partial"
    assert [partition.requestId for partition in result.partitions] == ["dartAll", "edgarAll"]
    assert result.continuation is not None
    assert owner.calls == [("resource.finance", 0, 2), ("resource.edgar", 0, 2)]


def testOneResultMethodConsumesAllDartAndEdgarPages(owner: _SyntheticOwner) -> None:
    first = _publicData("query", query=_pageQuery())
    dartIds: list[str] = []
    edgarIds: list[int] = []

    for _key, batch in first.iterAllArrowBatches(maxRows=1, maxBytes=1024):
        if "companyId" in batch.schema.names:
            dartIds.extend(batch.column("companyId").to_pylist())
        if "cik" in batch.schema.names:
            edgarIds.extend(batch.column("cik").to_pylist())

    assert dartIds == ["K1", "K2", "K3", "K4", "K5"]
    assert edgarIds == [10, 20, 30, 40]
    assert len(owner.calls) >= 4


def testSameResourceCanBeRequestedTwiceWithDifferentViews(owner: _SyntheticOwner) -> None:
    result = _publicData(
        "query",
        query=DataQuery(
            requests=(
                DataRequest("resource.finance", "ids", params={"columns": ["companyId"]}),
                DataRequest("resource.finance", "values", params={"columns": ["value"]}),
            ),
            budget=QueryBudget(maxRows=4, maxBytes=1024 * 1024),
        ),
    )

    assert result.status == "partial"
    assert [partition.requestId for partition in result.partitions] == ["ids", "values"]
    assert [partition.schema[0][0] for partition in result.partitions] == ["companyId", "value"]
    assert len(result.assets) == 1
    assert owner.calls == [("resource.finance", 0, 2), ("resource.finance", 0, 2)]


def testPlanningFailureDoesNotLeakOwnerDetails(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dartlab.providers.resourceStream.workbench as workbenchModule

    del owner

    def failDescription(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(r"C:\private\manifest-secret")

    monkeypatch.setattr(workbenchModule, "describeResource", failDescription)
    monkeypatch.setattr(workbenchModule, "prepareResourceRead", failDescription)
    result = _publicData("query", query=_pageQuery())

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["RESOURCE_PAGE_PLAN_FAILED"]
    assert "private" not in result.gaps[0].message
    assert "RuntimeError" not in result.gaps[0].message


def testContinuationBlocksTargetAndAssetsOverrideBeforeLookup(owner: _SyntheticOwner) -> None:
    del owner
    resumed = DataQuery(continuation="dltc1.invalid")
    with pytest.raises(ValueError, match="override"):
        _publicData("query", "resource.finance", query=resumed)
    with pytest.raises(ValueError, match="override"):
        _publicData("query", assets=("resource.finance",), query=resumed)


def testInvalidContinuationBecomesSafeCodeGap(owner: _SyntheticOwner) -> None:
    del owner
    result = _publicData("query", query=DataQuery(continuation="not-a-token"))
    assert result.status == "failed"
    assert len(result.gaps) == 1
    assert result.gaps[0].code == "CONTINUATION_INVALID"
    assert "not-a-token" not in result.gaps[0].message
    assert result.gaps[0].systemic is True


def testMixedPageableAndEagerShareOneOuterExecution(
    owner: _SyntheticOwner,
) -> None:
    result = _publicData(
        "query",
        query=DataQuery(
            requests=(
                DataRequest("resource.finance", "page", params={"columns": ["companyId"]}),
                DataRequest(
                    "resource.finance",
                    "locator",
                    projection=ResourceProjection(),
                    subjects=("K1",),
                ),
            ),
            budget=QueryBudget(maxRows=2, maxConcurrency=2),
        ),
    )
    assert result.status == "partial", result.gaps
    assert [partition.requestId for partition in result.partitions] == ["page"]
    assert result.continuation is not None
    pages = [result]
    token = result.continuation
    while token is not None:
        page = _publicData("query", query=DataQuery(continuation=token))
        pages.append(page)
        token = page.continuation
    assert pages[-1].status == "ok", pages[-1].gaps
    assert sum(partition.rowCount for page in pages for partition in page.byRequest("page")) == 5
    assert sum(partition.rowCount for page in pages for partition in page.byRequest("locator")) == 1
    assert len(owner.calls) == 3


def testMixedPageableAndMonkeypatchedEagerFailsCodePinBeforeAnyExecution(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dartlab

    eagerCalled = False

    def eager(*_args: object, **_kwargs: object):
        nonlocal eagerCalled
        eagerCalled = True
        return pl.DataFrame({"value": [1]})

    monkeypatch.setattr(dartlab, "scan", eager)
    result = _publicData(
        "query",
        query=DataQuery(
            requests=(
                DataRequest("resource.finance", "page", params={"columns": ["companyId"]}),
                DataRequest("scan.governance", "eager"),
            ),
            # 이 회귀는 code pin 검사가 owner 실행보다 먼저인지를 본다. 자식은 fresh spawn
            # 이라 pin 을 계산하기 전에 owner 모듈 전체를 sandbox 하위에서 새로 import
            # 해야 하고, 병렬 부하가 큰 CI 러너에서는 기본 30 초 안에 그 지점에 닿지
            # 못해 timeout 이 pin 실패를 가린다. 순서 계약을 보려면 기한이 넉넉해야 한다.
            budget=QueryBudget(timeoutMs=180_000),
        ),
    )

    assert result.status == "failed"
    assert result.gaps[0].code == "PAGEABLE_EAGER_CODE_PIN_FAILED"
    assert owner.calls == []
    assert eagerCalled is False


def testRequireCompletePageableFailsBeforeOwnerExecution(owner: _SyntheticOwner) -> None:
    result = _publicData("query", query=_pageQuery(completeness="requireComplete"))
    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["PAGEABLE_REQUIRE_COMPLETE_UNSUPPORTED"]
    assert owner.calls == []


def testResourceLocatorRemainsOnExistingEagerPath(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadData",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("locator가 payload를 읽음")),
    )
    result = _publicData(
        "query",
        "resource.finance",
        query=DataQuery(projection=ResourceProjection()),
    )
    assert result.status == "ok"
    assert result.partitions[0].projectionKind == "resource"
    assert result.partitions[0].data["payload"] is None
    assert owner.calls == []


def testSourceDriftOnResumeIsSafeAndDoesNotReadNextPage(owner: _SyntheticOwner) -> None:
    first = _publicData("query", query=_pageQuery())
    assert first.continuation is not None
    callsBefore = len(owner.calls)
    owner.sourcePins["resource.finance"] = "resource-source-full:" + "c" * 64
    result = _publicData("query", query=DataQuery(continuation=first.continuation))
    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_SOURCE_STALE"]
    assert len(owner.calls) == callsBefore
    assert "resource-source-full" not in result.gaps[0].message


def testContractDriftOnPendingResumeFailsBeforeOwnerRead(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # `_contractDigest` 는 `_pins` 와 같은 source 계층이 소유한다. 파사드를 패치하면
    # 호출자가 자기 모듈의 이름을 그대로 보므로 drift 가 재현되지 않는다.
    import dartlab.dataHub.paging.resource.source as resourcePagingSourceModule

    first = _publicData("query", query=_pageQuery())
    assert first.continuation is not None
    callsBefore = len(owner.calls)
    monkeypatch.setattr(resourcePagingSourceModule, "_contractDigest", lambda _session: "f" * 64)

    result = _publicData("query", query=DataQuery(continuation=first.continuation))

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_CONTRACT_STALE"]
    assert len(owner.calls) == callsBefore


def testPageableQueryEnforcesTimeoutBudget(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dartlab.providers.resourceStream.workbench as workbenchModule

    def slowRead(*args: Any, **kwargs: Any) -> Any:
        time.sleep(0.02)
        return owner.read(*args, **kwargs)

    monkeypatch.setattr(workbenchModule, "readResourcePage", slowRead)
    query = replace(_pageQuery(), budget=QueryBudget(maxRows=4, maxBytes=1024 * 1024, timeoutMs=1))

    result = _publicData("query", query=query)

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_TIMEOUT"]
    assert result.continuation is None


def testZeroRowPageMayAdvancePhysicalCursor(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dartlab.dataHub.paging.resource.api as resourcePagingModule

    monkeypatch.setattr(resourcePagingModule, "_MAX_PAGE_SHARDS", 1)
    result = _publicData(
        "query",
        query=DataQuery(
            requests=(
                DataRequest(
                    "resource.finance",
                    "emptyScan",
                    params={
                        "columns": ["companyId", "value"],
                        "predicates": [{"column": "value", "operator": "gt", "value": 999}],
                    },
                ),
            ),
            budget=QueryBudget(maxRows=1, maxBytes=1024 * 1024),
        ),
    )

    assert result.status == "partial"
    assert result.continuation is not None
    assert result.partitions[0].rowCount == 0
    selector = dict(result.partitions[0].selector)
    assert selector["completedShardCount"] == "1"
    assert selector["cursorShardOrdinal"] == "1"
    assert selector["pageScannedShardCount"] == "1"
    assert selector["complete"] == "false"
    assert owner.calls == [("resource.finance", 0, 0)]


def testResumeDeadlineIncludesContextLoad(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dartlab.dataHub.continuation import ContinuationStore
    from dartlab.dataHub.paging.resource import resumeResourcePaging

    first = _publicData("query", query=_pageQuery())
    assert first.continuation is not None
    original = ContinuationStore.loadContext

    def slowLoad(self: ContinuationStore, token: str):
        time.sleep(0.02)
        return original(self, token)

    monkeypatch.setattr(ContinuationStore, "loadContext", slowLoad)
    result = resumeResourcePaging(first.continuation, deadline=time.perf_counter() + 0.001)

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_TIMEOUT"]


def testResumeDeadlineIncludesCommittedReplay(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dartlab.dataHub.continuation import ContinuationStore
    from dartlab.dataHub.paging.resource import resumeResourcePaging

    first = _publicData("query", query=_pageQuery())
    assert first.continuation is not None
    committed = _publicData("query", query=DataQuery(continuation=first.continuation))
    assert committed.status == "partial"
    callsBefore = len(owner.calls)
    original = ContinuationStore.redeem

    def slowRedeem(self: ContinuationStore, *args: Any, **kwargs: Any) -> Any:
        time.sleep(0.02)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(ContinuationStore, "redeem", slowRedeem)
    result = resumeResourcePaging(first.continuation, deadline=time.perf_counter() + 0.001)

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_TIMEOUT"]
    assert len(owner.calls) == callsBefore


def testTokenOnlyResumeReusesTheIssuedPageTimeout(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dartlab.dataHub.paging.resource.api as resourcePagingModule

    query = replace(
        _pageQuery(),
        budget=QueryBudget(maxRows=4, maxBytes=1024 * 1024, timeoutMs=60_000),
    )
    first = _publicData("query", query=query)
    assert first.continuation is not None
    capturedDeadlines: list[float] = []
    original = resourcePagingModule._materialize

    def captureDeadline(*args: Any, **kwargs: Any) -> Any:
        capturedDeadlines.append(cast(float, kwargs["deadline"]))
        return original(*args, **kwargs)

    monkeypatch.setattr(resourcePagingModule, "_materialize", captureDeadline)
    resumed = _publicData("query", query=DataQuery(continuation=first.continuation))

    assert resumed.status == "partial"
    assert capturedDeadlines
    assert 50 < capturedDeadlines[0] - time.perf_counter() <= 60
    assert owner.calls


def testPublicPagingRunsOneBoundedMaintenanceStepAndForwardsWaitBudget(
    owner: _SyntheticOwner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dartlab.dataHub.continuation import ContinuationMaintenanceBudget, ContinuationStore

    maintenanceBudgets: list[ContinuationMaintenanceBudget] = []
    waitBudgets: list[float | None] = []
    originalMaintain = ContinuationStore.maintain
    originalRedeem = ContinuationStore.redeem

    def observeMaintain(self: ContinuationStore, budget: ContinuationMaintenanceBudget | None = None):
        assert budget is not None
        maintenanceBudgets.append(budget)
        return originalMaintain(self, budget)

    def observeRedeem(self: ContinuationStore, *args: Any, **kwargs: Any) -> Any:
        waitBudgets.append(cast(float | None, kwargs.get("waitSeconds")))
        return originalRedeem(self, *args, **kwargs)

    monkeypatch.setattr(ContinuationStore, "maintain", observeMaintain)
    monkeypatch.setattr(ContinuationStore, "redeem", observeRedeem)

    first = _publicData("query", query=_pageQuery())
    assert first.continuation is not None
    assert len(maintenanceBudgets) == 1
    assert maintenanceBudgets[0].maxContinuationRows == 32
    assert maintenanceBudgets[0].maxCasEntries == 32
    assert len(waitBudgets) == 1
    assert waitBudgets[0] is not None and 0 < waitBudgets[0] <= 30

    maintenanceBudgets.clear()
    waitBudgets.clear()
    resumed = _publicData("query", query=DataQuery(continuation=first.continuation))
    assert resumed.status == "partial"
    assert len(maintenanceBudgets) == 1
    assert len(waitBudgets) == 1
    assert owner.calls


def testCommittedReplaySurvivesSourceDriftWithoutProviderContact(owner: _SyntheticOwner) -> None:
    first = _publicData("query", query=_pageQuery())
    assert first.continuation is not None
    token = first.continuation
    committed = _publicData("query", query=DataQuery(continuation=token))
    assert committed.status == "partial"
    callsBefore = len(owner.calls)
    owner.sourcePins["resource.finance"] = "resource-source-full:" + "d" * 64

    replay = _publicData("query", query=DataQuery(continuation=token))

    assert replay.executionReceipts == committed.executionReceipts
    assert replay.dataSnapshotId == committed.dataSnapshotId
    assert [partition.contentHash for partition in replay.partitions] == [
        partition.contentHash for partition in committed.partitions
    ]
    assert replay.continuation == committed.continuation
    assert len(owner.calls) == callsBefore


@pytest.mark.parametrize(
    "tamper",
    [
        "rowCount",
        "sourcePin",
        "schema",
        "encodedByteCount",
        "byteCount",
        "rowCountBool",
        "truncatedType",
        "cursorNoProgress",
        "scannedShardCount",
    ],
)
def testLowerOwnerReceiptAndPayloadClaimsAreRevalidated(
    owner: _SyntheticOwner,
    tamper: str,
) -> None:
    owner.tamper = tamper
    result = _publicData("query", query=_pageQuery())
    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_OWNER_FAILED"]
    assert tamper not in result.gaps[0].message


def testBackwardOwnerCursorIsRejectedOnResume(owner: _SyntheticOwner) -> None:
    first = _publicData("query", query=_pageQuery())
    assert first.continuation is not None
    owner.tamper = "cursorBackward"

    result = _publicData("query", query=DataQuery(continuation=first.continuation))

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_OWNER_FAILED"]


def testPrivateStoreAndManifestCacheUseDartlabHome(owner: _SyntheticOwner) -> None:
    import os

    del owner
    result = _publicData("query", query=_pageQuery())
    assert result.continuation is not None
    root = Path(os.environ["DARTLAB_HOME"]) / "dataHub"
    assert (root / "continuations" / "continuations.sqlite").is_file()
    assert (root / "manifest-cache").is_dir()
