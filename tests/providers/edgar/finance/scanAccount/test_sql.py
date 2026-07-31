"""scanAccount DuckDB SQL 과 실행 상한 계약 회귀."""

from __future__ import annotations

import pytest

from dartlab.providers.edgar.finance.scanAccount import sql

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("name", "low", "high"),
    [
        ("_DUCKDB_THREADS", 1, 16),
        ("_DUCKDB_MEMORY_LIMIT_MB", 32, 4096),
        ("_DUCKDB_BATCH_THREADS", 1, 16),
        ("_DUCKDB_BATCH_MEMORY_LIMIT_MB", 32, 4096),
        ("_DUCKDB_BATCH_ACCOUNT_LIMIT", 1, 64),
    ],
)
def testExecutionLimitsStayBounded(name: str, low: int, high: int) -> None:
    """실행 상한은 OOM 가드다. 무제한이나 0 으로 풀리지 않는다."""
    value = getattr(sql, name)

    assert isinstance(value, int)
    assert low <= value <= high


@pytest.mark.parametrize("name", ["_DUCKDB_YEAR_SQL", "_DUCKDB_BATCH_YEAR_SQL"])
def testYearSqlSelectsBothTaxonomies(name: str) -> None:
    """연도 집계 SQL 은 us-gaap 과 ifrs-full 을 모두 훑는다."""
    text = getattr(sql, name)

    assert "us-gaap" in text
    assert "ifrs-full" in text
    assert "GROUP BY" in text


def testBatchSqlKeepsAccountIdentity() -> None:
    """batch SQL 은 계정을 snakeId 로 구분해 서로 섞이지 않게 한다."""
    assert "snakeId" in sql._DUCKDB_BATCH_YEAR_SQL
