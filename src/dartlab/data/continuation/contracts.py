"""Data Workbench continuation control-plane contracts."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

_ERROR_MESSAGES = {
    "CONTINUATION_INVALID": "continuation token이 유효하지 않습니다",
    "CONTINUATION_EXPIRED": "continuation token이 만료되었습니다",
    "CONTINUATION_SOURCE_STALE": "continuation source pin이 현재 실행과 다릅니다",
    "CONTINUATION_QUERY_STALE": "continuation query pin이 현재 실행과 다릅니다",
    "CONTINUATION_CONTRACT_STALE": "continuation contract pin이 현재 실행과 다릅니다",
    "CONTINUATION_SCHEMA_STALE": "continuation schema pin이 현재 실행과 다릅니다",
    "CONTINUATION_BUSY": "continuation owner 완료를 기다리는 시간이 초과되었습니다",
    "CONTINUATION_TIMEOUT": "continuation page 실행 시간이 query budget을 초과했습니다",
    "CONTINUATION_CORRUPT": "continuation 저장 상태의 무결성 검증에 실패했습니다",
    "CONTINUATION_ROW_BUDGET": "continuation page row budget을 초과했습니다",
    "CONTINUATION_BYTE_BUDGET": "continuation page byte budget을 초과했습니다",
    "CONTINUATION_STATE_BUDGET": "continuation private state budget을 초과했습니다",
    "CONTINUATION_CLAIM_LOST": "continuation owner claim을 잃었습니다",
    "CONTINUATION_PAYLOAD_INVALID": "continuation Arrow IPC payload가 유효하지 않습니다",
    "CONTINUATION_PAYLOAD_ROW_MISMATCH": "continuation Arrow IPC row count가 다릅니다",
    "CONTINUATION_PAYLOAD_SCHEMA_MISMATCH": "continuation Arrow IPC schema가 다릅니다",
    "CONTINUATION_OWNER_FAILED": "continuation page owner 실행에 실패했습니다",
    "CONTINUATION_GC_FAILED": "continuation 만료 데이터 정리에 실패했습니다",
    "CONTINUATION_CLOCK_INVALID": "continuation clock 값이 유효하지 않습니다",
    "CONTINUATION_TOKEN_COLLISION": "continuation token 발급 충돌 한도를 초과했습니다",
    "CONTINUATION_SCHEMA_VERSION_UNSUPPORTED": "continuation ledger schema version을 지원하지 않습니다",
    "CONTINUATION_SECURITY_FAILED": "continuation private storage 보안 설정에 실패했습니다",
    "CONTINUATION_COMPRESSION_UNSUPPORTED": "continuation Arrow IPC compression을 지원하지 않습니다",
    "CONTINUATION_LOGICAL_BYTE_BUDGET": "continuation Arrow logical byte budget을 초과했습니다",
}


def _finitePositiveNumber(value: Any) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        number = float(value)
    except (OverflowError, TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


class ContinuationError(RuntimeError):
    """비밀값을 포함하지 않는 machine-readable continuation 오류.

    Args:
        code: ``CONTINUATION_*`` 형식의 안정 오류 코드.

    Returns:
        안전한 고정 메시지와 ``code``를 가진 예외.

    Raises:
        ValueError: 등록되지 않은 오류 코드를 받았을 때.

    Example:
        ``raise ContinuationError("CONTINUATION_EXPIRED")``.

    Guide:
        상위 query 축은 ``code``만 구조화된 gap으로 옮긴다.

    SeeAlso:
        ``ContinuationStore.loadContext``.

    Requires:
        token, query, cursor, owner 예외 원문을 메시지에 넣지 않는다.

    AIContext:
        고정 메시지는 bearer secret이 traceback과 gap으로 번지는 것을 막는다.
    """

    def __init__(self, code: str):
        if code not in _ERROR_MESSAGES:
            raise ValueError("등록되지 않은 continuation 오류 코드입니다")
        self.code = code
        super().__init__(_ERROR_MESSAGES[code])

    def __repr__(self) -> str:
        return f"ContinuationError(code={self.code!r})"


def _strictJsonTree(value: Any, *, seen: set[int]) -> Any:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("canonical JSON float는 유한해야 합니다")
        return value
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in seen:
            raise ValueError("canonical JSON tree에 cycle이 있습니다")
        seen.add(identity)
        try:
            normalized = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise TypeError("canonical JSON mapping key는 str이어야 합니다")
                normalized[key] = _strictJsonTree(item, seen=seen)
            return normalized
        finally:
            seen.remove(identity)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        identity = id(value)
        if identity in seen:
            raise ValueError("canonical JSON tree에 cycle이 있습니다")
        seen.add(identity)
        try:
            return [_strictJsonTree(item, seen=seen) for item in value]
        finally:
            seen.remove(identity)
    raise TypeError("canonical JSON tree에 지원하지 않는 타입이 있습니다")


def canonicalJsonBytes(value: Any) -> bytes:
    """JSON-compatible 값을 결정적 UTF-8 bytes로 직렬화한다.

    Args:
        value: query 또는 contract identity 값.

    Returns:
        key 순서와 공백이 정규화된 JSON bytes.

    Raises:
        TypeError: JSON으로 직렬화할 수 없을 때.

    Example:
        ``canonicalJsonBytes({"market": "KR"})``.

    Guide:
        query state와 queryDigest를 같은 bytes에서 만든다.

    SeeAlso:
        ``canonicalDigest``.

    Requires:
        호출자는 의미 있는 타입 변환을 사전에 끝내야 한다.

    AIContext:
        repr 기반 hash를 금지하고 cross-process pin을 재현한다.
    """
    normalized = _strictJsonTree(value, seen=set())
    return json.dumps(
        normalized,
        allow_nan=False,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonicalDigest(value: Any) -> str:
    """JSON-compatible identity의 canonical SHA-256을 만든다.

    Args:
        value: source, query, contract identity 값.

    Returns:
        lowercase SHA-256 hex digest.

    Raises:
        TypeError: JSON으로 직렬화할 수 없을 때.

    Example:
        ``canonicalDigest({"asset": "scan.account"})``.

    Guide:
        이미 canonical bytes인 값은 ``bytesDigest``를 사용한다.

    SeeAlso:
        ``canonicalJsonBytes``, ``bytesDigest``.

    Requires:
        값은 JSON 의미론 안에서 결정적이어야 한다.

    AIContext:
        control plane의 source와 contract pin 생성 seam이다.
    """
    return hashlib.sha256(canonicalJsonBytes(value)).hexdigest()


def bytesDigest(value: bytes) -> str:
    """bytes의 SHA-256 digest를 만든다.

    Args:
        value: canonical query 또는 artifact bytes.

    Returns:
        lowercase SHA-256 hex digest.

    Raises:
        TypeError: bytes가 아닐 때.

    Example:
        ``bytesDigest(b"{}")``.

    Guide:
        QueryState.queryPayload와 queryDigest를 결박할 때 사용한다.

    SeeAlso:
        ``canonicalDigest``.

    Requires:
        mutable bytearray는 먼저 immutable bytes로 바꾼다.

    AIContext:
        query 원문을 ledger에 보관하지 않고 equality를 증명한다.
    """
    if not isinstance(value, bytes):
        raise TypeError("digest 입력은 bytes여야 합니다")
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class ContinuationPins:
    """source, query, contract, Arrow schema를 고정하는 digest pins."""

    sourceDigest: str
    queryDigest: str
    contractDigest: str
    schemaDigest: str

    def __post_init__(self) -> None:
        for name in ("sourceDigest", "queryDigest", "contractDigest", "schemaDigest"):
            value = getattr(self, name)
            if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
                raise ValueError(f"{name}는 lowercase SHA-256이어야 합니다")


@dataclass(frozen=True, slots=True)
class ContinuationPolicy:
    """page, private state, token lifetime, claim, GC 상한."""

    maxPageRows: int = 10_000
    maxPageBytes: int = 8 * 1024 * 1024
    maxPageLogicalBytes: int = 8 * 1024 * 1024
    maxStateBytes: int = 512 * 1024
    maxTokenIssueAttempts: int = 8
    tokenTtlSeconds: float = 900.0
    leaseSeconds: float = 30.0
    waitSeconds: float = 30.0
    pollSeconds: float = 0.01
    pruneGraceSeconds: float = 60.0
    artifactStageSeconds: float = 300.0

    def __post_init__(self) -> None:
        integers = (
            self.maxPageRows,
            self.maxPageBytes,
            self.maxPageLogicalBytes,
            self.maxStateBytes,
            self.maxTokenIssueAttempts,
        )
        if any(type(value) is not int or value <= 0 for value in integers):
            raise ValueError("continuation 정수 budget은 양의 int여야 합니다")
        times = (
            self.tokenTtlSeconds,
            self.leaseSeconds,
            self.waitSeconds,
            self.pollSeconds,
            self.pruneGraceSeconds,
            self.artifactStageSeconds,
        )
        if any(not _finitePositiveNumber(value) for value in times):
            raise ValueError("continuation 시간 정책은 유한한 양수여야 합니다")


@dataclass(frozen=True, slots=True)
class ContinuationMaintenanceBudget:
    """한 maintenance 호출이 소비할 chain, ledger, CAS 작업 상한."""

    maxChains: int = 100
    maxRootScans: int = 400
    maxContinuationRows: int = 10_000
    maxLedgerScans: int = 10_000
    maxCasPrefixes: int = 16
    maxCasEntries: int = 10_000
    maxArtifactDeletes: int = 10_000

    def __post_init__(self) -> None:
        values = (
            self.maxChains,
            self.maxRootScans,
            self.maxContinuationRows,
            self.maxLedgerScans,
            self.maxCasPrefixes,
            self.maxCasEntries,
            self.maxArtifactDeletes,
        )
        if any(type(value) is not int or value <= 0 for value in values):
            raise ValueError("continuation maintenance budget은 양의 int여야 합니다")
        if self.maxCasPrefixes > 256:
            raise ValueError("maxCasPrefixes는 256 이하여야 합니다")


@dataclass(frozen=True, slots=True)
class ContinuationQueryState:
    """CAS에만 보관되는 canonical query와 owner cursor."""

    queryPayload: bytes = field(repr=False)
    cursorPayload: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.queryPayload, bytes) or not isinstance(self.cursorPayload, bytes):
            raise TypeError("queryPayload와 cursorPayload는 bytes여야 합니다")


@dataclass(frozen=True, slots=True)
class LoadedContinuationContext:
    """token 원문 없이 복원한 private state와 immutable pins."""

    tokenDigest: str
    state: ContinuationQueryState = field(repr=False)
    pins: ContinuationPins
    issuedAt: float
    expiresAt: float


@dataclass(frozen=True, slots=True)
class PageEnvelope:
    """owner가 반환하는 Arrow IPC page와 다음 private state."""

    payload: bytes = field(repr=False)
    rowCount: int
    nextState: ContinuationQueryState | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.payload, bytes):
            raise TypeError("payload는 bytes여야 합니다")
        if type(self.rowCount) is not int or self.rowCount < 0:
            raise ValueError("rowCount는 음수가 아닌 int여야 합니다")
        if self.nextState is not None and not isinstance(self.nextState, ContinuationQueryState):
            raise TypeError("nextState는 ContinuationQueryState 또는 None이어야 합니다")


@dataclass(frozen=True, slots=True)
class ArrowPayloadFacts:
    """Arrow IPC bytes에서 직접 계산한 page facts."""

    rowCount: int
    byteCount: int
    logicalByteCount: int
    schemaDigest: str
    containerKind: str


@dataclass(frozen=True, slots=True)
class IssuedContinuation:
    """최초 1회 반환되는 bearer token과 안전한 audit metadata."""

    token: str = field(repr=False)
    tokenDigest: str
    expiresAt: float


@dataclass(frozen=True, slots=True)
class ContinuationPage:
    """CAS 검증을 통과한 bounded Arrow IPC page."""

    pageRef: str
    pageDigest: str
    payload: bytes = field(repr=False)
    rowCount: int
    byteCount: int
    schemaDigest: str
    nextToken: str | None = field(repr=False)
    replayed: bool
    resultDigest: str


@dataclass(frozen=True, slots=True)
class PruneReport:
    """만료 chain과 unreferenced CAS 정리 결과."""

    chainsDeleted: int
    rowsDeleted: int
    artifactsDeleted: int
    bytesFreed: int
    rootsScanned: int = 0
    continuationRowsExamined: int = 0
    ledgerArtifactsScanned: int = 0
    casPrefixesScanned: int = 0
    casEntriesExamined: int = 0
    sweepCyclesCompleted: int = 0
