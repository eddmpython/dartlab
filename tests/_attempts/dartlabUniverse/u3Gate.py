"""Current C2 checkpoint와 live G1을 결합해 Universe U3 gate를 판정한다."""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

from dotenv import load_dotenv

from .canonical import canonicalDigest, canonicalJson
from .catalog.compiler import attachCapabilityRegistry, attachIdentityRecords, compileCatalog
from .catalog.descriptorCheckpoint import DescriptorCheckpointStore
from .catalog.descriptorCrawler import DescriptorPolicy
from .catalog.recoveryStore import ResourceRecoveryStore, defaultRecoveryRoot
from .catalog.snapshot import buildCatalogSnapshot
from .census import defaultRepoRoot, runFullCensus
from .graph.relations import compileCatalogRelations, defaultRelationTaxonomy
from .u3C2 import assertPinnedHfRevisions, defaultCheckpointPath, probeHfHeadAdvances
from .validation.g2 import validateG2
from .validation.liveG1 import buildLiveG1
from .validation.slo import benchmarkU3Runtime
from .validation.u3 import U3Report, validateU3


def recordRuntimeFailure(report: U3Report, code: str) -> U3Report:
    """Gate 외곽의 live failure도 digest가 결박된 U3 report로 닫는다."""
    failureCodes = tuple(sorted({*getattr(report, "failureCodes"), code}))
    updated = replace(report, passed=False, failureCodes=failureCodes, digest="")
    return replace(updated, digest=canonicalDigest(updated))


def defaultControlRoot() -> Path:
    root = Path(os.getenv("LOCALAPPDATA") or (Path.home() / ".dartlab"))
    return root / "DartLab" / "universe" / "control" / "u3"


def runLiveU3(*, checkpointPath: Path, recoveryRoot: Path, controlRoot: Path) -> tuple[object, dict[str, object]]:
    """Live G0, G1, C2, catalog snapshot, evidence relation을 한 번에 검증한다."""
    repoRoot = defaultRepoRoot()
    load_dotenv(repoRoot / ".env", override=False)
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    started = time.perf_counter()
    census = runFullCensus(repoRoot, token=token, protectExisting=False)
    catalog = compileCatalog(census)
    policy = DescriptorPolicy()
    with DescriptorCheckpointStore(checkpointPath) as checkpoint:
        checkpoint.assertNoActiveLease()
        reusableDescriptors = checkpoint.load(catalog.resources, policy)
        descriptorByVersion = {item.resourceVersionId: item for item in reusableDescriptors}
        for attempt in checkpoint.loadTerminalAttempts(catalog.resources, policy):
            descriptorByVersion.setdefault(attempt.resourceVersionId, attempt)
        descriptors = tuple(sorted(descriptorByVersion.values(), key=lambda item: item.resourceVersionId))
    taxonomy = defaultRelationTaxonomy()
    liveG1 = buildLiveG1(
        census,
        repoRoot=repoRoot,
        controlRoot=controlRoot,
        relationTaxonomyVersion=taxonomy.version,
    )
    g2 = validateG2(liveG1.capabilityRegistry)
    catalog = attachCapabilityRegistry(catalog, liveG1.capabilityRegistry)
    catalog = attachIdentityRecords(catalog, liveG1.identityRecords)
    with ResourceRecoveryStore(recoveryRoot) as recoveryStore:
        recoveries = recoveryStore.load(catalog, descriptors)
        recoveryReceiptCount = recoveryStore.receiptCount()
        staleRecoveryReceiptCount = recoveryStore.staleReceiptCount
        snapshot = buildCatalogSnapshot(
            catalog,
            universeSnapshotId=liveG1.snapshot.snapshotId,
            descriptors=descriptors,
            recoveries=recoveries,
            capabilityRegistryVersion=liveG1.capabilityRegistry.registryDigest,
            identityLedgerVersion=liveG1.identityCensus.digest,
            relationTaxonomyVersion=taxonomy.version,
        )
        relations = compileCatalogRelations(catalog, taxonomy=taxonomy)
        slo = benchmarkU3Runtime(catalog, relations, snapshot)
        report = validateU3(
            catalog,
            descriptors,
            snapshot,
            statements=(),
            relations=relations,
            upstreamG1Passed=liveG1.report.g1Passed,
            upstreamG2Passed=g2.passed,
            upstreamUniverseSnapshotId=liveG1.snapshot.snapshotId,
            upstreamCensusSnapshotDigest=liveG1.report.u0SnapshotDigest,
            upstreamCapabilityRegistryVersion=liveG1.capabilityRegistry.registryDigest,
            upstreamIdentityLedgerVersion=liveG1.identityCensus.digest,
            upstreamRelationTaxonomyVersion=taxonomy.version,
            recoveries=recoveries,
            recoveryCas=recoveryStore.cas,
        )
    pinnedRevisionFailureCodes = []
    sourceHeadAdvanceEvents = []
    sourceHeadProbeFailureCodes = []
    try:
        assertPinnedHfRevisions(census.discovery.pinnedRepositories, token=token)
    except Exception as exc:
        pinnedRevisionFailureCodes.append(type(exc).__name__)
        report = recordRuntimeFailure(report, "PINNED_REVISION_VALIDATION_FAILED")
    try:
        sourceHeadAdvanceEvents.extend(probeHfHeadAdvances(census.discovery.pinnedRepositories, token=token))
    except Exception as exc:
        sourceHeadProbeFailureCodes.append(type(exc).__name__)
    metrics = {
        "schemaVersion": "du-u3-gate-live-v5",
        "passed": report.passed and slo.passed,
        "durationSeconds": round(time.perf_counter() - started, 6),
        "sourceRevisions": tuple((item.repoId, item.revision or "") for item in census.discovery.pinnedRepositories),
        "hfRepoFileCounts": tuple((item.repoId, len(item.files)) for item in census.discovery.pinnedRepositories),
        "hfDiscoveredFileCount": census.coverage.discoveredFileCount,
        "hfDiscoveredByteCount": census.coverage.discoveredByteCount,
        "blogPostCount": census.coverage.blogPostCount,
        "mediaCatalogRecordCount": len(census.discovery.mediaCensus.records),
        "u0SnapshotDigest": census.snapshotDigest,
        "g1Digest": liveG1.report.digest,
        "g2Digest": g2.digest,
        "universeSnapshotId": liveG1.snapshot.snapshotId,
        "catalogDigest": catalog.digest,
        "catalogSnapshotId": snapshot.snapshotId,
        "catalogResourceCount": len(catalog.resources),
        "catalogObjectCount": len(catalog.objects),
        "catalogEvidenceCount": len(catalog.evidence),
        "identityEntityCount": liveG1.identityCensus.totalEntityCount,
        "identitySourceCounts": tuple((item.sourceRef, item.entityCount) for item in liveG1.identityCensus.sources),
        "capabilityCandidateCount": liveG1.capabilityRegistry.discoveredCandidateCount,
        "eligibleCapabilityCount": liveG1.capabilityRegistry.eligibleCallableCount,
        "validatedCapabilitySchemaCount": liveG1.capabilityRegistry.validatedSchemaCount,
        "inventedCapabilityCount": liveG1.capabilityRegistry.inventedAxisCount,
        "descriptorCount": len(descriptors),
        "recoveryReceiptCount": recoveryReceiptCount,
        "activeRecoveryCount": len(recoveries),
        "staleRecoveryReceiptCount": staleRecoveryReceiptCount,
        "recoverySetDigest": snapshot.recoverySetDigest,
        "relationCount": len(relations),
        "pinnedRevisionValidationPassed": not pinnedRevisionFailureCodes,
        "pinnedRevisionFailureCodes": tuple(pinnedRevisionFailureCodes),
        "sourceFreshnessStatus": (
            "UNKNOWN" if sourceHeadProbeFailureCodes else "ADVANCED" if sourceHeadAdvanceEvents else "CURRENT"
        ),
        "sourceHeadAdvanceDetected": bool(sourceHeadAdvanceEvents),
        "sourceHeadAdvanceEvents": tuple(sourceHeadAdvanceEvents),
        "sourceHeadProbeFailureCodes": tuple(sourceHeadProbeFailureCodes),
        "slo": asdict(slo),
        "u3": asdict(report),
    }
    return report.passed and slo.passed, metrics


def buildArgumentParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DartLab Universe U3 live catalog gate")
    parser.add_argument("--checkpoint", type=Path, default=defaultCheckpointPath())
    parser.add_argument("--recovery-root", type=Path, default=defaultRecoveryRoot())
    parser.add_argument("--control-root", type=Path, default=defaultControlRoot())
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = buildArgumentParser().parse_args(argv)
    passed, metrics = runLiveU3(
        checkpointPath=args.checkpoint,
        recoveryRoot=args.recovery_root,
        controlRoot=args.control_root,
    )
    sys.stdout.buffer.write(canonicalJson(metrics) + b"\n")
    return 2 if args.strict and not passed else 0


if __name__ == "__main__":
    raise SystemExit(main())
