"""Universe U0 census가 공유하는 불변 계약과 canonical digest 도구."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


def _canonicalValue(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: _canonicalValue(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        normalized = {}
        for key, item in value.items():
            normalizedKey = unicodedata.normalize("NFC", str(key))
            if normalizedKey in normalized:
                raise ValueError(f"canonical key collision: {normalizedKey}")
            normalized[normalizedKey] = _canonicalValue(item)
        return dict(sorted(normalized.items()))
    if isinstance(value, (tuple, list)):
        return [_canonicalValue(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_canonicalValue(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("naive datetime은 canonical JSON에서 금지")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return unicodedata.normalize("NFC", value.as_posix())
    if isinstance(value, bytes):
        return {"sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("NaN과 Infinity는 canonical JSON에서 금지")
        return 0.0 if value == 0.0 else value
    return value


def canonicalJson(value: Any) -> bytes:
    """값을 플랫폼에 독립적인 UTF-8 JSON byte로 직렬화한다.

    Args:
        value: dataclass, mapping, sequence 또는 JSON scalar.

    Returns:
        key 정렬과 compact separator가 적용된 UTF-8 byte.

    Raises:
        TypeError: 지원하지 않는 값이 JSON encoder에 도달한 경우.

    Example:
        ``canonicalJson({"b": 2, "a": 1})``은 항상 같은 byte를 반환한다.
    """
    return json.dumps(
        _canonicalValue(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonicalDigest(value: Any) -> str:
    """Canonical JSON의 SHA-256을 계산한다.

    Args:
        value: digest 대상.

    Returns:
        64자리 소문자 SHA-256.

    Raises:
        TypeError: canonical JSON으로 직렬화할 수 없는 경우.

    Example:
        ``canonicalDigest({"a": 1})``.
    """
    return hashlib.sha256(canonicalJson(value)).hexdigest()


class DiscoveryState(str, Enum):
    """U0 discovery가 허용하는 terminal state."""

    PINNED = "PINNED"
    CLASSIFIED = "CLASSIFIED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    ACCESS_DENIED = "ACCESS_DENIED"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    PARTIAL = "PARTIAL"
    PARSE_ERROR = "PARSE_ERROR"


@dataclass(frozen=True, slots=True)
class ConfiguredRepoSet:
    repoIds: tuple[str, ...]
    authorityDigest: str


@dataclass(frozen=True, slots=True)
class HfFileMetadata:
    path: str
    size: int
    oid: str | None
    lfsSha256: str | None = None


@dataclass(frozen=True, slots=True)
class PinnedRepo:
    repoId: str
    revision: str | None
    lastModifiedUtc: str | None
    private: bool | None
    state: DiscoveryState
    files: tuple[HfFileMetadata, ...]
    errorCode: str | None = None


@dataclass(frozen=True, slots=True)
class DiscoveredFile:
    repoId: str
    revision: str
    path: str
    size: int
    oid: str | None
    formatKind: str
    state: DiscoveryState
    payloadBodyRead: bool = False
    lfsSha256: str | None = None


@dataclass(frozen=True, slots=True)
class ReleaseDeclaration:
    releaseId: str
    repoId: str
    prefix: str
    public: bool
    ipcMirror: bool


@dataclass(frozen=True, slots=True)
class RegistryRecord:
    recordId: str
    owner: str
    sourceKind: str
    hidden: bool


@dataclass(frozen=True, slots=True)
class CapabilityCensus:
    runtimeIds: tuple[str, ...]
    registryRecords: tuple[RegistryRecord, ...]
    sourceDigests: tuple[tuple[str, str], ...]
    errors: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class BlogPostRecord:
    relativePath: str
    category: str
    slug: str
    title: str | None
    publishedAt: str | None
    youtubeId: str | None
    contentDigest: str
    frontmatterDigest: str
    headingCount: int
    tableRowCount: int
    codeBlockCount: int
    paragraphCount: int
    imageRefs: tuple[str, ...]
    linkRefs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BlogCensus:
    posts: tuple[BlogPostRecord, ...]
    parseErrors: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class CompanionRecord:
    relativePath: str
    ownerPath: str
    kind: str
    contentDigest: str


@dataclass(frozen=True, slots=True)
class CompanionCensus:
    records: tuple[CompanionRecord, ...]
    unknownPaths: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class MediaCatalogRecord:
    recordKind: str
    recordKey: str
    targetRef: str | None
    metadataDigest: str
    relatedRefs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MediaCensus:
    objectCount: int
    aliasCount: int
    postCount: int
    collectionCount: int
    manifestCount: int
    missingObjectPaths: tuple[str, ...]
    unregisteredHfObjectPaths: tuple[str, ...]
    brokenBlogRefs: tuple[str, ...]
    unreferencedObjectDigests: tuple[str, ...]
    errors: tuple[str, ...]
    digest: str
    records: tuple[MediaCatalogRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class PodcastRecord:
    episodeId: str
    relativePath: str
    title: str | None
    youtubeId: str | None
    hasEpisodeMetadata: bool
    hasPublishedReceipt: bool
    hasScript: bool
    metadataDigest: str


@dataclass(frozen=True, slots=True)
class PodcastCensus:
    episodes: tuple[PodcastRecord, ...]
    parseErrors: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class SourceDiscovery:
    configuredRepoSet: ConfiguredRepoSet
    pinnedRepositories: tuple[PinnedRepo, ...]
    hfFiles: tuple[DiscoveredFile, ...]
    releaseDeclarations: tuple[ReleaseDeclaration, ...]
    capabilityCensus: CapabilityCensus
    blogCensus: BlogCensus
    companionCensus: CompanionCensus
    mediaCensus: MediaCensus
    podcastCensus: PodcastCensus
    networkOperations: tuple[str, ...]
    payloadBodiesRead: int


@dataclass(frozen=True, slots=True)
class CoverageLedger:
    configuredRepoCount: int
    pinnedRepoCount: int
    accessDeniedRepoIds: tuple[str, ...]
    discoveredFileCount: int
    discoveredByteCount: int
    classifiedFileCount: int
    unsupportedFormatCount: int
    unconfiguredRepoIds: tuple[str, ...]
    declaredOnlyPrefixes: tuple[str, ...]
    liveOnlyPathCount: int
    runtimeCapabilityCount: int
    registryRecordCount: int
    blogPostCount: int
    blogParseErrorCount: int
    companionCount: int
    unknownCompanionCount: int
    mediaObjectCount: int
    mediaMissingObjectCount: int
    mediaUnregisteredObjectCount: int
    mediaBrokenRefCount: int
    mediaUnreferencedObjectCount: int
    podcastCount: int
    terminalCoverageRatio: float
    g0Passed: bool
    failureCodes: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class CensusResult:
    observedAtUtc: str
    discovery: SourceDiscovery
    coverage: CoverageLedger
    snapshotDigest: str


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    durationSeconds: float
    discoveredFileCount: int
    discoveredByteCount: int
    networkOperationCount: int
    payloadBodiesRead: int
    peakMemoryBytes: int
    targetSeconds: float
    targetMet: bool
    censusDigest: str
