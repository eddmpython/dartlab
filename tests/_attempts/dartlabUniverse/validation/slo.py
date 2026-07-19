"""Universe U3 runtime catalog와 evidence graph의 제품 SLO 측정기."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, fields, replace

from ..canonical import canonicalDigest
from ..catalog.models import CatalogState
from ..catalog.snapshot import CatalogSnapshot, validateCatalogSnapshot
from ..catalog.store import InMemoryCatalog
from ..contracts import Visibility
from ..graph.query import GraphStore, TraversalBudget
from ..graph.relations import GraphRelation
from .runtimeEnvironment import memoryEnvironment, runtimeEnvironment


@dataclass(frozen=True, slots=True)
class U3SloThresholds:
    exactLookupP50Ms: float = 30.0
    exactLookupP95Ms: float = 100.0
    exactLookupP99Ms: float = 300.0
    objectDetailP50Ms: float = 80.0
    objectDetailP95Ms: float = 300.0
    objectDetailP99Ms: float = 1000.0
    graphTraversalP50Ms: float = 100.0
    graphTraversalP95Ms: float = 300.0
    graphTraversalP99Ms: float = 1000.0
    snapshotReplayMs: float = 5000.0


@dataclass(frozen=True, slots=True)
class U3RuntimeSloReport:
    passed: bool
    catalogDigest: str
    snapshotId: str
    sourceRevisionDigest: str
    thresholdDigest: str
    runtimeEnvironment: tuple[tuple[str, str], ...]
    resourceCount: int
    objectCount: int
    relationCount: int
    sampleCount: int
    catalogProjectionBuildMs: float
    graphIndexBuildMs: float
    exactLookupP50Ms: float
    exactLookupP95Ms: float
    exactLookupP99Ms: float
    objectDetailP50Ms: float
    objectDetailP95Ms: float
    objectDetailP99Ms: float
    graphTraversalP50Ms: float
    graphTraversalP95Ms: float
    graphTraversalP99Ms: float
    snapshotReplayMs: float
    processPeakRssBytes: int | None
    failureCodes: tuple[str, ...]
    digest: str


def _percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * quantile) - 1))
    return ordered[index]


def _sample(values: tuple[str, ...], count: int) -> tuple[str, ...]:
    if not values:
        raise ValueError("SLO sample source가 비어 있음")
    if len(values) >= count:
        return tuple(values[index * len(values) // count] for index in range(count))
    return tuple(values[index % len(values)] for index in range(count))


def _milliseconds(call) -> float:
    started = time.perf_counter_ns()
    call()
    return (time.perf_counter_ns() - started) / 1_000_000


def benchmarkU3Runtime(
    catalog: CatalogState,
    relations: tuple[GraphRelation, ...],
    snapshot: CatalogSnapshot,
    *,
    sampleCount: int = 200,
    thresholds: U3SloThresholds | None = None,
) -> U3RuntimeSloReport:
    """실제 runtime projection과 bounded graph query의 p50, p95, p99를 측정한다."""
    if sampleCount < 10:
        raise ValueError("SLO sampleCount는 10 이상이어야 함")
    activeThresholds = thresholds or U3SloThresholds()
    if any(
        isinstance(value := getattr(activeThresholds, field.name), bool) or not math.isfinite(value) or value <= 0
        for field in fields(activeThresholds)
    ):
        raise ValueError("SLO threshold는 0보다 큰 유한값이어야 함")
    allowedVisibility = frozenset(Visibility)
    resourceRefs = _sample(tuple(item.resourceVersionId for item in catalog.resources), sampleCount)
    objectRefs = _sample(tuple(item.objectId for item in catalog.objects), sampleCount)

    projectionStarted = time.perf_counter_ns()
    with InMemoryCatalog(catalog) as store:
        catalogProjectionBuildMs = (time.perf_counter_ns() - projectionStarted) / 1_000_000
        for resourceRef, objectRef in zip(resourceRefs[:5], objectRefs[:5], strict=True):
            store.resourceByVersion(resourceRef, allowedVisibility=allowedVisibility)
            store.objectDetail(objectRef, allowedVisibility=allowedVisibility)
        exactSamples = [
            _milliseconds(
                lambda resourceRef=resourceRef: store.resourceByVersion(
                    resourceRef,
                    allowedVisibility=allowedVisibility,
                )
            )
            for resourceRef in resourceRefs
        ]
        detailSamples = [
            _milliseconds(
                lambda objectRef=objectRef: store.objectDetail(
                    objectRef,
                    allowedVisibility=allowedVisibility,
                )
            )
            for objectRef in objectRefs
        ]

    graphStarted = time.perf_counter_ns()
    graph = GraphStore((), relations)
    graphIndexBuildMs = (time.perf_counter_ns() - graphStarted) / 1_000_000
    traversalBudget = TraversalBudget(maxDepth=3, maxNodes=1000, maxEdges=5000)
    for objectRef in objectRefs[:5]:
        graph.traverse(
            (objectRef,),
            validAt="9999-12-30T00:00:00Z",
            knownAt="9999-12-30T00:00:00Z",
            allowedVisibility=allowedVisibility,
            budget=traversalBudget,
        )
    graphSamples = [
        _milliseconds(
            lambda objectRef=objectRef: graph.traverse(
                (objectRef,),
                validAt="9999-12-30T00:00:00Z",
                knownAt="9999-12-30T00:00:00Z",
                allowedVisibility=allowedVisibility,
                budget=traversalBudget,
            )
        )
        for objectRef in objectRefs
    ]

    snapshotStarted = time.perf_counter_ns()
    snapshotIssues = validateCatalogSnapshot(snapshot)
    snapshotReplayMs = (time.perf_counter_ns() - snapshotStarted) / 1_000_000
    failures = []
    exactP50 = _percentile(exactSamples, 0.5)
    exactP95 = _percentile(exactSamples, 0.95)
    exactP99 = _percentile(exactSamples, 0.99)
    detailP50 = _percentile(detailSamples, 0.5)
    detailP95 = _percentile(detailSamples, 0.95)
    detailP99 = _percentile(detailSamples, 0.99)
    graphP50 = _percentile(graphSamples, 0.5)
    graphP95 = _percentile(graphSamples, 0.95)
    graphP99 = _percentile(graphSamples, 0.99)
    if exactP50 > activeThresholds.exactLookupP50Ms:
        failures.append("EXACT_LOOKUP_P50_SLO_EXCEEDED")
    if exactP95 > activeThresholds.exactLookupP95Ms:
        failures.append("EXACT_LOOKUP_P95_SLO_EXCEEDED")
    if exactP99 > activeThresholds.exactLookupP99Ms:
        failures.append("EXACT_LOOKUP_P99_SLO_EXCEEDED")
    if detailP50 > activeThresholds.objectDetailP50Ms:
        failures.append("OBJECT_DETAIL_P50_SLO_EXCEEDED")
    if detailP95 > activeThresholds.objectDetailP95Ms:
        failures.append("OBJECT_DETAIL_P95_SLO_EXCEEDED")
    if detailP99 > activeThresholds.objectDetailP99Ms:
        failures.append("OBJECT_DETAIL_P99_SLO_EXCEEDED")
    if graphP50 > activeThresholds.graphTraversalP50Ms:
        failures.append("GRAPH_TRAVERSAL_P50_SLO_EXCEEDED")
    if graphP95 > activeThresholds.graphTraversalP95Ms:
        failures.append("GRAPH_TRAVERSAL_P95_SLO_EXCEEDED")
    if graphP99 > activeThresholds.graphTraversalP99Ms:
        failures.append("GRAPH_TRAVERSAL_P99_SLO_EXCEEDED")
    if snapshotReplayMs > activeThresholds.snapshotReplayMs:
        failures.append("SNAPSHOT_REPLAY_SLO_EXCEEDED")
    if snapshotIssues:
        failures.append("SNAPSHOT_REPLAY_INVALID")
    base = U3RuntimeSloReport(
        passed=False,
        catalogDigest=catalog.digest,
        snapshotId=snapshot.snapshotId,
        sourceRevisionDigest=canonicalDigest(
            tuple(sorted({(item.sourceRef, item.sourceRevision) for item in snapshot.resources}))
        ),
        thresholdDigest=canonicalDigest(activeThresholds),
        runtimeEnvironment=runtimeEnvironment(
            cacheProfile="COLD_PROJECTION_WARM_LOOKUPS",
            networkProfile="NOT_APPLICABLE_RUNTIME_QUERY",
        ),
        resourceCount=len(catalog.resources),
        objectCount=len(catalog.objects),
        relationCount=len(relations),
        sampleCount=sampleCount,
        catalogProjectionBuildMs=round(catalogProjectionBuildMs, 6),
        graphIndexBuildMs=round(graphIndexBuildMs, 6),
        exactLookupP50Ms=round(exactP50, 6),
        exactLookupP95Ms=round(exactP95, 6),
        exactLookupP99Ms=round(exactP99, 6),
        objectDetailP50Ms=round(detailP50, 6),
        objectDetailP95Ms=round(detailP95, 6),
        objectDetailP99Ms=round(detailP99, 6),
        graphTraversalP50Ms=round(graphP50, 6),
        graphTraversalP95Ms=round(graphP95, 6),
        graphTraversalP99Ms=round(graphP99, 6),
        snapshotReplayMs=round(snapshotReplayMs, 6),
        processPeakRssBytes=memoryEnvironment()[1],
        failureCodes=tuple(sorted(set(failures))),
        digest="",
    )
    report = replace(base, passed=not base.failureCodes)
    return replace(report, digest=canonicalDigest(report))
