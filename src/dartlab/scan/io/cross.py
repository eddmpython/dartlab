"""Cross-company parquet query engines.

두 엔진은 같은 :class:`CrossScanQuery`를 소비한다.

- Polars는 parquet predicate pushdown과 streaming collect를 사용한다.
- DuckDB는 parquet를 SQL에서 직접 읽고 명시적 memory limit 안에서 실행한다.

LazyFrame을 먼저 수집해 DuckDB에 등록하는 경로는 OOC가 아니므로 사용하지 않는다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

import polars as pl


@dataclass(frozen=True)
class CrossScanQuery:
    """docs index cross-company query의 불변 입력."""

    path: Path
    sectionTitle: str | None = None
    year: int | None = None
    stockCodes: tuple[str, ...] = ()
    onlyWithContent: bool = False
    limit: int | None = None

    def __post_init__(self) -> None:
        if self.limit is not None and self.limit <= 0:
            raise ValueError(f"limit은 양수 또는 None이어야 합니다: {self.limit!r}")
        if any(not code for code in self.stockCodes):
            raise ValueError("stockCodes는 빈 문자열을 포함할 수 없습니다")


@runtime_checkable
class CrossScanEngine(Protocol):
    """Cross-company parquet query 엔진 surface."""

    def execute(self, query: CrossScanQuery) -> pl.DataFrame:
        """query를 실행해 DataFrame을 반환한다."""
        ...


def _polarsPlan(query: CrossScanQuery) -> pl.LazyFrame:
    """CrossScanQuery를 predicate pushdown 가능한 Polars plan으로 바꾼다."""

    lf = pl.scan_parquet(str(query.path))
    if query.sectionTitle:
        lf = lf.filter(pl.col("sectionTitle").str.contains(query.sectionTitle, literal=True))
    if query.year is not None:
        lf = lf.filter(pl.col("year") == query.year)
    if query.stockCodes:
        lf = lf.filter(pl.col("stockCode").is_in(query.stockCodes))
    if query.onlyWithContent:
        lf = lf.filter(pl.col("contentLength") > 0)
    if query.limit is not None:
        lf = lf.limit(query.limit)
    return lf


class PolarsCrossScan:
    """Polars predicate pushdown과 streaming collect 엔진."""

    def execute(self, query: CrossScanQuery) -> pl.DataFrame:
        """parquet를 streaming collect한다."""

        return _polarsPlan(query).collect(engine="streaming")


class DuckDbCrossScan:
    """DuckDB가 parquet를 직접 읽는 bounded OOC 엔진."""

    def __init__(self, *, memoryLimitMb: int = 256, threads: int = 2) -> None:
        if memoryLimitMb <= 0:
            raise ValueError(f"memoryLimitMb는 양수여야 합니다: {memoryLimitMb!r}")
        if threads <= 0:
            raise ValueError(f"threads는 양수여야 합니다: {threads!r}")
        self._memoryLimitMb = memoryLimitMb
        self._threads = threads

    def execute(self, query: CrossScanQuery) -> pl.DataFrame:
        """parquet source를 DuckDB SQL에서 직접 filter하고 반환한다."""

        import duckdb

        clauses: list[str] = []
        params: list[object] = [str(query.path)]
        if query.sectionTitle:
            clauses.append('contains("sectionTitle", ?)')
            params.append(query.sectionTitle)
        if query.year is not None:
            clauses.append('"year" = ?')
            params.append(query.year)
        if query.stockCodes:
            clauses.append('"stockCode" IN (SELECT unnest(?))')
            params.append(list(query.stockCodes))
        if query.onlyWithContent:
            clauses.append('"contentLength" > 0')

        whereSql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        limitSql = f" LIMIT {query.limit}" if query.limit is not None else ""
        sql = f"SELECT * FROM read_parquet(?){whereSql}{limitSql}"

        connection = duckdb.connect(":memory:")
        try:
            connection.execute(f"PRAGMA threads={self._threads}")
            connection.execute(f"PRAGMA memory_limit='{self._memoryLimitMb}MB'")
            connection.execute("PRAGMA preserve_insertion_order=false")
            return connection.execute(sql, params).pl()
        finally:
            connection.close()


def pickCrossScanEngine(
    *,
    engine: Literal["polars", "duckdb"] | str | None = None,
) -> CrossScanEngine:
    """caller 인자, 환경변수, 기본값 순서로 엔진을 고른다."""

    name = (engine or os.environ.get("DARTLAB_CROSS_SCAN_ENGINE") or "polars").strip().lower()
    if name == "polars":
        return PolarsCrossScan()
    if name == "duckdb":
        return DuckDbCrossScan()
    raise ValueError(f"지원하지 않는 cross scan engine: {name!r}. polars 또는 duckdb만 사용하세요.")


__all__: list[str] = [
    "CrossScanEngine",
    "CrossScanQuery",
    "DuckDbCrossScan",
    "PolarsCrossScan",
    "pickCrossScanEngine",
]
