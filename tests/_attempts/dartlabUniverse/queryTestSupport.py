"""U4 query tests가 공유하는 DART, EDGAR, statement fixture."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from tests._attempts.dartlabUniverse.catalog.compiler import attachIdentityRecords, compileCatalog
from tests._attempts.dartlabUniverse.catalog.models import CatalogState
from tests._attempts.dartlabUniverse.catalog.snapshot import CatalogSnapshot, buildCatalogSnapshot
from tests._attempts.dartlabUniverse.contracts import (
    EpistemicClass,
    SystemTime,
    TimeRange,
    VerificationState,
    Visibility,
)
from tests._attempts.dartlabUniverse.graph.query import GraphStore
from tests._attempts.dartlabUniverse.graph.relations import (
    buildRelation,
    compileCatalogRelations,
    defaultRelationTaxonomy,
)
from tests._attempts.dartlabUniverse.graph.statements import GraphStatement, buildStatement
from tests._attempts.dartlabUniverse.identity.ledger import (
    AliasRecord,
    IdentifierRef,
    IdentityEvidence,
    IdentityLedger,
    buildIdentityLedger,
)
from tests._attempts.dartlabUniverse.ids import dartOrganizationId, edgarOrganizationId
from tests._attempts.dartlabUniverse.testCoverage import _fakeResult


@dataclass(frozen=True, slots=True)
class QueryRuntimeFixture:
    catalog: CatalogState
    snapshot: CatalogSnapshot
    graph: GraphStore
    ledger: IdentityLedger
    dartEntityId: str
    edgarEntityId: str
    statements: tuple[GraphStatement, ...]


def _identityRecords() -> tuple[IdentityEvidence, ...]:
    dartId = dartOrganizationId("00126380")
    edgarId = edgarOrganizationId("320193")
    return (
        IdentityEvidence(
            entityId=dartId,
            jurisdiction="KR",
            canonicalIdentifier=IdentifierRef("DART_CORP_CODE", "00126380"),
            legalName="삼성전자",
            aliases=(
                AliasRecord("KR_STOCK_CODE", "005930", None, None, "fixture:dart:evidence"),
                AliasRecord("LEGAL_NAME_EN", "Samsung Electronics", None, None, "fixture:dart:evidence"),
            ),
            sourceRef="DART_CORP_CODE_PARQUET",
            sourceRevision="d" * 64,
            rowLocator="corp_code=00126380",
            observedAt="2026-07-18T00:00:00Z",
        ),
        IdentityEvidence(
            entityId=edgarId,
            jurisdiction="US",
            canonicalIdentifier=IdentifierRef("SEC_CIK", "320193"),
            legalName="Apple Inc.",
            aliases=(
                AliasRecord("US_TICKER", "AAPL", None, None, "fixture:edgar:evidence"),
                AliasRecord("LEGAL_NAME_EN", "Apple", None, None, "fixture:edgar:evidence"),
            ),
            sourceRef="SEC_COMPANY_TICKERS_JSON",
            sourceRevision="e" * 64,
            rowLocator="cik=0000320193",
            observedAt="2026-07-18T00:00:00Z",
        ),
    )


@cache
def buildQueryRuntimeFixture() -> QueryRuntimeFixture:
    records = _identityRecords()
    ledger = buildIdentityLedger(records)
    catalog = attachIdentityRecords(compileCatalog(_fakeResult()), records)
    evidenceByObject = {
        entityId: next(item for item in catalog.evidence if item.objectId == entityId)
        for entityId in (records[0].entityId, records[1].entityId)
    }
    evidenceById = {item.evidenceId: item for item in catalog.evidence}
    validTime = TimeRange("2025-01-01T00:00:00Z", None)
    systemTime = SystemTime("2026-01-01T00:00:00Z")
    first = buildStatement(
        subjectRef=records[0].entityId,
        predicate="assets",
        value=100_000_000,
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
        evidenceRefs=(evidenceByObject[records[0].entityId].evidenceId,),
        evidenceById=evidenceById,
        conflictGroupId="fixture:assets:2025",
        visibility=Visibility.LOCAL,
    )
    second = buildStatement(
        subjectRef=records[0].entityId,
        predicate="assets",
        value=99_000_000,
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
        verificationState=VerificationState.CONFLICTED,
        evidenceRefs=(evidenceByObject[records[0].entityId].evidenceId,),
        evidenceById=evidenceById,
        conflictGroupId="fixture:assets:2025",
        visibility=Visibility.LOCAL,
    )
    taxonomy = defaultRelationTaxonomy()
    relations = list(compileCatalogRelations(catalog, taxonomy=taxonomy))
    for statement in (first, second):
        relations.append(
            buildRelation(
                fromRef=records[0].entityId,
                relationType="REPORTS",
                toRef=statement.statementId,
                taxonomy=taxonomy,
                statementRefs=(statement.statementId,),
                evidenceRefs=statement.evidenceRefs,
                epistemicClass=EpistemicClass.OBSERVED,
                validTime=validTime,
                systemTime=systemTime,
                verificationState=statement.verificationState,
                visibility=Visibility.LOCAL,
            )
        )
    relations.append(
        buildRelation(
            fromRef=first.statementId,
            relationType="CONTRADICTS",
            toRef=second.statementId,
            taxonomy=taxonomy,
            statementRefs=(first.statementId, second.statementId),
            evidenceRefs=first.evidenceRefs,
            epistemicClass=EpistemicClass.OBSERVED,
            validTime=validTime,
            systemTime=systemTime,
            verificationState=VerificationState.CONFLICTED,
            visibility=Visibility.LOCAL,
        )
    )
    graph = GraphStore((first, second), tuple(relations))
    snapshot = buildCatalogSnapshot(
        catalog,
        universeSnapshotId="du:v1:snapshot:" + "1" * 64,
        capabilityRegistryVersion="fixture:capability:v1",
        identityLedgerVersion=ledger.revision,
        relationTaxonomyVersion=taxonomy.version,
        createdAt="2026-07-19T00:00:00Z",
    )
    return QueryRuntimeFixture(
        catalog=catalog,
        snapshot=snapshot,
        graph=graph,
        ledger=ledger,
        dartEntityId=records[0].entityId,
        edgarEntityId=records[1].entityId,
        statements=(first, second),
    )
