"""Universe U0 coverage ledger의 fail-closed mutation을 검증한다."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tests._attempts.dartlabUniverse.canonical import DiscoveredFile, DiscoveryState
from tests._attempts.dartlabUniverse.census import defaultRepoRoot, runFullCensus
from tests._attempts.dartlabUniverse.sources.hfSource import (
    discoverConfiguredHfRepositories,
    discoverHfRepositories,
)
from tests._attempts.dartlabUniverse.sources.mediaSource import reconcileMedia
from tests._attempts.dartlabUniverse.testSupport import FakeHfApi, FakeHttpError, fakeConfig, fakeHfApi
from tests._attempts.dartlabUniverse.validation.coverage import buildCoverageLedger


def _fakeResult():
    repoRoot = defaultRepoRoot()
    return runFullCensus(
        repoRoot,
        configModule=fakeConfig(),
        apiFactory=lambda: fakeHfApi(repoRoot),
        protectExisting=False,
    )


def testUnconfiguredRepositoryInjectionFailsG0():
    result = _fakeResult()
    injected = DiscoveredFile(
        repoId="attacker/repo",
        revision="f" * 40,
        path="data.json",
        size=1,
        oid="e" * 64,
        formatKind="JSON",
        state=DiscoveryState.CLASSIFIED,
    )
    discovery = replace(result.discovery, hfFiles=(*result.discovery.hfFiles, injected))
    ledger = buildCoverageLedger(discovery)

    assert not ledger.g0Passed
    assert ledger.unconfiguredRepoIds == ("attacker/repo",)
    assert "UNCONFIGURED_REPOSITORY" in ledger.failureCodes


def testFifthConfiguredRepositoryMissingFailsG0():
    repoRoot = defaultRepoRoot()
    config = fakeConfig(extraRepo="fixture/fifth")
    api = fakeHfApi(repoRoot)
    configured = discoverConfiguredHfRepositories(config)
    pinned = discoverHfRepositories(configured, "token", apiFactory=lambda: api)

    assert any(repo.repoId == "fixture/fifth" and repo.state is not DiscoveryState.PINNED for repo in pinned)


def testPrivateAccessDeniedIsTerminalAndFailsG0():
    repoRoot = defaultRepoRoot()
    baseApi = fakeHfApi(repoRoot)
    api = FakeHfApi(baseApi.repositories, failures={"fixture/private": FakeHttpError(403)})
    result = runFullCensus(
        repoRoot,
        configModule=fakeConfig(),
        apiFactory=lambda: api,
        protectExisting=False,
    )

    assert not result.coverage.g0Passed
    assert result.coverage.accessDeniedRepoIds == ("fixture/private",)
    assert "PRIVATE_ACCESS_DENIED" in result.coverage.failureCodes


def testUnsupportedFormatIsExplicitTerminalNotCoverageLoss():
    result = _fakeResult()

    assert result.coverage.unsupportedFormatCount == 1
    assert result.coverage.terminalCoverageRatio == 1.0
    assert result.coverage.g0Passed


def testReleaseOverlaySeparatesDeclaredOnlyAndLiveOnly():
    result = _fakeResult()

    assert result.coverage.declaredOnlyPrefixes == ()
    assert result.coverage.liveOnlyPathCount >= 2


def testMediaReconciliationFindsMissingUnregisteredAndBroken(tmp_path: Path):
    catalog = {
        "version": 1,
        "repo": "fixture/media",
        "objectPrefix": "objects/sha256",
        "objects": {
            "a" * 64: {"bytes": 10, "path": f"objects/sha256/aa/{'a' * 64}.webp"},
            "b" * 64: {"bytes": 20, "path": f"objects/sha256/bb/{'b' * 64}.webp"},
        },
        "files": {"blog/a.webp": "a" * 64},
        "posts": {"post": {"og": "blog/a.webp"}},
        "collections": {},
        "manifests": {},
    }
    live = (
        DiscoveredFile(
            repoId="fixture/media",
            revision="f" * 40,
            path=f"objects/sha256/aa/{'a' * 64}.webp",
            size=10,
            oid="1" * 64,
            formatKind="IMAGE",
            state=DiscoveryState.CLASSIFIED,
        ),
        DiscoveredFile(
            repoId="fixture/media",
            revision="f" * 40,
            path=f"objects/sha256/cc/{'c' * 64}.webp",
            size=30,
            oid="2" * 64,
            formatKind="IMAGE",
            state=DiscoveryState.CLASSIFIED,
        ),
    )
    census = reconcileMedia(catalog, live, ("blog/a.webp", f"objects/sha256/bb/{'b' * 64}.webp"))

    assert census.missingObjectPaths == (f"objects/sha256/bb/{'b' * 64}.webp",)
    assert census.unregisteredHfObjectPaths == (f"objects/sha256/cc/{'c' * 64}.webp",)
    assert census.brokenBlogRefs == (f"objects/sha256/bb/{'b' * 64}.webp",)

    result = _fakeResult()
    ledger = buildCoverageLedger(replace(result.discovery, mediaCensus=census))
    assert not ledger.g0Passed
    assert {
        "MEDIA_OBJECT_MISSING",
        "MEDIA_OBJECT_UNREGISTERED",
        "MEDIA_BROKEN_REFERENCE",
    } <= set(ledger.failureCodes)
