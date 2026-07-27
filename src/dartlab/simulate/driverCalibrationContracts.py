"""PIT 계수 보정 계약면. 상수·승인 룰 명세·전 dataclass 의 단일 정의처.

계수 보정은 스칼라(단일 source) 와 벡터(source 다변량) 두 벌이 같은 프로토콜을
평행 구현한다. 두 벌이 공유하는 것은 "무엇을 계약이라 부르는가" 뿐이라, 타입과
룰 명세만 여기 모으고 계산·검증·승인은 각 반쪽의 형제 모듈이 가져간다.
이 모듈은 계산을 하지 않는 순수 선언면이다.
"""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.simulate.admissionRegistry import AdmissionReceipt
from dartlab.simulate.driverObservationFrames import (
    DRIVER_DESIGN_FRAME_VERSION,
    DRIVER_OBSERVATION_FRAME_VERSION,
    DriverDesignColumnSpec,
)
from dartlab.simulate.vintage import canonicalPayloadHash

CALIBRATION_VERSION = "driver-coefficient-calibration-v1"


COEFFICIENT_OOS_VERSION = "driver-coefficient-oos-v1"


MULTIVARIABLE_CALIBRATION_VERSION = "driver-coefficient-vector-calibration-v1"


MULTIVARIABLE_COEFFICIENT_OOS_VERSION = "driver-coefficient-vector-oos-v1"


PARENT_COVERAGE_VERSION = "driver-coefficient-parent-coverage-v1"


_OBSERVABLE_TARGET_KINDS = {"observedOutcome", "realizedOutcome", "observedOperatingShock"}


_CALIBRATION_METHODS = {"olsThroughOrigin"}


_OOS_STATUS_SET = {"oosEligible", "rejected"}


_OBSERVATION_FACTOR_TIMING_COMPATIBILITY = {
    "change": {"flow", "ratio"},
    "innovation": {"flow", "ratio"},
    "level": {"stock"},
    "rate": {"ratio"},
}


_BASE_RECEIPT_WARNINGS = {
    "coefficientCalibrationNotAdmitted",
    "coefficientRequiresOosAdmission",
    "registryValidation:retrospectiveOnly",
    "registryWarning:historyStatus:asKnown",
}


_BENIGN_REGISTRY_WARNINGS = {"historyStatus:asKnown"}


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


@dataclass(frozen=True)
class MultivariableDriverDesignFrameBinding:
    """Signed multivariable design frame metadata bound into a coefficient vector receipt."""

    frameId: str
    frameHash: str
    specHash: str
    rowCount: int
    sourceBatchReceiptIds: tuple[str, ...]
    labelBatchReceiptId: str
    sourceColumns: tuple[DriverDesignColumnSpec, ...]
    labelSignalId: str
    targetVariableId: str
    targetUnit: str
    frequency: str
    stepSpan: int
    horizonSteps: int
    originStart: str
    originThrough: str
    labelEvidenceRoles: tuple[str, ...]
    selectionRuleId: str
    originKnowledgePolicy: str
    sourceRefPolicy: str
    missingPolicy: str
    droppedOriginCount: int
    droppedOriginHash: str
    missingCountByVariable: tuple[tuple[str, int], ...]
    columnOrderHash: str
    schemaVersion: str = DRIVER_DESIGN_FRAME_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceBatchReceiptIds", tuple(self.sourceBatchReceiptIds))
        object.__setattr__(self, "sourceColumns", tuple(self.sourceColumns))
        object.__setattr__(self, "labelEvidenceRoles", tuple(self.labelEvidenceRoles))
        object.__setattr__(self, "missingCountByVariable", tuple(self.missingCountByVariable))


@dataclass(frozen=True)
class MultivariableDriverCoefficientTerm:
    """One scalar coefficient inside a measured coefficient vector."""

    position: int
    variableId: str
    coefficient: float
    coefficientUnit: str
    sourceUnit: str
    sourceFrequency: str
    sourceTiming: str
    sourceTransformId: str
    sourceFactorContractHash: str


@dataclass(frozen=True)
class MultivariableDriverSourceCell:
    """One source observation cell used by a multivariable coefficient row."""

    variableId: str
    eventTime: str
    availableAt: str
    knowledgeAsOf: str
    value: float
    unit: str
    sourceRef: str


@dataclass(frozen=True)
class MultivariableDriverCoefficientTraceRow:
    """One fit origin for a coefficient vector and its residual trace."""

    originId: str
    originEventTime: str
    originKnowledgeAsOf: str
    sourceAvailableAt: str
    targetEventTime: str
    targetAvailableAt: str
    sourceCells: tuple[MultivariableDriverSourceCell, ...]
    targetValue: float
    fittedValue: float
    residual: float
    labelSourceRef: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceCells", tuple(self.sourceCells))


@dataclass(frozen=True)
class MultivariableDriverCoefficientCalibrationSpec:
    """PIT origin-grid and model contract for a source vector to target coefficient fit."""

    calibrationId: str
    sourceVariableIds: tuple[str, ...]
    minOrigins: int
    lagSteps: int = 0
    responseKernel: tuple[float, ...] = (1.0,)
    method: str = "olsThroughOrigin"
    fitIntercept: bool = False
    sourceParentReceiptIds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceVariableIds", tuple(self.sourceVariableIds))
        object.__setattr__(self, "responseKernel", tuple(self.responseKernel))
        object.__setattr__(self, "sourceParentReceiptIds", tuple(self.sourceParentReceiptIds))


@dataclass(frozen=True)
class MultivariableDriverCoefficientCalibrationReceipt:
    """Fit receipt for one measured association coefficient vector."""

    calibrationId: str
    receiptId: str
    receiptHash: str
    generatorVersion: str
    status: str
    validationStatus: str
    historyStatus: str
    calibrationKnowledgeAsOf: str
    sourceVariableIds: tuple[str, ...]
    targetVariableId: str
    targetShock: str
    targetUnit: str
    coefficientTerms: tuple[MultivariableDriverCoefficientTerm, ...]
    intercept: float
    residualStandardError: float
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
    featureSpecHash: str
    designFrameHash: str
    coefficientVectorHash: str
    calibrationSpecHash: str
    originGridHash: str
    targetOutcomeHash: str
    coefficientTraceHash: str
    warnings: tuple[str, ...]
    sourceRefs: tuple[str, ...]
    sourceParentReceiptIds: tuple[str, ...]
    labelParentReceiptIds: tuple[str, ...]
    traceRows: tuple[MultivariableDriverCoefficientTraceRow, ...]
    fitDesignFrameBinding: MultivariableDriverDesignFrameBinding

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceVariableIds", tuple(self.sourceVariableIds))
        object.__setattr__(self, "coefficientTerms", tuple(self.coefficientTerms))
        object.__setattr__(self, "responseKernel", tuple(self.responseKernel))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))
        object.__setattr__(self, "sourceParentReceiptIds", tuple(self.sourceParentReceiptIds))
        object.__setattr__(self, "labelParentReceiptIds", tuple(self.labelParentReceiptIds))
        object.__setattr__(self, "traceRows", tuple(self.traceRows))


@dataclass(frozen=True)
class MultivariableDriverCoefficientOosSpec:
    """Held-out admission thresholds for one coefficient vector receipt."""

    evaluationId: str
    minOosOrigins: int
    minSkillVsBaseline: float
    maxRmse: float
    maxAbsBias: float
    baselineValue: float
    frequency: str
    stepSpan: int
    maxAdmittedStep: int
    sourceParentReceiptIds: tuple[str, ...] = ()
    labelParentReceiptIds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceParentReceiptIds", tuple(self.sourceParentReceiptIds))
        object.__setattr__(self, "labelParentReceiptIds", tuple(self.labelParentReceiptIds))


@dataclass(frozen=True)
class MultivariableDriverCoefficientOosTraceRow:
    """One held-out row scored by a fixed coefficient vector."""

    originId: str
    originEventTime: str
    originKnowledgeAsOf: str
    sourceAvailableAt: str
    targetEventTime: str
    targetAvailableAt: str
    sourceCells: tuple[MultivariableDriverSourceCell, ...]
    targetValue: float
    predictedValue: float
    baselineValue: float
    residual: float
    baselineResidual: float
    labelSourceRef: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceCells", tuple(self.sourceCells))


@dataclass(frozen=True)
class MultivariableDriverCoefficientOosReport:
    """Unsigned OOS report that can admit a coefficient vector artifact."""

    evaluationId: str
    reportId: str
    generatorVersion: str
    status: str
    admissionStatus: str
    receiptHash: str
    receiptId: str
    calibrationId: str
    sourceVariableIds: tuple[str, ...]
    targetVariableId: str
    targetShock: str
    targetUnit: str
    coefficientTerms: tuple[MultivariableDriverCoefficientTerm, ...]
    pathSetHash: str
    factorContractHash: str
    featureSpecHash: str
    designFrameHash: str
    coefficientVectorHash: str
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
    traceRows: tuple[MultivariableDriverCoefficientOosTraceRow, ...]
    fitDesignFrameBinding: MultivariableDriverDesignFrameBinding
    oosDesignFrameBinding: MultivariableDriverDesignFrameBinding

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceVariableIds", tuple(self.sourceVariableIds))
        object.__setattr__(self, "coefficientTerms", tuple(self.coefficientTerms))
        object.__setattr__(self, "reasons", tuple(self.reasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))
        object.__setattr__(self, "fitSourceParentReceiptIds", tuple(self.fitSourceParentReceiptIds))
        object.__setattr__(self, "fitLabelParentReceiptIds", tuple(self.fitLabelParentReceiptIds))
        object.__setattr__(self, "oosSourceParentReceiptIds", tuple(self.oosSourceParentReceiptIds))
        object.__setattr__(self, "oosLabelParentReceiptIds", tuple(self.oosLabelParentReceiptIds))
        object.__setattr__(self, "traceRows", tuple(self.traceRows))
