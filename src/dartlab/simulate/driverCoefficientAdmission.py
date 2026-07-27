"""스칼라 계수 승인 검증과 운영 노출 승격.

측정된 계수가 운영 exposure 가 되는 유일한 문이다. 서명 영수증·부모 계보·커버리지가
모두 맞을 때만 통과하므로, 이 판정을 적합이나 판정 모듈에 섞으면 아직 승인되지 않은
계수가 exposure 로 새어 나갈 여지가 생긴다.
"""

from __future__ import annotations

import math

from dartlab.simulate.admissionRegistry import AdmissionVerifier, artifactPath
from dartlab.simulate.driverCalibrationContracts import (
    DriverCalibrationError,
    DriverCoefficientCalibrationReceipt,
    DriverCoefficientOosReport,
    VerifiedDriverCoefficientAdmission,
)
from dartlab.simulate.driverCalibrationKernel import _dateText, _dedupe, _finite
from dartlab.simulate.driverCoefficientFrameBinding import _verifyObservationFrameReplay
from dartlab.simulate.driverCoefficientLineage import (
    _expectedCoverageRowsFromTraceRows,
    _verifyCoefficientParent,
    _verifyParentCoverage,
)
from dartlab.simulate.driverCoefficientOos import (
    _validateCoefficientReport,
    driverCoefficientAdmissionArtifact,
    driverCoefficientAdmissionParentReceiptIds,
    driverCoefficientAdmissionSubjectHash,
)
from dartlab.simulate.driverCoefficientReceipt import _oosReportPayload, _validateCalibrationReceipt
from dartlab.simulate.driverCoefficientRules import (
    _LABEL_PARENT_KINDS,
    _SOURCE_PARENT_KINDS,
    DRIVER_COEFFICIENT_RULE_HASH,
    DRIVER_COEFFICIENT_RULE_ID,
    DRIVER_COEFFICIENT_RULE_VERSION,
)
from dartlab.simulate.operatingBridge import OPERATING_TARGET_UNITS, OperatingTransmissionExposure
from dartlab.simulate.vintage import canonicalPayloadHash


def _verifyCoefficientParents(
    report: DriverCoefficientOosReport,
    calibrationReceipt: DriverCoefficientCalibrationReceipt,
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
    if report.fitFrameBinding != calibrationReceipt.fitFrameBinding:
        raise DriverCalibrationError("coefficient fit observation frame binding does not match receipt")
    _verifyObservationFrameReplay(
        admissionVerifier,
        fitSourceParents,
        fitLabelParents,
        calibrationReceipt.fitFrameBinding,
        roleLabel="fit",
    )
    _verifyObservationFrameReplay(
        admissionVerifier,
        oosSourceParents,
        oosLabelParents,
        report.oosFrameBinding,
        roleLabel="OOS",
    )
    _verifyParentCoverage(
        admissionVerifier,
        fitSourceParents,
        _expectedCoverageRowsFromTraceRows(
            calibrationReceipt.traceRows,
            role="source",
            sourceUnit=calibrationReceipt.sourceUnit,
            targetUnit=calibrationReceipt.targetUnit,
        ),
        role="source",
        roleLabel="fit source",
    )
    _verifyParentCoverage(
        admissionVerifier,
        fitLabelParents,
        _expectedCoverageRowsFromTraceRows(
            calibrationReceipt.traceRows,
            role="label",
            sourceUnit=calibrationReceipt.sourceUnit,
            targetUnit=calibrationReceipt.targetUnit,
        ),
        role="label",
        roleLabel="fit label",
    )
    _verifyParentCoverage(
        admissionVerifier,
        oosSourceParents,
        _expectedCoverageRowsFromTraceRows(
            report.traceRows,
            role="source",
            sourceUnit=calibrationReceipt.sourceUnit,
            targetUnit=calibrationReceipt.targetUnit,
        ),
        role="source",
        roleLabel="OOS source",
    )
    _verifyParentCoverage(
        admissionVerifier,
        oosLabelParents,
        _expectedCoverageRowsFromTraceRows(
            report.traceRows,
            role="label",
            sourceUnit=calibrationReceipt.sourceUnit,
            targetUnit=calibrationReceipt.targetUnit,
        ),
        role="label",
        roleLabel="OOS label",
    )
    return (
        _dedupe((*report.fitSourceParentReceiptIds, *report.oosSourceParentReceiptIds)),
        _dedupe((*report.fitLabelParentReceiptIds, *report.oosLabelParentReceiptIds)),
    )


def validateDriverCoefficientAdmission(
    report: DriverCoefficientOosReport,
    admissionVerifier: AdmissionVerifier,
    *,
    calibrationReceipt: DriverCoefficientCalibrationReceipt,
    receiptId: str,
    decisionAsOf: str,
) -> VerifiedDriverCoefficientAdmission:
    """Verify a signed coefficient OOS report against the admission registry.

    Args:
        report: Unsigned OOS report whose artifact is stored in the registry.
        admissionVerifier: Runtime verifier with trusted public keys and artifact root.
        calibrationReceipt: Original fit receipt whose fit trace must be covered by fit parents.
        receiptId: Admission receipt identifier to verify.
        decisionAsOf: Decision date that must be after receipt issuance.

    Returns:
        ``VerifiedDriverCoefficientAdmission`` for a fully parent-checked coefficient.

    Raises:
        DriverCalibrationError: If the report is ineligible, parent lineage is incomplete, or receipt drifts.

    Example:
        ``admission = validateDriverCoefficientAdmission(report, verifier, calibrationReceipt=receipt, receiptId=rid, decisionAsOf="20251231")``
    """

    _validateCalibrationReceipt(calibrationReceipt)
    _validateCoefficientReport(report)
    if report.status != "oosEligible":
        raise DriverCalibrationError("coefficient OOS report is not eligible for admission")
    if (
        report.receiptHash != calibrationReceipt.receiptHash
        or report.receiptId != calibrationReceipt.receiptId
        or report.calibrationId != calibrationReceipt.calibrationId
        or report.sourceVariableId != calibrationReceipt.sourceVariableId
        or report.targetVariableId != calibrationReceipt.targetVariableId
        or report.targetShock != calibrationReceipt.targetShock
        or report.coefficientUnit != calibrationReceipt.coefficientUnit
        or report.calibrationKnowledgeAsOf != calibrationReceipt.calibrationKnowledgeAsOf
        or not math.isclose(report.coefficient, calibrationReceipt.coefficient, rel_tol=1e-12, abs_tol=1e-12)
    ):
        raise DriverCalibrationError("coefficient OOS report does not match calibration receipt")
    subjectHash = driverCoefficientAdmissionSubjectHash(report)
    expectedParentReceiptIds = driverCoefficientAdmissionParentReceiptIds(report)
    try:
        receipt = admissionVerifier.verify(
            receiptId,
            expectedSubjectHash=subjectHash,
            expectedKind="driverCoefficient",
        )
    except RuntimeError as error:
        raise DriverCalibrationError(f"coefficient admission verification failed: {error}") from error
    if (
        receipt.status != "admitted"
        or receipt.artifactHash != subjectHash
        or (receipt.ruleId, receipt.ruleVersion, receipt.ruleHash)
        != (DRIVER_COEFFICIENT_RULE_ID, DRIVER_COEFFICIENT_RULE_VERSION, DRIVER_COEFFICIENT_RULE_HASH)
        or receipt.knowledgeAsOf != report.evaluationKnowledgeAsOf
        or receipt.frequency != report.frequency
        or receipt.stepSpan != report.stepSpan
        or receipt.maxAdmittedStep != report.maxAdmittedStep
        or receipt.revisionPolicy != "asKnown"
        or receipt.coverage != "asOfExact"
        or receipt.parentReceiptIds != expectedParentReceiptIds
        or _dateText(receipt.issuedAt, "coefficient receipt issuedAt") > _dateText(decisionAsOf, "decisionAsOf")
    ):
        raise DriverCalibrationError("coefficient admission receipt contract mismatch")
    sourceParentReceiptIds, labelParentReceiptIds = _verifyCoefficientParents(
        report,
        calibrationReceipt,
        admissionVerifier,
        decisionAsOf=decisionAsOf,
    )
    try:
        artifactBytes = artifactPath(admissionVerifier.artifactRoot, subjectHash).read_bytes()
    except OSError as error:
        raise DriverCalibrationError("coefficient admission artifact is unavailable") from error
    if artifactBytes != driverCoefficientAdmissionArtifact(report):
        raise DriverCalibrationError("coefficient admission artifact content mismatch")
    return VerifiedDriverCoefficientAdmission(
        receipt=receipt,
        sourceParentReceiptIds=sourceParentReceiptIds,
        labelParentReceiptIds=labelParentReceiptIds,
    )


def calibrationReceiptToOperatingExposure(
    receipt: DriverCoefficientCalibrationReceipt,
    *,
    exposureId: str,
    oosReport: DriverCoefficientOosReport | None = None,
    admissionReceipt: VerifiedDriverCoefficientAdmission | None = None,
    modifierVariableId: str = "",
    modifierUnit: str = "",
    aggregationGroup: str = "",
) -> OperatingTransmissionExposure:
    """Convert an admitted coefficient into a measured-association exposure.

    Args:
        receipt: Calibration receipt returned by ``fitDriverCoefficientPit``.
        exposureId: Stable exposure identifier for the operating bridge.
        oosReport: Eligible OOS report for the frozen receipt.
        admissionReceipt: Verified typed admission wrapper for the OOS report.
        modifierVariableId: Optional PIT state primitive that scales the coefficient.
        modifierUnit: Required unit when a modifier is present.
        aggregationGroup: Optional duplicate source-target aggregation group.

    Returns:
        ``OperatingTransmissionExposure`` with sourceRef bound to the admission receipt.

    Raises:
        DriverCalibrationError: If OOS admission is missing, rejected, or mismatched.

    Example:
        ``exposure = calibrationReceiptToOperatingExposure(receipt, exposureId="fx-price", oosReport=report, admissionReceipt=signed)``
    """

    if receipt.status == "rejected" or receipt.validationStatus == "rejected":
        raise DriverCalibrationError("rejected coefficient receipt cannot become an exposure")
    if oosReport is None or admissionReceipt is None:
        raise DriverCalibrationError("coefficient exposure requires OOS admission")
    if not isinstance(admissionReceipt, VerifiedDriverCoefficientAdmission):
        raise DriverCalibrationError("coefficient exposure requires verified coefficient admission")
    _validateCalibrationReceipt(receipt)
    expectedUnit = f"{OPERATING_TARGET_UNITS[receipt.targetShock]}/{receipt.sourceUnit}"
    if receipt.coefficientUnit != expectedUnit:
        raise DriverCalibrationError("coefficient receipt unit drift")
    _finite(receipt.coefficient, "receipt.coefficient")
    _validateCoefficientReport(oosReport)
    subjectHash = canonicalPayloadHash(_oosReportPayload(oosReport))
    if (
        oosReport.status != "oosEligible"
        or oosReport.receiptHash != receipt.receiptHash
        or oosReport.receiptId != receipt.receiptId
        or oosReport.calibrationId != receipt.calibrationId
        or oosReport.sourceVariableId != receipt.sourceVariableId
        or oosReport.targetVariableId != receipt.targetVariableId
        or oosReport.targetShock != receipt.targetShock
        or oosReport.coefficientUnit != receipt.coefficientUnit
        or oosReport.fitFrameBinding != receipt.fitFrameBinding
        or not math.isclose(oosReport.coefficient, receipt.coefficient, rel_tol=1e-12, abs_tol=1e-12)
    ):
        raise DriverCalibrationError("coefficient OOS report does not match receipt")
    signedReceipt = admissionReceipt.receipt
    if (
        signedReceipt.kind != "driverCoefficient"
        or signedReceipt.status != "admitted"
        or signedReceipt.subjectHash != subjectHash
        or signedReceipt.artifactHash != subjectHash
        or (signedReceipt.ruleId, signedReceipt.ruleVersion, signedReceipt.ruleHash)
        != (DRIVER_COEFFICIENT_RULE_ID, DRIVER_COEFFICIENT_RULE_VERSION, DRIVER_COEFFICIENT_RULE_HASH)
        or signedReceipt.knowledgeAsOf != oosReport.evaluationKnowledgeAsOf
        or signedReceipt.frequency != oosReport.frequency
        or signedReceipt.stepSpan != oosReport.stepSpan
        or signedReceipt.maxAdmittedStep != oosReport.maxAdmittedStep
        or signedReceipt.revisionPolicy != "asKnown"
        or signedReceipt.coverage != "asOfExact"
        or signedReceipt.parentReceiptIds != driverCoefficientAdmissionParentReceiptIds(oosReport)
    ):
        raise DriverCalibrationError("coefficient admission receipt does not match OOS report")
    return OperatingTransmissionExposure(
        exposureId=exposureId,
        sourceVariableId=receipt.sourceVariableId,
        targetShock=receipt.targetShock,
        coefficient=receipt.coefficient,
        coefficientUnit=receipt.coefficientUnit,
        evidenceKind="measuredAssociation",
        sourceRef=f"driverCoefficientAdmission:{signedReceipt.receiptId}",
        modifierVariableId=modifierVariableId,
        modifierUnit=modifierUnit,
        lagSteps=receipt.lagSteps,
        responseKernel=receipt.responseKernel,
        aggregationGroup=aggregationGroup,
        sourceFrequency=receipt.sourceFrequency,
        sourceTiming=receipt.sourceTiming,
        sourceTransformId=receipt.sourceTransformId,
        sourceFactorContractHash=receipt.sourceFactorContractHash,
    )
