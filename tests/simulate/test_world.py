"""Kill tests for the world-evolution concept proof."""

from __future__ import annotations

from dataclasses import replace

import pytest

from dartlab.simulate.world import (
    ActionSpec,
    ConstraintSpec,
    LawCertificate,
    LawSpec,
    ObjectiveSpec,
    ScenarioPath,
    SimulationBlocked,
    SimulationSpecError,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    bindAdmittedPathContent,
    issueLawCertificate,
    simulateWorld,
)

_SYNTHETIC_CERTIFICATE = "a" * 64
_GLOBAL_MULTIPLIER = 1.0


def _certifyLaw(law: LawSpec, *, steps: int = 8, historyStatus: str = "asKnown") -> LawSpec:
    evidence = tuple(
        {"step": step, "metric": "syntheticOos", "estimate": 1.0, "threshold": 0.0, "operator": "gt"}
        for step in range(1, steps + 1)
    )
    certificate = issueLawCertificate(
        law,
        evidenceRows=evidence,
        knowledgeAsOf="20250101",
        historyStatus=historyStatus,
        frequency="step",
        rules="synthetic known data generating process",
    )
    return replace(law, certificate=certificate)


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
            fn=finance,
        ),
    )
    laws = tuple(
        _certifyLaw(law) if law.evidenceKind in {"measuredAssociation", "identifiedIntervention"} else law
        for law in laws
    )
    return WorldModel("synthetic-company", "1", variables, actions, laws)


def _state(cash: float = 8.0, debt: float = 2.0):
    return WorldState(
        {"capacity": 10.0, "cash": cash, "debt": debt},
        asOf="2025-Q4",
        knowledgeAsOf="20250101",
    )


def _path(pathId: str, demand: tuple[float, ...], rate: float = 0.05):
    path = ScenarioPath(
        pathId,
        tuple({"demand": value, "rate": rate} for value in demand),
        certificateId=_SYNTHETIC_CERTIFICATE,
        validationStatus="admitted",
        maxAdmittedStep=len(demand),
        knowledgeAsOf="20250101",
        historyStatus="asKnown",
    )
    return bindAdmittedPathContent((path,))[0]


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
    assert short.recommendation is None
    assert long.recommendation is None
    assert short.decisionStatus == "conditionalOnly"
    assert long.decisionStatus == "conditionalOnly"
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
    assert any("conditional assumptions" in warning for warning in run.warnings)


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
        _certifyLaw(replace(law, fn=issuedReader, certificate=None)) if law.lawId == "capacityRollForward" else law
        for law in model.laws
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
        knowledgeAsOf="20250101",
        historyStatus="asKnown",
    )
    path = bindAdmittedPathContent((path,))[0]
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


def testLawCertificateBindsContractParametersAndExecutable():
    first = _model()
    second = _model()
    firstLaw = next(law for law in first.laws if law.lawId == "capacityRollForward")
    secondLaw = next(law for law in second.laws if law.lawId == "capacityRollForward")
    assert firstLaw.certificate is not None
    assert secondLaw.certificate is not None
    assert firstLaw.certificate.certificateId == secondLaw.certificate.certificateId

    changed = replace(firstLaw, parameters={"capacityPerCapex": 3.0})
    laws = tuple(changed if law.lawId == changed.lawId else law for law in first.laws)
    with pytest.raises(SimulationSpecError, match="binding"):
        WorldModel(first.modelId, first.version, first.variables, first.actions, laws)


def testArbitraryLawCertificateDigestIsRejected():
    model = _model()
    law = next(law for law in model.laws if law.lawId == "capacityRollForward")
    assert law.certificate is not None
    fake = LawCertificate(
        certificateId="a" * 64,
        lawId=law.lawId,
        lawVersion=law.version,
        evidenceKind=law.evidenceKind,
        contractHash=law.certificate.contractHash,
        parameterHash=law.certificate.parameterHash,
        executableHash=law.certificate.executableHash,
        evidenceHash=law.certificate.evidenceHash,
        knowledgeAsOf=law.certificate.knowledgeAsOf,
        historyStatus=law.certificate.historyStatus,
        frequency=law.certificate.frequency,
        stepSpan=law.certificate.stepSpan,
        maxAdmittedStep=law.certificate.maxAdmittedStep,
        status=law.certificate.status,
        rules=law.certificate.rules,
    )
    laws = tuple(replace(law, certificate=fake) if item.lawId == law.lawId else item for item in model.laws)
    with pytest.raises(SimulationSpecError, match="digest"):
        WorldModel(model.modelId, model.version, model.variables, model.actions, laws)


def testLawCannotRunPastAdmittedHorizon():
    path = _path("too-long", (10.0,) * 9)
    with pytest.raises(SimulationSpecError, match="law exceeds admitted horizon"):
        _run(path, _strategy("noop", (0.0,) * 9))


def testRevisedHistoryCertificateCannotMakeAnActiveLaw():
    model = _model()
    law = next(law for law in model.laws if law.lawId == "capacityRollForward")
    retrospective = _certifyLaw(replace(law, certificate=None), historyStatus="revisedHistory")
    assert retrospective.certificate is not None
    assert retrospective.certificate.status == "retrospectiveOnly"
    laws = tuple(retrospective if item.lawId == law.lawId else item for item in model.laws)
    with pytest.raises(SimulationSpecError, match="active law needs admitted evidence"):
        WorldModel(model.modelId, model.version, model.variables, model.actions, laws)


def testLawCertificateEvaluatorDoesNotTrustCallerPassedClaim():
    model = _model()
    law = next(law for law in model.laws if law.lawId == "capacityRollForward")
    certificate = issueLawCertificate(
        replace(law, certificate=None),
        evidenceRows=(
            {
                "step": 1,
                "metric": "trustMe",
                "estimate": -999.0,
                "threshold": 999.0,
                "operator": "gt",
                "passed": True,
            },
        ),
        knowledgeAsOf="20250101",
        historyStatus="asKnown",
        frequency="step",
        rules="estimate must exceed threshold",
    )
    assert certificate.status == "rejected"
    assert certificate.maxAdmittedStep == 0


def testFutureLawCertificateCannotEnterPastInitialState():
    path = _path("base", (10.0,) * 4)
    state = WorldState({"capacity": 10.0, "cash": 8.0, "debt": 2.0}, asOf="20240101")
    with pytest.raises(SimulationSpecError, match="newer than initial state"):
        _run(path, _strategy("noop", (0.0,) * 4), state=state)


def testFiscalLabelCannotBypassInitialKnowledgeCutoff():
    path = _path("base", (10.0,) * 4)
    state = WorldState(
        {"capacity": 10.0, "cash": 8.0, "debt": 2.0},
        asOf="2024-Q4",
        knowledgeAsOf="20241231",
    )
    with pytest.raises(SimulationSpecError, match="newer than initial state"):
        _run(path, _strategy("noop", (0.0,) * 4), state=state)


def testReferencedMutableGlobalChangesCertificateBinding():
    global _GLOBAL_MULTIPLIER

    model = _model()
    original = next(law for law in model.laws if law.lawId == "capacityRollForward")

    def globalLaw(ctx):
        capex = 2.0 * _GLOBAL_MULTIPLIER
        return {"capex": capex, "capacity": ctx.prior["capacity"] + capex}

    law = _certifyLaw(replace(original, fn=globalLaw, certificate=None))
    laws = tuple(law if item.lawId == law.lawId else item for item in model.laws)
    certifiedModel = WorldModel(model.modelId, model.version, model.variables, model.actions, laws)
    try:
        _GLOBAL_MULTIPLIER = 2.0
        with pytest.raises(SimulationSpecError, match="binding"):
            _run(_path("base", (10.0,) * 4), _strategy("noop", (0.0,) * 4), model=certifiedModel)
    finally:
        _GLOBAL_MULTIPLIER = 1.0


def testAdmittedPathContentCannotBeChangedUnderSameCertificate():
    path = _path("base", (10.0,) * 4)
    tampered = replace(path, steps=({"demand": 999.0, "rate": 0.05},) * 4)
    with pytest.raises(SimulationSpecError, match="content binding mismatch"):
        _run(tampered, _strategy("noop", (0.0,) * 4))


def testLawCertificateCannotMoveAcrossTimeGrid():
    model = _model()
    with pytest.raises(SimulationSpecError, match="step contract mismatch"):
        WorldModel(
            model.modelId,
            model.version,
            model.variables,
            model.actions,
            model.laws,
            stepFrequency="year",
        )


def testPathParameterDrawIsFixedAcrossStepsAndSharedAcrossStrategies():
    def transition(ctx):
        loading = ctx.pathParameters.get("loading", 1.0)
        return {"value": ctx.prior["value"] + ctx.shocks["innovation"] * loading}

    model = WorldModel(
        "parameter-draw",
        "1",
        (
            VariableSpec("value", "index", "state"),
            VariableSpec("innovation", "indexChange", "shock"),
        ),
        (),
        (
            LawSpec(
                "transition",
                outputs=("value",),
                priorInputs=("value",),
                shockInputs=("innovation",),
                pathParameterInputs=("loading",),
                pathParameterUnits={"loading": "outputPerInnovation"},
                parameters={"loading": 1.0},
                fn=transition,
            ),
        ),
    )
    paths = (
        ScenarioPath("low", ({"innovation": 1.0},) * 2, parameterDraws={"loading": 0.5}),
        ScenarioPath("high", ({"innovation": 1.0},) * 2, parameterDraws={"loading": 2.0}),
    )
    strategies = (StrategySpec("a", ({},) * 2), StrategySpec("b", ({},) * 2))
    run = simulateWorld(model, WorldState({"value": 0.0}), paths, strategies)
    low = [trace for trace in run.traces if trace.pathId == "low"]
    high = [trace for trace in run.traces if trace.pathId == "high"]
    assert {trace.steps[-1].after["value"] for trace in low} == {1.0}
    assert {trace.steps[-1].after["value"] for trace in high} == {4.0}
    assert all(step.laws[0].pathParameters == {"loading": 0.5} for trace in low for step in trace.steps)


def testUndeclaredPathParameterIsRejected():
    path = replace(_path("base", (10.0,) * 4), parameterDraws={"unknown": 1.0})
    with pytest.raises(SimulationSpecError, match="unknown path parameters"):
        _run(path, _strategy("noop", (0.0,) * 4))


def testClosedLoopPolicyReactsToObservedStateWithoutSeeingCurrentShock():
    seenKeys: list[set[str]] = []

    def policy(ctx):
        seenKeys.append(set(ctx.prior))
        priorRevenue = ctx.prior.get("revenue", 20.0)
        return {"capexCut": 1.0 if priorRevenue < 10.0 else 0.0}

    paths = (
        ScenarioPath("calm", ({"demand": 4.0, "rate": 0.05},) * 3),
        ScenarioPath("surge", ({"demand": 10.0, "rate": 0.05},) * 3),
    )
    strategy = StrategySpec(
        "adaptive",
        ({},) * 3,
        policyVersion="1",
        policyProvenance="test:revenue-threshold",
        policyFn=policy,
    )
    run = simulateWorld(_model(), _state(), paths, (strategy,))
    calm = next(trace for trace in run.traces if trace.pathId == "calm")
    surge = next(trace for trace in run.traces if trace.pathId == "surge")
    assert calm.steps[0].issuedActions == surge.steps[0].issuedActions == {"capexCut": 0.0}
    assert calm.steps[1].issuedActions == {"capexCut": 1.0}
    assert surge.steps[1].issuedActions == {"capexCut": 0.0}
    assert all("demand" not in keys and "rate" not in keys for keys in seenKeys)
    assert calm.policyVersion == "1"
    assert calm.policyProvenance == "test:revenue-threshold"


def testClosedLoopPolicyExecutableChangesExecutableHash():
    path = ScenarioPath("path", ({"demand": 10.0, "rate": 0.05},) * 2)

    def preserve(_ctx):
        return {"capexCut": 0.0}

    def cut(_ctx):
        return {"capexCut": 1.0}

    common = {
        "strategyId": "adaptive",
        "actionsByStep": ({},) * 2,
        "policyVersion": "1",
        "policyProvenance": "test:hash",
    }
    first = simulateWorld(_model(), _state(), (path,), (StrategySpec(**common, policyFn=preserve),))
    second = simulateWorld(_model(), _state(), (path,), (StrategySpec(**common, policyFn=cut),))
    assert first.executableHash != second.executableHash
    assert first.resultHash != second.resultHash


def testCompactTraceRetentionKeepsExactAverageAndWholeTraceRoot():
    paths = tuple(
        ScenarioPath(
            f"path-{index:03d}",
            ({"demand": float(5 + index % 7), "rate": 0.05},) * 4,
        )
        for index in range(50)
    )
    strategies = (_strategy("noop", (0.0,) * 4), _strategy("cut", (0.5,) * 4))
    objectives = (ObjectiveSpec("netCash", risk="average"),)
    full = simulateWorld(_model(), _state(), paths, strategies, objectives=objectives)
    compact = simulateWorld(
        _model(),
        _state(),
        paths,
        strategies,
        objectives=objectives,
        traceLimit=3,
    )
    assert compact.traceCount == full.traceCount == 100
    assert compact.retainedTraceCount == len(compact.traces) == 3
    assert compact.traceRoot == full.traceRoot
    for compactEvaluation, fullEvaluation in zip(compact.evaluations, full.evaluations, strict=True):
        assert compactEvaluation.objectiveScores == pytest.approx(fullEvaluation.objectiveScores)
    assert all(item.pathValues == () for item in compact.evaluations)


def testCompactTraceRetentionSpillsExactWeightedCvar():
    paths = tuple(
        ScenarioPath(
            f"path-{index}",
            ({"demand": float(5 + index), "rate": 0.05},) * 2,
            weight=float(index + 1),
            weightKind="subjective",
        )
        for index in range(10)
    )
    strategy = (_strategy("noop", (0.0,) * 2),)
    objectives = (ObjectiveSpec("netCash", risk="cvar", tailFraction=0.2),)
    full = simulateWorld(_model(), _state(), paths, strategy, objectives=objectives)
    compact = simulateWorld(
        _model(),
        _state(),
        paths,
        strategy,
        objectives=objectives,
        traceLimit=0,
    )
    assert compact.evaluations[0].objectiveScores == pytest.approx(full.evaluations[0].objectiveScores)
    assert compact.traceRoot == full.traceRoot
    assert compact.traces == ()
