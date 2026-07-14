from __future__ import annotations

import gc
from dataclasses import replace

import pytest

from dartlab.simulate.financialWorld import (
    FinancialWorldInputs,
    OperatingDriverInputs,
    buildFinancialPath,
    buildFinancialStrategy,
    buildOperatingFinancialPath,
    financialInputsFromSnapshot,
    runFinancialStrategies,
)
from dartlab.simulate.world import SimulationBlocked, SimulationSpecError


def _series():
    q = 8
    return {
        "IS": {
            "sales": [25.0] * q,
            "operating_profit": [3.75] * q,
            "profit_before_tax": [3.0] * q,
            "income_tax_expense": [0.6] * q,
            "finance_costs": [0.75] * q,
            "gross_profit": [10.0] * q,
            "selling_and_administrative_expenses": [5.0] * q,
            "net_profit": [2.4] * q,
        },
        "BS": {
            "cash_and_cash_equivalents": [20.0] * q,
            "shortterm_borrowings": [10.0] * q,
            "longterm_borrowings": [20.0] * q,
            "debentures": [0.0] * q,
            "trade_receivables": [10.0] * q,
            "inventories": [10.0] * q,
            "trade_payables": [10.0] * q,
            "tangible_assets": [50.0] * q,
            "total_assets": [120.0] * q,
            "total_liabilities": [70.0] * q,
            "total_stockholders_equity": [50.0] * q,
            "current_assets": [50.0] * q,
            "current_liabilities": [30.0] * q,
        },
        "CF": {
            "depreciation": [1.25] * q,
            "purchase_of_property_plant_and_equipment": [2.0] * q,
            "dividends_paid": [0.5] * q,
        },
    }


def _inputs():
    snapshot = {
        "series": _series(),
        "baseRevenue": 100.0,
        "baseMargin": 15.0,
        "asOf": "2025-Q4",
    }
    return financialInputsFromSnapshot(snapshot, capacityHeadroom=0.20)


def _path(pathId="base", growth=(0.0, 0.0, 0.0, 0.0)):
    return buildFinancialPath(
        pathId,
        demandGrowth=growth,
        marginChange=(0.0,) * len(growth),
        debtRate=(0.05,) * len(growth),
    )


def _strategy(strategyId, capex, inventory=0.10, borrow=0.0, repay=0.0):
    horizon = len(capex)
    return buildFinancialStrategy(
        strategyId,
        capexRatio=capex,
        inventoryRatio=(inventory,) * horizon,
        borrow=(borrow,) * horizon,
        repay=(repay,) * horizon,
    )


def testSnapshotCompilesActualBalanceSheetStateWithoutZeroFill():
    inputs = _inputs()
    state = inputs.state
    assert state.revenue == 100.0
    assert state.latentDemandRevenue == 100.0
    assert state.debt == 30.0
    identity = state.cash + state.receivables + state.inventories + state.ppe + state.otherNetAssets
    assert identity - state.payables - state.debt == pytest.approx(state.equity)
    broken = {"series": _series(), "baseRevenue": 100.0, "baseMargin": 15.0}
    del broken["series"]["BS"]["inventories"]
    with pytest.raises(SimulationBlocked, match="inventories"):
        financialInputsFromSnapshot(broken, capacityHeadroom=0.20)

    partialDebt = {"series": _series(), "baseRevenue": 100.0, "baseMargin": 15.0}
    del partialDebt["series"]["BS"]["debentures"]
    with pytest.raises(SimulationBlocked, match="incomplete debt"):
        financialInputsFromSnapshot(partialDebt, capacityHeadroom=0.20)

    zeroReceivables = {"series": _series(), "baseRevenue": 100.0, "baseMargin": 15.0, "asOf": "2025-Q4"}
    zeroReceivables["series"]["BS"]["trade_receivables"] = [0.0] * 8
    compiled = financialInputsFromSnapshot(zeroReceivables, capacityHeadroom=0.20)
    assert compiled.state.receivables == 0.0


def testFinancialWorldRunsStepwiseAndClosesEveryPeriod():
    run = runFinancialStrategies(
        _inputs(),
        (_path(),),
        (_strategy("steady", (0.08,) * 4),),
        debtLimit=100.0,
        maxFinancing=50.0,
    )
    trace = run.traces[0]
    assert len(trace.steps) == 4
    assert all(abs(step.after["identityResidual"]) < 1e-8 for step in trace.steps)
    assert trace.steps[1].before["cash"] == trace.steps[0].after["cash"]


def testQuarterGridRequiresQuarterParametersAndRunsWithoutAnnualCoercion():
    quarterPath = buildFinancialPath(
        "quarter",
        demandGrowth=(0.01, 0.01),
        marginChange=(0.0, 0.0),
        debtRate=(0.01, 0.01),
        frequency="quarter",
    )
    strategy = _strategy("steady", (0.08, 0.08))
    with pytest.raises(SimulationSpecError, match="parameter frequency"):
        runFinancialStrategies(
            replace(_inputs(), stepFrequency="quarter"),
            (quarterPath,),
            (strategy,),
            debtLimit=100.0,
            maxFinancing=50.0,
        )

    run = runFinancialStrategies(
        replace(_inputs(), stepFrequency="quarter", parameterFrequency="quarter"),
        (quarterPath,),
        (strategy,),
        debtLimit=100.0,
        maxFinancing=50.0,
    )
    assert len(run.traces[0].steps) == 2
    assert all(abs(step.after["identityResidual"]) < 1e-8 for step in run.traces[0].steps)


def testFinancialParameterUncertaintyUsesOneDrawPerWorldPath():
    lowCapacity = buildFinancialPath(
        "low-capacity",
        demandGrowth=(0.0, 0.0),
        marginChange=(0.0, 0.0),
        debtRate=(0.05, 0.05),
        parameterDraws={"revenuePerPpe": 1.0},
    )
    baseCapacity = buildFinancialPath(
        "base-capacity",
        demandGrowth=(0.0, 0.0),
        marginChange=(0.0, 0.0),
        debtRate=(0.05, 0.05),
    )
    run = runFinancialStrategies(
        _inputs(),
        (lowCapacity, baseCapacity),
        (_strategy("steady", (0.08, 0.08)),),
        debtLimit=100.0,
        maxFinancing=50.0,
    )
    lowTrace = next(trace for trace in run.traces if trace.pathId == "low-capacity")
    baseTrace = next(trace for trace in run.traces if trace.pathId == "base-capacity")
    assert lowTrace.steps[0].after["revenue"] == 50.0
    assert baseTrace.steps[0].after["revenue"] == 100.0
    assert all(step.laws[0].pathParameters == {"revenuePerPpe": 1.0} for step in lowTrace.steps)


def testFinancialWorldExposesUnmetDemandAndPreservesItAcrossSteps():
    inputs = _inputs()
    constrainedState = type(inputs.state)(**{**inputs.state.__dict__, "latentDemandRevenue": 150.0})
    constrainedInputs = type(inputs)(
        state=constrainedState,
        parameters=inputs.parameters,
        asOf=inputs.asOf,
        refs=inputs.refs,
        warnings=inputs.warnings,
    )
    run = runFinancialStrategies(
        constrainedInputs,
        (_path(growth=(0.0, 0.0)),),
        (_strategy("expand", (0.25, 0.0)),),
        debtLimit=100.0,
        maxFinancing=50.0,
    )
    steps = run.traces[0].steps
    assert steps[0].after["unmetDemand"] > 0
    assert steps[0].after["latentDemandRevenue"] == 150.0
    assert steps[1].after["unmetDemand"] == 0.0
    assert steps[1].after["revenue"] == 150.0


def testOperatingDriverPathKeepsPriceVolumeCostAndCapacityVisible():
    inputs = financialInputsFromSnapshot(
        {
            "series": _series(),
            "baseRevenue": 100.0,
            "baseMargin": 15.0,
            "asOf": "2025-Q4",
        },
        capacityHeadroom=0.10,
        operatingDrivers=OperatingDriverInputs(
            unitPrice=10.0,
            demandUnits=10.0,
            unitCost=6.0,
            fixedCost=25.0,
            capacityUnits=11.0,
            refs=("assumption://operating-drivers",),
        ),
    )
    path = buildOperatingFinancialPath(
        "unit-shock",
        priceChange=(0.10, 0.0),
        volumeChange=(0.50, 0.0),
        unitCostChange=(0.20, 0.0),
        fixedCostChange=(0.0, 0.0),
        capacityChange=(0.0, 0.0),
        debtRate=(0.05, 0.05),
        frequency="year",
    )
    run = runFinancialStrategies(
        inputs,
        (path,),
        (_strategy("expand", (0.30, 0.0)),),
        debtLimit=100.0,
        maxFinancing=50.0,
    )
    first = run.traces[0].steps[0]
    second = run.traces[0].steps[1]
    assert first.shocks["priceChange"] == pytest.approx(0.10)
    assert first.after["unitPrice"] == pytest.approx(11.0)
    assert first.after["unitCost"] == pytest.approx(7.2)
    assert first.after["fixedCost"] == pytest.approx(25.0)
    assert first.after["demandUnits"] == pytest.approx(15.0)
    assert first.after["servedUnits"] == pytest.approx(11.0)
    assert first.after["unmetUnits"] == pytest.approx(4.0)
    assert first.after["effectiveCapacityUnits"] == pytest.approx(11.0)
    assert first.after["operatingDriverRevenue"] == pytest.approx(121.0)
    assert first.after["operatingDriverProfit"] == pytest.approx(16.8)
    assert first.after["capacityBound"] == pytest.approx(1.0)
    assert second.after["servedUnits"] > first.after["servedUnits"]
    assert "operatingDriverInputs:explicitAssumption" in run.warnings
    assert run.decisionStatus == "conditionalOnly"


def testOperatingDriverInputsNeedExecutablePhysicalBoundary():
    with pytest.raises(ValueError, match="unitPrice"):
        financialInputsFromSnapshot(
            {
                "series": _series(),
                "baseRevenue": 100.0,
                "baseMargin": 15.0,
                "asOf": "2025-Q4",
            },
            capacityHeadroom=0.10,
            operatingDrivers=OperatingDriverInputs(
                unitPrice=0.0,
                demandUnits=10.0,
                unitCost=6.0,
                fixedCost=25.0,
                capacityUnits=11.0,
            ),
        )


def testOperatingDriversMustReconcileWithObservedMargin():
    with pytest.raises(SimulationSpecError, match="observed margin"):
        financialInputsFromSnapshot(
            {
                "series": _series(),
                "baseRevenue": 100.0,
                "baseMargin": 15.0,
                "asOf": "2025-Q4",
            },
            capacityHeadroom=0.10,
            operatingDrivers=OperatingDriverInputs(
                unitPrice=10.0,
                demandUnits=10.0,
                unitCost=6.0,
                fixedCost=1.0,
                capacityUnits=11.0,
            ),
        )


def testRealAdapterKeepsAssumptionBoundaryAndDoesNotRecommend():
    run = runFinancialStrategies(
        _inputs(),
        (_path("down", (-0.1, -0.1, -0.1, -0.1)),),
        (
            _strategy("invest", (0.12,) * 4),
            _strategy("preserve", (0.02,) * 4),
        ),
        debtLimit=100.0,
        maxFinancing=50.0,
    )
    assert run.decisionStatus == "conditionalOnly"
    assert run.recommendation is None
    assert set(run.paretoStrategies) <= {"invest", "preserve"}


def testSnapshotPitWarningsReachRunAudit():
    snapshot = {
        "series": _series(),
        "baseRevenue": 100.0,
        "baseMargin": 15.0,
        "asOf": "2025-Q4",
        "assumptions": ("baseWacc10Pct",),
        "warnings": ("periodScopedPitOnly",),
    }
    inputs = financialInputsFromSnapshot(snapshot, capacityHeadroom=0.20)
    run = runFinancialStrategies(
        inputs,
        (_path(),),
        (_strategy("steady", (0.08,) * 4),),
        debtLimit=100.0,
        maxFinancing=50.0,
    )
    assert "snapshotAssumption:baseWacc10Pct" in run.warnings
    assert "snapshotWarning:periodScopedPitOnly" in run.warnings


def testFinancingMustBeExplicitAndConstraintBreachIsVisible():
    stress = buildFinancialPath(
        "stress",
        demandGrowth=(-0.8,) * 4,
        marginChange=(-0.1,) * 4,
        debtRate=(0.20,) * 4,
    )
    run = runFinancialStrategies(
        _inputs(),
        (stress,),
        (
            _strategy("no-funding", (1.0,) * 4, inventory=1.0),
            _strategy("funded", (1.0,) * 4, inventory=1.0, borrow=10.0),
        ),
        debtLimit=55.0,
        maxFinancing=20.0,
    )
    noFunding = next(trace for trace in run.traces if trace.strategyId == "no-funding")
    funded = next(trace for trace in run.traces if trace.strategyId == "funded")
    assert any("cash:ge" in breach for step in noFunding.steps for breach in step.breaches)
    assert funded.steps[-1].after["debt"] > noFunding.steps[-1].after["debt"]
    assert funded.steps[-1].after["cash"] > noFunding.steps[-1].after["cash"]


@pytest.mark.realData
@pytest.mark.serial
def testRealDataSamsungSnapshotRunsAuditedFinancialWorld():
    from dartlab.providers.dart.company import Company
    from dartlab.simulate.registry import buildSnapshot

    company = Company("005930")
    try:
        snapshot = buildSnapshot(company)
        if not snapshot.get("series") or snapshot.get("baseRevenue") is None:
            pytest.skip("005930 finance series unavailable")
        inputs = financialInputsFromSnapshot(snapshot, capacityHeadroom=0.20)
        horizon = 4
        path = buildFinancialPath(
            "stress",
            demandGrowth=(-0.12, -0.08, 0.02, 0.03),
            marginChange=(-0.02, -0.01, 0.01, 0.01),
            debtRate=(0.06,) * horizon,
        )
        capexRatio = min(
            0.25,
            max(0.01, inputs.parameters.depreciationRate * inputs.state.ppe / inputs.state.revenue),
        )
        inventoryRatio = inputs.state.inventories / inputs.state.revenue
        strategy = buildFinancialStrategy(
            "preserve",
            capexRatio=(capexRatio * 0.5,) * horizon,
            inventoryRatio=(inventoryRatio * 0.9,) * horizon,
            borrow=(0.0,) * horizon,
            repay=(0.0,) * horizon,
        )
        run = runFinancialStrategies(
            inputs,
            (path,),
            (strategy,),
            debtLimit=max(inputs.state.debt * 2, 1.0),
            maxFinancing=max(inputs.state.revenue * 0.2, 1.0),
        )
        assert inputs.state.revenue > 0
        assert max(abs(step.after["identityResidualRatio"]) for step in run.traces[0].steps) < 1e-10
        assert run.decisionStatus == "conditionalOnly"
        assert run.recommendation is None
    finally:
        del company
        gc.collect()
