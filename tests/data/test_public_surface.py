"""Unified Data Workbench root public surface tests."""

from __future__ import annotations


def testRootDataIsCallableAndHasOnlyTwoAxes():
    import dartlab

    assert callable(dartlab.data)
    guide = dartlab.data()
    assert guide["axis"].to_list() == ["catalog", "query"]
    queryExample = guide.filter(guide["axis"] == "query")["예시"].item()
    assert "resource.finance" in queryExample
    assert "resource.edgar" in queryExample


def testCapabilityCatalogIncludesDataAndAnalysisAxes():
    import dartlab

    capabilities = dartlab.capabilities()
    keys = set(capabilities)
    assert {"data.catalog", "data.query"} <= keys
    assert sum(key.startswith("analysis.") for key in keys) == 22
