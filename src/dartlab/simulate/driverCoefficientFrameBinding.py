"""서명된 provider 관측 프레임 결속의 검증과 재생.

fit·OOS·승인 세 단계가 모두 "이 영수증이 가리키는 프레임을 지금 다시 지어도
같은가" 를 묻는다. 그 질문 하나만 떼어 두면 세 단계가 각자 재생 규칙을 들고
갈라질 여지가 없다. 스칼라 관측 프레임과 벡터 설계 프레임은 대상만 다른
같은 질문이라 나란히 둔다.
"""

from __future__ import annotations

from dartlab.simulate.admissionRegistry import AdmissionReceipt, AdmissionVerifier, artifactPath
from dartlab.simulate.driverCalibrationContracts import (
    DriverCalibrationError,
    DriverObservationFrameBinding,
    MultivariableDriverDesignFrameBinding,
)
from dartlab.simulate.driverCalibrationKernel import _validateReceiptIds, _validDigest
from dartlab.simulate.driverObservationFrames import (
    DRIVER_DESIGN_FRAME_VERSION,
    DRIVER_OBSERVATION_FRAME_VERSION,
    DriverCoefficientObservationFrame,
    DriverCoefficientObservationFrameSpec,
    MultivariableDriverCoefficientObservationFrame,
    MultivariableDriverCoefficientObservationFrameSpec,
    _columnOrderPayload,
    buildDriverCoefficientObservationFrame,
    buildMultivariableDriverCoefficientObservationFrame,
)
from dartlab.simulate.stateCompiler import _batchFromArtifact
from dartlab.simulate.vintage import canonicalPayloadHash


def _frameSpecFromBinding(binding: DriverObservationFrameBinding) -> DriverCoefficientObservationFrameSpec:
    return DriverCoefficientObservationFrameSpec(
        frameId=binding.frameId,
        sourceSignalId=binding.sourceSignalId,
        labelSignalId=binding.labelSignalId,
        sourceVariableId=binding.sourceVariableId,
        targetVariableId=binding.targetVariableId,
        sourceUnit=binding.sourceUnit,
        targetUnit=binding.targetUnit,
        frequency=binding.frequency,
        stepSpan=binding.stepSpan,
        horizonSteps=binding.horizonSteps,
        originStart=binding.originStart,
        originThrough=binding.originThrough,
        sourceEvidenceRoles=binding.sourceEvidenceRoles,
        labelEvidenceRoles=binding.labelEvidenceRoles,
        selectionRuleId=binding.selectionRuleId,
        originKnowledgePolicy=binding.originKnowledgePolicy,
        sourceRefPolicy=binding.sourceRefPolicy,
        schemaVersion=binding.schemaVersion,
    )


def _validateFrameBinding(binding: DriverObservationFrameBinding, label: str) -> None:
    if (
        not isinstance(binding, DriverObservationFrameBinding)
        or binding.schemaVersion != DRIVER_OBSERVATION_FRAME_VERSION
        or not binding.frameId
        or binding.rowCount < 1
        or not binding.sourceSignalId
        or not binding.labelSignalId
        or not binding.sourceVariableId
        or not binding.targetVariableId
        or not binding.sourceUnit
        or not binding.targetUnit
        or not binding.frequency
        or binding.stepSpan < 1
        or binding.horizonSteps < 1
    ):
        raise DriverCalibrationError(f"coefficient {label} observation frame binding is incomplete")
    for field, value in (
        ("frameHash", binding.frameHash),
        ("specHash", binding.specHash),
        ("sourceBatchReceiptId", binding.sourceBatchReceiptId),
        ("labelBatchReceiptId", binding.labelBatchReceiptId),
    ):
        if not _validDigest(value):
            raise DriverCalibrationError(f"coefficient {label} observation frame {field} is invalid")
    if binding.specHash != canonicalPayloadHash(_frameSpecFromBinding(binding)):
        raise DriverCalibrationError(f"coefficient {label} observation frame spec hash mismatch")


def _frameBindingFromObservationFrame(frame: DriverCoefficientObservationFrame) -> DriverObservationFrameBinding:
    if not isinstance(frame, DriverCoefficientObservationFrame) or frame.spec is None:
        raise DriverCalibrationError("coefficient observation frame binding requires typed frame")
    if canonicalPayloadHash(frame.spec) != frame.specHash:
        raise DriverCalibrationError("coefficient observation frame spec hash mismatch")
    if frame.rowCount != frame.frame.height:
        raise DriverCalibrationError("coefficient observation frame row count mismatch")
    binding = DriverObservationFrameBinding(
        frameId=frame.frameId,
        frameHash=frame.frameHash,
        specHash=frame.specHash,
        rowCount=frame.rowCount,
        sourceBatchReceiptId=frame.sourceBatchReceiptId,
        labelBatchReceiptId=frame.labelBatchReceiptId,
        sourceSignalId=frame.spec.sourceSignalId,
        labelSignalId=frame.spec.labelSignalId,
        sourceVariableId=frame.spec.sourceVariableId,
        targetVariableId=frame.spec.targetVariableId,
        sourceUnit=frame.spec.sourceUnit,
        targetUnit=frame.spec.targetUnit,
        frequency=frame.spec.frequency,
        stepSpan=frame.spec.stepSpan,
        horizonSteps=frame.spec.horizonSteps,
        originStart=frame.spec.originStart,
        originThrough=frame.spec.originThrough,
        sourceEvidenceRoles=frame.spec.sourceEvidenceRoles,
        labelEvidenceRoles=frame.spec.labelEvidenceRoles,
        selectionRuleId=frame.spec.selectionRuleId,
        originKnowledgePolicy=frame.spec.originKnowledgePolicy,
        sourceRefPolicy=frame.spec.sourceRefPolicy,
        schemaVersion=frame.spec.schemaVersion,
    )
    _validateFrameBinding(binding, "typed")
    return binding


def _providerBatchFromParent(admissionVerifier: AdmissionVerifier, parent: AdmissionReceipt):
    try:
        raw = artifactPath(admissionVerifier.artifactRoot, parent.artifactHash).read_bytes()
    except OSError as error:
        raise DriverCalibrationError("coefficient provider batch artifact is unavailable") from error
    try:
        return _batchFromArtifact(parent, raw)
    except ValueError as error:
        raise DriverCalibrationError("coefficient provider batch artifact does not replay") from error


def _verifyObservationFrameReplay(
    admissionVerifier: AdmissionVerifier,
    sourceParents: tuple[AdmissionReceipt, ...],
    labelParents: tuple[AdmissionReceipt, ...],
    binding: DriverObservationFrameBinding | None,
    *,
    roleLabel: str,
) -> None:
    providerSourceParents = tuple(parent for parent in sourceParents if parent.kind == "providerObservationBatch")
    providerLabelParents = tuple(parent for parent in labelParents if parent.kind == "providerObservationBatch")
    if not providerSourceParents and not providerLabelParents:
        return
    if (
        len(sourceParents) != 1
        or len(labelParents) != 1
        or len(providerSourceParents) != 1
        or len(providerLabelParents) != 1
    ):
        raise DriverCalibrationError(f"coefficient {roleLabel} observation frame requires provider batch parents")
    if binding is None:
        raise DriverCalibrationError(f"coefficient {roleLabel} observation frame binding is missing")
    _validateFrameBinding(binding, roleLabel)
    sourceParent = providerSourceParents[0]
    labelParent = providerLabelParents[0]
    if sourceParent.receiptId != binding.sourceBatchReceiptId or labelParent.receiptId != binding.labelBatchReceiptId:
        raise DriverCalibrationError(f"coefficient {roleLabel} observation frame parent mismatch")
    rebuilt = buildDriverCoefficientObservationFrame(
        _providerBatchFromParent(admissionVerifier, sourceParent),
        _providerBatchFromParent(admissionVerifier, labelParent),
        _frameSpecFromBinding(binding),
    )
    if (
        rebuilt.frameHash != binding.frameHash
        or rebuilt.specHash != binding.specHash
        or rebuilt.rowCount != binding.rowCount
        or rebuilt.sourceBatchReceiptId != binding.sourceBatchReceiptId
        or rebuilt.labelBatchReceiptId != binding.labelBatchReceiptId
    ):
        raise DriverCalibrationError(f"coefficient {roleLabel} observation frame replay mismatch")


def _designSpecFromBinding(
    binding: MultivariableDriverDesignFrameBinding,
) -> MultivariableDriverCoefficientObservationFrameSpec:
    return MultivariableDriverCoefficientObservationFrameSpec(
        frameId=binding.frameId,
        sourceColumns=binding.sourceColumns,
        labelSignalId=binding.labelSignalId,
        targetVariableId=binding.targetVariableId,
        targetUnit=binding.targetUnit,
        frequency=binding.frequency,
        stepSpan=binding.stepSpan,
        horizonSteps=binding.horizonSteps,
        originStart=binding.originStart,
        originThrough=binding.originThrough,
        labelEvidenceRoles=binding.labelEvidenceRoles,
        selectionRuleId=binding.selectionRuleId,
        originKnowledgePolicy=binding.originKnowledgePolicy,
        sourceRefPolicy=binding.sourceRefPolicy,
        missingPolicy=binding.missingPolicy,
        schemaVersion=binding.schemaVersion,
    )


def _validateDesignFrameBinding(binding: MultivariableDriverDesignFrameBinding, label: str) -> None:
    if (
        not isinstance(binding, MultivariableDriverDesignFrameBinding)
        or binding.schemaVersion != DRIVER_DESIGN_FRAME_VERSION
        or not binding.frameId
        or binding.rowCount < 1
        or not binding.sourceBatchReceiptIds
        or not binding.sourceColumns
        or len(binding.sourceBatchReceiptIds) != len(binding.sourceColumns)
        or not binding.labelSignalId
        or not binding.targetVariableId
        or not binding.targetUnit
        or not binding.frequency
        or binding.stepSpan < 1
        or binding.horizonSteps < 1
        or binding.droppedOriginCount < 0
        or not binding.labelEvidenceRoles
    ):
        raise DriverCalibrationError(f"coefficient {label} design frame binding is incomplete")
    variableIds = tuple(column.variableId for column in binding.sourceColumns)
    if len(set(variableIds)) != len(variableIds):
        raise DriverCalibrationError(f"coefficient {label} design frame source variables must be unique")
    for field, value in (
        ("frameHash", binding.frameHash),
        ("specHash", binding.specHash),
        ("labelBatchReceiptId", binding.labelBatchReceiptId),
        ("droppedOriginHash", binding.droppedOriginHash),
        ("columnOrderHash", binding.columnOrderHash),
    ):
        if not _validDigest(value):
            raise DriverCalibrationError(f"coefficient {label} design frame {field} is invalid")
    _validateReceiptIds(binding.sourceBatchReceiptIds, f"{label} design source batch")
    if tuple(variable for variable, _count in binding.missingCountByVariable) != variableIds:
        raise DriverCalibrationError(f"coefficient {label} design frame missing count variable order mismatch")
    if any(count < 0 for _variable, count in binding.missingCountByVariable):
        raise DriverCalibrationError(f"coefficient {label} design frame missing count is invalid")
    if binding.specHash != canonicalPayloadHash(_designSpecFromBinding(binding)):
        raise DriverCalibrationError(f"coefficient {label} design frame spec hash mismatch")
    # 칼럼 순서 payload 는 프레임을 지은 쪽 (`driverObservationFrames`) 이 정본이다.
    # 여기서 같은 dict 를 다시 적으면 한쪽만 필드가 늘었을 때 해시가 조용히 갈라진다.
    if binding.columnOrderHash != canonicalPayloadHash(_columnOrderPayload(binding.sourceColumns)):
        raise DriverCalibrationError(f"coefficient {label} design frame column order hash mismatch")


def _designFrameBindingFromObservationFrame(
    frame: MultivariableDriverCoefficientObservationFrame,
) -> MultivariableDriverDesignFrameBinding:
    if not isinstance(frame, MultivariableDriverCoefficientObservationFrame) or frame.spec is None:
        raise DriverCalibrationError("coefficient design frame binding requires typed frame")
    if canonicalPayloadHash(frame.spec) != frame.specHash:
        raise DriverCalibrationError("coefficient design frame spec hash mismatch")
    if frame.rowCount != frame.frame.height:
        raise DriverCalibrationError("coefficient design frame row count mismatch")
    binding = MultivariableDriverDesignFrameBinding(
        frameId=frame.frameId,
        frameHash=frame.frameHash,
        specHash=frame.specHash,
        rowCount=frame.rowCount,
        sourceBatchReceiptIds=frame.sourceBatchReceiptIds,
        labelBatchReceiptId=frame.labelBatchReceiptId,
        sourceColumns=frame.spec.sourceColumns,
        labelSignalId=frame.spec.labelSignalId,
        targetVariableId=frame.spec.targetVariableId,
        targetUnit=frame.spec.targetUnit,
        frequency=frame.spec.frequency,
        stepSpan=frame.spec.stepSpan,
        horizonSteps=frame.spec.horizonSteps,
        originStart=frame.spec.originStart,
        originThrough=frame.spec.originThrough,
        labelEvidenceRoles=frame.spec.labelEvidenceRoles,
        selectionRuleId=frame.spec.selectionRuleId,
        originKnowledgePolicy=frame.spec.originKnowledgePolicy,
        sourceRefPolicy=frame.spec.sourceRefPolicy,
        missingPolicy=frame.spec.missingPolicy,
        droppedOriginCount=frame.droppedOriginCount,
        droppedOriginHash=frame.droppedOriginHash,
        missingCountByVariable=frame.missingCountByVariable,
        columnOrderHash=frame.columnOrderHash,
        schemaVersion=frame.spec.schemaVersion,
    )
    _validateDesignFrameBinding(binding, "typed")
    return binding


def _verifyMultivariableDesignFrameReplay(
    admissionVerifier: AdmissionVerifier,
    sourceParents: tuple[AdmissionReceipt, ...],
    labelParents: tuple[AdmissionReceipt, ...],
    binding: MultivariableDriverDesignFrameBinding,
    *,
    roleLabel: str,
) -> None:
    if (
        len(sourceParents) != len(binding.sourceBatchReceiptIds)
        or len(labelParents) != 1
        or any(parent.kind != "providerObservationBatch" for parent in sourceParents)
        or labelParents[0].kind != "providerObservationBatch"
    ):
        raise DriverCalibrationError(f"coefficient {roleLabel} design frame requires provider batch parents")
    _validateDesignFrameBinding(binding, roleLabel)
    if (
        tuple(parent.receiptId for parent in sourceParents) != binding.sourceBatchReceiptIds
        or labelParents[0].receiptId != binding.labelBatchReceiptId
    ):
        raise DriverCalibrationError(f"coefficient {roleLabel} design frame parent mismatch")
    rebuilt = buildMultivariableDriverCoefficientObservationFrame(
        tuple(_providerBatchFromParent(admissionVerifier, parent) for parent in sourceParents),
        _providerBatchFromParent(admissionVerifier, labelParents[0]),
        _designSpecFromBinding(binding),
    )
    if (
        rebuilt.frameHash != binding.frameHash
        or rebuilt.specHash != binding.specHash
        or rebuilt.rowCount != binding.rowCount
        or rebuilt.sourceBatchReceiptIds != binding.sourceBatchReceiptIds
        or rebuilt.labelBatchReceiptId != binding.labelBatchReceiptId
        or rebuilt.columnOrderHash != binding.columnOrderHash
        or rebuilt.droppedOriginHash != binding.droppedOriginHash
        or rebuilt.droppedOriginCount != binding.droppedOriginCount
        or rebuilt.missingCountByVariable != binding.missingCountByVariable
    ):
        raise DriverCalibrationError(f"coefficient {roleLabel} design frame replay mismatch")
