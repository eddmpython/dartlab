"""Unified Data Workbench query and projection tests."""

from __future__ import annotations

import time

import polars as pl

from dartlab.data import DataQuery, FactorProjection, QueryBudget, ResourceProjection, TimeContext


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
    result = dartlab.data("query", "scan.ratio", query=query)

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
    result = dartlab.data(
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

    result = dartlab.data("query", "missing.asset", query=DataQuery())
    assert result.status == "failed"
    assert result.partitions == ()
    assert [gap.code for gap in result.gaps] == ["ASSET_NOT_FOUND"]


def testNativeProjectionAppliesRowBudget(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: _ratioFrame())
    result = dartlab.data(
        "query",
        "scan.governance",
        query=DataQuery(budget=QueryBudget(maxRows=1)),
    )
    assert result.status == "ok"
    assert result.partitions[0].rowCount == 1
    assert result.partitions[0].truncated
    assert result.continuation == "row-budget"


def testFactorProjectionRejectsUnknownUnit(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: _ratioFrame())
    result = dartlab.data(
        "query",
        "scan.ratio",
        query=DataQuery(projection=FactorProjection(measures=("roe",))),
    )

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["FACTOR_UNIT_REQUIRED"]


def testResourceLocatorDoesNotLoadPayload(monkeypatch):
    import dartlab

    def failIfLoaded(*args, **kwargs):
        raise AssertionError("locator projection이 resource payload를 읽음")

    monkeypatch.setattr("dartlab.core.dataLoader.loadData", failIfLoaded)
    result = dartlab.data(
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
    result = dartlab.data(
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
    result = dartlab.data(
        "query",
        "quant.momentum",
        query=DataQuery(subjects=("005930", "000660"), budget=QueryBudget(maxRows=3)),
    )

    assert result.status == "ok"
    assert sum(partition.rowCount for partition in result.partitions) == 3
    assert result.partitions[-1].truncated


def testTimeoutDropsLateOwnerResult(monkeypatch):
    import dartlab

    def slowScan(*args, **kwargs):
        time.sleep(0.01)
        return _ratioFrame()

    monkeypatch.setattr(dartlab, "scan", slowScan)
    result = dartlab.data(
        "query",
        "scan.governance",
        query=DataQuery(budget=QueryBudget(timeoutMs=1)),
    )

    assert result.status == "failed"
    assert result.partitions == ()
    assert [gap.code for gap in result.gaps] == ["QUERY_TIMEOUT"]
