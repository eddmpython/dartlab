"""Production continuation ledger, replay, secrecy, and GC locks."""

from __future__ import annotations

import math
import sqlite3
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path

import pyarrow as pa
import pytest

import dartlab.dataHub.continuation.continuationStore as continuationStoreModule
from dartlab.dataHub.continuation import (
    ContinuationError,
    ContinuationMaintenanceBudget,
    ContinuationPins,
    ContinuationPolicy,
    ContinuationQueryState,
    ContinuationStore,
    PageEnvelope,
    arrowSchemaDigest,
    bytesDigest,
    canonicalDigest,
    canonicalJsonBytes,
)


def _queryPayload() -> bytes:
    return canonicalJsonBytes({"assets": ["scan.account"], "markets": ["KR", "US"]})


def _schema() -> pa.Schema:
    return pa.schema((pa.field("entityId", pa.string()), pa.field("value", pa.int64())))


def _pins() -> ContinuationPins:
    return ContinuationPins(
        sourceDigest=canonicalDigest({"snapshot": "dart-edgar-1"}),
        queryDigest=bytesDigest(_queryPayload()),
        contractDigest=canonicalDigest({"asset": "scan.account", "version": 1}),
        schemaDigest=arrowSchemaDigest(_schema()),
    )


def _policy(**overrides) -> ContinuationPolicy:
    values = {
        "maxPageRows": 3,
        "maxPageBytes": 1_000_000,
        "maxStateBytes": 1024,
        "tokenTtlSeconds": 60,
        "leaseSeconds": 2,
        "waitSeconds": 5,
        "pollSeconds": 0.005,
        "pruneGraceSeconds": 2,
    }
    values.update(overrides)
    return ContinuationPolicy(**values)


def _state(cursor: bytes = b"offset:0") -> ContinuationQueryState:
    return ContinuationQueryState(_queryPayload(), cursor)


def _payload(values: tuple[int, ...] = (1, 2)) -> bytes:
    table = pa.Table.from_arrays(
        [pa.array([f"entity:{value}" for value in values], type=pa.string()), pa.array(values, type=pa.int64())],
        schema=_schema(),
    )
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()


def _redeemFromProcess(rootValue: str, token: str) -> tuple[str, bool]:
    root = Path(rootValue)
    store = ContinuationStore(root / "control", _policy())
    countPath = root / "owner.sqlite"
    startedPath = root / "owner.started"

    def owner(state: ContinuationQueryState) -> PageEnvelope:
        with sqlite3.connect(countPath, timeout=10) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY AUTOINCREMENT)")
            connection.execute("INSERT INTO calls DEFAULT VALUES")
        startedPath.touch()
        time.sleep(0.6)
        return PageEnvelope(_payload(), 2, _state(state.cursorPayload + b":next"))

    page = store.redeem(token, _pins(), materialize=owner)
    return page.pageDigest, page.replayed


def testLoadContextRestoresPrivateStateAndPinsAfterRestart(tmp_path):
    root = tmp_path / "control"
    first = ContinuationStore(root, _policy())
    issued = first.issue(_state(b"private-cursor:0"), _pins())

    reopened = ContinuationStore(root, _policy())
    context = reopened.loadContext(issued.token)

    assert context.state == _state(b"private-cursor:0")
    assert context.pins == _pins()
    assert context.tokenDigest == issued.tokenDigest
    assert issued.token not in repr(context)
    assert "private-cursor:0" not in repr(context)


def testSqliteAndReprsNeverContainTokenQueryCursorOrPagePlaintext(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    query = _queryPayload()
    cursor = b"private-cursor:sqlite-check"
    issued = store.issue(ContinuationQueryState(query, cursor), _pins())
    pagePayload = _payload((7,))
    page = store.redeem(
        issued.token,
        _pins(),
        materialize=lambda state: PageEnvelope(pagePayload, 1),
    )

    with sqlite3.connect(store.databasePath) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(continuations)")}
    assert "token" not in columns
    assert "query" not in columns
    assert "cursor" not in columns
    sqliteBytes = b"".join(path.read_bytes() for path in store.root.glob("continuations.sqlite*") if path.is_file())
    assert issued.token.encode("ascii") not in sqliteBytes
    assert query not in sqliteBytes
    assert cursor not in sqliteBytes
    assert pagePayload not in sqliteBytes
    rendered = repr(issued) + repr(page)
    assert issued.token not in rendered
    assert "entity:7" not in rendered


@pytest.mark.parametrize(
    ("fieldName", "code"),
    (
        ("sourceDigest", "CONTINUATION_SOURCE_STALE"),
        ("queryDigest", "CONTINUATION_QUERY_STALE"),
        ("contractDigest", "CONTINUATION_CONTRACT_STALE"),
        ("schemaDigest", "CONTINUATION_SCHEMA_STALE"),
    ),
)
def testEveryPinMismatchFailsBeforeOwner(tmp_path, fieldName, code):
    store = ContinuationStore(tmp_path / fieldName, _policy())
    issued = store.issue(_state(), _pins())
    stalePins = replace(_pins(), **{fieldName: canonicalDigest({"drift": fieldName})})
    called = False

    def owner(state: ContinuationQueryState) -> PageEnvelope:
        nonlocal called
        called = True
        return PageEnvelope(_payload((1,)), 1)

    with pytest.raises(ContinuationError) as error:
        store.redeem(issued.token, stalePins, materialize=owner)
    assert error.value.code == code
    assert called is False


def testInvalidUnknownAndExpiredTokensHaveDistinctJudgements(tmp_path):
    now = [100.0]
    store = ContinuationStore(tmp_path / "control", _policy(), clock=lambda: now[0])
    issued = store.issue(_state(), _pins(), ttlSeconds=2)

    with pytest.raises(ContinuationError) as malformed:
        store.loadContext("not-a-token")
    assert malformed.value.code == "CONTINUATION_INVALID"

    with pytest.raises(ContinuationError) as unknown:
        store.loadContext("dltc1." + "A" * 43)
    assert unknown.value.code == "CONTINUATION_INVALID"

    now[0] = 102.0
    with pytest.raises(ContinuationError) as expired:
        store.loadContext(issued.token)
    assert expired.value.code == "CONTINUATION_EXPIRED"


def testStateBudgetIsEnforcedOnIssueLoadAndNextPage(tmp_path):
    smallPolicy = _policy(maxStateBytes=96)
    small = ContinuationStore(tmp_path / "small", smallPolicy)
    with pytest.raises(ContinuationError) as issueError:
        small.issue(_state(b"x" * 200), _pins())
    assert issueError.value.code == "CONTINUATION_STATE_BUDGET"

    large = ContinuationStore(tmp_path / "large", _policy(maxStateBytes=1024))
    issued = large.issue(_state(b"x" * 200), _pins())
    reopenedSmall = ContinuationStore(tmp_path / "large", smallPolicy)
    with pytest.raises(ContinuationError) as loadError:
        reopenedSmall.loadContext(issued.token)
    assert loadError.value.code == "CONTINUATION_STATE_BUDGET"

    retryStore = ContinuationStore(tmp_path / "retry", smallPolicy)
    retryIssued = retryStore.issue(_state(), _pins())
    with pytest.raises(ContinuationError) as nextError:
        retryStore.redeem(
            retryIssued.token,
            _pins(),
            materialize=lambda state: PageEnvelope(_payload((1,)), 1, _state(b"z" * 200)),
        )
    assert nextError.value.code == "CONTINUATION_STATE_BUDGET"
    recovered = retryStore.redeem(
        retryIssued.token,
        _pins(),
        materialize=lambda state: PageEnvelope(_payload((1,)), 1),
    )
    assert recovered.rowCount == 1


def testOwnerExceptionIsWrappedWithoutCursorLeakAndRetryWorks(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    issued = store.issue(_state(b"owner-secret-cursor"), _pins())

    def failingOwner(state: ContinuationQueryState) -> PageEnvelope:
        raise RuntimeError(state.cursorPayload.decode())

    with pytest.raises(ContinuationError) as error:
        store.redeem(issued.token, _pins(), materialize=failingOwner)
    assert error.value.code == "CONTINUATION_OWNER_FAILED"
    assert "owner-secret-cursor" not in str(error.value)
    assert "owner-secret-cursor" not in repr(error.value)

    page = store.redeem(
        issued.token,
        _pins(),
        materialize=lambda state: PageEnvelope(_payload((1,)), 1),
    )
    assert page.rowCount == 1


def testActualArrowRowsAndSchemaAreVerifiedBeforeCommit(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    issued = store.issue(_state(), _pins())

    with pytest.raises(ContinuationError) as rowError:
        store.redeem(
            issued.token,
            _pins(),
            materialize=lambda state: PageEnvelope(_payload((1, 2)), 1),
        )
    assert rowError.value.code == "CONTINUATION_PAYLOAD_ROW_MISMATCH"

    wrongTable = pa.table({"different": [1]})
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, wrongTable.schema) as writer:
        writer.write_table(wrongTable)
    wrongPayload = sink.getvalue().to_pybytes()
    with pytest.raises(ContinuationError) as schemaError:
        store.redeem(
            issued.token,
            _pins(),
            materialize=lambda state: PageEnvelope(wrongPayload, 1),
        )
    assert schemaError.value.code == "CONTINUATION_PAYLOAD_SCHEMA_MISMATCH"


def testReplayIsIdempotentAndChildRestoresPinnedQueryAndCursor(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    issued = store.issue(_state(), _pins())
    calls = []

    def firstOwner(state: ContinuationQueryState) -> PageEnvelope:
        calls.append(state.cursorPayload)
        return PageEnvelope(_payload((1, 2, 3)), 3, _state(b"offset:3"))

    first = store.redeem(issued.token, _pins(), materialize=firstOwner)
    replay = store.redeem(
        issued.token,
        _pins(),
        materialize=lambda state: pytest.fail("replay called owner"),
    )

    assert calls == [b"offset:0"]
    assert first.replayed is False
    assert replay.replayed is True
    assert replay.payload == first.payload
    assert replay.pageRef == first.pageRef
    assert replay.resultDigest == first.resultDigest
    assert replay.nextToken == first.nextToken

    observed = []
    second = store.redeem(
        first.nextToken or "",
        _pins(),
        materialize=lambda state: observed.append(state) or PageEnvelope(_payload((4,)), 1),
    )
    assert observed == [_state(b"offset:3")]
    assert second.nextToken is None
    assert store.verifyIntegrity()


def testConcurrentThreadsInvokeOneOwnerAndReplayOnePage(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    issued = store.issue(_state(), _pins())
    callCount = 0
    countLock = threading.Lock()
    ownerStarted = threading.Event()

    def owner(state: ContinuationQueryState) -> PageEnvelope:
        nonlocal callCount
        with countLock:
            callCount += 1
        ownerStarted.set()
        time.sleep(0.12)
        return PageEnvelope(_payload(), 2, _state(b"offset:2"))

    with ThreadPoolExecutor(max_workers=12) as pool:
        firstFuture = pool.submit(store.redeem, issued.token, _pins(), materialize=owner)
        assert ownerStarted.wait(timeout=2)
        others = [pool.submit(store.redeem, issued.token, _pins(), materialize=owner) for _ in range(11)]
        pages = [firstFuture.result(timeout=5), *(future.result(timeout=5) for future in others)]

    assert callCount == 1
    assert {page.pageDigest for page in pages} == {pages[0].pageDigest}
    assert {page.nextToken for page in pages} == {pages[0].nextToken}
    assert sum(not page.replayed for page in pages) == 1
    assert sum(page.replayed for page in pages) == 11


@pytest.mark.parametrize("waitSeconds", (True, "1", -1, math.nan, math.inf, -math.inf))
def testCallerWaitBudgetRejectsInvalidValues(tmp_path, waitSeconds):
    store = ContinuationStore(tmp_path / "control", _policy())
    issued = store.issue(_state(), _pins())

    with pytest.raises(ValueError):
        store.redeem(
            issued.token,
            _pins(),
            materialize=lambda state: PageEnvelope(_payload((1,)), 1),
            waitSeconds=waitSeconds,
        )


def testCallerZeroWaitAllowsOneImmediateClaim(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    issued = store.issue(_state(), _pins())

    page = store.redeem(
        issued.token,
        _pins(),
        materialize=lambda _state: PageEnvelope(_payload((1,)), 1),
        waitSeconds=0,
    )

    assert page.rowCount == 1
    assert not page.replayed


def testCallerWaitBudgetCapsBusySleepToRemainingTime(tmp_path, monkeypatch):
    clockValue = [100.0]
    monotonic = [10.0]
    sleeps = []
    store = ContinuationStore(
        tmp_path / "control",
        _policy(waitSeconds=5, pollSeconds=1),
        clock=lambda: clockValue[0],
    )
    issued = store.issue(_state(), _pins())
    with sqlite3.connect(store.databasePath) as connection:
        connection.execute(
            "UPDATE continuations SET status='RUNNING', owner_id='other-owner', lease_until=200 WHERE token_digest=?",
            (issued.tokenDigest,),
        )

    monkeypatch.setattr(continuationStoreModule.time, "monotonic", lambda: monotonic[0])

    def advance(seconds: float) -> None:
        sleeps.append(seconds)
        monotonic[0] += seconds

    monkeypatch.setattr(continuationStoreModule.time, "sleep", advance)
    with pytest.raises(ContinuationError) as error:
        store.redeem(
            issued.token,
            _pins(),
            materialize=lambda state: pytest.fail("busy waiter called owner"),
            waitSeconds=0.25,
        )

    assert error.value.code == "CONTINUATION_BUSY"
    assert sleeps == [0.25]


def testCallerWaitBudgetCapsSqliteLockWaitBeforeOwnerExecution(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy(waitSeconds=5))
    issued = store.issue(_state(), _pins())
    lockReady = threading.Event()

    def holdWriteLock() -> None:
        with sqlite3.connect(store.databasePath) as connection:
            connection.execute("BEGIN IMMEDIATE")
            lockReady.set()
            time.sleep(0.3)

    ownerCalled = False

    def owner(_state: ContinuationQueryState) -> PageEnvelope:
        nonlocal ownerCalled
        ownerCalled = True
        return PageEnvelope(_payload((1,)), 1)

    with ThreadPoolExecutor(max_workers=1) as pool:
        holder = pool.submit(holdWriteLock)
        assert lockReady.wait(timeout=1)
        started = time.monotonic()
        with pytest.raises(ContinuationError) as error:
            store.redeem(issued.token, _pins(), materialize=owner, waitSeconds=0.02)
        elapsed = time.monotonic() - started
        holder.result(timeout=1)

    assert error.value.code == "CONTINUATION_BUSY"
    assert elapsed < 0.2
    assert not ownerCalled


def testLeaseHeartbeatStaysActiveWhileCommitStagesArtifacts(tmp_path, monkeypatch):
    store = ContinuationStore(
        tmp_path / "control",
        _policy(leaseSeconds=0.2, waitSeconds=3, pollSeconds=0.005),
    )
    issued = store.issue(_state(), _pins())
    realStage = store._stageArtifact
    stageStarted = threading.Event()
    stageCalls = 0
    ownerCalls = 0
    ownerLock = threading.Lock()

    def slowFirstStage(payload: bytes, *, now: float):
        nonlocal stageCalls
        stageCalls += 1
        if stageCalls == 1:
            stageStarted.set()
            time.sleep(0.7)
        return realStage(payload, now=now)

    def owner(state: ContinuationQueryState) -> PageEnvelope:
        nonlocal ownerCalls
        with ownerLock:
            ownerCalls += 1
        return PageEnvelope(_payload(), 2)

    monkeypatch.setattr(store, "_stageArtifact", slowFirstStage)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(store.redeem, issued.token, _pins(), materialize=owner)
        assert stageStarted.wait(timeout=1)
        second = pool.submit(store.redeem, issued.token, _pins(), materialize=owner)
        pages = (first.result(timeout=3), second.result(timeout=3))

    assert ownerCalls == 1
    assert pages[0].pageDigest == pages[1].pageDigest
    assert sum(page.replayed for page in pages) == 1


def testCommitRechecksTokenTtlAfterArtifactStaging(tmp_path, monkeypatch):
    clockValue = [100.0]
    store = ContinuationStore(tmp_path / "control", _policy(), clock=lambda: clockValue[0])
    issued = store.issue(_state(), _pins(), ttlSeconds=2)
    realStage = store._stageArtifact
    stageCalls = 0

    def materialize(state: ContinuationQueryState) -> PageEnvelope:
        return PageEnvelope(_payload(), 2)

    def stageAndExpire(payload: bytes, *, now: float):
        nonlocal stageCalls
        stageCalls += 1
        staged = realStage(payload, now=now)
        if stageCalls == 1:
            clockValue[0] = 103.0
        return staged

    monkeypatch.setattr(store, "_stageArtifact", stageAndExpire)
    with pytest.raises(ContinuationError) as error:
        store.redeem(issued.token, _pins(), materialize=materialize)

    assert error.value.code == "CONTINUATION_EXPIRED"


def testConcurrentProcessesInvokeOneOwnerAndReplayOnePage(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    issued = store.issue(_state(b"process-offset:0"), _pins())
    startedPath = tmp_path / "owner.started"

    with ProcessPoolExecutor(max_workers=6, mp_context=get_context("spawn")) as pool:
        firstFuture = pool.submit(_redeemFromProcess, str(tmp_path), issued.token)
        deadline = time.monotonic() + 10
        while not startedPath.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert startedPath.exists()
        others = [pool.submit(_redeemFromProcess, str(tmp_path), issued.token) for _ in range(5)]
        results = [firstFuture.result(timeout=20), *(future.result(timeout=20) for future in others)]

    with sqlite3.connect(tmp_path / "owner.sqlite") as connection:
        callCount = connection.execute("SELECT count(*) FROM calls").fetchone()[0]
    assert callCount == 1
    assert {digest for digest, _ in results} == {results[0][0]}
    assert sum(not replayed for _, replayed in results) == 1
    assert sum(replayed for _, replayed in results) == 5


def testPruneExpiredDeletesWholeChainAndAllUnreferencedCas(tmp_path):
    now = [100.0]
    store = ContinuationStore(tmp_path / "control", _policy(), clock=lambda: now[0])
    issued = store.issue(_state(), _pins(), ttlSeconds=2)
    first = store.redeem(
        issued.token,
        _pins(),
        materialize=lambda state: PageEnvelope(_payload((1,)), 1, _state(b"offset:1")),
    )
    store.redeem(
        first.nextToken or "",
        _pins(),
        materialize=lambda state: PageEnvelope(_payload((2,)), 1),
    )
    assert len(store.cas.iterDigests()) == 4

    now[0] = 105.0
    report = store.pruneExpired()

    assert report.chainsDeleted == 1
    assert report.rowsDeleted == 2
    assert report.artifactsDeleted == 4
    assert report.bytesFreed > 0
    assert store.cas.iterDigests() == ()
    with sqlite3.connect(store.databasePath) as connection:
        assert connection.execute("SELECT count(*) FROM continuations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM continuation_artifacts").fetchone()[0] == 0
    assert store.verifyIntegrity()


def testPruneKeepsSharedCasUntilLastReferencingChainExpires(tmp_path):
    now = [100.0]
    store = ContinuationStore(tmp_path / "control", _policy(), clock=lambda: now[0])
    short = store.issue(_state(), _pins(), ttlSeconds=2)
    long = store.issue(_state(), _pins(), ttlSeconds=100)
    stateDigest = next(iter(store.cas.iterDigests()))
    store.redeem(short.token, _pins(), materialize=lambda state: PageEnvelope(_payload((1,)), 1))

    now[0] = 105.0
    firstPrune = store.pruneExpired()
    assert firstPrune.chainsDeleted == 1
    assert store.cas.pathForDigest(stateDigest).is_file()
    assert store.loadContext(long.token).state == _state()

    now[0] = 205.0
    secondPrune = store.pruneExpired()
    assert secondPrune.chainsDeleted == 1
    assert store.cas.iterDigests() == ()


def testPersistentRootSweepDoesNotStarveBehindLiveLease(tmp_path):
    now = [100.0]
    root = tmp_path / "control"
    store = ContinuationStore(root, _policy(), clock=lambda: now[0])
    issued = [store.issue(_state(), _pins(), ttlSeconds=2) for _ in range(3)]
    with sqlite3.connect(store.databasePath) as connection:
        firstDigest = connection.execute(
            "SELECT token_digest FROM continuations ORDER BY expires_at, token_digest LIMIT 1"
        ).fetchone()[0]
        connection.execute(
            "UPDATE continuations SET status='RUNNING', owner_id='live-owner', lease_until=200 WHERE token_digest=?",
            (firstDigest,),
        )
    now[0] = 105.0
    budget = ContinuationMaintenanceBudget(
        maxChains=1,
        maxRootScans=1,
        maxLedgerScans=1,
        maxCasPrefixes=1,
        maxCasEntries=1,
        maxArtifactDeletes=1,
    )

    first = store.maintain(budget)
    reopened = ContinuationStore(root, _policy(), clock=lambda: now[0])
    second = reopened.maintain(budget)

    assert first.rootsScanned == 1
    assert first.chainsDeleted == 0
    assert second.rootsScanned == 1
    assert second.chainsDeleted == 1
    with sqlite3.connect(store.databasePath) as connection:
        remaining = {row[0] for row in connection.execute("SELECT token_digest FROM continuations")}
    assert firstDigest in remaining
    assert len(remaining) == 2
    assert {item.tokenDigest for item in issued} >= remaining


def testLongExpiredChainUsesRestartSafeBoundedRowPhases(tmp_path):
    now = [100.0]
    root = tmp_path / "control"
    store = ContinuationStore(root, _policy(), clock=lambda: now[0])
    issued = store.issue(_state(b"offset:0"), _pins(), ttlSeconds=2)
    token = issued.token
    for index in range(26):
        nextState = _state(f"offset:{index + 1}".encode()) if index < 25 else None
        page = store.redeem(
            token,
            _pins(),
            materialize=lambda _state, nextState=nextState: PageEnvelope(_payload((1,)), 1, nextState),
        )
        if page.nextToken is not None:
            token = page.nextToken

    now[0] = 105.0
    budget = ContinuationMaintenanceBudget(
        maxChains=1,
        maxRootScans=1,
        maxContinuationRows=2,
        maxLedgerScans=1,
        maxCasPrefixes=1,
        maxCasEntries=1,
        maxArtifactDeletes=100,
    )
    deletedRows = 0
    deletedChains = 0
    sawPersistentWork = False
    for _attempt in range(40):
        reopened = ContinuationStore(root, _policy(), clock=lambda: now[0])
        report = reopened.maintain(budget)
        assert report.rootsScanned <= 1
        assert report.continuationRowsExamined <= 2
        assert report.rowsDeleted <= 2
        deletedRows += report.rowsDeleted
        deletedChains += report.chainsDeleted
        with sqlite3.connect(reopened.databasePath) as connection:
            workCount = connection.execute("SELECT count(*) FROM continuation_prune_work").fetchone()[0]
        sawPersistentWork = sawPersistentWork or workCount == 1
        if deletedChains:
            break

    assert sawPersistentWork
    assert deletedChains == 1
    assert deletedRows == 26
    with sqlite3.connect(store.databasePath) as connection:
        assert connection.execute("SELECT count(*) FROM continuations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM continuation_prune_work").fetchone()[0] == 0
    assert reopened.verifyIntegrity()


def testPruneSkipsLiveLeaseThenCollectsAndRecoversTombstone(tmp_path, monkeypatch):
    now = [100.0]
    store = ContinuationStore(tmp_path / "control", _policy(), clock=lambda: now[0])
    issued = store.issue(_state(), _pins(), ttlSeconds=2)
    now[0] = 105.0
    with sqlite3.connect(store.databasePath) as connection:
        connection.execute("UPDATE continuations SET status='RUNNING', owner_id='live-owner', lease_until=200")
    assert store.pruneExpired().chainsDeleted == 0

    with sqlite3.connect(store.databasePath) as connection:
        connection.execute("UPDATE continuations SET lease_until=0")
    originalDelete = store.cas.deleteBytes

    def failDelete(digest: str):
        raise ContinuationError("CONTINUATION_GC_FAILED")

    monkeypatch.setattr(store.cas, "deleteBytes", failDelete)
    with pytest.raises(ContinuationError) as error:
        store.pruneExpired()
    assert error.value.code == "CONTINUATION_GC_FAILED"
    with sqlite3.connect(store.databasePath) as connection:
        assert connection.execute("SELECT count(*) FROM continuations").fetchone()[0] == 0
        assert (
            connection.execute("SELECT count(*) FROM continuation_artifacts WHERE status='GC_PENDING'").fetchone()[0]
            == 1
        )

    monkeypatch.setattr(store.cas, "deleteBytes", originalDelete)
    recovered = store.pruneExpired()
    assert recovered.chainsDeleted == 0
    assert recovered.artifactsDeleted == 1
    assert store.cas.iterDigests() == ()


def testExpiredOwnerLeaseCannotBeRenewedAndChainBecomesCollectable(tmp_path):
    clockValue = [100.0]
    store = ContinuationStore(tmp_path / "control", _policy(), clock=lambda: clockValue[0])
    issued = store.issue(_state(), _pins(), ttlSeconds=2)
    with sqlite3.connect(store.databasePath) as connection:
        connection.execute(
            "UPDATE continuations SET status='RUNNING', owner_id='stuck-owner', lease_until=104 WHERE token_digest=?",
            (issued.tokenDigest,),
        )

    clockValue[0] = 103.0
    assert store._renew(issued.tokenDigest, "stuck-owner") is False
    clockValue[0] = 105.0

    report = store.pruneExpired()

    assert report.chainsDeleted == 1
    assert store.cas.iterDigests() == ()


def testCasCorruptionIsDetectedOnReplayAndIntegrityAudit(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    issued = store.issue(_state(), _pins())
    page = store.redeem(
        issued.token,
        _pins(),
        materialize=lambda state: PageEnvelope(_payload((1,)), 1),
    )
    store.cas.pathForDigest(page.pageDigest).write_bytes(b"tampered")

    with pytest.raises(ContinuationError) as replayError:
        store.redeem(
            issued.token,
            _pins(),
            materialize=lambda state: pytest.fail("corrupt replay called owner"),
        )
    assert replayError.value.code == "CONTINUATION_CORRUPT"
    with pytest.raises(ContinuationError) as auditError:
        store.verifyIntegrity()
    assert auditError.value.code == "CONTINUATION_CORRUPT"
