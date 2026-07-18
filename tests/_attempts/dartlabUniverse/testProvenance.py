"""Universe U1 CAS, append-only control plane, snapshot replayability 검증."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from dotenv import load_dotenv

from tests._attempts.dartlabUniverse.canonical import canonicalJson
from tests._attempts.dartlabUniverse.census import defaultRepoRoot, runFullCensus
from tests._attempts.dartlabUniverse.contracts import Replayability, ValidationReport
from tests._attempts.dartlabUniverse.controlPlane.cas import CasIntegrityError, ContentAddressedStore
from tests._attempts.dartlabUniverse.controlPlane.store import (
    ConcurrentHeadError,
    ControlDecision,
    ControlPlaneIntegrityError,
    ControlPlaneStore,
    DecisionStatus,
)
from tests._attempts.dartlabUniverse.identity.census import censusIdentitySources
from tests._attempts.dartlabUniverse.provenance import (
    SourceInput,
    buildUniverseSnapshot,
    enumerateGitSourceInputs,
    validateSnapshotReplay,
)
from tests._attempts.dartlabUniverse.testSupport import fakeConfig, fakeHfApi
from tests._attempts.dartlabUniverse.validation.g1 import buildG1Report


@pytest.fixture(scope="module")
def fakeCensus():
    repoRoot = defaultRepoRoot()
    return runFullCensus(
        repoRoot,
        configModule=fakeConfig(),
        apiFactory=lambda: fakeHfApi(repoRoot),
        protectExisting=False,
    )


@pytest.fixture(scope="module")
def identityCensus():
    return censusIdentitySources()


def _decision(
    decisionId: str,
    *,
    previousDecisionId: str | None = None,
    status: DecisionStatus = DecisionStatus.APPROVED,
    payload: bytes = b"decision-payload",
    evidenceRefs: tuple[str, ...] = ("evidence:fixture",),
    subjectRefs: tuple[str, ...] = ("organization:fixture",),
) -> ControlDecision:
    return ControlDecision(
        decisionId=decisionId,
        decisionKind="IDENTITY_MERGE",
        subjectRefs=subjectRefs,
        inputEvidenceRefs=evidenceRefs,
        ruleVersion="identity-rule-v1",
        payloadDigest=hashlib.sha256(payload).hexdigest(),
        status=status,
        reviewer="operator",
        reasonCode="FIXTURE_REVIEWED",
        previousDecisionId=previousDecisionId,
        createdAt="2026-07-18T00:00:00Z",
        approvedAt="2026-07-18T00:01:00Z" if status is DecisionStatus.APPROVED else None,
    )


def _snapshot(fakeCensus, sourceInputs, controlHead, **kwargs):
    return buildUniverseSnapshot(
        fakeCensus,
        sourceInputs=sourceInputs,
        controlPlaneHeadId=controlHead,
        identityLedgerVersion="identity-v1",
        conceptMappingVersion="concept-v1",
        relationTaxonomyVersion="relation-v1",
        schemaDescriptorSetVersion="schema-v1",
        visibilityScope="LOCAL_PRIVATE",
        **kwargs,
    )


def testCasDetectsMissingAndTamperedObjects(tmp_path: Path):
    cas = ContentAddressedStore(tmp_path / "universeHome")
    objectRef = cas.putBytes(b"immutable")
    assert cas.readBytes(objectRef) == b"immutable"
    objectPath = cas.pathForDigest(cas.digestFromRef(objectRef))

    objectPath.write_bytes(b"tampered")
    with pytest.raises(CasIntegrityError):
        cas.readBytes(objectRef)
    objectPath.unlink()
    with pytest.raises(CasIntegrityError):
        cas.readBytes(objectRef)


def testControlPlaneOptimisticHeadSupersedeAndRollback(tmp_path: Path):
    store = ControlPlaneStore(tmp_path / "universeHome" / "control.sqlite")
    genesis = store.currentHead()
    first = _decision("decision-1")
    firstHead = store.appendControlDecision(first, genesis.headId)
    assert [item.decisionId for item in store.approvedDecisions()] == ["decision-1"]

    with pytest.raises(ConcurrentHeadError):
        store.appendControlDecision(_decision("stale-writer"), genesis.headId)
    assert store.currentHead() == firstHead

    with pytest.raises(ValueError):
        store.appendControlDecision(_decision("missing-successor-link"), firstHead.headId)
    assert store.currentHead() == firstHead

    with pytest.raises(ValueError):
        store.appendControlDecision(
            _decision("invalid-successor", previousDecisionId="missing"),
            firstHead.headId,
        )
    assert store.currentHead() == firstHead

    second = _decision("decision-2", previousDecisionId="decision-1")
    secondHead = store.appendControlDecision(second, firstHead.headId)
    assert secondHead.sequence == 2
    assert [item.decisionId for item in store.approvedDecisions()] == ["decision-2"]

    retired = _decision(
        "decision-3",
        previousDecisionId="decision-2",
        status=DecisionStatus.SUPERSEDED,
    )
    store.appendControlDecision(retired, secondHead.headId)
    assert store.approvedDecisions() == ()


def testControlPlaneCorruptionBlocksAdmission(tmp_path: Path):
    databasePath = tmp_path / "universeHome" / "control.sqlite"
    store = ControlPlaneStore(databasePath)
    store.appendControlDecision(_decision("decision-1"), store.currentHead().headId)

    with sqlite3.connect(databasePath) as connection:
        connection.execute("DROP TRIGGER decisions_no_update")
        connection.execute("UPDATE decisions SET record_json=? WHERE decision_id=?", (b"{}", "decision-1"))
    with pytest.raises(ControlPlaneIntegrityError):
        store.verifyIntegrity()


def testControlPlaneMissingCasArtifactBlocksAdmission(tmp_path: Path):
    cas = ContentAddressedStore(tmp_path / "universeHome")
    objectRef = cas.putBytes(b"review evidence")
    store = ControlPlaneStore(tmp_path / "universeHome" / "control.sqlite", artifactStore=cas)
    store.appendControlDecision(
        _decision("decision-1", evidenceRefs=(objectRef,)),
        store.currentHead().headId,
    )
    cas.pathForDigest(cas.digestFromRef(objectRef)).unlink()
    with pytest.raises(ControlPlaneIntegrityError):
        store.verifyIntegrity()


def testControlPlaneReleasesDatabaseFileHandle(tmp_path: Path):
    databasePath = tmp_path / "universeHome" / "control.sqlite"
    store = ControlPlaneStore(databasePath)
    store.appendControlDecision(_decision("decision-1"), store.currentHead().headId)
    assert store.verifyIntegrity()

    databasePath.unlink()
    assert not databasePath.exists()


def testCleanAndDirtySnapshotReplayability(fakeCensus, tmp_path: Path):
    store = ControlPlaneStore(tmp_path / "universeHome" / "control.sqlite")
    cleanInputs = (SourceInput("code", "git:clean", hashlib.sha256(b"clean").hexdigest(), False),)
    first = _snapshot(fakeCensus, cleanInputs, store.currentHead().headId, createdAt="2026-07-18T00:00:00Z")
    second = _snapshot(fakeCensus, cleanInputs, store.currentHead().headId, createdAt="2026-07-19T00:00:00Z")
    assert first.snapshotId == second.snapshotId
    assert first.replayability is Replayability.VERIFIED
    assert validateSnapshotReplay(first).valid

    dirtyPath = tmp_path / "dirty-input.py"
    dirtyPath.write_bytes(b"dirty byte")
    dirtyDigest = hashlib.sha256(dirtyPath.read_bytes()).hexdigest()
    dirtyInputs = (SourceInput("dirty-code", "worktree", dirtyDigest, True, dirtyPath.as_posix()),)
    cas = ContentAddressedStore(tmp_path / "dirtyUniverseHome")
    captured = _snapshot(
        fakeCensus,
        dirtyInputs,
        store.currentHead().headId,
        cas=cas,
        captureDirty=True,
    )
    assert captured.replayability is Replayability.LOCAL_CAPTURED
    assert validateSnapshotReplay(captured, cas=cas).valid

    capture = captured.dirtyCaptureRefs[0]
    cas.pathForDigest(cas.digestFromRef(capture.objectRef)).unlink()
    assert not validateSnapshotReplay(captured, cas=cas).valid


def testCaptureDisabledSnapshotCannotPassG1(fakeCensus, tmp_path: Path):
    dirtyPath = tmp_path / "dirty-input.py"
    dirtyPath.write_bytes(b"uncaptured")
    source = SourceInput(
        "dirty-code",
        "worktree",
        hashlib.sha256(dirtyPath.read_bytes()).hexdigest(),
        True,
        dirtyPath.as_posix(),
    )
    snapshot = _snapshot(
        fakeCensus,
        (source,),
        "f" * 64,
        captureDirty=False,
    )
    assert snapshot.replayability is Replayability.NONREPLAYABLE
    report = validateSnapshotReplay(snapshot)
    assert not report.valid
    assert {issue.code for issue in report.issues} == {"SNAPSHOT_NONREPLAYABLE"}


def testSnapshotRootMutationIsDetected(fakeCensus):
    source = SourceInput("code", "git:clean", hashlib.sha256(b"clean").hexdigest(), False)
    snapshot = _snapshot(fakeCensus, (source,), "f" * 64)
    mutated = replace(snapshot, identityLedgerVersion="identity-v2")
    assert not validateSnapshotReplay(mutated).valid


def testGitSourceInputsSeparateCleanDirtyAndUntracked(tmp_path: Path):
    repo = tmp_path / "gitFixture"
    repo.mkdir()
    clean = repo / "clean.py"
    dirty = repo / "dirty.py"
    untracked = repo / "untracked.py"
    ignored = repo / "ignored.py"
    gitignore = repo / ".gitignore"
    clean.write_text("clean = True\n", encoding="utf-8")
    dirty.write_text("dirty = False\n", encoding="utf-8")
    gitignore.write_text("ignored.py\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", ".gitignore", "clean.py", "dirty.py"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=DartLab",
            "-c",
            "user.email=dartlab@example.invalid",
            "commit",
            "-q",
            "-m",
            "초기: provenance fixture",
        ],
        cwd=repo,
        check=True,
    )
    dirty.write_text("dirty = True\n", encoding="utf-8")
    untracked.write_text("untracked = True\n", encoding="utf-8")
    ignored.write_text("ignored = True\n", encoding="utf-8")

    records = enumerateGitSourceInputs(repo, ("clean.py", "dirty.py", "untracked.py", "ignored.py"))
    byRef = {record.sourceRef: record for record in records}
    assert not byRef["clean.py"].dirty and byRef["clean.py"].path is None
    assert byRef["dirty.py"].dirty and byRef["dirty.py"].path
    assert byRef["untracked.py"].dirty and byRef["untracked.py"].path
    assert byRef["ignored.py"].dirty and byRef["ignored.py"].path


def testG1MachineGatePassesAndFailsClosed(fakeCensus, identityCensus, tmp_path: Path):
    store = ControlPlaneStore(tmp_path / "universeHome" / "control.sqlite")
    source = SourceInput("code", "git:clean", hashlib.sha256(b"clean").hexdigest(), False)
    snapshot = _snapshot(fakeCensus, (source,), store.currentHead().headId)
    replay = validateSnapshotReplay(snapshot)
    validContract = ValidationReport(True, (), hashlib.sha256(b"valid").hexdigest())
    report = buildG1Report(
        fakeCensus,
        identityCensus,
        snapshot,
        replay,
        contractValidations=(validContract,),
        temporalFutureLeakCount=0,
        falseMergeCount=0,
        controlPlaneIntegrity=store.verifyIntegrity(),
        currentControlPlaneHeadId=store.currentHead().headId,
    )
    assert report.g1Passed
    assert report.identityEntityCount == identityCensus.totalEntityCount

    failed = buildG1Report(
        fakeCensus,
        identityCensus,
        snapshot,
        replay,
        temporalFutureLeakCount=1,
        falseMergeCount=1,
        controlPlaneIntegrity=False,
        currentControlPlaneHeadId=store.currentHead().headId,
    )
    assert not failed.g1Passed
    assert set(failed.failureCodes) == {
        "CONTROL_PLANE_INVALID",
        "IDENTITY_FALSE_MERGE",
        "TEMPORAL_FUTURE_LEAK",
    }

    mismatched = buildG1Report(
        fakeCensus,
        identityCensus,
        snapshot,
        replace(replay, snapshotId="du:v1:snapshot:" + "0" * 64),
        controlPlaneIntegrity=True,
        currentControlPlaneHeadId="e" * 64,
    )
    assert {"CONTROL_HEAD_MISMATCH", "REPLAY_SUBJECT_MISMATCH"} <= set(mismatched.failureCodes)


@pytest.mark.network
@pytest.mark.slow
def testLiveG1CapturesDirtyInputsAndWritesMachineArtifact(identityCensus, tmp_path: Path):
    repoRoot = defaultRepoRoot()
    load_dotenv(dotenv_path=repoRoot / ".env", override=False)
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    if not token:
        pytest.skip("private HF authority token 없음")
    census = runFullCensus(repoRoot, token=token, protectExisting=False)
    relativePaths = {
        "src/dartlab/core/dataConfig.py",
        "media/catalog.json",
        *(f"blog/{post.relativePath}" for post in census.discovery.blogCensus.posts),
        *(f"blog/{record.relativePath}" for record in census.discovery.companionCensus.records),
    }
    relativePaths.update(
        path.relative_to(repoRoot).as_posix()
        for path in (repoRoot / "tests" / "_attempts" / "dartlabUniverse").rglob("*.py")
    )
    for sourcePath, _digest in census.discovery.capabilityCensus.sourceDigests:
        path = Path(sourcePath).resolve()
        if path.is_relative_to(repoRoot):
            relativePaths.add(path.relative_to(repoRoot).as_posix())
    gitInputs = enumerateGitSourceInputs(repoRoot, tuple(sorted(relativePaths)))
    sourceByRef = {source.sourceRef: source for source in identityCensus.sources}
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
    cas = ContentAddressedStore(tmp_path / "universeHome")
    store = ControlPlaneStore(tmp_path / "universeHome" / "control.sqlite", artifactStore=cas)
    snapshot = buildUniverseSnapshot(
        census,
        sourceInputs=(*gitInputs, *localInputs),
        controlPlaneHeadId=store.currentHead().headId,
        identityLedgerVersion=identityCensus.digest,
        conceptMappingVersion=hashlib.sha256(b"concept-mapping-v1-empty").hexdigest(),
        relationTaxonomyVersion=hashlib.sha256(b"relation-taxonomy-v1").hexdigest(),
        schemaDescriptorSetVersion=hashlib.sha256(b"schema-descriptor-v1-empty").hexdigest(),
        visibilityScope="LOCAL_PRIVATE",
        cas=cas,
        captureDirty=True,
    )
    replay = validateSnapshotReplay(snapshot, cas=cas)
    report = buildG1Report(
        census,
        identityCensus,
        snapshot,
        replay,
        temporalFutureLeakCount=0,
        falseMergeCount=0,
        controlPlaneIntegrity=store.verifyIntegrity(),
        currentControlPlaneHeadId=store.currentHead().headId,
    )
    outputPath = tmp_path / "universe-g1.json"
    outputPath.write_bytes(canonicalJson(report))
    decoded = json.loads(outputPath.read_text(encoding="utf-8"))

    assert report.g1Passed, report.failureCodes
    assert snapshot.replayability is Replayability.LOCAL_CAPTURED
    assert snapshot.dirtyCaptureRefs
    assert decoded["digest"] == report.digest
    assert outputPath.parent == tmp_path
