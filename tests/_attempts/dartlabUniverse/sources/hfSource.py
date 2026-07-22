"""설정된 Hugging Face authority를 payload 다운로드 없이 전수 열거한다."""

from __future__ import annotations

import socket
from collections.abc import Callable, Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import PurePosixPath
from types import ModuleType
from typing import Any

from huggingface_hub import HfApi

from ..canonical import (
    ConfiguredRepoSet,
    DiscoveredFile,
    DiscoveryState,
    HfFileMetadata,
    PinnedRepo,
    canonicalDigest,
)

_FORMAT_KIND_BY_SUFFIX = {
    ".arrow": "ARROW",
    ".bin": "BINARY",
    ".csv": "CSV",
    ".etag": "ETAG",
    ".gif": "IMAGE",
    ".html": "HTML",
    ".jpeg": "IMAGE",
    ".jpg": "IMAGE",
    ".json": "JSON",
    ".jsonl": "JSONL",
    ".md": "MARKDOWN",
    ".npz": "NPZ",
    ".parquet": "PARQUET",
    ".png": "IMAGE",
    ".svg": "IMAGE",
    ".tar": "ARCHIVE",
    ".txt": "TEXT",
    ".webp": "IMAGE",
    ".whl": "WHEEL",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".zip": "ARCHIVE",
}
_CONTROL_NAMES = frozenset({".gitattributes", ".gitignore", "README", "LICENSE"})


def _moduleValue(module: ModuleType | Any, name: str) -> Any:
    if not hasattr(module, name):
        raise ValueError(f"설정 authority 누락: {name}")
    return getattr(module, name)


def discoverConfiguredHfRepositories(configModule: ModuleType | Any | None = None) -> ConfiguredRepoSet:
    """현재 설정에서 HF authority repo 합집합을 계산한다.

    Args:
        configModule: `HF_REPO`, `HF_MEDIA_REPO`, `DATA_RELEASES`를 가진 객체.

    Returns:
        정렬된 repo ID와 authority digest.

    Raises:
        ValueError: 필수 authority가 비었거나 release 선언 형식이 잘못된 경우.

    Example:
        ``discoverConfiguredHfRepositories()``는 현재 설정을 그대로 읽는다.
    """
    if configModule is None:
        from dartlab.core import dataConfig as configModule

    repoIds = {
        str(_moduleValue(configModule, "HF_REPO")).strip(),
        str(_moduleValue(configModule, "HF_MEDIA_REPO")).strip(),
    }
    releases = _moduleValue(configModule, "DATA_RELEASES")
    if not isinstance(releases, dict):
        raise ValueError("DATA_RELEASES는 dict여야 함")
    for releaseId, spec in releases.items():
        if not isinstance(spec, dict):
            raise ValueError(f"release 선언이 dict가 아님: {releaseId}")
        repoId = str(spec.get("repo") or "").strip()
        if repoId:
            repoIds.add(repoId)
    if "" in repoIds:
        raise ValueError("빈 HF authority repo ID")
    ordered = tuple(sorted(repoIds))
    return ConfiguredRepoSet(repoIds=ordered, authorityDigest=canonicalDigest(ordered))


def _lfsOid(sibling: Any) -> str | None:
    lfs = getattr(sibling, "lfs", None)
    if isinstance(lfs, dict):
        return str(lfs.get("sha256") or lfs.get("oid") or "") or None
    return str(getattr(lfs, "sha256", None) or getattr(lfs, "oid", None) or "") or None


def _errorState(exc: Exception) -> tuple[DiscoveryState, str]:
    response = getattr(exc, "response", None)
    statusCode = getattr(response, "status_code", None)
    if statusCode in {401, 403}:
        return DiscoveryState.ACCESS_DENIED, f"HTTP_{statusCode}"
    if statusCode == 404:
        return DiscoveryState.NOT_FOUND, "HTTP_404"
    if statusCode == 429:
        return DiscoveryState.RATE_LIMITED, "HTTP_429"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return DiscoveryState.TIMEOUT, type(exc).__name__
    return DiscoveryState.PARTIAL, type(exc).__name__


def _discoverOne(repoId: str, apiFactory: Callable[[], Any], revision: str | None = None) -> PinnedRepo:
    try:
        api = apiFactory()
        request = {"repo_type": "dataset", "files_metadata": True}
        if revision is not None:
            request["revision"] = revision
        info = api.repo_info(repoId, **request)
        resolvedRevision = str(getattr(info, "sha", "") or "").strip()
        if not resolvedRevision:
            raise ValueError("repo revision 누락")
        if revision is not None and resolvedRevision != revision:
            raise ValueError("repo pinned revision 불일치")
        files = []
        for sibling in getattr(info, "siblings", ()) or ():
            path = str(getattr(sibling, "rfilename", "") or "").strip()
            if not path:
                raise ValueError("HF sibling path 누락")
            rawSize = getattr(sibling, "size", None)
            size = int(rawSize) if rawSize is not None else -1
            lfsSha256 = _lfsOid(sibling)
            oid = str(getattr(sibling, "blob_id", "") or "") or lfsSha256
            files.append(HfFileMetadata(path=path, size=size, oid=oid, lfsSha256=lfsSha256))
        lastModified = getattr(info, "last_modified", None)
        return PinnedRepo(
            repoId=repoId,
            revision=resolvedRevision,
            lastModifiedUtc=lastModified.isoformat()
            if hasattr(lastModified, "isoformat")
            else str(lastModified or "") or None,
            private=bool(getattr(info, "private", False)),
            state=DiscoveryState.PINNED,
            files=tuple(sorted(files, key=lambda item: item.path)),
        )
    except Exception as exc:
        state, errorCode = _errorState(exc)
        return PinnedRepo(
            repoId=repoId,
            revision=None,
            lastModifiedUtc=None,
            private=None,
            state=state,
            files=(),
            errorCode=errorCode,
        )


def discoverHfRepositories(
    configuredRepoSet: ConfiguredRepoSet,
    token: str | None,
    *,
    apiFactory: Callable[[], Any] | None = None,
    maxWorkers: int = 4,
    sourceRevisions: Mapping[str, str] | None = None,
) -> tuple[PinnedRepo, ...]:
    """설정 authority를 병렬 조회하고 각 tree를 한 revision에 고정한다.

    Args:
        configuredRepoSet: 설정에서 계산된 authority 집합.
        token: private dataset을 읽을 HF token. 값은 결과에 기록하지 않는다.
        apiFactory: 테스트용 API factory.
        maxWorkers: 동시 repo metadata 조회 상한.
        sourceRevisions: 지정하면 HEAD 대신 이 exact commit들의 metadata tree를 읽음.

    Returns:
        성공과 실패를 모두 포함하는 repo별 terminal record.

    Raises:
        ValueError: worker 상한이 1보다 작은 경우.

    Example:
        ``discoverHfRepositories(configured, token)``.
    """
    if maxWorkers < 1:
        raise ValueError("maxWorkers는 1 이상이어야 함")
    if sourceRevisions is not None and set(sourceRevisions) != set(configuredRepoSet.repoIds):
        raise ValueError("source revision repo 집합이 configured authority와 다름")
    factory = apiFactory or (lambda: HfApi(token=token))
    workerCount = min(maxWorkers, max(1, len(configuredRepoSet.repoIds)))
    with ThreadPoolExecutor(max_workers=workerCount, thread_name_prefix="universe-census") as executor:
        pinned = tuple(
            executor.map(
                lambda repoId: _discoverOne(
                    repoId,
                    factory,
                    sourceRevisions[repoId] if sourceRevisions is not None else None,
                ),
                configuredRepoSet.repoIds,
            )
        )
    return tuple(sorted(pinned, key=lambda repo: repo.repoId))


def classifyHfPath(path: str) -> tuple[str, DiscoveryState]:
    """HF 경로를 payload를 열지 않고 format terminal state로 분류한다.

    Args:
        path: repo 상대 POSIX 경로.

    Returns:
        format kind와 terminal state.

    Raises:
        ValueError: 절대 경로나 상위 이동 경로인 경우.

    Example:
        ``classifyHfPath("dart/finance/a.parquet")``.
    """
    purePath = PurePosixPath(path)
    if purePath.is_absolute() or ".." in purePath.parts:
        raise ValueError(f"안전하지 않은 HF path: {path}")
    if purePath.name in _CONTROL_NAMES or purePath.name.startswith("README."):
        return "CONTROL", DiscoveryState.CLASSIFIED
    suffix = purePath.suffix.lower()
    if not suffix:
        return "NO_EXTENSION", DiscoveryState.CLASSIFIED
    formatKind = _FORMAT_KIND_BY_SUFFIX.get(suffix)
    if formatKind is None:
        return f"UNSUPPORTED:{suffix}", DiscoveryState.UNSUPPORTED_FORMAT
    return formatKind, DiscoveryState.CLASSIFIED


def enumerateHfTree(repo: PinnedRepo) -> Iterator[DiscoveredFile]:
    """Pinned repo의 metadata tree를 결정론 순서로 변환한다.

    Args:
        repo: `discoverHfRepositories`가 고정한 repo.

    Returns:
        path 정렬된 metadata iterator.

    Raises:
        ValueError: PINNED인데 revision이 없는 경우.

    Example:
        ``tuple(enumerateHfTree(repo))``.
    """
    if repo.state is not DiscoveryState.PINNED:
        return
    if not repo.revision:
        raise ValueError(f"PINNED repo revision 누락: {repo.repoId}")
    for fileMeta in repo.files:
        formatKind, state = classifyHfPath(fileMeta.path)
        yield DiscoveredFile(
            repoId=repo.repoId,
            revision=repo.revision,
            path=fileMeta.path,
            size=fileMeta.size,
            oid=fileMeta.oid,
            formatKind=formatKind,
            state=state,
            lfsSha256=fileMeta.lfsSha256,
        )
