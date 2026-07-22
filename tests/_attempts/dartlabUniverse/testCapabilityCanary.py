from __future__ import annotations

import hashlib
import io
from dataclasses import replace

import polars as pl

from .query.capabilityCanary import _sourceUniverseCount, _validateArrow, bindCapabilityDataArtifact
from .queryTestSupport import buildQueryRuntimeFixture


def testCapabilityDataBindingRequiresExactCatalogBytes(tmp_path):
    runtime = buildQueryRuntimeFixture()
    payload = b"pinned-engine-data"
    relativePath = "dart/scan/finance.parquet"
    localPath = tmp_path / relativePath
    localPath.parent.mkdir(parents=True)
    localPath.write_bytes(payload)
    original = runtime.catalog.resources[0]
    resource = replace(
        original,
        resourceKind="HF_FILE",
        locator=(("repo", "fixture/data"), ("revision", "abc"), ("path", relativePath), ("oid", "def")),
        contentDigest=hashlib.sha256(payload).hexdigest(),
        byteSize=len(payload),
    )
    catalog = replace(runtime.catalog, resources=(resource, *runtime.catalog.resources[1:]))

    binding = bindCapabilityDataArtifact(
        catalog,
        dataRoot=tmp_path,
        market="DART",
        relativePath=relativePath,
    )
    assert binding.contentDigest == hashlib.sha256(payload).hexdigest()
    expectedObject = next(item for item in runtime.catalog.objects if original.resourceVersionId in item.resourceRefs)
    assert binding.objectId == expectedObject.objectId

    localPath.write_bytes(b"mutated")
    try:
        bindCapabilityDataArtifact(catalog, dataRoot=tmp_path, market="DART", relativePath=relativePath)
    except ValueError as exc:
        assert "snapshot mismatch" in str(exc)
    else:
        raise AssertionError("mutated data artifact가 결박됨")


def testCapabilityArrowValidationRequiresRowsPeriodsAndNumbers():
    frame = pl.DataFrame(
        {
            "stockCode": ["005930", "000660"],
            "2025": [1.0, 2.0],
            "2024": [0.5, 1.5],
            "2023": [0.25, 1.0],
        }
    )
    buffer = io.BytesIO()
    frame.write_ipc(buffer, compression="zstd")
    valid, rows, periods, numericValues = _validateArrow(buffer.getvalue())
    assert valid
    assert rows == 2
    assert periods == 3
    assert numericValues == 6


def testCapabilitySourceUniverseUsesPinnedMarketInputs(tmp_path):
    dartPath = tmp_path / "dart" / "scan" / "finance.parquet"
    dartPath.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "stockCode": ["005930", "005930", "000660", "035420"],
            "account_id_std": ["sales", "sales", "sales", "total_assets"],
        }
    ).write_parquet(dartPath)
    financeRoot = tmp_path / "edgar" / "finance"
    financeRoot.mkdir(parents=True)
    for cik in ("0000000001", "0000000002", "0000000003"):
        (financeRoot / f"{cik}.parquet").write_bytes(b"pinned")
    pl.DataFrame({"cik": ["1", "0000000003", "0000000004"]}).write_parquet(tmp_path / "edgar" / "tickers.parquet")

    assert _sourceUniverseCount(tmp_path, "DART") == 2
    assert _sourceUniverseCount(tmp_path, "EDGAR") == 2
