from __future__ import annotations

import pytest

from dartlab.simulate.operatingWorld import (
    OperatingPrimitive,
    buildOperatingPath,
    buildOperatingStrategy,
    operatingInputsFromCompiledState,
    operatingInputsFromPrimitives,
    operatingInputsFromStatePrimitives,
    runOperatingStrategies,
)
from dartlab.simulate.stateCompiler import CompiledPointInTimeState
from dartlab.simulate.stateSupport import StatePrimitive


def _primitive(variableId: str, value: float, unit: str, sourceRef: str, evidenceRole: str = "explicitAssumption"):
    return OperatingPrimitive(variableId, value, unit, evidenceRole, sourceRef)


def _rows():
    return (
        _primitive("price", 10.0, "currencyPerUnit", "assumption://price"),
        _primitive("demandVolume", 100.0, "units", "assumption://volume"),
        _primitive("unitCost", 6.0, "currencyPerUnit", "assumption://unit-cost"),
        _primitive("fixedCost", 100.0, "currency", "assumption://fixed-cost"),
        _primitive("capacityUnits", 80.0, "units", "assumption://capacity"),
        _primitive("cash", 100.0, "currency", "filing://cash", "observed"),
        _primitive("debt", 20.0, "currency", "filing://debt", "observed"),
    )


def _statePrimitive(
    variableId: str,
    value: float,
    unit: str,
    evidenceRole: str = "observed",
    role: str = "state",
) -> StatePrimitive:
    return StatePrimitive(
        variableId=variableId,
        unit=unit,
        role=role,
        value=value,
        frequency="quarter",
        timing="stock",
        transformId="level-v1",
        evidenceRole=evidenceRole,
    )


def _stateRows():
    return (
        _statePrimitive("operating.price", 10.0, "USDPerUnit", "explicitAssumption"),
        _statePrimitive("operating.demandVolume", 100.0, "units", "explicitAssumption"),
        _statePrimitive("operating.unitCost", 6.0, "USDPerUnit", "explicitAssumption"),
        _statePrimitive("operating.fixedCost", 100.0, "USD", "explicitAssumption"),
        _statePrimitive("operating.capacityUnits", 80.0, "units", "explicitAssumption"),
        _statePrimitive("financial.cash", 100.0, "USD", "observed"),
        _statePrimitive("financial.debt", 20.0, "USD", "deterministicDerived"),
    )


def _compiledState(
    primitives: tuple[StatePrimitive, ...],
    *,
    limitations: tuple[str, ...] = ("unsignedProviderBatches",),
    manifestHash: str = "manifest-1",
    stateCompilationContractHash: str = "compile-1",
) -> CompiledPointInTimeState:
    return CompiledPointInTimeState(
        stateId="state-1",
        manifestHash=manifestHash,
        registryHash="registry-1",
        stateContractHash="contract-1",
        stateCompilationContractHash=stateCompilationContractHash,
        entityId="AAPL",
        market="US",
        decisionAsOf="20250201",
        knowledgeAsOf="20250130",
        statePrimitives=primitives,
        selectedObservationIds=("obs-cash", "obs-debt"),
        providerBatchIds=("batch-1",),
        providerBatchReceiptIds=("receipt-1",),
        historyStatus="conditional",
        admissionStatus="documented",
        aggregateRevisionPolicy="latestRetained",
        aggregateCoverage="periodOnly",
        limitations=limitations,
        manifestArtifact=b"{}",
    )


def _inputs(**kwargs):
    params = {
        "asOf": "2025Q4",
        "priceElasticity": 1.0,
        "capacityUnitsPerCurrency": 1.0,
        "taxRate": 0.0,
    }
    params.update(kwargs)
    return operatingInputsFromPrimitives(_rows(), **params)


def _path(pathId="base", horizon=2, **kwargs):
    values = {
        "marketPriceChange": (0.0,) * horizon,
        "demandChange": (0.0,) * horizon,
        "unitCostChange": (0.0,) * horizon,
        "fixedCostChange": (0.0,) * horizon,
        "capacityChange": (0.0,) * horizon,
        "debtRate": (0.05,) * horizon,
        "refs": ("assumption://path",),
    }
    values.update(kwargs)
    return buildOperatingPath(pathId, **values)


def _strategy(strategyId, horizon=2, **kwargs):
    values = {
        "priceChange": (0.0,) * horizon,
        "capacityInvestment": (0.0,) * horizon,
        "borrow": (0.0,) * horizon,
        "repay": (0.0,) * horizon,
        "refs": (f"assumption://strategy/{strategyId}",),
    }
    values.update(kwargs)
    return buildOperatingStrategy(strategyId, **values)


def _run(inputs, path, *strategies):
    return runOperatingStrategies(
        inputs,
        (path,),
        tuple(strategies),
        debtLimit=500.0,
        maxFinancing=300.0,
        maxInvestment=300.0,
    )


def _trace(run, strategyId):
    return next(item for item in run.traces if item.strategyId == strategyId)


def testOperatingInputsNeedSourceOrExplicitAssumptionBoundary():
    inputs = _inputs()
    assert inputs.state["price"] == 10.0
    assert "assumption://capacity" in inputs.refs
    assert "operatingAssumption:price" in inputs.warnings

    missingRef = list(_rows())
    missingRef[0] = _primitive("price", 10.0, "currencyPerUnit", "")
    with pytest.raises(ValueError, match="source ref"):
        operatingInputsFromPrimitives(
            missingRef,
            asOf="2025Q4",
            priceElasticity=1.0,
            capacityUnitsPerCurrency=1.0,
        )

    wrongUnit = list(_rows())
    wrongUnit[1] = _primitive("demandVolume", 100.0, "currency", "assumption://volume")
    with pytest.raises(ValueError, match="unit drift"):
        operatingInputsFromPrimitives(
            wrongUnit,
            asOf="2025Q4",
            priceElasticity=1.0,
            capacityUnitsPerCurrency=1.0,
        )


def testOperatingInputsCanBindTypedPitStateWithoutLosingLineage():
    inputs = operatingInputsFromCompiledState(
        _compiledState(_stateRows()),
        priceElasticity=1.0,
        capacityUnitsPerCurrency=1.0,
    )
    assert inputs.state["price"] == 10.0
    assert inputs.state["cash"] == 100.0
    assert "compiledState:state-1" in inputs.refs
    assert "providerBatchReceipt:receipt-1" in inputs.refs
    assert "observation:obs-cash" in inputs.refs
    assert "compiledStateLimitation:unsignedProviderBatches" in inputs.warnings
    assert "compiledStateHistory:conditional" in inputs.warnings
    assert "operatingAssumption:capacityUnits" in inputs.warnings


def testOperatingRunPreservesCompiledStateTemporalLineage():
    manifestHash = "a" * 64
    contractHash = "b" * 64
    inputs = operatingInputsFromCompiledState(
        _compiledState(
            _stateRows(),
            limitations=(),
            manifestHash=manifestHash,
            stateCompilationContractHash=contractHash,
        ),
        priceElasticity=1.0,
        capacityUnitsPerCurrency=1.0,
    )
    assert inputs.knowledgeAsOf == "20250130"
    assert inputs.decisionAsOf == "20250201"
    assert inputs.stateManifestHash == manifestHash
    assert inputs.stateCompilationContractHash == contractHash
    assert inputs.stateVintage is not None
    assert inputs.stateVintage.contractHash == contractHash

    run = _run(inputs, _path(horizon=1), _strategy("hold", horizon=1))
    assert run.decisionAsOf == "20250201"
    assert run.dataVintageHash


def testOperatingInputsFromPitStateFailClosedOnMeaningDrift():
    missing = _stateRows()[:-1]
    with pytest.raises(ValueError, match="operating inputs are missing"):
        operatingInputsFromStatePrimitives(
            missing,
            asOf="20250201",
            priceElasticity=1.0,
            capacityUnitsPerCurrency=1.0,
        )

    wrongUnit = list(_stateRows())
    wrongUnit[0] = _statePrimitive("operating.price", 10.0, "USD", "explicitAssumption")
    with pytest.raises(ValueError, match="unit drift"):
        operatingInputsFromStatePrimitives(
            wrongUnit,
            asOf="20250201",
            priceElasticity=1.0,
            capacityUnitsPerCurrency=1.0,
        )

    wrongRole = list(_stateRows())
    wrongRole[1] = _statePrimitive("operating.demandVolume", 100.0, "units", "explicitAssumption", "observedFeature")
    with pytest.raises(ValueError, match="role drift"):
        operatingInputsFromStatePrimitives(
            wrongRole,
            asOf="20250201",
            priceElasticity=1.0,
            capacityUnitsPerCurrency=1.0,
        )


def testOperatingInputsRejectMixedPitCurrencyFamilies():
    mixed = list(_stateRows())
    mixed[5] = _statePrimitive("financial.cash", 100.0, "KRW")
    with pytest.raises(ValueError, match="mixes monetary units"):
        operatingInputsFromStatePrimitives(
            mixed,
            asOf="20250201",
            priceElasticity=1.0,
            capacityUnitsPerCurrency=1.0,
        )


def testOperatingWorldTurnsPriceVolumeCostAndCapacityIntoPnl():
    run = _run(_inputs(), _path(horizon=1), _strategy("hold", horizon=1))
    step = run.traces[0].steps[0]
    assert step.after["soldVolume"] == 80.0
    assert step.after["unmetVolume"] == 20.0
    assert step.after["revenue"] == 800.0
    assert step.after["variableCost"] == 480.0
    assert step.after["operatingProfit"] == 220.0
    assert step.after["capacityBound"] == 1.0
    assert run.decisionStatus == "conditionalOnly"
    assert run.recommendation is None


def testCapacityShockMovesAvailableCapacityWithoutPretendingItIsStrategy():
    run = _run(
        _inputs(),
        _path("outage", horizon=1, demandChange=(0.5,), capacityChange=(-0.5,)),
        _strategy("hold", horizon=1),
    )
    step = run.traces[0].steps[0]
    assert step.shocks["capacityChange"] == pytest.approx(-0.5)
    assert step.after["availableCapacityUnits"] == pytest.approx(40.0)
    assert step.after["soldVolume"] == pytest.approx(40.0)
    assert step.after["unmetVolume"] == pytest.approx(110.0)
    assert step.after["capacityBound"] == pytest.approx(1.0)


def testCapacityInvestmentStrategyChangesFutureSalesAndCash():
    demandPath = _path(
        "surge",
        demandChange=(0.5, 0.0),
        marketPriceChange=(0.0, 0.0),
        unitCostChange=(0.0, 0.0),
        fixedCostChange=(0.0, 0.0),
        capacityChange=(0.0, 0.0),
        debtRate=(0.05, 0.05),
    )
    run = _run(
        _inputs(),
        demandPath,
        _strategy("hold", isBaseline=True),
        _strategy("invest", capacityInvestment=(70.0, 0.0)),
    )
    hold = _trace(run, "hold")
    invest = _trace(run, "invest")
    assert invest.steps[0].after["capacityUnits"] == pytest.approx(hold.steps[0].after["capacityUnits"])
    assert invest.steps[0].after["soldVolume"] == pytest.approx(hold.steps[0].after["soldVolume"])
    assert invest.steps[0].after["operatingProfit"] == pytest.approx(hold.steps[0].after["operatingProfit"])
    assert invest.steps[0].after["cashChange"] == pytest.approx(invest.steps[0].after["netIncome"] - 70.0)
    assert invest.steps[1].after["capacityUnits"] > hold.steps[1].after["capacityUnits"]
    assert invest.steps[1].after["soldVolume"] > hold.steps[1].after["soldVolume"]
    assert invest.steps[1].after["operatingProfit"] > hold.steps[1].after["operatingProfit"]
    assert set(run.paretoStrategies) <= {"hold", "invest"}


def testOperatingPolicyAdmissionRequiresScalarObjectiveIndex():
    inputs = _inputs()
    path = _path("base")
    with pytest.raises(ValueError, match="policyObjectiveIndex"):
        runOperatingStrategies(
            inputs,
            (path,),
            (_strategy("hold", isBaseline=True), _strategy("invest")),
            debtLimit=500.0,
            maxFinancing=300.0,
            maxInvestment=300.0,
            policyAdmissionEvidence=object(),
            policyObjectiveIndex=3,
        )


def testPricePolicyMovesVolumeAndProfitThroughElasticity():
    rows = list(_rows())
    rows[4] = _primitive("capacityUnits", 200.0, "units", "assumption://capacity")
    inputs = operatingInputsFromPrimitives(
        rows,
        asOf="2025Q4",
        priceElasticity=1.0,
        capacityUnitsPerCurrency=1.0,
        taxRate=0.0,
    )
    run = _run(
        inputs,
        _path(horizon=1),
        _strategy("hold", horizon=1, isBaseline=True),
        _strategy("raise-price", horizon=1, priceChange=(0.10,)),
    )
    hold = _trace(run, "hold").steps[0].after
    raised = _trace(run, "raise-price").steps[0].after
    assert raised["price"] == pytest.approx(11.0)
    assert raised["soldVolume"] < hold["soldVolume"]
    assert raised["operatingProfit"] > hold["operatingProfit"]


def testPathAndStrategyRefsAreMandatory():
    with pytest.raises(ValueError, match="operating path"):
        buildOperatingPath(
            "bad",
            marketPriceChange=(0.0,),
            demandChange=(0.0,),
            unitCostChange=(0.0,),
            fixedCostChange=(0.0,),
            capacityChange=(0.0,),
            debtRate=(0.05,),
            refs=(),
        )
    with pytest.raises(ValueError, match="operating strategy"):
        buildOperatingStrategy(
            "bad",
            priceChange=(0.0,),
            capacityInvestment=(0.0,),
            borrow=(0.0,),
            repay=(0.0,),
            refs=(),
        )


def testSolvencyAndRunwayBreachRemainVisibleInsteadOfBlocking():
    stress = _path(
        "stress",
        horizon=1,
        marketPriceChange=(0.0,),
        demandChange=(-0.9,),
        unitCostChange=(0.5,),
        fixedCostChange=(1.0,),
        debtRate=(0.2,),
    )
    run = _run(_inputs(), stress, _strategy("fund-none", horizon=1, capacityInvestment=(150.0,)))
    step = run.traces[0].steps[0]
    assert step.after["cash"] < 0
    assert step.after["cashRunwaySteps"] == 0.0
    assert "cash:ge:0.0" in step.breaches
