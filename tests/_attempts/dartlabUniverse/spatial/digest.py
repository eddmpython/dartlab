"""대규모 spatial primitive sequence용 length-prefixed SHA-256."""

from __future__ import annotations

import hashlib
import math
import re
import struct
import unicodedata
from dataclasses import fields, is_dataclass
from enum import Enum

import msgspec

_KIND_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")


def _update(digest, value) -> None:
    if value is None:
        digest.update(b"N")
    elif isinstance(value, Enum):
        digest.update(b"E")
        _update(digest, value.value)
    elif isinstance(value, bool):
        digest.update(b"B1" if value else b"B0")
    elif isinstance(value, int):
        payload = str(value).encode("ascii")
        digest.update(b"I" + len(payload).to_bytes(4, "big") + payload)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("spatial digest는 finite float만 허용함")
        digest.update(b"F" + struct.pack(">d", 0.0 if value == 0.0 else value))
    elif isinstance(value, str):
        payload = unicodedata.normalize("NFC", value).encode("utf-8")
        digest.update(b"S" + len(payload).to_bytes(8, "big") + payload)
    elif isinstance(value, (tuple, list)):
        digest.update(b"[" + len(value).to_bytes(8, "big"))
        for item in value:
            _update(digest, item)
        digest.update(b"]")
    elif is_dataclass(value):
        itemFields = fields(value)
        digest.update(b"D" + len(itemFields).to_bytes(4, "big"))
        for field in itemFields:
            _update(digest, field.name)
            _update(digest, getattr(value, field.name))
    else:
        raise TypeError(f"spatial digest unsupported type: {type(value).__name__}")


def spatialDigest(*values) -> str:
    """Nested primitive sequence를 모호성 없는 byte stream으로 hash한다."""
    digest = hashlib.sha256(b"dartlab-universe-spatial-v1\0")
    _update(digest, values)
    return digest.hexdigest()


def spatialId(kind: str, *values) -> str:
    normalized = kind.strip().casefold()
    if not _KIND_RE.fullmatch(normalized):
        raise ValueError("spatial ID kind가 잘못됨")
    return f"du:v1:{normalized}:{spatialDigest(normalized, values)}"


def spatialTextDigest(*values: str) -> str:
    """이미 정규화된 ID와 상수만 받는 hot-path length-prefixed digest다."""
    digest = hashlib.sha256(b"dartlab-universe-spatial-text-v1\0")
    for value in values:
        payload = value.encode("utf-8")
        digest.update(len(payload).to_bytes(4, "big"))
        digest.update(payload)
    return digest.hexdigest()


def spatialPackedDigest(domain: str, *values) -> str:
    """대규모 불변 구조를 versioned deterministic MessagePack으로 hash한다."""
    if not domain:
        raise ValueError("spatial packed digest domain이 비어 있음")
    payload = msgspec.msgpack.encode(("dartlab-universe-spatial-packed-v1", domain, values))
    return hashlib.sha256(payload).hexdigest()


class _CountingDigest:
    def __init__(self) -> None:
        self.digest = hashlib.sha256()
        self.byteSize = 0

    def update(self, payload: bytes) -> None:
        self.digest.update(payload)
        self.byteSize += len(payload)


def spatialDigestAndSize(*values) -> tuple[str, int]:
    """Spatial binary canonical stream의 digest와 정확한 encoded byte를 함께 계산한다."""
    target = _CountingDigest()
    target.update(b"dartlab-universe-spatial-v1\0")
    _update(target, values)
    return target.digest.hexdigest(), target.byteSize


def scenePayloadDigestAndSize(proxies, nodes, edges) -> tuple[str, int]:
    """Scene payload를 deterministic MessagePack으로 직렬화해 digest와 byte 수를 얻는다."""
    payload = msgspec.msgpack.encode(("dartlab-universe-scene-tile-v1", proxies, nodes, edges))
    return hashlib.sha256(payload).hexdigest(), len(payload)
