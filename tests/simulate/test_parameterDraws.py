"""Kill tests for exact, PIT-aware joint parameter draw provenance."""

from __future__ import annotations

from dataclasses import replace

import pytest

from dartlab.simulate.parameterDraws import (
    ParameterDrawError,
    bindParameterDrawSetReceipt,
    issueParameterDrawSetReceipt,
)
from dartlab.simulate.world import (
    LawSpec,
    ScenarioPath,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    simulateWorld,
)


def _paths() -> tuple[ScenarioPath, ...]:
    return (
        ScenarioPath(
            "low",
            ({"innovation": 1.0},),
            parameterDraws={"loading": 0.5, "decay": 0.8},
            knowledgeAsOf="20250101",
            historyStatus="asKnown",
        ),
        ScenarioPath(
            "high",
            ({"innovation": 1.0},),
            parameterDraws={"loading": 2.0, "decay": 0.6},
            knowledgeAsOf="20250101",
            historyStatus="asKnown",
        ),
    )


def _receipt(paths=None, **overrides):
    args = {
        "distributionId": "joint-loading-decay",
        "distributionKind": "jointEmpirical",
        "generatorVersion": "draw-v1",
        "seed": 7,
        "parameterUnits": {"loading": "outputPerInnovation", "decay": "ratio"},
        "frequency": "step",
        "stepSpan": 1,
        "maxAdmittedStep": 1,
        "fitThrough": "20241231",
        "availableAt": "20241231",
        "knowledgeAsOf": "20250101",
        "revisionPolicy": "asKnown",
        "coverage": "asOfExact",
        "distributionArtifactHash": "b" * 64,
    }
    args.update(overrides)
    return issueParameterDrawSetReceipt(_paths() if paths is None else paths, **args)


def _model() -> WorldModel:
    def law(ctx):
        return {"value": ctx.shocks["innovation"] * ctx.pathParameters["loading"] * ctx.pathParameters["decay"]}

    return WorldModel(
        "draw-world",
        "1",
        (
            VariableSpec("innovation", "change", "shock"),
            VariableSpec("value", "value", "metric"),
        ),
        (),
        (
            LawSpec(
                "draw-law",
                outputs=("value",),
                shockInputs=("innovation",),
                pathParameterInputs=("loading", "decay"),
                pathParameterUnits={"loading": "outputPerInnovation", "decay": "ratio"},
                parameters={"loading": 1.0, "decay": 1.0},
                fn=law,
            ),
        ),
    )


def _run(paths):
    return simulateWorld(
        _model(),
        WorldState({}, asOf="20250101", knowledgeAsOf="20250101", decisionAsOf="20250101"),
        paths,
        (StrategySpec("baseline", ({},), isBaseline=True),),
    )


def test_draw_receipt_binds_exact_joint_draw_set_and_digest() -> None:
    paths = _paths()
    receipt = _receipt(paths)
    bound = bindParameterDrawSetReceipt(paths, receipt)
    run = _run(bound)
    assert receipt.status == "documented"
    assert "parameterMeasure:documentedOnly" in run.warnings
    with pytest.raises(ParameterDrawError, match="digest mismatch"):
        bindParameterDrawSetReceipt(paths, replace(receipt, seed=8))
    tampered = (replace(bound[0], parameterDraws={"loading": 9.0, "decay": 0.8}), bound[1])
    with pytest.raises(ParameterDrawError, match="draw set hash mismatch"):
        _run(tampered)


def test_draw_receipt_rejects_future_or_mixed_parameter_evidence() -> None:
    with pytest.raises(ParameterDrawError, match="fitThrough is newer"):
        _receipt(fitThrough="20250102")
    mixed = (_paths()[0], replace(_paths()[1], parameterDraws={"loading": 2.0}))
    with pytest.raises(ParameterDrawError, match="same parameter names"):
        _receipt(mixed)
    receipt = _receipt(knowledgeAsOf="20250102")
    with pytest.raises(ParameterDrawError, match="newer than path"):
        bindParameterDrawSetReceipt(_paths(), receipt)


def test_distribution_artifact_changes_receipt_and_data_vintage() -> None:
    paths = _paths()
    first = _receipt(paths)
    second = _receipt(paths, distributionArtifactHash="c" * 64)
    assert first.receiptId != second.receiptId
    firstRun = _run(bindParameterDrawSetReceipt(paths, first))
    secondRun = _run(bindParameterDrawSetReceipt(paths, second))
    assert firstRun.dataVintageHash != secondRun.dataVintageHash


def test_evidence_available_after_decision_cannot_enter_run() -> None:
    futurePaths = tuple(replace(path, knowledgeAsOf="20250102") for path in _paths())
    receipt = _receipt(futurePaths, availableAt="20250102", knowledgeAsOf="20250102")
    with pytest.raises(ParameterDrawError, match="newer than decision state"):
        _run(bindParameterDrawSetReceipt(futurePaths, receipt))


def test_undocumented_draws_stay_explicitly_conditional() -> None:
    run = _run(_paths())
    assert run.decisionStatus != "comparable"
    assert run.recommendation is None
    assert any("parameterMeasure:undocumented" in warning for warning in run.warnings)
