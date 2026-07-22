"""Pageable resource dataset attempt tests."""

from __future__ import annotations

import hashlib
import shutil

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from dataResourceStreaming import (
    ResourcePredicate,
    ResourceReadRequest,
    buildResourceManifest,
    openResourceBatchReader,
)


def _writeShard(path, companyId: str, values: tuple[tuple[int, float, str], ...]) -> None:
    table = pa.table(
        {
            "companyId": [companyId] * len(values),
            "year": [value[0] for value in values],
            "value": [value[1] for value in values],
            "payload": [value[2] for value in values],
        }
    )
    pq.write_table(table, path, row_group_size=2)


def _resourceRoot(tmpPath):
    root = tmpPath / "resource"
    root.mkdir(parents=True)
    _writeShard(root / "B.parquet", "B", ((2023, 3.0, "b3"), (2024, 4.0, "b4")))
    _writeShard(root / "A.parquet", "A", ((2022, 1.0, "a2"), (2024, 2.0, "a4")))
    return root


def testManifestIsSortedDeterministicAndAbsolutePathIndependent(tmp_path):
    firstRoot = _resourceRoot(tmp_path / "first")
    secondRoot = tmp_path / "second" / "resource"
    secondRoot.mkdir(parents=True)
    for path in firstRoot.glob("*.parquet"):
        shutil.copy2(path, secondRoot / path.name)

    first = buildResourceManifest("resource.demo", firstRoot)
    repeated = buildResourceManifest("resource.demo", firstRoot)
    copied = buildResourceManifest("resource.demo", secondRoot)

    assert tuple(entry.companyId for entry in first.entries) == ("A", "B")
    assert first.sourcePin == repeated.sourcePin == copied.sourcePin
    assert first.totalBytes == copied.totalBytes
    assert first.integrityMode == "full"
    assert first.sourcePin.startswith("resource-source-full:")
    aEntry = next(entry for entry in first.entries if entry.companyId == "A")
    assert aEntry.integrityDigest == hashlib.sha256((firstRoot / "A.parquet").read_bytes()).hexdigest()


@pytest.mark.parametrize("backend", ("duckdb", "arrowDataset"))
def testProjectionPredicateAndSourceIdentityRunInsideDatasetScanner(tmp_path, backend):
    manifest = buildResourceManifest("resource.demo", _resourceRoot(tmp_path))
    request = ResourceReadRequest(
        columns=("companyId", "year", "value"),
        predicates=(
            ResourcePredicate("year", "ge", 2024),
            ResourcePredicate("companyId", "isin", ("A", "B")),
        ),
        companyIds=("B", "A"),
        batchRows=1,
        maxRows=10,
        maxBytes=10_000,
    )

    with openResourceBatchReader(manifest, request, backend=backend) as reader:
        batches = tuple(reader)
        receipt = reader.receipt()

    table = pa.Table.from_batches(batches)
    assert table.schema.names == ["companyId", "year", "value", "sourcePath"]
    assert table.column("year").to_pylist() == [2024, 2024]
    assert set(table.column("companyId").to_pylist()) == {"A", "B"}
    assert "payload" not in table.schema.names
    assert set(table.column("sourcePath").to_pylist()) == {"A.parquet", "B.parquet"}
    assert receipt.rowCount == 2
    assert not receipt.truncated
    assert receipt.sourcePin == manifest.sourcePin


def testReaderAppliesGlobalRowBudgetAcrossBatches(tmp_path):
    manifest = buildResourceManifest("resource.demo", _resourceRoot(tmp_path))
    request = ResourceReadRequest(
        columns=("companyId", "year", "payload"),
        batchRows=2,
        maxRows=3,
        maxBytes=100_000,
    )

    with openResourceBatchReader(manifest, request) as reader:
        batches = tuple(reader)
        receipt = reader.receipt()

    assert sum(batch.num_rows for batch in batches) == 3
    assert receipt.rowCount == 3
    assert receipt.batchCount == 2
    assert receipt.truncated


def testReaderAppliesGlobalByteBudgetWithoutOvershoot(tmp_path):
    manifest = buildResourceManifest("resource.demo", _resourceRoot(tmp_path))
    request = ResourceReadRequest(
        columns=("payload",),
        batchRows=4,
        maxRows=100,
        maxBytes=12,
        includeSourcePath=False,
    )

    with openResourceBatchReader(manifest, request) as reader:
        batches = tuple(reader)
        receipt = reader.receipt()

    assert receipt.byteCount <= 12
    assert receipt.truncated
    assert receipt.rowCount == sum(batch.num_rows for batch in batches)


def testFooterChangeChangesSourcePin(tmp_path):
    root = _resourceRoot(tmp_path)
    before = buildResourceManifest("resource.demo", root)
    _writeShard(root / "A.parquet", "A", ((2022, 1.0, "changed"), (2024, 2.0, "a4")))

    after = buildResourceManifest("resource.demo", root)

    assert before.sourcePin != after.sourcePin


def testUnknownCompanyAndColumnFailBeforeScan(tmp_path):
    manifest = buildResourceManifest("resource.demo", _resourceRoot(tmp_path))

    with pytest.raises(ValueError, match="company ID"):
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(columns=("year",), companyIds=("UNKNOWN",)),
        )
    with pytest.raises(ValueError, match="column"):
        openResourceBatchReader(
            manifest,
            ResourceReadRequest(columns=("missingColumn",)),
        )


def testPinnedResumeHasNoDuplicateOrMissingRowsAcrossBackends(tmp_path):
    manifest = buildResourceManifest("resource.demo", _resourceRoot(tmp_path))
    backendRows = {}
    for backend in ("duckdb", "arrowDataset"):
        firstRequest = ResourceReadRequest(
            columns=("companyId", "year", "value"),
            batchRows=1,
            maxRows=2,
            maxBytes=10_000,
        )
        with openResourceBatchReader(manifest, firstRequest, backend=backend) as reader:
            firstBatches = tuple(reader)
            firstReceipt = reader.receipt()
        secondRequest = ResourceReadRequest(
            columns=("companyId", "year", "value"),
            batchRows=1,
            maxRows=2,
            maxBytes=10_000,
            startRow=firstReceipt.nextRow,
            expectedSourcePin=firstReceipt.sourcePin,
            expectedQueryPin=firstReceipt.queryPin,
        )
        with openResourceBatchReader(manifest, secondRequest, backend=backend) as reader:
            secondBatches = tuple(reader)
            secondReceipt = reader.receipt()
        combined = pa.Table.from_batches((*firstBatches, *secondBatches))
        rows = tuple(
            zip(
                combined.column("companyId").to_pylist(),
                combined.column("year").to_pylist(),
                combined.column("value").to_pylist(),
                strict=True,
            )
        )
        assert len(rows) == len(set(rows)) == 4
        assert firstReceipt.startRow == 0
        assert firstReceipt.nextRow == secondReceipt.startRow == 2
        assert secondReceipt.nextRow == 4
        assert firstReceipt.sourcePin == secondReceipt.sourcePin == manifest.sourcePin
        assert firstReceipt.queryPin == secondReceipt.queryPin
        backendRows[backend] = rows

    assert backendRows["duckdb"] == backendRows["arrowDataset"]


def testResumeRejectsFastIntegrityAndPinDrift(tmp_path):
    root = _resourceRoot(tmp_path)
    fullManifest = buildResourceManifest("resource.demo", root)
    firstRequest = ResourceReadRequest(columns=("companyId", "year"), maxRows=2)
    with openResourceBatchReader(fullManifest, firstRequest) as reader:
        tuple(reader)
        receipt = reader.receipt()

    with pytest.raises(ValueError, match="sourcePin"):
        openResourceBatchReader(
            fullManifest,
            ResourceReadRequest(
                columns=("companyId", "year"),
                startRow=2,
                expectedSourcePin="resource-source-full:stale",
                expectedQueryPin=receipt.queryPin,
            ),
        )
    with pytest.raises(ValueError, match="queryPin"):
        openResourceBatchReader(
            fullManifest,
            ResourceReadRequest(
                columns=("companyId", "value"),
                startRow=2,
                expectedSourcePin=receipt.sourcePin,
                expectedQueryPin=receipt.queryPin,
            ),
        )

    fastManifest = buildResourceManifest("resource.demo", root, integrityMode="footerFast")
    assert fastManifest.sourcePin.startswith("resource-source-footer-fast:")
    with openResourceBatchReader(fastManifest, firstRequest) as reader:
        tuple(reader)
        fastReceipt = reader.receipt()
    with pytest.raises(ValueError, match="integrityMode='full'"):
        openResourceBatchReader(
            fastManifest,
            ResourceReadRequest(
                columns=("companyId", "year"),
                startRow=2,
                expectedSourcePin=fastReceipt.sourcePin,
                expectedQueryPin=fastReceipt.queryPin,
            ),
        )
