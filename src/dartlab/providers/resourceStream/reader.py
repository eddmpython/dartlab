"""Pinned resource manifest를 bounded shard-local Arrow page로 읽는다."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from .contracts import (
    ResourceCursorV2,
    ResourceManifest,
    ResourcePredicate,
    ResourceReadReceipt,
    ResourceReadRequest,
    ResourceShard,
)
from .manifest import validateManifestSources

_RAW_CONTENT_MAX_BYTES = 2 * 1024 * 1024
_RAW_CONTENT_MAX_BATCH_ROWS = 256
_PHYSICAL_ROW_COLUMN = "__dartlab_physical_row_v2"


def _compileFilter(predicates: tuple[ResourcePredicate, ...]) -> duckdb.Expression | None:
    expression: duckdb.Expression | None = None
    for predicate in predicates:
        field = duckdb.ColumnExpression(predicate.column)
        if predicate.operator == "isin":
            values = cast(tuple[Any, ...], predicate.value)
            current = (
                field.isin(*(duckdb.ConstantExpression(item) for item in values))
                if values
                else duckdb.ConstantExpression(False)
            )
        else:
            constant = duckdb.ConstantExpression(cast(Any, predicate.value))
            if predicate.operator == "eq":
                current = field == constant
            elif predicate.operator == "ne":
                current = field != constant
            elif predicate.operator == "gt":
                current = field > constant
            elif predicate.operator == "ge":
                current = field >= constant
            elif predicate.operator == "lt":
                current = field < constant
            else:
                current = field <= constant
        expression = current if expression is None else expression & current
    return expression


def _validateRawContentPolicy(request: ResourceReadRequest) -> None:
    if "contentRaw" not in request.columns:
        return
    if not request.allowRawContent:
        raise ValueError("contentRaw projection에는 allowRawContent=True가 필요합니다")
    if request.maxBytes > _RAW_CONTENT_MAX_BYTES:
        raise ValueError("contentRaw projection maxBytes는 2 MiB 이하여야 합니다")
    if request.batchRows > _RAW_CONTENT_MAX_BATCH_ROWS:
        raise ValueError("contentRaw projection batchRows는 256 이하여야 합니다")


def _arrowType(typeName: str) -> pa.DataType:
    try:
        return pa.type_for_alias(typeName)
    except ValueError:
        raise ValueError(f"RESOURCE_SCHEMA_INCOMPATIBLE: 지원하지 않는 Arrow type: {typeName}") from None


def _projectedSchema(manifest: ResourceManifest, request: ResourceReadRequest) -> pa.Schema:
    manifestTypes = dict(manifest.schemaFields)
    fields = [pa.field(column, _arrowType(manifestTypes[column])) for column in request.columns]
    if request.includeSourcePath:
        if "sourcePath" in request.columns:
            raise ValueError("sourcePath는 includeSourcePath가 예약한 column입니다")
        fields.append(pa.field("sourcePath", pa.string()))
    return pa.schema(fields)


def _pinnedShardMetadata(path: Path, shard: ResourceShard) -> tuple[pa.Schema, int]:
    before = path.stat()
    if (before.st_size, before.st_mtime_ns) != (shard.byteSize, shard.mtimeNs):
        raise ValueError(f"RESOURCE_SOURCE_DRIFT: shard read 전 변경됨: {shard.relativePath}")
    parquet = pq.ParquetFile(path)
    schema = parquet.schema_arrow
    rowCount = parquet.metadata.num_rows
    after = path.stat()
    if (after.st_size, after.st_mtime_ns) != (shard.byteSize, shard.mtimeNs):
        raise ValueError(f"RESOURCE_SOURCE_DRIFT: shard metadata read 중 변경됨: {shard.relativePath}")
    return schema, rowCount


def _fitTableByteBudget(table: pa.Table, maxBytes: int) -> pa.Table:
    if table.nbytes <= maxBytes:
        return table
    low = 0
    high = table.num_rows
    while low < high:
        middle = (low + high + 1) // 2
        if table.slice(0, middle).nbytes <= maxBytes:
            low = middle
        else:
            high = middle - 1
    return table.slice(0, low)


def _normalizeShardTable(
    table: pa.Table,
    *,
    shard: ResourceShard,
    request: ResourceReadRequest,
    projectedSchema: pa.Schema,
) -> pa.Table:
    arrays: list[pa.Array | pa.ChunkedArray] = []
    for column in request.columns:
        targetType = projectedSchema.field(column).type
        if column not in table.column_names:
            arrays.append(pa.nulls(table.num_rows, type=targetType))
            continue
        array = table[column]
        if array.type != targetType:
            try:
                array = pc.cast(array, target_type=targetType, safe=True)
            except (pa.ArrowInvalid, pa.ArrowNotImplementedError, pa.ArrowTypeError):
                raise ValueError(
                    f"RESOURCE_SCHEMA_INCOMPATIBLE: {shard.relativePath}의 {column} type이 manifest와 다릅니다"
                ) from None
        arrays.append(array)
    if request.includeSourcePath:
        arrays.append(pa.array([shard.relativePath] * table.num_rows, type=pa.string()))
    return pa.Table.from_arrays(arrays, schema=projectedSchema)


def _readShardCandidates(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    *,
    shardSchema: pa.Schema,
    request: ResourceReadRequest,
    physicalRowInShard: int,
    limit: int,
) -> tuple[pa.Table, tuple[int, ...]]:
    availableColumns = set(shardSchema.names)
    predicateColumns = {predicate.column for predicate in request.predicates}
    if not predicateColumns.issubset(availableColumns):
        return pa.table({_PHYSICAL_ROW_COLUMN: pa.array([], type=pa.uint64())}), ()

    relation = connection.read_parquet(
        [str(path)],
        file_row_number=True,
        filename=False,
        union_by_name=False,
    )
    physical = duckdb.ColumnExpression("file_row_number")
    relation = relation.filter(physical >= duckdb.ConstantExpression(physicalRowInShard))
    filterExpression = _compileFilter(request.predicates)
    if filterExpression is not None:
        relation = relation.filter(filterExpression)
    expressions = [duckdb.ColumnExpression(column) for column in request.columns if column in availableColumns]
    expressions.append(physical.alias(_PHYSICAL_ROW_COLUMN))
    table = relation.select(*expressions).limit(limit).to_arrow_table()
    physicalRows = tuple(int(value) for value in table[_PHYSICAL_ROW_COLUMN].to_pylist())
    return table.drop([_PHYSICAL_ROW_COLUMN]), physicalRows


class BoundedBatchReader:
    """Pinned manifest를 shard-local v2 cursor로 bounded page 하나만 읽는다.

    Capabilities:
        전역 OFFSET 없이 selected shard 순서를 따라 physical row cursor로 재개한다. Predicate로
        반환행이 0이어도 maxShards 안에서 cursor를 전진시키며 page row와 byte 상한을 지킨다.

    Args:
        manifest: Full source pin과 sorted shard tuple.
        request: Projection, predicate, cursor와 page budget.
        selectedShards: Query가 선택한 stable shard tuple.
        projectedSchema: 모든 page에서 유지할 manifest-derived Arrow schema.
        validateAfterRead: page materialization 뒤 manifest 전수를 다시 검증할지 여부.

    Returns:
        Arrow RecordBatch iterator와 v2 cursor receipt.

    Raises:
        ValueError: cursor, schema, source identity 또는 page budget이 유효하지 않을 때.

    Example:
        ``with reader as batches: page = tuple(batches)``.

    Guide:
        끝까지 iteration한 뒤 receipt의 nextCursor를 다음 request cursor로 전달한다.

    When:
        Full-universe resource를 bounded page로 순차 소비할 때 사용한다.

    How:
        한 shard씩 physical row filter를 적용하고 page가 찰 때까지 다음 shard를 이어 붙인다.

    SeeAlso:
        openResourceBatchReader, ResourceCursorV2, ResourceReadReceipt.

    Requires:
        Source와 query pin이 resume cursor에 함께 전달돼야 한다.

    AIContext:
        startRow는 telemetry일 뿐 selector가 아니다. exact resume selector는 cursor다.

    LLM Specifications:
        AntiPatterns:
            - 전체 file list에 global OFFSET 적용
            - rowCount 0을 cursor no-progress로 간주
        Freshness:
            각 shard 전 metadata identity와 page 후 manifest validation에 고정된다.
    """

    def __init__(
        self,
        manifest: ResourceManifest,
        request: ResourceReadRequest,
        selectedShards: tuple[ResourceShard, ...],
        projectedSchema: pa.Schema,
        *,
        validateAfterRead: bool,
    ) -> None:
        self._manifest = manifest
        self._request = request
        self._selectedShards = selectedShards
        self._schema = projectedSchema
        self._validateAfterRead = validateAfterRead
        self._startCursor = request.cursor or ResourceCursorV2(0, 0)
        self._batches: tuple[pa.RecordBatch, ...] | None = None
        self._receipt: ResourceReadReceipt | None = None
        self._batchIndex = 0
        self._closed = False
        self._connection = duckdb.connect(
            config={
                "threads": "2",
                "memory_limit": "256MB",
                "preserve_insertion_order": "true",
            }
        )
        self._connectionClosed = False

    def __enter__(self) -> BoundedBatchReader:
        """Context manager에서 reader를 반환한다."""

        return self

    def __exit__(self, excType: object, excValue: object, traceback: object) -> None:
        """Context manager 종료 시 reader를 닫는다."""

        self.close()

    def __iter__(self) -> BoundedBatchReader:
        """현재 reader를 순차 RecordBatch iterator로 반환한다."""

        return self

    @property
    def schema(self) -> pa.Schema:
        """Reader가 닫힌 뒤에도 유효한 projected Arrow schema를 반환한다."""

        return self._schema

    def _materialize(self) -> None:
        if self._batches is not None:
            return
        request = self._request
        root = Path(self._manifest.rootPath)
        cursor = self._startCursor
        pageTables: list[pa.Table] = []
        rowCount = 0
        byteCount = 0
        scannedShardCount = 0

        while cursor.shardOrdinal < len(self._selectedShards):
            if scannedShardCount >= request.maxShards:
                break
            shard = self._selectedShards[cursor.shardOrdinal]
            path = root / shard.relativePath
            shardSchema, shardRowCount = _pinnedShardMetadata(path, shard)
            scannedShardCount += 1
            if _PHYSICAL_ROW_COLUMN in shardSchema.names:
                raise ValueError(f"RESOURCE_SCHEMA_RESERVED_COLUMN: {_PHYSICAL_ROW_COLUMN}")
            if cursor.physicalRowInShard > shardRowCount:
                raise ValueError("RESOURCE_CURSOR_OUT_OF_RANGE: physicalRowInShard가 shard row 수를 초과합니다")
            if cursor.physicalRowInShard == shardRowCount:
                cursor = ResourceCursorV2(cursor.shardOrdinal + 1, 0)
                continue

            remainingRows = request.maxRows - rowCount
            remainingBytes = request.maxBytes - byteCount
            if remainingRows <= 0 or remainingBytes <= 0:
                break
            rawTable, physicalRows = _readShardCandidates(
                self._connection,
                path,
                shardSchema=shardSchema,
                request=request,
                physicalRowInShard=cursor.physicalRowInShard,
                limit=remainingRows + 1,
            )
            if not physicalRows:
                cursor = ResourceCursorV2(cursor.shardOrdinal + 1, 0)
                continue
            normalized = _normalizeShardTable(
                rawTable,
                shard=shard,
                request=request,
                projectedSchema=self._schema,
            )
            candidate = normalized.slice(0, min(remainingRows, normalized.num_rows))
            fitted = _fitTableByteBudget(candidate, remainingBytes)
            if fitted.num_rows == 0:
                if rowCount == 0:
                    raise ValueError("RESOURCE_ROW_EXCEEDS_MAX_BYTES: 첫 행이 page maxBytes를 초과합니다")
                break
            pageTables.append(fitted)
            rowCount += fitted.num_rows
            byteCount += fitted.nbytes
            nextPhysicalRow = physicalRows[fitted.num_rows - 1] + 1
            if fitted.num_rows < len(physicalRows):
                cursor = ResourceCursorV2(cursor.shardOrdinal, nextPhysicalRow)
                break
            cursor = ResourceCursorV2(cursor.shardOrdinal + 1, 0)
            if rowCount >= request.maxRows or byteCount >= request.maxBytes:
                break

        if scannedShardCount == 0:
            raise ValueError("RESOURCE_CURSOR_OUT_OF_RANGE: selected shard 끝 이후 cursor입니다")
        complete = cursor.shardOrdinal >= len(self._selectedShards)
        nextCursor = None if complete else cursor
        if nextCursor is not None and nextCursor <= self._startCursor:
            raise ValueError("RESOURCE_CURSOR_NO_PROGRESS: shard cursor가 전진하지 않았습니다")
        if pageTables:
            pageTable = pa.concat_tables(pageTables).combine_chunks()
            if pageTable.nbytes > request.maxBytes:
                raise ValueError("RESOURCE_LOGICAL_BYTE_BUDGET: page가 maxBytes를 초과했습니다")
            batches = tuple(pageTable.to_batches(max_chunksize=request.batchRows))
        else:
            pageTable = pa.Table.from_batches([], schema=self._schema)
            batches = ()
        if self._validateAfterRead:
            validateManifestSources(self._manifest)
        self._closeConnection()
        self._batches = batches
        self._receipt = ResourceReadReceipt(
            sourcePin=self._manifest.sourcePin,
            queryPin=request.queryPin(self._manifest.resourceId),
            integrityMode=self._manifest.integrityMode,
            startRow=request.startRow,
            nextRow=request.startRow + pageTable.num_rows,
            batchCount=len(batches),
            rowCount=pageTable.num_rows,
            byteCount=pageTable.nbytes,
            truncated=nextCursor is not None,
            startCursor=self._startCursor,
            nextCursor=nextCursor,
            scannedShardCount=scannedShardCount,
        )

    def __next__(self) -> pa.RecordBatch:
        """다음 bounded RecordBatch를 반환한다."""

        if self._closed:
            raise StopIteration
        try:
            self._materialize()
        except Exception:
            self.close()
            raise
        assert self._batches is not None
        if self._batchIndex >= len(self._batches):
            self.close()
            raise StopIteration
        batch = self._batches[self._batchIndex]
        self._batchIndex += 1
        return batch

    def close(self) -> None:
        """Reader를 idempotent하게 닫는다."""

        self._closeConnection()
        self._closed = True

    def _closeConnection(self) -> None:
        if self._connectionClosed:
            return
        self._connection.close()
        self._connectionClosed = True

    def receipt(self) -> ResourceReadReceipt:
        """Materialized page의 pinned cursor receipt를 반환한다."""

        try:
            self._materialize()
        except Exception:
            self.close()
            raise
        assert self._receipt is not None
        return self._receipt


def openResourceBatchReader(
    manifest: ResourceManifest,
    request: ResourceReadRequest,
    *,
    sourcesPrevalidated: bool = False,
    validateAfterRead: bool = True,
) -> BoundedBatchReader:
    """Manifest 전체 또는 선택 shard를 bounded shard-local reader로 연다.

    Capabilities:
        Python company object loop 없이 provider parquet shard를 manifest 순서대로 읽는다. Global
        OFFSET 대신 ``ResourceCursorV2``를 사용하고 variable schema를 manifest type으로 정규화한다.

    Args:
        manifest: source identity와 sorted shard set이 고정된 manifest.
        request: projection, predicate, physical cursor와 budget 계약.
        sourcesPrevalidated: caller가 방금 manifest file set과 stat을 검증했는지 여부.
        validateAfterRead: iteration 뒤 manifest 전수 drift를 재검증할지 여부.

    Returns:
        Arrow RecordBatch를 순차 제공하는 BoundedBatchReader.

    Raises:
        ValueError: source drift, pin mismatch, cursor, column 또는 schema가 유효하지 않을 때.

    Example:
        ``reader = openResourceBatchReader(manifest, request)``.

    Guide:
        companyIds가 비면 전종목 shard를 대상으로 하며 receipt.nextCursor를 다음 요청에 전달한다.

    When:
        Manifest에 고정된 전체 또는 선택 company resource page를 실행할 때 호출한다.

    How:
        Request와 pin을 검증하고 context manager로 batch를 소비한 뒤 receipt를 저장한다.

    SeeAlso:
        ResourceReadRequest, ResourceCursorV2, loadResourceManifest.

    Requires:
        Resume cursor는 full manifest와 expected source/query pin을 모두 요구한다.

    AIContext:
        DART variable schema와 EDGAR common schema를 같은 physical cursor 계약으로 소비한다.

    LLM Specifications:
        AntiPatterns:
            - 전체 relation에 global OFFSET 적용
            - pin 없는 cursor continuation
        Freshness:
            caller prevalidation 또는 open 시 전수검사와 page 후 validation을 적용한다.
        Dataflow:
            manifest shard cursor -> single-shard DuckDB pushdown -> normalized Arrow page.
        TargetMarkets:
            - KR (DART)
            - US (EDGAR)
    """

    if not sourcesPrevalidated:
        validateManifestSources(manifest)
    queryPin = request.queryPin(manifest.resourceId)
    if request.expectedSourcePin is not None and request.expectedSourcePin != manifest.sourcePin:
        raise ValueError("resume sourcePin이 현재 manifest와 다릅니다")
    if request.expectedQueryPin is not None and request.expectedQueryPin != queryPin:
        raise ValueError("resume queryPin이 현재 query와 다릅니다")
    if request.cursor is not None and manifest.integrityMode != "full":
        raise ValueError("continuation은 integrityMode='full' manifest만 지원합니다")

    byCompany = {shard.companyId: shard for shard in manifest.shards}
    if request.companyIds:
        missingIds = tuple(companyId for companyId in request.companyIds if companyId not in byCompany)
        if missingIds:
            raise ValueError(f"manifest에 없는 company ID: {missingIds}")
        selectedShards = tuple(byCompany[companyId] for companyId in request.companyIds)
    else:
        selectedShards = manifest.shards
    if not selectedShards:
        raise ValueError("resource selected shard가 없습니다")
    availableColumns = {name for name, _fieldType in manifest.schemaFields}
    requestedColumns = set(request.columns)
    predicateColumns = {predicate.column for predicate in request.predicates}
    missingColumns = tuple(sorted((requestedColumns | predicateColumns) - availableColumns))
    if missingColumns:
        raise ValueError(f"resource column이 없습니다: {missingColumns}")
    _validateRawContentPolicy(request)
    projectedSchema = _projectedSchema(manifest, request)
    startCursor = request.cursor or ResourceCursorV2(0, 0)
    if startCursor.shardOrdinal >= len(selectedShards):
        raise ValueError("RESOURCE_CURSOR_OUT_OF_RANGE: shardOrdinal이 selected shard 수를 초과합니다")
    return BoundedBatchReader(
        manifest,
        request,
        selectedShards,
        projectedSchema,
        validateAfterRead=validateAfterRead,
    )
