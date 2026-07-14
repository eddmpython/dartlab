from __future__ import annotations

import pytest

from dartlab.simulate.driverPaths import (
    DriverAssumptionSource,
    DriverCard,
    DriverFactorSpec,
    buildDriverPathSet,
)
from dartlab.simulate.operatingBridge import OperatingShockBaseline, OperatingTransmissionExposure
from dartlab.simulate.operatingWorld import (
    OperatingPrimitive,
    buildOperatingStrategy,
    operatingInputsFromPrimitives,
)
from dartlab.simulate.scenarioComposition import (
    OperatingScenarioCase,
    ScenarioCompositionError,
    compareOperatingScenarioCases,
)


def _inputs():
    rows = (
        OperatingPrimitive("price", 10.0, "currencyPerUnit", "explicitAssumption", "assumption://price"),
        OperatingPrimitive("demandVolume", 100.0, "units", "explicitAssumption", "assumption://volume"),
        OperatingPrimitive("unitCost", 6.0, "currencyPerUnit", "explicitAssumption", "assumption://unit-cost"),
        OperatingPrimitive("fixedCost", 100.0, "currency", "explicitAssumption", "assumption://fixed-cost"),
        OperatingPrimitive("capacityUnits", 150.0, "units", "explicitAssumption", "assumption://capacity"),
        OperatingPrimitive("cash", 500.0, "currency", "observed", "filing://cash"),
        OperatingPrimitive("debt", 20.0, "currency", "observed", "filing://debt"),
    )
    return operatingInputsFromPrimitives(
        rows,
        asOf="20250101",
        priceElasticity=1.0,
        capacityUnitsPerCurrency=1.0,
        taxRate=0.0,
    )


def _baselines():
    return tuple(
        OperatingShockBaseline(
            target,
            0.04 if target == "debtRate" else 0.0,
            "effectiveRatePerStep" if target == "debtRate" else "ratioChangePerStep",
            "explicitAssumption",
            f"assumption://baseline/{target}",
        )
        for target in (
            "marketPriceChange",
            "demandChange",
            "unitCostChange",
            "fixedCostChange",
            "capacityChange",
            "debtRate",
        )
    )


def _case(caseId: str, demandShock: tuple[float, ...], variableId: str = "demandShock") -> OperatingScenarioCase:
    card = DriverCard(
        cardId=f"{caseId}-demand",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec(variableId, "simpleReturn", "quarter", "innovation", "manual-shock-v1"),),
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/demand",),
        assumptionId=f"{caseId}-demand",
        claim=f"{caseId} demand scenario.",
        falsifier="Order book does not move with the demand scenario.",
    )
    pathSet = buildDriverPathSet(
        (
            DriverAssumptionSource(
                card,
                tuple({variableId: value} for value in demandShock),
            ),
        ),
        knowledgeAsOf="20250101",
        horizon=len(demandShock),
        pathCount=1,
        blockLength=1,
        seed=1,
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        (
            OperatingTransmissionExposure(
                f"{caseId}-demand-volume",
                variableId,
                "demandChange",
                1.0,
                "ratioChangePerStep/simpleReturn",
                "explicitAssumption",
                f"assumption://{caseId}/demand-volume",
            ),
        ),
        _baselines(),
        refs=(f"scenario://{caseId}",),
    )


def _strategies():
    return (
        buildOperatingStrategy(
            "hold",
            priceChange=(0.0, 0.0),
            capacityInvestment=(0.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://hold",),
            isBaseline=True,
        ),
        buildOperatingStrategy(
            "invest",
            priceChange=(0.0, 0.0),
            capacityInvestment=(25.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://invest",),
        ),
    )


def _score(result, strategyId: str, objectiveIndex: int = 0) -> float:
    row = next(item for item in result.strategyScores if item.strategyId == strategyId)
    return row.objectiveScores[objectiveIndex]


def testScenarioCompositionRunsSharedStrategiesAcrossNamedCases() -> None:
    comparison = compareOperatingScenarioCases(
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert comparison.decisionStatus == "conditionalOnly"
    assert comparison.recommendation is None
    assert comparison.strategyIds == ("hold", "invest")
    assert len(comparison.caseResults) == 2
    base, stress = comparison.caseResults
    assert base.caseId == "base"
    assert stress.caseId == "stress"
    assert _score(base, "hold") > _score(stress, "hold")
    assert all(result.counts.interventionCount == 1 for result in comparison.caseResults)
    assert all(result.counts.explicitAssumptionCount > 0 for result in comparison.caseResults)
    assert all(result.decisionStatus == "conditionalOnly" for result in comparison.caseResults)
    assert any("automatic recommendation disabled" in warning for warning in comparison.warnings)
    assert comparison.comparisonHash


def testScenarioCompositionHashBindsCaseAssumptionContent() -> None:
    first = compareOperatingScenarioCases(
        _inputs(),
        (_case("base", (0.0, 0.0)),),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changed = compareOperatingScenarioCases(
        _inputs(),
        (_case("base", (0.0, -0.1)),),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert first.comparisonHash != changed.comparisonHash
    assert first.caseResults[0].pathSetHash != changed.caseResults[0].pathSetHash


def testScenarioCompositionRejectsInterventionInsidePath() -> None:
    with pytest.raises(ScenarioCompositionError, match="intervention actions"):
        compareOperatingScenarioCases(
            _inputs(),
            (_case("bad", (0.1, 0.1), variableId="priceChange"),),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testScenarioCompositionRejectsDuplicateCaseIds() -> None:
    with pytest.raises(ScenarioCompositionError, match="unique ids"):
        compareOperatingScenarioCases(
            _inputs(),
            (_case("base", (0.0, 0.0)), _case("base", (-0.1, -0.1))),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )
