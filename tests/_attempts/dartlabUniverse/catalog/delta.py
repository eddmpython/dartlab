"""Catalog snapshot 사이 add, change, delete와 tombstone 계약."""

from __future__ import annotations

from dataclasses import dataclass

from ..canonical import canonicalDigest
from .snapshot import CatalogSnapshot, SnapshotResourceRef


@dataclass(frozen=True, slots=True)
class CatalogChange:
    changeKind: str
    resourceId: str
    previous: SnapshotResourceRef | None
    current: SnapshotResourceRef | None
    tombstoneDigest: str | None


@dataclass(frozen=True, slots=True)
class CatalogDelta:
    schemaVersion: str
    previousSnapshotId: str
    currentSnapshotId: str
    changes: tuple[CatalogChange, ...]
    addedCount: int
    changedCount: int
    deletedCount: int
    digest: str


def buildCatalogDelta(previous: CatalogSnapshot, current: CatalogSnapshot) -> CatalogDelta:
    """Logical resource ID를 기준으로 source revision 변화를 완전 분류한다."""
    if current.previousSnapshotId != previous.snapshotId:
        raise ValueError("current snapshot previousSnapshotId mismatch")
    before = {item.resourceId: item for item in previous.resources}
    after = {item.resourceId: item for item in current.resources}
    if len(before) != len(previous.resources) or len(after) != len(current.resources):
        raise ValueError("snapshot resource logical ID duplicate")
    changes = []
    for resourceId in sorted(set(before) | set(after)):
        old = before.get(resourceId)
        new = after.get(resourceId)
        if old is None:
            changes.append(CatalogChange("ADDED", resourceId, None, new, None))
        elif new is None:
            tombstone = canonicalDigest(
                {
                    "resourceId": resourceId,
                    "previousVersionId": old.resourceVersionId,
                    "deletedInSnapshot": current.snapshotId,
                    "status": "TOMBSTONED",
                }
            )
            changes.append(CatalogChange("DELETED", resourceId, old, None, tombstone))
        elif old != new:
            changes.append(CatalogChange("CHANGED", resourceId, old, new, None))
    ordered = tuple(changes)
    base = {
        "schemaVersion": "du-catalog-delta-v2",
        "previousSnapshotId": previous.snapshotId,
        "currentSnapshotId": current.snapshotId,
        "changes": ordered,
    }
    return CatalogDelta(
        schemaVersion="du-catalog-delta-v2",
        previousSnapshotId=previous.snapshotId,
        currentSnapshotId=current.snapshotId,
        changes=ordered,
        addedCount=sum(item.changeKind == "ADDED" for item in ordered),
        changedCount=sum(item.changeKind == "CHANGED" for item in ordered),
        deletedCount=sum(item.changeKind == "DELETED" for item in ordered),
        digest=canonicalDigest(base),
    )


def validateCatalogDelta(delta: CatalogDelta) -> tuple[str, ...]:
    """Delta digest, count, tombstone, logical resource cardinality를 검증한다."""
    issues = []
    if delta.schemaVersion != "du-catalog-delta-v2":
        issues.append("DELTA_SCHEMA_VERSION_MISMATCH")
    if not delta.previousSnapshotId or not delta.currentSnapshotId:
        issues.append("DELTA_SNAPSHOT_ID_MISSING")
    if delta.previousSnapshotId == delta.currentSnapshotId:
        issues.append("DELTA_SNAPSHOT_ID_REUSED")
    if len({item.resourceId for item in delta.changes}) != len(delta.changes):
        issues.append("DELTA_RESOURCE_ID_DUPLICATE")
    if delta.changes != tuple(sorted(delta.changes, key=lambda item: item.resourceId)):
        issues.append("DELTA_CHANGE_ORDER_MISMATCH")
    expectedCounts = (
        sum(item.changeKind == "ADDED" for item in delta.changes),
        sum(item.changeKind == "CHANGED" for item in delta.changes),
        sum(item.changeKind == "DELETED" for item in delta.changes),
    )
    if expectedCounts != (delta.addedCount, delta.changedCount, delta.deletedCount):
        issues.append("DELTA_COUNT_MISMATCH")
    for change in delta.changes:
        if change.changeKind == "ADDED":
            if change.previous is not None or change.current is None or change.tombstoneDigest is not None:
                issues.append("DELTA_ADDED_SHAPE_INVALID")
            elif change.current.resourceId != change.resourceId:
                issues.append("DELTA_RESOURCE_SUBJECT_MISMATCH")
        elif change.changeKind == "CHANGED":
            if change.previous is None or change.current is None or change.tombstoneDigest is not None:
                issues.append("DELTA_CHANGED_SHAPE_INVALID")
            elif change.previous.resourceId != change.resourceId or change.current.resourceId != change.resourceId:
                issues.append("DELTA_RESOURCE_SUBJECT_MISMATCH")
        elif change.changeKind == "DELETED":
            if change.previous is None or change.current is not None or not change.tombstoneDigest:
                issues.append("DELTA_DELETED_SHAPE_INVALID")
                continue
            expectedTombstone = canonicalDigest(
                {
                    "resourceId": change.resourceId,
                    "previousVersionId": change.previous.resourceVersionId,
                    "deletedInSnapshot": delta.currentSnapshotId,
                    "status": "TOMBSTONED",
                }
            )
            if change.previous.resourceId != change.resourceId:
                issues.append("DELTA_RESOURCE_SUBJECT_MISMATCH")
            if change.tombstoneDigest != expectedTombstone:
                issues.append("DELTA_TOMBSTONE_DIGEST_MISMATCH")
        else:
            issues.append("DELTA_CHANGE_KIND_INVALID")
    expectedDigest = canonicalDigest(
        {
            "schemaVersion": delta.schemaVersion,
            "previousSnapshotId": delta.previousSnapshotId,
            "currentSnapshotId": delta.currentSnapshotId,
            "changes": delta.changes,
        }
    )
    if delta.digest != expectedDigest:
        issues.append("DELTA_DIGEST_MISMATCH")
    return tuple(sorted(set(issues)))


def applyDeltaResources(
    previousResources: tuple[SnapshotResourceRef, ...],
    delta: CatalogDelta,
) -> tuple[SnapshotResourceRef, ...]:
    """Delta가 target resource set을 손실 없이 재구성하는지 검증할 때 사용한다."""
    current = {item.resourceId: item for item in previousResources}
    for change in delta.changes:
        if change.changeKind == "ADDED":
            if change.current is None or change.resourceId in current:
                raise ValueError("invalid ADDED change")
            current[change.resourceId] = change.current
        elif change.changeKind == "CHANGED":
            if change.previous != current.get(change.resourceId) or change.current is None:
                raise ValueError("invalid CHANGED change")
            current[change.resourceId] = change.current
        elif change.changeKind == "DELETED":
            if change.previous != current.get(change.resourceId) or not change.tombstoneDigest:
                raise ValueError("invalid DELETED change")
            del current[change.resourceId]
        else:
            raise ValueError(f"unknown change kind: {change.changeKind}")
    return tuple(sorted(current.values(), key=lambda item: (item.resourceId, item.resourceVersionId)))
