"""Right-handed Y-up 정수 Q 좌표를 만드는 deterministic 3D layout."""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from itertools import pairwise

from ..catalog.models import CatalogObject
from ..graph.relations import GraphRelation
from .community import objectImportance
from .contracts import CommunityVersion, LogicalCoordinate, ProjectionBudget, ProjectionState

_RADIUS_BY_KIND = {
    "ORGANIZATION": 24,
    "BLOG_POST": 22,
    "CAPABILITY": 20,
    "DATASET": 18,
    "TABLE": 14,
    "DOCUMENT": 12,
    "MEDIA": 12,
}

_COLLISION_SLOT_Q = 64
_MAX_NODE_RADIUS_Q = max(_RADIUS_BY_KIND.values()) + 4


def nodeRadiusQ(obj: CatalogObject) -> int:
    """Object byte와 kind만으로 안정적인 scene radius를 만든다."""
    kindBase = _RADIUS_BY_KIND.get(obj.objectKind, 10)
    jitter = int(obj.objectId.rsplit(":", 1)[-1][-2:], 16) % 5
    return kindBase + jitter


def _vector(identifier: str, radius: int) -> tuple[int, int, int]:
    payload = hashlib.sha256(identifier.encode("utf-8")).digest()
    x = int.from_bytes(payload[0:8], "big") - 2**63
    y = int.from_bytes(payload[8:16], "big") - 2**63
    z = int.from_bytes(payload[16:24], "big") - 2**63
    norm = math.sqrt(x * x + y * y + z * z)
    if norm == 0:
        return radius, 0, 0
    return int(round(x * radius / norm)), int(round(y * radius / norm)), int(round(z * radius / norm))


def _add(left: tuple[int, int, int], right: tuple[int, int, int]) -> tuple[int, int, int]:
    return left[0] + right[0], left[1] + right[1], left[2] + right[2]


def _clamp(position: tuple[int, int, int], halfExtent: int) -> tuple[int, int, int]:
    margin = 256
    limit = halfExtent - margin
    return tuple(max(-limit, min(limit, value)) for value in position)  # type: ignore[return-value]


def _snapToCollisionSlot(position: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(round(value / _COLLISION_SLOT_Q) * _COLLISION_SLOT_Q for value in position)  # type: ignore[return-value]


def communityAnchors(
    communities: tuple[CommunityVersion, ...],
    budget: ProjectionBudget,
) -> dict[str, tuple[int, int, int]]:
    """L1은 root sphere, L2는 L1 주변에 배치하고 lineage ID로 안정화한다."""
    anchors = {}
    root = next((item for item in communities if item.level == 0), None)
    if root is None:
        raise ValueError("root projection community가 없음")
    anchors[root.communityLogicalId] = (0, 0, 0)
    for community in (item for item in communities if item.level == 1):
        anchors[community.communityLogicalId] = _vector(
            f"L1:{community.communityLogicalId}",
            int(budget.rootHalfExtentQ * 0.52),
        )
    for community in (item for item in communities if item.level == 2):
        parent = anchors.get(community.parentCommunityLogicalId or "")
        if parent is None:
            raise ValueError("L2 parent community anchor가 없음")
        anchors[community.communityLogicalId] = _clamp(
            _add(parent, _vector(f"L2:{community.communityLogicalId}", int(budget.rootHalfExtentQ * 0.18))),
            budget.rootHalfExtentQ,
        )
    return anchors


class _CollisionIndex:
    def __init__(self) -> None:
        if _MAX_NODE_RADIUS_Q * 2 * 1.05 >= _COLLISION_SLOT_Q:
            raise ValueError("collision slot 간격이 최대 node 지름보다 작음")
        self.entries: dict[tuple[int, int, int], tuple[int, str]] = {}

    def collides(self, position: tuple[int, int, int], radius: int) -> bool:
        if radius > _MAX_NODE_RADIUS_Q or any(value % _COLLISION_SLOT_Q for value in position):
            raise ValueError("node radius 또는 coordinate quantization이 collision slot 계약을 위반함")
        return position in self.entries

    def add(self, position: tuple[int, int, int], radius: int, objectId: str) -> None:
        if self.collides(position, radius):
            raise ValueError(f"collision slot 중복 object={objectId}")
        self.entries[position] = (radius, objectId)


def _neighborBarycenter(
    objectId: str,
    relationsByObject: dict[str, list[GraphRelation]],
    priorByObject: dict[str, LogicalCoordinate],
) -> tuple[int, int, int] | None:
    values = []
    for relation in relationsByObject.get(objectId, ()):
        other = relation.toRef if relation.fromRef == objectId else relation.fromRef
        coordinate = priorByObject.get(other)
        if coordinate is not None:
            values.append(coordinate.positionQ)
    if not values:
        return None
    return tuple(round(sum(item[index] for item in values) / len(values)) for index in range(3))  # type: ignore[return-value]


def compileCoordinates(
    objects: tuple[CatalogObject, ...],
    relations: tuple[GraphRelation, ...],
    communities: tuple[CommunityVersion, ...],
    homeCommunityByObject: dict[str, str],
    *,
    budget: ProjectionBudget,
    seed: int,
    priorState: ProjectionState | None = None,
) -> tuple[LogicalCoordinate, ...]:
    """기존 object를 pin하고 신규 object만 barycenter 또는 ID jitter로 배치한다."""
    anchors = communityAnchors(communities, budget)
    priorByObject = {item.objectId: item for item in priorState.coordinates} if priorState else {}
    objectById = {item.objectId: item for item in objects}
    orderedObjectIds = tuple(objectById)
    if len(objectById) != len(objects) or any(left >= right for left, right in pairwise(orderedObjectIds)):
        raise ValueError("projection object 입력이 stable ID 순서가 아님")
    visibleIds = frozenset(objectById)
    relationsByObject: dict[str, list[GraphRelation]] = defaultdict(list)
    if priorByObject:
        for relation in relations:
            if relation.fromRef in visibleIds:
                relationsByObject[relation.fromRef].append(relation)
            if relation.toRef in visibleIds and relation.toRef != relation.fromRef:
                relationsByObject[relation.toRef].append(relation)
    collision = _CollisionIndex()
    coordinates = {}
    retainedIds = tuple(item for item in orderedObjectIds if item in priorByObject)
    for objectId in retainedIds:
        prior = priorByObject[objectId]
        radius = nodeRadiusQ(objectById[objectId])
        if any(abs(value) > budget.rootHalfExtentQ for value in prior.positionQ) or collision.collides(
            prior.positionQ, radius
        ):
            raise ValueError("prior projection coordinate가 bounds 또는 collision 계약을 위반함")
        coordinate = LogicalCoordinate(objectId, homeCommunityByObject[objectId], prior.positionQ, radius)
        coordinates[objectId] = coordinate
        collision.add(prior.positionQ, radius, objectId)
    for objectId in (item for item in orderedObjectIds if item not in priorByObject):
        obj = objectById[objectId]
        clusterId = homeCommunityByObject[objectId]
        anchor = anchors[clusterId]
        barycenter = _neighborBarycenter(objectId, relationsByObject, priorByObject) if priorByObject else None
        if barycenter is None:
            base = _add(anchor, _vector(f"NODE:{seed}:{objectId}", int(budget.rootHalfExtentQ * 0.075)))
        else:
            base = _add(barycenter, _vector(f"NEW:{seed}:{objectId}", 512))
        radius = nodeRadiusQ(obj)
        accepted = None
        for attempt in range(9):
            candidate = _clamp(
                base if attempt == 0 else _add(base, _vector(f"COLLISION:{seed}:{objectId}:{attempt}", attempt * 257)),
                budget.rootHalfExtentQ,
            )
            candidate = _snapToCollisionSlot(candidate)
            if not collision.collides(candidate, radius):
                accepted = candidate
                break
        if accepted is None:
            raise ValueError(f"PROJECTION_REJECTED collision object={objectId}")
        coordinate = LogicalCoordinate(objectId, clusterId, accepted, radius)
        coordinates[objectId] = coordinate
        collision.add(accepted, radius, objectId)
    if len(coordinates) != len(objects):
        raise ValueError("projection coordinate mapping이 완전하지 않음")
    if sum(item.positionQ[2] == 0 for item in coordinates.values()) / len(coordinates) >= 0.01:
        raise ValueError("projection z=0 node 비율이 1% 이상임")
    return tuple(coordinates[item] for item in orderedObjectIds)


def coordinateImportance(objects: tuple[CatalogObject, ...]) -> tuple[tuple[str, int], ...]:
    return tuple((item.objectId, objectImportance(item)) for item in sorted(objects, key=lambda value: value.objectId))
