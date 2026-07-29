"""로컬 parquet 종목 인덱스용 projection 집계.

원본 본문 컬럼은 읽지 않고 회사명·기간·문서 식별자만 집계한다. 한 파일이 손상되면
부분 인덱스를 반환하지 않고 파일과 카테고리를 보존한 오류로 즉시 실패한다.
"""

from __future__ import annotations

import os
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Callable

import polars as pl

INDEX_SCHEMA = {
    "stockCode": pl.String,
    "corpName": pl.String,
    "rows": pl.Int64,
    "yearFrom": pl.String,
    "yearTo": pl.String,
    "nDocs": pl.Int64,
}

_COMPANY_NAME_COLUMNS = ("corp_name", "company_name")
_YEAR_COLUMNS = ("year", "period", "bsns_year")
_DOC_ID_COLUMNS = ("rcept_no", "rceptNo", "accession_no")
_MAX_INDEX_WORKERS = 4


class DataIndexError(RuntimeError):
    """단일 parquet의 인덱스 메타 집계 실패."""

    def __init__(self, category: str, path: Path, cause: BaseException):
        self.category = category
        self.path = path
        super().__init__(f"{category} parquet 인덱스 생성 실패: {path} ({type(cause).__name__}: {cause})")


def emptyDataIndex() -> pl.DataFrame:
    """고정 공개 스키마의 빈 종목 인덱스."""
    return pl.DataFrame(schema=INDEX_SCHEMA)


def buildDataIndex(
    files: list[Path],
    category: str,
    *,
    pyodide: bool = False,
    onProgress: Callable[[], None] | None = None,
) -> pl.DataFrame:
    """정렬된 회사별 parquet 목록을 bounded 병렬 projection으로 집계한다."""
    if not files:
        return emptyDataIndex()

    readRecord = _readPyodideRecord if pyodide else _readLazyRecord
    workerCount = 1 if pyodide else min(_MAX_INDEX_WORKERS, os.cpu_count() or 1, len(files))
    records: list[dict] = []

    if workerCount == 1:
        for path in files:
            records.append(readRecord(path, category))
            if onProgress is not None:
                onProgress()
    else:
        with ThreadPoolExecutor(
            max_workers=workerCount,
            thread_name_prefix="dartlab-index",
        ) as executor:
            _collectBounded(
                executor,
                readRecord,
                files,
                category,
                records,
                onProgress,
                workerCount,
            )

    return pl.from_dicts(records, schema=INDEX_SCHEMA)


def _readLazyRecord(path: Path, category: str) -> dict:
    """네이티브 Polars lazy scan으로 필요한 컬럼만 읽는다."""
    try:
        scan = pl.scan_parquet(path)
        columns = set(scan.collect_schema().names())
        stats = scan.select(_indexExpressions(columns)).collect(engine="streaming")
    except (OSError, pl.exceptions.PolarsError) as exc:
        raise DataIndexError(category, path, exc) from exc
    return _record(path, stats.row(0, named=True))


def _readPyodideRecord(path: Path, category: str) -> dict:
    """Pyodide에서 pyarrow projection과 parquet row metadata로 같은 통계를 만든다."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    from dartlab.core.dataLoaderPyodide import arrowToPolars

    try:
        with path.open("rb") as source:
            parquet = pq.ParquetFile(source)
            columns = set(parquet.schema_arrow.names)
            rows = parquet.metadata.num_rows
            projected = sorted(columns.intersection((*_COMPANY_NAME_COLUMNS, *_YEAR_COLUMNS, *_DOC_ID_COLUMNS)))
            if projected:
                frame = arrowToPolars(parquet.read(columns=projected))
                stats = frame.lazy().select(_indexExpressions(columns)).collect()
            else:
                stats = pl.DataFrame(
                    {
                        "rows": [rows],
                        "corpName": [None],
                        "yearFrom": [None],
                        "yearTo": [None],
                        "nDocs": [0],
                    },
                    schema={
                        "rows": pl.Int64,
                        "corpName": pl.String,
                        "yearFrom": pl.String,
                        "yearTo": pl.String,
                        "nDocs": pl.Int64,
                    },
                )
    except (OSError, pa.ArrowException, pl.exceptions.PolarsError) as exc:
        raise DataIndexError(category, path, exc) from exc
    return _record(path, stats.row(0, named=True), rows=rows)


def _collectBounded(
    executor: ThreadPoolExecutor,
    readRecord: Callable[[Path, str], dict],
    files: list[Path],
    category: str,
    records: list[dict],
    onProgress: Callable[[], None] | None,
    workerCount: int,
) -> None:
    """최대 workerCount Future만 유지하며 오류를 즉시 전파하고 입력 순서를 보존한다."""
    pending: dict[Future[dict], int] = {}
    completed: dict[int, dict] = {}
    nextSubmit = 0
    nextEmit = 0

    def submitOne(index: int) -> None:
        """입력 위치 하나를 실행 큐에 넣고 Future와 순서를 함께 기록한다."""
        pending[executor.submit(readRecord, files[index], category)] = index

    while nextSubmit < min(workerCount, len(files)):
        submitOne(nextSubmit)
        nextSubmit += 1

    try:
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                index = pending.pop(future)
                completed[index] = future.result()
                if nextSubmit < len(files):
                    submitOne(nextSubmit)
                    nextSubmit += 1

            while nextEmit in completed:
                records.append(completed.pop(nextEmit))
                nextEmit += 1
                if onProgress is not None:
                    onProgress()
    except BaseException:
        for future in pending:
            future.cancel()
        raise


def _indexExpressions(columns: set[str]) -> list[pl.Expr]:
    expressions = [
        pl.len().cast(pl.Int64).alias("rows"),
        _firstText(_present(_COMPANY_NAME_COLUMNS, columns)).alias("corpName"),
    ]
    expressions.extend(_yearRange(_present(_YEAR_COLUMNS, columns)))
    expressions.append(_documentCount(_present(_DOC_ID_COLUMNS, columns)).alias("nDocs"))
    return expressions


def _present(candidates: tuple[str, ...], columns: set[str]) -> list[str]:
    return [column for column in candidates if column in columns]


def _firstText(columns: list[str]) -> pl.Expr:
    if not columns:
        return pl.lit(None, dtype=pl.String)
    values = pl.coalesce([_nonEmptyText(column) for column in columns])
    return values.drop_nulls().first()


def _yearRange(columns: list[str]) -> list[pl.Expr]:
    if not columns:
        return [
            pl.lit(None, dtype=pl.String).alias("yearFrom"),
            pl.lit(None, dtype=pl.String).alias("yearTo"),
        ]
    values = pl.coalesce([_canonicalYear(column) for column in columns]).drop_nulls()
    return [
        values.min().alias("yearFrom"),
        values.max().alias("yearTo"),
    ]


def _documentCount(columns: list[str]) -> pl.Expr:
    if not columns:
        return pl.lit(0, dtype=pl.Int64)
    values = pl.coalesce([_nonEmptyText(column) for column in columns])
    return values.drop_nulls().n_unique().cast(pl.Int64)


def _nonEmptyText(column: str) -> pl.Expr:
    text = pl.col(column).cast(pl.String, strict=False)
    return pl.when(text.is_not_null() & (text != "")).then(text).otherwise(None)


def _canonicalYear(column: str) -> pl.Expr:
    text = pl.col(column).cast(pl.String, strict=False)
    if column == "period":
        text = text.str.slice(0, 4)
    return pl.when(text.str.contains(r"^\d{4}$")).then(text).otherwise(None)


def _record(path: Path, stats: dict, *, rows: int | None = None) -> dict:
    return {
        "stockCode": path.stem,
        "corpName": stats["corpName"],
        "rows": stats["rows"] if rows is None else rows,
        "yearFrom": stats["yearFrom"],
        "yearTo": stats["yearTo"],
        "nDocs": stats["nDocs"],
    }


__all__ = [
    "DataIndexError",
    "INDEX_SCHEMA",
    "buildDataIndex",
    "emptyDataIndex",
]
