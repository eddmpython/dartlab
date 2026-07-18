"""Universe U1 source snapshot, dirty byte capture, replayability contract."""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from .canonical import CensusResult, canonicalDigest
from .contracts import Replayability, ValidationIssue
from .controlPlane.cas import CasIntegrityError, ContentAddressedStore

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SourceInput:
    sourceRef: str
    revision: str
    contentDigest: str
    dirty: bool
    path: str | None = None


@dataclass(frozen=True, slots=True)
class DirtyCaptureRef:
    sourceRef: str
    path: str
    contentDigest: str
    objectRef: str
    byteSize: int


@dataclass(frozen=True, slots=True)
class UniverseSnapshot:
    snapshotId: str
    schemaVersion: str
    sourceRevisionSet: tuple[tuple[str, str], ...]
    sourceInputs: tuple[SourceInput, ...]
    blogRevision: str
    dirtyCaptureRefs: tuple[DirtyCaptureRef, ...]
    nonreplayableSourceRefs: tuple[str, ...]
    mediaCatalogDigest: str
    capabilityCatalogDigest: str
    identityLedgerVersion: str
    conceptMappingVersion: str
    relationTaxonomyVersion: str
    schemaDescriptorSetVersion: str
    controlPlaneHeadId: str
    visibilityScope: str
    previousSnapshotId: str | None
    coverageLedgerDigest: str
    replayability: Replayability
    rootInputsDigest: str
    createdAt: str


@dataclass(frozen=True, slots=True)
class SnapshotValidationReport:
    snapshotId: str
    valid: bool
    issues: tuple[ValidationIssue, ...]
    digest: str


def enumerateGitSourceInputs(
    repoRoot: Path,
    relativePaths: tuple[str, ...],
) -> tuple[SourceInput, ...]:
    """Git HEAD와 current byte를 읽어 clean commit input과 dirty capture 대상을 구분한다."""
    root = repoRoot.resolve()
    if not (root / ".git").exists():
        raise ValueError(f"git repository가 아님: {root}")
    headResult = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=10.0,
    )
    if headResult.returncode != 0:
        raise RuntimeError("git HEAD 조회 실패")
    head = headResult.stdout.strip()
    pathsByRelative = {}
    for relativePath in sorted(set(relativePaths)):
        path = (root / relativePath).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.is_symlink():
            raise ValueError(f"안전하지 않은 git source input: {relativePath}")
        relative = path.relative_to(root).as_posix()
        pathsByRelative[relative] = path
    trackedRefs = set()
    dirtyRefs = set()
    orderedRelatives = tuple(sorted(pathsByRelative))
    for start in range(0, len(orderedRelatives), 100):
        chunk = orderedRelatives[start : start + 100]
        tracked = subprocess.run(
            ["git", "ls-files", "-z", "--", *chunk],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10.0,
        )
        if tracked.returncode != 0:
            raise RuntimeError(f"git tracked source 조회 실패: {chunk[0]}")
        trackedRefs.update(item.replace("\\", "/") for item in tracked.stdout.split("\0") if item)
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *chunk],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10.0,
        )
        if status.returncode != 0:
            raise RuntimeError(f"git status 조회 실패: {chunk[0]}")
        for entry in (item for item in status.stdout.split("\0") if item):
            candidate = entry[3:] if len(entry) > 3 and entry[2] == " " else entry
            normalized = candidate.replace("\\", "/")
            if normalized in pathsByRelative:
                dirtyRefs.add(normalized)
    dirtyRefs.update(set(orderedRelatives) - trackedRefs)
    records = []
    for relative, path in pathsByRelative.items():
        dirty = relative in dirtyRefs
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(
            SourceInput(
                sourceRef=relative,
                revision=f"git:{head}:dirty" if dirty else f"git:{head}",
                contentDigest=digest,
                dirty=dirty,
                path=path.as_posix() if dirty else None,
            )
        )
    return tuple(records)


def captureDirtyInput(
    path: Path,
    cas: ContentAddressedStore,
    *,
    sourceRef: str | None = None,
) -> DirtyCaptureRef:
    """Dirty source byte를 local CAS에 저장하고 복원 가능한 ref를 만든다."""
    resolved = path.resolve()
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError(f"dirty capture 대상은 regular file이어야 함: {resolved}")
    payload = resolved.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    objectRef = cas.putBytes(payload)
    cas.verify(objectRef)
    return DirtyCaptureRef(
        sourceRef=sourceRef or resolved.as_posix(),
        path=resolved.as_posix(),
        contentDigest=digest,
        objectRef=objectRef,
        byteSize=len(payload),
    )


def _rootInputs(snapshot: UniverseSnapshot) -> dict[str, object]:
    return {
        "schemaVersion": snapshot.schemaVersion,
        "sourceRevisionSet": snapshot.sourceRevisionSet,
        "sourceInputs": snapshot.sourceInputs,
        "blogRevision": snapshot.blogRevision,
        "dirtyCaptureRefs": snapshot.dirtyCaptureRefs,
        "nonreplayableSourceRefs": snapshot.nonreplayableSourceRefs,
        "mediaCatalogDigest": snapshot.mediaCatalogDigest,
        "capabilityCatalogDigest": snapshot.capabilityCatalogDigest,
        "identityLedgerVersion": snapshot.identityLedgerVersion,
        "conceptMappingVersion": snapshot.conceptMappingVersion,
        "relationTaxonomyVersion": snapshot.relationTaxonomyVersion,
        "schemaDescriptorSetVersion": snapshot.schemaDescriptorSetVersion,
        "controlPlaneHeadId": snapshot.controlPlaneHeadId,
        "visibilityScope": snapshot.visibilityScope,
        "previousSnapshotId": snapshot.previousSnapshotId,
        "coverageLedgerDigest": snapshot.coverageLedgerDigest,
        "replayability": snapshot.replayability,
    }


def buildUniverseSnapshot(
    census: CensusResult,
    *,
    sourceInputs: tuple[SourceInput, ...],
    controlPlaneHeadId: str,
    identityLedgerVersion: str,
    conceptMappingVersion: str,
    relationTaxonomyVersion: str,
    schemaDescriptorSetVersion: str,
    visibilityScope: str,
    cas: ContentAddressedStore | None = None,
    captureDirty: bool = True,
    previousSnapshotId: str | None = None,
    createdAt: str | None = None,
) -> UniverseSnapshot:
    """U0 authority와 U1 control versions를 immutable snapshot으로 조립한다."""
    orderedInputs = tuple(sorted(sourceInputs, key=lambda item: item.sourceRef))
    captures = []
    nonreplayable = []
    for source in orderedInputs:
        if not _SHA256_RE.fullmatch(source.contentDigest):
            raise ValueError(f"source input digest invalid: {source.sourceRef}")
        if not source.dirty:
            continue
        if captureDirty and cas is not None and source.path is not None:
            capture = captureDirtyInput(Path(source.path), cas, sourceRef=source.sourceRef)
            if capture.contentDigest != source.contentDigest:
                raise ValueError(f"dirty input digest drift: {source.sourceRef}")
            captures.append(capture)
        else:
            nonreplayable.append(source.sourceRef)
    if nonreplayable:
        replayability = Replayability.NONREPLAYABLE
    elif captures:
        replayability = Replayability.LOCAL_CAPTURED
    else:
        replayability = Replayability.VERIFIED
    sourceRevisionSet = tuple(
        sorted((repo.repoId, str(repo.revision or "")) for repo in census.discovery.pinnedRepositories)
    )
    base = UniverseSnapshot(
        snapshotId="",
        schemaVersion="du-snapshot-v1",
        sourceRevisionSet=sourceRevisionSet,
        sourceInputs=orderedInputs,
        blogRevision=census.discovery.blogCensus.digest,
        dirtyCaptureRefs=tuple(sorted(captures, key=lambda item: item.sourceRef)),
        nonreplayableSourceRefs=tuple(sorted(nonreplayable)),
        mediaCatalogDigest=census.discovery.mediaCensus.digest,
        capabilityCatalogDigest=census.discovery.capabilityCensus.digest,
        identityLedgerVersion=identityLedgerVersion,
        conceptMappingVersion=conceptMappingVersion,
        relationTaxonomyVersion=relationTaxonomyVersion,
        schemaDescriptorSetVersion=schemaDescriptorSetVersion,
        controlPlaneHeadId=controlPlaneHeadId,
        visibilityScope=visibilityScope,
        previousSnapshotId=previousSnapshotId,
        coverageLedgerDigest=census.coverage.digest,
        replayability=replayability,
        rootInputsDigest="",
        createdAt=createdAt or datetime.now(timezone.utc).isoformat(),
    )
    rootDigest = canonicalDigest(_rootInputs(base))
    return replace(
        base,
        snapshotId=f"du:v1:snapshot:{rootDigest}",
        rootInputsDigest=rootDigest,
    )


def validateSnapshotReplay(
    snapshot: UniverseSnapshot,
    *,
    cas: ContentAddressedStore | None = None,
) -> SnapshotValidationReport:
    """Snapshot root digest, source revision, dirty CAS object, replayability를 검증한다."""
    issues = []
    expectedDigest = canonicalDigest(_rootInputs(snapshot))
    if snapshot.rootInputsDigest != expectedDigest or snapshot.snapshotId != f"du:v1:snapshot:{expectedDigest}":
        issues.append(ValidationIssue("SNAPSHOT_ROOT_MISMATCH", "snapshotId", expectedDigest))
    for repoId, revision in snapshot.sourceRevisionSet:
        if not repoId or not revision:
            issues.append(ValidationIssue("SOURCE_REVISION_MISSING", "sourceRevisionSet", repoId))
    for source in snapshot.sourceInputs:
        if not source.sourceRef or not source.revision:
            issues.append(ValidationIssue("SOURCE_INPUT_REVISION_MISSING", "sourceInputs", source.sourceRef))
        if not _SHA256_RE.fullmatch(source.contentDigest):
            issues.append(ValidationIssue("SOURCE_INPUT_DIGEST_INVALID", "sourceInputs", source.sourceRef))
    if not _SHA256_RE.fullmatch(snapshot.controlPlaneHeadId):
        issues.append(ValidationIssue("CONTROL_HEAD_INVALID", "controlPlaneHeadId", snapshot.controlPlaneHeadId))
    for fieldName in (
        "identityLedgerVersion",
        "conceptMappingVersion",
        "relationTaxonomyVersion",
        "schemaDescriptorSetVersion",
    ):
        if not getattr(snapshot, fieldName):
            issues.append(ValidationIssue("CONTROL_VERSION_MISSING", fieldName, fieldName))
    for capture in snapshot.dirtyCaptureRefs:
        if cas is None:
            issues.append(ValidationIssue("CAS_REQUIRED", "dirtyCaptureRefs", capture.sourceRef))
            continue
        try:
            payload = cas.readBytes(capture.objectRef)
            if hashlib.sha256(payload).hexdigest() != capture.contentDigest or len(payload) != capture.byteSize:
                issues.append(ValidationIssue("DIRTY_CAPTURE_MISMATCH", "dirtyCaptureRefs", capture.sourceRef))
        except CasIntegrityError:
            issues.append(ValidationIssue("DIRTY_CAPTURE_UNAVAILABLE", "dirtyCaptureRefs", capture.sourceRef))
    if snapshot.replayability is Replayability.NONREPLAYABLE or snapshot.nonreplayableSourceRefs:
        issues.append(ValidationIssue("SNAPSHOT_NONREPLAYABLE", "replayability", snapshot.replayability.value))
    if snapshot.replayability is Replayability.LOCAL_CAPTURED and not snapshot.dirtyCaptureRefs:
        issues.append(ValidationIssue("LOCAL_CAPTURE_MISSING", "dirtyCaptureRefs", "LOCAL_CAPTURED"))
    if snapshot.replayability is Replayability.VERIFIED and any(source.dirty for source in snapshot.sourceInputs):
        issues.append(ValidationIssue("DIRTY_INPUT_UNCAPTURED", "sourceInputs", "VERIFIED"))
    ordered = tuple(sorted(issues, key=lambda item: (item.code, item.path, item.detail)))
    digest = canonicalDigest({"snapshotId": snapshot.snapshotId, "issues": ordered})
    return SnapshotValidationReport(
        snapshotId=snapshot.snapshotId,
        valid=not ordered,
        issues=ordered,
        digest=digest,
    )
