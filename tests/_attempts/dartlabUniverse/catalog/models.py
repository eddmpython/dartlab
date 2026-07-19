"""Universe U3 catalog의 Arrow 호환 불변 record."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts import EpistemicClass, SystemTime, TimeRange, VerificationState, Visibility
from ..ids import versionId

CATALOG_OBJECT_SCHEMA_VERSION = "du-catalog-object-v1"


def catalogObjectVersionId(
    *,
    objectId: str,
    objectKind: str,
    canonicalLabel: str,
    aliases: tuple[str, ...],
    identifierRefs: tuple[str, ...],
    resourceRefs: tuple[str, ...],
    epistemicClass: EpistemicClass,
    verificationState: VerificationState,
    validTime: TimeRange,
    attributes: tuple[tuple[str, str], ...],
) -> str:
    """System 관측 시각과 무관한 object semantic version ID를 만든다."""
    return versionId(
        objectId,
        (
            CATALOG_OBJECT_SCHEMA_VERSION,
            objectKind,
            canonicalLabel,
            aliases,
            identifierRefs,
            resourceRefs,
            epistemicClass,
            verificationState,
            validTime,
            attributes,
        ),
    )


@dataclass(frozen=True, slots=True)
class CatalogResource:
    """원본 payload를 복제하지 않고 source object를 주소화한다."""

    resourceId: str
    resourceVersionId: str
    resourceKind: str
    label: str
    namespace: str
    sourceKind: str
    sourceRef: str
    sourceRevision: str
    locator: tuple[tuple[str, str], ...]
    contentSelector: tuple[tuple[str, str], ...]
    contentDigest: str
    mediaType: str | None
    schemaFingerprint: str | None
    byteSize: int | None
    rowCount: int | None
    visibility: Visibility
    licenseRef: str | None
    status: str
    discoveredAt: str
    observedAt: str
    gapReason: str | None = None
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class CatalogObject:
    """Resource 위에 놓이는 탐색 가능한 지식 객체다."""

    schemaVersion: str
    objectId: str
    objectVersionId: str
    objectKind: str
    canonicalLabel: str
    aliases: tuple[str, ...]
    identifierRefs: tuple[str, ...]
    resourceRefs: tuple[str, ...]
    epistemicClass: EpistemicClass
    verificationState: VerificationState
    validTime: TimeRange
    systemTime: SystemTime
    visibility: Visibility
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class CatalogEvidence:
    """Catalog object에서 원본 revision까지 이어지는 근거 anchor다."""

    evidenceId: str
    objectId: str
    resourceVersionId: str
    sourceKind: str
    sourceRef: str
    sourceRevision: str
    locator: tuple[tuple[str, str], ...]
    selector: tuple[tuple[str, str], ...]
    contentDigest: str
    retrievedAt: str
    visibility: Visibility
    licenseRef: str | None
    quoteDigest: str | None


@dataclass(frozen=True, slots=True)
class CatalogCoverage:
    discoveredCount: int
    resourceCount: int
    objectCount: int
    evidenceCount: int
    sourcePayloadCopies: int
    duplicateLogicalIds: int
    duplicateVersionIds: int
    missingLocatorCount: int
    coverageRatio: float


@dataclass(frozen=True, slots=True)
class CatalogState:
    schemaVersion: str
    censusSnapshotDigest: str
    resources: tuple[CatalogResource, ...]
    objects: tuple[CatalogObject, ...]
    evidence: tuple[CatalogEvidence, ...]
    coverage: CatalogCoverage
    digest: str
