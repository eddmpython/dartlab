"""Pinned source object의 schema와 row descriptor를 bounded range로 읽는다."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import struct
import threading
import time
import zipfile
from collections.abc import Callable, Mapping
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Protocol
from urllib.parse import quote

import httpx
import numpy as np
import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.parquet as pq
import yaml

from ..canonical import canonicalDigest
from .models import CatalogResource

MIB = 1024 * 1024
DESCRIPTOR_SCHEMA_VERSION = "du-descriptor-v3"
_PARQUET_FOOTER_PROBE_BYTES = 256 * 1024
_DESCRIBED_FORMATS = frozenset(
    {
        "ARROW",
        "CSV",
        "HTML",
        "IMAGE",
        "JSON",
        "JSONL",
        "MARKDOWN",
        "NPZ",
        "PARQUET",
        "TEXT",
        "YAML",
    }
)


class DescriptorReadError(RuntimeError):
    """Descriptor source read가 terminal state로 닫혀야 할 때 사용한다."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code = code


@dataclass(frozen=True, slots=True)
class DescriptorPolicy:
    maxWholeObjectBytes: int = 32 * MIB
    maxRangeRequests: int = 256
    maxRangeBytes: int = 64 * MIB
    timeoutSeconds: float = 30.0
    maxTransientAttempts: int = 12
    maxRetryDelaySeconds: float = 310.0
    maxRequestsPerSecond: float = 12.0


@dataclass(frozen=True, slots=True)
class RangeChunk:
    start: int
    endExclusive: int
    payload: bytes
    responseDigest: str


class RangeReader(Protocol):
    size: int

    def read(self, start: int, endExclusive: int) -> RangeChunk: ...


@dataclass(frozen=True, slots=True)
class ResourceDescriptor:
    descriptorId: str
    schemaVersion: str
    resourceVersionId: str
    sourceRevision: str
    formatKind: str
    status: str
    schemaFingerprint: str | None
    rowCount: int | None
    rowCountUnavailableReason: str | None
    metadata: tuple[tuple[str, str], ...]
    magicHex: str | None
    rangeRequestCount: int
    rangeBytesRead: int
    responseDigest: str
    errorCode: str | None
    digest: str


class LocalRangeReader:
    """Fixture와 local authority를 같은 range 계약으로 읽는다."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        if not self.path.is_file() or self.path.is_symlink():
            raise FileNotFoundError(self.path)
        self.size = self.path.stat().st_size

    def read(self, start: int, endExclusive: int) -> RangeChunk:
        if start < 0 or endExclusive < start or endExclusive > self.size:
            raise DescriptorReadError("INVALID_RANGE", f"{start}:{endExclusive}/{self.size}")
        with self.path.open("rb") as stream:
            stream.seek(start)
            payload = stream.read(endExclusive - start)
        if len(payload) != endExclusive - start:
            raise DescriptorReadError("SHORT_RANGE_RESPONSE")
        return RangeChunk(start, endExclusive, payload, hashlib.sha256(payload).hexdigest())


class HfPinnedRangeReader:
    """HF dataset의 exact revision URL만 허용하는 HTTP Range reader."""

    def __init__(
        self,
        *,
        repoId: str,
        revision: str,
        path: str,
        size: int,
        token: str | None,
        timeoutSeconds: float = 30.0,
        clientFactory: Callable[..., httpx.Client] = httpx.Client,
        client: httpx.Client | None = None,
        policy: DescriptorPolicy | None = None,
        rateLimiter: "_AdaptiveRateLimiter | None" = None,
    ):
        if not repoId or not revision or not path or size < 0:
            raise ValueError("HF range reader에는 repo, revision, path, size가 필요함")
        if not re.fullmatch(r"[0-9a-f]{40,64}", revision):
            raise ValueError("HF range reader revision은 exact commit digest여야 함")
        purePath = PurePosixPath(path)
        if purePath.is_absolute() or ".." in purePath.parts:
            raise ValueError("HF range reader path는 안전한 POSIX 상대경로여야 함")
        self.size = size
        self.url = (
            f"https://huggingface.co/datasets/{quote(repoId, safe='/')}/resolve/"
            f"{quote(revision, safe='')}/{quote(path, safe='/')}"
        )
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._ownsClient = client is None
        self._client = client or clientFactory(headers=headers, timeout=timeoutSeconds, follow_redirects=True)
        self._authorization = headers.get("Authorization")
        self.policy = policy or DescriptorPolicy(timeoutSeconds=timeoutSeconds)
        self.rateLimiter = rateLimiter

    def read(self, start: int, endExclusive: int) -> RangeChunk:
        if start < 0 or endExclusive < start or endExclusive > self.size:
            raise DescriptorReadError("INVALID_RANGE")
        headers = {"Range": f"bytes={start}-{endExclusive - 1}"}
        if self._authorization:
            headers["Authorization"] = self._authorization
        response = None
        lastError = ""
        for attempt in range(1, self.policy.maxTransientAttempts + 1):
            if self.rateLimiter is not None:
                self.rateLimiter.beforeRequest()
            try:
                response = self._client.get(self.url, headers=headers)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                lastError = type(exc).__name__
                if attempt >= self.policy.maxTransientAttempts:
                    raise DescriptorReadError("TIMEOUT", lastError) from exc
                self._retryDelay(attempt, None, None)
                continue
            if response.status_code == 429 or 500 <= response.status_code <= 599:
                lastError = f"HTTP_{response.status_code}"
                if attempt >= self.policy.maxTransientAttempts:
                    code = "RATE_LIMITED" if response.status_code == 429 else "SOURCE_HTTP_ERROR"
                    response.close()
                    raise DescriptorReadError(code, lastError)
                retryAfter = response.headers.get("retry-after")
                rateLimit = response.headers.get("ratelimit")
                response.close()
                self._retryDelay(
                    attempt,
                    retryAfter,
                    rateLimit,
                )
                continue
            break
        if response is None:
            raise DescriptorReadError("SOURCE_HTTP_ERROR", lastError or "NO_RESPONSE")
        try:
            if response.status_code in {401, 403}:
                raise DescriptorReadError("ACCESS_DENIED", f"HTTP_{response.status_code}")
            if response.status_code == 404:
                raise DescriptorReadError("NOT_FOUND", "HTTP_404")
            if response.status_code == 200 and start == 0 and endExclusive == self.size:
                payload = response.content
            elif response.status_code == 206:
                contentRange = response.headers.get("content-range", "")
                expected = f"bytes {start}-{endExclusive - 1}/{self.size}"
                if contentRange.lower() != expected.lower():
                    raise DescriptorReadError("CONTENT_RANGE_MISMATCH", contentRange)
                payload = response.content
            elif response.status_code == 200:
                raise DescriptorReadError("RANGE_UNSUPPORTED", "server returned full object")
            else:
                raise DescriptorReadError("SOURCE_HTTP_ERROR", f"HTTP_{response.status_code}")
        finally:
            response.close()
        if len(payload) != endExclusive - start:
            raise DescriptorReadError("SHORT_RANGE_RESPONSE")
        return RangeChunk(start, endExclusive, payload, hashlib.sha256(payload).hexdigest())

    def _retryDelay(self, attempt: int, retryAfter: str | None, rateLimit: str | None) -> None:
        try:
            declaredDelay = float(retryAfter) if retryAfter is not None else 0.0
        except ValueError:
            declaredDelay = 0.0
        if rateLimit:
            resetMatch = re.search(r"(?:^|;)t=(\d+)", rateLimit)
            remainingMatch = re.search(r"(?:^|;)r=(\d+)", rateLimit)
            if resetMatch and remainingMatch and int(remainingMatch.group(1)) == 0:
                declaredDelay = max(declaredDelay, float(resetMatch.group(1)) + 1.0)
        jitterSeed = hashlib.sha256(f"{self.url}:{attempt}".encode("utf-8")).digest()[0] / 2550.0
        delay = min(
            self.policy.maxRetryDelaySeconds,
            max(declaredDelay, 0.5 * (2 ** (attempt - 1)) + jitterSeed),
        )
        if self.rateLimiter is not None:
            self.rateLimiter.penalize(delay)
        _boundedSleep(delay)

    def close(self) -> None:
        if self._ownsClient:
            self._client.close()


class _AdaptiveRateLimiter:
    def __init__(self, maxRequestsPerSecond: float):
        if maxRequestsPerSecond <= 0:
            raise ValueError("maxRequestsPerSecond는 양수여야 함")
        self.interval = 1.0 / maxRequestsPerSecond
        self.nextRequestAt = 0.0
        self.lock = threading.Lock()

    def beforeRequest(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                scheduled = max(now, self.nextRequestAt)
                delay = scheduled - now
                if delay <= 0:
                    self.nextRequestAt = now + self.interval
                    return
            _boundedSleep(min(delay, 60.0))

    def penalize(self, delay: float) -> None:
        with self.lock:
            self.nextRequestAt = max(self.nextRequestAt, time.monotonic() + delay)


def _boundedSleep(delay: float) -> None:
    remaining = max(0.0, delay)
    while remaining > 0:
        started = time.monotonic()
        time.sleep(min(remaining, 60.0))
        remaining -= time.monotonic() - started


class HfRangeReaderFactory:
    """Full crawl 동안 connection pool을 공유하고 token은 receipt에서 제외한다."""

    def __init__(
        self,
        *,
        token: str | None,
        allowedRepoIds: frozenset[str],
        policy: DescriptorPolicy | None = None,
    ):
        if not allowedRepoIds or any(not repoId for repoId in allowedRepoIds):
            raise ValueError("HF descriptor factory에는 configured repo allowlist가 필요함")
        self.policy = policy or DescriptorPolicy()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.client = httpx.Client(
            headers=headers,
            timeout=self.policy.timeoutSeconds,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=32, max_keepalive_connections=16),
        )
        self.token = token
        self.allowedRepoIds = allowedRepoIds
        self.rateLimiter = _AdaptiveRateLimiter(self.policy.maxRequestsPerSecond)

    def __call__(self, resource: CatalogResource) -> HfPinnedRangeReader:
        locator = dict(resource.locator)
        if resource.byteSize is None:
            raise DescriptorReadError("SOURCE_SIZE_MISSING")
        repoId = locator.get("repo", "")
        if repoId not in self.allowedRepoIds:
            raise DescriptorReadError("REPOSITORY_NOT_ALLOWLISTED")
        return HfPinnedRangeReader(
            repoId=repoId,
            revision=resource.sourceRevision,
            path=locator.get("path", ""),
            size=resource.byteSize,
            token=self.token,
            timeoutSeconds=self.policy.timeoutSeconds,
            client=self.client,
            policy=self.policy,
            rateLimiter=self.rateLimiter,
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "HfRangeReaderFactory":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


class _BudgetedRangeFile(io.RawIOBase):
    def __init__(self, reader: RangeReader, policy: DescriptorPolicy):
        self.reader = reader
        self.policy = policy
        self.position = 0
        self.chunks: list[RangeChunk] = []

    @property
    def requestCount(self) -> int:
        return len(self.chunks)

    @property
    def bytesRead(self) -> int:
        return sum(len(chunk.payload) for chunk in self.chunks)

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            position = offset
        elif whence == io.SEEK_CUR:
            position = self.position + offset
        elif whence == io.SEEK_END:
            position = self.reader.size + offset
        else:
            raise ValueError(f"지원하지 않는 whence: {whence}")
        if position < 0 or position > self.reader.size:
            raise OSError("seek out of bounds")
        self.position = position
        return position

    def readinto(self, buffer: bytearray | memoryview) -> int:
        payload = self.read(len(buffer))
        buffer[: len(payload)] = payload
        return len(payload)

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self.reader.size - self.position
        end = min(self.reader.size, self.position + size)
        if end <= self.position:
            return b""
        if self.requestCount + 1 > self.policy.maxRangeRequests:
            raise DescriptorReadError("RANGE_REQUEST_BUDGET_EXCEEDED")
        if self.bytesRead + end - self.position > self.policy.maxRangeBytes:
            raise DescriptorReadError("RANGE_BYTE_BUDGET_EXCEEDED")
        chunk = self.reader.read(self.position, end)
        self.chunks.append(chunk)
        self.position = end
        return chunk.payload


def _whole(stream: _BudgetedRangeFile) -> bytes:
    if stream.reader.size > stream.policy.maxWholeObjectBytes:
        raise DescriptorReadError("DESCRIPTOR_BLOCKED_RANGE", "whole object exceeds bounded fallback")
    stream.seek(0)
    return stream.read(stream.reader.size)


def _jsonType(value: Any) -> Any:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return {"array": sorted({_jsonSchemaToken(item) for item in value})}
    if isinstance(value, Mapping):
        return {"object": {str(key): _jsonType(item) for key, item in sorted(value.items())}}
    return type(value).__name__


def _jsonSchemaToken(value: Any) -> str:
    return json.dumps(_jsonType(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _tabularJsonSchema(rows: list[Any]) -> object:
    fields: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            return {"items": sorted({_jsonSchemaToken(item) for item in rows})}
        for key, value in row.items():
            fields.setdefault(str(key), set()).add(_jsonSchemaToken(value))
    return {"fields": {key: sorted(values) for key, values in sorted(fields.items())}}


def _describeParquet(stream: _BudgetedRangeFile) -> tuple[object, int, str | None, dict[str, str]]:
    size = stream.reader.size
    if size < 12:
        raise DescriptorReadError("INVALID_PARQUET_FOOTER", "file is smaller than parquet envelope")

    probeStart = max(0, size - _PARQUET_FOOTER_PROBE_BYTES)
    stream.seek(probeStart)
    footerPayload = stream.read(size - probeStart)
    if footerPayload[-4:] != b"PAR1":
        raise DescriptorReadError("INVALID_PARQUET_FOOTER", "terminal magic mismatch")
    footerLength = int.from_bytes(footerPayload[-8:-4], "little")
    if footerLength <= 0 or footerLength > size - 12:
        raise DescriptorReadError("INVALID_PARQUET_FOOTER", "metadata length is outside file envelope")

    footerStart = size - 8 - footerLength
    if footerStart < probeStart:
        stream.seek(footerStart)
        footerPayload = stream.read(size - footerStart)
    metadataBytes = footerPayload[-8 - footerLength : -8]
    syntheticEnvelope = b"PAR1" + metadataBytes + footerLength.to_bytes(4, "little") + b"PAR1"
    with pa.BufferReader(syntheticEnvelope) as buffer:
        metadata = pq.read_metadata(buffer)
    schema = metadata.schema.to_arrow_schema()
    details = {
        "columnCount": str(metadata.num_columns),
        "rowGroupCount": str(metadata.num_row_groups),
        "createdBy": str(metadata.created_by or ""),
        "descriptorRead": "footer-range",
    }
    return str(schema), metadata.num_rows, None, details


def _describeArrow(stream: _BudgetedRangeFile) -> tuple[object, int, str | None, dict[str, str]]:
    try:
        reader = ipc.open_file(pa.PythonFile(stream, mode="r"))
        rows = sum(reader.get_batch(index).num_rows for index in range(reader.num_record_batches))
        return str(reader.schema), rows, None, {"container": "file", "batchCount": str(reader.num_record_batches)}
    except pa.ArrowInvalid:
        payload = _whole(stream)
        buffer = pa.py_buffer(payload)
        reader = ipc.open_stream(buffer)
        batches = tuple(reader)
        return (
            str(reader.schema),
            sum(batch.num_rows for batch in batches),
            None,
            {
                "container": "stream",
                "batchCount": str(len(batches)),
            },
        )


def _describeJson(stream: _BudgetedRangeFile) -> tuple[object, int | None, str | None, dict[str, str]]:
    value = json.loads(_whole(stream).decode("utf-8"))
    if isinstance(value, list):
        return _tabularJsonSchema(value), len(value), None, {"topLevel": "array"}
    return _jsonType(value), None, "NON_TABULAR_DOCUMENT", {"topLevel": type(value).__name__}


def _describeJsonl(stream: _BudgetedRangeFile) -> tuple[object, int, str | None, dict[str, str]]:
    rows = [json.loads(line) for line in _whole(stream).decode("utf-8").splitlines() if line.strip()]
    return _tabularJsonSchema(rows), len(rows), None, {"container": "jsonl"}


def _describeCsv(stream: _BudgetedRangeFile) -> tuple[object, int, str | None, dict[str, str]]:
    text = _whole(stream).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    schema = {"fields": tuple(reader.fieldnames or ()), "types": "string-unparsed"}
    return schema, len(rows), None, {"dialect": type(reader.dialect).__name__}


def _readNpyHeader(member: Any) -> tuple[tuple[int, ...], bool, np.dtype[Any]]:
    version = np.lib.format.read_magic(member)
    if version == (1, 0):
        return np.lib.format.read_array_header_1_0(member)
    if version in {(2, 0), (3, 0)}:
        return np.lib.format.read_array_header_2_0(member)
    raise ValueError(f"지원하지 않는 NPY version: {version}")


def _describeNpz(stream: _BudgetedRangeFile) -> tuple[object, int | None, str | None, dict[str, str]]:
    arrays = {}
    leading = set()
    with zipfile.ZipFile(stream) as archive:
        for name in sorted(archive.namelist()):
            if not name.endswith(".npy"):
                continue
            with archive.open(name) as member:
                shape, fortranOrder, dtype = _readNpyHeader(member)
            arrays[name[:-4]] = {
                "dtype": dtype.str,
                "shape": shape,
                "fortranOrder": fortranOrder,
            }
            if shape:
                leading.add(shape[0])
    if len(leading) == 1:
        rowCount = next(iter(leading))
        reason = None
    else:
        rowCount = None
        reason = "HETEROGENEOUS_ARRAY_SHAPES" if leading else "NO_ROW_AXIS"
    return arrays, rowCount, reason, {"arrayCount": str(len(arrays))}


def _describeDocument(
    stream: _BudgetedRangeFile,
    formatKind: str,
) -> tuple[object, int | None, str | None, dict[str, str]]:
    text = _whole(stream).decode("utf-8")
    if formatKind == "YAML":
        value = yaml.safe_load(text)
        if isinstance(value, list):
            return _tabularJsonSchema(value), len(value), None, {"document": "yaml"}
        return _jsonType(value), None, "NON_TABULAR_DOCUMENT", {"document": "yaml"}
    headings = tuple(re.findall(r"(?m)^#{1,6}\s+(.+?)\s*$", text)) if formatKind == "MARKDOWN" else ()
    schema = {
        "document": formatKind.lower(),
        "headingCount": len(headings),
        "lineCount": len(text.splitlines()),
    }
    return schema, None, "NON_TABULAR_DOCUMENT", {"encoding": "utf-8"}


def _jpegDimensions(payload: bytes) -> tuple[int, int] | None:
    position = 2
    while position + 9 <= len(payload):
        if payload[position] != 0xFF:
            position += 1
            continue
        marker = payload[position + 1]
        position += 2
        if marker in {0xD8, 0xD9}:
            continue
        if position + 2 > len(payload):
            return None
        length = int.from_bytes(payload[position : position + 2], "big")
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if position + 7 > len(payload):
                return None
            return (
                int.from_bytes(payload[position + 5 : position + 7], "big"),
                int.from_bytes(payload[position + 3 : position + 5], "big"),
            )
        position += max(2, length)
    return None


def _describeImage(stream: _BudgetedRangeFile) -> tuple[object, None, str, dict[str, str]]:
    headerBytes = min(stream.reader.size, 256 * 1024)
    stream.seek(0)
    payload = stream.read(headerBytes)
    width = height = None
    kind = "UNKNOWN"
    if payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 24:
        kind = "PNG"
        width, height = struct.unpack(">II", payload[16:24])
    elif payload.startswith((b"GIF87a", b"GIF89a")) and len(payload) >= 10:
        kind = "GIF"
        width, height = struct.unpack("<HH", payload[6:10])
    elif payload.startswith(b"\xff\xd8"):
        kind = "JPEG"
        dimensions = _jpegDimensions(payload)
        if dimensions:
            width, height = dimensions
    elif payload.startswith(b"RIFF") and payload[8:12] == b"WEBP" and len(payload) >= 30:
        kind = "WEBP"
        if payload[12:16] == b"VP8X":
            width = 1 + int.from_bytes(payload[24:27], "little")
            height = 1 + int.from_bytes(payload[27:30], "little")
        elif payload[12:16] == b"VP8 " and payload[23:26] == b"\x9d\x01\x2a":
            width = int.from_bytes(payload[26:28], "little") & 0x3FFF
            height = int.from_bytes(payload[28:30], "little") & 0x3FFF
        elif payload[12:16] == b"VP8L" and payload[20] == 0x2F:
            dimensionBits = int.from_bytes(payload[21:25], "little")
            width = 1 + (dimensionBits & 0x3FFF)
            height = 1 + ((dimensionBits >> 14) & 0x3FFF)
    elif b"<svg" in payload[:4096].lower():
        kind = "SVG"
        text = payload.decode("utf-8", errors="replace")
        widthMatch = re.search(r"\bwidth=['\"]([^'\"]+)", text)
        heightMatch = re.search(r"\bheight=['\"]([^'\"]+)", text)
        return (
            {
                "format": kind,
                "width": widthMatch.group(1) if widthMatch else None,
                "height": heightMatch.group(1) if heightMatch else None,
            },
            None,
            "NON_TABULAR_MEDIA",
            {"format": kind},
        )
    if width is None or height is None:
        return (
            {"format": kind, "width": None, "height": None, "headerBytes": headerBytes},
            None,
            "NON_TABULAR_MEDIA",
            {"format": kind, "dimensionStatus": "UNAVAILABLE_IN_HEADER"},
        )
    return {"format": kind, "width": width, "height": height}, None, "NON_TABULAR_MEDIA", {"format": kind}


def descriptorFormatKind(resource: CatalogResource) -> str:
    declared = dict(resource.attributes).get("formatKind")
    if declared:
        return declared if declared in _DESCRIBED_FORMATS else "UNSUPPORTED"
    path = dict(resource.locator).get("path", "").lower()
    suffix = Path(path).suffix
    return {
        ".arrow": "ARROW",
        ".csv": "CSV",
        ".gif": "IMAGE",
        ".html": "HTML",
        ".jpeg": "IMAGE",
        ".jpg": "IMAGE",
        ".json": "JSON",
        ".jsonl": "JSONL",
        ".md": "MARKDOWN",
        ".npz": "NPZ",
        ".parquet": "PARQUET",
        ".png": "IMAGE",
        ".svg": "IMAGE",
        ".txt": "TEXT",
        ".webp": "IMAGE",
        ".yaml": "YAML",
        ".yml": "YAML",
    }.get(suffix, "UNSUPPORTED")


def _responseDigest(chunks: list[RangeChunk]) -> str:
    return canonicalDigest(tuple((item.start, item.endExclusive, item.responseDigest) for item in chunks))


def crawlDescriptor(
    resource: CatalogResource,
    reader: RangeReader,
    *,
    formatKind: str | None = None,
    policy: DescriptorPolicy | None = None,
) -> ResourceDescriptor:
    """한 resource의 C2 descriptor를 terminal state로 닫는다.

    Range가 가능한 columnar container는 필요한 byte만 읽는다. 전체 byte가 필요한
    format은 32 MiB 이하에서만 bounded fallback을 허용한다.
    """
    activePolicy = policy or DescriptorPolicy()
    kind = formatKind or descriptorFormatKind(resource)
    stream = _BudgetedRangeFile(reader, activePolicy)
    descriptorId = canonicalDigest((resource.resourceVersionId, kind, DESCRIPTOR_SCHEMA_VERSION))
    status = "DESCRIBED"
    schemaFingerprint = None
    rowCount = None
    rowReason = None
    metadata: dict[str, str] = {}
    errorCode = None
    magicHex = None
    try:
        if kind not in _DESCRIBED_FORMATS:
            magic = stream.read(min(32, reader.size))
            magicHex = magic.hex()
            status = "UNSUPPORTED_FORMAT"
            rowReason = "UNSUPPORTED_FORMAT"
            metadata = {
                "declaredFormatKind": dict(resource.attributes).get("formatKind", kind),
                "reason": "NO_SAFE_DESCRIPTOR_PARSER",
                "sourceMeaning": resource.resourceKind,
            }
        else:
            parser = {
                "ARROW": _describeArrow,
                "CSV": _describeCsv,
                "IMAGE": _describeImage,
                "JSON": _describeJson,
                "JSONL": _describeJsonl,
                "NPZ": _describeNpz,
                "PARQUET": _describeParquet,
            }.get(kind)
            if parser is None:
                schema, rowCount, rowReason, metadata = _describeDocument(stream, kind)
            else:
                schema, rowCount, rowReason, metadata = parser(stream)
            schemaFingerprint = canonicalDigest(schema)
    except DescriptorReadError as exc:
        errorCode = exc.code
        if exc.code == "ACCESS_DENIED":
            status = "ACCESS_DENIED"
        elif exc.code in {"DESCRIPTOR_BLOCKED_RANGE", "RANGE_UNSUPPORTED"}:
            status = "DESCRIPTOR_BLOCKED_RANGE"
        else:
            status = "PARSE_ERROR"
        rowReason = exc.code
        metadata = {"detail": str(exc)}
    except Exception as exc:
        status = "PARSE_ERROR"
        errorCode = type(exc).__name__
        rowReason = "PARSE_ERROR"
        metadata = {"detail": str(exc)[:500]}
    base = ResourceDescriptor(
        descriptorId=descriptorId,
        schemaVersion=DESCRIPTOR_SCHEMA_VERSION,
        resourceVersionId=resource.resourceVersionId,
        sourceRevision=resource.sourceRevision,
        formatKind=kind,
        status=status,
        schemaFingerprint=schemaFingerprint,
        rowCount=rowCount,
        rowCountUnavailableReason=rowReason,
        metadata=tuple(sorted((str(key), str(value)) for key, value in metadata.items())),
        magicHex=magicHex,
        rangeRequestCount=stream.requestCount,
        rangeBytesRead=stream.bytesRead,
        responseDigest=_responseDigest(stream.chunks),
        errorCode=errorCode,
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))


def crawlCatalogDescriptors(
    resources: tuple[CatalogResource, ...],
    readerFactory: Callable[[CatalogResource], RangeReader],
    *,
    policy: DescriptorPolicy | None = None,
    maxWorkers: int = 8,
    resumeDescriptors: tuple[ResourceDescriptor, ...] = (),
    onDescriptor: Callable[[ResourceDescriptor], None] | None = None,
) -> tuple[ResourceDescriptor, ...]:
    """모든 HF file을 결정론 순서로 병렬 crawl하고 항목별 terminal receipt를 만든다."""
    if maxWorkers < 1:
        raise ValueError("maxWorkers는 1 이상이어야 함")
    activePolicy = policy or DescriptorPolicy()
    candidates = tuple(
        sorted((item for item in resources if item.resourceKind == "HF_FILE"), key=lambda item: item.resourceVersionId)
    )
    candidateByVersion = {item.resourceVersionId: item for item in candidates}
    resumed = {item.resourceVersionId: item for item in resumeDescriptors}
    if len(resumed) != len(resumeDescriptors):
        raise ValueError("resume descriptor duplicate")
    for resourceVersionId, descriptor in resumed.items():
        resource = candidateByVersion.get(resourceVersionId)
        if resource is None:
            raise ValueError(f"resume descriptor catalog mismatch: {resourceVersionId}")
        expectedDigest = canonicalDigest(replace(descriptor, digest=""))
        if (
            descriptor.schemaVersion != DESCRIPTOR_SCHEMA_VERSION
            or descriptor.sourceRevision != resource.sourceRevision
            or descriptor.formatKind != descriptorFormatKind(resource)
            or descriptor.digest != expectedDigest
        ):
            raise ValueError(f"stale or corrupt resume descriptor: {resourceVersionId}")
    todo = tuple(item for item in candidates if item.resourceVersionId not in resumed)

    def crawlOne(resource: CatalogResource) -> ResourceDescriptor:
        try:
            reader = readerFactory(resource)
        except DescriptorReadError as exc:
            errorCode = exc.code
            errorDetail = str(exc)

            class FailedReader:
                size = resource.byteSize or 0

                def read(self, _start: int, _endExclusive: int) -> RangeChunk:
                    raise DescriptorReadError(errorCode, errorDetail)

            return crawlDescriptor(resource, FailedReader(), policy=activePolicy)
        try:
            return crawlDescriptor(resource, reader, policy=activePolicy)
        finally:
            close = getattr(reader, "close", None)
            if callable(close):
                close()

    workerCount = min(maxWorkers, max(1, len(todo)))
    crawled = []
    with ThreadPoolExecutor(max_workers=workerCount, thread_name_prefix="universe-descriptor") as executor:
        iterator = iter(todo)
        pending = {
            executor.submit(crawlOne, resource)
            for resource in tuple(next(iterator, None) for _ in range(workerCount * 2))
            if resource is not None
        }
        while pending:
            completed, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                descriptor = future.result()
                crawled.append(descriptor)
                if onDescriptor is not None:
                    onDescriptor(descriptor)
                resource = next(iterator, None)
                if resource is not None:
                    pending.add(executor.submit(crawlOne, resource))
    descriptors = (*resumed.values(), *crawled)
    if len(descriptors) != len(candidates):
        raise RuntimeError("descriptor crawl cardinality mismatch")
    return tuple(sorted(descriptors, key=lambda item: item.resourceVersionId))
