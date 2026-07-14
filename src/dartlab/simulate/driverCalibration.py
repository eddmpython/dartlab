"""Fit PIT driver coefficients without granting path or policy admission.

This module is the measured-law boundary between a registered source factor
and an operating shock target. It accepts an already compiled driver registry
result plus an origin-level calibration frame, fits only observable forward
labels, and returns a receipt that can be referenced by an operating exposure.
It does not admit paths, transfer calibrated weights, or recommend policies.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date

import polars as pl

from dartlab.simulate.admissionRegistry import (
    AdmissionReceipt,
    AdmissionVerifier,
    artifactPath,
)
from dartlab.simulate.driverObservationFrames import (
    DRIVER_OBSERVATION_FRAME_VERSION,
    DriverCoefficientObservationFrame,
    DriverCoefficientObservationFrameSpec,
    buildDriverCoefficientObservationFrame,
)
from dartlab.simulate.driverRegistry import DriverRegistryResult
from dartlab.simulate.operatingBridge import (
    OPERATING_TARGET_UNITS,
    OperatingBridgeError,
    OperatingTransmissionExposure,
    sourceFactorContractHash,
)
from dartlab.simulate.stateCompiler import _batchFromArtifact
from dartlab.simulate.vintage import canonicalPayloadBytes, canonicalPayloadHash

CALIBRATION_VERSION = "driver-coefficient-calibration-v1"
COEFFICIENT_OOS_VERSION = "driver-coefficient-oos-v1"
PARENT_COVERAGE_VERSION = "driver-coefficient-parent-coverage-v1"
DRIVER_COEFFICIENT_RULE_ID = "driver-coefficient-oos-admission"
DRIVER_COEFFICIENT_RULE_VERSION = "1"
_OBSERVABLE_TARGET_KINDS = {"observedOutcome", "realizedOutcome", "observedOperatingShock"}
_CALIBRATION_METHODS = {"olsThroughOrigin"}
_OOS_STATUS_SET = {"oosEligible", "rejected"}
_BASE_RECEIPT_WARNINGS = {
    "coefficientCalibrationNotAdmitted",
    "coefficientRequiresOosAdmission",
    "registryValidation:retrospectiveOnly",
    "registryWarning:historyStatus:asKnown",
}
_BENIGN_REGISTRY_WARNINGS = {"historyStatus:asKnown"}
_SOURCE_PARENT_KINDS = {"dataVintage", "providerObservationBatch", "vintage"}
_LABEL_PARENT_KINDS = {"dataVintage", "providerObservationBatch", "vintage"}
DRIVER_COEFFICIENT_RULE_SPEC = {
    "ruleId": DRIVER_COEFFICIENT_RULE_ID,
    "ruleVersion": DRIVER_COEFFICIENT_RULE_VERSION,
    "rulePurpose": "admit a driver coefficient only after held-out PIT replay and signed lineage checks",
    "reportContract": {
        "generatorVersion": COEFFICIENT_OOS_VERSION,
        "requiredStatus": "oosEligible",
        "requiredAdmissionStatus": "unsigned",
        "requiredParentRoles": (
            "fitSourceParentReceiptIds",
            "fitLabelParentReceiptIds",
            "oosSourceParentReceiptIds",
            "oosLabelParentReceiptIds",
        ),
        "requiredContentHashes": (
            "receiptHash",
            "pathSetHash",
            "factorContractHash",
            "oosSpecHash",
            "oosGridHash",
            "oosOutcomeHash",
            "predictionTraceHash",
            "reportId",
        ),
    },
    "heldOutContract": {
        "fitOverlap": "originEventTime greater than receipt.fitThrough",
        "labelLeakage": "targetAvailableAt greater than receipt.calibrationKnowledgeAsOf",
        "targetDirection": "targetEventTime greater than originEventTime",
        "sourcePit": "sourceAvailableAt no later than originKnowledgeAsOf",
        "evaluationCutoff": "targetAvailableAt no later than evaluationKnowledgeAsOf",
        "horizonPolicy": "period distance must align with stepSpan and not exceed maxAdmittedStep",
    },
    "thresholdContract": {
        "minOosOrigins": "report.nOosOrigins at least spec.minOosOrigins",
        "skillVsBaseline": "report.skillVsBaseline at least spec.minSkillVsBaseline",
        "rmse": "report.rmse no greater than spec.maxRmse",
        "absBias": "absolute report.bias no greater than spec.maxAbsBias",
        "baselineLoss": "baselineMse must be positive",
    },
    "parentContract": {
        "sourceParentKinds": tuple(sorted(_SOURCE_PARENT_KINDS)),
        "labelParentKinds": tuple(sorted(_LABEL_PARENT_KINDS)),
        "requiredParentStatus": "verifiedVintage",
        "revisionPolicy": "asKnown",
        "coverage": "asOfExact",
        "fitParentKnowledgeCutoff": "no later than calibrationKnowledgeAsOf",
        "oosParentKnowledgeCutoff": "no later than evaluationKnowledgeAsOf",
        "availabilityCutoff": "parent issuedAt no later than decisionAsOf",
        "receiptParentSet": "exact ordered driverCoefficientAdmissionParentReceiptIds(report)",
        "parentArtifactCoverageSchema": PARENT_COVERAGE_VERSION,
        "parentArtifactCanonical": "canonical JSON bytes only",
        "rowCoverageRequired": (
            "fit source",
            "fit label",
            "OOS source",
            "OOS label",
        ),
        "coverageMatchFields": ("ref", "role", "eventTime", "availableAt", "value", "unit"),
        "providerBatchFrameReplay": "providerObservationBatch parents require signed observation frame binding replay",
        "providerBatchRowRefPolicy": "provider observation row refs must be observationId only",
        "opaqueParentArtifactPolicy": "reject",
    },
    "admissionReceiptContract": {
        "kind": "driverCoefficient",
        "status": "admitted",
        "revisionPolicy": "asKnown",
        "coverage": "asOfExact",
        "artifactHash": "driverCoefficientAdmissionSubjectHash(report)",
        "subjectHash": "driverCoefficientAdmissionSubjectHash(report)",
        "knowledgeAsOf": "report.evaluationKnowledgeAsOf",
        "frequency": "report.frequency",
        "stepSpan": "report.stepSpan",
        "maxAdmittedStep": "report.maxAdmittedStep",
    },
    "replayContract": {
        "artifactBytes": "canonicalPayloadBytes(_oosReportPayload(report))",
        "gridHash": "_oosGridHashFromTraceRows(report.traceRows)",
        "outcomeHash": "_oosOutcomeHashFromTraceRows(report.traceRows)",
        "predictionTraceHash": "_predictionTraceHash(report trace rows and metrics)",
        "metrics": ("mse", "baselineMse", "rmse", "mae", "bias", "skillVsBaseline"),
        "exposureBoundary": "only VerifiedDriverCoefficientAdmission can become measuredAssociation exposure",
    },
}
DRIVER_COEFFICIENT_RULE_HASH = canonicalPayloadHash(DRIVER_COEFFICIENT_RULE_SPEC)


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
    labelParentReceiptIds: tuple[str, ...] = ()
    semanticRefs: tuple[str, ...] = ()
    targetProxyRef: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "labelSourceRefs", tuple(self.labelSourceRefs))
        object.__setattr__(self, "labelParentReceiptIds", tuple(self.labelParentReceiptIds))
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
    sourceParentReceiptIds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "responseKernel", tuple(self.responseKernel))
        object.__setattr__(self, "sourceParentReceiptIds", tuple(self.sourceParentReceiptIds))


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
class DriverObservationFrameBinding:
    """Signed provider observation frame metadata bound into a coefficient receipt."""

    frameId: str
    frameHash: str
    specHash: str
    rowCount: int
    sourceBatchReceiptId: str
    labelBatchReceiptId: str
    sourceSignalId: str
    labelSignalId: str
    sourceVariableId: str
    targetVariableId: str
    sourceUnit: str
    targetUnit: str
    frequency: str
    stepSpan: int
    horizonSteps: int
    originStart: str
    originThrough: str
    sourceEvidenceRoles: tuple[str, ...]
    labelEvidenceRoles: tuple[str, ...]
    selectionRuleId: str
    originKnowledgePolicy: str
    sourceRefPolicy: str
    schemaVersion: str = DRIVER_OBSERVATION_FRAME_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceEvidenceRoles", tuple(self.sourceEvidenceRoles))
        object.__setattr__(self, "labelEvidenceRoles", tuple(self.labelEvidenceRoles))


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
    sourceParentReceiptIds: tuple[str, ...]
    labelParentReceiptIds: tuple[str, ...]
    traceRows: tuple[DriverCoefficientTraceRow, ...]
    sourceFrequency: str = ""
    sourceTiming: str = ""
    sourceTransformId: str = ""
    sourceFactorContractHash: str = ""
    fitFrameBinding: DriverObservationFrameBinding | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "responseKernel", tuple(self.responseKernel))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))
        object.__setattr__(self, "sourceParentReceiptIds", tuple(self.sourceParentReceiptIds))
        object.__setattr__(self, "labelParentReceiptIds", tuple(self.labelParentReceiptIds))
        object.__setattr__(self, "traceRows", tuple(self.traceRows))


@dataclass(frozen=True)
class DriverCoefficientOosSpec:
    """Held-out admission thresholds for one coefficient receipt."""

    evaluationId: str
    minOosOrigins: int
    minSkillVsBaseline: float
    maxRmse: float
    maxAbsBias: float
    baselineValue: float
    frequency: str
    stepSpan: int
    maxAdmittedStep: int
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
    sourceParentReceiptIds: tuple[str, ...] = ()
    labelParentReceiptIds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceParentReceiptIds", tuple(self.sourceParentReceiptIds))
        object.__setattr__(self, "labelParentReceiptIds", tuple(self.labelParentReceiptIds))


@dataclass(frozen=True)
class DriverCoefficientOosTraceRow:
    """One held-out row scored by a fixed coefficient receipt."""

    originId: str
    originEventTime: str
    originKnowledgeAsOf: str
    sourceAvailableAt: str
    targetEventTime: str
    targetAvailableAt: str
    sourceValue: float
    targetValue: float
    predictedValue: float
    baselineValue: float
    residual: float
    baselineResidual: float
    sourceRef: str
    labelSourceRef: str


@dataclass(frozen=True)
class DriverCoefficientOosReport:
    """Unsigned OOS report that can become a signed admission artifact."""

    evaluationId: str
    reportId: str
    generatorVersion: str
    status: str
    admissionStatus: str
    receiptHash: str
    receiptId: str
    calibrationId: str
    sourceVariableId: str
    targetVariableId: str
    targetShock: str
    coefficient: float
    coefficientUnit: str
    pathSetHash: str
    factorContractHash: str
    frequency: str
    stepSpan: int
    maxAdmittedStep: int
    calibrationKnowledgeAsOf: str
    evaluationKnowledgeAsOf: str
    nOosOrigins: int
    oosStart: str
    oosThrough: str
    labelThrough: str
    baselineValue: float
    mse: float
    baselineMse: float
    rmse: float
    mae: float
    bias: float
    skillVsBaseline: float
    minSkillVsBaseline: float
    maxRmse: float
    maxAbsBias: float
    oosSpecHash: str
    oosGridHash: str
    oosOutcomeHash: str
    predictionTraceHash: str
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    sourceRefs: tuple[str, ...]
    fitSourceParentReceiptIds: tuple[str, ...]
    fitLabelParentReceiptIds: tuple[str, ...]
    oosSourceParentReceiptIds: tuple[str, ...]
    oosLabelParentReceiptIds: tuple[str, ...]
    traceRows: tuple[DriverCoefficientOosTraceRow, ...]
    fitFrameBinding: DriverObservationFrameBinding | None = None
    oosFrameBinding: DriverObservationFrameBinding | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "reasons", tuple(self.reasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))
        object.__setattr__(self, "fitSourceParentReceiptIds", tuple(self.fitSourceParentReceiptIds))
        object.__setattr__(self, "fitLabelParentReceiptIds", tuple(self.fitLabelParentReceiptIds))
        object.__setattr__(self, "oosSourceParentReceiptIds", tuple(self.oosSourceParentReceiptIds))
        object.__setattr__(self, "oosLabelParentReceiptIds", tuple(self.oosLabelParentReceiptIds))
        object.__setattr__(self, "traceRows", tuple(self.traceRows))


@dataclass(frozen=True)
class VerifiedDriverCoefficientAdmission:
    """Driver coefficient admission after report, signature, artifact, and parent role checks."""

    receipt: AdmissionReceipt
    sourceParentReceiptIds: tuple[str, ...]
    labelParentReceiptIds: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceParentReceiptIds", tuple(self.sourceParentReceiptIds))
        object.__setattr__(self, "labelParentReceiptIds", tuple(self.labelParentReceiptIds))


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise DriverCalibrationError(f"invalid {label}: {value}")
    return text


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _validateReceiptIds(receiptIds: tuple[str, ...], label: str) -> None:
    if len(set(receiptIds)) != len(receiptIds) or any(not _validDigest(receiptId) for receiptId in receiptIds):
        raise DriverCalibrationError(f"{label} receipt identifiers are invalid")


def _dateParts(value: str, label: str) -> tuple[int, int, int]:
    text = _dateText(value, label)
    year = int(text[:4])
    month = int(text[4:6])
    day = int(text[6:8])
    try:
        date(year, month, day)
    except ValueError as error:
        raise DriverCalibrationError(f"invalid {label}: {value}") from error
    return year, month, day


def _periodIndex(value: str, frequency: str, label: str) -> int:
    year, month, day = _dateParts(value, label)
    normalized = frequency.lower()
    if normalized in {"day", "daily"}:
        return date(year, month, day).toordinal()
    if normalized in {"month", "monthly"}:
        return year * 12 + month - 1
    if normalized in {"quarter", "quarterly"}:
        return year * 4 + (month - 1) // 3
    if normalized in {"year", "yearly", "annual"}:
        return year
    raise DriverCalibrationError(f"unsupported coefficient OOS frequency: {frequency}")


def _validateOosHorizon(originEventTime: str, targetEventTime: str, spec: DriverCoefficientOosSpec) -> None:
    originIndex = _periodIndex(originEventTime, spec.frequency, "originEventTime")
    targetIndex = _periodIndex(targetEventTime, spec.frequency, "targetEventTime")
    distance = targetIndex - originIndex
    if distance <= 0:
        raise DriverCalibrationError("coefficient OOS target event must be after origin event")
    if distance % spec.stepSpan:
        raise DriverCalibrationError("coefficient OOS horizon does not align with stepSpan")
    admittedStep = distance // spec.stepSpan
    if admittedStep > spec.maxAdmittedStep:
        raise DriverCalibrationError("coefficient OOS horizon exceeds maxAdmittedStep")


def _finite(value: float | None, label: str) -> float:
    if value is None:
        raise DriverCalibrationError(f"{label} is missing")
    number = float(value)
    if not math.isfinite(number):
        raise DriverCalibrationError(f"{label} must be finite")
    return number


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _driverSourceFactorContractHash(
    *,
    variableId: str,
    unit: str,
    frequency: str,
    timing: str,
    transformId: str,
) -> str:
    try:
        return sourceFactorContractHash(
            variableId=variableId,
            unit=unit,
            frequency=frequency,
            timing=timing,
            transformId=transformId,
        )
    except OperatingBridgeError as error:
        raise DriverCalibrationError("coefficient source factor contract is incomplete") from error


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
    _validateReceiptIds(target.labelParentReceiptIds, "label parent")


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


def _assertClose(left: float, right: float, label: str) -> None:
    if not math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12):
        raise DriverCalibrationError(f"coefficient OOS report {label} mismatch")


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


def _validateCalibrationReceipt(receipt: DriverCoefficientCalibrationReceipt) -> None:
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
    if receipt.originGridHash != _calibrationOriginGridHashFromTraceRows(receipt.traceRows):
        raise DriverCalibrationError("coefficient calibration receipt grid hash mismatch")
    if receipt.coefficientTraceHash != _calibrationCoefficientTraceHash(receipt):
        raise DriverCalibrationError("coefficient calibration receipt trace hash mismatch")


def _coverageRow(
    *,
    ref: str,
    role: str,
    eventTime: str,
    availableAt: str,
    value: float,
    unit: str,
) -> dict:
    if not ref or role not in {"source", "label"} or not unit:
        raise DriverCalibrationError("coefficient parent coverage row is incomplete")
    return {
        "ref": ref,
        "role": role,
        "eventTime": _dateText(eventTime, "parent coverage eventTime"),
        "availableAt": _dateText(availableAt, "parent coverage availableAt"),
        "value": _finite(value, "parent coverage value"),
        "unit": unit,
    }


def _coverageRowsFromManifest(payload: dict, *, role: str) -> tuple[dict, ...]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise DriverCalibrationError("coefficient parent coverage manifest is malformed")
    out = []
    for item in rows:
        if not isinstance(item, dict):
            raise DriverCalibrationError("coefficient parent coverage row is malformed")
        rowRole = str(item.get("role", ""))
        if rowRole not in {"source", "label"}:
            raise DriverCalibrationError("coefficient parent coverage row role is invalid")
        if rowRole != role:
            continue
        out.append(
            _coverageRow(
                ref=str(item.get("ref", "")),
                role=rowRole,
                eventTime=str(item.get("eventTime", "")),
                availableAt=str(item.get("availableAt", "")),
                value=item.get("value"),
                unit=str(item.get("unit", "")),
            )
        )
    return tuple(out)


def _coverageRowsFromProviderBatch(payload: dict, *, role: str) -> tuple[dict, ...]:
    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise DriverCalibrationError("coefficient provider batch coverage artifact is malformed")
    out = []
    for item in observations:
        if not isinstance(item, dict):
            raise DriverCalibrationError("coefficient provider batch observation is malformed")
        out.append(
            _coverageRow(
                ref=str(item.get("observationId", "")),
                role=role,
                eventTime=str(item.get("eventAt", "")),
                availableAt=str(item.get("availableAt", "")),
                value=item.get("value"),
                unit=str(item.get("unit", "")),
            )
        )
    return tuple(out)


def _coverageRowsFromParent(
    admissionVerifier: AdmissionVerifier,
    parent: AdmissionReceipt,
    *,
    role: str,
) -> tuple[dict, ...]:
    try:
        raw = artifactPath(admissionVerifier.artifactRoot, parent.artifactHash).read_bytes()
    except OSError as error:
        raise DriverCalibrationError("coefficient parent coverage artifact is unavailable") from error
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise DriverCalibrationError("coefficient parent coverage artifact is not canonical JSON") from error
    if canonicalPayloadBytes(payload) != raw:
        raise DriverCalibrationError("coefficient parent coverage artifact is not canonical")
    if not isinstance(payload, dict):
        raise DriverCalibrationError("coefficient parent coverage artifact is malformed")
    schemaVersion = payload.get("schemaVersion")
    if schemaVersion == PARENT_COVERAGE_VERSION:
        return _coverageRowsFromManifest(payload, role=role)
    if schemaVersion == "provider-observation-batch-v1":
        return _coverageRowsFromProviderBatch(payload, role=role)
    raise DriverCalibrationError("coefficient parent coverage artifact is unsupported")


def _coverageIndex(
    admissionVerifier: AdmissionVerifier,
    parents: tuple[AdmissionReceipt, ...],
    *,
    role: str,
) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for parent in parents:
        for row in _coverageRowsFromParent(admissionVerifier, parent, role=role):
            ref = row["ref"]
            if ref in index:
                raise DriverCalibrationError("coefficient parent coverage has duplicate row ref")
            index[ref] = row
    return index


def _expectedCoverageRowsFromTraceRows(
    traceRows,
    *,
    role: str,
    sourceUnit: str,
    targetUnit: str,
) -> tuple[dict, ...]:
    rows = []
    for row in traceRows:
        if role == "source":
            rows.append(
                _coverageRow(
                    ref=row.sourceRef,
                    role="source",
                    eventTime=row.originEventTime,
                    availableAt=row.sourceAvailableAt,
                    value=row.sourceValue,
                    unit=sourceUnit,
                )
            )
        elif role == "label":
            rows.append(
                _coverageRow(
                    ref=row.labelSourceRef,
                    role="label",
                    eventTime=row.targetEventTime,
                    availableAt=row.targetAvailableAt,
                    value=row.targetValue,
                    unit=targetUnit,
                )
            )
        else:
            raise DriverCalibrationError("coefficient coverage role is invalid")
    return tuple(rows)


def _verifyParentCoverage(
    admissionVerifier: AdmissionVerifier,
    parents: tuple[AdmissionReceipt, ...],
    expectedRows: tuple[dict, ...],
    *,
    role: str,
    roleLabel: str,
) -> None:
    index = _coverageIndex(admissionVerifier, parents, role=role)
    missing = tuple(row["ref"] for row in expectedRows if row["ref"] not in index)
    if missing:
        raise DriverCalibrationError(f"coefficient {roleLabel} parent coverage missing row refs")
    for expected in expectedRows:
        actual = index[expected["ref"]]
        if (
            actual["role"] != expected["role"]
            or actual["eventTime"] != expected["eventTime"]
            or actual["availableAt"] != expected["availableAt"]
            or actual["unit"] != expected["unit"]
        ):
            raise DriverCalibrationError(f"coefficient {roleLabel} parent coverage row mismatch")
        try:
            _assertClose(actual["value"], expected["value"], f"{roleLabel} parent coverage value")
        except DriverCalibrationError as error:
            raise DriverCalibrationError(f"coefficient {roleLabel} parent coverage row mismatch") from error


def _validateCoefficientReport(report: DriverCoefficientOosReport) -> None:
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
        _validateFrameBinding(oosFrameBinding, "OOS")
        if (
            oosFrameBinding.rowCount != len(rows)
            or oosFrameBinding.sourceBatchReceiptId not in spec.sourceParentReceiptIds
            or oosFrameBinding.labelBatchReceiptId not in spec.labelParentReceiptIds
            or oosFrameBinding.sourceVariableId != receipt.sourceVariableId
            or oosFrameBinding.targetVariableId != receipt.targetVariableId
            or oosFrameBinding.sourceUnit != receipt.sourceUnit
            or oosFrameBinding.targetUnit != receipt.targetUnit
        ):
            raise DriverCalibrationError("coefficient OOS observation frame binding mismatch")
    if receipt.status == "rejected" or receipt.validationStatus == "rejected":
        raise DriverCalibrationError("rejected coefficient receipt cannot be OOS evaluated")
    expectedUnit = f"{OPERATING_TARGET_UNITS[receipt.targetShock]}/{receipt.sourceUnit}"
    if receipt.coefficientUnit != expectedUnit:
        raise DriverCalibrationError("coefficient receipt unit drift")
    traceRows: list[DriverCoefficientOosTraceRow] = []
    squared = 0.0
    absolute = 0.0
    residualTotal = 0.0
    baselineSquared = 0.0
    baselineValue = _finite(spec.baselineValue, "oos.baselineValue")
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
    nOrigins = len(traceRows)
    mse = squared / nOrigins
    baselineMse = baselineSquared / nOrigins
    if baselineMse <= 1e-24:
        raise DriverCalibrationError("coefficient OOS baseline has no loss to beat")
    rmse = math.sqrt(mse)
    mae = absolute / nOrigins
    bias = residualTotal / nOrigins
    skill = 1.0 - mse / baselineMse
    reasons: list[str] = []
    if receipt.historyStatus != "asKnown":
        reasons.append("receiptHistoryNotAsKnown")
    disallowedWarnings = tuple(warning for warning in receipt.warnings if warning not in _BASE_RECEIPT_WARNINGS)
    if disallowedWarnings:
        reasons.append("receiptHasNonAdmissionWarnings")
    if nOrigins < spec.minOosOrigins:
        reasons.append("oosOriginsBelowMinimum")
    if skill < spec.minSkillVsBaseline:
        reasons.append("skillBelowThreshold")
    if rmse > spec.maxRmse:
        reasons.append("rmseAboveThreshold")
    if abs(bias) > spec.maxAbsBias:
        reasons.append("biasAboveThreshold")
    if not receipt.sourceParentReceiptIds:
        reasons.append("fitSourceParentsMissing")
    if not receipt.labelParentReceiptIds:
        reasons.append("fitLabelParentsMissing")
    if not spec.sourceParentReceiptIds:
        reasons.append("oosSourceParentsMissing")
    if not spec.labelParentReceiptIds:
        reasons.append("oosLabelParentsMissing")
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


def _verifyCoefficientParent(
    admissionVerifier: AdmissionVerifier,
    receiptId: str,
    *,
    role: str,
    allowedKinds: set[str],
    maxKnowledgeAsOf: str,
    decisionAsOf: str,
) -> AdmissionReceipt:
    try:
        parent = admissionVerifier.verify(receiptId)
    except RuntimeError as error:
        raise DriverCalibrationError(f"coefficient parent admission verification failed: {error}") from error
    if (
        parent.kind not in allowedKinds
        or parent.status != "verifiedVintage"
        or parent.revisionPolicy != "asKnown"
        or parent.coverage != "asOfExact"
    ):
        raise DriverCalibrationError(f"coefficient {role} parent receipt must be verified vintage")
    if _dateText(parent.knowledgeAsOf, f"{role} parent knowledgeAsOf") > _dateText(
        maxKnowledgeAsOf,
        f"{role} parent maxKnowledgeAsOf",
    ):
        raise DriverCalibrationError(f"coefficient {role} parent knowledge is after coefficient cutoff")
    if _dateText(parent.issuedAt, f"{role} parent issuedAt") > _dateText(decisionAsOf, "decisionAsOf"):
        raise DriverCalibrationError(f"coefficient {role} parent is not available by decisionAsOf")
    return parent


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
