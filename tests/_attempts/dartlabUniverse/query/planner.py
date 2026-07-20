"""U4 allowlist-only deterministic query planner."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ..canonical import canonicalDigest
from ..catalog.snapshot import CatalogSnapshot
from .models import QueryLane, UniverseQuery

QUERY_PLAN_SCHEMA_VERSION = "du-query-plan-v1"


@dataclass(frozen=True, slots=True)
class QueryStep:
    ordinal: int
    lane: QueryLane
    operation: str
    limit: int
    dependsOn: tuple[QueryLane, ...]
    required: bool


@dataclass(frozen=True, slots=True)
class QueryPlan:
    schemaVersion: str
    queryId: str
    snapshotId: str
    snapshotRootInputsDigest: str
    queryDigest: str
    visibilityPolicyDigest: str
    steps: tuple[QueryStep, ...]
    allowsCapabilityExecution: bool
    allowsExternalToolCalls: bool
    digest: str


def visibilityPolicyDigest(query: UniverseQuery) -> str:
    return canonicalDigest(
        {
            "allowedVisibility": query.allowedVisibility,
            "policy": "PRE_FILTER_FAIL_CLOSED",
            "unknownVisibility": "DENY",
        }
    )


def buildQueryPlan(query: UniverseQuery, snapshot: CatalogSnapshot) -> QueryPlan:
    """고정된 읽기 전용 operation만 배치하며 query text로 실행 단계를 만들지 않는다."""
    if snapshot.catalogDigest == "" or snapshot.rootInputsDigest == "":
        raise ValueError("query plan에는 완전한 catalog snapshot이 필요함")
    steps = (
        QueryStep(0, QueryLane.EXACT, "LOOKUP_EXACT_REFS", query.budget.exactLimit, (), True),
        QueryStep(1, QueryLane.STRUCTURED, "FILTER_CATALOG_AND_STATEMENTS", query.budget.structuredLimit, (), True),
        QueryStep(2, QueryLane.LEXICAL, "SCAN_VISIBLE_METADATA", query.budget.lexicalLimit, (), True),
        QueryStep(
            3,
            QueryLane.GRAPH,
            "TRAVERSE_VISIBLE_EVIDENCE_GRAPH",
            query.budget.graphMaxNodes,
            (QueryLane.EXACT, QueryLane.STRUCTURED, QueryLane.LEXICAL),
            True,
        ),
        QueryStep(
            4,
            QueryLane.CONTRADICTION,
            "SEARCH_CONFLICTS",
            query.budget.structuredLimit,
            (QueryLane.STRUCTURED, QueryLane.GRAPH),
            True,
        ),
    )
    base = QueryPlan(
        schemaVersion=QUERY_PLAN_SCHEMA_VERSION,
        queryId=query.queryId,
        snapshotId=snapshot.snapshotId,
        snapshotRootInputsDigest=snapshot.rootInputsDigest,
        queryDigest=query.digest,
        visibilityPolicyDigest=visibilityPolicyDigest(query),
        steps=steps,
        allowsCapabilityExecution=False,
        allowsExternalToolCalls=False,
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))
