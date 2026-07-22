"""Contract tests for source-native EDGAR universe account scans."""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
from polars.testing import assert_frame_equal

ATTEMPT_DIR = Path(__file__).resolve().parent
if str(ATTEMPT_DIR) not in sys.path:
    sys.path.insert(0, str(ATTEMPT_DIR))

from prototype import (  # noqa: E402
    EdgarScanContext,
    scanAccountsDuckDbNative,
    scanArrowBatched,
    scanDuckDbBatched,
    scanDuckDbNative,
    scanPolarsNative,
)


def _writeCompany(path: Path, cik: str, rows: list[dict[str, object]]) -> None:
    base = {
        "cik": cik,
        "entityName": "Test Corp",
        "namespace": "us-gaap",
        "tag": "Revenues",
        "label": "Revenue",
        "unit": "USD",
        "form": "10-Q",
        "filed": None,
        "frame": None,
        "start": None,
        "end": None,
        "accn": "x",
    }
    pl.DataFrame([{**base, **row} for row in rows]).write_parquet(path)


def _context(tmpPath: Path) -> EdgarScanContext:
    first = tmpPath / "0000000001.parquet"
    second = tmpPath / "0000000002.parquet"
    ignored = tmpPath / "0000000003.parquet"
    _writeCompany(
        first,
        "0000000000",
        [
            {"fy": 2023, "fp": "Q1", "val": 30.0},
            {"fy": 2023, "fp": "Q1", "val": -20.0},
            {"fy": 2023, "fp": "Q2", "val": 40.0},
            {"fy": 2023, "fp": "Q3", "val": 50.0},
            {"fy": 2023, "fp": "FY", "val": 200.0},
            {"fy": 2023, "fp": "FY", "val": 999.0},
        ],
    )
    _writeCompany(
        second,
        "0000000002",
        [
            {"fy": 2023, "fp": "Q1", "val": 10.0},
            {"fy": 2023, "fp": "FY", "val": 80.0},
        ],
    )
    _writeCompany(ignored, "0000000003", [{"fy": 2023, "fp": "FY", "val": 7.0}])
    return EdgarScanContext(
        allPaths=(first, second, ignored),
        listedPaths=(first, second),
        tickerMap={"0000000001": "AAA", "0000000002": "BBB"},
        tagKeys=frozenset({"revenues"}),
    )


def _canonical(frame: pl.DataFrame) -> pl.DataFrame:
    return (
        frame.drop("corpName", strict=False)
        .sort("stockCode")
        .select(sorted(frame.drop("corpName", strict=False).columns))
    )


def testDuckDbAndPolarsPreserveQuarterlySemantics(tmp_path: Path) -> None:
    context = _context(tmp_path)
    duck = _canonical(scanDuckDbNative(context, threads=1))
    polars = _canonical(scanPolarsNative(context))
    assert_frame_equal(duck, polars, check_column_order=False)

    aaa = duck.filter(pl.col("stockCode") == "AAA").row(0, named=True)
    assert aaa["2023Q1"] == -20.0
    assert aaa["2023Q4"] == 130.0
    bbb = duck.filter(pl.col("stockCode") == "BBB").row(0, named=True)
    assert bbb["2023Q4"] == 80.0


def testListedPathPruningExcludesUnmappedFiles(tmp_path: Path) -> None:
    context = _context(tmp_path)
    result = scanDuckDbNative(context, threads=1, pruneListed=True)
    assert set(result["stockCode"].to_list()) == {"AAA", "BBB"}


def testFilenameCikOverridesBrokenPayloadCik(tmp_path: Path) -> None:
    context = _context(tmp_path)
    result = scanDuckDbNative(context, threads=1)
    assert "AAA" in result["stockCode"].to_list()


def testBatchedDuckDbMatchesSingleScan(tmp_path: Path) -> None:
    context = _context(tmp_path)
    expected = _canonical(scanDuckDbNative(context, threads=1))
    actual = _canonical(scanDuckDbBatched(context, batchFiles=1, threads=1))
    assert_frame_equal(expected, actual, check_column_order=False)


def testArrowBatchMatchesSingleScan(tmp_path: Path) -> None:
    context = _context(tmp_path)
    expected = _canonical(scanDuckDbNative(context, threads=1))
    actual = _canonical(scanArrowBatched(context, batchFiles=1, rowBatchSize=2))
    assert_frame_equal(expected, actual, check_column_order=False)


def testTwoMeasuresShareOneSourceScan(tmp_path: Path) -> None:
    base = _context(tmp_path)
    firstPath = base.listedPaths[0]
    rows = pl.read_parquet(firstPath).to_dicts()
    rows.append(
        {
            **rows[0],
            "tag": "OperatingIncomeLoss",
            "fy": 2023,
            "fp": "FY",
            "val": 55.0,
        }
    )
    pl.DataFrame(rows).write_parquet(firstPath)
    operating = EdgarScanContext(
        allPaths=base.allPaths,
        listedPaths=base.listedPaths,
        tickerMap=base.tickerMap,
        tagKeys=frozenset({"operatingincomeloss"}),
    )
    results = scanAccountsDuckDbNative({"sales": base, "operating_profit": operating}, threads=1)
    assert set(results) == {"sales", "operating_profit"}
    op = results["operating_profit"].filter(pl.col("stockCode") == "AAA").row(0, named=True)
    assert op["2023Q4"] == 55.0
