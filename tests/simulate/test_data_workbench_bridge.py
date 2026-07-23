"""Simulator가 통합 Data Workbench 입력 스냅샷을 실제로 소비하는지 검증한다."""

from __future__ import annotations


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

    monkeypatch.setattr("dartlab.simulate.registry._getSeriesAndShares", lambda company: (None, 100, "KRW"))
    monkeypatch.setattr("dartlab.simulate.registry._resolveSectorKey", lambda company: None)

    snapshot = buildSnapshot(FakeCompany(), asOf="2020Q4")

    assert snapshot["baseRevenue"] == 100.0
    assert snapshot["dataSnapshotId"].startswith("data-content-snapshot:")
    assert snapshot["dataCatalogSnapshotId"].startswith("data-snapshot:")
    assert len(snapshot["dataContractHash"]) == 64
    assert snapshot["dataLineageRefs"]
    assert snapshot["dataExecutionReceipts"][0].startswith("data-execution:")
