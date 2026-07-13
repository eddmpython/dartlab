"""Kill tests for the world-evolution concept proof."""

from __future__ import annotations

from dataclasses import replace

import pytest

from dartlab.simulate.world import (
    ActionSpec,
    ConstraintSpec,
    LawSpec,
    ObjectiveSpec,
    ScenarioPath,
    SimulationBlocked,
    SimulationSpecError,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    simulateWorld,
)

_SYNTHETIC_CERTIFICATE = "a" * 64


def _model(*, actionEvidence: str = "identifiedIntervention", lawEvidence: str = "identifiedIntervention"):
    variables = (
        VariableSpec("demand", "units", "shock", lower=0),
        VariableSpec("rate", "ratio", "shock", lower=0),
        VariableSpec("capacity", "units", "state", lower=0),
        VariableSpec("cash", "currency", "state", lower=0),
        VariableSpec("debt", "currency", "state", lower=0),
        VariableSpec("capex", "currency", "state", lower=0),
        VariableSpec("revenue", "currency", "state", lower=0),
        VariableSpec("operatingProfit", "currency", "state"),
        VariableSpec("interest", "currency", "state", lower=0),
        VariableSpec("netCash", "currency", "metric"),
    )
    actions = (
        ActionSpec(
            "capexCut",
            "ratio",
            0.0,
            1.0,
            leadSteps=1,
            costPerUnit=0.25,
            effectEvidence=actionEvidence,
            provenance="synthetic-randomized-policy",
            certificateId=_SYNTHETIC_CERTIFICATE if actionEvidence == "identifiedIntervention" else "",
        ),
    )

    def capacity(ctx):
        capex = 2.0 * (1.0 - ctx.actions["capexCut"])
        return {"capex": capex, "capacity": max(0.0, ctx.prior["capacity"] + capex - 1.0)}

    def revenue(ctx):
        return {"revenue": min(ctx.shocks["demand"], ctx.current["capacity"]) * 2.0}

    def profit(ctx):
        return {"operatingProfit": ctx.current["revenue"] * 0.35 - 1.0}

    def finance(ctx):
        interest = ctx.prior["debt"] * ctx.shocks["rate"]
        beforeFunding = (
            ctx.prior["cash"] + ctx.current["operatingProfit"] - interest - ctx.current["capex"] - ctx.actionCost
        )
        borrowing = max(0.0, -beforeFunding)
        cash = max(0.0, beforeFunding)
        debt = ctx.prior["debt"] + borrowing
        return {"interest": interest, "cash": cash, "debt": debt, "netCash": cash - debt}

    laws = (
        LawSpec(
            "capacityRollForward",
            outputs=("capacity", "capex"),
            priorInputs=("capacity",),
            actionInputs=("capexCut",),
            evidenceKind=lawEvidence,
            provenance="synthetic-known-dgp:capacity",
            certificateId=_SYNTHETIC_CERTIFICATE if lawEvidence == "identifiedIntervention" else "",
            fn=capacity,
        ),
        LawSpec(
            "revenueIdentity",
            outputs=("revenue",),
            currentInputs=("capacity",),
            shockInputs=("demand",),
            evidenceKind="accountingIdentity",
            provenance="synthetic-known-dgp:units-times-price",
            fn=revenue,
        ),
        LawSpec(
            "profitIdentity",
            outputs=("operatingProfit",),
            currentInputs=("revenue",),
            evidenceKind="accountingIdentity",
            provenance="synthetic-known-dgp:profit",
            fn=profit,
        ),
        LawSpec(
            "fundingPolicy",
            outputs=("interest", "cash", "debt", "netCash"),
            priorInputs=("cash", "debt"),
            currentInputs=("operatingProfit", "capex"),
            shockInputs=("rate",),
            usesActionCost=True,
            evidenceKind="identifiedIntervention",
            provenance="synthetic-known-dgp:credit-line",
            certificateId=_SYNTHETIC_CERTIFICATE,
            fn=finance,
        ),
    )
    return WorldModel("synthetic-company", "1", variables, actions, laws)


def _state(cash: float = 8.0, debt: float = 2.0):
    return WorldState({"capacity": 10.0, "cash": cash, "debt": debt}, asOf="2025-Q4")


def _path(pathId: str, demand: tuple[float, ...], rate: float = 0.05):
    return ScenarioPath(
        pathId,
        tuple({"demand": value, "rate": rate} for value in demand),
        certificateId=_SYNTHETIC_CERTIFICATE,
        validationStatus="admitted",
        maxAdmittedStep=len(demand),
    )


def _strategy(strategyId: str, cuts: tuple[float, ...]):
    return StrategySpec(
        strategyId,
        tuple({"capexCut": value} for value in cuts),
        isBaseline=strategyId.startswith("noop"),
    )


def _run(path, *strategies, model=None, state=None):
    return simulateWorld(
        model or _model(),
        state or _state(),
        (path,),
        tuple(strategies),
        constraints=(ConstraintSpec("debt", "le", 30.0),),
        objectives=(ObjectiveSpec("netCash", risk="worst"),),
    )


def _evaluation(run, strategyId):
    return next(item for item in run.evaluations if item.strategyId == strategyId)


def _trace(run, strategyId):
    return next(item for item in run.traces if item.strategyId == strategyId)


def testMultiStepStateUsesPriorStateAndDebtInterestFeedbackPersists():
    path = _path("stress", (2.0, 2.0, 2.0, 2.0), rate=0.20)
    lowDebt = _run(path, _strategy("noop", (0.0,) * 4), state=_state(cash=1.0, debt=1.0))
    highDebt = _run(path, _strategy("noop", (0.0,) * 4), state=_state(cash=1.0, debt=10.0))
    low = _trace(lowDebt, "noop")
    high = _trace(highDebt, "noop")
    assert high.steps[1].after["interest"] > low.steps[1].after["interest"]
    assert high.steps[-1].after["debt"] > high.steps[0].after["debt"]
    assert high.steps[-1].after["netCash"] < low.steps[-1].after["netCash"]


def testNoOpAndStrategyNameDoNotChangePath():
    path = _path("base", (10.0, 10.0, 10.0, 10.0))
    run = _run(path, _strategy("noop-a", (0.0,) * 4), _strategy("renamed", (0.0,) * 4))
    a = _trace(run, "noop-a")
    b = _trace(run, "renamed")
    assert [step.after for step in a.steps] == [step.after for step in b.steps]
    assert _evaluation(run, "noop-a").objectiveScores == _evaluation(run, "renamed").objectiveScores
    assert run.recommendation is None


def testActionHasLeadTimeCostAndChangesOnlyThroughDeclaredLaw():
    path = _path("base", (10.0, 10.0, 10.0, 10.0))
    run = _run(path, _strategy("noop", (0.0,) * 4), _strategy("cut", (1.0,) * 4))
    noop = _trace(run, "noop")
    cut = _trace(run, "cut")
    assert cut.steps[0].effectiveActions["capexCut"] == 0.0
    assert cut.steps[0].actionCost == 0.25
    assert cut.steps[0].after["capacity"] == noop.steps[0].after["capacity"]
    assert cut.steps[1].after["capacity"] < noop.steps[1].after["capacity"]
    capacityLaw = next(item for item in cut.steps[1].laws if item.lawId == "capacityRollForward")
    assert capacityLaw.inputs["action.capexCut"] == 1.0


def testStrategyRankReversesWhenShockDurationChanges():
    strategies = (_strategy("noop", (0.0,) * 4), _strategy("cut", (1.0,) * 4))
    short = _run(_path("short", (5.0, 5.0, 20.0, 20.0)), *strategies)
    long = _run(_path("long", (5.0, 5.0, 5.0, 5.0)), *strategies)
    assert short.recommendation == "noop"
    assert long.recommendation == "cut"
    assert _evaluation(short, "noop").objectiveScores[0] > _evaluation(short, "cut").objectiveScores[0]
    assert _evaluation(long, "cut").objectiveScores[0] > _evaluation(long, "noop").objectiveScores[0]


def testShockMagnitudeSurvivesDecisionLayer():
    strategy = _strategy("noop", (0.0,) * 4)
    mild = _run(_path("mild", (8.0,) * 4), strategy)
    severe = _run(_path("severe", (2.0,) * 4), strategy)
    assert _trace(mild, "noop").steps[-1].after["netCash"] > _trace(severe, "noop").steps[-1].after["netCash"]


def testMissingShockBlocksInsteadOfBecomingZero():
    bad = ScenarioPath("bad", ({"rate": 0.05},) * 4)
    with pytest.raises(SimulationBlocked, match="missing shocks"):
        _run(bad, _strategy("noop", (0.0,) * 4))


def testUnvalidatedInterventionCannotProduceRecommendation():
    model = _model(actionEvidence="explicitAssumption", lawEvidence="explicitAssumption")
    run = _run(
        _path("long", (5.0,) * 4),
        _strategy("noop", (0.0,) * 4),
        _strategy("cut", (1.0,) * 4),
        model=model,
    )
    assert run.decisionStatus == "conditionalOnly"
    assert run.recommendation is None
    assert "conditional assumptions" in run.warnings[-1]


def testUnvalidatedWorldLawCannotProduceRecommendation():
    model = _model()
    laws = tuple(
        replace(law, evidenceKind="explicitAssumption") if law.lawId == "profitIdentity" else law for law in model.laws
    )
    assumed = WorldModel(model.modelId, model.version, model.variables, model.actions, laws)
    run = _run(
        _path("long", (5.0,) * 4),
        _strategy("noop", (0.0,) * 4),
        _strategy("cut", (1.0,) * 4),
        model=assumed,
    )
    assert run.decisionStatus == "conditionalOnly"
    assert run.recommendation is None


def testSameInputsHaveSameHashAndCommonWorldPaths():
    path = _path("base", (10.0, 7.0, 9.0, 11.0))
    strategies = (_strategy("noop", (0.0,) * 4), _strategy("cut", (1.0,) * 4))
    first = _run(path, *strategies)
    second = _run(path, *strategies)
    assert first.runHash == second.runHash
    assert _trace(first, "noop").steps[2].shocks == _trace(first, "cut").steps[2].shocks
    assert first.weightLabel == "scenarioCoverage"


def testPartialLawCapsRunQuality():
    model = _model()
    laws = tuple(replace(law, status="partial") if law.lawId == "capacityRollForward" else law for law in model.laws)
    partial = WorldModel(model.modelId, model.version, model.variables, model.actions, laws)
    run = _run(_path("base", (10.0,) * 4), _strategy("noop", (0.0,) * 4), model=partial)
    assert run.status == "partial"
    assert run.decisionStatus == "conditionalOnly"
    assert run.recommendation is None


def testLawContextExposesOnlyDeclaredInputsAndNoIssuedActionBackdoor():
    model = _model()
    hiddenShockLaws = tuple(
        replace(law, shockInputs=()) if law.lawId == "revenueIdentity" else law for law in model.laws
    )
    hiddenShock = WorldModel(model.modelId, model.version, model.variables, model.actions, hiddenShockLaws)
    with pytest.raises(KeyError, match="demand"):
        _run(_path("base", (10.0,) * 4), _strategy("noop", (0.0,) * 4), model=hiddenShock)

    def issuedReader(ctx):
        return {"capex": 2.0, "capacity": ctx.prior["capacity"] + ctx.issuedActions["capexCut"]}

    leadBypassLaws = tuple(
        replace(law, fn=issuedReader) if law.lawId == "capacityRollForward" else law for law in model.laws
    )
    leadBypass = WorldModel(model.modelId, model.version, model.variables, model.actions, leadBypassLaws)
    with pytest.raises(KeyError, match="capexCut"):
        _run(_path("base", (10.0,) * 4), _strategy("noop", (1.0,) * 4), model=leadBypass)


def testExecutableParametersAndResultHaveIndependentDigests():
    model = _model()

    def changedProfit(ctx):
        return {"operatingProfit": ctx.current["revenue"] * 0.35 - 2.0}

    changedLaws = tuple(
        replace(law, fn=changedProfit, parameters={"fixedCost": 2.0}) if law.lawId == "profitIdentity" else law
        for law in model.laws
    )
    changed = WorldModel(model.modelId, model.version, model.variables, model.actions, changedLaws)
    path = _path("base", (10.0,) * 4)
    strategy = _strategy("noop", (0.0,) * 4)
    first = _run(path, strategy, model=model)
    second = _run(path, strategy, model=changed)
    assert first.runHash != second.runHash
    assert first.executableHash != second.executableHash
    assert first.parameterHash != second.parameterHash
    assert first.resultHash != second.resultHash
    assert first.traceRoot != second.traceRoot


def testInputAndTraceMappingsAreDeeplyImmutable():
    step = {"demand": 10.0, "rate": 0.05}
    actions = {"capexCut": 0.0}
    path = ScenarioPath(
        "base",
        (step,) * 4,
        certificateId=_SYNTHETIC_CERTIFICATE,
        validationStatus="admitted",
        maxAdmittedStep=4,
    )
    strategy = StrategySpec("noop", (actions,) * 4, isBaseline=True)
    step["demand"] = 999.0
    actions["capexCut"] = 1.0
    run = _run(path, strategy)
    assert run.traces[0].steps[0].shocks["demand"] == 10.0
    assert run.traces[0].steps[0].issuedActions["capexCut"] == 0.0
    with pytest.raises(TypeError):
        run.traces[0].steps[0].after["cash"] = 999.0


def testCalibratedMeasureNeedsFiniteNormalizedCertifiedPaths():
    path = ScenarioPath("bad", ({"demand": 10.0, "rate": 0.05},) * 4, weight=1.0, weightKind="calibrated")
    with pytest.raises(SimulationSpecError, match="certificate"):
        _run(path, _strategy("noop", (0.0,) * 4))
    nanPath = replace(
        _path("nan", (10.0,) * 4),
        weight=float("nan"),
        weightKind="calibrated",
    )
    with pytest.raises(SimulationSpecError, match="finite"):
        _run(nanPath, _strategy("noop", (0.0,) * 4))


def testPathTimeUnitMustMatchWorldModel():
    weekly = replace(_path("weekly", (10.0,) * 4), frequency="week")
    with pytest.raises(SimulationSpecError, match="step contract mismatch"):
        _run(weekly, _strategy("noop", (0.0,) * 4))
