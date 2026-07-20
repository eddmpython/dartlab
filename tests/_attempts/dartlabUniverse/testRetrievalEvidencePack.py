"""Universe U4 G4E evidence pack replay와 mutation detection을 검증한다."""

from __future__ import annotations

from dataclasses import replace

from tests._attempts.dartlabUniverse.contracts import Visibility
from tests._attempts.dartlabUniverse.query.engine import UniverseQueryEngine
from tests._attempts.dartlabUniverse.query.models import QueryTimeContext, buildUniverseQuery
from tests._attempts.dartlabUniverse.query.planner import buildQueryPlan
from tests._attempts.dartlabUniverse.queryTestSupport import buildQueryRuntimeFixture
from tests._attempts.dartlabUniverse.validation.g4e import validateRetrievalEvidencePack


def _pack():
    runtime = buildQueryRuntimeFixture()
    query = buildUniverseQuery(
        "Apple SEC_CIK:0000320193",
        timeContext=QueryTimeContext("2026-07-19T00:00:00Z", "2026-07-19T00:00:00Z"),
        allowedVisibility=frozenset({Visibility.LOCAL}),
    )
    plan = buildQueryPlan(query, runtime.snapshot)
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
    ) as engine:
        pack = engine.execute(query, plan=plan)
    return runtime, query, plan, pack


def testEvidencePackReplaysAgainstExactSnapshotWithoutModel():
    runtime, query, plan, pack = _pack()

    report = validateRetrievalEvidencePack(
        pack,
        query=query,
        plan=plan,
        snapshot=runtime.snapshot,
        catalog=runtime.catalog,
        graph=runtime.graph,
    )

    assert report.valid, report.issues
    assert report.checkedEvidenceCount == len(pack.candidateEvidence) + len(pack.contradictoryEvidence)
    assert report.checkedLaneCount == 5
    assert pack.sourceRevisionSet
    assert pack.executionRefs == ()


def testEvidenceMutationBreaksPackDigestAndCatalogBinding():
    runtime, query, plan, pack = _pack()
    first = pack.candidateEvidence[0]
    mutatedEvidence = replace(first.evidence, contentDigest="0" * 64)
    mutated = replace(
        pack,
        candidateEvidence=(replace(first, evidence=mutatedEvidence), *pack.candidateEvidence[1:]),
    )

    report = validateRetrievalEvidencePack(
        mutated,
        query=query,
        plan=plan,
        snapshot=runtime.snapshot,
        catalog=runtime.catalog,
        graph=runtime.graph,
    )

    assert not report.valid
    assert {item.code for item in report.issues} >= {"PACK_DIGEST_MISMATCH", "EVIDENCE_CATALOG_MISMATCH"}


def testSameSnapshotAndQueryProduceSameImmutablePack():
    runtime, query, plan, first = _pack()
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
    ) as engine:
        second = engine.execute(query, plan=plan)

    assert second == first
    assert second.packId == first.packId
    assert second.digest == first.digest
