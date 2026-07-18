"""Universe U0 source census의 authority, 결정론, live metadata 경계를 검증한다."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest
from dotenv import load_dotenv

from tests._attempts.dartlabUniverse.benchmark import runMetadataCensusBenchmark
from tests._attempts.dartlabUniverse.canonical import DiscoveryState, canonicalJson
from tests._attempts.dartlabUniverse.census import defaultRepoRoot, runFullCensus
from tests._attempts.dartlabUniverse.census import main as censusMain
from tests._attempts.dartlabUniverse.sources.blogSource import enumerateBlog
from tests._attempts.dartlabUniverse.sources.capabilitySource import enumerateCapabilities
from tests._attempts.dartlabUniverse.sources.contentCompanionSource import enumerateContentCompanions
from tests._attempts.dartlabUniverse.sources.hfSource import (
    discoverConfiguredHfRepositories,
    discoverHfRepositories,
    enumerateHfTree,
)
from tests._attempts.dartlabUniverse.sources.podcastSource import enumeratePodcasts
from tests._attempts.dartlabUniverse.testSupport import fakeConfig, fakeHfApi


def testConfiguredRepositorySetIsDynamicUnion():
    base = discoverConfiguredHfRepositories(fakeConfig())
    expanded = discoverConfiguredHfRepositories(fakeConfig(extraRepo="fixture/fifth"))

    assert base.repoIds == ("fixture/data", "fixture/media", "fixture/private")
    assert set(expanded.repoIds) == {*base.repoIds, "fixture/fifth"}
    assert base.authorityDigest != expanded.authorityDigest


def testHfDiscoveryPinsRevisionAndReadsMetadataOnly():
    repoRoot = defaultRepoRoot()
    api = fakeHfApi(repoRoot)
    configured = discoverConfiguredHfRepositories(fakeConfig())

    pinned = discoverHfRepositories(configured, "secret-not-recorded", apiFactory=lambda: api)
    files = tuple(file for repo in pinned for file in enumerateHfTree(repo))

    assert {repo.repoId for repo in pinned} == set(configured.repoIds)
    assert all(repo.state is DiscoveryState.PINNED and repo.revision for repo in pinned)
    assert all(call[1:] == ("dataset", True) for call in api.calls)
    assert len(api.calls) == len(configured.repoIds)
    assert all(file.payloadBodyRead is False for file in files)
    unknown = next(file for file in files if file.path.endswith(".mystery"))
    assert unknown.state is DiscoveryState.UNSUPPORTED_FORMAT


def testSameRevisionProducesSameSnapshotDigest():
    repoRoot = defaultRepoRoot()
    config = fakeConfig()
    first = runFullCensus(
        repoRoot,
        configModule=config,
        apiFactory=lambda: fakeHfApi(repoRoot),
        protectExisting=False,
    )
    second = runFullCensus(
        repoRoot,
        configModule=config,
        apiFactory=lambda: fakeHfApi(repoRoot),
        protectExisting=False,
    )

    assert first.snapshotDigest == second.snapshotDigest
    assert first.coverage.digest == second.coverage.digest
    assert first.discovery.payloadBodiesRead == 0
    assert first.coverage.g0Passed


def testCapabilityRuntimeAndSevenRegistriesAreEnumerated():
    census = enumerateCapabilities()

    assert census.runtimeIds
    assert not census.errors
    assert {record.owner for record in census.registryRecords} == {
        "analysis",
        "credit",
        "industry",
        "macro",
        "quant",
        "scan",
        "story",
    }
    assert len(census.registryRecords) == len({record.recordId for record in census.registryRecords})


def testBlogCompanionAndPodcastTreesAreFullyClassified():
    blogRoot = defaultRepoRoot() / "blog"
    blog = enumerateBlog(blogRoot)
    companions = enumerateContentCompanions(blogRoot)
    podcasts = enumeratePodcasts(blogRoot)

    assert blog.posts
    assert not blog.parseErrors
    assert all(post.contentDigest and post.frontmatterDigest for post in blog.posts)
    assert all(record.kind for record in companions.records)
    assert set(companions.unknownPaths) == {
        record.relativePath for record in companions.records if record.kind == "UNCLASSIFIED_COMPANION"
    }
    assert podcasts.episodes
    assert not podcasts.parseErrors


def testCensusCliEmitsCanonicalJsonAndStrictFailure(capfdbinary):
    repoRoot = defaultRepoRoot()
    result = runFullCensus(
        repoRoot,
        configModule=fakeConfig(),
        apiFactory=lambda: fakeHfApi(repoRoot),
        protectExisting=False,
    )

    assert censusMain(["--all", "--strict", "--format", "json"], censusRunner=lambda: result) == 0
    decoded = json.loads(capfdbinary.readouterr().out)
    assert decoded["snapshotDigest"] == result.snapshotDigest

    failedCoverage = replace(result.coverage, g0Passed=False, failureCodes=("FIXTURE_FAILURE",))
    failedResult = replace(result, coverage=failedCoverage)
    assert censusMain(["--all", "--strict"], censusRunner=lambda: failedResult) == 2
    capfdbinary.readouterr()


@pytest.mark.network
@pytest.mark.slow
def testLiveMetadataCensusMatchesPinnedTreesAndWritesMachineArtifact(tmp_path: Path):
    repoRoot = defaultRepoRoot()
    load_dotenv(dotenv_path=repoRoot / ".env", override=False)
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    if not token:
        pytest.skip("private HF authority token 없음")

    result, report = runMetadataCensusBenchmark(
        lambda: runFullCensus(repoRoot, token=token, protectExisting=False),
        targetSeconds=60.0,
    )
    outputPath = tmp_path / "universe-census.json"
    outputPath.write_bytes(canonicalJson(result))
    decoded = json.loads(outputPath.read_text(encoding="utf-8"))

    assert result.coverage.g0Passed, result.coverage.failureCodes
    assert result.coverage.discoveredFileCount == sum(len(repo.files) for repo in result.discovery.pinnedRepositories)
    assert result.coverage.discoveredByteCount == sum(file.size for file in result.discovery.hfFiles)
    assert report.payloadBodiesRead == 0
    assert report.targetMet, report
    assert decoded["snapshotDigest"] == result.snapshotDigest
    assert outputPath.parent == tmp_path
