"""U4 기존 contentIndex adapter와 virtual filing evidence를 검증한다."""

from __future__ import annotations

from dataclasses import replace

from tests._attempts.dartlabUniverse.canonical import canonicalJson
from tests._attempts.dartlabUniverse.contracts import Visibility
from tests._attempts.dartlabUniverse.query.adapters import LexicalAdapterContext
from tests._attempts.dartlabUniverse.query.contentSearch import DartContentSearchAdapter
from tests._attempts.dartlabUniverse.query.engine import UniverseQueryEngine
from tests._attempts.dartlabUniverse.query.models import QueryTimeContext, buildUniverseQuery
from tests._attempts.dartlabUniverse.query.planner import buildQueryPlan
from tests._attempts.dartlabUniverse.queryTestSupport import buildQueryRuntimeFixture
from tests._attempts.dartlabUniverse.validation.g4e import validateRetrievalEvidencePack


def _rows(_queryText: str, _limit: int) -> tuple[dict[str, object], ...]:
    return (
        {
            "score": 9.5,
            "source": "allFilings",
            "sourceRef": "dart:allFilings:20260615000001#section=2",
            "dataAsOf": "20260615",
            "rcept_no": "20260615000001",
            "section_order": 2,
            "scope": "content",
            "dartUrl": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260615000001",
            "snippet": "전환사채 발행 목적은 운영자금 조달이다.",
            "fieldCards": '[{"label":"chunk","evidence":"전환사채 발행"}]',
        },
        {
            "score": 4.0,
            "source": "news",
            "sourceRef": "news:fixture:abc",
            "dataAsOf": "20260614",
            "scope": "news",
            "url": "javascript:alert(1)",
            "snippet": "전환사채 관련 뉴스",
        },
    )


def _query():
    return buildUniverseQuery(
        "전환사채 발행 목적",
        timeContext=QueryTimeContext("2026-07-19T00:00:00Z", "2026-07-19T00:00:00Z"),
        allowedVisibility=frozenset({Visibility.PUBLIC}),
    )


def _publicAnchor(runtime):
    return next(
        item.resourceVersionId
        for item in runtime.catalog.resources
        if item.visibility is Visibility.PUBLIC
        and any(item.resourceVersionId in obj.resourceRefs for obj in runtime.catalog.objects)
    )


def testExistingContentIndexResultBecomesDrillableEvidenceWithoutRawSnippet():
    runtime = buildQueryRuntimeFixture()
    adapter = DartContentSearchAdapter(
        runtime.catalog,
        searchCallable=_rows,
        indexResourceVersionId=_publicAnchor(runtime),
    )
    query = _query()
    plan = buildQueryPlan(query, runtime.snapshot)
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
        lexicalAdapters=(adapter,),
    ) as engine:
        pack = engine.execute(query, plan=plan)

    hits = tuple(item for item in pack.candidateEvidence if item.candidateKind == "CONTENT_HIT")
    assert len(hits) == 2
    assert dict(hits[0].evidence.selector)["sourceRef"].startswith("dart:allFilings:")
    assert dict(hits[0].evidence.selector)["url"].startswith("https://dart.fss.or.kr/")
    assert dict(hits[1].evidence.selector)["url"] == ""
    assert hits[0].evidence.quoteDigest
    assert b"\xec\xa0\x84\xed\x99\x98\xec\x82\xac\xec\xb1\x84 \xeb\xb0\x9c\xed\x96\x89" not in canonicalJson(pack)
    assert adapter.latestRun is not None and adapter.latestRun.acceptedHitCount == 2


def testFreshAdapterReplayValidatesContentHitWithoutModel():
    runtime = buildQueryRuntimeFixture()
    anchor = _publicAnchor(runtime)
    adapter = DartContentSearchAdapter(runtime.catalog, searchCallable=_rows, indexResourceVersionId=anchor)
    query = _query()
    plan = buildQueryPlan(query, runtime.snapshot)
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
        lexicalAdapters=(adapter,),
    ) as engine:
        pack = engine.execute(query, plan=plan)
    replay = DartContentSearchAdapter(runtime.catalog, searchCallable=_rows, indexResourceVersionId=anchor)
    publicResources = {
        item.resourceVersionId: item for item in runtime.catalog.resources if item.visibility is Visibility.PUBLIC
    }
    publicObjects = {
        item.objectId: item
        for item in runtime.catalog.objects
        if item.visibility is Visibility.PUBLIC and set(item.resourceRefs).issubset(publicResources)
    }
    replay.search(
        query,
        LexicalAdapterContext(frozenset({Visibility.PUBLIC}), publicObjects, publicResources),
    )

    report = validateRetrievalEvidencePack(
        pack,
        query=query,
        plan=plan,
        snapshot=runtime.snapshot,
        catalog=runtime.catalog,
        graph=runtime.graph,
        virtualRetrievedVerifiers=(replay.verifyRetrieved,),
    )

    assert report.valid, report.issues


def testContentHitMutationAndVisibilityBypassAreRejected():
    runtime = buildQueryRuntimeFixture()
    adapter = DartContentSearchAdapter(
        runtime.catalog,
        searchCallable=_rows,
        indexResourceVersionId=_publicAnchor(runtime),
    )
    query = _query()
    plan = buildQueryPlan(query, runtime.snapshot)
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
        lexicalAdapters=(adapter,),
    ) as engine:
        pack = engine.execute(query, plan=plan)
    first = next(item for item in pack.candidateEvidence if item.candidateKind == "CONTENT_HIT")
    mutatedEvidence = replace(first.evidence, sourceRevision="0" * 40)
    mutatedItems = tuple(
        replace(item, evidence=mutatedEvidence) if item is first else item for item in pack.candidateEvidence
    )
    mutated = replace(pack, candidateEvidence=mutatedItems)

    report = validateRetrievalEvidencePack(
        mutated,
        query=query,
        plan=plan,
        snapshot=runtime.snapshot,
        catalog=runtime.catalog,
        graph=runtime.graph,
        virtualRetrievedVerifiers=(adapter.verifyRetrieved,),
    )

    assert not report.valid
    assert {item.code for item in report.issues} >= {"PACK_DIGEST_MISMATCH", "EVIDENCE_CATALOG_MISMATCH"}

    calls = []
    localAnchor = next(
        item.resourceVersionId for item in runtime.catalog.resources if item.visibility is Visibility.LOCAL
    )
    hiddenAdapter = DartContentSearchAdapter(
        runtime.catalog,
        searchCallable=lambda queryText, limit: calls.append((queryText, limit)) or _rows(queryText, limit),
        indexResourceVersionId=localAnchor,
    )
    publicResources = {
        item.resourceVersionId: item for item in runtime.catalog.resources if item.visibility is Visibility.PUBLIC
    }
    publicObjects = {
        item.objectId: item
        for item in runtime.catalog.objects
        if item.visibility is Visibility.PUBLIC and set(item.resourceRefs).issubset(publicResources)
    }
    hidden = hiddenAdapter.search(
        query,
        LexicalAdapterContext(frozenset({Visibility.PUBLIC}), publicObjects, publicResources),
    )
    assert hidden.hits == ()
    assert calls == []
