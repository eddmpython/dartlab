"""U4 기존 contentIndex adapter와 virtual filing evidence를 검증한다."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import polars as pl
import pytest

from tests._attempts.dartlabUniverse.canonical import canonicalJson
from tests._attempts.dartlabUniverse.contracts import Visibility
from tests._attempts.dartlabUniverse.query.adapters import LexicalAdapterContext
from tests._attempts.dartlabUniverse.query.contentSearch import (
    DartContentSearchAdapter,
    _bindLocalContentIndex,
    _defaultSearch,
)
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


@pytest.mark.parametrize(
    ("namespace", "identifier", "source", "sourceRef"),
    (
        ("DART_RCEPT_NO", "20260701900720", "allFilings", "dart:allFilings:20260701900720#section=0"),
        ("SEC_ACCESSION", "0001039399-26-000009", "edgar-panel", "edgar:panel:0001039399-26-000009#section=0"),
    ),
)
def testDartReceiptAndSecAccessionAreSourceNativeExactRankOne(namespace, identifier, source, sourceRef):
    runtime = buildQueryRuntimeFixture()

    def exactRows(value: str, _limit: int) -> tuple[dict[str, object], ...]:
        assert value == identifier
        return (
            {
                "rcept_no": identifier,
                "source": source,
                "sourceRef": sourceRef,
                "sourceDataAsOf": "20260708",
                "section_order": 0,
                "scope": "content",
            },
        )

    adapter = DartContentSearchAdapter(
        runtime.catalog,
        searchCallable=lambda _queryText, _limit: (),
        exactSearchCallable=exactRows,
        indexResourceVersionId=_publicAnchor(runtime),
    )
    query = buildUniverseQuery(
        f"{namespace}:{identifier}",
        timeContext=QueryTimeContext("2026-07-19T00:00:00Z", "2026-07-19T00:00:00Z"),
        allowedVisibility=frozenset({Visibility.PUBLIC}),
    )
    plan = buildQueryPlan(query, runtime.snapshot)
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        exactAdapters=(adapter,),
    ) as engine:
        pack = engine.execute(query, plan=plan)

    first = pack.candidateEvidence[0]
    assert first.rank == 1
    assert first.candidateKind == "CONTENT_HIT"
    assert dict(first.evidence.selector)["sourceRef"] == sourceRef
    assert any(item.lane.value == "EXACT" for item in first.scoreProvenance)
    assert adapter.latestRuns[0].lane.value == "EXACT"

    report = validateRetrievalEvidencePack(
        pack,
        query=query,
        plan=plan,
        snapshot=runtime.snapshot,
        catalog=runtime.catalog,
        graph=runtime.graph,
        virtualRetrievedVerifiers=(adapter.verifyRetrieved,),
    )
    assert report.valid, report.issues


def testLocalContentIndexArtifactsMustMatchCatalogResources(tmp_path, monkeypatch):
    runtime = buildQueryRuntimeFixture()
    active = tmp_path / "active"
    active.mkdir()
    payloads = {
        "main_meta.parquet": b"metadata",
        "main.postings.bin": b"postings",
    }
    fileHashes = {}
    fileSources = {}
    resources = []
    anchor = runtime.catalog.resources[0]
    for index, (name, payload) in enumerate(payloads.items()):
        (active / name).write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        sourcePath = f"dart/contentIndex/lite/_staging/fixture/{name}"
        fileHashes[name] = digest
        fileSources[name] = sourcePath
        resources.append(
            replace(
                anchor,
                resourceId=f"du:v1:hf-file:{index:064x}",
                resourceVersionId=f"du:v1:hf-file-version:{index:064x}",
                locator=(("path", sourcePath), ("lfsSha256", digest)),
                contentDigest=digest,
                byteSize=len(payload),
            )
        )
    (active / "manifest.json").write_text(
        json.dumps({"fileHashes": fileHashes, "fileSources": fileSources}),
        encoding="utf-8",
    )
    catalog = replace(runtime.catalog, resources=tuple(resources))
    monkeypatch.setattr("dartlab.providers.dart.search.fieldIndex._activeIndexDir", lambda: active)

    binding = _bindLocalContentIndex(catalog)
    assert binding.metaResourceVersionId == resources[0].resourceVersionId
    assert set(binding.resourceVersionIds) == {item.resourceVersionId for item in resources}

    (active / "main.postings.bin").write_bytes(b"mutated")
    with pytest.raises(ValueError, match="digest 불일치"):
        _bindLocalContentIndex(catalog)


def testDefaultContentSearchAppliesSourceIntentBeforeRanking(monkeypatch):
    calls = []

    def searchContent(queryText: str, *, sourceKind: str | None, limit: int):
        calls.append((queryText, sourceKind, limit))
        return pl.DataFrame({"sourceRef": ["edgar:panel:fixture"]})

    monkeypatch.setattr("dartlab.providers.dart.search.fieldIndex.searchContent", searchContent)

    rows = _defaultSearch("Apple Form 10-K", 20)

    assert calls == [("Apple Form 10-K", "filing", 20)]
    assert rows == ({"sourceRef": "edgar:panel:fixture"},)
