"""Live authority의 U3 C2 descriptor를 resume 가능한 방식으로 전수 검증한다."""

from __future__ import annotations

import argparse
import gc
import os
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import HfApi

from .canonical import canonicalDigest, canonicalJson
from .catalog.compiler import compileCatalog
from .catalog.descriptorCheckpoint import DescriptorCheckpointStore, descriptorPolicyDigest
from .catalog.descriptorCrawler import (
    DescriptorPolicy,
    HfRangeReaderFactory,
    ResourceDescriptor,
    crawlCatalogDescriptors,
)
from .catalog.recoveryStore import ResourceRecoveryStore, defaultRecoveryRoot
from .census import defaultRepoRoot, runFullCensus
from .validation.c2 import validateC2
from .validation.runtimeEnvironment import memoryEnvironment, runtimeEnvironment

CHECKPOINT_RESUME_P99_SECONDS = 15.0


class PinnedRevisionValidationError(RuntimeError):
    """Snapshot에 결박한 HF commit 자체를 다시 해석할 수 없다."""


@dataclass(frozen=True, slots=True)
class PinnedRevision:
    repoId: str
    revision: str


class SourceFreshnessMonitor:
    """고정 snapshot과 별개로 upstream HEAD 전진 여부를 기록한다."""

    def __init__(self, probe: Callable[[], tuple[str, ...]]):
        self.probe = probe
        self.checkCount = 0
        self.headAdvanced = False
        self.advanceEvents: list[str] = []
        self.probeFailureCodes: list[str] = []

    def check(self) -> bool:
        self.checkCount += 1
        try:
            events = self.probe()
        except Exception as exc:
            code = type(exc).__name__
            if code not in self.probeFailureCodes:
                self.probeFailureCodes.append(code)
            return False
        for event in events:
            if event not in self.advanceEvents:
                self.advanceEvents.append(event)
        self.headAdvanced = self.headAdvanced or bool(events)
        return not events


def assertPinnedHfRevisions(
    pinnedRepositories: tuple[object, ...],
    *,
    token: str | None,
    apiFactory=HfApi,
) -> None:
    """Snapshot에 결박한 commit이 같은 SHA로 계속 해석되는지 검증한다."""
    api = apiFactory(token=token)
    for repository in pinnedRepositories:
        repoId = str(getattr(repository, "repoId"))
        expectedRevision = str(getattr(repository, "revision") or "")
        if not expectedRevision:
            raise PinnedRevisionValidationError(f"HF pinned revision missing: {repoId}")
        info = api.repo_info(
            repoId,
            revision=expectedRevision,
            repo_type="dataset",
            files_metadata=False,
        )
        resolvedRevision = str(getattr(info, "sha", "") or "")
        if resolvedRevision != expectedRevision:
            raise PinnedRevisionValidationError(
                f"HF pinned revision mismatch: {repoId} expected={expectedRevision} resolved={resolvedRevision}"
            )


def probeHfHeadAdvances(
    pinnedRepositories: tuple[object, ...],
    *,
    token: str | None,
    apiFactory=HfApi,
) -> tuple[str, ...]:
    """상류 HEAD 전진을 snapshot 무결성과 분리한 freshness event로 반환한다."""
    api = apiFactory(token=token)
    events = []
    for repository in pinnedRepositories:
        repoId = str(getattr(repository, "repoId"))
        snapshotRevision = str(getattr(repository, "revision") or "")
        info = api.repo_info(repoId, repo_type="dataset", files_metadata=False)
        currentRevision = str(getattr(info, "sha", "") or "")
        if not currentRevision:
            raise RuntimeError(f"HF current revision missing: {repoId}")
        if currentRevision != snapshotRevision:
            events.append(f"HF head advanced: {repoId} snapshot={snapshotRevision} current={currentRevision}")
    return tuple(events)


def defaultCheckpointPath() -> Path:
    """Repo 밖 local control-plane의 기본 C2 checkpoint 위치를 반환한다."""
    root = Path(os.getenv("LOCALAPPDATA") or (Path.home() / ".dartlab"))
    return root / "DartLab" / "universe" / "control" / "descriptor-v1.sqlite"


def runLiveC2(
    *,
    checkpointPath: Path,
    recoveryRoot: Path,
    maxWorkers: int,
    maxRequestsPerSecond: float,
    progressEvery: int,
    driftCheckEvery: int,
) -> tuple[object, dict[str, object]]:
    """G0, catalog, resume crawl, C2 gate를 실행하고 machine report를 반환한다."""
    repoRoot = defaultRepoRoot()
    load_dotenv(repoRoot / ".env", override=False)
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    overallStarted = time.perf_counter()
    census = runFullCensus(repoRoot, token=token, protectExisting=False)
    if not census.coverage.g0Passed:
        raise RuntimeError(f"G0 failure: {census.coverage.failureCodes}")
    pinnedRevisions = tuple(
        PinnedRevision(item.repoId, item.revision or "") for item in census.discovery.pinnedRepositories
    )
    sourceRevisions = tuple((item.repoId, item.revision) for item in pinnedRevisions)
    hfRepoFileCounts = tuple((item.repoId, len(item.files)) for item in census.discovery.pinnedRepositories)
    allowedRepoIds = frozenset(census.discovery.configuredRepoSet.repoIds)
    observedAtUtc = census.observedAtUtc
    u0SnapshotDigest = census.snapshotDigest
    hfCandidateCount = len(census.discovery.hfFiles)
    hfDiscoveredByteCount = census.coverage.discoveredByteCount
    pinnedRevisionFailureCodes = []
    try:
        assertPinnedHfRevisions(pinnedRevisions, token=token)
    except Exception as exc:
        pinnedRevisionFailureCodes.append(type(exc).__name__)
    freshnessMonitor = SourceFreshnessMonitor(lambda: probeHfHeadAdvances(pinnedRevisions, token=token))
    freshnessMonitor.check()
    catalog = compileCatalog(census)
    catalogDigest = catalog.digest
    catalogResourceCount = len(catalog.resources)
    hfResources = tuple(item for item in catalog.resources if item.resourceKind == "HF_FILE")
    catalog = replace(catalog, resources=hfResources, objects=(), evidence=())
    resourcesByVersion = {item.resourceVersionId: item for item in hfResources}
    del census, hfResources
    gc.collect()
    policy = DescriptorPolicy(maxRequestsPerSecond=maxRequestsPerSecond)
    descriptorStarted = time.perf_counter()
    checkpointBuffer: list[ResourceDescriptor] = []
    completed = 0
    resumedCount = 0
    resumedContentDescriptorCount = 0
    checkpointLoadDurationSeconds = 0.0
    checkpointResumeDurationSeconds = 0.0
    exactReceiptCount = 0
    liveExactReceiptCount = 0
    contentCacheEntryCount = 0
    terminalAttemptCount = 0
    lastFlush = time.monotonic()

    checkpointResumeStarted = time.perf_counter()
    with DescriptorCheckpointStore(checkpointPath) as checkpoint:
        leaseOwner = checkpoint.acquireLease()
        heartbeat = checkpoint.startLeaseHeartbeat(leaseOwner)
        try:
            checkpointLoadStarted = time.perf_counter()
            resumed = checkpoint.load(catalog.resources, policy)
            checkpointLoadDurationSeconds = time.perf_counter() - checkpointLoadStarted
            resumedCount = len(resumed)
            resumedContentDescriptorCount = checkpoint.lastLoadReusedCount
            completed = resumedCount
            checkpointResumeDurationSeconds = time.perf_counter() - checkpointResumeStarted

            def flush() -> None:
                nonlocal lastFlush
                if checkpointBuffer:
                    checkpoint.putMany(
                        tuple(checkpointBuffer),
                        policy,
                        resourcesByVersion=resourcesByVersion,
                    )
                    checkpointBuffer.clear()
                heartbeat.check()
                checkpoint.renewLease(leaseOwner)
                lastFlush = time.monotonic()

            def onDescriptor(descriptor: ResourceDescriptor) -> None:
                nonlocal completed
                if descriptor.errorCode not in {"RATE_LIMITED", "SOURCE_HTTP_ERROR", "TIMEOUT"}:
                    checkpointBuffer.append(descriptor)
                completed += 1
                if len(checkpointBuffer) >= 50 or time.monotonic() - lastFlush >= 10.0:
                    flush()
                if completed % progressEvery == 0:
                    elapsed = max(0.001, time.perf_counter() - descriptorStarted)
                    newlyCompleted = completed - resumedCount
                    print(
                        f"C2_PROGRESS completed={completed} total={hfCandidateCount} "
                        f"rate={newlyCompleted / elapsed:.2f}/s resumed={resumedCount}",
                        file=sys.stderr,
                        flush=True,
                    )
                if completed % driftCheckEvery == 0 and not freshnessMonitor.headAdvanced:
                    freshnessMonitor.check()

            try:
                with HfRangeReaderFactory(
                    token=token,
                    allowedRepoIds=allowedRepoIds,
                    policy=policy,
                ) as readerFactory:
                    descriptors = crawlCatalogDescriptors(
                        catalog.resources,
                        readerFactory,
                        policy=policy,
                        maxWorkers=maxWorkers,
                        resumeDescriptors=resumed,
                        onDescriptor=onDescriptor,
                    )
            finally:
                flush()
            freshnessMonitor.check()
            exactReceiptCount, contentCacheEntryCount = checkpoint.receiptCounts(policy)
            liveExactReceiptCount = checkpoint.liveExactReceiptCount(catalog.resources, policy)
            terminalAttemptCount = checkpoint.terminalAttemptCount(policy)
        finally:
            try:
                heartbeat.close()
            finally:
                checkpoint.releaseLease(leaseOwner)
    with ResourceRecoveryStore(recoveryRoot) as recoveryStore:
        recoveries = recoveryStore.load(catalog, descriptors)
        recoveryReceiptCount = recoveryStore.receiptCount()
        staleRecoveryReceiptCount = recoveryStore.staleReceiptCount
        report = validateC2(
            catalog,
            descriptors,
            recoveries=recoveries,
            recoveryCas=recoveryStore.cas,
        )
    runtimeFailureCodes = set(report.failureCodes)
    if pinnedRevisionFailureCodes:
        runtimeFailureCodes.add("PINNED_REVISION_VALIDATION_FAILED")
    if checkpointResumeDurationSeconds > CHECKPOINT_RESUME_P99_SECONDS:
        runtimeFailureCodes.add("CHECKPOINT_RESUME_SLO_EXCEEDED")
    if runtimeFailureCodes != set(report.failureCodes):
        report = replace(
            report,
            passed=False,
            failureCodes=tuple(sorted(runtimeFailureCodes)),
            digest="",
        )
        report = replace(report, digest=canonicalDigest(report))
    prunedReceiptCount = 0
    if report.passed:
        with DescriptorCheckpointStore(checkpointPath) as checkpoint:
            prunedReceiptCount = checkpoint.pruneObsolete(catalog.resources, policy)
            exactReceiptCount, contentCacheEntryCount = checkpoint.receiptCounts(policy)
            liveExactReceiptCount = checkpoint.liveExactReceiptCount(catalog.resources, policy)
            terminalAttemptCount = checkpoint.terminalAttemptCount(policy)
    metrics = {
        "schemaVersion": "du-u3-c2-live-v5",
        "observedAtUtc": observedAtUtc,
        "sourceRevisions": sourceRevisions,
        "hfRepoFileCounts": hfRepoFileCounts,
        "hfDiscoveredByteCount": hfDiscoveredByteCount,
        "u0SnapshotDigest": u0SnapshotDigest,
        "catalogDigest": catalogDigest,
        "catalogResourceCount": catalogResourceCount,
        "hfCandidateCount": hfCandidateCount,
        "descriptorPolicyDigest": descriptorPolicyDigest(policy),
        "descriptorPolicy": asdict(policy),
        "maxWorkers": maxWorkers,
        "resumedDescriptorCount": resumedCount,
        "resumedExactDescriptorCount": resumedCount - resumedContentDescriptorCount,
        "resumedContentDescriptorCount": resumedContentDescriptorCount,
        "checkpointLoadDurationSeconds": round(checkpointLoadDurationSeconds, 6),
        "checkpointResumeDurationSeconds": round(checkpointResumeDurationSeconds, 6),
        "checkpointResumeP99BudgetSeconds": CHECKPOINT_RESUME_P99_SECONDS,
        "newDescriptorCount": hfCandidateCount - resumedCount,
        "durationSeconds": round(time.perf_counter() - overallStarted, 6),
        "descriptorCrawlDurationSeconds": round(time.perf_counter() - descriptorStarted, 6),
        "runtimeEnvironment": runtimeEnvironment(
            cacheProfile="LOCAL_DESCRIPTOR_CHECKPOINT_MIXED",
            networkProfile="LIVE_HF_PINNED_RANGE",
        ),
        "processPeakRssBytes": memoryEnvironment()[1],
        "checkpointKind": "LOCAL_CONTROL_PLANE",
        "checkpointExactReceiptCount": exactReceiptCount,
        "liveExactReceiptCount": liveExactReceiptCount,
        "contentCacheEntryCount": contentCacheEntryCount,
        "terminalAttemptCount": terminalAttemptCount,
        "recoveryReceiptCount": recoveryReceiptCount,
        "activeRecoveryCount": len(recoveries),
        "staleRecoveryReceiptCount": staleRecoveryReceiptCount,
        "recoverySetDigest": canonicalDigest(tuple(sorted(item.digest for item in recoveries))),
        "prunedReceiptCount": prunedReceiptCount,
        "pinnedRevisionValidationPassed": not pinnedRevisionFailureCodes,
        "pinnedRevisionFailureCodes": tuple(pinnedRevisionFailureCodes),
        "sourceFreshnessStatus": (
            "UNKNOWN"
            if freshnessMonitor.probeFailureCodes
            else "ADVANCED"
            if freshnessMonitor.headAdvanced
            else "CURRENT"
        ),
        "sourceFreshnessCheckCount": freshnessMonitor.checkCount,
        "sourceHeadAdvanceDetected": freshnessMonitor.headAdvanced,
        "sourceHeadAdvanceEvents": tuple(freshnessMonitor.advanceEvents),
        "sourceHeadProbeFailureCodes": tuple(freshnessMonitor.probeFailureCodes),
        "c2": asdict(report),
    }
    return report, metrics


def buildArgumentParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DartLab Universe U3 live C2 descriptor gate")
    parser.add_argument("--checkpoint", type=Path, default=defaultCheckpointPath())
    parser.add_argument("--recovery-root", type=Path, default=defaultRecoveryRoot())
    parser.add_argument("--max-workers", type=int, default=16)
    parser.add_argument("--max-requests-per-second", type=float, default=12.0)
    parser.add_argument("--progress-every", type=int, default=250)
    parser.add_argument("--drift-check-every", type=int, default=1000)
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = buildArgumentParser().parse_args(argv)
    if (
        args.max_workers < 1
        or args.max_requests_per_second <= 0
        or args.progress_every < 1
        or args.drift_check_every < 1
    ):
        raise ValueError("worker, 요청률, progress 상한은 0보다 커야 함")
    report, metrics = runLiveC2(
        checkpointPath=args.checkpoint,
        recoveryRoot=args.recovery_root,
        maxWorkers=args.max_workers,
        maxRequestsPerSecond=args.max_requests_per_second,
        progressEvery=args.progress_every,
        driftCheckEvery=args.drift_check_every,
    )
    sys.stdout.buffer.write(canonicalJson(metrics) + b"\n")
    return 2 if args.strict and not report.passed else 0


if __name__ == "__main__":
    raise SystemExit(main())
