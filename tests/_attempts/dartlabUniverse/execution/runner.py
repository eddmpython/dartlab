"""Subprocess 격리 실행, timeout, cancel, retry, partial, durable receipt orchestration."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib
import inspect
import io
import json
import platform
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..canonical import canonicalDigest, canonicalJson
from .admission import AdmissionDecision
from .receipts import (
    BudgetUsed,
    ExecutionError,
    ExecutionReceipt,
    ExecutionStore,
    OutputEnvelope,
)
from .sandbox import buildWorkerEnvironment, installWriteGuard, protectedPathDigests
from .schemaDescriptor import validateValue


class TransientExecutionError(RuntimeError):
    pass


class OutputNormalizationError(RuntimeError):
    pass


class CancelToken:
    """Thread-safe cooperative cancel signal. Parent가 worker를 강제 종료할 수도 있다."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    def isCancelled(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True, slots=True)
class WorkerResult:
    status: str
    mediaType: str | None
    schemaDigest: str | None
    rowCount: int
    truncated: bool
    estimatedTotalRows: int | None
    continuation: str | None
    errorCode: str | None
    errorMessage: str | None
    retryable: bool
    cpuMs: int
    peakRssBytes: int


def _utcNow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dependencyFingerprint() -> str:
    versions = {"python": platform.python_version(), "platform": platform.platform()}
    for name in ("polars", "pyarrow", "numpy"):
        try:
            versions[name] = importlib.metadata.version(name)  # type: ignore[attr-defined]
        except Exception:
            try:
                module = importlib.import_module(name)
                versions[name] = str(getattr(module, "__version__", "unknown"))
            except Exception:
                versions[name] = "unavailable"
    return canonicalDigest(versions)


def _tabularEnvelope(value: Any, schema: dict[str, Any], maxRows: int, maxOutputBytes: int) -> OutputEnvelope:
    try:
        import polars as pl
    except ImportError as exc:
        raise OutputNormalizationError("TABULAR_RUNTIME_UNAVAILABLE") from exc
    if isinstance(value, pl.LazyFrame):
        value = value.collect(engine="streaming")
    if not isinstance(value, pl.DataFrame):
        raise OutputNormalizationError("TABULAR_TYPE_UNSUPPORTED")
    totalRows = value.height
    returnedRows = min(totalRows, maxRows)
    frame = value.head(returnedRows)

    def encode(candidate: Any) -> bytes:
        buffer = io.BytesIO()
        candidate.write_ipc(buffer, compression="zstd")
        return buffer.getvalue()

    payload = encode(frame)
    while len(payload) > maxOutputBytes and returnedRows > 1:
        returnedRows = max(1, returnedRows // 2)
        frame = value.head(returnedRows)
        payload = encode(frame)
    if len(payload) > maxOutputBytes:
        raise OutputNormalizationError("OUTPUT_BUDGET_EXCEEDED")
    truncated = returnedRows < totalRows
    return OutputEnvelope(
        mediaType="application/vnd.apache.arrow.file",
        payload=payload,
        schemaDigest=canonicalDigest(
            {
                "declared": schema,
                "arrowSchema": str(frame.to_arrow().schema),
            }
        ),
        rowCount=returnedRows,
        truncated=truncated,
        estimatedTotalRows=totalRows if truncated else None,
        continuation=f"row:{returnedRows}" if truncated else None,
    )


def normalizeOutput(
    value: Any,
    schema: dict[str, Any],
    *,
    maxRows: int = 100_000,
    maxOutputBytes: int = 64 * 1024 * 1024,
) -> OutputEnvelope:
    """JSON value는 canonical JSON, DataFrame은 Arrow IPC byte로 정규화한다."""
    report = validateValue(value, schema)
    if not report.valid:
        raise OutputNormalizationError(f"OUTPUT_SCHEMA_MISMATCH:{report.digest}")
    className = value.__class__.__name__
    if className in {"DataFrame", "LazyFrame"}:
        return _tabularEnvelope(value, schema, maxRows, maxOutputBytes)
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    if isinstance(value, (list, tuple)):
        totalRows = len(value)
        returnedRows = min(totalRows, maxRows)
        candidate = value[:returnedRows]
        payload = canonicalJson(candidate)
        while len(payload) > maxOutputBytes and returnedRows > 1:
            returnedRows = max(1, returnedRows // 2)
            candidate = value[:returnedRows]
            payload = canonicalJson(candidate)
        if len(payload) > maxOutputBytes:
            raise OutputNormalizationError("OUTPUT_BUDGET_EXCEEDED")
        if returnedRows < totalRows:
            return OutputEnvelope(
                mediaType="application/json",
                payload=payload,
                schemaDigest=canonicalDigest(schema),
                rowCount=returnedRows,
                truncated=True,
                estimatedTotalRows=totalRows,
                continuation=f"row:{returnedRows}",
            )
        rowCount = totalRows
    else:
        payload = canonicalJson(value)
        rowCount = 1
    if len(payload) > maxOutputBytes:
        raise OutputNormalizationError("OUTPUT_BUDGET_EXCEEDED")
    return OutputEnvelope(
        mediaType="application/json",
        payload=payload,
        schemaDigest=canonicalDigest(schema),
        rowCount=rowCount,
        truncated=False,
        estimatedTotalRows=None,
        continuation=None,
    )


def _executorAllowed(apiRef: str, prefixes: tuple[str, ...]) -> bool:
    if apiRef.startswith("python:"):
        moduleName = apiRef.split(":", 2)[1]
        return any(moduleName == prefix or moduleName.startswith(prefix + ".") for prefix in prefixes)
    return any(apiRef == prefix or apiRef.startswith(prefix + ".") for prefix in prefixes)


def _resolveWorkerCallable(payload: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    apiRef = payload["apiRef"]
    args = dict(payload["args"])
    if apiRef.startswith("python:"):
        _, moduleName, attributeName = apiRef.split(":", 2)
        callableObject = getattr(importlib.import_module(moduleName), attributeName)
        if "attempt" in inspect.signature(callableObject).parameters:
            args["attempt"] = payload["attempt"]
        return callableObject, args
    engine = payload["engine"]
    axis = payload["axis"]
    dartlab = importlib.import_module("dartlab")
    callableObject = getattr(dartlab, engine)

    def executeEngine(**keywords: Any) -> Any:
        return callableObject(axis, **keywords)

    return executeEngine, args


def _workerMain(jobPath: Path) -> int:
    job = json.loads(jobPath.read_text(encoding="utf-8"))
    workerRoot = Path(job["workerRoot"]).resolve()
    resultPath = workerRoot / "result.json"
    outputPath = workerRoot / "output" / "result.bin"
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    startedCpu = time.process_time_ns()
    try:
        guard = installWriteGuard((workerRoot,))
        callableObject, args = _resolveWorkerCallable(job)
        value = callableObject(**args)
        envelope = normalizeOutput(
            value,
            job["outputSchema"],
            maxRows=int(job["budget"]["maxRows"]),
            maxOutputBytes=int(job["budget"]["maxOutputBytes"]),
        )
        outputPath.write_bytes(envelope.payload)
        result = {
            "status": "PARTIAL" if envelope.truncated else "SUCCEEDED",
            "mediaType": envelope.mediaType,
            "schemaDigest": envelope.schemaDigest,
            "rowCount": envelope.rowCount,
            "truncated": envelope.truncated,
            "estimatedTotalRows": envelope.estimatedTotalRows,
            "continuation": envelope.continuation,
            "errorCode": None,
            "errorMessage": None,
            "retryable": False,
            "cpuMs": (time.process_time_ns() - startedCpu) // 1_000_000,
            "peakRssBytes": 0,
            "auditEventCount": len(guard.events),
        }
    except BaseException as exc:
        retryable = isinstance(exc, (TransientExecutionError, ConnectionError, TimeoutError)) or type(exc).__name__ in {
            "TransientExecutionError",
            "ConnectError",
            "ReadTimeout",
        }
        errorCode = "SANDBOX_VIOLATION" if isinstance(exc, PermissionError) else type(exc).__name__
        result = {
            "status": "FAILED",
            "mediaType": None,
            "schemaDigest": None,
            "rowCount": 0,
            "truncated": False,
            "estimatedTotalRows": None,
            "continuation": None,
            "errorCode": errorCode,
            "errorMessage": str(exc)[:500],
            "retryable": retryable,
            "cpuMs": (time.process_time_ns() - startedCpu) // 1_000_000,
            "peakRssBytes": 0,
        }
    resultPath.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return 0


def _parseWorkerResult(path: Path) -> WorkerResult:
    value = json.loads(path.read_text(encoding="utf-8"))
    allowed = {field.name for field in dataclasses.fields(WorkerResult)}
    return WorkerResult(**{key: value[key] for key in allowed})


def _runWorker(
    admitted: AdmissionDecision, attempt: int, cancelToken: CancelToken, workerRoot: Path
) -> tuple[WorkerResult, bytes]:
    capability = admitted.capability
    if capability is None or capability.schemaDescriptor is None:
        raise RuntimeError("admitted capability descriptor 누락")
    if not _executorAllowed(capability.apiRef, admitted.policy.allowedExecutorPrefixes):
        raise RuntimeError("EXECUTOR_NOT_ALLOWLISTED")
    environment = buildWorkerEnvironment(workerRoot, readDataRoot=admitted.policy.readDataRoot)
    job = {
        "workerRoot": workerRoot.as_posix(),
        "apiRef": capability.apiRef,
        "engine": capability.engine,
        "axis": capability.axis,
        "args": admitted.normalizedArgs,
        "attempt": attempt,
        "outputSchema": capability.schemaDescriptor.outputSchema,
        "budget": dataclasses.asdict(admitted.request.budget),
    }
    jobPath = workerRoot / "job.json"
    jobPath.write_bytes(canonicalJson(job))
    command = [
        admitted.policy.workerExecutable or sys.executable,
        "-X",
        "utf8",
        "-m",
        "tests._attempts.dartlabUniverse.execution.runner",
        "--worker",
        jobPath.as_posix(),
    ]
    process = subprocess.Popen(
        command,
        cwd=Path(__file__).resolve().parents[4],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    deadline = time.monotonic() + admitted.request.budget.maxWallMs / 1000
    statusOverride = None
    while process.poll() is None:
        if cancelToken.isCancelled():
            statusOverride = "CANCELLED"
            process.kill()
            break
        if time.monotonic() >= deadline:
            statusOverride = "TIMED_OUT"
            process.kill()
            break
        time.sleep(max(0.001, admitted.policy.workerPollMs / 1000))
    stdout, stderr = process.communicate(timeout=5)
    if statusOverride is not None:
        return (
            WorkerResult(
                status=statusOverride,
                mediaType=None,
                schemaDigest=None,
                rowCount=0,
                truncated=False,
                estimatedTotalRows=None,
                continuation=None,
                errorCode=statusOverride,
                errorMessage=statusOverride,
                retryable=statusOverride == "TIMED_OUT",
                cpuMs=0,
                peakRssBytes=0,
            ),
            b"",
        )
    resultPath = workerRoot / "result.json"
    if process.returncode != 0 or not resultPath.exists():
        safe = (stderr or stdout or f"worker exit {process.returncode}")[-500:]
        return (
            WorkerResult(
                status="FAILED",
                mediaType=None,
                schemaDigest=None,
                rowCount=0,
                truncated=False,
                estimatedTotalRows=None,
                continuation=None,
                errorCode="WORKER_CRASHED",
                errorMessage=safe,
                retryable=False,
                cpuMs=0,
                peakRssBytes=0,
            ),
            b"",
        )
    result = _parseWorkerResult(resultPath)
    outputPath = workerRoot / "output" / "result.bin"
    output = outputPath.read_bytes() if result.status in {"SUCCEEDED", "PARTIAL"} and outputPath.exists() else b""
    return result, output


def _makeReceipt(
    admitted: AdmissionDecision,
    *,
    attempt: int,
    status: str,
    startedAt: str,
    finishedAt: str,
    wallMs: int,
    result: WorkerResult | None,
    outputRefs: tuple[str, ...] = (),
    outputDigest: str | None = None,
    outputBytes: int = 0,
    gapReasons: tuple[str, ...] = (),
) -> ExecutionReceipt:
    capability = admitted.capability
    error = None
    if status not in {"SUCCEEDED", "PARTIAL"}:
        error = ExecutionError(
            code=(result.errorCode if result else None) or (gapReasons[0] if gapReasons else status),
            phase="ADMISSION" if status == "REJECTED" else "EXECUTION",
            retryable=bool(result.retryable) if result else False,
            sourceRefs=(capability.apiRef,) if capability else (),
            messageSafe=(result.errorMessage if result else None) or status,
            debugRefLocal=None,
            observedAt=finishedAt,
        )
    executionDigest = canonicalDigest(
        {
            "requestId": admitted.request.requestId,
            "idempotencyKey": admitted.idempotencyKey,
            "attempt": attempt,
            "startedAt": startedAt,
            "status": status,
        }
    )
    return ExecutionReceipt(
        executionId=f"du:v1:execution:{executionDigest}",
        requestId=admitted.request.requestId,
        parentExecutionId=None,
        capabilityId=admitted.request.capabilityId,
        snapshotId=admitted.request.snapshotId,
        targetRefs=admitted.request.targetRefs,
        normalizedArgs=admitted.normalizedArgs,
        argsDigest=canonicalDigest(admitted.normalizedArgs),
        inputRefs=admitted.request.targetRefs,
        assumptionRefs=admitted.request.assumptionRefs,
        engineVersion=capability.sourceDigest if capability else "missing",
        codeRevision=capability.sourceRevision if capability else "missing",
        dependencyFingerprint=_dependencyFingerprint(),
        seed=admitted.request.seed,
        startedAt=startedAt,
        finishedAt=finishedAt,
        status=status,
        attempt=attempt,
        budgetUsed=BudgetUsed(
            wallMs=wallMs,
            cpuMs=result.cpuMs if result else 0,
            peakRssBytes=result.peakRssBytes if result else 0,
            networkBytes=0,
            returnedRows=result.rowCount if result else 0,
            outputBytes=outputBytes,
            toolCalls=1 if result else 0,
            retries=max(0, attempt - 1),
        ),
        sourceReadStats=(),
        outputRefs=outputRefs,
        outputSchemaRef=capability.schemaDescriptor.descriptorId if capability and capability.schemaDescriptor else "",
        outputDigest=outputDigest,
        gapReasons=gapReasons,
        error=error,
        idempotencyKey=admitted.idempotencyKey,
    )


def runCapability(admitted: AdmissionDecision, cancelToken: CancelToken) -> ExecutionReceipt:
    """Admitted execution을 격리 worker에서 실행하고 CAS와 receipt를 원자 결합한다."""
    store = ExecutionStore(Path(admitted.policy.controlRoot))
    if not admitted.admitted:
        now = _utcNow()
        receipt = _makeReceipt(
            admitted,
            attempt=0,
            status="REJECTED",
            startedAt=now,
            finishedAt=now,
            wallMs=0,
            result=None,
            gapReasons=admitted.reasonCodes,
        )
        return store.appendReceipt(receipt)
    ownerId = uuid.uuid4().hex
    waitDeadline = time.monotonic() + admitted.policy.idempotencyWaitMs / 1000
    while True:
        claim = store.claim(admitted.idempotencyKey, ownerId=ownerId)
        if claim.status == "REPLAY" and claim.receipt is not None:
            return claim.receipt
        if claim.status in {"ACQUIRED", "RECOVERED"}:
            break
        if cancelToken.isCancelled() or time.monotonic() >= waitDeadline:
            now = _utcNow()
            return _makeReceipt(
                admitted,
                attempt=0,
                status="CANCELLED" if cancelToken.isCancelled() else "TIMED_OUT",
                startedAt=now,
                finishedAt=now,
                wallMs=0,
                result=None,
                gapReasons=("IDEMPOTENCY_WAIT",),
            )
        time.sleep(max(0.001, admitted.policy.workerPollMs / 1000))
    protectedBefore = protectedPathDigests(admitted.policy.protectedPaths)
    maxAttempts = 1 + min(admitted.request.budget.maxRetries, admitted.policy.maxRetries)
    lastReceipt = None
    for attempt in range(1, maxAttempts + 1):
        startedAt = _utcNow()
        started = time.monotonic()
        workerRoot = (
            Path(admitted.policy.controlRoot).resolve()
            / "workers"
            / f"{admitted.idempotencyKey[:16]}-{attempt}-{uuid.uuid4().hex}"
        )
        workerRoot.mkdir(parents=True, exist_ok=False)
        try:
            result, payload = _runWorker(admitted, attempt, cancelToken, workerRoot)
        finally:
            shutil.rmtree(workerRoot, ignore_errors=True)
        finishedAt = _utcNow()
        wallMs = int((time.monotonic() - started) * 1000)
        protectedAfter = protectedPathDigests(admitted.policy.protectedPaths)
        if protectedAfter != protectedBefore:
            result = WorkerResult(
                status="FAILED",
                mediaType=None,
                schemaDigest=None,
                rowCount=0,
                truncated=False,
                estimatedTotalRows=None,
                continuation=None,
                errorCode="PROTECTED_PATH_MUTATION",
                errorMessage="worker 실행 중 보호 경로 byte가 바뀜",
                retryable=False,
                cpuMs=result.cpuMs,
                peakRssBytes=result.peakRssBytes,
            )
            payload = b""
        staged = ()
        outputRefs = ()
        outputDigest = None
        if result.status in {"SUCCEEDED", "PARTIAL"}:
            envelope = OutputEnvelope(
                mediaType=result.mediaType or "application/octet-stream",
                payload=payload,
                schemaDigest=result.schemaDigest or "",
                rowCount=result.rowCount,
                truncated=result.truncated,
                estimatedTotalRows=result.estimatedTotalRows,
                continuation=result.continuation,
            )
            stagedOutput = store.stageOutput(envelope, ownerId)
            staged = (stagedOutput,)
            outputRefs = (stagedOutput.objectRef,)
            outputDigest = hashlib.sha256(payload).hexdigest()
        receipt = _makeReceipt(
            admitted,
            attempt=attempt,
            status=result.status,
            startedAt=startedAt,
            finishedAt=finishedAt,
            wallMs=wallMs,
            result=result,
            outputRefs=outputRefs,
            outputDigest=outputDigest,
            outputBytes=len(payload),
        )
        terminal = (
            result.status in {"SUCCEEDED", "PARTIAL", "CANCELLED"} or not result.retryable or attempt == maxAttempts
        )
        lastReceipt = store.appendReceipt(receipt, ownerId=ownerId if terminal else None, stagedOutputs=staged)
        if terminal:
            return lastReceipt
    if lastReceipt is None:
        raise RuntimeError("execution attempt가 생성되지 않음")
    return lastReceipt


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker is None:
        parser.error("--worker가 필요")
    return _workerMain(args.worker)


if __name__ == "__main__":
    raise SystemExit(_main())
