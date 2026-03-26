"""AI 답변 평가 프레임워크.

Golden dataset + persona question set + replay utilities.
"""

from __future__ import annotations

import json
from pathlib import Path

from dartlab.ai.eval.diagnoser import (
    DiagnosisReport,
    diagnoseBatchResults,
    diagnoseFull,
    findCoverageGaps,
    findRegressions,
    findWeakTypes,
    mapCodeImpact,
)
from dartlab.ai.eval.remediation import (
    RemediationPlan,
    extractFailureCounts,
    generateRemediations,
)
from dartlab.ai.eval.replayRunner import (
    PersonaEvalCase,
    ReplayResult,
    ReviewEntry,
    StructuralEval,
    appendReviewEntry,
    evaluateReplay,
    loadPersonaCases,
    loadPersonaQuestionSet,
    loadReviewLog,
    replayCase,
    replaySuite,
    summarizeReplayResults,
)
from dartlab.ai.eval.scorer import ScoreCard, auto_score
from dartlab.ai.eval.truthHarvester import harvestBatch, harvestTruth

_GOLDEN_PATH = Path(__file__).parent / "golden.json"


def load_golden_dataset() -> list[dict]:
    """golden.json에서 QA pair 로드."""
    if not _GOLDEN_PATH.exists():
        return []
    with open(_GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


__all__ = [
    "PersonaEvalCase",
    "ReplayResult",
    "ReviewEntry",
    "ScoreCard",
    "StructuralEval",
    "appendReviewEntry",
    "auto_score",
    "evaluateReplay",
    "load_golden_dataset",
    "loadPersonaCases",
    "loadPersonaQuestionSet",
    "loadReviewLog",
    "replayCase",
    "replaySuite",
    "summarizeReplayResults",
    "harvestTruth",
    "harvestBatch",
    "DiagnosisReport",
    "diagnoseBatchResults",
    "diagnoseFull",
    "findCoverageGaps",
    "findRegressions",
    "findWeakTypes",
    "mapCodeImpact",
    "RemediationPlan",
    "extractFailureCounts",
    "generateRemediations",
]
