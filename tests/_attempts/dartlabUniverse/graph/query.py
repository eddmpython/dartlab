"""시간, visibility, node, edge, depth를 제한하는 evidence graph query."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime

import pyarrow as pa

from ..contracts import VerificationState, Visibility
from ..temporal import parseInstant
from .relations import GraphRelation
from .statements import GraphStatement

_STATEMENT_SCHEMA = pa.schema(
    [
        ("schemaVersion", pa.string()),
        ("statementId", pa.string()),
        ("subjectRef", pa.string()),
        ("predicate", pa.string()),
        ("objectRef", pa.string()),
        ("value", pa.string()),
        ("valueType", pa.string()),
        ("unit", pa.string()),
        ("currency", pa.string()),
        ("scale", pa.int64()),
        ("scope", pa.string()),
        ("periodStart", pa.string()),
        ("periodEnd", pa.string()),
        ("instant", pa.string()),
        ("validTime", pa.string()),
        ("systemTime", pa.string()),
        ("epistemicClass", pa.string()),
        ("verificationState", pa.string()),
        ("evidenceRefs", pa.string()),
        ("derivationRef", pa.string()),
        ("assumptionRefs", pa.string()),
        ("confidence", pa.float64()),
        ("conflictGroupId", pa.string()),
        ("visibility", pa.string()),
        ("digest", pa.string()),
    ]
)
_RELATION_SCHEMA = pa.schema(
    [
        ("schemaVersion", pa.string()),
        ("relationId", pa.string()),
        ("fromRef", pa.string()),
        ("relationType", pa.string()),
        ("taxonomyVersion", pa.string()),
        ("toRef", pa.string()),
        ("direction", pa.string()),
        ("statementRefs", pa.string()),
        ("evidenceRefs", pa.string()),
        ("epistemicClass", pa.string()),
        ("derivationRef", pa.string()),
        ("weight", pa.float64()),
        ("confidence", pa.float64()),
        ("validTime", pa.string()),
        ("systemTime", pa.string()),
        ("verificationState", pa.string()),
        ("visibility", pa.string()),
        ("digest", pa.string()),
    ]
)


@dataclass(frozen=True, slots=True)
class TraversalBudget:
    maxDepth: int = 3
    maxNodes: int = 1000
    maxEdges: int = 5000


@dataclass(frozen=True, slots=True)
class TraversalResult:
    rootRefs: tuple[str, ...]
    nodeRefs: tuple[str, ...]
    relations: tuple[GraphRelation, ...]
    truncated: bool
    truncationReason: str | None


def _timeVisible(relation: GraphRelation, valid: datetime, known: datetime) -> bool:
    start = parseInstant(relation.validTime.start) if relation.validTime.start else None
    end = parseInstant(relation.validTime.end) if relation.validTime.end else None
    knownStart = parseInstant(relation.systemTime.knownAt)
    retracted = parseInstant(relation.systemTime.retractedAt) if relation.systemTime.retractedAt else None
    return (
        (start is None or start <= valid)
        and (end is None or valid < end)
        and knownStart <= known
        and (retracted is None or known < retracted)
        and relation.verificationState not in {VerificationState.RETRACTED, VerificationState.TOMBSTONED}
    )


class GraphStore:
    """Snapshot별 immutable statement와 relation을 bounded traversal로 제공한다."""

    def __init__(self, statements: tuple[GraphStatement, ...], relations: tuple[GraphRelation, ...]):
        self.statements = tuple(sorted(statements, key=lambda item: item.statementId))
        self.relations = tuple(sorted(relations, key=lambda item: item.relationId))
        if len({item.statementId for item in self.statements}) != len(self.statements):
            raise ValueError("duplicate statement ID")
        if len({item.relationId for item in self.relations}) != len(self.relations):
            raise ValueError("duplicate relation ID")
        self._outgoing: dict[str, list[GraphRelation]] = {}
        for relation in self.relations:
            self._outgoing.setdefault(relation.fromRef, []).append(relation)

    def traverse(
        self,
        rootRefs: tuple[str, ...],
        *,
        validAt: str,
        knownAt: str,
        allowedVisibility: frozenset[Visibility],
        budget: TraversalBudget | None = None,
    ) -> TraversalResult:
        """Root에서 directed edge를 BFS하며 모든 상한을 fail-closed 적용한다."""
        active = budget or TraversalBudget()
        if active.maxDepth < 0 or active.maxNodes < 1 or active.maxEdges < 0:
            raise ValueError("traversal budget이 잘못됨")
        if not allowedVisibility:
            raise ValueError("allowedVisibility는 비어 있을 수 없음")
        requestedRoots = tuple(sorted(set(rootRefs)))
        if any(not item for item in requestedRoots):
            raise ValueError("rootRef는 비어 있을 수 없음")
        rootLimitExceeded = len(requestedRoots) > active.maxNodes
        roots = requestedRoots[: active.maxNodes]
        validInstant = parseInstant(validAt)
        knownInstant = parseInstant(knownAt)
        visited = set(roots)
        queue = deque((root, 0) for root in roots)
        edges = []
        truncated = rootLimitExceeded
        reason = "MAX_NODES" if rootLimitExceeded else None
        while queue:
            current, depth = queue.popleft()
            if depth >= active.maxDepth:
                if any(
                    relation.visibility in allowedVisibility and _timeVisible(relation, validInstant, knownInstant)
                    for relation in self._outgoing.get(current, ())
                ):
                    truncated = True
                    reason = reason or "MAX_DEPTH"
                continue
            for relation in self._outgoing.get(current, ()):
                if relation.visibility not in allowedVisibility or not _timeVisible(
                    relation,
                    validInstant,
                    knownInstant,
                ):
                    continue
                if len(edges) >= active.maxEdges:
                    truncated = True
                    reason = "MAX_EDGES"
                    queue.clear()
                    break
                if relation.toRef not in visited and len(visited) >= active.maxNodes:
                    truncated = True
                    reason = "MAX_NODES"
                    continue
                edges.append(relation)
                if relation.toRef not in visited:
                    visited.add(relation.toRef)
                    queue.append((relation.toRef, depth + 1))
        return TraversalResult(roots, tuple(sorted(visited)), tuple(edges), truncated, reason)

    def arrowTables(self, *, allowedVisibility: frozenset[Visibility]) -> dict[str, pa.Table]:
        """호출자 visibility로 축소된 statement와 relation Arrow batch를 만든다."""
        if not allowedVisibility:
            raise ValueError("allowedVisibility는 비어 있을 수 없음")
        statementRows = []
        for item in self.statements:
            if item.visibility not in allowedVisibility:
                continue
            row = asdict(item)
            for key in ("validTime", "systemTime", "value", "evidenceRefs", "assumptionRefs"):
                row[key] = json.dumps(row[key], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            row["epistemicClass"] = item.epistemicClass.value
            row["verificationState"] = item.verificationState.value
            row["visibility"] = item.visibility.value
            statementRows.append(row)
        relationRows = []
        for item in self.relations:
            if item.visibility not in allowedVisibility:
                continue
            row = asdict(item)
            for key in ("validTime", "systemTime", "statementRefs", "evidenceRefs"):
                row[key] = json.dumps(row[key], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            row["verificationState"] = item.verificationState.value
            row["epistemicClass"] = item.epistemicClass.value
            row["visibility"] = item.visibility.value
            relationRows.append(row)
        return {
            "statements": pa.Table.from_pylist(statementRows, schema=_STATEMENT_SCHEMA),
            "relations": pa.Table.from_pylist(relationRows, schema=_RELATION_SCHEMA),
        }
