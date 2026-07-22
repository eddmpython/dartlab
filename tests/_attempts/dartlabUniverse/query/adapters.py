"""기존 runtime source를 U4 lane에 연결하는 read-only adapter 계약."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..catalog.models import CatalogObject, CatalogResource
from ..contracts import Visibility
from .lanes import LaneHit, LaneResult
from .models import QueryLane, UniverseQuery


@dataclass(frozen=True, slots=True)
class LexicalAdapterContext:
    allowedVisibility: frozenset[Visibility]
    objectById: dict[str, CatalogObject]
    resourceByVersion: dict[str, CatalogResource]


class LexicalQueryAdapter(Protocol):
    """Source payload를 복제하지 않고 lexical candidate를 반환하는 port."""

    def search(self, query: UniverseQuery, context: LexicalAdapterContext) -> LaneResult: ...


class ExactQueryAdapter(Protocol):
    """Source-native exact identifier를 반환하는 port."""

    def searchExact(self, query: UniverseQuery, context: LexicalAdapterContext) -> LaneResult: ...


def _mergeResults(results: tuple[LaneResult, ...], *, lane: QueryLane, limit: int) -> LaneResult:
    if limit < 1 or not results or any(item.lane is not lane for item in results):
        raise ValueError(f"{lane.value.casefold()} result merge 입력이 잘못됨")
    combined: dict[tuple[str, str], LaneHit] = {}
    for result in results:
        for hit in result.hits:
            key = (hit.candidateKind, hit.candidateRef)
            previous = combined.get(key)
            if previous is None:
                combined[key] = hit
                continue
            evidenceById = {item.evidenceId: item for item in (*previous.evidenceOverride, *hit.evidenceOverride)}
            combined[key] = LaneHit(
                candidateRef=hit.candidateRef,
                candidateKind=hit.candidateKind,
                laneScore=max(previous.laneScore, hit.laneScore),
                reasonCodes=tuple(sorted({*previous.reasonCodes, *hit.reasonCodes})),
                evidenceOverride=tuple(evidenceById[key] for key in sorted(evidenceById)),
            )
    ordered = tuple(
        sorted(combined.values(), key=lambda item: (-item.laneScore, item.candidateKind, item.candidateRef))
    )
    selected = ordered[:limit]
    truncated = len(ordered) > len(selected) or any(item.truncated for item in results)
    if truncated:
        reason = "LIMIT"
    elif selected:
        reason = "COMPLETE"
    elif lane is QueryLane.EXACT:
        reason = "NO_EXACT_INPUT" if all(item.reasonCode == "NO_EXACT_INPUT" for item in results) else "NO_EXACT_MATCH"
    elif any(item.reasonCode == "NO_SEARCH_TERMS" for item in results):
        reason = "NO_SEARCH_TERMS"
    else:
        reason = "NO_TERM_MATCH"
    return LaneResult(
        lane=lane,
        hits=selected,
        candidateCount=len(ordered),
        withheldCount=sum(item.withheldCount for item in results),
        truncated=truncated,
        reasonCode=reason,
    )


def mergeExactResults(results: tuple[LaneResult, ...], *, limit: int) -> LaneResult:
    """Catalog와 source-native exact hit를 deterministic하게 한 lane으로 합친다."""
    return _mergeResults(results, lane=QueryLane.EXACT, limit=limit)


def mergeLexicalResults(results: tuple[LaneResult, ...], *, limit: int) -> LaneResult:
    """Metadata와 source adapter lexical hit를 deterministic하게 한 lane으로 합친다."""
    return _mergeResults(results, lane=QueryLane.LEXICAL, limit=limit)
