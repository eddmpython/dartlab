"""지식 의미와 화면 공간을 분리하는 U3 relation taxonomy."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace

from ..canonical import canonicalDigest
from ..catalog.models import CatalogEvidence, CatalogObject, CatalogState
from ..contracts import EpistemicClass, SystemTime, TimeRange, VerificationState, Visibility
from ..ids import logicalId
from ..temporal import parseInstant

GRAPH_RELATION_SCHEMA_VERSION = "du-graph-relation-v3"


@dataclass(frozen=True, slots=True)
class RelationType:
    name: str
    directed: bool
    transitive: bool
    evidenceRequired: bool
    description: str


@dataclass(frozen=True, slots=True)
class RelationTaxonomy:
    schemaVersion: str
    types: tuple[RelationType, ...]
    version: str

    def get(self, name: str) -> RelationType | None:
        return next((item for item in self.types if item.name == name), None)


@dataclass(frozen=True, slots=True)
class GraphRelation:
    schemaVersion: str
    relationId: str
    fromRef: str
    relationType: str
    taxonomyVersion: str
    toRef: str
    direction: str
    statementRefs: tuple[str, ...]
    evidenceRefs: tuple[str, ...]
    epistemicClass: EpistemicClass
    derivationRef: str | None
    weight: float | None
    confidence: float | None
    validTime: TimeRange
    systemTime: SystemTime
    verificationState: VerificationState
    visibility: Visibility
    digest: str


def defaultRelationTaxonomy() -> RelationTaxonomy:
    """제품 의미 edge만 허용한다. 3D 거리와 군집은 포함하지 않는다."""
    definitions = (
        RelationType("AFFECTS", True, False, True, "한 객체가 다른 객체에 영향을 준다"),
        RelationType("ALIAS_OF", True, False, True, "identifier가 canonical object를 가리킨다"),
        RelationType("BLOG_ASSERTS_STATEMENT", True, False, True, "블로그가 특정 statement를 주장한다"),
        RelationType("CAPABILITY_ACCEPTS_OBJECT", True, False, True, "capability가 객체 kind를 입력으로 받는다"),
        RelationType("CITES", True, False, True, "문서 또는 statement가 근거를 인용한다"),
        RelationType("CONTAINS", True, False, False, "resource가 하위 구조를 포함한다"),
        RelationType("CONTRADICTS", True, False, True, "statement가 다른 statement와 충돌한다"),
        RelationType("CORRECTS", True, False, True, "새 statement가 이전 statement를 정정한다"),
        RelationType("DEPENDS_ON", True, False, True, "파생 결과가 입력에 의존한다"),
        RelationType("DERIVED_FROM", True, False, True, "결과가 source나 execution에서 파생된다"),
        RelationType("DESCRIBES", True, False, True, "문서나 statement가 대상을 설명한다"),
        RelationType("EXECUTED_BY", True, False, True, "result가 capability execution에서 생성됐다"),
        RelationType("EXECUTION_DERIVED_STATEMENT", True, False, True, "execution이 statement를 파생했다"),
        RelationType("FILE_DESCRIBES_ORGANIZATION", True, False, True, "file이 organization을 기술한다"),
        RelationType("FILED_BY", True, False, True, "filing이 organization에 의해 제출됐다"),
        RelationType("FILING_CONTAINS_SECTION", True, False, True, "filing이 section을 포함한다"),
        RelationType("ISSUED_BY", True, False, True, "security나 document가 organization에 의해 발행됐다"),
        RelationType("MEDIA_ILLUSTRATES_BLOCK", True, False, True, "media가 document block을 시각화한다"),
        RelationType("MEMBER_OF", True, False, True, "object가 collection 또는 classification에 속한다"),
        RelationType("ORGANIZATION_SUPPLIES", True, False, True, "organization이 다른 organization에 공급한다"),
        RelationType("PRODUCED", True, False, True, "execution이 output을 생성했다"),
        RelationType("REPORTS", True, False, True, "statement가 subject의 fact를 보고한다"),
        RelationType("SECURITY_ISSUED_BY", True, False, True, "security가 organization에 의해 발행됐다"),
        RelationType("SUPERSEDES", True, False, True, "새 version이나 statement가 이전 것을 대체한다"),
        RelationType("SUPPORTS", True, False, True, "evidence나 statement가 statement를 지지한다"),
        RelationType("TABLE_CONTAINS_CONCEPT", True, False, True, "table이 accounting concept를 포함한다"),
    )
    schemaVersion = "du-relation-taxonomy-v2"
    return RelationTaxonomy(
        schemaVersion=schemaVersion,
        types=definitions,
        version=canonicalDigest((schemaVersion, definitions)),
    )


def buildRelation(
    *,
    fromRef: str,
    relationType: str,
    toRef: str,
    taxonomy: RelationTaxonomy,
    direction: str | None = None,
    statementRefs: tuple[str, ...],
    evidenceRefs: tuple[str, ...],
    epistemicClass: EpistemicClass,
    derivationRef: str | None = None,
    weight: float | None = None,
    confidence: float | None = None,
    validTime: TimeRange,
    systemTime: SystemTime,
    verificationState: VerificationState,
    visibility: Visibility,
) -> GraphRelation:
    """Taxonomy, evidence, self-edge 불변식을 통과한 relation만 만든다."""
    relationSpec = taxonomy.get(relationType)
    if relationSpec is None:
        raise ValueError(f"taxonomy 밖 relation: {relationType}")
    if relationType in {"SPATIAL_NEAR", "CLUSTERED_WITH", "VISUALLY_SIMILAR"}:
        raise ValueError("공간 배치는 지식 relation이 아님")
    if not fromRef or not toRef or fromRef == toRef:
        raise ValueError("relation endpoint가 잘못됨")
    expectedDirection = "OUTBOUND" if relationSpec.directed else "UNDIRECTED"
    activeDirection = direction or expectedDirection
    if activeDirection != expectedDirection:
        raise ValueError(f"{relationType} relation direction이 taxonomy와 다름")
    if relationSpec.evidenceRequired and not (statementRefs or evidenceRefs):
        raise ValueError(f"{relationType} relation에는 근거가 필요함")
    if epistemicClass is EpistemicClass.OBSERVED and not evidenceRefs:
        raise ValueError("OBSERVED relation에는 evidence가 필요함")
    if epistemicClass in {EpistemicClass.DERIVED, EpistemicClass.INFERRED, EpistemicClass.SIMULATED}:
        if not derivationRef:
            raise ValueError("파생 relation에는 derivationRef가 필요함")
    if weight is not None and (isinstance(weight, bool) or not math.isfinite(weight) or weight < 0):
        raise ValueError("relation weight는 0 이상의 유한값이어야 함")
    if confidence is not None and (
        isinstance(confidence, bool) or not math.isfinite(confidence) or not 0 <= confidence <= 1
    ):
        raise ValueError("relation confidence는 0과 1 사이 유한값이어야 함")
    validStart = parseInstant(validTime.start) if validTime.start else None
    validEnd = parseInstant(validTime.end) if validTime.end else None
    if validStart is not None and validEnd is not None and validEnd <= validStart:
        raise ValueError("relation validTime은 비어 있지 않은 반개방 구간이어야 함")
    knownAt = parseInstant(systemTime.knownAt)
    for instantValue in (systemTime.observedAt, systemTime.ingestedAt):
        if instantValue:
            parseInstant(instantValue)
    if systemTime.retractedAt and parseInstant(systemTime.retractedAt) < knownAt:
        raise ValueError("relation retractedAt은 knownAt보다 이를 수 없음")
    if verificationState is VerificationState.RETRACTED and not systemTime.retractedAt:
        raise ValueError("RETRACTED relation에는 retractedAt이 필요함")
    if visibility is Visibility.PUBLIC and verificationState is VerificationState.UNRESOLVED:
        raise ValueError("UNRESOLVED relation은 공개할 수 없음")
    base = GraphRelation(
        schemaVersion=GRAPH_RELATION_SCHEMA_VERSION,
        relationId="",
        fromRef=fromRef,
        relationType=relationType,
        taxonomyVersion=taxonomy.version,
        toRef=toRef,
        direction=activeDirection,
        statementRefs=tuple(sorted(set(statementRefs))),
        evidenceRefs=tuple(sorted(set(evidenceRefs))),
        epistemicClass=epistemicClass,
        derivationRef=derivationRef,
        weight=weight,
        confidence=confidence,
        validTime=validTime,
        systemTime=systemTime,
        verificationState=verificationState,
        visibility=visibility,
        digest="",
    )
    digest = canonicalDigest(base)
    return replace(base, relationId=logicalId("relation", (digest,)), digest=digest)


def compileCatalogRelations(
    catalog: CatalogState,
    *,
    taxonomy: RelationTaxonomy | None = None,
) -> tuple[GraphRelation, ...]:
    """모든 catalog object를 원본 resource version에 evidence edge로 결박한다."""
    activeTaxonomy = taxonomy or defaultRelationTaxonomy()
    evidenceByObject: dict[str, list[CatalogEvidence]] = {}
    for evidence in catalog.evidence:
        evidenceByObject.setdefault(evidence.objectId, []).append(evidence)
    resourceByVersion = {item.resourceVersionId: item for item in catalog.resources}
    visibilityByRef = {
        **{item.objectId: item.visibility for item in catalog.objects},
        **{item.resourceVersionId: item.visibility for item in catalog.resources},
    }
    relations = []

    def primaryResourceRef(obj: CatalogObject) -> str:
        if not obj.resourceRefs:
            raise ValueError(f"U3 catalog object resource ref missing: {obj.objectId}")
        return obj.resourceRefs[0]

    def appendRelation(
        fromRef: str,
        relationType: str,
        toRef: str,
        evidenceObjectId: str,
        *,
        evidenceResourceRef: str | None = None,
    ) -> None:
        evidenceItems = tuple(
            item
            for item in evidenceByObject[evidenceObjectId]
            if evidenceResourceRef is None or item.resourceVersionId == evidenceResourceRef
        )
        if not evidenceItems:
            raise ValueError(f"relation evidence path 누락: {evidenceObjectId}")
        visibilityRank = {
            Visibility.PUBLIC: 0,
            Visibility.LOCAL: 1,
            Visibility.PRIVATE: 2,
            Visibility.RESTRICTED: 3,
            Visibility.UNKNOWN: 4,
        }
        visibility = max(
            (
                *(item.visibility for item in evidenceItems),
                visibilityByRef.get(fromRef, evidenceItems[0].visibility),
                visibilityByRef.get(toRef, evidenceItems[0].visibility),
            ),
            key=visibilityRank.__getitem__,
        )
        relations.append(
            buildRelation(
                fromRef=fromRef,
                relationType=relationType,
                toRef=toRef,
                taxonomy=activeTaxonomy,
                statementRefs=(),
                evidenceRefs=tuple(item.evidenceId for item in evidenceItems),
                epistemicClass=EpistemicClass.OBSERVED,
                validTime=TimeRange(),
                systemTime=SystemTime(max(item.retrievedAt for item in evidenceItems)),
                verificationState=VerificationState.ADDRESSABLE,
                visibility=visibility,
            )
        )

    for obj in catalog.objects:
        evidenceItems = evidenceByObject.get(obj.objectId)
        if evidenceItems is None:
            raise ValueError(f"object evidence path 누락: {obj.objectId}")
        for resourceRef in obj.resourceRefs:
            appendRelation(
                obj.objectId,
                "DERIVED_FROM",
                resourceRef,
                obj.objectId,
                evidenceResourceRef=resourceRef,
            )

    mediaRecords = {}
    mediaObjectByDigest = {}
    mediaDigestByPath = {}
    mediaAliasTarget = {}
    for obj in catalog.objects:
        resource = resourceByVersion[primaryResourceRef(obj)]
        if resource.resourceKind != "MEDIA_CATALOG_RECORD":
            continue
        locator = dict(resource.locator)
        kind = locator["recordKind"]
        key = locator["recordKey"]
        mediaRecords[(kind, key)] = obj
        attributes = dict(resource.attributes)
        if kind == "OBJECT":
            mediaObjectByDigest[key] = obj
            if attributes.get("targetRef"):
                mediaDigestByPath[attributes["targetRef"]] = key
        elif kind == "ALIAS":
            mediaAliasTarget[key] = attributes.get("targetRef", "")

    def resolveMedia(ref: str):
        digest = mediaAliasTarget.get(ref, ref if ref in mediaObjectByDigest else None)
        if digest is None:
            digest = mediaDigestByPath.get(ref)
        if digest is None and "/resolve/" in ref:
            remotePath = ref.split("/resolve/", 1)[1].split("/", 1)
            if len(remotePath) == 2:
                digest = mediaDigestByPath.get(remotePath[1])
        return mediaObjectByDigest.get(digest) if digest else None

    hfObjectByRepoPath = {}
    hfObjectsByPath: dict[str, list[CatalogObject]] = {}
    for obj in catalog.objects:
        resource = resourceByVersion[primaryResourceRef(obj)]
        if resource.resourceKind == "HF_FILE":
            locator = dict(resource.locator)
            hfObjectByRepoPath[(locator["repo"], locator["path"])] = obj
            hfObjectsByPath.setdefault(locator["path"], []).append(obj)

    for mediaObject in mediaObjectByDigest.values():
        resource = resourceByVersion[primaryResourceRef(mediaObject)]
        targetPath = dict(resource.attributes).get("targetRef", "")
        for hfObject in hfObjectsByPath.get(targetPath, ()):
            appendRelation(mediaObject.objectId, "DESCRIBES", hfObject.objectId, mediaObject.objectId)

    for alias, targetDigest in mediaAliasTarget.items():
        aliasObject = mediaRecords.get(("ALIAS", alias))
        targetObject = mediaObjectByDigest.get(targetDigest)
        if aliasObject is not None and targetObject is not None:
            appendRelation(aliasObject.objectId, "ALIAS_OF", targetObject.objectId, aliasObject.objectId)

    for (kind, _key), sourceObject in mediaRecords.items():
        if kind not in {"POST", "COLLECTION", "MANIFEST"}:
            continue
        resource = resourceByVersion[primaryResourceRef(sourceObject)]
        for ref in json.loads(dict(resource.attributes).get("relatedRefs", "[]")):
            targetObject = resolveMedia(str(ref))
            if targetObject is not None:
                appendRelation(sourceObject.objectId, "CONTAINS", targetObject.objectId, sourceObject.objectId)

    ownerByDirectory = {}
    for obj in catalog.objects:
        resource = resourceByVersion[primaryResourceRef(obj)]
        locator = dict(resource.locator)
        if resource.resourceKind == "BLOG_POST":
            ownerByDirectory[str(locator["path"]).rsplit("/", 1)[0]] = obj
        elif resource.resourceKind == "PODCAST_EPISODE":
            ownerByDirectory[str(locator["path"])] = obj
    for obj in catalog.objects:
        resource = resourceByVersion[primaryResourceRef(obj)]
        locator = dict(resource.locator)
        if resource.resourceKind == "BLOG_COMPANION":
            owner = ownerByDirectory.get(locator.get("ownerPath", ""))
            if owner is not None:
                appendRelation(owner.objectId, "CONTAINS", obj.objectId, owner.objectId)
        elif resource.resourceKind == "BLOG_POST":
            for ref in json.loads(dict(resource.attributes).get("imageRefs", "[]")):
                targetObject = resolveMedia(str(ref))
                if targetObject is not None:
                    appendRelation(obj.objectId, "CITES", targetObject.objectId, obj.objectId)

    for releaseObject in catalog.objects:
        releaseResource = resourceByVersion[primaryResourceRef(releaseObject)]
        if releaseResource.resourceKind != "RELEASE_DECLARATION":
            continue
        locator = dict(releaseResource.locator)
        repo = locator["repo"]
        prefix = locator["prefix"].rstrip("/")
        for (fileRepo, path), fileObject in hfObjectByRepoPath.items():
            if fileRepo == repo and (path == prefix or path.startswith(f"{prefix}/")):
                appendRelation(
                    releaseObject.objectId,
                    "CONTAINS",
                    fileObject.objectId,
                    releaseObject.objectId,
                )

    unique = {item.relationId: item for item in relations}
    return tuple(sorted(unique.values(), key=lambda item: item.relationId))
