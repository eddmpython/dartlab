"""Projection byte determinism, incremental displacement, community continuity metric."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from ..canonical import canonicalDigest
from .contracts import ProjectionState


@dataclass(frozen=True, slots=True)
class ProjectionStabilityReport:
    passed: bool
    unchangedObjectCount: int
    coordinateDeterminism: float
    normalizedDisplacementP95: float
    clusterContinuity: float
    selectedObjectLossCount: int
    failureCodes: tuple[str, ...]
    digest: str


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * quantile) - 1))
    return ordered[index]


def evaluateProjectionStability(
    prior: ProjectionState,
    current: ProjectionState,
    *,
    selectedObjectIds: tuple[str, ...] = (),
) -> ProjectionStabilityReport:
    """Minor projection의 unchanged coordinate와 retained co-membership을 계산한다."""
    priorCoordinates = {item.objectId: item for item in prior.coordinates}
    currentCoordinates = {item.objectId: item for item in current.coordinates}
    unchanged = tuple(sorted(priorCoordinates.keys() & currentCoordinates.keys()))
    identical = sum(priorCoordinates[item].positionQ == currentCoordinates[item].positionQ for item in unchanged)
    displacement = []
    priorCommunity = {item.communityLogicalId: item for item in prior.communities if item.level == 2}
    currentCommunity = {item.communityLogicalId: item for item in current.communities if item.level == 2}
    clusterRadius = {}
    for communityId, community in priorCommunity.items():
        positions = [priorCoordinates[item].positionQ for item in community.memberObjectIds if item in priorCoordinates]
        if not positions:
            clusterRadius[communityId] = 1.0
            continue
        center = tuple(sum(value[index] for value in positions) / len(positions) for index in range(3))
        clusterRadius[communityId] = max(
            1.0,
            max(math.dist(position, center) for position in positions),
        )
    for objectId in unchanged:
        old = priorCoordinates[objectId]
        new = currentCoordinates[objectId]
        displacement.append(math.dist(old.positionQ, new.positionQ) / clusterRadius.get(old.clusterId, 1.0))
    priorPairs = 0
    retainedPairs = 0
    for communityId, old in priorCommunity.items():
        count = len(old.memberObjectIds)
        denominator = count * (count - 1) // 2 if count > 1 else count
        priorPairs += denominator
        new = currentCommunity.get(communityId)
        if new is None:
            continue
        shared = len(set(old.memberObjectIds) & set(new.memberObjectIds))
        retainedPairs += shared * (shared - 1) // 2 if shared > 1 else shared
    continuity = retainedPairs / priorPairs if priorPairs else 1.0
    selectedLoss = sum(item not in currentCoordinates for item in selectedObjectIds)
    determinism = identical / len(unchanged) if unchanged else 1.0
    p95 = _percentile(displacement, 0.95)
    failures = []
    if determinism != 1.0:
        failures.append("COORDINATE_DETERMINISM_FAILED")
    if p95 > 0.02:
        failures.append("NORMALIZED_DISPLACEMENT_P95_EXCEEDED")
    if continuity < 0.98:
        failures.append("CLUSTER_CONTINUITY_BELOW_THRESHOLD")
    if selectedLoss:
        failures.append("SELECTED_OBJECT_LOST")
    base = ProjectionStabilityReport(
        passed=not failures,
        unchangedObjectCount=len(unchanged),
        coordinateDeterminism=determinism,
        normalizedDisplacementP95=round(p95, 9),
        clusterContinuity=round(continuity, 9),
        selectedObjectLossCount=selectedLoss,
        failureCodes=tuple(sorted(failures)),
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))
