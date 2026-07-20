"""U4 RetrievalEvidencePack을 모델 없이 재검증하는 G4E gate."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from ..canonical import canonicalDigest
from ..catalog.models import CatalogState
from ..catalog.snapshot import CatalogSnapshot
from ..contracts import ValidationIssue, Visibility
from ..graph.query import GraphStore
from ..ids import logicalId
from ..query.models import (
    REQUIRED_QUERY_LANES,
    RETRIEVAL_EVIDENCE_PACK_SCHEMA_VERSION,
    RetrievalEvidencePack,
    RetrievedEvidence,
    UniverseQuery,
)
from ..query.planner import QueryPlan, visibilityPolicyDigest


@dataclass(frozen=True, slots=True)
class G4EValidationReport:
    valid: bool
    issues: tuple[ValidationIssue, ...]
    checkedEvidenceCount: int
    checkedLaneCount: int
    digest: str


def _issue(issues: list[ValidationIssue], code: str, path: str, detail: str) -> None:
    issues.append(ValidationIssue(code, path, detail))


def _validateRetrieved(
    item: RetrievedEvidence,
    *,
    path: str,
    catalog: CatalogState,
    graph: GraphStore,
    snapshot: CatalogSnapshot,
    allowedVisibility: frozenset[Visibility],
    issues: list[ValidationIssue],
) -> None:
    evidenceById = {evidence.evidenceId: evidence for evidence in catalog.evidence}
    objectById = {obj.objectId: obj for obj in catalog.objects}
    statementById = {statement.statementId: statement for statement in graph.statements}
    resourceByVersion = {resource.resourceVersionId: resource for resource in catalog.resources}
    snapshotByVersion = {resource.resourceVersionId: resource for resource in snapshot.resources}
    canonicalEvidence = evidenceById.get(item.evidence.evidenceId)
    if canonicalEvidence is None or canonicalEvidence != item.evidence:
        _issue(issues, "EVIDENCE_CATALOG_MISMATCH", f"{path}.evidence", item.evidence.evidenceId)
        return
    if item.candidateKind == "OBJECT":
        obj = objectById.get(item.candidateRef)
        if obj is None or item.evidence.objectId != item.candidateRef:
            _issue(issues, "CANDIDATE_OBJECT_BINDING_MISMATCH", path, item.candidateRef)
        elif obj.visibility not in allowedVisibility:
            _issue(issues, "CANDIDATE_VISIBILITY_DENIED", path, item.candidateRef)
    elif item.candidateKind == "STATEMENT":
        statement = statementById.get(item.candidateRef)
        if statement is None or item.evidence.evidenceId not in statement.evidenceRefs:
            _issue(issues, "CANDIDATE_STATEMENT_BINDING_MISMATCH", path, item.candidateRef)
        elif statement.visibility not in allowedVisibility:
            _issue(issues, "CANDIDATE_VISIBILITY_DENIED", path, item.candidateRef)
    else:
        _issue(issues, "CANDIDATE_KIND_INVALID", f"{path}.candidateKind", item.candidateKind)
    resource = resourceByVersion.get(item.evidence.resourceVersionId)
    snapshotResource = snapshotByVersion.get(item.evidence.resourceVersionId)
    if resource is None or snapshotResource is None:
        _issue(
            issues, "EVIDENCE_RESOURCE_MISSING", f"{path}.evidence.resourceVersionId", item.evidence.resourceVersionId
        )
    else:
        if resource.visibility not in allowedVisibility or item.evidence.visibility not in allowedVisibility:
            _issue(issues, "EVIDENCE_VISIBILITY_DENIED", path, item.evidence.evidenceId)
        expected = (
            resource.sourceKind,
            resource.sourceRef,
            resource.sourceRevision,
            resource.locator,
            resource.contentDigest,
            resource.licenseRef,
        )
        actual = (
            item.evidence.sourceKind,
            item.evidence.sourceRef,
            item.evidence.sourceRevision,
            item.evidence.locator,
            item.evidence.contentDigest,
            item.evidence.licenseRef,
        )
        if actual != expected:
            _issue(issues, "EVIDENCE_PROVENANCE_MISMATCH", path, item.evidence.evidenceId)
        snapshotExpected = (
            snapshotResource.sourceKind,
            snapshotResource.sourceRef,
            snapshotResource.sourceRevision,
            snapshotResource.locator,
            snapshotResource.contentDigest,
            snapshotResource.licenseRef,
        )
        if actual != snapshotExpected:
            _issue(issues, "EVIDENCE_SNAPSHOT_MISMATCH", path, item.evidence.evidenceId)
    if item.rank < 1 or not math.isfinite(item.score) or item.score < 0:
        _issue(issues, "SCORE_INVALID", path, item.candidateRef)
    if not item.scoreProvenance:
        _issue(issues, "SCORE_PROVENANCE_MISSING", path, item.candidateRef)
    for contribution in item.scoreProvenance:
        if (
            contribution.rank < 1
            or not math.isfinite(contribution.laneScore)
            or contribution.laneScore < 0
            or not math.isfinite(contribution.fusionContribution)
            or contribution.fusionContribution < 0
        ):
            _issue(issues, "SCORE_PROVENANCE_INVALID", path, item.candidateRef)


def validateRetrievalEvidencePack(
    pack: RetrievalEvidencePack,
    *,
    query: UniverseQuery,
    plan: QueryPlan,
    snapshot: CatalogSnapshot,
    catalog: CatalogState,
    graph: GraphStore,
) -> G4EValidationReport:
    """Pack digest, plan, snapshot, visibility, locator, lane coverage를 전부 재생한다."""
    issues: list[ValidationIssue] = []
    if pack.schemaVersion != RETRIEVAL_EVIDENCE_PACK_SCHEMA_VERSION:
        _issue(issues, "PACK_SCHEMA_VERSION_MISMATCH", "schemaVersion", pack.schemaVersion)
    expectedDigest = canonicalDigest(replace(pack, packId="", digest=""))
    if pack.digest != expectedDigest or pack.packId != logicalId("retrieval-pack", (expectedDigest,)):
        _issue(issues, "PACK_DIGEST_MISMATCH", "packId", pack.packId)
    if (
        pack.queryId != query.queryId
        or plan.queryId != query.queryId
        or plan.queryDigest != query.digest
        or pack.queryPlanDigest != plan.digest
    ):
        _issue(issues, "QUERY_PLAN_BINDING_MISMATCH", "queryPlanDigest", pack.queryPlanDigest)
    if (
        pack.snapshotId != snapshot.snapshotId
        or plan.snapshotId != snapshot.snapshotId
        or pack.snapshotRootInputsDigest != snapshot.rootInputsDigest
        or plan.snapshotRootInputsDigest != snapshot.rootInputsDigest
        or pack.descriptorSetDigest != snapshot.descriptorSetDigest
        or pack.recoverySetDigest != snapshot.recoverySetDigest
        or catalog.digest != snapshot.catalogDigest
    ):
        _issue(issues, "SNAPSHOT_BINDING_MISMATCH", "snapshotId", pack.snapshotId)
    expectedPolicy = visibilityPolicyDigest(query)
    if pack.visibilityPolicyDigest != expectedPolicy or plan.visibilityPolicyDigest != expectedPolicy:
        _issue(issues, "VISIBILITY_POLICY_MISMATCH", "visibilityPolicyDigest", pack.visibilityPolicyDigest)
    if plan.allowsCapabilityExecution or plan.allowsExternalToolCalls or pack.executionRefs:
        _issue(issues, "EXECUTION_ESCALATION_FORBIDDEN", "executionRefs", "U4 retrieval은 read-only")
    laneNames = tuple(item.lane.value for item in pack.laneCoverage)
    if laneNames != REQUIRED_QUERY_LANES or any(not item.executed for item in pack.laneCoverage):
        _issue(issues, "LANE_COVERAGE_INCOMPLETE", "laneCoverage", ",".join(laneNames))
    if pack.laneCoverage[-1].lane.value != "CONTRADICTION":
        _issue(issues, "CONTRADICTION_LANE_MISSING", "laneCoverage", "contradiction search required")
    for index, item in enumerate(pack.laneCoverage):
        if min(item.candidateCount, item.returnedCount, item.withheldCount) < 0:
            _issue(issues, "LANE_COUNT_INVALID", f"laneCoverage[{index}]", item.lane.value)
        if item.returnedCount > item.candidateCount:
            _issue(issues, "LANE_RETURN_COUNT_INVALID", f"laneCoverage[{index}]", item.lane.value)
        if item.truncated and not item.reasonCode:
            _issue(issues, "TRUNCATION_REASON_MISSING", f"laneCoverage[{index}]", item.lane.value)
    allowed = frozenset(query.allowedVisibility)
    allRetrieved = (*pack.candidateEvidence, *pack.contradictoryEvidence)
    seen = set()
    previousKey: tuple[int, str, str] | None = None
    for index, item in enumerate(allRetrieved):
        section = "candidateEvidence" if index < len(pack.candidateEvidence) else "contradictoryEvidence"
        localIndex = index if section == "candidateEvidence" else index - len(pack.candidateEvidence)
        path = f"{section}[{localIndex}]"
        key = (section, item.candidateRef, item.evidence.evidenceId)
        if key in seen:
            _issue(issues, "EVIDENCE_DUPLICATE", path, item.evidence.evidenceId)
        seen.add(key)
        orderKey = (item.rank, item.candidateRef, item.evidence.evidenceId)
        if previousKey is not None and section == "candidateEvidence" and orderKey < previousKey:
            _issue(issues, "EVIDENCE_ORDER_MISMATCH", path, item.evidence.evidenceId)
        if section == "candidateEvidence":
            previousKey = orderKey
        _validateRetrieved(
            item,
            path=path,
            catalog=catalog,
            graph=graph,
            snapshot=snapshot,
            allowedVisibility=allowed,
            issues=issues,
        )
    expectedSourceRevisions = tuple(
        sorted({(item.evidence.sourceRef, item.evidence.sourceRevision) for item in allRetrieved})
    )
    if pack.sourceRevisionSet != expectedSourceRevisions:
        _issue(issues, "SOURCE_REVISION_SET_MISMATCH", "sourceRevisionSet", "evidence revision set differs")
    expectedTruncations = {f"{item.lane.value}:{item.reasonCode}" for item in pack.laneCoverage if item.truncated}
    if not expectedTruncations.issubset(pack.truncationReasons):
        _issue(issues, "TRUNCATION_DISCLOSURE_MISSING", "truncationReasons", "lane truncation omitted")
    if any(item.withheldCount for item in pack.laneCoverage) and not pack.withheldReasons:
        _issue(issues, "WITHHELD_DISCLOSURE_MISSING", "withheldReasons", "withheld result omitted")
    if not pack.candidateEvidence and pack.completeness != "ABSTAIN":
        _issue(issues, "ABSTENTION_REQUIRED", "completeness", pack.completeness)
    if pack.candidateEvidence and (pack.truncationReasons or pack.unresolvedReasons) and pack.completeness != "PARTIAL":
        _issue(issues, "PARTIAL_DISCLOSURE_REQUIRED", "completeness", pack.completeness)
    if pack.completeness not in {"COMPLETE", "PARTIAL", "ABSTAIN"}:
        _issue(issues, "COMPLETENESS_INVALID", "completeness", pack.completeness)
    ordered = tuple(sorted(issues, key=lambda item: (item.code, item.path, item.detail)))
    return G4EValidationReport(
        valid=not ordered,
        issues=ordered,
        checkedEvidenceCount=len(allRetrieved),
        checkedLaneCount=len(pack.laneCoverage),
        digest=canonicalDigest(ordered),
    )
