from __future__ import annotations

import pytest

from dartlab.simulate.operatingBridge import (
    OperatingBridgeError,
    OperatingFactorSpec,
    OperatingShockBaseline,
    OperatingTransmissionExposure,
    bridgeOperatingPath,
    sourceFactorContractHash,
)
from dartlab.simulate.operatingWorld import (
    OperatingPrimitive,
    buildOperatingStrategy,
    operatingInputsFromPrimitives,
    runOperatingStrategies,
)
from dartlab.simulate.stateCompiler import CompiledPointInTimeState
from dartlab.simulate.stateSupport import StatePrimitive
from dartlab.simulate.vintage import VintageRef
from dartlab.simulate.world import ScenarioPath


def _sourcePath(**kwargs) -> ScenarioPath:
    values = {
        "pathId": "macro-factor",
        "steps": (
            {"fxChange": 0.10, "demandShock": -0.05, "commodityShock": 0.20},
            {"fxChange": -0.02, "demandShock": 0.03, "commodityShock": -0.10},
        ),
        "refs": ("macro://fx-demand",),
        "frequency": "quarter",
        "knowledgeAsOf": "20250101",
        "historyStatus": "asKnown",
    }
    values.update(kwargs)
    return ScenarioPath(**values)


def _admittedPath() -> ScenarioPath:
    vintage = VintageRef(
        artifactKind="pathSet",
        provider="simulate",
        artifactId="path-set",
        artifactHash="e" * 64,
        payloadHash="f" * 64,
        knowledgeAsOf="20250101",
        availableAt="20241231",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        receiptId="1" * 64,
    )
    return _sourcePath(
        validationStatus="admitted",
        certificateId="2" * 64,
        maxAdmittedStep=2,
        admissionContentHash="a" * 64,
        admissionReceiptId="3" * 64,
        vintage=vintage,
    )


def _factorSpecs() -> tuple[OperatingFactorSpec, ...]:
    return tuple(
        OperatingFactorSpec(name, "simpleReturn", "quarter", "innovation", "simple-return-v1")
        for name in ("fxChange", "demandShock", "commodityShock")
    )


def _baselines() -> tuple[OperatingShockBaseline, ...]:
    return tuple(
        OperatingShockBaseline(
            target,
            0.04 if target == "debtRate" else 0.0,
            "effectiveRatePerStep" if target == "debtRate" else "ratioChangePerStep",
            "observed" if target == "debtRate" else "explicitAssumption",
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


def _state(*, unit: str = "ratio", evidenceRole: str = "observed", role: str = "observedFeature"):
    return (StatePrimitive("business.exportRatio", unit, role, 0.60, evidenceRole=evidenceRole),)


def _exposures(*, evidenceKind: str = "explicitAssumption") -> tuple[OperatingTransmissionExposure, ...]:
    return (
        OperatingTransmissionExposure(
            "fx-price",
            "fxChange",
            "marketPriceChange",
            0.50,
            "ratioChangePerStep/simpleReturn",
            evidenceKind,
            "assumption://fx-price",
            modifierVariableId="business.exportRatio",
            modifierUnit="ratio",
        ),
        OperatingTransmissionExposure(
            "fx-unit-cost",
            "fxChange",
            "unitCostChange",
            0.20,
            "ratioChangePerStep/simpleReturn",
            evidenceKind,
            "assumption://fx-cost",
        ),
        OperatingTransmissionExposure(
            "demand-volume",
            "demandShock",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            evidenceKind,
            "assumption://demand-volume",
        ),
    )


def _compiledState() -> CompiledPointInTimeState:
    return CompiledPointInTimeState(
        stateId="state-id",
        manifestHash="b" * 64,
        registryHash="c" * 64,
        stateContractHash="d" * 64,
        stateCompilationContractHash="e" * 64,
        entityId="005930",
        market="KR",
        decisionAsOf="20250101",
        knowledgeAsOf="20241231",
        statePrimitives=_state(),
        selectedObservationIds=("observation-id",),
        providerBatchIds=("batch-id",),
        providerBatchReceiptIds=("receipt-id",),
        historyStatus="conditional",
        admissionStatus="documented",
        aggregateRevisionPolicy="mixed",
        aggregateCoverage="mixed",
        limitations=("conditionalObservation:business.exportRatio",),
        manifestArtifact=b"{}",
    )


def _bridge(path: ScenarioPath | None = None, **kwargs):
    values = {
        "factorSpecs": _factorSpecs(),
        "baselines": _baselines(),
        "statePrimitives": _state(),
        "stateRef": "pit://state",
    }
    values.update(kwargs)
    return bridgeOperatingPath(path or _sourcePath(), _exposures(), **values)


def testOperatingBridgeMapsFactorsThroughPitModifiersToWorldPath():
    result = _bridge()
    assert result.path.pathId == "operating-macro-factor"
    assert result.path.frequency == "quarter"
    assert result.path.steps[0]["marketPriceChange"] == pytest.approx(0.03)
    assert result.path.steps[0]["unitCostChange"] == pytest.approx(0.02)
    assert result.path.steps[0]["demandChange"] == pytest.approx(-0.05)
    assert result.path.steps[0]["fixedCostChange"] == 0.0
    assert result.path.steps[0]["capacityChange"] == 0.0
    assert result.path.steps[0]["debtRate"] == pytest.approx(0.04)
    assert "bridgeEvidence:explicitAssumption" in result.audit.warnings
    assert "unusedSourceFactor:commodityShock" in result.audit.warnings
    assert "pit://state" in result.path.refs
    assert result.audit.stateContractHash
    assert result.audit.stateContentHash
    assert result.audit.factorContractHash


def testMissingFactorModifierMeaningAndPhysicalBoundsFailClosed():
    missing = _sourcePath(steps=({"demandShock": 0.0},))
    with pytest.raises(OperatingBridgeError, match="factor coverage"):
        _bridge(missing)

    with pytest.raises(OperatingBridgeError, match="modifier unit"):
        _bridge(statePrimitives=_state(unit="percent"))

    with pytest.raises(OperatingBridgeError, match="modifier role"):
        _bridge(statePrimitives=_state(role="metric"))

    dimensionalModifier = OperatingTransmissionExposure(
        "fx-price-dimensional",
        "fxChange",
        "marketPriceChange",
        0.5,
        "ratioChangePerStep/simpleReturn",
        "explicitAssumption",
        "assumption://fx-price-dimensional",
        modifierVariableId="business.exportRatio",
        modifierUnit="USD",
    )
    with pytest.raises(OperatingBridgeError, match="modifier must be dimensionless"):
        bridgeOperatingPath(
            _sourcePath(),
            (dimensionalModifier,),
            factorSpecs=_factorSpecs(),
            baselines=_baselines(),
            statePrimitives=_state(unit="USD"),
            stateRef="pit://state",
        )

    crash = (
        OperatingTransmissionExposure(
            "crash",
            "fxChange",
            "marketPriceChange",
            -20.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            "assumption://crash",
        ),
    )
    with pytest.raises(OperatingBridgeError, match="physical floor"):
        bridgeOperatingPath(
            _sourcePath(),
            crash,
            factorSpecs=_factorSpecs(),
            baselines=_baselines(),
        )


def testCoefficientUnitsAndDuplicateAggregationGroupsFailClosed():
    badUnit = OperatingTransmissionExposure(
        "bad-unit",
        "fxChange",
        "marketPriceChange",
        0.5,
        "ratioPerRatio",
        "explicitAssumption",
        "assumption://bad-unit",
    )
    with pytest.raises(OperatingBridgeError, match="coefficient unit"):
        bridgeOperatingPath(
            _sourcePath(),
            (badUnit,),
            factorSpecs=_factorSpecs(),
            baselines=_baselines(),
        )

    duplicate = OperatingTransmissionExposure(
        "fx-price-2",
        "fxChange",
        "marketPriceChange",
        0.2,
        "ratioChangePerStep/simpleReturn",
        "explicitAssumption",
        "assumption://duplicate",
    )
    with pytest.raises(OperatingBridgeError, match="aggregation groups"):
        bridgeOperatingPath(
            _sourcePath(),
            (_exposures()[0], duplicate),
            factorSpecs=_factorSpecs(),
            baselines=_baselines(),
            statePrimitives=_state(),
            stateRef="pit://state",
        )


def testMeasuredAssociationRequiresDriverCoefficientAdmissionRef():
    manual = OperatingTransmissionExposure(
        "manual-measured",
        "fxChange",
        "marketPriceChange",
        0.5,
        "ratioChangePerStep/simpleReturn",
        "measuredAssociation",
        "fit://fx-price",
    )
    with pytest.raises(OperatingBridgeError, match="driver coefficient admission ref"):
        bridgeOperatingPath(
            _sourcePath(),
            (manual,),
            factorSpecs=_factorSpecs(),
            baselines=_baselines(),
        )


def testMeasuredAssociationRejectsSourceFactorContractDrift():
    drifted = OperatingTransmissionExposure(
        "drifted-measured",
        "fxChange",
        "marketPriceChange",
        0.5,
        "ratioChangePerStep/simpleReturn",
        "measuredAssociation",
        f"driverCoefficientAdmission:{'5' * 64}",
        sourceFrequency="quarter",
        sourceTiming="level",
        sourceTransformId="simple-return-v1",
        sourceFactorContractHash=sourceFactorContractHash(
            variableId="fxChange",
            unit="simpleReturn",
            frequency="quarter",
            timing="level",
            transformId="simple-return-v1",
        ),
    )
    with pytest.raises(OperatingBridgeError, match="source factor contract drift"):
        bridgeOperatingPath(
            _sourcePath(),
            (drifted,),
            factorSpecs=_factorSpecs(),
            baselines=_baselines(),
        )


def testSourceStatusCannotBePromotedOrLaundered():
    admitted = _bridge(_admittedPath())
    assert admitted.path.validationStatus == "retrospectiveOnly"
    assert admitted.audit.sourceAdmissionContentHash == "a" * 64
    assert admitted.audit.sourcePathCertificateId == "2" * 64
    assert admitted.audit.sourceAdmissionReceiptId == "3" * 64
    assert f"sourcePathAdmissionReceipt:{'3' * 64}" in admitted.path.refs
    assert "sourceAdmissionNotTransferredAcrossBridge" in admitted.audit.warnings

    unvalidated = _bridge(_sourcePath(validationStatus="unvalidated"))
    assert unvalidated.path.validationStatus == "unvalidated"

    with pytest.raises(OperatingBridgeError, match="rejected"):
        _bridge(_sourcePath(validationStatus="rejected"))


def testCompiledStateLineageAndLimitationsReachBridgeAudit():
    result = bridgeOperatingPath(
        _sourcePath(),
        _exposures(),
        factorSpecs=_factorSpecs(),
        baselines=_baselines(),
        compiledState=_compiledState(),
    )
    assert "compiledState:state-id" in result.path.refs
    assert "providerBatchReceipt:receipt-id" in result.path.refs
    assert "compiledStateHistory:conditional" in result.audit.warnings
    assert "compiledStateAdmission:documented" in result.audit.warnings
    assert "compiledStateLimitation:conditionalObservation:business.exportRatio" in result.audit.warnings

    with pytest.raises(OperatingBridgeError, match="cannot be mixed"):
        bridgeOperatingPath(
            _sourcePath(),
            _exposures(),
            factorSpecs=_factorSpecs(),
            baselines=_baselines(),
            compiledState=_compiledState(),
            statePrimitives=_state(),
            stateRef="pit://state",
        )


def testLagKernelAndParameterDrawBoundaryRemainVisible():
    lagged = OperatingTransmissionExposure(
        "fx-price-lagged",
        "fxChange",
        "marketPriceChange",
        0.5,
        "ratioChangePerStep/simpleReturn",
        "measuredAssociation",
        f"driverCoefficientAdmission:{'4' * 64}",
        lagSteps=1,
        responseKernel=(1.0, 0.5),
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
    )
    result = bridgeOperatingPath(
        _sourcePath(parameterDraws={"betaDraw": 0.7}),
        (lagged,),
        factorSpecs=_factorSpecs(),
        baselines=_baselines(),
    )
    assert result.path.steps[0]["marketPriceChange"] == 0.0
    assert result.path.steps[1]["marketPriceChange"] == pytest.approx(0.05)
    assert not result.path.parameterDraws
    assert result.path.parameterDrawReceipt is None
    assert "truncatedResponseTail:fx-price-lagged" in result.audit.warnings
    assert "sourceParameterDrawsNotTransferred" in result.audit.warnings


def testOperatingBridgeOutputRunsThroughOperatingWorldStrategyComparison():
    path = _bridge().path
    inputs = operatingInputsFromPrimitives(
        (
            OperatingPrimitive("price", 10.0, "currencyPerUnit", "explicitAssumption", "assumption://price"),
            OperatingPrimitive("demandVolume", 100.0, "units", "explicitAssumption", "assumption://volume"),
            OperatingPrimitive("unitCost", 6.0, "currencyPerUnit", "explicitAssumption", "assumption://cost"),
            OperatingPrimitive("fixedCost", 100.0, "currency", "explicitAssumption", "assumption://fixed"),
            OperatingPrimitive("capacityUnits", 120.0, "units", "explicitAssumption", "assumption://capacity"),
            OperatingPrimitive("cash", 100.0, "currency", "observed", "filing://cash"),
            OperatingPrimitive("debt", 20.0, "currency", "observed", "filing://debt"),
        ),
        asOf="2025Q4",
        priceElasticity=0.0,
        capacityUnitsPerCurrency=1.0,
    )
    strategy = buildOperatingStrategy(
        "hold",
        priceChange=(0.0, 0.0),
        capacityInvestment=(0.0, 0.0),
        borrow=(0.0, 0.0),
        repay=(0.0, 0.0),
        refs=("strategy://hold",),
        isBaseline=True,
    )
    run = runOperatingStrategies(
        inputs,
        (path,),
        (strategy,),
        debtLimit=100.0,
        maxFinancing=10.0,
        maxInvestment=10.0,
    )
    first = run.traces[0].steps[0]
    assert first.after["price"] == pytest.approx(10.3)
    assert first.after["unitCost"] == pytest.approx(6.12)
    assert first.after["soldVolume"] == pytest.approx(95.0)
    assert run.decisionStatus == "conditionalOnly"
