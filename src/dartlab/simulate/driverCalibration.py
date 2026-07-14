"""Fit PIT driver coefficients without granting path or policy admission.

This module is the measured-law boundary between a registered source factor
and an operating shock target. It accepts an already compiled driver registry
result plus an origin-level calibration frame, fits only observable forward
labels, and returns a receipt that can be referenced by an operating exposure.
It does not admit paths, transfer calibrated weights, or recommend policies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import polars as pl

from dartlab.simulate.driverRegistry import DriverRegistryResult
from dartlab.simulate.operatingBridge import (
    OPERATING_TARGET_UNITS,
    OperatingTransmissionExposure,
)
from dartlab.simulate.vintage import canonicalPayloadHash

CALIBRATION_VERSION = "driver-coefficient-calibration-v1"
_OBSERVABLE_TARGET_KINDS = {"observedOutcome", "realizedOutcome", "observedOperatingShock"}
_CALIBRATION_METHODS = {"olsThroughOrigin"}


class DriverCalibrationError(ValueError):
    """Raised when a PIT coefficient calibration contract is unsafe or incomplete."""


@dataclass(frozen=True)
class DriverCalibrationTarget:
    """Observed target label contract for one coefficient fit."""

    targetVariableId: str
    targetShock: str
    targetUnit: str
    targetEvidenceKind: str
    labelProviderId: str
    labelDatasetId: str
    labelSourceRefs: tuple[str, ...]
    historyStatus: str
    semanticRefs: tuple[str, ...] = ()
    targetProxyRef: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "labelSourceRefs", tuple(self.labelSourceRefs))
        object.__setattr__(self, "semanticRefs", tuple(self.semanticRefs))


@dataclass(frozen=True)
class DriverCoefficientCalibrationSpec:
    """PIT origin-grid and model contract for one source to target coefficient."""

    calibrationId: str
    sourceVariableId: str
    minOrigins: int
    lagSteps: int = 0
    responseKernel: tuple[float, ...] = (1.0,)
    method: str = "olsThroughOrigin"
    fitIntercept: bool = False
    originIdColumn: str = "originId"
    originEventTimeColumn: str = "originEventTime"
    originKnowledgeAsOfColumn: str = "originKnowledgeAsOf"
    sourceAvailableAtColumn: str = "sourceAvailableAt"
    targetEventTimeColumn: str = "targetEventTime"
    targetAvailableAtColumn: str = "targetAvailableAt"
    sourceValueColumn: str = "sourceValue"
    targetValueColumn: str = "targetValue"
    sourceRefColumn: str = "sourceRef"
    labelSourceRefColumn: str = "labelSourceRef"

    def __post_init__(self) -> None:
        object.__setattr__(self, "responseKernel", tuple(self.responseKernel))


@dataclass(frozen=True)
class DriverCoefficientTraceRow:
    """One origin used by a coefficient fit and its residual trace."""

    originId: str
    originEventTime: str
    originKnowledgeAsOf: str
    sourceAvailableAt: str
    targetEventTime: str
    targetAvailableAt: str
    sourceValue: float
    targetValue: float
    fittedValue: float
    residual: float
    sourceRef: str
    labelSourceRef: str


@dataclass(frozen=True)
class DriverCoefficientCalibrationReceipt:
    """Fit receipt for one measured association coefficient."""

    calibrationId: str
    receiptId: str
    receiptHash: str
    generatorVersion: str
    status: str
    validationStatus: str
    historyStatus: str
    calibrationKnowledgeAsOf: str
    sourceVariableId: str
    targetVariableId: str
    targetShock: str
    sourceUnit: str
    targetUnit: str
    coefficient: float
    coefficientUnit: str
    intercept: float
    standardError: float
    rSquared: float
    nOrigins: int
    droppedRows: int
    fitStart: str
    fitThrough: str
    labelThrough: str
    lagSteps: int
    responseKernel: tuple[float, ...]
    modelFormula: str
    registryHash: str
    pathSetHash: str
    pathSetInputHash: str
    factorContractHash: str
    calibrationSpecHash: str
    originGridHash: str
    targetOutcomeHash: str
    coefficientTraceHash: str
    warnings: tuple[str, ...]
    sourceRefs: tuple[str, ...]
    traceRows: tuple[DriverCoefficientTraceRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "responseKernel", tuple(self.responseKernel))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))
        object.__setattr__(self, "traceRows", tuple(self.traceRows))


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise DriverCalibrationError(f"invalid {label}: {value}")
    return text


def _finite(value: float | None, label: str) -> float:
    if value is None:
        raise DriverCalibrationError(f"{label} is missing")
    number = float(value)
    if not math.isfinite(number):
        raise DriverCalibrationError(f"{label} must be finite")
    return number


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _validateTarget(target: DriverCalibrationTarget) -> None:
    if (
        not target.targetVariableId
        or target.targetShock not in OPERATING_TARGET_UNITS
        or target.targetUnit != OPERATING_TARGET_UNITS[target.targetShock]
        or not target.labelProviderId
        or not target.labelDatasetId
        or not target.labelSourceRefs
        or not target.historyStatus
    ):
        raise DriverCalibrationError("calibration target contract is incomplete")
    if target.targetEvidenceKind not in _OBSERVABLE_TARGET_KINDS:
        raise DriverCalibrationError("coefficient calibration target must be an observable label")
    if target.targetProxyRef:
        raise DriverCalibrationError("proxy target labels cannot fit operating coefficients")


def _validateSpec(spec: DriverCoefficientCalibrationSpec) -> None:
    if (
        not spec.calibrationId
        or not spec.sourceVariableId
        or spec.minOrigins < 2
        or spec.lagSteps < 0
        or not spec.responseKernel
        or spec.method not in _CALIBRATION_METHODS
    ):
        raise DriverCalibrationError("coefficient calibration spec is incomplete")
    if spec.fitIntercept:
        raise DriverCalibrationError("coefficient calibration intercept must remain in explicit baselines")
    kernel = tuple(_finite(value, f"responseKernel.{index}") for index, value in enumerate(spec.responseKernel))
    if all(abs(value) <= 1e-15 for value in kernel):
        raise DriverCalibrationError("coefficient calibration response kernel is zero")


def _sourceFactor(registryResult: DriverRegistryResult, variableId: str):
    matches = tuple(factor for factor in registryResult.pathSet.factorSpecs if factor.variableId == variableId)
    if len(matches) != 1:
        raise DriverCalibrationError(f"source variable must match one registry factor: {variableId}")
    return matches[0]


def _requiredColumns(spec: DriverCoefficientCalibrationSpec) -> set[str]:
    return {
        spec.originIdColumn,
        spec.originEventTimeColumn,
        spec.originKnowledgeAsOfColumn,
        spec.sourceAvailableAtColumn,
        spec.targetEventTimeColumn,
        spec.targetAvailableAtColumn,
        spec.sourceValueColumn,
        spec.targetValueColumn,
        spec.sourceRefColumn,
        spec.labelSourceRefColumn,
    }


def _cleanCalibrationRows(
    frame: pl.DataFrame,
    spec: DriverCoefficientCalibrationSpec,
    *,
    calibrationKnowledgeAsOf: str,
) -> tuple[tuple[dict, ...], str, str, str]:
    missing = _requiredColumns(spec) - set(frame.columns)
    if missing:
        raise DriverCalibrationError(f"calibration frame missing columns: {sorted(missing)}")
    cutoff = _dateText(calibrationKnowledgeAsOf, "calibrationKnowledgeAsOf")
    rows: list[dict] = []
    for index, raw in enumerate(frame.to_dicts()):
        originId = str(raw[spec.originIdColumn])
        sourceRef = str(raw[spec.sourceRefColumn])
        labelSourceRef = str(raw[spec.labelSourceRefColumn])
        if not originId or not sourceRef or not labelSourceRef:
            raise DriverCalibrationError(f"calibration row needs origin and refs: {index}")
        originEventTime = _dateText(raw[spec.originEventTimeColumn], "originEventTime")
        originKnowledgeAsOf = _dateText(raw[spec.originKnowledgeAsOfColumn], "originKnowledgeAsOf")
        sourceAvailableAt = _dateText(raw[spec.sourceAvailableAtColumn], "sourceAvailableAt")
        targetEventTime = _dateText(raw[spec.targetEventTimeColumn], "targetEventTime")
        targetAvailableAt = _dateText(raw[spec.targetAvailableAtColumn], "targetAvailableAt")
        if originKnowledgeAsOf > cutoff:
            raise DriverCalibrationError("origin knowledge is after calibration knowledge")
        if sourceAvailableAt > originKnowledgeAsOf:
            raise DriverCalibrationError("source availability after origin knowledge")
        if targetEventTime <= originEventTime:
            raise DriverCalibrationError("target event must be after origin event")
        if targetAvailableAt <= originKnowledgeAsOf:
            raise DriverCalibrationError("target label is not a forward outcome")
        if targetAvailableAt > cutoff:
            raise DriverCalibrationError("target label availability after calibration knowledge")
        rows.append(
            {
                "originId": originId,
                "originEventTime": originEventTime,
                "originKnowledgeAsOf": originKnowledgeAsOf,
                "sourceAvailableAt": sourceAvailableAt,
                "targetEventTime": targetEventTime,
                "targetAvailableAt": targetAvailableAt,
                "sourceValue": _finite(raw[spec.sourceValueColumn], f"sourceValue.{index}"),
                "targetValue": _finite(raw[spec.targetValueColumn], f"targetValue.{index}"),
                "sourceRef": sourceRef,
                "labelSourceRef": labelSourceRef,
            }
        )
    rows.sort(key=lambda item: (item["originEventTime"], item["originId"]))
    originIds = tuple(item["originId"] for item in rows)
    if len(set(originIds)) != len(originIds):
        raise DriverCalibrationError("calibration origin ids must be unique")
    if not rows:
        raise DriverCalibrationError("calibration frame needs origins")
    return (
        tuple(rows),
        rows[0]["originEventTime"],
        rows[-1]["originEventTime"],
        max(item["targetAvailableAt"] for item in rows),
    )


def _fitThroughOrigin(rows: tuple[dict, ...]) -> tuple[float, float, float, tuple[DriverCoefficientTraceRow, ...]]:
    denominator = sum(item["sourceValue"] * item["sourceValue"] for item in rows)
    if denominator <= 1e-24:
        raise DriverCalibrationError("source values have no calibratable variance")
    coefficient = sum(item["sourceValue"] * item["targetValue"] for item in rows) / denominator
    traceRows = []
    residualSum = 0.0
    targets = [item["targetValue"] for item in rows]
    targetMean = sum(targets) / len(targets)
    targetTotal = sum((value - targetMean) ** 2 for value in targets)
    for item in rows:
        fitted = coefficient * item["sourceValue"]
        residual = item["targetValue"] - fitted
        residualSum += residual * residual
        traceRows.append(
            DriverCoefficientTraceRow(
                originId=item["originId"],
                originEventTime=item["originEventTime"],
                originKnowledgeAsOf=item["originKnowledgeAsOf"],
                sourceAvailableAt=item["sourceAvailableAt"],
                targetEventTime=item["targetEventTime"],
                targetAvailableAt=item["targetAvailableAt"],
                sourceValue=item["sourceValue"],
                targetValue=item["targetValue"],
                fittedValue=fitted,
                residual=residual,
                sourceRef=item["sourceRef"],
                labelSourceRef=item["labelSourceRef"],
            )
        )
    standardError = math.sqrt((residualSum / max(len(rows) - 1, 1)) / denominator)
    rSquared = 1.0 if targetTotal <= 1e-24 and residualSum <= 1e-24 else 1.0 - residualSum / targetTotal
    return coefficient, standardError, rSquared, tuple(traceRows)


def fitDriverCoefficientPit(
    registryResult: DriverRegistryResult,
    target: DriverCalibrationTarget,
    frame: pl.DataFrame,
    spec: DriverCoefficientCalibrationSpec,
    *,
    calibrationKnowledgeAsOf: str,
) -> DriverCoefficientCalibrationReceipt:
    """Fit a PIT source to observable target coefficient receipt.

    Args:
        registryResult: Compiled driver registry result that owns the source factor contract.
        target: Observable target label contract. Proxy or assumption labels are rejected.
        frame: Origin-level calibration rows with source and target availability dates.
        spec: Source variable, model, row-column, lag, and minimum-origin contract.
        calibrationKnowledgeAsOf: Date when the fit is allowed to know labels.

    Returns:
        ``DriverCoefficientCalibrationReceipt`` with a retrospective measured association.

    Raises:
        DriverCalibrationError: If target labels, PIT cutoffs, units, support, or source contracts fail.

    Example:
        ``receipt = fitDriverCoefficientPit(registryResult, target, frame, spec, calibrationKnowledgeAsOf="20251231")``
    """

    _validateTarget(target)
    _validateSpec(spec)
    cutoff = _dateText(calibrationKnowledgeAsOf, "calibrationKnowledgeAsOf")
    sourceFactor = _sourceFactor(registryResult, spec.sourceVariableId)
    coefficientUnit = f"{target.targetUnit}/{sourceFactor.unit}"
    rows, fitStart, fitThrough, labelThrough = _cleanCalibrationRows(
        frame,
        spec,
        calibrationKnowledgeAsOf=cutoff,
    )
    if len(rows) < spec.minOrigins:
        raise DriverCalibrationError("coefficient calibration support below minOrigins")
    coefficient, standardError, rSquared, traceRows = _fitThroughOrigin(rows)
    calibrationSpecHash = canonicalPayloadHash(
        {
            "version": CALIBRATION_VERSION,
            "spec": spec,
            "target": target,
            "sourceUnit": sourceFactor.unit,
            "coefficientUnit": coefficientUnit,
        }
    )
    originGridHash = canonicalPayloadHash(
        tuple(
            {
                "originId": item["originId"],
                "originEventTime": item["originEventTime"],
                "originKnowledgeAsOf": item["originKnowledgeAsOf"],
                "sourceAvailableAt": item["sourceAvailableAt"],
                "targetEventTime": item["targetEventTime"],
                "targetAvailableAt": item["targetAvailableAt"],
            }
            for item in rows
        )
    )
    targetOutcomeHash = canonicalPayloadHash(
        {
            "target": target,
            "labels": tuple(
                {
                    "originId": item["originId"],
                    "targetValue": item["targetValue"],
                    "targetEventTime": item["targetEventTime"],
                    "targetAvailableAt": item["targetAvailableAt"],
                    "labelSourceRef": item["labelSourceRef"],
                }
                for item in rows
            ),
        }
    )
    coefficientTraceHash = canonicalPayloadHash(
        {
            "registryHash": registryResult.audit.registryHash,
            "pathSetHash": registryResult.audit.pathSetHash,
            "pathSetInputHash": registryResult.audit.pathSetInputHash,
            "factorContractHash": registryResult.pathSet.audit.factorContractHash,
            "calibrationSpecHash": calibrationSpecHash,
            "originGridHash": originGridHash,
            "targetOutcomeHash": targetOutcomeHash,
            "coefficient": coefficient,
            "standardError": standardError,
            "rSquared": rSquared,
            "traceRows": traceRows,
        }
    )
    warnings = [
        "coefficientCalibrationNotAdmitted",
        "coefficientRequiresOosAdmission",
        f"registryValidation:{registryResult.audit.validationStatus}",
    ]
    warnings.extend(f"registryWarning:{warning}" for warning in registryResult.audit.warnings)
    if registryResult.audit.historyStatus != "asKnown" or target.historyStatus != "asKnown":
        warnings.append("calibrationContainsRevisedHistory")
    if registryResult.audit.warnings:
        warnings.append("calibrationContainsSourceWarnings")
    historyStatus = (
        "asKnown"
        if registryResult.audit.historyStatus == "asKnown" and target.historyStatus == "asKnown"
        else "revisedHistory"
    )
    baseRefs = _dedupe(
        (
            *registryResult.audit.sourceRefs,
            *registryResult.audit.semanticRefs,
            *target.labelSourceRefs,
            *(item.sourceRef for item in traceRows),
            *(item.labelSourceRef for item in traceRows),
            f"registryHash:{registryResult.audit.registryHash}",
            f"pathSetHash:{registryResult.audit.pathSetHash}",
            f"pathSetInputHash:{registryResult.audit.pathSetInputHash}",
            f"factorContractHash:{registryResult.pathSet.audit.factorContractHash}",
            f"calibrationSpec:{calibrationSpecHash}",
            f"originGrid:{originGridHash}",
            f"targetOutcome:{targetOutcomeHash}",
            f"coefficientTrace:{coefficientTraceHash}",
        )
    )
    receiptPayload = {
        "version": CALIBRATION_VERSION,
        "calibrationId": spec.calibrationId,
        "status": "retrospectiveOnly",
        "validationStatus": "retrospectiveOnly",
        "historyStatus": historyStatus,
        "calibrationKnowledgeAsOf": cutoff,
        "sourceVariableId": spec.sourceVariableId,
        "targetVariableId": target.targetVariableId,
        "targetShock": target.targetShock,
        "sourceUnit": sourceFactor.unit,
        "targetUnit": target.targetUnit,
        "coefficient": coefficient,
        "coefficientUnit": coefficientUnit,
        "intercept": 0.0,
        "standardError": standardError,
        "rSquared": rSquared,
        "nOrigins": len(rows),
        "droppedRows": 0,
        "fitStart": fitStart,
        "fitThrough": fitThrough,
        "labelThrough": labelThrough,
        "lagSteps": spec.lagSteps,
        "responseKernel": spec.responseKernel,
        "modelFormula": f"{target.targetVariableId} = coefficient * {spec.sourceVariableId}",
        "registryHash": registryResult.audit.registryHash,
        "pathSetHash": registryResult.audit.pathSetHash,
        "pathSetInputHash": registryResult.audit.pathSetInputHash,
        "factorContractHash": registryResult.pathSet.audit.factorContractHash,
        "calibrationSpecHash": calibrationSpecHash,
        "originGridHash": originGridHash,
        "targetOutcomeHash": targetOutcomeHash,
        "coefficientTraceHash": coefficientTraceHash,
        "warnings": tuple(sorted(set(warnings))),
        "sourceRefs": baseRefs,
    }
    receiptHash = canonicalPayloadHash(receiptPayload)
    sourceRefs = _dedupe((*baseRefs, f"driverCoefficientFit:{receiptHash}"))
    return DriverCoefficientCalibrationReceipt(
        calibrationId=spec.calibrationId,
        receiptId=receiptHash,
        receiptHash=receiptHash,
        generatorVersion=CALIBRATION_VERSION,
        status="retrospectiveOnly",
        validationStatus="retrospectiveOnly",
        historyStatus=historyStatus,
        calibrationKnowledgeAsOf=cutoff,
        sourceVariableId=spec.sourceVariableId,
        targetVariableId=target.targetVariableId,
        targetShock=target.targetShock,
        sourceUnit=sourceFactor.unit,
        targetUnit=target.targetUnit,
        coefficient=coefficient,
        coefficientUnit=coefficientUnit,
        intercept=0.0,
        standardError=standardError,
        rSquared=rSquared,
        nOrigins=len(rows),
        droppedRows=0,
        fitStart=fitStart,
        fitThrough=fitThrough,
        labelThrough=labelThrough,
        lagSteps=spec.lagSteps,
        responseKernel=spec.responseKernel,
        modelFormula=f"{target.targetVariableId} = coefficient * {spec.sourceVariableId}",
        registryHash=registryResult.audit.registryHash,
        pathSetHash=registryResult.audit.pathSetHash,
        pathSetInputHash=registryResult.audit.pathSetInputHash,
        factorContractHash=registryResult.pathSet.audit.factorContractHash,
        calibrationSpecHash=calibrationSpecHash,
        originGridHash=originGridHash,
        targetOutcomeHash=targetOutcomeHash,
        coefficientTraceHash=coefficientTraceHash,
        warnings=tuple(sorted(set(warnings))),
        sourceRefs=sourceRefs,
        traceRows=traceRows,
    )


def calibrationReceiptToOperatingExposure(
    receipt: DriverCoefficientCalibrationReceipt,
    *,
    exposureId: str,
    modifierVariableId: str = "",
    modifierUnit: str = "",
    aggregationGroup: str = "",
) -> OperatingTransmissionExposure:
    """Convert a coefficient receipt into a measured-association exposure.

    Args:
        receipt: Non-rejected calibration receipt returned by ``fitDriverCoefficientPit``.
        exposureId: Stable exposure identifier for the operating bridge.
        modifierVariableId: Optional PIT state primitive that scales the coefficient.
        modifierUnit: Required unit when a modifier is present.
        aggregationGroup: Optional duplicate source-target aggregation group.

    Returns:
        ``OperatingTransmissionExposure`` with sourceRef bound to the receipt hash.

    Raises:
        DriverCalibrationError: If the receipt is rejected or no longer matches target units.

    Example:
        ``exposure = calibrationReceiptToOperatingExposure(receipt, exposureId="fx-price")``
    """

    if receipt.status == "rejected" or receipt.validationStatus == "rejected":
        raise DriverCalibrationError("rejected coefficient receipt cannot become an exposure")
    expectedUnit = f"{OPERATING_TARGET_UNITS[receipt.targetShock]}/{receipt.sourceUnit}"
    if receipt.coefficientUnit != expectedUnit:
        raise DriverCalibrationError("coefficient receipt unit drift")
    _finite(receipt.coefficient, "receipt.coefficient")
    return OperatingTransmissionExposure(
        exposureId=exposureId,
        sourceVariableId=receipt.sourceVariableId,
        targetShock=receipt.targetShock,
        coefficient=receipt.coefficient,
        coefficientUnit=receipt.coefficientUnit,
        evidenceKind="measuredAssociation",
        sourceRef=f"driverCoefficientFit:{receipt.receiptHash}",
        modifierVariableId=modifierVariableId,
        modifierUnit=modifierUnit,
        lagSteps=receipt.lagSteps,
        responseKernel=receipt.responseKernel,
        aggregationGroup=aggregationGroup,
    )
