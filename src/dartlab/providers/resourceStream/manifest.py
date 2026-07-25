"""Full-integrity resource manifest와 process-safe persistent cache."""

from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from filelock import FileLock

from .contracts import (
    IntegrityMode,
    ResourceManifest,
    ResourceShard,
)
from .contracts import (
    canonicalJsonBytes as canonicalJsonBytes,
)
from .manifestCache import (
    _CACHE_VALIDATION,
    _defaultCachePath,
    _readCacheCandidate,
    _sourcePin,
    _writeCache,
    loadPinnedResourceManifest,
    loadPinnedResourceManifestReadOnly,
)

_SCHEMA_POLICY = "allShardsArrowPermissiveV1"
_SCHEMA_READ_CHUNK_SIZE = 256


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


def _stableDigest(path: Path, digestFn: Any) -> tuple[str, os.stat_result]:
    """파일 metadata가 digest 계산 중 바뀌면 source pin 생성을 중단한다."""

    before = path.stat()
    digest = digestFn(path)
    after = path.stat()
    identityBefore = (before.st_size, before.st_mtime_ns)
    identityAfter = (after.st_size, after.st_mtime_ns)
    if identityBefore != identityAfter:
        raise ValueError(f"RESOURCE_SOURCE_DRIFT: manifest hash 중 변경됨: {path.name}")
    return digest, after


def _schemaForPinnedShard(path: Path, shard: ResourceShard) -> pa.Schema:
    """Pinned stat identity 안에서 parquet schema를 읽는다."""

    before = path.stat()
    if (before.st_size, before.st_mtime_ns) != (shard.byteSize, shard.mtimeNs):
        raise ValueError(f"RESOURCE_SOURCE_DRIFT: schema read 전 변경됨: {path.name}")
    schema = pq.read_schema(path)
    after = path.stat()
    if (after.st_size, after.st_mtime_ns) != (shard.byteSize, shard.mtimeNs):
        raise ValueError(f"RESOURCE_SOURCE_DRIFT: schema read 중 변경됨: {path.name}")
    return schema


def _resourcePaths(root: Path) -> tuple[Path, ...]:
    paths = tuple(sorted(root.glob("*.parquet"), key=lambda path: path.name))
    if not paths:
        raise ValueError("resource parquet shard가 없습니다")
    return paths


def _cacheIsFresh(candidate: ResourceManifest, paths: tuple[Path, ...]) -> bool:
    if tuple(path.name for path in paths) != tuple(shard.relativePath for shard in candidate.shards):
        return False
    for path, shard in zip(paths, candidate.shards, strict=True):
        stat = path.stat()
        if stat.st_size != shard.byteSize or stat.st_mtime_ns != shard.mtimeNs:
            return False
    return True


def _unifiedPinnedSchema(
    paths: tuple[Path, ...],
    shards: tuple[ResourceShard, ...],
) -> tuple[pa.Schema, tuple[tuple[str, str], ...]]:
    unified: pa.Schema | None = None
    commonTypes: dict[str, str] | None = None
    maxWorkers = min(8, os.cpu_count() or 1)
    try:
        with ThreadPoolExecutor(max_workers=maxWorkers, thread_name_prefix="resource-schema") as executor:
            for offset in range(0, len(paths), _SCHEMA_READ_CHUNK_SIZE):
                pathChunk = paths[offset : offset + _SCHEMA_READ_CHUNK_SIZE]
                shardChunk = shards[offset : offset + _SCHEMA_READ_CHUNK_SIZE]
                schemas = tuple(executor.map(_schemaForPinnedShard, pathChunk, shardChunk))
                for schema in schemas:
                    currentTypes = {field.name: str(field.type) for field in schema}
                    if commonTypes is None:
                        commonTypes = currentTypes
                    else:
                        commonTypes = {
                            name: fieldType
                            for name, fieldType in commonTypes.items()
                            if currentTypes.get(name) == fieldType
                        }
                candidates = schemas if unified is None else (unified, *schemas)
                unified = pa.unify_schemas(candidates, promote_options="permissive")
    except (pa.ArrowInvalid, pa.ArrowTypeError):
        raise ValueError("RESOURCE_SCHEMA_INCOMPATIBLE: parquet shard schema를 합칠 수 없습니다") from None
    if unified is None or commonTypes is None:
        raise ValueError("resource parquet shard schema가 없습니다")
    return unified, tuple(commonTypes.items())


def _buildManifest(
    resourceId: str,
    root: Path,
    paths: tuple[Path, ...],
    integrityMode: IntegrityMode,
    candidate: ResourceManifest | None,
) -> ResourceManifest:
    cachedByPath = {shard.relativePath: shard for shard in candidate.shards} if candidate else {}
    digestFn = _fullFileDigest if integrityMode == "full" else _footerDigest
    pending: list[Path] = []
    resolved: dict[str, ResourceShard] = {}
    for path in paths:
        stat = path.stat()
        cached = cachedByPath.get(path.name)
        if cached is not None and cached.byteSize == stat.st_size and cached.mtimeNs == stat.st_mtime_ns:
            resolved[path.name] = cached
        else:
            pending.append(path)
    if pending:
        maxWorkers = min(8, os.cpu_count() or 1)
        with ThreadPoolExecutor(max_workers=maxWorkers, thread_name_prefix="resource-integrity") as executor:
            inspected = tuple(executor.map(lambda path: _stableDigest(path, digestFn), pending))
        for path, (digest, stat) in zip(pending, inspected, strict=True):
            resolved[path.name] = ResourceShard(
                companyId=path.stem,
                relativePath=path.name,
                byteSize=stat.st_size,
                mtimeNs=stat.st_mtime_ns,
                integrityDigest=digest,
            )
    shards = tuple(resolved[path.name] for path in paths)
    companyIds = tuple(shard.companyId for shard in shards)
    if len(companyIds) != len(set(companyIds)):
        raise ValueError("company shard ID가 중복됐습니다")
    schema, commonSchemaFields = _unifiedPinnedSchema(paths, shards)
    schemaFields = tuple((field.name, str(field.type)) for field in schema)
    sourcePin = _sourcePin(
        resourceId,
        integrityMode,
        schemaFields,
        commonSchemaFields,
        shards,
    )
    return ResourceManifest(
        resourceId=resourceId,
        rootPath=str(root),
        shards=shards,
        schemaFields=schemaFields,
        totalBytes=sum(shard.byteSize for shard in shards),
        integrityMode=integrityMode,
        sourcePin=sourcePin,
        commonSchemaFields=commonSchemaFields,
        cacheHit=False,
        cacheValidation=_CACHE_VALIDATION,
    )


def loadResourceManifest(
    resourceId: str,
    rootPath: str | Path,
    *,
    integrityMode: IntegrityMode = "full",
    cachePath: str | Path | None = None,
    useCache: bool = True,
    lockTimeoutSeconds: float = 120.0,
) -> ResourceManifest:
    """Company parquet resource의 integrity manifest를 load 또는 build한다.

    Capabilities:
        full-file SHA-256 기본, footerFast 명시 모드, process lock, atomic cache write,
        unchanged shard digest 재사용을 제공한다.

    Args:
        resourceId: stable resource ID.
        rootPath: flat company parquet directory.
        integrityMode: full 또는 benchmark-only footerFast.
        cachePath: persistent cache JSON path. None이면 사용자 cache directory를 사용한다.
        useCache: False면 cache read와 write를 모두 건너뛴다.
        lockTimeoutSeconds: process lock 대기 상한.

    Returns:
        ResourceManifest.

    Raises:
        ValueError: resource, mode 또는 parquet 구성이 유효하지 않을 때.
        filelock.Timeout: 다른 process가 lock을 제한 시간보다 오래 점유할 때.

    Example:
        ``loadResourceManifest("resource.edgar", "data/edgar/finance")``.

    Guide:
        한 query session에서 반환 manifest를 모든 page에 재사용한다.

    When:
        resource query 시작 전 또는 source drift 뒤 새 revision을 고정할 때 호출한다.

    How:
        기본 full mode로 한 번 load하고 반환 manifest를 page reader에 반복 전달한다.

    SeeAlso:
        validateManifestSources.

    Requires:
        cache hit은 file set, size, mtimeNs와 cache document SHA-256을 검증한다.

    AIContext:
        cache hit은 full payload 재해시가 아니다. 동일 size와 mtime을 보존한 외부 변조는
        ``useCache=False`` full rebuild로만 재검증한다.

    LLM Specifications:
        AntiPatterns:
            - page마다 full manifest rebuild
            - footerFast manifest로 continuation 허용
            - size와 mtime cache hit을 payload rehash라고 설명
        Freshness:
            cache miss와 changed shard는 payload 또는 footer bytes를 새로 hash한다.
        Dataflow:
            sorted shards -> process lock -> cache validate -> changed shard hash -> atomic cache.
    """
    normalizedId = resourceId.strip()
    root = Path(rootPath).resolve()
    if not normalizedId:
        raise ValueError("resourceId가 비었습니다")
    if integrityMode not in {"full", "footerFast"}:
        raise ValueError("integrityMode가 유효하지 않습니다")
    if not root.is_dir():
        raise ValueError(f"resource root가 없습니다: {root}")
    paths = _resourcePaths(root)
    if not useCache:
        return _buildManifest(normalizedId, root, paths, integrityMode, None)
    resolvedCachePath = (
        Path(cachePath).resolve() if cachePath is not None else _defaultCachePath(normalizedId, root, integrityMode)
    )
    resolvedCachePath.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(f"{resolvedCachePath}.lock", timeout=lockTimeoutSeconds):
        candidate = _readCacheCandidate(resolvedCachePath, root, normalizedId, integrityMode)
        if candidate is not None and _cacheIsFresh(candidate, paths):
            return ResourceManifest(
                resourceId=candidate.resourceId,
                rootPath=candidate.rootPath,
                shards=candidate.shards,
                schemaFields=candidate.schemaFields,
                totalBytes=candidate.totalBytes,
                integrityMode=candidate.integrityMode,
                sourcePin=candidate.sourcePin,
                commonSchemaFields=candidate.commonSchemaFields,
                cacheHit=True,
                cacheValidation=_CACHE_VALIDATION,
            )
        manifest = _buildManifest(normalizedId, root, paths, integrityMode, candidate)
        _writeCache(resolvedCachePath, manifest)
        return manifest


def validateManifestSources(manifest: ResourceManifest) -> None:
    """Manifest file set, size와 mtimeNs가 현재 source와 같은지 검증한다.

    Capabilities:
        page open 직전 삭제, 추가, 교체, 일반 수정을 payload read 없이 탐지한다.

    Args:
        manifest: 이전에 load된 resource manifest.

    Returns:
        None.

    Raises:
        ValueError: file set, size 또는 mtimeNs drift가 있을 때.

    Example:
        ``validateManifestSources(manifest)``.

    Guide:
        drift면 기존 continuation을 폐기하고 full manifest를 다시 load한다.

    When:
        각 page reader를 열기 직전에 pinned source가 유지되는지 확인할 때 호출한다.

    How:
        manifest root의 현재 flat parquet file set과 저장된 stat identity를 비교한다.

    SeeAlso:
        loadResourceManifest.

    Requires:
        same-size same-mtime 변조의 강한 탐지는 cache bypass full rebuild가 필요하다.

    AIContext:
        빠른 page gate이며 payload integrity 재해시가 아니다.

    LLM Specifications:
        AntiPatterns:
            - stat validation을 cryptographic payload validation으로 설명
        Freshness:
            호출 시점 filesystem metadata다.
    """
    root = Path(manifest.rootPath)
    paths = _resourcePaths(root)
    if tuple(path.name for path in paths) != tuple(shard.relativePath for shard in manifest.shards):
        raise ValueError("RESOURCE_SOURCE_DRIFT: shard file set이 변경됐습니다")
    for path, shard in zip(paths, manifest.shards, strict=True):
        stat = path.stat()
        if stat.st_size != shard.byteSize or stat.st_mtime_ns != shard.mtimeNs:
            raise ValueError(f"RESOURCE_SOURCE_DRIFT: {shard.relativePath}")


def _manifestShardPath(manifest: ResourceManifest, companyId: str) -> tuple[ResourceShard, Path]:
    if not isinstance(manifest, ResourceManifest):
        raise TypeError("manifest는 ResourceManifest여야 합니다")
    if not isinstance(companyId, str):
        raise TypeError("companyId는 str이어야 합니다")
    normalizedCompanyId = companyId.strip()
    if not normalizedCompanyId:
        raise ValueError("companyId가 비었습니다")
    if manifest.integrityMode != "full":
        raise ValueError("RESOURCE_INTEGRITY_MODE_UNSUPPORTED: full manifest가 필요합니다")

    shard = next((item for item in manifest.shards if item.companyId == normalizedCompanyId), None)
    if shard is None:
        raise ValueError(f"RESOURCE_COMPANY_UNKNOWN: {normalizedCompanyId}")

    root = Path(manifest.rootPath).resolve()
    expectedRelativePath = f"{shard.companyId}.parquet"
    if shard.relativePath != expectedRelativePath:
        raise ValueError("RESOURCE_SHARD_PATH_ESCAPE: pinned shard path가 flat identity와 다릅니다")
    path = (root / shard.relativePath).resolve()
    if path.parent != root:
        raise ValueError("RESOURCE_SHARD_PATH_ESCAPE: pinned shard path가 resource root를 벗어났습니다")
    if not path.is_file():
        raise ValueError(f"RESOURCE_SOURCE_DRIFT: {shard.relativePath}")
    return shard, path


def readVerifiedManifestShard(
    manifest: ResourceManifest,
    companyId: str,
) -> tuple[ResourceShard, bytes]:
    """Pinned full manifest의 company shard bytes를 한 번 읽어 재검증한다.

    Capabilities:
        전체 resource를 다시 hash하지 않고 선택한 shard 하나를 같은 file descriptor에서 읽고
        full-file SHA-256과 pre/post stat identity를 pinned identity와 비교한다.

    Args:
        manifest: cache document와 source pin 검증을 통과한 resource manifest.
        companyId: manifest에 등록된 정확한 company shard ID.

    Returns:
        검증된 immutable ``ResourceShard`` identity와 그 검증에 사용한 동일 immutable bytes.

    Raises:
        TypeError: manifest 또는 companyId 타입이 유효하지 않을 때.
        ValueError: full integrity가 아니거나 company, path, stat, payload가 pinned identity와 다를 때.

    Example:
        ``identity, payload = readVerifiedManifestShard(manifest, "0000320193")``.

    Guide:
        Consumer는 반환 bytes를 직접 parse하고 같은 path를 다시 열지 않는다.

    When:
        persistent manifest cache가 metadata cache hit이어도 선택 payload의 강한 무결성이 필요할 때 호출한다.

    How:
        Flat root path를 고정하고 한 descriptor에서 bytes와 SHA-256을 만들며 전후 fstat을 검증한다.

    SeeAlso:
        loadPinnedResourceManifest, validateManifestSources.

    Requires:
        manifest는 ``integrityMode="full"``이어야 하고 shard path는 flat root를 벗어나면 안 된다.

    AIContext:
        same-size same-mtime 교체와 hash 뒤 path reopen TOCTOU를 selected shard 비용만으로 닫는다.

    LLM Specifications:
        AntiPatterns:
            - footerFast digest를 payload verification에 사용
            - manifest 전체 payload를 company마다 다시 hash
            - relativePath를 검증 없이 filesystem path로 결합
            - 검증 뒤 같은 path를 다시 열어 parse
        Freshness:
            호출 시점의 selected shard bytes와 pre/post filesystem stat이다.
        Dataflow:
            pinned shard -> flat path gate -> open -> pre-fstat -> bytes+SHA-256 -> post-fstat -> digest compare.
        OutputSchema:
            - companyId : str, verified company identity
            - integrityDigest : str, verified full-file SHA-256
            - payload : bytes, digest를 계산한 동일 bytes
        Prerequisites:
            cache document SHA-256과 sourcePin 재계산 검증을 통과한 manifest.
        TargetMarkets:
            DATA_RELEASES flat company-sharded resources.
    """
    shard, path = _manifestShardPath(manifest, companyId)
    digest = hashlib.sha256()
    payload = bytearray()
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if (before.st_size, before.st_mtime_ns) != (shard.byteSize, shard.mtimeNs):
                raise ValueError(f"RESOURCE_SOURCE_DRIFT: {shard.relativePath}")
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                payload.extend(chunk)
            after = os.fstat(stream.fileno())
    except FileNotFoundError:
        raise ValueError(f"RESOURCE_SOURCE_DRIFT: {shard.relativePath}") from None
    beforeIdentity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    afterIdentity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if beforeIdentity != afterIdentity or (after.st_size, after.st_mtime_ns) != (shard.byteSize, shard.mtimeNs):
        raise ValueError(f"RESOURCE_SOURCE_DRIFT: {shard.relativePath}")
    if len(payload) != shard.byteSize or digest.hexdigest() != shard.integrityDigest:
        raise ValueError(f"RESOURCE_SOURCE_DRIFT: {shard.relativePath} payload digest")
    return shard, bytes(payload)
