"""Universe U4 query contract와 allowlist planner를 검증한다."""

from __future__ import annotations

from tests._attempts.dartlabUniverse.contracts import Visibility
from tests._attempts.dartlabUniverse.query.models import (
    REQUIRED_QUERY_LANES,
    QueryFilters,
    QueryTimeContext,
    buildUniverseQuery,
)
from tests._attempts.dartlabUniverse.query.planner import buildQueryPlan
from tests._attempts.dartlabUniverse.queryTestSupport import buildQueryRuntimeFixture


def _time() -> QueryTimeContext:
    return QueryTimeContext("2026-07-19T00:00:00Z", "2026-07-19T00:00:00Z")


def testQueryStoresDigestAndTermsButNotRawText():
    query = buildUniverseQuery(
        "삼성전자 DART_CORP_CODE:00126380 자산",
        timeContext=_time(),
        allowedVisibility=frozenset({Visibility.LOCAL}),
    )

    assert query.queryTextDigest
    assert "삼성전자" in query.searchTerms
    assert query.explicitIdentifiers == ("DART_CORP_CODE:00126380",)
    assert not hasattr(query, "queryText")


def testPlannerAlwaysCoversFiveReadOnlyLanes():
    runtime = buildQueryRuntimeFixture()
    query = buildUniverseQuery(
        "Apple SEC_CIK:320193",
        timeContext=_time(),
        allowedVisibility=frozenset({Visibility.LOCAL}),
        filters=QueryFilters(sourceKinds=("IDENTITY_AUTHORITY",)),
    )
    plan = buildQueryPlan(query, runtime.snapshot)

    assert tuple(step.lane.value for step in plan.steps) == REQUIRED_QUERY_LANES
    assert not plan.allowsCapabilityExecution
    assert not plan.allowsExternalToolCalls
    assert plan.queryId == query.queryId
    assert plan.snapshotId == runtime.snapshot.snapshotId
