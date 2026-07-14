from __future__ import annotations

import polars as pl
import pytest

from dartlab.simulate.driverCalibration import (
    DriverCalibrationError,
    DriverCalibrationTarget,
    DriverCoefficientCalibrationSpec,
    calibrationReceiptToOperatingExposure,
    fitDriverCoefficientPit,
)
from dartlab.simulate.driverPaths import DriverCard, DriverFactorSpec, DriverHistorySource
from dartlab.simulate.driverRegistry import DriverRegistryCandidate, compileDriverRegistryPathSet


def _registryResult():
    factor = DriverFactorSpec(
        "fxChange",
        "simpleReturn",
        "quarter",
        "change",
        "fx-change-quarterly-v1",
    )
    card = DriverCard(
        cardId="macro-fx-change",
        sourceKind="history",
        providerId="macro",
        datasetId="macro.fx.quarterly",
        entityId="KR",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        historyStatus="asKnown",
        sourceRefs=("artifact:macro/fx.parquet", "artifactHash:" + "a" * 64),
    )
    panel = pl.DataFrame(
        {
            "eventTime": ["20200331", "20200630", "20200930", "20201231"],
            "availableAt": ["20200401", "20200701", "20201001", "20210101"],
            "fxChange": [0.10, -0.20, 0.30, 0.40],
        }
    )
    return compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "macro-fx",
                "pathHistory",
                DriverHistorySource(card, panel),
                semanticRefs=("semantics:macro-fx-change-path",),
                selectionReason="FX quarterly change is an observable macro path.",
            ),
        ),
        registryId="macro-driver-registry",
        knowledgeAsOf="20210131",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=7,
        minObservations=4,
    )


def _target(evidenceKind: str = "observedOutcome", proxyRef: str = "") -> DriverCalibrationTarget:
    return DriverCalibrationTarget(
        targetVariableId="realizedMarketPriceChange",
        targetShock="marketPriceChange",
        targetUnit="ratioChangePerStep",
        targetEvidenceKind=evidenceKind,
        labelProviderId="gov",
        labelDatasetId="equity.forwardReturn",
        labelSourceRefs=("label:equity-forward-return",),
        historyStatus="asKnown",
        semanticRefs=("semantics:observed-forward-equity-return",),
        targetProxyRef=proxyRef,
    )


def _spec(minOrigins: int = 4) -> DriverCoefficientCalibrationSpec:
    return DriverCoefficientCalibrationSpec(
        calibrationId="fx-to-price-fit",
        sourceVariableId="fxChange",
        minOrigins=minOrigins,
    )


def _frame(**overrides) -> pl.DataFrame:
    values = {
        "originId": ["o1", "o2", "o3", "o4"],
        "originEventTime": ["20200331", "20200630", "20200930", "20201231"],
        "originKnowledgeAsOf": ["20200410", "20200710", "20201010", "20210110"],
        "sourceAvailableAt": ["20200401", "20200701", "20201001", "20210101"],
        "targetEventTime": ["20200630", "20200930", "20201231", "20210331"],
        "targetAvailableAt": ["20200705", "20201005", "20210105", "20210405"],
        "sourceValue": [0.10, -0.20, 0.30, 0.40],
        "targetValue": [0.05, -0.10, 0.15, 0.20],
        "sourceRef": ["source:o1", "source:o2", "source:o3", "source:o4"],
        "labelSourceRef": ["label:o1", "label:o2", "label:o3", "label:o4"],
    }
    values.update(overrides)
    return pl.DataFrame(values)


def testDriverCalibrationIssuesRetrospectiveReceiptAndExposureRef() -> None:
    registryResult = _registryResult()
    receipt = fitDriverCoefficientPit(
        registryResult,
        _target(),
        _frame(),
        _spec(),
        calibrationKnowledgeAsOf="20210430",
    )
    assert receipt.status == "retrospectiveOnly"
    assert receipt.validationStatus == "retrospectiveOnly"
    assert receipt.coefficient == pytest.approx(0.5)
    assert receipt.coefficientUnit == "ratioChangePerStep/simpleReturn"
    assert receipt.registryHash == registryResult.audit.registryHash
    assert receipt.pathSetInputHash == registryResult.audit.pathSetInputHash
    assert receipt.factorContractHash == registryResult.pathSet.audit.factorContractHash
    assert "coefficientRequiresOosAdmission" in receipt.warnings

    exposure = calibrationReceiptToOperatingExposure(receipt, exposureId="fx-price")
    assert exposure.evidenceKind == "measuredAssociation"
    assert exposure.sourceRef == f"driverCoefficientFit:{receipt.receiptHash}"


def testDriverCalibrationBlocksPitCutoffLeaks() -> None:
    with pytest.raises(DriverCalibrationError, match="source availability after origin knowledge"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(),
            _frame(sourceAvailableAt=["20200430", "20200701", "20201001", "20210101"]),
            _spec(),
            calibrationKnowledgeAsOf="20210430",
        )
    with pytest.raises(DriverCalibrationError, match="target label availability after calibration knowledge"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(),
            _frame(targetAvailableAt=["20200705", "20201005", "20210105", "20210505"]),
            _spec(),
            calibrationKnowledgeAsOf="20210430",
        )


def testDriverCalibrationRejectsProxyAssumptionAndWeakSupport() -> None:
    with pytest.raises(DriverCalibrationError, match="observable label"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(evidenceKind="explicitAssumption"),
            _frame(),
            _spec(),
            calibrationKnowledgeAsOf="20210430",
        )
    with pytest.raises(DriverCalibrationError, match="proxy target"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(proxyRef="proxy:revenue-split-to-demand"),
            _frame(),
            _spec(),
            calibrationKnowledgeAsOf="20210430",
        )
    with pytest.raises(DriverCalibrationError, match="support below minOrigins"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(),
            _frame().head(2),
            _spec(minOrigins=4),
            calibrationKnowledgeAsOf="20210430",
        )
