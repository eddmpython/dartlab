"""Fit PIT driver coefficients without granting path or policy admission.

This module is the measured-law boundary between a registered source factor
and an operating shock target. It accepts an already compiled driver registry
result plus an origin-level calibration frame, fits only observable forward
labels, and returns a receipt that can be referenced by an operating exposure.
It does not admit paths, transfer calibrated weights, or recommend policies.

계약면은 그대로 두고 구현만 도메인 형제 모듈로 나눴다. 이 파일은 이제 그 모듈들의
단일 진입점이며, 기존 import 경로 (`dartlab.simulate.driverCalibration`) 를 쓰던
호출부는 아무것도 바꿀 필요가 없다. 실제 코드는 다음 자리에 있다.

- `driverCalibrationContracts`: 상수와 전 dataclass
- `driverCoefficientRules`: 승인 룰 명세와 그 내용 해시
- `driverCalibrationKernel`: 두 반쪽이 공유하는 PIT 원시 연산
- `driverCoefficientFrameBinding`: 서명 프레임 결속 검증과 재생
- `driverCoefficientLineage`: 부모 영수증 검증과 커버리지 아티팩트
- `driverCoefficient{Receipt,Fit,Oos,Admission}`: 스칼라 계수 반쪽
- `driverCoefficientVector{Receipt,Fit,Oos,Admission}`: 벡터 계수 반쪽
"""

from __future__ import annotations

from dartlab.simulate.driverCalibrationContracts import (
    _BASE_RECEIPT_WARNINGS,
    _BENIGN_REGISTRY_WARNINGS,
    _CALIBRATION_METHODS,
    _OBSERVABLE_TARGET_KINDS,
    _OBSERVATION_FACTOR_TIMING_COMPATIBILITY,
    _OOS_STATUS_SET,
    CALIBRATION_VERSION,
    COEFFICIENT_OOS_VERSION,
    MULTIVARIABLE_CALIBRATION_VERSION,
    MULTIVARIABLE_COEFFICIENT_OOS_VERSION,
    PARENT_COVERAGE_VERSION,
    DriverCalibrationError,
    DriverCalibrationTarget,
    DriverCoefficientCalibrationReceipt,
    DriverCoefficientCalibrationSpec,
    DriverCoefficientOosReport,
    DriverCoefficientOosSpec,
    DriverCoefficientOosTraceRow,
    DriverCoefficientTraceRow,
    DriverObservationFrameBinding,
    MultivariableDriverCoefficientCalibrationReceipt,
    MultivariableDriverCoefficientCalibrationSpec,
    MultivariableDriverCoefficientOosReport,
    MultivariableDriverCoefficientOosSpec,
    MultivariableDriverCoefficientOosTraceRow,
    MultivariableDriverCoefficientTerm,
    MultivariableDriverCoefficientTraceRow,
    MultivariableDriverDesignFrameBinding,
    MultivariableDriverSourceCell,
    VerifiedDriverCoefficientAdmission,
)
from dartlab.simulate.driverCalibrationKernel import (
    _assertClose,
    _dateParts,
    _dateText,
    _dedupe,
    _driverSourceFactorContractHash,
    _finite,
    _periodIndex,
    _sourceFactor,
    _validateOosHorizon,
    _validateReceiptIds,
    _validateTarget,
    _validDigest,
)
from dartlab.simulate.driverCoefficientAdmission import (
    _verifyCoefficientParents,
    calibrationReceiptToOperatingExposure,
    validateDriverCoefficientAdmission,
)
from dartlab.simulate.driverCoefficientFit import (
    _cleanCalibrationRows,
    _fitThroughOrigin,
    _requiredColumns,
    _validateSpec,
    fitDriverCoefficientPit,
    fitDriverCoefficientPitFromObservationFrame,
)
from dartlab.simulate.driverCoefficientFrameBinding import (
    _designFrameBindingFromObservationFrame,
    _designSpecFromBinding,
    _frameBindingFromObservationFrame,
    _frameSpecFromBinding,
    _providerBatchFromParent,
    _validateDesignFrameBinding,
    _validateFrameBinding,
    _verifyMultivariableDesignFrameReplay,
    _verifyObservationFrameReplay,
)
from dartlab.simulate.driverCoefficientLineage import (
    _coverageIndex,
    _coverageRow,
    _coverageRowsFromManifest,
    _coverageRowsFromParent,
    _coverageRowsFromProviderBatch,
    _expectedCoverageRowsFromTraceRows,
    _expectedMultivariableCoverageRowsFromTraceRows,
    _verifyCoefficientParent,
    _verifyParentCoverage,
)
from dartlab.simulate.driverCoefficientOos import (
    _cleanOosRows,
    _oosRequiredColumns,
    _validateCoefficientReport,
    _validateOosSpec,
    driverCoefficientAdmissionArtifact,
    driverCoefficientAdmissionParentReceiptIds,
    driverCoefficientAdmissionSubjectHash,
    evaluateDriverCoefficientOos,
    evaluateDriverCoefficientOosFromObservationFrame,
)
from dartlab.simulate.driverCoefficientReceipt import (
    _calibrationCoefficientTraceHash,
    _calibrationOriginGridHashFromTraceRows,
    _calibrationReceiptPayload,
    _oosGridHashFromTraceRows,
    _oosOutcomeHashFromTraceRows,
    _oosReportPayload,
    _predictionTraceHash,
    _validateCalibrationReceipt,
)
from dartlab.simulate.driverCoefficientRules import (
    _LABEL_PARENT_KINDS,
    _SOURCE_PARENT_KINDS,
    DRIVER_COEFFICIENT_RULE_HASH,
    DRIVER_COEFFICIENT_RULE_ID,
    DRIVER_COEFFICIENT_RULE_SPEC,
    DRIVER_COEFFICIENT_RULE_VERSION,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_SPEC,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
)
from dartlab.simulate.driverCoefficientVectorAdmission import (
    _verifyMultivariableCoefficientParents,
    multivariableCalibrationReceiptToOperatingExposures,
    validateMultivariableDriverCoefficientAdmission,
)
from dartlab.simulate.driverCoefficientVectorFit import (
    _cleanMultivariableRows,
    _featureTermsFromFactors,
    _fitMultivariableThroughOrigin,
    _multivariableSourceFactors,
    _requiredDesignColumns,
    _solveLinearSystem,
    _validateMultivariableSpec,
    fitMultivariableDriverCoefficientPit,
    fitMultivariableDriverCoefficientPitFromObservationFrame,
)
from dartlab.simulate.driverCoefficientVectorOos import (
    _validateMultivariableCoefficientReport,
    _validateMultivariableOosSpec,
    evaluateMultivariableDriverCoefficientOos,
    evaluateMultivariableDriverCoefficientOosFromObservationFrame,
    multivariableDriverCoefficientAdmissionArtifact,
    multivariableDriverCoefficientAdmissionParentReceiptIds,
    multivariableDriverCoefficientAdmissionSubjectHash,
)
from dartlab.simulate.driverCoefficientVectorReceipt import (
    _coefficientVectorHash,
    _featureSpecHash,
    _multivariableCalibrationReceiptPayload,
    _multivariableCoefficientTraceHash,
    _multivariableOosReportPayload,
    _multivariableOriginGridHashFromTraceRows,
    _multivariableOutcomeHashFromTraceRows,
    _multivariablePredictionTraceHash,
    _predictMultivariable,
    _validateMultivariableCalibrationReceipt,
)
from dartlab.simulate.driverObservationFrames import (
    _sourceAvailableColumn,
    _sourceEventColumn,
    _sourceKnowledgeColumn,
    _sourceRefColumn,
    _sourceValueColumn,
)

# 이 파사드가 내보내는 이름. 예전 모듈의 공개 표면을 그대로 유지하려고 재내보내는 것이라
# 본문에서 쓰이지 않는다. 명시해 두지 않으면 죽은 코드 검사가 재내보내기를 미사용 import 로
# 잡는다. 실제로는 여덟 이름 모두 다른 모듈이 이 경로로 가져다 쓴다.
__all__ = [
    "DriverCalibrationError",
    "DriverCalibrationTarget",
    "DriverCoefficientCalibrationReceipt",
    "DriverCoefficientCalibrationSpec",
    "DriverCoefficientOosReport",
    "DriverCoefficientOosSpec",
    "DriverCoefficientOosTraceRow",
    "DriverCoefficientTraceRow",
    "DriverObservationFrameBinding",
    "MultivariableDriverCoefficientCalibrationReceipt",
    "MultivariableDriverCoefficientCalibrationSpec",
    "MultivariableDriverCoefficientOosReport",
    "MultivariableDriverCoefficientOosSpec",
    "MultivariableDriverCoefficientOosTraceRow",
    "MultivariableDriverCoefficientTerm",
    "MultivariableDriverCoefficientTraceRow",
    "MultivariableDriverDesignFrameBinding",
    "MultivariableDriverSourceCell",
    "VerifiedDriverCoefficientAdmission",
    "calibrationReceiptToOperatingExposure",
    "driverCoefficientAdmissionArtifact",
    "driverCoefficientAdmissionParentReceiptIds",
    "driverCoefficientAdmissionSubjectHash",
    "evaluateDriverCoefficientOos",
    "evaluateDriverCoefficientOosFromObservationFrame",
    "evaluateMultivariableDriverCoefficientOos",
    "evaluateMultivariableDriverCoefficientOosFromObservationFrame",
    "fitDriverCoefficientPit",
    "fitDriverCoefficientPitFromObservationFrame",
    "fitMultivariableDriverCoefficientPit",
    "fitMultivariableDriverCoefficientPitFromObservationFrame",
    "multivariableCalibrationReceiptToOperatingExposures",
    "multivariableDriverCoefficientAdmissionArtifact",
    "multivariableDriverCoefficientAdmissionParentReceiptIds",
    "multivariableDriverCoefficientAdmissionSubjectHash",
    "validateDriverCoefficientAdmission",
    "validateMultivariableDriverCoefficientAdmission",
]
