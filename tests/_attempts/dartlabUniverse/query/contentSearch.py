"""기존 dartlab.search contentIndex 결과를 source-bound virtual evidence로 연결한다."""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from ..canonical import canonicalDigest
from ..catalog.models import CatalogEvidence, CatalogObject, CatalogResource, CatalogState
from ..ids import logicalId
from ..temporal import parseInstant
from .adapters import LexicalAdapterContext
from .lanes import LaneHit, LaneResult
from .models import QueryLane, RetrievedEvidence, UniverseQuery


@dataclass(frozen=True, slots=True)
class ContentSearchRun:
    queryId: str
    lane: QueryLane
    indexResourceVersionId: str
    artifactSetDigest: str
    requestedLimit: int
    receivedRowCount: int
    acceptedHitCount: int
    rejectedRowCount: int
    outputDigest: str


@dataclass(frozen=True, slots=True)
class ContentIndexBinding:
    manifestDigest: str
    artifactSetDigest: str
    resourceVersionIds: tuple[str, ...]
    metaResourceVersionId: str
    metaPath: Path


@dataclass(frozen=True, slots=True)
class ContentIndexPreparation:
    artifactSetDigest: str
    warmupResultCount: int
    durationMs: float
    outputDigest: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _catalogPath(resource: CatalogResource) -> str:
    return dict(resource.locator).get("path", "")


def _bindLocalContentIndex(catalog: CatalogState) -> ContentIndexBinding:
    """실제로 열린 local index artifact 전부를 current catalog resource와 결박한다."""
    from dartlab.providers.dart.search.fieldIndex import _activeIndexDir

    activeDir = _activeIndexDir().resolve()
    manifestPath = activeDir / "manifest.json"
    if not manifestPath.is_file():
        raise ValueError("active contentIndex manifest가 없음")
    manifestBytes = manifestPath.read_bytes()
    try:
        manifest = json.loads(manifestBytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("active contentIndex manifest를 해석할 수 없음") from exc
    fileHashes = manifest.get("fileHashes")
    fileSources = manifest.get("fileSources")
    if (
        not isinstance(fileHashes, dict)
        or not isinstance(fileSources, dict)
        or set(fileHashes) != set(fileSources)
        or "main_meta.parquet" not in fileHashes
    ):
        raise ValueError("contentIndex manifest artifact set이 불완전함")
    catalogByPath = {_catalogPath(resource): resource for resource in catalog.resources if _catalogPath(resource)}
    bound = []
    metaResource = None
    for name in sorted(fileHashes):
        expectedDigest = str(fileHashes[name]).strip().casefold()
        sourcePath = str(fileSources[name]).strip().replace("\\", "/")
        localPath = (activeDir / name).resolve()
        if localPath.parent != activeDir or not localPath.is_file():
            raise ValueError(f"contentIndex local artifact 누락: {name}")
        if len(expectedDigest) != 64 or _sha256(localPath) != expectedDigest:
            raise ValueError(f"contentIndex local artifact digest 불일치: {name}")
        resource = catalogByPath.get(sourcePath)
        if resource is None:
            raise ValueError(f"contentIndex artifact가 catalog snapshot에 없음: {sourcePath}")
        catalogLfsDigest = dict(resource.locator).get("lfsSha256")
        if catalogLfsDigest is not None and catalogLfsDigest != expectedDigest:
            raise ValueError(f"contentIndex artifact와 catalog LFS digest가 다름: {sourcePath}")
        if resource.byteSize != localPath.stat().st_size:
            raise ValueError(f"contentIndex artifact와 catalog byte size가 다름: {sourcePath}")
        bound.append((name, expectedDigest, sourcePath, resource.resourceVersionId))
        if name == "main_meta.parquet":
            metaResource = resource
    if metaResource is None:
        raise ValueError("contentIndex main metadata resource binding 실패")
    return ContentIndexBinding(
        manifestDigest=hashlib.sha256(manifestBytes).hexdigest(),
        artifactSetDigest=canonicalDigest(tuple(bound)),
        resourceVersionIds=tuple(sorted(item[3] for item in bound)),
        metaResourceVersionId=metaResource.resourceVersionId,
        metaPath=(activeDir / "main_meta.parquet").resolve(),
    )


def _defaultSearch(queryText: str, limit: int) -> tuple[dict[str, object], ...]:
    from dartlab.providers.dart.search.fieldIndex import searchContent
    from dartlab.providers.dart.search.sourceIntent import detectSourceIntent

    sourceKind = detectSourceIntent(queryText, explicitScope="auto").sourceKind
    result = searchContent(queryText, sourceKind=sourceKind, limit=limit)
    if hasattr(result, "to_dicts"):
        return tuple(result.to_dicts())
    raise TypeError("dartlab.search 결과가 row mapping을 제공하지 않음")


def _defaultExactSearch(metaPath: Path, identifier: str, limit: int) -> tuple[dict[str, object], ...]:
    import polars as pl

    frame = (
        pl.scan_parquet(metaPath)
        .filter(
            (pl.col("rcept_no") == identifier)
            | pl.col("sourceRef").fill_null("").str.contains(identifier, literal=True)
        )
        .head(limit)
        .collect()
    )
    return tuple(frame.to_dicts())


def _dateValue(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    if re.fullmatch(r"\d{8}", text):
        return date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    try:
        return parseInstant(text).date()
    except ValueError:
        return None


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
        exactSearchCallable: Callable[[str, int], tuple[dict[str, object], ...]] | None = None,
        indexResourceVersionId: str | None = None,
    ) -> None:
        self.catalog = catalog
        self.binding = _bindLocalContentIndex(catalog) if searchCallable is None else None
        self.searchCallable = searchCallable or _defaultSearch
        self.exactSearchCallable = exactSearchCallable
        resourceByVersion = {item.resourceVersionId: item for item in catalog.resources}
        objectByResource: dict[str, CatalogObject] = {}
        for obj in catalog.objects:
            for resourceRef in obj.resourceRefs:
                objectByResource.setdefault(resourceRef, obj)
        if self.binding is not None:
            if indexResourceVersionId is not None and indexResourceVersionId != self.binding.metaResourceVersionId:
                raise ValueError("요청한 contentIndex resource와 active artifact binding이 다름")
            candidates = (resourceByVersion[self.binding.metaResourceVersionId],)
        elif indexResourceVersionId is not None:
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
        self.latestRuns: tuple[ContentSearchRun, ...] = ()
        self.preparation: ContentIndexPreparation | None = None
        self._retrievedByKey: dict[tuple[str, str], RetrievedEvidence] = {}
        self._activeQueryId: str | None = None

    def prepare(self) -> ContentIndexPreparation:
        """Source adapter cold load를 query latency 밖에서 명시적으로 준비한다."""
        if self.preparation is not None:
            return self.preparation
        started = time.perf_counter_ns()
        rows = self.searchCallable("qzvwxjkluniverseadapterwarmup", 1)
        outputDigest = canonicalDigest(
            tuple(
                (
                    self._safeText(row, "sourceRef"),
                    self._safeText(row, "rcept_no"),
                    self._safeText(row, "sourceDataAsOf") or self._safeText(row, "dataAsOf"),
                )
                for row in rows
            )
        )
        self.preparation = ContentIndexPreparation(
            artifactSetDigest=self.binding.artifactSetDigest if self.binding is not None else "FIXTURE",
            warmupResultCount=len(rows),
            durationMs=round((time.perf_counter_ns() - started) / 1_000_000, 6),
            outputDigest=outputDigest,
        )
        return self.preparation

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
        lane: QueryLane,
        query: UniverseQuery,
        exactNamespace: str = "",
    ) -> LaneHit | None:
        knownDate = parseInstant(query.timeContext.knownAt).date()
        rowKnownDate = (
            _dateValue(row.get("rcept_dt")) or _dateValue(row.get("dataAsOf")) or _dateValue(row.get("sourceDataAsOf"))
        )
        if rowKnownDate is None or rowKnownDate > knownDate:
            return None
        sourceRef = self._safeText(row, "sourceRef")
        rceptNo = self._safeText(row, "rcept_no")
        if not sourceRef and rceptNo:
            sourceRef = f"dart:filing:{rceptNo}"
        if not sourceRef:
            return None
        dataAsOf = self._safeText(row, "dataAsOf") or self._safeText(row, "sourceDataAsOf")
        rceptDate = self._safeText(row, "rcept_dt")
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
            ("artifactSetDigest", self.binding.artifactSetDigest if self.binding is not None else "FIXTURE"),
            ("indexManifestDigest", self.binding.manifestDigest if self.binding is not None else "FIXTURE"),
            ("sourceRef", sourceRef),
            ("dataAsOf", dataAsOf),
            ("rceptNo", rceptNo),
            ("rceptDate", rceptDate),
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
        laneScore = 1.0 if lane is QueryLane.EXACT else rawScore / maxScore if maxScore > 0 else 1.0 / rank
        reasons = (
            (f"EXACT_CONTENT_ID:{exactNamespace}", f"CONTENT_INDEX:{resultSource.upper()}")
            if lane is QueryLane.EXACT
            else (f"CONTENT_INDEX:{resultSource.upper()}", f"CONTENT_SCOPE:{scope.upper()}")
        )
        return LaneHit(
            candidateRef=candidateRef,
            candidateKind="CONTENT_HIT",
            laneScore=laneScore,
            reasonCodes=reasons,
            evidenceOverride=(evidence,),
        )

    def _visible(self, context: LexicalAdapterContext) -> bool:
        return (
            self.indexResource.visibility in context.allowedVisibility
            and self.indexObject.objectId in context.objectById
        )

    def _startQuery(self, query: UniverseQuery) -> None:
        if self._activeQueryId == query.queryId:
            return
        self._activeQueryId = query.queryId
        self._retrievedByKey.clear()
        self.latestRuns = ()

    def _recordRun(
        self,
        query: UniverseQuery,
        *,
        lane: QueryLane,
        requestedLimit: int,
        rows: tuple[dict[str, object], ...],
        selected: tuple[LaneHit, ...],
        rejected: int,
    ) -> None:
        for rank, hit in enumerate(selected, start=1):
            evidence = hit.evidenceOverride[0]
            self._retrievedByKey[(hit.candidateRef, evidence.evidenceId)] = RetrievedEvidence(
                candidateRef=hit.candidateRef,
                candidateKind=hit.candidateKind,
                rank=rank,
                score=hit.laneScore,
                scoreProvenance=(),
                evidence=evidence,
            )
        run = ContentSearchRun(
            queryId=query.queryId,
            lane=lane,
            indexResourceVersionId=self.indexResource.resourceVersionId,
            artifactSetDigest=self.binding.artifactSetDigest if self.binding is not None else "FIXTURE",
            requestedLimit=requestedLimit,
            receivedRowCount=len(rows),
            acceptedHitCount=len(selected),
            rejectedRowCount=rejected,
            outputDigest=canonicalDigest(
                tuple((hit.candidateRef, hit.laneScore, hit.reasonCodes, hit.evidenceOverride[0]) for hit in selected)
            ),
        )
        self.latestRun = run
        self.latestRuns = (*self.latestRuns, run)

    @staticmethod
    def _contentIdentifiers(query: UniverseQuery) -> tuple[tuple[str, str], ...]:
        identifiers = []
        for item in query.explicitIdentifiers:
            namespace, separator, value = item.partition(":")
            if not separator:
                continue
            if namespace == "DART_RCEPT_NO" and re.fullmatch(r"\d{14}", value):
                identifiers.append((namespace, value))
            elif namespace == "SEC_ACCESSION" and re.fullmatch(r"\d{10}-\d{2}-\d{6}", value):
                identifiers.append((namespace, value))
        return tuple(sorted(set(identifiers)))

    @staticmethod
    def _exactRowMatches(row: dict[str, object], namespace: str, value: str) -> bool:
        rceptNo = str(row.get("rcept_no") or "").strip()
        sourceRef = str(row.get("sourceRef") or "").strip().casefold()
        source = str(row.get("source") or "").strip().casefold()
        if rceptNo != value and value.casefold() not in sourceRef:
            return False
        if namespace == "DART_RCEPT_NO":
            return sourceRef.startswith("dart:") or source in {"allfilings", "panel"}
        return sourceRef.startswith("edgar:") or source.startswith("edgar")

    def searchExact(self, query: UniverseQuery, context: LexicalAdapterContext) -> LaneResult:
        self._startQuery(query)
        if not self._visible(context):
            return LaneResult(QueryLane.EXACT, (), 0, 0, False, "CONTENT_INDEX_VISIBILITY_DENIED")
        identifiers = self._contentIdentifiers(query)
        if not identifiers:
            return LaneResult(QueryLane.EXACT, (), 0, 0, False, "NO_EXACT_INPUT")
        requestedLimit = min(query.budget.exactLimit, 50)
        rows = []
        hits = []
        rejected = 0
        seen = set()
        for namespace, value in identifiers:
            if self.exactSearchCallable is not None:
                found = self.exactSearchCallable(value, requestedLimit)
            elif self.binding is not None:
                found = _defaultExactSearch(self.binding.metaPath, value, requestedLimit)
            else:
                found = ()
            rows.extend(found)
            for row in found:
                if not self._exactRowMatches(row, namespace, value):
                    rejected += 1
                    continue
                hit = self._hit(
                    row,
                    rank=len(hits) + 1,
                    maxScore=1.0,
                    lane=QueryLane.EXACT,
                    query=query,
                    exactNamespace=namespace,
                )
                if hit is None or hit.candidateRef in seen:
                    rejected += 1
                    continue
                seen.add(hit.candidateRef)
                hits.append(hit)
        ordered = tuple(sorted(hits, key=lambda item: (item.candidateKind, item.candidateRef)))
        selected = ordered[:requestedLimit]
        rowTuple = tuple(rows)
        self._recordRun(
            query,
            lane=QueryLane.EXACT,
            requestedLimit=requestedLimit,
            rows=rowTuple,
            selected=selected,
            rejected=rejected,
        )
        return LaneResult(
            lane=QueryLane.EXACT,
            hits=selected,
            candidateCount=len(ordered),
            withheldCount=0,
            truncated=len(ordered) > len(selected),
            reasonCode="LIMIT" if len(ordered) > len(selected) else ("COMPLETE" if selected else "NO_EXACT_MATCH"),
        )

    def search(self, query: UniverseQuery, context: LexicalAdapterContext) -> LaneResult:
        self._startQuery(query)
        if not self._visible(context):
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
            hit = self._hit(row, rank=rank, maxScore=maxScore, lane=QueryLane.LEXICAL, query=query)
            if hit is None or hit.candidateRef in seenCandidates:
                rejected += 1
                continue
            seenCandidates.add(hit.candidateRef)
            hits.append(hit)
        selected = tuple(hits[:requestedLimit])
        self._recordRun(
            query,
            lane=QueryLane.LEXICAL,
            requestedLimit=requestedLimit,
            rows=rows,
            selected=selected,
            rejected=rejected,
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
