"""Persona question replay runner for ask regression."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from dartlab.engines.ai.eval.scorer import ScoreCard, auto_score, score_module_utilization
from dartlab.engines.ai.runtime.events import AnalysisEvent

_PERSONA_CASES_PATH = Path(__file__).parent / "personaCases.json"
_REVIEW_LOG_DIR = Path(__file__).parent / "reviewLog"


@dataclass(frozen=True)
class PersonaEvalCase:
    """Single curated ask regression case."""

    id: str
    persona: str
    personaLabel: str
    question: str
    userIntent: str
    stockCode: str | None = None
    expectedAnswerShape: list[str] = field(default_factory=list)
    expectedEvidenceKinds: list[str] = field(default_factory=list)
    expectedUserFacingTerms: list[str] = field(default_factory=list)
    forbiddenUiTerms: list[str] = field(default_factory=list)
    expectedRoute: str | None = None
    expectedModules: list[str] = field(default_factory=list)
    allowedClarification: bool = False
    mustNotSay: list[str] = field(default_factory=list)
    mustInclude: list[str] = field(default_factory=list)
    expectedFollowups: list[str] = field(default_factory=list)
    groundTruthFacts: list[dict[str, Any]] = field(default_factory=list)
    severity: str = "medium"


@dataclass
class StructuralEval:
    """Replay structure checks before answer-quality scoring."""

    expectedRoute: str | None = None
    actualRoute: str | None = None
    routeMatch: float = 1.0
    moduleUtilization: float = 1.0
    clarificationAllowed: bool = False
    clarificationNeeded: bool = False
    clarificationQuality: float = 1.0
    unexpectedModules: list[str] = field(default_factory=list)
    failureTypes: list[str] = field(default_factory=list)


@dataclass
class ReplayResult:
    """Full replay result for a single curated case."""

    case: PersonaEvalCase
    answer: str
    provider: str | None = None
    model: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    done: dict[str, Any] = field(default_factory=dict)
    contexts: list[dict[str, Any]] = field(default_factory=list)
    toolEvents: list[dict[str, Any]] = field(default_factory=list)
    structural: StructuralEval = field(default_factory=StructuralEval)
    score: ScoreCard = field(default_factory=ScoreCard)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def toDict(self) -> dict[str, Any]:
        """Dataclass-friendly JSON view."""
        payload = asdict(self)
        payload["score"]["overall"] = self.score.overall
        return payload


@dataclass(frozen=True)
class ReviewEntry:
    """Human-reviewed replay note for long-term stabilization."""

    reviewedAt: str
    caseId: str
    persona: str
    provider: str | None
    model: str | None
    effectiveness: str
    improvementActions: list[str] = field(default_factory=list)
    failureTypes: list[str] = field(default_factory=list)
    notes: str = ""


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": "missing", "cases": []}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def loadPersonaQuestionSet() -> dict[str, Any]:
    """Load persona question set manifest."""
    return _load_json(_PERSONA_CASES_PATH)


def loadPersonaCases(*, persona: str | None = None, severity: str | None = None) -> list[PersonaEvalCase]:
    """Load curated persona cases with optional filters."""
    raw = loadPersonaQuestionSet()
    cases: list[PersonaEvalCase] = []
    for item in raw.get("cases", []):
        if persona and item.get("persona") != persona:
            continue
        if severity and item.get("severity") != severity:
            continue
        cases.append(
            PersonaEvalCase(
                id=item["id"],
                persona=item["persona"],
                personaLabel=item.get("personaLabel", item["persona"]),
                stockCode=item.get("stockCode"),
                question=item["question"],
                userIntent=item.get("userIntent", ""),
                expectedAnswerShape=list(item.get("expectedAnswerShape", [])),
                expectedEvidenceKinds=list(item.get("expectedEvidenceKinds", [])),
                expectedUserFacingTerms=list(item.get("expectedUserFacingTerms", [])),
                forbiddenUiTerms=list(item.get("forbiddenUiTerms", [])),
                expectedRoute=item.get("expectedRoute"),
                expectedModules=list(item.get("expectedModules", [])),
                allowedClarification=bool(item.get("allowedClarification", False)),
                mustNotSay=list(item.get("mustNotSay", [])),
                mustInclude=list(item.get("mustInclude", [])),
                expectedFollowups=list(item.get("expectedFollowups", [])),
                groundTruthFacts=list(item.get("groundTruthFacts", [])),
                severity=item.get("severity", "medium"),
            )
        )
    return cases


def _resolve_company(stockCode: str | None) -> Any | None:
    if not stockCode:
        return None
    from dartlab import Company

    return Company(stockCode)


def _collect_replay_data(
    events: list[AnalysisEvent],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], str, list[dict[str, Any]]]:
    meta: dict[str, Any] = {}
    done: dict[str, Any] = {}
    contexts: list[dict[str, Any]] = []
    toolEvents: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    chunks: list[str] = []

    for event in events:
        data = event.data or {}
        if event.kind == "meta":
            meta.update(data)
        elif event.kind == "context":
            contexts.append(data)
        elif event.kind == "tool_call":
            toolEvents.append({"type": "call"} | data)
        elif event.kind == "tool_result":
            toolEvents.append({"type": "result"} | data)
        elif event.kind == "chunk":
            chunks.append(data.get("text", ""))
        elif event.kind == "done":
            done = data
        elif event.kind == "error":
            errors.append(data)

    return meta, done, contexts, toolEvents, "".join(chunks), errors


def evaluateReplay(
    case: PersonaEvalCase, events: list[AnalysisEvent], *, provider: str | None = None, model: str | None = None
) -> ReplayResult:
    """Evaluate already-collected analysis events."""
    meta, done, contexts, toolEvents, answer, errors = _collect_replay_data(events)
    includedModules = list(done.get("includedModules") or meta.get("includedModules") or [])
    actualRoute = done.get("route")
    clarificationNeeded = bool(done.get("clarificationNeeded"))
    moduleUtilization = score_module_utilization(includedModules, case.expectedModules)
    routeMatch = 1.0 if not case.expectedRoute or case.expectedRoute == actualRoute else 0.0
    clarificationQuality = 1.0
    if clarificationNeeded and not case.allowedClarification:
        clarificationQuality = 0.0

    structuralFailures: list[str] = []
    if routeMatch == 0.0:
        structuralFailures.append("routing_failure")
    if moduleUtilization < 1.0:
        structuralFailures.append("retrieval_failure")
    if clarificationQuality == 0.0:
        structuralFailures.append("clarification_failure")
    if errors:
        structuralFailures.append("runtime_error")

    score = auto_score(
        answer,
        expected_facts=case.groundTruthFacts,
        expected_topics=case.expectedUserFacingTerms,
        included_modules=includedModules,
        expected_modules=case.expectedModules,
        must_not_say=case.mustNotSay,
        must_include=case.mustInclude,
        forbidden_terms=case.forbiddenUiTerms,
        clarification_allowed=case.allowedClarification,
        expected_followups=case.expectedFollowups,
        expected_route=case.expectedRoute,
        actual_route=actualRoute,
    )
    failureTypes = sorted(set(structuralFailures + score.failure_types))
    score.failure_types = failureTypes

    structural = StructuralEval(
        expectedRoute=case.expectedRoute,
        actualRoute=actualRoute,
        routeMatch=routeMatch,
        moduleUtilization=moduleUtilization,
        clarificationAllowed=case.allowedClarification,
        clarificationNeeded=clarificationNeeded,
        clarificationQuality=clarificationQuality,
        unexpectedModules=sorted(set(includedModules) - set(case.expectedModules)),
        failureTypes=failureTypes,
    )

    return ReplayResult(
        case=case,
        answer=answer,
        provider=provider,
        model=model,
        meta=meta,
        done=done,
        contexts=contexts,
        toolEvents=toolEvents,
        structural=structural,
        score=score,
        errors=errors,
    )


def replayCase(
    case: PersonaEvalCase,
    *,
    provider: str | None = None,
    model: str | None = None,
    reportMode: bool = False,
    useTools: bool = False,
    analyzeFn: Callable[..., Any] | None = None,
    company: Any | None = None,
    **kwargs: Any,
) -> ReplayResult:
    """Run a real ask replay for one curated case."""
    if analyzeFn is None:
        from dartlab.engines.ai.runtime.core import analyze as analyzeFn

    effectiveCompany = company if company is not None else _resolve_company(case.stockCode)
    events = list(
        analyzeFn(
            effectiveCompany,
            case.question,
            provider=provider,
            model=model,
            report_mode=reportMode,
            use_tools=useTools,
            **kwargs,
        )
    )
    return evaluateReplay(case, events, provider=provider, model=model)


def replaySuite(
    cases: list[PersonaEvalCase],
    *,
    provider: str | None = None,
    model: str | None = None,
    reportMode: bool = False,
    useTools: bool = False,
    analyzeFn: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> list[ReplayResult]:
    """Replay a full curated suite."""
    return [
        replayCase(
            case,
            provider=provider,
            model=model,
            reportMode=reportMode,
            useTools=useTools,
            analyzeFn=analyzeFn,
            **kwargs,
        )
        for case in cases
    ]


def summarizeReplayResults(results: list[ReplayResult]) -> dict[str, Any]:
    """Aggregate replay results for regression dashboards or logs."""
    if not results:
        return {
            "cases": 0,
            "personas": 0,
            "avgOverall": 0.0,
            "avgRouteMatch": 0.0,
            "avgModuleUtilization": 0.0,
            "falseUnavailableCases": 0,
            "failureCounts": {},
        }

    failureCounts: dict[str, int] = {}
    for result in results:
        for failure in result.score.failure_types:
            failureCounts[failure] = failureCounts.get(failure, 0) + 1

    return {
        "cases": len(results),
        "personas": len({result.case.persona for result in results}),
        "avgOverall": round(mean(result.score.overall for result in results), 3),
        "avgRouteMatch": round(mean(result.structural.routeMatch for result in results), 3),
        "avgModuleUtilization": round(mean(result.structural.moduleUtilization for result in results), 3),
        "falseUnavailableCases": sum(1 for result in results if result.score.false_unavailable == 0.0),
        "failureCounts": dict(sorted(failureCounts.items())),
    }


def _reviewLogPath(persona: str) -> Path:
    return _REVIEW_LOG_DIR / f"{persona}.jsonl"


def loadReviewLog(*, persona: str | None = None, caseId: str | None = None) -> list[ReviewEntry]:
    """Load human review history for persona replays."""
    paths: list[Path]
    if persona:
        path = _reviewLogPath(persona)
        paths = [path] if path.exists() else []
    else:
        if not _REVIEW_LOG_DIR.exists():
            return []
        paths = sorted(_REVIEW_LOG_DIR.glob("*.jsonl"))

    entries: list[ReviewEntry] = []
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                item = json.loads(stripped)
                if caseId and item.get("caseId") != caseId:
                    continue
                entries.append(
                    ReviewEntry(
                        reviewedAt=item["reviewedAt"],
                        caseId=item["caseId"],
                        persona=item["persona"],
                        provider=item.get("provider"),
                        model=item.get("model"),
                        effectiveness=item["effectiveness"],
                        improvementActions=list(item.get("improvementActions", [])),
                        failureTypes=list(item.get("failureTypes", [])),
                        notes=item.get("notes", ""),
                    )
                )
    return sorted(entries, key=lambda item: item.reviewedAt)


def appendReviewEntry(
    result: ReplayResult,
    *,
    effectiveness: str,
    improvementActions: list[str] | None = None,
    notes: str = "",
    reviewedAt: str | None = None,
) -> ReviewEntry:
    """Append a reviewed replay note to the long-term stabilization log."""
    entry = ReviewEntry(
        reviewedAt=reviewedAt or datetime.now().isoformat(timespec="seconds"),
        caseId=result.case.id,
        persona=result.case.persona,
        provider=result.provider,
        model=result.model,
        effectiveness=effectiveness,
        improvementActions=list(improvementActions or []),
        failureTypes=list(result.score.failure_types),
        notes=notes,
    )
    _REVIEW_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(_reviewLogPath(result.case.persona), "a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    return entry
