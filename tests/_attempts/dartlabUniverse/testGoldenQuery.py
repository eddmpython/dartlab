"""U4 golden corpus schema와 G3, G4E model-free evaluator를 검증한다."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from tests._attempts.dartlabUniverse.query.engine import UniverseQueryEngine
from tests._attempts.dartlabUniverse.query.golden import evaluateGoldenQueries, loadGoldenQueries
from tests._attempts.dartlabUniverse.queryTestSupport import buildQueryRuntimeFixture


def _fixturePath() -> Path:
    return Path(__file__).parent / "fixtures" / "universeGoldenQueries.json"


def testFixtureGoldenQueriesPassExactStructuredPITContradictionAndLeakageGates():
    runtime = buildQueryRuntimeFixture()
    cases = loadGoldenQueries(_fixturePath(), scope="FIXTURE")

    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
    ) as engine:
        report = evaluateGoldenQueries(
            cases,
            engine=engine,
            catalog=runtime.catalog,
            snapshot=runtime.snapshot,
            graph=runtime.graph,
        )

    assert report.passed, report.failureCodes
    assert report.exactRecallAt1 == 1.0
    assert report.recallAt20 == 1.0
    assert report.structuredNumericAccuracy == 1.0
    assert report.sourceUnitPeriodMisclassificationCount == 0
    assert report.privateLeakageCount == 0
    assert report.g4eValidationRate == 1.0
    assert report.contradictionLaneExecutionRate == 1.0
    assert dict(report.laneContributionCounts)["CONTRADICTION"] > 0
    assert {item.caseId for item in report.results if item.completeness == "ABSTAIN"} == {
        "fixture-point-in-time-abstain",
        "fixture-public-cannot-see-local-resource",
    }


def testGoldenCorpusRejectsUnknownFieldsAndThresholdMutation(tmp_path):
    raw = json.loads(_fixturePath().read_text(encoding="utf-8"))
    raw["cases"][0]["inventedField"] = True
    changed = tmp_path / "bad.json"
    changed.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown fields"):
        loadGoldenQueries(changed)

    runtime = buildQueryRuntimeFixture()
    cases = loadGoldenQueries(_fixturePath(), scope="FIXTURE")
    wrong = replace(cases[0].expectations[0], candidateRef="du:v1:organization:" + "0" * 64)
    mutated = (replace(cases[0], expectations=(wrong,)), *cases[1:])
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
    ) as engine:
        report = evaluateGoldenQueries(
            mutated,
            engine=engine,
            catalog=runtime.catalog,
            snapshot=runtime.snapshot,
            graph=runtime.graph,
        )

    assert not report.passed
    assert {"EXACT_RECALL_AT_1_BELOW_THRESHOLD", "RECALL_AT_20_BELOW_THRESHOLD", "GOLDEN_CASE_FAILURE"}.issubset(
        report.failureCodes
    )
