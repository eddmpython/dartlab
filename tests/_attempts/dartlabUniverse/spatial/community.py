"""전체 Universe object를 하나의 계층형 의미 community 후보로 분할한다."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import pairwise

from ..catalog.models import CatalogObject, CatalogResource, CatalogState
from ..contracts import VerificationState, Visibility
from ..temporal import parseInstant
from .contracts import ProjectionRequest
from .digest import spatialPackedDigest


@dataclass(frozen=True, slots=True)
class CommunityCandidate:
    level: int
    semanticKey: str
    parentSemanticKey: str | None
    memberObjectIds: tuple[str, ...]
    memberImportance: tuple[tuple[str, int], ...]
    memberDigest: str


@dataclass(frozen=True, slots=True)
class CommunityCandidates:
    objects: tuple[CatalogObject, ...]
    candidates: tuple[CommunityCandidate, ...]
    homeSemanticKeyByObject: tuple[tuple[str, str], ...]
    digest: str


_FAMILY_BY_KIND = {
    "ORGANIZATION": "ENTITY",
    "SECURITY": "ENTITY",
    "TABLE": "DATA",
    "FILE": "DATA",
    "DATASET": "DATA",
    "DOCUMENT": "KNOWLEDGE",
    "BLOG_POST": "KNOWLEDGE",
    "MEDIA": "MEDIA",
    "VIDEO_SEGMENT": "MEDIA",
    "COLLECTION": "MEDIA",
    "CAPABILITY": "CAPABILITY",
}

_IMPORTANCE_BY_KIND = {
    "ORGANIZATION": 120,
    "BLOG_POST": 110,
    "CAPABILITY": 100,
    "DATASET": 90,
    "TABLE": 70,
    "DOCUMENT": 60,
    "MEDIA": 50,
    "COLLECTION": 45,
    "VIDEO_SEGMENT": 45,
    "FILE": 30,
}

_IMPORTANCE_BY_VERIFICATION = {
    VerificationState.VERIFIED: 30,
    VerificationState.STRUCTURED: 20,
    VerificationState.ADDRESSABLE: 10,
}


@lru_cache(maxsize=16_384)
def _parseInstant(value: str):
    return parseInstant(value)


def clearCommunityRuntimeCaches() -> None:
    _parseInstant.cache_clear()


def objectImportance(obj: CatalogObject) -> int:
    """좌표와 대표 object 선정에 쓰는 source byte 독립 중요도다."""
    kindBase = _IMPORTANCE_BY_KIND.get(obj.objectKind, 20)
    verification = _IMPORTANCE_BY_VERIFICATION.get(obj.verificationState, 0)
    return kindBase + verification + min(20, len(obj.identifierRefs) * 2 + len(obj.aliases))


def _timeVisible(obj: CatalogObject, request: ProjectionRequest, *, validAt, knownAt) -> bool:
    start = _parseInstant(obj.validTime.start) if obj.validTime.start else None
    end = _parseInstant(obj.validTime.end) if obj.validTime.end else None
    known = _parseInstant(obj.systemTime.knownAt)
    retracted = _parseInstant(obj.systemTime.retractedAt) if obj.systemTime.retractedAt else None
    return (
        obj.visibility in request.allowedVisibility
        and (start is None or start <= validAt)
        and (end is None or validAt < end)
        and known <= knownAt
        and (retracted is None or knownAt < retracted)
        and obj.verificationState not in {VerificationState.RETRACTED, VerificationState.TOMBSTONED}
    )


def _semanticToken(obj: CatalogObject, resource: CatalogResource) -> str:
    if obj.objectKind == "ORGANIZATION":
        attributes = dict(obj.attributes)
        jurisdiction = attributes.get("jurisdiction", "GLOBAL").upper()
        return f"organization:{jurisdiction}"
    if obj.objectKind == "CAPABILITY":
        return f"capability:{obj.canonicalLabel.partition('.')[0].casefold()}"
    locator = dict(resource.locator)
    path = locator.get("path") or locator.get("ownerPath") or locator.get("rowLocator") or ""
    parts = tuple(item.casefold() for item in path.replace("\\", "/").split("/") if item)
    if parts and parts[0] in {"dart", "edgar", "news", "blog", "media"}:
        parts = parts[1:]
    semantic = parts[0] if parts else resource.resourceKind.casefold()
    if semantic.isdigit() or len(semantic) > 32:
        semantic = resource.resourceKind.casefold()
    return f"{obj.objectKind.casefold()}:{semantic}"


def _validateRequest(request: ProjectionRequest) -> None:
    budget = request.budget
    if (
        not request.snapshotId
        or not request.projectionVersion
        or not request.allowedVisibility
        or request.generation < 1
        or budget.rootHalfExtentQ < 10_000
        or budget.clusterHashBits < 4
        or budget.clusterHashBits > 12
        or budget.maxNodesPerTile < 1
        or budget.maxTileBytes < 1
    ):
        raise ValueError("projection request 또는 budget이 잘못됨")
    if any(not isinstance(item, Visibility) for item in request.allowedVisibility):
        raise ValueError("projection visibility가 잘못됨")
    parseInstant(request.validAt)
    parseInstant(request.knownAt)


def buildCommunityCandidates(catalog: CatalogState, request: ProjectionRequest) -> CommunityCandidates:
    """Source를 우주 경계로 쓰지 않는 semantic family와 stable shard 후보를 만든다."""
    _validateRequest(request)
    validAt = parseInstant(request.validAt)
    knownAt = parseInstant(request.knownAt)
    resourceByVersion = {item.resourceVersionId: item for item in catalog.resources}
    scope = frozenset(request.objectScope)
    objects = tuple(
        item
        for item in catalog.objects
        if _timeVisible(item, request, validAt=validAt, knownAt=knownAt)
        and (not scope or item.objectKind in scope or item.objectId in scope)
    )
    if not objects:
        raise ValueError("projection object scope가 비어 있음")
    objectIds = tuple(item.objectId for item in objects)
    if any(left >= right for left, right in pairwise(objectIds)):
        raise ValueError("projection catalog object가 stable ID 순서가 아님")
    importanceByObject = {item.objectId: objectImportance(item) for item in objects}
    membersByKey: dict[tuple[int, str, str | None], list[str]] = defaultdict(list)
    homeByObject = {}
    rootKey = "L0:UNIVERSE"
    for obj in objects:
        resource = resourceByVersion[obj.resourceRefs[0]]
        family = _FAMILY_BY_KIND.get(obj.objectKind, "OTHER")
        familyKey = f"L1:{family}"
        semantic = _semanticToken(obj, resource)
        familyShardBits = request.budget.clusterHashBits + 1 if family == "ENTITY" else request.budget.clusterHashBits
        familyShardBits = familyShardBits if family == "DATA" or family == "ENTITY" else 4
        shardValue = int(obj.objectId.rsplit(":", 1)[-1][:4], 16)
        shard = f"{shardValue & ((1 << familyShardBits) - 1):03x}"
        clusterKey = f"L2:{family}:{semantic}:{shard}"
        membersByKey[(0, rootKey, None)].append(obj.objectId)
        membersByKey[(1, familyKey, rootKey)].append(obj.objectId)
        membersByKey[(2, clusterKey, familyKey)].append(obj.objectId)
        homeByObject[obj.objectId] = clusterKey
    candidates = []
    for (level, key, parentKey), memberIds in sorted(membersByKey.items()):
        ordered = tuple(memberIds)
        importance = tuple((item, importanceByObject[item]) for item in ordered)
        candidates.append(
            CommunityCandidate(
                level=level,
                semanticKey=key,
                parentSemanticKey=parentKey,
                memberObjectIds=ordered,
                memberImportance=importance,
                memberDigest=spatialPackedDigest("COMMUNITY_MEMBERS", ordered),
            )
        )
    orderedHome = tuple(homeByObject.items())
    digest = spatialPackedDigest(
        "COMMUNITY_CANDIDATES",
        tuple((item.objectId, item.objectVersionId) for item in objects),
        tuple((item.level, item.semanticKey, item.parentSemanticKey, item.memberDigest) for item in candidates),
        orderedHome,
    )
    return CommunityCandidates(
        objects=objects,
        candidates=tuple(candidates),
        homeSemanticKeyByObject=orderedHome,
        digest=digest,
    )


def communityDistribution(candidates: CommunityCandidates) -> tuple[tuple[int, int, int], ...]:
    """level별 community 수와 member 합계를 진단한다."""
    counts = Counter(item.level for item in candidates.candidates)
    members = Counter()
    for item in candidates.candidates:
        members[item.level] += item.memberCount if hasattr(item, "memberCount") else len(item.memberObjectIds)
    return tuple((level, counts[level], members[level]) for level in sorted(counts))
