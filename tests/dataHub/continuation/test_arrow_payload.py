"""Actual Arrow IPC continuation payload validation locks."""

from __future__ import annotations

import pyarrow as pa
import pytest

from dartlab.dataHub.continuation import (
    ContinuationError,
    arrowSchemaDigest,
    inspectArrowIpcPayload,
    validateArrowIpcPayload,
)


def _table() -> pa.Table:
    return pa.table({"entityId": ["KR:005930", "US:AAPL"], "value": [100, 200]})


def _streamPayload(table: pa.Table) -> bytes:
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()


def _filePayload(table: pa.Table) -> bytes:
    sink = pa.BufferOutputStream()
    with pa.ipc.new_file(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()


@pytest.mark.parametrize(("factory", "kind"), ((_streamPayload, "stream"), (_filePayload, "file")))
def testArrowPayloadFactsComeFromActualIpc(factory, kind):
    table = _table()
    payload = factory(table)
    facts = inspectArrowIpcPayload(payload)

    assert facts.rowCount == table.num_rows
    assert facts.byteCount == len(payload)
    assert facts.logicalByteCount == table.nbytes
    assert facts.schemaDigest == arrowSchemaDigest(table.schema)
    assert facts.containerKind == kind


def testArrowPayloadRejectsFalseRowsSchemaAndBytes():
    table = _table()
    payload = _streamPayload(table)
    schemaDigest = arrowSchemaDigest(table.schema)

    with pytest.raises(ContinuationError) as rowError:
        validateArrowIpcPayload(
            payload,
            claimedRowCount=999,
            expectedSchemaDigest=schemaDigest,
            maxPageBytes=len(payload),
        )
    assert rowError.value.code == "CONTINUATION_PAYLOAD_ROW_MISMATCH"

    with pytest.raises(ContinuationError) as schemaError:
        validateArrowIpcPayload(
            payload,
            claimedRowCount=2,
            expectedSchemaDigest="0" * 64,
            maxPageBytes=len(payload),
        )
    assert schemaError.value.code == "CONTINUATION_PAYLOAD_SCHEMA_MISMATCH"

    with pytest.raises(ContinuationError) as byteError:
        validateArrowIpcPayload(
            payload,
            claimedRowCount=2,
            expectedSchemaDigest=schemaDigest,
            maxPageBytes=len(payload) - 1,
        )
    assert byteError.value.code == "CONTINUATION_BYTE_BUDGET"


@pytest.mark.parametrize("payload", (b"not-arrow", _streamPayload(_table()) + b"trailing-secret"))
def testMalformedOrTrailingArrowBytesFailClosed(payload):
    with pytest.raises(ContinuationError) as error:
        inspectArrowIpcPayload(payload)
    assert error.value.code == "CONTINUATION_PAYLOAD_INVALID"
    assert "trailing-secret" not in str(error.value)


def testConcatenatedArrowFilesFailClosed():
    payload = _filePayload(_table())

    with pytest.raises(ContinuationError) as error:
        inspectArrowIpcPayload(payload + payload)
    assert error.value.code == "CONTINUATION_PAYLOAD_INVALID"


@pytest.mark.parametrize("containerKind", ("stream", "file"))
def testCompressedIpcBombIsRejectedBeforeDecode(containerKind):
    table = pa.table({"blob": ["x" * 4096] * 4096})
    sink = pa.BufferOutputStream()
    options = pa.ipc.IpcWriteOptions(compression="zstd")
    factory = pa.ipc.new_stream if containerKind == "stream" else pa.ipc.new_file
    with factory(sink, table.schema, options=options) as writer:
        writer.write_table(table)
    payload = sink.getvalue().to_pybytes()

    assert len(payload) < table.nbytes // 10
    with pytest.raises(ContinuationError) as error:
        inspectArrowIpcPayload(payload, maxLogicalBytes=1024)
    assert error.value.code == "CONTINUATION_COMPRESSION_UNSUPPORTED"


def testUncompressedLogicalBodyBudgetIsCheckedBeforeDecode():
    payload = _streamPayload(_table())

    with pytest.raises(ContinuationError) as error:
        inspectArrowIpcPayload(payload, maxLogicalBytes=1)
    assert error.value.code == "CONTINUATION_LOGICAL_BYTE_BUDGET"
