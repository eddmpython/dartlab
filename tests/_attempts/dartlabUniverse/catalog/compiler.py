"""U0 discovery를 payload 사본 없는 U3 runtime catalog로 컴파일한다."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

from ..canonical import CensusResult, DiscoveryState, canonicalDigest, canonicalJson
from ..contracts import EpistemicClass, SystemTime, TimeRange, VerificationState, Visibility
from ..identity.ledger import IdentityEvidence
from ..ids import blogPostIds, hfFileIds, logicalId, versionId
from ..temporal import parseInstant
from .models import (
    CATALOG_OBJECT_SCHEMA_VERSION,
    CatalogCoverage,
    CatalogEvidence,
    CatalogObject,
    CatalogResource,
    CatalogState,
    catalogObjectVersionId,
)

if TYPE_CHECKING:
    from ..execution.registry import UniverseCapabilityRegistry

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_VERSION_ID_RE = re.compile(r"^du:v1:[a-z][a-z0-9-]*-version:[0-9a-f]{64}$")
_MEDIA_TYPE = {
    "ARROW": "application/vnd.apache.arrow.file",
    "CSV": "text/csv",
    "HTML": "text/html",
    "IMAGE": "image/*",
    "JSON": "application/json",
    "JSONL": "application/x-ndjson",
    "MARKDOWN": "text/markdown",
    "NPZ": "application/x-npz",
    "PARQUET": "application/vnd.apache.parquet",
    "TEXT": "text/plain",
    "YAML": "application/yaml",
}
_OWNED_CONTENT_LICENSE = "policy:dartlab-owned-content-v1"
_OWNED_METADATA_LICENSE = "policy:dartlab-owned-metadata-v1"
CATALOG_SCHEMA_VERSION = "du-catalog-v3"


def _visibility(private: bool | None) -> Visibility:
    if private is True:
        return Visibility.PRIVATE
    if private is False:
        return Visibility.LOCAL
    return Visibility.UNKNOWN


def _objectKind(formatKind: str) -> str:
    if formatKind in {"ARROW", "CSV", "JSONL", "NPZ", "PARQUET"}:
        return "TABLE"
    if formatKind in {"MARKDOWN", "HTML", "TEXT", "YAML", "JSON"}:
        return "DOCUMENT"
    if formatKind == "IMAGE":
        return "MEDIA"
    return "FILE"


def _digestOrMetadata(value: str | None, metadata: object) -> str:
    return value if value is not None and _SHA256_RE.fullmatch(value) else canonicalDigest(metadata)


def _verificationState(status: str) -> VerificationState:
    if status == "VERIFIED":
        return VerificationState.VERIFIED
    if status == "STRUCTURED":
        return VerificationState.STRUCTURED
    if status in {"REJECTED", "TOMBSTONED"}:
        return VerificationState(status)
    return VerificationState.ADDRESSABLE


def _catalogObject(
    resource: CatalogResource,
    *,
    objectId: str,
    objectKind: str,
    canonicalLabel: str,
    aliases: tuple[str, ...] = (),
    identifierRefs: tuple[str, ...] = (),
    epistemicClass: EpistemicClass = EpistemicClass.OBSERVED,
    verificationState: VerificationState | None = None,
    validTime: TimeRange | None = None,
    attributes: tuple[tuple[str, str], ...] = (),
) -> CatalogObject:
    orderedAliases = tuple(sorted(set(aliases)))
    orderedIdentifiers = tuple(sorted(set(identifierRefs)))
    activeValidTime = validTime or TimeRange()
    resourceRefs = (resource.resourceVersionId,)
    state = verificationState or _verificationState(resource.status)
    orderedAttributes = tuple(sorted(attributes))
    objectVersionId = catalogObjectVersionId(
        objectId=objectId,
        objectKind=objectKind,
        canonicalLabel=canonicalLabel,
        aliases=orderedAliases,
        identifierRefs=orderedIdentifiers,
        resourceRefs=resourceRefs,
        epistemicClass=epistemicClass,
        verificationState=state,
        validTime=activeValidTime,
        attributes=orderedAttributes,
    )
    return CatalogObject(
        schemaVersion=CATALOG_OBJECT_SCHEMA_VERSION,
        objectId=objectId,
        objectVersionId=objectVersionId,
        objectKind=objectKind,
        canonicalLabel=canonicalLabel,
        aliases=orderedAliases,
        identifierRefs=orderedIdentifiers,
        resourceRefs=resourceRefs,
        epistemicClass=epistemicClass,
        verificationState=state,
        validTime=activeValidTime,
        systemTime=SystemTime(
            knownAt=resource.observedAt,
            observedAt=resource.observedAt,
            ingestedAt=resource.observedAt,
        ),
        visibility=resource.visibility,
        attributes=orderedAttributes,
    )


def _triplet(resource: CatalogResource, *, objectKind: str, label: str, observedAt: str):
    objectId = logicalId("catalog-object", (resource.resourceId, objectKind))
    obj = _catalogObject(
        resource,
        objectId=objectId,
        objectKind=objectKind,
        canonicalLabel=label,
    )
    evidence = CatalogEvidence(
        evidenceId=logicalId("catalog-evidence", (objectId, resource.resourceVersionId, resource.locator)),
        objectId=objectId,
        resourceVersionId=resource.resourceVersionId,
        sourceKind=resource.sourceKind,
        sourceRef=resource.sourceRef,
        sourceRevision=resource.sourceRevision,
        locator=resource.locator,
        selector=resource.contentSelector,
        contentDigest=resource.contentDigest,
        retrievedAt=observedAt,
        visibility=resource.visibility,
        licenseRef=resource.licenseRef,
        quoteDigest=None,
    )
    return obj, evidence


def _duplicateCount(values: Iterable[str]) -> int:
    ordered = tuple(values)
    return len(ordered) - len(set(ordered))


def _merkleRoot(domain: str, records: Iterable[object]) -> str:
    """대형 record set을 한 JSON 사본으로 만들지 않고 순서 결박 digest를 계산한다."""
    digest = hashlib.sha256()
    digest.update(domain.encode("utf-8"))
    digest.update(b"\0")
    count = 0
    for record in records:
        digest.update(hashlib.sha256(canonicalJson(record)).digest())
        count += 1
    digest.update(count.to_bytes(8, "big"))
    return digest.hexdigest()


def _catalogDigest(
    *,
    censusSnapshotDigest: str,
    resources: tuple[CatalogResource, ...],
    objects: tuple[CatalogObject, ...],
    evidence: tuple[CatalogEvidence, ...],
    coverage: CatalogCoverage,
) -> str:
    return canonicalDigest(
        {
            "schemaVersion": CATALOG_SCHEMA_VERSION,
            "censusSnapshotDigest": censusSnapshotDigest,
            "resourceRoot": _merkleRoot("du-catalog-resource-v1", resources),
            "objectRoot": _merkleRoot(CATALOG_OBJECT_SCHEMA_VERSION, objects),
            "evidenceRoot": _merkleRoot("du-catalog-evidence-v1", evidence),
            "coverage": coverage,
        }
    )


def validateCatalogState(catalog: CatalogState) -> tuple[str, ...]:
    """Catalog payload, coverage, ID cardinality가 선언된 digest와 일치하는지 검증한다."""
    issues = []
    if catalog.schemaVersion != CATALOG_SCHEMA_VERSION:
        issues.append("CATALOG_SCHEMA_VERSION_MISMATCH")
    if catalog.coverage.resourceCount != len(catalog.resources):
        issues.append("CATALOG_RESOURCE_COUNT_MISMATCH")
    if catalog.coverage.objectCount != len(catalog.objects):
        issues.append("CATALOG_OBJECT_COUNT_MISMATCH")
    if catalog.coverage.evidenceCount != len(catalog.evidence):
        issues.append("CATALOG_EVIDENCE_COUNT_MISMATCH")
    logicalDuplicates = _duplicateCount(item.resourceId for item in catalog.resources)
    versionDuplicates = _duplicateCount(item.resourceVersionId for item in catalog.resources)
    missingLocators = sum(not item.locator for item in catalog.resources)
    expectedRatio = (
        len(catalog.resources) / catalog.coverage.discoveredCount if catalog.coverage.discoveredCount else 1.0
    )
    if catalog.coverage.discoveredCount != len(catalog.resources) or catalog.coverage.coverageRatio != expectedRatio:
        issues.append("CATALOG_DISCOVERY_COVERAGE_MISMATCH")
    if (
        catalog.coverage.duplicateLogicalIds != logicalDuplicates
        or catalog.coverage.duplicateVersionIds != versionDuplicates
        or catalog.coverage.missingLocatorCount != missingLocators
    ):
        issues.append("CATALOG_COVERAGE_COUNTER_MISMATCH")
    if logicalDuplicates:
        issues.append("CATALOG_RESOURCE_ID_DUPLICATE")
    if versionDuplicates:
        issues.append("CATALOG_RESOURCE_VERSION_ID_DUPLICATE")
    if _duplicateCount(item.objectId for item in catalog.objects):
        issues.append("CATALOG_OBJECT_ID_DUPLICATE")
    if _duplicateCount(item.objectVersionId for item in catalog.objects):
        issues.append("CATALOG_OBJECT_VERSION_ID_DUPLICATE")
    if _duplicateCount(item.evidenceId for item in catalog.evidence):
        issues.append("CATALOG_EVIDENCE_ID_DUPLICATE")
    if any(
        not item.resourceId.startswith("du:v1:") or not _VERSION_ID_RE.fullmatch(item.resourceVersionId)
        for item in catalog.resources
    ):
        issues.append("CATALOG_RESOURCE_ID_FORMAT_INVALID")
    if any(
        not item.objectId.startswith("du:v1:") or not _VERSION_ID_RE.fullmatch(item.objectVersionId)
        for item in catalog.objects
    ):
        issues.append("CATALOG_OBJECT_ID_FORMAT_INVALID")
    if any(not item.evidenceId.startswith("du:v1:catalog-evidence:") for item in catalog.evidence):
        issues.append("CATALOG_EVIDENCE_ID_FORMAT_INVALID")
    if catalog.resources != tuple(
        sorted(catalog.resources, key=lambda item: (item.resourceId, item.resourceVersionId))
    ):
        issues.append("CATALOG_RESOURCE_ORDER_MISMATCH")
    if catalog.objects != tuple(sorted(catalog.objects, key=lambda item: item.objectId)):
        issues.append("CATALOG_OBJECT_ORDER_MISMATCH")
    if catalog.evidence != tuple(sorted(catalog.evidence, key=lambda item: item.evidenceId)):
        issues.append("CATALOG_EVIDENCE_ORDER_MISMATCH")
    if missingLocators:
        issues.append("CATALOG_RESOURCE_LOCATOR_MISSING")
    if any(
        len(item.locator) != len(dict(item.locator))
        or len(item.contentSelector) != len(dict(item.contentSelector))
        or len(item.attributes) != len(dict(item.attributes))
        for item in catalog.resources
    ):
        issues.append("CATALOG_RESOURCE_KEY_DUPLICATE")
    if any(
        not item.resourceId
        or not item.resourceVersionId
        or not item.resourceKind
        or not item.label
        or not item.namespace
        or not item.sourceKind
        or not item.sourceRef
        or not item.sourceRevision
        or not item.contentDigest
        or not item.status
        or not item.discoveredAt
        or not item.observedAt
        for item in catalog.resources
    ):
        issues.append("CATALOG_RESOURCE_REQUIRED_FIELD_MISSING")
    if any(item.visibility is Visibility.PUBLIC and not item.licenseRef for item in catalog.resources):
        issues.append("PUBLIC_RESOURCE_LICENSE_MISSING")
    resourceByVersion = {item.resourceVersionId: item for item in catalog.resources}
    visibilityRank = {
        Visibility.PUBLIC: 0,
        Visibility.LOCAL: 1,
        Visibility.PRIVATE: 2,
        Visibility.RESTRICTED: 3,
        Visibility.UNKNOWN: 4,
    }
    if any(
        item.schemaVersion != CATALOG_OBJECT_SCHEMA_VERSION
        or not item.objectId
        or not item.objectKind
        or not item.canonicalLabel
        or not item.resourceRefs
        for item in catalog.objects
    ):
        issues.append("CATALOG_OBJECT_REQUIRED_FIELD_MISSING")
    if any(
        any(not value for value in (*item.aliases, *item.identifierRefs))
        or any(not key for key, _value in item.attributes)
        for item in catalog.objects
    ):
        issues.append("CATALOG_OBJECT_VALUE_INVALID")
    if any(
        item.aliases != tuple(sorted(set(item.aliases)))
        or item.identifierRefs != tuple(sorted(set(item.identifierRefs)))
        or item.resourceRefs != tuple(sorted(set(item.resourceRefs)))
        or len(item.attributes) != len(dict(item.attributes))
        for item in catalog.objects
    ):
        issues.append("CATALOG_OBJECT_CANONICAL_ORDER_MISMATCH")
    if any(any(ref not in resourceByVersion for ref in item.resourceRefs) for item in catalog.objects):
        issues.append("CATALOG_OBJECT_RESOURCE_REF_MISSING")
    if any(
        item.objectVersionId
        != catalogObjectVersionId(
            objectId=item.objectId,
            objectKind=item.objectKind,
            canonicalLabel=item.canonicalLabel,
            aliases=item.aliases,
            identifierRefs=item.identifierRefs,
            resourceRefs=item.resourceRefs,
            epistemicClass=item.epistemicClass,
            verificationState=item.verificationState,
            validTime=item.validTime,
            attributes=item.attributes,
        )
        for item in catalog.objects
    ):
        issues.append("CATALOG_OBJECT_VERSION_ID_MISMATCH")
    if any(
        visibilityRank[item.visibility]
        < max((visibilityRank[resourceByVersion[ref].visibility] for ref in item.resourceRefs), default=0)
        for item in catalog.objects
        if all(ref in resourceByVersion for ref in item.resourceRefs)
    ):
        issues.append("CATALOG_OBJECT_VISIBILITY_DOWNGRADE")
    objectById = {item.objectId: item for item in catalog.objects}
    if any(
        item.objectId not in objectById
        or not item.evidenceId
        or not item.sourceKind
        or not item.sourceRef
        or not item.sourceRevision
        or not item.contentDigest
        or not item.retrievedAt
        or item.resourceVersionId not in objectById[item.objectId].resourceRefs
        or len(item.locator) != len(dict(item.locator))
        or len(item.selector) != len(dict(item.selector))
        for item in catalog.evidence
    ):
        issues.append("CATALOG_EVIDENCE_PATH_INVALID")
    evidencePairs = {(item.objectId, item.resourceVersionId) for item in catalog.evidence}
    requiredEvidencePairs = {
        (item.objectId, resourceRef) for item in catalog.objects for resourceRef in item.resourceRefs
    }
    if not requiredEvidencePairs.issubset(evidencePairs):
        issues.append("CATALOG_OBJECT_EVIDENCE_INCOMPLETE")
    if any(item.visibility is Visibility.PUBLIC and not item.licenseRef for item in catalog.evidence):
        issues.append("PUBLIC_EVIDENCE_LICENSE_MISSING")
    if any(
        item.resourceVersionId in resourceByVersion
        and (
            item.sourceRef != resourceByVersion[item.resourceVersionId].sourceRef
            or item.sourceRevision != resourceByVersion[item.resourceVersionId].sourceRevision
            or item.contentDigest != resourceByVersion[item.resourceVersionId].contentDigest
            or item.licenseRef != resourceByVersion[item.resourceVersionId].licenseRef
        )
        for item in catalog.evidence
    ):
        issues.append("CATALOG_EVIDENCE_PROVENANCE_MISMATCH")
    if any(
        item.resourceVersionId in resourceByVersion
        and visibilityRank[item.visibility] < visibilityRank[resourceByVersion[item.resourceVersionId].visibility]
        for item in catalog.evidence
    ):
        issues.append("CATALOG_EVIDENCE_VISIBILITY_DOWNGRADE")
    try:
        for item in catalog.resources:
            discoveredAt = parseInstant(item.discoveredAt)
            observedAt = parseInstant(item.observedAt)
            if observedAt < discoveredAt:
                issues.append("CATALOG_RESOURCE_TIME_ORDER_INVALID")
        for item in catalog.objects:
            validStart = parseInstant(item.validTime.start) if item.validTime.start else None
            validEnd = parseInstant(item.validTime.end) if item.validTime.end else None
            if validStart is not None and validEnd is not None and validEnd <= validStart:
                issues.append("CATALOG_OBJECT_VALID_TIME_ORDER_INVALID")
            knownAt = parseInstant(item.systemTime.knownAt)
            if item.systemTime.observedAt:
                if parseInstant(item.systemTime.observedAt) < knownAt:
                    issues.append("CATALOG_OBJECT_SYSTEM_TIME_ORDER_INVALID")
            if item.systemTime.ingestedAt:
                if parseInstant(item.systemTime.ingestedAt) < knownAt:
                    issues.append("CATALOG_OBJECT_SYSTEM_TIME_ORDER_INVALID")
            if item.systemTime.retractedAt:
                if parseInstant(item.systemTime.retractedAt) < knownAt:
                    issues.append("CATALOG_OBJECT_SYSTEM_TIME_ORDER_INVALID")
            if item.verificationState is VerificationState.RETRACTED and not item.systemTime.retractedAt:
                issues.append("CATALOG_OBJECT_RETRACTION_TIME_MISSING")
        for item in catalog.evidence:
            parseInstant(item.retrievedAt)
    except ValueError:
        issues.append("CATALOG_TIME_INVALID")
    if any(not _SHA256_RE.fullmatch(item.contentDigest) for item in catalog.resources):
        issues.append("CATALOG_CONTENT_DIGEST_INVALID")
    if any(
        item.schemaFingerprint is not None and not _SHA256_RE.fullmatch(item.schemaFingerprint)
        for item in catalog.resources
    ):
        issues.append("CATALOG_SCHEMA_FINGERPRINT_INVALID")
    if any(
        item.byteSize is not None
        and (isinstance(item.byteSize, bool) or item.byteSize < 0)
        or item.rowCount is not None
        and (isinstance(item.rowCount, bool) or item.rowCount < 0)
        for item in catalog.resources
    ):
        issues.append("CATALOG_RESOURCE_COUNT_INVALID")
    if any(
        not _SHA256_RE.fullmatch(item.contentDigest)
        or item.quoteDigest is not None
        and not _SHA256_RE.fullmatch(item.quoteDigest)
        for item in catalog.evidence
    ):
        issues.append("CATALOG_EVIDENCE_DIGEST_INVALID")
    expectedDigest = _catalogDigest(
        censusSnapshotDigest=catalog.censusSnapshotDigest,
        resources=catalog.resources,
        objects=catalog.objects,
        evidence=catalog.evidence,
        coverage=catalog.coverage,
    )
    if catalog.digest != expectedDigest:
        issues.append("CATALOG_DIGEST_MISMATCH")
    return tuple(sorted(set(issues)))


def compileCatalog(census: CensusResult) -> CatalogState:
    """U0 전수 census를 resource, object, evidence catalog로 변환한다.

    Args:
        census: G0를 통과한 현재 authority census.

    Returns:
        결정론 정렬된 immutable catalog. 원본 payload byte는 포함하지 않는다.

    Raises:
        ValueError: 발견 항목이 누락되거나 ID, locator 불변식이 깨진 경우.

    Example:
        ``compileCatalog(census)`` 뒤 `coverage.coverageRatio`는 1.0이다.
    """
    discovery = census.discovery
    privateByRepo = {repo.repoId: repo.private for repo in discovery.pinnedRepositories}
    resources: list[CatalogResource] = []
    objects: list[CatalogObject] = []
    evidence: list[CatalogEvidence] = []

    for item in discovery.hfFiles:
        oid = _digestOrMetadata(
            item.oid,
            (item.repoId, item.revision, item.path, item.size, item.formatKind),
        )
        resourceId, resourceVersionId = hfFileIds(item.repoId, item.path, item.revision, oid)
        locatorItems = [
            ("repo", item.repoId),
            ("revision", item.revision),
            ("path", item.path),
            ("oid", item.oid or oid),
        ]
        if item.lfsSha256:
            locatorItems.append(("lfsSha256", item.lfsSha256))
        locator = tuple(locatorItems)
        status = "DISCOVERED" if item.state is DiscoveryState.CLASSIFIED else item.state.value
        resource = CatalogResource(
            resourceId=resourceId,
            resourceVersionId=resourceVersionId,
            resourceKind="HF_FILE",
            label=item.path,
            namespace=item.repoId,
            sourceKind="HF_FILE",
            sourceRef=item.repoId,
            sourceRevision=item.revision,
            locator=locator,
            contentSelector=(),
            contentDigest=item.lfsSha256 or oid,
            mediaType=_MEDIA_TYPE.get(item.formatKind),
            schemaFingerprint=None,
            byteSize=item.size if item.size >= 0 else None,
            rowCount=None,
            visibility=_visibility(privateByRepo.get(item.repoId)),
            licenseRef=None,
            status=status,
            discoveredAt=census.observedAtUtc,
            observedAt=census.observedAtUtc,
            gapReason=item.formatKind if item.state is DiscoveryState.UNSUPPORTED_FORMAT else None,
            attributes=(("formatKind", item.formatKind),),
        )
        obj, proof = _triplet(
            resource,
            objectKind=_objectKind(item.formatKind),
            label=item.path,
            observedAt=census.observedAtUtc,
        )
        resources.append(resource)
        objects.append(obj)
        evidence.append(proof)

    blogRevision = discovery.blogCensus.digest
    for post in discovery.blogCensus.posts:
        resourceId, resourceVersionId = blogPostIds("dartlab/blog", post.relativePath, post.contentDigest)
        locator = (
            ("repository", "dartlab"),
            ("revision", blogRevision),
            ("path", f"blog/{post.relativePath}"),
            ("contentDigest", post.contentDigest),
        )
        resource = CatalogResource(
            resourceId=resourceId,
            resourceVersionId=resourceVersionId,
            resourceKind="BLOG_POST",
            label=post.title or post.slug,
            namespace="dartlab/blog",
            sourceKind="GIT_BLOG",
            sourceRef="dartlab/blog",
            sourceRevision=blogRevision,
            locator=locator,
            contentSelector=(),
            contentDigest=post.contentDigest,
            mediaType="text/markdown",
            schemaFingerprint=post.frontmatterDigest,
            byteSize=None,
            rowCount=None,
            visibility=Visibility.PUBLIC,
            licenseRef=_OWNED_CONTENT_LICENSE,
            status="STRUCTURED",
            discoveredAt=census.observedAtUtc,
            observedAt=census.observedAtUtc,
            attributes=(
                ("category", post.category),
                ("slug", post.slug),
                ("publishedAt", post.publishedAt or ""),
                ("youtubeId", post.youtubeId or ""),
                ("headingCount", str(post.headingCount)),
                ("tableRowCount", str(post.tableRowCount)),
                ("codeBlockCount", str(post.codeBlockCount)),
                ("paragraphCount", str(post.paragraphCount)),
                ("imageRefs", json.dumps(post.imageRefs, ensure_ascii=False, separators=(",", ":"))),
                ("linkRefs", json.dumps(post.linkRefs, ensure_ascii=False, separators=(",", ":"))),
            ),
        )
        obj, proof = _triplet(
            resource,
            objectKind="BLOG_POST",
            label=post.title or post.slug,
            observedAt=census.observedAtUtc,
        )
        resources.append(resource)
        objects.append(obj)
        evidence.append(proof)

    companionRevision = discovery.companionCensus.digest
    for item in discovery.companionCensus.records:
        resourceId = logicalId("blog-companion", (item.relativePath,))
        resourceVersionId = versionId(resourceId, (item.contentDigest,))
        locator = (
            ("repository", "dartlab"),
            ("revision", companionRevision),
            ("path", f"blog/{item.relativePath}"),
            ("ownerPath", f"blog/{item.ownerPath}"),
        )
        status = "UNSUPPORTED_FORMAT" if item.kind == "UNCLASSIFIED_COMPANION" else "DISCOVERED"
        resource = CatalogResource(
            resourceId=resourceId,
            resourceVersionId=resourceVersionId,
            resourceKind="BLOG_COMPANION",
            label=item.relativePath,
            namespace="dartlab/blog",
            sourceKind="GIT_BLOG",
            sourceRef="dartlab/blog",
            sourceRevision=companionRevision,
            locator=locator,
            contentSelector=(),
            contentDigest=item.contentDigest,
            mediaType=None,
            schemaFingerprint=None,
            byteSize=None,
            rowCount=None,
            visibility=Visibility.LOCAL,
            licenseRef=_OWNED_CONTENT_LICENSE,
            status=status,
            discoveredAt=census.observedAtUtc,
            observedAt=census.observedAtUtc,
            gapReason=item.kind if status == "UNSUPPORTED_FORMAT" else None,
            attributes=(("companionKind", item.kind),),
        )
        obj, proof = _triplet(
            resource,
            objectKind="DOCUMENT",
            label=item.relativePath,
            observedAt=census.observedAtUtc,
        )
        resources.append(resource)
        objects.append(obj)
        evidence.append(proof)

    podcastRevision = discovery.podcastCensus.digest
    for episode in discovery.podcastCensus.episodes:
        resourceId = logicalId("podcast-episode", (episode.episodeId, episode.relativePath))
        resourceVersionId = versionId(resourceId, (episode.metadataDigest,))
        locator = (
            ("repository", "dartlab"),
            ("revision", podcastRevision),
            ("path", f"blog/{episode.relativePath}"),
            ("episodeId", episode.episodeId),
        )
        resource = CatalogResource(
            resourceId=resourceId,
            resourceVersionId=resourceVersionId,
            resourceKind="PODCAST_EPISODE",
            label=episode.title or episode.episodeId,
            namespace="dartlab/blog",
            sourceKind="GIT_BLOG",
            sourceRef="dartlab/blog",
            sourceRevision=podcastRevision,
            locator=locator,
            contentSelector=(),
            contentDigest=episode.metadataDigest,
            mediaType="application/yaml",
            schemaFingerprint=None,
            byteSize=None,
            rowCount=None,
            visibility=Visibility.PUBLIC,
            licenseRef=_OWNED_CONTENT_LICENSE,
            status="STRUCTURED" if episode.hasEpisodeMetadata else "PARTIAL",
            discoveredAt=census.observedAtUtc,
            observedAt=census.observedAtUtc,
            gapReason=None if episode.hasEpisodeMetadata else "EPISODE_METADATA_MISSING",
            attributes=(
                ("youtubeId", episode.youtubeId or ""),
                ("hasEpisodeMetadata", str(episode.hasEpisodeMetadata).lower()),
                ("hasPublishedReceipt", str(episode.hasPublishedReceipt).lower()),
                ("hasScript", str(episode.hasScript).lower()),
            ),
        )
        obj, proof = _triplet(
            resource,
            objectKind="VIDEO_SEGMENT" if episode.youtubeId else "DOCUMENT",
            label=episode.title or episode.episodeId,
            observedAt=census.observedAtUtc,
        )
        resources.append(resource)
        objects.append(obj)
        evidence.append(proof)

    capabilityRevision = discovery.capabilityCensus.digest
    capabilityIds = set(discovery.capabilityCensus.runtimeIds)
    capabilityIds.update(record.recordId for record in discovery.capabilityCensus.registryRecords)
    runtimeIds = set(discovery.capabilityCensus.runtimeIds)
    registryById = {record.recordId: record for record in discovery.capabilityCensus.registryRecords}
    for capabilityId in sorted(capabilityIds):
        resourceId = logicalId("capability", (capabilityId,))
        resourceVersionId = versionId(resourceId, (capabilityRevision,))
        registryRecord = registryById.get(capabilityId)
        locator = (("catalogDigest", capabilityRevision), ("capabilityId", capabilityId))
        resource = CatalogResource(
            resourceId=resourceId,
            resourceVersionId=resourceVersionId,
            resourceKind="CAPABILITY",
            label=capabilityId,
            namespace="dartlab/capabilities",
            sourceKind="RUNTIME_CAPABILITY",
            sourceRef="dartlab/capabilities",
            sourceRevision=capabilityRevision,
            locator=locator,
            contentSelector=(),
            contentDigest=capabilityRevision,
            mediaType="application/vnd.dartlab.capability+json",
            schemaFingerprint=None,
            byteSize=None,
            rowCount=None,
            visibility=Visibility.LOCAL,
            licenseRef=None,
            status="DISCOVERED",
            discoveredAt=census.observedAtUtc,
            observedAt=census.observedAtUtc,
            attributes=(
                ("runtimePresent", str(capabilityId in runtimeIds).lower()),
                ("registryOwner", registryRecord.owner if registryRecord else ""),
                ("registrySourceKind", registryRecord.sourceKind if registryRecord else ""),
                ("hidden", str(registryRecord.hidden).lower() if registryRecord else "false"),
            ),
        )
        obj, proof = _triplet(
            resource,
            objectKind="CAPABILITY",
            label=capabilityId,
            observedAt=census.observedAtUtc,
        )
        resources.append(resource)
        objects.append(obj)
        evidence.append(proof)

    releaseRevision = canonicalDigest(discovery.releaseDeclarations)
    for declaration in discovery.releaseDeclarations:
        resourceId = logicalId("release-declaration", (declaration.releaseId,))
        resourceVersionId = versionId(resourceId, (releaseRevision, declaration))
        locator = (
            ("releaseId", declaration.releaseId),
            ("repo", declaration.repoId),
            ("prefix", declaration.prefix),
        )
        resource = CatalogResource(
            resourceId=resourceId,
            resourceVersionId=resourceVersionId,
            resourceKind="RELEASE_DECLARATION",
            label=declaration.releaseId,
            namespace="dartlab/releases",
            sourceKind="RUNTIME_CONFIG",
            sourceRef="dartlab/dataConfig",
            sourceRevision=releaseRevision,
            locator=locator,
            contentSelector=(),
            contentDigest=canonicalDigest(declaration),
            mediaType="application/vnd.dartlab.release+json",
            schemaFingerprint=None,
            byteSize=None,
            rowCount=None,
            visibility=Visibility.PUBLIC if declaration.public else Visibility.PRIVATE,
            licenseRef=_OWNED_METADATA_LICENSE,
            status="DISCOVERED",
            discoveredAt=census.observedAtUtc,
            observedAt=census.observedAtUtc,
            attributes=(("ipcMirror", str(declaration.ipcMirror).lower()),),
        )
        obj, proof = _triplet(
            resource,
            objectKind="DATASET",
            label=declaration.releaseId,
            observedAt=census.observedAtUtc,
        )
        resources.append(resource)
        objects.append(obj)
        evidence.append(proof)

    mediaRevision = discovery.mediaCensus.digest
    for record in discovery.mediaCensus.records:
        resourceId = logicalId("media-catalog-record", (record.recordKind, record.recordKey))
        resourceVersionId = versionId(
            resourceId,
            (mediaRevision, record.metadataDigest, record.targetRef, record.relatedRefs),
        )
        locator = (
            ("catalog", "media/catalog.json"),
            ("recordKind", record.recordKind),
            ("recordKey", record.recordKey),
        )
        resource = CatalogResource(
            resourceId=resourceId,
            resourceVersionId=resourceVersionId,
            resourceKind="MEDIA_CATALOG_RECORD",
            label=record.recordKey,
            namespace="dartlab/media/catalog",
            sourceKind="GIT_MEDIA_CATALOG",
            sourceRef="dartlab/media/catalog.json",
            sourceRevision=mediaRevision,
            locator=locator,
            contentSelector=(),
            contentDigest=record.metadataDigest,
            mediaType="application/json",
            schemaFingerprint=None,
            byteSize=None,
            rowCount=None,
            visibility=Visibility.PUBLIC,
            licenseRef=_OWNED_METADATA_LICENSE,
            status="STRUCTURED",
            discoveredAt=census.observedAtUtc,
            observedAt=census.observedAtUtc,
            attributes=(
                ("targetRef", record.targetRef or ""),
                ("relatedRefs", json.dumps(record.relatedRefs, ensure_ascii=False, separators=(",", ":"))),
            ),
        )
        obj, proof = _triplet(
            resource,
            objectKind="MEDIA" if record.recordKind in {"OBJECT", "ALIAS"} else "COLLECTION",
            label=record.recordKey,
            observedAt=census.observedAtUtc,
        )
        resources.append(resource)
        objects.append(obj)
        evidence.append(proof)

    resources.sort(key=lambda item: (item.resourceId, item.resourceVersionId))
    objects.sort(key=lambda item: item.objectId)
    evidence.sort(key=lambda item: item.evidenceId)
    logicalDuplicates = _duplicateCount(item.resourceId for item in resources)
    versionDuplicates = _duplicateCount(item.resourceVersionId for item in resources)
    missingLocators = sum(not item.locator for item in resources)
    discoveredCount = (
        len(discovery.hfFiles)
        + len(discovery.blogCensus.posts)
        + len(discovery.companionCensus.records)
        + len(discovery.podcastCensus.episodes)
        + len(capabilityIds)
        + len(discovery.releaseDeclarations)
        + len(discovery.mediaCensus.records)
    )
    coverage = CatalogCoverage(
        discoveredCount=discoveredCount,
        resourceCount=len(resources),
        objectCount=len(objects),
        evidenceCount=len(evidence),
        sourcePayloadCopies=0,
        duplicateLogicalIds=logicalDuplicates,
        duplicateVersionIds=versionDuplicates,
        missingLocatorCount=missingLocators,
        coverageRatio=len(resources) / discoveredCount if discoveredCount else 1.0,
    )
    if (
        coverage.coverageRatio != 1.0
        or logicalDuplicates
        or versionDuplicates
        or missingLocators
        or len(objects) != len(resources)
        or len(evidence) != len(resources)
    ):
        raise ValueError(f"catalog coverage invariant failure: {coverage}")
    resourceTuple = tuple(resources)
    objectTuple = tuple(objects)
    evidenceTuple = tuple(evidence)
    digest = _catalogDigest(
        censusSnapshotDigest=census.snapshotDigest,
        resources=resourceTuple,
        objects=objectTuple,
        evidence=evidenceTuple,
        coverage=coverage,
    )
    state = CatalogState(
        schemaVersion=CATALOG_SCHEMA_VERSION,
        censusSnapshotDigest=census.snapshotDigest,
        resources=resourceTuple,
        objects=objectTuple,
        evidence=evidenceTuple,
        coverage=coverage,
        digest=digest,
    )
    return state


def attachIdentityRecords(
    catalog: CatalogState,
    records: Iterable[IdentityEvidence],
) -> CatalogState:
    """U1 organization identity를 row locator가 보존된 catalog object로 결합한다."""
    resources = list(catalog.resources)
    objects = list(catalog.objects)
    evidence = list(catalog.evidence)
    identityCount = 0
    entityIds = {item.objectId for item in objects}
    for record in records:
        if record.entityId in entityIds:
            raise ValueError(f"identity entity collision: {record.entityId}")
        entityIds.add(record.entityId)
        identityCount += 1
        resourceId = logicalId("identity-row", (record.sourceRef, record.rowLocator))
        resourceVersionId = versionId(resourceId, (record.sourceRevision,))
        locator = (
            ("sourceRef", record.sourceRef),
            ("sourceRevision", record.sourceRevision),
            ("rowLocator", record.rowLocator),
        )
        contentDigest = canonicalDigest(record)
        attributes = (
            ("jurisdiction", record.jurisdiction),
            ("canonicalNamespace", record.canonicalIdentifier.namespace),
            ("canonicalValue", record.canonicalIdentifier.value),
            (
                "aliases",
                json.dumps(
                    [
                        {
                            "namespace": alias.namespace,
                            "value": alias.value,
                            "validFrom": alias.validFrom,
                            "validTo": alias.validTo,
                            "evidenceRef": alias.sourceEvidenceRef,
                            "confidence": alias.confidence,
                        }
                        for alias in record.aliases
                    ],
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
        )
        resource = CatalogResource(
            resourceId=resourceId,
            resourceVersionId=resourceVersionId,
            resourceKind="IDENTITY_ROW",
            label=record.legalName,
            namespace=record.sourceRef,
            sourceKind="IDENTITY_AUTHORITY",
            sourceRef=record.sourceRef,
            sourceRevision=record.sourceRevision,
            locator=locator,
            contentSelector=(("rowLocator", record.rowLocator),),
            contentDigest=contentDigest,
            mediaType="application/vnd.dartlab.identity+json",
            schemaFingerprint=canonicalDigest(("organization", "identity-v1")),
            byteSize=None,
            rowCount=1,
            visibility=Visibility.LOCAL,
            licenseRef=None,
            status="VERIFIED",
            discoveredAt=record.observedAt,
            observedAt=record.observedAt,
            attributes=attributes,
        )
        aliases = tuple(sorted(f"{item.namespace}:{item.value}" for item in record.aliases))
        identifierRefs = tuple(
            sorted(
                {
                    f"{record.canonicalIdentifier.namespace}:{record.canonicalIdentifier.value}",
                    *aliases,
                }
            )
        )
        canonicalIdentifierRef = f"{record.canonicalIdentifier.namespace}:{record.canonicalIdentifier.value}"
        obj = _catalogObject(
            resource,
            objectId=record.entityId,
            objectKind="ORGANIZATION",
            canonicalLabel=record.legalName,
            aliases=aliases,
            identifierRefs=identifierRefs,
            verificationState=VerificationState.VERIFIED,
            attributes=(
                ("jurisdiction", record.jurisdiction),
                ("canonicalIdentifier", canonicalIdentifierRef),
            ),
        )
        proof = CatalogEvidence(
            evidenceId=logicalId("catalog-evidence", (record.entityId, resourceVersionId, locator)),
            objectId=record.entityId,
            resourceVersionId=resourceVersionId,
            sourceKind="IDENTITY_AUTHORITY",
            sourceRef=record.sourceRef,
            sourceRevision=record.sourceRevision,
            locator=locator,
            selector=(("rowLocator", record.rowLocator),),
            contentDigest=contentDigest,
            retrievedAt=record.observedAt,
            visibility=Visibility.LOCAL,
            licenseRef=None,
            quoteDigest=None,
        )
        resources.append(resource)
        objects.append(obj)
        evidence.append(proof)
    resources.sort(key=lambda item: (item.resourceId, item.resourceVersionId))
    objects.sort(key=lambda item: item.objectId)
    evidence.sort(key=lambda item: item.evidenceId)
    coverage = CatalogCoverage(
        discoveredCount=catalog.coverage.discoveredCount + identityCount,
        resourceCount=len(resources),
        objectCount=len(objects),
        evidenceCount=len(evidence),
        sourcePayloadCopies=0,
        duplicateLogicalIds=_duplicateCount(item.resourceId for item in resources),
        duplicateVersionIds=_duplicateCount(item.resourceVersionId for item in resources),
        missingLocatorCount=sum(not item.locator for item in resources),
        coverageRatio=len(resources) / (catalog.coverage.discoveredCount + identityCount)
        if catalog.coverage.discoveredCount + identityCount
        else 1.0,
    )
    if (
        coverage.coverageRatio != 1.0
        or coverage.duplicateLogicalIds
        or coverage.duplicateVersionIds
        or coverage.missingLocatorCount
    ):
        raise ValueError(f"identity catalog coverage invariant failure: {coverage}")
    resourceTuple = tuple(resources)
    objectTuple = tuple(objects)
    evidenceTuple = tuple(evidence)
    return CatalogState(
        schemaVersion=catalog.schemaVersion,
        censusSnapshotDigest=catalog.censusSnapshotDigest,
        resources=resourceTuple,
        objects=objectTuple,
        evidence=evidenceTuple,
        coverage=coverage,
        digest=_catalogDigest(
            censusSnapshotDigest=catalog.censusSnapshotDigest,
            resources=resourceTuple,
            objects=objectTuple,
            evidence=evidenceTuple,
            coverage=coverage,
        ),
    )


def attachCapabilityRegistry(
    catalog: CatalogState,
    registry: "UniverseCapabilityRegistry",
) -> CatalogState:
    """U2 candidate classification과 exact schema를 U3 capability object에 결박한다."""
    capabilityByCandidate = {item.candidateId: item for item in registry.capabilities}
    resources = []
    replacedVersionByOld = {}
    for resource in catalog.resources:
        if resource.resourceKind != "CAPABILITY":
            resources.append(resource)
            continue
        candidateId = dict(resource.locator)["capabilityId"]
        capability = capabilityByCandidate.pop(candidateId, None)
        if capability is None:
            raise ValueError(f"U2 registry에서 capability 누락: {candidateId}")
        descriptor = capability.schemaDescriptor
        descriptorDigest = canonicalDigest(descriptor) if descriptor is not None else None
        newVersionId = versionId(
            resource.resourceId,
            (
                registry.registryDigest,
                capability.sourceRevision,
                capability.sourceDigest,
                descriptorDigest,
                capability.status,
            ),
        )
        visibility = (
            Visibility(capability.visibility)
            if capability.visibility in {item.value for item in Visibility}
            else Visibility.LOCAL
        )
        if visibility is Visibility.PUBLIC and resource.licenseRef is None:
            visibility = Visibility.LOCAL
        attributes = {
            **dict(resource.attributes),
            "apiRef": capability.apiRef,
            "engine": capability.engine or "",
            "axis": capability.axis or "",
            "targetScope": capability.targetScope,
            "runtimeBoundary": capability.runtimeBoundary,
            "determinism": capability.determinism,
            "seedPolicy": capability.seedPolicy,
            "costClass": capability.costClass,
            "memoryClass": capability.memoryClass,
            "timeoutMs": str(capability.timeoutMs),
            "retryPolicy": capability.retryPolicy,
            "cachePolicy": capability.cachePolicy,
            "concurrencyClass": capability.concurrencyClass,
            "maturity": capability.maturity,
            "declaredVisibility": capability.visibility,
            "effectiveVisibility": visibility.value,
            "eligible": str(capability.eligible).lower(),
            "gapReasons": json.dumps(capability.gapReasons, ensure_ascii=False, separators=(",", ":")),
            "schemaDescriptorId": descriptor.descriptorId if descriptor else "",
            "argsSchema": json.dumps(
                descriptor.argsSchema if descriptor else None,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            "outputSchema": json.dumps(
                descriptor.outputSchema if descriptor else None,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        }
        updated = CatalogResource(
            resourceId=resource.resourceId,
            resourceVersionId=newVersionId,
            resourceKind=resource.resourceKind,
            label=resource.label,
            namespace=resource.namespace,
            sourceKind="CAPABILITY_REGISTRY",
            sourceRef=capability.apiRef,
            sourceRevision=capability.sourceRevision,
            locator=resource.locator
            + (
                ("apiRef", capability.apiRef),
                ("engine", capability.engine or ""),
                ("axis", capability.axis or ""),
            ),
            contentSelector=resource.contentSelector,
            contentDigest=capability.sourceDigest,
            mediaType=resource.mediaType,
            schemaFingerprint=descriptorDigest,
            byteSize=None,
            rowCount=None,
            visibility=visibility,
            licenseRef=resource.licenseRef,
            status=capability.status,
            discoveredAt=resource.discoveredAt,
            observedAt=resource.observedAt,
            gapReason="|".join(capability.gapReasons) or None,
            attributes=tuple(sorted(attributes.items())),
        )
        resources.append(updated)
        replacedVersionByOld[resource.resourceVersionId] = updated
    if capabilityByCandidate:
        raise ValueError(f"U3 catalog에서 capability 누락: {sorted(capabilityByCandidate)[0]}")

    objects = []
    evidence = []
    evidenceByObject = {item.objectId: item for item in catalog.evidence}
    for obj in catalog.objects:
        if len(obj.resourceRefs) != 1:
            raise ValueError(f"U3 capability object resource cardinality invalid: {obj.objectId}")
        replacement = replacedVersionByOld.get(obj.resourceRefs[0])
        if replacement is None:
            objects.append(obj)
            evidence.append(evidenceByObject[obj.objectId])
            continue
        updatedObject = _catalogObject(
            replacement,
            objectId=obj.objectId,
            objectKind=obj.objectKind,
            canonicalLabel=obj.canonicalLabel,
            aliases=obj.aliases,
            identifierRefs=obj.identifierRefs,
            epistemicClass=obj.epistemicClass,
            verificationState=_verificationState(replacement.status),
            validTime=obj.validTime,
            attributes=obj.attributes,
        )
        updatedEvidence = CatalogEvidence(
            evidenceId=logicalId(
                "catalog-evidence",
                (updatedObject.objectId, replacement.resourceVersionId, replacement.locator),
            ),
            objectId=updatedObject.objectId,
            resourceVersionId=replacement.resourceVersionId,
            sourceKind=replacement.sourceKind,
            sourceRef=replacement.sourceRef,
            sourceRevision=replacement.sourceRevision,
            locator=replacement.locator,
            selector=replacement.contentSelector,
            contentDigest=replacement.contentDigest,
            retrievedAt=evidenceByObject[obj.objectId].retrievedAt,
            visibility=replacement.visibility,
            licenseRef=replacement.licenseRef,
            quoteDigest=evidenceByObject[obj.objectId].quoteDigest,
        )
        objects.append(updatedObject)
        evidence.append(updatedEvidence)
    resources.sort(key=lambda item: (item.resourceId, item.resourceVersionId))
    objects.sort(key=lambda item: item.objectId)
    evidence.sort(key=lambda item: item.evidenceId)
    coverage = CatalogCoverage(
        discoveredCount=catalog.coverage.discoveredCount,
        resourceCount=len(resources),
        objectCount=len(objects),
        evidenceCount=len(evidence),
        sourcePayloadCopies=0,
        duplicateLogicalIds=_duplicateCount(item.resourceId for item in resources),
        duplicateVersionIds=_duplicateCount(item.resourceVersionId for item in resources),
        missingLocatorCount=sum(not item.locator for item in resources),
        coverageRatio=len(resources) / catalog.coverage.discoveredCount if catalog.coverage.discoveredCount else 1.0,
    )
    if (
        coverage.coverageRatio != 1.0
        or coverage.duplicateLogicalIds
        or coverage.duplicateVersionIds
        or coverage.missingLocatorCount
    ):
        raise ValueError(f"capability catalog coverage invariant failure: {coverage}")
    resourceTuple = tuple(resources)
    objectTuple = tuple(objects)
    evidenceTuple = tuple(evidence)
    return CatalogState(
        schemaVersion=catalog.schemaVersion,
        censusSnapshotDigest=catalog.censusSnapshotDigest,
        resources=resourceTuple,
        objects=objectTuple,
        evidence=evidenceTuple,
        coverage=coverage,
        digest=_catalogDigest(
            censusSnapshotDigest=catalog.censusSnapshotDigest,
            resources=resourceTuple,
            objects=objectTuple,
            evidence=evidenceTuple,
            coverage=coverage,
        ),
    )
