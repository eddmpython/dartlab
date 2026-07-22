"""U4 blog 전체 AST lexical retrieval과 virtual evidence replay를 검증한다."""

from __future__ import annotations

from dataclasses import replace
from functools import cache

from tests._attempts.dartlabUniverse.census import defaultRepoRoot
from tests._attempts.dartlabUniverse.contracts import Visibility
from tests._attempts.dartlabUniverse.query.blogAst import BlogAstIndex
from tests._attempts.dartlabUniverse.query.engine import UniverseQueryEngine
from tests._attempts.dartlabUniverse.query.models import QueryTimeContext, buildUniverseQuery
from tests._attempts.dartlabUniverse.query.planner import buildQueryPlan
from tests._attempts.dartlabUniverse.queryTestSupport import buildQueryRuntimeFixture
from tests._attempts.dartlabUniverse.validation.g4e import validateRetrievalEvidencePack


@cache
def _blogIndex() -> BlogAstIndex:
    runtime = buildQueryRuntimeFixture()
    return BlogAstIndex(defaultRepoRoot(), runtime.catalog)


def _queryAndPack():
    runtime = buildQueryRuntimeFixture()
    index = _blogIndex()
    query = buildUniverseQuery(
        "54V는 왜 갑자기 200kg의 구리가 되는가",
        timeContext=QueryTimeContext("9999-12-30T00:00:00Z", "9999-12-30T00:00:00Z"),
        allowedVisibility=frozenset({Visibility.PUBLIC}),
    )
    plan = buildQueryPlan(query, runtime.snapshot)
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
        lexicalAdapters=(index,),
    ) as engine:
        pack = engine.execute(query, plan=plan)
    return runtime, index, query, plan, pack


def testBlogAstCoversFrontmatterBodyTableCodeImageLinkAndVideo():
    runtime = buildQueryRuntimeFixture()
    index = _blogIndex()
    blogPostCount = sum(item.objectKind == "BLOG_POST" for item in runtime.catalog.objects)
    kinds = {item.blockKind for item in index.blocks}

    assert index.report.postCount == blogPostCount
    assert index.report.blockCount == len(index.blocks)
    assert index.report.staleResourceCount == 0
    assert index.report.parseErrors == ()
    assert {
        "FRONTMATTER_FIELD",
        "HEADING",
        "PARAGRAPH",
        "TABLE_ROW",
        "CODE_BLOCK",
        "IMAGE",
        "LINK",
        "EXTERNAL_VIDEO",
    }.issubset(kinds)
    assert index.report.frontmatterFieldCount > blogPostCount
    assert index.report.imageCount > 0
    assert index.report.linkCount > 0
    assert index.report.externalVideoCount > 0


def testBlogBodyQueryReturnsOriginalMarkdownAstLocator():
    runtime, _index, _query, _plan, pack = _queryAndPack()
    target = next(
        item
        for item in runtime.catalog.objects
        if item.objectKind == "BLOG_POST" and "GPU 코어는 1V 미만" in item.canonicalLabel
    )
    hits = tuple(item for item in pack.candidateEvidence if item.candidateRef == target.objectId)

    assert hits
    assert hits[0].rank == 1
    assert dict(hits[0].evidence.selector)["astPath"].startswith("/blocks/")
    assert dict(hits[0].evidence.selector)["blockKind"] in {"HEADING", "PARAGRAPH"}
    assert hits[0].evidence.quoteDigest
    assert "text" not in dict(hits[0].evidence.selector)


def testBlogImageAltQueryKeepsImageEvidenceKind():
    runtime = buildQueryRuntimeFixture()
    index = _blogIndex()
    query = buildUniverseQuery(
        "사업보고서 전체를 panel 위치 지도로 여는 흐름",
        timeContext=QueryTimeContext("9999-12-30T00:00:00Z", "9999-12-30T00:00:00Z"),
        allowedVisibility=frozenset({Visibility.PUBLIC}),
    )
    plan = buildQueryPlan(query, runtime.snapshot)
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
        lexicalAdapters=(index,),
    ) as engine:
        pack = engine.execute(query, plan=plan)

    assert any(dict(item.evidence.selector).get("blockKind") == "IMAGE" for item in pack.candidateEvidence[:20])


def testG4EReparsesVirtualBlogEvidenceWithoutModel():
    runtime, index, query, plan, pack = _queryAndPack()

    rejected = validateRetrievalEvidencePack(
        pack,
        query=query,
        plan=plan,
        snapshot=runtime.snapshot,
        catalog=runtime.catalog,
        graph=runtime.graph,
    )
    accepted = validateRetrievalEvidencePack(
        pack,
        query=query,
        plan=plan,
        snapshot=runtime.snapshot,
        catalog=runtime.catalog,
        graph=runtime.graph,
        virtualRetrievedVerifiers=(index.verifyRetrieved,),
    )

    assert not rejected.valid
    assert "EVIDENCE_CATALOG_MISMATCH" in {item.code for item in rejected.issues}
    assert accepted.valid, accepted.issues


def testVirtualBlogEvidenceMutationCannotPassResolver():
    runtime, index, query, plan, pack = _queryAndPack()
    first = pack.candidateEvidence[0]
    changed = replace(first.evidence, quoteDigest="0" * 64)
    mutated = replace(pack, candidateEvidence=(replace(first, evidence=changed), *pack.candidateEvidence[1:]))

    report = validateRetrievalEvidencePack(
        mutated,
        query=query,
        plan=plan,
        snapshot=runtime.snapshot,
        catalog=runtime.catalog,
        graph=runtime.graph,
        virtualRetrievedVerifiers=(index.verifyRetrieved,),
    )

    assert not report.valid
    assert {item.code for item in report.issues} >= {"PACK_DIGEST_MISMATCH", "EVIDENCE_CATALOG_MISMATCH"}
