"""Universe U3 deterministic snapshot과 tombstone delta를 검증한다."""

from __future__ import annotations

from dataclasses import replace

from tests._attempts.dartlabUniverse.canonical import canonicalDigest
from tests._attempts.dartlabUniverse.catalog.compiler import compileCatalog
from tests._attempts.dartlabUniverse.catalog.delta import (
    applyDeltaResources,
    buildCatalogDelta,
    validateCatalogDelta,
)
from tests._attempts.dartlabUniverse.catalog.snapshot import buildCatalogSnapshot, validateCatalogSnapshot
from tests._attempts.dartlabUniverse.ids import versionId
from tests._attempts.dartlabUniverse.testCoverage import _fakeResult


def testSameCatalogProducesSameRootIndependentOfCreatedAt():
    catalog = compileCatalog(_fakeResult())
    first = buildCatalogSnapshot(
        catalog,
        universeSnapshotId="du:v1:snapshot:" + "a" * 64,
        capabilityRegistryVersion="capability-v1",
        identityLedgerVersion="identity-v1",
        relationTaxonomyVersion="taxonomy-v1",
        createdAt="2026-07-19T00:00:00+00:00",
    )
    second = buildCatalogSnapshot(
        catalog,
        universeSnapshotId="du:v1:snapshot:" + "a" * 64,
        capabilityRegistryVersion="capability-v1",
        identityLedgerVersion="identity-v1",
        relationTaxonomyVersion="taxonomy-v1",
        createdAt="2026-07-20T00:00:00+00:00",
    )

    assert first.snapshotId == second.snapshotId
    assert first.rootInputsDigest == second.rootInputsDigest
    assert first.rootInputsDigest == canonicalDigest(
        {
            "schemaVersion": first.schemaVersion,
            "universeSnapshotId": first.universeSnapshotId,
            "catalogDigest": first.catalogDigest,
            "descriptorSetDigest": first.descriptorSetDigest,
            "recoverySetDigest": first.recoverySetDigest,
            "capabilityRegistryVersion": first.capabilityRegistryVersion,
            "identityLedgerVersion": first.identityLedgerVersion,
            "relationTaxonomyVersion": first.relationTaxonomyVersion,
            "resources": first.resources,
            "previousSnapshotId": first.previousSnapshotId,
        }
    )
    assert validateCatalogSnapshot(first) == ()
    assert "SNAPSHOT_CREATED_AT_INVALID" in validateCatalogSnapshot(replace(first, createdAt="invalid"))


def testDeltaCoversAddChangeDeleteAndRebuildsTarget():
    catalog = compileCatalog(_fakeResult())
    previous = buildCatalogSnapshot(
        catalog,
        universeSnapshotId="du:v1:snapshot:" + "a" * 64,
        capabilityRegistryVersion="capability-v1",
        identityLedgerVersion="identity-v1",
        relationTaxonomyVersion="taxonomy-v1",
    )
    resources = list(catalog.resources)
    removed = resources.pop(0)
    changed = resources[0]
    resources[0] = replace(
        changed,
        resourceVersionId=versionId(changed.resourceId, ("new-revision",)),
        sourceRevision="new-revision",
        contentDigest="f" * 64,
    )
    added = replace(
        removed,
        resourceId=removed.resourceId.replace("du:v1:", "du:v1:added-", 1),
        resourceVersionId=removed.resourceVersionId.replace("du:v1:", "du:v1:added-", 1),
    )
    resources.append(added)
    resources.sort(key=lambda item: (item.resourceId, item.resourceVersionId))
    currentCatalog = replace(catalog, resources=tuple(resources), digest="")
    currentCatalog = replace(currentCatalog, digest=canonicalDigest(currentCatalog))
    current = buildCatalogSnapshot(
        currentCatalog,
        universeSnapshotId="du:v1:snapshot:" + "b" * 64,
        capabilityRegistryVersion="capability-v1",
        identityLedgerVersion="identity-v1",
        relationTaxonomyVersion="taxonomy-v1",
        previousSnapshotId=previous.snapshotId,
    )
    delta = buildCatalogDelta(previous, current)

    assert (delta.addedCount, delta.changedCount, delta.deletedCount) == (1, 1, 1)
    assert validateCatalogDelta(delta) == ()
    assert applyDeltaResources(previous.resources, delta) == current.resources
    tombstone = next(item for item in delta.changes if item.changeKind == "DELETED")
    assert tombstone.previous == next(item for item in previous.resources if item.resourceId == removed.resourceId)
    assert tombstone.tombstoneDigest

    countMutation = replace(delta, addedCount=99)
    assert "DELTA_COUNT_MISMATCH" in validateCatalogDelta(countMutation)

    mutatedChanges = tuple(
        replace(item, tombstoneDigest="f" * 64) if item.changeKind == "DELETED" else item for item in delta.changes
    )
    tombstoneMutation = replace(delta, changes=mutatedChanges)
    issues = validateCatalogDelta(tombstoneMutation)
    assert "DELTA_TOMBSTONE_DIGEST_MISMATCH" in issues
    assert "DELTA_DIGEST_MISMATCH" in issues
