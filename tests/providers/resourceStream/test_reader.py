"""resourceStream DuckDB Arrow paging, pin과 budget behavior mirror tests."""

from __future__ import annotations

import os
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from dartlab.providers.resourceStream import (
    BoundedBatchReader,
    ResourceCursorV2,
    ResourcePredicate,
    ResourceReadReceipt,
    ResourceReadRequest,
    loadResourceManifest,
    openResourceBatchReader,
)

pytestmark = pytest.mark.unit


def _writeShard(path: Path, companyId: str, values: tuple[int, ...]) -> None:
    table = pa.table(
        {
            "companyId": [companyId] * len(values),
            "fy": list(range(2023, 2023 + len(values))),
            "value": list(values),
            "payload": [f"{companyId}-{value}-" + "x" * 2_000 for value in values],
            "contentRaw": [f"raw-{companyId}-{value}" for value in values],
        }
    )
    pq.write_table(table, path, row_group_size=2)


def _writeResourceRoot(root: Path) -> None:
    root.mkdir()
    _writeShard(root / "A.parquet", "A", (10, 20, 30))
    _writeShard(root / "B.parquet", "B", (40, 50, 60))


def _readTable(reader: BoundedBatchReader) -> tuple[pa.Table, ResourceReadReceipt]:
    with reader:
        batches = tuple(reader)
        receipt = reader.receipt()
    if batches:
        return pa.Table.from_batches(batches), receipt
    return pa.table({}), receipt


def test_openResourceBatchReader_pagesAllShardsWithoutDuplicates(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    firstRequest = ResourceReadRequest.fromMapping(
        {
            "columns": ["companyId", "fy", "value"],
            "batchRows": 2,
            "maxRows": 4,
            "maxBytes": 1_000_000,
        }
    )
    firstReader = openResourceBatchReader(manifest, firstRequest)
    firstTable, firstReceipt = _readTable(firstReader)
    secondRequest = ResourceReadRequest(
        columns=firstRequest.columns,
        batchRows=3,
        maxRows=4,
        maxBytes=1_000_000,
        startRow=firstReceipt.nextRow,
        expectedSourcePin=firstReceipt.sourcePin,
        expectedQueryPin=firstReceipt.queryPin,
        cursor=firstReceipt.nextCursor,
    )
    secondTable, secondReceipt = _readTable(openResourceBatchReader(manifest, secondRequest))

    assert firstTable["value"].to_pylist() == [10, 20, 30, 40]
    assert secondTable["value"].to_pylist() == [50, 60]
    assert firstTable["value"].to_pylist() + secondTable["value"].to_pylist() == [
        10,
        20,
        30,
        40,
        50,
        60,
    ]
    assert firstReceipt.truncated is True
    assert firstReceipt.nextCursor is not None
    assert secondReceipt.nextRow == 6
    assert secondReceipt.truncated is False
    sourcePaths = firstTable["sourcePath"].to_pylist() + secondTable["sourcePath"].to_pylist()
    assert sourcePaths == [
        "A.parquet",
        "A.parquet",
        "A.parquet",
        "B.parquet",
        "B.parquet",
        "B.parquet",
    ]
    assert all(not Path(sourcePath).is_absolute() for sourcePath in sourcePaths)


def test_openResourceBatchReader_reportsCompleteAtExactRowLimit(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    request = ResourceReadRequest(
        ("value",),
        batchRows=2,
        maxRows=6,
        maxBytes=1_000_000,
    )
    table, receipt = _readTable(openResourceBatchReader(manifest, request))
    assert table["value"].to_pylist() == [10, 20, 30, 40, 50, 60]
    assert receipt.nextRow == 6
    assert receipt.truncated is False


def test_openResourceBatchReader_pushesFilterAndCompanySelection(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    request = ResourceReadRequest(
        columns=("companyId", "fy", "value"),
        predicates=(ResourcePredicate("fy", "ge", 2025),),
        companyIds=("B",),
        maxRows=10,
    )
    table, _receipt = _readTable(openResourceBatchReader(manifest, request))
    assert table.to_pydict() == {
        "companyId": ["B"],
        "fy": [2025],
        "value": [60],
        "sourcePath": ["B.parquet"],
    }


def test_openResourceBatchReader_unionsMissingHistoricalColumns(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    root.mkdir()
    pq.write_table(pa.table({"companyId": ["A"], "value": [1], "legacy": ["kept"]}), root / "A.parquet")
    pq.write_table(pa.table({"companyId": ["B"], "value": [2]}), root / "B.parquet")
    manifest = loadResourceManifest("resource.test", root, useCache=False)

    commonTable, commonReceipt = _readTable(
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(("companyId", "value"), maxRows=10),
        )
    )
    assert commonTable.to_pydict() == {
        "companyId": ["A", "B"],
        "value": [1, 2],
        "sourcePath": ["A.parquet", "B.parquet"],
    }
    assert commonReceipt.truncated is False

    request = ResourceReadRequest(("companyId", "value", "legacy"), maxRows=10)
    table, receipt = _readTable(openResourceBatchReader(manifest, request))

    assert table.to_pydict() == {
        "companyId": ["A", "B"],
        "value": [1, 2],
        "legacy": ["kept", None],
        "sourcePath": ["A.parquet", "B.parquet"],
    }
    assert receipt.truncated is False

    selectedTable, selectedReceipt = _readTable(
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(
                ("companyId", "legacy"),
                companyIds=("B",),
                maxRows=10,
            ),
        )
    )
    assert selectedTable.to_pydict() == {
        "companyId": ["B"],
        "legacy": [None],
        "sourcePath": ["B.parquet"],
    }
    assert selectedReceipt.truncated is False


def test_openResourceBatchReader_matchesPromotedManifestType(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    root.mkdir()
    pq.write_table(
        pa.table({"metric": pa.array([1], type=pa.int32())}),
        root / "A.parquet",
    )
    pq.write_table(
        pa.table({"metric": pa.array([2], type=pa.int64())}),
        root / "B.parquet",
    )
    manifest = loadResourceManifest("resource.test", root, useCache=False)

    table, receipt = _readTable(
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(("metric",), maxRows=10),
        )
    )

    assert dict(manifest.schemaFields)["metric"] == "int64"
    assert table.schema.field("metric").type == pa.int64()
    assert table["metric"].to_pylist() == [1, 2]
    assert receipt.truncated is False


def test_openResourceBatchReader_pinsSourceAndQueryOnResume(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    query = ResourceReadRequest(("value",))
    queryPin = query.queryPin(manifest.resourceId)
    with pytest.raises(ValueError, match="sourcePin"):
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(
                ("value",),
                expectedSourcePin="resource-source-full:wrong",
            ),
        )
    with pytest.raises(ValueError, match="queryPin"):
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(
                ("value",),
                expectedQueryPin="resource-query:wrong",
            ),
        )
    footerManifest = loadResourceManifest(
        "resource.test",
        root,
        integrityMode="footerFast",
        useCache=False,
    )
    with pytest.raises(ValueError, match="integrityMode='full'"):
        openResourceBatchReader(
            footerManifest,
            ResourceReadRequest(
                ("value",),
                startRow=1,
                expectedSourcePin=footerManifest.sourcePin,
                expectedQueryPin=queryPin,
                cursor=ResourceCursorV2(0, 1),
            ),
        )


def test_openResourceBatchReader_detectsSourceDriftBeforeScan(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    path = root / "A.parquet"
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    with pytest.raises(ValueError, match="RESOURCE_SOURCE_DRIFT"):
        openResourceBatchReader(manifest, ResourceReadRequest(("value",)))


def test_openResourceBatchReader_enforcesRawContentOptIn(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    with pytest.raises(ValueError, match="allowRawContent"):
        openResourceBatchReader(manifest, ResourceReadRequest(("contentRaw",)))
    with pytest.raises(ValueError, match="2 MiB"):
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(("contentRaw",), allowRawContent=True),
        )
    with pytest.raises(ValueError, match="256"):
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(
                ("contentRaw",),
                maxBytes=2 * 1024 * 1024,
                allowRawContent=True,
            ),
        )
    request = ResourceReadRequest(
        ("contentRaw",),
        batchRows=256,
        maxRows=2,
        maxBytes=2 * 1024 * 1024,
        allowRawContent=True,
    )
    table, receipt = _readTable(openResourceBatchReader(manifest, request))
    assert table.num_rows == 2
    assert receipt.byteCount <= request.maxBytes


def test_openResourceBatchReader_enforcesRowAndLogicalByteBudgets(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    request = ResourceReadRequest(
        ("payload",),
        batchRows=6,
        maxRows=6,
        maxBytes=2_500,
        includeSourcePath=False,
    )
    table, receipt = _readTable(openResourceBatchReader(manifest, request))
    assert 0 < table.num_rows < 6
    assert receipt.rowCount == table.num_rows
    assert receipt.byteCount <= request.maxBytes
    assert receipt.truncated is True

    oversized = openResourceBatchReader(
        manifest,
        ResourceReadRequest(
            ("payload",),
            batchRows=1,
            maxRows=6,
            maxBytes=1,
            includeSourcePath=False,
        ),
    )
    with oversized, pytest.raises(ValueError, match="RESOURCE_ROW_EXCEEDS_MAX_BYTES"):
        tuple(oversized)


def test_openResourceBatchReader_rejectsUnknownColumnsAndCompanies(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    with pytest.raises(ValueError, match="resource column"):
        openResourceBatchReader(manifest, ResourceReadRequest(("unknown",)))
    with pytest.raises(ValueError, match="company ID"):
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(("value",), companyIds=("MISSING",)),
        )


def test_receipt_tracksPinnedBoundedUsage(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    request = ResourceReadRequest(("value",), maxRows=1)
    reader = openResourceBatchReader(manifest, request)
    table, receipt = _readTable(reader)
    assert receipt.sourcePin == manifest.sourcePin
    assert receipt.queryPin == request.queryPin(manifest.resourceId)
    assert receipt.rowCount == table.num_rows == 1
    assert receipt.nextRow == 1
    assert receipt.startCursor == ResourceCursorV2(0, 0)
    assert receipt.nextCursor == ResourceCursorV2(0, 1)
    assert receipt.scannedShardCount == 1
    assert receipt.toBytes()


def test_close_isIdempotent(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    reader = openResourceBatchReader(manifest, ResourceReadRequest(("value",)))
    reader.close()
    reader.close()
    assert tuple(reader) == ()


def test_schema_remainsAvailableAfterClose(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    reader = openResourceBatchReader(
        manifest,
        ResourceReadRequest(("value",), includeSourcePath=False),
    )
    expected = reader.schema
    reader.close()
    assert reader.schema == expected
    assert reader.schema.names == ["value"]


def test_shardCursorV2_advancesAcrossZeroMatchShardsWithoutMissingRows(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    root.mkdir()
    _writeShard(root / "A.parquet", "A", (1, 2))
    _writeShard(root / "B.parquet", "B", (10, 11))
    _writeShard(root / "C.parquet", "C", (20, 21))
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    predicate = ResourcePredicate("value", "ge", 10)
    cursor: ResourceCursorV2 | None = None
    logicalRow = 0
    sourcePin: str | None = None
    queryPin: str | None = None
    collected: list[int] = []
    observedCursors: list[ResourceCursorV2] = []

    while True:
        request = ResourceReadRequest(
            ("value",),
            predicates=(predicate,),
            maxRows=1,
            maxBytes=1_000_000,
            maxShards=1,
            startRow=logicalRow,
            cursor=cursor,
            expectedSourcePin=sourcePin,
            expectedQueryPin=queryPin,
        )
        table, receipt = _readTable(openResourceBatchReader(manifest, request))
        if table.num_rows:
            collected.extend(table["value"].to_pylist())
        logicalRow = receipt.nextRow
        sourcePin = receipt.sourcePin
        queryPin = receipt.queryPin
        assert receipt.scannedShardCount == 1
        if receipt.nextCursor is None:
            break
        observedCursors.append(receipt.nextCursor)
        cursor = receipt.nextCursor

    assert collected == [10, 11, 20, 21]
    assert observedCursors == sorted(observedCursors)
    assert len(set(observedCursors)) == len(observedCursors)
    assert observedCursors[0] == ResourceCursorV2(1, 0)
    assert logicalRow == 4


def test_shardCursorV2_deepResumeOpensOnlyCurrentShard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dartlab.providers.resourceStream.reader as readerModule

    root = tmp_path / "resource"
    root.mkdir()
    for index in range(10):
        companyId = chr(ord("A") + index)
        _writeShard(root / f"{companyId}.parquet", companyId, (index,))
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    base = ResourceReadRequest(("value",), maxRows=1, maxShards=1)
    opened: list[str] = []
    realMetadata = readerModule._pinnedShardMetadata

    def recordMetadata(path: Path, shard):
        opened.append(path.name)
        return realMetadata(path, shard)

    monkeypatch.setattr(readerModule, "_pinnedShardMetadata", recordMetadata)
    request = ResourceReadRequest(
        ("value",),
        maxRows=1,
        maxShards=1,
        startRow=8,
        cursor=ResourceCursorV2(8, 0),
        expectedSourcePin=manifest.sourcePin,
        expectedQueryPin=base.queryPin(manifest.resourceId),
    )
    table, receipt = _readTable(openResourceBatchReader(manifest, request))

    assert table["value"].to_pylist() == [8]
    assert opened == ["I.parquet"]
    assert receipt.nextCursor == ResourceCursorV2(9, 0)


def test_variableSchemaPagesFillMissingColumnsWithoutGlobalUnion(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    root.mkdir()
    pq.write_table(pa.table({"companyId": ["A"], "left": [1]}), root / "A.parquet")
    pq.write_table(pa.table({"companyId": ["B"], "right": [2]}), root / "B.parquet")
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    assert manifest.commonSchemaFields == (("companyId", "string"),)
    request = ResourceReadRequest(("companyId", "left", "right"), maxRows=10)
    table, receipt = _readTable(openResourceBatchReader(manifest, request))

    assert table.to_pydict() == {
        "companyId": ["A", "B"],
        "left": [1, None],
        "right": [None, 2],
        "sourcePath": ["A.parquet", "B.parquet"],
    }
    assert receipt.truncated is False
    assert receipt.scannedShardCount == 2


@pytest.mark.parametrize(
    "typeName",
    ["bool", "date32[day]", "double", "float", "int32", "int64", "large_string", "null", "uint32"],
)
def test_projectedSchema_supportsCurrentFlatResourceScalarTypes(typeName: str) -> None:
    import dartlab.providers.resourceStream.reader as readerModule

    assert str(readerModule._arrowType(typeName)) == typeName


def test_projectedSchema_rejectsUnsupportedNestedTypeExplicitly(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    root.mkdir()
    pq.write_table(pa.table({"nested": [[1, 2], [3]]}), root / "A.parquet")
    manifest = loadResourceManifest("resource.test", root, useCache=False)

    with pytest.raises(ValueError, match="RESOURCE_SCHEMA_INCOMPATIBLE"):
        openResourceBatchReader(manifest, ResourceReadRequest(("nested",)))


def test_pageReader_reusesOneDuckdbConnectionAcrossShardWindow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dartlab.providers.resourceStream.reader as readerModule

    root = tmp_path / "resource"
    root.mkdir()
    for companyId in ("A", "B", "C"):
        _writeShard(root / f"{companyId}.parquet", companyId, (1,))
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    realConnect = readerModule.duckdb.connect
    connectionCount = 0

    def countConnect(*args, **kwargs):
        nonlocal connectionCount
        connectionCount += 1
        return realConnect(*args, **kwargs)

    monkeypatch.setattr(readerModule.duckdb, "connect", countConnect)
    request = ResourceReadRequest(
        ("value",),
        predicates=(ResourcePredicate("value", "gt", 1_000),),
        maxShards=3,
    )
    table, receipt = _readTable(openResourceBatchReader(manifest, request))

    assert table.num_rows == 0
    assert receipt.scannedShardCount == 3
    assert connectionCount == 1
