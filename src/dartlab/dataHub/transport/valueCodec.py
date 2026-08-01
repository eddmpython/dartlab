"""Native result tree의 deterministic typed wire codec과 byte accounting."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
from collections.abc import Mapping
from typing import Any

import polars as pl
import pyarrow as pa

from dartlab.dataHub.continuation import canonicalJsonBytes

_FORMAT = "data-hub-value-v1"


class ValueCodecError(ValueError):
    """지원하지 않는 값과 byte budget 위반을 구분하는 typed 오류."""

    def __init__(self, code: str):
        if code not in {"PROJECTION_VALUE_UNSUPPORTED", "PROJECTION_BYTE_BUDGET", "PROJECTION_VALUE_CORRUPT"}:
            raise ValueError("value codec code가 유효하지 않습니다")
        self.code = code
        super().__init__(code)


def _arrowBytes(frame: pl.DataFrame) -> bytes:
    table = frame.to_arrow().replace_schema_metadata(None).combine_chunks()
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()


def _tree(value: Any, *, seen: set[int], maximum: int | None) -> dict[str, Any]:
    if value is None:
        return {"type": "null"}
    if type(value) is bool:
        return {"type": "bool", "value": value}
    if type(value) is int:
        return {"type": "int", "value": value}
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueCodecError("PROJECTION_VALUE_UNSUPPORTED")
        return {"type": "float", "value": value}
    if type(value) is str:
        return {"type": "str", "value": value}
    if type(value) is bytes:
        if maximum is not None and len(value) > maximum:
            raise ValueCodecError("PROJECTION_BYTE_BUDGET")
        return {"type": "bytes", "value": base64.b64encode(value).decode("ascii")}
    if isinstance(value, pl.DataFrame):
        if maximum is not None and value.estimated_size() > maximum:
            raise ValueCodecError("PROJECTION_BYTE_BUDGET")
        payload = _arrowBytes(value)
        if maximum is not None and len(payload) > maximum:
            raise ValueCodecError("PROJECTION_BYTE_BUDGET")
        return {
            "type": "polars",
            "payload": base64.b64encode(payload).decode("ascii"),
            "payloadDigest": hashlib.sha256(payload).hexdigest(),
        }
    identity = id(value)
    if identity in seen:
        raise ValueCodecError("PROJECTION_VALUE_UNSUPPORTED")
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise ValueCodecError("PROJECTION_VALUE_UNSUPPORTED")
        seen.add(identity)
        try:
            entries = [[key, _tree(value[key], seen=seen, maximum=maximum)] for key in sorted(value)]
        finally:
            seen.remove(identity)
        return {"type": "mapping", "entries": entries}
    if isinstance(value, (list, tuple)):
        seen.add(identity)
        try:
            items = [_tree(item, seen=seen, maximum=maximum) for item in value]
        finally:
            seen.remove(identity)
        return {"type": "tuple" if isinstance(value, tuple) else "list", "items": items}
    raise ValueCodecError("PROJECTION_VALUE_UNSUPPORTED")


def encodeValueTree(value: Any, *, maxBytes: int | None = None) -> bytes:
    """지원 값 전체를 tagged canonical JSON bytes로 변환한다."""

    if maxBytes is not None and (type(maxBytes) is not int or maxBytes <= 0):
        raise ValueError("maxBytes는 양의 int여야 합니다")
    payload = canonicalJsonBytes({"format": _FORMAT, "value": _tree(value, seen=set(), maximum=maxBytes)})
    if maxBytes is not None and len(payload) > maxBytes:
        raise ValueCodecError("PROJECTION_BYTE_BUDGET")
    return payload


def encodedValueSize(value: Any) -> int:
    """Wire와 동일한 codec으로 native value의 실제 encoded byte 수를 센다."""

    if isinstance(value, pl.DataFrame):
        return len(_arrowBytes(value))
    return len(encodeValueTree(value))


def _decode(value: Any) -> Any:
    if not isinstance(value, dict) or type(value.get("type")) is not str:
        raise ValueCodecError("PROJECTION_VALUE_CORRUPT")
    kind = value["type"]
    if kind == "null" and set(value) == {"type"}:
        return None
    if kind in {"bool", "int", "float", "str"} and set(value) == {"type", "value"}:
        item = value["value"]
        expected = {"bool": bool, "int": int, "float": float, "str": str}[kind]
        if type(item) is not expected or kind == "float" and not math.isfinite(item):
            raise ValueCodecError("PROJECTION_VALUE_CORRUPT")
        return item
    if kind == "bytes" and set(value) == {"type", "value"} and type(value["value"]) is str:
        try:
            return base64.b64decode(value["value"], validate=True)
        except ValueError:
            raise ValueCodecError("PROJECTION_VALUE_CORRUPT") from None
    if kind == "polars" and set(value) == {"type", "payload", "payloadDigest"}:
        try:
            payload = base64.b64decode(value["payload"], validate=True)
        except (TypeError, ValueError):
            raise ValueCodecError("PROJECTION_VALUE_CORRUPT") from None
        if type(value["payloadDigest"]) is not str or not hmac.compare_digest(
            hashlib.sha256(payload).hexdigest(), value["payloadDigest"]
        ):
            raise ValueCodecError("PROJECTION_VALUE_CORRUPT")
        try:
            reader = pa.ipc.open_stream(pa.BufferReader(payload))
            table = reader.read_all()
        except Exception:
            raise ValueCodecError("PROJECTION_VALUE_CORRUPT") from None
        return pl.from_arrow(table)
    if kind == "mapping" and set(value) == {"type", "entries"} and isinstance(value["entries"], list):
        result = {}
        for entry in value["entries"]:
            if not isinstance(entry, list) or len(entry) != 2 or type(entry[0]) is not str or entry[0] in result:
                raise ValueCodecError("PROJECTION_VALUE_CORRUPT")
            result[entry[0]] = _decode(entry[1])
        return result
    if kind in {"list", "tuple"} and set(value) == {"type", "items"} and isinstance(value["items"], list):
        items = [_decode(item) for item in value["items"]]
        return tuple(items) if kind == "tuple" else items
    raise ValueCodecError("PROJECTION_VALUE_CORRUPT")


def decodeValueTree(payload: bytes) -> Any:
    """Canonical tagged JSON bytes를 원래 native value tree로 복원한다."""

    try:
        tree = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueCodecError("PROJECTION_VALUE_CORRUPT") from None
    if canonicalJsonBytes(tree) != payload or not isinstance(tree, dict) or set(tree) != {"format", "value"}:
        raise ValueCodecError("PROJECTION_VALUE_CORRUPT")
    if tree["format"] != _FORMAT:
        raise ValueCodecError("PROJECTION_VALUE_CORRUPT")
    return _decode(tree["value"])


__all__ = ["ValueCodecError", "decodeValueTree", "encodedValueSize", "encodeValueTree"]
