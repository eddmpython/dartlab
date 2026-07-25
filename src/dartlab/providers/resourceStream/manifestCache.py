"""Resource manifest cache의 atomic publication과 pinned read 계약."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from filelock import FileLock

from .contracts import (
    IntegrityMode,
    ResourceManifest,
    ResourceShard,
    canonicalJsonBytes,
)

_CACHE_FORMAT = "dartlab-resource-manifest-v2"
_CACHE_VALIDATION = "fileSet+size+mtimeNs+cacheDocumentSha256"
_SCHEMA_POLICY = "allShardsArrowPermissiveV1"
_CACHE_REPLACE_ATTEMPTS = 40
_CACHE_REPLACE_RETRY_SECONDS = 0.005
_CACHE_READ_ATTEMPTS = 8
_CACHE_READ_RETRY_SECONDS = 0.002
_WINDOWS_TRANSIENT_REPLACE_ERRORS = frozenset({5, 32, 33})


def _sourcePin(
    resourceId: str,
    integrityMode: IntegrityMode,
    schemaFields: tuple[tuple[str, str], ...],
    commonSchemaFields: tuple[tuple[str, str], ...],
    shards: tuple[ResourceShard, ...],
) -> str:
    payload = {
        "format": ("full-file-sha256-manifest-v2" if integrityMode == "full" else "parquet-footer-fast-manifest-v2"),
        "resourceId": resourceId,
        "integrityMode": integrityMode,
        "schemaPolicy": _SCHEMA_POLICY,
        "schemaFields": schemaFields,
        "commonSchemaFields": commonSchemaFields,
        "shards": [
            (
                shard.companyId,
                shard.relativePath,
                shard.byteSize,
                shard.integrityDigest,
            )
            for shard in shards
        ],
    }
    pinKind = "full" if integrityMode == "full" else "footer-fast"
    return f"resource-source-{pinKind}:{hashlib.sha256(canonicalJsonBytes(payload)).hexdigest()}"


def _defaultCachePath(
    resourceId: str,
    root: Path,
    integrityMode: IntegrityMode,
) -> Path:
    configured = os.getenv("DARTLAB_RESOURCE_MANIFEST_CACHE")
    cacheRoot = Path(configured).expanduser() if configured else Path.home() / ".dartlab" / "cache" / "resourceStream"
    identity = hashlib.sha256(
        canonicalJsonBytes(
            {
                "resourceId": resourceId,
                "rootPath": str(root),
                "integrityMode": integrityMode,
            }
        )
    ).hexdigest()
    return cacheRoot / f"{identity}.json"


def _cachePayload(manifest: ResourceManifest) -> dict[str, object]:
    return {
        "format": _CACHE_FORMAT,
        "rootPath": manifest.rootPath,
        "resourceId": manifest.resourceId,
        "integrityMode": manifest.integrityMode,
        "schemaPolicy": _SCHEMA_POLICY,
        "schemaFields": [list(field) for field in manifest.schemaFields],
        "commonSchemaFields": [list(field) for field in manifest.commonSchemaFields],
        "totalBytes": manifest.totalBytes,
        "sourcePin": manifest.sourcePin,
        "cacheValidation": _CACHE_VALIDATION,
        "shards": [shard.toMapping() for shard in manifest.shards],
    }


def _retryableReplaceError(error: PermissionError) -> bool:
    """Windows open-reader sharing 충돌만 bounded retry 대상으로 인정한다."""

    return os.name == "nt" and getattr(error, "winerror", None) in _WINDOWS_TRANSIENT_REPLACE_ERRORS


def _retryableReadError(error: PermissionError) -> bool:
    """Windows read/open sharing 충돌만 bounded retry 대상으로 인정한다."""

    windowsError = getattr(error, "winerror", None)
    return os.name == "nt" and (
        windowsError in _WINDOWS_TRANSIENT_REPLACE_ERRORS
        or (windowsError is None and error.errno in {errno.EACCES, errno.EPERM})
    )


def _writeCache(cachePath: Path, manifest: ResourceManifest) -> None:
    """같은 directory temp와 atomic replace로 cache 문서를 게시한다."""

    cachePath.parent.mkdir(parents=True, exist_ok=True)
    payload = _cachePayload(manifest)
    document = dict(payload)
    document["cacheDocumentSha256"] = hashlib.sha256(canonicalJsonBytes(payload)).hexdigest()
    tempPath: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f"{cachePath.name}.",
            suffix=".tmp",
            dir=cachePath.parent,
            delete=False,
        ) as stream:
            tempPath = Path(stream.name)
            stream.write(canonicalJsonBytes(document))
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(_CACHE_REPLACE_ATTEMPTS):
            try:
                os.replace(tempPath, cachePath)
                tempPath = None
                break
            except PermissionError as error:
                if not _retryableReplaceError(error) or attempt + 1 >= _CACHE_REPLACE_ATTEMPTS:
                    raise
                time.sleep(_CACHE_REPLACE_RETRY_SECONDS)
    finally:
        if tempPath is not None and tempPath.exists():
            tempPath.unlink()


def _manifestFromCacheDocument(
    document: dict[str, Any],
    root: Path,
    resourceId: str,
    integrityMode: IntegrityMode,
) -> ResourceManifest | None:
    expectedIntegrity = document.get("cacheDocumentSha256")
    payload = {key: value for key, value in document.items() if key != "cacheDocumentSha256"}
    expectedPayloadKeys = {
        "format",
        "rootPath",
        "resourceId",
        "integrityMode",
        "schemaPolicy",
        "schemaFields",
        "commonSchemaFields",
        "totalBytes",
        "sourcePin",
        "cacheValidation",
        "shards",
    }
    if (
        set(document) != {*expectedPayloadKeys, "cacheDocumentSha256"}
        or not isinstance(expectedIntegrity, str)
        or hashlib.sha256(canonicalJsonBytes(payload)).hexdigest() != expectedIntegrity
        or payload.get("format") != _CACHE_FORMAT
        or payload.get("rootPath") != str(root)
        or payload.get("resourceId") != resourceId
        or payload.get("integrityMode") != integrityMode
        or payload.get("schemaPolicy") != _SCHEMA_POLICY
        or payload.get("cacheValidation") != _CACHE_VALIDATION
    ):
        return None
    shardValues = payload.get("shards")
    schemaValues = payload.get("schemaFields")
    commonSchemaValues = payload.get("commonSchemaFields")
    if (
        not isinstance(shardValues, list)
        or not shardValues
        or not isinstance(schemaValues, list)
        or not schemaValues
        or not isinstance(commonSchemaValues, list)
    ):
        return None
    shardKeys = {
        "companyId",
        "relativePath",
        "byteSize",
        "mtimeNs",
        "integrityDigest",
    }
    if any(
        not isinstance(value, dict)
        or set(value) != shardKeys
        or not isinstance(value["companyId"], str)
        or not value["companyId"]
        or not isinstance(value["relativePath"], str)
        or not value["relativePath"]
        or type(value["byteSize"]) is not int
        or value["byteSize"] < 0
        or type(value["mtimeNs"]) is not int
        or value["mtimeNs"] < 0
        or not isinstance(value["integrityDigest"], str)
        or len(value["integrityDigest"]) != 64
        or any(character not in "0123456789abcdef" for character in value["integrityDigest"])
        for value in shardValues
    ):
        return None
    if any(
        not isinstance(value, list) or len(value) != 2 or any(not isinstance(item, str) or not item for item in value)
        for value in (*schemaValues, *commonSchemaValues)
    ):
        return None
    shards = tuple(
        ResourceShard(
            companyId=value["companyId"],
            relativePath=value["relativePath"],
            byteSize=value["byteSize"],
            mtimeNs=value["mtimeNs"],
            integrityDigest=value["integrityDigest"],
        )
        for value in shardValues
    )
    companyIds = tuple(shard.companyId for shard in shards)
    relativePaths = tuple(shard.relativePath for shard in shards)
    totalBytes = payload.get("totalBytes")
    if (
        len(companyIds) != len(set(companyIds))
        or len(relativePaths) != len(set(relativePaths))
        or type(totalBytes) is not int
        or totalBytes < 0
        or totalBytes != sum(shard.byteSize for shard in shards)
    ):
        return None
    schemaFields = tuple((value[0], value[1]) for value in schemaValues)
    commonSchemaFields = tuple((value[0], value[1]) for value in commonSchemaValues)
    sourcePin = _sourcePin(
        resourceId,
        integrityMode,
        schemaFields,
        commonSchemaFields,
        shards,
    )
    if payload.get("sourcePin") != sourcePin:
        return None
    return ResourceManifest(
        resourceId=resourceId,
        rootPath=str(root),
        shards=shards,
        schemaFields=schemaFields,
        totalBytes=totalBytes,
        integrityMode=integrityMode,
        sourcePin=sourcePin,
        commonSchemaFields=commonSchemaFields,
        cacheHit=False,
        cacheValidation=_CACHE_VALIDATION,
    )


def _readCacheCandidate(
    cachePath: Path,
    root: Path,
    resourceId: str,
    integrityMode: IntegrityMode,
    *,
    retryTransientPermission: bool = False,
) -> ResourceManifest | None:
    for attempt in range(_CACHE_READ_ATTEMPTS):
        try:
            document = json.loads(cachePath.read_text(encoding="utf-8"))
            if not isinstance(document, dict):
                return None
            return _manifestFromCacheDocument(
                document,
                root,
                resourceId,
                integrityMode,
            )
        except FileNotFoundError:
            if retryTransientPermission and os.name == "nt" and attempt + 1 < _CACHE_READ_ATTEMPTS:
                time.sleep(_CACHE_READ_RETRY_SECONDS)
                continue
            return None
        except PermissionError as error:
            if retryTransientPermission and _retryableReadError(error) and attempt + 1 < _CACHE_READ_ATTEMPTS:
                time.sleep(_CACHE_READ_RETRY_SECONDS)
                continue
            return None
        except (
            OSError,
            TypeError,
            ValueError,
            KeyError,
            IndexError,
            json.JSONDecodeError,
        ):
            return None
    return None


def _pinnedManifestRequest(
    resourceId: str,
    rootPath: str | Path,
    expectedSourcePin: str,
    *,
    cachePath: str | Path | None = None,
) -> tuple[str, Path, str, Path]:
    if not isinstance(expectedSourcePin, str):
        raise TypeError("expectedSourcePin은 str이어야 합니다")
    normalizedSourcePin = expectedSourcePin.strip()
    if not normalizedSourcePin.startswith("resource-source-full:"):
        raise ValueError("RESOURCE_SOURCE_DRIFT: expected sourcePin이 full identity가 아닙니다")
    normalizedId = resourceId.strip()
    root = Path(rootPath).resolve()
    if not normalizedId:
        raise ValueError("resourceId가 비었습니다")
    if not root.is_dir():
        raise ValueError(f"resource root가 없습니다: {root}")
    resolvedCachePath = (
        Path(cachePath).resolve() if cachePath is not None else _defaultCachePath(normalizedId, root, "full")
    )
    if not resolvedCachePath.parent.is_dir():
        raise ValueError("RESOURCE_SOURCE_DRIFT: pinned manifest cache가 없습니다")
    return normalizedId, root, normalizedSourcePin, resolvedCachePath


def _readPinnedResourceManifest(
    normalizedId: str,
    root: Path,
    normalizedSourcePin: str,
    resolvedCachePath: Path,
    *,
    retryTransientPermission: bool = False,
) -> ResourceManifest:
    manifest = _readCacheCandidate(
        resolvedCachePath,
        root,
        normalizedId,
        "full",
        retryTransientPermission=retryTransientPermission,
    )
    if manifest is None:
        raise ValueError("RESOURCE_SOURCE_DRIFT: pinned manifest cache가 없거나 유효하지 않습니다")
    if manifest.sourcePin != normalizedSourcePin:
        raise ValueError("RESOURCE_SOURCE_DRIFT: expected sourcePin이 pinned manifest와 다릅니다")
    return ResourceManifest(
        resourceId=manifest.resourceId,
        rootPath=manifest.rootPath,
        shards=manifest.shards,
        schemaFields=manifest.schemaFields,
        totalBytes=manifest.totalBytes,
        integrityMode=manifest.integrityMode,
        sourcePin=manifest.sourcePin,
        commonSchemaFields=manifest.commonSchemaFields,
        cacheHit=True,
        cacheValidation=manifest.cacheValidation,
    )


def loadPinnedResourceManifest(
    resourceId: str,
    rootPath: str | Path,
    expectedSourcePin: str,
    *,
    cachePath: str | Path | None = None,
    lockTimeoutSeconds: float = 120.0,
) -> ResourceManifest:
    """Expected full source pin에 결박된 cache를 process lock 아래 읽는다."""

    request = _pinnedManifestRequest(
        resourceId,
        rootPath,
        expectedSourcePin,
        cachePath=cachePath,
    )
    with FileLock(f"{request[3]}.lock", timeout=lockTimeoutSeconds):
        return _readPinnedResourceManifest(*request)


def loadPinnedResourceManifestReadOnly(
    resourceId: str,
    rootPath: str | Path,
    expectedSourcePin: str,
    *,
    cachePath: str | Path | None = None,
) -> ResourceManifest:
    """Sandbox child에서 lock file 없이 pinned cache를 fail-closed 읽는다.

    Writer의 same-directory fsync와 atomic replace로 old 또는 new 완성 문서만
    관측한다. Parse, envelope SHA-256, binding, recomputed source pin 또는 caller
    expected source pin이 다르면 cache 재생성 없이 source drift로 거부한다.
    """

    request = _pinnedManifestRequest(
        resourceId,
        rootPath,
        expectedSourcePin,
        cachePath=cachePath,
    )
    return _readPinnedResourceManifest(
        *request,
        retryTransientPermission=True,
    )


__all__ = [
    "_CACHE_REPLACE_ATTEMPTS",
    "_CACHE_REPLACE_RETRY_SECONDS",
    "_CACHE_READ_ATTEMPTS",
    "_CACHE_READ_RETRY_SECONDS",
    "_CACHE_VALIDATION",
    "_defaultCachePath",
    "_manifestFromCacheDocument",
    "_readCacheCandidate",
    "_retryableReadError",
    "_retryableReplaceError",
    "_sourcePin",
    "_writeCache",
    "loadPinnedResourceManifest",
    "loadPinnedResourceManifestReadOnly",
]
