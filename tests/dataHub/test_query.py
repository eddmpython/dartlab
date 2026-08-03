"""Unified Data Workbench query and projection tests."""

from __future__ import annotations

import time
from collections import Counter
from threading import Lock
from types import SimpleNamespace

import polars as pl

from dartlab.dataHub import DataQuery, DataRequest, FactorProjection, QueryBudget, ResourceProjection, TimeContext


def _ratioFrame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "종목코드": ["005930", "000660"],
            "종목명": ["삼성전자", "SK하이닉스"],
            "2024": [10.0, 20.0],
            "2025": [11.0, 22.0],
        }
    )


def testFactorProjectionUsesSamePublicQueryContract(monkeypatch):
    import dartlab

    calls = []

    def fakeScan(axis, target=None, **kwargs):
        calls.append((axis, target, kwargs))
        return _ratioFrame()

    monkeypatch.setattr(dartlab, "scan", fakeScan)
    query = DataQuery(projection=FactorProjection(measures=("roe",), unit="percent", frequency="Y"))
    result = dartlab.dataHub("query", "scan.ratio", query=query)

    assert result.status == "ok"
    assert calls == [("ratio", "roe", {})]
    assert len(result.partitions) == 1
    frame = result.partitions[0].data
    assert frame.height == 4
    assert frame["measureId"].unique().to_list() == ["roe"]
    assert set(frame["entityId"].to_list()) == {"005930", "000660"}
    assert set(frame["unit"].to_list()) == {"percent"}
    assert result.executionReceipts
    assert result.lineageRefs


def testHistoricalKnowledgeTimeFailsClosedBeforeOwnerCall(monkeypatch):
    import dartlab

    called = False

    def fakeScan(*args, **kwargs):
        nonlocal called
        called = True
        return _ratioFrame()

    monkeypatch.setattr(dartlab, "scan", fakeScan)
    result = dartlab.dataHub(
        "query",
        "scan.ratio",
        query=DataQuery(
            projection=FactorProjection(measures=("roe",)),
            time=TimeContext(knownAt="2025-01-01"),
        ),
    )

    assert result.status == "failed"
    assert not called
    assert [gap.code for gap in result.gaps] == ["PIT_UNSUPPORTED"]


def testUnknownAssetIsFailureNotEmptySuccess():
    import dartlab

    result = dartlab.dataHub("query", "missing.asset", query=DataQuery())
    assert result.status == "failed"
    assert result.partitions == ()
    assert [gap.code for gap in result.gaps] == ["ASSET_NOT_FOUND"]


def testEmptyOwnerOutputIsNoDataGapNotEmptySuccess(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: pl.DataFrame())
    result = dartlab.dataHub("query", "scan.governance", query=DataQuery())

    assert result.status == "failed"
    assert result.partitions == ()
    assert [gap.code for gap in result.gaps] == ["NO_DATA"]


def testNativeProjectionAppliesRowBudget(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: _ratioFrame())
    result = dartlab.dataHub(
        "query",
        "scan.governance",
        query=DataQuery(budget=QueryBudget(maxRows=1)),
    )
    assert result.status == "partial"
    assert result.partitions[0].rowCount == 1
    assert result.partitions[0].truncated
    assert result.continuation is None
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_UNSUPPORTED"]


def testRequireCompleteRejectsEagerTruncation(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: _ratioFrame())
    result = dartlab.dataHub(
        "query",
        "scan.governance",
        query=DataQuery(budget=QueryBudget(maxRows=1), completeness="requireComplete"),
    )

    assert result.status == "failed"
    assert result.partitions == ()
    assert result.continuation is None
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_UNSUPPORTED"]


def testFactorProjectionRejectsUnknownUnit(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: _ratioFrame())
    result = dartlab.dataHub(
        "query",
        "scan.ratio",
        query=DataQuery(projection=FactorProjection(measures=("roe",))),
    )

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["FACTOR_UNIT_REQUIRED"]


def testResourceLocatorDoesNotLoadPayload(monkeypatch, tmp_path):
    # 로컬 구운 데이터에 의존하면 CI(빈 dataDir)에서 RESOURCE_ROOT_EMPTY로 죽는다.
    # locator 계약(=payload를 읽지 않고 description만 발행)은 임시 flat root 하나로 충분히
    # 실측되므로 dataDir·DARTLAB_HOME을 격리해 hermetic하게 검증한다.
    import polars as pl

    import dartlab

    scanRoot = tmp_path / "data" / "dart" / "scan"
    scanRoot.mkdir(parents=True)
    pl.DataFrame({"stockCode": ["005930"], "value": [1.0]}).write_parquet(scanRoot / "seed.parquet")
    monkeypatch.setattr("dartlab.config.dataDir", str(tmp_path / "data"))
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path / "home"))

    def failIfLoaded(*args, **kwargs):
        raise AssertionError("locator projection이 resource payload를 읽음")

    monkeypatch.setattr("dartlab.core.dataLoader.loadData", failIfLoaded)
    result = dartlab.dataHub(
        "query",
        "resource.scan",
        query=DataQuery(subjects=("latest",), projection=ResourceProjection()),
    )

    assert result.status == "ok"
    assert result.partitions[0].data["payload"] is None


def testBulkResourcePayloadFailsBeforeLoader(monkeypatch):
    import dartlab

    called = False

    def failIfLoaded(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("unbounded resource payload를 읽음")

    monkeypatch.setattr("dartlab.core.dataLoader.loadData", failIfLoaded)
    result = dartlab.dataHub(
        "query",
        "resource.scan",
        query=DataQuery(subjects=("latest",)),
    )

    assert result.status == "failed"
    assert not called
    assert "RESOURCE_PAYLOAD_UNBOUNDED" in result.gaps[0].message


def testRowBudgetIsGlobalAcrossPartitions(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "quant", lambda *args, **kwargs: _ratioFrame())
    result = dartlab.dataHub(
        "query",
        "quant.momentum",
        query=DataQuery(subjects=("005930", "000660"), budget=QueryBudget(maxRows=3)),
    )

    assert result.status == "partial"
    assert sum(partition.rowCount for partition in result.partitions) == 3
    assert result.partitions[-1].truncated
    assert result.continuation is None
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_UNSUPPORTED"]


def testRowBudgetReservesCapacityForLaterMixedRequests(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: pl.DataFrame({"value": list(range(100))}))
    monkeypatch.setattr(dartlab, "macro", lambda *args, **kwargs: {"value": 1})
    result = dartlab.dataHub(
        "query",
        query=DataQuery(
            requests=(
                DataRequest("scan.governance", "wide"),
                DataRequest("macro.cycle", "scalar"),
            ),
            budget=QueryBudget(maxRows=10, maxConcurrency=2),
        ),
    )

    assert result.status == "partial"
    assert [partition.rowCount for partition in result.partitions] == [9, 1]
    assert [partition.requestId for partition in result.partitions] == ["wide", "scalar"]
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_UNSUPPORTED"]


def testTimeoutDropsLateOwnerResult(monkeypatch):
    import dartlab

    def slowScan(*args, **kwargs):
        time.sleep(0.01)
        return _ratioFrame()

    monkeypatch.setattr(dartlab, "scan", slowScan)
    result = dartlab.dataHub(
        "query",
        "scan.governance",
        query=DataQuery(budget=QueryBudget(timeoutMs=1)),
    )

    assert result.status == "failed"
    assert result.partitions == ()
    assert [gap.code for gap in result.gaps] == ["QUERY_TIMEOUT"]


def testOptionalMacroSubjectIsForwardedByDescriptor(monkeypatch):
    import dartlab

    calls = []

    def fakeMacro(axis, **kwargs):
        calls.append((axis, kwargs))
        return {"market": kwargs.get("target")}

    monkeypatch.setattr(dartlab, "macro", fakeMacro)
    result = dartlab.dataHub(
        "query",
        "macro.cycle",
        query=DataQuery(subjects=("KR",)),
    )

    assert result.status == "ok"
    assert calls == [("cycle", {"target": "KR"})]
    assert result.partitions[0].selector == (("subject", "KR"),)


def testRequiredSelectorFailsBeforeOwnerExecution(monkeypatch):
    import dartlab

    called = False

    def failIfCalled(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("필수 selector 검증 전에 owner가 실행됨")

    monkeypatch.setattr(dartlab, "quant", failIfCalled)
    result = dartlab.dataHub("query", "quant.momentum", query=DataQuery())

    assert result.status == "failed"
    assert not called
    assert [gap.code for gap in result.gaps] == ["MISSING_SELECTOR"]
    assert result.gaps[0].requestId == "quant.momentum"


def testEveryGenericQueryableAssetRoutesThroughOneMixedQuery(monkeypatch):
    import dartlab
    from dartlab.analysis.financial import dataAssets

    catalog = dartlab.dataHub("catalog")
    monkeypatch.setattr(
        "dartlab.providers.resourceStream.workbench.describeResource",
        lambda resourceId, category, _cachePath: SimpleNamespace(
            resourceId=resourceId,
            category=category,
            sourcePin="resource-source-full:" + "1" * 64,
            shardCount=1,
            totalBytes=1,
            schemaFields=(("value", "Int64"),),
        ),
    )
    assets = tuple(
        asset for asset in catalog.assets if asset.queryable and dict(asset.metadata).get("observationPIT") is not True
    )
    engineCalls = []

    def fakeEngine(owner):
        def execute(axis, *args, **kwargs):
            engineCalls.append((owner, axis, args, kwargs))
            return {"owner": owner, "axis": axis, "args": args, "kwargs": kwargs}

        return execute

    for owner in {asset.owner for asset in assets if asset.executorKind == "engineAxis"}:
        monkeypatch.setattr(dartlab, owner, fakeEngine(owner))
    simulationCalls = []

    def fakeSimulationInputs(**kwargs):
        simulationCalls.append(kwargs)
        return {"simulation": kwargs}

    monkeypatch.setattr(dataAssets, "simulationInputs", fakeSimulationInputs)
    featureCalls = []

    def fakeEdgarFinancialFeatures(**kwargs):
        featureCalls.append(kwargs)
        return {"features": kwargs}

    monkeypatch.setattr(dataAssets, "edgarFinancialFeatures", fakeEdgarFinancialFeatures)
    dartFeatureCalls = []

    def fakeDartFinancialFeatures(**kwargs):
        dartFeatureCalls.append(kwargs)
        return {"features": kwargs}

    monkeypatch.setattr(dataAssets, "dartFinancialFeatures", fakeDartFinancialFeatures)

    requests = []
    for asset in assets:
        subjects = ("probe",) if asset.selectorKind == "subject" else ()
        measures = ("probe",) if asset.selectorKind == "measure" else ()
        projection = ResourceProjection() if asset.executorKind == "resource" else None
        requests.append(
            DataRequest(
                asset.assetId,
                requestId=asset.assetId,
                projection=projection,
                subjects=subjects,
                measures=measures,
                time=(TimeContext(knownAt="20250201") if dict(asset.metadata).get("knownAtRequired") is True else None),
            )
        )

    result = dartlab.dataHub(
        "query",
        query=DataQuery(
            requests=tuple(requests),
            budget=QueryBudget(maxAssets=len(requests), maxRows=1_000, timeoutMs=120_000),
            completeness="requireComplete",
        ),
    )

    assert result.status == "ok", result.gaps
    assert not result.gaps
    assert len(result.partitions) == len(assets) == 170
    assert {partition.requestId for partition in result.partitions} == {asset.assetId for asset in assets}
    assert Counter(owner for owner, *_ in engineCalls) == Counter(
        asset.owner for asset in assets if asset.executorKind == "engineAxis"
    )
    assert simulationCalls == [{"subject": "probe"}]
    assert featureCalls == []
    assert dartFeatureCalls == []


def testMaxConcurrencyAcceleratesMixedQueryAndKeepsResultOrder(monkeypatch):
    import dartlab

    def fakeScan(axis, *args, **kwargs):
        time.sleep(0.08)
        return pl.DataFrame({"axis": [axis]})

    monkeypatch.setattr(dartlab, "scan", fakeScan)
    requests = tuple(
        DataRequest(assetId, requestId=assetId) for assetId in ("scan.governance", "scan.workforce", "scan.capital")
    )

    started = time.perf_counter()
    sequential = dartlab.dataHub(
        "query",
        query=DataQuery(requests=requests, budget=QueryBudget(maxConcurrency=1)),
    )
    sequentialElapsed = time.perf_counter() - started
    started = time.perf_counter()
    concurrent = dartlab.dataHub(
        "query",
        query=DataQuery(requests=requests, budget=QueryBudget(maxConcurrency=3)),
    )
    concurrentElapsed = time.perf_counter() - started

    assert sequential.status == concurrent.status == "ok"
    assert [partition.requestId for partition in concurrent.partitions] == [request.requestId for request in requests]
    assert concurrentElapsed < sequentialElapsed * 0.8


def testConcurrencyGroupSerializesCompanyDataOwners(monkeypatch):
    import dartlab

    lock = Lock()
    active = 0
    maxActive = 0

    def sharedOwner(axis, *args, **kwargs):
        nonlocal active, maxActive
        with lock:
            active += 1
            maxActive = max(maxActive, active)
        time.sleep(0.04)
        with lock:
            active -= 1
        return {"axis": axis}

    monkeypatch.setattr(dartlab, "analysis", sharedOwner)
    monkeypatch.setattr(dartlab, "credit", sharedOwner)
    monkeypatch.setattr(dartlab, "macro", lambda axis, *args, **kwargs: {"axis": axis})
    result = dartlab.dataHub(
        "query",
        query=DataQuery(
            requests=(
                DataRequest("analysis.수익성", "analysis", subjects=("005930",)),
                DataRequest("credit.grade", "credit", subjects=("005930",)),
                DataRequest("macro.cycle", "macro"),
            ),
            budget=QueryBudget(maxConcurrency=2),
        ),
    )

    assert result.status == "ok"
    assert maxActive == 1
    assert [partition.requestId for partition in result.partitions] == ["analysis", "credit", "macro"]


def testCoverageCountsFailedAssetsNotGapRows() -> None:
    """성적표는 asset 단위 실패 수다. 한 asset 이 gap 을 여럿 만들어도 실패는 하나다."""

    import dartlab

    result = dartlab.dataHub(
        "query",
        assets=("does.notExistOne", "does.notExistTwo"),
        query=DataQuery(subjects=("005930",)),
    )

    assert result.status == "failed"
    assert result.coverage.requestedAssets == 2
    # gap 은 asset 마다 하나씩이므로 실패 수와 일치해야 한다.
    assert result.coverage.failedPartitions == len({(g.requestId, g.assetId) for g in result.gaps})
    assert result.coverage.failedPartitions <= len(result.gaps)
