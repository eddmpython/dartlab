"""Universe U3 virtual locator, statement, relation, bounded graph를 검증한다."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests._attempts.dartlabUniverse.catalog.compiler import compileCatalog
from tests._attempts.dartlabUniverse.catalog.models import catalogObjectVersionId
from tests._attempts.dartlabUniverse.contracts import (
    EpistemicClass,
    SystemTime,
    TimeRange,
    VerificationState,
    Visibility,
)
from tests._attempts.dartlabUniverse.graph.query import GraphStore, TraversalBudget
from tests._attempts.dartlabUniverse.graph.relations import (
    buildRelation,
    compileCatalogRelations,
    defaultRelationTaxonomy,
)
from tests._attempts.dartlabUniverse.graph.statements import buildStatement, virtualCellRef, virtualRowRef
from tests._attempts.dartlabUniverse.ids import logicalId
from tests._attempts.dartlabUniverse.testCoverage import _fakeResult


def _times():
    return TimeRange("2025-01-01T00:00:00Z", None), SystemTime("2025-02-01T00:00:00Z")


def testVirtualRowAndCellKeepOriginalRevisionLocator():
    catalog = compileCatalog(_fakeResult())
    resource = next(item for item in catalog.resources if item.resourceKind == "HF_FILE")
    row = virtualRowRef(resource, tableId="facts", rowGroup=2, rowOffset=11)
    cell = virtualCellRef(row, "assets")

    locator = dict(cell.locator)
    assert row.identityScope == "REVISION_SCOPED"
    assert locator["repo"] == resource.sourceRef
    assert locator["revision"] == resource.sourceRevision
    assert locator["fileVersionId"] == resource.resourceVersionId
    assert locator["rowGroup"] == "2"
    assert locator["rowOffset"] == "11"
    assert locator["column"] == "assets"

    with pytest.raises(ValueError, match="virtual row locator"):
        virtualRowRef(resource, tableId="facts", rowGroup=-1, rowOffset=0)
    with pytest.raises(ValueError, match="virtual cell locator"):
        virtualCellRef(row, "")


def testObservedStatementAndEvidenceRelationAreTraceable():
    catalog = compileCatalog(_fakeResult())
    evidence = catalog.evidence[0]
    validTime, systemTime = _times()
    statement = buildStatement(
        subjectRef="organization:005930",
        predicate="assets",
        value=100,
        valueType="integer",
        unit="currency",
        currency="KRW",
        scale=0,
        scope="consolidated",
        periodStart="2025-01-01",
        periodEnd="2025-12-31",
        validTime=validTime,
        systemTime=systemTime,
        epistemicClass=EpistemicClass.OBSERVED,
        verificationState=VerificationState.VERIFIED,
        evidenceRefs=(evidence.evidenceId,),
        evidenceById={evidence.evidenceId: evidence},
        visibility=Visibility.LOCAL,
    )
    taxonomy = defaultRelationTaxonomy()
    relation = buildRelation(
        fromRef=statement.subjectRef,
        relationType="REPORTS",
        toRef=statement.statementId,
        taxonomy=taxonomy,
        statementRefs=(statement.statementId,),
        evidenceRefs=(evidence.evidenceId,),
        epistemicClass=EpistemicClass.OBSERVED,
        validTime=validTime,
        systemTime=systemTime,
        verificationState=VerificationState.VERIFIED,
        visibility=Visibility.LOCAL,
    )
    store = GraphStore((statement,), (relation,))
    traversed = store.traverse(
        (statement.subjectRef,),
        validAt="2025-06-01T00:00:00Z",
        knownAt="2025-06-02T00:00:00Z",
        allowedVisibility=frozenset({Visibility.LOCAL}),
    )

    assert traversed.nodeRefs == tuple(sorted((statement.subjectRef, statement.statementId)))
    assert traversed.relations == (relation,)
    assert relation.direction == "OUTBOUND"
    tables = store.arrowTables(allowedVisibility=frozenset({Visibility.LOCAL}))
    assert tables["statements"].num_rows == 1
    assert tables["relations"].num_rows == 1


def testGraphTraversalIsBoundedAndTimeVisibilityAware():
    validTime, systemTime = _times()
    taxonomy = defaultRelationTaxonomy()
    relations = tuple(
        buildRelation(
            fromRef=f"node:{index}",
            relationType="CONTAINS",
            toRef=f"node:{index + 1}",
            taxonomy=taxonomy,
            statementRefs=(),
            evidenceRefs=(),
            epistemicClass=EpistemicClass.ASSERTED,
            validTime=validTime,
            systemTime=systemTime,
            verificationState=VerificationState.VERIFIED,
            visibility=Visibility.LOCAL,
        )
        for index in range(10)
    )
    result = GraphStore((), relations).traverse(
        ("node:0",),
        validAt="2025-03-01T00:00:00Z",
        knownAt="2025-03-01T00:00:00Z",
        allowedVisibility=frozenset({Visibility.LOCAL}),
        budget=TraversalBudget(maxDepth=20, maxNodes=4, maxEdges=20),
    )

    assert result.truncated
    assert result.truncationReason == "MAX_NODES"
    assert len(result.nodeRefs) == 4


def testGraphRootFanoutCannotBypassNodeBudget():
    result = GraphStore((), ()).traverse(
        tuple(f"node:{index}" for index in range(10)),
        validAt="2025-03-01T00:00:00Z",
        knownAt="2025-03-01T00:00:00Z",
        allowedVisibility=frozenset({Visibility.LOCAL}),
        budget=TraversalBudget(maxDepth=1, maxNodes=3, maxEdges=10),
    )

    assert result.rootRefs == ("node:0", "node:1", "node:2")
    assert result.nodeRefs == result.rootRefs
    assert result.truncated
    assert result.truncationReason == "MAX_NODES"


def testGraphTraversalRequiresExplicitVisibilityScope():
    with pytest.raises(ValueError, match="allowedVisibility"):
        GraphStore((), ()).traverse(
            ("node:root",),
            validAt="2025-03-01T00:00:00Z",
            knownAt="2025-03-01T00:00:00Z",
            allowedVisibility=frozenset(),
        )


def testCatalogObjectCanBindMultipleResourceEvidencePaths():
    catalog = compileCatalog(_fakeResult())
    candidates = [item for item in catalog.objects if item.visibility is Visibility.LOCAL]
    first = candidates[0]
    second = candidates[1]
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

    relations = compileCatalogRelations(mergedCatalog)
    derivedRefs = {
        item.toRef for item in relations if item.fromRef == first.objectId and item.relationType == "DERIVED_FROM"
    }

    assert derivedRefs == set(refs)


def testGraphRejectsSpatialPseudoRelationAndMissingEvidence():
    taxonomy = defaultRelationTaxonomy()
    validTime, systemTime = _times()
    with pytest.raises(ValueError, match="taxonomy 밖 relation"):
        buildRelation(
            fromRef="a",
            relationType="SPATIAL_NEAR",
            toRef="b",
            taxonomy=taxonomy,
            statementRefs=(),
            evidenceRefs=(),
            epistemicClass=EpistemicClass.ASSERTED,
            validTime=validTime,
            systemTime=systemTime,
            verificationState=VerificationState.VERIFIED,
            visibility=Visibility.LOCAL,
        )

    with pytest.raises(ValueError, match="validTime"):
        buildRelation(
            fromRef="a",
            relationType="CONTAINS",
            toRef="b",
            taxonomy=taxonomy,
            statementRefs=(),
            evidenceRefs=(),
            epistemicClass=EpistemicClass.ASSERTED,
            validTime=TimeRange("2025-02-01T00:00:00Z", "2025-01-01T00:00:00Z"),
            systemTime=systemTime,
            verificationState=VerificationState.VERIFIED,
            visibility=Visibility.LOCAL,
        )
    with pytest.raises(ValueError, match="근거가 필요"):
        buildRelation(
            fromRef="a",
            relationType="REPORTS",
            toRef="b",
            taxonomy=taxonomy,
            statementRefs=(),
            evidenceRefs=(),
            epistemicClass=EpistemicClass.ASSERTED,
            validTime=validTime,
            systemTime=systemTime,
            verificationState=VerificationState.VERIFIED,
            visibility=Visibility.LOCAL,
        )


def testEmptyGraphArrowBatchKeepsProductSchema():
    tables = GraphStore((), ()).arrowTables(allowedVisibility=frozenset({Visibility.PUBLIC}))

    assert tables["statements"].num_rows == 0
    assert tables["relations"].num_rows == 0
    assert {"statementId", "evidenceRefs", "digest"} <= set(tables["statements"].column_names)
    assert {"relationId", "relationType", "visibility"} <= set(tables["relations"].column_names)


def testPrivateEdgeDoesNotLeakThroughPublicTruncationFlag():
    validTime, systemTime = _times()
    relation = buildRelation(
        fromRef="public:root",
        relationType="CONTAINS",
        toRef="private:child",
        taxonomy=defaultRelationTaxonomy(),
        statementRefs=(),
        evidenceRefs=(),
        epistemicClass=EpistemicClass.ASSERTED,
        validTime=validTime,
        systemTime=systemTime,
        verificationState=VerificationState.VERIFIED,
        visibility=Visibility.PRIVATE,
    )
    result = GraphStore((), (relation,)).traverse(
        ("public:root",),
        validAt="2025-03-01T00:00:00Z",
        knownAt="2025-03-01T00:00:00Z",
        allowedVisibility=frozenset({Visibility.PUBLIC}),
        budget=TraversalBudget(maxDepth=0, maxNodes=10, maxEdges=10),
    )

    assert result.nodeRefs == ("public:root",)
    assert result.relations == ()
    assert not result.truncated
    tables = GraphStore((), (relation,)).arrowTables(allowedVisibility=frozenset({Visibility.PUBLIC}))
    assert tables["relations"].num_rows == 0


def testStatementCannotWidenPrivateEvidenceVisibility():
    catalog = compileCatalog(_fakeResult())
    evidence = next(item for item in catalog.evidence if item.visibility is Visibility.PRIVATE)
    validTime, systemTime = _times()

    with pytest.raises(ValueError, match="evidence보다 넓을 수 없음"):
        buildStatement(
            subjectRef="organization:private",
            predicate="privateFact",
            value=1,
            valueType="integer",
            scope="entity",
            validTime=validTime,
            systemTime=systemTime,
            epistemicClass=EpistemicClass.OBSERVED,
            verificationState=VerificationState.VERIFIED,
            evidenceRefs=(evidence.evidenceId,),
            evidenceById={evidence.evidenceId: evidence},
            visibility=Visibility.PUBLIC,
        )


def testStatementRejectsBooleanConfidence():
    catalog = compileCatalog(_fakeResult())
    evidence = next(item for item in catalog.evidence if item.visibility is Visibility.LOCAL)
    validTime, systemTime = _times()

    with pytest.raises(ValueError, match="confidence"):
        buildStatement(
            subjectRef=evidence.objectId,
            predicate="fixtureFact",
            value=1,
            valueType="integer",
            scope="entity",
            validTime=validTime,
            systemTime=systemTime,
            epistemicClass=EpistemicClass.OBSERVED,
            verificationState=VerificationState.VERIFIED,
            evidenceRefs=(evidence.evidenceId,),
            evidenceById={evidence.evidenceId: evidence},
            confidence=True,
            visibility=Visibility.LOCAL,
        )
