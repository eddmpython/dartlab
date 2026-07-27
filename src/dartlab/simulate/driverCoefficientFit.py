"""스칼라 계수 적합. origin 격자 정제와 원점 통과 최소자승.

적합은 "관측된 forward label 만으로 계수 하나를 재는" 단계다. 판정(OOS) 과 승인은
적합된 계수를 고정한 뒤에 오므로, 적합에 그 둘을 섞으면 fit 창이 판정 창을 볼 수
있게 된다. 그 누수를 구조로 막으려고 단계마다 모듈을 끊는다.
"""

from __future__ import annotations

import math

import polars as pl

from dartlab.simulate.driverCalibrationContracts import (
    _BENIGN_REGISTRY_WARNINGS,
    _CALIBRATION_METHODS,
    CALIBRATION_VERSION,
    DriverCalibrationError,
    DriverCalibrationTarget,
    DriverCoefficientCalibrationReceipt,
    DriverCoefficientCalibrationSpec,
    DriverCoefficientTraceRow,
    DriverObservationFrameBinding,
)
from dartlab.simulate.driverCalibrationKernel import (
    _dateText,
    _dedupe,
    _driverSourceFactorContractHash,
    _finite,
    _sourceFactor,
    _validateReceiptIds,
    _validateTarget,
)
from dartlab.simulate.driverCoefficientFrameBinding import (
    _frameBindingFromObservationFrame,
    _validateFrameBinding,
)
from dartlab.simulate.driverObservationFrames import DriverCoefficientObservationFrame
from dartlab.simulate.driverRegistry import DriverRegistryResult
from dartlab.simulate.vintage import canonicalPayloadHash


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
    _validateReceiptIds(spec.sourceParentReceiptIds, "source parent")


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
    fitFrameBinding: DriverObservationFrameBinding | None = None,
) -> DriverCoefficientCalibrationReceipt:
    """Fit a PIT source to observable target coefficient receipt.

    Args:
        registryResult: Compiled driver registry result that owns the source factor contract.
        target: Observable target label contract. Proxy or assumption labels are rejected.
        frame: Origin-level calibration rows with source and target availability dates.
        spec: Source variable, model, row-column, lag, and minimum-origin contract.
        calibrationKnowledgeAsOf: Date when the fit is allowed to know labels.
        fitFrameBinding: Optional replayable signed provider observation frame binding.

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
    sourceFactorHash = _driverSourceFactorContractHash(
        variableId=sourceFactor.variableId,
        unit=sourceFactor.unit,
        frequency=sourceFactor.frequency,
        timing=sourceFactor.timing,
        transformId=sourceFactor.transformId,
    )
    coefficientUnit = f"{target.targetUnit}/{sourceFactor.unit}"
    rows, fitStart, fitThrough, labelThrough = _cleanCalibrationRows(
        frame,
        spec,
        calibrationKnowledgeAsOf=cutoff,
    )
    if fitFrameBinding is not None:
        _validateFrameBinding(fitFrameBinding, "fit")
        if (
            fitFrameBinding.rowCount != len(rows)
            or fitFrameBinding.sourceBatchReceiptId not in spec.sourceParentReceiptIds
            or fitFrameBinding.labelBatchReceiptId not in target.labelParentReceiptIds
            or fitFrameBinding.sourceVariableId != spec.sourceVariableId
            or fitFrameBinding.targetVariableId != target.targetVariableId
            or fitFrameBinding.sourceUnit != sourceFactor.unit
            or fitFrameBinding.targetUnit != target.targetUnit
        ):
            raise DriverCalibrationError("coefficient fit observation frame binding mismatch")
    if len(rows) < spec.minOrigins:
        raise DriverCalibrationError("coefficient calibration support below minOrigins")
    coefficient, standardError, rSquared, traceRows = _fitThroughOrigin(rows)
    calibrationSpecHash = canonicalPayloadHash(
        {
            "version": CALIBRATION_VERSION,
            "spec": spec,
            "target": target,
            "sourceUnit": sourceFactor.unit,
            "sourceFrequency": sourceFactor.frequency,
            "sourceTiming": sourceFactor.timing,
            "sourceTransformId": sourceFactor.transformId,
            "sourceFactorContractHash": sourceFactorHash,
            "coefficientUnit": coefficientUnit,
            "sourceParentReceiptIds": spec.sourceParentReceiptIds,
            "labelParentReceiptIds": target.labelParentReceiptIds,
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
    if any(warning not in _BENIGN_REGISTRY_WARNINGS for warning in registryResult.audit.warnings):
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
            f"fitFrame:{fitFrameBinding.frameHash}" if fitFrameBinding is not None else "",
            f"fitFrameSpec:{fitFrameBinding.specHash}" if fitFrameBinding is not None else "",
            *(f"fitSourceParentReceipt:{receiptId}" for receiptId in spec.sourceParentReceiptIds),
            *(f"fitLabelParentReceipt:{receiptId}" for receiptId in target.labelParentReceiptIds),
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
        "sourceFrequency": sourceFactor.frequency,
        "sourceTiming": sourceFactor.timing,
        "sourceTransformId": sourceFactor.transformId,
        "sourceFactorContractHash": sourceFactorHash,
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
        "sourceParentReceiptIds": spec.sourceParentReceiptIds,
        "labelParentReceiptIds": target.labelParentReceiptIds,
        "fitFrameBinding": fitFrameBinding,
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
        sourceFrequency=sourceFactor.frequency,
        sourceTiming=sourceFactor.timing,
        sourceTransformId=sourceFactor.transformId,
        sourceFactorContractHash=sourceFactorHash,
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
        sourceParentReceiptIds=spec.sourceParentReceiptIds,
        labelParentReceiptIds=target.labelParentReceiptIds,
        traceRows=traceRows,
        fitFrameBinding=fitFrameBinding,
    )


def fitDriverCoefficientPitFromObservationFrame(
    registryResult: DriverRegistryResult,
    target: DriverCalibrationTarget,
    observationFrame: DriverCoefficientObservationFrame,
    spec: DriverCoefficientCalibrationSpec,
    *,
    calibrationKnowledgeAsOf: str,
) -> DriverCoefficientCalibrationReceipt:
    """Fit a coefficient only from a typed signed provider observation frame.

    Args:
        registryResult: Compiled source factor registry result.
        target: Observable target label contract whose parents match the frame.
        observationFrame: Typed provider observation frame built from signed exact batches.
        spec: Source variable, model, lag, and minimum-origin contract.
        calibrationKnowledgeAsOf: Date when the fit may know labels.

    Returns:
        ``DriverCoefficientCalibrationReceipt`` carrying replayable fit frame binding.

    Raises:
        DriverCalibrationError: If the frame parents or meaning drift from the fit contract.

    Example:
        ``receipt = fitDriverCoefficientPitFromObservationFrame(registry, target, frame, spec, calibrationKnowledgeAsOf="20251231")``
    """

    binding = _frameBindingFromObservationFrame(observationFrame)
    if (
        observationFrame.sourceParentReceiptIds != spec.sourceParentReceiptIds
        or observationFrame.labelParentReceiptIds != target.labelParentReceiptIds
    ):
        raise DriverCalibrationError("coefficient observation frame parent contract mismatch")
    return fitDriverCoefficientPit(
        registryResult,
        target,
        observationFrame.frame,
        spec,
        calibrationKnowledgeAsOf=calibrationKnowledgeAsOf,
        fitFrameBinding=binding,
    )
