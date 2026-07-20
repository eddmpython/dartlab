"""기존 dartlab.search contentIndex 결과를 source-bound virtual evidence로 연결한다."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

from ..canonical import canonicalDigest
from ..catalog.models import CatalogEvidence, CatalogObject, CatalogResource, CatalogState
from ..ids import logicalId
from .adapters import LexicalAdapterContext
from .lanes import LaneHit, LaneResult
from .models import QueryLane, RetrievedEvidence, UniverseQuery


@dataclass(frozen=True, slots=True)
class ContentSearchRun:
    queryId: str
    indexResourceVersionId: str
    requestedLimit: int
    receivedRowCount: int
    acceptedHitCount: int
    rejectedRowCount: int
    outputDigest: str


def _defaultSearch(queryText: str, limit: int) -> tuple[dict[str, object], ...]:
    import dartlab

    result = dartlab.search(queryText, limit=limit, scope="auto")
    if hasattr(result, "to_dicts"):
        return tuple(result.to_dicts())
    raise TypeError("dartlab.search 결과가 row mapping을 제공하지 않음")


def _indexPriority(resource: CatalogResource) -> tuple[int, str]:
    locator = dict(resource.locator)
    path = locator.get("path", "")
    prefix = locator.get("prefix", "")
    if path == "dart/contentIndex/manifest.json":
        priority = 0
    elif path == "dart/contentIndex/active.json":
        priority = 1
    elif path.startswith("dart/contentIndex/") and path.endswith("manifest.json"):
        priority = 2
    elif prefix == "dart/contentIndex" or resource.label == "contentIndex":
        priority = 3
    else:
        priority = 100
    return priority, resource.resourceVersionId


class DartContentSearchAdapter:
    """Public search API를 실행하되 원문 대신 index revision과 result locator만 pack에 넣는다."""

    def __init__(
        self,
        catalog: CatalogState,
        *,
        searchCallable: Callable[[str, int], tuple[dict[str, object], ...]] | None = None,
        indexResourceVersionId: str | None = None,
    ) -> None:
        self.catalog = catalog
        self.searchCallable = searchCallable or _defaultSearch
        resourceByVersion = {item.resourceVersionId: item for item in catalog.resources}
        objectByResource: dict[str, CatalogObject] = {}
        for obj in catalog.objects:
            for resourceRef in obj.resourceRefs:
                objectByResource.setdefault(resourceRef, obj)
        if indexResourceVersionId is not None:
            candidates = (resourceByVersion[indexResourceVersionId],)
        else:
            candidates = tuple(
                item
                for item in catalog.resources
                if _indexPriority(item)[0] < 100 and item.resourceVersionId in objectByResource
            )
        if not candidates:
            raise ValueError("catalog에 contentIndex authority resource가 없음")
        self.indexResource = min(candidates, key=_indexPriority)
        self.indexObject = objectByResource.get(self.indexResource.resourceVersionId)
        if self.indexObject is None:
            raise ValueError("contentIndex authority object가 없음")
        self.latestRun: ContentSearchRun | None = None
        self._retrievedByKey: dict[tuple[str, str], RetrievedEvidence] = {}

    @staticmethod
    def _safeText(row: dict[str, object], key: str) -> str:
        value = row.get(key)
        return "" if value is None else str(value).strip()

    @staticmethod
    def _safeUrl(value: str) -> str:
        if not value:
            return ""
        parsed = urlparse(value)
        return value if parsed.scheme in {"http", "https"} and bool(parsed.netloc) else ""

    def _hit(
        self,
        row: dict[str, object],
        *,
        rank: int,
        maxScore: float,
    ) -> LaneHit | None:
        sourceRef = self._safeText(row, "sourceRef")
        rceptNo = self._safeText(row, "rcept_no")
        if not sourceRef and rceptNo:
            sourceRef = f"dart:filing:{rceptNo}"
        if not sourceRef:
            return None
        dataAsOf = self._safeText(row, "dataAsOf") or self._safeText(row, "sourceDataAsOf")
        resultSource = self._safeText(row, "source") or "unknown"
        sectionOrder = self._safeText(row, "section_order")
        scope = self._safeText(row, "scope") or "auto"
        dartUrl = self._safeUrl(self._safeText(row, "dartUrl") or self._safeText(row, "url"))
        snippet = self._safeText(row, "snippet") or self._safeText(row, "section_content")
        fieldCards = self._safeText(row, "fieldCards")
        try:
            rawScore = float(row.get("score") or 0.0)
        except (TypeError, ValueError):
            rawScore = 0.0
        if not math.isfinite(rawScore) or rawScore < 0:
            return None
        selector = (
            ("sourceRef", sourceRef),
            ("dataAsOf", dataAsOf),
            ("rceptNo", rceptNo),
            ("sectionOrder", sectionOrder),
            ("resultSource", resultSource),
            ("scope", scope),
            ("url", dartUrl),
        )
        quoteDigest = canonicalDigest({"snippet": snippet, "fieldCards": fieldCards})
        candidateRef = logicalId("content-hit", (sourceRef, dataAsOf, sectionOrder, scope))
        evidenceId = logicalId(
            "query-evidence",
            (candidateRef, self.indexResource.resourceVersionId, selector, quoteDigest),
        )
        evidence = CatalogEvidence(
            evidenceId=evidenceId,
            objectId=self.indexObject.objectId,
            resourceVersionId=self.indexResource.resourceVersionId,
            sourceKind=self.indexResource.sourceKind,
            sourceRef=self.indexResource.sourceRef,
            sourceRevision=self.indexResource.sourceRevision,
            locator=self.indexResource.locator + selector,
            selector=selector,
            contentDigest=self.indexResource.contentDigest,
            retrievedAt=self.indexResource.observedAt,
            visibility=self.indexResource.visibility,
            licenseRef=self.indexResource.licenseRef,
            quoteDigest=quoteDigest,
        )
        laneScore = rawScore / maxScore if maxScore > 0 else 1.0 / rank
        return LaneHit(
            candidateRef=candidateRef,
            candidateKind="CONTENT_HIT",
            laneScore=laneScore,
            reasonCodes=(f"CONTENT_INDEX:{resultSource.upper()}", f"CONTENT_SCOPE:{scope.upper()}"),
            evidenceOverride=(evidence,),
        )

    def search(self, query: UniverseQuery, context: LexicalAdapterContext) -> LaneResult:
        if (
            self.indexResource.visibility not in context.allowedVisibility
            or self.indexObject.objectId not in context.objectById
        ):
            return LaneResult(QueryLane.LEXICAL, (), 0, 0, False, "CONTENT_INDEX_VISIBILITY_DENIED")
        queryText = " ".join(query.searchTerms)
        requestedLimit = min(query.budget.lexicalLimit, 200)
        rows = self.searchCallable(queryText, requestedLimit)
        scoredRows = []
        for index, row in enumerate(rows):
            try:
                score = float(row.get("score") or 0.0)
            except (TypeError, ValueError):
                score = -1.0
            scoredRows.append((score, index, row))
        scoredRows.sort(key=lambda item: (-item[0], item[1]))
        maxScore = max((item[0] for item in scoredRows if math.isfinite(item[0]) and item[0] >= 0), default=0.0)
        hits = []
        rejected = 0
        seenCandidates = set()
        for rank, (_score, _index, row) in enumerate(scoredRows, start=1):
            hit = self._hit(row, rank=rank, maxScore=maxScore)
            if hit is None or hit.candidateRef in seenCandidates:
                rejected += 1
                continue
            seenCandidates.add(hit.candidateRef)
            hits.append(hit)
        selected = tuple(hits[:requestedLimit])
        self._retrievedByKey.clear()
        for rank, hit in enumerate(selected, start=1):
            evidence = hit.evidenceOverride[0]
            retrieved = RetrievedEvidence(
                candidateRef=hit.candidateRef,
                candidateKind=hit.candidateKind,
                rank=rank,
                score=hit.laneScore,
                scoreProvenance=(),
                evidence=evidence,
            )
            self._retrievedByKey[(hit.candidateRef, evidence.evidenceId)] = retrieved
        outputDigest = canonicalDigest(
            tuple((hit.candidateRef, hit.laneScore, hit.reasonCodes, hit.evidenceOverride[0]) for hit in selected)
        )
        self.latestRun = ContentSearchRun(
            queryId=query.queryId,
            indexResourceVersionId=self.indexResource.resourceVersionId,
            requestedLimit=requestedLimit,
            receivedRowCount=len(rows),
            acceptedHitCount=len(selected),
            rejectedRowCount=rejected,
            outputDigest=outputDigest,
        )
        return LaneResult(
            lane=QueryLane.LEXICAL,
            hits=selected,
            candidateCount=len(hits),
            withheldCount=0,
            truncated=len(hits) > len(selected),
            reasonCode="LIMIT" if len(hits) > len(selected) else ("COMPLETE" if selected else "NO_TERM_MATCH"),
        )

    def verifyRetrieved(self, retrieved: RetrievedEvidence) -> bool:
        expected = self._retrievedByKey.get((retrieved.candidateRef, retrieved.evidence.evidenceId))
        return (
            expected is not None
            and retrieved.candidateKind == "CONTENT_HIT"
            and expected.candidateRef == retrieved.candidateRef
            and expected.evidence == retrieved.evidence
        )
