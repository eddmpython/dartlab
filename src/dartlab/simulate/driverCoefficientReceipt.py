"""스칼라 계수 영수증·보고서의 정규 직렬화와 프로토콜 재검증.

영수증 해시는 payload 직렬화 한 벌에만 의존해야 한다. 적합(fit) 과 판정(OOS) 이
각자 payload 를 만들면 같은 영수증이 두 해시를 갖게 되므로, 직렬화와 그 역검증을
두 소비자 위쪽 한 모듈에 모아 둔다.
"""

from __future__ import annotations

import math

from dartlab.simulate.driverCalibrationContracts import (
    CALIBRATION_VERSION,
    DriverCalibrationError,
    DriverCoefficientCalibrationReceipt,
    DriverCoefficientOosReport,
    DriverCoefficientOosTraceRow,
    DriverCoefficientTraceRow,
)
from dartlab.simulate.driverCalibrationKernel import (
    _assertClose,
    _dateText,
    _driverSourceFactorContractHash,
    _finite,
    _validDigest,
)
from dartlab.simulate.driverCoefficientFrameBinding import _validateFrameBinding
from dartlab.simulate.vintage import canonicalPayloadHash


def _calibrationOriginGridHashFromTraceRows(traceRows: tuple[DriverCoefficientTraceRow, ...]) -> str:
    return canonicalPayloadHash(
        tuple(
            {
                "originId": row.originId,
                "originEventTime": row.originEventTime,
                "originKnowledgeAsOf": row.originKnowledgeAsOf,
                "sourceAvailableAt": row.sourceAvailableAt,
                "targetEventTime": row.targetEventTime,
                "targetAvailableAt": row.targetAvailableAt,
            }
            for row in traceRows
        )
    )


def _calibrationCoefficientTraceHash(receipt: DriverCoefficientCalibrationReceipt) -> str:
    return canonicalPayloadHash(
        {
            "registryHash": receipt.registryHash,
            "pathSetHash": receipt.pathSetHash,
            "pathSetInputHash": receipt.pathSetInputHash,
            "factorContractHash": receipt.factorContractHash,
            "calibrationSpecHash": receipt.calibrationSpecHash,
            "originGridHash": receipt.originGridHash,
            "targetOutcomeHash": receipt.targetOutcomeHash,
            "coefficient": receipt.coefficient,
            "standardError": receipt.standardError,
            "rSquared": receipt.rSquared,
            "traceRows": receipt.traceRows,
        }
    )


def _calibrationReceiptPayload(receipt: DriverCoefficientCalibrationReceipt) -> dict:
    fitRef = f"driverCoefficientFit:{receipt.receiptHash}"
    baseSourceRefs = tuple(item for item in receipt.sourceRefs if item != fitRef)
    return {
        "version": CALIBRATION_VERSION,
        "calibrationId": receipt.calibrationId,
        "status": receipt.status,
        "validationStatus": receipt.validationStatus,
        "historyStatus": receipt.historyStatus,
        "calibrationKnowledgeAsOf": receipt.calibrationKnowledgeAsOf,
        "sourceVariableId": receipt.sourceVariableId,
        "targetVariableId": receipt.targetVariableId,
        "targetShock": receipt.targetShock,
        "sourceUnit": receipt.sourceUnit,
        "sourceFrequency": receipt.sourceFrequency,
        "sourceTiming": receipt.sourceTiming,
        "sourceTransformId": receipt.sourceTransformId,
        "sourceFactorContractHash": receipt.sourceFactorContractHash,
        "targetUnit": receipt.targetUnit,
        "coefficient": receipt.coefficient,
        "coefficientUnit": receipt.coefficientUnit,
        "intercept": receipt.intercept,
        "standardError": receipt.standardError,
        "rSquared": receipt.rSquared,
        "nOrigins": receipt.nOrigins,
        "droppedRows": receipt.droppedRows,
        "fitStart": receipt.fitStart,
        "fitThrough": receipt.fitThrough,
        "labelThrough": receipt.labelThrough,
        "lagSteps": receipt.lagSteps,
        "responseKernel": receipt.responseKernel,
        "modelFormula": receipt.modelFormula,
        "registryHash": receipt.registryHash,
        "pathSetHash": receipt.pathSetHash,
        "pathSetInputHash": receipt.pathSetInputHash,
        "factorContractHash": receipt.factorContractHash,
        "calibrationSpecHash": receipt.calibrationSpecHash,
        "originGridHash": receipt.originGridHash,
        "targetOutcomeHash": receipt.targetOutcomeHash,
        "coefficientTraceHash": receipt.coefficientTraceHash,
        "warnings": receipt.warnings,
        "sourceRefs": baseSourceRefs,
        "sourceParentReceiptIds": receipt.sourceParentReceiptIds,
        "labelParentReceiptIds": receipt.labelParentReceiptIds,
        "fitFrameBinding": receipt.fitFrameBinding,
    }


def _validateCalibrationReceiptIdentity(receipt: DriverCoefficientCalibrationReceipt) -> None:
    """영수증 자체의 정체성 (프로토콜 필드·다이제스트·내용 해시) 을 검사한다."""
    if (
        receipt.generatorVersion != CALIBRATION_VERSION
        or receipt.status != "retrospectiveOnly"
        or receipt.validationStatus != "retrospectiveOnly"
        or receipt.nOrigins < 1
        or receipt.droppedRows < 0
        or receipt.intercept != 0.0
        or not receipt.traceRows
        or receipt.receiptId != receipt.receiptHash
        or not receipt.sourceRefs
    ):
        raise DriverCalibrationError("coefficient calibration receipt protocol mismatch")
    for label, value in (
        ("receiptHash", receipt.receiptHash),
        ("registryHash", receipt.registryHash),
        ("pathSetHash", receipt.pathSetHash),
        ("pathSetInputHash", receipt.pathSetInputHash),
        ("factorContractHash", receipt.factorContractHash),
        ("sourceFactorContractHash", receipt.sourceFactorContractHash),
        ("calibrationSpecHash", receipt.calibrationSpecHash),
        ("originGridHash", receipt.originGridHash),
        ("targetOutcomeHash", receipt.targetOutcomeHash),
        ("coefficientTraceHash", receipt.coefficientTraceHash),
    ):
        if not _validDigest(value):
            raise DriverCalibrationError(f"coefficient calibration receipt {label} is invalid")
    expectedSourceFactorContractHash = _driverSourceFactorContractHash(
        variableId=receipt.sourceVariableId,
        unit=receipt.sourceUnit,
        frequency=receipt.sourceFrequency,
        timing=receipt.sourceTiming,
        transformId=receipt.sourceTransformId,
    )
    if receipt.sourceFactorContractHash != expectedSourceFactorContractHash:
        raise DriverCalibrationError("coefficient calibration receipt source factor contract mismatch")
    if f"driverCoefficientFit:{receipt.receiptHash}" not in receipt.sourceRefs:
        raise DriverCalibrationError("coefficient calibration receipt fit ref is missing")
    if receipt.receiptHash != canonicalPayloadHash(_calibrationReceiptPayload(receipt)):
        raise DriverCalibrationError("coefficient calibration receipt hash mismatch")
    if receipt.nOrigins != len(receipt.traceRows):
        raise DriverCalibrationError("coefficient calibration receipt origin count mismatch")
    if receipt.fitFrameBinding is not None:
        _validateFrameBinding(receipt.fitFrameBinding, "fit")
        if receipt.fitFrameBinding.rowCount != receipt.nOrigins:
            raise DriverCalibrationError("coefficient calibration receipt fit frame row count mismatch")


def _validateCalibrationReceiptWindow(receipt: DriverCoefficientCalibrationReceipt) -> None:
    """origin 정렬과 fit 창 경계가 trace 행과 일치하는지 검사한다."""
    originKeys = tuple((row.originEventTime, row.originId) for row in receipt.traceRows)
    if originKeys != tuple(sorted(originKeys)) or len({row.originId for row in receipt.traceRows}) != len(
        receipt.traceRows
    ):
        raise DriverCalibrationError("coefficient calibration receipt origin order mismatch")
    if (
        receipt.fitStart != receipt.traceRows[0].originEventTime
        or receipt.fitThrough != receipt.traceRows[-1].originEventTime
        or receipt.labelThrough != max(row.targetAvailableAt for row in receipt.traceRows)
    ):
        raise DriverCalibrationError("coefficient calibration receipt window mismatch")


def _validateCalibrationReceiptRows(receipt: DriverCoefficientCalibrationReceipt) -> None:
    """trace 행마다 PIT 시점과 적합 잔차 항등식을 다시 계산해 대조한다."""
    for index, row in enumerate(receipt.traceRows):
        originEventTime = _dateText(row.originEventTime, f"calibrationReceipt.originEventTime.{index}")
        originKnowledgeAsOf = _dateText(row.originKnowledgeAsOf, f"calibrationReceipt.originKnowledgeAsOf.{index}")
        sourceAvailableAt = _dateText(row.sourceAvailableAt, f"calibrationReceipt.sourceAvailableAt.{index}")
        targetEventTime = _dateText(row.targetEventTime, f"calibrationReceipt.targetEventTime.{index}")
        targetAvailableAt = _dateText(row.targetAvailableAt, f"calibrationReceipt.targetAvailableAt.{index}")
        if sourceAvailableAt > originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient calibration receipt source timing mismatch")
        if targetEventTime <= originEventTime or targetAvailableAt <= originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient calibration receipt target timing mismatch")
        sourceValue = _finite(row.sourceValue, f"calibrationReceipt.sourceValue.{index}")
        targetValue = _finite(row.targetValue, f"calibrationReceipt.targetValue.{index}")
        fittedValue = _finite(row.fittedValue, f"calibrationReceipt.fittedValue.{index}")
        residual = _finite(row.residual, f"calibrationReceipt.residual.{index}")
        if not row.sourceRef or not row.labelSourceRef:
            raise DriverCalibrationError("coefficient calibration receipt source refs mismatch")
        _assertClose(fittedValue, receipt.coefficient * sourceValue, "calibration fitted value")
        _assertClose(residual, targetValue - fittedValue, "calibration residual")


def _validateCalibrationReceipt(receipt: DriverCoefficientCalibrationReceipt) -> None:
    """적합 영수증이 스스로 재생 가능한지 정체성·창·행 순서로 검사한다."""
    _validateCalibrationReceiptIdentity(receipt)
    _validateCalibrationReceiptWindow(receipt)
    _validateCalibrationReceiptRows(receipt)
    if receipt.originGridHash != _calibrationOriginGridHashFromTraceRows(receipt.traceRows):
        raise DriverCalibrationError("coefficient calibration receipt grid hash mismatch")
    if receipt.coefficientTraceHash != _calibrationCoefficientTraceHash(receipt):
        raise DriverCalibrationError("coefficient calibration receipt trace hash mismatch")


def _oosReportPayload(report: DriverCoefficientOosReport) -> dict:
    return {name: getattr(report, name) for name in report.__dataclass_fields__ if name != "reportId"}


def _oosGridHashFromTraceRows(traceRows: tuple[DriverCoefficientOosTraceRow, ...]) -> str:
    return canonicalPayloadHash(
        tuple(
            {
                "originId": row.originId,
                "originEventTime": row.originEventTime,
                "originKnowledgeAsOf": row.originKnowledgeAsOf,
                "sourceAvailableAt": row.sourceAvailableAt,
                "targetEventTime": row.targetEventTime,
                "targetAvailableAt": row.targetAvailableAt,
            }
            for row in traceRows
        )
    )


def _oosOutcomeHashFromTraceRows(traceRows: tuple[DriverCoefficientOosTraceRow, ...]) -> str:
    return canonicalPayloadHash(
        tuple(
            {
                "originId": row.originId,
                "targetValue": row.targetValue,
                "targetEventTime": row.targetEventTime,
                "targetAvailableAt": row.targetAvailableAt,
                "labelSourceRef": row.labelSourceRef,
            }
            for row in traceRows
        )
    )


def _predictionTraceHash(
    *,
    receiptHash: str,
    oosSpecHash: str,
    oosGridHash: str,
    oosOutcomeHash: str,
    traceRows: tuple[DriverCoefficientOosTraceRow, ...],
    mse: float,
    baselineMse: float,
    skillVsBaseline: float,
    bias: float,
) -> str:
    return canonicalPayloadHash(
        {
            "receiptHash": receiptHash,
            "oosSpecHash": oosSpecHash,
            "oosGridHash": oosGridHash,
            "oosOutcomeHash": oosOutcomeHash,
            "traceRows": traceRows,
            "mse": mse,
            "baselineMse": baselineMse,
            "skillVsBaseline": skillVsBaseline,
            "bias": bias,
        }
    )
