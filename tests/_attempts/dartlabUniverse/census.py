"""Universe U0 source adapter를 하나의 결정론적 metadata census로 조합한다."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

from dotenv import load_dotenv

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from tests._attempts.dartlabUniverse.canonical import (
        CensusResult,
        SourceDiscovery,
        canonicalDigest,
        canonicalJson,
    )
    from tests._attempts.dartlabUniverse.sources.blogSource import enumerateBlog
    from tests._attempts.dartlabUniverse.sources.capabilitySource import enumerateCapabilities
    from tests._attempts.dartlabUniverse.sources.contentCompanionSource import enumerateContentCompanions
    from tests._attempts.dartlabUniverse.sources.hfSource import (
        discoverConfiguredHfRepositories,
        discoverHfRepositories,
        enumerateHfTree,
    )
    from tests._attempts.dartlabUniverse.sources.mediaSource import reconcileMedia
    from tests._attempts.dartlabUniverse.sources.podcastSource import enumeratePodcasts
    from tests._attempts.dartlabUniverse.sources.releaseOverlay import readReleaseOverlay
    from tests._attempts.dartlabUniverse.validation.coverage import (
        assertProtectedPathsUnchanged,
        buildCoverageLedger,
        captureProtectedPathDigests,
    )
else:
    from .canonical import CensusResult, SourceDiscovery, canonicalDigest, canonicalJson
    from .sources.blogSource import enumerateBlog
    from .sources.capabilitySource import enumerateCapabilities
    from .sources.contentCompanionSource import enumerateContentCompanions
    from .sources.hfSource import discoverConfiguredHfRepositories, discoverHfRepositories, enumerateHfTree
    from .sources.mediaSource import reconcileMedia
    from .sources.podcastSource import enumeratePodcasts
    from .sources.releaseOverlay import readReleaseOverlay
    from .validation.coverage import (
        assertProtectedPathsUnchanged,
        buildCoverageLedger,
        captureProtectedPathDigests,
    )


def defaultRepoRoot() -> Path:
    """현재 attempt package에서 repository root를 계산한다.

    Args:
        없음.

    Returns:
        repository root absolute path.

    Raises:
        RuntimeError: `CLAUDE.md`가 없는 잘못된 위치인 경우.

    Example:
        ``defaultRepoRoot()``.
    """
    root = Path(__file__).resolve().parents[3]
    if not (root / "CLAUDE.md").is_file():
        raise RuntimeError(f"repository root 탐지 실패: {root}")
    return root


def _resolveToken(repoRoot: Path, token: str | None) -> str | None:
    if token:
        return token
    load_dotenv(dotenv_path=repoRoot / ".env", override=False)
    return os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")


def runFullCensus(
    repoRoot: Path | None = None,
    token: str | None = None,
    *,
    configModule: ModuleType | Any | None = None,
    apiFactory: Callable[[], Any] | None = None,
    maxWorkers: int = 4,
    protectExisting: bool = True,
    sourceRevisions: tuple[tuple[str, str], ...] | None = None,
) -> CensusResult:
    """HF, capability, blog, companion, media, podcast metadata를 전수 조사한다.

    Args:
        repoRoot: repository root. 생략하면 attempt 위치에서 계산.
        token: private HF dataset token. 결과와 log에는 기록하지 않는다.
        configModule: 테스트용 설정 객체.
        apiFactory: 테스트용 HF API factory.
        maxWorkers: repo metadata 병렬 조회 상한.
        protectExisting: 기존 시스템 byte digest 전후 검증 여부.
        sourceRevisions: 지정하면 HEAD가 아니라 검증된 exact HF commit 집합.

    Returns:
        machine-readable `CensusResult`.

    Raises:
        AssertionError: 기존 보호 path가 census 중 바뀐 경우.

    Example:
        ``result = runFullCensus()``.
    """
    root = (repoRoot or defaultRepoRoot()).resolve()
    before = captureProtectedPathDigests(root) if protectExisting else None
    configured = discoverConfiguredHfRepositories(configModule)
    pinned = discoverHfRepositories(
        configured,
        _resolveToken(root, token),
        apiFactory=apiFactory,
        maxWorkers=maxWorkers,
        sourceRevisions=dict(sourceRevisions) if sourceRevisions is not None else None,
    )
    hfFiles = tuple(file for repo in pinned for file in enumerateHfTree(repo))
    releases = readReleaseOverlay(configModule)
    capabilities = enumerateCapabilities()
    blog = enumerateBlog(root / "blog")
    companions = enumerateContentCompanions(root / "blog")
    podcasts = enumeratePodcasts(root / "blog")
    if configModule is None:
        from dartlab.core import dataConfig as activeConfig
    else:
        activeConfig = configModule
    mediaRepoId = str(getattr(activeConfig, "HF_MEDIA_REPO"))
    mediaFiles = tuple(file for file in hfFiles if file.repoId == mediaRepoId)
    blogRefs = tuple(ref for post in blog.posts for ref in post.imageRefs)
    media = reconcileMedia(root / "media" / "catalog.json", mediaFiles, blogRefs)
    discovery = SourceDiscovery(
        configuredRepoSet=configured,
        pinnedRepositories=pinned,
        hfFiles=hfFiles,
        releaseDeclarations=releases,
        capabilityCensus=capabilities,
        blogCensus=blog,
        companionCensus=companions,
        mediaCensus=media,
        podcastCensus=podcasts,
        networkOperations=tuple(f"HF_REPO_INFO_METADATA:{repo.repoId}" for repo in pinned),
        payloadBodiesRead=sum(file.payloadBodyRead for file in hfFiles),
    )
    coverage = buildCoverageLedger(discovery)
    snapshotDigest = canonicalDigest(discovery)
    result = CensusResult(
        observedAtUtc=datetime.now(timezone.utc).isoformat(),
        discovery=discovery,
        coverage=coverage,
        snapshotDigest=snapshotDigest,
    )
    if before is not None:
        after = captureProtectedPathDigests(root)
        assertProtectedPathsUnchanged(before, after)
    return result


def buildArgumentParser() -> argparse.ArgumentParser:
    """U0 machine census 단일 명령의 argument parser를 만든다."""
    parser = argparse.ArgumentParser(description="DartLab Universe U0 metadata census")
    parser.add_argument("--all", dest="allSources", action="store_true", required=True)
    parser.add_argument("--strict", action="store_true", help="G0 실패 시 종료 코드 2 반환")
    parser.add_argument("--format", choices=("json",), default="json")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    censusRunner: Callable[[], CensusResult] | None = None,
) -> int:
    """전체 source census를 실행하고 canonical JSON만 stdout에 기록한다.

    Args:
        argv: 테스트 또는 CLI argument. 생략하면 process argument를 쓴다.
        censusRunner: 테스트용 무인자 census callable.

    Returns:
        성공은 0, strict G0 실패는 2.

    Raises:
        Census adapter 예외는 숨기지 않고 호출자에게 전달한다.

    Example:
        ``main(["--all", "--strict", "--format", "json"])``.
    """
    arguments = buildArgumentParser().parse_args(argv)
    runner = censusRunner or (lambda: runFullCensus(protectExisting=False))
    result = runner()
    sys.stdout.buffer.write(canonicalJson(result) + b"\n")
    sys.stdout.buffer.flush()
    if arguments.strict and not result.coverage.g0Passed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
