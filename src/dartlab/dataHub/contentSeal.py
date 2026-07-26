"""Data Workbench 결과값을 결정적 content identity로 봉인한다."""

from __future__ import annotations

import dataclasses
import hashlib
import math
from collections.abc import Mapping, Sequence, Set
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import PurePath
from typing import Any

import polars as pl
import pyarrow as pa


class ContentSealError(TypeError):
    """결정적으로 직렬화할 수 없는 값이라 content seal을 만들 수 없을 때 발생한다."""


def _frame(tag: bytes, payload: bytes) -> bytes:
    """형과 길이를 포함해 hash tree의 경계를 모호하지 않게 만든다."""

    return tag + len(payload).to_bytes(8, "big") + payload


def _arrowBytes(value: pl.DataFrame | pa.Table | pa.RecordBatch) -> bytes:
    """Arrow 호환 표를 chunk 배치와 schema metadata에 무관한 IPC로 정규화한다."""

    if isinstance(value, pl.DataFrame):
        table = value.to_arrow()
    elif isinstance(value, pa.RecordBatch):
        table = pa.Table.from_batches([value])
    else:
        table = value
    table = table.replace_schema_metadata(None).combine_chunks()
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()


def _encoded(value: Any, *, seen: set[int]) -> bytes:
    """지원 값의 typed canonical tree를 만든다."""

    if value is None:
        return b"n"
    if type(value) is bool:
        return b"b1" if value else b"b0"
    if type(value) is int:
        return _frame(b"i", str(value).encode("ascii"))
    if type(value) is float:
        if math.isnan(value):
            payload = b"nan"
        elif math.isinf(value):
            payload = b"+inf" if value > 0 else b"-inf"
        else:
            payload = value.hex().encode("ascii")
        return _frame(b"f", payload)
    if isinstance(value, str):
        return _frame(b"s", value.encode("utf-8"))
    if isinstance(value, (bytes, bytearray, memoryview)):
        return _frame(b"y", bytes(value))
    if isinstance(value, Decimal):
        return _frame(b"d", str(value).encode("ascii"))
    if isinstance(value, (datetime, date, time)):
        return _frame(b"t", value.isoformat().encode("utf-8"))
    if isinstance(value, PurePath):
        return _frame(b"p", value.as_posix().encode("utf-8"))
    if isinstance(value, Enum):
        return _frame(
            b"e",
            _encoded(f"{type(value).__module__}.{type(value).__qualname__}", seen=seen)
            + _encoded(value.value, seen=seen),
        )
    if isinstance(value, (pl.DataFrame, pa.Table, pa.RecordBatch)):
        return _frame(b"a", _arrowBytes(value))

    identity = id(value)
    if identity in seen:
        raise ContentSealError("content tree에 cycle이 있습니다")

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        seen.add(identity)
        try:
            payload = _encoded(
                {field.name: getattr(value, field.name) for field in dataclasses.fields(value)},
                seen=seen,
            )
        finally:
            seen.remove(identity)
        return _frame(b"c", payload)

    if isinstance(value, Mapping):
        seen.add(identity)
        try:
            entries = [(_encoded(key, seen=seen), _encoded(item, seen=seen)) for key, item in value.items()]
        finally:
            seen.remove(identity)
        entries.sort(key=lambda pair: pair[0])
        return _frame(b"m", b"".join(_frame(b"k", key) + _frame(b"v", item) for key, item in entries))

    if isinstance(value, Set) and not isinstance(value, (str, bytes, bytearray)):
        seen.add(identity)
        try:
            entries = sorted(_encoded(item, seen=seen) for item in value)
        finally:
            seen.remove(identity)
        return _frame(b"u", b"".join(_frame(b"v", item) for item in entries))

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        seen.add(identity)
        try:
            payload = b"".join(_frame(b"v", _encoded(item, seen=seen)) for item in value)
        finally:
            seen.remove(identity)
        return _frame(b"q", payload)

    item = getattr(value, "item", None)
    if callable(item):
        try:
            scalar = item()
        except (TypeError, ValueError, OverflowError) as exc:
            raise ContentSealError(type(value).__name__) from exc
        if scalar is not value:
            return _frame(b"x", _encoded(scalar, seen=seen))
    raise ContentSealError(f"지원하지 않는 content type: {type(value).__module__}.{type(value).__qualname__}")


def contentHash(value: Any) -> str | None:
    """값과 schema를 결박한 SHA-256 identity를 반환한다.

    지원하지 않는 opaque owner object는 문자열로 약식 해시하지 않고 ``None``을 반환한다.
    """

    try:
        payload = _encoded(value, seen=set())
    except (ContentSealError, pa.ArrowException, pl.exceptions.PolarsError, OverflowError, ValueError):
        return None
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def executionReceipt(requestRef: str, contentHashRef: str | None) -> str:
    """요청 identity와 실제 반환값을 함께 결박한 실행 영수증을 만든다."""

    sealed = contentHashRef is not None
    payload = _encoded(
        {
            "requestRef": requestRef,
            "contentHash": contentHashRef if sealed else "UNSEALED",
        },
        seen=set(),
    )
    return f"data-execution:{hashlib.sha256(payload).hexdigest()}"


def resultSnapshotId(
    *,
    catalogSnapshotId: str,
    contractHash: str,
    partitions: Sequence[Any],
    universeSnapshotId: str | None,
) -> str | None:
    """반환 partition 전체를 결박한 실제 data snapshot ID를 만든다."""

    if not partitions or any(getattr(partition, "contentHash", None) is None for partition in partitions):
        return None
    payload = {
        "catalogSnapshotId": catalogSnapshotId,
        "contractHash": contractHash,
        "universeSnapshotId": universeSnapshotId,
        "partitions": [
            {
                "assetId": partition.asset.assetId,
                "assetVersionId": partition.asset.assetVersionId,
                "requestId": partition.requestId,
                "projectionKind": partition.projectionKind,
                "selector": partition.selector,
                "rowCount": partition.rowCount,
                "truncated": partition.truncated,
                "contentHash": partition.contentHash,
            }
            for partition in partitions
        ],
    }
    return f"data-content-snapshot:{hashlib.sha256(_encoded(payload, seen=set())).hexdigest()}"


__all__ = ["ContentSealError", "contentHash", "executionReceipt", "resultSnapshotId"]
