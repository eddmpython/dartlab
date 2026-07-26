"""Resource manifest cache publication과 sandbox pinned read tests."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import dartlab.providers.resourceStream.manifestCache as cacheModule
from dartlab.providers.resourceStream.contracts import (
    ResourceManifest,
    canonicalJsonBytes,
)
from dartlab.providers.resourceStream.manifest import (
    loadResourceManifest,
    readVerifiedManifestShard,
)
from dartlab.providers.resourceStream.manifestCache import (
    loadPinnedResourceManifestReadOnly,
)

pytestmark = pytest.mark.unit


def _writeResourceRoot(root: Path) -> None:
    root.mkdir()
    for companyId, value in (("A", 1), ("B", 2)):
        pq.write_table(
            pa.table(
                {
                    "companyId": [companyId],
                    "value": [value],
                }
            ),
            root / f"{companyId}.parquet",
        )


def _sandboxPinnedRead(
    rootPath: str,
    cachePath: str,
    expectedSourcePin: str,
    artifactPath: str,
    resultQueue: Any,
) -> None:
    try:
        from dartlab.dataHub.eagerSandbox import enforceProcessSandbox
        from dartlab.providers.resourceStream.manifest import (
            readVerifiedManifestShard,
        )
        from dartlab.providers.resourceStream.manifestCache import (
            loadPinnedResourceManifestReadOnly,
        )

        enforceProcessSandbox(Path(artifactPath))
        manifest = loadPinnedResourceManifestReadOnly(
            "resource.test",
            rootPath,
            expectedSourcePin,
            cachePath=cachePath,
        )
        shard, payload = readVerifiedManifestShard(manifest, "A")
        resultQueue.put(
            (
                "ok",
                manifest.sourcePin,
                shard.companyId,
                hashlib.sha256(payload).hexdigest(),
            )
        )
    except BaseException as error:
        resultQueue.put(
            (
                "error",
                type(error).__name__,
                getattr(error, "code", None),
                str(error),
            )
        )


def _fixture(
    tmp_path: Path,
) -> tuple[Path, Path, ResourceManifest]:
    root = tmp_path / "resource"
    cachePath = tmp_path / "manifest.json"
    _writeResourceRoot(root)
    manifest = loadResourceManifest(
        "resource.test",
        root,
        cachePath=cachePath,
    )
    return root, cachePath, manifest


def testReadOnlyPinnedLoadNeverCreatesLockFile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, cachePath, first = _fixture(tmp_path)
    lockPath = Path(f"{cachePath}.lock")
    assert not lockPath.exists()

    def failLock(*_args: object, **_kwargs: object):
        raise AssertionError("read-only pinned cache가 lock file을 열었습니다")

    monkeypatch.setattr(cacheModule, "FileLock", failLock)
    replayed = loadPinnedResourceManifestReadOnly(
        "resource.test",
        root,
        first.sourcePin,
        cachePath=cachePath,
    )

    assert replayed.sourcePin == first.sourcePin
    assert replayed.cacheHit is True
    assert not lockPath.exists()


def testReadOnlyPinnedLoadRejectsTornDocumentWithoutRetry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, cachePath, first = _fixture(tmp_path)
    cachePath.write_text(
        '{"format":"dartlab-resource-manifest-v2"',
        encoding="utf-8",
    )

    def failSleep(_seconds: float) -> None:
        raise AssertionError("invalid JSON을 retry했습니다")

    monkeypatch.setattr(cacheModule.time, "sleep", failSleep)
    with pytest.raises(ValueError, match="RESOURCE_SOURCE_DRIFT"):
        loadPinnedResourceManifestReadOnly(
            "resource.test",
            root,
            first.sourcePin,
            cachePath=cachePath,
        )


def testReadOnlyPinnedLoadRejectsSelfHashedTotalByteMismatch(
    tmp_path: Path,
) -> None:
    root, cachePath, first = _fixture(tmp_path)
    document = json.loads(cachePath.read_text(encoding="utf-8"))
    document["totalBytes"] += 1
    payload = {key: value for key, value in document.items() if key != "cacheDocumentSha256"}
    document["cacheDocumentSha256"] = hashlib.sha256(canonicalJsonBytes(payload)).hexdigest()
    cachePath.write_bytes(canonicalJsonBytes(document))

    with pytest.raises(ValueError, match="RESOURCE_SOURCE_DRIFT"):
        loadPinnedResourceManifestReadOnly(
            "resource.test",
            root,
            first.sourcePin,
            cachePath=cachePath,
        )


def testSandboxSpawnReadsPinnedCacheWithoutWrite(
    tmp_path: Path,
) -> None:
    root, cachePath, first = _fixture(tmp_path)
    artifactPath = tmp_path / "owner-result.arrow"
    artifactPath.touch()
    expectedDigest = hashlib.sha256((root / "A.parquet").read_bytes()).hexdigest()
    context = get_context("spawn")
    resultQueue = context.Queue()
    process = context.Process(
        target=_sandboxPinnedRead,
        args=(
            str(root),
            str(cachePath),
            first.sourcePin,
            str(artifactPath),
            resultQueue,
        ),
    )
    process.start()
    process.join(timeout=30)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        pytest.fail("sandbox pinned cache child가 종료되지 않았습니다")
    result = resultQueue.get(timeout=5)
    resultQueue.close()
    resultQueue.join_thread()

    assert process.exitcode == 0
    assert result == (
        "ok",
        first.sourcePin,
        "A",
        expectedDigest,
    )
    assert not Path(f"{cachePath}.lock").exists()


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows open reader와 replace sharing regression",
)
def testWindowsConcurrentPublishAndReadOnlyReplayIsBounded(
    tmp_path: Path,
) -> None:
    root, cachePath, first = _fixture(tmp_path)
    start = threading.Barrier(3)

    def publish() -> None:
        start.wait(timeout=5)
        for _ in range(50):
            cacheModule._writeCache(cachePath, first)

    def replay() -> None:
        start.wait(timeout=5)
        for _ in range(100):
            loaded = loadPinnedResourceManifestReadOnly(
                "resource.test",
                root,
                first.sourcePin,
                cachePath=cachePath,
            )
            assert loaded.sourcePin == first.sourcePin

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = (
            executor.submit(publish),
            executor.submit(replay),
            executor.submit(replay),
        )
        for future in futures:
            future.result(timeout=30)

    replayed = loadPinnedResourceManifestReadOnly(
        "resource.test",
        root,
        first.sourcePin,
        cachePath=cachePath,
    )
    assert replayed.sourcePin == first.sourcePin
    assert tuple(tmp_path.glob("manifest.json.*.tmp")) == ()


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows open reader와 replace sharing regression",
)
def testReadOnlyPinnedLoadRetriesOnlyTransientWindowsPermission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, cachePath, first = _fixture(tmp_path)
    originalReadText = Path.read_text
    attempts = 0
    sleeps: list[float] = []

    def collideOnce(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> str:
        nonlocal attempts
        if path == cachePath:
            attempts += 1
            if attempts == 1:
                error = PermissionError(13, "sharing collision")
                error.winerror = 5
                raise error
        return originalReadText(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", collideOnce)
    monkeypatch.setattr(
        cacheModule.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )
    replayed = loadPinnedResourceManifestReadOnly(
        "resource.test",
        root,
        first.sourcePin,
        cachePath=cachePath,
    )

    assert replayed.sourcePin == first.sourcePin
    assert attempts == 2
    assert sleeps == [cacheModule._CACHE_READ_RETRY_SECONDS]


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows replace의 destination 교체 간극 regression",
)
def testReadOnlyPinnedLoadMissingCacheRetryIsBounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, cachePath, first = _fixture(tmp_path)
    cachePath.unlink()
    sleeps: list[float] = []
    monkeypatch.setattr(
        cacheModule.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )

    with pytest.raises(ValueError, match="RESOURCE_SOURCE_DRIFT"):
        loadPinnedResourceManifestReadOnly(
            "resource.test",
            root,
            first.sourcePin,
            cachePath=cachePath,
        )

    assert len(sleeps) == cacheModule._CACHE_READ_ATTEMPTS - 1
    assert sum(sleeps) == pytest.approx(cacheModule._CACHE_READ_RETRY_SECONDS * (cacheModule._CACHE_READ_ATTEMPTS - 1))


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows Python open 오류의 errno fallback regression",
)
def testReadOnlyPinnedLoadRetriesTransientErrnoWithoutWinerror(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, cachePath, first = _fixture(tmp_path)
    originalReadText = Path.read_text
    attempts = 0

    def collideOnce(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> str:
        nonlocal attempts
        if path == cachePath:
            attempts += 1
            if attempts == 1:
                error = PermissionError(errno.EACCES, "sharing collision")
                error.winerror = None
                raise error
        return originalReadText(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", collideOnce)
    monkeypatch.setattr(cacheModule.time, "sleep", lambda _seconds: None)
    replayed = loadPinnedResourceManifestReadOnly(
        "resource.test",
        root,
        first.sourcePin,
        cachePath=cachePath,
    )

    assert replayed.sourcePin == first.sourcePin
    assert attempts == 2


def testCachePublishDoesNotRetryNonTransientPermission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _root, cachePath, first = _fixture(tmp_path)
    attempts = 0

    def denyReplace(_source: object, _destination: object) -> None:
        nonlocal attempts
        attempts += 1
        error = PermissionError(13, "non-transient")
        error.winerror = 999
        raise error

    def failSleep(_seconds: float) -> None:
        raise AssertionError("non-transient permission error를 retry했습니다")

    monkeypatch.setattr(cacheModule.os, "replace", denyReplace)
    monkeypatch.setattr(cacheModule.time, "sleep", failSleep)
    with pytest.raises(PermissionError, match="non-transient"):
        cacheModule._writeCache(cachePath, first)

    assert attempts == 1
    assert tuple(tmp_path.glob("manifest.json.*.tmp")) == ()


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows transient replace retry contract",
)
def testCachePublishTransientRetryHasFixedAttemptBound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _root, cachePath, first = _fixture(tmp_path)
    attempts = 0
    sleeps = 0

    def denyReplace(_source: object, _destination: object) -> None:
        nonlocal attempts
        attempts += 1
        error = PermissionError(13, "sharing violation")
        error.winerror = 5
        raise error

    def countSleep(seconds: float) -> None:
        nonlocal sleeps
        assert seconds == cacheModule._CACHE_REPLACE_RETRY_SECONDS
        sleeps += 1

    monkeypatch.setattr(cacheModule.os, "replace", denyReplace)
    monkeypatch.setattr(cacheModule.time, "sleep", countSleep)
    with pytest.raises(PermissionError, match="sharing violation"):
        cacheModule._writeCache(cachePath, first)

    assert attempts == cacheModule._CACHE_REPLACE_ATTEMPTS
    assert sleeps == cacheModule._CACHE_REPLACE_ATTEMPTS - 1
    assert tuple(tmp_path.glob("manifest.json.*.tmp")) == ()


def testVerifiedShardStillMatchesReadOnlyManifest(tmp_path: Path) -> None:
    root, cachePath, first = _fixture(tmp_path)
    replayed = loadPinnedResourceManifestReadOnly(
        "resource.test",
        root,
        first.sourcePin,
        cachePath=cachePath,
    )
    shard, payload = readVerifiedManifestShard(replayed, "B")

    assert shard.companyId == "B"
    assert hashlib.sha256(payload).hexdigest() == shard.integrityDigest
