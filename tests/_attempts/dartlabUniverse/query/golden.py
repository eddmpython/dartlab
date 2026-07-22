"""U4 golden query corpus와 model-free G3, G4E 품질 평가기."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Callable

from ..canonical import canonicalDigest
from ..catalog.models import CatalogObject, CatalogState
from ..catalog.snapshot import CatalogSnapshot
from ..contracts import Visibility
from ..graph.query import GraphStore
from ..graph.statements import GraphStatement
from ..query.engine import UniverseQueryEngine
from ..query.models import (
    REQUIRED_QUERY_LANES,
    QueryFilters,
    QueryLane,
    QueryTimeContext,
    RetrievedEvidence,
    UniverseQuery,
    buildUniverseQuery,
)
from ..query.planner import buildQueryPlan
from ..validation.g4e import validateRetrievalEvidencePack

GOLDEN_QUERY_SCHEMA_VERSION = "du-query-gold-v1"


@dataclass(frozen=True, slots=True)
class GoldenStatementExpectation:
    predicate: str | None = None
    value: object | None = None
    unit: str | None = None
    currency: str | None = None
    scope: str | None = None
    periodStart: str | None = None
    periodEnd: str | None = None
    instant: str | None = None
    epistemicClass: str | None = None


@dataclass(frozen=True, slots=True)
class GoldenExpectation:
    section: str
    topK: int
    candidateKind: str | None = None
    candidateRef: str | None = None
    objectIdentifier: str | None = None
    objectLabelContains: str | None = None
    sourceRefPrefix: str | None = None
    selector: tuple[tuple[str, str], ...] = ()
    statement: GoldenStatementExpectation | None = None


@dataclass(frozen=True, slots=True)
class GoldenQueryCase:
    caseId: str
    scope: str
    tags: tuple[str, ...]
    queryText: str
    timeContext: QueryTimeContext
    visibility: frozenset[Visibility]
    filters: QueryFilters
    expectations: tuple[GoldenExpectation, ...]
    expectNoEvidence: bool
    expectCompleteness: str | None


@dataclass(frozen=True, slots=True)
class GoldenCaseResult:
    caseId: str
    passed: bool
    latencyMs: float
    packId: str
    completeness: str
    candidateEvidenceCount: int
    contradictoryEvidenceCount: int
    matchedExpectationCount: int
    expectedExpectationCount: int
    g4eValid: bool
    laneCandidateCounts: tuple[tuple[str, int], ...]
    laneContributionCounts: tuple[tuple[str, int], ...]
    ablationRetained: tuple[tuple[str, bool], ...]
    failureCodes: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class GoldenThresholds:
    exactRecallAt1: float = 1.0
    recallAt20: float = 0.95
    structuredNumericAccuracy: float = 1.0
    maxSourceUnitPeriodMisclassificationCount: int = 0
    maxPrivateLeakageCount: int = 0
    g4eValidationRate: float = 1.0
    contradictionLaneExecutionRate: float = 1.0
    hybridRetrievalP95Ms: float = 1500.0


@dataclass(frozen=True, slots=True)
class GoldenEvaluationReport:
    passed: bool
    schemaVersion: str
    corpusDigest: str
    snapshotId: str
    scope: str
    caseCount: int
    exactCaseCount: int
    exactRecallAt1: float
    positiveCaseCount: int
    recallAt20: float
    structuredNumericCaseCount: int
    structuredNumericAccuracy: float
    sourceUnitPeriodMisclassificationCount: int
    privateLeakageCaseCount: int
    privateLeakageCount: int
    g4eValidationRate: float
    contradictionLaneExecutionRate: float
    hybridRetrievalP95Ms: float
    laneContributionCounts: tuple[tuple[str, int], ...]
    laneAblationRecallAt20: tuple[tuple[str, float], ...]
    thresholdsDigest: str
    results: tuple[GoldenCaseResult, ...]
    failureCodes: tuple[str, ...]
    digest: str


def _exactKeys(value: dict[str, object], allowed: frozenset[str], *, path: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"{path} unknown fields: {','.join(sorted(unknown))}")


def _tupleStrings(value: object, *, path: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{path}는 non-empty string array여야 함")
    return tuple(value)


def _loadFilters(value: object, *, path: str) -> QueryFilters:
    if value is None:
        return QueryFilters()
    if not isinstance(value, dict):
        raise ValueError(f"{path}는 object여야 함")
    allowed = frozenset(field.name for field in fields(QueryFilters))
    _exactKeys(value, allowed, path=path)
    sequenceFields = {
        "exactRefs",
        "identifiers",
        "objectKinds",
        "resourceKinds",
        "sourceKinds",
        "subjectRefs",
        "predicates",
    }
    normalized = {
        key: _tupleStrings(item, path=f"{path}.{key}") if key in sequenceFields else item for key, item in value.items()
    }
    return QueryFilters(**normalized)


def _loadStatement(value: object, *, path: str) -> GoldenStatementExpectation | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"{path}는 object여야 함")
    allowed = frozenset(field.name for field in fields(GoldenStatementExpectation))
    _exactKeys(value, allowed, path=path)
    return GoldenStatementExpectation(**value)


def _loadExpectation(value: object, *, path: str) -> GoldenExpectation:
    if not isinstance(value, dict):
        raise ValueError(f"{path}는 object여야 함")
    allowed = frozenset(field.name for field in fields(GoldenExpectation))
    _exactKeys(value, allowed, path=path)
    selector = value.get("selector") or {}
    if not isinstance(selector, dict) or any(
        not isinstance(key, str) or not isinstance(item, str) for key, item in selector.items()
    ):
        raise ValueError(f"{path}.selector는 string map이어야 함")
    section = str(value.get("section") or "CANDIDATE").upper()
    topK = value.get("topK", 20)
    if (
        section not in {"CANDIDATE", "CONTRADICTORY"}
        or isinstance(topK, bool)
        or not isinstance(topK, int)
        or topK < 1
        or topK > 100
    ):
        raise ValueError(f"{path} section 또는 topK가 잘못됨")
    return GoldenExpectation(
        section=section,
        topK=topK,
        candidateKind=value.get("candidateKind"),
        candidateRef=value.get("candidateRef"),
        objectIdentifier=value.get("objectIdentifier"),
        objectLabelContains=value.get("objectLabelContains"),
        sourceRefPrefix=value.get("sourceRefPrefix"),
        selector=tuple(sorted((str(key), str(item)) for key, item in selector.items())),
        statement=_loadStatement(value.get("statement"), path=f"{path}.statement"),
    )


def loadGoldenQueries(path: Path, *, scope: str | None = None) -> tuple[GoldenQueryCase, ...]:
    """Strict JSON fixture를 typed golden case로 읽는다."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("golden corpus root는 object여야 함")
    _exactKeys(raw, frozenset({"schemaVersion", "cases"}), path="root")
    if raw.get("schemaVersion") != GOLDEN_QUERY_SCHEMA_VERSION or not isinstance(raw.get("cases"), list):
        raise ValueError("golden corpus schema가 잘못됨")
    cases = []
    allowed = frozenset(field.name for field in fields(GoldenQueryCase))
    allowed = (allowed - {"visibility"}) | {"allowedVisibility"}
    for index, value in enumerate(raw["cases"]):
        if not isinstance(value, dict):
            raise ValueError(f"cases[{index}]는 object여야 함")
        _exactKeys(value, allowed, path=f"cases[{index}]")
        caseScope = str(value.get("scope") or "").upper()
        if scope is not None and caseScope != scope.upper():
            continue
        visibilityValues = _tupleStrings(value.get("allowedVisibility"), path=f"cases[{index}].allowedVisibility")
        try:
            visibility = frozenset(Visibility(item) for item in visibilityValues)
        except ValueError as exc:
            raise ValueError(f"cases[{index}] visibility가 잘못됨") from exc
        expectationsRaw = value.get("expectations") or []
        if not isinstance(expectationsRaw, list):
            raise ValueError(f"cases[{index}].expectations는 array여야 함")
        expectations = tuple(
            _loadExpectation(item, path=f"cases[{index}].expectations[{offset}]")
            for offset, item in enumerate(expectationsRaw)
        )
        expectNoEvidence = bool(value.get("expectNoEvidence", False))
        if not visibility or not caseScope or expectNoEvidence == bool(expectations):
            raise ValueError(f"cases[{index}] visibility, scope 또는 expectation 계약이 잘못됨")
        timeValue = value.get("timeContext")
        if not isinstance(timeValue, dict) or set(timeValue) != {"validAt", "knownAt"}:
            raise ValueError(f"cases[{index}].timeContext가 잘못됨")
        cases.append(
            GoldenQueryCase(
                caseId=str(value.get("caseId") or ""),
                scope=caseScope,
                tags=tuple(sorted(set(_tupleStrings(value.get("tags"), path=f"cases[{index}].tags")))),
                queryText=str(value.get("queryText") or ""),
                timeContext=QueryTimeContext(str(timeValue["validAt"]), str(timeValue["knownAt"])),
                visibility=visibility,
                filters=_loadFilters(value.get("filters"), path=f"cases[{index}].filters"),
                expectations=expectations,
                expectNoEvidence=expectNoEvidence,
                expectCompleteness=value.get("expectCompleteness"),
            )
        )
    if any(not item.caseId or not item.queryText for item in cases) or len({item.caseId for item in cases}) != len(
        cases
    ):
        raise ValueError("golden case ID 또는 query text가 비었거나 중복됨")
    return tuple(cases)


def _statementMatches(statement: GraphStatement, expected: GoldenStatementExpectation) -> bool:
    for field in fields(expected):
        value = getattr(expected, field.name)
        if value is None:
            continue
        actual = getattr(statement, field.name)
        if field.name == "epistemicClass":
            actual = actual.value
        if actual != value:
            return False
    return True


def _matches(
    item: RetrievedEvidence,
    expected: GoldenExpectation,
    *,
    objectById: dict[str, CatalogObject],
    statementById: dict[str, GraphStatement],
) -> bool:
    if item.rank > expected.topK:
        return False
    if expected.candidateKind is not None and item.candidateKind != expected.candidateKind:
        return False
    if expected.candidateRef is not None and item.candidateRef != expected.candidateRef:
        return False
    obj = objectById.get(item.candidateRef)
    if expected.objectIdentifier is not None and (obj is None or expected.objectIdentifier not in obj.identifierRefs):
        return False
    if expected.objectLabelContains is not None and (
        obj is None or expected.objectLabelContains.casefold() not in obj.canonicalLabel.casefold()
    ):
        return False
    selector = dict(item.evidence.selector)
    if expected.sourceRefPrefix is not None:
        sourceRef = selector.get("sourceRef", item.evidence.sourceRef)
        if not sourceRef.startswith(expected.sourceRefPrefix):
            return False
    if any(selector.get(key) != value for key, value in expected.selector):
        return False
    if expected.statement is not None:
        statement = statementById.get(item.candidateRef)
        if statement is None or not _statementMatches(statement, expected.statement):
            return False
    return True


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * quantile) - 1))
    return ordered[index]


def _ablation(
    evidence: tuple[RetrievedEvidence, ...],
    expectations: tuple[GoldenExpectation, ...],
    *,
    lane: QueryLane,
    objectById: dict[str, CatalogObject],
    statementById: dict[str, GraphStatement],
) -> bool:
    candidateByKey: dict[tuple[str, str], RetrievedEvidence] = {}
    scoreByKey: dict[tuple[str, str], float] = {}
    for item in evidence:
        key = (item.candidateKind, item.candidateRef)
        remaining = tuple(part for part in item.scoreProvenance if part.lane is not lane)
        if not remaining:
            continue
        candidateByKey.setdefault(key, item)
        scoreByKey[key] = sum(part.fusionContribution for part in remaining)
    ranked = sorted(candidateByKey, key=lambda key: (-scoreByKey[key], key))
    reranked = tuple(
        replace(candidateByKey[key], rank=rank, score=scoreByKey[key]) for rank, key in enumerate(ranked, 1)
    )
    return all(
        any(_matches(item, expected, objectById=objectById, statementById=statementById) for item in reranked)
        for expected in expectations
        if expected.section == "CANDIDATE"
    )


def evaluateGoldenQueries(
    cases: tuple[GoldenQueryCase, ...],
    *,
    engine: UniverseQueryEngine,
    catalog: CatalogState,
    snapshot: CatalogSnapshot,
    graph: GraphStore,
    virtualRetrievedVerifiers: tuple[Callable[[RetrievedEvidence], bool], ...] = (),
    executionRefVerifiers: tuple[Callable[[str], bool], ...] = (),
    prepareVirtualReplay: Callable[[UniverseQuery], None] | None = None,
    thresholds: GoldenThresholds | None = None,
) -> GoldenEvaluationReport:
    """Golden query를 실행하고 retrieval, provenance, leakage, ablation을 한 report로 닫는다."""
    if not cases:
        raise ValueError("golden case가 비어 있음")
    activeThresholds = thresholds or GoldenThresholds()
    objectById = {item.objectId: item for item in catalog.objects}
    statementById = {item.statementId: item for item in graph.statements}
    results = []
    exactPassed = 0
    positivePassed = 0
    structuredPassed = 0
    misclassified = 0
    leakageCount = 0
    g4ePassed = 0
    contradictionExecuted = 0
    contributionCounts = {lane: 0 for lane in REQUIRED_QUERY_LANES}
    ablationPassed = {lane: 0 for lane in REQUIRED_QUERY_LANES}
    latencies = []
    positiveCases = tuple(item for item in cases if item.expectations)
    exactCases = tuple(item for item in cases if "EXACT" in item.tags)
    structuredCases = tuple(item for item in cases if "STRUCTURED_NUMERIC" in item.tags)
    leakageCases = tuple(item for item in cases if "PRIVATE_LEAKAGE" in item.tags)
    for visibility in {item.visibility for item in cases}:
        engine.prepare(visibility)
    for case in cases:
        query = buildUniverseQuery(
            case.queryText,
            timeContext=case.timeContext,
            allowedVisibility=case.visibility,
            filters=case.filters,
        )
        plan = buildQueryPlan(query, snapshot)
        started = time.perf_counter_ns()
        pack = engine.execute(query, plan=plan)
        latencyMs = (time.perf_counter_ns() - started) / 1_000_000
        latencies.append(latencyMs)
        if prepareVirtualReplay is not None:
            prepareVirtualReplay(query)
        g4e = validateRetrievalEvidencePack(
            pack,
            query=query,
            plan=plan,
            snapshot=snapshot,
            catalog=catalog,
            graph=graph,
            virtualRetrievedVerifiers=virtualRetrievedVerifiers,
            executionRefVerifiers=executionRefVerifiers,
        )
        if g4e.valid:
            g4ePassed += 1
        contradictionCoverage = next(
            (item for item in pack.laneCoverage if item.lane is QueryLane.CONTRADICTION),
            None,
        )
        if contradictionCoverage is not None and contradictionCoverage.executed:
            contradictionExecuted += 1
        sectionItems = {
            "CANDIDATE": pack.candidateEvidence,
            "CONTRADICTORY": pack.contradictoryEvidence,
        }
        matched = tuple(
            any(
                _matches(item, expected, objectById=objectById, statementById=statementById)
                for item in sectionItems[expected.section]
            )
            for expected in case.expectations
        )
        failures = []
        if case.expectations and not all(matched):
            failures.append("EXPECTED_EVIDENCE_MISSING")
        if case.expectNoEvidence and (pack.candidateEvidence or pack.contradictoryEvidence):
            failures.append("NEGATIVE_CASE_EVIDENCE_LEAK")
            if "PRIVATE_LEAKAGE" in case.tags:
                leakageCount += 1
        if case.expectCompleteness is not None and pack.completeness != case.expectCompleteness:
            failures.append("COMPLETENESS_MISMATCH")
        if not g4e.valid:
            failures.append("G4E_INVALID")
        passed = not failures
        if case.expectations and all(matched):
            positivePassed += 1
        if "EXACT" in case.tags and all(matched) and all(expected.topK == 1 for expected in case.expectations):
            exactPassed += 1
        if "STRUCTURED_NUMERIC" in case.tags:
            if all(matched):
                structuredPassed += 1
            elif any(item.candidateKind == "STATEMENT" for item in pack.candidateEvidence):
                misclassified += 1
        localContributionCounts = {lane: 0 for lane in REQUIRED_QUERY_LANES}
        for item in (*pack.candidateEvidence, *pack.contradictoryEvidence):
            for contribution in item.scoreProvenance:
                localContributionCounts[contribution.lane.value] += 1
                contributionCounts[contribution.lane.value] += 1
        ablation = []
        for laneName in REQUIRED_QUERY_LANES:
            retained = (
                _ablation(
                    pack.candidateEvidence,
                    case.expectations,
                    lane=QueryLane(laneName),
                    objectById=objectById,
                    statementById=statementById,
                )
                if case.expectations
                else True
            )
            ablation.append((laneName, retained))
            if case.expectations and retained:
                ablationPassed[laneName] += 1
        baseResult = GoldenCaseResult(
            caseId=case.caseId,
            passed=passed,
            latencyMs=round(latencyMs, 6),
            packId=pack.packId,
            completeness=pack.completeness,
            candidateEvidenceCount=len(pack.candidateEvidence),
            contradictoryEvidenceCount=len(pack.contradictoryEvidence),
            matchedExpectationCount=sum(matched),
            expectedExpectationCount=len(matched),
            g4eValid=g4e.valid,
            laneCandidateCounts=tuple((item.lane.value, item.candidateCount) for item in pack.laneCoverage),
            laneContributionCounts=tuple(sorted(localContributionCounts.items())),
            ablationRetained=tuple(ablation),
            failureCodes=tuple(sorted(failures)),
            digest="",
        )
        results.append(replace(baseResult, digest=canonicalDigest(baseResult)))
    exactRecall = exactPassed / len(exactCases) if exactCases else 1.0
    recallAt20 = positivePassed / len(positiveCases) if positiveCases else 1.0
    structuredAccuracy = structuredPassed / len(structuredCases) if structuredCases else 1.0
    g4eRate = g4ePassed / len(cases)
    contradictionRate = contradictionExecuted / len(cases)
    latencyP95 = _percentile(latencies, 0.95)
    failures = []
    if exactRecall < activeThresholds.exactRecallAt1:
        failures.append("EXACT_RECALL_AT_1_BELOW_THRESHOLD")
    if recallAt20 < activeThresholds.recallAt20:
        failures.append("RECALL_AT_20_BELOW_THRESHOLD")
    if structuredAccuracy < activeThresholds.structuredNumericAccuracy:
        failures.append("STRUCTURED_NUMERIC_ACCURACY_BELOW_THRESHOLD")
    if misclassified > activeThresholds.maxSourceUnitPeriodMisclassificationCount:
        failures.append("SOURCE_UNIT_PERIOD_MISCLASSIFIED")
    if leakageCount > activeThresholds.maxPrivateLeakageCount:
        failures.append("PRIVATE_VISIBILITY_LEAK")
    if g4eRate < activeThresholds.g4eValidationRate:
        failures.append("G4E_VALIDATION_RATE_BELOW_THRESHOLD")
    if contradictionRate < activeThresholds.contradictionLaneExecutionRate:
        failures.append("CONTRADICTION_LANE_EXECUTION_BELOW_THRESHOLD")
    if latencyP95 > activeThresholds.hybridRetrievalP95Ms:
        failures.append("HYBRID_RETRIEVAL_P95_SLO_EXCEEDED")
    if any(not item.passed for item in results):
        failures.append("GOLDEN_CASE_FAILURE")
    base = GoldenEvaluationReport(
        passed=False,
        schemaVersion=GOLDEN_QUERY_SCHEMA_VERSION,
        corpusDigest=canonicalDigest(cases),
        snapshotId=snapshot.snapshotId,
        scope=cases[0].scope if len({item.scope for item in cases}) == 1 else "MIXED",
        caseCount=len(cases),
        exactCaseCount=len(exactCases),
        exactRecallAt1=exactRecall,
        positiveCaseCount=len(positiveCases),
        recallAt20=recallAt20,
        structuredNumericCaseCount=len(structuredCases),
        structuredNumericAccuracy=structuredAccuracy,
        sourceUnitPeriodMisclassificationCount=misclassified,
        privateLeakageCaseCount=len(leakageCases),
        privateLeakageCount=leakageCount,
        g4eValidationRate=g4eRate,
        contradictionLaneExecutionRate=contradictionRate,
        hybridRetrievalP95Ms=round(latencyP95, 6),
        laneContributionCounts=tuple(sorted(contributionCounts.items())),
        laneAblationRecallAt20=tuple(
            (lane, ablationPassed[lane] / len(positiveCases) if positiveCases else 1.0) for lane in REQUIRED_QUERY_LANES
        ),
        thresholdsDigest=canonicalDigest(activeThresholds),
        results=tuple(results),
        failureCodes=tuple(sorted(set(failures))),
        digest="",
    )
    report = replace(base, passed=not base.failureCodes)
    return replace(report, digest=canonicalDigest(report))
