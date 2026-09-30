"""원자료 전체 계산, 근거 연결, 세션 격리와 SQL 읽기 경계를 검증한다."""

from __future__ import annotations

import importlib

import polars as pl
import pytest

from dartlab.ai.contracts import Ref
from dartlab.ai.tools.queryTable import captureTable, queryTable, tableScope
from dartlab.core.memory import BoundedCache

pytestmark = pytest.mark.unit


@pytest.fixture
def table():
    with tableScope(BoundedCache()):
        frame = pl.DataFrame({"year": [2023, 2024, 2025], "sales": [10.0, None, 20.0]})
        yield captureTable(
            frame, [Ref(id="source:finance", kind="tableRef", title="원자료", source="test", payload={})]
        )


def testWindowPreservesMissingValueAndSource(table):
    result = queryTable(
        {"t": table["tableId"]}, "SELECT year, sales / lag(sales) OVER (ORDER BY year) - 1 AS growth FROM t"
    )
    assert result.ok
    assert result.refs[0].payload["rows"] == [{"year": year, "growth": None} for year in (2023, 2024, 2025)]
    assert "source:finance" in result.refs[0].payload["sourceRefs"]
    assert table["snapshotRef"] in result.refs[0].payload["sourceRefs"]
    assert result.refs[1].payload["sql"].startswith("SELECT")
    nextResult = queryTable({"derived": result.data["table"]["tableId"]}, "SELECT COUNT(*) AS n FROM derived")
    assert nextResult.refs[0].payload["rows"] == [{"n": 3}]
    assert result.refs[0].id in nextResult.refs[0].payload["sourceRefs"]


def testWholeInputIsQueriedBeforeOutputLimit():
    with tableScope(BoundedCache()):
        table = captureTable(pl.DataFrame({"x": range(5000)}), [])
        result = queryTable({"t": table["tableId"]}, "SELECT COUNT(*) AS n, MAX(x) AS biggest FROM t", limit=1)
        assert result.refs[0].payload["rows"] == [{"n": 5000, "biggest": 4999}]
        result = queryTable({"t": table["tableId"]}, "SELECT x FROM t ORDER BY x DESC", limit=2)
        assert result.refs[0].payload["rows"] == [{"x": 4999}, {"x": 4998}]
        assert result.data["truncated"]
        assert "table" not in result.data


def testJoinUsesBothSourceTables(table):
    other = captureTable(pl.DataFrame({"year": [2025], "cost": [5.0]}), [])
    result = queryTable(
        {"a": table["tableId"], "b": other["tableId"]},
        "SELECT a.year, (a.sales-b.cost)/a.sales AS margin FROM a JOIN b ON a.year=b.year",
    )
    assert result.refs[0].payload["rows"] == [{"year": 2025, "margin": 0.75}]


def testSqlTextFilterUsesLike():
    with tableScope(BoundedCache()):
        handle = captureTable(pl.DataFrame({"name": ["삼성전자", "삼성물산", "현대건설"]}), [])
        result = queryTable({"t": handle["tableId"]}, "SELECT name FROM t WHERE name LIKE '삼성%'")
    assert result.ok
    assert result.refs[0].payload["rows"] == [{"name": "삼성전자"}, {"name": "삼성물산"}]


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM t",
        "UPDATE t SET sales=0",
        "DROP TABLE t",
        "CREATE TABLE stolen(x)",
        "ATTACH DATABASE ':memory:' AS other",
        "PRAGMA database_list",
        "VACUUM",
        "SELECT load_extension('missing')",
        "SELECT readfile('private')",
        "SELECT writefile('private', 'data')",
        "SELECT randomblob(1000000000)",
        "SELECT * FROM sqlite_master",
        "SELECT * FROM t; DELETE FROM t",
        "WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n) SELECT SUM(x) FROM n",
    ],
)
def testReadOnlySqlRejectsWritesFilesAndUnboundedGenerators(table, sql):
    assert not queryTable({"t": table["tableId"]}, sql).ok
    assert queryTable({"t": table["tableId"]}, "SELECT SUM(sales) AS total FROM t").refs[0].payload["rows"] == [
        {"total": 30.0}
    ]


def testSessionIsolationAndEviction(table):
    with tableScope(BoundedCache()):
        assert queryTable({"t": table["tableId"]}, "SELECT * FROM t").error == "table_not_found"
    assert queryTable({"t": table["tableId"]}, "SELECT * FROM t").ok
    with tableScope(BoundedCache(maxEntries=1)):
        first = captureTable(pl.DataFrame({"x": [1]}), [])
        captureTable(pl.DataFrame({"x": [2]}), [])
        assert queryTable({"t": first["tableId"]}, "SELECT * FROM t").error == "table_not_found"


def testLargeTableIsNotRetained():
    with tableScope(BoundedCache()):
        result = captureTable(pl.DataFrame({"x": ["x" * 1000] * 5000}), [])
    assert result["reason"] == "table_budget_exceeded"
    assert "tableId" not in result


def testWideSqlResultStopsAtByteBudget():
    with tableScope(BoundedCache()):
        handle = captureTable(pl.DataFrame({"body": ["x" * 4000] * 100}), [])
        result = queryTable({"t": handle["tableId"]}, "SELECT body FROM t", limit=500)
    assert result.ok and result.data["truncated"]
    assert 0 < len(result.refs[0].payload["rows"]) < 10
    assert "table" not in result.data


def testSqlDeadlineInterruptsExpensiveQuery(table, monkeypatch):
    module = importlib.import_module("dartlab.ai.tools.queryTable")
    ticks = iter([0, 10, 10, 10])
    monkeypatch.setattr(module.time, "monotonic", lambda: next(ticks, 10))
    result = queryTable({"t": table["tableId"]}, "SELECT SUM(a.sales) FROM t a,t b,t c,t d,t e,t f,t g")
    assert result.error == "invalid_table_query"
    assert "interrupted" in result.summary


def testOnlyNativeSessionAdvertisesQueryTable():
    from dartlab.ai.runtime.sessionTools import sessionToolSpecs
    from dartlab.ai.tools.registry import agentToolSpecs

    assert "QueryTable" in {tool["name"] for tool in sessionToolSpecs()}
    assert "QueryTable" not in {tool["name"] for tool in agentToolSpecs()}


def testDataHubNativePartitionRetainsPartialCoverage():
    from dartlab.ai.tools.queryTable import capturePartition
    from dartlab.dataHub.contracts import AssetRef, DataPartition

    partition = DataPartition(
        asset=AssetRef("scan.ratio", "v1"),
        projectionKind="native",
        data=pl.DataFrame({"code": ["005930"], "roe": [12.0]}),
        schema=(("roe", "Float64"),),
        rowCount=1,
        truncated=True,
        selector=(),
        temporalStatus="latest",
        lineageRefs=("lineage:1",),
    )
    with tableScope(BoundedCache()):
        handle = capturePartition(partition, [], status="partial")
        result = queryTable({"t": handle["tableId"]}, "SELECT AVG(roe) AS average FROM t")
    assert result.refs[0].payload["rows"] == [{"average": 12.0}]
    assert result.refs[0].payload["inputCoverage"] == {"t": "dataHub_partial_partition"}
