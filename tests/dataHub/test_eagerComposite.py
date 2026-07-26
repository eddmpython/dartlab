"""General eager seal과 locator가 한 outer continuation을 쓰는 production integration test."""

from __future__ import annotations

import os
import socket
import time

from dartlab.dataHub.compositePaging import (
    executeInitialCompositePaging,
    resumeCompositePaging,
)
from dartlab.dataHub.contracts import (
    Coverage,
    DataAssetDescriptor,
    DataCatalogResult,
    DataQuery,
    DataRequest,
    QueryBudget,
    ResourceProjection,
)

_CONTRACT_HASH = "d" * 64


def _fixtureMixedEager():
    return {
        "pid": os.getpid(),
        "noRefresh": os.environ.get("DARTLAB_NO_REFRESH"),
        "value": 7,
    }


def _fixtureMixedNetwork():
    return socket.getaddrinfo("huggingface.co", 443)


def _eagerDescriptor(
    attribute: str = "_fixtureMixedEager",
) -> DataAssetDescriptor:
    return DataAssetDescriptor(
        assetId=f"analysis.mixedEagerFixture.{attribute}",
        assetVersionId=f"analysis.mixedEagerFixture.{attribute}:v1",
        owner="tests.dataHub.test_eagerComposite",
        layer="L2",
        kind="computed",
        label="Mixed eager fixture",
        description="Fixture-only mixed eager executor",
        sourceRef=f"python:tests.dataHub.test_eagerComposite:{attribute}",
        queryable=True,
        executorKind="callable",
        executorModule="tests.dataHub.test_eagerComposite",
        executorAttribute=attribute,
    )


def _locatorDescriptor() -> DataAssetDescriptor:
    return DataAssetDescriptor(
        assetId="resource.mixedLocatorFixture",
        assetVersionId="resource.mixedLocatorFixture:v1",
        owner="resource",
        layer="L1",
        kind="resource",
        label="Mixed locator fixture",
        description="Fixture-only locator",
        sourceRef="fixture:locator",
        queryable=True,
        executorKind="resource",
        executorAxis="fixture",
    )


def testMixedInitialSealsGeneralEagerAndResumeTouchesOnlyLocator(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    eagerDescriptor = _eagerDescriptor()
    locatorDescriptor = _locatorDescriptor()
    budget = QueryBudget(
        maxRows=1,
        maxBytes=192 * 1024,
        timeoutMs=30_000,
        maxAssets=2,
        maxSubjects=10,
        maxConcurrency=1,
    )
    eagerQuery = DataQuery(
        measures=("fixture.value",),
        budget=budget,
    )
    locatorQuery = DataQuery(
        projection=ResourceProjection(),
        budget=budget,
    )
    outerQuery = DataQuery(
        requests=(
            DataRequest(
                eagerDescriptor.assetId,
                "eager",
                measures=("fixture.value",),
            ),
            DataRequest(
                locatorDescriptor.assetId,
                "locator",
                projection=ResourceProjection(),
            ),
        ),
        budget=budget,
    )
    catalog = DataCatalogResult(
        status="ok",
        assets=(locatorDescriptor,),
        snapshotId="catalog:fixture",
        coverage=Coverage(1, 1, 0, 0),
    )
    monkeypatch.setattr(
        "dartlab.dataHub.execution.buildCatalog",
        lambda: catalog,
    )

    first = executeInitialCompositePaging(
        (),
        outerQuery,
        requestedAssets=2,
        snapshotId="catalog:fixture",
        contractHash=_CONTRACT_HASH,
        resolved=(
            ("eager", eagerDescriptor, eagerQuery),
            ("locator", locatorDescriptor, locatorQuery),
        ),
        hasPlanningGaps=False,
        deadline=time.perf_counter() + 30,
    )

    assert first.status == "partial", first.gaps
    assert first.continuation is not None
    assert [partition.requestId for partition in first.partitions] == ["eager"]
    assert first.partitions[0].data["noRefresh"] == "1"
    assert first.partitions[0].data["pid"] != os.getpid()

    def failIfEagerRunsAgain(*args, **kwargs):
        raise AssertionError(f"resume이 eager owner를 다시 호출했습니다: {args!r} {kwargs!r}")

    monkeypatch.setattr(
        "tests.dataHub.test_eagerComposite._fixtureMixedEager",
        failIfEagerRunsAgain,
    )
    monkeypatch.setattr(
        "dartlab.dataHub.isolation.eagerSupervisor.runEagerSeal",
        failIfEagerRunsAgain,
    )
    resumed = resumeCompositePaging(
        first.continuation,
        deadline=time.perf_counter() + 20,
    )

    assert resumed.status == "ok", resumed.gaps
    assert resumed.continuation is None
    assert [partition.requestId for partition in resumed.partitions] == ["locator"]
    assert resumed.partitions[0].data["payload"] is None


def testInitialPlanPreservesOfflineFailureCodeAndIssuesNoToken(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    descriptor = _eagerDescriptor("_fixtureMixedNetwork")
    budget = QueryBudget(
        maxRows=1,
        maxBytes=64 * 1024,
        timeoutMs=30_000,
        maxAssets=1,
        maxSubjects=1,
        maxConcurrency=1,
    )
    query = DataQuery(budget=budget)

    result = executeInitialCompositePaging(
        (),
        query,
        requestedAssets=1,
        snapshotId="catalog:fixture",
        contractHash=_CONTRACT_HASH,
        resolved=(("network", descriptor, query),),
        hasPlanningGaps=False,
        deadline=time.perf_counter() + 30,
    )

    assert result.status == "failed"
    assert result.continuation is None
    assert [gap.code for gap in result.gaps] == ["OFFLINE_NETWORK_BLOCKED"]
