"""Unified Data Workbench root public surface tests."""

from __future__ import annotations


def testRootDataIsCallableAndHasOnlyTwoAxes():
    import dartlab
    from dartlab.dataHub import AsyncDataHubClient, DataHubClient, DataHubWorker

    assert callable(dartlab.dataHub)
    assert callable(dartlab.data)
    assert dartlab.dataHub is dartlab.data
    guide = dartlab.dataHub()
    assert guide["axis"].to_list() == ["catalog", "query"]
    queryExample = guide.filter(guide["axis"] == "query")["예시"].item()
    assert "resource.finance" in queryExample
    assert "resource.edgar" in queryExample
    assert DataHubClient.__name__ == "DataHubClient"
    assert AsyncDataHubClient.__name__ == "AsyncDataHubClient"
    assert DataHubWorker.__name__ == "DataHubWorker"


def testCapabilityCatalogIncludesDataAndAnalysisAxes():
    import dartlab

    capabilities = dartlab.capabilities()
    keys = set(capabilities)
    assert {"dataHub.catalog", "dataHub.query"} <= keys
    assert sum(key.startswith("analysis.") for key in keys) == 22


def testDataHubPrivateRootUsesCanonicalName(tmp_path, monkeypatch):
    from dartlab.dataHub.pagingRuntime import dataHubRoot

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    assert dataHubRoot() == tmp_path / "dataHub"
