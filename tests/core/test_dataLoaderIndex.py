"""로컬 parquet 종목 인덱스의 projection·오류 계약 회귀."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import polars as pl
import pytest

_INDEX_COLUMNS = ["stockCode", "corpName", "rows", "yearFrom", "yearTo", "nDocs"]


def _panelDir(tmpPath: Path) -> Path:
    target = tmpPath / "dart" / "panel"
    target.mkdir(parents=True)
    return target


def test_buildIndex_projects_metadata_columns_without_full_read(tmp_path: Path, monkeypatch) -> None:
    from dartlab import config
    from dartlab.core import dataLoader

    panelDir = _panelDir(tmp_path)
    pl.DataFrame(
        {
            "corp_name": ["테스트", "테스트", None],
            "period": ["2023Q4", "2024Q1", None],
            "rceptNo": ["A", "B", None],
            "contentRaw": ["x" * 100_000, "y" * 100_000, "z" * 100_000],
        }
    ).write_parquet(panelDir / "000001.parquet")
    monkeypatch.setattr(config, "dataDir", str(tmp_path))
    monkeypatch.setattr(
        dataLoader.pl,
        "read_parquet",
        lambda *_args, **_kwargs: pytest.fail("buildIndex가 전체 parquet read 경로를 사용함"),
    )

    result = dataLoader.buildIndex()

    assert result.columns == _INDEX_COLUMNS
    assert result.schema == {
        "stockCode": pl.String,
        "corpName": pl.String,
        "rows": pl.Int64,
        "yearFrom": pl.String,
        "yearTo": pl.String,
        "nDocs": pl.Int64,
    }
    assert result.to_dicts() == [
        {
            "stockCode": "000001",
            "corpName": "테스트",
            "rows": 3,
            "yearFrom": "2023",
            "yearTo": "2024",
            "nDocs": 2,
        }
    ]


def test_buildIndex_does_not_present_identifier_as_company_name(tmp_path: Path, monkeypatch) -> None:
    from dartlab import config
    from dartlab.core.dataLoader import buildIndex

    panelDir = _panelDir(tmp_path)
    pl.DataFrame(
        {
            "corp": ["005930"],
            "period": ["2024Q4"],
            "rceptNo": ["202501010001"],
        }
    ).write_parquet(panelDir / "005930.parquet")
    monkeypatch.setattr(config, "dataDir", str(tmp_path))

    row = buildIndex().row(0, named=True)

    assert row["stockCode"] == "005930"
    assert row["corpName"] is None


def test_buildIndex_missing_columns_and_empty_file_keep_exact_schema(tmp_path: Path, monkeypatch) -> None:
    from dartlab import config
    from dartlab.core.dataLoader import buildIndex

    panelDir = _panelDir(tmp_path)
    pl.DataFrame({"payload": ["x", "y"]}).write_parquet(panelDir / "000002.parquet")
    pl.DataFrame(schema={"corp_name": pl.String, "period": pl.String, "rceptNo": pl.String}).write_parquet(
        panelDir / "000003.parquet"
    )
    monkeypatch.setattr(config, "dataDir", str(tmp_path))

    result = buildIndex()

    assert result.schema == {
        "stockCode": pl.String,
        "corpName": pl.String,
        "rows": pl.Int64,
        "yearFrom": pl.String,
        "yearTo": pl.String,
        "nDocs": pl.Int64,
    }
    assert result.to_dicts() == [
        {
            "stockCode": "000002",
            "corpName": None,
            "rows": 2,
            "yearFrom": None,
            "yearTo": None,
            "nDocs": 0,
        },
        {
            "stockCode": "000003",
            "corpName": None,
            "rows": 0,
            "yearFrom": None,
            "yearTo": None,
            "nDocs": 0,
        },
    ]


def test_buildIndex_empty_directory_has_exact_schema(tmp_path: Path, monkeypatch) -> None:
    from dartlab import config
    from dartlab.core.dataLoader import buildIndex

    _panelDir(tmp_path)
    monkeypatch.setattr(config, "dataDir", str(tmp_path))

    result = buildIndex()

    assert result.columns == _INDEX_COLUMNS
    assert result.schema == {
        "stockCode": pl.String,
        "corpName": pl.String,
        "rows": pl.Int64,
        "yearFrom": pl.String,
        "yearTo": pl.String,
        "nDocs": pl.Int64,
    }
    assert result.is_empty()


def test_buildIndex_corrupt_file_raises_contextual_error(tmp_path: Path, monkeypatch) -> None:
    from dartlab import config
    from dartlab.core.dataLoader import DataIndexError, buildIndex

    panelDir = _panelDir(tmp_path)
    corrupt = panelDir / "000004.parquet"
    corrupt.write_bytes(b"not parquet")
    monkeypatch.setattr(config, "dataDir", str(tmp_path))

    with pytest.raises(DataIndexError) as caught:
        buildIndex()

    assert caught.value.category == "panel"
    assert caught.value.path == corrupt
    assert str(corrupt) in str(caught.value)
    assert caught.value.__cause__ is not None
    assert isinstance(caught.value.__cause__, pl.exceptions.PolarsError)


def test_buildIndex_supports_edgar_name_year_and_accession(tmp_path: Path, monkeypatch) -> None:
    from dartlab import config
    from dartlab.core.dataLoader import buildIndex

    docsDir = tmp_path / "edgar" / "docs"
    docsDir.mkdir(parents=True)
    pl.DataFrame(
        {
            "company_name": ["Apple Inc.", "Apple Inc.", "Apple Inc."],
            "year": ["2022", "2024", None],
            "accession_no": ["a", "b", None],
            "section_content": ["large" * 10_000] * 3,
        }
    ).write_parquet(docsDir / "AAPL.parquet")
    monkeypatch.setattr(config, "dataDir", str(tmp_path))

    result = buildIndex(category="edgarDocs")

    assert result.to_dicts() == [
        {
            "stockCode": "AAPL",
            "corpName": "Apple Inc.",
            "rows": 3,
            "yearFrom": "2022",
            "yearTo": "2024",
            "nDocs": 2,
        }
    ]


def test_buildIndex_falls_back_from_empty_or_invalid_preferred_aliases(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from dartlab import config
    from dartlab.core.dataLoader import buildIndex

    panelDir = _panelDir(tmp_path)
    pl.DataFrame(
        {
            "corp_name": [None, None],
            "company_name": ["Correct Inc.", "Correct Inc."],
            "year": ["제8기 1분기", None],
            "bsns_year": ["2023", "2024"],
            "rcept_no": [None, None],
            "rceptNo": ["one", "two"],
        },
        schema={
            "corp_name": pl.String,
            "company_name": pl.String,
            "year": pl.String,
            "bsns_year": pl.String,
            "rcept_no": pl.String,
            "rceptNo": pl.String,
        },
    ).write_parquet(panelDir / "000005.parquet")
    monkeypatch.setattr(config, "dataDir", str(tmp_path))

    assert buildIndex().to_dicts() == [
        {
            "stockCode": "000005",
            "corpName": "Correct Inc.",
            "rows": 2,
            "yearFrom": "2023",
            "yearTo": "2024",
            "nDocs": 2,
        }
    ]


def test_buildDataIndex_bounds_in_flight_work_to_worker_count(tmp_path: Path, monkeypatch) -> None:
    import dartlab.core.dataLoaderIndex as indexModule

    gate = threading.Event()
    started = 0
    startedLock = threading.Lock()

    def fakeRead(path: Path, _category: str) -> dict:
        nonlocal started
        with startedLock:
            started += 1
        gate.wait(timeout=5)
        return {
            "stockCode": path.stem,
            "corpName": None,
            "rows": 0,
            "yearFrom": None,
            "yearTo": None,
            "nDocs": 0,
        }

    files = [tmp_path / f"{index:06d}.parquet" for index in range(100)]
    monkeypatch.setattr(indexModule, "_readLazyRecord", fakeRead)

    with ThreadPoolExecutor(max_workers=1) as caller:
        resultFuture = caller.submit(indexModule.buildDataIndex, files, "panel")
        try:
            deadline = time.monotonic() + 2
            while started < indexModule._MAX_INDEX_WORKERS and time.monotonic() < deadline:
                time.sleep(0.01)
            assert started == indexModule._MAX_INDEX_WORKERS
            time.sleep(0.05)
            assert started == indexModule._MAX_INDEX_WORKERS
        finally:
            gate.set()
        result = resultFuture.result(timeout=5)

    assert result["stockCode"].to_list() == [path.stem for path in files]


def test_pyodide_index_path_uses_projected_arrow_columns(tmp_path: Path) -> None:
    from dartlab.core.dataLoaderIndex import buildDataIndex

    source = tmp_path / "BROWSER.parquet"
    pl.DataFrame(
        {
            "company_name": ["Browser Corp", "Browser Corp"],
            "year": ["2023", "2024"],
            "accession_no": ["one", "two"],
            "section_content": ["unused" * 10_000, "unused" * 10_000],
        }
    ).write_parquet(source)

    result = buildDataIndex([source], "edgarDocs", pyodide=True)

    assert result.to_dicts() == [
        {
            "stockCode": "BROWSER",
            "corpName": "Browser Corp",
            "rows": 2,
            "yearFrom": "2023",
            "yearTo": "2024",
            "nDocs": 2,
        }
    ]


def test_pyodide_index_never_wraps_arrow_oom(monkeypatch) -> None:
    """Arrow OOM은 손상 파일 오류로 위장하지 않고 MemoryError로 전파한다."""
    import pyarrow as pa

    from dartlab.core import dataLoaderIndex, dataLoaderPyodide

    @contextmanager
    def outOfMemory(_source):
        raise pa.ArrowMemoryError("wasm heap exhausted")
        yield

    monkeypatch.setattr(dataLoaderPyodide, "openParquetFile", outOfMemory)

    with pytest.raises(MemoryError, match="wasm heap exhausted"):
        dataLoaderIndex._readPyodideRecord(Path("sample.parquet"), "panel")
