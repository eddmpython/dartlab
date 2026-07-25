from __future__ import annotations

import hashlib
import os
import sqlite3
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.ipc as ipc
import pytest

from dartlab.data.continuation import (
    ContinuationError,
    arrowSchemaDigest,
    canonicalDigest,
)
from dartlab.data.materialization import (
    GenerationPins,
    MaintenanceBudget,
    MaterializationDirective,
    MaterializationError,
    MaterializationPolicy,
    MaterializationReceipt,
    MaterializationStore,
    PageDraft,
    generationKey,
    parseMaterializationDirective,
)

pytestmark = pytest.mark.unit

SCHEMA = pa.schema(
    [
        pa.field("entity", pa.string(), nullable=False),
        pa.field("value", pa.int64(), nullable=False),
    ]
)


class FakeClock:
    def __init__(self, value: float = 100.0):
        self.value = value
        self.lock = threading.Lock()

    def __call__(self) -> float:
        with self.lock:
            return self.value

    def advance(self, seconds: float) -> None:
        with self.lock:
            self.value += seconds


def digest(label: str) -> str:
    return canonicalDigest({"label": label})


def pins(
    *,
    asset: str = "asset-v1",
    source: str = "source-v1",
    query: str = "query-v1",
    universe: str = "universe-v1",
    contract: str = "contract-v1",
    schemaDigest: str | None = None,
) -> GenerationPins:
    return GenerationPins(
        assetDigest=digest(asset),
        sourceDigest=digest(source),
        queryDigest=digest(query),
        universeDigest=digest(universe),
        contractDigest=digest(contract),
        schemaDigest=schemaDigest or arrowSchemaDigest(SCHEMA),
    )


def draft(*values: int, prefix: str = "entity") -> PageDraft:
    table = pa.Table.from_arrays(
        [
            pa.array(
                [f"{prefix}-{index}" for index in range(len(values))],
                type=pa.string(),
            ),
            pa.array(values, type=pa.int64()),
        ],
        schema=SCHEMA,
    )
    sink = pa.BufferOutputStream()
    with ipc.new_stream(sink, SCHEMA) as writer:
        writer.write_table(table)
    return PageDraft(payload=sink.getvalue().to_pybytes(), rowCount=len(values))


def policy(**overrides: Any) -> MaterializationPolicy:
    values: dict[str, Any] = {
        "maxPageRows": 100,
        "maxPageBytes": 256 * 1024,
        "maxPageLogicalBytes": 256 * 1024,
        "maxPagesPerGeneration": 16,
        "maxRowsPerGeneration": 1_000,
        "maxBytesPerGeneration": 4 * 1024 * 1024,
        "maxManifestBytes": 64 * 1024,
        "builderLeaseSeconds": 3.0,
        "readerLeaseSeconds": 3.0,
        "artifactStageSeconds": 2.0,
        "readyRetentionSeconds": 5.0,
    }
    values.update(overrides)
    return MaterializationPolicy(**values)


def build(
    store: MaterializationStore,
    exactPins: GenerationPins,
    pages: tuple[PageDraft, ...],
    *,
    builderId: str = "builder",
):
    claim = store.claimBuild(exactPins, builderId=builderId)
    assert claim.acquired
    for ordinal, pageDraft in enumerate(pages):
        store.appendPage(claim, ordinal=ordinal, draft=pageDraft)
    root = store.publishReady(claim)
    return claim, root


def processClaim(
    root: str,
    exactPins: GenerationPins,
    storePolicy: MaterializationPolicy,
    resultQueue: Any,
) -> None:
    try:
        store = MaterializationStore(Path(root), policy=storePolicy)
        claim = store.claimBuild(exactPins, builderId="spawned-competitor")
        resultQueue.put(("ok", claim.acquired, claim.ready, claim.epoch))
    except Exception as error:
        resultQueue.put(("error", type(error).__name__))


def processOfflineReplay(
    root: str,
    receiptTree: dict[str, Any],
    storePolicy: MaterializationPolicy,
    resultQueue: Any,
) -> None:
    try:
        directive = parseMaterializationDirective({"mode": "offline", "receipt": receiptTree})
        assert directive.receipt is not None
        store = MaterializationStore(Path(root), policy=storePolicy)
        generation = store.readReceipt(directive.receipt)
        resultQueue.put(
            (
                "ok",
                generation.terminalRootDigest,
                generation.pages[0].payloadDigest,
                hashlib.sha256(generation.pages[0].payload).hexdigest(),
                generation.rowCount,
                0,
                0,
            )
        )
    except Exception as error:
        resultQueue.put(("error", type(error).__name__))


def testGenerationKeyBindsEveryExactPinAndSourceDriftCreatesNewGeneration() -> None:
    baseline = pins()
    baselineKey = generationKey(baseline)

    assert generationKey(pins()) == baselineKey
    assert {
        generationKey(pins(asset="asset-v2")),
        generationKey(pins(source="source-v2")),
        generationKey(pins(query="query-v2")),
        generationKey(pins(universe="universe-v2")),
        generationKey(pins(contract="contract-v2")),
        generationKey(pins(schemaDigest=digest("schema-v2"))),
    }.isdisjoint({baselineKey})


def testBuildingIsInvisibleAndReadyCommitsOrderedPagesAndRoot(
    tmp_path: Path,
) -> None:
    store = MaterializationStore(tmp_path / "materialization", policy=policy())
    exactPins = pins()
    first = draft(1, 2, prefix="first")
    second = draft(3, prefix="second")
    claim = store.claimBuild(exactPins, builderId="builder-a")
    store.appendPage(claim, ordinal=0, draft=first)
    store.appendPage(claim, ordinal=1, draft=second)

    assert store.readReady(exactPins) is None

    terminalRoot = store.publishReady(claim)
    ready = store.readReady(exactPins)
    assert ready is not None
    assert ready.terminalRootDigest == terminalRoot
    assert ready.generationKey == generationKey(exactPins)
    assert [page.ordinal for page in ready.pages] == [0, 1]
    assert [page.payload for page in ready.pages] == [first.payload, second.payload]
    assert ready.rowCount == 3
    assert ready.byteCount == len(first.payload) + len(second.payload)


def testReadyReplayInvokesNeitherOwnerNorSource(tmp_path: Path) -> None:
    store = MaterializationStore(tmp_path / "materialization", policy=policy())
    exactPins = pins()
    calls = {"owner": 0, "source": 0}

    def coldOwner():
        calls["owner"] += 1
        calls["source"] += 1
        yield draft(1, 2, 3)

    cold = store.materializeOrReplay(
        exactPins,
        builderId="cold-builder",
        ownerProducer=coldOwner,
    )

    def forbiddenOwner():
        calls["owner"] += 1
        calls["source"] += 1
        raise AssertionError("READY replay에서 owner/source가 호출됐습니다")
        yield draft(99)

    warm = store.materializeOrReplay(
        exactPins,
        builderId="warm-reader",
        ownerProducer=forbiddenOwner,
    )
    assert not cold.replayed
    assert warm.replayed
    assert calls == {"owner": 1, "source": 1}
    assert warm.generation.terminalRootDigest == cold.generation.terminalRootDigest


@pytest.mark.parametrize(
    "methodName",
    ("materializeOrReplay", "materializeOrReplayHandle"),
)
def testProducerFailureImmediatelyAbortsBuildingAndPreservesTypedCause(
    tmp_path: Path,
    methodName: str,
) -> None:
    store = MaterializationStore(
        tmp_path / "materialization",
        policy=policy(),
    )
    exactPins = pins(query=f"producer-failure-{methodName}")

    def failingOwner():
        yield draft(1)
        raise ContinuationError("CONTINUATION_SOURCE_STALE")

    materialize = getattr(store, methodName)
    with pytest.raises(ContinuationError) as failed:
        materialize(
            exactPins,
            builderId="failed-builder",
            ownerProducer=failingOwner,
        )

    assert failed.value.code == "CONTINUATION_SOURCE_STALE"
    with sqlite3.connect(store.databasePath) as connection:
        assert (
            connection.execute("SELECT count(*) FROM materialization_generations WHERE status='BUILDING'").fetchone()[0]
            == 0
        )
        assert connection.execute("SELECT count(*) FROM materialization_pages").fetchone()[0] == 0
    recovered = store.claimBuild(
        exactPins,
        builderId="recovered-builder",
    )
    assert recovered.acquired
    assert recovered.epoch == 1


def testAbortCleanupFailureCannotOverwriteProducerCause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MaterializationStore(
        tmp_path / "materialization",
        policy=policy(),
    )

    def failingOwner():
        yield draft(1)
        raise RuntimeError("primary producer failure")

    def failingAbort(_claim: object) -> None:
        raise MaterializationError("MATERIALIZATION_CORRUPT")

    monkeypatch.setattr(store, "abortBuild", failingAbort)
    with pytest.raises(RuntimeError, match="primary producer failure"):
        store.materializeOrReplayHandle(
            pins(query="abort-cleanup-failure"),
            builderId="failed-builder",
            ownerProducer=failingOwner,
        )


def testSingleBuilderLeaseAndCrashRecoveryUseNewEpoch(tmp_path: Path) -> None:
    clock = FakeClock()
    store = MaterializationStore(
        tmp_path / "materialization",
        policy=policy(),
        clock=clock,
    )
    exactPins = pins()
    stale = store.claimBuild(exactPins, builderId="builder-a")
    stalePage = store.appendPage(
        stale,
        ordinal=0,
        draft=draft(1, prefix="stale"),
    )
    blocked = store.claimBuild(exactPins, builderId="builder-b")
    assert not blocked.acquired and not blocked.ready
    assert store.readReady(exactPins) is None

    clock.advance(4.0)
    recovered = store.claimBuild(exactPins, builderId="builder-b")
    assert recovered.acquired and recovered.epoch == stale.epoch + 1
    with pytest.raises(MaterializationError, match="lease") as lost:
        store.renewBuild(stale)
    assert lost.value.code == "MATERIALIZATION_LEASE_LOST"

    recoveredDraft = draft(2, prefix="recovered")
    store.appendPage(recovered, ordinal=0, draft=recoveredDraft)
    store.publishReady(recovered)
    ready = store.readReady(exactPins)
    assert ready is not None
    assert [page.payload for page in ready.pages] == [recoveredDraft.payload]

    clock.advance(3.0)
    report = store.maintain(
        MaintenanceBudget(
            maxReaderLeases=10,
            maxGenerationTransitions=10,
            maxPageReferences=10,
            maxArtifacts=10,
        )
    )
    assert report.artifactsDeleted >= 1
    assert not store.cas.pathForDigest(stalePage.payloadDigest).exists()


def testCrashBeforeReadyCommitLeavesGenerationInvisible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MaterializationStore(tmp_path / "materialization", policy=policy())
    exactPins = pins()
    claim = store.claimBuild(exactPins, builderId="builder")
    store.appendPage(claim, ordinal=0, draft=draft(1))
    originalCommit = store._commitReady

    def crashBeforeCommit(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("simulated process crash")

    monkeypatch.setattr(store, "_commitReady", crashBeforeCommit)
    with pytest.raises(RuntimeError, match="simulated"):
        store.publishReady(claim)
    assert store.readReady(exactPins) is None

    monkeypatch.setattr(store, "_commitReady", originalCommit)
    store.publishReady(claim)
    assert store.readReady(exactPins) is not None


def testConcurrentBuildersAndReadersConvergeOnOneRoot(tmp_path: Path) -> None:
    store = MaterializationStore(tmp_path / "materialization", policy=policy())
    exactPins = pins()
    owner = store.claimBuild(exactPins, builderId="owner")

    def competingClaim(index: int):
        return store.claimBuild(exactPins, builderId=f"competitor-{index}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        blocked = tuple(executor.map(competingClaim, range(12)))
    assert all(not claim.acquired and not claim.ready for claim in blocked)

    store.appendPage(owner, ordinal=0, draft=draft(1, 2))
    store.appendPage(owner, ordinal=1, draft=draft(3, 4))
    terminalRoot = store.publishReady(owner)

    def readRoot(_index: int) -> str:
        ready = store.readReady(exactPins)
        assert ready is not None and ready.rowCount == 4
        return ready.terminalRootDigest

    with ThreadPoolExecutor(max_workers=8) as executor:
        roots = tuple(executor.map(readRoot, range(24)))
    assert set(roots) == {terminalRoot}


def testSpawnedProcessCannotStealLiveBuilderLease(tmp_path: Path) -> None:
    root = tmp_path / "materialization"
    storePolicy = policy(builderLeaseSeconds=20.0)
    exactPins = pins()
    store = MaterializationStore(root, policy=storePolicy)
    owner = store.claimBuild(exactPins, builderId="main-owner")
    context = get_context("spawn")
    resultQueue = context.Queue()
    process = context.Process(
        target=processClaim,
        args=(str(root), exactPins, storePolicy, resultQueue),
    )
    process.start()
    process.join(timeout=30.0)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5.0)
        pytest.fail("spawned builder process가 제한 시간 안에 종료되지 않았습니다")
    assert process.exitcode == 0
    assert resultQueue.get(timeout=5.0) == (
        "ok",
        False,
        False,
        owner.epoch,
    )


def testFreshSpawnedProcessReplaysReceiptOfflineWithNoOwnerOrSource(
    tmp_path: Path,
) -> None:
    root = tmp_path / "materialization"
    storePolicy = policy(builderLeaseSeconds=20.0)
    store = MaterializationStore(root, policy=storePolicy)
    exactPins = pins(query="external-process-query")
    built = store.materializeOrReplay(
        exactPins,
        builderId="process-a-owner",
        ownerProducer=lambda: (draft(11, 12, prefix="process-a"),),
    ).generation
    receipt = built.receipt
    context = get_context("spawn")
    resultQueue = context.Queue()
    process = context.Process(
        target=processOfflineReplay,
        args=(str(root), receipt.asTree(), storePolicy, resultQueue),
    )
    process.start()
    process.join(timeout=30.0)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5.0)
        pytest.fail("spawned offline reader가 제한 시간 안에 종료되지 않았습니다")

    assert process.exitcode == 0
    assert resultQueue.get(timeout=5.0) == (
        "ok",
        receipt.terminalRootDigest,
        built.pages[0].payloadDigest,
        hashlib.sha256(built.pages[0].payload).hexdigest(),
        built.rowCount,
        0,
        0,
    )


def testArrowAndLedgerCorruptionFailClosed(tmp_path: Path) -> None:
    store = MaterializationStore(tmp_path / "materialization", policy=policy())
    exactPins = pins()
    build(store, exactPins, (draft(1, 2),))
    ready = store.readReady(exactPins)
    assert ready is not None

    with sqlite3.connect(store.databasePath) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE materialization_pages SET row_count=row_count + 1 WHERE generation_key=? AND ordinal=0",
                (generationKey(exactPins),),
            )

    pagePath = store.cas.pathForDigest(ready.pages[0].payloadDigest)
    payload = bytearray(pagePath.read_bytes())
    payload[len(payload) // 2] ^= 0x01
    pagePath.write_bytes(payload)
    with pytest.raises(MaterializationError) as corrupted:
        store.readReady(exactPins)
    assert corrupted.value.code == "MATERIALIZATION_CORRUPT"


def testGcHonorsEveryPerCallBoundAndEventuallyCollects(tmp_path: Path) -> None:
    clock = FakeClock()
    store = MaterializationStore(
        tmp_path / "materialization",
        policy=policy(),
        clock=clock,
    )
    firstPins = pins(query="query-first")
    secondPins = pins(query="query-second")
    build(
        store,
        firstPins,
        (draft(1, prefix="first-a"), draft(2, prefix="first-b")),
        builderId="first-builder",
    )
    build(
        store,
        secondPins,
        (draft(3, prefix="second-a"), draft(4, prefix="second-b")),
        builderId="second-builder",
    )
    clock.advance(6.0)
    bounds = MaintenanceBudget(
        maxReaderLeases=1,
        maxGenerationTransitions=1,
        maxPageReferences=1,
        maxArtifacts=1,
    )

    for _index in range(20):
        report = store.maintain(bounds)
        assert report.readerLeasesDeleted <= 1
        assert report.generationsMarked <= 1
        assert report.pageReferencesReleased <= 1
        assert report.generationsDeleted <= 1
        assert report.artifactsDeleted <= 1
        if store.readReady(firstPins) is None and store.readReady(secondPins) is None:
            with sqlite3.connect(store.databasePath) as connection:
                generationCount = connection.execute("SELECT COUNT(*) FROM materialization_generations").fetchone()[0]
                artifactCount = connection.execute("SELECT COUNT(*) FROM materialization_artifacts").fetchone()[0]
            if generationCount == 0 and artifactCount == 0:
                break
    else:
        pytest.fail("bounded GC가 유한 반복 안에 수렴하지 않았습니다")
    assert store.cas.iterDigests() == ()


def testSqliteContainsNoRawQueryOwnerTokenOrArrowPayload(tmp_path: Path) -> None:
    rawQuery = "query-plaintext-never-in-ledger"
    rawOwner = "owner-bearer-never-in-ledger"
    rawToken = "opaque-continuation-never-in-ledger"
    rawPayload = "arrow-plaintext-never-in-ledger"
    exactPins = pins(query=rawQuery)
    store = MaterializationStore(tmp_path / "materialization", policy=policy())

    def owner():
        assert rawToken
        yield draft(7, prefix=rawPayload)

    store.materializeOrReplay(
        exactPins,
        builderId=rawOwner,
        ownerProducer=owner,
    )
    databaseBytes = b""
    for path in (
        store.databasePath,
        Path(f"{store.databasePath}-wal"),
        Path(f"{store.databasePath}-shm"),
    ):
        if path.exists():
            databaseBytes += path.read_bytes()
    for forbidden in (rawQuery, rawOwner, rawToken, rawPayload):
        assert forbidden.encode("utf-8") not in databaseBytes
    ready = store.readReady(exactPins)
    assert ready is not None
    assert rawPayload.encode("utf-8") in ready.pages[0].payload


def testPrivateRootRejectsSymlinkOrWindowsReparsePoint(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    linked = tmp_path / "linked"
    try:
        os.symlink(target, linked, target_is_directory=True)
    except (NotImplementedError, OSError):
        if os.name != "nt":
            pytest.skip("현재 환경에서 directory symlink 생성이 허용되지 않습니다")
        created = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(linked), str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        if created.returncode != 0:
            pytest.skip("현재 Windows 설정에서 reparse point 생성이 허용되지 않습니다")
        isJunction = getattr(linked, "is_junction", None)
        if not callable(isJunction) or not isJunction():
            pytest.fail("Windows junction을 reparse point로 판독하지 못했습니다")

    try:
        with pytest.raises(MaterializationError) as rejected:
            MaterializationStore(linked, policy=policy())
        assert rejected.value.code == "MATERIALIZATION_SECURITY"
    finally:
        isJunction = getattr(linked, "is_junction", None)
        if callable(isJunction) and isJunction():
            linked.rmdir()
        else:
            linked.unlink(missing_ok=True)


def testReceiptAndMappingDirectiveProvideExactOfflineIdentity(
    tmp_path: Path,
) -> None:
    store = MaterializationStore(tmp_path / "materialization", policy=policy())
    exactPins = pins()
    outcome = store.materializeOrReplay(
        exactPins,
        builderId="builder",
        ownerProducer=lambda: (draft(1),),
    )
    receipt = outcome.generation.receipt
    restored = MaterializationReceipt.fromTree(receipt.asTree())
    directive = parseMaterializationDirective({"mode": "offline", "receipt": restored.asTree()})

    assert directive == MaterializationDirective("offline", restored)
    assert store.readReceipt(restored).terminalRootDigest == receipt.terminalRootDigest
    with pytest.raises(ValueError, match="receipt"):
        parseMaterializationDirective("offline")


def testLedgerRegistrationRemainsLockedThroughCasPublication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MaterializationStore(
        tmp_path / "materialization",
        policy=policy(artifactStageSeconds=60.0),
    )
    payload = draft(1).payload
    entered = threading.Event()
    release = threading.Event()
    originalPut = store.cas.putBytes

    def blockedPut(value: bytes) -> str:
        entered.set()
        assert release.wait(timeout=10.0)
        return originalPut(value)

    monkeypatch.setattr(store.cas, "putBytes", blockedPut)
    with ThreadPoolExecutor(max_workers=2) as executor:
        publishFuture = executor.submit(store._prepareArtifact, payload)
        assert entered.wait(timeout=10.0)
        maintenanceFuture = executor.submit(store.maintain)
        time.sleep(0.1)
        assert not maintenanceFuture.done()
        release.set()
        artifactDigest = publishFuture.result(timeout=10.0)
        maintenanceFuture.result(timeout=10.0)
    assert store.cas.pathForDigest(artifactDigest).exists()


def testInlineReaderRenewalFailsClosedWithoutBackgroundThread(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MaterializationStore(tmp_path / "materialization", policy=policy())
    exactPins = pins()
    build(store, exactPins, (draft(1), draft(2)))
    originalRenew = store._renewReader
    calls = 0

    def failSecondRenew(key: str, readerDigest: str) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise MaterializationError("MATERIALIZATION_NOT_READY")
        originalRenew(key, readerDigest)

    monkeypatch.setattr(store, "_renewReader", failSecondRenew)
    with pytest.raises(MaterializationError) as failed:
        store.readReady(exactPins)
    assert failed.value.code == "MATERIALIZATION_NOT_READY"
    assert not any(thread.name.startswith("materialization-") for thread in threading.enumerate())


def testReceiptPageBindsHandleAndPageAcrossGcRace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    store = MaterializationStore(
        tmp_path / "materialization",
        policy=policy(readyRetentionSeconds=5.0),
        clock=clock,
    )
    exactPins = pins(query="gc-race")
    _, terminalRoot = build(store, exactPins, (draft(1), draft(2)))
    receipt = MaterializationReceipt(
        generationKey=generationKey(exactPins),
        terminalRootDigest=terminalRoot,
        pins=exactPins,
    )
    clock.advance(6.0)
    originalRead = store._readValidatedPage
    reports = []

    def maintainDuringPageRead(*args: Any, **kwargs: Any):
        reports.append(store.maintain())
        return originalRead(*args, **kwargs)

    monkeypatch.setattr(store, "_readValidatedPage", maintainDuringPageRead)
    handle, page = store.readReceiptPage(receipt, 1)

    assert handle.receipt == receipt
    assert handle.pageCount == 2
    assert page.ordinal == 1
    assert reports[0].generationsMarked == 0
    assert store.maintain().generationsMarked == 1
