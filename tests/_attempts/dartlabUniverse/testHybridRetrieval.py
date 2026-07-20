"""Universe U4 exact, structured, lexical, graph, contradiction retrieval을 검증한다."""

from __future__ import annotations

from tests._attempts.dartlabUniverse.contracts import Visibility
from tests._attempts.dartlabUniverse.query.engine import UniverseQueryEngine
from tests._attempts.dartlabUniverse.query.models import QueryFilters, QueryTimeContext, buildUniverseQuery
from tests._attempts.dartlabUniverse.queryTestSupport import buildQueryRuntimeFixture


def _time() -> QueryTimeContext:
    return QueryTimeContext("2026-07-19T00:00:00Z", "2026-07-19T00:00:00Z")


def _execute(runtime, text: str, *, filters: QueryFilters | None = None, visibility=None):
    query = buildUniverseQuery(
        text,
        timeContext=_time(),
        allowedVisibility=visibility or frozenset({Visibility.LOCAL}),
        filters=filters,
    )
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
    ) as engine:
        return query, engine.execute(query)


def testDartAndEdgarIdentifiersResolveAtRankOne():
    runtime = buildQueryRuntimeFixture()

    _dartQuery, dartPack = _execute(runtime, "DART_CORP_CODE:00126380")
    _edgarQuery, edgarPack = _execute(runtime, "SEC_CIK:320193")

    assert dartPack.candidateEvidence[0].candidateRef == runtime.dartEntityId
    assert dartPack.candidateEvidence[0].rank == 1
    assert edgarPack.candidateEvidence[0].candidateRef == runtime.edgarEntityId
    assert edgarPack.candidateEvidence[0].rank == 1


def testStructuredStatementKeepsNumericUnitPeriodAndContradictionEvidence():
    runtime = buildQueryRuntimeFixture()
    filters = QueryFilters(
        subjectRefs=(runtime.dartEntityId,),
        predicates=("assets",),
        periodStart="2025-01-01",
        periodEnd="2025-12-31",
    )

    _query, pack = _execute(runtime, "삼성전자 연결 자산", filters=filters)

    statementRefs = {item.candidateRef for item in pack.candidateEvidence if item.candidateKind == "STATEMENT"}
    contradictionRefs = {item.candidateRef for item in pack.contradictoryEvidence}
    assert {item.statementId for item in runtime.statements}.issubset(statementRefs)
    assert contradictionRefs
    assert all(item.evidence.sourceRevision for item in pack.contradictoryEvidence)


def testKoreanAndEnglishMetadataParticipateInLexicalLane():
    runtime = buildQueryRuntimeFixture()

    _koreanQuery, koreanPack = _execute(runtime, "삼성전자")
    _englishQuery, englishPack = _execute(runtime, "Apple")

    assert any(item.candidateRef == runtime.dartEntityId for item in koreanPack.candidateEvidence)
    assert any(item.candidateRef == runtime.edgarEntityId for item in englishPack.candidateEvidence)
    assert next(item for item in koreanPack.laneCoverage if item.lane.value == "LEXICAL").candidateCount >= 1


def testPublicPolicyCannotSeePrivateObjectEvenByExactId():
    runtime = buildQueryRuntimeFixture()
    privateObject = next(item for item in runtime.catalog.objects if item.visibility is Visibility.PRIVATE)

    _query, pack = _execute(
        runtime,
        privateObject.objectId,
        filters=QueryFilters(exactRefs=(privateObject.objectId,)),
        visibility=frozenset({Visibility.PUBLIC}),
    )

    assert all(item.candidateRef != privateObject.objectId for item in pack.candidateEvidence)
    assert all(item.evidence.visibility is Visibility.PUBLIC for item in pack.candidateEvidence)
    assert next(item for item in pack.laneCoverage if item.lane.value == "EXACT").candidateCount == 0
