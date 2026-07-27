"""계수 승인 룰 명세와 그 내용 해시.

서명 영수증이 어떤 룰 아래 발급됐는지는 룰 본문의 정규 해시로 결속된다. 그래서
룰 명세는 값이 아니라 계약이고, 한 글자만 바뀌어도 기존 승인이 전부 무효가 된다.
타입 정의와 섞어 두면 무해해 보이는 편집이 승인 파기로 번지므로 따로 세운다.
"""

from __future__ import annotations

from dartlab.simulate.driverCalibrationContracts import (
    COEFFICIENT_OOS_VERSION,
    MULTIVARIABLE_COEFFICIENT_OOS_VERSION,
    PARENT_COVERAGE_VERSION,
)
from dartlab.simulate.vintage import canonicalPayloadHash

DRIVER_COEFFICIENT_RULE_ID = "driver-coefficient-oos-admission"


DRIVER_COEFFICIENT_RULE_VERSION = "1"


MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID = "driver-coefficient-vector-oos-admission"


MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION = "1"


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


MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_SPEC = {
    "ruleId": MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
    "ruleVersion": MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
    "rulePurpose": "admit a driver coefficient vector after held-out PIT replay and signed lineage checks",
    "reportContract": {
        "generatorVersion": MULTIVARIABLE_COEFFICIENT_OOS_VERSION,
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
            "featureSpecHash",
            "designFrameHash",
            "coefficientVectorHash",
            "oosSpecHash",
            "oosGridHash",
            "oosOutcomeHash",
            "predictionTraceHash",
            "reportId",
        ),
    },
    "heldOutContract": DRIVER_COEFFICIENT_RULE_SPEC["heldOutContract"],
    "thresholdContract": DRIVER_COEFFICIENT_RULE_SPEC["thresholdContract"],
    "parentContract": {
        **DRIVER_COEFFICIENT_RULE_SPEC["parentContract"],
        "providerBatchFrameReplay": "providerObservationBatch parents require signed multivariable design frame replay",
        "rowCoverageRequired": (
            "fit source cells",
            "fit label",
            "OOS source cells",
            "OOS label",
        ),
    },
    "admissionReceiptContract": DRIVER_COEFFICIENT_RULE_SPEC["admissionReceiptContract"],
    "replayContract": {
        "artifactBytes": "canonicalPayloadBytes(_multivariableOosReportPayload(report))",
        "gridHash": "_multivariableOriginGridHashFromTraceRows(report.traceRows)",
        "outcomeHash": "_multivariableOutcomeHashFromTraceRows(report.traceRows)",
        "predictionTraceHash": "_multivariablePredictionTraceHash(report trace rows and metrics)",
        "metrics": ("mse", "baselineMse", "rmse", "mae", "bias", "skillVsBaseline"),
        "exposureBoundary": "only VerifiedDriverCoefficientAdmission can become measuredAssociation exposures",
    },
}


MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH = canonicalPayloadHash(MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_SPEC)
