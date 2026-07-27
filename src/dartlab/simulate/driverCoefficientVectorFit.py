"""벡터 계수 적합. 설계행렬 정제와 원점 통과 다변량 최소자승.

스칼라 적합의 쌍이지만 계산이 다르다. 여기서만 정규방정식을 세우고 소거로 풀며,
rank 결손을 계수 대신 오류로 되돌린다. 설계 프레임 칼럼 이름 helper 는
`driverObservationFrames` 의 것을 그대로 쓴다 (같은 격자를 두 벌 정의하지 않는다).
"""

from __future__ import annotations

import math

import polars as pl

from dartlab.simulate.driverCalibrationContracts import (
    _BENIGN_REGISTRY_WARNINGS,
    _CALIBRATION_METHODS,
    _OBSERVATION_FACTOR_TIMING_COMPATIBILITY,
    MULTIVARIABLE_CALIBRATION_VERSION,
    DriverCalibrationError,
    DriverCalibrationTarget,
    DriverDesignColumnSpec,
    MultivariableDriverCoefficientCalibrationReceipt,
    MultivariableDriverCoefficientCalibrationSpec,
    MultivariableDriverCoefficientOosSpec,
    MultivariableDriverCoefficientTerm,
    MultivariableDriverCoefficientTraceRow,
    MultivariableDriverDesignFrameBinding,
    MultivariableDriverSourceCell,
)
from dartlab.simulate.driverCalibrationKernel import (
    _dateText,
    _dedupe,
    _driverSourceFactorContractHash,
    _finite,
    _sourceFactor,
    _validateOosHorizon,
    _validateReceiptIds,
    _validateTarget,
)
from dartlab.simulate.driverCoefficientFrameBinding import (
    _designFrameBindingFromObservationFrame,
    _validateDesignFrameBinding,
)
from dartlab.simulate.driverCoefficientVectorReceipt import (
    _coefficientVectorHash,
    _featureSpecHash,
    _multivariableCalibrationReceiptPayload,
    _multivariableCoefficientTraceHash,
    _multivariableOriginGridHashFromTraceRows,
    _multivariableOutcomeHashFromTraceRows,
    _validateMultivariableCalibrationReceipt,
)
from dartlab.simulate.driverObservationFrames import (
    MultivariableDriverCoefficientObservationFrame,
    _sourceAvailableColumn,
    _sourceEventColumn,
    _sourceKnowledgeColumn,
    _sourceRefColumn,
    _sourceValueColumn,
)
from dartlab.simulate.driverRegistry import DriverRegistryResult
from dartlab.simulate.vintage import canonicalPayloadHash


def _validateMultivariableSpec(spec: MultivariableDriverCoefficientCalibrationSpec) -> None:
    if (
        not spec.calibrationId
        or not spec.sourceVariableIds
        or len(set(spec.sourceVariableIds)) != len(spec.sourceVariableIds)
        or spec.minOrigins < max(2, len(spec.sourceVariableIds))
        or spec.lagSteps < 0
        or not spec.responseKernel
        or spec.method not in _CALIBRATION_METHODS
    ):
        raise DriverCalibrationError("coefficient vector calibration spec is incomplete")
    if spec.fitIntercept:
        raise DriverCalibrationError("coefficient vector intercept must remain in explicit baselines")
    kernel = tuple(_finite(value, f"responseKernel.{index}") for index, value in enumerate(spec.responseKernel))
    if all(abs(value) <= 1e-15 for value in kernel):
        raise DriverCalibrationError("coefficient vector response kernel is zero")
    _validateReceiptIds(spec.sourceParentReceiptIds, "vector source parent")


def _multivariableSourceFactors(
    registryResult: DriverRegistryResult,
    sourceVariableIds: tuple[str, ...],
) -> dict[str, object]:
    pairs = tuple((variableId, _sourceFactor(registryResult, variableId)) for variableId in sourceVariableIds)
    factors = {variableId: factor for variableId, factor in pairs}
    if tuple(factors) != sourceVariableIds:
        raise DriverCalibrationError("coefficient vector source factor order mismatch")
    return factors


def _featureTermsFromFactors(
    sourceColumns: tuple[DriverDesignColumnSpec, ...],
    factorsById: dict[str, object],
    targetUnit: str,
    coefficients: tuple[float, ...],
) -> tuple[MultivariableDriverCoefficientTerm, ...]:
    terms = []
    for index, (column, coefficient) in enumerate(zip(sourceColumns, coefficients)):
        factor = factorsById.get(column.variableId)
        if factor is None:
            raise DriverCalibrationError(f"coefficient vector source factor is missing: {column.variableId}")
        compatibleTiming = _OBSERVATION_FACTOR_TIMING_COMPATIBILITY.get(factor.timing, set())
        if (
            factor.unit != column.unit
            or factor.frequency != column.frequency
            or factor.transformId != column.transformId
            or column.timing not in compatibleTiming
        ):
            raise DriverCalibrationError("coefficient vector source factor contract drift")
        sourceFactorHash = _driverSourceFactorContractHash(
            variableId=factor.variableId,
            unit=factor.unit,
            frequency=factor.frequency,
            timing=factor.timing,
            transformId=factor.transformId,
        )
        terms.append(
            MultivariableDriverCoefficientTerm(
                position=index,
                variableId=factor.variableId,
                coefficient=coefficient,
                coefficientUnit=f"{targetUnit}/{factor.unit}",
                sourceUnit=factor.unit,
                sourceFrequency=factor.frequency,
                sourceTiming=factor.timing,
                sourceTransformId=factor.transformId,
                sourceFactorContractHash=sourceFactorHash,
            )
        )
    return tuple(terms)


def _requiredDesignColumns(binding: MultivariableDriverDesignFrameBinding) -> set[str]:
    columns = {
        "originId",
        "originEventTime",
        "originKnowledgeAsOf",
        "sourceAvailableAt",
        "targetEventTime",
        "targetAvailableAt",
        "targetValue",
        "labelSourceRef",
        "columnOrderHash",
    }
    for column in binding.sourceColumns:
        columns.update(
            {
                _sourceValueColumn(column.variableId),
                _sourceRefColumn(column.variableId),
                _sourceAvailableColumn(column.variableId),
                _sourceKnowledgeColumn(column.variableId),
                _sourceEventColumn(column.variableId),
            }
        )
    return columns


def _cleanMultivariableRows(
    frame: pl.DataFrame,
    binding: MultivariableDriverDesignFrameBinding,
    *,
    cutoff: str,
    oosSpec: MultivariableDriverCoefficientOosSpec | None = None,
    receipt: MultivariableDriverCoefficientCalibrationReceipt | None = None,
) -> tuple[tuple[dict, ...], str, str, str]:
    missing = _requiredDesignColumns(binding) - set(frame.columns)
    if missing:
        raise DriverCalibrationError(f"coefficient vector design frame missing columns: {sorted(missing)}")
    rows: list[dict] = []
    fitThrough = _dateText(receipt.fitThrough, "receipt.fitThrough") if receipt is not None else ""
    calibrationCutoff = (
        _dateText(receipt.calibrationKnowledgeAsOf, "receipt.calibrationKnowledgeAsOf") if receipt is not None else ""
    )
    cutoffText = _dateText(cutoff, "coefficient vector cutoff")
    for index, raw in enumerate(frame.to_dicts()):
        originId = str(raw["originId"])
        labelSourceRef = str(raw["labelSourceRef"])
        if not originId or not labelSourceRef:
            raise DriverCalibrationError(f"coefficient vector row needs origin and label ref: {index}")
        if str(raw["columnOrderHash"]) != binding.columnOrderHash:
            raise DriverCalibrationError("coefficient vector design frame column order drift")
        originEventTime = _dateText(raw["originEventTime"], "originEventTime")
        originKnowledgeAsOf = _dateText(raw["originKnowledgeAsOf"], "originKnowledgeAsOf")
        sourceAvailableAt = _dateText(raw["sourceAvailableAt"], "sourceAvailableAt")
        targetEventTime = _dateText(raw["targetEventTime"], "targetEventTime")
        targetAvailableAt = _dateText(raw["targetAvailableAt"], "targetAvailableAt")
        if receipt is not None:
            if oosSpec is None:
                raise DriverCalibrationError("coefficient vector OOS spec is missing")
            if originEventTime <= fitThrough:
                raise DriverCalibrationError("coefficient vector OOS origin overlaps fit window")
            if targetAvailableAt <= calibrationCutoff:
                raise DriverCalibrationError("coefficient vector OOS label was known at calibration knowledge")
            _validateOosHorizon(originEventTime, targetEventTime, oosSpec)
        if originKnowledgeAsOf > cutoffText:
            raise DriverCalibrationError("coefficient vector origin knowledge is after cutoff")
        if sourceAvailableAt > originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient vector source availability after origin knowledge")
        if targetEventTime <= originEventTime:
            raise DriverCalibrationError("coefficient vector target event must be after origin event")
        if targetAvailableAt <= originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient vector target label is not a forward outcome")
        if targetAvailableAt > cutoffText:
            raise DriverCalibrationError("coefficient vector target label availability after cutoff")
        sourceCells = []
        for column in binding.sourceColumns:
            variableId = column.variableId
            cellEventTime = _dateText(raw[_sourceEventColumn(variableId)], f"{variableId}.eventTime")
            cellAvailableAt = _dateText(raw[_sourceAvailableColumn(variableId)], f"{variableId}.availableAt")
            cellKnowledgeAsOf = _dateText(raw[_sourceKnowledgeColumn(variableId)], f"{variableId}.knowledgeAsOf")
            cellRef = str(raw[_sourceRefColumn(variableId)])
            if not cellRef:
                raise DriverCalibrationError("coefficient vector source cell ref is missing")
            if cellEventTime != originEventTime:
                raise DriverCalibrationError("coefficient vector source cell event drift")
            if cellAvailableAt > cellKnowledgeAsOf or cellKnowledgeAsOf > originKnowledgeAsOf:
                raise DriverCalibrationError("coefficient vector source cell timing drift")
            sourceCells.append(
                MultivariableDriverSourceCell(
                    variableId=variableId,
                    eventTime=cellEventTime,
                    availableAt=cellAvailableAt,
                    knowledgeAsOf=cellKnowledgeAsOf,
                    value=_finite(raw[_sourceValueColumn(variableId)], f"{variableId}.value.{index}"),
                    unit=column.unit,
                    sourceRef=cellRef,
                )
            )
        rows.append(
            {
                "originId": originId,
                "originEventTime": originEventTime,
                "originKnowledgeAsOf": originKnowledgeAsOf,
                "sourceAvailableAt": sourceAvailableAt,
                "targetEventTime": targetEventTime,
                "targetAvailableAt": targetAvailableAt,
                "sourceCells": tuple(sourceCells),
                "targetValue": _finite(raw["targetValue"], f"targetValue.{index}"),
                "labelSourceRef": labelSourceRef,
            }
        )
    rows.sort(key=lambda item: (item["originEventTime"], item["originId"]))
    originIds = tuple(item["originId"] for item in rows)
    if len(set(originIds)) != len(originIds):
        raise DriverCalibrationError("coefficient vector origin ids must be unique")
    if not rows:
        raise DriverCalibrationError("coefficient vector design frame needs origins")
    return (
        tuple(rows),
        rows[0]["originEventTime"],
        rows[-1]["originEventTime"],
        max(item["targetAvailableAt"] for item in rows),
    )


def _solveLinearSystem(matrix: list[list[float]], vector: list[float]) -> tuple[float, ...]:
    size = len(vector)
    augmented = [list(row) + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= 1e-18:
            raise DriverCalibrationError("coefficient vector design matrix is rank deficient")
        if pivot != column:
            augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivotValue = augmented[column][column]
        for item in range(column, size + 1):
            augmented[column][item] /= pivotValue
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if abs(factor) <= 1e-24:
                continue
            for item in range(column, size + 1):
                augmented[row][item] -= factor * augmented[column][item]
    return tuple(augmented[row][size] for row in range(size))


def _fitMultivariableThroughOrigin(
    rows: tuple[dict, ...],
    sourceVariableIds: tuple[str, ...],
) -> tuple[tuple[float, ...], float, float, tuple[MultivariableDriverCoefficientTraceRow, ...]]:
    width = len(sourceVariableIds)
    matrix = [[0.0 for _column in range(width)] for _row in range(width)]
    vector = [0.0 for _column in range(width)]
    for item in rows:
        values = [cell.value for cell in item["sourceCells"]]
        if len(values) != width:
            raise DriverCalibrationError("coefficient vector source cell width mismatch")
        for rowIndex in range(width):
            vector[rowIndex] += values[rowIndex] * item["targetValue"]
            for columnIndex in range(width):
                matrix[rowIndex][columnIndex] += values[rowIndex] * values[columnIndex]
    coefficients = _solveLinearSystem(matrix, vector)
    traceRows = []
    residualSum = 0.0
    targets = [item["targetValue"] for item in rows]
    targetMean = sum(targets) / len(targets)
    targetTotal = sum((value - targetMean) ** 2 for value in targets)
    for item in rows:
        fitted = sum(coefficients[index] * cell.value for index, cell in enumerate(item["sourceCells"]))
        residual = item["targetValue"] - fitted
        residualSum += residual * residual
        traceRows.append(
            MultivariableDriverCoefficientTraceRow(
                originId=item["originId"],
                originEventTime=item["originEventTime"],
                originKnowledgeAsOf=item["originKnowledgeAsOf"],
                sourceAvailableAt=item["sourceAvailableAt"],
                targetEventTime=item["targetEventTime"],
                targetAvailableAt=item["targetAvailableAt"],
                sourceCells=item["sourceCells"],
                targetValue=item["targetValue"],
                fittedValue=fitted,
                residual=residual,
                labelSourceRef=item["labelSourceRef"],
            )
        )
    residualStandardError = math.sqrt(residualSum / max(len(rows) - width, 1))
    rSquared = 1.0 if targetTotal <= 1e-24 and residualSum <= 1e-24 else 1.0 - residualSum / targetTotal
    return coefficients, residualStandardError, rSquared, tuple(traceRows)


def fitMultivariableDriverCoefficientPit(
    registryResult: DriverRegistryResult,
    target: DriverCalibrationTarget,
    frame: pl.DataFrame,
    spec: MultivariableDriverCoefficientCalibrationSpec,
    *,
    calibrationKnowledgeAsOf: str,
    fitDesignFrameBinding: MultivariableDriverDesignFrameBinding | None = None,
) -> MultivariableDriverCoefficientCalibrationReceipt:
    """Fit a PIT coefficient vector from a typed signed design frame binding.

    Args:
        registryResult: Compiled driver registry result that owns every source factor contract.
        target: Observable target label contract. Proxy or assumption labels are rejected.
        frame: Wide design frame carrying one source value column per variable.
        spec: Source variable order, model, lag, and minimum-origin contract.
        calibrationKnowledgeAsOf: Date when the fit is allowed to know labels.
        fitDesignFrameBinding: Replayable signed design frame binding. Raw frames are rejected without it.

    Returns:
        ``MultivariableDriverCoefficientCalibrationReceipt`` with a measured coefficient vector.

    Raises:
        DriverCalibrationError: If target labels, PIT cutoffs, rank, units, or source contracts fail.

    Example:
        ``receipt = fitMultivariableDriverCoefficientPit(registry, target, frame, spec, calibrationKnowledgeAsOf="20251231", fitDesignFrameBinding=binding)``
    """

    _validateTarget(target)
    _validateMultivariableSpec(spec)
    if fitDesignFrameBinding is None:
        raise DriverCalibrationError("coefficient vector fit requires typed design frame binding")
    _validateDesignFrameBinding(fitDesignFrameBinding, "fit")
    if (
        tuple(column.variableId for column in fitDesignFrameBinding.sourceColumns) != spec.sourceVariableIds
        or fitDesignFrameBinding.sourceBatchReceiptIds != spec.sourceParentReceiptIds
        or (fitDesignFrameBinding.labelBatchReceiptId,) != target.labelParentReceiptIds
        or fitDesignFrameBinding.targetVariableId != target.targetVariableId
        or fitDesignFrameBinding.targetUnit != target.targetUnit
    ):
        raise DriverCalibrationError("coefficient vector fit design frame binding mismatch")
    cutoff = _dateText(calibrationKnowledgeAsOf, "calibrationKnowledgeAsOf")
    factorsById = _multivariableSourceFactors(registryResult, spec.sourceVariableIds)
    rows, fitStart, fitThrough, labelThrough = _cleanMultivariableRows(
        frame,
        fitDesignFrameBinding,
        cutoff=cutoff,
    )
    if len(rows) < spec.minOrigins:
        raise DriverCalibrationError("coefficient vector calibration support below minOrigins")
    coefficients, residualStandardError, rSquared, traceRows = _fitMultivariableThroughOrigin(
        rows,
        spec.sourceVariableIds,
    )
    coefficientTerms = _featureTermsFromFactors(
        fitDesignFrameBinding.sourceColumns,
        factorsById,
        target.targetUnit,
        coefficients,
    )
    featureSpecHash = _featureSpecHash(fitDesignFrameBinding.sourceColumns, coefficientTerms)
    coefficientVectorHash = _coefficientVectorHash(coefficientTerms)
    calibrationSpecHash = canonicalPayloadHash(
        {
            "version": MULTIVARIABLE_CALIBRATION_VERSION,
            "spec": spec,
            "target": target,
            "sourceColumns": fitDesignFrameBinding.sourceColumns,
            "coefficientTerms": coefficientTerms,
            "featureSpecHash": featureSpecHash,
            "designFrameHash": fitDesignFrameBinding.frameHash,
            "coefficientVectorHash": coefficientVectorHash,
            "sourceParentReceiptIds": spec.sourceParentReceiptIds,
            "labelParentReceiptIds": target.labelParentReceiptIds,
        }
    )
    originGridHash = _multivariableOriginGridHashFromTraceRows(traceRows)
    targetOutcomeHash = _multivariableOutcomeHashFromTraceRows(traceRows)
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
    modelFormula = f"{target.targetVariableId} = " + " + ".join(
        f"beta[{term.variableId}] * {term.variableId}" for term in coefficientTerms
    )
    baseRefs = _dedupe(
        (
            *registryResult.audit.sourceRefs,
            *registryResult.audit.semanticRefs,
            *target.labelSourceRefs,
            *(cell.sourceRef for row in traceRows for cell in row.sourceCells),
            *(row.labelSourceRef for row in traceRows),
            f"registryHash:{registryResult.audit.registryHash}",
            f"pathSetHash:{registryResult.audit.pathSetHash}",
            f"pathSetInputHash:{registryResult.audit.pathSetInputHash}",
            f"factorContractHash:{registryResult.pathSet.audit.factorContractHash}",
            f"featureSpec:{featureSpecHash}",
            f"fitDesignFrame:{fitDesignFrameBinding.frameHash}",
            f"fitDesignFrameSpec:{fitDesignFrameBinding.specHash}",
            f"coefficientVector:{coefficientVectorHash}",
            f"calibrationSpec:{calibrationSpecHash}",
            f"originGrid:{originGridHash}",
            f"targetOutcome:{targetOutcomeHash}",
            *(f"fitSourceParentReceipt:{receiptId}" for receiptId in spec.sourceParentReceiptIds),
            *(f"fitLabelParentReceipt:{receiptId}" for receiptId in target.labelParentReceiptIds),
        )
    )
    provisional = MultivariableDriverCoefficientCalibrationReceipt(
        calibrationId=spec.calibrationId,
        receiptId="",
        receiptHash="",
        generatorVersion=MULTIVARIABLE_CALIBRATION_VERSION,
        status="retrospectiveOnly",
        validationStatus="retrospectiveOnly",
        historyStatus=historyStatus,
        calibrationKnowledgeAsOf=cutoff,
        sourceVariableIds=spec.sourceVariableIds,
        targetVariableId=target.targetVariableId,
        targetShock=target.targetShock,
        targetUnit=target.targetUnit,
        coefficientTerms=coefficientTerms,
        intercept=0.0,
        residualStandardError=residualStandardError,
        rSquared=rSquared,
        nOrigins=len(rows),
        droppedRows=fitDesignFrameBinding.droppedOriginCount,
        fitStart=fitStart,
        fitThrough=fitThrough,
        labelThrough=labelThrough,
        lagSteps=spec.lagSteps,
        responseKernel=spec.responseKernel,
        modelFormula=modelFormula,
        registryHash=registryResult.audit.registryHash,
        pathSetHash=registryResult.audit.pathSetHash,
        pathSetInputHash=registryResult.audit.pathSetInputHash,
        factorContractHash=registryResult.pathSet.audit.factorContractHash,
        featureSpecHash=featureSpecHash,
        designFrameHash=fitDesignFrameBinding.frameHash,
        coefficientVectorHash=coefficientVectorHash,
        calibrationSpecHash=calibrationSpecHash,
        originGridHash=originGridHash,
        targetOutcomeHash=targetOutcomeHash,
        coefficientTraceHash="",
        warnings=tuple(sorted(set(warnings))),
        sourceRefs=baseRefs,
        sourceParentReceiptIds=spec.sourceParentReceiptIds,
        labelParentReceiptIds=target.labelParentReceiptIds,
        traceRows=traceRows,
        fitDesignFrameBinding=fitDesignFrameBinding,
    )
    coefficientTraceHash = _multivariableCoefficientTraceHash(provisional)
    sourceRefsWithTrace = _dedupe((*baseRefs, f"coefficientTrace:{coefficientTraceHash}"))
    payload = {
        **_multivariableCalibrationReceiptPayload(provisional),
        "coefficientTraceHash": coefficientTraceHash,
        "sourceRefs": sourceRefsWithTrace,
    }
    receiptHash = canonicalPayloadHash(payload)
    receipt = MultivariableDriverCoefficientCalibrationReceipt(
        **{
            name: (
                receiptHash
                if name in {"receiptId", "receiptHash"}
                else coefficientTraceHash
                if name == "coefficientTraceHash"
                else _dedupe((*sourceRefsWithTrace, f"driverCoefficientVectorFit:{receiptHash}"))
                if name == "sourceRefs"
                else getattr(provisional, name)
            )
            for name in provisional.__dataclass_fields__
        }
    )
    _validateMultivariableCalibrationReceipt(receipt)
    return receipt


def fitMultivariableDriverCoefficientPitFromObservationFrame(
    registryResult: DriverRegistryResult,
    target: DriverCalibrationTarget,
    observationFrame: MultivariableDriverCoefficientObservationFrame,
    spec: MultivariableDriverCoefficientCalibrationSpec,
    *,
    calibrationKnowledgeAsOf: str,
) -> MultivariableDriverCoefficientCalibrationReceipt:
    """Fit a coefficient vector only from a typed signed multivariable observation frame.

    Args:
        registryResult: Compiled source factor registry result.
        target: Observable target label contract whose parents match the frame.
        observationFrame: Typed design frame built from signed exact provider batches.
        spec: Source variable order, model, lag, and minimum-origin contract.
        calibrationKnowledgeAsOf: Date when the fit may know labels.

    Returns:
        ``MultivariableDriverCoefficientCalibrationReceipt`` carrying replayable design binding.

    Raises:
        DriverCalibrationError: If the frame parents or meaning drift from the fit contract.

    Example:
        ``receipt = fitMultivariableDriverCoefficientPitFromObservationFrame(registry, target, frame, spec, calibrationKnowledgeAsOf="20251231")``
    """

    binding = _designFrameBindingFromObservationFrame(observationFrame)
    if (
        observationFrame.sourceParentReceiptIds != spec.sourceParentReceiptIds
        or observationFrame.labelParentReceiptIds != target.labelParentReceiptIds
    ):
        raise DriverCalibrationError("coefficient vector observation frame parent contract mismatch")
    return fitMultivariableDriverCoefficientPit(
        registryResult,
        target,
        observationFrame.frame,
        spec,
        calibrationKnowledgeAsOf=calibrationKnowledgeAsOf,
        fitDesignFrameBinding=binding,
    )
