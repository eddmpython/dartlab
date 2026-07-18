"""Universe U1 DART, EDGAR identity, alias time, concept mapping 검증."""

from __future__ import annotations

from tests._attempts.dartlabUniverse.identity.census import censusIdentitySources
from tests._attempts.dartlabUniverse.identity.conceptMapping import (
    ConceptMappingRecord,
    MappingState,
    MappingType,
    buildConceptMappingLedger,
    resolveConcept,
)
from tests._attempts.dartlabUniverse.identity.dartIdentitySource import enumerateDartIdentities
from tests._attempts.dartlabUniverse.identity.edgarIdentitySource import enumerateEdgarIdentities
from tests._attempts.dartlabUniverse.identity.ledger import (
    AliasRecord,
    IdentifierRef,
    IdentityEvidence,
    buildIdentityLedger,
)
from tests._attempts.dartlabUniverse.identity.resolver import ResolutionState, resolveOrganization
from tests._attempts.dartlabUniverse.ids import dartOrganizationId, edgarOrganizationId, logicalId


def _evidence(
    entityId: str,
    jurisdiction: str,
    canonical: IdentifierRef,
    legalName: str,
    aliases: tuple[AliasRecord, ...],
) -> IdentityEvidence:
    return IdentityEvidence(
        entityId=entityId,
        jurisdiction=jurisdiction,
        canonicalIdentifier=canonical,
        legalName=legalName,
        aliases=aliases,
        sourceRef="FIXTURE_IDENTITY",
        sourceRevision="a" * 64,
        rowLocator=f"entity={entityId}",
        observedAt="2026-07-18T00:00:00Z",
    )


def _alias(namespace: str, value: str, validFrom=None, validTo=None) -> AliasRecord:
    return AliasRecord(namespace, value, validFrom, validTo, "fixture:evidence")


def testSameNameOrganizationsRemainAmbiguous():
    first = _evidence(
        dartOrganizationId("00000001"),
        "KR",
        IdentifierRef("DART_CORP_CODE", "00000001"),
        "동일상사",
        (_alias("LEGAL_NAME_KO", "동일상사"),),
    )
    second = _evidence(
        dartOrganizationId("00000002"),
        "KR",
        IdentifierRef("DART_CORP_CODE", "00000002"),
        "동일상사",
        (_alias("LEGAL_NAME_KO", "동일상사"),),
    )
    result = resolveOrganization(
        (IdentifierRef("LEGAL_NAME_KO", "동일상사"),),
        buildIdentityLedger((first, second)),
    )
    assert result.state is ResolutionState.AMBIGUOUS
    assert set(result.candidateEntityIds) == {first.entityId, second.entityId}


def testTickerChangeDelistingAndRelistingUseValidityIntervals():
    old = _evidence(
        edgarOrganizationId("1"),
        "US",
        IdentifierRef("SEC_CIK", "1"),
        "Old Corp",
        (_alias("US_TICKER", "MAGIC", "2010-01-01T00:00:00Z", "2020-01-01T00:00:00Z"),),
    )
    current = _evidence(
        edgarOrganizationId("2"),
        "US",
        IdentifierRef("SEC_CIK", "2"),
        "New Corp",
        (_alias("US_TICKER", "MAGIC", "2022-01-01T00:00:00Z", None),),
    )
    ledger = buildIdentityLedger((old, current))

    before = resolveOrganization(
        (IdentifierRef("US_TICKER", "MAGIC"),),
        ledger,
        validAt="2019-01-01T00:00:00Z",
    )
    gap = resolveOrganization(
        (IdentifierRef("US_TICKER", "MAGIC"),),
        ledger,
        validAt="2021-01-01T00:00:00Z",
    )
    after = resolveOrganization(
        (IdentifierRef("US_TICKER", "MAGIC"),),
        ledger,
        validAt="2023-01-01T00:00:00Z",
    )
    assert before.entityId == old.entityId
    assert gap.state is ResolutionState.UNRESOLVED
    assert after.entityId == current.entityId


def testCrossListedMergerAndSpinOffCandidatesNeverAutoMerge():
    korean = _evidence(
        dartOrganizationId("00126380"),
        "KR",
        IdentifierRef("DART_CORP_CODE", "00126380"),
        "Example Holdings",
        (_alias("LEGAL_NAME_EN", "Example Holdings"), _alias("KR_STOCK_CODE", "005930")),
    )
    american = _evidence(
        edgarOrganizationId("320193"),
        "US",
        IdentifierRef("SEC_CIK", "320193"),
        "Example Holdings",
        (_alias("LEGAL_NAME_EN", "Example Holdings"), _alias("US_TICKER", "EXM")),
    )
    result = resolveOrganization(
        (
            IdentifierRef("DART_CORP_CODE", "00126380"),
            IdentifierRef("SEC_CIK", "320193"),
        ),
        buildIdentityLedger((korean, american)),
    )
    assert result.state is ResolutionState.CONFLICTING_IDENTIFIERS
    assert set(result.candidateEntityIds) == {korean.entityId, american.entityId}


def testConceptMappingPreservesAccountingBasisAndConflict():
    ifrs = ConceptMappingRecord(
        "KIFRS",
        "Revenue",
        "REVENUE",
        MappingType.EXACT,
        "consolidated",
        "currency",
        "as-reported",
        "duration",
        "evidence:ifrs",
        True,
        "v1",
    )
    usGaap = ConceptMappingRecord(
        "US-GAAP",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "REVENUE",
        MappingType.NARROWER,
        "consolidated",
        "currency",
        "as-reported",
        "duration",
        "evidence:gaap",
        True,
        "v1",
    )
    unresolved = ConceptMappingRecord(
        "KIFRS",
        "CustomMember",
        None,
        MappingType.UNRESOLVED,
        None,
        None,
        None,
        None,
        "evidence:custom",
        True,
        "v1",
    )
    ledger = buildConceptMappingLedger((ifrs, usGaap, unresolved))
    assert resolveConcept("Revenue", ledger, sourceNamespace="KIFRS").state is MappingState.RESOLVED
    assert (
        resolveConcept(
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            ledger,
            sourceNamespace="US-GAAP",
        )
        .candidates[0]
        .mappingType
        is MappingType.NARROWER
    )
    assert resolveConcept("CustomMember", ledger, sourceNamespace="KIFRS").state is MappingState.UNRESOLVED


def testLiveDartAndEdgarIdentityAuthoritiesEnumerateWithoutCollision():
    census = censusIdentitySources()

    assert census.totalEntityCount
    assert census.crossSourceEntityCollisions == ()
    assert all(source.entityCount and len(source.sourceRevisions) == 1 for source in census.sources)
    assert all(source.duplicateEntityIds == () for source in census.sources)
    assert all(source.duplicateCanonicalKeys == () for source in census.sources)
    assert logicalId("identity-ledger", (census.digest,))
