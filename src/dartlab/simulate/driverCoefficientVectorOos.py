"""벡터 계수의 held-out 판정과 서명 대상 아티팩트.

스칼라 판정의 쌍이다. 예측이 내적이라 셀 순서가 곧 계수 순서이고, 그래서 행마다
셀 순서와 셀 시점까지 다시 확인해야 재생이 성립한다. 그 추가 계약이 스칼라와
합칠 수 없는 지점이다.
"""

from __future__ import annotations

import math

import polars as pl

from dartlab.simulate.driverCalibrationContracts import (
    _OOS_STATUS_SET,
    MULTIVARIABLE_COEFFICIENT_OOS_VERSION,
    DriverCalibrationError,
    MultivariableDriverCoefficientCalibrationReceipt,
    MultivariableDriverCoefficientOosReport,
    MultivariableDriverCoefficientOosSpec,
    MultivariableDriverCoefficientOosTraceRow,
    MultivariableDriverDesignFrameBinding,
)
from dartlab.simulate.driverCalibrationKernel import (
    _assertClose,
    _dateText,
    _dedupe,
    _finite,
    _oosRejectionReasons,
    _validateReceiptIds,
    _validDigest,
)
from dartlab.simulate.driverCoefficientFrameBinding import (
    _designFrameBindingFromObservationFrame,
    _validateDesignFrameBinding,
)
from dartlab.simulate.driverCoefficientVectorFit import _cleanMultivariableRows
from dartlab.simulate.driverCoefficientVectorReceipt import (
    _coefficientVectorHash,
    _featureSpecHash,
    _multivariableOosReportPayload,
    _multivariableOriginGridHashFromTraceRows,
    _multivariableOutcomeHashFromTraceRows,
    _multivariablePredictionTraceHash,
    _predictMultivariable,
    _validateMultivariableCalibrationReceipt,
)
from dartlab.simulate.driverObservationFrames import MultivariableDriverCoefficientObservationFrame
from dartlab.simulate.vintage import canonicalPayloadBytes, canonicalPayloadHash


def _validateMultivariableOosSpec(spec: MultivariableDriverCoefficientOosSpec) -> None:
    if (
        not spec.evaluationId
        or spec.minOosOrigins < 2
        or not math.isfinite(float(spec.minSkillVsBaseline))
        or not math.isfinite(float(spec.maxRmse))
        or not math.isfinite(float(spec.maxAbsBias))
        or not math.isfinite(float(spec.baselineValue))
        or spec.maxRmse < 0.0
        or spec.maxAbsBias < 0.0
        or not spec.frequency
        or spec.stepSpan < 1
        or spec.maxAdmittedStep < 1
    ):
        raise DriverCalibrationError("coefficient vector OOS spec is incomplete")
    _validateReceiptIds(spec.sourceParentReceiptIds, "vector OOS source parent")
    _validateReceiptIds(spec.labelParentReceiptIds, "vector OOS label parent")


def _validateVectorReportIdentity(report: MultivariableDriverCoefficientOosReport) -> None:
    """보고서 정체성 (프로토콜 필드·다이제스트·부모 영수증·양쪽 설계 프레임) 을 검사한다."""
    if (
        report.generatorVersion != MULTIVARIABLE_COEFFICIENT_OOS_VERSION
        or report.status not in _OOS_STATUS_SET
        or report.admissionStatus != "unsigned"
        or not report.evaluationId
        or not report.pathSetHash
        or not report.factorContractHash
        or not report.featureSpecHash
        or not report.designFrameHash
        or not report.coefficientVectorHash
        or report.stepSpan < 1
        or report.maxAdmittedStep < 1
        or report.nOosOrigins < 1
        or not report.frequency
        or not report.traceRows
        or len(report.sourceVariableIds) != len(report.coefficientTerms)
    ):
        raise DriverCalibrationError("coefficient vector OOS report protocol mismatch")
    if report.reportId != canonicalPayloadHash(_multivariableOosReportPayload(report)):
        raise DriverCalibrationError("coefficient vector OOS report hash mismatch")
    if tuple(term.variableId for term in report.coefficientTerms) != report.sourceVariableIds:
        raise DriverCalibrationError("coefficient vector OOS report source variable order mismatch")
    for label, value in (
        ("receiptHash", report.receiptHash),
        ("receiptId", report.receiptId),
        ("pathSetHash", report.pathSetHash),
        ("factorContractHash", report.factorContractHash),
        ("featureSpecHash", report.featureSpecHash),
        ("designFrameHash", report.designFrameHash),
        ("coefficientVectorHash", report.coefficientVectorHash),
        ("oosSpecHash", report.oosSpecHash),
        ("oosGridHash", report.oosGridHash),
        ("oosOutcomeHash", report.oosOutcomeHash),
        ("predictionTraceHash", report.predictionTraceHash),
    ):
        if not _validDigest(value):
            raise DriverCalibrationError(f"coefficient vector OOS report {label} is invalid")
    _validateReceiptIds(report.fitSourceParentReceiptIds, "vector fit source parent")
    _validateReceiptIds(report.fitLabelParentReceiptIds, "vector fit label parent")
    _validateReceiptIds(report.oosSourceParentReceiptIds, "vector OOS source parent")
    _validateReceiptIds(report.oosLabelParentReceiptIds, "vector OOS label parent")
    if report.status == "oosEligible" and (
        not report.fitSourceParentReceiptIds
        or not report.fitLabelParentReceiptIds
        or not report.oosSourceParentReceiptIds
        or not report.oosLabelParentReceiptIds
    ):
        raise DriverCalibrationError("coefficient vector OOS report parent receipts are incomplete")


def _validateVectorReportDesignFrames(report: MultivariableDriverCoefficientOosReport) -> None:
    """적합·판정 설계 프레임이 같은 칼럼 순서와 특성 해시를 가리키는지 검사한다."""
    _validateDesignFrameBinding(report.fitDesignFrameBinding, "fit")
    _validateDesignFrameBinding(report.oosDesignFrameBinding, "OOS")
    if (
        report.fitDesignFrameBinding.frameHash != report.designFrameHash
        or report.oosDesignFrameBinding.rowCount != report.nOosOrigins
        or tuple(column.variableId for column in report.fitDesignFrameBinding.sourceColumns) != report.sourceVariableIds
        or tuple(column.variableId for column in report.oosDesignFrameBinding.sourceColumns) != report.sourceVariableIds
        or report.oosDesignFrameBinding.sourceColumns != report.fitDesignFrameBinding.sourceColumns
    ):
        raise DriverCalibrationError("coefficient vector OOS report design frame mismatch")
    if report.featureSpecHash != _featureSpecHash(
        report.fitDesignFrameBinding.sourceColumns,
        report.coefficientTerms,
    ):
        raise DriverCalibrationError("coefficient vector OOS report feature spec hash mismatch")
    if report.coefficientVectorHash != _coefficientVectorHash(report.coefficientTerms):
        raise DriverCalibrationError("coefficient vector OOS report coefficient vector hash mismatch")


def _validateVectorReportWindow(report: MultivariableDriverCoefficientOosReport) -> str:
    """보정·판정 시점 순서와 판정 창 경계를 검사하고 보정 cutoff 를 돌려준다."""
    calibrationCutoff = _dateText(report.calibrationKnowledgeAsOf, "vectorReport.calibrationKnowledgeAsOf")
    evaluationCutoff = _dateText(report.evaluationKnowledgeAsOf, "vectorReport.evaluationKnowledgeAsOf")
    if calibrationCutoff > evaluationCutoff:
        raise DriverCalibrationError("coefficient vector OOS report evaluation precedes calibration")
    if report.nOosOrigins != len(report.traceRows):
        raise DriverCalibrationError("coefficient vector OOS report origin count mismatch")
    originKeys = tuple((row.originEventTime, row.originId) for row in report.traceRows)
    if originKeys != tuple(sorted(originKeys)) or len({row.originId for row in report.traceRows}) != len(
        report.traceRows
    ):
        raise DriverCalibrationError("coefficient vector OOS report origin order mismatch")
    if (
        report.oosStart != report.traceRows[0].originEventTime
        or report.oosThrough != report.traceRows[-1].originEventTime
        or report.labelThrough != max(row.targetAvailableAt for row in report.traceRows)
    ):
        raise DriverCalibrationError("coefficient vector OOS report window mismatch")
    return calibrationCutoff


def _validateVectorReportRows(
    report: MultivariableDriverCoefficientOosReport,
    calibrationCutoff: str,
) -> tuple[float, float, float, float]:
    """행마다 셀 순서·누수·예측 항등식을 다시 계산하고 손실 누적값을 되돌린다."""
    squared = 0.0
    baselineSquared = 0.0
    absolute = 0.0
    residualTotal = 0.0
    for index, row in enumerate(report.traceRows):
        originEventTime = _dateText(row.originEventTime, f"vectorReport.originEventTime.{index}")
        originKnowledgeAsOf = _dateText(row.originKnowledgeAsOf, f"vectorReport.originKnowledgeAsOf.{index}")
        sourceAvailableAt = _dateText(row.sourceAvailableAt, f"vectorReport.sourceAvailableAt.{index}")
        targetEventTime = _dateText(row.targetEventTime, f"vectorReport.targetEventTime.{index}")
        targetAvailableAt = _dateText(row.targetAvailableAt, f"vectorReport.targetAvailableAt.{index}")
        if sourceAvailableAt > originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient vector OOS report source availability mismatch")
        if targetEventTime <= originEventTime or targetAvailableAt <= originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient vector OOS report target timing mismatch")
        if targetAvailableAt <= calibrationCutoff:
            raise DriverCalibrationError("coefficient vector OOS report fit leakage mismatch")
        if tuple(cell.variableId for cell in row.sourceCells) != report.sourceVariableIds:
            raise DriverCalibrationError("coefficient vector OOS report source cell order mismatch")
        for cell in row.sourceCells:
            _dateText(cell.eventTime, "vectorReport.cell.eventTime")
            _dateText(cell.availableAt, "vectorReport.cell.availableAt")
            _dateText(cell.knowledgeAsOf, "vectorReport.cell.knowledgeAsOf")
            _finite(cell.value, "vectorReport.cell.value")
            if not cell.sourceRef or not cell.unit:
                raise DriverCalibrationError("coefficient vector OOS report source cell ref mismatch")
        targetValue = _finite(row.targetValue, f"vectorReport.targetValue.{index}")
        predictedValue = _finite(row.predictedValue, f"vectorReport.predictedValue.{index}")
        baselineValue = _finite(row.baselineValue, f"vectorReport.baselineValue.{index}")
        residual = _finite(row.residual, f"vectorReport.residual.{index}")
        baselineResidual = _finite(row.baselineResidual, f"vectorReport.baselineResidual.{index}")
        if not row.labelSourceRef:
            raise DriverCalibrationError("coefficient vector OOS report label ref mismatch")
        _assertClose(predictedValue, _predictMultivariable(row.sourceCells, report.coefficientTerms), "prediction")
        _assertClose(residual, targetValue - predictedValue, "residual")
        _assertClose(baselineValue, report.baselineValue, "baseline")
        _assertClose(baselineResidual, targetValue - baselineValue, "baseline residual")
        squared += residual * residual
        baselineSquared += baselineResidual * baselineResidual
        absolute += abs(residual)
        residualTotal += residual
    return squared, baselineSquared, absolute, residualTotal


def _validateMultivariableCoefficientReport(report: MultivariableDriverCoefficientOosReport) -> None:
    """벡터 OOS 보고서를 정체성·창·행·지표 순으로 처음부터 다시 계산해 대조한다."""
    _validateVectorReportIdentity(report)
    _validateVectorReportDesignFrames(report)
    calibrationCutoff = _validateVectorReportWindow(report)
    squared, baselineSquared, absolute, residualTotal = _validateVectorReportRows(report, calibrationCutoff)
    mse = squared / report.nOosOrigins
    baselineMse = baselineSquared / report.nOosOrigins
    if baselineMse <= 1e-24:
        raise DriverCalibrationError("coefficient vector OOS report baseline loss mismatch")
    bias = residualTotal / report.nOosOrigins
    _assertClose(report.mse, mse, "mse")
    _assertClose(report.baselineMse, baselineMse, "baselineMse")
    _assertClose(report.rmse, math.sqrt(mse), "rmse")
    _assertClose(report.mae, absolute / report.nOosOrigins, "mae")
    _assertClose(report.bias, bias, "bias")
    _assertClose(report.skillVsBaseline, 1.0 - mse / baselineMse, "skill")
    if report.oosGridHash != _multivariableOriginGridHashFromTraceRows(report.traceRows):
        raise DriverCalibrationError("coefficient vector OOS report grid hash mismatch")
    if report.oosOutcomeHash != _multivariableOutcomeHashFromTraceRows(report.traceRows):
        raise DriverCalibrationError("coefficient vector OOS report outcome hash mismatch")
    if report.predictionTraceHash != _multivariablePredictionTraceHash(
        receiptHash=report.receiptHash,
        oosSpecHash=report.oosSpecHash,
        oosGridHash=report.oosGridHash,
        oosOutcomeHash=report.oosOutcomeHash,
        traceRows=report.traceRows,
        mse=report.mse,
        baselineMse=report.baselineMse,
        skillVsBaseline=report.skillVsBaseline,
        bias=report.bias,
    ):
        raise DriverCalibrationError("coefficient vector OOS report trace hash mismatch")
    if (report.status == "oosEligible") != (not report.reasons):
        raise DriverCalibrationError("coefficient vector OOS report status mismatch")


def _validateVectorOosFrameBinding(
    oosDesignFrameBinding: MultivariableDriverDesignFrameBinding,
    spec: MultivariableDriverCoefficientOosSpec,
    receipt: MultivariableDriverCoefficientCalibrationReceipt,
) -> None:
    """판정 설계 프레임 결속이 OOS spec 부모와 적합 칼럼 순서에 맞는지 검사한다."""
    _validateDesignFrameBinding(oosDesignFrameBinding, "OOS")
    if (
        tuple(column.variableId for column in oosDesignFrameBinding.sourceColumns) != receipt.sourceVariableIds
        or oosDesignFrameBinding.sourceColumns != receipt.fitDesignFrameBinding.sourceColumns
        or oosDesignFrameBinding.sourceBatchReceiptIds != spec.sourceParentReceiptIds
        or (oosDesignFrameBinding.labelBatchReceiptId,) != spec.labelParentReceiptIds
        or oosDesignFrameBinding.targetVariableId != receipt.targetVariableId
        or oosDesignFrameBinding.targetUnit != receipt.targetUnit
    ):
        raise DriverCalibrationError("coefficient vector OOS design frame binding mismatch")


def _scoreVectorOosRows(
    receipt: MultivariableDriverCoefficientCalibrationReceipt,
    rows: tuple[dict, ...],
    baselineValue: float,
) -> tuple[list[MultivariableDriverCoefficientOosTraceRow], float, float, float, float]:
    """얼린 계수 벡터로 held-out 행을 채점하고 손실을 원래 누적 순서로 되돌린다."""
    traceRows: list[MultivariableDriverCoefficientOosTraceRow] = []
    squared = 0.0
    absolute = 0.0
    residualTotal = 0.0
    baselineSquared = 0.0
    for item in rows:
        predicted = receipt.intercept + _predictMultivariable(item["sourceCells"], receipt.coefficientTerms)
        residual = item["targetValue"] - predicted
        baselineResidual = item["targetValue"] - baselineValue
        squared += residual * residual
        absolute += abs(residual)
        residualTotal += residual
        baselineSquared += baselineResidual * baselineResidual
        traceRows.append(
            MultivariableDriverCoefficientOosTraceRow(
                originId=item["originId"],
                originEventTime=item["originEventTime"],
                originKnowledgeAsOf=item["originKnowledgeAsOf"],
                sourceAvailableAt=item["sourceAvailableAt"],
                targetEventTime=item["targetEventTime"],
                targetAvailableAt=item["targetAvailableAt"],
                sourceCells=item["sourceCells"],
                targetValue=item["targetValue"],
                predictedValue=predicted,
                baselineValue=baselineValue,
                residual=residual,
                baselineResidual=baselineResidual,
                labelSourceRef=item["labelSourceRef"],
            )
        )
    return traceRows, squared, absolute, residualTotal, baselineSquared


def evaluateMultivariableDriverCoefficientOos(
    receipt: MultivariableDriverCoefficientCalibrationReceipt,
    frame: pl.DataFrame,
    spec: MultivariableDriverCoefficientOosSpec,
    *,
    evaluationKnowledgeAsOf: str,
    oosDesignFrameBinding: MultivariableDriverDesignFrameBinding | None = None,
) -> MultivariableDriverCoefficientOosReport:
    """Score a fixed coefficient vector on held-out PIT origins.

    Args:
        receipt: Calibration receipt whose coefficient vector is frozen before OOS scoring.
        frame: Held-out wide design rows with source cells and target availability dates.
        spec: OOS thresholds, baseline, and artifact step contract.
        evaluationKnowledgeAsOf: Date when held-out labels are allowed to be known.
        oosDesignFrameBinding: Replayable signed held-out design frame binding.

    Returns:
        Unsigned ``MultivariableDriverCoefficientOosReport``.

    Raises:
        DriverCalibrationError: If OOS timing, row lineage, thresholds, or protocol fields fail.

    Example:
        ``report = evaluateMultivariableDriverCoefficientOos(receipt, frame, spec, evaluationKnowledgeAsOf="20251231", oosDesignFrameBinding=binding)``
    """

    _validateMultivariableCalibrationReceipt(receipt)
    _validateMultivariableOosSpec(spec)
    if oosDesignFrameBinding is None:
        raise DriverCalibrationError("coefficient vector OOS requires typed design frame binding")
    _validateVectorOosFrameBinding(oosDesignFrameBinding, spec, receipt)
    cutoff = _dateText(evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf")
    rows, oosStart, oosThrough, labelThrough = _cleanMultivariableRows(
        frame,
        oosDesignFrameBinding,
        cutoff=cutoff,
        oosSpec=spec,
        receipt=receipt,
    )
    baselineValue = _finite(spec.baselineValue, "vectorOos.baselineValue")
    traceRows, squared, absolute, residualTotal, baselineSquared = _scoreVectorOosRows(receipt, rows, baselineValue)
    nOrigins = len(traceRows)
    mse = squared / nOrigins
    baselineMse = baselineSquared / nOrigins
    if baselineMse <= 1e-24:
        raise DriverCalibrationError("coefficient vector OOS baseline has no loss to beat")
    rmse = math.sqrt(mse)
    mae = absolute / nOrigins
    bias = residualTotal / nOrigins
    skill = 1.0 - mse / baselineMse
    reasons = _oosRejectionReasons(receipt, spec, nOrigins=nOrigins, skill=skill, rmse=rmse, bias=bias)
    status = "oosEligible" if not reasons else "rejected"
    oosSpecHash = canonicalPayloadHash(
        {"version": MULTIVARIABLE_COEFFICIENT_OOS_VERSION, "spec": spec, "receipt": receipt.receiptHash}
    )
    oosGridHash = _multivariableOriginGridHashFromTraceRows(tuple(traceRows))
    oosOutcomeHash = _multivariableOutcomeHashFromTraceRows(tuple(traceRows))
    predictionTraceHash = _multivariablePredictionTraceHash(
        receiptHash=receipt.receiptHash,
        oosSpecHash=oosSpecHash,
        oosGridHash=oosGridHash,
        oosOutcomeHash=oosOutcomeHash,
        traceRows=tuple(traceRows),
        mse=mse,
        baselineMse=baselineMse,
        skillVsBaseline=skill,
        bias=bias,
    )
    sourceRefs = _dedupe(
        (
            *receipt.sourceRefs,
            *(cell.sourceRef for row in traceRows for cell in row.sourceCells),
            *(row.labelSourceRef for row in traceRows),
            f"driverCoefficientVectorFit:{receipt.receiptHash}",
            f"coefficientVectorOosSpec:{oosSpecHash}",
            f"coefficientVectorOosGrid:{oosGridHash}",
            f"coefficientVectorOosOutcome:{oosOutcomeHash}",
            f"coefficientVectorPredictionTrace:{predictionTraceHash}",
            f"fitDesignFrame:{receipt.fitDesignFrameBinding.frameHash}",
            f"oosDesignFrame:{oosDesignFrameBinding.frameHash}",
            f"oosDesignFrameSpec:{oosDesignFrameBinding.specHash}",
            *(f"fitSourceParentReceipt:{receiptId}" for receiptId in receipt.sourceParentReceiptIds),
            *(f"fitLabelParentReceipt:{receiptId}" for receiptId in receipt.labelParentReceiptIds),
            *(f"oosSourceParentReceipt:{receiptId}" for receiptId in spec.sourceParentReceiptIds),
            *(f"oosLabelParentReceipt:{receiptId}" for receiptId in spec.labelParentReceiptIds),
        )
    )
    provisional = MultivariableDriverCoefficientOosReport(
        evaluationId=spec.evaluationId,
        reportId="",
        generatorVersion=MULTIVARIABLE_COEFFICIENT_OOS_VERSION,
        status=status,
        admissionStatus="unsigned",
        receiptHash=receipt.receiptHash,
        receiptId=receipt.receiptId,
        calibrationId=receipt.calibrationId,
        sourceVariableIds=receipt.sourceVariableIds,
        targetVariableId=receipt.targetVariableId,
        targetShock=receipt.targetShock,
        targetUnit=receipt.targetUnit,
        coefficientTerms=receipt.coefficientTerms,
        pathSetHash=receipt.pathSetHash,
        factorContractHash=receipt.factorContractHash,
        featureSpecHash=receipt.featureSpecHash,
        designFrameHash=receipt.designFrameHash,
        coefficientVectorHash=receipt.coefficientVectorHash,
        frequency=spec.frequency,
        stepSpan=spec.stepSpan,
        maxAdmittedStep=spec.maxAdmittedStep,
        calibrationKnowledgeAsOf=receipt.calibrationKnowledgeAsOf,
        evaluationKnowledgeAsOf=cutoff,
        nOosOrigins=nOrigins,
        oosStart=oosStart,
        oosThrough=oosThrough,
        labelThrough=labelThrough,
        baselineValue=baselineValue,
        mse=mse,
        baselineMse=baselineMse,
        rmse=rmse,
        mae=mae,
        bias=bias,
        skillVsBaseline=skill,
        minSkillVsBaseline=spec.minSkillVsBaseline,
        maxRmse=spec.maxRmse,
        maxAbsBias=spec.maxAbsBias,
        oosSpecHash=oosSpecHash,
        oosGridHash=oosGridHash,
        oosOutcomeHash=oosOutcomeHash,
        predictionTraceHash=predictionTraceHash,
        reasons=tuple(reasons),
        warnings=("coefficientVectorOosReportUnsigned",),
        sourceRefs=sourceRefs,
        fitSourceParentReceiptIds=receipt.sourceParentReceiptIds,
        fitLabelParentReceiptIds=receipt.labelParentReceiptIds,
        oosSourceParentReceiptIds=spec.sourceParentReceiptIds,
        oosLabelParentReceiptIds=spec.labelParentReceiptIds,
        traceRows=tuple(traceRows),
        fitDesignFrameBinding=receipt.fitDesignFrameBinding,
        oosDesignFrameBinding=oosDesignFrameBinding,
    )
    report = MultivariableDriverCoefficientOosReport(
        **{
            name: (
                canonicalPayloadHash(_multivariableOosReportPayload(provisional))
                if name == "reportId"
                else getattr(provisional, name)
            )
            for name in provisional.__dataclass_fields__
        }
    )
    _validateMultivariableCoefficientReport(report)
    return report


def evaluateMultivariableDriverCoefficientOosFromObservationFrame(
    receipt: MultivariableDriverCoefficientCalibrationReceipt,
    observationFrame: MultivariableDriverCoefficientObservationFrame,
    spec: MultivariableDriverCoefficientOosSpec,
    *,
    evaluationKnowledgeAsOf: str,
) -> MultivariableDriverCoefficientOosReport:
    """Evaluate a coefficient vector only on a typed signed provider design frame.

    Args:
        receipt: Frozen fit receipt whose coefficient vector is being admitted.
        observationFrame: Typed held-out design frame built from signed exact batches.
        spec: OOS thresholds and parent receipt contract matching the frame.
        evaluationKnowledgeAsOf: Date when held-out labels may be known.

    Returns:
        ``MultivariableDriverCoefficientOosReport`` carrying replayable OOS design binding.

    Raises:
        DriverCalibrationError: If the OOS frame parents or meaning drift from the report contract.

    Example:
        ``report = evaluateMultivariableDriverCoefficientOosFromObservationFrame(receipt, frame, spec, evaluationKnowledgeAsOf="20251231")``
    """

    binding = _designFrameBindingFromObservationFrame(observationFrame)
    if (
        observationFrame.sourceParentReceiptIds != spec.sourceParentReceiptIds
        or observationFrame.labelParentReceiptIds != spec.labelParentReceiptIds
    ):
        raise DriverCalibrationError("coefficient vector OOS observation frame parent contract mismatch")
    return evaluateMultivariableDriverCoefficientOos(
        receipt,
        observationFrame.frame,
        spec,
        evaluationKnowledgeAsOf=evaluationKnowledgeAsOf,
        oosDesignFrameBinding=binding,
    )


def multivariableDriverCoefficientAdmissionArtifact(report: MultivariableDriverCoefficientOosReport) -> bytes:
    """Return canonical bytes to store under a vector coefficient admission artifact.

    Args:
        report: OOS report returned by ``evaluateMultivariableDriverCoefficientOos``.

    Returns:
        Canonical JSON bytes whose SHA-256 is the coefficient vector admission subject.

    Raises:
        DriverCalibrationError: If the report protocol or hash is invalid.

    Example:
        ``artifact = multivariableDriverCoefficientAdmissionArtifact(report)``
    """

    _validateMultivariableCoefficientReport(report)
    return canonicalPayloadBytes(_multivariableOosReportPayload(report))


def multivariableDriverCoefficientAdmissionSubjectHash(report: MultivariableDriverCoefficientOosReport) -> str:
    """Return the content hash used as the signed coefficient vector subject.

    Args:
        report: OOS report returned by ``evaluateMultivariableDriverCoefficientOos``.

    Returns:
        SHA-256 subject hash for an admission registry receipt.

    Raises:
        DriverCalibrationError: If the report protocol or hash is invalid.

    Example:
        ``subject = multivariableDriverCoefficientAdmissionSubjectHash(report)``
    """

    return canonicalPayloadHash(_multivariableOosReportPayload(report))


def multivariableDriverCoefficientAdmissionParentReceiptIds(
    report: MultivariableDriverCoefficientOosReport,
) -> tuple[str, ...]:
    """Return the exact source and label parents required by a coefficient vector admission.

    Args:
        report: OOS report returned by ``evaluateMultivariableDriverCoefficientOos``.

    Returns:
        Ordered unique parent receipt identifiers for the signed admission receipt.

    Raises:
        DriverCalibrationError: If the report protocol or parent identifiers are invalid.

    Example:
        ``parents = multivariableDriverCoefficientAdmissionParentReceiptIds(report)``
    """

    _validateMultivariableCoefficientReport(report)
    return _dedupe(
        (
            *report.fitSourceParentReceiptIds,
            *report.fitLabelParentReceiptIds,
            *report.oosSourceParentReceiptIds,
            *report.oosLabelParentReceiptIds,
        )
    )
