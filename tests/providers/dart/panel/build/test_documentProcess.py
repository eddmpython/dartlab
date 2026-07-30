"""Panel 공시 변환 process 경계의 구조화 실패 회귀."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import polars as pl
import pytest


def _exitWithoutResult(document: object, request: object, refDf: pl.DataFrame) -> Any:
    del document, request, refDf
    os._exit(17)


def test_invalid_zip_failure_crosses_process_boundary_without_loss(tmp_path: Path) -> None:
    from dartlab.providers.dart.panel.build.builder import (
        _processDocumentInput,
        panelXbrlRefPath,
    )
    from dartlab.providers.dart.panel.build.documentProcess import (
        DocumentInput,
        DocumentProcessRequest,
        processDocumentChunk,
    )

    refPath = tmp_path / "ref.parquet"
    pl.read_parquet(panelXbrlRefPath()).write_parquet(refPath)
    request = DocumentProcessRequest(
        code="000001",
        refPath=str(refPath),
        stageRoot=str(tmp_path),
        documents=(
            DocumentInput(
                receiptNumber="20250319000001",
                sequence=0,
                expandedBytes=9,
                transportBytes=9,
                zipBytes=b"not-a-zip",
            ),
        ),
        matchThreshold=0.70,
    )

    result = processDocumentChunk(request, _processDocumentInput)

    assert result.processedReceipts == ()
    assert result.stages == ()
    assert result.failure is not None
    assert result.failure.errorType == "PanelBuildError"
    assert "zip_read" in result.failure.message
    assert "20250319000001" in result.failure.tracebackText


def test_spawn_process_returns_structured_failure_and_exits(tmp_path: Path) -> None:
    from dartlab.providers.dart.panel.build.builder import (
        _processDocumentInput,
        panelXbrlRefPath,
    )
    from dartlab.providers.dart.panel.build.documentProcess import (
        DocumentInput,
        DocumentProcessRequest,
        runDocumentProcess,
    )

    refPath = tmp_path / "ref.parquet"
    pl.read_parquet(panelXbrlRefPath()).write_parquet(refPath)
    request = DocumentProcessRequest(
        code="000001",
        refPath=str(refPath),
        stageRoot=str(tmp_path),
        documents=(
            DocumentInput(
                receiptNumber="20250319000001",
                sequence=0,
                expandedBytes=9,
                transportBytes=9,
                zipBytes=b"not-a-zip",
            ),
        ),
        matchThreshold=0.70,
    )

    result = runDocumentProcess(
        request,
        _processDocumentInput,
        timeoutSeconds=30,
    )

    assert result.failure is not None
    assert result.failure.errorType == "PanelBuildError"
    assert result.processedReceipts == ()


def test_spawn_process_exit_without_result_fails_immediately(tmp_path: Path) -> None:
    """pipe EOF가 오지 않아도 process sentinel이 비정상 종료를 즉시 알린다."""

    from dartlab.providers.dart.panel.build.builder import panelXbrlRefPath
    from dartlab.providers.dart.panel.build.documentProcess import (
        DocumentInput,
        DocumentProcessExecutionError,
        DocumentProcessRequest,
        runDocumentProcess,
    )

    refPath = tmp_path / "ref.parquet"
    pl.read_parquet(panelXbrlRefPath()).write_parquet(refPath)
    request = DocumentProcessRequest(
        code="000001",
        refPath=str(refPath),
        stageRoot=str(tmp_path),
        documents=(
            DocumentInput(
                receiptNumber="20250319000001",
                sequence=0,
                expandedBytes=1,
                zipPath=str(tmp_path / "unused.zip"),
            ),
        ),
        matchThreshold=0.70,
    )

    started = time.perf_counter()
    with pytest.raises(DocumentProcessExecutionError, match="exitCode=17"):
        runDocumentProcess(
            request,
            _exitWithoutResult,
            timeoutSeconds=30,
        )
    assert time.perf_counter() - started < 15


def test_document_chunks_are_bounded_and_reject_duplicate_receipts() -> None:
    from dartlab.providers.dart.panel.build.builder import _documentChunks
    from dartlab.providers.dart.panel.build.documentProcess import DocumentInput

    documents = [
        DocumentInput(
            receiptNumber=f"{index:014d}",
            sequence=index,
            expandedBytes=1,
            transportBytes=1,
            zipBytes=b"x",
        )
        for index in range(17)
    ]
    chunks = list(_documentChunks(documents))
    assert [len(chunk) for chunk in chunks] == [12, 5]

    with pytest.raises(ValueError, match="중복"):
        list(_documentChunks([documents[0], documents[0]]))


def test_document_chunks_honor_expanded_byte_budget() -> None:
    from dartlab.providers.dart.panel.build.builder import (
        _EXPANDED_BYTES_PER_PROCESS,
        _ZIP_BYTES_PER_PROCESS,
        PanelBuildError,
        _documentChunks,
    )
    from dartlab.providers.dart.panel.build.documentProcess import DocumentInput

    first = DocumentInput(
        receiptNumber="20250319000001",
        sequence=0,
        expandedBytes=_EXPANDED_BYTES_PER_PROCESS - 1,
        transportBytes=1,
        zipBytes=b"x",
    )
    second = DocumentInput(
        receiptNumber="20250320000002",
        sequence=1,
        expandedBytes=2,
        transportBytes=1,
        zipBytes=b"x",
    )
    assert [len(chunk) for chunk in _documentChunks([first, second])] == [1, 1]

    oversized = DocumentInput(
        receiptNumber="20250321000003",
        sequence=2,
        expandedBytes=_EXPANDED_BYTES_PER_PROCESS + 1,
        transportBytes=1,
        zipBytes=b"x",
    )
    with pytest.raises(PanelBuildError, match="document_memory"):
        list(_documentChunks([oversized]))

    transportOversized = DocumentInput(
        receiptNumber="20250322000004",
        sequence=3,
        expandedBytes=1,
        transportBytes=_ZIP_BYTES_PER_PROCESS + 1,
        zipBytes=b"x",
    )
    with pytest.raises(PanelBuildError, match="document_memory"):
        list(_documentChunks([transportOversized]))
