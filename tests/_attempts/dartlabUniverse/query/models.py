"""U4 query와 불변 RetrievalEvidencePack 계약."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from enum import Enum

from ..canonical import canonicalDigest
from ..catalog.models import CatalogEvidence
from ..contracts import Visibility
from ..ids import logicalId
from ..temporal import parseInstant

QUERY_SCHEMA_VERSION = "du-query-v1"
RETRIEVAL_EVIDENCE_PACK_SCHEMA_VERSION = "du-retrieval-evidence-pack-v1"
REQUIRED_QUERY_LANES = ("EXACT", "STRUCTURED", "LEXICAL", "GRAPH", "CONTRADICTION")
_TOKEN_RE = re.compile(r"[\w가-힣]+(?:[-._:/][\w가-힣]+)*", re.UNICODE)
_DU_ID_RE = re.compile(r"du:v1:[a-z][a-z0-9-]{0,62}:[0-9a-f]{64}")
_EXPLICIT_IDENTIFIER_RE = re.compile(
    r"(?i)\b(DART_CORP_CODE|SEC_CIK|KR_STOCK_CODE|US_TICKER|ISIN)\s*[:=]\s*([A-Z0-9.-]+)"
)


class QueryLane(str, Enum):
    EXACT = "EXACT"
    STRUCTURED = "STRUCTURED"
    LEXICAL = "LEXICAL"
    GRAPH = "GRAPH"
    CONTRADICTION = "CONTRADICTION"


@dataclass(frozen=True, slots=True)
class QueryTimeContext:
    validAt: str
    knownAt: str


@dataclass(frozen=True, slots=True)
class QueryBudget:
    exactLimit: int = 100
    structuredLimit: int = 200
    lexicalLimit: int = 200
    graphMaxDepth: int = 2
    graphMaxNodes: int = 1000
    graphMaxEdges: int = 5000
    resultLimit: int = 100


@dataclass(frozen=True, slots=True)
class QueryFilters:
    exactRefs: tuple[str, ...] = ()
    identifiers: tuple[str, ...] = ()
    objectKinds: tuple[str, ...] = ()
    resourceKinds: tuple[str, ...] = ()
    sourceKinds: tuple[str, ...] = ()
    subjectRefs: tuple[str, ...] = ()
    predicates: tuple[str, ...] = ()
    periodStart: str | None = None
    periodEnd: str | None = None
    instant: str | None = None


@dataclass(frozen=True, slots=True)
class UniverseQuery:
    schemaVersion: str
    queryId: str
    queryTextDigest: str
    searchTerms: tuple[str, ...]
    explicitIdentifiers: tuple[str, ...]
    explicitUniverseRefs: tuple[str, ...]
    filters: QueryFilters
    timeContext: QueryTimeContext
    allowedVisibility: tuple[Visibility, ...]
    budget: QueryBudget
    digest: str


@dataclass(frozen=True, slots=True)
class LaneContribution:
    lane: QueryLane
    rank: int
    laneScore: float
    fusionContribution: float
    reasonCodes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RetrievedEvidence:
    candidateRef: str
    candidateKind: str
    rank: int
    score: float
    scoreProvenance: tuple[LaneContribution, ...]
    evidence: CatalogEvidence


@dataclass(frozen=True, slots=True)
class LaneCoverage:
    lane: QueryLane
    executed: bool
    candidateCount: int
    returnedCount: int
    withheldCount: int
    truncated: bool
    reasonCode: str


@dataclass(frozen=True, slots=True)
class RetrievalEvidencePack:
    schemaVersion: str
    packId: str
    snapshotId: str
    snapshotRootInputsDigest: str
    descriptorSetDigest: str
    recoverySetDigest: str
    queryId: str
    queryPlanDigest: str
    visibilityPolicyDigest: str
    sourceRevisionSet: tuple[tuple[str, str], ...]
    candidateEvidence: tuple[RetrievedEvidence, ...]
    contradictoryEvidence: tuple[RetrievedEvidence, ...]
    executionRefs: tuple[str, ...]
    laneCoverage: tuple[LaneCoverage, ...]
    truncationReasons: tuple[str, ...]
    withheldReasons: tuple[str, ...]
    unresolvedReasons: tuple[str, ...]
    completeness: str
    digest: str


def normalizeSearchTerms(queryText: str) -> tuple[str, ...]:
    """원문을 보존하지 않고 검색 가능한 NFC casefold term만 만든다."""
    normalized = unicodedata.normalize("NFC", queryText)
    return tuple(sorted({match.group(0).casefold() for match in _TOKEN_RE.finditer(normalized)}))


def _normalizeFilter(filters: QueryFilters) -> QueryFilters:
    return QueryFilters(
        exactRefs=tuple(sorted({item.strip() for item in filters.exactRefs if item.strip()})),
        identifiers=tuple(sorted({item.strip().upper() for item in filters.identifiers if item.strip()})),
        objectKinds=tuple(sorted({item.strip().upper() for item in filters.objectKinds if item.strip()})),
        resourceKinds=tuple(sorted({item.strip().upper() for item in filters.resourceKinds if item.strip()})),
        sourceKinds=tuple(sorted({item.strip().upper() for item in filters.sourceKinds if item.strip()})),
        subjectRefs=tuple(sorted({item.strip() for item in filters.subjectRefs if item.strip()})),
        predicates=tuple(sorted({item.strip().casefold() for item in filters.predicates if item.strip()})),
        periodStart=filters.periodStart,
        periodEnd=filters.periodEnd,
        instant=filters.instant,
    )


def _validateBudget(budget: QueryBudget) -> None:
    values = (
        budget.exactLimit,
        budget.structuredLimit,
        budget.lexicalLimit,
        budget.graphMaxNodes,
        budget.resultLimit,
    )
    if any(isinstance(item, bool) or item < 1 for item in values):
        raise ValueError("query 결과 budget은 1 이상이어야 함")
    if budget.graphMaxDepth < 0 or budget.graphMaxEdges < 0:
        raise ValueError("graph budget은 0 이상이어야 함")
    if max(values) > 100_000 or budget.graphMaxEdges > 100_000 or budget.graphMaxDepth > 8:
        raise ValueError("query budget 상한을 초과함")


def buildUniverseQuery(
    queryText: str,
    *,
    timeContext: QueryTimeContext,
    allowedVisibility: frozenset[Visibility],
    filters: QueryFilters | None = None,
    budget: QueryBudget | None = None,
) -> UniverseQuery:
    """비신뢰 원문은 digest와 term으로 축소하고 실행 가능한 명령은 만들지 않는다."""
    if not isinstance(queryText, str) or not queryText.strip():
        raise ValueError("query text는 비어 있을 수 없음")
    if not allowedVisibility or Visibility.UNKNOWN in allowedVisibility:
        raise ValueError("query visibility는 명시적이며 UNKNOWN일 수 없음")
    parseInstant(timeContext.validAt)
    parseInstant(timeContext.knownAt)
    activeBudget = budget or QueryBudget()
    _validateBudget(activeBudget)
    activeFilters = _normalizeFilter(filters or QueryFilters())
    normalizedText = unicodedata.normalize("NFC", queryText)
    explicitIdentifiers = tuple(
        sorted(
            {
                f"{match.group(1).upper()}:{match.group(2).upper()}"
                for match in _EXPLICIT_IDENTIFIER_RE.finditer(normalizedText)
            }
            | set(activeFilters.identifiers)
        )
    )
    explicitRefs = tuple(sorted(set(_DU_ID_RE.findall(normalizedText)) | set(activeFilters.exactRefs)))
    visibility = tuple(sorted(allowedVisibility, key=lambda item: item.value))
    queryTextDigest = canonicalDigest(normalizedText)
    base = UniverseQuery(
        schemaVersion=QUERY_SCHEMA_VERSION,
        queryId="",
        queryTextDigest=queryTextDigest,
        searchTerms=normalizeSearchTerms(normalizedText),
        explicitIdentifiers=explicitIdentifiers,
        explicitUniverseRefs=explicitRefs,
        filters=activeFilters,
        timeContext=timeContext,
        allowedVisibility=visibility,
        budget=activeBudget,
        digest="",
    )
    digest = canonicalDigest(base)
    return replace(base, queryId=logicalId("query", (digest,)), digest=digest)
