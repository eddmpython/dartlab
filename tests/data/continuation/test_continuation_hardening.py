"""Continuation crash recovery, numeric, schema, and collision hardening locks."""

from __future__ import annotations

import hashlib
import math
import os
import sqlite3

import pytest

import dartlab.data.continuation.artifactStore as artifactStoreModule
import dartlab.data.continuation.continuationStore as continuationStoreModule
import dartlab.data.continuation.privateStorage as privateStorageModule
from dartlab.data.continuation import (
    ArtifactStore,
    ContinuationError,
    ContinuationMaintenanceBudget,
    ContinuationPins,
    ContinuationPolicy,
    ContinuationQueryState,
    ContinuationStore,
    bytesDigest,
    canonicalDigest,
    canonicalJsonBytes,
)
from dartlab.data.continuation.privateStorage import (
    _windowsOwnerSid,
    currentWindowsUserSid,
    securePrivatePath,
    verifyPrivatePath,
    windowsDaclSids,
)


def _queryPayload() -> bytes:
    return canonicalJsonBytes({"assets": ["scan.account"], "markets": ["KR", "US"]})


def _pins() -> ContinuationPins:
    return ContinuationPins(
        sourceDigest=canonicalDigest({"snapshot": "dart-edgar-1"}),
        queryDigest=bytesDigest(_queryPayload()),
        contractDigest=canonicalDigest({"asset": "scan.account", "version": 1}),
        schemaDigest=canonicalDigest({"arrowSchema": "test"}),
    )


def _state() -> ContinuationQueryState:
    return ContinuationQueryState(_queryPayload(), b"offset:0")


def _putLegacyObject(store: ContinuationStore, payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    directory = store.cas.legacyObjectRoot / digest[:2]
    directory.mkdir(parents=True, exist_ok=True)
    securePrivatePath(directory)
    path = directory / digest
    path.write_bytes(payload)
    securePrivatePath(path)
    return digest


def _policy(**overrides) -> ContinuationPolicy:
    values = {
        "maxPageRows": 3,
        "maxPageBytes": 1_000_000,
        "maxPageLogicalBytes": 1_000_000,
        "maxStateBytes": 1024,
        "maxTokenIssueAttempts": 3,
        "tokenTtlSeconds": 60,
        "leaseSeconds": 2,
        "waitSeconds": 5,
        "pollSeconds": 0.005,
        "pruneGraceSeconds": 2,
        "artifactStageSeconds": 1,
    }
    values.update(overrides)
    return ContinuationPolicy(**values)


def _leavePartialVersionThreeIndexes(connection: sqlite3.Connection) -> None:
    for name in (
        "continuation_page_artifact",
        "continuation_next_state_artifact",
        "continuation_root_sweep",
    ):
        connection.execute(f"DROP INDEX {name}")


@pytest.mark.parametrize("clockValue", (True, "1", math.nan, math.inf, -math.inf, -1, 10**1000))
def testClockRejectsNonFiniteAndWrongNumericValues(tmp_path, clockValue):
    store = ContinuationStore(tmp_path / "control", _policy(), clock=lambda: clockValue)

    with pytest.raises(ContinuationError) as error:
        store.issue(_state(), _pins())
    assert error.value.code == "CONTINUATION_CLOCK_INVALID"


def testClockExceptionIsMappedToFixedSafeError(tmp_path):
    def failingClock():
        raise RuntimeError("private-clock-detail")

    store = ContinuationStore(tmp_path / "control", _policy(), clock=failingClock)
    with pytest.raises(ContinuationError) as error:
        store.issue(_state(), _pins())
    assert error.value.code == "CONTINUATION_CLOCK_INVALID"
    assert "private-clock-detail" not in str(error.value)


@pytest.mark.parametrize("ttl", (True, "1", 0, math.nan, math.inf, -math.inf, 10**1000))
def testIssueRejectsInvalidTtlBeforeArtifactPublication(tmp_path, ttl):
    store = ContinuationStore(tmp_path / "control", _policy())

    with pytest.raises(ValueError):
        store.issue(_state(), _pins(), ttlSeconds=ttl)
    assert store.cas.iterDigests() == ()


def testTokenCollisionRetriesExactlyToPolicyBound(tmp_path, monkeypatch):
    calls = 0

    def fixedRandomBytes(size: int) -> bytes:
        nonlocal calls
        calls += 1
        assert size == 32
        return b"x" * size

    monkeypatch.setattr(continuationStoreModule.secrets, "token_bytes", fixedRandomBytes)
    store = ContinuationStore(tmp_path / "control", _policy(maxTokenIssueAttempts=4))
    store.issue(_state(), _pins())
    calls = 0

    with pytest.raises(ContinuationError) as error:
        store.issue(_state(), _pins())
    assert error.value.code == "CONTINUATION_TOKEN_COLLISION"
    assert calls == 4
    assert store.verifyIntegrity()


def testNonTokenIntegrityFailureIsNotRetriedAndStagingIsCollectable(tmp_path, monkeypatch):
    now = [10.0]
    calls = 0

    def randomBytes(size: int) -> bytes:
        nonlocal calls
        calls += 1
        return bytes([calls]) * size

    monkeypatch.setattr(continuationStoreModule.secrets, "token_bytes", randomBytes)
    store = ContinuationStore(tmp_path / "control", _policy(), clock=lambda: now[0])
    with sqlite3.connect(store.databasePath) as connection:
        connection.execute(
            "CREATE TRIGGER reject_issue BEFORE INSERT ON continuations "
            "BEGIN SELECT RAISE(ABORT, 'different constraint'); END"
        )

    with pytest.raises(ContinuationError) as error:
        store.issue(_state(), _pins())
    assert error.value.code == "CONTINUATION_CORRUPT"
    assert calls == 1
    assert len(store.cas.iterDigests()) == 1
    with pytest.raises(ContinuationError):
        store.verifyIntegrity()

    with sqlite3.connect(store.databasePath) as connection:
        connection.execute("DROP TRIGGER reject_issue")
    now[0] = 12.0
    report = store.pruneExpired()
    assert report.artifactsDeleted == 1
    assert store.verifyIntegrity()


def testCrashAfterCasPublishLeavesDurableStageAndGcRecovers(tmp_path, monkeypatch):
    now = [10.0]
    store = ContinuationStore(tmp_path / "control", _policy(), clock=lambda: now[0])
    originalPut = store.cas.putBytes

    def publishThenFail(payload: bytes) -> str:
        originalPut(payload)
        raise ContinuationError("CONTINUATION_CORRUPT")

    monkeypatch.setattr(store.cas, "putBytes", publishThenFail)
    with pytest.raises(ContinuationError):
        store.issue(_state(), _pins())
    assert len(store.cas.iterDigests()) == 1
    with sqlite3.connect(store.databasePath) as connection:
        staged = connection.execute("SELECT status FROM continuation_artifacts").fetchone()
    assert staged == ("STAGED",)
    with pytest.raises(ContinuationError) as integrityError:
        store.verifyIntegrity()
    assert integrityError.value.code == "CONTINUATION_CORRUPT"

    monkeypatch.setattr(store.cas, "putBytes", originalPut)
    now[0] = 12.0
    report = store.pruneExpired()
    assert report.artifactsDeleted == 1
    assert store.cas.iterDigests() == ()
    assert store.verifyIntegrity()


def testCasPublicationHoldsLedgerWriteLockAcrossRegistrationCheck(tmp_path, monkeypatch):
    store = ContinuationStore(tmp_path / "control", _policy())
    originalLink = artifactStoreModule.os.link
    lockObserved = False

    def linkWhileCheckingLock(source, destination):
        nonlocal lockObserved
        contender = sqlite3.connect(store.databasePath, timeout=0)
        try:
            contender.execute("PRAGMA busy_timeout=0")
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                contender.execute("BEGIN IMMEDIATE")
            lockObserved = True
        finally:
            contender.close()
        originalLink(source, destination)

    monkeypatch.setattr(artifactStoreModule.os, "link", linkWhileCheckingLock)
    store.issue(_state(), _pins())

    assert lockObserved
    assert store.verifyIntegrity()


def testUnknownCasOrphanFailsAuditAndBoundedPruneRemovesIt(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    orphanDigest = _putLegacyObject(store, b"unregistered-orphan")

    with pytest.raises(ContinuationError) as error:
        store.verifyIntegrity()
    assert error.value.code == "CONTINUATION_CORRUPT"

    deleted = 0
    for _attempt in range(257):
        store = ContinuationStore(tmp_path / "control", _policy())
        report = store.maintain(
            ContinuationMaintenanceBudget(
                maxChains=1,
                maxRootScans=1,
                maxLedgerScans=1,
                maxCasPrefixes=1,
                maxCasEntries=1,
                maxArtifactDeletes=1,
            )
        )
        assert report.casEntriesExamined <= 1
        deleted += report.artifactsDeleted
        if deleted:
            break
    assert deleted == 1
    assert not store.cas.pathForDigest(orphanDigest).exists()
    assert store.verifyIntegrity()


def testContinuationCasRejectsPublishBeforeLedgerRegistration(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())

    with pytest.raises(ContinuationError) as error:
        store.cas.putBytes(b"unregistered-new-layout-object")

    assert error.value.code == "CONTINUATION_CORRUPT"
    assert store.cas.iterDigests() == ()


def testMaintenanceNeverEnumeratesWholeCas(tmp_path, monkeypatch):
    store = ContinuationStore(tmp_path / "control", _policy())

    def failFullScan():
        raise AssertionError("bounded maintenance must not enumerate the full CAS")

    monkeypatch.setattr(store.cas, "iterDigests", failFullScan)
    report = store.maintain(
        ContinuationMaintenanceBudget(
            maxChains=1,
            maxRootScans=1,
            maxLedgerScans=1,
            maxCasPrefixes=1,
            maxCasEntries=1,
            maxArtifactDeletes=1,
        )
    )

    assert report.casPrefixesScanned == 1
    assert report.casEntriesExamined == 0


def testBoundedPruneFindsOrphanAfterTrackedDigestPrefix(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    payloads = []
    prefix = None
    index = 0
    while len(payloads) < 12:
        payload = f"orphan:{index}".encode()
        digest = hashlib.sha256(payload).hexdigest()
        if prefix is None:
            prefix = digest[:2]
        if digest.startswith(prefix):
            payloads.append(payload)
        index += 1
    digests = [_putLegacyObject(store, payload) for payload in payloads]
    assert prefix is not None
    with sqlite3.connect(store.databasePath) as connection:
        connection.execute(
            "UPDATE continuation_sweeps SET cursor_value=? WHERE sweep_name='cas'",
            (int(prefix, 16),),
        )
    budget = ContinuationMaintenanceBudget(
        maxChains=1,
        maxRootScans=1,
        maxLedgerScans=1,
        maxCasPrefixes=1,
        maxCasEntries=3,
        maxArtifactDeletes=3,
    )
    deleted = 0
    for _attempt in range(8):
        reopened = ContinuationStore(tmp_path / "control", _policy())
        report = reopened.maintain(budget)
        assert report.casPrefixesScanned == 1
        assert report.casEntriesExamined <= 3
        deleted += report.artifactsDeleted
        if deleted == len(digests):
            break

    assert deleted == len(digests)
    assert all(not store.cas.pathForDigest(digest).exists() for digest in digests)
    assert store.verifyIntegrity()


def testBoundedPruneSelectsDanglingReferencePastValidPrefix(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    store.issue(_state(), _pins())
    validDigest = store.cas.iterDigests()[0]
    danglingDigest = None
    danglingPayload = b""
    for index in range(10_000):
        payload = f"dangling:{index}".encode()
        candidate = _putLegacyObject(store, payload)
        if candidate > validDigest:
            danglingDigest = candidate
            danglingPayload = payload
            break
        store.cas.deleteBytes(candidate)
    assert danglingDigest is not None
    with sqlite3.connect(store.databasePath) as connection:
        connection.execute(
            "INSERT INTO continuation_artifacts "
            "(digest, byte_count, status, stage_owner, staged_at, referenced_at) "
            "VALUES (?, ?, 'REFERENCED', NULL, 1, 1)",
            (danglingDigest, len(danglingPayload)),
        )

    deleted = 0
    budget = ContinuationMaintenanceBudget(
        maxChains=1,
        maxRootScans=1,
        maxLedgerScans=1,
        maxCasPrefixes=1,
        maxCasEntries=1,
        maxArtifactDeletes=1,
    )
    for _attempt in range(4):
        reopened = ContinuationStore(tmp_path / "control", _policy())
        report = reopened.maintain(budget)
        assert report.ledgerArtifactsScanned <= 1
        deleted += report.artifactsDeleted
        if deleted:
            break

    assert deleted == 1
    assert not store.cas.pathForDigest(danglingDigest).exists()
    assert store.verifyIntegrity()


def testFutureAndIncompleteSchemasFailClosed(tmp_path):
    futureRoot = tmp_path / "future"
    future = ContinuationStore(futureRoot, _policy())
    with sqlite3.connect(future.databasePath) as connection:
        connection.execute("PRAGMA user_version=99")
    with pytest.raises(ContinuationError) as futureError:
        ContinuationStore(futureRoot, _policy())
    assert futureError.value.code == "CONTINUATION_SCHEMA_VERSION_UNSUPPORTED"

    incompleteRoot = tmp_path / "incomplete"
    incompleteRoot.mkdir()
    with sqlite3.connect(incompleteRoot / "continuations.sqlite") as connection:
        connection.execute("CREATE TABLE unexpected(value TEXT)")
    with pytest.raises(ContinuationError) as incompleteError:
        ContinuationStore(incompleteRoot, _policy())
    assert incompleteError.value.code == "CONTINUATION_SCHEMA_VERSION_UNSUPPORTED"


def testVersionOneLedgerMigratesExplicitlyToVersionThree(tmp_path, monkeypatch):
    root = tmp_path / "control"
    original = ContinuationStore(root, _policy())
    issued = original.issue(_state(), _pins())
    with sqlite3.connect(original.databasePath) as connection:
        _leavePartialVersionThreeIndexes(connection)
        connection.execute("DROP TRIGGER continuation_artifact_identity_immutable")
        connection.execute("DROP INDEX continuation_artifact_status")
        connection.execute("DROP TABLE continuation_artifacts")
        connection.execute(
            "CREATE TABLE continuation_gc_artifacts (digest TEXT PRIMARY KEY, enqueued_at REAL NOT NULL)"
        )
        connection.execute("DROP TABLE continuation_sweeps")
        connection.execute("PRAGMA user_version=1")

    def failFullScan(_store):
        raise AssertionError("schema migration must not enumerate the full CAS")

    with monkeypatch.context() as migrationPatch:
        migrationPatch.setattr(ArtifactStore, "iterDigests", failFullScan)
        migrated = ContinuationStore(root, _policy())
    with sqlite3.connect(migrated.databasePath) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert version == 3
    assert "continuation_artifacts" in tables
    assert "continuation_sweeps" in tables
    assert "continuation_gc_artifacts" not in tables
    assert migrated.loadContext(issued.token).state == _state()
    assert migrated.verifyIntegrity()


def testFailedVersionOneMigrationRollsBackAtomically(tmp_path):
    root = tmp_path / "control"
    original = ContinuationStore(root, _policy())
    original.issue(_state(), _pins())
    stateDigest = original.cas.iterDigests()[0]
    original.cas.deleteBytes(stateDigest)
    with sqlite3.connect(original.databasePath) as connection:
        _leavePartialVersionThreeIndexes(connection)
        connection.execute("DROP TRIGGER continuation_artifact_identity_immutable")
        connection.execute("DROP INDEX continuation_artifact_status")
        connection.execute("DROP TABLE continuation_artifacts")
        connection.execute(
            "CREATE TABLE continuation_gc_artifacts (digest TEXT PRIMARY KEY, enqueued_at REAL NOT NULL)"
        )
        connection.execute("DROP TABLE continuation_sweeps")
        connection.execute("PRAGMA user_version=1")

    with pytest.raises(ContinuationError) as error:
        ContinuationStore(root, _policy())
    assert error.value.code == "CONTINUATION_CORRUPT"
    with sqlite3.connect(original.databasePath) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert version == 1
    assert "continuation_gc_artifacts" in tables
    assert "continuation_artifacts" not in tables


def testVersionTwoLedgerMigratesPersistentSweepState(tmp_path):
    root = tmp_path / "version-two"
    original = ContinuationStore(root, _policy())
    issued = original.issue(_state(), _pins())
    with sqlite3.connect(original.databasePath) as connection:
        _leavePartialVersionThreeIndexes(connection)
        connection.execute("DROP TABLE continuation_sweeps")
        connection.execute("PRAGMA user_version=2")

    migrated = ContinuationStore(root, _policy())
    with sqlite3.connect(migrated.databasePath) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        sweeps = connection.execute("SELECT sweep_name FROM continuation_sweeps ORDER BY sweep_name").fetchall()

    assert version == 3
    assert sweeps == [("artifacts",), ("cas",), ("roots",)]
    assert migrated.loadContext(issued.token).state == _state()


def testIncompleteVersionThreeSchemaFailsClosed(tmp_path):
    root = tmp_path / "control"
    store = ContinuationStore(root, _policy())
    with sqlite3.connect(store.databasePath) as connection:
        connection.execute("DROP TRIGGER continuation_artifact_identity_immutable")

    with pytest.raises(ContinuationError) as error:
        ContinuationStore(root, _policy())
    assert error.value.code == "CONTINUATION_SCHEMA_VERSION_UNSUPPORTED"


def testIntegrityRejectsWrongStoredNumericType(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    issued = store.issue(_state(), _pins())
    with sqlite3.connect(store.databasePath) as connection:
        connection.execute(
            "UPDATE continuations SET lease_until='not-a-number' WHERE token_digest=?",
            (issued.tokenDigest,),
        )

    with pytest.raises(ContinuationError) as error:
        store.verifyIntegrity()
    assert error.value.code == "CONTINUATION_CORRUPT"


@pytest.mark.skipif(os.name != "nt", reason="Windows DACL integration lock")
def testWindowsControlPlaneDaclIsVerifiedEndToEnd(tmp_path):
    store = ContinuationStore(tmp_path / "control", _policy())
    store.issue(_state(), _pins())
    expected = {"S-1-5-18", currentWindowsUserSid()}
    paths = [store.root, store.databasePath, store.cas.root, store.cas.objectRoot]
    paths.extend(store.cas.pathForDigest(digest) for digest in store.cas.iterDigests())

    for path in paths:
        actual = {"S-1-5-18" if sid == "SY" else sid for sid in windowsDaclSids(path)}
        assert actual == expected
        assert _windowsOwnerSid(path) in expected
        assert verifyPrivatePath(path)
    assert store.verifyIntegrity()


def testPreexistingPrivateRootSymlinkFailsBeforeResolve(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(ContinuationError) as storeError:
        ContinuationStore(link, _policy())
    with pytest.raises(ContinuationError) as artifactError:
        ArtifactStore(link)

    assert storeError.value.code == "CONTINUATION_SECURITY_FAILED"
    assert artifactError.value.code == "CONTINUATION_SECURITY_FAILED"


@pytest.mark.skipif(os.name == "nt", reason="POSIX ownership metadata contract")
def testPosixPrivatePathRejectsDifferentOwnerUid(tmp_path, monkeypatch):
    private = tmp_path / "private.bin"
    private.write_bytes(b"private")
    private.chmod(0o600)
    actualUid = getattr(os, "geteuid")()
    monkeypatch.setattr(privateStorageModule.os, "geteuid", lambda: actualUid + 1)

    with pytest.raises(ContinuationError) as error:
        verifyPrivatePath(private)

    assert error.value.code == "CONTINUATION_SECURITY_FAILED"
