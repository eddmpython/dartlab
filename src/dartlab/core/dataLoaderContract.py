"""``core.dataLoader`` 요청·경로·query 계약 SSOT."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Sequence

import polars as pl

_BASE_REFRESH_POLICIES = frozenset({"auto", "force_check", "local_only"})
_EDGAR_DOCS_NATIVE_REFRESH_POLICIES = _BASE_REFRESH_POLICIES | {"force_rebuild"}
_YEAR_COLUMNS = ("year", "bsns_year")


class DataArtifactError(OSError):
    """Parquet artifact의 저장·검증·정리 실패."""

    def __init__(self, operation: str, target: str | Path, cause: BaseException):
        self.operation = operation
        self.target = str(target)
        super().__init__(f"parquet {operation} 실패: {self.target} ({type(cause).__name__}: {cause})")


class DataQueryError(ValueError):
    """요청한 filter·projection을 artifact schema에 적용할 수 없음."""


def validateRefreshPolicy(category: str, refresh: str, *, pyodide: bool) -> None:
    """Runtime·category별 공개 refresh 정책을 검증한다."""
    allowed = _EDGAR_DOCS_NATIVE_REFRESH_POLICIES if category == "edgarDocs" and not pyodide else _BASE_REFRESH_POLICIES
    if not isinstance(refresh, str) or refresh not in allowed:
        policies = ", ".join(sorted(allowed))
        runtime = "Pyodide" if pyodide else "native"
        raise ValueError(
            f"지원하지 않는 refresh 정책: {refresh!r} (category={category}, runtime={runtime}, allowed={policies})"
        )


def validateShardKey(stockCode: str) -> tuple[str, ...]:
    """중첩 shard는 허용하되 절대·drive·상위 경로를 거부한다."""
    if not isinstance(stockCode, str) or not stockCode or stockCode != stockCode.strip():
        raise ValueError(f"stockCode는 비어 있지 않은 정규 경로 key여야 합니다: {stockCode!r}")
    if "\x00" in stockCode:
        raise ValueError("stockCode에 NUL 문자를 사용할 수 없습니다")

    normalized = stockCode.replace("\\", "/")
    if PurePosixPath(normalized).is_absolute() or PureWindowsPath(stockCode).drive:
        raise ValueError(f"stockCode에 절대 경로 또는 drive를 사용할 수 없습니다: {stockCode!r}")

    segments = tuple(normalized.split("/"))
    if any(segment in {"", ".", ".."} or ":" in segment or segment != segment.strip() for segment in segments):
        raise ValueError(f"stockCode에 비정규 경로 segment를 사용할 수 없습니다: {stockCode!r}")
    return segments


def resolveShardPath(dataDir: Path, stockCode: str) -> Path:
    """Category root 안에서만 ``stockCode`` parquet 경로를 해소한다."""
    segments = validateShardKey(stockCode)
    base = dataDir.resolve(strict=False)
    candidate = base.joinpath(*segments[:-1], f"{segments[-1]}.parquet").resolve(strict=False)
    if not candidate.is_relative_to(base):
        raise ValueError(f"stockCode가 category 경로를 벗어납니다: {stockCode!r}")
    return candidate


def collectLazyQuery(
    frame: pl.LazyFrame,
    *,
    sinceYear: int | None,
    columns: Sequence[str] | None,
    predicate: pl.Expr | None,
) -> pl.DataFrame:
    """Schema를 한 번만 읽어 filter·projection을 적용하고 streaming collect한다."""
    schema = frame.collect_schema()
    yearFilter = _yearFilter(schema, sinceYear)
    if yearFilter is not None:
        frame = frame.filter(yearFilter)
    if predicate is not None:
        frame = frame.filter(predicate)
    projection = _availableProjection(schema.names(), columns)
    if projection is not None:
        frame = frame.select(projection)
    return frame.collect(engine="streaming")


def applyEagerQuery(
    frame: pl.DataFrame,
    *,
    sinceYear: int | None,
    columns: Sequence[str] | None,
    predicate: pl.Expr | None,
) -> pl.DataFrame:
    """Pyodide eager frame에 native와 같은 filter·projection 계약을 적용한다."""
    yearFilter = _yearFilter(frame.schema, sinceYear)
    if yearFilter is not None:
        frame = frame.filter(yearFilter)
    if predicate is not None:
        frame = frame.filter(predicate)
    projection = _availableProjection(frame.columns, columns)
    if projection is not None:
        frame = frame.select(projection)
    return frame


def projectedColumns(
    schemaNames: Sequence[str],
    *,
    category: str,
    sinceYear: int | None,
    asOf: str | None,
    columns: Sequence[str] | None,
    predicate: pl.Expr | None,
) -> list[str] | None:
    """PyArrow read 전에 최종 열과 filter 보조열의 최소 합집합을 만든다."""
    projection = _availableProjection(schemaNames, columns)
    if projection is None:
        return None

    schemaSet = set(schemaNames)
    needed = set(projection)
    if sinceYear is not None:
        yearColumn = _yearColumn(schemaSet)
        if yearColumn is None:
            raise DataQueryError(f"sinceYear={sinceYear}을 적용할 year/bsns_year 열이 없습니다")
        needed.add(yearColumn)
    if category == "edgarDocs" and asOf is not None and "filing_date" in schemaSet:
        needed.add("filing_date")
    if predicate is not None:
        try:
            predicateColumns = predicate.meta.root_names()
        except (AttributeError, pl.exceptions.PolarsError):
            return None
        if not predicateColumns:
            return None
        needed.update(predicateColumns)
    return [column for column in schemaNames if column in needed]


def _availableProjection(
    schemaNames: Sequence[str],
    columns: Sequence[str] | None,
) -> list[str] | None:
    if columns is None:
        return None
    if not columns:
        raise DataQueryError("columns에는 하나 이상의 요청 열이 필요합니다")
    schemaSet = set(schemaNames)
    available = [column for column in columns if column in schemaSet]
    if not available:
        raise DataQueryError(f"요청 열이 artifact schema에 없습니다: {list(columns)!r}")
    return available


def _yearFilter(schema: pl.Schema, sinceYear: int | None) -> pl.Expr | None:
    if sinceYear is None:
        return None
    column = _yearColumn(schema)
    if column is None:
        raise DataQueryError(f"sinceYear={sinceYear}을 적용할 year/bsns_year 열이 없습니다")
    expression = pl.col(column)
    if schema[column] == pl.String:
        expression = expression.cast(pl.Int32, strict=False)
    return expression >= sinceYear


def _yearColumn(schema: pl.Schema | set[str]) -> str | None:
    for column in _YEAR_COLUMNS:
        if column in schema:
            return column
    return None


__all__ = [
    "DataArtifactError",
    "DataQueryError",
    "applyEagerQuery",
    "collectLazyQuery",
    "projectedColumns",
    "resolveShardPath",
    "validateRefreshPolicy",
    "validateShardKey",
]
