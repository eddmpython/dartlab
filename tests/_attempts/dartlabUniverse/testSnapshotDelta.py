"""Universe U3 deterministic snapshot과 tombstone delta를 검증한다."""

from __future__ import annotations

from dataclasses import replace

from tests._attempts.dartlabUniverse.canonical import canonicalDigest, canonicalJson
from tests._attempts.dartlabUniverse.catalog.compiler import compileCatalog
from tests._attempts.dartlabUniverse.catalog.delta import (
    applyDeltaResources,
    buildCatalogDelta,
    validateCatalogDelta,
)
from tests._attempts.dartlabUniverse.catalog.snapshot import (
    SnapshotResourceRef,
    _snapshotResourceJson,
    buildCatalogSnapshot,
    validateCatalogSnapshot,
)
from tests._attempts.dartlabUniverse.contracts import Visibility
from tests._attempts.dartlabUniverse.ids import versionId
from tests._attempts.dartlabUniverse.testCoverage import _fakeResult


def testSnapshotResourceFastEncodingPreservesCanonicalUnicodeAndFallback(monkeypatch):
    normalizedItem = SnapshotResourceRef(
        resourceId="du:v1:resource:한글",
        resourceVersionId="du:v1:resource-version:é",
        sourceKind="HF_FILE",
        sourceRef="조직/저장소",
        sourceRevision="revision",
        locator=(("path", "폴더/é.parquet"),),
        contentSelector=(("kind", "parquet"),),
        contentDigest="a" * 64,
        visibility=Visibility.PUBLIC,
        licenseRef="Apache-2.0",
        status="DESCRIBED",
        descriptorDigest="b" * 64,
    )
    decomposedItem = replace(
        normalizedItem,
        resourceVersionId="du:v1:resource-version:e\u0301",
        locator=(("path", "폴더/e\u0301.parquet"),),
    )
    escapedItem = replace(
        normalizedItem,
        sourceRef='repo/"quoted"\\line\n',
        locator=(("z", "two"), ("a", "one")),
        contentSelector=(("path", "a/b"), ("control", "\t")),
        visibility=Visibility.LOCAL,
        licenseRef=None,
        descriptorDigest=None,
    )

    assert _snapshotResourceJson(normalizedItem) == canonicalJson(normalizedItem)
    assert _snapshotResourceJson(decomposedItem) == canonicalJson(decomposedItem)
    assert _snapshotResourceJson(escapedItem) == canonicalJson(escapedItem)

    monkeypatch.setattr(
        "tests._attempts.dartlabUniverse.catalog.snapshot._RESOURCE_JSON_ENCODER",
        None,
    )
    assert _snapshotResourceJson(normalizedItem) == canonicalJson(normalizedItem)


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
    tamperedResource = replace(first.resources[0], contentDigest="invalid")
    tampered = replace(first, resources=(tamperedResource, *first.resources[1:]))
    tamperedIssues = validateCatalogSnapshot(tampered)
    assert "SNAPSHOT_ROOT_MISMATCH" in tamperedIssues
    assert "SNAPSHOT_RESOURCE_INTEGRITY_INVALID" in tamperedIssues


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
