"""Immutable Data Workbench generation contracts.

SQLite sees only digests, counters, states, and lease times. Raw queries,
continuation tokens, owner identifiers, and Arrow payloads never enter the
ledger.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Literal, Never, cast

from dartlab.data.continuation import (
    ContinuationError,
    canonicalDigest,
)

FORMAT_VERSION = 1
SCHEMA_VERSION = 1
DIGEST_LENGTH = 64

ERROR_MESSAGES = {
    "MATERIALIZATION_INVALID": "materialization 입력이 유효하지 않습니다",
    "MATERIALIZATION_BUSY": "materialization generation을 다른 builder가 생성 중입니다",
    "MATERIALIZATION_LEASE_LOST": "materialization builder lease를 잃었습니다",
    "MATERIALIZATION_NOT_READY": "materialization generation이 READY 상태가 아닙니다",
    "MATERIALIZATION_CORRUPT": "materialization 저장 상태의 무결성 검증에 실패했습니다",
    "MATERIALIZATION_BUDGET": "materialization budget을 초과했습니다",
    "MATERIALIZATION_PAYLOAD_INVALID": "materialization Arrow payload가 유효하지 않습니다",
    "MATERIALIZATION_SECURITY": "materialization private storage 검증에 실패했습니다",
    "MATERIALIZATION_SCHEMA_UNSUPPORTED": "materialization ledger schema를 지원하지 않습니다",
}


class MaterializationError(RuntimeError):
    """비밀 원문을 노출하지 않는 materialization 오류.

    Capabilities:
        고정 code와 고정 메시지만 외부로 전달한다.

    Args:
        code: 등록된 ``MATERIALIZATION_*`` 오류 code.

    Returns:
        machine-readable ``code``를 가진 예외.

    Example:
        ``raise MaterializationError("MATERIALIZATION_CORRUPT")``.

    Guide:
        query, owner, payload 원문을 예외 메시지에 넣지 않는다.

    SeeAlso:
        ``MaterializationStore.readReady``.

    Requires:
        code가 이 모듈의 고정 오류 집합에 등록되어 있어야 한다.

    AIContext:
        SQLite와 로그에 bearer나 query 원문이 번지는 것을 막는다.
    """

    def __init__(self, code: str):
        if code not in ERROR_MESSAGES:
            raise ValueError("등록되지 않은 materialization 오류 code입니다")
        self.code = code
        super().__init__(ERROR_MESSAGES[code])

    def __repr__(self) -> str:
        return f"MaterializationError(code={self.code!r})"


def raiseFromContinuation(error: ContinuationError) -> Never:
    """Continuation 오류를 비밀값 없는 materialization 오류로 바꾼다."""

    if error.code == "CONTINUATION_SECURITY_FAILED":
        raise MaterializationError("MATERIALIZATION_SECURITY") from None
    if error.code in {
        "CONTINUATION_BYTE_BUDGET",
        "CONTINUATION_LOGICAL_BYTE_BUDGET",
        "CONTINUATION_ROW_BUDGET",
        "CONTINUATION_STATE_BUDGET",
    }:
        raise MaterializationError("MATERIALIZATION_BUDGET") from None
    if error.code in {
        "CONTINUATION_COMPRESSION_UNSUPPORTED",
        "CONTINUATION_PAYLOAD_INVALID",
        "CONTINUATION_PAYLOAD_ROW_MISMATCH",
        "CONTINUATION_PAYLOAD_SCHEMA_MISMATCH",
    }:
        raise MaterializationError("MATERIALIZATION_PAYLOAD_INVALID") from None
    raise MaterializationError("MATERIALIZATION_CORRUPT") from None


def isDigest(value: Any) -> bool:
    """값이 canonical lowercase SHA-256인지 판정한다."""

    return (
        type(value) is str
        and len(value) == DIGEST_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def requireDigest(value: Any) -> str:
    """저장값을 digest로 검증하거나 fail-closed 한다."""

    if not isDigest(value):
        raise MaterializationError("MATERIALIZATION_CORRUPT")
    return value


def requireNonNegativeInt(value: Any) -> int:
    """저장값을 음수가 아닌 int로 검증한다."""

    if type(value) is not int or value < 0:
        raise MaterializationError("MATERIALIZATION_CORRUPT")
    return value


def requireNonNegativeNumber(value: Any) -> float:
    """저장값을 유한한 음수가 아닌 실수로 검증한다."""

    if type(value) not in (int, float):
        raise MaterializationError("MATERIALIZATION_CORRUPT")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise MaterializationError("MATERIALIZATION_CORRUPT")
    return number


def identityDigest(value: str) -> str:
    """Process-local identity 원문을 ledger용 digest로 바꾼다."""

    if type(value) is not str or not value or len(value) > 512:
        raise MaterializationError("MATERIALIZATION_INVALID")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class GenerationPins:
    """한 immutable generation을 이루는 exact identity pins."""

    assetDigest: str
    sourceDigest: str
    queryDigest: str
    universeDigest: str
    contractDigest: str
    schemaDigest: str

    def __post_init__(self) -> None:
        for name in (
            "assetDigest",
            "sourceDigest",
            "queryDigest",
            "universeDigest",
            "contractDigest",
            "schemaDigest",
        ):
            if not isDigest(getattr(self, name)):
                raise ValueError(f"{name}는 lowercase SHA-256이어야 합니다")

    def asTree(self) -> dict[str, str]:
        """Canonical generation identity tree를 반환한다."""

        return {
            "assetDigest": self.assetDigest,
            "sourceDigest": self.sourceDigest,
            "queryDigest": self.queryDigest,
            "universeDigest": self.universeDigest,
            "contractDigest": self.contractDigest,
            "schemaDigest": self.schemaDigest,
        }

    @classmethod
    def fromTree(cls, value: Any) -> GenerationPins:
        """Digest-only mapping에서 exact pins를 복원한다."""

        expected = {
            "assetDigest",
            "sourceDigest",
            "queryDigest",
            "universeDigest",
            "contractDigest",
            "schemaDigest",
        }
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("materialization pins mapping이 유효하지 않습니다")
        return cls(**value)


def generationKey(pins: GenerationPins) -> str:
    """Exact pins에서 deterministic generation key를 만든다.

    Capabilities:
        asset, source, query, universe, contract, schema pin을 한 key에 결박한다.

    Args:
        pins: 이미 canonical digest로 고정한 generation identity.

    Returns:
        lowercase SHA-256 generation key.

    Example:
        ``key = generationKey(pins)``.

    Guide:
        raw query나 source path를 key 입력으로 직접 넣지 않는다.

    SeeAlso:
        ``GenerationPins``.

    Requires:
        모든 pin은 exact source snapshot과 public query contract에서 계산돼야 한다.

    AIContext:
        source drift는 overwrite가 아니라 새 generation key를 만든다.
    """

    if not isinstance(pins, GenerationPins):
        raise TypeError("pins는 GenerationPins여야 합니다")
    return canonicalDigest({"formatVersion": FORMAT_VERSION, "pins": pins.asTree()})


@dataclass(frozen=True, slots=True)
class MaterializationPolicy:
    """Generation 실행, lease, payload, retention 상한."""

    maxPageRows: int = 10_000
    maxPageBytes: int = 8 * 1024 * 1024
    maxPageLogicalBytes: int = 8 * 1024 * 1024
    maxPagesPerGeneration: int = 4_096
    maxRowsPerGeneration: int = 10_000_000
    maxBytesPerGeneration: int = 4 * 1024 * 1024 * 1024
    maxManifestBytes: int = 4 * 1024 * 1024
    builderLeaseSeconds: float = 30.0
    readerLeaseSeconds: float = 30.0
    artifactStageSeconds: float = 300.0
    readyRetentionSeconds: float = 7 * 24 * 60 * 60
    maxBuildSeconds: float = 6 * 60 * 60

    def __post_init__(self) -> None:
        integers = (
            self.maxPageRows,
            self.maxPageBytes,
            self.maxPageLogicalBytes,
            self.maxPagesPerGeneration,
            self.maxRowsPerGeneration,
            self.maxBytesPerGeneration,
            self.maxManifestBytes,
        )
        if any(type(value) is not int or value <= 0 for value in integers):
            raise ValueError("materialization 정수 budget은 양의 int여야 합니다")
        times = (
            self.builderLeaseSeconds,
            self.readerLeaseSeconds,
            self.artifactStageSeconds,
            self.readyRetentionSeconds,
            self.maxBuildSeconds,
        )
        if any(
            type(value) not in (int, float) or not math.isfinite(float(value)) or float(value) <= 0 for value in times
        ):
            raise ValueError("materialization 시간 정책은 유한한 양수여야 합니다")


@dataclass(frozen=True, slots=True)
class MaintenanceBudget:
    """Maintenance 한 호출의 정확한 작업 상한."""

    maxReaderLeases: int = 100
    maxGenerationTransitions: int = 10
    maxPageReferences: int = 100
    maxArtifacts: int = 100

    def __post_init__(self) -> None:
        values = (
            self.maxReaderLeases,
            self.maxGenerationTransitions,
            self.maxPageReferences,
            self.maxArtifacts,
        )
        if any(type(value) is not int or value <= 0 for value in values):
            raise ValueError("maintenance budget은 양의 int여야 합니다")


@dataclass(frozen=True, slots=True)
class BuildClaim:
    """Digest-only builder claim."""

    generationKey: str
    pins: GenerationPins
    ownerDigest: str
    epoch: int
    acquired: bool
    ready: bool


@dataclass(frozen=True, slots=True)
class PageDraft:
    """Owner가 생성한 immutable 등록 전 Arrow IPC page."""

    payload: bytes = field(repr=False)
    rowCount: int

    def __post_init__(self) -> None:
        if not isinstance(self.payload, bytes):
            raise TypeError("payload는 bytes여야 합니다")
        if type(self.rowCount) is not int or self.rowCount < 0:
            raise ValueError("rowCount는 음수가 아닌 int여야 합니다")


@dataclass(frozen=True, slots=True)
class MaterializedPage:
    """검증된 immutable Arrow page."""

    ordinal: int
    payloadDigest: str
    payload: bytes = field(repr=False)
    rowCount: int
    byteCount: int
    logicalByteCount: int
    schemaDigest: str


@dataclass(frozen=True, slots=True)
class MaterializationReceipt:
    """외부 process가 보존할 수 있는 digest-only reuse identity."""

    generationKey: str
    terminalRootDigest: str
    pins: GenerationPins

    def __post_init__(self) -> None:
        if not isDigest(self.generationKey) or not isDigest(self.terminalRootDigest):
            raise ValueError("materialization receipt digest가 유효하지 않습니다")
        if self.generationKey != generationKey(self.pins):
            raise ValueError("materialization receipt generation key가 pins와 다릅니다")

    def asTree(self) -> dict[str, Any]:
        """Mapping query와 receipt 직렬화를 위한 구조를 반환한다."""

        return {
            "generationKey": self.generationKey,
            "terminalRootDigest": self.terminalRootDigest,
            "pins": self.pins.asTree(),
        }

    @classmethod
    def fromTree(cls, value: Any) -> MaterializationReceipt:
        """Digest-only mapping에서 receipt를 복원한다."""

        expected = {"generationKey", "terminalRootDigest", "pins"}
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("materialization receipt mapping이 유효하지 않습니다")
        return cls(
            generationKey=value["generationKey"],
            terminalRootDigest=value["terminalRootDigest"],
            pins=GenerationPins.fromTree(value["pins"]),
        )


@dataclass(frozen=True, slots=True)
class MaterializedGeneration:
    """Terminal manifest에서 복원한 READY generation."""

    generationKey: str
    pins: GenerationPins
    terminalRootDigest: str
    pages: tuple[MaterializedPage, ...]
    rowCount: int
    byteCount: int

    @property
    def receipt(self) -> MaterializationReceipt:
        """Generation의 구조화된 재사용 identity를 반환한다."""

        return MaterializationReceipt(
            generationKey=self.generationKey,
            terminalRootDigest=self.terminalRootDigest,
            pins=self.pins,
        )


@dataclass(frozen=True, slots=True)
class MaterializedGenerationHandle:
    """Payload를 적재하지 않는 READY generation metadata handle."""

    generationKey: str
    pins: GenerationPins
    terminalRootDigest: str
    pageCount: int
    rowCount: int
    byteCount: int

    @property
    def receipt(self) -> MaterializationReceipt:
        """Handle의 구조화된 재사용 identity를 반환한다."""

        return MaterializationReceipt(
            generationKey=self.generationKey,
            terminalRootDigest=self.terminalRootDigest,
            pins=self.pins,
        )


@dataclass(frozen=True, slots=True)
class BuildOutcome:
    """Build 또는 replay 결과와 명시적 replay 여부."""

    generation: MaterializedGeneration
    replayed: bool


@dataclass(frozen=True, slots=True)
class BuildHandleOutcome:
    """Payload eager load 없는 build 또는 replay 결과."""

    generation: MaterializedGenerationHandle
    replayed: bool


@dataclass(frozen=True, slots=True)
class MaintenanceReport:
    """Bounded maintenance 작업 카운터."""

    readerLeasesDeleted: int
    generationsMarked: int
    pageReferencesReleased: int
    generationsDeleted: int
    artifactsDeleted: int
    bytesFreed: int


@dataclass(frozen=True, slots=True)
class PageRecord:
    """SQLite와 terminal manifest가 공유하는 page facts."""

    ordinal: int
    payloadDigest: str
    rowCount: int
    byteCount: int
    logicalByteCount: int
    schemaDigest: str

    def asTree(self) -> dict[str, Any]:
        """Canonical terminal manifest page tree를 반환한다."""

        return {
            "ordinal": self.ordinal,
            "payloadDigest": self.payloadDigest,
            "rowCount": self.rowCount,
            "byteCount": self.byteCount,
            "logicalByteCount": self.logicalByteCount,
            "schemaDigest": self.schemaDigest,
        }


MaterializationMode = Literal["runtime", "reuse", "refresh", "offline"]


@dataclass(frozen=True, slots=True)
class MaterializationDirective:
    """기존 query axis에 얹는 명시적 materialization 정책."""

    mode: MaterializationMode = "runtime"
    receipt: MaterializationReceipt | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"runtime", "reuse", "refresh", "offline"}:
            raise ValueError("materialization mode가 유효하지 않습니다")
        if self.mode == "offline" and self.receipt is None:
            raise ValueError("offline materialization은 receipt가 필요합니다")
        if self.mode in {"runtime", "refresh"} and self.receipt is not None:
            raise ValueError(f"{self.mode} materialization은 receipt를 받지 않습니다")


def parseMaterializationDirective(value: Any) -> MaterializationDirective:
    """Python과 mapping query 입력을 같은 정책 객체로 정규화한다."""

    if value is None:
        return MaterializationDirective()
    if isinstance(value, MaterializationDirective):
        return value
    if isinstance(value, str):
        return MaterializationDirective(mode=cast(MaterializationMode, value))
    if not isinstance(value, dict):
        raise TypeError("materialization은 mode 문자열 또는 mapping이어야 합니다")
    expected = {"mode", "receipt"}
    if not set(value) <= expected:
        raise ValueError("materialization mapping에 알 수 없는 field가 있습니다")
    receiptValue = value.get("receipt")
    receipt = (
        receiptValue
        if isinstance(receiptValue, MaterializationReceipt)
        else MaterializationReceipt.fromTree(receiptValue)
        if receiptValue is not None
        else None
    )
    mode = cast(MaterializationMode, value.get("mode", "runtime"))
    return MaterializationDirective(mode=mode, receipt=receipt)
