"""Universe U3 full catalog와 in-memory projection을 검증한다."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests._attempts.dartlabUniverse.catalog.compiler import (
    attachCapabilityRegistry,
    attachIdentityRecords,
    compileCatalog,
)
from tests._attempts.dartlabUniverse.catalog.models import (
    CATALOG_OBJECT_SCHEMA_VERSION,
    catalogObjectVersionId,
)
from tests._attempts.dartlabUniverse.catalog.store import InMemoryCatalog, catalogArrowTables
from tests._attempts.dartlabUniverse.contracts import EpistemicClass, VerificationState, Visibility
from tests._attempts.dartlabUniverse.execution.registry import buildCapabilityRegistry
from tests._attempts.dartlabUniverse.identity.ledger import AliasRecord, IdentifierRef, IdentityEvidence
from tests._attempts.dartlabUniverse.ids import dartOrganizationId, logicalId
from tests._attempts.dartlabUniverse.testCoverage import _fakeResult


def testFullDiscoveryCompilesToTraceableCatalog():
    census = _fakeResult()
    catalog = compileCatalog(census)

    expected = (
        len(census.discovery.hfFiles)
        + len(census.discovery.blogCensus.posts)
        + len(census.discovery.companionCensus.records)
        + len(census.discovery.podcastCensus.episodes)
        + len(census.discovery.releaseDeclarations)
        + len(census.discovery.mediaCensus.records)
        + len(
            set(census.discovery.capabilityCensus.runtimeIds)
            | {item.recordId for item in census.discovery.capabilityCensus.registryRecords}
        )
    )
    assert catalog.coverage.discoveredCount == expected
    assert catalog.coverage.resourceCount == expected
    assert catalog.coverage.objectCount == expected
    assert catalog.coverage.evidenceCount == expected
    assert catalog.coverage.coverageRatio == 1.0
    assert catalog.coverage.sourcePayloadCopies == 0
    assert catalog.coverage.duplicateLogicalIds == 0
    assert catalog.coverage.duplicateVersionIds == 0
    assert catalog.coverage.missingLocatorCount == 0
    assert all(item.sourceRevision and item.locator and item.contentDigest for item in catalog.resources)
    assert all(item.label and item.namespace and item.discoveredAt and item.observedAt for item in catalog.resources)
    assert all(item.visibility is not Visibility.PUBLIC or item.licenseRef for item in catalog.resources)
    assert all(item.schemaVersion == CATALOG_OBJECT_SCHEMA_VERSION for item in catalog.objects)
    assert all(item.objectVersionId and item.canonicalLabel and item.resourceRefs for item in catalog.objects)


def testCatalogKeepsGitObjectAddressAndUsesLfsPayloadAsContentDigest():
    census = _fakeResult()
    source = census.discovery.hfFiles[0]
    payloadDigest = "f" * 64
    changedFile = replace(source, lfsSha256=payloadDigest)
    discovery = replace(
        census.discovery,
        hfFiles=tuple(changedFile if item is source else item for item in census.discovery.hfFiles),
    )
    catalog = compileCatalog(replace(census, discovery=discovery))
    resource = next(item for item in catalog.resources if dict(item.locator).get("path") == source.path)

    assert dict(resource.locator)["oid"] == source.oid
    assert dict(resource.locator)["lfsSha256"] == payloadDigest
    assert resource.contentDigest == payloadDigest
    assert all(item.epistemicClass is EpistemicClass.OBSERVED for item in catalog.objects)
    assert all(item.systemTime.knownAt for item in catalog.objects)


def testCatalogArrowAndDuckDbAreRuntimeOnly():
    catalog = compileCatalog(_fakeResult())
    tables = catalogArrowTables(catalog, allowedVisibility=frozenset(Visibility))

    assert tables["resources"].num_rows == len(catalog.resources)
    assert tables["objects"].num_rows == len(catalog.objects)
    assert tables["evidence"].num_rows == len(catalog.evidence)
    with InMemoryCatalog(catalog) as store:
        counts = store.connection.execute(
            "SELECT (SELECT count(*) FROM resources), (SELECT count(*) FROM objects), (SELECT count(*) FROM evidence)"
        ).fetchone()
        databaseRows = store.connection.execute("PRAGMA database_list").fetchall()
        allowed = frozenset({Visibility.PUBLIC, Visibility.LOCAL, Visibility.PRIVATE})
        resource = store.resourceByVersion(catalog.resources[0].resourceVersionId, allowedVisibility=allowed)
        detail = store.objectDetail(catalog.objects[0].objectId, allowedVisibility=allowed)
    assert counts == (len(catalog.resources), len(catalog.objects), len(catalog.evidence))
    assert all(row[2] in {None, "", ":memory:"} for row in databaseRows)
    assert resource is not None and resource["resourceVersionId"] == catalog.resources[0].resourceVersionId
    assert detail is not None and detail["evidenceLocator"] == detail["resourceLocator"]
    assert detail["evidenceSelector"] == detail["contentSelector"]
    assert detail["evidenceLicenseRef"] == detail["licenseRef"]
    assert len(detail["resources"]) == 1
    assert len(detail["evidence"]) == 1

    publicTables = catalogArrowTables(catalog, allowedVisibility=frozenset({Visibility.PUBLIC}))
    assert set(publicTables["resources"].column("visibility").to_pylist()) <= {Visibility.PUBLIC.value}
    assert set(publicTables["objects"].column("visibility").to_pylist()) <= {Visibility.PUBLIC.value}
    assert set(publicTables["evidence"].column("visibility").to_pylist()) <= {Visibility.PUBLIC.value}


def testPrivateCatalogObjectIsInvisibleToPublicLookup():
    catalog = compileCatalog(_fakeResult())
    privateObject = next(item for item in catalog.objects if item.visibility is Visibility.PRIVATE)

    with InMemoryCatalog(catalog) as store:
        hidden = store.objectDetail(
            privateObject.objectId,
            allowedVisibility=frozenset({Visibility.PUBLIC}),
        )
        visible = store.objectDetail(
            privateObject.objectId,
            allowedVisibility=frozenset({Visibility.PRIVATE}),
        )

    assert hidden is None
    assert visible is not None


def testObjectDetailReturnsEveryResourceEvidencePath():
    catalog = compileCatalog(_fakeResult())
    candidates = [item for item in catalog.objects if item.visibility is Visibility.LOCAL]
    first, second = candidates[:2]
    refs = tuple(sorted((*first.resourceRefs, *second.resourceRefs)))
    merged = replace(
        first,
        resourceRefs=refs,
        objectVersionId=catalogObjectVersionId(
            objectId=first.objectId,
            objectKind=first.objectKind,
            canonicalLabel=first.canonicalLabel,
            aliases=first.aliases,
            identifierRefs=first.identifierRefs,
            resourceRefs=refs,
            epistemicClass=first.epistemicClass,
            verificationState=first.verificationState,
            validTime=first.validTime,
            attributes=first.attributes,
        ),
    )
    secondEvidence = next(item for item in catalog.evidence if item.objectId == second.objectId)
    reboundEvidence = replace(
        secondEvidence,
        evidenceId=logicalId(
            "catalog-evidence",
            (first.objectId, secondEvidence.resourceVersionId, secondEvidence.locator),
        ),
        objectId=first.objectId,
    )
    mergedCatalog = replace(
        catalog,
        objects=tuple(
            merged if item.objectId == first.objectId else item for item in catalog.objects if item != second
        ),
        evidence=tuple(
            sorted(
                (reboundEvidence if item.objectId == second.objectId else item for item in catalog.evidence),
                key=lambda item: item.evidenceId,
            )
        ),
    )

    with InMemoryCatalog(mergedCatalog) as store:
        detail = store.objectDetail(first.objectId, allowedVisibility=frozenset({Visibility.LOCAL}))

    assert detail is not None
    assert {item["resourceVersionId"] for item in detail["resources"]} == set(refs)
    assert {item["resourceVersionId"] for item in detail["evidence"]} == set(refs)


def testObjectDetailRejectsUnboundedResourceFanout():
    catalog = compileCatalog(_fakeResult())
    publicObject = next(item for item in catalog.objects if item.visibility is Visibility.PUBLIC)
    resourceRefs = tuple(item.resourceVersionId for item in catalog.resources if item.visibility is Visibility.PUBLIC)[
        :1001
    ]
    assert len(resourceRefs) == 1001
    mutated = replace(
        catalog,
        objects=tuple(
            replace(publicObject, resourceRefs=resourceRefs) if item.objectId == publicObject.objectId else item
            for item in catalog.objects
        ),
    )

    with InMemoryCatalog(mutated) as store:
        with pytest.raises(ValueError, match="resource budget"):
            store.objectDetail(
                publicObject.objectId,
                allowedVisibility=frozenset({Visibility.PUBLIC}),
            )


def testPublicObjectMutationCannotLeakPrivateJoinedResource():
    catalog = compileCatalog(_fakeResult())
    privateObject = next(item for item in catalog.objects if item.visibility is Visibility.PRIVATE)
    mutatedObjects = tuple(
        replace(item, visibility=Visibility.PUBLIC) if item.objectId == privateObject.objectId else item
        for item in catalog.objects
    )
    mutated = replace(catalog, objects=mutatedObjects)

    with InMemoryCatalog(mutated) as store:
        hidden = store.objectDetail(
            privateObject.objectId,
            allowedVisibility=frozenset({Visibility.PUBLIC}),
        )

    assert hidden is None

    publicObject = next(item for item in catalog.objects if item.visibility is Visibility.PUBLIC)
    hiddenObjectCatalog = replace(
        catalog,
        objects=tuple(
            replace(item, visibility=Visibility.PRIVATE) if item.objectId == publicObject.objectId else item
            for item in catalog.objects
        ),
    )
    publicTables = catalogArrowTables(
        hiddenObjectCatalog,
        allowedVisibility=frozenset({Visibility.PUBLIC}),
    )
    assert publicObject.objectId not in set(publicTables["objects"].column("objectId").to_pylist())
    assert publicObject.objectId not in set(publicTables["evidence"].column("objectId").to_pylist())


def testUnsupportedDiscoveryRemainsVisibleAsGap():
    catalog = compileCatalog(_fakeResult())
    resource = next(item for item in catalog.resources if dict(item.locator).get("path", "").endswith(".mystery"))

    assert resource.status == "UNSUPPORTED_FORMAT"
    assert resource.gapReason == "UNSUPPORTED:.mystery"


def testIdentityRecordsBecomeOrganizationObjectsWithAliasEvidence():
    catalog = compileCatalog(_fakeResult())
    entityId = dartOrganizationId("00126380")
    evidenceRef = "du:v1:identity-evidence:" + "a" * 64
    identity = IdentityEvidence(
        entityId=entityId,
        jurisdiction="KR",
        canonicalIdentifier=IdentifierRef("DART_CORP_CODE", "00126380"),
        legalName="삼성전자",
        aliases=(AliasRecord("KR_STOCK_CODE", "005930", None, None, evidenceRef),),
        sourceRef="DART_CORP_CODE_PARQUET",
        sourceRevision="b" * 64,
        rowLocator="corp_code=00126380",
        observedAt="2026-07-19T00:00:00Z",
    )

    expanded = attachIdentityRecords(catalog, (identity,))
    obj = next(item for item in expanded.objects if item.objectId == entityId)
    resource = next(item for item in expanded.resources if item.resourceVersionId == obj.resourceRefs[0])

    assert obj.objectKind == "ORGANIZATION"
    assert obj.canonicalLabel == "삼성전자"
    assert obj.aliases == ("KR_STOCK_CODE:005930",)
    assert obj.identifierRefs == ("DART_CORP_CODE:00126380", "KR_STOCK_CODE:005930")
    assert obj.verificationState is VerificationState.VERIFIED
    assert dict(resource.locator)["rowLocator"] == "corp_code=00126380"
    assert "005930" in dict(resource.attributes)["aliases"]
    assert expanded.coverage.coverageRatio == 1.0
    assert expanded.coverage.sourcePayloadCopies == 0
    assert resource.visibility is Visibility.LOCAL


def testU2CapabilitySchemasAreBoundIntoCatalogWithoutInventedAxis():
    census = _fakeResult()
    catalog = compileCatalog(census)
    registry = buildCapabilityRegistry(census.discovery.capabilityCensus)

    expanded = attachCapabilityRegistry(catalog, registry)
    capabilityResources = tuple(item for item in expanded.resources if item.resourceKind == "CAPABILITY")
    candidateIds = {dict(item.locator)["capabilityId"] for item in capabilityResources}

    assert candidateIds == {item.candidateId for item in registry.capabilities}
    assert len(capabilityResources) == registry.discoveredCandidateCount
    assert sum(dict(item.attributes)["eligible"] == "true" for item in capabilityResources) == (
        registry.eligibleCallableCount
    )
    assert all(item.schemaFingerprint for item in capabilityResources if dict(item.attributes)["eligible"] == "true")
    assert expanded.coverage.coverageRatio == 1.0
