from __future__ import annotations

import threading
import time
from dataclasses import replace

from .canonical import canonicalDigest
from .execution.admission import ExecutionBudget, ExecutionPolicy, ExecutionRequest, admitExecution
from .execution.receipts import ExecutionStore, OutputEnvelope, replayExecution
from .execution.registry import CapabilityRef, UniverseCapabilityRegistry
from .execution.runner import CancelToken, runCapability
from .execution.sandbox import buildWorkerEnvironment
from .execution.schemaDescriptor import SchemaDescriptor


def _schema(schemaType: str) -> SchemaDescriptor:
    sourceDigest = "a" * 64
    argsProperties = {
        "value": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "delayMs": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "rows": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "path": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    }
    outputSchema = {"type": "object", "additionalProperties": True} if schemaType == "object" else {"type": schemaType}
    return SchemaDescriptor(
        descriptorId="du:v1:schema:" + "b" * 64,
        apiRef="fixture",
        axis="fixture",
        sourceRevision="test",
        sourceDigest=sourceDigest,
        extractionEvidenceRefs=("test",),
        argsSchema={
            "type": "object",
            "properties": argsProperties,
            "required": [],
            "additionalProperties": False,
        },
        outputSchema=outputSchema,
        validationCorpusRef="test-corpus",
        validationReportRef="c" * 64,
        reviewer="test",
        version="1",
        status="VALIDATED",
    )


def _capability(functionName: str, schemaType: str = "object") -> CapabilityRef:
    descriptor = replace(
        _schema(schemaType),
        apiRef=f"python:tests._attempts.dartlabUniverse.executionFixtures:{functionName}",
    )
    return CapabilityRef(
        capabilityId="du:v1:capability:" + canonicalDigest(functionName),
        candidateId=f"fixture.{functionName}",
        kind="AXIS",
        apiRef=descriptor.apiRef,
        engine="fixture",
        axis=functionName,
        targetScope="TEST",
        runtimeBoundary="LOCAL_PYTHON",
        determinism="SNAPSHOT_BOUND",
        seedPolicy="FORBIDDEN",
        costClass="LOW",
        memoryClass="BOUNDED_WORKER",
        timeoutMs=2000,
        retryPolicy="TRANSIENT_ONLY",
        cachePolicy="SNAPSHOT_IDEMPOTENT",
        concurrencyClass="LIGHT_IO",
        maturity="OBSERVED",
        visibility="LOCAL",
        sourceRevision="test",
        sourceDigest="a" * 64,
        status="ACTIVE",
        eligible=True,
        gapReasons=(),
        schemaDescriptor=descriptor,
    )


def _registry(capability: CapabilityRef) -> UniverseCapabilityRegistry:
    return UniverseCapabilityRegistry(
        capabilities=(capability,),
        discoveredCandidateCount=1,
        classifiedCandidateCount=1,
        eligibleCallableCount=1,
        validatedSchemaCount=1,
        blockedEligibleCount=0,
        catalogCoverage=1.0,
        executionReadiness=1.0,
        inventedAxisCount=0,
        censusDigest="d" * 64,
        registryDigest="e" * 64,
    )


def _decision(tmp_path, functionName: str, *, args=None, budget=None, schemaType="object", protectedPaths=()):
    capability = _capability(functionName, schemaType)
    request = ExecutionRequest(
        requestId=f"request-{functionName}-{canonicalDigest(args or {})[:8]}",
        capabilityId=capability.capabilityId,
        snapshotId="du:v1:snapshot:" + "1" * 64,
        targetRefs=("du:v1:entity:test",),
        args=args or {},
        assumptionRefs=(),
        visibilityScope="LOCAL",
        budget=budget or ExecutionBudget(maxWallMs=15_000, maxRetries=1),
        priority=5,
        deadline=None,
        idempotencyKey=None,
        requestedBy="test",
    )
    policy = ExecutionPolicy(
        controlRoot=tmp_path.as_posix(),
        allowedExecutorPrefixes=("tests",),
        maxWallMs=20_000,
        maxRetries=1,
        protectedPaths=tuple(str(item) for item in protectedPaths),
    )
    decision = admitExecution(request, _registry(capability), policy)
    assert decision.admitted, decision.reasonCodes
    return decision


def testDeterministicExecutionReceiptAndReplay(tmp_path):
    decision = _decision(tmp_path, "deterministicFixture", args={"value": 7})
    receipt = runCapability(decision, CancelToken())
    assert receipt.status == "SUCCEEDED"
    assert receipt.outputDigest
    store = ExecutionStore(tmp_path)
    replay = replayExecution(receipt, store)
    assert replay.valid, replay.issues
    assert b'"value":7' in replay.payloads[0]


def testInvalidArgsAreRejectedBeforeWorker(tmp_path):
    valid = _decision(tmp_path, "deterministicFixture", args={"value": 7})
    invalidRequest = replace(valid.request, requestId="invalid-args", args={"invented": True})
    decision = admitExecution(invalidRequest, _registry(valid.capability), valid.policy)
    assert not decision.admitted
    assert "INVALID_ARGS" in decision.reasonCodes
    receipt = runCapability(decision, CancelToken())
    assert receipt.status == "REJECTED"
    assert receipt.error and receipt.error.phase == "ADMISSION"


def testStochasticCapabilityWithoutSeedIsRejected(tmp_path):
    capability = replace(_capability("deterministicFixture"), determinism="STOCHASTIC", seedPolicy="REQUIRED")
    valid = _decision(tmp_path, "deterministicFixture")
    request = replace(valid.request, capabilityId=capability.capabilityId, requestId="missing-seed", seed=None)
    decision = admitExecution(request, _registry(capability), valid.policy)
    assert not decision.admitted
    assert "NONDETERMINISTIC_WITHOUT_SEED" in decision.reasonCodes


def testWorkerEnvironmentDropsAmbientSecrets(tmp_path, monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "secret")
    monkeypatch.setenv("DART_API_KEY", "secret")
    monkeypatch.setenv("SAFE_SETTING", "visible")
    environment = buildWorkerEnvironment(tmp_path / "worker-env")
    assert "HF_TOKEN" not in environment
    assert "DART_API_KEY" not in environment
    assert environment["SAFE_SETTING"] == "visible"


def testWorkerEnvironmentMountsExistingDataRootWithoutMakingItWritable(tmp_path):
    readDataRoot = tmp_path / "source-data"
    readDataRoot.mkdir()
    (readDataRoot / "source.txt").write_text("immutable", encoding="utf-8")
    environment = buildWorkerEnvironment(tmp_path / "worker-env", readDataRoot=readDataRoot)
    assert environment["DARTLAB_DATA_DIR"] == readDataRoot.resolve().as_posix()
    assert environment["DARTLAB_UNIVERSE_READ_DATA_ROOT"] == readDataRoot.resolve().as_posix()
    assert environment["DARTLAB_NO_HF_DOWNLOAD"] == "1"
    assert (readDataRoot / "source.txt").read_text(encoding="utf-8") == "immutable"


def testAdmissionRejectsMissingOrOverlappingReadDataRoot(tmp_path):
    valid = _decision(tmp_path / "valid-control", "deterministicFixture")
    missingPolicy = replace(valid.policy, readDataRoot=(tmp_path / "missing").as_posix())
    missing = admitExecution(valid.request, _registry(valid.capability), missingPolicy)
    assert not missing.admitted
    assert "READ_DATA_ROOT_INVALID" in missing.reasonCodes

    dataRoot = tmp_path / "data"
    dataRoot.mkdir()
    overlappingPolicy = replace(
        valid.policy, controlRoot=(dataRoot / "control").as_posix(), readDataRoot=dataRoot.as_posix()
    )
    overlapping = admitExecution(valid.request, _registry(valid.capability), overlappingPolicy)
    assert not overlapping.admitted
    assert "CONTROL_ROOT_OVERLAPS_READ_DATA_ROOT" in overlapping.reasonCodes


def testIdempotencyReturnsSameSuccessReceipt(tmp_path):
    decision = _decision(tmp_path, "deterministicFixture", args={"value": 8})
    first = runCapability(decision, CancelToken())
    second = runCapability(decision, CancelToken())
    assert first.executionId == second.executionId
    store = ExecutionStore(tmp_path)
    with store._connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM receipts WHERE idempotency_key=? AND status='SUCCEEDED'",
            (decision.idempotencyKey,),
        ).fetchone()[0]
    assert count == 1


def testConcurrentIdempotencyProducesOneSuccess(tmp_path):
    decision = _decision(tmp_path, "deterministicFixture", args={"value": 9})
    receipts = []

    def execute():
        receipts.append(runCapability(decision, CancelToken()))

    threads = [threading.Thread(target=execute) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert len(receipts) == 2
    assert len({item.executionId for item in receipts}) == 1


def testTransientFailureRetriesExactlyOnce(tmp_path):
    decision = _decision(tmp_path, "transientFixture", args={"value": 3})
    receipt = runCapability(decision, CancelToken())
    assert receipt.status == "SUCCEEDED"
    assert receipt.attempt == 2
    assert receipt.budgetUsed.retries == 1


def testTimeoutTerminatesWorker(tmp_path):
    budget = ExecutionBudget(maxWallMs=100, maxRetries=0)
    decision = _decision(tmp_path, "slowFixture", args={"delayMs": 2000}, budget=budget)
    started = time.monotonic()
    receipt = runCapability(decision, CancelToken())
    assert receipt.status == "TIMED_OUT"
    assert time.monotonic() - started < 2.0


def testCancellationTerminatesWorker(tmp_path):
    decision = _decision(tmp_path, "slowFixture", args={"delayMs": 2000})
    token = CancelToken()
    box = []
    thread = threading.Thread(target=lambda: box.append(runCapability(decision, token)))
    thread.start()
    time.sleep(0.1)
    token.cancel()
    thread.join(timeout=5)
    assert box and box[0].status == "CANCELLED"


def testPartialDataFrameUsesArrowAndNeverMasqueradesAsSuccess(tmp_path):
    budget = ExecutionBudget(maxWallMs=15_000, maxRows=3, maxRetries=0)
    decision = _decision(
        tmp_path,
        "partialFrameFixture",
        args={"rows": 10},
        budget=budget,
        schemaType="tabular",
    )
    receipt = runCapability(decision, CancelToken())
    assert receipt.status == "PARTIAL"
    assert receipt.budgetUsed.returnedRows == 3
    payload = ExecutionStore(tmp_path).cas.readBytes(receipt.outputRefs[0])
    assert payload[:6] == b"ARROW1"


def testPartialJsonListHasContinuationAndNeverMasqueradesAsSuccess(tmp_path):
    budget = ExecutionBudget(maxWallMs=15_000, maxRows=3, maxRetries=0)
    decision = _decision(
        tmp_path,
        "partialListFixture",
        args={"rows": 10},
        budget=budget,
        schemaType="array",
    )
    receipt = runCapability(decision, CancelToken())
    assert receipt.status == "PARTIAL"
    assert receipt.budgetUsed.returnedRows == 3
    payload = ExecutionStore(tmp_path).cas.readBytes(receipt.outputRefs[0])
    assert payload.count(b'"row"') == 3


def testWriteOutsideWorkerRootIsBlockedAndProtectedByteUnchanged(tmp_path):
    protected = tmp_path.parent / f"protected-{tmp_path.name}.txt"
    protected.write_text("original", encoding="utf-8")
    decision = _decision(
        tmp_path,
        "hardCodedWriteFixture",
        args={"path": protected.as_posix()},
        protectedPaths=(protected,),
    )
    receipt = runCapability(decision, CancelToken())
    assert receipt.status == "FAILED"
    assert receipt.error and receipt.error.code == "SANDBOX_VIOLATION"
    assert protected.read_text(encoding="utf-8") == "original"


def testSubprocessIsBlocked(tmp_path):
    decision = _decision(tmp_path, "subprocessWriteFixture")
    receipt = runCapability(decision, CancelToken())
    assert receipt.status == "FAILED"
    assert receipt.error and receipt.error.code == "SANDBOX_VIOLATION"


def testOutputSchemaMismatchFailsWithoutCasOutput(tmp_path):
    decision = _decision(tmp_path, "wrongOutputFixture", schemaType="object")
    receipt = runCapability(decision, CancelToken())
    assert receipt.status == "FAILED"
    assert receipt.outputRefs == ()
    assert receipt.error and receipt.error.code == "OutputNormalizationError"


def testCrashAfterCasCommitIsRecoveredAsOrphan(tmp_path):
    store = ExecutionStore(tmp_path)
    staged = store.stageOutput(
        OutputEnvelope(
            mediaType="application/json",
            payload=b'{"orphan":true}',
            schemaDigest="f" * 64,
            rowCount=1,
            truncated=False,
            estimatedTotalRows=None,
            continuation=None,
        ),
        ownerId="crashed-worker",
    )
    assert store.cas.pathForDigest(staged.outputDigest).exists()
    recovered = store.recoverOrphans()
    assert recovered == (staged.objectRef,)
    assert not store.cas.pathForDigest(staged.outputDigest).exists()
    assert (store.quarantineRoot / staged.outputDigest[:2] / staged.outputDigest).exists()
