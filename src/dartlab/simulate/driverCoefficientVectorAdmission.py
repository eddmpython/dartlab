"""벡터 계수 승인 검증과 운영 노출 묶음 승격.

스칼라 승인의 쌍이다. 승인 하나가 계수 항 수만큼의 exposure 로 갈라지므로,
항별 exposure id 와 aggregation group 을 여기서 정한다. 승인 이전 계수가
exposure 로 새지 않게 막는 문 역할은 스칼라 쪽과 같다.
"""

from __future__ import annotations

from dartlab.simulate.admissionRegistry import AdmissionVerifier, artifactPath
from dartlab.simulate.driverCalibrationContracts import (
    DriverCalibrationError,
    MultivariableDriverCoefficientCalibrationReceipt,
    MultivariableDriverCoefficientOosReport,
    VerifiedDriverCoefficientAdmission,
)
from dartlab.simulate.driverCalibrationKernel import _dateText, _dedupe
from dartlab.simulate.driverCoefficientFrameBinding import _verifyMultivariableDesignFrameReplay
from dartlab.simulate.driverCoefficientLineage import (
    _expectedMultivariableCoverageRowsFromTraceRows,
    _verifyCoefficientParent,
    _verifyParentCoverage,
)
from dartlab.simulate.driverCoefficientRules import (
    _LABEL_PARENT_KINDS,
    _SOURCE_PARENT_KINDS,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
)
from dartlab.simulate.driverCoefficientVectorOos import (
    _validateMultivariableCoefficientReport,
    multivariableDriverCoefficientAdmissionArtifact,
    multivariableDriverCoefficientAdmissionParentReceiptIds,
    multivariableDriverCoefficientAdmissionSubjectHash,
)
from dartlab.simulate.driverCoefficientVectorReceipt import (
    _multivariableOosReportPayload,
    _validateMultivariableCalibrationReceipt,
)
from dartlab.simulate.operatingBridge import OperatingTransmissionExposure
from dartlab.simulate.vintage import canonicalPayloadHash


def _verifyMultivariableCoefficientParents(
    report: MultivariableDriverCoefficientOosReport,
    calibrationReceipt: MultivariableDriverCoefficientCalibrationReceipt,
    admissionVerifier: AdmissionVerifier,
    *,
    decisionAsOf: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    fitSourceParents = tuple(
        _verifyCoefficientParent(
            admissionVerifier,
            receiptId,
            role="fit source",
            allowedKinds=_SOURCE_PARENT_KINDS,
            maxKnowledgeAsOf=report.calibrationKnowledgeAsOf,
            decisionAsOf=decisionAsOf,
        )
        for receiptId in report.fitSourceParentReceiptIds
    )
    fitLabelParents = tuple(
        _verifyCoefficientParent(
            admissionVerifier,
            receiptId,
            role="fit label",
            allowedKinds=_LABEL_PARENT_KINDS,
            maxKnowledgeAsOf=report.calibrationKnowledgeAsOf,
            decisionAsOf=decisionAsOf,
        )
        for receiptId in report.fitLabelParentReceiptIds
    )
    oosSourceParents = tuple(
        _verifyCoefficientParent(
            admissionVerifier,
            receiptId,
            role="OOS source",
            allowedKinds=_SOURCE_PARENT_KINDS,
            maxKnowledgeAsOf=report.evaluationKnowledgeAsOf,
            decisionAsOf=decisionAsOf,
        )
        for receiptId in report.oosSourceParentReceiptIds
    )
    oosLabelParents = tuple(
        _verifyCoefficientParent(
            admissionVerifier,
            receiptId,
            role="OOS label",
            allowedKinds=_LABEL_PARENT_KINDS,
            maxKnowledgeAsOf=report.evaluationKnowledgeAsOf,
            decisionAsOf=decisionAsOf,
        )
        for receiptId in report.oosLabelParentReceiptIds
    )
    if report.fitDesignFrameBinding != calibrationReceipt.fitDesignFrameBinding:
        raise DriverCalibrationError("coefficient vector fit design frame binding does not match receipt")
    _verifyMultivariableDesignFrameReplay(
        admissionVerifier,
        fitSourceParents,
        fitLabelParents,
        calibrationReceipt.fitDesignFrameBinding,
        roleLabel="fit",
    )
    _verifyMultivariableDesignFrameReplay(
        admissionVerifier,
        oosSourceParents,
        oosLabelParents,
        report.oosDesignFrameBinding,
        roleLabel="OOS",
    )
    _verifyParentCoverage(
        admissionVerifier,
        fitSourceParents,
        _expectedMultivariableCoverageRowsFromTraceRows(
            calibrationReceipt.traceRows,
            role="source",
            targetUnit=calibrationReceipt.targetUnit,
        ),
        role="source",
        roleLabel="fit source",
    )
    _verifyParentCoverage(
        admissionVerifier,
        fitLabelParents,
        _expectedMultivariableCoverageRowsFromTraceRows(
            calibrationReceipt.traceRows,
            role="label",
            targetUnit=calibrationReceipt.targetUnit,
        ),
        role="label",
        roleLabel="fit label",
    )
    _verifyParentCoverage(
        admissionVerifier,
        oosSourceParents,
        _expectedMultivariableCoverageRowsFromTraceRows(
            report.traceRows,
            role="source",
            targetUnit=calibrationReceipt.targetUnit,
        ),
        role="source",
        roleLabel="OOS source",
    )
    _verifyParentCoverage(
        admissionVerifier,
        oosLabelParents,
        _expectedMultivariableCoverageRowsFromTraceRows(
            report.traceRows,
            role="label",
            targetUnit=calibrationReceipt.targetUnit,
        ),
        role="label",
        roleLabel="OOS label",
    )
    return (
        _dedupe((*report.fitSourceParentReceiptIds, *report.oosSourceParentReceiptIds)),
        _dedupe((*report.fitLabelParentReceiptIds, *report.oosLabelParentReceiptIds)),
    )


def validateMultivariableDriverCoefficientAdmission(
    report: MultivariableDriverCoefficientOosReport,
    admissionVerifier: AdmissionVerifier,
    *,
    calibrationReceipt: MultivariableDriverCoefficientCalibrationReceipt,
    receiptId: str,
    decisionAsOf: str,
) -> VerifiedDriverCoefficientAdmission:
    """Verify a signed coefficient vector OOS report against the admission registry.

    Args:
        report: Unsigned vector OOS report whose artifact is stored in the registry.
        admissionVerifier: Runtime verifier with trusted public keys and artifact root.
        calibrationReceipt: Original fit receipt whose fit trace must be parent covered.
        receiptId: Admission receipt identifier to verify.
        decisionAsOf: Decision date that must be after receipt issuance.

    Returns:
        ``VerifiedDriverCoefficientAdmission`` for a fully parent-checked coefficient vector.

    Raises:
        DriverCalibrationError: If the report is ineligible, parent lineage is incomplete, or receipt drifts.

    Example:
        ``admission = validateMultivariableDriverCoefficientAdmission(report, verifier, calibrationReceipt=receipt, receiptId=rid, decisionAsOf="20251231")``
    """

    _validateMultivariableCalibrationReceipt(calibrationReceipt)
    _validateMultivariableCoefficientReport(report)
    if report.status != "oosEligible":
        raise DriverCalibrationError("coefficient vector OOS report is not eligible for admission")
    if (
        report.receiptHash != calibrationReceipt.receiptHash
        or report.receiptId != calibrationReceipt.receiptId
        or report.calibrationId != calibrationReceipt.calibrationId
        or report.sourceVariableIds != calibrationReceipt.sourceVariableIds
        or report.targetVariableId != calibrationReceipt.targetVariableId
        or report.targetShock != calibrationReceipt.targetShock
        or report.targetUnit != calibrationReceipt.targetUnit
        or report.coefficientTerms != calibrationReceipt.coefficientTerms
        or report.featureSpecHash != calibrationReceipt.featureSpecHash
        or report.designFrameHash != calibrationReceipt.designFrameHash
        or report.coefficientVectorHash != calibrationReceipt.coefficientVectorHash
        or report.calibrationKnowledgeAsOf != calibrationReceipt.calibrationKnowledgeAsOf
    ):
        raise DriverCalibrationError("coefficient vector OOS report does not match calibration receipt")
    subjectHash = multivariableDriverCoefficientAdmissionSubjectHash(report)
    expectedParentReceiptIds = multivariableDriverCoefficientAdmissionParentReceiptIds(report)
    try:
        receipt = admissionVerifier.verify(
            receiptId,
            expectedSubjectHash=subjectHash,
            expectedKind="driverCoefficient",
        )
    except RuntimeError as error:
        raise DriverCalibrationError(f"coefficient vector admission verification failed: {error}") from error
    if (
        receipt.status != "admitted"
        or receipt.artifactHash != subjectHash
        or (receipt.ruleId, receipt.ruleVersion, receipt.ruleHash)
        != (
            MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
            MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
            MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
        )
        or receipt.knowledgeAsOf != report.evaluationKnowledgeAsOf
        or receipt.frequency != report.frequency
        or receipt.stepSpan != report.stepSpan
        or receipt.maxAdmittedStep != report.maxAdmittedStep
        or receipt.revisionPolicy != "asKnown"
        or receipt.coverage != "asOfExact"
        or receipt.parentReceiptIds != expectedParentReceiptIds
        or _dateText(receipt.issuedAt, "coefficient vector receipt issuedAt") > _dateText(decisionAsOf, "decisionAsOf")
    ):
        raise DriverCalibrationError("coefficient vector admission receipt contract mismatch")
    sourceParentReceiptIds, labelParentReceiptIds = _verifyMultivariableCoefficientParents(
        report,
        calibrationReceipt,
        admissionVerifier,
        decisionAsOf=decisionAsOf,
    )
    try:
        artifactBytes = artifactPath(admissionVerifier.artifactRoot, subjectHash).read_bytes()
    except OSError as error:
        raise DriverCalibrationError("coefficient vector admission artifact is unavailable") from error
    if artifactBytes != multivariableDriverCoefficientAdmissionArtifact(report):
        raise DriverCalibrationError("coefficient vector admission artifact content mismatch")
    return VerifiedDriverCoefficientAdmission(
        receipt=receipt,
        sourceParentReceiptIds=sourceParentReceiptIds,
        labelParentReceiptIds=labelParentReceiptIds,
    )


def _verifyVectorExposureAdmission(
    receipt: MultivariableDriverCoefficientCalibrationReceipt,
    oosReport: MultivariableDriverCoefficientOosReport,
    admissionReceipt: VerifiedDriverCoefficientAdmission,
):
    """exposure 승격 직전 영수증·보고서·서명 승인 삼자가 같은 대상인지 확인한다."""
    _validateMultivariableCalibrationReceipt(receipt)
    _validateMultivariableCoefficientReport(oosReport)
    subjectHash = canonicalPayloadHash(_multivariableOosReportPayload(oosReport))
    if (
        oosReport.status != "oosEligible"
        or oosReport.receiptHash != receipt.receiptHash
        or oosReport.receiptId != receipt.receiptId
        or oosReport.calibrationId != receipt.calibrationId
        or oosReport.sourceVariableIds != receipt.sourceVariableIds
        or oosReport.targetVariableId != receipt.targetVariableId
        or oosReport.targetShock != receipt.targetShock
        or oosReport.targetUnit != receipt.targetUnit
        or oosReport.coefficientTerms != receipt.coefficientTerms
        or oosReport.fitDesignFrameBinding != receipt.fitDesignFrameBinding
    ):
        raise DriverCalibrationError("coefficient vector OOS report does not match receipt")
    signedReceipt = admissionReceipt.receipt
    if (
        signedReceipt.kind != "driverCoefficient"
        or signedReceipt.status != "admitted"
        or signedReceipt.subjectHash != subjectHash
        or signedReceipt.artifactHash != subjectHash
        or (signedReceipt.ruleId, signedReceipt.ruleVersion, signedReceipt.ruleHash)
        != (
            MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
            MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
            MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
        )
        or signedReceipt.knowledgeAsOf != oosReport.evaluationKnowledgeAsOf
        or signedReceipt.frequency != oosReport.frequency
        or signedReceipt.stepSpan != oosReport.stepSpan
        or signedReceipt.maxAdmittedStep != oosReport.maxAdmittedStep
        or signedReceipt.revisionPolicy != "asKnown"
        or signedReceipt.coverage != "asOfExact"
        or signedReceipt.parentReceiptIds != multivariableDriverCoefficientAdmissionParentReceiptIds(oosReport)
    ):
        raise DriverCalibrationError("coefficient vector admission receipt does not match OOS report")
    return signedReceipt


def multivariableCalibrationReceiptToOperatingExposures(
    receipt: MultivariableDriverCoefficientCalibrationReceipt,
    *,
    exposureIdPrefix: str,
    oosReport: MultivariableDriverCoefficientOosReport | None = None,
    admissionReceipt: VerifiedDriverCoefficientAdmission | None = None,
    modifierVariableId: str = "",
    modifierUnit: str = "",
    aggregationGroup: str = "",
) -> tuple[OperatingTransmissionExposure, ...]:
    """Convert an admitted coefficient vector into scalar measured-association exposures.

    Args:
        receipt: Vector calibration receipt returned by ``fitMultivariableDriverCoefficientPit``.
        exposureIdPrefix: Stable prefix used to create one exposure id per source variable.
        oosReport: Eligible OOS report for the frozen vector receipt.
        admissionReceipt: Verified typed admission wrapper for the OOS report.
        modifierVariableId: Optional PIT state primitive that scales every coefficient.
        modifierUnit: Required unit when a modifier is present.
        aggregationGroup: Optional group label shared by the vector-derived scalar exposures.

    Returns:
        Tuple of ``OperatingTransmissionExposure`` objects, one per coefficient term.

    Raises:
        DriverCalibrationError: If OOS admission is missing, rejected, or mismatched.

    Example:
        ``exposures = multivariableCalibrationReceiptToOperatingExposures(receipt, exposureIdPrefix="macro-price", oosReport=report, admissionReceipt=signed)``
    """

    if not exposureIdPrefix:
        raise DriverCalibrationError("coefficient vector exposure prefix is required")
    if receipt.status == "rejected" or receipt.validationStatus == "rejected":
        raise DriverCalibrationError("rejected coefficient vector receipt cannot become exposures")
    if oosReport is None or admissionReceipt is None:
        raise DriverCalibrationError("coefficient vector exposure requires OOS admission")
    if not isinstance(admissionReceipt, VerifiedDriverCoefficientAdmission):
        raise DriverCalibrationError("coefficient vector exposure requires verified coefficient admission")
    signedReceipt = _verifyVectorExposureAdmission(receipt, oosReport, admissionReceipt)
    group = aggregationGroup or f"{exposureIdPrefix}:vector:{signedReceipt.receiptId[:12]}"
    return tuple(
        OperatingTransmissionExposure(
            exposureId=f"{exposureIdPrefix}:{term.variableId}",
            sourceVariableId=term.variableId,
            targetShock=receipt.targetShock,
            coefficient=term.coefficient,
            coefficientUnit=term.coefficientUnit,
            evidenceKind="measuredAssociation",
            sourceRef=f"driverCoefficientAdmission:{signedReceipt.receiptId}",
            modifierVariableId=modifierVariableId,
            modifierUnit=modifierUnit,
            lagSteps=receipt.lagSteps,
            responseKernel=receipt.responseKernel,
            aggregationGroup=group,
            sourceFrequency=term.sourceFrequency,
            sourceTiming=term.sourceTiming,
            sourceTransformId=term.sourceTransformId,
            sourceFactorContractHash=term.sourceFactorContractHash,
        )
        for term in receipt.coefficientTerms
    )
