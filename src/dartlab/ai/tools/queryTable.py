"""같은 세션에서 조회한 표를 읽기 전용 SQL로 계산하고 원자료 근거를 유지한다."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import partial
from typing import Any

import polars as pl

from dartlab.ai.contracts import Ref
from dartlab.core.memory import BoundedCache

from .types import ToolResult

_ACTIVE_TABLES: ContextVar[BoundedCache | None] = ContextVar("dartlabSessionTables", default=None)
_MAX_TABLE_BYTES = 4 * 1024 * 1024
_MAX_RESULT_BYTES = 32 * 1024
_SQL_FUNCTIONS = frozenset(
    "abs avg coalesce count ifnull iif lag lead length lower max min nullif pow power round "
    "row_number rank dense_rank sqrt sum total upper substr substring first_value last_value "
    "date datetime strftime julianday unixepoch typeof cast like glob trim ltrim rtrim replace instr".split()
)


@dataclass(frozen=True)
class QuerySource:
    """조회 표와 원자료 근거 및 조회 범위를 세션에 보존한다."""

    frame: pl.DataFrame
    sourceRefs: tuple[str, ...]
    coverage: str


@contextmanager
def tableScope(tables: BoundedCache):
    """호스트가 소유하는 세션의 표만 현재 도구 호출에서 접근하게 한다."""
    token = _ACTIVE_TABLES.set(tables)
    try:
        yield
    finally:
        _ACTIVE_TABLES.reset(token)


def captureTable(frame: pl.DataFrame, refs: list[Ref], *, coverage: str = "returned") -> dict[str, Any]:
    """직렬화 전 표를 bounded 세션 메모리에 보존한다. 큰 표는 저장하지 않는다."""
    tables = _ACTIVE_TABLES.get()
    if tables is None or not frame.width:
        return {}
    if frame.height > 100_000 or frame.width > 160 or frame.estimated_size() > _MAX_TABLE_BYTES:
        return {"available": False, "reason": "table_budget_exceeded", "rowCount": frame.height}
    if any(dtype.is_nested() or dtype == pl.Object for dtype in frame.dtypes):
        return {"available": False, "reason": "non_scalar_columns"}
    tableId = f"tableData:{uuid.uuid4().hex}"
    snapshotRef = f"dataset:{tableId}"
    sourceRefs = tuple(dict.fromkeys([snapshotRef, *(ref.id for ref in refs)]))
    tables[tableId] = QuerySource(frame.clone(), sourceRefs, coverage)
    return {
        "tableId": tableId,
        "rowCount": frame.height,
        "columns": {name: str(dtype) for name, dtype in frame.schema.items()},
        "coverage": coverage,
        "snapshotRef": snapshotRef,
        "contentHash": hashlib.sha256(frame.serialize()).hexdigest(),
        "sourceRefs": list(sourceRefs),
        "example": {"tables": {"t": tableId}, "sql": "SELECT * FROM t LIMIT 5"},
    }


def capturePartition(partition: Any, refs: list[Ref], *, status: str) -> dict[str, Any]:
    """DataHub의 records/native 표를 owner가 제공하는 표 변환으로 연결한다."""
    if _ACTIVE_TABLES.get() is None or partition.rowCount > 100_000 or len(partition.schema) > 160:
        return {}
    try:
        frame = partition.toPolars()
    except TypeError:
        return {}
    return captureTable(frame, refs, coverage=f"dataHub_{status}_partition")


def _loadSourceTables(database: sqlite3.Connection, sources: dict[str, QuerySource]) -> None:
    """확인된 세션 표만 제한된 메모리 DB로 복사한다."""
    database.execute("PRAGMA temp_store=MEMORY")
    database.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, _MAX_TABLE_BYTES)
    database.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 16_000)
    database.setlimit(sqlite3.SQLITE_LIMIT_COLUMN, 160)
    database.setlimit(sqlite3.SQLITE_LIMIT_ATTACHED, 0)
    for alias, source in sources.items():
        names = [str(name).replace('"', '""') for name in source.frame.columns]
        columns = ",".join(f'"{name}"' for name in names)
        database.execute(f'CREATE TABLE "{alias}" ({columns})')
        placeholders = ",".join("?" for _ in names)
        database.executemany(f'INSERT INTO "{alias}" VALUES ({placeholders})', source.frame.iter_rows())
    database.commit()
    database.execute("PRAGMA query_only=ON")


def _authorizeQuery(action: int, first: str | None, second: str | None, *unused: Any, sources: dict) -> int:
    """등록된 메모리 표 읽기와 허용 함수만 실행한다."""
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ and first in sources:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and str(second).lower() in _SQL_FUNCTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _querySources(active: BoundedCache, tables: dict[str, str]) -> dict[str, QuerySource] | ToolResult:
    """SQL 식별자를 검증하고 현재 세션에 남아 있는 원표만 선택한다."""
    sources: dict[str, QuerySource] = {}
    for alias, tableId in tables.items():
        if not isinstance(alias, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,31}", alias):
            return ToolResult(False, "표 alias는 영문자로 시작하는 짧은 식별자입니다.", error="invalid_alias")
        source = active.get(tableId) if isinstance(tableId, str) else None
        if source is None:
            return ToolResult(
                False, "표가 만료되었거나 현재 세션에 없습니다. 원자료를 다시 조회하세요.", error="table_not_found"
            )
        sources[alias] = source
    return sources


def queryTable(tables: dict[str, str], sql: str, *, limit: int = 100) -> ToolResult:
    """SQL SELECT로 조회 표의 필터·비율·순위·시계열·join을 계산한다.

    Args: tables는 SQL alias와 같은 세션의 tableId mapping, sql은 SELECT 한 문장이다.
    Returns: 계산 표, 실행 SQL, 원자료 ref, 이어 계산할 tableId.
    Guide: 단위·기간·연결/별도 기준은 원표를 따른다. NULL을 임의로 0으로 대체하지 않는다.
    Example: queryTable({"t": tableId}, 'SELECT * FROM t ORDER BY "매출" DESC LIMIT 5').
    """
    active = _ACTIVE_TABLES.get()
    if active is None:
        return ToolResult(False, "QueryTable은 조회한 표가 있는 native 세션에서 사용합니다.", error="no_table_session")
    if not isinstance(tables, dict) or not 1 <= len(tables) <= 4:
        return ToolResult(False, "tables는 alias: tableId 1~4개입니다.", error="invalid_tables")
    if type(limit) is not int or not 1 <= limit <= 500 or not isinstance(sql, str) or len(sql) > 16_000:
        return ToolResult(False, "limit은 1~500, SQL은 16000자 이하여야 합니다.", error="invalid_query")
    sources = _querySources(active, tables)
    if isinstance(sources, ToolResult):
        return sources
    database = sqlite3.connect(":memory:")
    try:
        _loadSourceTables(database, sources)
        deadline = time.monotonic() + 3.0
        database.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)

        database.set_authorizer(partial(_authorizeQuery, sources=sources))
        cursor = database.execute(sql)
        if cursor.description is None:
            raise ValueError("SELECT 결과가 필요합니다")
        columns = [column[0] for column in cursor.description]
        if len(set(columns)) != len(columns):
            raise ValueError("중복 열은 AS로 서로 다른 이름을 지정하세요")
        truncated = False
        rows = []
        used = 0
        for index in range(limit + 1):
            values = cursor.fetchone()
            if values is None:
                break
            if index == limit:
                truncated = True
                break
            row = dict(zip(columns, values, strict=True))
            size = len(json.dumps(row, ensure_ascii=False, default=str).encode("utf-8"))
            if used + size > _MAX_RESULT_BYTES:
                truncated = True
                break
            rows.append(row)
            used += size
    except (sqlite3.Error, ValueError, TypeError, OverflowError) as exc:
        return ToolResult(False, f"SQL 조회 실패: {exc}", error="invalid_table_query")
    finally:
        database.close()
    sourceRefs = list(dict.fromkeys(ref for source in sources.values() for ref in source.sourceRefs))
    refId = f"table:query:{uuid.uuid4().hex}"
    payload = {
        "columns": columns,
        "rows": rows,
        "sql": sql,
        "sourceRefs": sourceRefs,
        "inputTables": tables,
        "inputCoverage": {alias: source.coverage for alias, source in sources.items()},
        "returnedRowCount": len(rows),
        "previewTruncated": truncated,
    }
    ref = Ref(id=refId, kind="tableRef", title="표 계산 결과", source="QueryTable", payload=payload)
    receipt = Ref(
        id=refId.replace("table:", "execution:", 1),
        kind="executionRef",
        title="표 계산식과 원자료",
        source="QueryTable",
        payload={"sql": sql, "sourceRefs": sourceRefs, "inputTables": tables},
    )
    data: dict[str, Any] = {"tableRef": refId, "returnedRowCount": len(rows), "truncated": truncated}
    if rows and not truncated:
        data["table"] = captureTable(pl.DataFrame(rows, infer_schema_length=None), [ref, receipt])
    return ToolResult(
        True,
        f"표 계산 {len(rows)}행" + (" (결과 일부, limit을 SQL에 명시해 범위를 좁히세요)" if truncated else ""),
        refs=[ref, receipt],
        data=data,
    )
