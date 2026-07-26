"""Mixed continuation의 eager executor 결과를 fresh process에서 봉인한다.

Capabilities:
    Strict JSON request, spawn child, bounded Arrow artifact, Windows Job Object,
    POSIX process group, digest 검증과 zero-live cleanup을 제공한다.

Args:
    공개 함수는 descriptor, query, selector와 monotonic deadline을 받는다.

Returns:
    Content-sealed eager result bundle 또는 구조화된 process failure를 반환한다.

Raises:
    호출 계약 자체가 유효하지 않으면 ``ValueError``를 발생시킨다.

Example:
    ``outcome = runEagerSeal(descriptor, query, selectors, requestId="x", ...)``.

Guide:
    Callable 객체를 직렬화하지 않는다. Module과 attribute descriptor만 child가 재구성한다.

When:
    Pageable owner와 일반 eager asset이 한 ``data("query")``에 함께 있을 때 사용한다.

How:
    Parent가 임시 artifact를 만들고 child 결과를 Arrow IPC와 SHA-256으로 검증한다.

See Also:
    ``dartlab.dataHub.compositePaging``과 ``dartlab.dataHub.ownerProcess``.

Requires:
    Descriptor와 query는 strict canonical JSON으로 표현 가능해야 한다.

AI Context:
    결과는 첫 public page 전에 계산되며 continuation resume은 owner를 다시 호출하지 않는다.
"""

from __future__ import annotations

import base64
import binascii
import dataclasses
import hashlib
import hmac
import importlib
import importlib.util
import inspect
import os
import sys
import threading
import zlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

import pyarrow as pa

from dartlab.dataHub.continuation import (
    ContinuationError,
    arrowSchemaDigest,
    canonicalDigest,
    inspectArrowIpcPayload,
)
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataGap,
    DataQuery,
    DataResult,
    QueryBudget,
    UniverseCoverage,
)
from dartlab.dataHub.ownerProcess import (
    _artifactPath,
    _ensureArtifactRoot,
    _loadStrictJson,
    _ProtocolViolation,
    _safeErrorCode,
    _strictJson,
)
from dartlab.dataHub.pagingRuntime import (
    MAX_OWNER_PROCESS_REQUEST_BYTES,
    requireDeadline,
)
from dartlab.dataHub.processLifecycle import becomeProcessGroupLeader
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

_FORMAT_VERSION = 1
_PACK_ENCODING = "zlib-base64-v1"
_DIGEST_LENGTH = 64
_MAX_BUNDLE_BYTES = 192 * 1024
_MAX_RESULT_COUNT = 1_000
_BUNDLE_OVERHEAD_BYTES = 8 * 1024
_MIN_RESULT_BYTES = 4 * 1024
_EAGER_METADATA = {b"dartlab.dataHub.eager-seal": b"v1"}
_EAGER_SCHEMA = pa.schema(
    [
        pa.field("resultIndex", pa.int32(), nullable=False),
        pa.field("selectorDigest", pa.string(), nullable=False),
        pa.field("resultPayload", pa.binary(), nullable=False),
        pa.field("resultDigest", pa.string(), nullable=False),
    ],
    metadata=_EAGER_METADATA,
)


_log = dataHubLogger(__name__)


@dataclass(frozen=True, slots=True)
class EagerSeal:
    """Parent가 검증한 eager result bundle."""

    payload: bytes
    payloadDigest: str
    byteCount: int
    resultCount: int
    schemaDigest: str


def _requireDigest(value: Any) -> str:
    if (
        type(value) is not str
        or len(value) != _DIGEST_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    return value


def _arrowPayload(table: pa.Table) -> bytes:
    combined = table.combine_chunks()
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(
        sink,
        combined.schema,
        options=pa.ipc.IpcWriteOptions(compression=None),
    ) as writer:
        writer.write_table(combined)
    return sink.getvalue().to_pybytes()


def _decodeBundle(
    payload: bytes,
    *,
    selectors: Sequence[Mapping[str, str]],
) -> tuple[bytes, ...]:
    if not isinstance(payload, bytes) or not payload or len(payload) > _MAX_BUNDLE_BYTES:
        raise ContinuationError("PAGEABLE_EAGER_SEAL_BUDGET")
    facts = inspectArrowIpcPayload(payload, maxLogicalBytes=_MAX_BUNDLE_BYTES)
    if facts.containerKind != "stream" or facts.rowCount != len(selectors):
        raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
    try:
        reader = pa.ipc.open_stream(pa.BufferReader(payload))
        schema = reader.schema
        batches = tuple(reader)
        table = pa.Table.from_batches(batches, schema=schema)
    except Exception:
        recordFailure(_log, "CONTINUATION_PAYLOAD_INVALID")
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID") from None
    if schema != _EAGER_SCHEMA or len(batches) != 1 or table.num_rows != len(selectors):
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    composite = importlib.import_module("dartlab.dataHub.compositePaging")
    results: list[bytes] = []
    for expectedIndex, (row, selector) in enumerate(zip(table.to_pylist(), selectors, strict=True)):
        resultPayload = row["resultPayload"]
        resultDigest = _requireDigest(row["resultDigest"])
        if (
            row["resultIndex"] != expectedIndex
            or row["selectorDigest"] != canonicalDigest(dict(selector))
            or not isinstance(resultPayload, bytes)
            or not resultPayload
            or not hmac.compare_digest(
                hashlib.sha256(resultPayload).hexdigest(),
                resultDigest,
            )
        ):
            raise ContinuationError("CONTINUATION_CORRUPT")
        composite._decodeEagerResult(resultPayload)
        results.append(resultPayload)
    return tuple(results)


def packEagerSeal(seal: EagerSeal) -> dict[str, Any]:
    """Eager bundle을 bounded compressed strict JSON tree로 바꾼다."""

    if (
        not isinstance(seal, EagerSeal)
        or seal.byteCount != len(seal.payload)
        or seal.byteCount > _MAX_BUNDLE_BYTES
        or seal.resultCount <= 0
        or seal.schemaDigest != arrowSchemaDigest(_EAGER_SCHEMA)
        or not hmac.compare_digest(
            seal.payloadDigest,
            hashlib.sha256(seal.payload).hexdigest(),
        )
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    compressed = zlib.compress(seal.payload, level=9)
    encoded = base64.b64encode(compressed).decode("ascii")
    return {
        "encoding": _PACK_ENCODING,
        "rawSize": seal.byteCount,
        "rawDigest": seal.payloadDigest,
        "resultCount": seal.resultCount,
        "schemaDigest": seal.schemaDigest,
        "payload": encoded,
    }


def unpackEagerSeal(
    value: Any,
    *,
    selectors: Sequence[Mapping[str, str]],
) -> EagerSeal:
    """Compressed private state를 복원하고 Arrow result identity를 전수 검증한다."""

    expected = {
        "encoding",
        "rawSize",
        "rawDigest",
        "resultCount",
        "schemaDigest",
        "payload",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ContinuationError("CONTINUATION_CORRUPT")
    rawSize = value["rawSize"]
    resultCount = value["resultCount"]
    encoded = value["payload"]
    if (
        value["encoding"] != _PACK_ENCODING
        or type(rawSize) is not int
        or not 0 < rawSize <= _MAX_BUNDLE_BYTES
        or type(resultCount) is not int
        or resultCount != len(selectors)
        or not 0 < resultCount <= _MAX_RESULT_COUNT
        or type(encoded) is not str
        or not encoded
        or len(encoded) > 4 * ((_MAX_BUNDLE_BYTES + 2) // 3)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    rawDigest = _requireDigest(value["rawDigest"])
    schemaDigest = _requireDigest(value["schemaDigest"])
    if schemaDigest != arrowSchemaDigest(_EAGER_SCHEMA):
        raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
    try:
        compressed = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None
    decoder = zlib.decompressobj()
    try:
        payload = decoder.decompress(compressed, _MAX_BUNDLE_BYTES + 1)
    except zlib.error:
        raise ContinuationError("CONTINUATION_CORRUPT") from None
    if (
        len(payload) > _MAX_BUNDLE_BYTES
        or decoder.unconsumed_tail
        or not decoder.eof
        or decoder.unused_data
        or decoder.flush()
        or len(payload) != rawSize
        or not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), rawDigest)
    ):
        raise ContinuationError("CONTINUATION_CORRUPT")
    _decodeBundle(payload, selectors=selectors)
    return EagerSeal(payload, rawDigest, rawSize, resultCount, schemaDigest)


def eagerResultAt(
    packedSeal: Any,
    *,
    selectors: Sequence[Mapping[str, str]],
    index: int,
) -> bytes:
    """검증된 seal에서 한 selector의 encoded DataResult를 반환한다."""

    if type(index) is not int or not 0 <= index < len(selectors):
        raise ContinuationError("CONTINUATION_CORRUPT")
    seal = unpackEagerSeal(packedSeal, selectors=selectors)
    return _decodeBundle(seal.payload, selectors=selectors)[index]


def validateEagerSeal(
    packedSeal: Any,
    *,
    selectors: Sequence[Mapping[str, str]],
    descriptor: DataAssetDescriptor,
    requestId: str,
    snapshotId: str,
    contractHash: str,
) -> EagerSeal:
    """Seal payload 전체를 request, asset, selector identity에 다시 결박한다."""

    seal = unpackEagerSeal(packedSeal, selectors=selectors)
    payloads = _decodeBundle(seal.payload, selectors=selectors)
    composite = importlib.import_module("dartlab.dataHub.compositePaging")
    expectedAsset = (AssetRef(descriptor.assetId, descriptor.assetVersionId),)
    for payload, selector in zip(payloads, selectors, strict=True):
        result = composite._decodeEagerResult(payload)
        if (
            result.assets != expectedAsset
            or result.snapshotId != snapshotId
            or result.contractHash != contractHash
            or result.continuation is not None
            or any(partition.requestId != requestId for partition in result.partitions)
            or any(dict(partition.selector) != dict(selector) for partition in result.partitions)
        ):
            raise ContinuationError("CONTINUATION_CORRUPT")
    return seal


def eagerCodePin(
    descriptor: DataAssetDescriptor,
    *,
    requestedMeasures: Sequence[str] = (),
) -> str:
    """Callable 또는 engine axis의 parent-child 실행 identity를 만든다."""

    owner = importlib.import_module("dartlab.dataHub.ownerPaging")
    activeMeasures = tuple(requestedMeasures)
    if any(type(measure) is not str or not measure for measure in activeMeasures):
        raise ContinuationError("PAGEABLE_EAGER_CODE_PIN_FAILED")
    if descriptor.executorKind == "callable":
        return owner._ownerCodePin(descriptor, activeMeasures)
    if descriptor.executorKind != "engineAxis":
        raise ContinuationError("PAGEABLE_EAGER_EXECUTOR_UNSUPPORTED")
    import dartlab

    executor = getattr(dartlab, descriptor.owner, None)
    if not callable(executor):
        raise ContinuationError("PAGEABLE_EAGER_EXECUTOR_UNSUPPORTED")
    call = getattr(type(executor), "__call__", None)
    moduleNames = {
        type(executor).__module__,
        f"dartlab.{descriptor.owner}",
    }
    sourceParts = descriptor.sourceRef.split(":", 2)
    if len(sourceParts) == 3 and sourceParts[0] == "python" and sourceParts[1]:
        moduleNames.add(sourceParts[1])
    try:
        sourceFile = inspect.getsourcefile(type(executor))
    except (OSError, TypeError):
        sourceFile = None
    moduleFiles: set[str] = set()
    candidateFiles = (
        sourceFile,
        getattr(executor, "__file__", None),
        *(getattr(sys.modules.get(moduleName), "__file__", None) for moduleName in moduleNames),
    )
    for candidate in candidateFiles:
        if isinstance(candidate, str) and candidate:
            path = Path(candidate)
            if path.is_file():
                moduleFiles.add(str(path.resolve()))
    for moduleName in moduleNames:
        try:
            spec = importlib.util.find_spec(moduleName)
        except (ImportError, ValueError):
            spec = None
        if spec is not None and isinstance(spec.origin, str) and spec.origin:
            path = Path(spec.origin)
            if path.is_file():
                moduleFiles.add(str(path.resolve()))
    try:
        moduleDigests = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in sorted(moduleFiles)}
    except OSError:
        raise ContinuationError("PAGEABLE_EAGER_CODE_PIN_FAILED") from None
    if not moduleDigests:
        raise ContinuationError("PAGEABLE_EAGER_CODE_PIN_FAILED")
    try:
        callCode = None if call is None else owner._codePinTree(call.__code__)
    except AttributeError:
        callCode = None
    if callCode is None:
        try:
            callCode = owner._codePinTree(executor.__code__)
        except AttributeError:
            pass
    if callCode is None:
        raise ContinuationError("PAGEABLE_EAGER_CODE_PIN_FAILED")
    return canonicalDigest(
        {
            "descriptor": owner._descriptorTree(descriptor),
            "executorType": f"{type(executor).__module__}.{type(executor).__qualname__}",
            "moduleDigests": moduleDigests,
            "callCode": callCode,
            "requestedMeasures": list(activeMeasures),
        }
    )


def _resultForSelector(
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    selector: Mapping[str, str],
    *,
    requestId: str,
    snapshotId: str,
    contractHash: str,
    universeSnapshotId: str | None,
    maxRows: int,
    maxBytes: int,
    workDeadline: float,
) -> bytes:
    execution = importlib.import_module("dartlab.dataHub.execution")
    activeQuery = dataclasses.replace(
        query,
        budget=QueryBudget(
            maxRows=maxRows,
            maxBytes=maxBytes,
            timeoutMs=max(1, min(query.budget.timeoutMs, int(requireDeadline(workDeadline) * 1000))),
            maxAssets=1,
            maxSubjects=query.budget.maxSubjects,
            maxConcurrency=1,
        ),
    )
    requestRef = execution._requestRef(descriptor, activeQuery, selector, requestId)
    partitions = ()
    gaps: list[DataGap] = []
    coverageRows: tuple[UniverseCoverage, ...] = ()
    try:
        raw = execution._execute(descriptor, activeQuery, selector)
        requireDeadline(workDeadline)
        membership = None
        if activeQuery.universe is not None:
            resolved = importlib.import_module("dartlab.dataHub.universe").resolveUniverse(activeQuery.universe)
            requireDeadline(workDeadline)
            if resolved.gaps or resolved.snapshotId != universeSnapshotId:
                raise ContinuationError("CONTINUATION_SOURCE_STALE")
            membership = resolved.byMarket().get(selector.get("market"))
        task = execution._ExecutionTask(
            requestId,
            descriptor,
            activeQuery,
            selector,
            requestRef,
            membership,
            universeSnapshotId,
        )
        coverage = execution._universeCoverage(task, raw)
        if coverage is not None:
            coverageRows = (coverage,)
        partition, projectionGaps = importlib.import_module("dartlab.dataHub.projections").projectOutput(
            raw,
            descriptor,
            activeQuery,
            selector=selector,
            receiptRef=requestRef,
            requestId=requestId,
        )
        gaps.extend(dataclasses.replace(gap, requestId=gap.requestId or requestId) for gap in projectionGaps)
        if partition is not None:
            partitions = (partition,)
            if partition.truncated:
                gaps.append(
                    DataGap(
                        "PAGEABLE_EAGER_SEAL_TRUNCATED",
                        "eager 결과가 content-seal byte 또는 row 상한에서 잘렸습니다",
                        descriptor.assetId,
                        requestId=requestId,
                    )
                )
    except ContinuationError:
        raise
    except Exception as error:
        guardCode = getattr(error, "code", None)
        if guardCode in {
            "OFFLINE_NETWORK_BLOCKED",
            "PAGEABLE_EAGER_WRITE_BLOCKED",
        }:
            raise
        gaps.append(
            DataGap(
                "ASSET_EXECUTION_FAILED",
                "eager owner 실행이 실패했습니다",
                descriptor.assetId,
                requestId=requestId,
            )
        )
    assets = (AssetRef(descriptor.assetId, descriptor.assetVersionId),)
    lineageRefs = tuple(dict.fromkeys(ref for partition in partitions for ref in partition.lineageRefs))
    receipts = tuple(
        dict.fromkeys(partition.lineage.runId for partition in partitions if partition.lineage is not None)
    )
    resultSnapshotId = importlib.import_module("dartlab.dataHub.contentSeal").resultSnapshotId
    result = DataResult(
        status="failed" if not partitions and gaps else "partial" if gaps else "ok",
        partitions=partitions,
        assets=assets,
        snapshotId=snapshotId,
        contractHash=contractHash,
        coverage=Coverage(1, 1, len(partitions), len(gaps)),
        gaps=tuple(gaps),
        lineageRefs=lineageRefs,
        executionReceipts=receipts,
        continuation=None,
        qualityAssertions=tuple(assertion for partition in partitions for assertion in partition.qualityAssertions),
        universeSnapshotId=universeSnapshotId,
        universeCoverage=coverageRows,
        dataSnapshotId=resultSnapshotId(
            catalogSnapshotId=snapshotId,
            contractHash=contractHash,
            partitions=partitions,
            universeSnapshotId=universeSnapshotId,
        ),
    )
    try:
        return importlib.import_module("dartlab.dataHub.compositePaging")._encodeEagerResult(
            result,
            maxBytes=maxBytes,
        )
    except ContinuationError as error:
        if error.code == "CONTINUATION_BYTE_BUDGET":
            raise ContinuationError("PAGEABLE_EAGER_SEAL_RESULT_BUDGET") from None
        raise


def _buildBundle(request: Mapping[str, Any], *, workDeadline: float) -> bytes:
    owner = importlib.import_module("dartlab.dataHub.ownerPaging")
    composite = importlib.import_module("dartlab.dataHub.compositePaging")
    execution = importlib.import_module("dartlab.dataHub.execution")
    descriptor = owner._decodeDescriptor(request["descriptor"])
    query = composite._decodeQuery(request["query"])
    selectors = request["selectors"]
    if (
        not isinstance(selectors, list)
        or not selectors
        or len(selectors) > _MAX_RESULT_COUNT
        or any(
            not isinstance(selector, dict)
            or any(type(key) is not str or type(value) is not str for key, value in selector.items())
            for selector in selectors
        )
    ):
        raise ContinuationError("PAGEABLE_EAGER_SELECTOR_UNSUPPORTED")
    requestedMeasures = execution._requestedMeasures(query)
    if not hmac.compare_digest(
        eagerCodePin(
            descriptor,
            requestedMeasures=requestedMeasures,
        ),
        request["codePin"],
    ):
        raise ContinuationError("PAGEABLE_EAGER_CODE_PIN_FAILED")
    count = len(selectors)
    totalRows = request["maxRows"]
    totalBytes = request["maxBytes"]
    if totalRows < count:
        raise ContinuationError("PAGEABLE_EAGER_SEAL_ROW_BUDGET")
    resultBytes = (totalBytes - _BUNDLE_OVERHEAD_BYTES) // count
    if resultBytes < _MIN_RESULT_BYTES:
        raise ContinuationError("PAGEABLE_EAGER_SEAL_BUDGET")
    rowBase, rowExtra = divmod(totalRows, count)
    rows = []
    for index, selector in enumerate(selectors):
        requireDeadline(workDeadline)
        payload = _resultForSelector(
            descriptor,
            query,
            selector,
            requestId=request["requestId"],
            snapshotId=request["snapshotId"],
            contractHash=request["contractHash"],
            universeSnapshotId=request["universeSnapshotId"],
            maxRows=rowBase + (1 if index < rowExtra else 0),
            maxBytes=resultBytes,
            workDeadline=workDeadline,
        )
        rows.append(
            {
                "resultIndex": index,
                "selectorDigest": canonicalDigest(selector),
                "resultPayload": payload,
                "resultDigest": hashlib.sha256(payload).hexdigest(),
            }
        )
    bundle = _arrowPayload(pa.Table.from_pylist(rows, schema=_EAGER_SCHEMA))
    if len(bundle) > totalBytes or len(bundle) > _MAX_BUNDLE_BYTES:
        raise ContinuationError("PAGEABLE_EAGER_SEAL_BUDGET")
    _decodeBundle(bundle, selectors=selectors)
    return bundle


def _decodeRequest(payload: bytes) -> dict[str, Any]:
    root = _loadStrictJson(payload, maxBytes=MAX_OWNER_PROCESS_REQUEST_BYTES)
    expected = {
        "artifactId",
        "codePin",
        "contractHash",
        "descriptor",
        "maxBytes",
        "maxRows",
        "query",
        "requestId",
        "selectors",
        "snapshotId",
        "universeSnapshotId",
        "version",
        "workDeadlineNs",
    }
    if not isinstance(root, dict) or set(root) != expected or root["version"] != _FORMAT_VERSION:
        raise _ProtocolViolation("EAGER_PROCESS_REQUEST_SCHEMA")
    for name in ("artifactId", "codePin", "contractHash"):
        _requireDigest(root[name])
    if (
        type(root["requestId"]) is not str
        or not root["requestId"]
        or type(root["snapshotId"]) is not str
        or not root["snapshotId"]
        or root["universeSnapshotId"] is not None
        and type(root["universeSnapshotId"]) is not str
        or type(root["maxRows"]) is not int
        or root["maxRows"] <= 0
        or type(root["maxBytes"]) is not int
        or not _MIN_RESULT_BYTES < root["maxBytes"] <= _MAX_BUNDLE_BYTES
        or type(root["workDeadlineNs"]) is not int
        or root["workDeadlineNs"] <= 0
        or not isinstance(root["descriptor"], dict)
        or not isinstance(root["query"], dict)
        or not isinstance(root["selectors"], list)
    ):
        raise _ProtocolViolation("EAGER_PROCESS_REQUEST_VALUE")
    return root


def _worker(
    requestPayload: bytes,
    artifactId: str,
    output: list[dict[str, Any]],
) -> None:
    try:
        request = _decodeRequest(requestPayload)
        if request["artifactId"] != artifactId:
            raise _ProtocolViolation("OWNER_PROCESS_ARTIFACT_ID_MISMATCH")
        workDeadline = request["workDeadlineNs"] / 1_000_000_000
        bundle = _buildBundle(request, workDeadline=workDeadline)
        requireDeadline(workDeadline)
        root = _ensureArtifactRoot()
        path = _artifactPath(root, artifactId)
        from dartlab.dataHub.ownerProcess import _writeArtifact

        _writeArtifact(path, root, bundle, maxBytes=_MAX_BUNDLE_BYTES)
        output.append(
            {
                "artifactId": artifactId,
                "byteCount": len(bundle),
                "digest": hashlib.sha256(bundle).hexdigest(),
                "errorCode": None,
                "kind": "result",
                "rowCount": len(request["selectors"]),
                "status": "ok",
            }
        )
    except BaseException as error:
        output.append(
            {
                "artifactId": artifactId,
                "byteCount": None,
                "digest": None,
                "errorCode": _safeErrorCode(error),
                "kind": "result",
                "rowCount": None,
                "status": "failed",
            }
        )


def _childMain(
    sendConnection: Connection,
    startGate: Any,
    requestPayload: bytes,
    artifactId: str,
) -> None:
    output: list[dict[str, Any]] = []
    worker: threading.Thread | None = None
    workerGate = threading.Event()
    try:
        becomeProcessGroupLeader()
        if not startGate.wait(timeout=10.0):
            return
        root = _ensureArtifactRoot()
        path = _artifactPath(root, artifactId)
        from dartlab.dataHub.eagerSandbox import enforceEagerSandbox

        enforceEagerSandbox(path)

        def runWorker() -> None:
            """격리된 thread에서 eager owner worker를 실행한다."""
            workerGate.wait()
            _worker(requestPayload, artifactId, output)

        worker = threading.Thread(
            target=runWorker,
            name="dartlab-eager-process-worker",
            daemon=False,
        )
        worker.start()
        if worker.native_id is None:
            raise RuntimeError("EAGER_PROCESS_WORKER_ID_UNAVAILABLE")
        sendConnection.send_bytes(
            _strictJson(
                {
                    "kind": "ready",
                    "pid": os.getpid(),
                    "threadNativeId": worker.native_id,
                }
            )
        )
        workerGate.set()
        worker.join()
        if len(output) != 1:
            raise RuntimeError("EAGER_PROCESS_WORKER_RESULT_INVALID")
        sendConnection.send_bytes(_strictJson(output[0]))
    except BaseException as error:
        if worker is None or not worker.is_alive():
            try:
                sendConnection.send_bytes(
                    _strictJson(
                        {
                            "artifactId": artifactId,
                            "byteCount": None,
                            "digest": None,
                            "errorCode": _safeErrorCode(error),
                            "kind": "result",
                            "rowCount": None,
                            "status": "failed",
                        }
                    )
                )
            except BaseException:
                pass
    finally:
        workerGate.set()
        sendConnection.close()


__all__ = [
    "EagerSeal",
    "eagerCodePin",
    "eagerResultAt",
    "packEagerSeal",
    "unpackEagerSeal",
    "validateEagerSeal",
]
