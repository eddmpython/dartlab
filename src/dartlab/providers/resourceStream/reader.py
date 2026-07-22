"""Pinned resource manifest를 bounded DuckDB Arrow batch로 읽는다."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.compute as pc

from .contracts import (
    IntegrityMode,
    ResourceManifest,
    ResourcePredicate,
    ResourceReadReceipt,
    ResourceReadRequest,
)
from .manifest import validateManifestSources

_RAW_CONTENT_MAX_BYTES = 2 * 1024 * 1024
_RAW_CONTENT_MAX_BATCH_ROWS = 256


def _compileFilter(predicates: tuple[ResourcePredicate, ...]) -> duckdb.Expression | None:
    expression: duckdb.Expression | None = None
    for predicate in predicates:
        field = duckdb.ColumnExpression(predicate.column)
        if predicate.operator == "isin":
            current = field.isin(*(duckdb.ConstantExpression(item) for item in predicate.value))
        else:
            constant = duckdb.ConstantExpression(predicate.value)
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


def _relativeSourcePath(batch: pa.RecordBatch, sourceRoot: str) -> pa.RecordBatch:
    if "sourcePath" not in batch.schema.names:
        return batch
    sourceIndex = batch.schema.get_field_index("sourcePath")
    sourceColumn = pc.replace_substring(
        batch.column(sourceIndex),
        pattern="\\",
        replacement="/",
    )
    normalizedRoot = sourceRoot.replace("\\", "/").rstrip("/") + "/"
    withinRoot = pc.starts_with(sourceColumn, pattern=normalizedRoot)
    if not pc.all(withinRoot).as_py():
        raise ValueError("sourcePath가 manifest root 밖에 있습니다")
    relativeColumn = pc.replace_substring(
        sourceColumn,
        pattern=normalizedRoot,
        replacement="",
    )
    columns = list(batch.columns)
    columns[sourceIndex] = relativeColumn
    return pa.RecordBatch.from_arrays(columns, schema=batch.schema)


def _fitByteBudget(batch: pa.RecordBatch, maxBytes: int) -> pa.RecordBatch:
    if batch.nbytes <= maxBytes:
        return batch
    low = 0
    high = batch.num_rows
    while low < high:
        middle = (low + high + 1) // 2
        if batch.slice(0, middle).nbytes <= maxBytes:
            low = middle
        else:
            high = middle - 1
    return batch.slice(0, low)


class BoundedBatchReader:
    """DuckDB Arrow reader에 page 전체 row와 logical byte 상한을 적용한다.

    Capabilities:
        RecordBatch iteration을 유지하고 마지막 batch를 slice해 hard page budget을 지킨다.

    Args:
        reader: DuckDB relation이 만든 Arrow RecordBatchReader.
        sourcePin: manifest source identity.
        queryPin: query semantics identity.
        integrityMode: manifest integrity mode.
        sourceRoot: sourcePath를 상대경로로 바꿀 manifest root.
        maxRows: page 전체 row 상한.
        maxBytes: page 전체 Arrow logical byte 상한.
        startRow: 이번 page의 pinned logical offset.
        cleanup: reader 종료 뒤 실행할 connection cleanup.

    Returns:
        iterator와 context manager를 구현하는 bounded reader.

    Example:
        ``with reader as batches: page = tuple(batches)``.

    Guide:
        끝까지 iteration한 뒤 receipt를 읽고, 조기 중단이면 반드시 close한다.

    SeeAlso:
        openResourceBatchReader, ResourceReadReceipt.

    Requires:
        단일 consumer가 순차 iteration한다.

    AIContext:
        lower data owner에는 batch iterator와 strict JSON receipt만 노출한다.

    LLM Specifications:
        AntiPatterns:
            - read_all 또는 fetchall
            - batch마다 maxRows를 다시 적용
        Freshness:
            sourcePin과 queryPin에 고정된다.
    """

    def __init__(
        self,
        reader: pa.RecordBatchReader,
        sourcePin: str,
        queryPin: str,
        integrityMode: IntegrityMode,
        sourceRoot: str,
        maxRows: int,
        maxBytes: int,
        startRow: int,
        cleanup: Callable[[], None] | None = None,
    ) -> None:
        self._reader = reader
        self._sourcePin = sourcePin
        self._queryPin = queryPin
        self._integrityMode = integrityMode
        self._sourceRoot = sourceRoot
        self._maxRows = maxRows
        self._maxBytes = maxBytes
        self._startRow = startRow
        self._cleanup = cleanup
        self._rowCount = 0
        self._byteCount = 0
        self._batchCount = 0
        self._closed = False
        self._truncated = False
        self._stopAfterBatch = False

    def __enter__(self) -> BoundedBatchReader:
        """Context manager에서 reader를 반환한다."""
        return self

    def __exit__(self, excType: object, excValue: object, traceback: object) -> None:
        """Context manager 종료 시 native reader와 connection을 닫는다."""
        self.close()

    def __iter__(self) -> BoundedBatchReader:
        """현재 reader를 순차 RecordBatch iterator로 반환한다."""
        return self

    def _hasMoreRows(self) -> bool:
        while True:
            overflow = self._reader.read_next_batch()
            if overflow.num_rows:
                return True

    def __next__(self) -> pa.RecordBatch:
        """다음 budget-bounded RecordBatch를 반환한다."""
        if self._closed:
            raise StopIteration
        if self._stopAfterBatch:
            self.close()
            raise StopIteration
        remainingRows = self._maxRows - self._rowCount
        remainingBytes = self._maxBytes - self._byteCount
        if remainingRows <= 0 or remainingBytes <= 0:
            try:
                self._truncated = self._truncated or self._hasMoreRows()
            except StopIteration:
                pass
            except Exception:
                self.close()
                raise
            self.close()
            raise StopIteration
        try:
            batch = self._reader.read_next_batch()
            batch = _relativeSourcePath(batch, self._sourceRoot)
        except StopIteration:
            self.close()
            raise
        except Exception:
            self.close()
            raise
        originalRows = batch.num_rows
        if originalRows > remainingRows:
            batch = batch.slice(0, remainingRows)
            self._truncated = True
            self._stopAfterBatch = True
        fitted = _fitByteBudget(batch, remainingBytes)
        if fitted.num_rows < batch.num_rows:
            self._truncated = True
            self._stopAfterBatch = True
        batch = fitted
        if batch.num_rows == 0:
            self._truncated = True
            self.close()
            if self._rowCount == 0:
                raise ValueError("RESOURCE_ROW_EXCEEDS_MAX_BYTES: 첫 행이 page maxBytes를 초과합니다")
            raise StopIteration
        self._rowCount += batch.num_rows
        self._byteCount += batch.nbytes
        self._batchCount += 1
        return batch

    def close(self) -> None:
        """Native Arrow reader와 DuckDB connection을 idempotent하게 닫는다.

        Capabilities:
            부분 iteration과 정상 완료 모두에서 native resource를 한 번만 해제한다.

        AIContext:
            외부 consumer 취소 시 connection 누수를 막는 명시적 cleanup 경계다.

        Guide:
            context manager를 선호하고 조기 중단 시 직접 호출한다.

        When:
            page 소비 완료, 취소 또는 iteration exception 뒤 호출한다.

        How:
            Arrow reader를 먼저 닫고 finally에서 DuckDB cleanup을 실행한다.

        Requires:
            같은 reader의 순차 consumer에서 호출한다.

        Raises:
            Exception: native reader 또는 connection cleanup이 실패할 때.

        Example:
            ``reader.close()``.

        SeeAlso:
            BoundedBatchReader.__exit__.
        """
        if self._closed:
            return
        self._closed = True
        try:
            self._reader.close()
        finally:
            if self._cleanup is not None:
                self._cleanup()

    def receipt(self) -> ResourceReadReceipt:
        """현재까지 반환한 batch의 pinned page receipt를 만든다.

        Requires:
            완전한 page 결과에는 reader iteration을 끝까지 진행해야 한다.

        Raises:
            None.

        Example:
            ``receipt = reader.receipt()``.
        """
        return ResourceReadReceipt(
            sourcePin=self._sourcePin,
            queryPin=self._queryPin,
            integrityMode=self._integrityMode,
            startRow=self._startRow,
            nextRow=self._startRow + self._rowCount,
            batchCount=self._batchCount,
            rowCount=self._rowCount,
            byteCount=self._byteCount,
            truncated=self._truncated,
        )


def openResourceBatchReader(
    manifest: ResourceManifest,
    request: ResourceReadRequest,
) -> BoundedBatchReader:
    """Manifest 전체 또는 선택 shard를 bounded DuckDB Arrow reader로 연다.

    Capabilities:
        Python company loop 없이 전체 file list를 한 relation으로 만들고 projection, predicate,
        offset과 page limit을 DuckDB에 전달한다.

    Args:
        manifest: source identity와 relative shard set이 고정된 manifest.
        request: projection, predicate, company selection, paging과 budget 계약.

    Returns:
        Arrow RecordBatch를 순차 제공하는 BoundedBatchReader.

    Raises:
        ValueError: source drift, pin mismatch, column 오류, raw policy 위반 또는 unsafe resume일 때.

    Example:
        ``reader = openResourceBatchReader(manifest, request)``.

    Guide:
        companyIds가 비면 전종목 shard를 대상으로 하며 receipt의 세 pin 값을 다음 요청에 전달한다.

    When:
        manifest에 고정된 전체 또는 선택 company resource page를 실행할 때 호출한다.

    How:
        request를 검증하고 context manager로 batch를 소비한 뒤 receipt를 저장한다.

    SeeAlso:
        ResourceReadRequest, loadResourceManifest.

    Requires:
        continuation startRow는 full manifest와 expected source/query pin을 모두 요구한다.

    AIContext:
        DART와 EDGAR provider resource를 외부 Data Workbench가 같은 Arrow paging 계약으로 소비한다.

    LLM Specifications:
        AntiPatterns:
            - 회사별 pq.read_table loop
            - pin 없는 offset continuation
            - contentRaw 무제한 projection
        Freshness:
            open 직전에 file set, size와 mtimeNs drift를 검증한다.
        Dataflow:
            manifest paths -> DuckDB pushdown -> Arrow RecordBatchReader -> page budget gate.
        TargetMarkets:
            - KR (DART)
            - US (EDGAR)
    """
    validateManifestSources(manifest)
    queryPin = request.queryPin(manifest.resourceId)
    if request.expectedSourcePin is not None and request.expectedSourcePin != manifest.sourcePin:
        raise ValueError("resume sourcePin이 현재 manifest와 다릅니다")
    if request.expectedQueryPin is not None and request.expectedQueryPin != queryPin:
        raise ValueError("resume queryPin이 현재 query와 다릅니다")
    if request.startRow > 0 and manifest.integrityMode != "full":
        raise ValueError("continuation은 integrityMode='full' manifest만 지원합니다")

    byCompany = {shard.companyId: shard for shard in manifest.shards}
    if request.companyIds:
        missingIds = tuple(companyId for companyId in request.companyIds if companyId not in byCompany)
        if missingIds:
            raise ValueError(f"manifest에 없는 company ID: {missingIds}")
        shards = tuple(byCompany[companyId] for companyId in request.companyIds)
    else:
        shards = manifest.shards
    root = Path(manifest.rootPath)
    selectedPaths = [str(root / shard.relativePath) for shard in shards]

    availableColumns = {name for name, _type in manifest.schemaFields}
    requestedColumns = set(request.columns)
    predicateColumns = {predicate.column for predicate in request.predicates}
    missingColumns = tuple(sorted((requestedColumns | predicateColumns) - availableColumns))
    if missingColumns:
        raise ValueError(f"resource column이 없습니다: {missingColumns}")
    _validateRawContentPolicy(request)
    commonColumns = {name for name, _type in manifest.commonSchemaFields}
    unionByName = not (requestedColumns | predicateColumns).issubset(commonColumns)
    needsGlobalSchemaAnchor = unionByName and len(shards) != len(manifest.shards)
    paths = [str(root / shard.relativePath) for shard in manifest.shards] if needsGlobalSchemaAnchor else selectedPaths

    connection = duckdb.connect(
        config={
            "threads": "2",
            "memory_limit": "256MB",
            "preserve_insertion_order": "true",
        }
    )
    try:
        relation = connection.read_parquet(
            paths,
            filename=True,
            union_by_name=unionByName,
        )
        if needsGlobalSchemaAnchor:
            relation = relation.filter(
                duckdb.ColumnExpression("filename").isin(*(duckdb.ConstantExpression(path) for path in selectedPaths))
            )
        filterExpression = _compileFilter(request.predicates)
        if filterExpression is not None:
            relation = relation.filter(filterExpression)
        columns = [duckdb.ColumnExpression(column) for column in request.columns]
        if request.includeSourcePath:
            columns.append(duckdb.ColumnExpression("filename").alias("sourcePath"))
        relation = relation.select(*columns).limit(
            request.maxRows + 1,
            offset=request.startRow,
        )
        reader = relation.to_arrow_reader(batch_size=request.batchRows)
    except Exception:
        connection.close()
        raise
    return BoundedBatchReader(
        reader=reader,
        sourcePin=manifest.sourcePin,
        queryPin=queryPin,
        integrityMode=manifest.integrityMode,
        sourceRoot=manifest.rootPath,
        maxRows=request.maxRows,
        maxBytes=request.maxBytes,
        startRow=request.startRow,
        cleanup=connection.close,
    )
