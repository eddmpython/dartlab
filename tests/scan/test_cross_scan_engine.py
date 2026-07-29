"""CrossScanQuery와 Polars, DuckDB parquet engine 동치 회귀."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from dartlab.scan.io.cross import (
    CrossScanEngine,
    CrossScanQuery,
    DuckDbCrossScan,
    PolarsCrossScan,
    pickCrossScanEngine,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def docsIndex(tmp_path: Path) -> Path:
    """3개 회사의 최소 docs index parquet."""

    path = tmp_path / "docsIndex.parquet"
    pl.DataFrame(
        {
            "stockCode": ["005930", "005930", "000660", "000660", "035420"],
            "year": [2023, 2024, 2023, 2024, 2024],
            "sectionTitle": ["BS", "IS[별도]", "BS", "IS", "BS"],
            "contentLength": [1000, 2000, 0, 2500, 3000],
        }
    ).write_parquet(path)
    return path


def test_engines_implement_protocol() -> None:
    assert isinstance(PolarsCrossScan(), CrossScanEngine)
    assert isinstance(DuckDbCrossScan(), CrossScanEngine)


@pytest.mark.parametrize(
    "queryArgs, expectedRows",
    [
        ({}, 5),
        ({"year": 2024}, 3),
        ({"stockCodes": ("005930", "035420")}, 3),
        ({"onlyWithContent": True}, 4),
        ({"limit": 2}, 2),
        ({"sectionTitle": "IS["}, 1),
    ],
)
def test_polars_and_duckdb_are_equivalent(
    docsIndex: Path,
    queryArgs: dict,
    expectedRows: int,
) -> None:
    """두 엔진은 literal filter와 limit에서 같은 결과를 반환한다."""

    query = CrossScanQuery(path=docsIndex, **queryArgs)
    polarsResult = PolarsCrossScan().execute(query)
    duckDbResult = DuckDbCrossScan().execute(query)

    assert polarsResult.height == duckDbResult.height == expectedRows
    assert set(polarsResult.columns) == set(duckDbResult.columns)
    assert polarsResult.sort(polarsResult.columns).equals(duckDbResult.sort(duckDbResult.columns))


def test_duckdb_reads_parquet_without_polars_collect(
    docsIndex: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DuckDB 경로는 Polars LazyFrame을 먼저 materialize하지 않는다."""

    monkeypatch.setattr(
        pl.LazyFrame,
        "collect",
        lambda *_args, **_kwargs: pytest.fail("DuckDB engine must not collect a Polars LazyFrame"),
    )

    result = DuckDbCrossScan(memoryLimitMb=64, threads=1).execute(CrossScanQuery(path=docsIndex, year=2024))

    assert result.height == 3


def test_dispatcher_validates_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DARTLAB_CROSS_SCAN_ENGINE", raising=False)
    assert isinstance(pickCrossScanEngine(), PolarsCrossScan)

    monkeypatch.setenv("DARTLAB_CROSS_SCAN_ENGINE", "duckdb")
    assert isinstance(pickCrossScanEngine(), DuckDbCrossScan)
    assert isinstance(pickCrossScanEngine(engine="polars"), PolarsCrossScan)

    with pytest.raises(ValueError, match="지원하지 않는 cross scan engine"):
        pickCrossScanEngine(engine="dukdb")


@pytest.mark.parametrize("limit", [0, -1])
def test_query_rejects_non_positive_limit(docsIndex: Path, limit: int) -> None:
    with pytest.raises(ValueError, match="limit"):
        CrossScanQuery(path=docsIndex, limit=limit)
