"""resourceStream Data Workbench adapter의 security와 Arrow IPC mirror tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import dartlab.providers.resourceStream.workbench as workbenchModule
from dartlab.providers.resourceStream import ResourcePage, describeResource, readResourcePage

pytestmark = pytest.mark.unit

_CATEGORY = "unitResourceStream"
_RESOURCE_ID = f"resource.{_CATEGORY}"


@pytest.fixture
def flatResource(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path]:
    dataRoot = tmp_path / "data"
    resourceRoot = dataRoot / "provider" / "flat"
    resourceRoot.mkdir(parents=True)
    pq.write_table(
        pa.table(
            {
                "companyId": ["A", "A", "A"],
                "value": [10, 20, 30],
                "contentRaw": ["raw-A-10", "raw-A-20", "raw-A-30"],
            }
        ),
        resourceRoot / "A.parquet",
        row_group_size=2,
    )
    pq.write_table(
        pa.table(
            {
                "companyId": ["B", "B", "B"],
                "value": [40, 50, 60],
                "contentRaw": ["raw-B-40", "raw-B-50", "raw-B-60"],
            }
        ),
        resourceRoot / "B.parquet",
        row_group_size=2,
    )
    monkeypatch.setattr(workbenchModule.dartlabConfig, "dataDir", str(dataRoot))
    monkeypatch.setitem(
        workbenchModule.DATA_RELEASES,
        _CATEGORY,
        {"dir": "provider/flat", "public": True},
    )
    return dataRoot, resourceRoot, tmp_path / "manifest.json"


def _decodePage(page: ResourcePage) -> tuple[pa.Schema, pa.Table]:
    stream = pa.ipc.open_stream(page.encodedBytes)
    schema = stream.schema
    batches = tuple(stream)
    return schema, pa.Table.from_batches(batches, schema=schema)


def test_describeResource_returnsImmutablePathSafeContract(
    flatResource: tuple[Path, Path, Path],
) -> None:
    dataRoot, resourceRoot, cachePath = flatResource
    first = describeResource(_RESOURCE_ID, _CATEGORY, cachePath)
    second = describeResource(_RESOURCE_ID, _CATEGORY, cachePath)

    assert first.resourceId == _RESOURCE_ID
    assert first.category == _CATEGORY
    assert first.sourcePin.startswith("resource-source-full:")
    assert dict(first.schemaFields) == {
        "companyId": "string",
        "value": "int64",
        "contentRaw": "string",
    }
    assert first.commonSchemaFields == first.schemaFields
    assert first.shardCount == 2
    assert first.totalBytes == sum(path.stat().st_size for path in resourceRoot.glob("*.parquet"))
    assert first.cacheHit is False
    assert second.cacheHit is True
    assert str(dataRoot) not in repr(first)
    assert str(resourceRoot) not in repr(first)
    with pytest.raises(FrozenInstanceError):
        first.totalBytes = 0  # type: ignore[misc]


def test_describeResource_rejectsUnknownMismatchAccessEscapeNestedAndMissing(
    flatResource: tuple[Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataRoot, _resourceRoot, cachePath = flatResource
    with pytest.raises(ValueError, match="RESOURCE_CATEGORY_UNKNOWN"):
        describeResource("resource.unknown", "unknown", cachePath)
    with pytest.raises(ValueError, match="RESOURCE_CATEGORY_MISMATCH"):
        describeResource("resource.other", _CATEGORY, cachePath)

    monkeypatch.setitem(
        workbenchModule.DATA_RELEASES,
        "privateResource",
        {"dir": "provider/flat", "public": False},
    )
    with pytest.raises(ValueError, match="RESOURCE_ACCESS_DENIED"):
        describeResource("resource.privateResource", "privateResource", cachePath)

    monkeypatch.setitem(
        workbenchModule.DATA_RELEASES,
        "deprecatedResource",
        {"dir": "provider/flat", "public": True, "deprecated": True},
    )
    with pytest.raises(ValueError, match="RESOURCE_ACCESS_DENIED"):
        readResourcePage("resource.deprecatedResource", "deprecatedResource", {}, cachePath)

    monkeypatch.setitem(
        workbenchModule.DATA_RELEASES,
        "escapeResource",
        {"dir": "../outside", "public": True},
    )
    with pytest.raises(ValueError, match="RESOURCE_ROOT_ESCAPE"):
        describeResource("resource.escapeResource", "escapeResource", cachePath)

    monkeypatch.setitem(
        workbenchModule.DATA_RELEASES,
        "nestedResource",
        {"dir": "provider/flat", "public": True, "nested": True},
    )
    with pytest.raises(ValueError, match="RESOURCE_ROOT_NOT_FLAT"):
        describeResource("resource.nestedResource", "nestedResource", cachePath)

    monkeypatch.setitem(
        workbenchModule.DATA_RELEASES,
        "missingResource",
        {"dir": "provider/missing", "public": True},
    )
    with pytest.raises(ValueError, match="RESOURCE_ROOT_MISSING"):
        describeResource("resource.missingResource", "missingResource", cachePath)
    assert Path(workbenchModule.dartlabConfig.dataDir).resolve() == dataRoot.resolve()


def test_readResourcePage_returnsTwoPinnedPagesWithoutDuplicates(
    flatResource: tuple[Path, Path, Path],
) -> None:
    dataRoot, _resourceRoot, cachePath = flatResource
    first = readResourcePage(
        _RESOURCE_ID,
        _CATEGORY,
        {
            "columns": ["companyId", "value"],
            "batchRows": 2,
            "maxRows": 4,
            "maxBytes": 1_000_000,
        },
        cachePath,
    )
    firstSchema, firstTable = _decodePage(first)
    assert first.receipt.nextCursor is not None
    second = readResourcePage(
        _RESOURCE_ID,
        _CATEGORY,
        {
            "columns": ["companyId", "value"],
            "batchRows": 3,
            "maxRows": 4,
            "maxBytes": 1_000_000,
            "startRow": first.receipt.nextRow,
            "expectedSourcePin": first.receipt.sourcePin,
            "expectedQueryPin": first.receipt.queryPin,
            "cursor": first.receipt.nextCursor.toMapping(),
        },
        cachePath,
    )
    secondSchema, secondTable = _decodePage(second)

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
    assert first.receipt.integrityMode == "full"
    assert first.receipt.truncated is True
    assert second.receipt.truncated is False
    assert firstSchema == secondSchema
    assert first.actualSchemaFields == tuple((field.name, str(field.type)) for field in firstSchema)
    assert first.encodedByteCount == len(first.encodedBytes)
    assert "encodedBytes" not in repr(first)
    assert str(dataRoot) not in repr(first)
    assert str(dataRoot).encode() not in first.encodedBytes
    assert firstTable["sourcePath"].to_pylist() == [
        "A.parquet",
        "A.parquet",
        "A.parquet",
        "B.parquet",
    ]


def test_readResourcePage_returnsSchemaValidEmptyStream(
    flatResource: tuple[Path, Path, Path],
) -> None:
    _dataRoot, _resourceRoot, cachePath = flatResource
    empty = readResourcePage(
        _RESOURCE_ID,
        _CATEGORY,
        {
            "columns": ["value"],
            "predicates": [{"column": "value", "operator": "gt", "value": 1_000_000}],
            "maxRows": 6,
            "maxBytes": 1_000_000,
        },
        cachePath,
    )
    schema, table = _decodePage(empty)

    assert schema.names == ["value", "sourcePath"]
    assert tuple((field.name, str(field.type)) for field in schema) == empty.actualSchemaFields
    assert table.num_rows == 0
    assert len(tuple(pa.ipc.open_stream(empty.encodedBytes))) == 1
    assert empty.receipt.startRow == empty.receipt.nextRow == 0
    assert empty.receipt.rowCount == 0
    assert empty.receipt.truncated is False
    assert empty.encodedBytes


def test_readResourcePage_writesExplicitUncompressedSingleStream(
    flatResource: tuple[Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _dataRoot, _resourceRoot, cachePath = flatResource
    realNewStream = workbenchModule.pa.ipc.new_stream
    compressionValues: list[object] = []

    def recordingNewStream(*args: object, **kwargs: object):
        options = kwargs.get("options")
        compressionValues.append(getattr(options, "compression", "missing"))
        return realNewStream(*args, **kwargs)

    monkeypatch.setattr(workbenchModule.pa.ipc, "new_stream", recordingNewStream)
    page = readResourcePage(
        _RESOURCE_ID,
        _CATEGORY,
        {"columns": ["value"], "batchRows": 1, "maxRows": 2, "maxBytes": 1_000_000},
        cachePath,
    )
    stream = pa.ipc.open_stream(page.encodedBytes)
    batches = tuple(stream)

    assert compressionValues == [None]
    assert sum(batch.num_rows for batch in batches) == 2
    assert stream.schema.names == ["value", "sourcePath"]


def test_readResourcePage_revalidatesSourceAfterIteration(
    flatResource: tuple[Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _dataRoot, resourceRoot, cachePath = flatResource
    realValidate = workbenchModule.validateManifestSources

    def mutateThenValidate(manifest):
        target = resourceRoot / "A.parquet"
        target.write_bytes(target.read_bytes() + b"changed-after-read")
        return realValidate(manifest)

    monkeypatch.setattr(workbenchModule, "validateManifestSources", mutateThenValidate)

    with pytest.raises(ValueError, match="RESOURCE_SOURCE_DRIFT"):
        readResourcePage(
            _RESOURCE_ID,
            _CATEGORY,
            {"columns": ["value"], "maxRows": 2, "maxBytes": 1_000_000},
            cachePath,
        )


def test_readResourcePage_preservesMissingAndRawContentPolicies(
    flatResource: tuple[Path, Path, Path],
) -> None:
    _dataRoot, _resourceRoot, cachePath = flatResource
    with pytest.raises(TypeError, match="requestMapping"):
        readResourcePage(_RESOURCE_ID, _CATEGORY, cast(Any, []), cachePath)
    with pytest.raises(ValueError, match="resource column"):
        readResourcePage(
            _RESOURCE_ID,
            _CATEGORY,
            {"columns": ["missingColumn"]},
            cachePath,
        )
    with pytest.raises(ValueError, match="allowRawContent"):
        readResourcePage(
            _RESOURCE_ID,
            _CATEGORY,
            {"columns": ["contentRaw"]},
            cachePath,
        )
