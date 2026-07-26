"""계산형 owner page의 spawn, deadline, artifact 회수 통합 tests."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import multiprocessing
import os
import socket
import subprocess
import sys
import time
import types
from pathlib import Path

import polars as pl
import pytest

import dartlab.dataHub.isolation.ownerProcess as ownerProcess
import dartlab.dataHub.isolation.ownerProcessArtifacts as ownerProcessArtifacts
import dartlab.dataHub.ownerPaging as ownerPaging
import dartlab.dataHub.ownerPagingApi as ownerPagingApi
from dartlab.dataHub import (
    DataAssetDescriptor,
    DataQuery,
    FactorProjection,
    QueryBudget,
    UniverseSelection,
)
from dartlab.dataHub.feature.observation import makeVariableObservation
from dartlab.dataHub.feature.query import buildFeatureObservationSet
from dartlab.dataHub.feature.registry import StateVariableSpec, buildStateVariableRegistry
from dartlab.dataHub.identity.vintage import VintageRef
from dartlab.dataHub.isolation.ownerProcess import (
    _artifactPath,
    _decodeControlFrame,
    runOwnerPage,
)
from dartlab.dataHub.pagingRuntime import (
    MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES,
    MAX_STATE_BYTES,
    MIN_OWNER_PROCESS_WORK_SECONDS,
    ownerProcessArtifactRoot,
)

_DIGEST = "1" * 64
_SECOND_DIGEST = "2" * 64


def _fixtureDataset(subject: str):
    entityId = f"US:{subject}"
    spec = StateVariableSpec(
        variableId="financial.revenue",
        signalId="financial.revenue",
        providerId="fixture",
        datasetId="owner-process",
        unit="USD",
        role="observedFeature",
        evidenceRole="observed",
        frequency="quarter",
        timing="flow",
        transformId="identity",
        maxStalenessDays=500,
    )
    registry = buildStateVariableRegistry((spec,))
    vintage = VintageRef(
        artifactKind="fixture",
        provider="fixture",
        artifactId=entityId,
        artifactHash=_DIGEST,
        payloadHash=_DIGEST,
        knowledgeAsOf="20250115",
        availableAt="20250115",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        fiscalThrough="20241231",
    )
    observation = makeVariableObservation(
        providerId="fixture",
        datasetId="owner-process",
        entityId=entityId,
        signalId="financial.revenue",
        value=100.0,
        unit="USD",
        frequency="quarter",
        timing="flow",
        transformId="identity",
        evidenceRole="observed",
        eventAt="20241231",
        availableAt="20250115",
        knowledgeAsOf="20250115",
        availabilityPrecision="date",
        revisionId=f"revision-{subject}",
        vintage=vintage,
        normalizationRuleHash=_SECOND_DIGEST,
    )
    return buildFeatureObservationSet(registry, (observation,))


def _fixtureOwner(*, subject: str):
    return _fixtureDataset(subject)


def _fixtureHang(*, subject: str):
    del subject
    while True:
        time.sleep(1)


def _fixturePartialHang(*, subject: str):
    if subject == "T000":
        return _fixtureDataset(subject)
    while True:
        time.sleep(1)


def _fixtureNetwork(*, subject: str, outputPath: str):
    del subject, outputPath
    return socket.getaddrinfo("huggingface.co", 443)


def _fixturePythonWrite(*, subject: str, outputPath: str):
    del subject
    Path(outputPath).write_text("blocked", encoding="utf-8")
    return _fixtureDataset("blocked")


def _fixturePolarsWrite(*, subject: str, outputPath: str):
    del subject
    pl.DataFrame({"value": [1]}).write_parquet(outputPath)
    return _fixtureDataset("blocked")


def _fixtureSubprocessWrite(*, subject: str, outputPath: str):
    del subject
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('blocked')",
            outputPath,
        ],
        check=True,
    )
    return _fixtureDataset("blocked")


def _sessionPayload(
    executorAttribute: str = "_fixtureOwner",
    *,
    entityCount: int = 1,
    params: dict[str, str] | None = None,
) -> bytes:
    descriptor = DataAssetDescriptor(
        assetId="analysis.ownerProcessFixture",
        assetVersionId="analysis.ownerProcessFixture:v1",
        owner="tests.dataHub.test_ownerProcess",
        layer="L2",
        kind="computed",
        label="Owner process fixture",
        description="Spawn child integration fixture",
        sourceRef="fixture:owner-process",
        queryable=True,
        temporalSupport=("latest",),
        executorKind="callable",
        executorModule="tests.dataHub.test_ownerProcess",
        executorAttribute=executorAttribute,
        subjectParam="subject",
        selectorKind="subject",
        selectorRequired=True,
        executionMode="subjectFanout",
        universeKind="listedEquity",
        universeMarkets=("US",),
        metadata=(("market", "US"),),
    )
    query = DataQuery(
        projection=FactorProjection(measures=("financial.revenue",)),
        params={} if params is None else params,
        budget=QueryBudget(
            maxRows=100,
            maxBytes=8 * 1024 * 1024,
            timeoutMs=10_000,
            maxConcurrency=2,
        ),
    )
    selection = UniverseSelection(("US",))
    ownerSourcePin = "resource-source-full:fixture"
    sourcePin = ownerPaging._sourcePin(
        ownerSourcePin,
        _DIGEST,
        ("financial.revenue",),
    )
    queryPin = ownerPaging.canonicalDigest(
        {
            "descriptor": ownerPaging._descriptorTree(descriptor),
            "query": ownerPaging._queryTree(query),
            "selection": ownerPaging._selectionTree(selection),
        }
    )
    entities = tuple(ownerPaging._EntityRef(f"T{index:03d}", None) for index in range(entityCount))
    task = ownerPaging._OwnerTask(
        requestId="fixture",
        descriptor=descriptor,
        query=query,
        selection=selection,
        market="US",
        provider="fixture",
        universeSnapshotId="universe-fixture",
        membershipDigest=_DIGEST,
        sourceAssetId="resource.fixture",
        sourceCategory="fixture",
        ownerSourcePin=ownerSourcePin,
        ownerCodePin=_SECOND_DIGEST,
        sourcePin=sourcePin,
        queryPin=queryPin,
        entities=entities,
    )
    session = ownerPaging._OwnerSession(
        snapshotId="catalog-fixture",
        contractHash=_DIGEST,
        requestedAssets=1,
        universeSnapshotId="universe-fixture",
        pageMaxRows=100,
        pageMaxBytes=8 * 1024 * 1024,
        pageMaxLogicalBytes=8 * 1024 * 1024,
        pageMaxEntities=entityCount,
        pageTimeoutMs=10_000,
        maxConcurrency=2,
        tasks=(task,),
    )
    # 자식 IPC payload 는 durable state 와 인코딩이 다르다. durable 쪽은 엔티티 목록을
    # 담지 않으므로 자식이 universe 를 재해소해야 하고, 합성 세션에는 그 universe 가 없다.
    return ownerPaging._encodeProcessSession(session)


def testShortBudgetIsRejectedBeforeSpawn() -> None:
    beforePids = {child.pid for child in multiprocessing.active_children() if child.pid is not None}

    outcome = runOwnerPage(
        _sessionPayload(),
        publicDeadline=time.perf_counter() + 8.49,
    )

    afterPids = {child.pid for child in multiprocessing.active_children() if child.pid is not None}
    assert outcome.status == "budgetRejected"
    assert not outcome.spawned
    assert outcome.zeroLive
    assert outcome.errorCode == "OWNER_PROCESS_INSUFFICIENT_WORK_BUDGET"
    assert outcome.elapsedSeconds < 1.0
    assert afterPids == beforePids


def testOversizedInputIsRejectedBeforeSpawn() -> None:
    beforePids = {child.pid for child in multiprocessing.active_children() if child.pid is not None}

    with pytest.raises(ValueError, match="payload 크기"):
        runOwnerPage(
            b"x" * (MAX_STATE_BYTES + 1),
            publicDeadline=time.perf_counter() + 30,
        )

    assert {child.pid for child in multiprocessing.active_children() if child.pid is not None} == beforePids


def testSpawnChildWritesSealedPageAndLeavesNoLiveWorker() -> None:
    outcome = runOwnerPage(
        _sessionPayload(entityCount=2),
        publicDeadline=time.perf_counter() + 30,
    )

    assert outcome.status == "ok", outcome
    assert outcome.page is not None
    assert outcome.page.rowCount == 2
    assert outcome.page.byteCount == len(outcome.page.payload)
    assert outcome.page.payloadDigest == hashlib.sha256(outcome.page.payload).hexdigest()
    assert outcome.ipcFrameCount == 2
    assert outcome.ipcByteCount <= 2 * MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES
    assert outcome.readySeconds is not None
    assert outcome.zeroLive
    assert outcome.pid not in {child.pid for child in multiprocessing.active_children() if child.is_alive()}
    if os.name == "nt":
        assert outcome.jobObjectAttempted
        assert outcome.jobObjectAssigned
    assert not tuple(ownerProcessArtifactRoot().glob("*.arrow"))


@pytest.mark.parametrize(
    ("attribute", "expectedCode"),
    (
        ("_fixtureNetwork", "OFFLINE_NETWORK_BLOCKED"),
        ("_fixturePythonWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixturePolarsWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixtureSubprocessWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
    ),
)
def testOwnerChildSandboxBlocksNetworkSourceAndDescendantWrites(
    tmp_path,
    monkeypatch,
    attribute: str,
    expectedCode: str,
) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path / "home"))
    outputPath = tmp_path / f"{attribute}.blocked"
    try:
        outcome = runOwnerPage(
            _sessionPayload(
                attribute,
                params={"outputPath": str(outputPath)},
            ),
            publicDeadline=time.perf_counter() + 30,
        )
        leaked = outputPath.exists()
    finally:
        outputPath.unlink(missing_ok=True)

    assert outcome.status == "childFailed", outcome
    assert outcome.page is None
    assert outcome.errorCode == expectedCode
    assert outcome.zeroLive
    assert not leaked
    assert not tuple(ownerProcessArtifactRoot().glob("*.arrow"))


@pytest.mark.parametrize(
    ("attribute", "expectedCode"),
    (
        ("_fixtureNetwork", "OFFLINE_NETWORK_BLOCKED"),
        ("_fixturePythonWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
    ),
)
def testOwnerSandboxCodeSurvivesActualSpawnToPublicDataGap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    attribute: str,
    expectedCode: str,
) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path / "home"))
    outputPath = tmp_path / f"{attribute}.blocked"
    session = ownerPaging._decodeSession(
        _sessionPayload(
            attribute,
            params={"outputPath": str(outputPath)},
        )
    )
    task = session.tasks[0]
    activeQuery = dataclasses.replace(
        task.query,
        universe=task.selection,
    )
    monkeypatch.setattr(
        ownerPagingApi,
        "isPageableOwner",
        lambda _descriptor, _query: True,
    )
    monkeypatch.setattr(
        ownerPagingApi,
        "_plannedTask",
        lambda _requestId, _descriptor, _query: task,
    )
    try:
        result = ownerPagingApi.executeInitialOwnerPaging(
            (task.descriptor.assetId,),
            activeQuery,
            requestedAssets=1,
            snapshotId="catalog-fixture",
            contractHash=_DIGEST,
            resolved=(("fixture", task.descriptor, activeQuery),),
            hasPlanningGaps=False,
            deadline=time.perf_counter() + 30,
        )
        leaked = outputPath.exists()
    finally:
        outputPath.unlink(missing_ok=True)

    assert result.status == "failed"
    assert result.gaps[0].code == expectedCode
    assert not leaked
    assert not tuple(ownerProcessArtifactRoot().glob("*.arrow"))


def testOwnerCleanupFailureKeepsPrimaryTypedCause() -> None:
    assert (
        ownerProcess._cleanupFailureCode(
            "OFFLINE_NETWORK_BLOCKED",
            "CONTINUATION_SECURITY_FAILED",
        )
        == "OFFLINE_NETWORK_BLOCKED"
    )
    assert (
        ownerProcess._cleanupFailureCode(
            None,
            "CONTINUATION_SECURITY_FAILED",
        )
        == "CONTINUATION_SECURITY_FAILED"
    )


def testOwnerArtifactWriteFailureRemainsTyped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path / "home"))
    root = ownerProcessArtifacts._ensureArtifactRoot()
    path = root / "result.arrow"
    ownerProcessArtifacts._createArtifact(path, root)
    originalOpen = Path.open

    def failWrite(
        candidate: Path,
        mode: str = "r",
        *args: object,
        **kwargs: object,
    ):
        if candidate == path and mode == "r+b":
            raise OSError("write failed")
        return originalOpen(candidate, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failWrite)
    with pytest.raises(ownerPaging.ContinuationError) as failed:
        ownerProcessArtifacts._writeArtifact(
            path,
            root,
            b"payload",
            maxBytes=1024,
        )

    assert failed.value.code == "CONTINUATION_ARTIFACT_WRITE_FAILED"


def testOwnerArtifactInvalidFailureRemainsTyped(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    path = root / "result.arrow"

    with pytest.raises(ownerPaging.ContinuationError) as failed:
        ownerProcessArtifacts._readArtifact(
            path,
            root,
            byteCount=0,
            digest=_DIGEST,
            maxBytes=1024,
        )

    assert failed.value.code == "CONTINUATION_ARTIFACT_INVALID"


def testOwnerArtifactCleanupFailureRemainsTyped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "result.arrow"
    path.touch()
    originalUnlink = Path.unlink

    def failUnlink(
        candidate: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        if candidate == path:
            raise OSError("cleanup failed")
        originalUnlink(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failUnlink)
    with pytest.raises(ownerPaging.ContinuationError) as failed:
        ownerProcessArtifacts._removeArtifact(path)

    assert failed.value.code == "CONTINUATION_ARTIFACT_CLEANUP_FAILED"


@pytest.mark.parametrize(
    ("status", "expectedCode"),
    (
        ("cleanupFailed", "CONTINUATION_OWNER_PROCESS_CLEANUP_FAILED"),
        ("jobFailed", "CONTINUATION_OWNER_PROCESS_JOB_FAILED"),
        ("childFailed", "CONTINUATION_OWNER_PROCESS_FAILED"),
    ),
)
def testOwnerProcessTerminalFailureStatusRemainsTyped(
    status: str,
    expectedCode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = ownerPaging._decodeSession(_sessionPayload())
    outcome = types.SimpleNamespace(
        status=status,
        page=None,
        zeroLive=False,
        errorCode=None,
    )
    monkeypatch.setattr(
        ownerProcess,
        "runOwnerPage",
        lambda *_args, **_kwargs: outcome,
    )

    with pytest.raises(ownerPaging.ContinuationError) as failed:
        ownerPaging._runOwnerPageProcess(
            session,
            deadline=time.perf_counter() + 30,
        )

    assert failed.value.code == expectedCode


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object 강제 종료 계약")
def testTimedOutOwnerKillsChildAndWorkerBeforeReturn() -> None:
    outcome = runOwnerPage(
        _sessionPayload("_fixtureHang"),
        publicDeadline=time.perf_counter() + 10.0,
    )

    assert outcome.status == "timedOut", outcome
    assert outcome.page is None
    assert outcome.readySeconds is not None
    assert outcome.cleanupTrace[0] == "terminate"
    assert outcome.cleanupTrace[-1] == "join"
    if "kill" in outcome.cleanupTrace:
        assert outcome.cleanupTrace.index("terminate") < outcome.cleanupTrace.index("kill")
        assert outcome.cleanupTrace.index("kill") < outcome.cleanupTrace.index("jobClose")
    assert outcome.cleanupTrace.index("jobClose") < outcome.cleanupTrace.index("join")
    assert outcome.deadlineOvershootSeconds <= 0.1
    assert outcome.zeroLive
    assert not tuple(ownerProcessArtifactRoot().glob("*.arrow"))


@pytest.mark.skipif(os.name != "nt", reason="Windows partial page 원자성 계약")
def testPartialPageThenHangIsNotAcceptedOrCommitted() -> None:
    outcome = runOwnerPage(
        _sessionPayload("_fixturePartialHang", entityCount=2),
        publicDeadline=time.perf_counter() + 10.0,
    )

    assert outcome.status == "timedOut", outcome
    assert outcome.page is None
    assert outcome.ipcFrameCount in {1, 2}
    assert outcome.zeroLive
    assert not tuple(ownerProcessArtifactRoot().glob("*.arrow"))


def testStrictControlFrameRejectsUnknownArtifactAndOversize() -> None:
    artifactId = "a" * 64
    frame = json.dumps(
        {
            "artifactId": "b" * 64,
            "byteCount": 1,
            "digest": _DIGEST,
            "errorCode": None,
            "kind": "result",
            "rowCount": 1,
            "status": "ok",
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")

    with pytest.raises(RuntimeError, match="OWNER_PROCESS_ARTIFACT_ID_MISMATCH"):
        _decodeControlFrame(frame, artifactId=artifactId)
    with pytest.raises(RuntimeError, match="OWNER_PROCESS_JSON_BYTE_BUDGET"):
        _decodeControlFrame(
            b"x" * (MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES + 1),
            artifactId=artifactId,
        )


def _controlFrames(artifactId: str) -> tuple[bytes, bytes]:
    ready = ownerProcess._strictJson(
        {
            "kind": "ready",
            "pid": 1234,
            "threadNativeId": 5678,
        }
    )
    result = ownerProcess._strictJson(
        {
            "artifactId": artifactId,
            "byteCount": 1,
            "digest": _DIGEST,
            "errorCode": None,
            "kind": "result",
            "rowCount": 1,
            "status": "ok",
        }
    )
    return ready, result


def testControlDrainAcceptsReadyResultThenEof() -> None:
    artifactId = "a" * 64
    receiveConnection, sendConnection = multiprocessing.Pipe(duplex=False)
    tracker = ownerProcess._ControlTracker(frames=[])
    try:
        for frame in _controlFrames(artifactId):
            sendConnection.send_bytes(frame)
        sendConnection.close()

        ownerProcess._drainAvailable(
            receiveConnection,
            tracker,
            artifactId=artifactId,
        )
    finally:
        sendConnection.close()
        receiveConnection.close()

    assert tracker.eof
    assert [frame["kind"] for frame in tracker.frames] == ["ready", "result"]


def testControlDrainRejectsActualThirdFrame() -> None:
    artifactId = "a" * 64
    ready, result = _controlFrames(artifactId)
    receiveConnection, sendConnection = multiprocessing.Pipe(duplex=False)
    tracker = ownerProcess._ControlTracker(frames=[])
    try:
        for frame in (ready, result, ready):
            sendConnection.send_bytes(frame)
        sendConnection.close()

        with pytest.raises(RuntimeError, match="OWNER_PROCESS_CONTROL_FRAME_COUNT"):
            ownerProcess._drainAvailable(
                receiveConnection,
                tracker,
                artifactId=artifactId,
            )
    finally:
        sendConnection.close()
        receiveConnection.close()

    assert [frame["kind"] for frame in tracker.frames] == ["ready", "result"]


def testArtifactIdCannotEscapeParentRoot() -> None:
    root = ownerProcessArtifactRoot()

    with pytest.raises(ownerPaging.ContinuationError):
        _artifactPath(root, "../outside")


def testSupervisorSetupFailureRemovesParentArtifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failContext(_method: str):
        raise RuntimeError("setup failure")

    monkeypatch.setattr(
        ownerProcess.multiprocessing,
        "get_context",
        failContext,
    )

    outcome = runOwnerPage(
        _sessionPayload(),
        publicDeadline=time.perf_counter() + 30,
    )

    assert outcome.status == "childFailed"
    assert not outcome.spawned
    assert outcome.zeroLive
    assert not tuple(ownerProcessArtifactRoot().glob("*.arrow"))


def testJobCloseFailureCannotReportZeroLive() -> None:
    job = ownerProcess._WindowsJob()
    job.attempted = True
    job.assigned = True
    job.closedSuccessfully = False
    job.error = "OWNER_PROCESS_JOB_CLOSE_FAILED:1"

    process = types.SimpleNamespace(is_alive=lambda: False)
    assert not ownerProcess._zeroLive(process, None, None, job)


def testConfiguredSymlinkRootIsRejected(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    linkedHome = tmp_path / "linked-home"
    try:
        linkedHome.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("현재 Windows 정책에서 directory symlink를 만들 수 없습니다")
    monkeypatch.setenv("DARTLAB_HOME", str(linkedHome))

    with pytest.raises(ownerPaging.ContinuationError) as error:
        ownerProcess._ensureArtifactRoot()

    assert error.value.code == "CONTINUATION_SECURITY_FAILED"


def testFreshOwnerSpawnReadyMeasurementStaysBelowMinimumWorkWindow() -> None:
    outcomes = tuple(
        runOwnerPage(
            _sessionPayload(),
            publicDeadline=time.perf_counter() + 30,
        )
        for _ in range(8)
    )
    observations = [
        {
            "cleanupTrace": outcome.cleanupTrace,
            "elapsedSeconds": outcome.elapsedSeconds,
            "errorCode": outcome.errorCode,
            "ipcFrameCount": outcome.ipcFrameCount,
            "jobObjectAssigned": outcome.jobObjectAssigned,
            "jobObjectAttempted": outcome.jobObjectAttempted,
            "jobObjectError": outcome.jobObjectError,
            "readySeconds": outcome.readySeconds,
            "status": outcome.status,
            "zeroLive": outcome.zeroLive,
        }
        for outcome in outcomes
    ]
    print(
        json.dumps(
            observations,
            sort_keys=True,
        )
    )
    samples = sorted(outcome.readySeconds for outcome in outcomes if outcome.readySeconds is not None)

    assert all(outcome.status == "ok" for outcome in outcomes), observations
    assert all(outcome.zeroLive for outcome in outcomes), observations
    assert len(samples) == 8
    p50 = samples[math.ceil(0.50 * len(samples)) - 1]
    p95 = samples[math.ceil(0.95 * len(samples)) - 1]
    assert p50 <= p95
    print(
        json.dumps(
            {
                "maximumSeconds": max(samples),
                "minimumWorkSeconds": MIN_OWNER_PROCESS_WORK_SECONDS,
                "p50Seconds": p50,
                "p95Seconds": p95,
                "sampleCount": len(samples),
            },
            sort_keys=True,
        )
    )
    assert p95 < MIN_OWNER_PROCESS_WORK_SECONDS


def testHangingWorkerSelfLimitsWithinItsOwnWorkDeadline() -> None:
    """자식은 자기 work deadline 안에서 스스로 끝난다. 부모 kill 에만 의존하지 않는다."""

    startedAt = time.perf_counter()
    outcome = runOwnerPage(
        _sessionPayload("_fixtureHang"),
        publicDeadline=startedAt + 12.0,
    )
    elapsed = time.perf_counter() - startedAt

    # 부모가 결국 회수하므로 zero-live 는 유지된다.
    assert outcome.zeroLive is True
    assert outcome.page is None
    # 자식이 무한 정지하지 않으므로 공개 기한을 크게 넘기지 않는다.
    assert elapsed < 30.0
    assert outcome.deadlineOvershootSeconds < 15.0
