from __future__ import annotations

import polars as pl
import pytest

from dartlab.simulate.driverPaths import (
    DriverAssumptionSource,
    DriverCard,
    DriverFactorSpec,
    DriverHistorySource,
    DriverPathError,
    buildDriverPathSet,
    driverFactorsToOperatingSpecs,
)
from dartlab.simulate.operatingBridge import (
    OperatingShockBaseline,
    OperatingTransmissionExposure,
    bridgeOperatingPath,
)


def _historyCard(
    cardId: str,
    variableId: str,
    *,
    sourceColumn: str = "",
    frequency: str = "quarter",
    status: str = "active",
    historyStatus: str = "revisedHistory",
) -> DriverCard:
    return DriverCard(
        cardId=cardId,
        sourceKind="history",
        providerId="macro",
        datasetId=f"{cardId}-dataset",
        entityId="KR",
        frequency=frequency,
        stepSpan=1,
        factors=(
            DriverFactorSpec(
                variableId,
                "simpleReturn",
                frequency,
                "innovation",
                "simple-return-v1",
                sourceColumn=sourceColumn,
            ),
        ),
        historyStatus=historyStatus,
        sourceRefs=(f"source://{cardId}",),
        status=status,
    )


def _assumptionCard() -> DriverCard:
    return DriverCard(
        cardId="demand-assumption",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec("demandShock", "simpleReturn", "quarter", "innovation", "manual-shock-v1"),),
        historyStatus="explicitAssumption",
        sourceRefs=("assumption://demand-down",),
        assumptionId="assumption-demand-down",
        claim="Demand units decline for two quarters.",
        falsifier="Observed order book does not decline.",
    )


def _baselines() -> tuple[OperatingShockBaseline, ...]:
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


def testDriverPathSetJoinsHistoryAndAssumptionsIntoBridgeReadyPath() -> None:
    history = pl.DataFrame(
        {
            "eventTime": ["20200103", "20200110", "20200117", "20200124", "20250103"],
            "availableAt": ["20200103", "20200110", "20200117", "20200124", "20250103"],
            "fx": [0.01, -0.02, 0.03, 0.04, 9.99],
        }
    )
    pathSet = buildDriverPathSet(
        (
            DriverHistorySource(_historyCard("fx-history", "fxChange", sourceColumn="fx"), history),
            DriverAssumptionSource(_assumptionCard(), ({"demandShock": -0.05}, {"demandShock": 0.02})),
        ),
        knowledgeAsOf="20201231",
        horizon=2,
        pathCount=3,
        blockLength=1,
        seed=7,
        minObservations=4,
    )
    assert pathSet.audit.validationStatus == "unvalidated"
    assert pathSet.audit.historyStatus == "explicitAssumption"
    assert "explicitAssumption:assumption-demand-down" in pathSet.audit.warnings
    assert {path.validationStatus for path in pathSet.paths} == {"unvalidated"}
    assert all("assumption://demand-down" in path.refs for path in pathSet.paths)
    assert all(
        "driverRegistry:" in ref for path in pathSet.paths for ref in path.refs if ref.startswith("driverRegistry:")
    )
    assert {step["demandShock"] for path in pathSet.paths for step in path.steps} == {-0.05, 0.02}
    assert all(step["fxChange"] != 9.99 for path in pathSet.paths for step in path.steps)

    factorSpecs = driverFactorsToOperatingSpecs(pathSet.factorSpecs)
    bridge = bridgeOperatingPath(
        pathSet.paths[0],
        (
            OperatingTransmissionExposure(
                "fx-price",
                "fxChange",
                "marketPriceChange",
                0.5,
                "ratioChangePerStep/simpleReturn",
                "explicitAssumption",
                "assumption://fx-price",
            ),
            OperatingTransmissionExposure(
                "demand-volume",
                "demandShock",
                "demandChange",
                1.0,
                "ratioChangePerStep/simpleReturn",
                "explicitAssumption",
                "assumption://demand-volume",
            ),
        ),
        factorSpecs=factorSpecs,
        baselines=_baselines(),
    )
    assert bridge.path.validationStatus == "unvalidated"
    assert bridge.path.steps[0]["demandChange"] == pytest.approx(-0.05)


def testDriverPathSetPreservesJointHistorySupportAcrossSources() -> None:
    fx = pl.DataFrame(
        {
            "eventTime": ["20200103", "20200110", "20200117", "20200124"],
            "availableAt": ["20200103", "20200110", "20200117", "20200124"],
            "fx": [1.0, 2.0, 3.0, 4.0],
        }
    )
    oil = pl.DataFrame(
        {
            "eventTime": ["20200110", "20200117", "20200124", "20200131"],
            "availableAt": ["20200110", "20200117", "20200124", "20200131"],
            "oil": [20.0, 30.0, 40.0, 50.0],
        }
    )
    pathSet = buildDriverPathSet(
        (
            DriverHistorySource(_historyCard("fx-history", "fxChange", sourceColumn="fx"), fx),
            DriverHistorySource(_historyCard("oil-history", "oilShock", sourceColumn="oil"), oil),
        ),
        knowledgeAsOf="20201231",
        horizon=3,
        pathCount=4,
        blockLength=1,
        seed=3,
        minObservations=3,
    )
    assert pathSet.audit.validationStatus == "retrospectiveOnly"
    support = {(2.0, 20.0), (3.0, 30.0), (4.0, 40.0)}
    assert {(step["fxChange"], step["oilShock"]) for path in pathSet.paths for step in path.steps}.issubset(support)


def testDriverPathSetFailsClosedOnStatusMeaningAndAssumptionDrift() -> None:
    panel = pl.DataFrame(
        {
            "eventTime": ["20200103", "20200110", "20200117", "20200124"],
            "availableAt": ["20200103", "20200110", "20200117", "20200124"],
            "fx": [0.01, -0.02, 0.03, 0.04],
        }
    )
    with pytest.raises(DriverPathError, match="not executable"):
        buildDriverPathSet(
            (DriverHistorySource(_historyCard("fx-history", "fxChange", sourceColumn="fx", status="rejected"), panel),),
            knowledgeAsOf="20201231",
            horizon=2,
            pathCount=2,
            blockLength=1,
            seed=1,
            minObservations=4,
        )
    with pytest.raises(DriverPathError, match="step contract"):
        buildDriverPathSet(
            (
                DriverHistorySource(_historyCard("fx-history", "fxChange", sourceColumn="fx"), panel),
                DriverHistorySource(
                    _historyCard("oil-history", "oilShock", sourceColumn="fx", frequency="week"), panel
                ),
            ),
            knowledgeAsOf="20201231",
            horizon=2,
            pathCount=2,
            blockLength=1,
            seed=1,
            minObservations=4,
        )
    badAssumption = DriverCard(
        cardId="bad-assumption",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec("demandShock", "simpleReturn", "quarter", "innovation", "manual-shock-v1"),),
        historyStatus="explicitAssumption",
        sourceRefs=("assumption://bad",),
        assumptionId="bad",
        claim="Demand changes.",
        falsifier="",
    )
    with pytest.raises(DriverPathError, match="falsifier"):
        buildDriverPathSet(
            (DriverAssumptionSource(badAssumption, ({"demandShock": 0.0},)),),
            knowledgeAsOf="20201231",
            horizon=1,
            pathCount=1,
            blockLength=1,
            seed=1,
        )


def testDriverPathSetHashBindsAssumptionContentAndRefs() -> None:
    first = buildDriverPathSet(
        (DriverAssumptionSource(_assumptionCard(), ({"demandShock": -0.05}, {"demandShock": 0.02})),),
        knowledgeAsOf="20201231",
        horizon=2,
        pathCount=1,
        blockLength=1,
        seed=1,
    )
    changedCard = DriverCard(
        **{
            **_assumptionCard().__dict__,
            "sourceRefs": ("assumption://changed",),
        }
    )
    changed = buildDriverPathSet(
        (DriverAssumptionSource(changedCard, ({"demandShock": -0.05}, {"demandShock": 0.02})),),
        knowledgeAsOf="20201231",
        horizon=2,
        pathCount=1,
        blockLength=1,
        seed=1,
    )
    changedValue = buildDriverPathSet(
        (DriverAssumptionSource(_assumptionCard(), ({"demandShock": -0.04}, {"demandShock": 0.02})),),
        knowledgeAsOf="20201231",
        horizon=2,
        pathCount=1,
        blockLength=1,
        seed=1,
    )
    assert first.audit.pathSetHash != changed.audit.pathSetHash
    assert first.audit.pathSetHash != changedValue.audit.pathSetHash
    assert first.paths[0].historyStatus == "explicitAssumption"
    assert first.paths[0].weightKind == "unweighted"
