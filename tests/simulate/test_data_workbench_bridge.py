"""Simulator가 통합 Data Workbench 입력 스냅샷을 실제로 소비하는지 검증한다."""

from __future__ import annotations

from types import SimpleNamespace

import pytest


def testBuildSnapshotBindsWorkbenchSnapshotAndReceipts(monkeypatch):
    from dartlab.simulate.registry import buildSnapshot

    class FakeCompany:
        stockCode = "000001"
        sectorParams = None

        def _buildFinanceSeries(self, *, freq="Q"):
            assert freq == "Q"
            return {
                "IS": {"sales": [10.0, 20.0, 30.0, 40.0], "operating_profit": [1.0, 2.0, 3.0, 4.0]},
                "BS": {"cash_and_cash_equivalents": [1.0], "shortterm_borrowings": [2.0]},
                "CF": {},
            }, ["2020-Q1", "2020-Q2", "2020-Q3", "2020-Q4"]

    monkeypatch.setattr("dartlab.simulate.registry._resolveSectorKey", lambda company: None)

    snapshot = buildSnapshot(FakeCompany(), asOf="2020Q4")
    equivalent = buildSnapshot(FakeCompany(), asOf="2020Q4")

    assert snapshot["baseRevenue"] == 100.0
    assert snapshot["dataSnapshotId"].startswith("data-content-snapshot:")
    assert snapshot["dataCatalogSnapshotId"].startswith("data-snapshot:")
    assert len(snapshot["dataContractHash"]) == 64
    assert snapshot["dataLineageRefs"]
    assert snapshot["dataExecutionReceipts"][0].startswith("data-execution:")
    assert snapshot["dataContractHash"] == equivalent["dataContractHash"]
    assert snapshot["dataSnapshotId"] == equivalent["dataSnapshotId"]


def testWorkbenchBridgeUsesCanonicalNameAndPreservesPartitionGaps(monkeypatch):
    import dartlab
    from dartlab.simulate.registry import _workbenchFinanceInputs

    payload = {
        "series": {"IS": {"sales": [1.0]}, "BS": {}, "CF": {}},
        "shares": None,
        "asOf": "2024-Q4",
        "latestAsOf": "2024-Q4",
        "requestedAsOf": "2024-Q4",
    }
    captured = {}

    def canonicalCall(action, axis, *, query, _runtimeBindings):
        captured["query"] = query
        captured["runtimeBindings"] = _runtimeBindings
        asset = SimpleNamespace(assetId="analysis.simulationInputs", assetVersionId="asset-version:test")
        partition = SimpleNamespace(
            data=payload,
            asset=asset,
            requestId=None,
            selector=(("subject", "000001"),),
            temporalStatus="validAt",
            contentHash="p" * 64,
            truncated=False,
        )
        return SimpleNamespace(
            status="partial",
            partitions=(partition,),
            assets=(asset,),
            coverage=SimpleNamespace(
                requestedAssets=1,
                resolvedAssets=1,
                succeededPartitions=1,
                failedPartitions=0,
            ),
            gaps=(
                SimpleNamespace(
                    code="FEATURE_OBSERVATION_CONDITIONAL",
                    message="unsigned history",
                    assetId="analysis.simulationInputs",
                    subject="000001",
                    systemic=False,
                    requestId=None,
                ),
            ),
            dataSnapshotId="data-content-snapshot:sealed",
            snapshotId="data-snapshot:catalog",
            contractHash="c" * 64,
            lineageRefs=("lineage:test",),
            executionReceipts=("data-execution:test",),
            qualityAssertions=(),
            materializationReceipt=None,
        )

    monkeypatch.setattr(dartlab, "dataHub", canonicalCall)
    monkeypatch.setattr(
        dartlab,
        "data",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("legacy alias called")),
    )

    result, metadata = _workbenchFinanceInputs(SimpleNamespace(stockCode="000001"), "2024Q4")

    assert result is payload
    assert captured["query"].params == {}
    assert captured["runtimeBindings"]["analysis.simulationInputs"]["company"].stockCode == "000001"
    assert metadata["dataInputGaps"] == ("FEATURE_OBSERVATION_CONDITIONAL:unsigned history",)
    assert metadata["dataEvidence"]["status"] == "partial"
    assert metadata["dataEvidence"]["partitions"][0]["contentHash"] == "p" * 64


def testRuntimeCompanyBindingCannotRelabelAnotherSubject():
    import dartlab
    from dartlab.dataHub import DataQuery

    with pytest.raises(ValueError, match="subject"):
        dartlab.dataHub(
            "query",
            "analysis.simulationInputs",
            query=DataQuery(subjects=("000001",)),
            _runtimeBindings={"analysis.simulationInputs": {"company": SimpleNamespace(stockCode="999999")}},
        )


def testDataQueryParamsRejectOpaqueRuntimeObjects():
    from dartlab.dataHub import DataQuery

    with pytest.raises(TypeError, match="JSON-safe"):
        DataQuery(params={"company": object()})
