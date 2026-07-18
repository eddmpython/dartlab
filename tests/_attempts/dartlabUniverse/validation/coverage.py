"""U0 coverage ledger와 기존 시스템 무변경 검증."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path

from ..canonical import CoverageLedger, DiscoveryState, SourceDiscovery, canonicalDigest

DEFAULT_PROTECTED_PATHS = (
    "src/dartlab",
    "ui/packages",
    "landing/src",
    "blog",
    "media/catalog.json",
)
_IGNORED_PARTS = frozenset({".pytest_cache", ".svelte-kit", "__pycache__", "build", "dist", "node_modules"})


def _matchesPrefix(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(f"{prefix}/")


def buildCoverageLedger(discovery: SourceDiscovery) -> CoverageLedger:
    """모든 discovery item의 terminal reconciliation과 G0를 계산한다.

    Args:
        discovery: U0 source adapter 전체 결과.

    Returns:
        수치, 실패 코드, canonical digest를 가진 coverage ledger.

    Raises:
        ValueError: configured authority가 비어 있는 경우.

    Example:
        ``buildCoverageLedger(discovery).g0Passed``.
    """
    configured = set(discovery.configuredRepoSet.repoIds)
    if not configured:
        raise ValueError("configured authority repo가 비어 있음")
    pinnedIds = {repo.repoId for repo in discovery.pinnedRepositories}
    accessDenied = tuple(
        sorted(repo.repoId for repo in discovery.pinnedRepositories if repo.state is DiscoveryState.ACCESS_DENIED)
    )
    failedRepos = tuple(
        sorted(repo.repoId for repo in discovery.pinnedRepositories if repo.state is not DiscoveryState.PINNED)
    )
    fileRepoIds = {file.repoId for file in discovery.hfFiles}
    unconfiguredRepoIds = tuple(sorted(fileRepoIds - configured))
    declarationsByRepo = {}
    for declaration in discovery.releaseDeclarations:
        declarationsByRepo.setdefault(declaration.repoId, []).append(declaration)
    declaredOnly = []
    for declaration in discovery.releaseDeclarations:
        if not any(
            file.repoId == declaration.repoId and _matchesPrefix(file.path, declaration.prefix)
            for file in discovery.hfFiles
        ):
            declaredOnly.append(f"{declaration.repoId}:{declaration.prefix}")
    liveOnlyCount = sum(
        1
        for file in discovery.hfFiles
        if not any(
            _matchesPrefix(file.path, declaration.prefix) for declaration in declarationsByRepo.get(file.repoId, ())
        )
    )
    classifiedCount = sum(file.state is DiscoveryState.CLASSIFIED for file in discovery.hfFiles)
    unsupportedCount = sum(file.state is DiscoveryState.UNSUPPORTED_FORMAT for file in discovery.hfFiles)
    fileTerminalCount = classifiedCount + unsupportedCount
    expectedCount = (
        len(configured)
        + len(discovery.hfFiles)
        + len(discovery.releaseDeclarations)
        + len(discovery.capabilityCensus.runtimeIds)
        + len(discovery.capabilityCensus.registryRecords)
        + len(discovery.blogCensus.posts)
        + len(discovery.blogCensus.parseErrors)
        + len(discovery.companionCensus.records)
        + discovery.mediaCensus.objectCount
        + len(discovery.podcastCensus.episodes)
        + len(discovery.podcastCensus.parseErrors)
    )
    terminalCount = (
        len(discovery.pinnedRepositories)
        + fileTerminalCount
        + len(discovery.releaseDeclarations)
        + len(discovery.capabilityCensus.runtimeIds)
        + len(discovery.capabilityCensus.registryRecords)
        + len(discovery.blogCensus.posts)
        + len(discovery.blogCensus.parseErrors)
        + len(discovery.companionCensus.records)
        + discovery.mediaCensus.objectCount
        + len(discovery.podcastCensus.episodes)
        + len(discovery.podcastCensus.parseErrors)
    )
    terminalCoverageRatio = terminalCount / expectedCount if expectedCount else 0.0
    failures = []
    if pinnedIds != configured:
        failures.append("AUTHORITY_SET_MISMATCH")
    if failedRepos:
        failures.append("REPOSITORY_DISCOVERY_FAILED")
    if accessDenied:
        failures.append("PRIVATE_ACCESS_DENIED")
    if unconfiguredRepoIds:
        failures.append("UNCONFIGURED_REPOSITORY")
    if fileTerminalCount != len(discovery.hfFiles):
        failures.append("FILE_CLASSIFICATION_INCOMPLETE")
    if any(file.size < 0 or not file.oid for file in discovery.hfFiles):
        failures.append("FILE_METADATA_INCOMPLETE")
    if discovery.capabilityCensus.errors:
        failures.append("CAPABILITY_ENUMERATION_ERROR")
    if discovery.blogCensus.parseErrors:
        failures.append("BLOG_PARSE_ERROR")
    if discovery.podcastCensus.parseErrors:
        failures.append("PODCAST_PARSE_ERROR")
    if discovery.mediaCensus.errors:
        failures.append("MEDIA_CATALOG_ERROR")
    if discovery.mediaCensus.missingObjectPaths:
        failures.append("MEDIA_OBJECT_MISSING")
    if discovery.mediaCensus.unregisteredHfObjectPaths:
        failures.append("MEDIA_OBJECT_UNREGISTERED")
    if discovery.mediaCensus.brokenBlogRefs:
        failures.append("MEDIA_BROKEN_REFERENCE")
    if discovery.payloadBodiesRead:
        failures.append("HF_PAYLOAD_BODY_READ")
    if terminalCoverageRatio != 1.0:
        failures.append("TERMINAL_COVERAGE_INCOMPLETE")
    orderedFailures = tuple(sorted(set(failures)))
    base = {
        "configuredRepoCount": len(configured),
        "pinnedRepoCount": sum(repo.state is DiscoveryState.PINNED for repo in discovery.pinnedRepositories),
        "accessDeniedRepoIds": accessDenied,
        "discoveredFileCount": len(discovery.hfFiles),
        "discoveredByteCount": sum(max(0, file.size) for file in discovery.hfFiles),
        "classifiedFileCount": classifiedCount,
        "unsupportedFormatCount": unsupportedCount,
        "unconfiguredRepoIds": unconfiguredRepoIds,
        "declaredOnlyPrefixes": tuple(sorted(declaredOnly)),
        "liveOnlyPathCount": liveOnlyCount,
        "runtimeCapabilityCount": len(discovery.capabilityCensus.runtimeIds),
        "registryRecordCount": len(discovery.capabilityCensus.registryRecords),
        "blogPostCount": len(discovery.blogCensus.posts),
        "blogParseErrorCount": len(discovery.blogCensus.parseErrors),
        "companionCount": len(discovery.companionCensus.records),
        "unknownCompanionCount": len(discovery.companionCensus.unknownPaths),
        "mediaObjectCount": discovery.mediaCensus.objectCount,
        "mediaMissingObjectCount": len(discovery.mediaCensus.missingObjectPaths),
        "mediaUnregisteredObjectCount": len(discovery.mediaCensus.unregisteredHfObjectPaths),
        "mediaBrokenRefCount": len(discovery.mediaCensus.brokenBlogRefs),
        "mediaUnreferencedObjectCount": len(discovery.mediaCensus.unreferencedObjectDigests),
        "podcastCount": len(discovery.podcastCensus.episodes),
        "terminalCoverageRatio": terminalCoverageRatio,
        "g0Passed": not orderedFailures,
        "failureCodes": orderedFailures,
    }
    return CoverageLedger(**base, digest=canonicalDigest(base))


def _iterProtectedFiles(repoRoot: Path, relativeRoots: Iterable[str]) -> Iterable[Path]:
    for relativeRoot in relativeRoots:
        path = (repoRoot / relativeRoot).resolve()
        if not path.exists():
            continue
        candidates = (path,) if path.is_file() else path.rglob("*")
        for candidate in candidates:
            if not candidate.is_file() or candidate.is_symlink():
                continue
            relative = candidate.relative_to(repoRoot.resolve())
            if any(part in _IGNORED_PARTS for part in relative.parts):
                continue
            yield candidate


def captureProtectedPathDigests(
    repoRoot: Path,
    relativeRoots: Iterable[str] = DEFAULT_PROTECTED_PATHS,
) -> dict[str, str]:
    """기존 시스템 파일의 byte digest snapshot을 만든다.

    Args:
        repoRoot: repository root.
        relativeRoots: 보호할 상대 경로.

    Returns:
        상대 POSIX path에서 SHA-256으로 가는 정렬 dict.

    Raises:
        ValueError: repo root가 directory가 아닌 경우.

    Example:
        ``captureProtectedPathDigests(repoRoot)``.
    """
    repoRoot = repoRoot.resolve()
    if not repoRoot.is_dir():
        raise ValueError(f"repository root가 아님: {repoRoot}")
    records = {
        path.relative_to(repoRoot).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in _iterProtectedFiles(repoRoot, relativeRoots)
    }
    return dict(sorted(records.items()))


def assertProtectedPathsUnchanged(before: Mapping[str, str], after: Mapping[str, str]) -> None:
    """보호 path의 추가, 삭제, byte 변경을 모두 차단한다.

    Args:
        before: 작업 전 digest map.
        after: 작업 후 digest map.

    Returns:
        변경이 없으면 None.

    Raises:
        AssertionError: 추가, 삭제 또는 변경 path가 있을 때.

    Example:
        ``assertProtectedPathsUnchanged(snapshot, snapshot)``.
    """
    beforeKeys = set(before)
    afterKeys = set(after)
    added = sorted(afterKeys - beforeKeys)
    removed = sorted(beforeKeys - afterKeys)
    changed = sorted(key for key in beforeKeys & afterKeys if before[key] != after[key])
    if added or removed or changed:
        raise AssertionError({"added": added, "removed": removed, "changed": changed})
