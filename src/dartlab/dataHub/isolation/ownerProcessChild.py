"""Owner page 자식 프로세스의 진입점과 worker.

부모는 cursor 와 commit 만 소유하고 자식은 bounded page 계산만 맡는다. 자식은 새
process group leader 가 되고 sandbox 를 설치한 뒤 무거운 모듈을 main thread 에서
먼저 import 한다. worker 는 자기 work deadline 안에서 스스로 끝난다.
"""

from __future__ import annotations

import hashlib
import importlib
import os
import sys
import threading
import time
from multiprocessing.connection import Connection
from typing import Any

from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.isolation.ownerProcessArtifacts import (
    _artifactPath,
    _decodeRequest,
    _ensureArtifactRoot,
    _safeErrorCode,
    _strictJson,
    _writeArtifact,
)
from dartlab.dataHub.isolation.ownerProcessModels import (
    _ProtocolViolation,
)
from dartlab.dataHub.isolation.processLifecycle import (
    becomeProcessGroupLeader,
    describeStalledThread,
)
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

_log = dataHubLogger(__name__)


def _pageWorker(
    requestPayload: bytes,
    assignedArtifactId: str,
    output: list[dict[str, Any]],
) -> None:
    try:
        artifactId, sessionPayload, workDeadline = _decodeRequest(requestPayload)
        if artifactId != assignedArtifactId:
            raise _ProtocolViolation("OWNER_PROCESS_ARTIFACT_ID_MISMATCH")
        from dartlab.dataHub.continuation import inspectArrowIpcPayload
        from dartlab.dataHub.paging import owner as ownerPaging

        # durable 인코딩은 엔티티 목록을 담지 않으므로 IPC 크기가 universe 규모와
        # 무관하다. 목록은 자식이 universe 를 재해소해 채우고, 이미 실려 온 경우
        # (합성 세션 등) 그대로 쓴다. `_decodeSession` 이 재수화까지 수행한다.
        session = ownerPaging._decodeProcessSession(sessionPayload)
        candidates = ownerPaging._candidates(session)
        if not candidates:
            raise ContinuationError("CONTINUATION_CORRUPT")
        verifiedSources = ownerPaging._prepareEntitySources(
            candidates,
            deadline=workDeadline,
        )
        ownerPaging.requireDeadline(workDeadline)
        entries = ownerPaging._boundedEntries(
            candidates,
            session,
            deadline=workDeadline,
            verifiedSources=verifiedSources,
        )
        ownerPaging.requireDeadline(workDeadline)
        payload = ownerPaging._encodePage(
            entries,
            maxPageRows=session.pageMaxRows,
            maxPageBytes=session.pageMaxBytes,
            maxLogicalBytes=session.pageMaxLogicalBytes,
        )
        ownerPaging.requireDeadline(workDeadline)
        claimedRows = sum(
            0 if entry.payload is None else inspectArrowIpcPayload(entry.payload).rowCount for entry in entries
        )
        decoded = ownerPaging._decodePage(
            payload,
            claimedRowCount=claimedRows,
            maxPageRows=session.pageMaxRows,
            maxPageBytes=session.pageMaxBytes,
            maxLogicalBytes=session.pageMaxLogicalBytes,
        )
        root = _ensureArtifactRoot()
        path = _artifactPath(root, assignedArtifactId)
        _writeArtifact(path, root, payload, maxBytes=session.pageMaxBytes)
        ownerPaging.requireDeadline(workDeadline)
        output.append(
            {
                "artifactId": assignedArtifactId,
                "byteCount": len(payload),
                "digest": hashlib.sha256(payload).hexdigest(),
                "errorCode": None,
                "kind": "result",
                "rowCount": decoded.facts.rowCount,
                "status": "ok",
            }
        )
    except BaseException as error:
        output.append(
            {
                "artifactId": assignedArtifactId,
                "byteCount": None,
                "digest": None,
                "errorCode": _safeErrorCode(error),
                "kind": "result",
                "rowCount": None,
                "status": "failed",
            }
        )


def _warmChildImports() -> None:
    """무거운 모듈을 main thread 에서 먼저 import 한다.

    worker 는 별도 thread 에서 돌고, 자식은 fresh spawn 이라 polars 와 pyarrow 같은
    C 확장을 그 thread 에서 최초로 import 하게 된다. POSIX 에서 비-main thread 의
    C 확장 최초 import 는 확장이 설치하는 thread pool 이나 lock 때문에 교착할 수 있고,
    그러면 자식이 자기 기한을 꽉 채우고도 끝나지 않는다.

    sandbox 를 이미 설치한 뒤 호출하므로 write 와 network 차단은 그대로 유지된다.
    실패는 삼키지 않고 worker 가 같은 import 를 다시 시도해 typed 오류로 보고하게 둔다.
    """

    for moduleName in (
        "polars",
        "pyarrow",
        "dartlab.dataHub.paging.owner",
        "dartlab.dataHub.paging.composite",
        "dartlab.dataHub.execution",
    ):
        try:
            importlib.import_module(moduleName)
        except Exception:
            recordFailure(_log, "CHILD_WARM_IMPORT_FAILED", context={"module": moduleName})


def _pageChildMain(
    sendConnection: Connection,
    startGate: Any,
    requestPayload: bytes,
    artifactId: str,
) -> None:
    output: list[dict[str, Any]] = []
    worker: threading.Thread | None = None
    workerGate = threading.Event()
    try:
        # POSIX 는 Job Object 가 없으므로 자식이 새 session leader 가 돼야 부모가
        # 손자까지 group 단위로 회수할 수 있다. Windows 에서는 아무 일도 하지 않는다.
        becomeProcessGroupLeader()
        if not startGate.wait(timeout=10.0):
            return
        _artifactId, _sessionPayload, workDeadline = _decodeRequest(requestPayload)
        root = _ensureArtifactRoot()
        path = _artifactPath(root, artifactId)
        from dartlab.dataHub.isolation.eagerSandbox import enforceProcessSandbox

        enforceProcessSandbox(path)

        def runWorker() -> None:
            """격리된 thread에서 owner page worker를 실행한다."""
            workerGate.wait()
            _pageWorker(requestPayload, artifactId, output)

        worker = threading.Thread(
            target=runWorker,
            name="dartlab-owner-process-worker",
            daemon=False,
        )
        worker.start()
        nativeId = worker.native_id
        if nativeId is None:
            raise RuntimeError("OWNER_PROCESS_WORKER_ID_UNAVAILABLE")
        sendConnection.send_bytes(
            _strictJson(
                {
                    "kind": "ready",
                    "pid": os.getpid(),
                    "threadNativeId": nativeId,
                }
            )
        )
        # ready 를 먼저 보낸 뒤 main thread 에서 무거운 모듈을 데운다. ready 는 자식이
        # 살아 있다는 신호이고 import 는 work 이므로 준비 창을 잡아먹으면 안 된다.
        # workerGate 를 아직 열지 않았으므로 worker 와 동시 import 경합도 없다.
        _warmChildImports()
        workerGate.set()
        # join 에 기한이 없으면 worker 가 멈출 때 자식이 영원히 살아남는다. 부모의 kill
        # 경로가 결국 회수하지만 그때까지 실행 슬롯을 통째로 붙잡고, 실패 원인도 남지
        # 않는다. 자식은 자기 work deadline 안에서 스스로 끝나야 한다.
        joinSeconds = max(0.0, workDeadline - time.perf_counter())
        worker.join(timeout=joinSeconds)
        if worker.is_alive():
            # 멈춘 지점을 자식 stderr 로 남긴다. 부모가 받는 것은 평평한 실패 코드라
            # 여기서 잡지 않으면 어디서 섰는지 영영 알 수 없다.
            print(
                f"[dataHub] owner worker stalled at {describeStalledThread(worker.ident)}",
                file=sys.stderr,
                flush=True,
            )
            raise RuntimeError("OWNER_PROCESS_WORKER_DID_NOT_FINISH")
        if len(output) != 1:
            raise RuntimeError("OWNER_PROCESS_WORKER_RESULT_INVALID")
        sendConnection.send_bytes(_strictJson(output[0]))
    except BaseException as error:
        # worker 는 결과를 `output` 리스트에만 넣고 이 connection 을 만지지 않는다.
        # 그래서 worker 가 아직 살아 있어도 여기서 실패를 보내는 것이 안전하다.
        # 보내지 않으면 부모는 원인 대신 자기 기한이 다 찰 때까지 침묵을 받는다.
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
