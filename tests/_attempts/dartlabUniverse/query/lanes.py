"""Visibility pre-filter 뒤에서만 동작하는 U4 retrieval lanes."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..catalog.models import CatalogEvidence, CatalogObject, CatalogResource, CatalogState
from ..contracts import VerificationState, Visibility
from ..graph.query import GraphStore, TraversalBudget
from ..graph.relations import GraphRelation
from ..graph.statements import GraphStatement
from ..identity.ledger import IdentifierRef, IdentityLedger, normalizeIdentifier
from ..identity.resolver import ResolutionState, resolveOrganization
from ..temporal import parseInstant
from .models import QueryLane, UniverseQuery, normalizeSearchTerms


@dataclass(frozen=True, slots=True)
class LaneHit:
    candidateRef: str
    candidateKind: str
    laneScore: float
    reasonCodes: tuple[str, ...]
    evidenceOverride: tuple[CatalogEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class LaneResult:
    lane: QueryLane
    hits: tuple[LaneHit, ...]
    candidateCount: int
    withheldCount: int
    truncated: bool
    reasonCode: str


def _normalizeIdentifierText(value: str) -> str | None:
    namespace, separator, identifier = value.partition(":")
    if not separator:
        return None
    try:
        normalizedNamespace, normalizedValue = normalizeIdentifier(namespace, identifier)
    except ValueError:
        return None
    return f"{normalizedNamespace}:{normalizedValue}"


def _timeVisibleObject(item: CatalogObject, query: UniverseQuery) -> bool:
    valid = parseInstant(query.timeContext.validAt)
    known = parseInstant(query.timeContext.knownAt)
    start = parseInstant(item.validTime.start) if item.validTime.start else None
    end = parseInstant(item.validTime.end) if item.validTime.end else None
    knownAt = parseInstant(item.systemTime.knownAt)
    retracted = parseInstant(item.systemTime.retractedAt) if item.systemTime.retractedAt else None
    return (
        (start is None or start <= valid)
        and (end is None or valid < end)
        and knownAt <= known
        and (retracted is None or known < retracted)
        and item.verificationState not in {VerificationState.RETRACTED, VerificationState.TOMBSTONED}
    )


def _timeVisibleStatement(item: GraphStatement, query: UniverseQuery) -> bool:
    valid = parseInstant(query.timeContext.validAt)
    known = parseInstant(query.timeContext.knownAt)
    start = parseInstant(item.validTime.start) if item.validTime.start else None
    end = parseInstant(item.validTime.end) if item.validTime.end else None
    knownAt = parseInstant(item.systemTime.knownAt)
    retracted = parseInstant(item.systemTime.retractedAt) if item.systemTime.retractedAt else None
    return (
        (start is None or start <= valid)
        and (end is None or valid < end)
        and knownAt <= known
        and (retracted is None or known < retracted)
        and item.verificationState not in {VerificationState.RETRACTED, VerificationState.TOMBSTONED}
    )


def _timeVisibleRelation(item: GraphRelation, query: UniverseQuery) -> bool:
    valid = parseInstant(query.timeContext.validAt)
    known = parseInstant(query.timeContext.knownAt)
    start = parseInstant(item.validTime.start) if item.validTime.start else None
    end = parseInstant(item.validTime.end) if item.validTime.end else None
    knownAt = parseInstant(item.systemTime.knownAt)
    retracted = parseInstant(item.systemTime.retractedAt) if item.systemTime.retractedAt else None
    return (
        (start is None or start <= valid)
        and (end is None or valid < end)
        and knownAt <= known
        and (retracted is None or known < retracted)
        and item.verificationState not in {VerificationState.RETRACTED, VerificationState.TOMBSTONED}
    )


class VisibleQueryView:
    """한 visibility policy에 허용된 provenance closure만 가진 process-local view."""

    def __init__(
        self,
        catalog: CatalogState,
        graph: GraphStore,
        *,
        allowedVisibility: frozenset[Visibility],
    ) -> None:
        if not allowedVisibility or Visibility.UNKNOWN in allowedVisibility:
            raise ValueError("visible query view policy가 잘못됨")
        resources = tuple(item for item in catalog.resources if item.visibility in allowedVisibility)
        resourceVersions = {item.resourceVersionId for item in resources}
        objects = tuple(
            item
            for item in catalog.objects
            if item.visibility in allowedVisibility and set(item.resourceRefs).issubset(resourceVersions)
        )
        objectIds = {item.objectId for item in objects}
        evidence = tuple(
            item
            for item in catalog.evidence
            if item.visibility in allowedVisibility
            and item.objectId in objectIds
            and item.resourceVersionId in resourceVersions
        )
        evidenceIds = {item.evidenceId for item in evidence}
        statements = tuple(
            item
            for item in graph.statements
            if item.visibility in allowedVisibility and set(item.evidenceRefs).issubset(evidenceIds)
        )
        self.allowedVisibility = allowedVisibility
        self.resources = resources
        self.objects = objects
        self.evidence = evidence
        self.statements = statements
        self.resourceByVersion = {item.resourceVersionId: item for item in resources}
        self.objectById = {item.objectId: item for item in objects}
        self.evidenceById = {item.evidenceId: item for item in evidence}
        self.statementById = {item.statementId: item for item in statements}
        self.evidenceByObject: dict[str, tuple[CatalogEvidence, ...]] = {}
        mutableEvidence: dict[str, list[CatalogEvidence]] = {}
        for item in evidence:
            mutableEvidence.setdefault(item.objectId, []).append(item)
        self.evidenceByObject = {
            key: tuple(sorted(values, key=lambda item: item.evidenceId)) for key, values in mutableEvidence.items()
        }
        self._exactObjectIndex: dict[str, set[str]] = {}
        self._lexicalPostings: dict[str, set[str]] = {}
        self._buildIndexes()

    def _addExact(self, key: str, objectId: str) -> None:
        normalized = key.strip().casefold()
        if normalized:
            self._exactObjectIndex.setdefault(normalized, set()).add(objectId)

    def _buildIndexes(self) -> None:
        for obj in self.objects:
            self._addExact(obj.objectId, obj.objectId)
            self._addExact(obj.objectVersionId, obj.objectId)
            for identifier in obj.identifierRefs:
                normalized = _normalizeIdentifierText(identifier)
                self._addExact(normalized or identifier, obj.objectId)
            for resourceRef in obj.resourceRefs:
                self._addExact(resourceRef, obj.objectId)
                resource = self.resourceByVersion[resourceRef]
                self._addExact(resource.resourceId, obj.objectId)
                for _key, value in resource.locator:
                    self._addExact(value, obj.objectId)
            searchable = (
                obj.canonicalLabel,
                *obj.aliases,
                *obj.identifierRefs,
                *(value for pair in obj.attributes for value in pair),
                *(self.resourceByVersion[ref].label for ref in obj.resourceRefs),
                *(value for ref in obj.resourceRefs for pair in self.resourceByVersion[ref].locator for value in pair),
            )
            tokens = set()
            for value in searchable:
                tokens.update(normalizeSearchTerms(str(value)))
            for token in tokens:
                self._lexicalPostings.setdefault(token, set()).add(obj.objectId)

    def evidenceForHit(self, hit: LaneHit) -> tuple[CatalogEvidence, ...]:
        if hit.evidenceOverride:
            return tuple(
                sorted(
                    (
                        item
                        for item in hit.evidenceOverride
                        if item.visibility in self.allowedVisibility
                        and item.objectId in self.objectById
                        and item.resourceVersionId in self.resourceByVersion
                    ),
                    key=lambda item: item.evidenceId,
                )
            )
        if hit.candidateKind == "OBJECT":
            return self.evidenceByObject.get(hit.candidateRef, ())
        if hit.candidateKind == "STATEMENT":
            statement = self.statementById.get(hit.candidateRef)
            if statement is None:
                return ()
            return tuple(self.evidenceById[ref] for ref in statement.evidenceRefs if ref in self.evidenceById)
        return ()

    def exact(self, query: UniverseQuery, ledger: IdentityLedger | None) -> LaneResult:
        keys = set(query.explicitUniverseRefs)
        normalizedIdentifiers = {
            normalized
            for item in query.explicitIdentifiers
            if (normalized := _normalizeIdentifierText(item)) is not None
        }
        keys.update(normalizedIdentifiers)
        objectIds: set[str] = set()
        reasons: dict[str, set[str]] = {}
        for key in sorted(keys):
            for objectId in self._exactObjectIndex.get(key.casefold(), ()):
                objectIds.add(objectId)
                reasons.setdefault(objectId, set()).add("EXACT_INDEX_MATCH")
        if ledger is not None:
            for value in sorted(normalizedIdentifiers):
                namespace, identifier = value.split(":", 1)
                resolution = resolveOrganization((IdentifierRef(namespace, identifier),), ledger)
                if resolution.state is ResolutionState.RESOLVED and resolution.entityId in self.objectById:
                    objectIds.add(str(resolution.entityId))
                    reasons.setdefault(str(resolution.entityId), set()).add("IDENTITY_LEDGER_MATCH")
        ordered = tuple(sorted(objectIds))
        total = len(ordered)
        selected = ordered[: query.budget.exactLimit]
        hits = tuple(
            LaneHit(item, "OBJECT", 1.0, tuple(sorted(reasons.get(item, {"EXACT_INDEX_MATCH"})))) for item in selected
        )
        return LaneResult(
            QueryLane.EXACT,
            hits,
            total,
            0,
            total > len(selected),
            "LIMIT" if total > len(selected) else ("NO_EXACT_INPUT" if not keys else "COMPLETE"),
        )

    def structured(self, query: UniverseQuery) -> LaneResult:
        filters = query.filters
        hasObjectFilters = bool(filters.objectKinds or filters.resourceKinds or filters.sourceKinds)
        hasStatementFilters = bool(
            filters.subjectRefs or filters.predicates or filters.periodStart or filters.periodEnd or filters.instant
        )
        hits: list[LaneHit] = []
        if hasObjectFilters:
            for obj in self.objects:
                if not _timeVisibleObject(obj, query):
                    continue
                resources = tuple(self.resourceByVersion[ref] for ref in obj.resourceRefs)
                if filters.objectKinds and obj.objectKind.upper() not in filters.objectKinds:
                    continue
                if filters.resourceKinds and not any(
                    item.resourceKind.upper() in filters.resourceKinds for item in resources
                ):
                    continue
                if filters.sourceKinds and not any(
                    item.sourceKind.upper() in filters.sourceKinds for item in resources
                ):
                    continue
                hits.append(LaneHit(obj.objectId, "OBJECT", 1.0, ("STRUCTURED_OBJECT_FILTER",)))
        if hasStatementFilters:
            for statement in self.statements:
                if not _timeVisibleStatement(statement, query):
                    continue
                if filters.subjectRefs and statement.subjectRef not in filters.subjectRefs:
                    continue
                if filters.predicates and statement.predicate.casefold() not in filters.predicates:
                    continue
                if filters.periodStart is not None and statement.periodStart != filters.periodStart:
                    continue
                if filters.periodEnd is not None and statement.periodEnd != filters.periodEnd:
                    continue
                if filters.instant is not None and statement.instant != filters.instant:
                    continue
                hits.append(LaneHit(statement.statementId, "STATEMENT", 1.0, ("STRUCTURED_STATEMENT_FILTER",)))
        ordered = tuple(sorted(hits, key=lambda item: (item.candidateKind, item.candidateRef)))
        total = len(ordered)
        selected = ordered[: query.budget.structuredLimit]
        return LaneResult(
            QueryLane.STRUCTURED,
            selected,
            total,
            0,
            total > len(selected),
            "LIMIT"
            if total > len(selected)
            else ("NO_STRUCTURED_FILTER" if not hasObjectFilters and not hasStatementFilters else "COMPLETE"),
        )

    def lexical(self, query: UniverseQuery) -> LaneResult:
        terms = tuple(item for item in query.searchTerms if len(item) >= 2)
        scores: dict[str, float] = {}
        matches: dict[str, set[str]] = {}
        objectCount = max(len(self.objects), 1)
        for term in terms:
            postings = self._lexicalPostings.get(term, set())
            if not postings:
                continue
            inverseFrequency = math.log1p(objectCount / len(postings))
            for objectId in postings:
                scores[objectId] = scores.get(objectId, 0.0) + inverseFrequency
                matches.setdefault(objectId, set()).add(term)
        ranked = tuple(sorted(scores, key=lambda item: (-scores[item], item)))
        selected = ranked[: query.budget.lexicalLimit]
        maxScore = scores[ranked[0]] if ranked else 1.0
        hits = tuple(
            LaneHit(
                objectId,
                "OBJECT",
                scores[objectId] / maxScore,
                tuple(f"TERM:{term}" for term in sorted(matches[objectId])),
            )
            for objectId in selected
        )
        return LaneResult(
            QueryLane.LEXICAL,
            hits,
            len(ranked),
            0,
            len(ranked) > len(selected),
            "LIMIT" if len(ranked) > len(selected) else ("NO_TERM_MATCH" if terms else "NO_SEARCH_TERMS"),
        )

    def graphLane(
        self,
        query: UniverseQuery,
        graph: GraphStore,
        prior: tuple[LaneResult, ...],
    ) -> LaneResult:
        roots = set(query.filters.subjectRefs)
        roots.update(hit.candidateRef for result in prior for hit in result.hits)
        if not roots:
            return LaneResult(QueryLane.GRAPH, (), 0, 0, False, "NO_GRAPH_ROOT")
        traversal = graph.traverse(
            tuple(sorted(roots)),
            validAt=query.timeContext.validAt,
            knownAt=query.timeContext.knownAt,
            allowedVisibility=self.allowedVisibility,
            budget=TraversalBudget(
                maxDepth=query.budget.graphMaxDepth,
                maxNodes=query.budget.graphMaxNodes,
                maxEdges=query.budget.graphMaxEdges,
            ),
        )
        candidates = []
        rootSet = set(traversal.rootRefs)
        for ref in traversal.nodeRefs:
            if ref in rootSet:
                continue
            if ref in self.objectById:
                candidates.append(LaneHit(ref, "OBJECT", 1.0, ("GRAPH_REACHABLE",)))
            elif ref in self.statementById:
                candidates.append(LaneHit(ref, "STATEMENT", 1.0, ("GRAPH_REACHABLE",)))
        ordered = tuple(sorted(candidates, key=lambda item: (item.candidateKind, item.candidateRef)))
        return LaneResult(
            QueryLane.GRAPH,
            ordered,
            len(ordered),
            0,
            traversal.truncated,
            traversal.truncationReason or "COMPLETE",
        )

    def contradiction(self, query: UniverseQuery, graph: GraphStore, prior: tuple[LaneResult, ...]) -> LaneResult:
        candidateStatements = {
            hit.candidateRef
            for result in prior
            for hit in result.hits
            if hit.candidateKind == "STATEMENT" and hit.candidateRef in self.statementById
        }
        conflictGroups = {
            self.statementById[ref].conflictGroupId
            for ref in candidateStatements
            if self.statementById[ref].conflictGroupId is not None
        }
        contradictions: set[str] = set()
        for statement in self.statements:
            if (
                statement.statementId not in candidateStatements
                and statement.conflictGroupId is not None
                and statement.conflictGroupId in conflictGroups
                and _timeVisibleStatement(statement, query)
            ):
                contradictions.add(statement.statementId)
        for relation in graph.relations:
            if (
                relation.relationType != "CONTRADICTS"
                or relation.visibility not in self.allowedVisibility
                or not _timeVisibleRelation(relation, query)
            ):
                continue
            if relation.fromRef in candidateStatements and relation.toRef in self.statementById:
                contradictions.add(relation.toRef)
            if relation.toRef in candidateStatements and relation.fromRef in self.statementById:
                contradictions.add(relation.fromRef)
        ordered = tuple(sorted(contradictions))
        selected = ordered[: query.budget.structuredLimit]
        hits = tuple(LaneHit(ref, "STATEMENT", 1.0, ("CONTRADICTION_MATCH",)) for ref in selected)
        return LaneResult(
            QueryLane.CONTRADICTION,
            hits,
            len(ordered),
            0,
            len(ordered) > len(selected),
            "LIMIT" if len(ordered) > len(selected) else "COMPLETE",
        )
