"""Panel 공시 변환을 제한된 수명의 자식 프로세스에서 실행한다."""

from __future__ import annotations

import gc
import multiprocessing as mp
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from multiprocessing.connection import wait
from typing import Any, cast

import polars as pl
import pyarrow as pa

_PROCESS_RESULT_TIMEOUT_SECONDS = 15 * 60
_PROCESS_EXIT_TIMEOUT_SECONDS = 30
_PROCESS_SENTINEL_GRACE_SECONDS = 5


@dataclass(frozen=True)
class DocumentInput:
    """공시 하나의 디스크 또는 메모리 zip 입력."""

    receiptNumber: str
    sequence: int
    expandedBytes: int
    transportBytes: int = 0
    zipPath: str | None = None
    zipBytes: bytes | None = None


@dataclass(frozen=True)
class DocumentStage:
    """자식 프로세스가 만든 공시별 bounded parquet stage."""

    path: str
    period: str
    receiptNumber: str
    sequence: int


@dataclass(frozen=True)
class DocumentProcessFailure:
    """pickle 경계를 보존하는 자식 프로세스 실패 정보."""

    errorType: str
    message: str
    tracebackText: str
    receiptNumber: str | None


@dataclass(frozen=True)
class DocumentProcessRequest:
    """자식 프로세스 한 번이 처리할 bounded 공시 묶음."""

    code: str
    refPath: str
    stageRoot: str
    documents: tuple[DocumentInput, ...]
    matchThreshold: float


@dataclass(frozen=True)
class DocumentProcessResult:
    """자식 프로세스의 성공 stage 또는 구조화 실패."""

    stages: tuple[DocumentStage, ...]
    processedReceipts: tuple[str, ...]
    failure: DocumentProcessFailure | None = None


class DocumentProcessExecutionError(RuntimeError):
    """자식 프로세스가 결과를 보내거나 제한 시간 안에 종료하지 못한 상태."""


DocumentProcessor = Callable[
    [DocumentInput, DocumentProcessRequest, pl.DataFrame],
    tuple[DocumentStage, ...],
]


def processDocumentChunk(
    request: DocumentProcessRequest,
    processor: DocumentProcessor,
) -> DocumentProcessResult:
    """공시 묶음을 변환하고 stage를 남긴 뒤 프로세스 종료로 native heap을 회수한다.

    Args:
        request: 회사, ref, stage 경로와 개수·해제 byte가 제한된 공시 입력.
        processor: builder가 주입하는 단일 공시 변환 함수.

    Returns:
        생성 stage, 처리 완료 접수번호와 선택적 구조화 실패.

    Raises:
        없음. pickle 불가능한 원 예외는 failure에 타입, 메시지, traceback으로 보존한다.

    Example:
        >>> processDocumentChunk(request, processor)  # doctest: +SKIP
    """

    from .refScan.refMatcher import precomputeRefTokens, setGlobalRefTokens

    stages: list[DocumentStage] = []
    processedReceipts: list[str] = []
    activeReceipt: str | None = None
    try:
        refDf = pl.read_parquet(request.refPath)
        setGlobalRefTokens(precomputeRefTokens(refDf))
        for document in request.documents:
            activeReceipt = document.receiptNumber
            stages.extend(processor(document, request, refDf))
            processedReceipts.append(document.receiptNumber)
            gc.collect()
            pa.default_memory_pool().release_unused()
    except BaseException as exc:
        return DocumentProcessResult(
            stages=tuple(stages),
            processedReceipts=tuple(processedReceipts),
            failure=DocumentProcessFailure(
                errorType=type(exc).__name__,
                message=str(exc),
                tracebackText=traceback.format_exc(),
                receiptNumber=activeReceipt,
            ),
        )
    return DocumentProcessResult(
        stages=tuple(stages),
        processedReceipts=tuple(processedReceipts),
    )


def _sendDocumentProcessResult(
    connection: Any,
    request: DocumentProcessRequest,
    processor: DocumentProcessor,
) -> None:
    """자식 진입점에서 구조화 결과를 pipe로 한 번 전송한다."""

    try:
        connection.send(processDocumentChunk(request, processor))
    finally:
        connection.close()


def _stopProcess(process: Any) -> list[BaseException]:
    """실패한 자식 프로세스를 종료하고 cleanup 오류를 모은다."""

    errors: list[BaseException] = []
    try:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join(timeout=5)
        if process.is_alive():
            errors.append(
                DocumentProcessExecutionError(f"panel document process를 종료하지 못했습니다: pid={process.pid}")
            )
    except BaseException as exc:
        errors.append(exc)
    return errors


def _closeProcessResources(
    process: Any,
    receiveConnection: Any,
    sendConnection: Any,
) -> list[BaseException]:
    """프로세스와 pipe handle을 닫고 모든 cleanup 실패를 반환한다."""

    errors = _stopProcess(process)
    for resource in (receiveConnection, sendConnection):
        try:
            resource.close()
        except BaseException as exc:
            errors.append(exc)
    try:
        if not process.is_alive():
            process.close()
    except BaseException as exc:
        errors.append(exc)
    return errors


def _receiveDocumentProcessResult(
    process: Any,
    receiveConnection: Any,
    *,
    code: str,
    timeoutSeconds: float,
) -> DocumentProcessResult:
    """pipe 결과와 자식 종료 sentinel을 함께 기다린다.

    Args:
        process: 시작된 multiprocessing Process.
        receiveConnection: 부모가 소유한 단방향 수신 pipe.
        code: 오류 provenance용 종목코드.
        timeoutSeconds: 결과 또는 자식 종료를 기다릴 최대 시간.

    Returns:
        자식이 pipe로 보낸 구조화 결과.

    Raises:
        DocumentProcessExecutionError: timeout, 결과 없는 종료 또는 EOF.

    Example:
        >>> _receiveDocumentProcessResult(process, connection, code="005930", timeoutSeconds=30)  # doctest: +SKIP
    """

    ready = wait(
        [receiveConnection, process.sentinel],
        timeout=timeoutSeconds,
    )
    if not ready:
        raise DocumentProcessExecutionError(
            f"panel document process 결과 대기 시간 초과: code={code}, timeoutSeconds={timeoutSeconds}"
        )

    if receiveConnection not in ready and not receiveConnection.poll(0):
        process.join(timeout=0)
        raise DocumentProcessExecutionError(
            f"panel document process가 결과 없이 종료했습니다: code={code}, exitCode={process.exitcode}"
        )
    try:
        return cast(DocumentProcessResult, receiveConnection.recv())
    except EOFError as exc:
        process.join(timeout=_PROCESS_SENTINEL_GRACE_SECONDS)
        raise DocumentProcessExecutionError(
            f"panel document process pipe가 결과 없이 닫혔습니다: code={code}, exitCode={process.exitcode}"
        ) from exc


def runDocumentProcess(
    request: DocumentProcessRequest,
    processor: DocumentProcessor,
    *,
    timeoutSeconds: float = _PROCESS_RESULT_TIMEOUT_SECONDS,
) -> DocumentProcessResult:
    """공시 묶음을 단일 spawn 자식에서 실행하고 결과와 종료를 모두 확인한다.

    Args:
        request: 회사 하나의 bounded 공시 입력 묶음.
        processor: builder가 주입하는 단일 공시 변환 함수.
        timeoutSeconds: 결과 수신 최대 대기 시간.

    Returns:
        자식이 보낸 구조화 성공 또는 실패 결과.

    Raises:
        ValueError: timeout이 양수가 아닐 때.
        DocumentProcessExecutionError: 결과 미전송, 비정상 종료 또는 종료 지연.

    Example:
        >>> runDocumentProcess(request, processor)  # doctest: +SKIP
    """

    if timeoutSeconds <= 0:
        raise ValueError("panel document process timeout은 양수여야 합니다")

    context = mp.get_context("spawn")
    receiveConnection, sendConnection = context.Pipe(duplex=False)
    process = context.Process(
        target=_sendDocumentProcessResult,
        args=(sendConnection, request, processor),
        name=f"panel-document-{request.code}",
    )
    primaryError: BaseException | None = None
    result: DocumentProcessResult | None = None
    try:
        process.start()
        sendConnection.close()
        result = _receiveDocumentProcessResult(
            process,
            receiveConnection,
            code=request.code,
            timeoutSeconds=timeoutSeconds,
        )

        process.join(timeout=_PROCESS_EXIT_TIMEOUT_SECONDS)
        if process.is_alive():
            raise DocumentProcessExecutionError(
                "panel document process가 결과 전송 후 종료하지 않았습니다: "
                f"code={request.code}, timeoutSeconds={_PROCESS_EXIT_TIMEOUT_SECONDS}"
            )
        if process.exitcode != 0:
            raise DocumentProcessExecutionError(
                f"panel document process가 비정상 종료했습니다: code={request.code}, exitCode={process.exitcode}"
            )
    except BaseException as exc:
        primaryError = exc
    cleanupErrors = _closeProcessResources(
        process,
        receiveConnection,
        sendConnection,
    )
    if primaryError is not None:
        if cleanupErrors:
            raise BaseExceptionGroup(
                "panel document process 실행과 cleanup이 모두 실패했습니다",
                [primaryError, *cleanupErrors],
            ) from None
        raise primaryError
    if cleanupErrors:
        raise BaseExceptionGroup(
            "panel document process cleanup이 실패했습니다",
            cleanupErrors,
        )
    if result is None:
        raise DocumentProcessExecutionError(f"panel document process 결과가 없습니다: code={request.code}")
    return result


__all__ = [
    "DocumentInput",
    "DocumentProcessExecutionError",
    "DocumentProcessFailure",
    "DocumentProcessRequest",
    "DocumentProcessResult",
    "DocumentProcessor",
    "DocumentStage",
    "processDocumentChunk",
    "runDocumentProcess",
]
