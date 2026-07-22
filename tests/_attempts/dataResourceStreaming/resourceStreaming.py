"""Company-sharded parquet를 native Arrow Dataset으로 읽는 순수 attempt.

카테고리
--------
Data Workbench resource asset의 pageable owner executor 후보를 검증한다.

가설
----
Python 회사별 load 없이 전체 shard 목록을 native columnar reader 하나로 열고, column과
row predicate를 pushdown하면서 반환 메모리는 row와 byte 예산으로 제한할 수 있다.

결과
----
날짜: 2026-07-22.
표본: 로컬 DART와 EDGAR panel, finance 24,489 shard, 18.668 GiB.
핵심 수치: resource별 50,000행, 총 200,000행. fast scan 0.465~3.076초, RSS 증가 20.578~75.254 MiB.
결론: DuckDB RecordBatchReader 기본 경로와 Arrow Dataset parity 경로가 bounded paging을 입증했다.
다음 단계: resource.edgar를 첫 pageable owner executor로 승격한다.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

PredicateOperator = Literal["eq", "ne", "gt", "ge", "lt", "le", "isin"]
IntegrityMode = Literal["full", "footerFast"]


def _canonicalBytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _fullFileDigest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _footerDigest(path: Path) -> str:
    fileSize = path.stat().st_size
    if fileSize < 8:
        raise ValueError(f"Parquet 파일이 너무 작습니다: {path.name}")
    with path.open("rb") as stream:
        stream.seek(-8, 2)
        trailer = stream.read(8)
        if trailer[4:] != b"PAR1":
            raise ValueError(f"Parquet footer magic이 없습니다: {path.name}")
        footerSize = int.from_bytes(trailer[:4], "little")
        if footerSize <= 0 or footerSize + 8 > fileSize:
            raise ValueError(f"Parquet footer 길이가 유효하지 않습니다: {path.name}")
        stream.seek(-(footerSize + 8), 2)
        footer = stream.read(footerSize)
    return hashlib.sha256(footer + trailer).hexdigest()


@dataclass(frozen=True, slots=True)
class _ShardEntry:
    companyId: str
    relativePath: str
    byteSize: int
    integrityDigest: str


@dataclass(frozen=True, slots=True)
class ResourceManifest:
    """Company shard 집합과 source pin을 고정한다.

    Capabilities:
        full 모드는 전체 file bytes SHA-256, footerFast 모드는 Parquet footer hash로 source를 식별한다.

    Args:
        resourceId: catalog resource asset ID.
        rootPath: 실행 시 사용할 local root.
        entries: company ID 순서로 정렬된 shard identity.
        schemaFields: 첫 shard의 Arrow schema 이름과 타입.
        totalBytes: 전체 shard byte 합계.
        integrityMode: full 또는 benchmark 전용 footerFast.
        sourcePin: canonical manifest SHA-256.

    Returns:
        immutable resource manifest.

    Example:
        ``manifest.sourcePin``.

    Guide:
        continuation은 full mode sourcePin만 사용할 수 있다.

    SeeAlso:
        buildResourceManifest, openResourceBatchReader.

    Requires:
        flat company-sharded parquet directory.

    AIContext:
        DATA_RELEASES resource descriptor에 승격할 source revision 후보 계약이다.

    LLM Specifications:
        AntiPatterns:
            - 절대 local path를 source pin에 포함
            - footerFast pin을 payload integrity pin으로 설명
        Freshness:
            full은 manifest 생성 시점의 전체 payload bytes에 고정된다.
        OutputSchema:
            - sourcePin : str, 전체 shard revision SHA-256
            - entries : tuple, 정렬된 company shard identity
    """

    resourceId: str
    rootPath: str
    entries: tuple[_ShardEntry, ...]
    schemaFields: tuple[tuple[str, str], ...]
    totalBytes: int
    integrityMode: IntegrityMode
    sourcePin: str


@dataclass(frozen=True, slots=True)
class ResourcePredicate:
    """DuckDB relation과 Arrow Dataset scanner로 밀어 넣을 단순 predicate다.

    Capabilities:
        eq, ne, gt, ge, lt, le, isin 연산을 typed expression으로 제한한다.

    Args:
        column: parquet column 이름.
        operator: 지원 predicate 연산자.
        value: scalar 또는 isin tuple.

    Returns:
        immutable predicate.

    Example:
        ``ResourcePredicate("fy", "ge", 2024)``.

    Guide:
        Python row filter 대신 scanner filter로 사용한다.

    SeeAlso:
        ResourceReadRequest.

    Requires:
        isin은 tuple value를 요구한다.

    AIContext:
        임의 SQL 문자열 없이 외부 JSON mapping으로 표현 가능한 filter 후보다.

    LLM Specifications:
        AntiPatterns:
            - Python lambda row filter
            - 검증하지 않은 SQL fragment
        Freshness:
            source와 무관한 query value다.
    """

    column: str
    operator: PredicateOperator
    value: object

    def __post_init__(self) -> None:
        if not self.column.strip():
            raise ValueError("predicate column이 비었습니다")
        if self.operator not in {"eq", "ne", "gt", "ge", "lt", "le", "isin"}:
            raise ValueError("predicate operator가 유효하지 않습니다")
        if self.operator == "isin" and not isinstance(self.value, tuple):
            raise ValueError("isin value는 tuple이어야 합니다")


@dataclass(frozen=True, slots=True)
class ResourceReadRequest:
    """Projection, predicate, shard 선택과 반환 예산을 한 번에 고정한다.

    Capabilities:
        전체 manifest 또는 선택 company shard를 같은 bounded scanner 계약으로 읽는다.

    Args:
        columns: storage projection에 사용할 실제 parquet column.
        predicates: AND로 결합할 scanner predicate.
        companyIds: 비면 전체 manifest, 있으면 선택 shard만 사용한다.
        batchRows: native RecordBatch 최대 행 수.
        maxRows: 전체 reader 반환 행 예산.
        maxBytes: 전체 reader Arrow logical byte 예산.
        includeSourcePath: virtual filename column을 sourcePath로 반환할지 여부.
        useThreads: Arrow scanner thread 사용 여부. 기본은 결정성과 RSS를 위해 False다.
        startRow: filter와 projection 뒤 logical result에서 재개할 0-based row offset.
        expectedSourcePin: startRow 재개가 결박된 full manifest source pin.
        expectedQueryPin: startRow 재개가 결박된 query semantics pin.

    Returns:
        immutable read request.

    Example:
        ``ResourceReadRequest(("cik", "tag", "val"), maxRows=10000)``.

    Guide:
        raw text column은 명시적으로 요청하고 기본 projection에서는 제외한다.

    SeeAlso:
        openResourceBatchReader.

    Requires:
        모든 예산은 양수여야 한다.

    AIContext:
        DataQuery resource projection의 paging 하위 계약 후보다.

    LLM Specifications:
        AntiPatterns:
            - contentRaw를 전시장 기본 projection에 포함
            - maxRows 없이 RecordBatchReader 노출
            - source와 query pin 없이 startRow만 전달
        Freshness:
            ResourceManifest sourcePin과 함께 해석한다.
        OutputSchema:
            - columns : tuple[str], storage projection
            - maxRows : int, 전체 행 상한
            - maxBytes : int, 전체 byte 상한
    """

    columns: tuple[str, ...]
    predicates: tuple[ResourcePredicate, ...] = ()
    companyIds: tuple[str, ...] = ()
    batchRows: int = 4_096
    maxRows: int = 50_000
    maxBytes: int = 16 * 1024 * 1024
    includeSourcePath: bool = True
    useThreads: bool = False
    startRow: int = 0
    expectedSourcePin: str | None = None
    expectedQueryPin: str | None = None

    def __post_init__(self) -> None:
        columns = tuple(column.strip() for column in self.columns)
        if not columns or any(not column for column in columns):
            raise ValueError("columns가 비었습니다")
        if len(columns) != len(set(columns)):
            raise ValueError("columns는 고유해야 합니다")
        companyIds = tuple(sorted({companyId.strip() for companyId in self.companyIds if companyId.strip()}))
        for name in ("batchRows", "maxRows", "maxBytes"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name}는 양수여야 합니다")
        if self.startRow < 0:
            raise ValueError("startRow는 0 이상이어야 합니다")
        if self.startRow > 0 and (not self.expectedSourcePin or not self.expectedQueryPin):
            raise ValueError("resume startRow에는 expectedSourcePin과 expectedQueryPin이 필요합니다")
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "companyIds", companyIds)


@dataclass(frozen=True, slots=True)
class ResourceReadReceipt:
    """Bounded RecordBatch iteration 결과를 source pin에 결박한다.

    Capabilities:
        batch, row, byte 수와 예산 절단 여부를 machine-readable 형태로 보존한다.

    Args:
        sourcePin: manifest source revision.
        queryPin: projection, predicate, company selection semantics pin.
        integrityMode: manifest integrity mode.
        startRow: 이번 page의 logical 시작 row.
        nextRow: 다음 page가 사용할 logical 시작 row.
        batchCount: 반환 batch 수.
        rowCount: 반환 row 수.
        byteCount: 반환 Arrow logical byte 합계.
        truncated: row 또는 byte 예산으로 중단했는지 여부.

    Returns:
        immutable read receipt.

    Example:
        ``reader.receipt().truncated``.

    Guide:
        continuation 발급 시 sourcePin과 row offset을 함께 사용한다.

    SeeAlso:
        BoundedBatchReader.

    Requires:
        reader iteration 완료 또는 close 뒤 읽는다.

    AIContext:
        DataResult execution receipt와 coverage에 결박할 후보 facet이다.

    LLM Specifications:
        AntiPatterns:
            - truncated 결과를 complete로 표기
            - sourcePin 없이 continuation 재개
        Freshness:
            ResourceManifest와 동일하다.
    """

    sourcePin: str
    queryPin: str
    integrityMode: IntegrityMode
    startRow: int
    nextRow: int
    batchCount: int
    rowCount: int
    byteCount: int
    truncated: bool


class BoundedBatchReader:
    """Arrow RecordBatchReader에 전체 row와 byte 상한을 적용한다.

    Capabilities:
        native batch iteration을 유지하면서 마지막 batch를 slice해 hard result budget을 지킨다.

    Args:
        reader: native columnar backend가 만든 RecordBatchReader.
        sourcePin: manifest source revision.
        maxRows: 전체 반환 row 상한.
        maxBytes: 전체 반환 logical byte 상한.
        renameFilename: __filename을 sourcePath로 바꿀지 여부.
        sourceRoot: sourcePath를 manifest root 상대경로로 정규화할 root.
        skipRows: Arrow backend가 scanner batch에서 건너뛸 logical row 수.
        startRow: receipt에 기록할 logical 시작 row.
        queryPin: query semantics pin.
        integrityMode: manifest integrity mode.

    Returns:
        iterator와 context manager를 구현하는 bounded reader.

    Example:
        ``with reader as pages: batches = tuple(pages)``.

    Guide:
        사용 후 close하거나 context manager로 감싼다.

    SeeAlso:
        openResourceBatchReader, ResourceReadReceipt.

    Requires:
        단일 소비자만 순차 iteration한다.

    AIContext:
        Python 회사 loop가 아니라 native dataset reader의 외곽 budget gate다.

    LLM Specifications:
        AntiPatterns:
            - read_all 호출
            - batch별 maxRows를 적용해 전체 예산 초과
        Freshness:
            full sourcePin과 queryPin에 고정된다.
    """

    def __init__(
        self,
        reader: pa.RecordBatchReader,
        sourcePin: str,
        maxRows: int,
        maxBytes: int,
        renameFilename: bool,
        sourceRoot: str,
        skipRows: int,
        startRow: int,
        queryPin: str,
        integrityMode: IntegrityMode,
        cleanup: Callable[[], None] | None = None,
    ) -> None:
        self._reader = reader
        self._sourcePin = sourcePin
        self._maxRows = maxRows
        self._maxBytes = maxBytes
        self._renameFilename = renameFilename
        self._sourceRoot = sourceRoot.replace("\\", "/").rstrip("/") + "/"
        self._skipRows = skipRows
        self._startRow = startRow
        self._queryPin = queryPin
        self._integrityMode = integrityMode
        self._cleanup = cleanup
        self._rowCount = 0
        self._byteCount = 0
        self._batchCount = 0
        self._closed = False
        self._truncated = False

    def __enter__(self) -> BoundedBatchReader:
        return self

    def __exit__(self, excType, excValue, traceback) -> None:
        self.close()

    def __iter__(self) -> BoundedBatchReader:
        return self

    def __next__(self) -> pa.RecordBatch:
        if self._closed:
            raise StopIteration
        remainingRows = self._maxRows - self._rowCount
        remainingBytes = self._maxBytes - self._byteCount
        if remainingRows <= 0 or remainingBytes <= 0:
            self._truncated = True
            self.close()
            raise StopIteration
        while True:
            try:
                batch = self._reader.read_next_batch()
            except StopIteration:
                self.close()
                raise
            if self._skipRows >= batch.num_rows:
                self._skipRows -= batch.num_rows
                continue
            if self._skipRows:
                batch = batch.slice(self._skipRows)
                self._skipRows = 0
            break
        if self._renameFilename:
            names = tuple("sourcePath" if name == "__filename" else name for name in batch.schema.names)
            batch = pa.RecordBatch.from_arrays(batch.columns, names=names)
        if "sourcePath" in batch.schema.names:
            sourceIndex = batch.schema.get_field_index("sourcePath")
            sourceColumn = pc.replace_substring(
                batch.column(sourceIndex),
                pattern="\\",
                replacement="/",
            )
            if not pc.all(pc.starts_with(sourceColumn, pattern=self._sourceRoot)).as_py():
                raise ValueError("sourcePath가 manifest root 밖에 있습니다")
            relativeColumn = pc.replace_substring(sourceColumn, pattern=self._sourceRoot, replacement="")
            columns = list(batch.columns)
            columns[sourceIndex] = relativeColumn
            batch = pa.RecordBatch.from_arrays(columns, schema=batch.schema)
        originalRows = batch.num_rows
        rowLimit = min(originalRows, remainingRows)
        batch = batch.slice(0, rowLimit)
        if batch.nbytes > remainingBytes:
            low = 0
            high = batch.num_rows
            while low < high:
                middle = (low + high + 1) // 2
                if batch.slice(0, middle).nbytes <= remainingBytes:
                    low = middle
                else:
                    high = middle - 1
            if low == 0:
                self._truncated = True
                self.close()
                raise StopIteration
            batch = batch.slice(0, low)
            self._truncated = True
        if rowLimit < originalRows or self._rowCount + batch.num_rows >= self._maxRows:
            self._truncated = True
        self._rowCount += batch.num_rows
        self._byteCount += batch.nbytes
        self._batchCount += 1
        return batch

    def close(self) -> None:
        """Native reader를 닫는다."""
        if not self._closed:
            self._reader.close()
            if self._cleanup is not None:
                self._cleanup()
            self._closed = True

    def receipt(self) -> ResourceReadReceipt:
        """현재까지의 bounded read receipt를 반환한다."""
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


def buildResourceManifest(
    resourceId: str,
    rootPath: str | Path,
    integrityMode: IntegrityMode = "full",
) -> ResourceManifest:
    """Flat company parquet directory의 deterministic manifest를 만든다.

    Capabilities:
        모든 shard를 정렬한다. 기본 full 모드는 전체 file bytes를 SHA-256으로 읽어
        continuation-safe source pin을 만든다. footerFast는 benchmark용 metadata pin이다.

    Args:
        resourceId: catalog stable resource ID.
        rootPath: flat parquet directory.
        integrityMode: full 또는 footerFast. 기본은 full이다.

    Returns:
        ResourceManifest.

    Example:
        ``buildResourceManifest("resource.edgar", "data/edgar/finance", "full")``.

    Guide:
        refresh와 query를 분리하고 manifest를 query 시작 전에 한 번 고정한다.

    SeeAlso:
        openResourceBatchReader.

    Requires:
        파일명 stem이 market 내부 company ID이며 모든 파일이 parquet다.

    AIContext:
        manifest scan은 metadata 경로이고 owner data payload를 실행하지 않는다.

    LLM Specifications:
        AntiPatterns:
            - glob 순서를 그대로 plan hash에 사용
            - footerFast를 continuation에 사용
        Freshness:
            full은 실행 시점의 sorted full-file SHA-256 set이다.
        Dataflow:
            flat parquet shards -> integrity manifest -> sourcePin -> query scanner.
    """
    normalizedId = resourceId.strip()
    root = Path(rootPath).resolve()
    if not normalizedId:
        raise ValueError("resourceId가 비었습니다")
    if integrityMode not in {"full", "footerFast"}:
        raise ValueError("integrityMode가 유효하지 않습니다")
    if not root.is_dir():
        raise ValueError(f"resource root가 없습니다: {root}")
    paths = tuple(sorted(root.glob("*.parquet"), key=lambda path: path.name))
    if not paths:
        raise ValueError("resource parquet shard가 없습니다")
    digestFn = _fullFileDigest if integrityMode == "full" else _footerDigest
    maxWorkers = min(8, os.cpu_count() or 1)
    with ThreadPoolExecutor(max_workers=maxWorkers, thread_name_prefix="resource-integrity") as executor:
        integrityDigests = tuple(executor.map(digestFn, paths))
    entries = tuple(
        _ShardEntry(
            companyId=path.stem,
            relativePath=path.relative_to(root).as_posix(),
            byteSize=path.stat().st_size,
            integrityDigest=integrityDigest,
        )
        for path, integrityDigest in zip(paths, integrityDigests, strict=True)
    )
    companyIds = tuple(entry.companyId for entry in entries)
    if len(companyIds) != len(set(companyIds)):
        raise ValueError("company shard ID가 중복됐습니다")
    schema = pq.read_schema(paths[0])
    schemaFields = tuple((field.name, str(field.type)) for field in schema)
    pinPayload = {
        "format": "full-file-sha256-manifest-v1" if integrityMode == "full" else "parquet-footer-fast-manifest-v1",
        "resourceId": normalizedId,
        "integrityMode": integrityMode,
        "schemaFields": schemaFields,
        "entries": [(entry.companyId, entry.relativePath, entry.byteSize, entry.integrityDigest) for entry in entries],
    }
    pinKind = "full" if integrityMode == "full" else "footer-fast"
    sourcePin = f"resource-source-{pinKind}:{hashlib.sha256(_canonicalBytes(pinPayload)).hexdigest()}"
    return ResourceManifest(
        resourceId=normalizedId,
        rootPath=str(root),
        entries=entries,
        schemaFields=schemaFields,
        totalBytes=sum(entry.byteSize for entry in entries),
        integrityMode=integrityMode,
        sourcePin=sourcePin,
    )


def _queryPin(manifest: ResourceManifest, request: ResourceReadRequest) -> str:
    payload = {
        "resourceId": manifest.resourceId,
        "columns": request.columns,
        "predicates": [dataclasses.asdict(predicate) for predicate in request.predicates],
        "companyIds": request.companyIds,
        "includeSourcePath": request.includeSourcePath,
    }
    return f"resource-query:{hashlib.sha256(_canonicalBytes(payload)).hexdigest()}"


def _compileFilter(predicates: tuple[ResourcePredicate, ...]) -> ds.Expression | None:
    expression = None
    for predicate in predicates:
        field = ds.field(predicate.column)
        if predicate.operator == "eq":
            current = field == predicate.value
        elif predicate.operator == "ne":
            current = field != predicate.value
        elif predicate.operator == "gt":
            current = field > predicate.value
        elif predicate.operator == "ge":
            current = field >= predicate.value
        elif predicate.operator == "lt":
            current = field < predicate.value
        elif predicate.operator == "le":
            current = field <= predicate.value
        else:
            current = field.isin(predicate.value)
        expression = current if expression is None else expression & current
    return expression


def _compileDuckDbFilter(predicates: tuple[ResourcePredicate, ...]) -> duckdb.Expression | None:
    expression = None
    for predicate in predicates:
        field = duckdb.ColumnExpression(predicate.column)
        value = predicate.value
        constant = duckdb.ConstantExpression(value) if predicate.operator != "isin" else None
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
        elif predicate.operator == "le":
            current = field <= constant
        else:
            current = field.isin(*(duckdb.ConstantExpression(item) for item in value))
        expression = current if expression is None else expression & current
    return expression


def openResourceBatchReader(
    manifest: ResourceManifest,
    request: ResourceReadRequest,
    backend: Literal["duckdb", "arrowDataset"] = "duckdb",
) -> BoundedBatchReader:
    """Manifest 전체 또는 선택 shard를 native columnar reader로 연다.

    Capabilities:
        Python 회사별 load 없이 file list 하나를 DuckDB relation 또는 Arrow Dataset으로 만든다.
        projection과 predicate는 native reader에 전달하며 Arrow parity 경로는 readahead를 1로 제한한다.

    Args:
        manifest: source pin이 고정된 company shard manifest.
        request: columns, predicates, company IDs, batch와 전체 예산.
        backend: duckdb 또는 arrowDataset. 많은 작은 shard는 duckdb가 기본이다.

    Returns:
        BoundedBatchReader.

    Example:
        ``reader = openResourceBatchReader(manifest, request)``.

    Guide:
        companyIds가 비면 전시장 dataset이며 반환은 maxRows와 maxBytes에서 절단된다.

    SeeAlso:
        buildResourceManifest, ResourceReadRequest.

    Requires:
        manifest 생성 뒤 shard 삭제나 크기 변경이 없어야 한다.

    AIContext:
        Data Workbench resource executor의 pageable owner path 후보다.

    LLM Specifications:
        AntiPatterns:
            - for companyId 루프에서 pq.read_table 호출
            - scanner.read_all 또는 relation fetchall 호출
            - projection 뒤 Python filter
        Freshness:
            manifest sourcePin에 고정된다.
        Dataflow:
            manifest paths -> Arrow Dataset -> scanner pushdown -> RecordBatchReader -> budget gate.
        TargetMarkets:
            - KR (DART)
            - US (EDGAR)
    """
    root = Path(manifest.rootPath)
    queryPin = _queryPin(manifest, request)
    if request.expectedSourcePin is not None and request.expectedSourcePin != manifest.sourcePin:
        raise ValueError("resume sourcePin이 현재 full manifest와 다릅니다")
    if request.expectedQueryPin is not None and request.expectedQueryPin != queryPin:
        raise ValueError("resume queryPin이 현재 query와 다릅니다")
    if request.startRow > 0 and manifest.integrityMode != "full":
        raise ValueError("continuation은 integrityMode='full' manifest만 지원합니다")
    byCompany = {entry.companyId: entry for entry in manifest.entries}
    if request.companyIds:
        missingIds = tuple(companyId for companyId in request.companyIds if companyId not in byCompany)
        if missingIds:
            raise ValueError(f"manifest에 없는 company ID: {missingIds}")
        entries = tuple(byCompany[companyId] for companyId in request.companyIds)
    else:
        entries = manifest.entries
    paths = []
    for entry in entries:
        path = root / entry.relativePath
        if not path.is_file() or path.stat().st_size != entry.byteSize:
            raise ValueError(f"manifest source가 변경됐습니다: {entry.relativePath}")
        paths.append(str(path))
    if backend not in {"duckdb", "arrowDataset"}:
        raise ValueError("resource backend가 유효하지 않습니다")
    availableColumns = {name for name, _type in manifest.schemaFields}
    requestedColumns = set(request.columns)
    predicateColumns = {predicate.column for predicate in request.predicates}
    missingColumns = tuple(sorted((requestedColumns | predicateColumns) - availableColumns))
    if missingColumns:
        raise ValueError(f"resource column이 없습니다: {missingColumns}")
    if backend == "arrowDataset":
        dataset = ds.dataset(paths, format="parquet")
        scanColumns = list(request.columns)
        if request.includeSourcePath:
            scanColumns.append("__filename")
        scanner = dataset.scanner(
            columns=scanColumns,
            filter=_compileFilter(request.predicates),
            batch_size=request.batchRows,
            batch_readahead=1,
            fragment_readahead=1,
            use_threads=request.useThreads,
        )
        return BoundedBatchReader(
            scanner.to_reader(),
            manifest.sourcePin,
            request.maxRows,
            request.maxBytes,
            request.includeSourcePath,
            manifest.rootPath,
            request.startRow,
            request.startRow,
            queryPin,
            manifest.integrityMode,
        )

    connection = duckdb.connect(
        config={
            "threads": "2",
            "memory_limit": "256MB",
            "preserve_insertion_order": "true",
        }
    )
    try:
        relation = connection.read_parquet(paths, filename=True)
        filterExpression = _compileDuckDbFilter(request.predicates)
        if filterExpression is not None:
            relation = relation.filter(filterExpression)
        columns = [duckdb.ColumnExpression(column) for column in request.columns]
        if request.includeSourcePath:
            columns.append(duckdb.ColumnExpression("filename").alias("sourcePath"))
        relation = relation.select(*columns).limit(request.maxRows, offset=request.startRow)
        reader = relation.to_arrow_reader(batch_size=request.batchRows)
    except Exception:
        connection.close()
        raise
    return BoundedBatchReader(
        reader,
        manifest.sourcePin,
        request.maxRows,
        request.maxBytes,
        False,
        manifest.rootPath,
        0,
        request.startRow,
        queryPin,
        manifest.integrityMode,
        connection.close,
    )
