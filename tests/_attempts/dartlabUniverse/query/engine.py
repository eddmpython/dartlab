"""다섯 retrieval lane을 immutable evidence pack으로 합치는 U4 engine."""

from __future__ import annotations

from dataclasses import replace

from ..canonical import canonicalDigest
from ..catalog.models import CatalogState
from ..catalog.snapshot import CatalogSnapshot
from ..graph.query import GraphStore
from ..identity.ledger import IdentityLedger
from ..ids import logicalId
from .adapters import LexicalAdapterContext, LexicalQueryAdapter, mergeLexicalResults
from .capability import QueryCapabilityExecutor
from .lanes import LaneHit, LaneResult, VisibleQueryView
from .models import (
    RETRIEVAL_EVIDENCE_PACK_SCHEMA_VERSION,
    LaneContribution,
    LaneCoverage,
    QueryLane,
    RetrievalEvidencePack,
    RetrievedEvidence,
    UniverseQuery,
)
from .planner import QueryPlan, buildQueryPlan

_LANE_WEIGHTS = {
    QueryLane.EXACT: 4.0,
    QueryLane.STRUCTURED: 3.0,
    QueryLane.LEXICAL: 1.5,
    QueryLane.GRAPH: 1.25,
    QueryLane.CONTRADICTION: 1.0,
}


class UniverseQueryEngine:
    """Source payload를 복제하지 않는 process-local query runtime."""

    def __init__(
        self,
        catalog: CatalogState,
        snapshot: CatalogSnapshot,
        graph: GraphStore,
        *,
        identityLedger: IdentityLedger | None = None,
        lexicalAdapters: tuple[LexicalQueryAdapter, ...] = (),
        capabilityExecutor: QueryCapabilityExecutor | None = None,
    ) -> None:
        if catalog.digest != snapshot.catalogDigest:
            raise ValueError("query engine catalog와 snapshot digest가 다름")
        if {item.resourceVersionId for item in catalog.resources} != {
            item.resourceVersionId for item in snapshot.resources
        }:
            raise ValueError("query engine catalog와 snapshot resource set이 다름")
        self.catalog = catalog
        self.snapshot = snapshot
        self.graph = graph
        self.identityLedger = identityLedger
        self.lexicalAdapters = lexicalAdapters
        self.capabilityExecutor = capabilityExecutor
        self._views: dict[tuple[str, ...], VisibleQueryView] = {}

    def _view(self, query: UniverseQuery) -> VisibleQueryView:
        key = tuple(item.value for item in query.allowedVisibility)
        if key not in self._views:
            self._views[key] = VisibleQueryView(
                self.catalog,
                self.graph,
                allowedVisibility=frozenset(query.allowedVisibility),
            )
        return self._views[key]

    @staticmethod
    def _fusion(results: tuple[LaneResult, ...]) -> tuple[tuple[LaneHit, tuple[LaneContribution, ...], float], ...]:
        contributions: dict[tuple[str, str], list[LaneContribution]] = {}
        hitByKey: dict[tuple[str, str], LaneHit] = {}
        for result in results:
            weight = _LANE_WEIGHTS[result.lane]
            for rank, hit in enumerate(result.hits, start=1):
                key = (hit.candidateKind, hit.candidateRef)
                hitByKey[key] = hit
                contribution = weight * hit.laneScore / (60 + rank)
                contributions.setdefault(key, []).append(
                    LaneContribution(result.lane, rank, hit.laneScore, contribution, hit.reasonCodes)
                )
        fused = []
        for key, items in contributions.items():
            score = sum(item.fusionContribution for item in items)
            fused.append((hitByKey[key], tuple(sorted(items, key=lambda item: item.lane.value)), score))
        return tuple(sorted(fused, key=lambda item: (-item[2], item[0].candidateKind, item[0].candidateRef)))

    @staticmethod
    def _retrievedEvidence(
        view: VisibleQueryView,
        fused: tuple[tuple[LaneHit, tuple[LaneContribution, ...], float], ...],
        *,
        resultLimit: int,
    ) -> tuple[tuple[RetrievedEvidence, ...], tuple[str, ...], bool]:
        selected = fused[:resultLimit]
        unresolved = []
        anchors = []
        for rank, (hit, provenance, score) in enumerate(selected, start=1):
            evidence = view.evidenceForHit(hit)
            if not evidence:
                unresolved.append(f"NO_EVIDENCE:{hit.candidateKind}:{hit.candidateRef}")
                continue
            for item in evidence:
                anchors.append(
                    RetrievedEvidence(
                        candidateRef=hit.candidateRef,
                        candidateKind=hit.candidateKind,
                        rank=rank,
                        score=score,
                        scoreProvenance=provenance,
                        evidence=item,
                    )
                )
        return tuple(anchors), tuple(sorted(unresolved)), len(fused) > len(selected)

    def execute(self, query: UniverseQuery, *, plan: QueryPlan | None = None) -> RetrievalEvidencePack:
        """모든 lane을 실행하고 source locator까지 포함한 model-free evidence pack을 만든다."""
        activePlan = plan or buildQueryPlan(query, self.snapshot)
        if (
            activePlan.queryId != query.queryId
            or activePlan.queryDigest != query.digest
            or activePlan.snapshotId != self.snapshot.snapshotId
            or activePlan.allowsExternalToolCalls
        ):
            raise ValueError("query와 plan binding이 잘못됨")
        if activePlan.allowsCapabilityExecution != bool(query.capabilityRequests):
            raise ValueError("query와 capability plan binding이 잘못됨")
        if query.capabilityRequests and self.capabilityExecutor is None:
            raise ValueError("명시적 capability request에는 executor가 필요함")
        view = self._view(query)
        exact = view.exact(query, self.identityLedger)
        structured = view.structured(query)
        metadataLexical = view.lexical(query)
        adapterContext = LexicalAdapterContext(
            allowedVisibility=view.allowedVisibility,
            objectById=view.objectById,
            resourceByVersion=view.resourceByVersion,
        )
        lexical = mergeLexicalResults(
            (
                metadataLexical,
                *(adapter.search(query, adapterContext) for adapter in self.lexicalAdapters),
            ),
            limit=query.budget.lexicalLimit,
        )
        graph = view.graphLane(query, self.graph, (exact, structured, lexical))
        contradiction = view.contradiction(query, self.graph, (structured, graph))
        results = (exact, structured, lexical, graph, contradiction)
        primaryFusion = self._fusion((exact, structured, lexical, graph))
        contradictionFusion = self._fusion((contradiction,))
        candidateEvidence, unresolved, resultTruncated = self._retrievedEvidence(
            view,
            primaryFusion,
            resultLimit=query.budget.resultLimit,
        )
        contradictoryEvidence, contradictionUnresolved, contradictionTruncated = self._retrievedEvidence(
            view,
            contradictionFusion,
            resultLimit=query.budget.resultLimit,
        )
        laneCoverage = tuple(
            LaneCoverage(
                lane=result.lane,
                executed=True,
                candidateCount=result.candidateCount,
                returnedCount=len(result.hits),
                withheldCount=result.withheldCount,
                truncated=result.truncated,
                reasonCode=result.reasonCode,
            )
            for result in results
        )
        truncationReasons = tuple(
            sorted(
                {
                    *(f"{item.lane.value}:{item.reasonCode}" for item in laneCoverage if item.truncated),
                    *(("RESULT_LIMIT",) if resultTruncated else ()),
                    *(("CONTRADICTION_RESULT_LIMIT",) if contradictionTruncated else ()),
                }
            )
        )
        unresolvedReasons = tuple(sorted((*unresolved, *contradictionUnresolved)))
        executionResults = (
            tuple(
                self.capabilityExecutor.execute(query, self.snapshot, request) for request in query.capabilityRequests
            )
            if self.capabilityExecutor is not None
            else ()
        )
        executionRefs = tuple(sorted(item.executionRef for item in executionResults))
        unresolvedReasons = tuple(
            sorted(
                {
                    *unresolvedReasons,
                    *(
                        f"EXECUTION_STATUS:{item.capabilityId}:{item.status}"
                        for item in executionResults
                        if item.status not in {"SUCCEEDED", "PARTIAL"}
                    ),
                }
            )
        )
        allEvidence = (*candidateEvidence, *contradictoryEvidence)
        sourceRevisionSet = tuple(
            sorted({(item.evidence.sourceRef, item.evidence.sourceRevision) for item in allEvidence})
        )
        if not candidateEvidence:
            completeness = "ABSTAIN"
            unresolvedReasons = tuple(sorted({*unresolvedReasons, "NO_CANDIDATE_EVIDENCE"}))
        elif truncationReasons or unresolvedReasons:
            completeness = "PARTIAL"
        else:
            completeness = "COMPLETE"
        base = RetrievalEvidencePack(
            schemaVersion=RETRIEVAL_EVIDENCE_PACK_SCHEMA_VERSION,
            packId="",
            snapshotId=self.snapshot.snapshotId,
            snapshotRootInputsDigest=self.snapshot.rootInputsDigest,
            descriptorSetDigest=self.snapshot.descriptorSetDigest,
            recoverySetDigest=self.snapshot.recoverySetDigest,
            queryId=query.queryId,
            queryPlanDigest=activePlan.digest,
            visibilityPolicyDigest=activePlan.visibilityPolicyDigest,
            sourceRevisionSet=sourceRevisionSet,
            candidateEvidence=candidateEvidence,
            contradictoryEvidence=contradictoryEvidence,
            executionRefs=executionRefs,
            laneCoverage=laneCoverage,
            truncationReasons=truncationReasons,
            withheldReasons=tuple(
                sorted(f"{item.lane.value}:VISIBILITY_POLICY" for item in laneCoverage if item.withheldCount)
            ),
            unresolvedReasons=unresolvedReasons,
            completeness=completeness,
            digest="",
        )
        digest = canonicalDigest(base)
        return replace(base, packId=logicalId("retrieval-pack", (digest,)), digest=digest)

    def close(self) -> None:
        self._views.clear()

    def __enter__(self) -> "UniverseQueryEngine":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
