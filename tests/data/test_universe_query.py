"""KR DART와 US EDGAR 전종목 Data Workbench query 계약 검증."""

from __future__ import annotations

import threading
import time

import polars as pl
import pytest

from dartlab.data import DataQuery, FactorProjection, QueryBudget, UniverseSelection


def _installUniverseFixtures(monkeypatch) -> None:
    kr = pl.DataFrame(
        {
            "회사명": ["삼성전자", "SK하이닉스"],
            "시장구분": ["유가", "유가"],
            "종목코드": ["005930", "000660"],
        }
    )
    us = pl.DataFrame(
        {
            "cik": ["0000320193", "0000789019"],
            "ticker": ["AAPL", "MSFT"],
            "title": ["Apple", "Microsoft"],
            "exchange": ["Nasdaq", "Nasdaq"],
            "is_exchange_listed": [True, True],
            "is_otc": [False, False],
        }
    )
    monkeypatch.setattr("dartlab.gather.krx.listing.registry.getKindList", lambda: kr)
    monkeypatch.setattr("dartlab.core.dataLoader.loadEdgarTargetUniverse", lambda tier="all": us)


def _marketFrame(market: str) -> pl.DataFrame:
    if market == "KR":
        return pl.DataFrame(
            {
                "stockCode": ["005930", "000660"],
                "corpName": ["삼성전자", "SK하이닉스"],
                "2025": [300.0, 100.0],
            }
        )
    return pl.DataFrame(
        {
            "stockCode": ["AAPL", "MSFT"],
            "corpName": ["Apple", "Microsoft"],
            "2025": [390.0, 280.0],
        }
    )


def testUniverseSelectionCanonicalizesAndDoesNotConsumeSubjectBudget():
    selection = UniverseSelection(markets=("us", "KR", "US"))
    query = DataQuery(universe=selection, budget=QueryBudget(maxSubjects=1))

    assert selection.markets == ("KR", "US")
    assert query.universe == selection
    with pytest.raises(ValueError, match="동시에"):
        DataQuery(subjects=("005930",), universe=selection)


def testScanCatalogDeclaresMarketBulkCapability():
    import dartlab

    byId = {asset.assetId: asset for asset in dartlab.data("catalog").assets}
    account = byId["scan.account"]
    governance = byId["scan.governance"]
    fields = byId["scan.fields"]

    assert account.executionMode == "ownerBulk"
    assert account.universeMarkets == ("KR", "US")
    assert account.marketUnits == (("KR", "KRW"), ("US", "USD"))
    assert account.concurrencyGroup == "local-finance-scan"
    assert governance.universeMarkets == ("KR",)
    assert fields.executionMode == "unsupported"


def testOneQueryCallsDartAndEdgarOnceEachWithoutSubjectFanout(monkeypatch):
    import dartlab

    _installUniverseFixtures(monkeypatch)
    calls = []

    def fakeScan(axis, target=None, **kwargs):
        calls.append((axis, target, kwargs))
        return _marketFrame(kwargs["market"])

    monkeypatch.setattr(dartlab, "scan", fakeScan)
    result = dartlab.data(
        "query",
        "scan.account",
        query=DataQuery(
            universe=UniverseSelection(("KR", "US")),
            measures=("sales",),
            budget=QueryBudget(maxConcurrency=2),
        ),
    )

    assert result.status == "ok"
    assert sorted(calls, key=lambda row: row[2]["market"]) == [
        ("account", "sales", {"market": "KR"}),
        ("account", "sales", {"market": "US"}),
    ]
    assert [partition.selector for partition in result.partitions] == [
        (("market", "KR"), ("measure", "sales")),
        (("market", "US"), ("measure", "sales")),
    ]
    assert [
        (row.market, row.requestedEntities, row.matchedEntities, row.status) for row in result.universeCoverage
    ] == [
        ("KR", 2, 2, "complete"),
        ("US", 2, 2, "complete"),
    ]
    assert result.universeSnapshotId is not None


def testLocalDartAndEdgarFinanceScansShareOneIoConcurrencyGroup(monkeypatch):
    import dartlab

    _installUniverseFixtures(monkeypatch)
    lock = threading.Lock()
    active = 0
    peak = 0

    def fakeScan(axis, target=None, **kwargs):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.02)
        with lock:
            active -= 1
        return _marketFrame(kwargs["market"])

    monkeypatch.setattr(dartlab, "scan", fakeScan)
    result = dartlab.data(
        "query",
        "scan.account",
        query=DataQuery(
            universe=UniverseSelection(("KR", "US")),
            measures=("sales",),
            budget=QueryBudget(maxConcurrency=2),
        ),
    )

    assert result.status == "ok"
    assert peak == 1


def testFactorProjectionNamespacesMarketsAndUsesNativeCurrency(monkeypatch):
    import dartlab

    _installUniverseFixtures(monkeypatch)
    monkeypatch.setattr(dartlab, "scan", lambda axis, target=None, **kwargs: _marketFrame(kwargs["market"]))
    result = dartlab.data(
        "query",
        "scan.account",
        query=DataQuery(
            universe=UniverseSelection(("KR", "US")),
            projection=FactorProjection(measures=("sales",), frequency="Y"),
            budget=QueryBudget(maxConcurrency=2),
        ),
    )

    assert result.status == "ok"
    kr, us = (partition.data for partition in result.partitions)
    assert set(kr["entityId"].to_list()) == {"KR:005930", "KR:000660"}
    assert set(us["entityId"].to_list()) == {"US:AAPL", "US:MSFT"}
    assert kr["market"].unique().to_list() == ["KR"]
    assert us["market"].unique().to_list() == ["US"]
    assert kr["unit"].unique().to_list() == ["KRW"]
    assert us["unit"].unique().to_list() == ["USD"]


def testUnsupportedMarketIsAVisibleGapAndSupportedMarketStillRuns(monkeypatch):
    import dartlab

    _installUniverseFixtures(monkeypatch)
    calls = []

    def fakeScan(axis, **kwargs):
        calls.append((axis, kwargs))
        return _marketFrame("KR")

    monkeypatch.setattr(dartlab, "scan", fakeScan)
    result = dartlab.data(
        "query",
        "scan.governance",
        query=DataQuery(universe=UniverseSelection(("KR", "US"))),
    )

    assert calls == [("governance", {"market": "KR"})]
    assert result.status == "partial"
    assert "UNIVERSE_MARKET_UNSUPPORTED" in {gap.code for gap in result.gaps}
    coverage = {row.market: row for row in result.universeCoverage}
    assert coverage["KR"].status == "complete"
    assert coverage["US"].status == "failed"


def testHistoricalUniverseFailsBeforeOwnerCall(monkeypatch):
    import dartlab

    called = False

    def fakeScan(*args, **kwargs):
        nonlocal called
        called = True
        return _marketFrame("KR")

    monkeypatch.setattr(dartlab, "scan", fakeScan)
    result = dartlab.data(
        "query",
        "scan.governance",
        query=DataQuery(universe=UniverseSelection(("KR",), asOf="2025-01-01")),
    )

    assert not called
    assert result.status == "failed"
    assert "UNIVERSE_PIT_UNSUPPORTED" in {gap.code for gap in result.gaps}


def testJsonMappingCanDeclareCrossMarketUniverse(monkeypatch):
    import dartlab

    _installUniverseFixtures(monkeypatch)
    monkeypatch.setattr(dartlab, "scan", lambda axis, target=None, **kwargs: _marketFrame(kwargs["market"]))
    result = dartlab.data(
        "query",
        "scan.account",
        query={
            "universe": {"markets": ["KR", "US"], "membership": "listed"},
            "measures": ["sales"],
            "budget": {"maxConcurrency": 2},
        },
    )

    assert result.status == "ok"
    assert {row.market for row in result.universeCoverage} == {"KR", "US"}
