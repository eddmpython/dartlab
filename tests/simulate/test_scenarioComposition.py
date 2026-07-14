from __future__ import annotations

from dataclasses import replace

import polars as pl
import pytest

from dartlab.simulate.driverCalibration import (
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
)
from dartlab.simulate.driverPaths import (
    DriverAssumptionSource,
    DriverCard,
    DriverFactorSpec,
    DriverHistorySource,
    buildDriverPathSet,
    composeDriverPathSetWithAssumptions,
)
from dartlab.simulate.operatingBridge import (
    OperatingShockBaseline,
    OperatingTransmissionExposure,
    sourceFactorContractHash,
)
from dartlab.simulate.operatingWorld import (
    OperatingPrimitive,
    buildOperatingStrategy,
    operatingInputsFromPrimitives,
)
from dartlab.simulate.scenarioComposition import (
    OperatingScenarioCase,
    ScenarioCoefficientBinding,
    ScenarioCompositionError,
    compareOneCompanyTwoScenarioStrategies,
    compareOperatingScenarioCases,
    runConditionalScenarioExperiment,
    scenarioCoefficientBindingHash,
    scenarioCoefficientExposureContractHash,
)
from dartlab.simulate.vintage import VintageRef
from dartlab.simulate.world import (
    bindAdmittedPathContent,
    bindPathAdmissionReceipt,
    pathSetAdmissionSubjectHash,
)

_COEFFICIENT_RECEIPT_ID = "a" * 64
_COEFFICIENT_SUBJECT_HASH = "b" * 64
_COEFFICIENT_RULE_HASH = MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH
_COEFFICIENT_VECTOR_HASH = "d" * 64
_COEFFICIENT_FEATURE_SPEC_HASH = "e" * 64
_COEFFICIENT_DESIGN_FRAME_HASH = "f" * 64
_COEFFICIENT_FIT_DESIGN_FRAME_HASH = "1" * 64
_COEFFICIENT_OOS_DESIGN_FRAME_HASH = "2" * 64
_COEFFICIENT_PARENT_RECEIPTS = ("3" * 64, "4" * 64)


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


def _admittedBasePathSet():
    card = DriverCard(
        cardId="observed-demand-history",
        sourceKind="history",
        providerId="fixture",
        datasetId="driver-history",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec("observedDemandShock", "simpleReturn", "quarter", "innovation", "history-v1"),),
        historyStatus="asKnown",
        sourceRefs=("providerObservationBatch:observed-demand-history",),
    )
    panel = pl.DataFrame(
        {
            "eventTime": ["20240101", "20240401", "20240701", "20241001"],
            "availableAt": ["20240102", "20240402", "20240702", "20241002"],
            "observedDemandShock": [0.01, -0.02, 0.03, 0.02],
        }
    )
    base = buildDriverPathSet(
        (DriverHistorySource(card, panel),),
        knowledgeAsOf="20250101",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=5,
        minObservations=4,
    )
    admittedPaths = bindPathAdmissionReceipt(
        bindAdmittedPathContent(
            tuple(
                replace(
                    path,
                    validationStatus="admitted",
                    certificateId="a" * 64,
                    maxAdmittedStep=2,
                    historyStatus="asKnown",
                )
                for path in base.paths
            )
        ),
        "b" * 64,
    )
    return replace(base, paths=admittedPaths)


def _conditionalOverlayCase(caseId: str, shock: tuple[float, float]) -> OperatingScenarioCase:
    card = DriverCard(
        cardId=f"{caseId}-manual-demand-overlay",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec("manualDemandAdjustment", "simpleReturn", "quarter", "change", "manual-v1"),),
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/manual-demand-overlay",),
        assumptionId=f"{caseId}-manual-demand-overlay",
        claim=f"{caseId} explicit future demand overlay.",
        falsifier="The manual demand overlay is not the tested scenario.",
    )
    pathSet = composeDriverPathSetWithAssumptions(
        _admittedBasePathSet(),
        (DriverAssumptionSource(card, tuple({"manualDemandAdjustment": value} for value in shock)),),
        registryId=f"{caseId}-admitted-base-plus-overlay",
    )
    exposures = (
        OperatingTransmissionExposure(
            f"{caseId}-observed-demand",
            "observedDemandShock",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/observed-demand",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-manual-demand",
            "manualDemandAdjustment",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/manual-demand",
        ),
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        exposures,
        _baselines(),
        refs=(f"scenario://{caseId}",),
    )


def _measured_case(
    caseId: str,
    shocks: tuple[tuple[float, float], ...],
    *,
    receiptId: str = _COEFFICIENT_RECEIPT_ID,
    fxCoefficient: float = 0.4,
    oilCoefficient: float = -0.2,
    aggregationGroup: str = "macro-demand-vector",
) -> OperatingScenarioCase:
    factors = (
        DriverFactorSpec("fxChange", "simpleReturn", "quarter", "innovation", "simple-return-v1"),
        DriverFactorSpec("oilChange", "simpleReturn", "quarter", "innovation", "simple-return-v1"),
    )
    card = DriverCard(
        cardId=f"{caseId}-macro",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=factors,
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/macro",),
        assumptionId=f"{caseId}-macro",
        claim=f"{caseId} macro scenario.",
        falsifier="Macro factor movement does not change demand.",
    )
    pathSet = buildDriverPathSet(
        (
            DriverAssumptionSource(
                card,
                tuple({"fxChange": fx, "oilChange": oil} for fx, oil in shocks),
            ),
        ),
        knowledgeAsOf="20250101",
        horizon=len(shocks),
        pathCount=1,
        blockLength=1,
        seed=1,
    )
    sourceRef = f"driverCoefficientAdmission:{receiptId}"
    exposures = (
        OperatingTransmissionExposure(
            f"{caseId}-fx-demand",
            "fxChange",
            "demandChange",
            fxCoefficient,
            "ratioChangePerStep/simpleReturn",
            "measuredAssociation",
            sourceRef,
            aggregationGroup=aggregationGroup,
            sourceFrequency="quarter",
            sourceTiming="innovation",
            sourceTransformId="simple-return-v1",
            sourceFactorContractHash=sourceFactorContractHash(
                variableId="fxChange",
                unit="simpleReturn",
                frequency="quarter",
                timing="innovation",
                transformId="simple-return-v1",
            ),
        ),
        OperatingTransmissionExposure(
            f"{caseId}-oil-demand",
            "oilChange",
            "demandChange",
            oilCoefficient,
            "ratioChangePerStep/simpleReturn",
            "measuredAssociation",
            sourceRef,
            aggregationGroup=aggregationGroup,
            sourceFrequency="quarter",
            sourceTiming="innovation",
            sourceTransformId="simple-return-v1",
            sourceFactorContractHash=sourceFactorContractHash(
                variableId="oilChange",
                unit="simpleReturn",
                frequency="quarter",
                timing="innovation",
                transformId="simple-return-v1",
            ),
        ),
    )
    binding = ScenarioCoefficientBinding(
        admissionReceiptId=receiptId,
        subjectHash=_COEFFICIENT_SUBJECT_HASH,
        ruleHash=_COEFFICIENT_RULE_HASH,
        ruleId=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
        parentReceiptIds=_COEFFICIENT_PARENT_RECEIPTS,
        sourceVariableIds=("fxChange", "oilChange"),
        targetShock="demandChange",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=len(shocks),
        coefficientVectorHash=_COEFFICIENT_VECTOR_HASH,
        featureSpecHash=_COEFFICIENT_FEATURE_SPEC_HASH,
        designFrameHash=_COEFFICIENT_DESIGN_FRAME_HASH,
        exposureContractHash=scenarioCoefficientExposureContractHash(exposures),
        calibrationId="macro-demand-calibration",
        reportId="macro-demand-oos",
        fitDesignFrameHash=_COEFFICIENT_FIT_DESIGN_FRAME_HASH,
        oosDesignFrameHash=_COEFFICIENT_OOS_DESIGN_FRAME_HASH,
        sourceRefs=("oosReport://macro-demand",),
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        exposures,
        _baselines(),
        refs=(f"scenario://{caseId}",),
        coefficientBindings=(binding,),
    )


def _strategies(investment: float = 25.0):
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
            capacityInvestment=(investment, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://invest",),
        ),
    )


def _threeStrategies():
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
            capacityInvestment=(35.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://invest",),
        ),
        buildOperatingStrategy(
            "defend",
            priceChange=(0.04, 0.04),
            capacityInvestment=(0.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(10.0, 0.0),
            refs=("strategy://defend",),
        ),
    )


def _multiVariableCase(
    caseId: str,
    demandShock: tuple[float, float],
    unitCostShock: tuple[float, float],
    capacityShock: tuple[float, float],
) -> OperatingScenarioCase:
    factors = (
        DriverFactorSpec("demandShock", "simpleReturn", "quarter", "innovation", "manual-shock-v1"),
        DriverFactorSpec("unitCostShock", "simpleReturn", "quarter", "innovation", "manual-shock-v1"),
        DriverFactorSpec("capacityShock", "simpleReturn", "quarter", "innovation", "manual-shock-v1"),
    )
    card = DriverCard(
        cardId=f"{caseId}-three-variable",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario-grid",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=factors,
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/three-variable",),
        assumptionId=f"{caseId}-three-variable",
        claim=f"{caseId} demand, unit cost, and capacity assumption set.",
        falsifier="Observed demand, unit cost, or capacity path does not match the assumption set.",
    )
    pathSet = buildDriverPathSet(
        (
            DriverAssumptionSource(
                card,
                tuple(
                    {
                        "demandShock": demandShock[index],
                        "unitCostShock": unitCostShock[index],
                        "capacityShock": capacityShock[index],
                    }
                    for index in range(2)
                ),
            ),
        ),
        knowledgeAsOf="20250101",
        horizon=2,
        pathCount=1,
        blockLength=1,
        seed=7,
    )
    exposures = (
        OperatingTransmissionExposure(
            f"{caseId}-demand",
            "demandShock",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/demand",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-unit-cost",
            "unitCostShock",
            "unitCostChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/unit-cost",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-capacity",
            "capacityShock",
            "capacityChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/capacity",
        ),
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        exposures,
        _baselines(),
        refs=(f"scenario://{caseId}",),
    )


def _experimentCases():
    return (
        _multiVariableCase("base", (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        _multiVariableCase("demandUp", (0.12, 0.08), (0.0, 0.0), (0.02, 0.02)),
        _multiVariableCase("costStress", (-0.04, -0.06), (0.16, 0.12), (-0.03, -0.02)),
        _multiVariableCase("capacityStress", (0.04, 0.02), (0.05, 0.03), (-0.18, -0.12)),
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


def testConditionalScenarioExperimentSweepsAssumptionsAndStrategies() -> None:
    experiment = runConditionalScenarioExperiment(
        "005930",
        _inputs(),
        _experimentCases(),
        _threeStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert experiment.schemaVersion == "conditional-scenario-experiment-v1"
    assert experiment.entityId == "005930"
    assert experiment.scenarioCount == 4
    assert experiment.strategyCount == 3
    assert experiment.cellCount == 12
    assert experiment.decisionStatus == "conditionalOnly"
    assert experiment.recommendationCeiling == "conditionalOnly"
    assert experiment.recommendation is None
    assert experiment.strategyIds == ("hold", "invest", "defend")
    assert experiment.assumptionSetIds == ("base", "demandUp", "costStress", "capacityStress")
    assert len(set(experiment.assumptionSetHashes)) == 4
    assert experiment.strategySetHash
    assert experiment.simulationSpecHash
    assert experiment.resultSetHash
    assert experiment.experimentHash
    assert len(experiment.caseLedgers) == 4
    assert len(experiment.caseLedgerHashes) == 4
    assert len(set(experiment.caseLedgerHashes)) == 4
    assert experiment.providerObservationBatchRefs == ()
    assert experiment.explicitAssumptionIds == (
        "base-three-variable",
        "demandUp-three-variable",
        "costStress-three-variable",
        "capacityStress-three-variable",
    )
    assert experiment.pathAssumptionHashes == tuple(ledger.pathAssumptionHash for ledger in experiment.caseLedgers)
    assert all(experiment.pathAssumptionHashes)
    assert len(experiment.strategySummaries) == 3
    assert len(experiment.fragilityCells) == 4
    assert all(summary.totalCellCount == 4 for summary in experiment.strategySummaries)
    assert sum(summary.leaderCellCount for summary in experiment.strategySummaries) >= 4
    assert all(cell.regret >= 0.0 for cell in experiment.cells)
    assert experiment.fragilityCells[0].leaderMargin <= experiment.fragilityCells[-1].leaderMargin
    assert "assumptionSweepPresent" in experiment.blockedReasons
    assert "strategySweepPresent" in experiment.blockedReasons
    assert "automaticRecommendationDisabled" in experiment.blockedReasons
    assert "conditionalExperimentNotPolicyRecommendation" in experiment.blockedReasons
    assert "pathAdmissionMissing" in experiment.blockedReasons
    assert "policyEvaluationCertificateMissing" in experiment.blockedReasons


def testConditionalScenarioExperimentHashBindsAssumptionGridAndResults() -> None:
    first = runConditionalScenarioExperiment(
        "005930",
        _inputs(),
        _experimentCases(),
        _threeStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    repeat = runConditionalScenarioExperiment(
        "005930",
        _inputs(),
        _experimentCases(),
        _threeStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedCases = (
        _multiVariableCase("base", (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        _multiVariableCase("demandUp", (0.18, 0.12), (0.0, 0.0), (0.02, 0.02)),
        _multiVariableCase("costStress", (-0.04, -0.06), (0.16, 0.12), (-0.03, -0.02)),
        _multiVariableCase("capacityStress", (0.04, 0.02), (0.05, 0.03), (-0.18, -0.12)),
    )
    changed = runConditionalScenarioExperiment(
        "005930",
        _inputs(),
        changedCases,
        _threeStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert first.experimentHash == repeat.experimentHash
    assert first.resultSetHash == repeat.resultSetHash
    assert first.simulationSpecHash == repeat.simulationSpecHash
    assert first.assumptionSetHashes != changed.assumptionSetHashes
    assert first.pathAssumptionHashes != changed.pathAssumptionHashes
    assert first.simulationSpecHash != changed.simulationSpecHash
    assert first.resultSetHash != changed.resultSetHash
    assert first.experimentHash != changed.experimentHash
    assert first.cells != changed.cells


def testConditionalScenarioExperimentRequiresSweepShape() -> None:
    with pytest.raises(ScenarioCompositionError, match="at least two assumption"):
        runConditionalScenarioExperiment(
            "005930",
            _inputs(),
            (_experimentCases()[0],),
            _threeStrategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )
    with pytest.raises(ScenarioCompositionError, match="at least two strategies"):
        runConditionalScenarioExperiment(
            "005930",
            _inputs(),
            _experimentCases(),
            (_threeStrategies()[0],),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


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


def testOneCompanyScenarioLoopSummarizesConditionsStateAndStrategyBlocks() -> None:
    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert loop.schemaVersion == "one-company-scenario-loop-v1"
    assert loop.entityId == "005930"
    assert loop.scenarioCount == 2
    assert loop.strategyCount == 2
    assert loop.decisionStatus == "conditionalOnly"
    assert loop.recommendationCeiling == "conditionalOnly"
    assert loop.recommendation is None
    assert loop.strategyIds == ("hold", "invest")
    assert "strategy://hold" in loop.strategyRefs
    assert "filing://cash" in loop.initialStateRefs
    assert "automaticRecommendationDisabled" in loop.blockedReasons
    assert "comparisonDecisionStatus:conditionalOnly" in loop.blockedReasons
    assert loop.loopHash
    base, stress = loop.caseLedgers
    assert base.caseId == "base"
    assert stress.caseId == "stress"
    assert base.factorIds == ("demandShock",)
    assert "scenario://base" in base.conditionRefs
    assert "assumption://base/demand" in base.assumptionRefs
    assert "filing://debt" in base.stateRefs
    assert base.bridgeHashes
    assert base.runHash
    assert base.resultHash
    assert base.executableHash
    assert base.parameterHash
    assert base.dataVintageHash
    assert base.traceRoot
    assert base.strategyScores
    assert base.scoreLeaderStrategies
    assert "explicitAssumptionPresent" in base.blockedReasons
    assert "pathAdmissionIncomplete" in base.blockedReasons
    assert "pathAdmissionMissing" in base.blockedReasons
    assert "policyEvaluationCertificateMissing" in base.blockedReasons


def testAdmittedBasePathReceiptDoesNotTransferToExplicitOverlayScenario() -> None:
    baseCase = _conditionalOverlayCase("base", (0.01, 0.02))
    stressCase = _conditionalOverlayCase("stress", (-0.03, -0.02))
    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (baseCase, stressCase),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    base, stress = loop.caseLedgers
    assert loop.recommendation is None
    assert base.pathHistoryInputHash == stress.pathHistoryInputHash
    assert base.basePathSetHash == stress.basePathSetHash
    assert base.basePathAdmissionReceiptId == "b" * 64
    assert base.basePathAdmissionReceiptId == stress.basePathAdmissionReceiptId
    assert base.basePathAdmissionContentHash == pathSetAdmissionSubjectHash(_admittedBasePathSet().paths)
    assert base.basePathAdmissionSubjectHash == base.basePathAdmissionContentHash
    assert base.basePathValidationStatus == "admitted"
    assert base.basePathMaxAdmittedStep == 2
    assert base.pathAssumptionHash != stress.pathAssumptionHash
    assert base.pathOverlayHash != stress.pathOverlayHash
    assert base.composedPathSetHash != base.basePathSetHash
    assert base.composedPathSetHash != stress.composedPathSetHash
    assert base.basePathAdmissionScope == "historyOnly"
    assert base.composedPathAdmissionStatus == "notAdmitted"
    assert base.pathAdmissionTransferStatus == "notTransferred"
    assert "basePathAdmittedButOverlayConditional" in base.pathAdmissionTransferBlockedBy
    assert "explicitFutureAdjustmentPresent" in base.pathAdmissionTransferBlockedBy
    assert "pathAdmissionNotTransferredFromObservedHistory" in base.pathAdmissionTransferBlockedBy
    assert base.pathAdmissionReceiptId == ""
    assert base.policyEvaluationCertificateId == ""
    assert "basePathAdmittedButOverlayConditional" in base.blockedReasons
    assert "basePathAdmissionScopeHistoryOnly" in base.blockedReasons
    assert "composedPathAdmissionNotGranted" in base.blockedReasons
    assert "pathAdmissionMissing" in base.blockedReasons
    assert "policyEvaluationRequiresAdmittedComposedPath" in base.blockedReasons
    assert "policyEvaluationCertificateMissing" in base.blockedReasons
    assert "automaticRecommendationDisabled" in loop.blockedReasons

    pathVintage = VintageRef(
        artifactKind="driverPathSet",
        provider="fixture",
        artifactId="base-path-vintage",
        artifactHash="c" * 64,
        payloadHash="d" * 64,
        knowledgeAsOf="20250101",
        availableAt="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        eventThrough="20241001",
        receiptId="e" * 64,
    )
    launderedPaths = tuple(
        replace(
            path,
            validationStatus="admitted",
            certificateId="a" * 64,
            maxAdmittedStep=2,
            historyStatus="asKnown",
            admissionContentHash=base.basePathAdmissionContentHash,
            admissionReceiptId=base.basePathAdmissionReceiptId,
            vintage=pathVintage,
        )
        for path in baseCase.pathSet.paths
    )
    launderedCase = replace(baseCase, pathSet=replace(baseCase.pathSet, paths=launderedPaths))
    with pytest.raises(ScenarioCompositionError, match="explicit overlay cannot carry path admission"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (launderedCase, stressCase),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testOneCompanyScenarioLoopCarriesAdmittedCoefficientBindingLedger() -> None:
    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_measured_case("base", ((0.0, 0.0), (0.1, -0.1))), _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2)))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert loop.decisionStatus == "conditionalOnly"
    assert loop.recommendationCeiling == "conditionalOnly"
    assert loop.recommendation is None
    base, _ = loop.caseLedgers
    binding = _measured_case("base", ((0.0, 0.0), (0.1, -0.1))).coefficientBindings[0]
    assert base.coefficientAdmissionReceiptIds == (_COEFFICIENT_RECEIPT_ID,)
    assert base.coefficientBindingHashes == (scenarioCoefficientBindingHash(binding),)
    assert base.coefficientParentReceiptIds == _COEFFICIENT_PARENT_RECEIPTS
    assert f"driverCoefficientAdmission:{_COEFFICIENT_RECEIPT_ID}" in base.conditionRefs
    assert f"coefficientBinding:{scenarioCoefficientBindingHash(binding)}" in base.conditionRefs
    assert f"coefficientVector:{_COEFFICIENT_VECTOR_HASH}" in base.conditionRefs
    assert (
        "coefficientParentReceipt:3333333333333333333333333333333333333333333333333333333333333333"
        in base.conditionRefs
    )
    assert len(base.exposureLedgers) == 2
    assert {row.evidenceKind for row in base.exposureLedgers} == {"measuredAssociation"}
    assert {row.admissionReceiptId for row in base.exposureLedgers} == {_COEFFICIENT_RECEIPT_ID}
    assert {row.aggregationGroup for row in base.exposureLedgers} == {"macro-demand-vector"}
    assert {row.sourceVariableId for row in base.exposureLedgers} == {"fxChange", "oilChange"}
    assert all(row.sourceFactorContractHash for row in base.exposureLedgers)
    assert "pathAdmissionMissing" in base.blockedReasons
    assert "policyEvaluationCertificateMissing" in base.blockedReasons
    assert "automaticRecommendationDisabled" in loop.blockedReasons


def testOneCompanyScenarioLoopHashBindsCoefficientBindingContent() -> None:
    first = compareOneCompanyTwoScenarioStrategies(
        "005930",
        (_inputs()),
        (_measured_case("base", ((0.0, 0.0), (0.1, -0.1))), _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2)))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedCoefficient = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (
            _measured_case("base", ((0.0, 0.0), (0.1, -0.1)), fxCoefficient=0.5),
            _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
        ),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedGroup = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (
            _measured_case("base", ((0.0, 0.0), (0.1, -0.1)), aggregationGroup="macro-demand-alt"),
            _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
        ),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedReceipt = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (
            _measured_case("base", ((0.0, 0.0), (0.1, -0.1)), receiptId="5" * 64),
            _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
        ),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert first.loopHash != changedCoefficient.loopHash
    assert first.loopHash != changedGroup.loopHash
    assert first.loopHash != changedReceipt.loopHash


def testOneCompanyScenarioLoopRejectsMeasuredExposureWithoutBinding() -> None:
    base = _measured_case("base", ((0.0, 0.0), (0.1, -0.1)))
    with pytest.raises(ScenarioCompositionError, match="coefficient binding"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (
                replace(base, coefficientBindings=()),
                _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
            ),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testOneCompanyScenarioLoopRejectsTamperedCoefficientBindingContract() -> None:
    base = _measured_case("base", ((0.0, 0.0), (0.1, -0.1)))
    tampered = replace(base.coefficientBindings[0], exposureContractHash="6" * 64)
    with pytest.raises(ScenarioCompositionError, match="exposure contract"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (
                replace(base, coefficientBindings=(tampered,)),
                _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
            ),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testOneCompanyScenarioLoopRequiresTwoCasesAndTwoStrategies() -> None:
    with pytest.raises(ScenarioCompositionError, match="exactly two scenario"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (_case("base", (0.0, 0.0)),),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )
    with pytest.raises(ScenarioCompositionError, match="exactly two strategies"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
            (_strategies()[0],),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testOneCompanyScenarioLoopHashBindsAssumptionAndStrategyContent() -> None:
    first = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedAssumption = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.4, -0.4))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedStrategy = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
        _strategies(investment=30.0),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert first.loopHash != changedAssumption.loopHash
    assert first.loopHash != changedStrategy.loopHash


def testOneCompanyScenarioLoopRejectsDuplicateStrategyIds() -> None:
    hold, _ = _strategies()
    duplicate = buildOperatingStrategy(
        "hold",
        priceChange=(0.0, 0.0),
        capacityInvestment=(10.0, 0.0),
        borrow=(0.0, 0.0),
        repay=(0.0, 0.0),
        refs=("strategy://hold-duplicate",),
    )
    with pytest.raises(ScenarioCompositionError, match="strategy ids"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
            (hold, duplicate),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )
