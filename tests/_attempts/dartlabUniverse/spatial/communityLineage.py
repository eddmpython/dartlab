"""Community overlap maximum matching과 split, merge, retirement lineage."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from scipy.optimize import linear_sum_assignment

from ..canonical import canonicalDigest
from ..ids import logicalId
from .community import CommunityCandidate
from .contracts import CommunityLineageEvent, CommunityVersion


def _overlap(old: CommunityVersion, new: CommunityCandidate) -> float:
    shared = len(set(old.memberObjectIds) & set(new.memberObjectIds))
    return shared / max(len(old.memberObjectIds), len(new.memberObjectIds)) if shared else 0.0


def _sharedImportance(old: CommunityVersion, new: CommunityCandidate) -> int:
    oldValues = dict(old.memberImportance)
    return sum(min(oldValues.get(item, 0), value) for item, value in new.memberImportance if item in oldValues)


def _maximumMatches(
    oldItems: tuple[CommunityVersion, ...],
    newItems: tuple[CommunityCandidate, ...],
) -> dict[int, int]:
    if not oldItems or not newItems:
        return {}
    weights = np.zeros((len(oldItems), len(newItems)), dtype=np.float64)
    lexicalScale = max(1, len(oldItems) * len(newItems))
    for oldIndex, old in enumerate(oldItems):
        for newIndex, new in enumerate(newItems):
            score = _overlap(old, new)
            if score < 0.80:
                continue
            sharedImportance = min(_sharedImportance(old, new), 1_000_000_000)
            lexicalPreference = (lexicalScale - (oldIndex * len(newItems) + newIndex)) / lexicalScale
            weights[oldIndex, newIndex] = score * 1_000_000 + sharedImportance * 1e-6 + lexicalPreference * 1e-9
    rows, columns = linear_sum_assignment(-weights)
    return {
        int(newIndex): int(oldIndex)
        for oldIndex, newIndex in zip(rows, columns, strict=True)
        if weights[oldIndex, newIndex] > 0
    }


def compileCommunityLineage(
    candidates: tuple[CommunityCandidate, ...],
    *,
    projectionVersion: str,
    priorCommunities: tuple[CommunityVersion, ...] = (),
) -> tuple[tuple[CommunityVersion, ...], tuple[CommunityLineageEvent, ...]]:
    """Level별 maximum-weight overlap으로 logical community ID를 계승한다."""
    priorByLevel = {}
    newByLevel = {}
    for item in priorCommunities:
        priorByLevel.setdefault(item.level, []).append(item)
    for item in candidates:
        newByLevel.setdefault(item.level, []).append(item)
    provisional = []
    events = []
    for level in sorted(newByLevel):
        oldItems = tuple(sorted(priorByLevel.get(level, ()), key=lambda item: item.communityLogicalId))
        newItems = tuple(sorted(newByLevel[level], key=lambda item: item.semanticKey))
        matches = _maximumMatches(oldItems, newItems)
        matchedOld = set(matches.values())
        for newIndex, new in enumerate(newItems):
            overlapping = tuple(
                sorted(
                    ((old, _overlap(old, new)) for old in oldItems if _overlap(old, new) >= 0.50),
                    key=lambda item: (-item[1], -_sharedImportance(item[0], new), item[0].communityLogicalId),
                )
            )
            if newIndex in matches:
                inherited = oldItems[matches[newIndex]]
                logical = inherited.communityLogicalId
                predecessors = tuple(item.communityLogicalId for item, _score in overlapping)
                kind = "MERGED_FROM" if len(predecessors) > 1 else "RETAINED"
            else:
                splitParents = tuple(
                    item.communityLogicalId
                    for item, _score in overlapping
                    if sum(_overlap(item, candidate) >= 0.50 for candidate in newItems) > 1
                )
                logical = logicalId("projection-community", ("du-spatial", level, new.memberDigest))
                predecessors = splitParents
                kind = "SPLIT_FROM" if splitParents else "NEW"
            versionId = logicalId(
                "projection-community-version",
                (logical, new.memberDigest, projectionVersion),
            )
            provisional.append(
                CommunityVersion(
                    communityLogicalId=logical,
                    communityVersionId=versionId,
                    level=level,
                    semanticKey=new.semanticKey,
                    parentCommunityLogicalId=new.parentSemanticKey,
                    memberDigest=new.memberDigest,
                    memberCount=len(new.memberObjectIds),
                    memberObjectIds=new.memberObjectIds,
                    memberImportance=new.memberImportance,
                    lineageKind=kind,
                    predecessorRefs=tuple(sorted(set(predecessors))),
                )
            )
            scores = tuple((item.communityLogicalId, logical, round(score, 9)) for item, score in overlapping)
            baseEvent = CommunityLineageEvent(kind, level, tuple(sorted(predecessors)), (logical,), scores, "")
            events.append(replace(baseEvent, digest=canonicalDigest(baseEvent)))
        for oldIndex, old in enumerate(oldItems):
            if oldIndex in matchedOld or any(old.communityLogicalId in item.predecessorRefs for item in provisional):
                continue
            baseEvent = CommunityLineageEvent("RETIRED", level, (old.communityLogicalId,), (), (), "")
            events.append(replace(baseEvent, digest=canonicalDigest(baseEvent)))
    logicalBySemantic = {item.semanticKey: item.communityLogicalId for item in provisional}
    resolved = tuple(
        replace(
            item,
            parentCommunityLogicalId=(
                logicalBySemantic.get(item.parentCommunityLogicalId, item.parentCommunityLogicalId)
                if item.parentCommunityLogicalId is not None
                else None
            ),
        )
        for item in provisional
    )
    if len({item.communityLogicalId for item in resolved}) != len(resolved):
        raise ValueError("community lineage logical ID collision")
    return (
        tuple(sorted(resolved, key=lambda item: (item.level, item.communityLogicalId))),
        tuple(sorted(events, key=lambda item: (item.level, item.eventKind, item.digest))),
    )
