"""Universe U3 catalog, descriptor, delta, evidence graph 통합 gate."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ..canonical import canonicalDigest
from ..catalog.compiler import validateCatalogState
from ..catalog.delta import CatalogDelta, applyDeltaResources, validateCatalogDelta
from ..catalog.descriptorCrawler import ResourceDescriptor
from ..catalog.models import CatalogEvidence, CatalogState, catalogObjectVersionId
from ..catalog.recovery import ResourceRecovery
from ..catalog.snapshot import CatalogSnapshot, SnapshotResourceRef, validateCatalogSnapshot
from ..contracts import Visibility
from ..controlPlane.cas import ContentAddressedStore
from ..graph.relations import (
    GraphRelation,
    RelationTaxonomy,
    buildRelation,
    defaultRelationTaxonomy,
)
from ..graph.statements import GraphStatement, buildStatement
from .c2 import validateC2


@dataclass(frozen=True, slots=True)
class U3Report:
    gate: str
    passed: bool
    catalogResourceCount: int
    catalogCoverageRatio: float
    descriptorCandidateCount: int
    descriptorTerminalCount: int
    descriptorEligibleCount: int
    describedEligibleCount: int
    directlyDescribedEligibleCount: int
    recoveredEligibleCount: int
    recoveryReceiptCount: int
    recoverySetDigest: str
    recoveryValidationDigest: str
    schemaFingerprintCoverageRatio: float
    rowContractCoverageRatio: float
    objectEvidenceCoverageRatio: float
    catalogRelationCoverageRatio: float
    statementCount: int
    statementProvenanceStatus: str
    sourcePayloadCopies: int
    upstreamG1Passed: bool
    upstreamG2Passed: bool
    upstreamUniverseSnapshotId: str
    upstreamCensusSnapshotDigest: str
    upstreamCapabilityRegistryVersion: str
    upstreamIdentityLedgerVersion: str
    upstreamRelationTaxonomyVersion: str
    failureCodes: tuple[str, ...]
    digest: str


def validateU3(
    catalog: CatalogState,
    descriptors: tuple[ResourceDescriptor, ...],
    snapshot: CatalogSnapshot,
    *,
    statements: tuple[GraphStatement, ...],
    relations: tuple[GraphRelation, ...],
    upstreamG1Passed: bool,
    upstreamG2Passed: bool,
    upstreamUniverseSnapshotId: str,
    upstreamCensusSnapshotDigest: str,
    upstreamCapabilityRegistryVersion: str,
    upstreamIdentityLedgerVersion: str,
    upstreamRelationTaxonomyVersion: str,
    recoveries: tuple[ResourceRecovery, ...] = (),
    recoveryCas: ContentAddressedStore | None = None,
    previousSnapshot: CatalogSnapshot | None = None,
    delta: CatalogDelta | None = None,
    relationTaxonomy: RelationTaxonomy | None = None,
) -> U3Report:
    """U3의 C0, C1, C2, snapshot, delta, evidence path를 하나의 gate로 닫는다."""
    failures = []
    activeTaxonomy = relationTaxonomy or defaultRelationTaxonomy()
    if activeTaxonomy.version != upstreamRelationTaxonomyVersion:
        failures.append("RELATION_TAXONOMY_SUBJECT_MISMATCH")
    failures.extend(validateCatalogState(catalog))
    if not upstreamG1Passed:
        failures.append("G1_REQUIRED")
    if not upstreamG2Passed:
        failures.append("G2_REQUIRED")
    if snapshot.universeSnapshotId != upstreamUniverseSnapshotId:
        failures.append("G1_SNAPSHOT_MISMATCH")
    if catalog.censusSnapshotDigest != upstreamCensusSnapshotDigest:
        failures.append("G0_SNAPSHOT_MISMATCH")
    if snapshot.capabilityRegistryVersion != upstreamCapabilityRegistryVersion:
        failures.append("CAPABILITY_REGISTRY_MISMATCH")
    if snapshot.identityLedgerVersion != upstreamIdentityLedgerVersion:
        failures.append("IDENTITY_LEDGER_MISMATCH")
    if snapshot.relationTaxonomyVersion != upstreamRelationTaxonomyVersion:
        failures.append("RELATION_TAXONOMY_MISMATCH")
    if catalog.coverage.coverageRatio != 1.0 or catalog.coverage.resourceCount != len(catalog.resources):
        failures.append("CATALOG_COVERAGE_INCOMPLETE")
    if catalog.coverage.sourcePayloadCopies != 0:
        failures.append("SOURCE_PAYLOAD_COPY_FORBIDDEN")
    capabilityResources = tuple(item for item in catalog.resources if item.resourceKind == "CAPABILITY")
    if not capabilityResources:
        failures.append("CAPABILITY_CATALOG_EMPTY")
    for resource in capabilityResources:
        attributes = dict(resource.attributes)
        if attributes.get("eligible") == "true" and not resource.schemaFingerprint:
            failures.append("ELIGIBLE_CAPABILITY_SCHEMA_MISSING")
        if attributes.get("eligible") == "false" and not resource.gapReason:
            failures.append("INELIGIBLE_CAPABILITY_REASON_MISSING")
    if validateCatalogSnapshot(snapshot):
        failures.append("CATALOG_SNAPSHOT_INVALID")
    if snapshot.catalogDigest != catalog.digest:
        failures.append("CATALOG_SNAPSHOT_SUBJECT_MISMATCH")
    expectedDescriptorSetDigest = canonicalDigest(tuple(sorted(item.digest for item in descriptors)))
    if snapshot.descriptorSetDigest != expectedDescriptorSetDigest:
        failures.append("DESCRIPTOR_SET_SNAPSHOT_MISMATCH")
    expectedRecoverySetDigest = canonicalDigest(tuple(sorted(item.digest for item in recoveries)))
    if snapshot.recoverySetDigest != expectedRecoverySetDigest:
        failures.append("RECOVERY_SET_SNAPSHOT_MISMATCH")
    descriptorByVersion = {item.resourceVersionId: item for item in descriptors}
    expectedSnapshotResources = tuple(
        SnapshotResourceRef(
            resourceId=item.resourceId,
            resourceVersionId=item.resourceVersionId,
            sourceKind=item.sourceKind,
            sourceRef=item.sourceRef,
            sourceRevision=item.sourceRevision,
            locator=item.locator,
            contentSelector=item.contentSelector,
            contentDigest=item.contentDigest,
            visibility=item.visibility,
            licenseRef=item.licenseRef,
            status=item.status,
            descriptorDigest=descriptorByVersion[item.resourceVersionId].digest
            if item.resourceVersionId in descriptorByVersion
            else None,
        )
        for item in catalog.resources
    )
    if snapshot.resources != expectedSnapshotResources:
        failures.append("CATALOG_SNAPSHOT_RESOURCE_MISMATCH")

    c2 = validateC2(catalog, descriptors, recoveries=recoveries, recoveryCas=recoveryCas)
    failures.extend(c2.failureCodes)

    visibilityRank = {
        Visibility.PUBLIC: 0,
        Visibility.LOCAL: 1,
        Visibility.PRIVATE: 2,
        Visibility.RESTRICTED: 3,
        Visibility.UNKNOWN: 4,
    }
    resourcesByVersion = {item.resourceVersionId: item for item in catalog.resources}
    evidenceById = {item.evidenceId: item for item in catalog.evidence}
    evidenceByObjectResource: dict[tuple[str, str], list[CatalogEvidence]] = {}
    for evidence in catalog.evidence:
        evidenceByObjectResource.setdefault((evidence.objectId, evidence.resourceVersionId), []).append(evidence)
    evidenceCovered = 0
    for obj in catalog.objects:
        objectVersionValid = obj.objectVersionId == catalogObjectVersionId(
            objectId=obj.objectId,
            objectKind=obj.objectKind,
            canonicalLabel=obj.canonicalLabel,
            aliases=obj.aliases,
            identifierRefs=obj.identifierRefs,
            resourceRefs=obj.resourceRefs,
            epistemicClass=obj.epistemicClass,
            verificationState=obj.verificationState,
            validTime=obj.validTime,
            attributes=obj.attributes,
        )
        objectEvidenceValid = objectVersionValid
        for resourceRef in obj.resourceRefs:
            resource = resourcesByVersion.get(resourceRef)
            candidates = evidenceByObjectResource.get((obj.objectId, resourceRef), ())
            matching = tuple(
                evidence
                for evidence in candidates
                if resource is not None
                and evidence.sourceRevision == resource.sourceRevision
                and evidence.locator == resource.locator
                and evidence.selector == resource.contentSelector
                and evidence.contentDigest == resource.contentDigest
                and evidence.licenseRef == resource.licenseRef
            )
            if resource is None or not matching:
                objectEvidenceValid = False
                continue
            if visibilityRank[obj.visibility] < visibilityRank[resource.visibility] or any(
                visibilityRank[evidence.visibility] < visibilityRank[resource.visibility] for evidence in matching
            ):
                failures.append("CATALOG_VISIBILITY_DOWNGRADE")
        if objectEvidenceValid:
            evidenceCovered += 1
        else:
            failures.append("OBJECT_EVIDENCE_PATH_BROKEN")

    objectById = {item.objectId: item for item in catalog.objects}
    objectIds = set(objectById)
    visibilityByRef = {
        **{item.objectId: item.visibility for item in catalog.objects},
        **{item.resourceVersionId: item.visibility for item in catalog.resources},
    }
    statementById = {item.statementId: item for item in statements}
    if len(statementById) != len(statements):
        failures.append("GRAPH_STATEMENT_ID_DUPLICATE")
    statementStatus = "NOT_APPLICABLE" if not statements else "COMPLETE"
    for statement in statements:
        try:
            rebuiltStatement = buildStatement(
                subjectRef=statement.subjectRef,
                predicate=statement.predicate,
                objectRef=statement.objectRef,
                value=statement.value,
                valueType=statement.valueType,
                unit=statement.unit,
                currency=statement.currency,
                scale=statement.scale,
                scope=statement.scope,
                periodStart=statement.periodStart,
                periodEnd=statement.periodEnd,
                instant=statement.instant,
                validTime=statement.validTime,
                systemTime=statement.systemTime,
                epistemicClass=statement.epistemicClass,
                verificationState=statement.verificationState,
                evidenceRefs=statement.evidenceRefs,
                evidenceById=evidenceById,
                derivationRef=statement.derivationRef,
                assumptionRefs=statement.assumptionRefs,
                confidence=statement.confidence,
                conflictGroupId=statement.conflictGroupId,
                visibility=statement.visibility,
            )
        except (TypeError, ValueError):
            failures.append("GRAPH_STATEMENT_INVALID")
            statementStatus = "INCOMPLETE"
        else:
            if rebuiltStatement != statement:
                failures.append("GRAPH_STATEMENT_INTEGRITY_MISMATCH")
                statementStatus = "INCOMPLETE"
        if statement.subjectRef not in visibilityByRef or (
            statement.objectRef is not None and statement.objectRef not in visibilityByRef
        ):
            failures.append("GRAPH_STATEMENT_ENDPOINT_BROKEN")
            statementStatus = "INCOMPLETE"
        if any(evidenceRef not in evidenceById for evidenceRef in statement.evidenceRefs):
            failures.append("STATEMENT_EVIDENCE_PATH_BROKEN")
            statementStatus = "INCOMPLETE"
            continue
        visibilityInputs = [evidenceById[item].visibility for item in statement.evidenceRefs]
        visibilityInputs.extend(
            item
            for item in (
                visibilityByRef.get(statement.subjectRef),
                visibilityByRef.get(statement.objectRef) if statement.objectRef else None,
            )
            if item is not None
        )
        requiredRank = max((visibilityRank[item] for item in visibilityInputs), default=0)
        if visibilityRank[statement.visibility] < requiredRank:
            failures.append("STATEMENT_VISIBILITY_DOWNGRADE")
            statementStatus = "INCOMPLETE"
    visibilityByRef.update({item.statementId: item.visibility for item in statements})
    relationCovered = 0
    catalogRelationPairs = set()
    relationIds = {item.relationId for item in relations}
    if len(relationIds) != len(relations):
        failures.append("GRAPH_RELATION_ID_DUPLICATE")
    for relation in relations:
        try:
            rebuiltRelation = buildRelation(
                fromRef=relation.fromRef,
                relationType=relation.relationType,
                toRef=relation.toRef,
                taxonomy=activeTaxonomy,
                direction=relation.direction,
                statementRefs=relation.statementRefs,
                evidenceRefs=relation.evidenceRefs,
                epistemicClass=relation.epistemicClass,
                derivationRef=relation.derivationRef,
                weight=relation.weight,
                confidence=relation.confidence,
                validTime=relation.validTime,
                systemTime=relation.systemTime,
                verificationState=relation.verificationState,
                visibility=relation.visibility,
            )
        except (TypeError, ValueError):
            failures.append("GRAPH_RELATION_INVALID")
        else:
            if rebuiltRelation != relation:
                failures.append("GRAPH_RELATION_INTEGRITY_MISMATCH")
        if relation.fromRef not in visibilityByRef or relation.toRef not in visibilityByRef:
            failures.append("GRAPH_RELATION_ENDPOINT_BROKEN")
        if any(ref not in evidenceById for ref in relation.evidenceRefs):
            failures.append("RELATION_EVIDENCE_PATH_BROKEN")
            continue
        if any(ref not in statementById for ref in relation.statementRefs):
            failures.append("RELATION_STATEMENT_PATH_BROKEN")
            continue
        visibilityInputs = [evidenceById[item].visibility for item in relation.evidenceRefs] + [
            statementById[item].visibility for item in relation.statementRefs
        ]
        visibilityInputs.extend(
            item
            for item in (
                visibilityByRef.get(relation.fromRef),
                visibilityByRef.get(relation.toRef),
            )
            if item is not None
        )
        requiredRank = max((visibilityRank[item] for item in visibilityInputs), default=0)
        if visibilityRank[relation.visibility] < requiredRank:
            failures.append("RELATION_VISIBILITY_DOWNGRADE")
        if relation.relationType == "DERIVED_FROM" and relation.fromRef in objectIds:
            sourceObject = objectById[relation.fromRef]
            expectedEvidence = evidenceByObjectResource.get((relation.fromRef, relation.toRef), ())
            if (
                relation.toRef not in sourceObject.resourceRefs
                or not expectedEvidence
                or set(relation.evidenceRefs) != {item.evidenceId for item in expectedEvidence}
            ):
                failures.append("CATALOG_RELATION_SUBJECT_MISMATCH")
            else:
                catalogRelationPairs.add((relation.fromRef, relation.toRef))
                relationCovered += 1
    expectedCatalogRelationPairs = {
        (item.objectId, resourceRef) for item in catalog.objects for resourceRef in item.resourceRefs
    }
    if catalogRelationPairs != expectedCatalogRelationPairs:
        failures.append("CATALOG_RELATION_COVERAGE_INCOMPLETE")

    if previousSnapshot is None and delta is not None:
        failures.append("DELTA_PREVIOUS_SNAPSHOT_MISSING")
    if delta is not None:
        failures.extend(validateCatalogDelta(delta))
        if delta.currentSnapshotId != snapshot.snapshotId:
            failures.append("DELTA_CURRENT_SNAPSHOT_MISMATCH")
    if previousSnapshot is not None:
        if delta is None:
            failures.append("CATALOG_DELTA_MISSING")
        else:
            if delta.previousSnapshotId != previousSnapshot.snapshotId:
                failures.append("DELTA_PREVIOUS_SNAPSHOT_MISMATCH")
            try:
                replayedResources = applyDeltaResources(previousSnapshot.resources, delta)
            except ValueError:
                failures.append("CATALOG_DELTA_REPLAY_INVALID")
            else:
                if replayedResources != snapshot.resources:
                    failures.append("CATALOG_DELTA_REPLAY_MISMATCH")

    objectCount = len(catalog.objects)
    base = U3Report(
        gate="U3",
        passed=False,
        catalogResourceCount=len(catalog.resources),
        catalogCoverageRatio=catalog.coverage.coverageRatio,
        descriptorCandidateCount=c2.candidateCount,
        descriptorTerminalCount=c2.terminalCount,
        descriptorEligibleCount=c2.eligibleCount,
        describedEligibleCount=c2.describedEligibleCount,
        directlyDescribedEligibleCount=c2.directlyDescribedEligibleCount,
        recoveredEligibleCount=c2.recoveredEligibleCount,
        recoveryReceiptCount=c2.recoveryReceiptCount,
        recoverySetDigest=c2.recoverySetDigest,
        recoveryValidationDigest=c2.recoveryValidationDigest,
        schemaFingerprintCoverageRatio=c2.schemaFingerprintCoverageRatio,
        rowContractCoverageRatio=c2.rowContractCoverageRatio,
        objectEvidenceCoverageRatio=evidenceCovered / objectCount if objectCount else 1.0,
        catalogRelationCoverageRatio=len(catalogRelationPairs) / len(expectedCatalogRelationPairs)
        if expectedCatalogRelationPairs
        else 1.0,
        statementCount=len(statements),
        statementProvenanceStatus=statementStatus,
        sourcePayloadCopies=catalog.coverage.sourcePayloadCopies,
        upstreamG1Passed=upstreamG1Passed,
        upstreamG2Passed=upstreamG2Passed,
        upstreamUniverseSnapshotId=upstreamUniverseSnapshotId,
        upstreamCensusSnapshotDigest=upstreamCensusSnapshotDigest,
        upstreamCapabilityRegistryVersion=upstreamCapabilityRegistryVersion,
        upstreamIdentityLedgerVersion=upstreamIdentityLedgerVersion,
        upstreamRelationTaxonomyVersion=upstreamRelationTaxonomyVersion,
        failureCodes=tuple(sorted(set(failures))),
        digest="",
    )
    report = replace(base, passed=not base.failureCodes)
    return replace(report, digest=canonicalDigest(report))
