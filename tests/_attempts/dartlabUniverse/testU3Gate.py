"""Universe U3 integrated catalog gate와 mutation failure를 검증한다."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests._attempts.dartlabUniverse.canonical import canonicalDigest
from tests._attempts.dartlabUniverse.catalog.compiler import attachCapabilityRegistry, compileCatalog
from tests._attempts.dartlabUniverse.catalog.descriptorCrawler import (
    DESCRIPTOR_SCHEMA_VERSION,
    ResourceDescriptor,
    descriptorFormatKind,
)
from tests._attempts.dartlabUniverse.catalog.snapshot import buildCatalogSnapshot
from tests._attempts.dartlabUniverse.contracts import (
    EpistemicClass,
    SystemTime,
    TimeRange,
    VerificationState,
    Visibility,
)
from tests._attempts.dartlabUniverse.execution.registry import buildCapabilityRegistry
from tests._attempts.dartlabUniverse.graph.relations import (
    buildRelation,
    compileCatalogRelations,
    defaultRelationTaxonomy,
)
from tests._attempts.dartlabUniverse.graph.statements import buildStatement
from tests._attempts.dartlabUniverse.testCoverage import _fakeResult
from tests._attempts.dartlabUniverse.u3Gate import recordRuntimeFailure
from tests._attempts.dartlabUniverse.validation.u3 import validateU3


def _descriptors(catalog):
    records = []
    for resource in catalog.resources:
        if resource.resourceKind != "HF_FILE":
            continue
        kind = descriptorFormatKind(resource)
        supported = kind != "UNSUPPORTED"
        base = ResourceDescriptor(
            descriptorId=canonicalDigest((resource.resourceVersionId, kind, DESCRIPTOR_SCHEMA_VERSION)),
            schemaVersion=DESCRIPTOR_SCHEMA_VERSION,
            resourceVersionId=resource.resourceVersionId,
            sourceRevision=resource.sourceRevision,
            formatKind=kind,
            status="DESCRIBED" if supported else "UNSUPPORTED_FORMAT",
            schemaFingerprint=canonicalDigest((kind, "schema")) if supported else None,
            rowCount=None,
            rowCountUnavailableReason="FIXTURE_METADATA_ONLY" if supported else "UNSUPPORTED_FORMAT",
            metadata=(
                (("fixture", "true"),)
                if supported
                else (
                    ("declaredFormatKind", dict(resource.attributes).get("formatKind", "UNSUPPORTED")),
                    ("reason", "NO_SAFE_DESCRIPTOR_PARSER"),
                    ("sourceMeaning", resource.resourceKind),
                )
            ),
            magicHex=None if supported else "00",
            rangeRequestCount=1,
            rangeBytesRead=16,
            responseDigest="f" * 64,
            errorCode=None,
            digest="",
        )
        records.append(replace(base, digest=canonicalDigest(base)))
    return tuple(sorted(records, key=lambda item: item.resourceVersionId))


@pytest.fixture(scope="module")
def gateFixture():
    census = _fakeResult()
    catalog = compileCatalog(census)
    registry = buildCapabilityRegistry(census.discovery.capabilityCensus)
    catalog = attachCapabilityRegistry(catalog, registry)
    descriptors = _descriptors(catalog)
    taxonomy = defaultRelationTaxonomy()
    snapshot = buildCatalogSnapshot(
        catalog,
        universeSnapshotId="du:v1:snapshot:" + "a" * 64,
        descriptors=descriptors,
        capabilityRegistryVersion=registry.registryDigest,
        identityLedgerVersion="identity-v1",
        relationTaxonomyVersion=taxonomy.version,
    )
    relations = compileCatalogRelations(catalog, taxonomy=taxonomy)
    return catalog, descriptors, snapshot, relations


def testU3PassesCompleteCatalogDescriptorAndEvidenceGraph(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    report = validateU3(
        catalog,
        descriptors,
        snapshot,
        statements=(),
        relations=relations,
        upstreamG1Passed=True,
        upstreamG2Passed=True,
        upstreamUniverseSnapshotId=snapshot.universeSnapshotId,
        upstreamCensusSnapshotDigest=catalog.censusSnapshotDigest,
        upstreamCapabilityRegistryVersion=snapshot.capabilityRegistryVersion,
        upstreamIdentityLedgerVersion=snapshot.identityLedgerVersion,
        upstreamRelationTaxonomyVersion=snapshot.relationTaxonomyVersion,
    )

    assert report.passed, report.failureCodes
    assert report.catalogCoverageRatio == 1.0
    assert report.descriptorCandidateCount == len(descriptors)
    assert report.descriptorTerminalCount == len(descriptors)
    assert report.descriptorEligibleCount == report.describedEligibleCount
    assert report.schemaFingerprintCoverageRatio == 1.0
    assert report.rowContractCoverageRatio == 1.0
    assert report.objectEvidenceCoverageRatio == 1.0
    assert report.catalogRelationCoverageRatio == 1.0
    assert report.statementProvenanceStatus == "NOT_APPLICABLE"
    assert report.sourcePayloadCopies == 0
    assert len(relations) > len(catalog.objects)
    assert any(item.relationType == "ALIAS_OF" for item in relations)
    assert any(item.relationType == "DESCRIBES" for item in relations)

    failed = recordRuntimeFailure(report, "PINNED_REVISION_VALIDATION_FAILED")
    assert not failed.passed
    assert failed.failureCodes == ("PINNED_REVISION_VALIDATION_FAILED",)
    assert failed.digest == canonicalDigest(replace(failed, digest=""))


def testU3RejectsUnknownStatementAndRelationEndpoints(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    evidence = next(item for item in catalog.evidence if item.visibility is Visibility.LOCAL)
    statement = buildStatement(
        subjectRef="unknown:subject",
        predicate="fixtureFact",
        value=1,
        valueType="integer",
        scope="entity",
        validTime=TimeRange(),
        systemTime=SystemTime(evidence.retrievedAt),
        epistemicClass=EpistemicClass.OBSERVED,
        verificationState=VerificationState.VERIFIED,
        evidenceRefs=(evidence.evidenceId,),
        evidenceById={evidence.evidenceId: evidence},
        visibility=Visibility.LOCAL,
    )
    relation = buildRelation(
        fromRef="unknown:source",
        relationType="DESCRIBES",
        toRef=evidence.objectId,
        taxonomy=defaultRelationTaxonomy(),
        statementRefs=(),
        evidenceRefs=(evidence.evidenceId,),
        epistemicClass=EpistemicClass.OBSERVED,
        validTime=TimeRange(),
        systemTime=SystemTime(evidence.retrievedAt),
        verificationState=VerificationState.VERIFIED,
        visibility=Visibility.LOCAL,
    )

    report = validateU3(
        catalog,
        descriptors,
        snapshot,
        statements=(statement,),
        relations=(*relations, relation),
        upstreamG1Passed=True,
        upstreamG2Passed=True,
        upstreamUniverseSnapshotId=snapshot.universeSnapshotId,
        upstreamCensusSnapshotDigest=catalog.censusSnapshotDigest,
        upstreamCapabilityRegistryVersion=snapshot.capabilityRegistryVersion,
        upstreamIdentityLedgerVersion=snapshot.identityLedgerVersion,
        upstreamRelationTaxonomyVersion=snapshot.relationTaxonomyVersion,
    )

    assert not report.passed
    assert "GRAPH_STATEMENT_ENDPOINT_BROKEN" in report.failureCodes
    assert "GRAPH_RELATION_ENDPOINT_BROKEN" in report.failureCodes


def testU3RejectsMissingDescriptorAndBrokenCatalogRelation(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    victim = catalog.objects[0]
    brokenRelations = tuple(
        item for item in relations if not (item.fromRef == victim.objectId and item.toRef == victim.resourceRefs[0])
    )
    report = validateU3(
        catalog,
        descriptors[1:],
        snapshot,
        statements=(),
        relations=brokenRelations,
        upstreamG1Passed=True,
        upstreamG2Passed=True,
        upstreamUniverseSnapshotId=snapshot.universeSnapshotId,
        upstreamCensusSnapshotDigest=catalog.censusSnapshotDigest,
        upstreamCapabilityRegistryVersion=snapshot.capabilityRegistryVersion,
        upstreamIdentityLedgerVersion=snapshot.identityLedgerVersion,
        upstreamRelationTaxonomyVersion=snapshot.relationTaxonomyVersion,
    )

    assert not report.passed
    assert "DESCRIPTOR_CANDIDATE_MISMATCH" in report.failureCodes
    assert "CATALOG_RELATION_COVERAGE_INCOMPLETE" in report.failureCodes


def testU3RejectsDerivedRelationUsingAnotherObjectsEvidence(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    victim = next(item for item in relations if item.relationType == "DERIVED_FROM")
    expectedEvidenceId = next(item.evidenceId for item in catalog.evidence if item.objectId == victim.fromRef)
    wrongEvidence = next(item for item in catalog.evidence if item.evidenceId != expectedEvidenceId)
    swapped = buildRelation(
        fromRef=victim.fromRef,
        relationType=victim.relationType,
        toRef=victim.toRef,
        taxonomy=defaultRelationTaxonomy(),
        statementRefs=victim.statementRefs,
        evidenceRefs=(wrongEvidence.evidenceId,),
        epistemicClass=victim.epistemicClass,
        derivationRef=victim.derivationRef,
        weight=victim.weight,
        confidence=victim.confidence,
        validTime=victim.validTime,
        systemTime=victim.systemTime,
        verificationState=victim.verificationState,
        visibility=victim.visibility,
    )
    mutatedRelations = tuple(swapped if item.relationId == victim.relationId else item for item in relations)

    report = validateU3(
        catalog,
        descriptors,
        snapshot,
        statements=(),
        relations=mutatedRelations,
        upstreamG1Passed=True,
        upstreamG2Passed=True,
        upstreamUniverseSnapshotId=snapshot.universeSnapshotId,
        upstreamCensusSnapshotDigest=catalog.censusSnapshotDigest,
        upstreamCapabilityRegistryVersion=snapshot.capabilityRegistryVersion,
        upstreamIdentityLedgerVersion=snapshot.identityLedgerVersion,
        upstreamRelationTaxonomyVersion=snapshot.relationTaxonomyVersion,
    )

    assert not report.passed
    assert "CATALOG_RELATION_SUBJECT_MISMATCH" in report.failureCodes
    assert "CATALOG_RELATION_COVERAGE_INCOMPLETE" in report.failureCodes


def testU3RejectsEligibleDescriptorFailureAndSourceDrift(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    index = next(index for index, item in enumerate(descriptors) if item.formatKind != "UNSUPPORTED")
    mutated = list(descriptors)
    mutated[index] = replace(
        mutated[index],
        status="ACCESS_DENIED",
        sourceRevision="drift",
        schemaFingerprint=None,
        errorCode="ACCESS_DENIED",
    )
    report = validateU3(
        catalog,
        tuple(mutated),
        snapshot,
        statements=(),
        relations=relations,
        upstreamG1Passed=True,
        upstreamG2Passed=True,
        upstreamUniverseSnapshotId=snapshot.universeSnapshotId,
        upstreamCensusSnapshotDigest=catalog.censusSnapshotDigest,
        upstreamCapabilityRegistryVersion=snapshot.capabilityRegistryVersion,
        upstreamIdentityLedgerVersion=snapshot.identityLedgerVersion,
        upstreamRelationTaxonomyVersion=snapshot.relationTaxonomyVersion,
    )

    assert not report.passed
    assert "DESCRIPTOR_ELIGIBLE_NOT_DESCRIBED" in report.failureCodes
    assert "DESCRIPTOR_SOURCE_MISMATCH" in report.failureCodes
    assert "DESCRIPTOR_DIGEST_MISMATCH" in report.failureCodes


def testU3RejectsMalformedDescriptorDigestFields(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    index = next(index for index, item in enumerate(descriptors) if item.formatKind != "UNSUPPORTED")
    mutated = list(descriptors)
    malformedBase = replace(
        mutated[index],
        schemaFingerprint="short",
        responseDigest="not-a-digest",
        rowCount=-1,
        digest="",
    )
    mutated[index] = replace(malformedBase, digest=canonicalDigest(malformedBase))

    report = validateU3(
        catalog,
        tuple(mutated),
        snapshot,
        statements=(),
        relations=relations,
        upstreamG1Passed=True,
        upstreamG2Passed=True,
        upstreamUniverseSnapshotId=snapshot.universeSnapshotId,
        upstreamCensusSnapshotDigest=catalog.censusSnapshotDigest,
        upstreamCapabilityRegistryVersion=snapshot.capabilityRegistryVersion,
        upstreamIdentityLedgerVersion=snapshot.identityLedgerVersion,
        upstreamRelationTaxonomyVersion=snapshot.relationTaxonomyVersion,
    )

    assert not report.passed
    assert "SCHEMA_FINGERPRINT_INVALID" in report.failureCodes
    assert "DESCRIPTOR_RESPONSE_DIGEST_INVALID" in report.failureCodes
    assert "DESCRIPTOR_ROW_COUNT_INVALID" in report.failureCodes


def testU3RejectsUpstreamFailureAndVisibilityDowngrade(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    privateRefs = {item.objectId for item in catalog.objects if item.visibility is Visibility.PRIVATE} | {
        item.resourceVersionId for item in catalog.resources if item.visibility is Visibility.PRIVATE
    }
    index = next(
        index for index, item in enumerate(relations) if item.fromRef in privateRefs or item.toRef in privateRefs
    )
    mutated = list(relations)
    mutated[index] = replace(mutated[index], visibility=Visibility.PUBLIC)
    report = validateU3(
        catalog,
        descriptors,
        snapshot,
        statements=(),
        relations=tuple(mutated),
        upstreamG1Passed=False,
        upstreamG2Passed=False,
        upstreamUniverseSnapshotId="du:v1:snapshot:" + "f" * 64,
        upstreamCensusSnapshotDigest="f" * 64,
        upstreamCapabilityRegistryVersion="wrong-capability",
        upstreamIdentityLedgerVersion="wrong-identity",
        upstreamRelationTaxonomyVersion="wrong-taxonomy",
    )

    assert not report.passed
    assert "G1_REQUIRED" in report.failureCodes
    assert "G2_REQUIRED" in report.failureCodes
    assert "G1_SNAPSHOT_MISMATCH" in report.failureCodes
    assert "G0_SNAPSHOT_MISMATCH" in report.failureCodes
    assert "CAPABILITY_REGISTRY_MISMATCH" in report.failureCodes
    assert "IDENTITY_LEDGER_MISMATCH" in report.failureCodes
    assert "RELATION_TAXONOMY_MISMATCH" in report.failureCodes
    assert "RELATION_VISIBILITY_DOWNGRADE" in report.failureCodes
    assert "GRAPH_RELATION_INTEGRITY_MISMATCH" in report.failureCodes


def testU3RecomputesCatalogDigestAndRejectsObjectVisibilityMutation(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    privateObject = next(item for item in catalog.objects if item.visibility is Visibility.PRIVATE)
    mutatedObjects = tuple(
        replace(item, visibility=Visibility.PUBLIC) if item.objectId == privateObject.objectId else item
        for item in catalog.objects
    )
    mutatedCatalog = replace(catalog, objects=mutatedObjects)

    report = validateU3(
        mutatedCatalog,
        descriptors,
        snapshot,
        statements=(),
        relations=relations,
        upstreamG1Passed=True,
        upstreamG2Passed=True,
        upstreamUniverseSnapshotId=snapshot.universeSnapshotId,
        upstreamCensusSnapshotDigest=catalog.censusSnapshotDigest,
        upstreamCapabilityRegistryVersion=snapshot.capabilityRegistryVersion,
        upstreamIdentityLedgerVersion=snapshot.identityLedgerVersion,
        upstreamRelationTaxonomyVersion=snapshot.relationTaxonomyVersion,
    )

    assert not report.passed
    assert "CATALOG_DIGEST_MISMATCH" in report.failureCodes
    assert "CATALOG_VISIBILITY_DOWNGRADE" in report.failureCodes


def testU3RejectsSnapshotResourceMutationEvenWhenControlVersionsMatch(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    first = snapshot.resources[0]
    mutatedSnapshot = replace(
        snapshot,
        resources=(replace(first, contentDigest="f" * 64), *snapshot.resources[1:]),
    )

    report = validateU3(
        catalog,
        descriptors,
        mutatedSnapshot,
        statements=(),
        relations=relations,
        upstreamG1Passed=True,
        upstreamG2Passed=True,
        upstreamUniverseSnapshotId=snapshot.universeSnapshotId,
        upstreamCensusSnapshotDigest=catalog.censusSnapshotDigest,
        upstreamCapabilityRegistryVersion=snapshot.capabilityRegistryVersion,
        upstreamIdentityLedgerVersion=snapshot.identityLedgerVersion,
        upstreamRelationTaxonomyVersion=snapshot.relationTaxonomyVersion,
    )

    assert not report.passed
    assert "CATALOG_SNAPSHOT_INVALID" in report.failureCodes
    assert "CATALOG_SNAPSHOT_RESOURCE_MISMATCH" in report.failureCodes


def testU3RelationCannotWidenReferencedPrivateStatement(gateFixture):
    catalog, descriptors, snapshot, relations = gateFixture
    privateEvidence = next(item for item in catalog.evidence if item.visibility is Visibility.PRIVATE)
    statement = buildStatement(
        subjectRef=privateEvidence.objectId,
        predicate="fixtureFact",
        value=1,
        valueType="integer",
        scope="entity",
        validTime=TimeRange(),
        systemTime=SystemTime(privateEvidence.retrievedAt),
        epistemicClass=EpistemicClass.OBSERVED,
        verificationState=VerificationState.VERIFIED,
        evidenceRefs=(privateEvidence.evidenceId,),
        evidenceById={privateEvidence.evidenceId: privateEvidence},
        visibility=Visibility.PRIVATE,
    )
    publicObjects = [item for item in catalog.objects if item.visibility is Visibility.PUBLIC]
    relation = buildRelation(
        fromRef=publicObjects[0].objectId,
        relationType="DESCRIBES",
        toRef=publicObjects[1].objectId,
        taxonomy=defaultRelationTaxonomy(),
        statementRefs=(statement.statementId,),
        evidenceRefs=(privateEvidence.evidenceId,),
        epistemicClass=EpistemicClass.OBSERVED,
        validTime=TimeRange(),
        systemTime=SystemTime(privateEvidence.retrievedAt),
        verificationState=VerificationState.VERIFIED,
        visibility=Visibility.PRIVATE,
    )
    widened = replace(relation, visibility=Visibility.PUBLIC)

    report = validateU3(
        catalog,
        descriptors,
        snapshot,
        statements=(statement,),
        relations=(*relations, widened),
        upstreamG1Passed=True,
        upstreamG2Passed=True,
        upstreamUniverseSnapshotId=snapshot.universeSnapshotId,
        upstreamCensusSnapshotDigest=catalog.censusSnapshotDigest,
        upstreamCapabilityRegistryVersion=snapshot.capabilityRegistryVersion,
        upstreamIdentityLedgerVersion=snapshot.identityLedgerVersion,
        upstreamRelationTaxonomyVersion=snapshot.relationTaxonomyVersion,
    )

    assert not report.passed
    assert "RELATION_VISIBILITY_DOWNGRADE" in report.failureCodes
    assert "GRAPH_RELATION_INTEGRITY_MISMATCH" in report.failureCodes
