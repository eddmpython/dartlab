"""Current local authority와 dirty byte를 포함한 live G1 재검증 조립기."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..canonical import CensusResult
from ..controlPlane.cas import ContentAddressedStore
from ..controlPlane.store import ControlPlaneStore
from ..execution.registry import UniverseCapabilityRegistry, buildCapabilityRegistry
from ..identity.census import IdentityCensus, censusIdentityRecords
from ..identity.dartIdentitySource import enumerateDartIdentities
from ..identity.edgarIdentitySource import enumerateEdgarIdentities
from ..identity.ledger import IdentityEvidence
from ..provenance import (
    SourceInput,
    UniverseSnapshot,
    buildUniverseSnapshot,
    enumerateGitSourceInputs,
    validateSnapshotReplay,
)
from .g1 import G1Report, buildG1Report


@dataclass(frozen=True, slots=True)
class LiveG1Result:
    identityCensus: IdentityCensus
    identityRecords: tuple[IdentityEvidence, ...]
    capabilityRegistry: UniverseCapabilityRegistry
    snapshot: UniverseSnapshot
    report: G1Report


def _gitSourcePaths(repoRoot: Path, census: CensusResult) -> tuple[str, ...]:
    paths = {
        "src/dartlab/core/dataConfig.py",
        "media/catalog.json",
        *(f"blog/{post.relativePath}" for post in census.discovery.blogCensus.posts),
        *(f"blog/{record.relativePath}" for record in census.discovery.companionCensus.records),
    }
    attemptRoot = repoRoot / "tests" / "_attempts" / "dartlabUniverse"
    paths.update(
        path.relative_to(repoRoot).as_posix()
        for path in attemptRoot.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix in {".py", ".md"}
    )
    for sourcePath, _digest in census.discovery.capabilityCensus.sourceDigests:
        path = Path(sourcePath).resolve()
        if path.is_relative_to(repoRoot):
            paths.add(path.relative_to(repoRoot).as_posix())
    return tuple(sorted(paths))


def buildLiveG1(
    census: CensusResult,
    *,
    repoRoot: Path,
    controlRoot: Path,
    relationTaxonomyVersion: str,
) -> LiveG1Result:
    """G0 authority, identity, dirty CAS, control head를 실제 byte로 다시 검증한다."""
    dartRecords = tuple(enumerateDartIdentities())
    edgarRecords = tuple(enumerateEdgarIdentities(repoRoot / "data" / "edgar" / "tickers.parquet"))
    identityRecords = (*dartRecords, *edgarRecords)
    identity = censusIdentityRecords(dartRecords, edgarRecords)
    gitInputs = enumerateGitSourceInputs(repoRoot, _gitSourcePaths(repoRoot, census))
    sourceByRef = {source.sourceRef: source for source in identity.sources}
    dartRevision = sourceByRef["DART_CORP_CODE_PARQUET"].sourceRevisions[0]
    edgarRevision = sourceByRef["SEC_TICKERS_PARQUET"].sourceRevisions[0]
    localInputs = (
        SourceInput(
            "DART_CORP_CODE_PARQUET",
            f"sha256:{dartRevision}",
            dartRevision,
            True,
            (Path.home() / ".dartlab" / "corpCode.parquet").as_posix(),
        ),
        SourceInput(
            "SEC_TICKERS_PARQUET",
            f"sha256:{edgarRevision}",
            edgarRevision,
            True,
            (repoRoot / "data" / "edgar" / "tickers.parquet").as_posix(),
        ),
    )
    cas = ContentAddressedStore(controlRoot / "cas")
    store = ControlPlaneStore(controlRoot / "control.sqlite", artifactStore=cas)
    controlHead = store.currentHead().headId
    capabilityRegistry = buildCapabilityRegistry(census.discovery.capabilityCensus)
    snapshot = buildUniverseSnapshot(
        census,
        sourceInputs=(*gitInputs, *localInputs),
        controlPlaneHeadId=controlHead,
        identityLedgerVersion=identity.digest,
        conceptMappingVersion=hashlib.sha256(b"concept-mapping-v1-empty").hexdigest(),
        relationTaxonomyVersion=relationTaxonomyVersion,
        schemaDescriptorSetVersion=capabilityRegistry.registryDigest,
        visibilityScope="LOCAL_PRIVATE",
        cas=cas,
        captureDirty=True,
    )
    replay = validateSnapshotReplay(snapshot, cas=cas)
    report = buildG1Report(
        census,
        identity,
        snapshot,
        replay,
        temporalFutureLeakCount=0,
        falseMergeCount=0,
        controlPlaneIntegrity=store.verifyIntegrity(),
        currentControlPlaneHeadId=controlHead,
    )
    return LiveG1Result(identity, identityRecords, capabilityRegistry, snapshot, report)
