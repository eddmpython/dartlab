"""스칼라 계수의 held-out 판정과 서명 대상 아티팩트.

계수를 얼린 뒤에만 열리는 단계다. 적합 창과 겹치는 origin, 보정 시점에 이미 알려진
label 을 여기서 거부해야 승인이 의미를 갖는다. 보고서 재검증도 같이 두어
"판정을 만든 규칙" 과 "판정을 다시 읽는 규칙" 이 갈라지지 않게 한다.
"""

from __future__ import annotations

import math

import polars as pl

from dartlab.simulate.driverCalibrationContracts import (
    _OOS_STATUS_SET,
    COEFFICIENT_OOS_VERSION,
    DriverCalibrationError,
    DriverCoefficientCalibrationReceipt,
    DriverCoefficientOosReport,
    DriverCoefficientOosSpec,
    DriverCoefficientOosTraceRow,
    DriverObservationFrameBinding,
)
from dartlab.simulate.driverCalibrationKernel import (
    _assertClose,
    _dateText,
    _dedupe,
    _finite,
    _oosRejectionReasons,
    _validateOosHorizon,
    _validateReceiptIds,
    _validDigest,
)
from dartlab.simulate.driverCoefficientFrameBinding import (
    _frameBindingFromObservationFrame,
    _validateFrameBinding,
)
from dartlab.simulate.driverCoefficientReceipt import (
    _oosGridHashFromTraceRows,
    _oosOutcomeHashFromTraceRows,
    _oosReportPayload,
    _predictionTraceHash,
)
from dartlab.simulate.driverObservationFrames import DriverCoefficientObservationFrame
from dartlab.simulate.operatingBridge import OPERATING_TARGET_UNITS
from dartlab.simulate.vintage import canonicalPayloadBytes, canonicalPayloadHash


def _validateOosSpec(spec: DriverCoefficientOosSpec) -> None:
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
        raise DriverCalibrationError("coefficient OOS spec is incomplete")
    _validateReceiptIds(spec.sourceParentReceiptIds, "OOS source parent")
    _validateReceiptIds(spec.labelParentReceiptIds, "OOS label parent")


def _oosRequiredColumns(spec: DriverCoefficientOosSpec) -> set[str]:
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


def _cleanOosRows(
    frame: pl.DataFrame,
    spec: DriverCoefficientOosSpec,
    receipt: DriverCoefficientCalibrationReceipt,
    *,
    evaluationKnowledgeAsOf: str,
) -> tuple[tuple[dict, ...], str, str, str]:
    missing = _oosRequiredColumns(spec) - set(frame.columns)
    if missing:
        raise DriverCalibrationError(f"coefficient OOS frame missing columns: {sorted(missing)}")
    cutoff = _dateText(evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf")
    rows: list[dict] = []
    fitThrough = _dateText(receipt.fitThrough, "receipt.fitThrough")
    calibrationCutoff = _dateText(receipt.calibrationKnowledgeAsOf, "receipt.calibrationKnowledgeAsOf")
    for index, raw in enumerate(frame.to_dicts()):
        originId = str(raw[spec.originIdColumn])
        sourceRef = str(raw[spec.sourceRefColumn])
        labelSourceRef = str(raw[spec.labelSourceRefColumn])
        if not originId or not sourceRef or not labelSourceRef:
            raise DriverCalibrationError(f"coefficient OOS row needs origin and refs: {index}")
        originEventTime = _dateText(raw[spec.originEventTimeColumn], "originEventTime")
        originKnowledgeAsOf = _dateText(raw[spec.originKnowledgeAsOfColumn], "originKnowledgeAsOf")
        sourceAvailableAt = _dateText(raw[spec.sourceAvailableAtColumn], "sourceAvailableAt")
        targetEventTime = _dateText(raw[spec.targetEventTimeColumn], "targetEventTime")
        targetAvailableAt = _dateText(raw[spec.targetAvailableAtColumn], "targetAvailableAt")
        if originEventTime <= fitThrough:
            raise DriverCalibrationError("coefficient OOS origin overlaps fit window")
        if originKnowledgeAsOf > cutoff:
            raise DriverCalibrationError("coefficient OOS origin knowledge is after evaluation knowledge")
        if sourceAvailableAt > originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient OOS source availability after origin knowledge")
        if targetEventTime <= originEventTime:
            raise DriverCalibrationError("coefficient OOS target event must be after origin event")
        if targetAvailableAt <= originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient OOS target label is not a forward outcome")
        if targetAvailableAt <= calibrationCutoff:
            raise DriverCalibrationError("coefficient OOS label was known at calibration knowledge")
        if targetAvailableAt > cutoff:
            raise DriverCalibrationError("coefficient OOS label availability after evaluation knowledge")
        _validateOosHorizon(originEventTime, targetEventTime, spec)
        rows.append(
            {
                "originId": originId,
                "originEventTime": originEventTime,
                "originKnowledgeAsOf": originKnowledgeAsOf,
                "sourceAvailableAt": sourceAvailableAt,
                "targetEventTime": targetEventTime,
                "targetAvailableAt": targetAvailableAt,
                "sourceValue": _finite(raw[spec.sourceValueColumn], f"oos.sourceValue.{index}"),
                "targetValue": _finite(raw[spec.targetValueColumn], f"oos.targetValue.{index}"),
                "sourceRef": sourceRef,
                "labelSourceRef": labelSourceRef,
            }
        )
    rows.sort(key=lambda item: (item["originEventTime"], item["originId"]))
    originIds = tuple(item["originId"] for item in rows)
    if len(set(originIds)) != len(originIds):
        raise DriverCalibrationError("coefficient OOS origin ids must be unique")
    if not rows:
        raise DriverCalibrationError("coefficient OOS frame needs origins")
    return (
        tuple(rows),
        rows[0]["originEventTime"],
        rows[-1]["originEventTime"],
        max(item["targetAvailableAt"] for item in rows),
    )


def _validateCoefficientReportIdentity(report: DriverCoefficientOosReport) -> None:
    """보고서 정체성 (프로토콜 필드·다이제스트·부모 영수증·프레임 결속) 을 검사한다."""
    if (
        report.generatorVersion != COEFFICIENT_OOS_VERSION
        or report.status not in _OOS_STATUS_SET
        or report.admissionStatus != "unsigned"
        or not report.evaluationId
        or not report.pathSetHash
        or not report.factorContractHash
        or report.stepSpan < 1
        or report.maxAdmittedStep < 1
        or report.nOosOrigins < 1
        or not report.frequency
        or not report.traceRows
    ):
        raise DriverCalibrationError("coefficient OOS report protocol mismatch")
    if report.reportId != canonicalPayloadHash(_oosReportPayload(report)):
        raise DriverCalibrationError("coefficient OOS report hash mismatch")
    for label, value in (
        ("receiptHash", report.receiptHash),
        ("receiptId", report.receiptId),
        ("pathSetHash", report.pathSetHash),
        ("factorContractHash", report.factorContractHash),
        ("oosSpecHash", report.oosSpecHash),
        ("oosGridHash", report.oosGridHash),
        ("oosOutcomeHash", report.oosOutcomeHash),
        ("predictionTraceHash", report.predictionTraceHash),
    ):
        if not _validDigest(value):
            raise DriverCalibrationError(f"coefficient OOS report {label} is invalid")
    _validateReceiptIds(report.fitSourceParentReceiptIds, "fit source parent")
    _validateReceiptIds(report.fitLabelParentReceiptIds, "fit label parent")
    _validateReceiptIds(report.oosSourceParentReceiptIds, "OOS source parent")
    _validateReceiptIds(report.oosLabelParentReceiptIds, "OOS label parent")
    if report.status == "oosEligible" and (
        not report.fitSourceParentReceiptIds
        or not report.fitLabelParentReceiptIds
        or not report.oosSourceParentReceiptIds
        or not report.oosLabelParentReceiptIds
    ):
        raise DriverCalibrationError("coefficient OOS report parent receipts are incomplete")
    calibrationCutoff = _dateText(report.calibrationKnowledgeAsOf, "report.calibrationKnowledgeAsOf")
    evaluationCutoff = _dateText(report.evaluationKnowledgeAsOf, "report.evaluationKnowledgeAsOf")
    if calibrationCutoff > evaluationCutoff:
        raise DriverCalibrationError("coefficient OOS report evaluation precedes calibration")
    if report.nOosOrigins != len(report.traceRows):
        raise DriverCalibrationError("coefficient OOS report origin count mismatch")
    if report.fitFrameBinding is not None:
        _validateFrameBinding(report.fitFrameBinding, "fit")
    if report.oosFrameBinding is not None:
        _validateFrameBinding(report.oosFrameBinding, "OOS")
        if report.oosFrameBinding.rowCount != report.nOosOrigins:
            raise DriverCalibrationError("coefficient OOS report frame row count mismatch")


def _validateCoefficientReportWindow(report: DriverCoefficientOosReport) -> None:
    """held-out origin 정렬과 판정 창 경계가 trace 행과 일치하는지 검사한다."""
    originKeys = tuple((row.originEventTime, row.originId) for row in report.traceRows)
    if originKeys != tuple(sorted(originKeys)) or len({row.originId for row in report.traceRows}) != len(
        report.traceRows
    ):
        raise DriverCalibrationError("coefficient OOS report origin order mismatch")
    if (
        report.oosStart != report.traceRows[0].originEventTime
        or report.oosThrough != report.traceRows[-1].originEventTime
        or report.labelThrough != max(row.targetAvailableAt for row in report.traceRows)
    ):
        raise DriverCalibrationError("coefficient OOS report window mismatch")


def _validateCoefficientReportRows(report: DriverCoefficientOosReport) -> tuple[float, float, float, float]:
    """행마다 예측·잔차 항등식을 다시 계산하고 손실 누적값을 원래 순서로 되돌린다."""
    squared = 0.0
    baselineSquared = 0.0
    absolute = 0.0
    residualTotal = 0.0
    for index, row in enumerate(report.traceRows):
        originEventTime = _dateText(row.originEventTime, f"oosReport.originEventTime.{index}")
        originKnowledgeAsOf = _dateText(row.originKnowledgeAsOf, f"oosReport.originKnowledgeAsOf.{index}")
        sourceAvailableAt = _dateText(row.sourceAvailableAt, f"oosReport.sourceAvailableAt.{index}")
        targetEventTime = _dateText(row.targetEventTime, f"oosReport.targetEventTime.{index}")
        targetAvailableAt = _dateText(row.targetAvailableAt, f"oosReport.targetAvailableAt.{index}")
        if sourceAvailableAt > originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient OOS report source availability mismatch")
        if targetEventTime <= originEventTime or targetAvailableAt <= originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient OOS report target timing mismatch")
        sourceValue = _finite(row.sourceValue, f"oosReport.sourceValue.{index}")
        targetValue = _finite(row.targetValue, f"oosReport.targetValue.{index}")
        predictedValue = _finite(row.predictedValue, f"oosReport.predictedValue.{index}")
        baselineValue = _finite(row.baselineValue, f"oosReport.baselineValue.{index}")
        residual = _finite(row.residual, f"oosReport.residual.{index}")
        baselineResidual = _finite(row.baselineResidual, f"oosReport.baselineResidual.{index}")
        if not row.sourceRef or not row.labelSourceRef:
            raise DriverCalibrationError("coefficient OOS report source refs mismatch")
        _assertClose(predictedValue, report.coefficient * sourceValue, "prediction")
        _assertClose(residual, targetValue - predictedValue, "residual")
        _assertClose(baselineValue, report.baselineValue, "baseline")
        _assertClose(baselineResidual, targetValue - baselineValue, "baseline residual")
        squared += residual * residual
        baselineSquared += baselineResidual * baselineResidual
        absolute += abs(residual)
        residualTotal += residual
    return squared, baselineSquared, absolute, residualTotal


def _validateCoefficientReport(report: DriverCoefficientOosReport) -> None:
    """OOS 보고서를 정체성·창·행·지표 순으로 처음부터 다시 계산해 대조한다."""
    _validateCoefficientReportIdentity(report)
    _validateCoefficientReportWindow(report)
    squared, baselineSquared, absolute, residualTotal = _validateCoefficientReportRows(report)
    mse = squared / report.nOosOrigins
    baselineMse = baselineSquared / report.nOosOrigins
    if baselineMse <= 1e-24:
        raise DriverCalibrationError("coefficient OOS report baseline loss mismatch")
    bias = residualTotal / report.nOosOrigins
    _assertClose(report.mse, mse, "mse")
    _assertClose(report.baselineMse, baselineMse, "baselineMse")
    _assertClose(report.rmse, math.sqrt(mse), "rmse")
    _assertClose(report.mae, absolute / report.nOosOrigins, "mae")
    _assertClose(report.bias, bias, "bias")
    _assertClose(report.skillVsBaseline, 1.0 - mse / baselineMse, "skill")
    if report.oosGridHash != _oosGridHashFromTraceRows(report.traceRows):
        raise DriverCalibrationError("coefficient OOS report grid hash mismatch")
    if report.oosOutcomeHash != _oosOutcomeHashFromTraceRows(report.traceRows):
        raise DriverCalibrationError("coefficient OOS report outcome hash mismatch")
    if report.predictionTraceHash != _predictionTraceHash(
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
        raise DriverCalibrationError("coefficient OOS report trace hash mismatch")
    if (report.status == "oosEligible") != (not report.reasons):
        raise DriverCalibrationError("coefficient OOS report status mismatch")


def _validateOosFrameBinding(
    oosFrameBinding: DriverObservationFrameBinding,
    spec: DriverCoefficientOosSpec,
    receipt: DriverCoefficientCalibrationReceipt,
    *,
    rowCount: int,
) -> None:
    """판정 프레임 결속이 OOS spec 부모와 영수증 의미에 모두 맞는지 검사한다."""
    _validateFrameBinding(oosFrameBinding, "OOS")
    if (
        oosFrameBinding.rowCount != rowCount
        or oosFrameBinding.sourceBatchReceiptId not in spec.sourceParentReceiptIds
        or oosFrameBinding.labelBatchReceiptId not in spec.labelParentReceiptIds
        or oosFrameBinding.sourceVariableId != receipt.sourceVariableId
        or oosFrameBinding.targetVariableId != receipt.targetVariableId
        or oosFrameBinding.sourceUnit != receipt.sourceUnit
        or oosFrameBinding.targetUnit != receipt.targetUnit
    ):
        raise DriverCalibrationError("coefficient OOS observation frame binding mismatch")


def _scoreOosRows(
    receipt: DriverCoefficientCalibrationReceipt,
    rows: tuple[dict, ...],
    baselineValue: float,
) -> tuple[list[DriverCoefficientOosTraceRow], float, float, float, float]:
    """얼린 계수로 held-out 행을 채점하고 손실을 원래 누적 순서로 되돌린다."""
    traceRows: list[DriverCoefficientOosTraceRow] = []
    squared = 0.0
    absolute = 0.0
    residualTotal = 0.0
    baselineSquared = 0.0
    for item in rows:
        predicted = receipt.intercept + receipt.coefficient * item["sourceValue"]
        residual = item["targetValue"] - predicted
        baselineResidual = item["targetValue"] - baselineValue
        squared += residual * residual
        absolute += abs(residual)
        residualTotal += residual
        baselineSquared += baselineResidual * baselineResidual
        traceRows.append(
            DriverCoefficientOosTraceRow(
                originId=item["originId"],
                originEventTime=item["originEventTime"],
                originKnowledgeAsOf=item["originKnowledgeAsOf"],
                sourceAvailableAt=item["sourceAvailableAt"],
                targetEventTime=item["targetEventTime"],
                targetAvailableAt=item["targetAvailableAt"],
                sourceValue=item["sourceValue"],
                targetValue=item["targetValue"],
                predictedValue=predicted,
                baselineValue=baselineValue,
                residual=residual,
                baselineResidual=baselineResidual,
                sourceRef=item["sourceRef"],
                labelSourceRef=item["labelSourceRef"],
            )
        )
    return traceRows, squared, absolute, residualTotal, baselineSquared


def evaluateDriverCoefficientOos(
    receipt: DriverCoefficientCalibrationReceipt,
    frame: pl.DataFrame,
    spec: DriverCoefficientOosSpec,
    *,
    evaluationKnowledgeAsOf: str,
    oosFrameBinding: DriverObservationFrameBinding | None = None,
) -> DriverCoefficientOosReport:
    """Score a fixed coefficient on held-out PIT origins.

    Args:
        receipt: Calibration receipt whose coefficient is frozen before OOS scoring.
        frame: Held-out origin rows with source and target availability dates.
        spec: OOS thresholds, baseline, and artifact step contract.
        evaluationKnowledgeAsOf: Date when held-out labels are allowed to be known.
        oosFrameBinding: Optional replayable signed provider observation frame binding.

    Returns:
        Unsigned ``DriverCoefficientOosReport``. It is eligible for signing only when
        ``status`` is ``oosEligible``.

    Raises:
        DriverCalibrationError: If OOS timing, rows, units, or protocol fields are invalid.

    Example:
        ``report = evaluateDriverCoefficientOos(receipt, frame, spec, evaluationKnowledgeAsOf="20251231")``
    """

    _validateOosSpec(spec)
    cutoff = _dateText(evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf")
    rows, oosStart, oosThrough, labelThrough = _cleanOosRows(
        frame,
        spec,
        receipt,
        evaluationKnowledgeAsOf=cutoff,
    )
    if oosFrameBinding is not None:
        _validateOosFrameBinding(oosFrameBinding, spec, receipt, rowCount=len(rows))
    if receipt.status == "rejected" or receipt.validationStatus == "rejected":
        raise DriverCalibrationError("rejected coefficient receipt cannot be OOS evaluated")
    expectedUnit = f"{OPERATING_TARGET_UNITS[receipt.targetShock]}/{receipt.sourceUnit}"
    if receipt.coefficientUnit != expectedUnit:
        raise DriverCalibrationError("coefficient receipt unit drift")
    baselineValue = _finite(spec.baselineValue, "oos.baselineValue")
    traceRows, squared, absolute, residualTotal, baselineSquared = _scoreOosRows(receipt, rows, baselineValue)
    nOrigins = len(traceRows)
    mse = squared / nOrigins
    baselineMse = baselineSquared / nOrigins
    if baselineMse <= 1e-24:
        raise DriverCalibrationError("coefficient OOS baseline has no loss to beat")
    rmse = math.sqrt(mse)
    mae = absolute / nOrigins
    bias = residualTotal / nOrigins
    skill = 1.0 - mse / baselineMse
    reasons = _oosRejectionReasons(receipt, spec, nOrigins=nOrigins, skill=skill, rmse=rmse, bias=bias)
    status = "oosEligible" if not reasons else "rejected"
    oosSpecHash = canonicalPayloadHash(
        {"version": COEFFICIENT_OOS_VERSION, "spec": spec, "receipt": receipt.receiptHash}
    )
    oosGridHash = _oosGridHashFromTraceRows(tuple(traceRows))
    oosOutcomeHash = _oosOutcomeHashFromTraceRows(tuple(traceRows))
    predictionTraceHash = _predictionTraceHash(
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
            *(row.sourceRef for row in traceRows),
            *(row.labelSourceRef for row in traceRows),
            f"driverCoefficientFit:{receipt.receiptHash}",
            f"coefficientOosSpec:{oosSpecHash}",
            f"coefficientOosGrid:{oosGridHash}",
            f"coefficientOosOutcome:{oosOutcomeHash}",
            f"coefficientPredictionTrace:{predictionTraceHash}",
            f"fitFrame:{receipt.fitFrameBinding.frameHash}" if receipt.fitFrameBinding is not None else "",
            f"oosFrame:{oosFrameBinding.frameHash}" if oosFrameBinding is not None else "",
            f"oosFrameSpec:{oosFrameBinding.specHash}" if oosFrameBinding is not None else "",
            *(f"fitSourceParentReceipt:{receiptId}" for receiptId in receipt.sourceParentReceiptIds),
            *(f"fitLabelParentReceipt:{receiptId}" for receiptId in receipt.labelParentReceiptIds),
            *(f"oosSourceParentReceipt:{receiptId}" for receiptId in spec.sourceParentReceiptIds),
            *(f"oosLabelParentReceipt:{receiptId}" for receiptId in spec.labelParentReceiptIds),
        )
    )
    provisional = DriverCoefficientOosReport(
        evaluationId=spec.evaluationId,
        reportId="",
        generatorVersion=COEFFICIENT_OOS_VERSION,
        status=status,
        admissionStatus="unsigned",
        receiptHash=receipt.receiptHash,
        receiptId=receipt.receiptId,
        calibrationId=receipt.calibrationId,
        sourceVariableId=receipt.sourceVariableId,
        targetVariableId=receipt.targetVariableId,
        targetShock=receipt.targetShock,
        coefficient=receipt.coefficient,
        coefficientUnit=receipt.coefficientUnit,
        pathSetHash=receipt.pathSetHash,
        factorContractHash=receipt.factorContractHash,
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
        warnings=("coefficientOosReportUnsigned",),
        sourceRefs=sourceRefs,
        fitSourceParentReceiptIds=receipt.sourceParentReceiptIds,
        fitLabelParentReceiptIds=receipt.labelParentReceiptIds,
        oosSourceParentReceiptIds=spec.sourceParentReceiptIds,
        oosLabelParentReceiptIds=spec.labelParentReceiptIds,
        traceRows=tuple(traceRows),
        fitFrameBinding=receipt.fitFrameBinding,
        oosFrameBinding=oosFrameBinding,
    )
    report = DriverCoefficientOosReport(
        **{
            name: (
                canonicalPayloadHash(_oosReportPayload(provisional))
                if name == "reportId"
                else getattr(provisional, name)
            )
            for name in provisional.__dataclass_fields__
        }
    )
    _validateCoefficientReport(report)
    return report


def evaluateDriverCoefficientOosFromObservationFrame(
    receipt: DriverCoefficientCalibrationReceipt,
    observationFrame: DriverCoefficientObservationFrame,
    spec: DriverCoefficientOosSpec,
    *,
    evaluationKnowledgeAsOf: str,
) -> DriverCoefficientOosReport:
    """Evaluate a coefficient only on a typed signed provider observation frame.

    Args:
        receipt: Frozen fit receipt whose coefficient is being admitted.
        observationFrame: Typed provider observation frame built from signed exact held-out batches.
        spec: OOS thresholds and parent receipt contract matching the frame.
        evaluationKnowledgeAsOf: Date when held-out labels may be known.

    Returns:
        ``DriverCoefficientOosReport`` carrying replayable OOS frame binding.

    Raises:
        DriverCalibrationError: If the OOS frame parents or meaning drift from the report contract.

    Example:
        ``report = evaluateDriverCoefficientOosFromObservationFrame(receipt, frame, spec, evaluationKnowledgeAsOf="20251231")``
    """

    binding = _frameBindingFromObservationFrame(observationFrame)
    if (
        observationFrame.sourceParentReceiptIds != spec.sourceParentReceiptIds
        or observationFrame.labelParentReceiptIds != spec.labelParentReceiptIds
    ):
        raise DriverCalibrationError("coefficient OOS observation frame parent contract mismatch")
    return evaluateDriverCoefficientOos(
        receipt,
        observationFrame.frame,
        spec,
        evaluationKnowledgeAsOf=evaluationKnowledgeAsOf,
        oosFrameBinding=binding,
    )


def driverCoefficientAdmissionArtifact(report: DriverCoefficientOosReport) -> bytes:
    """Return canonical bytes to store under an admission artifact address.

    Args:
        report: OOS report returned by ``evaluateDriverCoefficientOos``.

    Returns:
        Canonical JSON bytes whose SHA-256 is the coefficient admission subject.

    Raises:
        DriverCalibrationError: If the report protocol or hash is invalid.

    Example:
        ``artifact = driverCoefficientAdmissionArtifact(report)``
    """

    _validateCoefficientReport(report)
    return canonicalPayloadBytes(_oosReportPayload(report))


def driverCoefficientAdmissionSubjectHash(report: DriverCoefficientOosReport) -> str:
    """Return the content hash used as the signed coefficient subject.

    Args:
        report: OOS report returned by ``evaluateDriverCoefficientOos``.

    Returns:
        SHA-256 subject hash for an admission registry receipt.

    Raises:
        DriverCalibrationError: If the report protocol or hash is invalid.

    Example:
        ``subject = driverCoefficientAdmissionSubjectHash(report)``
    """

    return canonicalPayloadHash(_oosReportPayload(report))


def driverCoefficientAdmissionParentReceiptIds(report: DriverCoefficientOosReport) -> tuple[str, ...]:
    """Return the exact source and label parents required by a coefficient admission.

    Args:
        report: OOS report returned by ``evaluateDriverCoefficientOos``.

    Returns:
        Ordered unique parent receipt identifiers for the signed admission receipt.

    Raises:
        DriverCalibrationError: If the report protocol or parent identifiers are invalid.

    Example:
        ``parents = driverCoefficientAdmissionParentReceiptIds(report)``
    """

    _validateCoefficientReport(report)
    return _dedupe(
        (
            *report.fitSourceParentReceiptIds,
            *report.fitLabelParentReceiptIds,
            *report.oosSourceParentReceiptIds,
            *report.oosLabelParentReceiptIds,
        )
    )
