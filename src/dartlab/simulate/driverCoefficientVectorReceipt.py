"""벡터 계수 영수증의 정규 직렬화와 프로토콜 재검증.

스칼라 쪽 `driverCoefficientReceipt` 의 쌍이다. 계수 하나가 아니라 순서 있는 계수
항 묶음이라, 항 순서·단위·source 계약 해시까지 영수증 정체성에 들어간다. 그 차이가
스칼라와 공유할 수 없는 지점이라 별도 모듈로 둔다.
"""

from __future__ import annotations

import math

from dartlab.simulate.driverCalibrationContracts import (
    MULTIVARIABLE_CALIBRATION_VERSION,
    DriverCalibrationError,
    DriverDesignColumnSpec,
    MultivariableDriverCoefficientCalibrationReceipt,
    MultivariableDriverCoefficientOosReport,
    MultivariableDriverCoefficientOosTraceRow,
    MultivariableDriverCoefficientTerm,
    MultivariableDriverCoefficientTraceRow,
    MultivariableDriverSourceCell,
)
from dartlab.simulate.driverCalibrationKernel import (
    _assertClose,
    _dateText,
    _driverSourceFactorContractHash,
    _finite,
    _validDigest,
)
from dartlab.simulate.driverCoefficientFrameBinding import _validateDesignFrameBinding
from dartlab.simulate.operatingBridge import OPERATING_TARGET_UNITS
from dartlab.simulate.vintage import canonicalPayloadHash


def _predictMultivariable(
    sourceCells: tuple[MultivariableDriverSourceCell, ...],
    coefficientTerms: tuple[MultivariableDriverCoefficientTerm, ...],
) -> float:
    termByVariable = {term.variableId: term for term in coefficientTerms}
    return sum(termByVariable[cell.variableId].coefficient * cell.value for cell in sourceCells)


def _featureSpecHash(
    sourceColumns: tuple[DriverDesignColumnSpec, ...],
    coefficientTerms: tuple[MultivariableDriverCoefficientTerm, ...],
) -> str:
    return canonicalPayloadHash(
        tuple(
            {
                "position": index,
                "column": column,
                "term": coefficientTerms[index],
            }
            for index, column in enumerate(sourceColumns)
        )
    )


def _coefficientVectorHash(coefficientTerms: tuple[MultivariableDriverCoefficientTerm, ...]) -> str:
    return canonicalPayloadHash(
        tuple(
            {
                "position": term.position,
                "variableId": term.variableId,
                "coefficient": term.coefficient,
                "coefficientUnit": term.coefficientUnit,
                "sourceFactorContractHash": term.sourceFactorContractHash,
            }
            for term in coefficientTerms
        )
    )


def _multivariableOriginGridHashFromTraceRows(
    traceRows: tuple[MultivariableDriverCoefficientTraceRow | MultivariableDriverCoefficientOosTraceRow, ...],
) -> str:
    return canonicalPayloadHash(
        tuple(
            {
                "originId": row.originId,
                "originEventTime": row.originEventTime,
                "originKnowledgeAsOf": row.originKnowledgeAsOf,
                "sourceAvailableAt": row.sourceAvailableAt,
                "targetEventTime": row.targetEventTime,
                "targetAvailableAt": row.targetAvailableAt,
                "sourceCells": tuple(
                    {
                        "variableId": cell.variableId,
                        "eventTime": cell.eventTime,
                        "availableAt": cell.availableAt,
                        "knowledgeAsOf": cell.knowledgeAsOf,
                        "unit": cell.unit,
                        "sourceRef": cell.sourceRef,
                    }
                    for cell in row.sourceCells
                ),
            }
            for row in traceRows
        )
    )


def _multivariableOutcomeHashFromTraceRows(
    traceRows: tuple[MultivariableDriverCoefficientTraceRow | MultivariableDriverCoefficientOosTraceRow, ...],
) -> str:
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


def _multivariableCoefficientTraceHash(receipt: MultivariableDriverCoefficientCalibrationReceipt) -> str:
    return canonicalPayloadHash(
        {
            "registryHash": receipt.registryHash,
            "pathSetHash": receipt.pathSetHash,
            "pathSetInputHash": receipt.pathSetInputHash,
            "factorContractHash": receipt.factorContractHash,
            "featureSpecHash": receipt.featureSpecHash,
            "designFrameHash": receipt.designFrameHash,
            "coefficientVectorHash": receipt.coefficientVectorHash,
            "calibrationSpecHash": receipt.calibrationSpecHash,
            "originGridHash": receipt.originGridHash,
            "targetOutcomeHash": receipt.targetOutcomeHash,
            "coefficientTerms": receipt.coefficientTerms,
            "residualStandardError": receipt.residualStandardError,
            "rSquared": receipt.rSquared,
            "traceRows": receipt.traceRows,
        }
    )


def _multivariableCalibrationReceiptPayload(receipt: MultivariableDriverCoefficientCalibrationReceipt) -> dict:
    fitRef = f"driverCoefficientVectorFit:{receipt.receiptHash}"
    baseSourceRefs = tuple(item for item in receipt.sourceRefs if item != fitRef)
    return {
        "version": MULTIVARIABLE_CALIBRATION_VERSION,
        "calibrationId": receipt.calibrationId,
        "status": receipt.status,
        "validationStatus": receipt.validationStatus,
        "historyStatus": receipt.historyStatus,
        "calibrationKnowledgeAsOf": receipt.calibrationKnowledgeAsOf,
        "sourceVariableIds": receipt.sourceVariableIds,
        "targetVariableId": receipt.targetVariableId,
        "targetShock": receipt.targetShock,
        "targetUnit": receipt.targetUnit,
        "coefficientTerms": receipt.coefficientTerms,
        "intercept": receipt.intercept,
        "residualStandardError": receipt.residualStandardError,
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
        "featureSpecHash": receipt.featureSpecHash,
        "designFrameHash": receipt.designFrameHash,
        "coefficientVectorHash": receipt.coefficientVectorHash,
        "calibrationSpecHash": receipt.calibrationSpecHash,
        "originGridHash": receipt.originGridHash,
        "targetOutcomeHash": receipt.targetOutcomeHash,
        "coefficientTraceHash": receipt.coefficientTraceHash,
        "warnings": receipt.warnings,
        "sourceRefs": baseSourceRefs,
        "sourceParentReceiptIds": receipt.sourceParentReceiptIds,
        "labelParentReceiptIds": receipt.labelParentReceiptIds,
        "fitDesignFrameBinding": receipt.fitDesignFrameBinding,
    }


def _validateVectorReceiptIdentity(receipt: MultivariableDriverCoefficientCalibrationReceipt) -> None:
    """영수증 정체성 (프로토콜 필드·항 순서·다이제스트·설계 프레임) 을 검사한다."""
    if (
        receipt.generatorVersion != MULTIVARIABLE_CALIBRATION_VERSION
        or receipt.status != "retrospectiveOnly"
        or receipt.validationStatus != "retrospectiveOnly"
        or receipt.nOrigins < 1
        or receipt.droppedRows < 0
        or receipt.intercept != 0.0
        or not receipt.traceRows
        or receipt.receiptId != receipt.receiptHash
        or not receipt.sourceRefs
        or len(receipt.sourceVariableIds) != len(receipt.coefficientTerms)
    ):
        raise DriverCalibrationError("coefficient vector calibration receipt protocol mismatch")
    if tuple(term.variableId for term in receipt.coefficientTerms) != receipt.sourceVariableIds:
        raise DriverCalibrationError("coefficient vector calibration receipt source variable order mismatch")
    if tuple(term.position for term in receipt.coefficientTerms) != tuple(range(len(receipt.coefficientTerms))):
        raise DriverCalibrationError("coefficient vector calibration receipt term position mismatch")
    for label, value in (
        ("receiptHash", receipt.receiptHash),
        ("registryHash", receipt.registryHash),
        ("pathSetHash", receipt.pathSetHash),
        ("pathSetInputHash", receipt.pathSetInputHash),
        ("factorContractHash", receipt.factorContractHash),
        ("featureSpecHash", receipt.featureSpecHash),
        ("designFrameHash", receipt.designFrameHash),
        ("coefficientVectorHash", receipt.coefficientVectorHash),
        ("calibrationSpecHash", receipt.calibrationSpecHash),
        ("originGridHash", receipt.originGridHash),
        ("targetOutcomeHash", receipt.targetOutcomeHash),
        ("coefficientTraceHash", receipt.coefficientTraceHash),
    ):
        if not _validDigest(value):
            raise DriverCalibrationError(f"coefficient vector calibration receipt {label} is invalid")
    _validateDesignFrameBinding(receipt.fitDesignFrameBinding, "fit")
    if (
        receipt.fitDesignFrameBinding.rowCount != receipt.nOrigins
        or receipt.fitDesignFrameBinding.frameHash != receipt.designFrameHash
        or tuple(column.variableId for column in receipt.fitDesignFrameBinding.sourceColumns)
        != receipt.sourceVariableIds
    ):
        raise DriverCalibrationError("coefficient vector calibration receipt design frame mismatch")
    if receipt.featureSpecHash != _featureSpecHash(
        receipt.fitDesignFrameBinding.sourceColumns,
        receipt.coefficientTerms,
    ):
        raise DriverCalibrationError("coefficient vector calibration receipt feature spec hash mismatch")
    if receipt.coefficientVectorHash != _coefficientVectorHash(receipt.coefficientTerms):
        raise DriverCalibrationError("coefficient vector calibration receipt coefficient vector hash mismatch")


def _validateVectorReceiptTerms(receipt: MultivariableDriverCoefficientCalibrationReceipt) -> None:
    """계수 항마다 단위와 source 계약 해시를 다시 유도해 대조한다."""
    for term in receipt.coefficientTerms:
        _finite(term.coefficient, f"coefficientVector.{term.variableId}")
        expectedUnit = f"{OPERATING_TARGET_UNITS[receipt.targetShock]}/{term.sourceUnit}"
        if term.coefficientUnit != expectedUnit:
            raise DriverCalibrationError("coefficient vector calibration receipt coefficient unit drift")
        expectedContractHash = _driverSourceFactorContractHash(
            variableId=term.variableId,
            unit=term.sourceUnit,
            frequency=term.sourceFrequency,
            timing=term.sourceTiming,
            transformId=term.sourceTransformId,
        )
        if term.sourceFactorContractHash != expectedContractHash:
            raise DriverCalibrationError("coefficient vector calibration receipt source factor contract mismatch")


def _validateVectorReceiptWindow(receipt: MultivariableDriverCoefficientCalibrationReceipt) -> None:
    """fit ref·내용 해시·origin 정렬·적합 창 경계를 검사한다."""
    if f"driverCoefficientVectorFit:{receipt.receiptHash}" not in receipt.sourceRefs:
        raise DriverCalibrationError("coefficient vector calibration receipt fit ref is missing")
    if receipt.receiptHash != canonicalPayloadHash(_multivariableCalibrationReceiptPayload(receipt)):
        raise DriverCalibrationError("coefficient vector calibration receipt hash mismatch")
    if receipt.nOrigins != len(receipt.traceRows):
        raise DriverCalibrationError("coefficient vector calibration receipt origin count mismatch")
    originKeys = tuple((row.originEventTime, row.originId) for row in receipt.traceRows)
    if originKeys != tuple(sorted(originKeys)) or len({row.originId for row in receipt.traceRows}) != len(
        receipt.traceRows
    ):
        raise DriverCalibrationError("coefficient vector calibration receipt origin order mismatch")
    if (
        receipt.fitStart != receipt.traceRows[0].originEventTime
        or receipt.fitThrough != receipt.traceRows[-1].originEventTime
        or receipt.labelThrough != max(row.targetAvailableAt for row in receipt.traceRows)
    ):
        raise DriverCalibrationError("coefficient vector calibration receipt window mismatch")


def _validateVectorReceiptRows(receipt: MultivariableDriverCoefficientCalibrationReceipt) -> None:
    """trace 행마다 셀 순서·PIT 시점·적합 잔차 항등식을 다시 계산해 대조한다."""
    for index, row in enumerate(receipt.traceRows):
        originEventTime = _dateText(row.originEventTime, f"vectorReceipt.originEventTime.{index}")
        originKnowledgeAsOf = _dateText(row.originKnowledgeAsOf, f"vectorReceipt.originKnowledgeAsOf.{index}")
        sourceAvailableAt = _dateText(row.sourceAvailableAt, f"vectorReceipt.sourceAvailableAt.{index}")
        targetEventTime = _dateText(row.targetEventTime, f"vectorReceipt.targetEventTime.{index}")
        targetAvailableAt = _dateText(row.targetAvailableAt, f"vectorReceipt.targetAvailableAt.{index}")
        if sourceAvailableAt > originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient vector calibration receipt source timing mismatch")
        if targetEventTime <= originEventTime or targetAvailableAt <= originKnowledgeAsOf:
            raise DriverCalibrationError("coefficient vector calibration receipt target timing mismatch")
        if tuple(cell.variableId for cell in row.sourceCells) != receipt.sourceVariableIds:
            raise DriverCalibrationError("coefficient vector calibration receipt source cell order mismatch")
        for cell in row.sourceCells:
            _dateText(cell.eventTime, "vectorReceipt.cell.eventTime")
            _dateText(cell.availableAt, "vectorReceipt.cell.availableAt")
            _dateText(cell.knowledgeAsOf, "vectorReceipt.cell.knowledgeAsOf")
            _finite(cell.value, "vectorReceipt.cell.value")
            if not cell.sourceRef or not cell.unit:
                raise DriverCalibrationError("coefficient vector calibration receipt source cell ref mismatch")
        targetValue = _finite(row.targetValue, f"vectorReceipt.targetValue.{index}")
        fittedValue = _finite(row.fittedValue, f"vectorReceipt.fittedValue.{index}")
        residual = _finite(row.residual, f"vectorReceipt.residual.{index}")
        if not row.labelSourceRef:
            raise DriverCalibrationError("coefficient vector calibration receipt label ref mismatch")
        _assertClose(fittedValue, _predictMultivariable(row.sourceCells, receipt.coefficientTerms), "vector fitted")
        _assertClose(residual, targetValue - fittedValue, "vector residual")


def _validateMultivariableCalibrationReceipt(receipt: MultivariableDriverCoefficientCalibrationReceipt) -> None:
    """벡터 적합 영수증을 정체성·항·창·행 순으로 처음부터 다시 계산해 대조한다."""
    _validateVectorReceiptIdentity(receipt)
    _validateVectorReceiptTerms(receipt)
    _validateVectorReceiptWindow(receipt)
    _validateVectorReceiptRows(receipt)
    if receipt.originGridHash != _multivariableOriginGridHashFromTraceRows(receipt.traceRows):
        raise DriverCalibrationError("coefficient vector calibration receipt grid hash mismatch")
    if receipt.targetOutcomeHash != _multivariableOutcomeHashFromTraceRows(receipt.traceRows):
        raise DriverCalibrationError("coefficient vector calibration receipt outcome hash mismatch")
    if receipt.coefficientTraceHash != _multivariableCoefficientTraceHash(receipt):
        raise DriverCalibrationError("coefficient vector calibration receipt trace hash mismatch")


def _multivariableOosReportPayload(report: MultivariableDriverCoefficientOosReport) -> dict:
    return {name: getattr(report, name) for name in report.__dataclass_fields__ if name != "reportId"}


def _multivariablePredictionTraceHash(
    *,
    receiptHash: str,
    oosSpecHash: str,
    oosGridHash: str,
    oosOutcomeHash: str,
    traceRows: tuple[MultivariableDriverCoefficientOosTraceRow, ...],
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
