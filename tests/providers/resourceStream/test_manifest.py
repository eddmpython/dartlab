"""resourceStream manifest의 full integrity와 persistent cache mirror tests."""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import dartlab.providers.resourceStream.manifest as manifestModule
from dartlab.providers.resourceStream.manifest import (
    loadPinnedResourceManifest,
    loadResourceManifest,
    readVerifiedManifestShard,
    validateManifestSources,
)

pytestmark = pytest.mark.unit


def _writeShard(path: Path, companyId: str, values: tuple[int, ...]) -> None:
    table = pa.table(
        {
            "companyId": [companyId] * len(values),
            "fy": list(range(2023, 2023 + len(values))),
            "value": list(values),
            "contentRaw": [f"raw-{companyId}-{value}" for value in values],
        }
    )
    pq.write_table(table, path, row_group_size=2)


def _writeResourceRoot(root: Path) -> None:
    root.mkdir()
    _writeShard(root / "A.parquet", "A", (10, 20, 30))
    _writeShard(root / "B.parquet", "B", (40, 50, 60))


def _loadManifestInProcess(arguments: tuple[str, str]) -> tuple[str, bool]:
    rootPath, cachePath = arguments
    manifest = loadResourceManifest(
        "resource.test",
        rootPath,
        cachePath=cachePath,
    )
    return manifest.sourcePin, manifest.cacheHit


def test_loadResourceManifest_usesFullFileSha256ByDefault(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest(
        "resource.test",
        root,
        cachePath=tmp_path / "manifest.json",
    )
    expected = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.glob("*.parquet"))}
    assert manifest.integrityMode == "full"
    assert manifest.sourcePin.startswith("resource-source-full:")
    assert {shard.relativePath: shard.integrityDigest for shard in manifest.shards} == expected


def test_loadResourceManifest_cacheHitDoesNotRehashEveryPage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "resource"
    cachePath = tmp_path / "manifest.json"
    _writeResourceRoot(root)
    first = loadResourceManifest("resource.test", root, cachePath=cachePath)

    def failDigest(_path: Path) -> str:
        raise AssertionError("fresh persistent cache hit에서 payload를 재해시했습니다")

    monkeypatch.setattr(manifestModule, "_fullFileDigest", failDigest)
    second = loadResourceManifest("resource.test", root, cachePath=cachePath)
    assert second.cacheHit is True
    assert second.sourcePin == first.sourcePin


def test_loadResourceManifest_rehashesOnlyChangedShard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "resource"
    cachePath = tmp_path / "manifest.json"
    _writeResourceRoot(root)
    first = loadResourceManifest("resource.test", root, cachePath=cachePath)
    changedPath = root / "A.parquet"
    oldStat = changedPath.stat()
    _writeShard(changedPath, "A", (11, 21, 31))
    os.utime(
        changedPath,
        ns=(oldStat.st_atime_ns, oldStat.st_mtime_ns + 1_000_000_000),
    )
    realDigest = manifestModule._fullFileDigest
    digested: list[str] = []

    def recordDigest(path: Path) -> str:
        digested.append(path.name)
        return realDigest(path)

    monkeypatch.setattr(manifestModule, "_fullFileDigest", recordDigest)
    second = loadResourceManifest("resource.test", root, cachePath=cachePath)
    assert digested == ["A.parquet"]
    assert second.cacheHit is False
    assert second.sourcePin != first.sourcePin


def test_loadResourceManifest_rejectsCorruptCacheDocument(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "resource"
    cachePath = tmp_path / "manifest.json"
    _writeResourceRoot(root)
    loadResourceManifest("resource.test", root, cachePath=cachePath)
    document = json.loads(cachePath.read_text(encoding="utf-8"))
    document["sourcePin"] = "resource-source-full:corrupt"
    cachePath.write_text(json.dumps(document), encoding="utf-8")
    realDigest = manifestModule._fullFileDigest
    digested: list[str] = []

    def recordDigest(path: Path) -> str:
        digested.append(path.name)
        return realDigest(path)

    monkeypatch.setattr(manifestModule, "_fullFileDigest", recordDigest)
    rebuilt = loadResourceManifest("resource.test", root, cachePath=cachePath)
    assert sorted(digested) == ["A.parquet", "B.parquet"]
    assert rebuilt.cacheHit is False
    assert rebuilt.sourcePin != "resource-source-full:corrupt"


def test_loadPinnedResourceManifest_rejectsCorruptCacheWithoutTreeScan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "resource"
    cachePath = tmp_path / "manifest.json"
    _writeResourceRoot(root)
    first = loadResourceManifest("resource.test", root, cachePath=cachePath)
    document = json.loads(cachePath.read_text(encoding="utf-8"))
    document["sourcePin"] = "resource-source-full:corrupt"
    cachePath.write_text(json.dumps(document), encoding="utf-8")

    def failTreeScan(_root: Path) -> tuple[Path, ...]:
        raise AssertionError("pinned cache failure가 source tree rebuild로 우회했습니다")

    monkeypatch.setattr(manifestModule, "_resourcePaths", failTreeScan)
    with pytest.raises(ValueError, match="RESOURCE_SOURCE_DRIFT"):
        loadPinnedResourceManifest(
            "resource.test",
            root,
            first.sourcePin,
            cachePath=cachePath,
        )


def test_loadResourceManifest_cacheValidationHonestlyStopsAtSizeAndMtime(
    tmp_path: Path,
) -> None:
    root = tmp_path / "resource"
    cachePath = tmp_path / "manifest.json"
    _writeResourceRoot(root)
    first = loadResourceManifest("resource.test", root, cachePath=cachePath)
    changedPath = root / "A.parquet"
    oldStat = changedPath.stat()
    payload = bytearray(changedPath.read_bytes())
    payload[16] ^= 1
    changedPath.write_bytes(payload)
    os.utime(changedPath, ns=(oldStat.st_atime_ns, oldStat.st_mtime_ns))

    cached = loadResourceManifest("resource.test", root, cachePath=cachePath)
    rebuilt = loadResourceManifest("resource.test", root, useCache=False)
    assert cached.cacheHit is True
    assert cached.sourcePin == first.sourcePin
    assert cached.cacheValidation == "fileSet+size+mtimeNs+cacheDocumentSha256"
    assert rebuilt.sourcePin != first.sourcePin


def test_loadResourceManifest_cacheIsProcessSafe(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    cachePath = tmp_path / "manifest.json"
    _writeResourceRoot(root)
    arguments = (str(root), str(cachePath))
    with ProcessPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(_loadManifestInProcess, (arguments, arguments)))
    assert results[0][0] == results[1][0]
    assert sorted(result[1] for result in results) == [False, True]
    assert json.loads(cachePath.read_text(encoding="utf-8"))["cacheDocumentSha256"]


def test_loadResourceManifest_footerFastIsExplicitBenchmarkIdentity(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest(
        "resource.test",
        root,
        integrityMode="footerFast",
        cachePath=tmp_path / "footer.json",
    )
    assert manifest.integrityMode == "footerFast"
    assert manifest.sourcePin.startswith("resource-source-footer-fast:")


def test_readVerifiedManifestShard_rejectsFooterFastIdentity(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest(
        "resource.test",
        root,
        integrityMode="footerFast",
        useCache=False,
    )

    with pytest.raises(ValueError, match="RESOURCE_INTEGRITY_MODE_UNSUPPORTED"):
        readVerifiedManifestShard(manifest, "A")


def test_readVerifiedManifestShard_rejectsPinnedPathEscape(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    escapedShard = replace(
        manifest.shards[0],
        relativePath="../A.parquet",
    )
    escapedManifest = replace(
        manifest,
        shards=(escapedShard, *manifest.shards[1:]),
    )

    with pytest.raises(ValueError, match="RESOURCE_SHARD_PATH_ESCAPE"):
        readVerifiedManifestShard(escapedManifest, "A")


def test_loadResourceManifest_unionsHistoricalShardSchemas(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    root.mkdir()
    pq.write_table(pa.table({"companyId": ["A"], "value": [1], "legacy": ["kept"]}), root / "A.parquet")
    pq.write_table(pa.table({"companyId": ["B"], "value": [2]}), root / "B.parquet")

    manifest = loadResourceManifest("resource.test", root, useCache=False)

    assert dict(manifest.schemaFields) == {
        "companyId": "string",
        "value": "int64",
        "legacy": "string",
    }
    assert dict(manifest.commonSchemaFields) == {
        "companyId": "string",
        "value": "int64",
    }


def test_loadResourceManifest_schemaUnionIsDeterministicAndPromotesTypes(
    tmp_path: Path,
) -> None:
    roots = (tmp_path / "first", tmp_path / "second")
    for root, creationOrder in zip(roots, (("B", "A"), ("A", "B")), strict=True):
        root.mkdir()
        tables = {
            "A": pa.table(
                {
                    "z": ["first"],
                    "a": [1],
                    "metric": pa.array([10], type=pa.int32()),
                }
            ),
            "B": pa.table(
                {
                    "b": ["later"],
                    "a": [2],
                    "metric": pa.array([20], type=pa.int64()),
                }
            ),
        }
        for companyId in creationOrder:
            pq.write_table(tables[companyId], root / f"{companyId}.parquet")

    manifests = tuple(loadResourceManifest("resource.test", root, useCache=False) for root in roots)
    expected = (
        ("z", "string"),
        ("a", "int64"),
        ("metric", "int64"),
        ("b", "string"),
    )
    assert manifests[0].schemaFields == manifests[1].schemaFields == expected
    assert manifests[0].commonSchemaFields == manifests[1].commonSchemaFields == (("a", "int64"),)
    assert manifests[0].sourcePin == manifests[1].sourcePin


def test_loadResourceManifest_rejectsIncompatibleShardTypes(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    root.mkdir()
    pq.write_table(pa.table({"value": pa.array([1], type=pa.int64())}), root / "A.parquet")
    pq.write_table(pa.table({"value": ["one"]}), root / "B.parquet")

    with pytest.raises(ValueError, match="RESOURCE_SCHEMA_INCOMPATIBLE"):
        loadResourceManifest("resource.test", root, useCache=False)


def test_loadResourceManifest_invalidatesLegacySchemaCache(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    cachePath = tmp_path / "manifest.json"
    root.mkdir()
    pq.write_table(pa.table({"companyId": ["A"], "value": [1]}), root / "A.parquet")
    pq.write_table(
        pa.table({"companyId": ["B"], "value": [2], "legacy": ["kept"]}),
        root / "B.parquet",
    )
    loadResourceManifest("resource.test", root, cachePath=cachePath)
    legacyDocument = json.loads(cachePath.read_text(encoding="utf-8"))
    legacyDocument.pop("cacheDocumentSha256")
    legacyDocument["format"] = "dartlab-resource-manifest-v1"
    legacyDocument.pop("schemaPolicy")
    legacyDocument.pop("commonSchemaFields")
    legacyDocument["schemaFields"] = [["companyId", "string"], ["value", "int64"]]
    legacyDocument["cacheDocumentSha256"] = hashlib.sha256(
        manifestModule.canonicalJsonBytes(
            {key: value for key, value in legacyDocument.items() if key != "cacheDocumentSha256"}
        )
    ).hexdigest()
    cachePath.write_text(json.dumps(legacyDocument), encoding="utf-8")

    rebuilt = loadResourceManifest("resource.test", root, cachePath=cachePath)
    currentDocument = json.loads(cachePath.read_text(encoding="utf-8"))
    assert rebuilt.cacheHit is False
    assert dict(rebuilt.schemaFields)["legacy"] == "string"
    assert currentDocument["format"] == "dartlab-resource-manifest-v2"
    assert currentDocument["schemaPolicy"] == "allShardsArrowPermissiveV1"


def test_loadResourceManifest_rejectsMutationDuringFullHash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    realDigest = manifestModule._fullFileDigest

    def mutateAfterDigest(path: Path) -> str:
        digest = realDigest(path)
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
        return digest

    monkeypatch.setattr(manifestModule, "_fullFileDigest", mutateAfterDigest)
    with pytest.raises(ValueError, match="RESOURCE_SOURCE_DRIFT"):
        loadResourceManifest("resource.test", root, useCache=False)


def test_validateManifestSources_detectsFileSetAndMetadataDrift(tmp_path: Path) -> None:
    root = tmp_path / "resource"
    _writeResourceRoot(root)
    manifest = loadResourceManifest("resource.test", root, useCache=False)
    path = root / "A.parquet"
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    with pytest.raises(ValueError, match="RESOURCE_SOURCE_DRIFT"):
        validateManifestSources(manifest)
