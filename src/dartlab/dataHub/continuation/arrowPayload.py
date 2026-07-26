"""Arrow IPC payload inspection for bounded continuation pages."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from typing import Any, Never

from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

from .contracts import ArrowPayloadFacts, ContinuationError

_FILE_MAGIC = b"ARROW1"
_CONTINUATION_MARKER = 0xFFFFFFFF


_log = dataHubLogger(__name__)


@dataclass(frozen=True, slots=True)
class _IpcPreflight:
    containerKind: str
    rowCount: int
    recordBatchCount: int
    logicalBodyBytes: int


def _invalidPayload() -> Never:
    raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")


def _unpack(data: bytes, offset: int, formatValue: str) -> int:
    try:
        size = struct.calcsize(formatValue)
        if offset < 0 or offset + size > len(data):
            _invalidPayload()
        return int(struct.unpack_from(formatValue, data, offset)[0])
    except ContinuationError:
        raise
    except Exception:
        _invalidPayload()


def _tableField(data: bytes, table: int, fieldIndex: int) -> int | None:
    vtableDistance = _unpack(data, table, "<i")
    if vtableDistance <= 0:
        _invalidPayload()
    vtable = table - vtableDistance
    vtableSize = _unpack(data, vtable, "<H")
    objectSize = _unpack(data, vtable + 2, "<H")
    if vtable < 0 or vtableSize < 4 or vtable + vtableSize > len(data) or objectSize < 4:
        _invalidPayload()
    entry = vtable + 4 + fieldIndex * 2
    if entry + 2 > vtable + vtableSize:
        return None
    relative = _unpack(data, entry, "<H")
    if relative == 0:
        return None
    if relative >= objectSize:
        _invalidPayload()
    position = table + relative
    if position < 0 or position >= len(data):
        _invalidPayload()
    return position


def _followOffset(data: bytes, position: int) -> int:
    relative = _unpack(data, position, "<I")
    target = position + relative
    if relative == 0 or target < 0 or target + 4 > len(data):
        _invalidPayload()
    return target


def _recordBatchMetadata(data: bytes, table: int) -> tuple[int, bool]:
    lengthPosition = _tableField(data, table, 0)
    rowCount = 0 if lengthPosition is None else _unpack(data, lengthPosition, "<q")
    if rowCount < 0:
        _invalidPayload()
    return rowCount, _tableField(data, table, 3) is not None


def _messageMetadata(metadata: bytes) -> tuple[int, int, bool, bool, bool]:
    root = _unpack(metadata, 0, "<I")
    if root < 4 or root + 4 > len(metadata):
        _invalidPayload()
    headerTypePosition = _tableField(metadata, root, 1)
    headerPosition = _tableField(metadata, root, 2)
    bodyPosition = _tableField(metadata, root, 3)
    headerType = 0 if headerTypePosition is None else _unpack(metadata, headerTypePosition, "<B")
    bodyLength = 0 if bodyPosition is None else _unpack(metadata, bodyPosition, "<q")
    if bodyLength < 0 or bodyLength % 8 != 0 or headerType not in {1, 2, 3} or headerPosition is None:
        _invalidPayload()
    headerTable = _followOffset(metadata, headerPosition)
    if headerType == 1:
        if bodyLength != 0:
            _invalidPayload()
        return bodyLength, 0, False, True, False
    if headerType == 2:
        dataPosition = _tableField(metadata, headerTable, 1)
        if dataPosition is None:
            _invalidPayload()
        recordTable = _followOffset(metadata, dataPosition)
        _rows, compressed = _recordBatchMetadata(metadata, recordTable)
        return bodyLength, 0, compressed, False, False
    rows, compressed = _recordBatchMetadata(metadata, headerTable)
    return bodyLength, rows, compressed, False, True


def _containerBounds(payload: bytes) -> tuple[str, int, int]:
    if payload.startswith(_FILE_MAGIC):
        if len(payload) < 18 or payload[:8] != _FILE_MAGIC + b"\x00\x00" or not payload.endswith(_FILE_MAGIC):
            _invalidPayload()
        footerLength = _unpack(payload, len(payload) - 10, "<I")
        footerStart = len(payload) - 10 - footerLength
        if footerLength == 0 or footerStart < 8:
            _invalidPayload()
        return "file", 8, footerStart
    return "stream", 0, len(payload)


def _preflightIpc(payload: bytes, *, maxLogicalBytes: int | None = None) -> _IpcPreflight:
    containerKind, offset, end = _containerBounds(payload)
    rowCount = 0
    recordBatchCount = 0
    logicalBodyBytes = 0
    schemaCount = 0
    dataMessageCount = 0
    sawEnd = False
    while offset < end:
        prefix = _unpack(payload, offset, "<I")
        if prefix == _CONTINUATION_MARKER:
            metadataLength = _unpack(payload, offset + 4, "<I")
            metadataStart = offset + 8
        else:
            metadataLength = prefix
            metadataStart = offset + 4
        if metadataLength == 0:
            offset = metadataStart
            sawEnd = True
            break
        if metadataLength % 8 != 0 or metadataStart + metadataLength > end:
            _invalidPayload()
        metadataEnd = metadataStart + metadataLength
        bodyLength, messageRows, compressed, isSchema, isRecordBatch = _messageMetadata(
            payload[metadataStart:metadataEnd]
        )
        if compressed:
            raise ContinuationError("CONTINUATION_COMPRESSION_UNSUPPORTED")
        bodyEnd = metadataEnd + bodyLength
        if bodyEnd > end:
            _invalidPayload()
        if isSchema:
            schemaCount += 1
            if schemaCount != 1 or dataMessageCount:
                _invalidPayload()
        else:
            dataMessageCount += 1
            logicalBodyBytes += bodyLength
            if isRecordBatch:
                rowCount += messageRows
                recordBatchCount += 1
            if maxLogicalBytes is not None and logicalBodyBytes > maxLogicalBytes:
                raise ContinuationError("CONTINUATION_LOGICAL_BYTE_BUDGET")
        offset = bodyEnd
    if not sawEnd or offset != end or schemaCount != 1 or recordBatchCount == 0:
        _invalidPayload()
    return _IpcPreflight(containerKind, rowCount, recordBatchCount, logicalBodyBytes)


def arrowSchemaDigest(schema: Any) -> str:
    """Arrow schema IPC message의 SHA-256 digest를 계산한다.

    Args:
        schema: ``pyarrow.Schema`` compatible object.

    Returns:
        metadata를 포함한 serialized schema digest.

    Raises:
        ContinuationError: schema를 직렬화할 수 없을 때.

    Example:
        ``arrowSchemaDigest(table.schema)``.

    Guide:
        ContinuationPins.schemaDigest는 이 함수의 결과를 사용한다.

    SeeAlso:
        ``inspectArrowIpcPayload``.

    Requires:
        생산자와 소비자가 같은 Arrow logical schema를 공유한다.

    AIContext:
        선언 schema가 아니라 payload 안 실제 schema를 pin에 결박한다.
    """
    try:
        payload = schema.serialize().to_pybytes()
    except Exception:
        recordFailure(_log, "CONTINUATION_PAYLOAD_INVALID")
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID") from None
    return hashlib.sha256(payload).hexdigest()


def inspectArrowIpcPayload(payload: bytes, *, maxLogicalBytes: int | None = None) -> ArrowPayloadFacts:
    """Arrow IPC stream 또는 file bytes의 실제 facts를 읽는다.

    Capabilities:
        IPC container를 자동 판별하고 실제 rows, bytes, schema를 계산한다.

    Args:
        payload: 완전한 uncompressed Arrow IPC stream 또는 file bytes.
        maxLogicalBytes: decode 전 record body 최대 logical bytes.

    Returns:
        실제 row count, byte count, schema digest, container kind.

    Raises:
        ContinuationError: Arrow IPC가 아니거나 끝까지 소비되지 않을 때.

    Example:
        ``inspectArrowIpcPayload(ipcBytes)``.

    Guide:
        commit 전과 replay 때 모두 호출해 ledger metadata를 검증한다.

    When:
        owner page를 commit하거나 CAS page를 replay할 때 호출한다.

    How:
        stream reader를 먼저 시도하고 file reader로 안전하게 전환한다.

    SeeAlso:
        ``validateArrowIpcPayload``.

    Requires:
        외부 encoded byte budget 검사를 먼저 수행한다. 압축 IPC는 항상 거부한다.

    AIContext:
        owner가 주장한 rowCount를 신뢰하지 않고 IPC를 직접 센다.
    """
    if not isinstance(payload, bytes):
        raise TypeError("Arrow IPC payload는 bytes여야 합니다")
    if maxLogicalBytes is not None and (type(maxLogicalBytes) is not int or maxLogicalBytes <= 0):
        raise ValueError("maxLogicalBytes는 양의 int여야 합니다")
    preflight = _preflightIpc(payload, maxLogicalBytes=maxLogicalBytes)
    try:
        import pyarrow as pa

        source = pa.BufferReader(payload)
        if preflight.containerKind == "stream":
            reader = pa.ipc.open_stream(source)
            batches = list(reader)
            rowCount = sum(batch.num_rows for batch in batches)
            logicalByteCount = sum(batch.nbytes for batch in batches)
            if source.tell() != len(payload):
                raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
            schema = reader.schema
            containerKind = "stream"
        else:
            source = pa.BufferReader(payload)
            reader = pa.ipc.open_file(source)
            batches = [reader.get_batch(index) for index in range(reader.num_record_batches)]
            rowCount = sum(batch.num_rows for batch in batches)
            logicalByteCount = sum(batch.nbytes for batch in batches)
            schema = reader.schema
            containerKind = "file"
    except ContinuationError:
        raise
    except Exception:
        recordFailure(_log, "CONTINUATION_PAYLOAD_INVALID")
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID") from None
    if rowCount != preflight.rowCount or len(batches) != preflight.recordBatchCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_INVALID")
    if maxLogicalBytes is not None and logicalByteCount > maxLogicalBytes:
        raise ContinuationError("CONTINUATION_LOGICAL_BYTE_BUDGET")
    return ArrowPayloadFacts(
        rowCount=rowCount,
        byteCount=len(payload),
        logicalByteCount=logicalByteCount,
        schemaDigest=arrowSchemaDigest(schema),
        containerKind=containerKind,
    )


def validateArrowIpcPayload(
    payload: bytes,
    *,
    claimedRowCount: int,
    expectedSchemaDigest: str,
    maxPageBytes: int,
    maxLogicalBytes: int | None = None,
) -> ArrowPayloadFacts:
    """Arrow IPC 실제 facts를 page 주장과 budget에 대조한다.

    Capabilities:
        parse 전 byte bound와 parse 후 row 및 schema pin을 함께 강제한다.

    Args:
        payload: Arrow IPC bytes.
        claimedRowCount: owner 또는 ledger가 기록한 row count.
        expectedSchemaDigest: pinned Arrow schema digest.
        maxPageBytes: encoded payload 최대 bytes.
        maxLogicalBytes: decode 전과 후의 logical memory 최대 bytes.

    Returns:
        검증을 통과한 실제 payload facts.

    Raises:
        ContinuationError: byte, row, schema, IPC 검증이 실패했을 때.

    Example:
        ``validateArrowIpcPayload(payload, claimedRowCount=3, expectedSchemaDigest=digest, maxPageBytes=4096)``.

    Guide:
        row budget은 store가 별도로 검사하고 byte budget은 parse 전에 검사한다.

    When:
        continuation page를 CAS에 넣기 전과 CAS에서 읽은 직후 호출한다.

    How:
        ``inspectArrowIpcPayload`` 결과를 owner 주장과 exact digest로 비교한다.

    SeeAlso:
        ``inspectArrowIpcPayload``.

    Requires:
        expectedSchemaDigest는 ``arrowSchemaDigest``로 계산한다.

    AIContext:
        이 함수가 owner payload codec의 production 검증 seam이다.
    """
    if type(maxPageBytes) is not int or maxPageBytes <= 0:
        raise ValueError("maxPageBytes는 양의 int여야 합니다")
    if type(claimedRowCount) is not int or claimedRowCount < 0:
        raise ValueError("claimedRowCount는 음수가 아닌 int여야 합니다")
    logicalLimit = maxPageBytes if maxLogicalBytes is None else maxLogicalBytes
    if type(logicalLimit) is not int or logicalLimit <= 0:
        raise ValueError("maxLogicalBytes는 양의 int여야 합니다")
    if len(payload) > maxPageBytes:
        raise ContinuationError("CONTINUATION_BYTE_BUDGET")
    facts = inspectArrowIpcPayload(payload, maxLogicalBytes=logicalLimit)
    if facts.rowCount != claimedRowCount:
        raise ContinuationError("CONTINUATION_PAYLOAD_ROW_MISMATCH")
    if facts.schemaDigest != expectedSchemaDigest:
        raise ContinuationError("CONTINUATION_PAYLOAD_SCHEMA_MISMATCH")
    return facts
