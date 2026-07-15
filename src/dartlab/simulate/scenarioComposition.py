"""Assemble driver paths, operating bridges, and strategies into scenario comparisons.

This module is an internal experiment envelope. It does not create a new public
verb, admit evidence, fit coefficients, or promote a conditional run to a
recommendation. Its job is to keep future assumptions in paths, company
interventions in strategies, and run every strategy over the same path ensemble
inside each named scenario case.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from dartlab.simulate.driverCalibration import (
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
    MultivariableDriverCoefficientCalibrationReceipt,
    MultivariableDriverCoefficientOosReport,
    VerifiedDriverCoefficientAdmission,
    multivariableDriverCoefficientAdmissionParentReceiptIds,
    multivariableDriverCoefficientAdmissionSubjectHash,
)
from dartlab.simulate.driverPaths import (
    DriverPathSet,
    addDriverPathConditionFactorOverlay,
    driverFactorsToOperatingSpecs,
    replaceDriverPathAssumptionStep,
)
from dartlab.simulate.operatingBridge import (
    OperatingShockBaseline,
    OperatingTransmissionExposure,
    bridgeOperatingPath,
)
from dartlab.simulate.operatingWorld import OperatingWorldInputs, runOperatingStrategies
from dartlab.simulate.stateSupport import StatePrimitive
from dartlab.simulate.vintage import canonicalPayloadBytes, canonicalPayloadHash
from dartlab.simulate.world import (
    PathTrace,
    ScenarioPath,
    SimulationRun,
    StrategySpec,
    bindAdmittedPathContent,
    bindPathAdmissionReceipt,
    pathSetAdmissionSubjectHash,
    strategyContractHash,
)

if TYPE_CHECKING:
    from dartlab.simulate.admissionRegistry import AdmissionReceipt, AdmissionVerifier
    from dartlab.simulate.driverRegistry import DriverRegistryAudit
    from dartlab.simulate.policyEvaluation import PolicyAdmissionEvidence
    from dartlab.simulate.stateCompiler import CompiledPointInTimeState

SCENARIO_COMPOSITION_VERSION = "scenario-composition-v1"
ONE_COMPANY_SCENARIO_LOOP_VERSION = "one-company-scenario-loop-v1"
CONDITIONAL_SCENARIO_EXPERIMENT_VERSION = "conditional-scenario-experiment-v1"
SCENARIO_PATH_PACKAGE_VERSION = "scenario-path-package-v1"
COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND = "composedConditionalPathPackage"
COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_ID = "composed-conditional-path-package"
COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_VERSION = "1"
COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_HASH = canonicalPayloadHash(
    {
        "schemaVersion": SCENARIO_PATH_PACKAGE_VERSION,
        "kind": COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND,
        "status": "documented",
        "ruleId": COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_ID,
        "ruleVersion": COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_VERSION,
    }
)
CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_VERSION = "conditional-scenario-experiment-result-v1"
CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND = "conditionalScenarioExperimentResult"
CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_ID = "conditional-scenario-experiment-result"
CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_VERSION = "1"
CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_VERSION,
        "kind": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND,
        "status": "documented",
        "ruleId": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_ID,
        "ruleVersion": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_VERSION,
    }
)
CONDITIONAL_SCENARIO_EXPERIMENT_METRIC_DEFINITION_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_VERSION,
        "definition": "objective-score-cell-regret-v1",
    }
)
CONDITIONAL_SCENARIO_EXPERIMENT_COMPARISON_RULE_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_VERSION,
        "definition": "scenario-strategy-score-leader-v1",
    }
)
CONDITIONAL_SCENARIO_EXPERIMENT_FRAGILITY_RULE_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_VERSION,
        "definition": "leader-margin-fragility-v1",
    }
)
CONDITIONAL_SCENARIO_EXPERIMENT_BLOCKER_RULE_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_VERSION,
        "definition": "conditional-experiment-blocker-v1",
    }
)
CONDITIONAL_STRATEGY_EVALUATION_VERSION = "conditional-strategy-evaluation-v1"
CONDITIONAL_STRATEGY_EVALUATION_KIND = "conditionalStrategyEvaluation"
CONDITIONAL_STRATEGY_EVALUATION_RULE_ID = "conditional-strategy-evaluation"
CONDITIONAL_STRATEGY_EVALUATION_RULE_VERSION = "1"
CONDITIONAL_STRATEGY_EVALUATION_SELECTION_RULE_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_STRATEGY_EVALUATION_VERSION,
        "definition": "leader-frequency-worst-score-regret-breach-v1",
    }
)
CONDITIONAL_STRATEGY_EVALUATION_ROBUSTNESS_RULE_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_STRATEGY_EVALUATION_VERSION,
        "definition": "conditional-leader-classification-v1",
    }
)
CONDITIONAL_STRATEGY_EVALUATION_RULE_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_STRATEGY_EVALUATION_VERSION,
        "kind": CONDITIONAL_STRATEGY_EVALUATION_KIND,
        "status": "documented",
        "ruleId": CONDITIONAL_STRATEGY_EVALUATION_RULE_ID,
        "ruleVersion": CONDITIONAL_STRATEGY_EVALUATION_RULE_VERSION,
        "selectionRuleHash": CONDITIONAL_STRATEGY_EVALUATION_SELECTION_RULE_HASH,
        "robustnessRuleHash": CONDITIONAL_STRATEGY_EVALUATION_ROBUSTNESS_RULE_HASH,
    }
)
CONDITIONAL_STRATEGY_EVALUATION_CONTRACT_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_STRATEGY_EVALUATION_VERSION,
        "kind": CONDITIONAL_STRATEGY_EVALUATION_KIND,
        "metricDefinitionHash": CONDITIONAL_SCENARIO_EXPERIMENT_METRIC_DEFINITION_HASH,
        "comparisonRuleHash": CONDITIONAL_SCENARIO_EXPERIMENT_COMPARISON_RULE_HASH,
        "fragilityDefinitionHash": CONDITIONAL_SCENARIO_EXPERIMENT_FRAGILITY_RULE_HASH,
        "blockerRuleHash": CONDITIONAL_SCENARIO_EXPERIMENT_BLOCKER_RULE_HASH,
        "selectionRuleHash": CONDITIONAL_STRATEGY_EVALUATION_SELECTION_RULE_HASH,
        "robustnessRuleHash": CONDITIONAL_STRATEGY_EVALUATION_ROBUSTNESS_RULE_HASH,
    }
)
CONDITIONAL_PLAY_REPLAY_VERSION = "conditional-play-replay-v1"
CONDITIONAL_PLAY_REPLAY_KIND = "conditionalPlayReplay"
CONDITIONAL_PLAY_REPLAY_CONTRACT_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_PLAY_REPLAY_VERSION,
        "kind": CONDITIONAL_PLAY_REPLAY_KIND,
        "lineageMode": "conditionalWarGameProjection",
        "recommendationStatus": "disabled",
    }
)
CONDITIONAL_PLAY_CONTROL_SURFACE_VERSION = "conditional-play-control-surface-v1"
CONDITIONAL_PLAY_CONTROL_SURFACE_KIND = "conditionalPlayControlSurface"
CONDITIONAL_PLAY_CONTROL_SURFACE_PLANES = (
    "currentState",
    "conditionFactor",
    "assumptionDelta",
    "lawParameter",
    "strategyAction",
)
CONDITIONAL_PLAY_CONTROL_SURFACE_CONTRACT_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_PLAY_CONTROL_SURFACE_VERSION,
        "kind": CONDITIONAL_PLAY_CONTROL_SURFACE_KIND,
        "lineageMode": "conditionalWarGameControlProjection",
        "semanticPlanes": CONDITIONAL_PLAY_CONTROL_SURFACE_PLANES,
        "recommendationStatus": "disabled",
    }
)
CONDITIONAL_PLAY_CONTROL_EXECUTION_VERSION = "conditional-play-control-execution-v1"
CONDITIONAL_PLAY_CONTROL_EXECUTION_KIND = "conditionalPlayControlExecution"
CONDITIONAL_PLAY_SCENARIO_DECK_VERSION = "conditional-play-scenario-deck-v1"
CONDITIONAL_PLAY_SCENARIO_DECK_KIND = "conditionalPlayScenarioDeck"
CONDITIONAL_PLAY_SCENARIO_DECK_RULE_ID = "conditional-play-scenario-deck"
CONDITIONAL_PLAY_SCENARIO_DECK_RULE_VERSION = "1"
CONDITIONAL_PLAY_SCENARIO_DECK_RULE_HASH = canonicalPayloadHash(
    {
        "schemaVersion": CONDITIONAL_PLAY_SCENARIO_DECK_VERSION,
        "kind": CONDITIONAL_PLAY_SCENARIO_DECK_KIND,
        "status": "documented",
        "ruleId": CONDITIONAL_PLAY_SCENARIO_DECK_RULE_ID,
        "ruleVersion": CONDITIONAL_PLAY_SCENARIO_DECK_RULE_VERSION,
        "recommendationStatus": "disabled",
    }
)
CONDITIONAL_PLAY_SCENARIO_DECK_PLANE_ORDER = (
    "currentState",
    "conditionFactor",
    "assumptionDelta",
    "lawParameter",
    "strategyAction",
)
SCENARIO_ASSUMPTION_SET_VERSION = "scenario-assumption-set-v1"
SCENARIO_COEFFICIENT_BINDING_VERSION = "scenario-coefficient-binding-v1"
SCENARIO_EXPOSURE_CONTRACT_VERSION = "scenario-coefficient-exposure-contract-v1"
STRATEGY_SET_VERSION = "strategy-set-v1"
_OPERATING_ACTION_IDS = {"priceChange", "capacityInvestment", "borrow", "repay"}
_ASSUMPTION_REF_PREFIXES = ("assumption:", "assumption://")
_DRIVER_COEFFICIENT_ADMISSION_REF_PREFIX = "driverCoefficientAdmission:"
_PROVIDER_OBSERVATION_BATCH_REF_PREFIX = "providerObservationBatch:"
_PROVIDER_OBSERVATION_BATCH_ID_REF_PREFIX = "providerObservationBatchId:"
_PROVIDER_SOURCE_RECEIPT_REF_PREFIX = "sourceReceiptRef:"
_PRICE_SOURCE_LEG_RECEIPT_REF_PREFIX = "priceSourceLegReceiptId:"
_DERIVED_RETURN_RECEIPT_REF_PREFIX = "derivedReturnReceiptId:"
_ADJUSTMENT_POLICY_HASH_REF_PREFIX = "adjustmentPolicyHash:"
_NORMALIZATION_CONTRACT_HASH_REF_PREFIX = "normalizationContractHash:"
_RETURN_TRANSFORM_REF_PREFIX = "returnTransform:"
_RETURN_FORMULA_REF_PREFIX = "returnFormula:"
_FACTOR_MAPPING_REF_PREFIX = "factorMapping:"
_MACRO_REVISION_POLICY_REF_PREFIX = "macroRevisionPolicy:"
_PROVIDER_OBSERVATION_REF_PREFIXES = (
    _PROVIDER_OBSERVATION_BATCH_REF_PREFIX,
    _PROVIDER_OBSERVATION_BATCH_ID_REF_PREFIX,
)
_STRUCTURED_PROVIDER_LINEAGE_REF_PREFIXES = (
    *_PROVIDER_OBSERVATION_REF_PREFIXES,
    _PROVIDER_SOURCE_RECEIPT_REF_PREFIX,
    _PRICE_SOURCE_LEG_RECEIPT_REF_PREFIX,
    _DERIVED_RETURN_RECEIPT_REF_PREFIX,
    _ADJUSTMENT_POLICY_HASH_REF_PREFIX,
    _NORMALIZATION_CONTRACT_HASH_REF_PREFIX,
    _RETURN_TRANSFORM_REF_PREFIX,
    _RETURN_FORMULA_REF_PREFIX,
    _FACTOR_MAPPING_REF_PREFIX,
    _MACRO_REVISION_POLICY_REF_PREFIX,
)
_STATE_REF_PREFIXES = (
    "compiledState:",
    "initialStateAdmission:",
    "observation:",
    "providerBatch:",
    "providerBatchReceipt:",
    "stateCompilationContract:",
    "stateManifest:",
    "statePrimitive:",
    "stateReceipt:",
    "worldStatePayload:",
    "worldStateVintage:",
)


class ScenarioCompositionError(ValueError):
    """시나리오 case, path, bridge, strategy 역할 경계가 깨지면 발생한다."""


@dataclass(frozen=True)
class OperatingScenarioCase:
    """One named future assumption bundle to run through the operating world."""

    caseId: str
    label: str
    pathSet: DriverPathSet
    exposures: tuple[OperatingTransmissionExposure, ...]
    baselines: tuple[OperatingShockBaseline, ...]
    refs: tuple[str, ...] = ()
    compiledState: CompiledPointInTimeState | None = None
    statePrimitives: tuple[StatePrimitive, ...] = ()
    stateRef: str = ""
    coefficientBindings: tuple["ScenarioCoefficientBinding", ...] = ()
    admissionVerifier: AdmissionVerifier | None = None
    policyAdmissionEvidence: "PolicyAdmissionEvidence | None" = None
    driverRegistryAudit: "DriverRegistryAudit | None" = None
    scenarioPathPackageReceiptId: str = ""
    operatingPathAdmissionReceiptId: str = ""
    operatingPathCertificateId: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "exposures", tuple(self.exposures))
        object.__setattr__(self, "baselines", tuple(self.baselines))
        object.__setattr__(self, "refs", tuple(self.refs))
        object.__setattr__(self, "statePrimitives", tuple(self.statePrimitives))
        object.__setattr__(self, "coefficientBindings", tuple(self.coefficientBindings))


@dataclass(frozen=True)
class ScenarioCoefficientBinding:
    """Thin binding from admitted driver coefficient vector to scenario exposures."""

    admissionReceiptId: str
    subjectHash: str
    ruleHash: str
    ruleId: str
    ruleVersion: str
    parentReceiptIds: tuple[str, ...]
    sourceVariableIds: tuple[str, ...]
    targetShock: str
    frequency: str
    stepSpan: int
    maxAdmittedStep: int
    coefficientVectorHash: str
    featureSpecHash: str
    designFrameHash: str
    exposureContractHash: str
    calibrationId: str = ""
    reportId: str = ""
    fitDesignFrameHash: str = ""
    oosDesignFrameHash: str = ""
    sourceRefs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "parentReceiptIds", tuple(self.parentReceiptIds))
        object.__setattr__(self, "sourceVariableIds", tuple(self.sourceVariableIds))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))


@dataclass(frozen=True)
class ScenarioStrategyScore:
    """One strategy score row inside one scenario case."""

    strategyId: str
    objectiveScores: tuple[float, ...]
    feasible: bool
    breachCount: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "objectiveScores", tuple(float(value) for value in self.objectiveScores))


@dataclass(frozen=True)
class ScenarioBoundaryCounts:
    """Observable boundary counts for a composed scenario case."""

    driverCardCount: int
    pathCount: int
    bridgeCount: int
    admittedPathCount: int
    retrospectivePathCount: int
    unvalidatedPathCount: int
    providerBatchRefCount: int
    explicitAssumptionCount: int
    interventionCount: int
    conditionalWarningCount: int


@dataclass(frozen=True)
class ScenarioExposureLedger:
    """Readable factor to operating shock law row for a scenario case."""

    exposureId: str
    sourceVariableId: str
    targetShock: str
    coefficient: float
    coefficientUnit: str
    evidenceKind: str
    sourceRef: str
    admissionReceiptId: str
    modifierVariableId: str
    modifierUnit: str
    lagSteps: int
    responseKernel: tuple[float, ...]
    aggregationGroup: str
    sourceFrequency: str
    sourceTiming: str
    sourceTransformId: str
    sourceFactorContractHash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "responseKernel", tuple(float(value) for value in self.responseKernel))


@dataclass(frozen=True)
class ScenarioDriverRegistryLedger:
    """Readable registry source selection row for a scenario case."""

    registryId: str
    registryHash: str
    laneIds: tuple[str, ...]
    cardIds: tuple[str, ...]
    factorIds: tuple[str, ...]
    commonObservationCount: int
    sourceObservationCounts: tuple[tuple[str, int], ...]
    eventStart: str
    eventEnd: str
    sourceRefs: tuple[str, ...]
    semanticRefs: tuple[str, ...]
    warnings: tuple[str, ...]
    pathSetHash: str
    pathSetInputHash: str
    validationStatus: str
    historyStatus: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "laneIds", tuple(self.laneIds))
        object.__setattr__(self, "cardIds", tuple(self.cardIds))
        object.__setattr__(self, "factorIds", tuple(self.factorIds))
        object.__setattr__(self, "sourceObservationCounts", tuple(tuple(item) for item in self.sourceObservationCounts))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))
        object.__setattr__(self, "semanticRefs", tuple(self.semanticRefs))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class ScenarioProviderLineageLedger:
    """Structured provider source lineage row for one scenario case."""

    providerLaneLineageHash: str
    providerLineageStatus: tuple[str, ...]
    providerObservationBatchReceiptIds: tuple[str, ...]
    providerObservationBatchIds: tuple[str, ...]
    providerObservationBatchSourceReceiptIds: tuple[str, ...]
    priceSourceLegReceiptIds: tuple[str, ...]
    derivedReturnReceiptIds: tuple[str, ...]
    adjustmentPolicyHashes: tuple[str, ...]
    normalizationContractHashes: tuple[str, ...]
    returnTransformRefs: tuple[str, ...]
    returnTransformHash: str
    factorMappingRefs: tuple[str, ...]
    rawSourceRefs: tuple[str, ...]
    revisedHistoryRefs: tuple[str, ...]
    explicitAssumptionIds: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "providerLineageStatus", tuple(self.providerLineageStatus))
        object.__setattr__(
            self,
            "providerObservationBatchReceiptIds",
            tuple(self.providerObservationBatchReceiptIds),
        )
        object.__setattr__(self, "providerObservationBatchIds", tuple(self.providerObservationBatchIds))
        object.__setattr__(
            self,
            "providerObservationBatchSourceReceiptIds",
            tuple(self.providerObservationBatchSourceReceiptIds),
        )
        object.__setattr__(self, "priceSourceLegReceiptIds", tuple(self.priceSourceLegReceiptIds))
        object.__setattr__(self, "derivedReturnReceiptIds", tuple(self.derivedReturnReceiptIds))
        object.__setattr__(self, "adjustmentPolicyHashes", tuple(self.adjustmentPolicyHashes))
        object.__setattr__(self, "normalizationContractHashes", tuple(self.normalizationContractHashes))
        object.__setattr__(self, "returnTransformRefs", tuple(self.returnTransformRefs))
        object.__setattr__(self, "factorMappingRefs", tuple(self.factorMappingRefs))
        object.__setattr__(self, "rawSourceRefs", tuple(self.rawSourceRefs))
        object.__setattr__(self, "revisedHistoryRefs", tuple(self.revisedHistoryRefs))
        object.__setattr__(self, "explicitAssumptionIds", tuple(self.explicitAssumptionIds))


@dataclass(frozen=True)
class OperatingScenarioCaseResult:
    """Run output and audit envelope for one scenario case."""

    caseId: str
    label: str
    pathSetHash: str
    scenarioPathPackageHash: str
    scenarioPathPackageSubjectHash: str
    scenarioPathPackageReceiptId: str
    scenarioPathPackageReceiptKind: str
    scenarioPathPackageReceiptStatus: str
    pathHistoryInputHash: str
    pathAssumptionHash: str
    pathAssumptionStepHashes: tuple[str, ...]
    basePathSetHash: str
    pathOverlayHash: str
    pathFrequency: str
    pathHorizon: int
    observedHistoryStatus: str
    futureAdjustmentStatus: str
    composedPathAdmissionStatus: str
    pathAdmissionTransferStatus: str
    pathAdmissionTransferBlockedBy: tuple[str, ...]
    policyEvaluationEligibility: str
    bridgeHashes: tuple[str, ...]
    runHash: str
    resultHash: str
    executableHash: str
    parameterHash: str
    dataVintageHash: str
    traceRoot: str
    traceCount: int
    retainedTraceCount: int
    retainedTraces: tuple[PathTrace, ...]
    initialStateAdmissionReceiptId: str
    pathAdmissionReceiptId: str
    pathAdmissionContentHash: str
    pathCertificateIds: tuple[str, ...]
    policyEvaluationCertificateId: str
    policyEvaluationCertificateReceiptId: str
    policyEvaluationCertificateStatus: str
    policyEvaluationParentReceiptIds: tuple[str, ...]
    recommendationSource: str
    recommendationEvidenceKind: str
    recommendationEvidenceReceiptId: str
    conditionalReceiptIdsExcludedFromPolicy: tuple[str, ...]
    decisionStatus: str
    status: str
    weightLabel: str
    recommendation: str | None
    paretoStrategies: tuple[str, ...]
    strategyScores: tuple[ScenarioStrategyScore, ...]
    counts: ScenarioBoundaryCounts
    refs: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "pathAssumptionStepHashes", tuple(self.pathAssumptionStepHashes))
        object.__setattr__(self, "pathAdmissionTransferBlockedBy", tuple(self.pathAdmissionTransferBlockedBy))
        object.__setattr__(self, "bridgeHashes", tuple(self.bridgeHashes))
        object.__setattr__(self, "retainedTraces", tuple(self.retainedTraces))
        object.__setattr__(self, "pathCertificateIds", tuple(self.pathCertificateIds))
        object.__setattr__(self, "policyEvaluationParentReceiptIds", tuple(self.policyEvaluationParentReceiptIds))
        object.__setattr__(
            self,
            "conditionalReceiptIdsExcludedFromPolicy",
            tuple(self.conditionalReceiptIdsExcludedFromPolicy),
        )
        object.__setattr__(self, "paretoStrategies", tuple(self.paretoStrategies))
        object.__setattr__(self, "strategyScores", tuple(self.strategyScores))
        object.__setattr__(self, "refs", tuple(self.refs))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class OperatingScenarioComparison:
    """Conditional comparison result across named scenario cases."""

    comparisonHash: str
    decisionStatus: str
    recommendation: str | None
    caseResults: tuple[OperatingScenarioCaseResult, ...]
    strategyIds: tuple[str, ...]
    strategyContractHashes: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "caseResults", tuple(self.caseResults))
        object.__setattr__(self, "strategyIds", tuple(self.strategyIds))
        object.__setattr__(self, "strategyContractHashes", tuple(self.strategyContractHashes))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class OneCompanyScenarioCaseLedger:
    """Readable case row for one company scenario loop."""

    caseId: str
    label: str
    factorIds: tuple[str, ...]
    conditionRefs: tuple[str, ...]
    assumptionRefs: tuple[str, ...]
    stateRefs: tuple[str, ...]
    pathSetInputHash: str
    pathRegistryHash: str
    pathFactorContractHash: str
    pathSourceRefs: tuple[str, ...]
    providerObservationBatchRefs: tuple[str, ...]
    providerLineage: ScenarioProviderLineageLedger
    providerLaneLineageHash: str
    providerLineageStatus: tuple[str, ...]
    providerObservationBatchReceiptIds: tuple[str, ...]
    providerObservationBatchIds: tuple[str, ...]
    providerObservationBatchSourceReceiptIds: tuple[str, ...]
    priceSourceLegReceiptIds: tuple[str, ...]
    derivedReturnReceiptIds: tuple[str, ...]
    adjustmentPolicyHashes: tuple[str, ...]
    normalizationContractHashes: tuple[str, ...]
    returnTransformRefs: tuple[str, ...]
    returnTransformHash: str
    factorMappingRefs: tuple[str, ...]
    rawSourceRefs: tuple[str, ...]
    revisedHistoryRefs: tuple[str, ...]
    explicitAssumptionIds: tuple[str, ...]
    scenarioPathPackageHash: str
    scenarioPathPackageSubjectHash: str
    scenarioPathPackageReceiptId: str
    scenarioPathPackageReceiptKind: str
    scenarioPathPackageReceiptStatus: str
    scenarioPathPackageParentReceiptIds: tuple[str, ...]
    pathHistoryInputHash: str
    pathAssumptionHash: str
    pathAssumptionStepHashes: tuple[str, ...]
    basePathSetHash: str
    pathFrequency: str
    pathHorizon: int
    basePathAdmissionContentHash: str
    basePathAdmissionSubjectHash: str
    basePathValidationStatus: str
    basePathMaxAdmittedStep: int
    composedPathSetHash: str
    pathOverlayHash: str
    observedHistoryStatus: str
    futureAdjustmentStatus: str
    basePathAdmissionReceiptId: str
    basePathAdmissionScope: str
    composedPathAdmissionStatus: str
    pathAdmissionTransferStatus: str
    pathAdmissionTransferBlockedBy: tuple[str, ...]
    policyEvaluationEligibility: str
    recommendationCeiling: str
    driverRegistryLedger: ScenarioDriverRegistryLedger | None
    exposureLedgers: tuple[ScenarioExposureLedger, ...]
    coefficientAdmissionReceiptIds: tuple[str, ...]
    coefficientBindingHashes: tuple[str, ...]
    coefficientParentReceiptIds: tuple[str, ...]
    pathSetHash: str
    bridgeHashes: tuple[str, ...]
    runHash: str
    resultHash: str
    executableHash: str
    parameterHash: str
    dataVintageHash: str
    traceRoot: str
    traceCount: int
    retainedTraceCount: int
    initialStateAdmissionReceiptId: str
    pathAdmissionReceiptId: str
    pathAdmissionContentHash: str
    pathCertificateIds: tuple[str, ...]
    policyEvaluationCertificateId: str
    policyEvaluationCertificateReceiptId: str
    policyEvaluationCertificateStatus: str
    policyEvaluationParentReceiptIds: tuple[str, ...]
    recommendationSource: str
    recommendationEvidenceKind: str
    recommendationEvidenceReceiptId: str
    conditionalReceiptIdsExcludedFromPolicy: tuple[str, ...]
    decisionStatus: str
    status: str
    weightLabel: str
    recommendation: str | None
    paretoStrategies: tuple[str, ...]
    scoreLeaderStrategies: tuple[str, ...]
    strategyScores: tuple[ScenarioStrategyScore, ...]
    counts: ScenarioBoundaryCounts
    blockedReasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "factorIds", tuple(self.factorIds))
        object.__setattr__(self, "conditionRefs", tuple(self.conditionRefs))
        object.__setattr__(self, "assumptionRefs", tuple(self.assumptionRefs))
        object.__setattr__(self, "stateRefs", tuple(self.stateRefs))
        object.__setattr__(self, "pathSourceRefs", tuple(self.pathSourceRefs))
        object.__setattr__(self, "providerObservationBatchRefs", tuple(self.providerObservationBatchRefs))
        if not isinstance(self.providerLineage, ScenarioProviderLineageLedger):
            raise TypeError("providerLineage must be a ScenarioProviderLineageLedger")
        object.__setattr__(self, "providerLineageStatus", tuple(self.providerLineageStatus))
        object.__setattr__(
            self,
            "providerObservationBatchReceiptIds",
            tuple(self.providerObservationBatchReceiptIds),
        )
        object.__setattr__(self, "providerObservationBatchIds", tuple(self.providerObservationBatchIds))
        object.__setattr__(
            self,
            "providerObservationBatchSourceReceiptIds",
            tuple(self.providerObservationBatchSourceReceiptIds),
        )
        object.__setattr__(self, "priceSourceLegReceiptIds", tuple(self.priceSourceLegReceiptIds))
        object.__setattr__(self, "derivedReturnReceiptIds", tuple(self.derivedReturnReceiptIds))
        object.__setattr__(self, "adjustmentPolicyHashes", tuple(self.adjustmentPolicyHashes))
        object.__setattr__(self, "normalizationContractHashes", tuple(self.normalizationContractHashes))
        object.__setattr__(self, "returnTransformRefs", tuple(self.returnTransformRefs))
        object.__setattr__(self, "factorMappingRefs", tuple(self.factorMappingRefs))
        object.__setattr__(self, "rawSourceRefs", tuple(self.rawSourceRefs))
        object.__setattr__(self, "revisedHistoryRefs", tuple(self.revisedHistoryRefs))
        object.__setattr__(self, "explicitAssumptionIds", tuple(self.explicitAssumptionIds))
        object.__setattr__(
            self,
            "scenarioPathPackageParentReceiptIds",
            tuple(self.scenarioPathPackageParentReceiptIds),
        )
        object.__setattr__(self, "pathAssumptionStepHashes", tuple(self.pathAssumptionStepHashes))
        object.__setattr__(self, "pathAdmissionTransferBlockedBy", tuple(self.pathAdmissionTransferBlockedBy))
        if self.driverRegistryLedger is not None and not isinstance(
            self.driverRegistryLedger, ScenarioDriverRegistryLedger
        ):
            raise TypeError("driverRegistryLedger must be a ScenarioDriverRegistryLedger")
        object.__setattr__(self, "exposureLedgers", tuple(self.exposureLedgers))
        object.__setattr__(self, "coefficientAdmissionReceiptIds", tuple(self.coefficientAdmissionReceiptIds))
        object.__setattr__(self, "coefficientBindingHashes", tuple(self.coefficientBindingHashes))
        object.__setattr__(self, "coefficientParentReceiptIds", tuple(self.coefficientParentReceiptIds))
        object.__setattr__(self, "bridgeHashes", tuple(self.bridgeHashes))
        object.__setattr__(self, "pathCertificateIds", tuple(self.pathCertificateIds))
        object.__setattr__(self, "policyEvaluationParentReceiptIds", tuple(self.policyEvaluationParentReceiptIds))
        object.__setattr__(
            self,
            "conditionalReceiptIdsExcludedFromPolicy",
            tuple(self.conditionalReceiptIdsExcludedFromPolicy),
        )
        object.__setattr__(self, "paretoStrategies", tuple(self.paretoStrategies))
        object.__setattr__(self, "scoreLeaderStrategies", tuple(self.scoreLeaderStrategies))
        object.__setattr__(self, "strategyScores", tuple(self.strategyScores))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class OneCompanyScenarioLoop:
    """One company, two scenario, two strategy conditional experiment ledger."""

    loopHash: str
    schemaVersion: str
    entityId: str
    comparisonHash: str
    decisionStatus: str
    recommendationCeiling: str
    recommendation: str | None
    scenarioCount: int
    strategyCount: int
    strategyIds: tuple[str, ...]
    strategyContractHashes: tuple[str, ...]
    strategyRefs: tuple[str, ...]
    initialStateRefs: tuple[str, ...]
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]
    blockedReasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "strategyIds", tuple(self.strategyIds))
        object.__setattr__(self, "strategyContractHashes", tuple(self.strategyContractHashes))
        object.__setattr__(self, "strategyRefs", tuple(self.strategyRefs))
        object.__setattr__(self, "initialStateRefs", tuple(self.initialStateRefs))
        object.__setattr__(self, "caseLedgers", tuple(self.caseLedgers))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class ConditionalScenarioExperimentCell:
    """One assumption set and strategy score cell in a conditional experiment."""

    caseId: str
    label: str
    strategyId: str
    objectiveScores: tuple[float, ...]
    score: float
    feasible: bool
    breachCount: int
    regret: float
    scoreLeader: bool
    assumptionSetHash: str
    scenarioPathPackageHash: str
    pathSetHash: str
    runHash: str
    resultHash: str
    blockedReasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "objectiveScores", tuple(float(value) for value in self.objectiveScores))
        object.__setattr__(self, "score", float(self.score))
        object.__setattr__(self, "regret", float(self.regret))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))


@dataclass(frozen=True)
class ConditionalStrategySummary:
    """Strategy robustness summary across all assumption sets."""

    strategyId: str
    scoreMedian: float
    scoreWorst: float
    scoreBest: float
    regretMedian: float
    regretWorst: float
    leaderCellCount: int
    leaderFrequency: float
    feasibleCellCount: int
    totalCellCount: int
    breachCount: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "scoreMedian", float(self.scoreMedian))
        object.__setattr__(self, "scoreWorst", float(self.scoreWorst))
        object.__setattr__(self, "scoreBest", float(self.scoreBest))
        object.__setattr__(self, "regretMedian", float(self.regretMedian))
        object.__setattr__(self, "regretWorst", float(self.regretWorst))
        object.__setattr__(self, "leaderFrequency", float(self.leaderFrequency))


@dataclass(frozen=True)
class ConditionalAssumptionFragility:
    """Case-level row showing where strategy leadership is least robust."""

    caseId: str
    label: str
    assumptionSetHash: str
    scenarioPathPackageHash: str
    leaderStrategies: tuple[str, ...]
    runnerUpStrategies: tuple[str, ...]
    leaderScore: float
    runnerUpScore: float
    leaderMargin: float
    scoreSpread: float
    breachStrategies: tuple[str, ...]
    assumptionRefs: tuple[str, ...]
    blockedReasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "leaderStrategies", tuple(self.leaderStrategies))
        object.__setattr__(self, "runnerUpStrategies", tuple(self.runnerUpStrategies))
        object.__setattr__(self, "leaderScore", float(self.leaderScore))
        object.__setattr__(self, "runnerUpScore", float(self.runnerUpScore))
        object.__setattr__(self, "leaderMargin", float(self.leaderMargin))
        object.__setattr__(self, "scoreSpread", float(self.scoreSpread))
        object.__setattr__(self, "breachStrategies", tuple(self.breachStrategies))
        object.__setattr__(self, "assumptionRefs", tuple(self.assumptionRefs))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))


@dataclass(frozen=True)
class ConditionalScenarioExperiment:
    """N assumption sets by N strategies conditional simulation ledger."""

    experimentHash: str
    schemaVersion: str
    entityId: str
    comparisonHash: str
    strategySetHash: str
    simulationSpecHash: str
    resultSetHash: str
    decisionStatus: str
    recommendationCeiling: str
    recommendation: str | None
    scenarioCount: int
    strategyCount: int
    cellCount: int
    objectiveIndex: int
    strategyIds: tuple[str, ...]
    strategyContractHashes: tuple[str, ...]
    initialStateRefs: tuple[str, ...]
    caseLedgerHashes: tuple[str, ...]
    driverRegistryHashes: tuple[str, ...]
    driverRegistryLaneIds: tuple[str, ...]
    driverRegistrySemanticRefs: tuple[str, ...]
    driverRegistrySourceRefs: tuple[str, ...]
    driverRegistryWarnings: tuple[str, ...]
    providerObservationBatchRefs: tuple[str, ...]
    providerLaneLineageHashes: tuple[str, ...]
    providerLineageStatuses: tuple[str, ...]
    providerObservationBatchReceiptIds: tuple[str, ...]
    providerObservationBatchIds: tuple[str, ...]
    providerObservationBatchSourceReceiptIds: tuple[str, ...]
    priceSourceLegReceiptIds: tuple[str, ...]
    derivedReturnReceiptIds: tuple[str, ...]
    adjustmentPolicyHashes: tuple[str, ...]
    normalizationContractHashes: tuple[str, ...]
    returnTransformHashes: tuple[str, ...]
    rawSourceRefs: tuple[str, ...]
    revisedHistoryRefs: tuple[str, ...]
    explicitAssumptionIds: tuple[str, ...]
    pathHistoryInputHashes: tuple[str, ...]
    pathAssumptionHashes: tuple[str, ...]
    pathAssumptionStepHashes: tuple[tuple[str, ...], ...]
    assumptionSetIds: tuple[str, ...]
    assumptionSetHashes: tuple[str, ...]
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]
    strategySummaries: tuple[ConditionalStrategySummary, ...]
    cells: tuple[ConditionalScenarioExperimentCell, ...]
    traceRows: tuple[ConditionalPlayTraceRow, ...]
    fragilityCells: tuple[ConditionalAssumptionFragility, ...]
    blockedReasons: tuple[str, ...]
    warnings: tuple[str, ...]
    playReplayReport: ConditionalPlayReplayReport | None = None
    experimentReceiptSubjectHash: str = ""
    experimentReceiptId: str = ""
    experimentReceiptKind: str = ""
    experimentReceiptStatus: str = ""
    experimentReceiptParentReceiptIds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "strategyIds", tuple(self.strategyIds))
        object.__setattr__(self, "strategyContractHashes", tuple(self.strategyContractHashes))
        object.__setattr__(self, "initialStateRefs", tuple(self.initialStateRefs))
        object.__setattr__(self, "caseLedgerHashes", tuple(self.caseLedgerHashes))
        object.__setattr__(self, "driverRegistryHashes", tuple(self.driverRegistryHashes))
        object.__setattr__(self, "driverRegistryLaneIds", tuple(self.driverRegistryLaneIds))
        object.__setattr__(self, "driverRegistrySemanticRefs", tuple(self.driverRegistrySemanticRefs))
        object.__setattr__(self, "driverRegistrySourceRefs", tuple(self.driverRegistrySourceRefs))
        object.__setattr__(self, "driverRegistryWarnings", tuple(self.driverRegistryWarnings))
        object.__setattr__(self, "providerObservationBatchRefs", tuple(self.providerObservationBatchRefs))
        object.__setattr__(self, "providerLaneLineageHashes", tuple(self.providerLaneLineageHashes))
        object.__setattr__(self, "providerLineageStatuses", tuple(self.providerLineageStatuses))
        object.__setattr__(
            self,
            "providerObservationBatchReceiptIds",
            tuple(self.providerObservationBatchReceiptIds),
        )
        object.__setattr__(self, "providerObservationBatchIds", tuple(self.providerObservationBatchIds))
        object.__setattr__(
            self,
            "providerObservationBatchSourceReceiptIds",
            tuple(self.providerObservationBatchSourceReceiptIds),
        )
        object.__setattr__(self, "priceSourceLegReceiptIds", tuple(self.priceSourceLegReceiptIds))
        object.__setattr__(self, "derivedReturnReceiptIds", tuple(self.derivedReturnReceiptIds))
        object.__setattr__(self, "adjustmentPolicyHashes", tuple(self.adjustmentPolicyHashes))
        object.__setattr__(self, "normalizationContractHashes", tuple(self.normalizationContractHashes))
        object.__setattr__(self, "returnTransformHashes", tuple(self.returnTransformHashes))
        object.__setattr__(self, "rawSourceRefs", tuple(self.rawSourceRefs))
        object.__setattr__(self, "revisedHistoryRefs", tuple(self.revisedHistoryRefs))
        object.__setattr__(self, "explicitAssumptionIds", tuple(self.explicitAssumptionIds))
        object.__setattr__(self, "pathHistoryInputHashes", tuple(self.pathHistoryInputHashes))
        object.__setattr__(self, "pathAssumptionHashes", tuple(self.pathAssumptionHashes))
        object.__setattr__(
            self,
            "pathAssumptionStepHashes",
            tuple(tuple(stepHashes) for stepHashes in self.pathAssumptionStepHashes),
        )
        object.__setattr__(self, "assumptionSetIds", tuple(self.assumptionSetIds))
        object.__setattr__(self, "assumptionSetHashes", tuple(self.assumptionSetHashes))
        object.__setattr__(self, "caseLedgers", tuple(self.caseLedgers))
        object.__setattr__(self, "strategySummaries", tuple(self.strategySummaries))
        object.__setattr__(self, "cells", tuple(self.cells))
        object.__setattr__(self, "traceRows", tuple(self.traceRows))
        object.__setattr__(self, "fragilityCells", tuple(self.fragilityCells))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "experimentReceiptParentReceiptIds", tuple(self.experimentReceiptParentReceiptIds))


@dataclass(frozen=True)
class ConditionalStrategyEvaluationRow:
    """One strategy judgement row derived from a sealed conditional experiment."""

    strategyId: str
    conditionalLeader: bool
    robustnessClass: str
    leaderFrequency: float
    leaderCellCount: int
    totalCellCount: int
    feasibleCellCount: int
    breachCount: int
    scoreMedian: float
    scoreWorst: float
    scoreBest: float
    regretMedian: float
    regretWorst: float
    blockedReasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "leaderFrequency", float(self.leaderFrequency))
        object.__setattr__(self, "scoreMedian", float(self.scoreMedian))
        object.__setattr__(self, "scoreWorst", float(self.scoreWorst))
        object.__setattr__(self, "scoreBest", float(self.scoreBest))
        object.__setattr__(self, "regretMedian", float(self.regretMedian))
        object.__setattr__(self, "regretWorst", float(self.regretWorst))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))


@dataclass(frozen=True)
class ConditionalStrategyFragileCase:
    """Smallest leader margin case that should be surfaced before any strategy claim."""

    caseId: str
    label: str
    assumptionSetHash: str
    scenarioPathPackageHash: str
    leaderStrategies: tuple[str, ...]
    runnerUpStrategies: tuple[str, ...]
    leaderMargin: float
    scoreSpread: float
    breachStrategies: tuple[str, ...]
    blockedReasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "leaderStrategies", tuple(self.leaderStrategies))
        object.__setattr__(self, "runnerUpStrategies", tuple(self.runnerUpStrategies))
        object.__setattr__(self, "leaderMargin", float(self.leaderMargin))
        object.__setattr__(self, "scoreSpread", float(self.scoreSpread))
        object.__setattr__(self, "breachStrategies", tuple(self.breachStrategies))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))


@dataclass(frozen=True)
class ConditionalStrategyEvaluation:
    """Documented strategy judgement over a sealed conditional experiment."""

    evaluationHash: str
    schemaVersion: str
    kind: str
    entityId: str
    experimentReceiptId: str
    experimentReceiptSubjectHash: str
    experimentHash: str
    comparisonReplayHash: str
    simulationSpecHash: str
    resultSetHash: str
    strategySetHash: str
    strategyIds: tuple[str, ...]
    strategyContractHashes: tuple[str, ...]
    caseLedgerHashes: tuple[str, ...]
    caseResultHashes: tuple[str, ...]
    objectiveIndex: int
    decisionStatus: str
    recommendationCeiling: str
    recommendation: str | None
    recommendationStatus: str
    contractHash: str
    metricDefinitionHash: str
    comparisonRuleHash: str
    fragilityDefinitionHash: str
    blockerRuleHash: str
    selectionRuleHash: str
    robustnessRuleHash: str
    evaluationTableHash: str
    leaderboardHash: str
    fragilitySummaryHash: str
    blockerSummaryHash: str
    conditionalLeaderStrategyIds: tuple[str, ...]
    strategyRows: tuple[ConditionalStrategyEvaluationRow, ...]
    fragileCases: tuple[ConditionalStrategyFragileCase, ...]
    parentReceiptIds: tuple[str, ...]
    pathAdmissionReceiptIds: tuple[str, ...]
    policyEvaluationCertificateIds: tuple[str, ...]
    blockedReasons: tuple[str, ...]
    warnings: tuple[str, ...]
    evaluationReceiptSubjectHash: str = ""
    evaluationReceiptId: str = ""
    evaluationReceiptKind: str = ""
    evaluationReceiptStatus: str = ""
    evaluationReceiptParentReceiptIds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "strategyIds", tuple(self.strategyIds))
        object.__setattr__(self, "strategyContractHashes", tuple(self.strategyContractHashes))
        object.__setattr__(self, "caseLedgerHashes", tuple(self.caseLedgerHashes))
        object.__setattr__(self, "caseResultHashes", tuple(self.caseResultHashes))
        object.__setattr__(self, "conditionalLeaderStrategyIds", tuple(self.conditionalLeaderStrategyIds))
        object.__setattr__(self, "strategyRows", tuple(self.strategyRows))
        object.__setattr__(self, "fragileCases", tuple(self.fragileCases))
        object.__setattr__(self, "parentReceiptIds", tuple(self.parentReceiptIds))
        object.__setattr__(self, "pathAdmissionReceiptIds", tuple(self.pathAdmissionReceiptIds))
        object.__setattr__(self, "policyEvaluationCertificateIds", tuple(self.policyEvaluationCertificateIds))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(
            self,
            "evaluationReceiptParentReceiptIds",
            tuple(self.evaluationReceiptParentReceiptIds),
        )


@dataclass(frozen=True)
class ConditionalPlayConditionRow:
    """Condition lane row for the replay projection."""

    rowHash: str
    caseId: str
    label: str
    assumptionSetHash: str
    pathHistoryInputHash: str
    pathAssumptionHash: str
    pathAssumptionStepHashes: tuple[str, ...]
    observedHistoryStatus: str
    futureAdjustmentStatus: str
    composedPathAdmissionStatus: str
    pathAdmissionReceiptId: str
    policyEvaluationCertificateId: str
    basePathMaxAdmittedStep: int
    pathHorizon: int
    pathFrequency: str
    driverRegistryLaneIds: tuple[str, ...]
    factorIds: tuple[str, ...]
    providerLaneLineageHash: str
    providerLineageStatus: tuple[str, ...]
    blockedReasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "pathAssumptionStepHashes", tuple(self.pathAssumptionStepHashes))
        object.__setattr__(self, "driverRegistryLaneIds", tuple(self.driverRegistryLaneIds))
        object.__setattr__(self, "factorIds", tuple(self.factorIds))
        object.__setattr__(self, "providerLineageStatus", tuple(self.providerLineageStatus))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))


@dataclass(frozen=True)
class ConditionalPlayStrategyRow:
    """Strategy action and robustness row for the replay projection."""

    rowHash: str
    strategyId: str
    strategyContractHash: str
    actionIds: tuple[str, ...]
    actionsByStep: tuple[tuple[tuple[str, float], ...], ...]
    conditionalLeader: bool
    leaderFrequency: float
    scoreMedian: float
    scoreWorst: float
    scoreBest: float
    regretWorst: float
    feasibleCellCount: int
    totalCellCount: int
    breachCount: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "actionIds", tuple(self.actionIds))
        object.__setattr__(
            self,
            "actionsByStep",
            tuple(tuple((key, float(value)) for key, value in row) for row in self.actionsByStep),
        )
        object.__setattr__(self, "leaderFrequency", float(self.leaderFrequency))
        object.__setattr__(self, "scoreMedian", float(self.scoreMedian))
        object.__setattr__(self, "scoreWorst", float(self.scoreWorst))
        object.__setattr__(self, "scoreBest", float(self.scoreBest))
        object.__setattr__(self, "regretWorst", float(self.regretWorst))


@dataclass(frozen=True)
class ConditionalPlayCellRow:
    """Case by strategy score row for the replay projection."""

    rowHash: str
    caseId: str
    label: str
    strategyId: str
    objectiveScores: tuple[float, ...]
    score: float
    feasible: bool
    breachCount: int
    regret: float
    scoreLeader: bool
    assumptionSetHash: str
    scenarioPathPackageHash: str
    pathSetHash: str
    runHash: str
    resultHash: str
    blockedReasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "objectiveScores", tuple(float(value) for value in self.objectiveScores))
        object.__setattr__(self, "score", float(self.score))
        object.__setattr__(self, "regret", float(self.regret))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))


@dataclass(frozen=True)
class ConditionalPlayTraceRow:
    """State transition row retained from the executed operating world."""

    rowHash: str
    caseId: str
    label: str
    strategyId: str
    pathId: str
    step: int
    beforeState: tuple[tuple[str, float], ...]
    shocks: tuple[tuple[str, float], ...]
    issuedActions: tuple[tuple[str, float], ...]
    effectiveActions: tuple[tuple[str, float], ...]
    actionCost: float
    afterState: tuple[tuple[str, float], ...]
    lawIds: tuple[str, ...]
    lawEvidenceKinds: tuple[str, ...]
    lawCertificateIds: tuple[str, ...]
    breaches: tuple[str, ...]
    caseLedgerHash: str
    runHash: str
    resultHash: str
    traceRoot: str
    scenarioPathPackageHash: str
    scenarioPathPackageReceiptId: str
    scenarioPathPackageSubjectHash: str
    pathSetHash: str
    pathHistoryInputHash: str
    pathAssumptionHash: str
    assumptionStepHash: str
    providerLaneLineageHash: str
    strategyContractHash: str
    sourceLineageKeysByFactor: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        for name in ("beforeState", "shocks", "issuedActions", "effectiveActions", "afterState"):
            object.__setattr__(self, name, tuple((key, float(value)) for key, value in getattr(self, name)))
        object.__setattr__(self, "actionCost", float(self.actionCost))
        object.__setattr__(self, "lawIds", tuple(self.lawIds))
        object.__setattr__(self, "lawEvidenceKinds", tuple(self.lawEvidenceKinds))
        object.__setattr__(self, "lawCertificateIds", tuple(self.lawCertificateIds))
        object.__setattr__(self, "breaches", tuple(self.breaches))
        object.__setattr__(self, "sourceLineageKeysByFactor", tuple(self.sourceLineageKeysByFactor))


@dataclass(frozen=True)
class ConditionalPlayLeaderTransition:
    """Leader change row between adjacent condition rows."""

    rowHash: str
    fromCaseId: str
    toCaseId: str
    fromLeaderStrategies: tuple[str, ...]
    toLeaderStrategies: tuple[str, ...]
    changed: bool
    fromAssumptionSetHash: str
    toAssumptionSetHash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "fromLeaderStrategies", tuple(self.fromLeaderStrategies))
        object.__setattr__(self, "toLeaderStrategies", tuple(self.toLeaderStrategies))


@dataclass(frozen=True)
class ConditionalPlayBlockerRow:
    """Original blocker row preserved for display without laundering."""

    rowHash: str
    scope: str
    caseId: str
    reason: str
    sourceBlockedReasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceBlockedReasons", tuple(self.sourceBlockedReasons))


@dataclass(frozen=True)
class ConditionalPlayControlRow:
    """One internal control knob with semantic plane and lineage boundaries."""

    rowHash: str
    controlId: str
    semanticPlane: str
    controlKind: str
    adjustmentMode: str
    adjustabilityStatus: str
    scope: str
    caseId: str
    strategyId: str
    step: int
    targetId: str
    sourceVariableId: str
    targetVariableId: str
    laneId: str
    cardId: str
    unit: str
    frequency: str
    timing: str
    transformId: str
    valueSummary: tuple[tuple[str, float], ...]
    sourceRefs: tuple[str, ...]
    semanticRefs: tuple[str, ...]
    expectedHashImpacts: tuple[str, ...]
    forbiddenHashImpacts: tuple[str, ...]
    providerLaneLineageHash: str
    providerLineageStatus: tuple[str, ...]
    providerObservationBatchReceiptIds: tuple[str, ...]
    providerObservationBatchSourceReceiptIds: tuple[str, ...]
    priceSourceLegReceiptIds: tuple[str, ...]
    derivedReturnReceiptIds: tuple[str, ...]
    rawSourceRefs: tuple[str, ...]
    revisedHistoryRefs: tuple[str, ...]
    explicitAssumptionId: str
    claim: str
    falsifier: str
    pathHistoryInputHash: str
    pathAssumptionHash: str
    pathAssumptionStepHash: str
    assumptionSetHash: str
    caseLedgerHash: str
    strategyContractHash: str
    parameterHash: str
    blockedReasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.semanticPlane not in CONDITIONAL_PLAY_CONTROL_SURFACE_PLANES:
            raise ScenarioCompositionError(f"unknown control semantic plane: {self.semanticPlane}")
        object.__setattr__(
            self,
            "valueSummary",
            tuple((key, float(value)) for key, value in self.valueSummary),
        )
        for name in (
            "sourceRefs",
            "semanticRefs",
            "expectedHashImpacts",
            "forbiddenHashImpacts",
            "providerLineageStatus",
            "providerObservationBatchReceiptIds",
            "providerObservationBatchSourceReceiptIds",
            "priceSourceLegReceiptIds",
            "derivedReturnReceiptIds",
            "rawSourceRefs",
            "revisedHistoryRefs",
            "blockedReasons",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))


@dataclass(frozen=True)
class ConditionalPlayControlSurface:
    """Internal control deck for GUI knobs without creating a public API."""

    surfaceHash: str
    schemaVersion: str
    kind: str
    lineageMode: str
    entityId: str
    scenarioCount: int
    strategyCount: int
    horizon: int
    frequency: str
    controlCount: int
    controlPanelHash: str
    caseLedgerHashes: tuple[str, ...]
    providerLaneLineageHashes: tuple[str, ...]
    pathHistoryInputHashes: tuple[str, ...]
    pathAssumptionHashes: tuple[str, ...]
    assumptionSetHashes: tuple[str, ...]
    rowHashes: tuple[str, ...]
    adjustableControlIds: tuple[str, ...]
    overlayControlIds: tuple[str, ...]
    lockedControlIds: tuple[str, ...]
    rows: tuple[ConditionalPlayControlRow, ...]
    blockedReasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "caseLedgerHashes", tuple(self.caseLedgerHashes))
        object.__setattr__(self, "providerLaneLineageHashes", tuple(self.providerLaneLineageHashes))
        object.__setattr__(self, "pathHistoryInputHashes", tuple(self.pathHistoryInputHashes))
        object.__setattr__(self, "pathAssumptionHashes", tuple(self.pathAssumptionHashes))
        object.__setattr__(self, "assumptionSetHashes", tuple(self.assumptionSetHashes))
        object.__setattr__(self, "rowHashes", tuple(self.rowHashes))
        object.__setattr__(self, "adjustableControlIds", tuple(self.adjustableControlIds))
        object.__setattr__(self, "overlayControlIds", tuple(self.overlayControlIds))
        object.__setattr__(self, "lockedControlIds", tuple(self.lockedControlIds))
        object.__setattr__(self, "rows", tuple(self.rows))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class ConditionalPlayReplayReport:
    """GUI ready projection of a conditional experiment without policy promotion."""

    playReplayHash: str
    schemaVersion: str
    kind: str
    lineageMode: str
    entityId: str
    decisionStatus: str
    recommendationStatus: str
    recommendationCeiling: str
    recommendation: str | None
    scenarioCount: int
    strategyCount: int
    cellCount: int
    horizon: int
    frequency: str
    traceRetention: str
    experimentHash: str
    comparisonHash: str
    simulationSpecHash: str
    resultSetHash: str
    strategySetHash: str
    caseLedgerHashes: tuple[str, ...]
    providerLaneLineageHashes: tuple[str, ...]
    conditionPanelHash: str
    strategyPanelHash: str
    cellPanelHash: str
    tracePanelHash: str
    leaderPanelHash: str
    fragileCasePanelHash: str
    blockerPanelHash: str
    controlPanelHash: str
    provenanceIndexHash: str
    controlSurfaceHash: str
    conditionRows: tuple[ConditionalPlayConditionRow, ...]
    strategyRows: tuple[ConditionalPlayStrategyRow, ...]
    cellRows: tuple[ConditionalPlayCellRow, ...]
    traceRows: tuple[ConditionalPlayTraceRow, ...]
    leaderTransitions: tuple[ConditionalPlayLeaderTransition, ...]
    fragilityRows: tuple[ConditionalAssumptionFragility, ...]
    blockerRows: tuple[ConditionalPlayBlockerRow, ...]
    controlSurface: ConditionalPlayControlSurface
    blockedReasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "caseLedgerHashes", tuple(self.caseLedgerHashes))
        object.__setattr__(self, "providerLaneLineageHashes", tuple(self.providerLaneLineageHashes))
        object.__setattr__(self, "conditionRows", tuple(self.conditionRows))
        object.__setattr__(self, "strategyRows", tuple(self.strategyRows))
        object.__setattr__(self, "cellRows", tuple(self.cellRows))
        object.__setattr__(self, "traceRows", tuple(self.traceRows))
        object.__setattr__(self, "leaderTransitions", tuple(self.leaderTransitions))
        object.__setattr__(self, "fragilityRows", tuple(self.fragilityRows))
        object.__setattr__(self, "blockerRows", tuple(self.blockerRows))
        if not isinstance(self.controlSurface, ConditionalPlayControlSurface):
            raise TypeError("controlSurface must be a ConditionalPlayControlSurface")
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class ConditionalPlayControlPatch:
    """One requested edit against a conditional play control row."""

    controlId: str
    baseSurfaceHash: str
    baseRowHash: str
    value: float
    patchRef: str
    reason: str = ""
    claim: str = ""
    falsifier: str = ""

    def __post_init__(self) -> None:
        if (
            not self.controlId
            or not self.baseSurfaceHash
            or not self.baseRowHash
            or not self.patchRef
            or self.value != self.value
            or self.value in {float("inf"), float("-inf")}
        ):
            raise ScenarioCompositionError("conditional play control patch contract is incomplete")
        object.__setattr__(self, "value", float(self.value))


@dataclass(frozen=True)
class ConditionalPlayControlImpactRow:
    """Observed hash boundary impact for one executed control patch."""

    rowHash: str
    controlId: str
    semanticPlane: str
    expectedHashImpacts: tuple[str, ...]
    forbiddenHashImpacts: tuple[str, ...]
    changedHashImpacts: tuple[str, ...]
    unchangedHashImpacts: tuple[str, ...]
    missingExpectedHashImpacts: tuple[str, ...]
    forbiddenHashViolations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "expectedHashImpacts", tuple(self.expectedHashImpacts))
        object.__setattr__(self, "forbiddenHashImpacts", tuple(self.forbiddenHashImpacts))
        object.__setattr__(self, "changedHashImpacts", tuple(self.changedHashImpacts))
        object.__setattr__(self, "unchangedHashImpacts", tuple(self.unchangedHashImpacts))
        object.__setattr__(self, "missingExpectedHashImpacts", tuple(self.missingExpectedHashImpacts))
        object.__setattr__(self, "forbiddenHashViolations", tuple(self.forbiddenHashViolations))


@dataclass(frozen=True)
class ConditionalPlayControlRebaseRow:
    """Mapping from a base control patch to its staged execution patch."""

    rowHash: str
    controlId: str
    semanticPlane: str
    originalPatchHash: str
    rebasedPatchHash: str
    originalSurfaceHash: str
    originalRowHash: str
    stageSurfaceHash: str
    stageRowHash: str
    rebaseStatus: str


@dataclass(frozen=True)
class ConditionalPlayControlExecutionReport:
    """Internal report for replaying a conditional play after control patches."""

    executionHash: str
    schemaVersion: str
    kind: str
    patchSetHash: str
    baseExperimentHash: str
    patchedExperimentHash: str
    basePlayReplayHash: str
    patchedPlayReplayHash: str
    baseControlSurfaceHash: str
    patchedControlSurfaceHash: str
    changedControlIds: tuple[str, ...]
    semanticPlane: str
    impactRows: tuple[ConditionalPlayControlImpactRow, ...]
    patchedExperiment: "ConditionalScenarioExperiment"
    blockedReasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "changedControlIds", tuple(self.changedControlIds))
        object.__setattr__(self, "impactRows", tuple(self.impactRows))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class ConditionalPlayStrategyDeltaRow:
    """Base to final strategy robustness delta inside one scenario deck."""

    rowHash: str
    strategyId: str
    baseStrategyContractHash: str
    finalStrategyContractHash: str
    baseSummaryHash: str
    finalSummaryHash: str
    baseStrategyCellsHash: str
    finalStrategyCellsHash: str
    objectiveIndex: int
    baseScenarioCount: int
    finalScenarioCount: int
    baseStrategyCount: int
    finalStrategyCount: int
    baseCellCount: int
    finalCellCount: int
    baseScoreMedian: float
    finalScoreMedian: float
    scoreMedianDelta: float
    baseRegretWorst: float
    finalRegretWorst: float
    regretWorstDelta: float
    baseLeaderFrequency: float
    finalLeaderFrequency: float
    leaderFrequencyDelta: float
    baseBreachCount: int
    finalBreachCount: int
    breachCountDelta: int
    changed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "baseScoreMedian", float(self.baseScoreMedian))
        object.__setattr__(self, "finalScoreMedian", float(self.finalScoreMedian))
        object.__setattr__(self, "scoreMedianDelta", float(self.scoreMedianDelta))
        object.__setattr__(self, "baseRegretWorst", float(self.baseRegretWorst))
        object.__setattr__(self, "finalRegretWorst", float(self.finalRegretWorst))
        object.__setattr__(self, "regretWorstDelta", float(self.regretWorstDelta))
        object.__setattr__(self, "baseLeaderFrequency", float(self.baseLeaderFrequency))
        object.__setattr__(self, "finalLeaderFrequency", float(self.finalLeaderFrequency))
        object.__setattr__(self, "leaderFrequencyDelta", float(self.leaderFrequencyDelta))


@dataclass(frozen=True)
class ConditionalPlayCaseLeaderDeltaRow:
    """Base to final case-level strategy leader and fragility delta."""

    rowHash: str
    caseId: str
    label: str
    baseCaseLedgerHash: str
    finalCaseLedgerHash: str
    baseFragilityHash: str
    finalFragilityHash: str
    baseCaseCellsHash: str
    finalCaseCellsHash: str
    baseResultHash: str
    finalResultHash: str
    baseRunHash: str
    finalRunHash: str
    basePathSetHash: str
    finalPathSetHash: str
    basePathAssumptionHash: str
    finalPathAssumptionHash: str
    baseScenarioPathPackageHash: str
    finalScenarioPathPackageHash: str
    baseLeaderStrategies: tuple[str, ...]
    finalLeaderStrategies: tuple[str, ...]
    baseRunnerUpStrategies: tuple[str, ...]
    finalRunnerUpStrategies: tuple[str, ...]
    baseBreachStrategies: tuple[str, ...]
    finalBreachStrategies: tuple[str, ...]
    leaderChanged: bool
    changed: bool
    baseLeaderMargin: float
    finalLeaderMargin: float
    leaderMarginDelta: float
    baseScoreSpread: float
    finalScoreSpread: float
    scoreSpreadDelta: float
    baseAssumptionSetHash: str
    finalAssumptionSetHash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "baseLeaderStrategies", tuple(self.baseLeaderStrategies))
        object.__setattr__(self, "finalLeaderStrategies", tuple(self.finalLeaderStrategies))
        object.__setattr__(self, "baseRunnerUpStrategies", tuple(self.baseRunnerUpStrategies))
        object.__setattr__(self, "finalRunnerUpStrategies", tuple(self.finalRunnerUpStrategies))
        object.__setattr__(self, "baseBreachStrategies", tuple(self.baseBreachStrategies))
        object.__setattr__(self, "finalBreachStrategies", tuple(self.finalBreachStrategies))
        object.__setattr__(self, "baseLeaderMargin", float(self.baseLeaderMargin))
        object.__setattr__(self, "finalLeaderMargin", float(self.finalLeaderMargin))
        object.__setattr__(self, "leaderMarginDelta", float(self.leaderMarginDelta))
        object.__setattr__(self, "baseScoreSpread", float(self.baseScoreSpread))
        object.__setattr__(self, "finalScoreSpread", float(self.finalScoreSpread))
        object.__setattr__(self, "scoreSpreadDelta", float(self.scoreSpreadDelta))


@dataclass(frozen=True)
class ConditionalPlayScenarioDeckReport:
    """Internal report for executing a multi-plane conditional scenario deck."""

    deckHash: str
    schemaVersion: str
    kind: str
    baseExperimentHash: str
    finalExperimentHash: str
    basePlayReplayHash: str
    finalPlayReplayHash: str
    baseControlSurfaceHash: str
    finalControlSurfaceHash: str
    baseSimulationSpecHash: str
    finalSimulationSpecHash: str
    baseResultSetHash: str
    finalResultSetHash: str
    baseStrategySetHash: str
    finalStrategySetHash: str
    baseSourceSealHash: str
    finalSourceSealHash: str
    stageChainHash: str
    baseLineageParentReceiptIds: tuple[str, ...]
    finalLineageParentReceiptIds: tuple[str, ...]
    changedControlIds: tuple[str, ...]
    semanticPlanes: tuple[str, ...]
    stageExecutionHashes: tuple[str, ...]
    rebaseRows: tuple[ConditionalPlayControlRebaseRow, ...]
    strategyDeltaRows: tuple[ConditionalPlayStrategyDeltaRow, ...]
    caseLeaderDeltaRows: tuple[ConditionalPlayCaseLeaderDeltaRow, ...]
    stageReports: tuple[ConditionalPlayControlExecutionReport, ...]
    finalExperiment: "ConditionalScenarioExperiment"
    blockedReasons: tuple[str, ...]
    warnings: tuple[str, ...]
    baseExperimentReceiptId: str = ""
    baseExperimentReceiptSubjectHash: str = ""
    finalExperimentReceiptId: str = ""
    finalExperimentReceiptSubjectHash: str = ""
    deckReceiptSubjectHash: str = ""
    deckReceiptId: str = ""
    deckReceiptKind: str = ""
    deckReceiptStatus: str = ""
    deckReceiptParentReceiptIds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "baseLineageParentReceiptIds", tuple(self.baseLineageParentReceiptIds))
        object.__setattr__(self, "finalLineageParentReceiptIds", tuple(self.finalLineageParentReceiptIds))
        object.__setattr__(self, "changedControlIds", tuple(self.changedControlIds))
        object.__setattr__(self, "semanticPlanes", tuple(self.semanticPlanes))
        object.__setattr__(self, "stageExecutionHashes", tuple(self.stageExecutionHashes))
        object.__setattr__(self, "rebaseRows", tuple(self.rebaseRows))
        object.__setattr__(self, "strategyDeltaRows", tuple(self.strategyDeltaRows))
        object.__setattr__(self, "caseLeaderDeltaRows", tuple(self.caseLeaderDeltaRows))
        object.__setattr__(self, "stageReports", tuple(self.stageReports))
        object.__setattr__(self, "blockedReasons", tuple(self.blockedReasons))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "deckReceiptParentReceiptIds", tuple(self.deckReceiptParentReceiptIds))


@dataclass(frozen=True)
class _ConditionalPlayPatchedBundle:
    inputs: OperatingWorldInputs
    cases: tuple[OperatingScenarioCase, ...]
    strategies: tuple[StrategySpec, ...]
    report: ConditionalPlayControlExecutionReport

    def __post_init__(self) -> None:
        object.__setattr__(self, "cases", tuple(self.cases))
        object.__setattr__(self, "strategies", tuple(self.strategies))


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _driverCoefficientAdmissionReceiptId(sourceRef: str) -> str:
    if not sourceRef.startswith(_DRIVER_COEFFICIENT_ADMISSION_REF_PREFIX):
        return ""
    receiptId = sourceRef[len(_DRIVER_COEFFICIENT_ADMISSION_REF_PREFIX) :]
    return receiptId if _validDigest(receiptId) else ""


def _filterRefs(refs: tuple[str, ...], prefixes: tuple[str, ...]) -> tuple[str, ...]:
    return _dedupe(tuple(ref for ref in refs if ref.startswith(prefixes)))


def _dedupeSorted(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))


def _refValues(
    refs: tuple[str, ...],
    prefix: str,
    *,
    requireDigest: bool = False,
) -> tuple[str, ...]:
    values = tuple(ref[len(prefix) :] for ref in refs if ref.startswith(prefix) and ref[len(prefix) :])
    if requireDigest:
        values = tuple(value for value in values if _validDigest(value))
    return _dedupeSorted(values)


def _rawProviderSourceRefs(pathSourceRefs: tuple[str, ...]) -> tuple[str, ...]:
    return _dedupeSorted(
        tuple(
            ref
            for ref in pathSourceRefs
            if not ref.startswith(_STRUCTURED_PROVIDER_LINEAGE_REF_PREFIXES)
            and not ref.startswith(_ASSUMPTION_REF_PREFIXES)
        )
    )


def _providerLineageStatuses(
    *,
    providerObservationBatchRefs: tuple[str, ...],
    providerObservationBatchReceiptIds: tuple[str, ...],
    priceSourceLegReceiptIds: tuple[str, ...],
    derivedReturnReceiptIds: tuple[str, ...],
    rawSourceRefs: tuple[str, ...],
    revisedHistoryRefs: tuple[str, ...],
    explicitAssumptionIds: tuple[str, ...],
) -> tuple[str, ...]:
    statuses: list[str] = []
    if providerObservationBatchReceiptIds and (priceSourceLegReceiptIds or derivedReturnReceiptIds):
        statuses.append("derivedProviderObservationBatch")
    elif providerObservationBatchReceiptIds:
        statuses.append("exactProviderObservationBatch")
    elif providerObservationBatchRefs:
        statuses.append("unverifiedProviderObservationRef")
    if revisedHistoryRefs:
        statuses.append("revisedHistory")
    if rawSourceRefs:
        statuses.append("rawSourceRefOnly")
    if explicitAssumptionIds:
        statuses.append("explicitAssumption")
    if not statuses:
        statuses.append("noProviderLineage")
    return tuple(statuses)


def _providerLineageLedger(
    *,
    pathSourceRefs: tuple[str, ...],
    providerObservationBatchRefs: tuple[str, ...],
    explicitAssumptionIds: tuple[str, ...],
) -> ScenarioProviderLineageLedger:
    providerObservationBatchReceiptIds = _refValues(
        pathSourceRefs,
        _PROVIDER_OBSERVATION_BATCH_REF_PREFIX,
        requireDigest=True,
    )
    providerObservationBatchIds = _refValues(pathSourceRefs, _PROVIDER_OBSERVATION_BATCH_ID_REF_PREFIX)
    providerObservationBatchSourceReceiptIds = _refValues(
        pathSourceRefs,
        _PROVIDER_SOURCE_RECEIPT_REF_PREFIX,
        requireDigest=True,
    )
    priceSourceLegReceiptIds = _refValues(
        pathSourceRefs,
        _PRICE_SOURCE_LEG_RECEIPT_REF_PREFIX,
        requireDigest=True,
    )
    derivedReturnReceiptIds = _refValues(
        pathSourceRefs,
        _DERIVED_RETURN_RECEIPT_REF_PREFIX,
        requireDigest=True,
    )
    adjustmentPolicyHashes = _refValues(pathSourceRefs, _ADJUSTMENT_POLICY_HASH_REF_PREFIX, requireDigest=True)
    normalizationContractHashes = _refValues(
        pathSourceRefs,
        _NORMALIZATION_CONTRACT_HASH_REF_PREFIX,
        requireDigest=True,
    )
    returnTransformRefs = _refValues(pathSourceRefs, _RETURN_TRANSFORM_REF_PREFIX)
    returnFormulaRefs = _refValues(pathSourceRefs, _RETURN_FORMULA_REF_PREFIX)
    factorMappingRefs = _refValues(pathSourceRefs, _FACTOR_MAPPING_REF_PREFIX)
    revisedHistoryRefs = _refValues(pathSourceRefs, _MACRO_REVISION_POLICY_REF_PREFIX)
    rawSourceRefs = _rawProviderSourceRefs(pathSourceRefs)
    returnTransformHash = canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_VERSION,
            "returnTransformRefs": returnTransformRefs,
            "returnFormulaRefs": returnFormulaRefs,
        }
    )
    providerLineageStatus = _providerLineageStatuses(
        providerObservationBatchRefs=providerObservationBatchRefs,
        providerObservationBatchReceiptIds=providerObservationBatchReceiptIds,
        priceSourceLegReceiptIds=priceSourceLegReceiptIds,
        derivedReturnReceiptIds=derivedReturnReceiptIds,
        rawSourceRefs=rawSourceRefs,
        revisedHistoryRefs=revisedHistoryRefs,
        explicitAssumptionIds=explicitAssumptionIds,
    )
    payload = {
        "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_VERSION,
        "providerLineageStatus": providerLineageStatus,
        "providerObservationBatchReceiptIds": providerObservationBatchReceiptIds,
        "providerObservationBatchIds": providerObservationBatchIds,
        "providerObservationBatchSourceReceiptIds": providerObservationBatchSourceReceiptIds,
        "priceSourceLegReceiptIds": priceSourceLegReceiptIds,
        "derivedReturnReceiptIds": derivedReturnReceiptIds,
        "adjustmentPolicyHashes": adjustmentPolicyHashes,
        "normalizationContractHashes": normalizationContractHashes,
        "returnTransformRefs": returnTransformRefs,
        "returnFormulaRefs": returnFormulaRefs,
        "returnTransformHash": returnTransformHash,
        "factorMappingRefs": factorMappingRefs,
        "rawSourceRefs": rawSourceRefs,
        "revisedHistoryRefs": revisedHistoryRefs,
        "explicitAssumptionIds": explicitAssumptionIds,
    }
    return ScenarioProviderLineageLedger(
        providerLaneLineageHash=canonicalPayloadHash(payload),
        providerLineageStatus=providerLineageStatus,
        providerObservationBatchReceiptIds=providerObservationBatchReceiptIds,
        providerObservationBatchIds=providerObservationBatchIds,
        providerObservationBatchSourceReceiptIds=providerObservationBatchSourceReceiptIds,
        priceSourceLegReceiptIds=priceSourceLegReceiptIds,
        derivedReturnReceiptIds=derivedReturnReceiptIds,
        adjustmentPolicyHashes=adjustmentPolicyHashes,
        normalizationContractHashes=normalizationContractHashes,
        returnTransformRefs=returnTransformRefs,
        returnTransformHash=returnTransformHash,
        factorMappingRefs=factorMappingRefs,
        rawSourceRefs=rawSourceRefs,
        revisedHistoryRefs=revisedHistoryRefs,
        explicitAssumptionIds=explicitAssumptionIds,
    )


def _explicitAssumptionIds(warnings: tuple[str, ...]) -> tuple[str, ...]:
    prefix = "explicitAssumption:"
    return _dedupe(tuple(warning[len(prefix) :] for warning in warnings if warning.startswith(prefix)))


def _scenarioPathRows(pathSet: DriverPathSet) -> tuple[dict, ...]:
    return tuple(
        {
            "pathId": path.pathId,
            "steps": tuple(dict(step) for step in path.steps),
            "weight": path.weight,
            "weightKind": path.weightKind,
            "refs": path.refs,
            "frequency": path.frequency,
            "stepSpan": path.stepSpan,
            "certificateId": path.certificateId,
            "validationStatus": path.validationStatus,
            "maxAdmittedStep": path.maxAdmittedStep,
            "parameterDraws": dict(path.parameterDraws),
            "parameterDrawReceipt": path.parameterDrawReceipt,
            "knowledgeAsOf": path.knowledgeAsOf,
            "historyStatus": path.historyStatus,
            "admissionContentHash": path.admissionContentHash,
            "admissionReceiptId": path.admissionReceiptId,
            "vintage": path.vintage,
        }
        for path in pathSet.paths
    )


def _scenarioPathCompositionContractHash(pathSet: DriverPathSet) -> str:
    audit = pathSet.audit
    return canonicalPayloadHash(
        {
            "schemaVersion": "scenario-path-package-composition-contract-v1",
            "kind": COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND if audit.assumptionHash else "scenarioPathPackage",
            "composer": "composeDriverPathSetWithAssumptions" if audit.assumptionHash else "buildDriverPathSet",
            "pathRegistryHash": audit.registryHash,
            "pathFactorContractHash": audit.factorContractHash,
            "basePathSetHash": audit.basePathSetHash,
            "basePathAdmissionReceiptId": audit.basePathAdmissionReceiptId,
            "pathOverlayHash": audit.overlayHash,
            "pathAssumptionHash": audit.assumptionHash,
            "frequency": audit.frequency,
            "stepSpan": audit.stepSpan,
            "horizon": audit.horizon,
            "pathCount": audit.pathCount,
            "seed": audit.seed,
        }
    )


def scenarioPathPackageParentReceiptIds(pathSet: DriverPathSet) -> tuple[str, ...]:
    """Return signed parents that a documented composed path package must cite.

    Args:
        pathSet: Composed driver path set whose base admission lineage should be cited.

    Returns:
        Ordered parent receipt identifiers required by the package receipt.

    Raises:
        No explicit errors are raised by this wrapper.

    Example:
        ``parents = scenarioPathPackageParentReceiptIds(pathSet)``
    """

    audit = pathSet.audit
    parents = []
    if audit.basePathAdmissionReceiptId:
        parents.append(audit.basePathAdmissionReceiptId)
    return _dedupe(tuple(parents))


def scenarioPathPackagePayload(pathSet: DriverPathSet) -> dict:
    """Build the replay package for a conditional composed path set.

    The payload documents explicit future assumptions and their observed base
    lineage. It is not a path admission payload and cannot open a policy
    recommendation.

    Args:
        pathSet: Driver path set produced by a scenario composition step.

    Returns:
        Canonical payload dictionary for content binding and artifact storage.

    Raises:
        TypeError: If the path set contains values that cannot be canonicalized.

    Example:
        ``payload = scenarioPathPackagePayload(pathSet)``
    """

    audit = pathSet.audit
    explicitAssumptionIds = _explicitAssumptionIds(audit.warnings)
    providerRefs = _filterRefs(audit.sourceRefs, _PROVIDER_OBSERVATION_REF_PREFIXES)
    packageKind = COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND if audit.assumptionHash else "scenarioPathPackage"
    return {
        "schemaVersion": SCENARIO_PATH_PACKAGE_VERSION,
        "kind": packageKind,
        "status": "documented",
        "validationStatus": audit.validationStatus,
        "historyStatus": audit.historyStatus,
        "decisionStatus": "conditionalOnly" if audit.assumptionHash else "documentedOnly",
        "composedPathAdmissionStatus": "notAdmitted" if audit.assumptionHash else "",
        "pathAdmissionTransferStatus": "notTransferred" if audit.assumptionHash else "notApplicable",
        "base": {
            "basePathSetHash": audit.basePathSetHash,
            "basePathAdmissionReceiptId": audit.basePathAdmissionReceiptId,
            "basePathAdmissionContentHash": audit.basePathAdmissionContentHash,
            "basePathAdmissionSubjectHash": audit.basePathAdmissionSubjectHash,
            "basePathValidationStatus": audit.basePathValidationStatus,
            "basePathMaxAdmittedStep": audit.basePathMaxAdmittedStep,
            "pathHistoryInputHash": audit.historyInputHash,
            "providerObservationBatchRefs": providerRefs,
        },
        "overlay": {
            "pathOverlayHash": audit.overlayHash,
            "pathAssumptionHash": audit.assumptionHash,
            "explicitAssumptionIds": explicitAssumptionIds,
            "explicitAssumptionStepHashes": audit.assumptionStepHashes,
            "affectedFactorIds": tuple(factor.variableId for factor in pathSet.factorSpecs),
        },
        "composition": {
            "compositionContractHash": _scenarioPathCompositionContractHash(pathSet),
            "composedPathInputHash": audit.inputHash,
            "composedPathSetHash": audit.pathSetHash,
            "composedPaths": _scenarioPathRows(pathSet),
        },
        "contract": {
            "pathRegistryHash": audit.registryHash,
            "pathFactorContractHash": audit.factorContractHash,
            "horizon": audit.horizon,
            "frequency": audit.frequency,
            "stepSpan": audit.stepSpan,
            "pathCount": audit.pathCount,
            "blockLength": audit.blockLength,
            "seed": audit.seed,
            "knowledgeAsOf": audit.knowledgeAsOf,
            "driverCardIds": audit.driverCardIds,
        },
        "parentReceiptIds": scenarioPathPackageParentReceiptIds(pathSet),
        "pathSourceRefs": audit.sourceRefs,
        "warnings": audit.warnings,
    }


def scenarioPathPackageArtifact(pathSet: DriverPathSet) -> bytes:
    """Return canonical bytes for a documented composed path package.

    Args:
        pathSet: Driver path set to serialize as a package artifact.

    Returns:
        Canonical JSON bytes whose SHA-256 digest is the package subject hash.

    Raises:
        TypeError: If the path set contains values that cannot be canonicalized.

    Example:
        ``artifact = scenarioPathPackageArtifact(pathSet)``
    """

    return canonicalPayloadBytes(scenarioPathPackagePayload(pathSet))


def scenarioPathPackageSubjectHash(pathSet: DriverPathSet) -> str:
    """Return the content hash signed by a composed path package receipt.

    Args:
        pathSet: Driver path set to bind into a documented package.

    Returns:
        SHA-256 digest of the canonical package artifact.

    Raises:
        TypeError: If the path set contains values that cannot be canonicalized.

    Example:
        ``subjectHash = scenarioPathPackageSubjectHash(pathSet)``
    """

    return canonicalPayloadHash(scenarioPathPackagePayload(pathSet))


def _scenarioPathPackageHash(pathSet: DriverPathSet) -> str:
    return scenarioPathPackageSubjectHash(pathSet)


def validateScenarioPathPackageReceipt(
    pathSet: DriverPathSet,
    receiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> "AdmissionReceipt":
    """Verify a documented composed path package receipt.

    This receipt proves package integrity only. It is not a path-set admission
    receipt and it does not make the scenario eligible for recommendation.

    Args:
        pathSet: Composed driver path set whose package receipt is being checked.
        receiptId: Signed receipt identifier to verify.
        admissionVerifier: Runtime verifier with trusted issuer keys and artifact root.

    Returns:
        Verified admission registry receipt for the documented package.

    Raises:
        ScenarioCompositionError: If kind, status, parent lineage, artifact bytes, or scenario semantics do not match.

    Example:
        ``receipt = validateScenarioPathPackageReceipt(pathSet, receiptId, verifier)``
    """

    if not _validDigest(receiptId):
        raise ScenarioCompositionError("scenario path package receipt identifier is invalid")
    if not pathSet.audit.assumptionHash:
        raise ScenarioCompositionError("scenario path package receipt requires explicit future assumptions")
    subjectHash = scenarioPathPackageSubjectHash(pathSet)
    try:
        from dartlab.simulate.admissionRegistry import artifactPath

        receipt = admissionVerifier.verify(
            receiptId,
            expectedSubjectHash=subjectHash,
            expectedKind=COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND,
        )
        parentReceipts = tuple(admissionVerifier.verify(parentId) for parentId in receipt.parentReceiptIds)
        artifactBytes = artifactPath(admissionVerifier.artifactRoot, subjectHash).read_bytes()
    except (OSError, RuntimeError, ValueError) as error:
        raise ScenarioCompositionError(f"scenario path package receipt verification failed: {error}") from error
    if artifactBytes != scenarioPathPackageArtifact(pathSet):
        raise ScenarioCompositionError("scenario path package artifact content mismatch")
    if (
        receipt.status != "documented"
        or receipt.artifactHash != subjectHash
        or receipt.ruleId != COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_ID
        or receipt.ruleVersion != COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_VERSION
        or receipt.ruleHash != COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_HASH
        or receipt.revisionPolicy != "explicitAssumption"
        or receipt.coverage != "synthetic"
        or receipt.frequency != pathSet.audit.frequency
        or receipt.stepSpan != pathSet.audit.stepSpan
        or receipt.maxAdmittedStep != 0
    ):
        raise ScenarioCompositionError("scenario path package receipt contract mismatch")
    expectedParents = scenarioPathPackageParentReceiptIds(pathSet)
    if any(parentId not in receipt.parentReceiptIds for parentId in expectedParents):
        raise ScenarioCompositionError("scenario path package receipt missing base admission parent")
    if any(parent.kind in {"policyEvaluation", "policyEpisodeBatch"} for parent in parentReceipts):
        raise ScenarioCompositionError("scenario path package cannot depend on policy evaluation receipts")
    baseReceiptId = pathSet.audit.basePathAdmissionReceiptId
    if baseReceiptId:
        baseParents = tuple(parent for parent in parentReceipts if parent.receiptId == baseReceiptId)
        if len(baseParents) != 1:
            raise ScenarioCompositionError("scenario path package base admission parent mismatch")
        baseParent = baseParents[0]
        if (
            baseParent.kind != "pathSet"
            or baseParent.status != "admitted"
            or baseParent.subjectHash != pathSet.audit.basePathAdmissionSubjectHash
            or baseParent.artifactHash != pathSet.audit.basePathAdmissionSubjectHash
            or baseParent.revisionPolicy != "asKnown"
            or baseParent.coverage != "asOfExact"
        ):
            raise ScenarioCompositionError("scenario path package base admission parent is invalid")
    return receipt


def _bindOperatingPathAdmission(
    case: OperatingScenarioCase, paths: tuple[ScenarioPath, ...]
) -> tuple[ScenarioPath, ...]:
    if not case.operatingPathAdmissionReceiptId:
        return paths
    if case.admissionVerifier is None:
        raise ScenarioCompositionError("operating path admission receipt needs a verifier")
    if case.pathSet.audit.assumptionHash:
        raise ScenarioCompositionError("explicit overlay paths cannot bind official operating path admission")
    if not _validDigest(case.operatingPathCertificateId):
        raise ScenarioCompositionError("operating path admission needs a path certificate id")
    if not paths:
        raise ScenarioCompositionError("operating path admission needs executable paths")
    try:
        receipt = case.admissionVerifier.verify(
            case.operatingPathAdmissionReceiptId,
            expectedKind="pathSet",
        )
        parentReceipts = tuple(case.admissionVerifier.verify(parentId) for parentId in receipt.parentReceiptIds)
        candidate = tuple(
            replace(
                path,
                validationStatus="admitted",
                maxAdmittedStep=receipt.maxAdmittedStep,
                certificateId=case.operatingPathCertificateId,
            )
            for path in paths
        )
        candidate = bindAdmittedPathContent(candidate)
        subjectHash = pathSetAdmissionSubjectHash(candidate)
        receipt = case.admissionVerifier.verify(
            case.operatingPathAdmissionReceiptId,
            expectedSubjectHash=subjectHash,
            expectedKind="pathSet",
        )
        admitted = bindPathAdmissionReceipt(candidate, receipt.receiptId)
    except (RuntimeError, ValueError) as error:
        raise ScenarioCompositionError(f"operating path admission verification failed: {error}") from error
    horizon = len(paths[0].steps)
    if (
        receipt.status != "admitted"
        or receipt.artifactHash != subjectHash
        or receipt.revisionPolicy != "asKnown"
        or receipt.coverage != "asOfExact"
        or receipt.maxAdmittedStep < horizon
        or receipt.frequency != paths[0].frequency
        or receipt.stepSpan != paths[0].stepSpan
        or any(len(path.steps) != horizon for path in paths)
    ):
        raise ScenarioCompositionError("operating path admission receipt contract mismatch")
    forbiddenKinds = {
        COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND,
        CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND,
        CONDITIONAL_STRATEGY_EVALUATION_KIND,
        "policyEvaluation",
        "policyEpisodeBatch",
    }
    if any(parent.kind in forbiddenKinds for parent in parentReceipts):
        raise ScenarioCompositionError("operating path admission cannot depend on conditional or policy receipts")
    return admitted


def _verifyScenarioPathPackageReceipt(case: OperatingScenarioCase) -> "AdmissionReceipt | None":
    if not case.scenarioPathPackageReceiptId:
        return None
    if case.admissionVerifier is None:
        raise ScenarioCompositionError("scenario path package receipt needs an admission verifier")
    return validateScenarioPathPackageReceipt(
        case.pathSet,
        case.scenarioPathPackageReceiptId,
        case.admissionVerifier,
    )


def _scenarioPathPackageRefs(pathSet: DriverPathSet, receiptId: str) -> tuple[str, ...]:
    subjectHash = scenarioPathPackageSubjectHash(pathSet)
    refs = [
        f"composedPathSubject:{subjectHash}",
        f"composedPathSet:{pathSet.audit.pathSetHash}",
        f"compositionContract:{_scenarioPathCompositionContractHash(pathSet)}",
    ]
    if receiptId:
        refs.append(f"composedPathPackage:{receiptId}")
    if pathSet.audit.basePathAdmissionReceiptId:
        refs.append(f"basePathAdmission:{pathSet.audit.basePathAdmissionReceiptId}")
    if pathSet.audit.overlayHash:
        refs.append(f"explicitOverlay:{pathSet.audit.overlayHash}")
    refs.extend(f"explicitAssumptionStep:{stepHash}" for stepHash in pathSet.audit.assumptionStepHashes)
    return _dedupe(tuple(refs))


def _futureAdjustmentStatus(pathSet: DriverPathSet) -> str:
    return "explicitAssumption" if pathSet.audit.assumptionHash else ""


def _basePathAdmissionReceiptId(pathSet: DriverPathSet) -> str:
    if pathSet.audit.basePathAdmissionReceiptId:
        return pathSet.audit.basePathAdmissionReceiptId
    if pathSet.audit.assumptionHash or not pathSet.paths:
        return ""
    receiptIds = {path.admissionReceiptId for path in pathSet.paths}
    validationStatuses = {path.validationStatus for path in pathSet.paths}
    if validationStatuses == {"admitted"} and len(receiptIds) == 1:
        receiptId = next(iter(receiptIds))
        return receiptId if _validDigest(receiptId) else ""
    return ""


def _basePathAdmissionScope(pathSet: DriverPathSet) -> str:
    if not pathSet.audit.basePathSetHash:
        return ""
    if pathSet.audit.assumptionHash:
        return "historyOnly"
    return "composedPath"


def _composedPathAdmissionStatus(result: SimulationRun) -> str:
    return "admitted" if result.pathAdmissionReceiptId else "notAdmitted"


def _pathAdmissionTransferStatus(pathSet: DriverPathSet, result: SimulationRun) -> str:
    if pathSet.audit.assumptionHash:
        return "notTransferred"
    if result.pathAdmissionReceiptId:
        return "composedPathAdmitted"
    return "notApplicable"


def _pathAdmissionTransferBlockedBy(pathSet: DriverPathSet, result: SimulationRun) -> tuple[str, ...]:
    reasons: list[str] = []
    if pathSet.audit.assumptionHash:
        reasons.append("explicitFutureAdjustmentPresent")
    if pathSet.audit.assumptionHash and pathSet.audit.basePathAdmissionReceiptId:
        reasons.append("basePathAdmittedButOverlayConditional")
    if pathSet.audit.assumptionHash and pathSet.audit.basePathSetHash:
        reasons.append("pathAdmissionNotTransferredFromObservedHistory")
    if not result.pathAdmissionReceiptId:
        reasons.append("composedPathAdmissionNotGranted")
    return _dedupe(tuple(reasons))


def _policyEvaluationEligibility(result: SimulationRun) -> str:
    return "eligible" if result.policyEvaluationCertificateId else "blocked"


def _pathAdmissionContentHash(paths: tuple[ScenarioPath, ...], result: SimulationRun) -> str:
    if not result.pathAdmissionReceiptId:
        return ""
    try:
        return pathSetAdmissionSubjectHash(paths)
    except (RuntimeError, ValueError) as error:
        raise ScenarioCompositionError(f"path admission content hash failed: {error}") from error


def _pathCertificateIds(paths: tuple[ScenarioPath, ...], result: SimulationRun) -> tuple[str, ...]:
    if not result.pathAdmissionReceiptId:
        return ()
    return _dedupe(tuple(path.certificateId for path in paths))


def _policyCertificateReceiptId(case: OperatingScenarioCase, result: SimulationRun) -> str:
    if not result.policyEvaluationCertificateId or case.policyAdmissionEvidence is None:
        return ""
    return case.policyAdmissionEvidence.certificate.certificateReceiptId


def _policyCertificateStatus(case: OperatingScenarioCase, result: SimulationRun) -> str:
    if not result.policyEvaluationCertificateId or case.policyAdmissionEvidence is None:
        return ""
    return case.policyAdmissionEvidence.certificate.status


def _policyEvaluationParentReceiptIds(case: OperatingScenarioCase, result: SimulationRun) -> tuple[str, ...]:
    if not result.policyEvaluationCertificateId or case.policyAdmissionEvidence is None:
        return ()
    return (case.policyAdmissionEvidence.certificate.batchReceiptId,)


def _recommendationSource(case: OperatingScenarioCase, result: SimulationRun) -> str:
    if result.recommendation is None:
        return ""
    if not result.policyEvaluationCertificateId or case.policyAdmissionEvidence is None:
        raise ScenarioCompositionError("scenario recommendation needs policy admission evidence")
    return "policyAdmitted"


def _recommendationEvidenceKind(case: OperatingScenarioCase, result: SimulationRun) -> str:
    return "policyEvaluationCertificate" if _recommendationSource(case, result) else ""


def _recommendationEvidenceReceiptId(case: OperatingScenarioCase, result: SimulationRun) -> str:
    if result.recommendation is None:
        return ""
    return _policyCertificateReceiptId(case, result)


def _conditionalReceiptIdsExcludedFromPolicy(case: OperatingScenarioCase) -> tuple[str, ...]:
    receipts = []
    if case.scenarioPathPackageReceiptId:
        receipts.append(case.scenarioPathPackageReceiptId)
    return _dedupe(tuple(receipts))


def _exposureContractRows(exposures: tuple[OperatingTransmissionExposure, ...]) -> tuple[dict, ...]:
    return tuple(
        {
            "exposureId": item.exposureId,
            "sourceVariableId": item.sourceVariableId,
            "targetShock": item.targetShock,
            "coefficient": float(item.coefficient),
            "coefficientUnit": item.coefficientUnit,
            "evidenceKind": item.evidenceKind,
            "sourceRef": item.sourceRef,
            "modifierVariableId": item.modifierVariableId,
            "modifierUnit": item.modifierUnit,
            "lagSteps": item.lagSteps,
            "responseKernel": tuple(float(value) for value in item.responseKernel),
            "aggregationGroup": item.aggregationGroup,
            "sourceFrequency": item.sourceFrequency,
            "sourceTiming": item.sourceTiming,
            "sourceTransformId": item.sourceTransformId,
            "sourceFactorContractHash": item.sourceFactorContractHash,
        }
        for item in exposures
    )


def scenarioCoefficientExposureContractHash(exposures: tuple[OperatingTransmissionExposure, ...]) -> str:
    """Hash the scalar exposure contracts covered by one coefficient binding.

    Args:
        exposures: Ordered measured association exposures produced by one admitted coefficient vector.

    Returns:
        Canonical contract hash binding exposure coefficients, source refs, kernels, and factor contracts.

    Raises:
        ScenarioCompositionError: If no exposure is supplied.

    Example:
        ``contractHash = scenarioCoefficientExposureContractHash(exposures)``
    """

    exposureTuple = tuple(exposures)
    if not exposureTuple:
        raise ScenarioCompositionError("coefficient exposure contract needs exposures")
    return canonicalPayloadHash(
        {
            "schemaVersion": SCENARIO_EXPOSURE_CONTRACT_VERSION,
            "exposures": _exposureContractRows(exposureTuple),
        }
    )


def _coefficientBindingPayload(binding: ScenarioCoefficientBinding) -> dict:
    return {
        "schemaVersion": SCENARIO_COEFFICIENT_BINDING_VERSION,
        "admissionReceiptId": binding.admissionReceiptId,
        "subjectHash": binding.subjectHash,
        "ruleHash": binding.ruleHash,
        "ruleId": binding.ruleId,
        "ruleVersion": binding.ruleVersion,
        "parentReceiptIds": binding.parentReceiptIds,
        "sourceVariableIds": binding.sourceVariableIds,
        "targetShock": binding.targetShock,
        "frequency": binding.frequency,
        "stepSpan": binding.stepSpan,
        "maxAdmittedStep": binding.maxAdmittedStep,
        "coefficientVectorHash": binding.coefficientVectorHash,
        "featureSpecHash": binding.featureSpecHash,
        "designFrameHash": binding.designFrameHash,
        "exposureContractHash": binding.exposureContractHash,
        "calibrationId": binding.calibrationId,
        "reportId": binding.reportId,
        "fitDesignFrameHash": binding.fitDesignFrameHash,
        "oosDesignFrameHash": binding.oosDesignFrameHash,
        "sourceRefs": binding.sourceRefs,
    }


def scenarioCoefficientBindingHash(binding: ScenarioCoefficientBinding) -> str:
    """Hash a coefficient binding summary carried by a scenario case.

    Args:
        binding: Thin admitted coefficient vector binding attached to a scenario case.

    Returns:
        Canonical hash for ledger refs and loop hash binding.

    Raises:
        No explicit errors are raised by this wrapper.

    Example:
        ``bindingHash = scenarioCoefficientBindingHash(binding)``
    """

    return canonicalPayloadHash(_coefficientBindingPayload(binding))


def buildScenarioCoefficientBindingFromVerifiedMultivariableAdmission(
    receipt: MultivariableDriverCoefficientCalibrationReceipt,
    report: MultivariableDriverCoefficientOosReport,
    admissionReceipt: VerifiedDriverCoefficientAdmission,
    exposures: tuple[OperatingTransmissionExposure, ...],
) -> ScenarioCoefficientBinding:
    """Create a coefficient-only ledger binding for a scenario case.

    This does not admit scenario paths, initial state, policy evaluation, or
    recommendation.

    Args:
        receipt: Fitted multivariable coefficient vector receipt.
        report: OOS report that became the signed driver coefficient artifact.
        admissionReceipt: Verified admission wrapper returned by driver calibration.
        exposures: Scalar measured association exposures generated from the verified coefficient vector.

    Returns:
        ``ScenarioCoefficientBinding`` that can be attached to an ``OperatingScenarioCase``.

    Raises:
        ScenarioCompositionError: If receipt, report, admission, or generated exposures drift.

    Example:
        ``binding = buildScenarioCoefficientBindingFromVerifiedMultivariableAdmission(receipt, report, verified, exposures)``
    """

    if not isinstance(admissionReceipt, VerifiedDriverCoefficientAdmission):
        raise ScenarioCompositionError("coefficient binding requires verified driver coefficient admission")
    exposureTuple = tuple(exposures)
    if not exposureTuple:
        raise ScenarioCompositionError("coefficient binding requires generated exposures")
    if (
        report.status != "oosEligible"
        or report.receiptHash != receipt.receiptHash
        or report.receiptId != receipt.receiptId
        or report.calibrationId != receipt.calibrationId
        or report.sourceVariableIds != receipt.sourceVariableIds
        or report.targetVariableId != receipt.targetVariableId
        or report.targetShock != receipt.targetShock
        or report.targetUnit != receipt.targetUnit
        or report.coefficientTerms != receipt.coefficientTerms
        or report.featureSpecHash != receipt.featureSpecHash
        or report.designFrameHash != receipt.designFrameHash
        or report.coefficientVectorHash != receipt.coefficientVectorHash
        or report.fitDesignFrameBinding != receipt.fitDesignFrameBinding
    ):
        raise ScenarioCompositionError("coefficient vector report does not match receipt")
    subjectHash = multivariableDriverCoefficientAdmissionSubjectHash(report)
    parentReceiptIds = multivariableDriverCoefficientAdmissionParentReceiptIds(report)
    signedReceipt = admissionReceipt.receipt
    if (
        signedReceipt.kind != "driverCoefficient"
        or signedReceipt.status != "admitted"
        or signedReceipt.receiptId != _driverCoefficientAdmissionReceiptId(exposureTuple[0].sourceRef)
        or signedReceipt.subjectHash != subjectHash
        or signedReceipt.artifactHash != subjectHash
        or (signedReceipt.ruleId, signedReceipt.ruleVersion, signedReceipt.ruleHash)
        != (
            MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
            MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
            MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
        )
        or signedReceipt.parentReceiptIds != parentReceiptIds
        or signedReceipt.frequency != report.frequency
        or signedReceipt.stepSpan != report.stepSpan
        or signedReceipt.maxAdmittedStep != report.maxAdmittedStep
        or signedReceipt.revisionPolicy != "asKnown"
        or signedReceipt.coverage != "asOfExact"
    ):
        raise ScenarioCompositionError("coefficient admission receipt does not match report")
    expectedSourceParents = _dedupe((*report.fitSourceParentReceiptIds, *report.oosSourceParentReceiptIds))
    expectedLabelParents = _dedupe((*report.fitLabelParentReceiptIds, *report.oosLabelParentReceiptIds))
    if (
        admissionReceipt.sourceParentReceiptIds != expectedSourceParents
        or admissionReceipt.labelParentReceiptIds != expectedLabelParents
    ):
        raise ScenarioCompositionError("coefficient admission parent lineage does not match report")
    if tuple(exposure.sourceVariableId for exposure in exposureTuple) != receipt.sourceVariableIds:
        raise ScenarioCompositionError("coefficient exposure order does not match vector receipt")
    expectedSourceRef = f"driverCoefficientAdmission:{signedReceipt.receiptId}"
    if any(exposure.sourceRef != expectedSourceRef for exposure in exposureTuple):
        raise ScenarioCompositionError("coefficient exposure admission ref does not match verified receipt")
    for term, exposure in zip(receipt.coefficientTerms, exposureTuple, strict=True):
        if (
            exposure.evidenceKind != "measuredAssociation"
            or exposure.sourceVariableId != term.variableId
            or exposure.targetShock != receipt.targetShock
            or abs(float(exposure.coefficient) - float(term.coefficient)) > 1e-12
            or exposure.coefficientUnit != term.coefficientUnit
            or exposure.lagSteps != receipt.lagSteps
            or tuple(float(value) for value in exposure.responseKernel)
            != tuple(float(value) for value in receipt.responseKernel)
            or exposure.sourceFrequency != term.sourceFrequency
            or exposure.sourceTiming != term.sourceTiming
            or exposure.sourceTransformId != term.sourceTransformId
            or exposure.sourceFactorContractHash != term.sourceFactorContractHash
        ):
            raise ScenarioCompositionError("coefficient exposure does not match vector receipt")
    sourceRefs = _dedupe(
        (
            *report.sourceRefs,
            f"coefficientTrace:{receipt.coefficientTraceHash}",
            f"predictionTrace:{report.predictionTraceHash}",
            f"fitDesignFrame:{receipt.fitDesignFrameBinding.frameHash}",
            f"oosDesignFrame:{report.oosDesignFrameBinding.frameHash}",
        )
    )
    return ScenarioCoefficientBinding(
        admissionReceiptId=signedReceipt.receiptId,
        subjectHash=subjectHash,
        ruleHash=signedReceipt.ruleHash,
        ruleId=signedReceipt.ruleId,
        ruleVersion=signedReceipt.ruleVersion,
        parentReceiptIds=parentReceiptIds,
        sourceVariableIds=receipt.sourceVariableIds,
        targetShock=receipt.targetShock,
        frequency=report.frequency,
        stepSpan=report.stepSpan,
        maxAdmittedStep=report.maxAdmittedStep,
        coefficientVectorHash=receipt.coefficientVectorHash,
        featureSpecHash=receipt.featureSpecHash,
        designFrameHash=receipt.designFrameHash,
        exposureContractHash=scenarioCoefficientExposureContractHash(exposureTuple),
        calibrationId=receipt.calibrationId,
        reportId=report.reportId,
        fitDesignFrameHash=receipt.fitDesignFrameBinding.frameHash,
        oosDesignFrameHash=report.oosDesignFrameBinding.frameHash,
        sourceRefs=sourceRefs,
    )


def _coefficientBindingRefs(bindings: tuple[ScenarioCoefficientBinding, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    for binding in bindings:
        refs.extend(
            (
                f"driverCoefficientAdmission:{binding.admissionReceiptId}",
                f"driverCoefficientSubject:{binding.subjectHash}",
                f"driverCoefficientRule:{binding.ruleHash}",
                f"driverCoefficientRuleId:{binding.ruleId}",
                f"driverCoefficientRuleVersion:{binding.ruleVersion}",
                f"coefficientBinding:{scenarioCoefficientBindingHash(binding)}",
                f"coefficientVector:{binding.coefficientVectorHash}",
                f"coefficientFeatureSpec:{binding.featureSpecHash}",
                f"coefficientDesignFrame:{binding.designFrameHash}",
                f"coefficientExposureContract:{binding.exposureContractHash}",
            )
        )
        if binding.calibrationId:
            refs.append(f"coefficientCalibration:{binding.calibrationId}")
        if binding.reportId:
            refs.append(f"coefficientReport:{binding.reportId}")
        if binding.fitDesignFrameHash:
            refs.append(f"coefficientFitDesignFrame:{binding.fitDesignFrameHash}")
        if binding.oosDesignFrameHash:
            refs.append(f"coefficientOosDesignFrame:{binding.oosDesignFrameHash}")
        refs.extend(f"coefficientParentReceipt:{receiptId}" for receiptId in binding.parentReceiptIds)
        refs.extend(binding.sourceRefs)
    return _dedupe(tuple(refs))


def _exposureLedgerRows(exposures: tuple[OperatingTransmissionExposure, ...]) -> tuple[ScenarioExposureLedger, ...]:
    return tuple(
        ScenarioExposureLedger(
            exposureId=item.exposureId,
            sourceVariableId=item.sourceVariableId,
            targetShock=item.targetShock,
            coefficient=float(item.coefficient),
            coefficientUnit=item.coefficientUnit,
            evidenceKind=item.evidenceKind,
            sourceRef=item.sourceRef,
            admissionReceiptId=_driverCoefficientAdmissionReceiptId(item.sourceRef),
            modifierVariableId=item.modifierVariableId,
            modifierUnit=item.modifierUnit,
            lagSteps=item.lagSteps,
            responseKernel=item.responseKernel,
            aggregationGroup=item.aggregationGroup,
            sourceFrequency=item.sourceFrequency,
            sourceTiming=item.sourceTiming,
            sourceTransformId=item.sourceTransformId,
            sourceFactorContractHash=item.sourceFactorContractHash,
        )
        for item in exposures
    )


def _driverRegistryLedger(audit) -> ScenarioDriverRegistryLedger | None:
    if audit is None:
        return None
    return ScenarioDriverRegistryLedger(
        registryId=audit.registryId,
        registryHash=audit.registryHash,
        laneIds=audit.laneIds,
        cardIds=audit.cardIds,
        factorIds=audit.factorIds,
        commonObservationCount=audit.commonObservationCount,
        sourceObservationCounts=audit.sourceObservationCounts,
        eventStart=audit.eventStart,
        eventEnd=audit.eventEnd,
        sourceRefs=audit.sourceRefs,
        semanticRefs=audit.semanticRefs,
        warnings=audit.warnings,
        pathSetHash=audit.pathSetHash,
        pathSetInputHash=audit.pathSetInputHash,
        validationStatus=audit.validationStatus,
        historyStatus=audit.historyStatus,
    )


def _driverRegistryRefs(audit) -> tuple[str, ...]:
    if audit is None:
        return ()
    return _dedupe(
        (
            f"driverRegistry:{audit.registryHash}",
            f"driverRegistryId:{audit.registryId}",
            *(f"driverRegistryLane:{laneId}" for laneId in audit.laneIds),
            *(f"driverRegistryCard:{cardId}" for cardId in audit.cardIds),
            *(f"driverRegistryFactor:{factorId}" for factorId in audit.factorIds),
            *audit.sourceRefs,
            *audit.semanticRefs,
        )
    )


def _validateCoefficientBindingShape(binding: ScenarioCoefficientBinding) -> None:
    optionalDigests = (binding.fitDesignFrameHash, binding.oosDesignFrameHash)
    if (
        not _validDigest(binding.admissionReceiptId)
        or not _validDigest(binding.subjectHash)
        or not _validDigest(binding.ruleHash)
        or not binding.ruleId
        or not binding.ruleVersion
        or not binding.parentReceiptIds
        or any(not _validDigest(receiptId) for receiptId in binding.parentReceiptIds)
        or not binding.sourceVariableIds
        or len(set(binding.sourceVariableIds)) != len(binding.sourceVariableIds)
        or not binding.targetShock
        or not binding.frequency
        or binding.stepSpan < 1
        or binding.maxAdmittedStep < 1
        or not _validDigest(binding.coefficientVectorHash)
        or not _validDigest(binding.featureSpecHash)
        or not _validDigest(binding.designFrameHash)
        or not _validDigest(binding.exposureContractHash)
        or any(value and not _validDigest(value) for value in optionalDigests)
    ):
        raise ScenarioCompositionError("coefficient binding contract is incomplete")


def _validateCoefficientReceipt(
    case: OperatingScenarioCase,
    binding: ScenarioCoefficientBinding,
) -> None:
    if case.admissionVerifier is None:
        return
    try:
        receipt = case.admissionVerifier.verify(
            binding.admissionReceiptId,
            expectedSubjectHash=binding.subjectHash,
            expectedKind="driverCoefficient",
        )
    except RuntimeError as error:
        raise ScenarioCompositionError(f"coefficient admission verification failed: {error}") from error
    if (
        receipt.status != "admitted"
        or receipt.artifactHash != binding.subjectHash
        or receipt.ruleId != binding.ruleId
        or receipt.ruleVersion != binding.ruleVersion
        or receipt.ruleHash != binding.ruleHash
        or receipt.parentReceiptIds != binding.parentReceiptIds
        or receipt.frequency != binding.frequency
        or receipt.stepSpan != binding.stepSpan
        or receipt.maxAdmittedStep != binding.maxAdmittedStep
    ):
        raise ScenarioCompositionError("coefficient admission receipt does not match binding")


def _validateCoefficientBindings(case: OperatingScenarioCase) -> None:
    bindings = tuple(case.coefficientBindings)
    bindingIds = [binding.admissionReceiptId for binding in bindings]
    if len(set(bindingIds)) != len(bindingIds):
        raise ScenarioCompositionError("coefficient bindings need unique admission receipts")
    bindingById = {binding.admissionReceiptId: binding for binding in bindings}
    measuredIds = []
    for exposure in case.exposures:
        receiptId = _driverCoefficientAdmissionReceiptId(exposure.sourceRef)
        if receiptId and exposure.evidenceKind != "measuredAssociation":
            raise ScenarioCompositionError("driver coefficient admission refs are measured associations")
        if exposure.evidenceKind == "measuredAssociation":
            if not receiptId:
                raise ScenarioCompositionError("measured association exposure needs coefficient admission ref")
            measuredIds.append(receiptId)
            if receiptId not in bindingById:
                raise ScenarioCompositionError("measured association exposure needs coefficient binding")
    factorIds = {factor.variableId for factor in case.pathSet.factorSpecs}
    for binding in bindings:
        _validateCoefficientBindingShape(binding)
        matched = tuple(
            exposure
            for exposure in case.exposures
            if _driverCoefficientAdmissionReceiptId(exposure.sourceRef) == binding.admissionReceiptId
        )
        if not matched:
            raise ScenarioCompositionError("coefficient binding has no matching measured exposure")
        if tuple(exposure.sourceVariableId for exposure in matched) != binding.sourceVariableIds:
            raise ScenarioCompositionError("coefficient binding source variable mismatch")
        if any(exposure.sourceVariableId not in factorIds for exposure in matched):
            raise ScenarioCompositionError("coefficient binding source variable is missing from scenario factors")
        if any(exposure.targetShock != binding.targetShock for exposure in matched):
            raise ScenarioCompositionError("coefficient binding target shock mismatch")
        if binding.frequency != case.pathSet.audit.frequency or binding.stepSpan != case.pathSet.audit.stepSpan:
            raise ScenarioCompositionError("coefficient binding timing mismatch")
        if binding.maxAdmittedStep < case.pathSet.audit.horizon:
            raise ScenarioCompositionError("coefficient binding admitted horizon is too short")
        if scenarioCoefficientExposureContractHash(matched) != binding.exposureContractHash:
            raise ScenarioCompositionError("coefficient binding exposure contract mismatch")
        _validateCoefficientReceipt(case, binding)
    if measuredIds and set(measuredIds) != set(bindingById):
        raise ScenarioCompositionError("measured association coefficient binding coverage mismatch")


def _validateCases(cases: tuple[OperatingScenarioCase, ...], strategies: tuple[StrategySpec, ...]) -> None:
    if not cases:
        raise ScenarioCompositionError("scenario comparison needs at least one case")
    if not strategies:
        raise ScenarioCompositionError("scenario comparison needs at least one strategy")
    caseIds = [case.caseId for case in cases]
    if any(not case.caseId or not case.label for case in cases) or len(set(caseIds)) != len(caseIds):
        raise ScenarioCompositionError("scenario cases need unique ids and labels")
    if len({strategy.strategyId for strategy in strategies}) != len(strategies):
        raise ScenarioCompositionError("scenario comparison strategy ids must be unique")
    for case in cases:
        if case.compiledState is not None and (case.statePrimitives or case.stateRef):
            raise ScenarioCompositionError("scenario case cannot mix compiled and manual bridge state")
        if bool(case.statePrimitives) != bool(case.stateRef):
            raise ScenarioCompositionError("manual scenario bridge state needs both primitives and stateRef")
        if not case.pathSet.paths:
            raise ScenarioCompositionError(f"scenario case has no paths: {case.caseId}")
        factorIds = {factor.variableId for factor in case.pathSet.factorSpecs}
        if factorIds & _OPERATING_ACTION_IDS:
            raise ScenarioCompositionError("intervention actions must be strategies, not driver path factors")
        _validateCoefficientBindings(case)
        for path in case.pathSet.paths:
            if case.pathSet.audit.assumptionHash and (
                path.validationStatus == "admitted"
                or path.certificateId
                or path.admissionReceiptId
                or path.admissionContentHash
                or path.maxAdmittedStep
            ):
                raise ScenarioCompositionError("explicit overlay cannot carry path admission")
            for step in path.steps:
                if set(step) & _OPERATING_ACTION_IDS:
                    raise ScenarioCompositionError("intervention actions must be strategies, not scenario paths")


def _strategyScores(run: SimulationRun) -> tuple[ScenarioStrategyScore, ...]:
    return tuple(
        ScenarioStrategyScore(
            item.strategyId,
            item.objectiveScores,
            item.feasible,
            item.breachCount,
        )
        for item in run.evaluations
    )


def _scoreLeaderStrategies(scores: tuple[ScenarioStrategyScore, ...]) -> tuple[str, ...]:
    feasible = tuple(score for score in scores if score.feasible)
    candidates = feasible or scores
    if not candidates:
        return ()
    bestKey = max((score.objectiveScores, -score.breachCount) for score in candidates)
    return tuple(
        sorted(score.strategyId for score in candidates if (score.objectiveScores, -score.breachCount) == bestKey)
    )


def _interventionCount(strategies: tuple[StrategySpec, ...]) -> int:
    count = 0
    for strategy in strategies:
        for row in strategy.actionsByStep:
            count += sum(1 for value in row.values() if abs(float(value)) > 1e-15)
    return count


def _boundaryCounts(
    case: OperatingScenarioCase,
    run: SimulationRun,
    bridgeHashes: tuple[str, ...],
    warnings: tuple[str, ...],
    strategies: tuple[StrategySpec, ...],
) -> ScenarioBoundaryCounts:
    bridgePaths = len(bridgeHashes)
    providerRefs = [ref for ref in case.pathSet.audit.sourceRefs if ref.startswith("providerObservationBatch:")]
    allWarnings = tuple(warnings)
    return ScenarioBoundaryCounts(
        driverCardCount=len(case.pathSet.audit.driverCardIds),
        pathCount=len(case.pathSet.paths),
        bridgeCount=bridgePaths,
        admittedPathCount=sum(1 for path in case.pathSet.paths if path.validationStatus == "admitted"),
        retrospectivePathCount=sum(1 for path in case.pathSet.paths if path.validationStatus == "retrospectiveOnly"),
        unvalidatedPathCount=sum(1 for path in case.pathSet.paths if path.validationStatus == "unvalidated"),
        providerBatchRefCount=len(providerRefs),
        explicitAssumptionCount=sum(1 for warning in allWarnings if "Assumption" in warning or "assumption" in warning),
        interventionCount=_interventionCount(strategies),
        conditionalWarningCount=sum(
            1
            for warning in allWarnings
            if "conditional" in warning or "unvalidated" in warning or "not admitted" in warning
        ),
    )


def _initialStateRefs(inputs: OperatingWorldInputs) -> tuple[str, ...]:
    refs = list(inputs.refs)
    if inputs.initialStateAdmissionReceiptId:
        refs.append(f"initialStateAdmission:{inputs.initialStateAdmissionReceiptId}")
    if inputs.stateCompilationContractHash:
        refs.append(f"stateCompilationContract:{inputs.stateCompilationContractHash}")
    if inputs.stateManifestHash:
        refs.append(f"stateManifest:{inputs.stateManifestHash}")
    if inputs.stateVintage is not None:
        refs.append(f"worldStateVintage:{inputs.stateVintage.artifactId}")
        refs.append(f"worldStatePayload:{inputs.stateVintage.payloadHash}")
        refs.extend(inputs.stateVintage.sourceRefs)
    return _dedupe(tuple(refs))


def _strategyRefs(strategies: tuple[StrategySpec, ...]) -> tuple[str, ...]:
    return _dedupe(tuple(ref for strategy in strategies for ref in strategy.refs))


def _median(values: tuple[float, ...]) -> float:
    if not values:
        raise ScenarioCompositionError("median needs at least one value")
    ordered = sorted(float(value) for value in values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _scoreForObjective(score: ScenarioStrategyScore, objectiveIndex: int) -> float:
    if objectiveIndex < 0:
        raise ScenarioCompositionError("objective index must be nonnegative")
    if objectiveIndex >= len(score.objectiveScores):
        raise ScenarioCompositionError("objective index is outside strategy score contract")
    return float(score.objectiveScores[objectiveIndex])


def _objectiveLeaders(
    scores: tuple[ScenarioStrategyScore, ...],
    objectiveIndex: int,
) -> tuple[str, ...]:
    candidates = tuple(score for score in scores if score.feasible) or tuple(scores)
    if not candidates:
        return ()
    bestScore = max(_scoreForObjective(score, objectiveIndex) for score in candidates)
    return tuple(
        sorted(
            score.strategyId
            for score in candidates
            if abs(_scoreForObjective(score, objectiveIndex) - bestScore) <= 1e-12
        )
    )


def _assumptionSetHash(case: OperatingScenarioCase, result: OperatingScenarioCaseResult) -> str:
    return canonicalPayloadHash(
        {
            "schemaVersion": SCENARIO_ASSUMPTION_SET_VERSION,
            "caseId": case.caseId,
            "label": case.label,
            "caseRefs": case.refs,
            "factorIds": tuple(factor.variableId for factor in case.pathSet.factorSpecs),
            "pathSetInputHash": case.pathSet.audit.inputHash,
            "pathHistoryInputHash": result.pathHistoryInputHash,
            "pathAssumptionHash": result.pathAssumptionHash,
            "basePathSetHash": result.basePathSetHash,
            "pathOverlayHash": result.pathOverlayHash,
            "scenarioPathPackageHash": result.scenarioPathPackageHash,
            "scenarioPathPackageSubjectHash": result.scenarioPathPackageSubjectHash,
            "scenarioPathPackageReceiptId": result.scenarioPathPackageReceiptId,
            "coefficientBindingHashes": tuple(
                scenarioCoefficientBindingHash(binding) for binding in case.coefficientBindings
            ),
        }
    )


def _strategySetHash(
    strategies: tuple[StrategySpec, ...],
    strategyContractHashes: tuple[str, ...],
    strategyRefs: tuple[str, ...],
) -> str:
    return canonicalPayloadHash(
        {
            "schemaVersion": STRATEGY_SET_VERSION,
            "strategyIds": tuple(strategy.strategyId for strategy in strategies),
            "strategyContractHashes": strategyContractHashes,
            "strategyRefs": strategyRefs,
        }
    )


def _floatPairs(values) -> tuple[tuple[str, float], ...]:
    return tuple((str(key), float(value)) for key, value in sorted(values.items(), key=lambda item: str(item[0])))


def _actionRows(strategy: StrategySpec) -> tuple[tuple[tuple[str, float], ...], ...]:
    return tuple(_floatPairs(row) for row in strategy.actionsByStep)


def _rowHash(kind: str, payload: dict) -> str:
    return canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_PLAY_REPLAY_VERSION,
            "kind": kind,
            "payload": payload,
        }
    )


def _conditionRows(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
    caseLedgerHashes: tuple[str, ...],
    assumptionSetHashes: tuple[str, ...],
) -> tuple[ConditionalPlayConditionRow, ...]:
    rows: list[ConditionalPlayConditionRow] = []
    for ledger, caseLedgerHash, assumptionSetHash in zip(
        caseLedgers,
        caseLedgerHashes,
        assumptionSetHashes,
        strict=True,
    ):
        laneIds = ledger.driverRegistryLedger.laneIds if ledger.driverRegistryLedger is not None else ()
        payload = {
            "caseLedgerHash": caseLedgerHash,
            "caseId": ledger.caseId,
            "assumptionSetHash": assumptionSetHash,
            "pathHistoryInputHash": ledger.pathHistoryInputHash,
            "pathAssumptionHash": ledger.pathAssumptionHash,
            "pathAssumptionStepHashes": ledger.pathAssumptionStepHashes,
            "providerLaneLineageHash": ledger.providerLaneLineageHash,
            "blockedReasons": ledger.blockedReasons,
        }
        rows.append(
            ConditionalPlayConditionRow(
                rowHash=_rowHash("conditionRow", payload),
                caseId=ledger.caseId,
                label=ledger.label,
                assumptionSetHash=assumptionSetHash,
                pathHistoryInputHash=ledger.pathHistoryInputHash,
                pathAssumptionHash=ledger.pathAssumptionHash,
                pathAssumptionStepHashes=ledger.pathAssumptionStepHashes,
                observedHistoryStatus=ledger.observedHistoryStatus,
                futureAdjustmentStatus=ledger.futureAdjustmentStatus,
                composedPathAdmissionStatus=ledger.composedPathAdmissionStatus,
                pathAdmissionReceiptId=ledger.pathAdmissionReceiptId,
                policyEvaluationCertificateId=ledger.policyEvaluationCertificateId,
                basePathMaxAdmittedStep=ledger.basePathMaxAdmittedStep,
                pathHorizon=ledger.pathHorizon,
                pathFrequency=ledger.pathFrequency,
                driverRegistryLaneIds=laneIds,
                factorIds=ledger.factorIds,
                providerLaneLineageHash=ledger.providerLaneLineageHash,
                providerLineageStatus=ledger.providerLineageStatus,
                blockedReasons=ledger.blockedReasons,
            )
        )
    return tuple(rows)


def _playStrategyRows(
    strategies: tuple[StrategySpec, ...],
    strategyContractHashes: tuple[str, ...],
    summaries: tuple[ConditionalStrategySummary, ...],
) -> tuple[ConditionalPlayStrategyRow, ...]:
    summaryById = {summary.strategyId: summary for summary in summaries}
    leaderIds = {
        summary.strategyId
        for summary in summaries
        if summaries and abs(summary.leaderFrequency - max(item.leaderFrequency for item in summaries)) <= 1e-12
    }
    rows: list[ConditionalPlayStrategyRow] = []
    for strategy, contractHash in zip(strategies, strategyContractHashes, strict=True):
        summary = summaryById[strategy.strategyId]
        actionRows = _actionRows(strategy)
        actionIds = tuple(sorted({actionId for row in actionRows for actionId, _value in row}))
        payload = {
            "strategyId": strategy.strategyId,
            "strategyContractHash": contractHash,
            "actionsByStep": actionRows,
            "summary": summary,
            "conditionalLeader": strategy.strategyId in leaderIds,
        }
        rows.append(
            ConditionalPlayStrategyRow(
                rowHash=_rowHash("strategyRow", payload),
                strategyId=strategy.strategyId,
                strategyContractHash=contractHash,
                actionIds=actionIds,
                actionsByStep=actionRows,
                conditionalLeader=strategy.strategyId in leaderIds,
                leaderFrequency=summary.leaderFrequency,
                scoreMedian=summary.scoreMedian,
                scoreWorst=summary.scoreWorst,
                scoreBest=summary.scoreBest,
                regretWorst=summary.regretWorst,
                feasibleCellCount=summary.feasibleCellCount,
                totalCellCount=summary.totalCellCount,
                breachCount=summary.breachCount,
            )
        )
    return tuple(rows)


def _playCellRows(cells: tuple[ConditionalScenarioExperimentCell, ...]) -> tuple[ConditionalPlayCellRow, ...]:
    rows = []
    for cell in cells:
        payload = {
            "caseId": cell.caseId,
            "strategyId": cell.strategyId,
            "objectiveScores": cell.objectiveScores,
            "score": cell.score,
            "regret": cell.regret,
            "scoreLeader": cell.scoreLeader,
            "resultHash": cell.resultHash,
        }
        rows.append(
            ConditionalPlayCellRow(
                rowHash=_rowHash("cellRow", payload),
                caseId=cell.caseId,
                label=cell.label,
                strategyId=cell.strategyId,
                objectiveScores=cell.objectiveScores,
                score=cell.score,
                feasible=cell.feasible,
                breachCount=cell.breachCount,
                regret=cell.regret,
                scoreLeader=cell.scoreLeader,
                assumptionSetHash=cell.assumptionSetHash,
                scenarioPathPackageHash=cell.scenarioPathPackageHash,
                pathSetHash=cell.pathSetHash,
                runHash=cell.runHash,
                resultHash=cell.resultHash,
                blockedReasons=cell.blockedReasons,
            )
        )
    return tuple(rows)


def _sourceLineageKeysByFactor(ledger: OneCompanyScenarioCaseLedger) -> tuple[tuple[str, str], ...]:
    if ledger.driverRegistryLedger is None:
        return tuple((factorId, f"lineage:{ledger.caseId}:{factorId}") for factorId in ledger.factorIds)
    pairs = []
    for factorId, laneId in zip(
        ledger.driverRegistryLedger.factorIds, ledger.driverRegistryLedger.laneIds, strict=False
    ):
        pairs.append((factorId, f"lineage:{ledger.caseId}:{laneId}"))
    return tuple(pairs)


def _valueSummary(values: tuple[float, ...]) -> tuple[tuple[str, float], ...]:
    numbers = tuple(sorted(float(value) for value in values))
    if not numbers:
        raise ScenarioCompositionError("control surface value summary needs values")
    count = len(numbers)
    midpoint = count // 2
    median = numbers[midpoint] if count % 2 else (numbers[midpoint - 1] + numbers[midpoint]) / 2.0
    return (
        ("count", float(count)),
        ("min", numbers[0]),
        ("median", median),
        ("mean", sum(numbers) / count),
        ("max", numbers[-1]),
    )


def _actionUnit(actionId: str) -> str:
    return {
        "priceChange": "ratio",
        "capacityInvestment": "currency",
        "borrow": "currency",
        "repay": "currency",
    }.get(actionId, "actionUnit")


def _controlRowPayload(row: ConditionalPlayControlRow) -> dict:
    return {
        "controlId": row.controlId,
        "semanticPlane": row.semanticPlane,
        "controlKind": row.controlKind,
        "adjustmentMode": row.adjustmentMode,
        "adjustabilityStatus": row.adjustabilityStatus,
        "scope": row.scope,
        "caseId": row.caseId,
        "strategyId": row.strategyId,
        "step": row.step,
        "targetId": row.targetId,
        "sourceVariableId": row.sourceVariableId,
        "targetVariableId": row.targetVariableId,
        "laneId": row.laneId,
        "cardId": row.cardId,
        "unit": row.unit,
        "frequency": row.frequency,
        "timing": row.timing,
        "transformId": row.transformId,
        "valueSummary": row.valueSummary,
        "sourceRefs": row.sourceRefs,
        "semanticRefs": row.semanticRefs,
        "expectedHashImpacts": row.expectedHashImpacts,
        "forbiddenHashImpacts": row.forbiddenHashImpacts,
        "providerLaneLineageHash": row.providerLaneLineageHash,
        "providerLineageStatus": row.providerLineageStatus,
        "providerObservationBatchReceiptIds": row.providerObservationBatchReceiptIds,
        "providerObservationBatchSourceReceiptIds": row.providerObservationBatchSourceReceiptIds,
        "priceSourceLegReceiptIds": row.priceSourceLegReceiptIds,
        "derivedReturnReceiptIds": row.derivedReturnReceiptIds,
        "rawSourceRefs": row.rawSourceRefs,
        "revisedHistoryRefs": row.revisedHistoryRefs,
        "explicitAssumptionId": row.explicitAssumptionId,
        "claim": row.claim,
        "falsifier": row.falsifier,
        "pathHistoryInputHash": row.pathHistoryInputHash,
        "pathAssumptionHash": row.pathAssumptionHash,
        "pathAssumptionStepHash": row.pathAssumptionStepHash,
        "assumptionSetHash": row.assumptionSetHash,
        "caseLedgerHash": row.caseLedgerHash,
        "strategyContractHash": row.strategyContractHash,
        "parameterHash": row.parameterHash,
        "blockedReasons": row.blockedReasons,
    }


def _controlRow(**values) -> ConditionalPlayControlRow:
    payload = dict(values)
    return ConditionalPlayControlRow(rowHash=_rowHash("controlRow", payload), **values)


def _laneMetadataByFactor(ledger: OneCompanyScenarioCaseLedger) -> dict[str, tuple[str, str]]:
    if ledger.driverRegistryLedger is None:
        return {factorId: ("", "") for factorId in ledger.factorIds}
    return {
        factorId: (laneId, cardId)
        for factorId, laneId, cardId in zip(
            ledger.driverRegistryLedger.factorIds,
            ledger.driverRegistryLedger.laneIds,
            ledger.driverRegistryLedger.cardIds,
            strict=False,
        )
    }


def _assumptionDescriptorByFactor(case: OperatingScenarioCase) -> dict[str, tuple[str, str, str]]:
    return {
        factorId: (assumptionId, claim, falsifier)
        for factorId, assumptionId, claim, falsifier in case.pathSet.audit.assumptionDescriptors
    }


def _controlLineageBlockers(ledger: OneCompanyScenarioCaseLedger) -> tuple[str, ...]:
    return tuple(
        reason
        for reason in ("rawSourceRefOnly", "revisedHistory", "unverifiedProviderObservationRef")
        if reason in ledger.providerLineageStatus
    )


def _currentStateControlRows(inputs: OperatingWorldInputs) -> tuple[ConditionalPlayControlRow, ...]:
    primitiveById = {primitive.variableId: primitive for primitive in inputs.statePrimitiveContracts}
    rows: list[ConditionalPlayControlRow] = []
    for variableId, value in sorted(inputs.state.items(), key=lambda item: str(item[0])):
        primitive = primitiveById.get(variableId)
        rows.append(
            _controlRow(
                controlId=f"currentState:{variableId}",
                semanticPlane="currentState",
                controlKind="initialState",
                adjustmentMode="initialStateOverlay",
                adjustabilityStatus="overlayOnly",
                scope="experiment",
                caseId="",
                strategyId="",
                step=-1,
                targetId=variableId,
                sourceVariableId="",
                targetVariableId=variableId,
                laneId="",
                cardId="",
                unit=primitive.unit if primitive is not None else "",
                frequency=primitive.frequency if primitive is not None else inputs.stepFrequency,
                timing=primitive.timing if primitive is not None else "level",
                transformId=primitive.transformId if primitive is not None else "identity-v1",
                valueSummary=_valueSummary((float(value),)),
                sourceRefs=inputs.refs,
                semanticRefs=(),
                expectedHashImpacts=(
                    "initialState",
                    "simulationSpecHash",
                    "resultSetHash",
                    "tracePanelHash",
                    "playReplayHash",
                ),
                forbiddenHashImpacts=(
                    "providerLaneLineageHash",
                    "pathHistoryInputHash",
                    "pathAssumptionHash",
                    "strategySetHash",
                ),
                providerLaneLineageHash="",
                providerLineageStatus=(),
                providerObservationBatchReceiptIds=(),
                providerObservationBatchSourceReceiptIds=(),
                priceSourceLegReceiptIds=(),
                derivedReturnReceiptIds=(),
                rawSourceRefs=(),
                revisedHistoryRefs=(),
                explicitAssumptionId="",
                claim="",
                falsifier="",
                pathHistoryInputHash="",
                pathAssumptionHash="",
                pathAssumptionStepHash="",
                assumptionSetHash="",
                caseLedgerHash="",
                strategyContractHash="",
                parameterHash=inputs.stateManifestHash,
                blockedReasons=inputs.warnings,
            )
        )
    return tuple(rows)


def _conditionControlRows(
    cases: tuple[OperatingScenarioCase, ...],
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
    caseLedgerHashes: tuple[str, ...],
    assumptionSetHashes: tuple[str, ...],
) -> tuple[ConditionalPlayControlRow, ...]:
    rows: list[ConditionalPlayControlRow] = []
    for case, ledger, caseLedgerHash, assumptionSetHash in zip(
        cases,
        caseLedgers,
        caseLedgerHashes,
        assumptionSetHashes,
        strict=True,
    ):
        laneByFactor = _laneMetadataByFactor(ledger)
        descriptorByFactor = _assumptionDescriptorByFactor(case)
        sourceLineageByFactor = dict(_sourceLineageKeysByFactor(ledger))
        for factor in case.pathSet.factorSpecs:
            laneId, cardId = laneByFactor.get(factor.variableId, ("", ""))
            explicitAssumptionId, claim, falsifier = descriptorByFactor.get(factor.variableId, ("", "", ""))
            isExplicit = bool(explicitAssumptionId)
            semanticPlane = "assumptionDelta" if isExplicit else "conditionFactor"
            adjustmentMode = "setFutureAssumptionStep" if isExplicit else "addExplicitOverlay"
            adjustabilityStatus = "editableExplicitAssumption" if isExplicit else "overlayOnly"
            blockers = _controlLineageBlockers(ledger)
            if isExplicit:
                blockers = _dedupe((*blockers, "explicitFutureAdjustmentPresent"))
            expectedHashImpacts = (
                (
                    "pathAssumptionStepHash",
                    "pathAssumptionHash",
                    "assumptionSetHash",
                    "caseLedgerHash",
                    "experimentHash",
                    "playReplayHash",
                )
                if isExplicit
                else (
                    "pathAssumptionStepHash",
                    "pathAssumptionHash",
                    "assumptionSetHash",
                    "caseLedgerHash",
                    "parameterHash",
                    "simulationSpecHash",
                    "resultSetHash",
                    "tracePanelHash",
                    "controlPanelHash",
                    "controlSurfaceHash",
                    "experimentHash",
                    "playReplayHash",
                )
            )
            forbiddenHashImpacts = (
                (
                    "providerLaneLineageHash",
                    "pathHistoryInputHash",
                    "strategySetHash",
                    "rawSourceRefs",
                    "revisedHistoryRefs",
                )
                if isExplicit
                else (
                    "initialState",
                    "providerLaneLineageHash",
                    "providerObservationBatchReceiptIds",
                    "priceSourceLegReceiptIds",
                    "derivedReturnReceiptIds",
                    "pathHistoryInputHash",
                    "strategyContractHash",
                    "strategySetHash",
                    "rawSourceRefs",
                    "revisedHistoryRefs",
                )
            )
            for step in range(case.pathSet.audit.horizon):
                values = tuple(
                    float(path.steps[step][factor.variableId])
                    for path in case.pathSet.paths
                    if factor.variableId in path.steps[step]
                )
                if len(values) != len(case.pathSet.paths):
                    raise ScenarioCompositionError("control surface factor coverage mismatch")
                sourceLineageKey = sourceLineageByFactor.get(
                    factor.variableId,
                    f"lineage:{ledger.caseId}:{factor.variableId}",
                )
                pathAssumptionStepHash = (
                    ledger.pathAssumptionStepHashes[step] if step < len(ledger.pathAssumptionStepHashes) else ""
                )
                semanticRefs = (
                    f"sourceLineageKey:{sourceLineageKey}",
                    *(ledger.driverRegistryLedger.semanticRefs if ledger.driverRegistryLedger is not None else ()),
                )
                rows.append(
                    _controlRow(
                        controlId=f"{semanticPlane}:{ledger.caseId}:{factor.variableId}:step{step}",
                        semanticPlane=semanticPlane,
                        controlKind="driverPathFactor",
                        adjustmentMode=adjustmentMode,
                        adjustabilityStatus=adjustabilityStatus,
                        scope="caseStep",
                        caseId=ledger.caseId,
                        strategyId="",
                        step=step,
                        targetId=factor.variableId,
                        sourceVariableId=factor.variableId,
                        targetVariableId="",
                        laneId=laneId,
                        cardId=cardId,
                        unit=factor.unit,
                        frequency=factor.frequency,
                        timing=factor.timing,
                        transformId=factor.transformId,
                        valueSummary=_valueSummary(values),
                        sourceRefs=ledger.pathSourceRefs,
                        semanticRefs=semanticRefs,
                        expectedHashImpacts=expectedHashImpacts,
                        forbiddenHashImpacts=forbiddenHashImpacts,
                        providerLaneLineageHash=ledger.providerLaneLineageHash,
                        providerLineageStatus=ledger.providerLineageStatus,
                        providerObservationBatchReceiptIds=ledger.providerObservationBatchReceiptIds,
                        providerObservationBatchSourceReceiptIds=ledger.providerObservationBatchSourceReceiptIds,
                        priceSourceLegReceiptIds=ledger.priceSourceLegReceiptIds,
                        derivedReturnReceiptIds=ledger.derivedReturnReceiptIds,
                        rawSourceRefs=ledger.rawSourceRefs,
                        revisedHistoryRefs=ledger.revisedHistoryRefs,
                        explicitAssumptionId=explicitAssumptionId,
                        claim=claim,
                        falsifier=falsifier,
                        pathHistoryInputHash=ledger.pathHistoryInputHash,
                        pathAssumptionHash=ledger.pathAssumptionHash,
                        pathAssumptionStepHash=pathAssumptionStepHash,
                        assumptionSetHash=assumptionSetHash,
                        caseLedgerHash=caseLedgerHash,
                        strategyContractHash="",
                        parameterHash="",
                        blockedReasons=blockers,
                    )
                )
    return tuple(rows)


def _strategyActionControlRows(
    strategies: tuple[StrategySpec, ...],
    strategyContractHashes: tuple[str, ...],
) -> tuple[ConditionalPlayControlRow, ...]:
    rows: list[ConditionalPlayControlRow] = []
    for strategy, contractHash in zip(strategies, strategyContractHashes, strict=True):
        for step, actions in enumerate(strategy.actionsByStep):
            for actionId, value in sorted(actions.items(), key=lambda item: str(item[0])):
                rows.append(
                    _controlRow(
                        controlId=f"strategyAction:{strategy.strategyId}:{actionId}:step{step}",
                        semanticPlane="strategyAction",
                        controlKind="strategyActionSchedule",
                        adjustmentMode="setStrategyActionStep",
                        adjustabilityStatus="editableStrategyAction",
                        scope="strategyStep",
                        caseId="",
                        strategyId=strategy.strategyId,
                        step=step,
                        targetId=actionId,
                        sourceVariableId="",
                        targetVariableId=actionId,
                        laneId="",
                        cardId="",
                        unit=_actionUnit(actionId),
                        frequency="step",
                        timing="action",
                        transformId="identity-v1",
                        valueSummary=_valueSummary((float(value),)),
                        sourceRefs=strategy.refs,
                        semanticRefs=(),
                        expectedHashImpacts=(
                            "strategySetHash",
                            "simulationSpecHash",
                            "resultSetHash",
                            "tracePanelHash",
                            "playReplayHash",
                        ),
                        forbiddenHashImpacts=(
                            "providerLaneLineageHash",
                            "pathHistoryInputHash",
                            "pathAssumptionHash",
                            "assumptionSetHash",
                        ),
                        providerLaneLineageHash="",
                        providerLineageStatus=(),
                        providerObservationBatchReceiptIds=(),
                        providerObservationBatchSourceReceiptIds=(),
                        priceSourceLegReceiptIds=(),
                        derivedReturnReceiptIds=(),
                        rawSourceRefs=(),
                        revisedHistoryRefs=(),
                        explicitAssumptionId="",
                        claim="",
                        falsifier="",
                        pathHistoryInputHash="",
                        pathAssumptionHash="",
                        pathAssumptionStepHash="",
                        assumptionSetHash="",
                        caseLedgerHash="",
                        strategyContractHash=contractHash,
                        parameterHash="",
                        blockedReasons=(),
                    )
                )
    return tuple(rows)


def _lawParameterControlRows(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
    caseLedgerHashes: tuple[str, ...],
    assumptionSetHashes: tuple[str, ...],
) -> tuple[ConditionalPlayControlRow, ...]:
    rows: list[ConditionalPlayControlRow] = []
    for ledger, caseLedgerHash, assumptionSetHash in zip(
        caseLedgers,
        caseLedgerHashes,
        assumptionSetHashes,
        strict=True,
    ):
        blockers = _controlLineageBlockers(ledger)
        for exposure in ledger.exposureLedgers:
            parameterHash = canonicalPayloadHash(
                {
                    "schemaVersion": "conditional-play-law-parameter-v1",
                    "caseLedgerHash": caseLedgerHash,
                    "exposure": exposure,
                }
            )
            exposureBlockers = blockers
            if not exposure.admissionReceiptId:
                exposureBlockers = _dedupe((*exposureBlockers, "lawParameterAdmissionMissing"))
            rows.append(
                _controlRow(
                    controlId=f"lawParameter:{ledger.caseId}:{exposure.exposureId}:coefficient",
                    semanticPlane="lawParameter",
                    controlKind="operatingTransmissionCoefficient",
                    adjustmentMode="lawParameterOverride",
                    adjustabilityStatus="overlayOnly",
                    scope="caseLaw",
                    caseId=ledger.caseId,
                    strategyId="",
                    step=-1,
                    targetId=f"{exposure.sourceVariableId}->{exposure.targetShock}",
                    sourceVariableId=exposure.sourceVariableId,
                    targetVariableId=exposure.targetShock,
                    laneId="",
                    cardId="",
                    unit=exposure.coefficientUnit,
                    frequency=exposure.sourceFrequency,
                    timing=exposure.sourceTiming,
                    transformId=exposure.sourceTransformId,
                    valueSummary=_valueSummary((exposure.coefficient,)),
                    sourceRefs=(exposure.sourceRef,),
                    semanticRefs=(f"factorContractHash:{exposure.sourceFactorContractHash}",),
                    expectedHashImpacts=(
                        "parameterHash",
                        "simulationSpecHash",
                        "resultSetHash",
                        "tracePanelHash",
                        "playReplayHash",
                    ),
                    forbiddenHashImpacts=(
                        "providerLaneLineageHash",
                        "pathHistoryInputHash",
                        "pathAssumptionHash",
                        "strategySetHash",
                    ),
                    providerLaneLineageHash=ledger.providerLaneLineageHash,
                    providerLineageStatus=ledger.providerLineageStatus,
                    providerObservationBatchReceiptIds=ledger.providerObservationBatchReceiptIds,
                    providerObservationBatchSourceReceiptIds=ledger.providerObservationBatchSourceReceiptIds,
                    priceSourceLegReceiptIds=ledger.priceSourceLegReceiptIds,
                    derivedReturnReceiptIds=ledger.derivedReturnReceiptIds,
                    rawSourceRefs=ledger.rawSourceRefs,
                    revisedHistoryRefs=ledger.revisedHistoryRefs,
                    explicitAssumptionId="",
                    claim="",
                    falsifier="",
                    pathHistoryInputHash=ledger.pathHistoryInputHash,
                    pathAssumptionHash=ledger.pathAssumptionHash,
                    pathAssumptionStepHash="",
                    assumptionSetHash=assumptionSetHash,
                    caseLedgerHash=caseLedgerHash,
                    strategyContractHash="",
                    parameterHash=parameterHash,
                    blockedReasons=exposureBlockers,
                )
            )
    return tuple(rows)


def _controlSortKey(row: ConditionalPlayControlRow) -> tuple:
    return (row.semanticPlane, row.caseId, row.strategyId, row.step, row.targetId, row.controlId)


def _validateControlRows(
    rows: tuple[ConditionalPlayControlRow, ...],
    *,
    stateIds: set[str],
    actionIds: set[str],
    factorIds: set[str],
) -> None:
    if not rows:
        raise ScenarioCompositionError("conditional play control surface needs rows")
    controlIds = tuple(row.controlId for row in rows)
    if len(set(controlIds)) != len(controlIds):
        raise ScenarioCompositionError("conditional play control ids must be unique")
    for row in rows:
        if row.rowHash != _rowHash("controlRow", _controlRowPayload(row)):
            raise ScenarioCompositionError("conditional play control row hash mismatch")
        if row.semanticPlane in {"conditionFactor", "assumptionDelta"}:
            if row.targetId in actionIds or row.targetId in stateIds or row.targetId not in factorIds:
                raise ScenarioCompositionError("condition controls must stay in factor plane")
        if row.semanticPlane == "strategyAction" and row.targetId not in actionIds:
            raise ScenarioCompositionError("strategy controls must stay in action plane")
        if row.semanticPlane == "currentState" and row.targetId not in stateIds:
            raise ScenarioCompositionError("current state controls must stay in state plane")
        if row.semanticPlane == "lawParameter" and (
            row.targetId in actionIds or row.targetId in stateIds or not row.parameterHash
        ):
            raise ScenarioCompositionError("law controls must stay in parameter plane")
        if row.adjustabilityStatus == "editableExplicitAssumption" and (
            not row.explicitAssumptionId or not row.claim or not row.falsifier or not row.pathAssumptionStepHash
        ):
            raise ScenarioCompositionError("editable assumption controls need claim, falsifier, and step hash")
        if row.rawSourceRefs and "rawSourceRefOnly" not in row.blockedReasons:
            raise ScenarioCompositionError("raw source controls need raw source blocker")
        if row.revisedHistoryRefs and "revisedHistory" not in row.blockedReasons:
            raise ScenarioCompositionError("revised history controls need revised history blocker")


def conditionalPlayControlSurfacePayload(surface: ConditionalPlayControlSurface) -> dict:
    """Build canonical payload for the internal play control surface."""

    return {
        "schemaVersion": surface.schemaVersion,
        "kind": surface.kind,
        "lineageMode": surface.lineageMode,
        "contractHash": CONDITIONAL_PLAY_CONTROL_SURFACE_CONTRACT_HASH,
        "entityId": surface.entityId,
        "shape": {
            "scenarioCount": surface.scenarioCount,
            "strategyCount": surface.strategyCount,
            "horizon": surface.horizon,
            "frequency": surface.frequency,
            "controlCount": surface.controlCount,
        },
        "sourceSeals": {
            "caseLedgerHashes": surface.caseLedgerHashes,
            "providerLaneLineageHashes": surface.providerLaneLineageHashes,
            "pathHistoryInputHashes": surface.pathHistoryInputHashes,
            "pathAssumptionHashes": surface.pathAssumptionHashes,
            "assumptionSetHashes": surface.assumptionSetHashes,
        },
        "rowHashes": surface.rowHashes,
        "adjustableControlIds": surface.adjustableControlIds,
        "overlayControlIds": surface.overlayControlIds,
        "lockedControlIds": surface.lockedControlIds,
        "controlPanelHash": surface.controlPanelHash,
        "rows": surface.rows,
        "blockedReasons": surface.blockedReasons,
        "warnings": surface.warnings,
    }


def conditionalPlayControlSurfaceSubjectHash(surface: ConditionalPlayControlSurface) -> str:
    """Return the content hash for the internal play control surface."""

    return canonicalPayloadHash(conditionalPlayControlSurfacePayload(surface))


def _buildConditionalPlayControlSurface(
    *,
    entityId: str,
    inputs: OperatingWorldInputs,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
    caseLedgerHashes: tuple[str, ...],
    assumptionSetHashes: tuple[str, ...],
    strategyContractHashes: tuple[str, ...],
    warnings: tuple[str, ...],
) -> ConditionalPlayControlSurface:
    rows = tuple(
        sorted(
            (
                *_currentStateControlRows(inputs),
                *_conditionControlRows(cases, caseLedgers, caseLedgerHashes, assumptionSetHashes),
                *_strategyActionControlRows(strategies, strategyContractHashes),
                *_lawParameterControlRows(caseLedgers, caseLedgerHashes, assumptionSetHashes),
            ),
            key=_controlSortKey,
        )
    )
    stateIds = {str(variableId) for variableId in inputs.state}
    actionIds = {actionId for strategy in strategies for row in strategy.actionsByStep for actionId in row}
    factorIds = {factor.variableId for case in cases for factor in case.pathSet.factorSpecs}
    _validateControlRows(rows, stateIds=stateIds, actionIds=actionIds, factorIds=factorIds)
    adjustableControlIds = tuple(
        row.controlId
        for row in rows
        if row.adjustabilityStatus in {"editableExplicitAssumption", "editableStrategyAction"}
    )
    overlayControlIds = tuple(row.controlId for row in rows if row.adjustabilityStatus == "overlayOnly")
    lockedControlIds = tuple(row.controlId for row in rows if row.adjustabilityStatus.startswith("locked"))
    blockedReasons = _dedupe(tuple(reason for row in rows for reason in row.blockedReasons))
    controlPanelHash = canonicalPayloadHash(rows)
    draft = ConditionalPlayControlSurface(
        surfaceHash="",
        schemaVersion=CONDITIONAL_PLAY_CONTROL_SURFACE_VERSION,
        kind=CONDITIONAL_PLAY_CONTROL_SURFACE_KIND,
        lineageMode="conditionalWarGameControlProjection",
        entityId=entityId,
        scenarioCount=len(cases),
        strategyCount=len(strategies),
        horizon=caseLedgers[0].pathHorizon if caseLedgers else 0,
        frequency=caseLedgers[0].pathFrequency if caseLedgers else "",
        controlCount=len(rows),
        controlPanelHash=controlPanelHash,
        caseLedgerHashes=caseLedgerHashes,
        providerLaneLineageHashes=_dedupe(tuple(ledger.providerLaneLineageHash for ledger in caseLedgers)),
        pathHistoryInputHashes=_dedupe(tuple(ledger.pathHistoryInputHash for ledger in caseLedgers)),
        pathAssumptionHashes=tuple(ledger.pathAssumptionHash for ledger in caseLedgers),
        assumptionSetHashes=assumptionSetHashes,
        rowHashes=tuple(row.rowHash for row in rows),
        adjustableControlIds=adjustableControlIds,
        overlayControlIds=overlayControlIds,
        lockedControlIds=lockedControlIds,
        rows=rows,
        blockedReasons=blockedReasons,
        warnings=warnings,
    )
    return replace(draft, surfaceHash=conditionalPlayControlSurfaceSubjectHash(draft))


def _controlPatchPayload(patch: ConditionalPlayControlPatch) -> dict:
    return {
        "controlId": patch.controlId,
        "baseSurfaceHash": patch.baseSurfaceHash,
        "baseRowHash": patch.baseRowHash,
        "value": patch.value,
        "patchRef": patch.patchRef,
        "reason": patch.reason,
        "claim": patch.claim,
        "falsifier": patch.falsifier,
    }


def _controlPatchHash(patch: ConditionalPlayControlPatch) -> str:
    return canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_PLAY_CONTROL_EXECUTION_VERSION,
            "kind": "conditionalPlayControlPatch",
            "patch": _controlPatchPayload(patch),
        }
    )


def _controlPatchSetHash(
    *,
    baseExperiment: "ConditionalScenarioExperiment",
    controlSurface: ConditionalPlayControlSurface,
    patches: tuple[ConditionalPlayControlPatch, ...],
) -> str:
    report = baseExperiment.playReplayReport
    return canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_PLAY_CONTROL_EXECUTION_VERSION,
            "kind": "conditionalPlayControlPatchSet",
            "baseExperimentHash": baseExperiment.experimentHash,
            "basePlayReplayHash": report.playReplayHash if report is not None else "",
            "baseControlSurfaceHash": controlSurface.surfaceHash,
            "patches": tuple(_controlPatchPayload(patch) for patch in patches),
        }
    )


def _meanControlValue(row: ConditionalPlayControlRow) -> float:
    values = dict(row.valueSummary)
    if "mean" not in values:
        raise ScenarioCompositionError("control row lacks mean value")
    return float(values["mean"])


def _controlRowsById(surface: ConditionalPlayControlSurface) -> dict[str, ConditionalPlayControlRow]:
    rows = {row.controlId: row for row in surface.rows}
    if len(rows) != len(surface.rows):
        raise ScenarioCompositionError("conditional play control ids must be unique")
    return rows


def _validateControlPatchRows(
    surface: ConditionalPlayControlSurface,
    patches: tuple[ConditionalPlayControlPatch, ...],
    *,
    allowMixedPlanes: bool,
) -> tuple[ConditionalPlayControlRow, ...]:
    if not patches:
        raise ScenarioCompositionError("conditional play control execution needs patches")
    if len({patch.controlId for patch in patches}) != len(patches):
        raise ScenarioCompositionError("duplicate conditional play control patch")
    rowById = _controlRowsById(surface)
    rows = []
    for patch in patches:
        row = rowById.get(patch.controlId)
        if row is None:
            raise ScenarioCompositionError(f"unknown conditional play control: {patch.controlId}")
        if patch.baseSurfaceHash != surface.surfaceHash:
            raise ScenarioCompositionError("stale conditional play control surface hash")
        if patch.baseRowHash != row.rowHash:
            raise ScenarioCompositionError("stale conditional play control row hash")
        if row.adjustabilityStatus.startswith("locked"):
            raise ScenarioCompositionError("locked conditional play control cannot be patched")
        if patch.value == _meanControlValue(row):
            raise ScenarioCompositionError("conditional play control patch is a no-op")
        rows.append(row)
    semanticPlanes = {row.semanticPlane for row in rows}
    if not allowMixedPlanes and len(semanticPlanes) != 1:
        raise ScenarioCompositionError("mixed semantic plane control patches are not supported")
    unknownPlanes = sorted(set(semanticPlanes) - set(CONDITIONAL_PLAY_SCENARIO_DECK_PLANE_ORDER))
    if unknownPlanes:
        raise ScenarioCompositionError(f"{unknownPlanes[0]} control patch requires a separate overlay route")
    return tuple(rows)


def _validateControlPatches(
    surface: ConditionalPlayControlSurface,
    patches: tuple[ConditionalPlayControlPatch, ...],
) -> tuple[ConditionalPlayControlRow, ...]:
    return _validateControlPatchRows(surface, patches, allowMixedPlanes=False)


def _safeControlIdPart(value: str) -> str:
    text = "".join(character if character.isalnum() else "_" for character in str(value))
    return text.strip("_") or "control"


def _rejectUnsafeConditionPatchRef(patchRef: str) -> None:
    unsafePrefixes = (
        *_STRUCTURED_PROVIDER_LINEAGE_REF_PREFIXES,
        "pathAdmission:",
        "pathSetAdmission:",
        "driverCoefficientAdmission:",
        "initialStateAdmission:",
        "stateReceipt:",
        "verifiedStateReceipt:",
    )
    if patchRef.startswith(unsafePrefixes):
        raise ScenarioCompositionError("condition factor patch provenance cannot mimic admitted lineage")


def _patchConditionFactorCases(
    cases: tuple[OperatingScenarioCase, ...],
    rows: tuple[ConditionalPlayControlRow, ...],
    patches: tuple[ConditionalPlayControlPatch, ...],
) -> tuple[OperatingScenarioCase, ...]:
    caseById = {case.caseId: case for case in cases}
    patchedCases = dict(caseById)
    for row, patch in zip(rows, patches, strict=True):
        case = patchedCases.get(row.caseId)
        if case is None or row.step < 0 or not row.targetId:
            raise ScenarioCompositionError("condition factor patch target is invalid")
        if not patch.claim or not patch.falsifier:
            raise ScenarioCompositionError("condition factor overlay needs claim and falsifier")
        _rejectUnsafeConditionPatchRef(patch.patchRef)
        factorIds = {factor.variableId for factor in case.pathSet.factorSpecs}
        if row.targetId not in factorIds:
            raise ScenarioCompositionError("condition factor patch target is missing")
        matchingExposures = tuple(exposure for exposure in case.exposures if exposure.sourceVariableId == row.targetId)
        if not matchingExposures:
            raise ScenarioCompositionError("condition factor overlay needs a matching exposure")
        for exposure in matchingExposures:
            if exposure.evidenceKind == "measuredAssociation" or _driverCoefficientAdmissionReceiptId(
                exposure.sourceRef
            ):
                raise ScenarioCompositionError("condition factor overlay cannot reuse admitted coefficient evidence")
            for binding in case.coefficientBindings:
                if (
                    exposure.targetShock == binding.targetShock
                    and exposure.sourceVariableId in binding.sourceVariableIds
                ):
                    raise ScenarioCompositionError("condition factor overlay cannot reuse coefficient bindings")
        patchHash = _controlPatchHash(patch)
        overlayFactorId = (
            "conditionOverlay__"
            f"{_safeControlIdPart(row.caseId)}__"
            f"{_safeControlIdPart(row.targetId)}__"
            f"step{row.step}__"
            f"{patchHash[:12]}"
        )
        deltaValue = float(patch.value) - _meanControlValue(row)
        patchedPathSet = addDriverPathConditionFactorOverlay(
            case.pathSet,
            baseFactorId=row.targetId,
            overlayFactorId=overlayFactorId,
            stepIndex=row.step,
            deltaValue=deltaValue,
            sourceRef=f"assumption://condition-overlay/{patchHash}",
            patchRef=f"{patch.patchRef}|controlPatch:{patchHash}",
            assumptionId=f"conditionOverlay:{patchHash}",
            claim=patch.claim,
            falsifier=patch.falsifier,
            reason=patch.reason,
        )
        overlayExposures = tuple(
            replace(
                exposure,
                exposureId=f"{exposure.exposureId}-condition-overlay-{patchHash[:12]}",
                sourceVariableId=overlayFactorId,
                evidenceKind="explicitAssumption",
                sourceRef=f"{patch.patchRef}|controlPatch:{patchHash}",
            )
            for exposure in matchingExposures
        )
        patchedCases[row.caseId] = replace(
            case,
            pathSet=patchedPathSet,
            exposures=(*case.exposures, *overlayExposures),
            scenarioPathPackageReceiptId="",
            operatingPathAdmissionReceiptId="",
            operatingPathCertificateId="",
        )
    return tuple(patchedCases[case.caseId] for case in cases)


def _patchAssumptionDeltaCases(
    cases: tuple[OperatingScenarioCase, ...],
    rows: tuple[ConditionalPlayControlRow, ...],
    patches: tuple[ConditionalPlayControlPatch, ...],
) -> tuple[OperatingScenarioCase, ...]:
    caseById = {case.caseId: case for case in cases}
    patchedCases = dict(caseById)
    for row, patch in zip(rows, patches, strict=True):
        case = patchedCases.get(row.caseId)
        if case is None or row.step < 0 or not row.explicitAssumptionId:
            raise ScenarioCompositionError("assumption delta patch target is invalid")
        patchHash = _controlPatchHash(patch)
        patchedPathSet = replaceDriverPathAssumptionStep(
            case.pathSet,
            factorId=row.targetId,
            stepIndex=row.step,
            value=patch.value,
            sourceRef=f"{patch.patchRef}|controlPatch:{patchHash}",
            reason=patch.reason,
        )
        patchedCases[row.caseId] = replace(case, pathSet=patchedPathSet)
    return tuple(patchedCases[case.caseId] for case in cases)


def _patchStrategyActionStrategies(
    strategies: tuple[StrategySpec, ...],
    rows: tuple[ConditionalPlayControlRow, ...],
    patches: tuple[ConditionalPlayControlPatch, ...],
) -> tuple[StrategySpec, ...]:
    strategyById = {strategy.strategyId: strategy for strategy in strategies}
    patchedStrategies = dict(strategyById)
    for row, patch in zip(rows, patches, strict=True):
        strategy = patchedStrategies.get(row.strategyId)
        if strategy is None or row.step < 0 or row.step >= len(strategy.actionsByStep):
            raise ScenarioCompositionError("strategy action patch target is invalid")
        actions = [dict(item) for item in strategy.actionsByStep]
        if row.targetId not in actions[row.step]:
            raise ScenarioCompositionError("strategy action patch target is missing")
        actions[row.step][row.targetId] = float(patch.value)
        patchHash = _controlPatchHash(patch)
        patchedStrategies[row.strategyId] = replace(
            strategy,
            actionsByStep=tuple(actions),
            refs=_dedupe((*strategy.refs, patch.patchRef, f"controlPatch:{patchHash}")),
        )
    return tuple(patchedStrategies[strategy.strategyId] for strategy in strategies)


def _patchCurrentStateInputs(
    inputs: OperatingWorldInputs,
    rows: tuple[ConditionalPlayControlRow, ...],
    patches: tuple[ConditionalPlayControlPatch, ...],
) -> OperatingWorldInputs:
    state = {str(key): float(value) for key, value in inputs.state.items()}
    patchRecords = []
    for row, patch in zip(rows, patches, strict=True):
        if row.step != -1 or not row.targetId or row.targetId not in state:
            raise ScenarioCompositionError("current state patch target is invalid")
        if patch.value < 0.0:
            raise ScenarioCompositionError("current state patch must be nonnegative")
        patchHash = _controlPatchHash(patch)
        state[row.targetId] = float(patch.value)
        patchRecords.append(
            {
                "controlId": patch.controlId,
                "rowHash": row.rowHash,
                "patchHash": patchHash,
                "patchRef": patch.patchRef,
                "targetId": row.targetId,
                "value": float(patch.value),
                "reason": patch.reason,
            }
        )
    stateManifestHash = canonicalPayloadHash(
        {
            "schemaVersion": "conditional-play-current-state-overlay-v1",
            "baseStateManifestHash": inputs.stateManifestHash,
            "baseInitialStateAdmissionReceiptId": inputs.initialStateAdmissionReceiptId,
            "state": tuple(sorted(state.items())),
            "patches": tuple(patchRecords),
        }
    )
    patchedPrimitives = tuple(
        replace(primitive, value=state[primitive.variableId]) if primitive.variableId in state else primitive
        for primitive in inputs.statePrimitiveContracts
    )
    patchRefs = tuple(ref for patch in patches for ref in (patch.patchRef, f"controlPatch:{_controlPatchHash(patch)}"))
    return replace(
        inputs,
        state=state,
        refs=_dedupe((*inputs.refs, f"stateManifest:{stateManifestHash}", *patchRefs)),
        warnings=_dedupe((*inputs.warnings, "currentStateOverlayUnadmitted")),
        stateCompilationContractHash="",
        stateManifestHash="",
        stateVintage=None,
        initialStateAdmissionReceiptId="",
        statePrimitiveContracts=patchedPrimitives,
    )


def _patchLawParameterCases(
    cases: tuple[OperatingScenarioCase, ...],
    rows: tuple[ConditionalPlayControlRow, ...],
    patches: tuple[ConditionalPlayControlPatch, ...],
) -> tuple[OperatingScenarioCase, ...]:
    caseById = {case.caseId: case for case in cases}
    patchedCases = dict(caseById)
    for row, patch in zip(rows, patches, strict=True):
        case = patchedCases.get(row.caseId)
        if case is None or row.step != -1:
            raise ScenarioCompositionError("law parameter patch target is invalid")
        exposureIndex = next(
            (
                index
                for index, exposure in enumerate(case.exposures)
                if f"lawParameter:{case.caseId}:{exposure.exposureId}:coefficient" == row.controlId
            ),
            -1,
        )
        if exposureIndex < 0:
            raise ScenarioCompositionError("law parameter patch target is missing")
        exposure = case.exposures[exposureIndex]
        if exposure.evidenceKind == "measuredAssociation" or _driverCoefficientAdmissionReceiptId(exposure.sourceRef):
            raise ScenarioCompositionError("admitted law parameter patch needs a separate de-admission route")
        for binding in case.coefficientBindings:
            if exposure.targetShock == binding.targetShock and exposure.sourceVariableId in binding.sourceVariableIds:
                raise ScenarioCompositionError("law parameter patch cannot reuse coefficient bindings")
        patchHash = _controlPatchHash(patch)
        patchedExposure = replace(
            exposure,
            coefficient=float(patch.value),
            evidenceKind="explicitAssumption",
            sourceRef=f"{patch.patchRef}|controlPatch:{patchHash}",
        )
        exposures = tuple(
            patchedExposure if index == exposureIndex else item for index, item in enumerate(case.exposures)
        )
        patchedCases[row.caseId] = replace(case, exposures=exposures)
    return tuple(patchedCases[case.caseId] for case in cases)


def _applyControlPatchBundle(
    *,
    inputs: OperatingWorldInputs,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    semanticPlane: str,
    rows: tuple[ConditionalPlayControlRow, ...],
    patches: tuple[ConditionalPlayControlPatch, ...],
) -> tuple[OperatingWorldInputs, tuple[OperatingScenarioCase, ...], tuple[StrategySpec, ...]]:
    patchedInputs = inputs
    patchedCases = tuple(cases)
    patchedStrategies = tuple(strategies)
    if semanticPlane == "assumptionDelta":
        patchedCases = _patchAssumptionDeltaCases(patchedCases, rows, patches)
    elif semanticPlane == "conditionFactor":
        patchedCases = _patchConditionFactorCases(patchedCases, rows, patches)
    elif semanticPlane == "currentState":
        patchedInputs = _patchCurrentStateInputs(patchedInputs, rows, patches)
    elif semanticPlane == "lawParameter":
        patchedCases = _patchLawParameterCases(patchedCases, rows, patches)
    elif semanticPlane == "strategyAction":
        patchedStrategies = _patchStrategyActionStrategies(patchedStrategies, rows, patches)
    else:
        raise ScenarioCompositionError(f"{semanticPlane} control patch requires a separate overlay route")
    return patchedInputs, patchedCases, patchedStrategies


def _caseLawInputHash(ledger: OneCompanyScenarioCaseLedger) -> str:
    return canonicalPayloadHash(
        {
            "schemaVersion": "conditional-scenario-law-inputs-v1",
            "caseId": ledger.caseId,
            "exposureLedgers": ledger.exposureLedgers,
            "coefficientAdmissionReceiptIds": ledger.coefficientAdmissionReceiptIds,
            "coefficientBindingHashes": ledger.coefficientBindingHashes,
        }
    )


def _caseParameterBoundaryHash(ledger: OneCompanyScenarioCaseLedger) -> str:
    return canonicalPayloadHash(
        {
            "schemaVersion": "conditional-scenario-parameter-boundary-v1",
            "caseId": ledger.caseId,
            "runParameterHash": ledger.parameterHash,
            "lawInputHash": _caseLawInputHash(ledger),
        }
    )


def _controlHashSnapshot(
    inputs: OperatingWorldInputs,
    experiment: "ConditionalScenarioExperiment",
) -> dict[str, str]:
    report = experiment.playReplayReport
    return {
        "initialState": canonicalPayloadHash(
            {
                "state": tuple(sorted((key, float(value)) for key, value in inputs.state.items())),
                "refs": inputs.refs,
                "stateManifestHash": inputs.stateManifestHash,
                "initialStateAdmissionReceiptId": inputs.initialStateAdmissionReceiptId,
            }
        ),
        "providerLaneLineageHash": canonicalPayloadHash(experiment.providerLaneLineageHashes),
        "providerObservationBatchReceiptIds": canonicalPayloadHash(experiment.providerObservationBatchReceiptIds),
        "priceSourceLegReceiptIds": canonicalPayloadHash(experiment.priceSourceLegReceiptIds),
        "derivedReturnReceiptIds": canonicalPayloadHash(experiment.derivedReturnReceiptIds),
        "pathHistoryInputHash": canonicalPayloadHash(experiment.pathHistoryInputHashes),
        "pathAssumptionStepHash": canonicalPayloadHash(experiment.pathAssumptionStepHashes),
        "pathAssumptionHash": canonicalPayloadHash(experiment.pathAssumptionHashes),
        "assumptionSetHash": canonicalPayloadHash(experiment.assumptionSetHashes),
        "caseLedgerHash": canonicalPayloadHash(experiment.caseLedgerHashes),
        "strategyContractHash": canonicalPayloadHash(experiment.strategyContractHashes),
        "strategySetHash": experiment.strategySetHash,
        "parameterHash": canonicalPayloadHash(
            tuple(_caseParameterBoundaryHash(ledger) for ledger in experiment.caseLedgers)
        ),
        "simulationSpecHash": experiment.simulationSpecHash,
        "resultSetHash": experiment.resultSetHash,
        "experimentHash": experiment.experimentHash,
        "tracePanelHash": report.tracePanelHash if report is not None else "",
        "playReplayHash": report.playReplayHash if report is not None else "",
        "controlPanelHash": report.controlPanelHash if report is not None else "",
        "controlSurfaceHash": report.controlSurfaceHash if report is not None else "",
        "rawSourceRefs": canonicalPayloadHash(experiment.rawSourceRefs),
        "revisedHistoryRefs": canonicalPayloadHash(experiment.revisedHistoryRefs),
    }


def _controlImpactRowPayload(row: ConditionalPlayControlImpactRow) -> dict:
    return {
        "controlId": row.controlId,
        "semanticPlane": row.semanticPlane,
        "expectedHashImpacts": row.expectedHashImpacts,
        "forbiddenHashImpacts": row.forbiddenHashImpacts,
        "changedHashImpacts": row.changedHashImpacts,
        "unchangedHashImpacts": row.unchangedHashImpacts,
        "missingExpectedHashImpacts": row.missingExpectedHashImpacts,
        "forbiddenHashViolations": row.forbiddenHashViolations,
    }


def _controlImpactRows(
    rows: tuple[ConditionalPlayControlRow, ...],
    beforeSnapshot: dict[str, str],
    afterSnapshot: dict[str, str],
) -> tuple[ConditionalPlayControlImpactRow, ...]:
    changed = tuple(
        sorted(
            key
            for key in set(beforeSnapshot) | set(afterSnapshot)
            if beforeSnapshot.get(key, "") != afterSnapshot.get(key, "")
        )
    )
    unchanged = tuple(sorted((set(beforeSnapshot) | set(afterSnapshot)) - set(changed)))
    impactRows = []
    for row in rows:
        missingExpected = tuple(key for key in row.expectedHashImpacts if key in beforeSnapshot and key not in changed)
        forbiddenViolations = tuple(key for key in row.forbiddenHashImpacts if key in beforeSnapshot and key in changed)
        draft = ConditionalPlayControlImpactRow(
            rowHash="",
            controlId=row.controlId,
            semanticPlane=row.semanticPlane,
            expectedHashImpacts=row.expectedHashImpacts,
            forbiddenHashImpacts=row.forbiddenHashImpacts,
            changedHashImpacts=changed,
            unchangedHashImpacts=unchanged,
            missingExpectedHashImpacts=missingExpected,
            forbiddenHashViolations=forbiddenViolations,
        )
        impactRows.append(replace(draft, rowHash=_rowHash("controlImpactRow", _controlImpactRowPayload(draft))))
    return tuple(impactRows)


def conditionalPlayControlExecutionPayload(report: ConditionalPlayControlExecutionReport) -> dict:
    """Build canonical payload for an internal conditional play control execution."""

    return {
        "schemaVersion": report.schemaVersion,
        "kind": report.kind,
        "patchSetHash": report.patchSetHash,
        "baseExperimentHash": report.baseExperimentHash,
        "patchedExperimentHash": report.patchedExperimentHash,
        "basePlayReplayHash": report.basePlayReplayHash,
        "patchedPlayReplayHash": report.patchedPlayReplayHash,
        "baseControlSurfaceHash": report.baseControlSurfaceHash,
        "patchedControlSurfaceHash": report.patchedControlSurfaceHash,
        "changedControlIds": report.changedControlIds,
        "semanticPlane": report.semanticPlane,
        "impactRows": report.impactRows,
        "blockedReasons": report.blockedReasons,
        "warnings": report.warnings,
    }


def conditionalPlayControlExecutionSubjectHash(report: ConditionalPlayControlExecutionReport) -> str:
    """Return the content hash for a conditional play control execution report."""

    return canonicalPayloadHash(conditionalPlayControlExecutionPayload(report))


def _executeValidatedControlPatchGroup(
    entityId: str,
    inputs: OperatingWorldInputs,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    baseExperiment: "ConditionalScenarioExperiment",
    controlSurface: ConditionalPlayControlSurface,
    rows: tuple[ConditionalPlayControlRow, ...],
    patches: tuple[ConditionalPlayControlPatch, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    objectiveIndex: int = 0,
    traceLimit: int | None = None,
) -> _ConditionalPlayPatchedBundle:
    semanticPlane = rows[0].semanticPlane
    patchSetHash = _controlPatchSetHash(
        baseExperiment=baseExperiment,
        controlSurface=controlSurface,
        patches=patches,
    )
    patchedInputs, patchedCases, patchedStrategies = _applyControlPatchBundle(
        inputs=inputs,
        cases=cases,
        strategies=strategies,
        semanticPlane=semanticPlane,
        rows=rows,
        patches=patches,
    )
    patchedExperiment = runConditionalScenarioExperiment(
        entityId,
        patchedInputs,
        patchedCases,
        patchedStrategies,
        debtLimit=debtLimit,
        maxFinancing=maxFinancing,
        maxInvestment=maxInvestment,
        objectiveIndex=objectiveIndex,
        traceLimit=traceLimit,
    )
    baseReport = baseExperiment.playReplayReport
    patchedReport = patchedExperiment.playReplayReport
    if baseReport is None:
        raise ScenarioCompositionError("conditional play control execution needs parent replay")
    if (
        patchedReport is None
        or patchedExperiment.decisionStatus != "conditionalOnly"
        or patchedExperiment.recommendation is not None
        or patchedReport.recommendation is not None
        or patchedReport.traceRetention != "full"
    ):
        raise ScenarioCompositionError("control patch replay cannot promote a recommendation or drop full trace")
    impactRows = _controlImpactRows(
        rows,
        _controlHashSnapshot(inputs, baseExperiment),
        _controlHashSnapshot(patchedInputs, patchedExperiment),
    )
    missingExpected = tuple(reason for impact in impactRows for reason in impact.missingExpectedHashImpacts)
    forbiddenViolations = tuple(reason for impact in impactRows for reason in impact.forbiddenHashViolations)
    if missingExpected:
        raise ScenarioCompositionError(f"control patch missing expected hash impact: {missingExpected[0]}")
    if forbiddenViolations:
        raise ScenarioCompositionError(f"control patch changed forbidden hash: {forbiddenViolations[0]}")
    draft = ConditionalPlayControlExecutionReport(
        executionHash="",
        schemaVersion=CONDITIONAL_PLAY_CONTROL_EXECUTION_VERSION,
        kind=CONDITIONAL_PLAY_CONTROL_EXECUTION_KIND,
        patchSetHash=patchSetHash,
        baseExperimentHash=baseExperiment.experimentHash,
        patchedExperimentHash=patchedExperiment.experimentHash,
        basePlayReplayHash=baseReport.playReplayHash,
        patchedPlayReplayHash=patchedReport.playReplayHash,
        baseControlSurfaceHash=controlSurface.surfaceHash,
        patchedControlSurfaceHash=patchedReport.controlSurfaceHash,
        changedControlIds=tuple(patch.controlId for patch in patches),
        semanticPlane=semanticPlane,
        impactRows=impactRows,
        patchedExperiment=patchedExperiment,
        blockedReasons=patchedExperiment.blockedReasons,
        warnings=patchedExperiment.warnings,
    )
    report = replace(draft, executionHash=conditionalPlayControlExecutionSubjectHash(draft))
    return _ConditionalPlayPatchedBundle(
        inputs=patchedInputs,
        cases=patchedCases,
        strategies=patchedStrategies,
        report=report,
    )


def executeConditionalPlayControlPatch(
    entityId: str,
    inputs: OperatingWorldInputs,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    baseExperiment: "ConditionalScenarioExperiment",
    patches: tuple[ConditionalPlayControlPatch, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    objectiveIndex: int = 0,
    traceLimit: int | None = None,
) -> ConditionalPlayControlExecutionReport:
    """Replay a conditional experiment after applying safe control patches.

    Args:
        entityId: Company or security identifier for the experiment subject.
        inputs: Original operating state bundle used by the parent experiment.
        cases: Original scenario cases used by the parent experiment.
        strategies: Original strategies used by the parent experiment.
        baseExperiment: Parent conditional experiment with a play replay report.
        patches: Control patches against the parent control surface.
        debtLimit: Hard debt constraint passed to the operating world.
        maxFinancing: Per-step borrow and repay bound.
        maxInvestment: Per-step capacity investment bound.
        objectiveIndex: Objective score column used for scalar sweep summaries.
        traceLimit: Optional retained trace cap per case.

    Returns:
        ``ConditionalPlayControlExecutionReport`` containing the patched
        experiment and hash impact audit.

    Raises:
        ScenarioCompositionError: If a patch is stale, crosses semantic planes,
        targets observed history, or violates expected hash boundaries.

    Example:
        ``report = executeConditionalPlayControlPatch("005930", inputs, cases, strategies, experiment, patches, debtLimit=1000, maxFinancing=200, maxInvestment=200)``
    """

    baseReport = baseExperiment.playReplayReport
    if baseReport is None:
        raise ScenarioCompositionError("conditional play control execution needs parent replay")
    controlSurface = baseReport.controlSurface
    patchTuple = tuple(patches)
    rows = _validateControlPatches(controlSurface, patchTuple)
    bundle = _executeValidatedControlPatchGroup(
        entityId,
        inputs,
        tuple(cases),
        tuple(strategies),
        baseExperiment,
        controlSurface,
        rows,
        patchTuple,
        debtLimit=debtLimit,
        maxFinancing=maxFinancing,
        maxInvestment=maxInvestment,
        objectiveIndex=objectiveIndex,
        traceLimit=traceLimit,
    )
    return bundle.report


def _controlRebaseRowPayload(row: ConditionalPlayControlRebaseRow) -> dict:
    return {
        "controlId": row.controlId,
        "semanticPlane": row.semanticPlane,
        "originalPatchHash": row.originalPatchHash,
        "rebasedPatchHash": row.rebasedPatchHash,
        "originalSurfaceHash": row.originalSurfaceHash,
        "originalRowHash": row.originalRowHash,
        "stageSurfaceHash": row.stageSurfaceHash,
        "stageRowHash": row.stageRowHash,
        "rebaseStatus": row.rebaseStatus,
    }


def _controlRebaseRow(
    *,
    originalPatch: ConditionalPlayControlPatch,
    rebasedPatch: ConditionalPlayControlPatch,
    baseRow: ConditionalPlayControlRow,
    stageRow: ConditionalPlayControlRow,
    stageSurface: ConditionalPlayControlSurface,
) -> ConditionalPlayControlRebaseRow:
    statusParts = []
    if originalPatch.baseSurfaceHash != stageSurface.surfaceHash:
        statusParts.append("surfaceRebased")
    if originalPatch.baseRowHash != stageRow.rowHash:
        statusParts.append("rowRebased")
    status = "+".join(statusParts) if statusParts else "direct"
    draft = ConditionalPlayControlRebaseRow(
        rowHash="",
        controlId=originalPatch.controlId,
        semanticPlane=baseRow.semanticPlane,
        originalPatchHash=_controlPatchHash(originalPatch),
        rebasedPatchHash=_controlPatchHash(rebasedPatch),
        originalSurfaceHash=originalPatch.baseSurfaceHash,
        originalRowHash=originalPatch.baseRowHash,
        stageSurfaceHash=stageSurface.surfaceHash,
        stageRowHash=stageRow.rowHash,
        rebaseStatus=status,
    )
    return replace(draft, rowHash=_rowHash("controlRebaseRow", _controlRebaseRowPayload(draft)))


_CONTROL_REBASE_IDENTITY_FIELDS = (
    "controlId",
    "semanticPlane",
    "controlKind",
    "adjustmentMode",
    "scope",
    "caseId",
    "strategyId",
    "step",
    "targetId",
    "sourceVariableId",
    "targetVariableId",
    "unit",
    "frequency",
    "timing",
    "transformId",
    "expectedHashImpacts",
    "forbiddenHashImpacts",
)


def _assertControlRebaseCompatible(
    baseRow: ConditionalPlayControlRow,
    stageRow: ConditionalPlayControlRow,
) -> None:
    for fieldName in _CONTROL_REBASE_IDENTITY_FIELDS:
        if getattr(baseRow, fieldName) != getattr(stageRow, fieldName):
            raise ScenarioCompositionError("staged control patch target drifted")
    if stageRow.adjustabilityStatus.startswith("locked"):
        raise ScenarioCompositionError("locked conditional play control cannot be patched")


def _rejectUnsafeControlPatchRef(patchRef: str) -> None:
    unsafePrefixes = (
        *_STRUCTURED_PROVIDER_LINEAGE_REF_PREFIXES,
        "pathAdmission:",
        "pathSetAdmission:",
        "driverCoefficientAdmission:",
        "initialStateAdmission:",
        "stateReceipt:",
        "verifiedStateReceipt:",
    )
    if patchRef.startswith(unsafePrefixes):
        raise ScenarioCompositionError("control patch provenance cannot mimic admitted lineage")


def _validateScenarioDeckInteractions(rows: tuple[ConditionalPlayControlRow, ...]) -> None:
    conditionRows = tuple(row for row in rows if row.semanticPlane == "conditionFactor")
    lawRows = tuple(row for row in rows if row.semanticPlane == "lawParameter")
    for conditionRow in conditionRows:
        for lawRow in lawRows:
            if conditionRow.caseId == lawRow.caseId and conditionRow.targetId == lawRow.sourceVariableId:
                raise ScenarioCompositionError("scenario deck cannot mix condition and law patches on one exposure")


def _deckSourceSealHash(experiment: "ConditionalScenarioExperiment") -> str:
    return canonicalPayloadHash(
        {
            "providerLaneLineageHashes": experiment.providerLaneLineageHashes,
            "providerObservationBatchReceiptIds": experiment.providerObservationBatchReceiptIds,
            "providerObservationBatchIds": experiment.providerObservationBatchIds,
            "providerObservationBatchSourceReceiptIds": experiment.providerObservationBatchSourceReceiptIds,
            "priceSourceLegReceiptIds": experiment.priceSourceLegReceiptIds,
            "derivedReturnReceiptIds": experiment.derivedReturnReceiptIds,
            "adjustmentPolicyHashes": experiment.adjustmentPolicyHashes,
            "normalizationContractHashes": experiment.normalizationContractHashes,
            "returnTransformHashes": experiment.returnTransformHashes,
            "rawSourceRefs": experiment.rawSourceRefs,
            "revisedHistoryRefs": experiment.revisedHistoryRefs,
            "pathHistoryInputHashes": experiment.pathHistoryInputHashes,
            "basePathAdmission": tuple(
                (
                    ledger.caseId,
                    ledger.basePathAdmissionReceiptId,
                    ledger.basePathAdmissionContentHash,
                    ledger.basePathAdmissionSubjectHash,
                    ledger.basePathValidationStatus,
                    ledger.basePathMaxAdmittedStep,
                )
                for ledger in experiment.caseLedgers
            ),
        }
    )


def _strategyDeltaPayload(row: ConditionalPlayStrategyDeltaRow) -> dict:
    return {
        "strategyId": row.strategyId,
        "baseStrategyContractHash": row.baseStrategyContractHash,
        "finalStrategyContractHash": row.finalStrategyContractHash,
        "baseSummaryHash": row.baseSummaryHash,
        "finalSummaryHash": row.finalSummaryHash,
        "baseStrategyCellsHash": row.baseStrategyCellsHash,
        "finalStrategyCellsHash": row.finalStrategyCellsHash,
        "objectiveIndex": row.objectiveIndex,
        "baseScenarioCount": row.baseScenarioCount,
        "finalScenarioCount": row.finalScenarioCount,
        "baseStrategyCount": row.baseStrategyCount,
        "finalStrategyCount": row.finalStrategyCount,
        "baseCellCount": row.baseCellCount,
        "finalCellCount": row.finalCellCount,
        "baseScoreMedian": row.baseScoreMedian,
        "finalScoreMedian": row.finalScoreMedian,
        "scoreMedianDelta": row.scoreMedianDelta,
        "baseRegretWorst": row.baseRegretWorst,
        "finalRegretWorst": row.finalRegretWorst,
        "regretWorstDelta": row.regretWorstDelta,
        "baseLeaderFrequency": row.baseLeaderFrequency,
        "finalLeaderFrequency": row.finalLeaderFrequency,
        "leaderFrequencyDelta": row.leaderFrequencyDelta,
        "baseBreachCount": row.baseBreachCount,
        "finalBreachCount": row.finalBreachCount,
        "breachCountDelta": row.breachCountDelta,
        "changed": row.changed,
    }


def _caseLeaderDeltaPayload(row: ConditionalPlayCaseLeaderDeltaRow) -> dict:
    return {
        "caseId": row.caseId,
        "label": row.label,
        "baseCaseLedgerHash": row.baseCaseLedgerHash,
        "finalCaseLedgerHash": row.finalCaseLedgerHash,
        "baseFragilityHash": row.baseFragilityHash,
        "finalFragilityHash": row.finalFragilityHash,
        "baseCaseCellsHash": row.baseCaseCellsHash,
        "finalCaseCellsHash": row.finalCaseCellsHash,
        "baseResultHash": row.baseResultHash,
        "finalResultHash": row.finalResultHash,
        "baseRunHash": row.baseRunHash,
        "finalRunHash": row.finalRunHash,
        "basePathSetHash": row.basePathSetHash,
        "finalPathSetHash": row.finalPathSetHash,
        "basePathAssumptionHash": row.basePathAssumptionHash,
        "finalPathAssumptionHash": row.finalPathAssumptionHash,
        "baseScenarioPathPackageHash": row.baseScenarioPathPackageHash,
        "finalScenarioPathPackageHash": row.finalScenarioPathPackageHash,
        "baseLeaderStrategies": row.baseLeaderStrategies,
        "finalLeaderStrategies": row.finalLeaderStrategies,
        "baseRunnerUpStrategies": row.baseRunnerUpStrategies,
        "finalRunnerUpStrategies": row.finalRunnerUpStrategies,
        "baseBreachStrategies": row.baseBreachStrategies,
        "finalBreachStrategies": row.finalBreachStrategies,
        "leaderChanged": row.leaderChanged,
        "changed": row.changed,
        "baseLeaderMargin": row.baseLeaderMargin,
        "finalLeaderMargin": row.finalLeaderMargin,
        "leaderMarginDelta": row.leaderMarginDelta,
        "baseScoreSpread": row.baseScoreSpread,
        "finalScoreSpread": row.finalScoreSpread,
        "scoreSpreadDelta": row.scoreSpreadDelta,
        "baseAssumptionSetHash": row.baseAssumptionSetHash,
        "finalAssumptionSetHash": row.finalAssumptionSetHash,
    }


def _strategyDeltaRows(
    baseExperiment: "ConditionalScenarioExperiment",
    finalExperiment: "ConditionalScenarioExperiment",
) -> tuple[ConditionalPlayStrategyDeltaRow, ...]:
    if baseExperiment.strategyIds != finalExperiment.strategyIds:
        raise ScenarioCompositionError("strategy delta requires stable strategy ids")
    baseById = {summary.strategyId: summary for summary in baseExperiment.strategySummaries}
    finalById = {summary.strategyId: summary for summary in finalExperiment.strategySummaries}
    if set(baseById) != set(finalById) or set(baseById) != set(baseExperiment.strategyIds):
        raise ScenarioCompositionError("strategy delta requires complete strategy summaries")
    baseContractHashById = dict(zip(baseExperiment.strategyIds, baseExperiment.strategyContractHashes, strict=True))
    finalContractHashById = dict(zip(finalExperiment.strategyIds, finalExperiment.strategyContractHashes, strict=True))
    rows = []
    for strategyId in finalExperiment.strategyIds:
        base = baseById[strategyId]
        final = finalById[strategyId]
        baseSummaryHash = canonicalPayloadHash(base)
        finalSummaryHash = canonicalPayloadHash(final)
        baseCells = tuple(cell for cell in baseExperiment.cells if cell.strategyId == strategyId)
        finalCells = tuple(cell for cell in finalExperiment.cells if cell.strategyId == strategyId)
        baseStrategyCellsHash = canonicalPayloadHash(baseCells)
        finalStrategyCellsHash = canonicalPayloadHash(finalCells)
        baseContractHash = baseContractHashById[strategyId]
        finalContractHash = finalContractHashById[strategyId]
        changed = (
            baseSummaryHash != finalSummaryHash
            or baseStrategyCellsHash != finalStrategyCellsHash
            or baseContractHash != finalContractHash
        )
        draft = ConditionalPlayStrategyDeltaRow(
            rowHash="",
            strategyId=strategyId,
            baseStrategyContractHash=baseContractHash,
            finalStrategyContractHash=finalContractHash,
            baseSummaryHash=baseSummaryHash,
            finalSummaryHash=finalSummaryHash,
            baseStrategyCellsHash=baseStrategyCellsHash,
            finalStrategyCellsHash=finalStrategyCellsHash,
            objectiveIndex=finalExperiment.objectiveIndex,
            baseScenarioCount=baseExperiment.scenarioCount,
            finalScenarioCount=finalExperiment.scenarioCount,
            baseStrategyCount=baseExperiment.strategyCount,
            finalStrategyCount=finalExperiment.strategyCount,
            baseCellCount=baseExperiment.cellCount,
            finalCellCount=finalExperiment.cellCount,
            baseScoreMedian=base.scoreMedian,
            finalScoreMedian=final.scoreMedian,
            scoreMedianDelta=final.scoreMedian - base.scoreMedian,
            baseRegretWorst=base.regretWorst,
            finalRegretWorst=final.regretWorst,
            regretWorstDelta=final.regretWorst - base.regretWorst,
            baseLeaderFrequency=base.leaderFrequency,
            finalLeaderFrequency=final.leaderFrequency,
            leaderFrequencyDelta=final.leaderFrequency - base.leaderFrequency,
            baseBreachCount=base.breachCount,
            finalBreachCount=final.breachCount,
            breachCountDelta=final.breachCount - base.breachCount,
            changed=changed,
        )
        rows.append(replace(draft, rowHash=_rowHash("strategyDeltaRow", _strategyDeltaPayload(draft))))
    return tuple(rows)


def _caseLeaderDeltaRows(
    baseExperiment: "ConditionalScenarioExperiment",
    finalExperiment: "ConditionalScenarioExperiment",
) -> tuple[ConditionalPlayCaseLeaderDeltaRow, ...]:
    if baseExperiment.assumptionSetIds != finalExperiment.assumptionSetIds:
        raise ScenarioCompositionError("case leader delta requires stable case ids")
    baseLedgerById = {ledger.caseId: ledger for ledger in baseExperiment.caseLedgers}
    finalLedgerById = {ledger.caseId: ledger for ledger in finalExperiment.caseLedgers}
    baseFragilityById = {row.caseId: row for row in baseExperiment.fragilityCells}
    finalFragilityById = {row.caseId: row for row in finalExperiment.fragilityCells}
    if (
        set(baseLedgerById) != set(finalLedgerById)
        or set(baseLedgerById) != set(baseExperiment.assumptionSetIds)
        or set(baseFragilityById) != set(finalFragilityById)
        or set(baseFragilityById) != set(baseExperiment.assumptionSetIds)
    ):
        raise ScenarioCompositionError("case leader delta requires complete case rows")
    baseCaseLedgerHashById = dict(zip(baseExperiment.assumptionSetIds, baseExperiment.caseLedgerHashes, strict=True))
    finalCaseLedgerHashById = dict(zip(finalExperiment.assumptionSetIds, finalExperiment.caseLedgerHashes, strict=True))
    baseAssumptionSetHashById = dict(
        zip(baseExperiment.assumptionSetIds, baseExperiment.assumptionSetHashes, strict=True)
    )
    finalAssumptionSetHashById = dict(
        zip(finalExperiment.assumptionSetIds, finalExperiment.assumptionSetHashes, strict=True)
    )
    rows = []
    for caseId in finalExperiment.assumptionSetIds:
        baseLedger = baseLedgerById[caseId]
        finalLedger = finalLedgerById[caseId]
        baseFragility = baseFragilityById[caseId]
        finalFragility = finalFragilityById[caseId]
        baseCaseCells = tuple(cell for cell in baseExperiment.cells if cell.caseId == caseId)
        finalCaseCells = tuple(cell for cell in finalExperiment.cells if cell.caseId == caseId)
        baseCaseCellsHash = canonicalPayloadHash(baseCaseCells)
        finalCaseCellsHash = canonicalPayloadHash(finalCaseCells)
        baseFragilityHash = canonicalPayloadHash(baseFragility)
        finalFragilityHash = canonicalPayloadHash(finalFragility)
        baseCaseLedgerHash = baseCaseLedgerHashById[caseId]
        finalCaseLedgerHash = finalCaseLedgerHashById[caseId]
        changed = (
            baseCaseLedgerHash != finalCaseLedgerHash
            or baseFragilityHash != finalFragilityHash
            or baseCaseCellsHash != finalCaseCellsHash
        )
        draft = ConditionalPlayCaseLeaderDeltaRow(
            rowHash="",
            caseId=caseId,
            label=finalLedger.label,
            baseCaseLedgerHash=baseCaseLedgerHash,
            finalCaseLedgerHash=finalCaseLedgerHash,
            baseFragilityHash=baseFragilityHash,
            finalFragilityHash=finalFragilityHash,
            baseCaseCellsHash=baseCaseCellsHash,
            finalCaseCellsHash=finalCaseCellsHash,
            baseResultHash=baseLedger.resultHash,
            finalResultHash=finalLedger.resultHash,
            baseRunHash=baseLedger.runHash,
            finalRunHash=finalLedger.runHash,
            basePathSetHash=baseLedger.pathSetHash,
            finalPathSetHash=finalLedger.pathSetHash,
            basePathAssumptionHash=baseLedger.pathAssumptionHash,
            finalPathAssumptionHash=finalLedger.pathAssumptionHash,
            baseScenarioPathPackageHash=baseLedger.scenarioPathPackageHash,
            finalScenarioPathPackageHash=finalLedger.scenarioPathPackageHash,
            baseLeaderStrategies=baseLedger.scoreLeaderStrategies,
            finalLeaderStrategies=finalLedger.scoreLeaderStrategies,
            baseRunnerUpStrategies=baseFragility.runnerUpStrategies,
            finalRunnerUpStrategies=finalFragility.runnerUpStrategies,
            baseBreachStrategies=baseFragility.breachStrategies,
            finalBreachStrategies=finalFragility.breachStrategies,
            leaderChanged=baseLedger.scoreLeaderStrategies != finalLedger.scoreLeaderStrategies,
            changed=changed,
            baseLeaderMargin=baseFragility.leaderMargin,
            finalLeaderMargin=finalFragility.leaderMargin,
            leaderMarginDelta=finalFragility.leaderMargin - baseFragility.leaderMargin,
            baseScoreSpread=baseFragility.scoreSpread,
            finalScoreSpread=finalFragility.scoreSpread,
            scoreSpreadDelta=finalFragility.scoreSpread - baseFragility.scoreSpread,
            baseAssumptionSetHash=baseAssumptionSetHashById[caseId],
            finalAssumptionSetHash=finalAssumptionSetHashById[caseId],
        )
        rows.append(replace(draft, rowHash=_rowHash("caseLeaderDeltaRow", _caseLeaderDeltaPayload(draft))))
    return tuple(rows)


def _conditionalPlayDeckLineageParentReceiptIds(
    experiment: "ConditionalScenarioExperiment",
) -> tuple[str, ...]:
    coefficientReceipts = tuple(
        receiptId for ledger in experiment.caseLedgers for receiptId in ledger.coefficientAdmissionReceiptIds
    )
    return _dedupe(
        (
            experiment.experimentReceiptId,
            *_experimentInitialStateAdmissionReceiptIds(experiment),
            *_experimentScenarioPathPackageReceiptIds(experiment),
            *coefficientReceipts,
            *experiment.providerObservationBatchReceiptIds,
            *experiment.providerObservationBatchSourceReceiptIds,
            *experiment.priceSourceLegReceiptIds,
            *experiment.derivedReturnReceiptIds,
        )
    )


def conditionalPlayScenarioDeckParentReceiptIds(
    report: ConditionalPlayScenarioDeckReport,
) -> tuple[str, ...]:
    """Return receipt parents required to document a conditional play scenario deck."""

    stageParents = tuple(
        receiptId
        for stage in report.stageReports
        for receiptId in _conditionalPlayDeckLineageParentReceiptIds(stage.patchedExperiment)
    )
    return _dedupe(
        (
            report.baseExperimentReceiptId,
            report.finalExperimentReceiptId,
            report.finalExperiment.experimentReceiptId,
            *report.baseLineageParentReceiptIds,
            *report.finalLineageParentReceiptIds,
            *stageParents,
            *_conditionalPlayDeckLineageParentReceiptIds(report.finalExperiment),
        )
    )


def _conditionalPlayScenarioDeckBlockedReasons(
    experiment: "ConditionalScenarioExperiment",
) -> tuple[str, ...]:
    reasons = [
        "conditionalPlayScenarioDeckDocumentedOnly",
        "scenarioDeckReceiptNotPolicyCertificate",
    ]
    reasons.extend(experiment.blockedReasons)
    if experiment.recommendation is None:
        reasons.append("automaticRecommendationDisabled")
    if any(ledger.scoreLeaderStrategies for ledger in experiment.caseLedgers):
        reasons.append("scoreLeaderNotRecommendation")
    return _dedupe(tuple(reasons))


def conditionalPlayScenarioDeckPayload(report: ConditionalPlayScenarioDeckReport) -> dict:
    """Build canonical payload for a multi-plane conditional scenario deck."""

    parentReceiptIds = conditionalPlayScenarioDeckParentReceiptIds(report)
    return {
        "schemaVersion": report.schemaVersion,
        "kind": report.kind,
        "status": "documented",
        "recommendationStatus": "disabled",
        "semanticPlaneOrder": CONDITIONAL_PLAY_SCENARIO_DECK_PLANE_ORDER,
        "baseExperimentHash": report.baseExperimentHash,
        "finalExperimentHash": report.finalExperimentHash,
        "basePlayReplayHash": report.basePlayReplayHash,
        "finalPlayReplayHash": report.finalPlayReplayHash,
        "baseControlSurfaceHash": report.baseControlSurfaceHash,
        "finalControlSurfaceHash": report.finalControlSurfaceHash,
        "baseSimulationSpecHash": report.baseSimulationSpecHash,
        "finalSimulationSpecHash": report.finalSimulationSpecHash,
        "baseResultSetHash": report.baseResultSetHash,
        "finalResultSetHash": report.finalResultSetHash,
        "baseStrategySetHash": report.baseStrategySetHash,
        "finalStrategySetHash": report.finalStrategySetHash,
        "baseSourceSealHash": report.baseSourceSealHash,
        "finalSourceSealHash": report.finalSourceSealHash,
        "sourceSealPreserved": report.baseSourceSealHash == report.finalSourceSealHash,
        "experimentReceipts": {
            "baseExperimentReceiptId": report.baseExperimentReceiptId,
            "baseExperimentReceiptSubjectHash": report.baseExperimentReceiptSubjectHash,
            "finalExperimentReceiptId": report.finalExperimentReceiptId or report.finalExperiment.experimentReceiptId,
            "finalExperimentReceiptSubjectHash": (
                report.finalExperimentReceiptSubjectHash or report.finalExperiment.experimentReceiptSubjectHash
            ),
        },
        "lineageParents": {
            "baseLineageParentReceiptIds": report.baseLineageParentReceiptIds,
            "finalLineageParentReceiptIds": report.finalLineageParentReceiptIds,
            "parentReceiptIds": parentReceiptIds,
        },
        "rules": {
            "ruleId": CONDITIONAL_PLAY_SCENARIO_DECK_RULE_ID,
            "ruleVersion": CONDITIONAL_PLAY_SCENARIO_DECK_RULE_VERSION,
            "ruleHash": CONDITIONAL_PLAY_SCENARIO_DECK_RULE_HASH,
        },
        "stageChainHash": report.stageChainHash,
        "changedControlIds": report.changedControlIds,
        "semanticPlanes": report.semanticPlanes,
        "stageExecutionHashes": report.stageExecutionHashes,
        "stagePatchSetHashes": tuple(stage.patchSetHash for stage in report.stageReports),
        "stageBaseExperimentHashes": tuple(stage.baseExperimentHash for stage in report.stageReports),
        "stagePatchedExperimentHashes": tuple(stage.patchedExperimentHash for stage in report.stageReports),
        "rebaseRows": report.rebaseRows,
        "strategyDeltaRows": report.strategyDeltaRows,
        "caseLeaderDeltaRows": report.caseLeaderDeltaRows,
        "strategyDeltaHash": canonicalPayloadHash(report.strategyDeltaRows),
        "caseLeaderDeltaHash": canonicalPayloadHash(report.caseLeaderDeltaRows),
        "blockedReasons": report.blockedReasons,
        "warnings": report.warnings,
        "parentReceiptIds": parentReceiptIds,
    }


def conditionalPlayScenarioDeckSubjectHash(report: ConditionalPlayScenarioDeckReport) -> str:
    """Return the content hash for a multi-plane conditional scenario deck."""

    return canonicalPayloadHash(conditionalPlayScenarioDeckPayload(report))


def conditionalPlayScenarioDeckArtifact(report: ConditionalPlayScenarioDeckReport) -> bytes:
    """Return canonical bytes for a documented multi-plane conditional scenario deck."""

    return canonicalPayloadBytes(conditionalPlayScenarioDeckPayload(report))


def validateConditionalPlayScenarioDeckReceipt(
    report: ConditionalPlayScenarioDeckReport,
    receiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> "AdmissionReceipt":
    """Verify a documented conditional play scenario deck receipt."""

    if not _validDigest(receiptId):
        raise ScenarioCompositionError("conditional play scenario deck receipt identifier is invalid")
    subjectHash = conditionalPlayScenarioDeckSubjectHash(report)
    expectedParents = conditionalPlayScenarioDeckParentReceiptIds(report)
    if not expectedParents:
        raise ScenarioCompositionError("conditional play scenario deck receipt needs lineage parents")
    if report.deckHash != subjectHash:
        raise ScenarioCompositionError("conditional play scenario deck hash mismatch")
    if (
        report.schemaVersion != CONDITIONAL_PLAY_SCENARIO_DECK_VERSION
        or report.kind != CONDITIONAL_PLAY_SCENARIO_DECK_KIND
    ):
        raise ScenarioCompositionError("conditional play scenario deck contract mismatch")
    if report.baseSourceSealHash != report.finalSourceSealHash:
        raise ScenarioCompositionError("conditional play scenario deck source seal mismatch")
    if report.finalExperimentHash != report.finalExperiment.experimentHash:
        raise ScenarioCompositionError("conditional play scenario deck final experiment mismatch")
    if report.stageExecutionHashes != tuple(stage.executionHash for stage in report.stageReports):
        raise ScenarioCompositionError("conditional play scenario deck stage hash mismatch")
    if report.semanticPlanes != tuple(stage.semanticPlane for stage in report.stageReports):
        raise ScenarioCompositionError("conditional play scenario deck stage plane mismatch")
    if (
        report.finalExperiment.recommendation is not None
        or report.finalExperiment.decisionStatus != "conditionalOnly"
        or report.finalExperiment.recommendationCeiling != "conditionalOnly"
    ):
        raise ScenarioCompositionError("conditional play scenario deck cannot carry recommendation")
    if any(ledger.policyEvaluationCertificateId for ledger in report.finalExperiment.caseLedgers):
        raise ScenarioCompositionError("conditional play scenario deck cannot carry policy certificate ids")
    if any(ledger.pathAdmissionReceiptId for ledger in report.finalExperiment.caseLedgers):
        raise ScenarioCompositionError("conditional play scenario deck cannot carry path admission ids")
    requiredReasons = {
        "conditionalPlayScenarioDeckDocumentedOnly",
        "scenarioDeckReceiptNotPolicyCertificate",
        "conditionalExperimentNotPolicyRecommendation",
        "scoreLeaderNotRecommendation",
    }
    if not requiredReasons.issubset(set(report.blockedReasons)):
        raise ScenarioCompositionError("conditional play scenario deck needs recommendation blockers")
    try:
        from dartlab.simulate.admissionRegistry import artifactPath

        receipt = admissionVerifier.verify(
            receiptId,
            expectedSubjectHash=subjectHash,
            expectedKind=CONDITIONAL_PLAY_SCENARIO_DECK_KIND,
        )
        parentReceipts = tuple(admissionVerifier.verify(parentId) for parentId in receipt.parentReceiptIds)
        artifactBytes = artifactPath(admissionVerifier.artifactRoot, subjectHash).read_bytes()
    except (OSError, RuntimeError, ValueError) as error:
        raise ScenarioCompositionError(
            f"conditional play scenario deck receipt verification failed: {error}"
        ) from error
    if artifactBytes != conditionalPlayScenarioDeckArtifact(report):
        raise ScenarioCompositionError("conditional play scenario deck artifact content mismatch")
    if receipt.parentReceiptIds != expectedParents:
        raise ScenarioCompositionError("conditional play scenario deck receipt parent mismatch")
    if (
        receipt.status != "documented"
        or receipt.artifactHash != subjectHash
        or receipt.ruleId != CONDITIONAL_PLAY_SCENARIO_DECK_RULE_ID
        or receipt.ruleVersion != CONDITIONAL_PLAY_SCENARIO_DECK_RULE_VERSION
        or receipt.ruleHash != CONDITIONAL_PLAY_SCENARIO_DECK_RULE_HASH
        or receipt.revisionPolicy != "explicitAssumption"
        or receipt.coverage != "synthetic"
        or receipt.frequency != "scenario"
        or receipt.stepSpan != 1
        or receipt.maxAdmittedStep != 0
    ):
        raise ScenarioCompositionError("conditional play scenario deck receipt contract mismatch")
    if any(parent.kind in {"policyEvaluation", "policyEpisodeBatch"} for parent in parentReceipts):
        raise ScenarioCompositionError("conditional play scenario deck cannot depend on policy evaluation receipts")
    if any(parent.status == "policyAdmitted" for parent in parentReceipts):
        raise ScenarioCompositionError("conditional play scenario deck cannot inherit policy admitted parents")
    return receipt


def bindConditionalPlayScenarioDeckReceipt(
    report: ConditionalPlayScenarioDeckReport,
    receiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> ConditionalPlayScenarioDeckReport:
    """Attach a verified documented receipt to a conditional play scenario deck."""

    receipt = validateConditionalPlayScenarioDeckReceipt(report, receiptId, admissionVerifier)
    return replace(
        report,
        deckReceiptSubjectHash=conditionalPlayScenarioDeckSubjectHash(report),
        deckReceiptId=receipt.receiptId,
        deckReceiptKind=receipt.kind,
        deckReceiptStatus=receipt.status,
        deckReceiptParentReceiptIds=receipt.parentReceiptIds,
    )


def executeConditionalPlayScenarioDeck(
    entityId: str,
    inputs: OperatingWorldInputs,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    baseExperiment: "ConditionalScenarioExperiment",
    patches: tuple[ConditionalPlayControlPatch, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    objectiveIndex: int = 0,
    traceLimit: int | None = None,
) -> ConditionalPlayScenarioDeckReport:
    """Execute base-surface control patches as an ordered scenario deck."""

    baseReport = baseExperiment.playReplayReport
    if baseReport is None:
        raise ScenarioCompositionError("conditional play scenario deck needs parent replay")
    baseSurface = baseReport.controlSurface
    patchTuple = tuple(patches)
    baseRows = _validateControlPatchRows(baseSurface, patchTuple, allowMixedPlanes=True)
    for patch in patchTuple:
        _rejectUnsafeControlPatchRef(patch.patchRef)
    _validateScenarioDeckInteractions(baseRows)
    baseRowByControlId = dict(zip((patch.controlId for patch in patchTuple), baseRows, strict=True))
    patchByPlane = {
        semanticPlane: tuple(
            patch for patch, row in zip(patchTuple, baseRows, strict=True) if row.semanticPlane == semanticPlane
        )
        for semanticPlane in CONDITIONAL_PLAY_SCENARIO_DECK_PLANE_ORDER
    }
    stageInputs = inputs
    stageCases = tuple(cases)
    stageStrategies = tuple(strategies)
    stageExperiment = baseExperiment
    stageReports: list[ConditionalPlayControlExecutionReport] = []
    rebaseRows: list[ConditionalPlayControlRebaseRow] = []
    for semanticPlane in CONDITIONAL_PLAY_SCENARIO_DECK_PLANE_ORDER:
        planePatches = patchByPlane[semanticPlane]
        if not planePatches:
            continue
        stageReport = stageExperiment.playReplayReport
        if stageReport is None:
            raise ScenarioCompositionError("conditional play scenario stage needs parent replay")
        stageSurface = stageReport.controlSurface
        stageRowById = _controlRowsById(stageSurface)
        rebasedPatches = []
        for patch in planePatches:
            baseRow = baseRowByControlId[patch.controlId]
            stageRow = stageRowById.get(patch.controlId)
            if stageRow is None:
                raise ScenarioCompositionError("staged control patch target is missing")
            _assertControlRebaseCompatible(baseRow, stageRow)
            rebasedPatch = replace(
                patch,
                baseSurfaceHash=stageSurface.surfaceHash,
                baseRowHash=stageRow.rowHash,
            )
            rebasedPatches.append(rebasedPatch)
            rebaseRows.append(
                _controlRebaseRow(
                    originalPatch=patch,
                    rebasedPatch=rebasedPatch,
                    baseRow=baseRow,
                    stageRow=stageRow,
                    stageSurface=stageSurface,
                )
            )
        rebasedPatchTuple = tuple(rebasedPatches)
        stageRows = _validateControlPatches(stageSurface, rebasedPatchTuple)
        bundle = _executeValidatedControlPatchGroup(
            entityId,
            stageInputs,
            stageCases,
            stageStrategies,
            stageExperiment,
            stageSurface,
            stageRows,
            rebasedPatchTuple,
            debtLimit=debtLimit,
            maxFinancing=maxFinancing,
            maxInvestment=maxInvestment,
            objectiveIndex=objectiveIndex,
            traceLimit=traceLimit,
        )
        stageInputs = bundle.inputs
        stageCases = bundle.cases
        stageStrategies = bundle.strategies
        stageExperiment = bundle.report.patchedExperiment
        stageReports.append(bundle.report)
    if not stageReports:
        raise ScenarioCompositionError("conditional play scenario deck needs executable stages")
    if _deckSourceSealHash(baseExperiment) != _deckSourceSealHash(stageExperiment):
        raise ScenarioCompositionError("scenario deck changed provider history source seal")
    finalReport = stageExperiment.playReplayReport
    if finalReport is None:
        raise ScenarioCompositionError("conditional play scenario deck lost final replay")
    strategyDeltaRows = _strategyDeltaRows(baseExperiment, stageExperiment)
    caseLeaderDeltaRows = _caseLeaderDeltaRows(baseExperiment, stageExperiment)
    semanticPlanes = tuple(stage.semanticPlane for stage in stageReports)
    stageExecutionHashes = tuple(stage.executionHash for stage in stageReports)
    stageChainHash = canonicalPayloadHash(
        {
            "semanticPlanes": semanticPlanes,
            "stageExecutionHashes": stageExecutionHashes,
            "stagePatchSetHashes": tuple(stage.patchSetHash for stage in stageReports),
            "stageBaseExperimentHashes": tuple(stage.baseExperimentHash for stage in stageReports),
            "stagePatchedExperimentHashes": tuple(stage.patchedExperimentHash for stage in stageReports),
            "rebaseRowHashes": tuple(row.rowHash for row in rebaseRows),
        }
    )
    draft = ConditionalPlayScenarioDeckReport(
        deckHash="",
        schemaVersion=CONDITIONAL_PLAY_SCENARIO_DECK_VERSION,
        kind=CONDITIONAL_PLAY_SCENARIO_DECK_KIND,
        baseExperimentHash=baseExperiment.experimentHash,
        finalExperimentHash=stageExperiment.experimentHash,
        basePlayReplayHash=baseReport.playReplayHash,
        finalPlayReplayHash=finalReport.playReplayHash,
        baseControlSurfaceHash=baseSurface.surfaceHash,
        finalControlSurfaceHash=finalReport.controlSurfaceHash,
        baseSimulationSpecHash=baseExperiment.simulationSpecHash,
        finalSimulationSpecHash=stageExperiment.simulationSpecHash,
        baseResultSetHash=baseExperiment.resultSetHash,
        finalResultSetHash=stageExperiment.resultSetHash,
        baseStrategySetHash=baseExperiment.strategySetHash,
        finalStrategySetHash=stageExperiment.strategySetHash,
        baseSourceSealHash=_deckSourceSealHash(baseExperiment),
        finalSourceSealHash=_deckSourceSealHash(stageExperiment),
        stageChainHash=stageChainHash,
        baseLineageParentReceiptIds=_conditionalPlayDeckLineageParentReceiptIds(baseExperiment),
        finalLineageParentReceiptIds=_conditionalPlayDeckLineageParentReceiptIds(stageExperiment),
        changedControlIds=tuple(controlId for stage in stageReports for controlId in stage.changedControlIds),
        semanticPlanes=semanticPlanes,
        stageExecutionHashes=stageExecutionHashes,
        rebaseRows=tuple(rebaseRows),
        strategyDeltaRows=strategyDeltaRows,
        caseLeaderDeltaRows=caseLeaderDeltaRows,
        stageReports=tuple(stageReports),
        finalExperiment=stageExperiment,
        blockedReasons=_conditionalPlayScenarioDeckBlockedReasons(stageExperiment),
        warnings=stageExperiment.warnings,
        baseExperimentReceiptId=baseExperiment.experimentReceiptId,
        baseExperimentReceiptSubjectHash=baseExperiment.experimentReceiptSubjectHash,
        finalExperimentReceiptId=stageExperiment.experimentReceiptId,
        finalExperimentReceiptSubjectHash=stageExperiment.experimentReceiptSubjectHash,
    )
    return replace(draft, deckHash=conditionalPlayScenarioDeckSubjectHash(draft))


def _traceRows(
    comparison: OperatingScenarioComparison,
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
    caseLedgerHashes: tuple[str, ...],
    strategyContractHashes: tuple[str, ...],
) -> tuple[ConditionalPlayTraceRow, ...]:
    strategyHashById = dict(zip(comparison.strategyIds, strategyContractHashes, strict=True))
    rows: list[ConditionalPlayTraceRow] = []
    for result, ledger, caseLedgerHash in zip(comparison.caseResults, caseLedgers, caseLedgerHashes, strict=True):
        sourceLineageKeys = _sourceLineageKeysByFactor(ledger)
        for trace in result.retainedTraces:
            for step in trace.steps:
                assumptionStepHash = (
                    ledger.pathAssumptionStepHashes[step.step]
                    if 0 <= step.step < len(ledger.pathAssumptionStepHashes)
                    else ""
                )
                payload = {
                    "caseLedgerHash": caseLedgerHash,
                    "caseId": ledger.caseId,
                    "strategyId": trace.strategyId,
                    "pathId": trace.pathId,
                    "step": step.step,
                    "beforeState": _floatPairs(step.before),
                    "shocks": _floatPairs(step.shocks),
                    "issuedActions": _floatPairs(step.issuedActions),
                    "effectiveActions": _floatPairs(step.effectiveActions),
                    "afterState": _floatPairs(step.after),
                    "breaches": step.breaches,
                    "traceRoot": result.traceRoot,
                    "providerLaneLineageHash": ledger.providerLaneLineageHash,
                    "strategyContractHash": strategyHashById[trace.strategyId],
                    "sourceLineageKeysByFactor": sourceLineageKeys,
                }
                rows.append(
                    ConditionalPlayTraceRow(
                        rowHash=_rowHash("traceRow", payload),
                        caseId=ledger.caseId,
                        label=ledger.label,
                        strategyId=trace.strategyId,
                        pathId=trace.pathId,
                        step=step.step,
                        beforeState=_floatPairs(step.before),
                        shocks=_floatPairs(step.shocks),
                        issuedActions=_floatPairs(step.issuedActions),
                        effectiveActions=_floatPairs(step.effectiveActions),
                        actionCost=step.actionCost,
                        afterState=_floatPairs(step.after),
                        lawIds=tuple(law.lawId for law in step.laws),
                        lawEvidenceKinds=tuple(law.evidenceKind for law in step.laws),
                        lawCertificateIds=tuple(law.certificateId for law in step.laws),
                        breaches=step.breaches,
                        caseLedgerHash=caseLedgerHash,
                        runHash=result.runHash,
                        resultHash=result.resultHash,
                        traceRoot=result.traceRoot,
                        scenarioPathPackageHash=ledger.scenarioPathPackageHash,
                        scenarioPathPackageReceiptId=ledger.scenarioPathPackageReceiptId,
                        scenarioPathPackageSubjectHash=ledger.scenarioPathPackageSubjectHash,
                        pathSetHash=ledger.pathSetHash,
                        pathHistoryInputHash=ledger.pathHistoryInputHash,
                        pathAssumptionHash=ledger.pathAssumptionHash,
                        assumptionStepHash=assumptionStepHash,
                        providerLaneLineageHash=ledger.providerLaneLineageHash,
                        strategyContractHash=strategyHashById[trace.strategyId],
                        sourceLineageKeysByFactor=sourceLineageKeys,
                    )
                )
    return tuple(rows)


def _leaderTransitions(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
    assumptionSetHashes: tuple[str, ...],
) -> tuple[ConditionalPlayLeaderTransition, ...]:
    rows = []
    for index in range(1, len(caseLedgers)):
        before = caseLedgers[index - 1]
        after = caseLedgers[index]
        payload = {
            "fromCaseId": before.caseId,
            "toCaseId": after.caseId,
            "fromLeaderStrategies": before.scoreLeaderStrategies,
            "toLeaderStrategies": after.scoreLeaderStrategies,
            "fromAssumptionSetHash": assumptionSetHashes[index - 1],
            "toAssumptionSetHash": assumptionSetHashes[index],
        }
        rows.append(
            ConditionalPlayLeaderTransition(
                rowHash=_rowHash("leaderTransition", payload),
                fromCaseId=before.caseId,
                toCaseId=after.caseId,
                fromLeaderStrategies=before.scoreLeaderStrategies,
                toLeaderStrategies=after.scoreLeaderStrategies,
                changed=before.scoreLeaderStrategies != after.scoreLeaderStrategies,
                fromAssumptionSetHash=assumptionSetHashes[index - 1],
                toAssumptionSetHash=assumptionSetHashes[index],
            )
        )
    return tuple(rows)


def _blockerRows(
    experimentReasons: tuple[str, ...],
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[ConditionalPlayBlockerRow, ...]:
    rows: list[ConditionalPlayBlockerRow] = []
    for reason in experimentReasons:
        payload = {"scope": "experiment", "caseId": "", "reason": reason, "sourceBlockedReasons": experimentReasons}
        rows.append(
            ConditionalPlayBlockerRow(
                rowHash=_rowHash("blockerRow", payload),
                scope="experiment",
                caseId="",
                reason=reason,
                sourceBlockedReasons=experimentReasons,
            )
        )
    for ledger in caseLedgers:
        for reason in ledger.blockedReasons:
            payload = {
                "scope": "case",
                "caseId": ledger.caseId,
                "reason": reason,
                "sourceBlockedReasons": ledger.blockedReasons,
            }
            rows.append(
                ConditionalPlayBlockerRow(
                    rowHash=_rowHash("blockerRow", payload),
                    scope="case",
                    caseId=ledger.caseId,
                    reason=reason,
                    sourceBlockedReasons=ledger.blockedReasons,
                )
            )
    return tuple(rows)


def _experimentCells(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
    assumptionSetHashes: tuple[str, ...],
    objectiveIndex: int,
) -> tuple[ConditionalScenarioExperimentCell, ...]:
    cells: list[ConditionalScenarioExperimentCell] = []
    for ledger, assumptionSetHash in zip(caseLedgers, assumptionSetHashes, strict=True):
        candidateScores = tuple(score for score in ledger.strategyScores if score.feasible) or ledger.strategyScores
        if not candidateScores:
            continue
        bestScore = max(_scoreForObjective(score, objectiveIndex) for score in candidateScores)
        leaders = set(_objectiveLeaders(ledger.strategyScores, objectiveIndex))
        for score in ledger.strategyScores:
            value = _scoreForObjective(score, objectiveIndex)
            cells.append(
                ConditionalScenarioExperimentCell(
                    caseId=ledger.caseId,
                    label=ledger.label,
                    strategyId=score.strategyId,
                    objectiveScores=score.objectiveScores,
                    score=value,
                    feasible=score.feasible,
                    breachCount=score.breachCount,
                    regret=max(0.0, bestScore - value),
                    scoreLeader=score.strategyId in leaders,
                    assumptionSetHash=assumptionSetHash,
                    scenarioPathPackageHash=ledger.scenarioPathPackageHash,
                    pathSetHash=ledger.pathSetHash,
                    runHash=ledger.runHash,
                    resultHash=ledger.resultHash,
                    blockedReasons=ledger.blockedReasons,
                )
            )
    return tuple(cells)


def _strategySummaries(
    cells: tuple[ConditionalScenarioExperimentCell, ...],
    strategyIds: tuple[str, ...],
) -> tuple[ConditionalStrategySummary, ...]:
    summaries: list[ConditionalStrategySummary] = []
    for strategyId in strategyIds:
        rows = tuple(cell for cell in cells if cell.strategyId == strategyId)
        if not rows:
            continue
        scores = tuple(cell.score for cell in rows)
        regrets = tuple(cell.regret for cell in rows)
        leaderCount = sum(1 for cell in rows if cell.scoreLeader)
        summaries.append(
            ConditionalStrategySummary(
                strategyId=strategyId,
                scoreMedian=_median(scores),
                scoreWorst=min(scores),
                scoreBest=max(scores),
                regretMedian=_median(regrets),
                regretWorst=max(regrets),
                leaderCellCount=leaderCount,
                leaderFrequency=leaderCount / len(rows),
                feasibleCellCount=sum(1 for cell in rows if cell.feasible),
                totalCellCount=len(rows),
                breachCount=sum(cell.breachCount for cell in rows),
            )
        )
    return tuple(summaries)


def _fragilityCells(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
    assumptionSetHashes: tuple[str, ...],
    objectiveIndex: int,
) -> tuple[ConditionalAssumptionFragility, ...]:
    rows: list[ConditionalAssumptionFragility] = []
    for ledger, assumptionSetHash in zip(caseLedgers, assumptionSetHashes, strict=True):
        scores = ledger.strategyScores
        candidates = tuple(score for score in scores if score.feasible) or scores
        if not candidates:
            continue
        scorePairs = tuple((score.strategyId, _scoreForObjective(score, objectiveIndex)) for score in candidates)
        leaderScore = max(value for _, value in scorePairs)
        leaderStrategies = tuple(
            sorted(strategyId for strategyId, value in scorePairs if abs(value - leaderScore) <= 1e-12)
        )
        runnerPairs = tuple(
            (strategyId, value) for strategyId, value in scorePairs if strategyId not in leaderStrategies
        )
        if runnerPairs:
            runnerUpScore = max(value for _, value in runnerPairs)
            runnerUpStrategies = tuple(
                sorted(strategyId for strategyId, value in runnerPairs if abs(value - runnerUpScore) <= 1e-12)
            )
        else:
            runnerUpScore = leaderScore
            runnerUpStrategies = ()
        scoreSpread = leaderScore - min(value for _, value in scorePairs)
        breachStrategies = tuple(sorted(score.strategyId for score in scores if score.breachCount))
        rows.append(
            ConditionalAssumptionFragility(
                caseId=ledger.caseId,
                label=ledger.label,
                assumptionSetHash=assumptionSetHash,
                scenarioPathPackageHash=ledger.scenarioPathPackageHash,
                leaderStrategies=leaderStrategies,
                runnerUpStrategies=runnerUpStrategies,
                leaderScore=leaderScore,
                runnerUpScore=runnerUpScore,
                leaderMargin=leaderScore - runnerUpScore,
                scoreSpread=scoreSpread,
                breachStrategies=breachStrategies,
                assumptionRefs=ledger.assumptionRefs,
                blockedReasons=ledger.blockedReasons,
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.leaderMargin, row.caseId)))


def _caseBlockedReasons(result: OperatingScenarioCaseResult) -> tuple[str, ...]:
    reasons = []
    if result.decisionStatus != "comparable":
        reasons.append(f"decisionStatus:{result.decisionStatus}")
    if result.recommendation is None:
        reasons.append("caseRecommendationClosed")
        if result.strategyScores:
            reasons.append("scoreLeaderNotRecommendation")
    if result.counts.explicitAssumptionCount:
        reasons.append("explicitAssumptionPresent")
    if result.pathAssumptionHash:
        reasons.append("explicitFutureAdjustmentPresent")
        reasons.append("explicitOverlayBlocksPolicyRecommendation")
    if result.counts.unvalidatedPathCount:
        reasons.append("unvalidatedPathPresent")
    if result.counts.retrospectivePathCount:
        reasons.append("retrospectiveOnlyPathPresent")
    if result.counts.admittedPathCount < result.counts.pathCount:
        reasons.append("pathAdmissionIncomplete")
    if result.composedPathAdmissionStatus != "admitted":
        reasons.append("composedPathAdmissionNotGranted")
    if result.pathAdmissionTransferStatus == "notTransferred":
        reasons.extend(result.pathAdmissionTransferBlockedBy)
        if result.basePathSetHash:
            reasons.append("basePathAdmissionScopeHistoryOnly")
    if result.scenarioPathPackageReceiptId:
        reasons.append("conditionalReceiptNotPathAdmission")
        reasons.append("conditionalReceiptIdsExcludedFromPolicy")
        reasons.append("policyAdmittedRecommendationBlocked")
    if result.policyEvaluationEligibility == "blocked":
        reasons.append("policyEvaluationRequiresAdmittedComposedPath")
    if result.counts.conditionalWarningCount:
        reasons.append("conditionalWarningPresent")
    if not result.initialStateAdmissionReceiptId:
        reasons.append("initialStateAdmissionMissing")
    if not result.pathAdmissionReceiptId:
        reasons.append("pathAdmissionMissing")
    if not result.policyEvaluationCertificateId:
        reasons.append("policyEvaluationCertificateMissing")
        reasons.append("policyEvidenceMissing")
    return _dedupe(tuple(reasons))


def _loopBlockedReasons(
    comparison: OperatingScenarioComparison,
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    reasons = []
    if comparison.decisionStatus != "comparable":
        reasons.append(f"comparisonDecisionStatus:{comparison.decisionStatus}")
    if comparison.recommendation is None:
        reasons.append("automaticRecommendationDisabled")
    leaderSets = {case.scoreLeaderStrategies for case in caseLedgers}
    if len(leaderSets) > 1:
        reasons.append("scenarioScoreLeadersDiverge")
    reasons.extend(reason for case in caseLedgers for reason in case.blockedReasons)
    return _dedupe(tuple(reasons))


def _experimentBlockedReasons(
    comparison: OperatingScenarioComparison,
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    reasons = list(_loopBlockedReasons(comparison, caseLedgers))
    if "automaticRecommendationDisabled" not in reasons:
        reasons.append("automaticRecommendationDisabled")
    reasons.append("conditionalExperimentNotPolicyRecommendation")
    if len(caseLedgers) > 2:
        reasons.append("assumptionSweepPresent")
    if len(comparison.strategyIds) > 2:
        reasons.append("strategySweepPresent")
    return _dedupe(tuple(reasons))


def _caseLedger(
    case: OperatingScenarioCase,
    result: OperatingScenarioCaseResult,
    *,
    initialStateRefs: tuple[str, ...],
) -> OneCompanyScenarioCaseLedger:
    conditionRefs = _dedupe(result.refs)
    assumptionRefs = _filterRefs(conditionRefs, _ASSUMPTION_REF_PREFIXES)
    stateRefs = _dedupe((*initialStateRefs, *_filterRefs(conditionRefs, _STATE_REF_PREFIXES)))
    basePathAdmissionReceiptId = _basePathAdmissionReceiptId(case.pathSet)
    pathSourceRefs = case.pathSet.audit.sourceRefs
    providerObservationBatchRefs = _filterRefs(pathSourceRefs, _PROVIDER_OBSERVATION_REF_PREFIXES)
    explicitAssumptionIds = _explicitAssumptionIds(case.pathSet.audit.warnings)
    providerLineage = _providerLineageLedger(
        pathSourceRefs=pathSourceRefs,
        providerObservationBatchRefs=providerObservationBatchRefs,
        explicitAssumptionIds=explicitAssumptionIds,
    )
    return OneCompanyScenarioCaseLedger(
        caseId=result.caseId,
        label=result.label,
        factorIds=tuple(factor.variableId for factor in case.pathSet.factorSpecs),
        conditionRefs=conditionRefs,
        assumptionRefs=assumptionRefs,
        stateRefs=stateRefs,
        pathSetInputHash=case.pathSet.audit.inputHash,
        pathRegistryHash=case.pathSet.audit.registryHash,
        pathFactorContractHash=case.pathSet.audit.factorContractHash,
        pathSourceRefs=pathSourceRefs,
        providerObservationBatchRefs=providerObservationBatchRefs,
        providerLineage=providerLineage,
        providerLaneLineageHash=providerLineage.providerLaneLineageHash,
        providerLineageStatus=providerLineage.providerLineageStatus,
        providerObservationBatchReceiptIds=providerLineage.providerObservationBatchReceiptIds,
        providerObservationBatchIds=providerLineage.providerObservationBatchIds,
        providerObservationBatchSourceReceiptIds=providerLineage.providerObservationBatchSourceReceiptIds,
        priceSourceLegReceiptIds=providerLineage.priceSourceLegReceiptIds,
        derivedReturnReceiptIds=providerLineage.derivedReturnReceiptIds,
        adjustmentPolicyHashes=providerLineage.adjustmentPolicyHashes,
        normalizationContractHashes=providerLineage.normalizationContractHashes,
        returnTransformRefs=providerLineage.returnTransformRefs,
        returnTransformHash=providerLineage.returnTransformHash,
        factorMappingRefs=providerLineage.factorMappingRefs,
        rawSourceRefs=providerLineage.rawSourceRefs,
        revisedHistoryRefs=providerLineage.revisedHistoryRefs,
        explicitAssumptionIds=explicitAssumptionIds,
        scenarioPathPackageHash=result.scenarioPathPackageHash,
        scenarioPathPackageSubjectHash=result.scenarioPathPackageSubjectHash,
        scenarioPathPackageReceiptId=result.scenarioPathPackageReceiptId,
        scenarioPathPackageReceiptKind=result.scenarioPathPackageReceiptKind,
        scenarioPathPackageReceiptStatus=result.scenarioPathPackageReceiptStatus,
        scenarioPathPackageParentReceiptIds=scenarioPathPackageParentReceiptIds(case.pathSet),
        pathHistoryInputHash=result.pathHistoryInputHash,
        pathAssumptionHash=result.pathAssumptionHash,
        pathAssumptionStepHashes=case.pathSet.audit.assumptionStepHashes,
        basePathSetHash=result.basePathSetHash,
        pathFrequency=result.pathFrequency,
        pathHorizon=result.pathHorizon,
        basePathAdmissionContentHash=case.pathSet.audit.basePathAdmissionContentHash,
        basePathAdmissionSubjectHash=case.pathSet.audit.basePathAdmissionSubjectHash,
        basePathValidationStatus=case.pathSet.audit.basePathValidationStatus,
        basePathMaxAdmittedStep=case.pathSet.audit.basePathMaxAdmittedStep,
        composedPathSetHash=result.pathSetHash,
        pathOverlayHash=result.pathOverlayHash,
        observedHistoryStatus=result.observedHistoryStatus,
        futureAdjustmentStatus=result.futureAdjustmentStatus,
        basePathAdmissionReceiptId=basePathAdmissionReceiptId,
        basePathAdmissionScope=_basePathAdmissionScope(case.pathSet),
        composedPathAdmissionStatus=result.composedPathAdmissionStatus,
        pathAdmissionTransferStatus=result.pathAdmissionTransferStatus,
        pathAdmissionTransferBlockedBy=result.pathAdmissionTransferBlockedBy,
        policyEvaluationEligibility=result.policyEvaluationEligibility,
        recommendationCeiling=result.decisionStatus,
        driverRegistryLedger=_driverRegistryLedger(case.driverRegistryAudit),
        exposureLedgers=_exposureLedgerRows(case.exposures),
        coefficientAdmissionReceiptIds=tuple(binding.admissionReceiptId for binding in case.coefficientBindings),
        coefficientBindingHashes=tuple(scenarioCoefficientBindingHash(binding) for binding in case.coefficientBindings),
        coefficientParentReceiptIds=_dedupe(
            tuple(receiptId for binding in case.coefficientBindings for receiptId in binding.parentReceiptIds)
        ),
        pathSetHash=result.pathSetHash,
        bridgeHashes=result.bridgeHashes,
        runHash=result.runHash,
        resultHash=result.resultHash,
        executableHash=result.executableHash,
        parameterHash=result.parameterHash,
        dataVintageHash=result.dataVintageHash,
        traceRoot=result.traceRoot,
        traceCount=result.traceCount,
        retainedTraceCount=result.retainedTraceCount,
        initialStateAdmissionReceiptId=result.initialStateAdmissionReceiptId,
        pathAdmissionReceiptId=result.pathAdmissionReceiptId,
        pathAdmissionContentHash=result.pathAdmissionContentHash,
        pathCertificateIds=result.pathCertificateIds,
        policyEvaluationCertificateId=result.policyEvaluationCertificateId,
        policyEvaluationCertificateReceiptId=result.policyEvaluationCertificateReceiptId,
        policyEvaluationCertificateStatus=result.policyEvaluationCertificateStatus,
        policyEvaluationParentReceiptIds=result.policyEvaluationParentReceiptIds,
        recommendationSource=result.recommendationSource,
        recommendationEvidenceKind=result.recommendationEvidenceKind,
        recommendationEvidenceReceiptId=result.recommendationEvidenceReceiptId,
        conditionalReceiptIdsExcludedFromPolicy=result.conditionalReceiptIdsExcludedFromPolicy,
        decisionStatus=result.decisionStatus,
        status=result.status,
        weightLabel=result.weightLabel,
        recommendation=result.recommendation,
        paretoStrategies=result.paretoStrategies,
        scoreLeaderStrategies=_scoreLeaderStrategies(result.strategyScores),
        strategyScores=result.strategyScores,
        counts=result.counts,
        blockedReasons=_caseBlockedReasons(result),
        warnings=result.warnings,
    )


def _caseLedgerHashes(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return tuple(
        canonicalPayloadHash(
            {
                "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_VERSION,
                "caseId": ledger.caseId,
                "label": ledger.label,
                "factorIds": ledger.factorIds,
                "conditionRefs": ledger.conditionRefs,
                "assumptionRefs": ledger.assumptionRefs,
                "stateRefs": ledger.stateRefs,
                "pathSetInputHash": ledger.pathSetInputHash,
                "pathRegistryHash": ledger.pathRegistryHash,
                "pathFactorContractHash": ledger.pathFactorContractHash,
                "pathSourceRefs": ledger.pathSourceRefs,
                "providerObservationBatchRefs": ledger.providerObservationBatchRefs,
                "providerLineage": ledger.providerLineage,
                "providerLaneLineageHash": ledger.providerLaneLineageHash,
                "providerLineageStatus": ledger.providerLineageStatus,
                "providerObservationBatchReceiptIds": ledger.providerObservationBatchReceiptIds,
                "providerObservationBatchIds": ledger.providerObservationBatchIds,
                "providerObservationBatchSourceReceiptIds": ledger.providerObservationBatchSourceReceiptIds,
                "priceSourceLegReceiptIds": ledger.priceSourceLegReceiptIds,
                "derivedReturnReceiptIds": ledger.derivedReturnReceiptIds,
                "adjustmentPolicyHashes": ledger.adjustmentPolicyHashes,
                "normalizationContractHashes": ledger.normalizationContractHashes,
                "returnTransformRefs": ledger.returnTransformRefs,
                "returnTransformHash": ledger.returnTransformHash,
                "factorMappingRefs": ledger.factorMappingRefs,
                "rawSourceRefs": ledger.rawSourceRefs,
                "revisedHistoryRefs": ledger.revisedHistoryRefs,
                "explicitAssumptionIds": ledger.explicitAssumptionIds,
                "scenarioPathPackageHash": ledger.scenarioPathPackageHash,
                "scenarioPathPackageSubjectHash": ledger.scenarioPathPackageSubjectHash,
                "scenarioPathPackageReceiptId": ledger.scenarioPathPackageReceiptId,
                "scenarioPathPackageReceiptKind": ledger.scenarioPathPackageReceiptKind,
                "scenarioPathPackageReceiptStatus": ledger.scenarioPathPackageReceiptStatus,
                "scenarioPathPackageParentReceiptIds": ledger.scenarioPathPackageParentReceiptIds,
                "pathHistoryInputHash": ledger.pathHistoryInputHash,
                "pathAssumptionHash": ledger.pathAssumptionHash,
                "pathAssumptionStepHashes": ledger.pathAssumptionStepHashes,
                "basePathSetHash": ledger.basePathSetHash,
                "pathFrequency": ledger.pathFrequency,
                "pathHorizon": ledger.pathHorizon,
                "basePathAdmissionContentHash": ledger.basePathAdmissionContentHash,
                "basePathAdmissionSubjectHash": ledger.basePathAdmissionSubjectHash,
                "basePathValidationStatus": ledger.basePathValidationStatus,
                "basePathMaxAdmittedStep": ledger.basePathMaxAdmittedStep,
                "composedPathSetHash": ledger.composedPathSetHash,
                "pathOverlayHash": ledger.pathOverlayHash,
                "observedHistoryStatus": ledger.observedHistoryStatus,
                "futureAdjustmentStatus": ledger.futureAdjustmentStatus,
                "basePathAdmissionReceiptId": ledger.basePathAdmissionReceiptId,
                "basePathAdmissionScope": ledger.basePathAdmissionScope,
                "composedPathAdmissionStatus": ledger.composedPathAdmissionStatus,
                "pathAdmissionTransferStatus": ledger.pathAdmissionTransferStatus,
                "pathAdmissionTransferBlockedBy": ledger.pathAdmissionTransferBlockedBy,
                "policyEvaluationEligibility": ledger.policyEvaluationEligibility,
                "driverRegistryLedger": ledger.driverRegistryLedger,
                "exposureLedgers": ledger.exposureLedgers,
                "coefficientAdmissionReceiptIds": ledger.coefficientAdmissionReceiptIds,
                "coefficientBindingHashes": ledger.coefficientBindingHashes,
                "coefficientParentReceiptIds": ledger.coefficientParentReceiptIds,
                "pathSetHash": ledger.pathSetHash,
                "bridgeHashes": ledger.bridgeHashes,
                "runHash": ledger.runHash,
                "resultHash": ledger.resultHash,
                "executableHash": ledger.executableHash,
                "parameterHash": ledger.parameterHash,
                "dataVintageHash": ledger.dataVintageHash,
                "traceRoot": ledger.traceRoot,
                "traceCount": ledger.traceCount,
                "retainedTraceCount": ledger.retainedTraceCount,
                "initialStateAdmissionReceiptId": ledger.initialStateAdmissionReceiptId,
                "pathAdmissionReceiptId": ledger.pathAdmissionReceiptId,
                "pathAdmissionContentHash": ledger.pathAdmissionContentHash,
                "pathCertificateIds": ledger.pathCertificateIds,
                "policyEvaluationCertificateId": ledger.policyEvaluationCertificateId,
                "policyEvaluationCertificateReceiptId": ledger.policyEvaluationCertificateReceiptId,
                "policyEvaluationCertificateStatus": ledger.policyEvaluationCertificateStatus,
                "policyEvaluationParentReceiptIds": ledger.policyEvaluationParentReceiptIds,
                "recommendationSource": ledger.recommendationSource,
                "recommendationEvidenceKind": ledger.recommendationEvidenceKind,
                "recommendationEvidenceReceiptId": ledger.recommendationEvidenceReceiptId,
                "conditionalReceiptIdsExcludedFromPolicy": ledger.conditionalReceiptIdsExcludedFromPolicy,
                "recommendationCeiling": ledger.recommendationCeiling,
                "decisionStatus": ledger.decisionStatus,
                "status": ledger.status,
                "weightLabel": ledger.weightLabel,
                "recommendation": ledger.recommendation,
                "paretoStrategies": ledger.paretoStrategies,
                "scoreLeaderStrategies": ledger.scoreLeaderStrategies,
                "strategyScores": ledger.strategyScores,
                "counts": ledger.counts,
                "blockedReasons": ledger.blockedReasons,
                "warnings": ledger.warnings,
            }
        )
        for ledger in caseLedgers
    )


def _experimentProviderObservationBatchRefs(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(tuple(ref for ledger in caseLedgers for ref in ledger.providerObservationBatchRefs))


def _experimentProviderLaneLineageHashes(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(tuple(ledger.providerLaneLineageHash for ledger in caseLedgers))


def _experimentProviderLineageStatuses(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(tuple(status for ledger in caseLedgers for status in ledger.providerLineageStatus))


def _experimentProviderObservationBatchReceiptIds(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(
        tuple(receiptId for ledger in caseLedgers for receiptId in ledger.providerObservationBatchReceiptIds)
    )


def _experimentProviderObservationBatchIds(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(tuple(batchId for ledger in caseLedgers for batchId in ledger.providerObservationBatchIds))


def _experimentProviderObservationBatchSourceReceiptIds(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(
        tuple(receiptId for ledger in caseLedgers for receiptId in ledger.providerObservationBatchSourceReceiptIds)
    )


def _experimentPriceSourceLegReceiptIds(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(tuple(receiptId for ledger in caseLedgers for receiptId in ledger.priceSourceLegReceiptIds))


def _experimentDerivedReturnReceiptIds(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(tuple(receiptId for ledger in caseLedgers for receiptId in ledger.derivedReturnReceiptIds))


def _experimentAdjustmentPolicyHashes(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(tuple(policyHash for ledger in caseLedgers for policyHash in ledger.adjustmentPolicyHashes))


def _experimentNormalizationContractHashes(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(tuple(contractHash for ledger in caseLedgers for contractHash in ledger.normalizationContractHashes))


def _experimentReturnTransformHashes(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[str, ...]:
    return _dedupe(tuple(ledger.returnTransformHash for ledger in caseLedgers))


def _experimentRawSourceRefs(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(tuple(ref for ledger in caseLedgers for ref in ledger.rawSourceRefs))


def _experimentRevisedHistoryRefs(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(tuple(ref for ledger in caseLedgers for ref in ledger.revisedHistoryRefs))


def _experimentDriverRegistryHashes(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(
        tuple(ledger.driverRegistryLedger.registryHash for ledger in caseLedgers if ledger.driverRegistryLedger)
    )


def _experimentDriverRegistryLaneIds(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(
        tuple(
            laneId
            for ledger in caseLedgers
            if ledger.driverRegistryLedger
            for laneId in ledger.driverRegistryLedger.laneIds
        )
    )


def _experimentDriverRegistrySemanticRefs(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(
        tuple(
            ref
            for ledger in caseLedgers
            if ledger.driverRegistryLedger
            for ref in ledger.driverRegistryLedger.semanticRefs
        )
    )


def _experimentDriverRegistrySourceRefs(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(
        tuple(
            ref
            for ledger in caseLedgers
            if ledger.driverRegistryLedger
            for ref in ledger.driverRegistryLedger.sourceRefs
        )
    )


def _experimentDriverRegistryWarnings(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(
        tuple(
            warning
            for ledger in caseLedgers
            if ledger.driverRegistryLedger
            for warning in ledger.driverRegistryLedger.warnings
        )
    )


def _experimentExplicitAssumptionIds(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(tuple(assumptionId for ledger in caseLedgers for assumptionId in ledger.explicitAssumptionIds))


def _experimentPathHistoryInputHashes(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(tuple(ledger.pathHistoryInputHash for ledger in caseLedgers))


def _experimentPathAssumptionHashes(caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...]) -> tuple[str, ...]:
    return _dedupe(tuple(ledger.pathAssumptionHash for ledger in caseLedgers))


def _experimentPathAssumptionStepHashes(
    caseLedgers: tuple[OneCompanyScenarioCaseLedger, ...],
) -> tuple[tuple[str, ...], ...]:
    return tuple(ledger.pathAssumptionStepHashes for ledger in caseLedgers)


def _experimentInitialStateAdmissionReceiptIds(experiment: ConditionalScenarioExperiment) -> tuple[str, ...]:
    return _dedupe(tuple(ledger.initialStateAdmissionReceiptId for ledger in experiment.caseLedgers))


def _experimentScenarioPathPackageReceiptIds(experiment: ConditionalScenarioExperiment) -> tuple[str, ...]:
    return _dedupe(tuple(ledger.scenarioPathPackageReceiptId for ledger in experiment.caseLedgers))


def _experimentCaseResultHashes(experiment: ConditionalScenarioExperiment) -> tuple[str, ...]:
    return tuple(ledger.resultHash for ledger in experiment.caseLedgers)


def _experimentRunHashes(experiment: ConditionalScenarioExperiment) -> tuple[str, ...]:
    return tuple(ledger.runHash for ledger in experiment.caseLedgers)


def _experimentLeaderStrategyIds(experiment: ConditionalScenarioExperiment) -> tuple[str, ...]:
    if not experiment.strategySummaries:
        return ()
    leaderFrequency = max(summary.leaderFrequency for summary in experiment.strategySummaries)
    return tuple(
        sorted(
            summary.strategyId
            for summary in experiment.strategySummaries
            if abs(summary.leaderFrequency - leaderFrequency) <= 1e-12
        )
    )


def _conditionalExperimentComparisonReplayHash(experiment: ConditionalScenarioExperiment) -> str:
    return canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_VERSION,
            "decisionStatus": experiment.decisionStatus,
            "recommendationCeiling": experiment.recommendationCeiling,
            "recommendation": experiment.recommendation,
            "strategySetHash": experiment.strategySetHash,
            "caseLedgerHashes": experiment.caseLedgerHashes,
            "resultSetHash": experiment.resultSetHash,
            "blockedReasons": experiment.blockedReasons,
            "warnings": experiment.warnings,
        }
    )


def conditionalScenarioExperimentParentReceiptIds(
    experiment: ConditionalScenarioExperiment,
) -> tuple[str, ...]:
    """Return receipt parents required to document a conditional experiment result.

    Args:
        experiment: Conditional scenario experiment returned by the simulator.

    Returns:
        Ordered parent receipt identifiers for state, path packages, and coefficients.

    Raises:
        ScenarioCompositionError: If a case with explicit assumptions lacks a composed path package receipt.

    Example:
        ``parents = conditionalScenarioExperimentParentReceiptIds(experiment)``
    """

    missingPathPackages = tuple(
        ledger.caseId
        for ledger in experiment.caseLedgers
        if ledger.pathAssumptionHash and not ledger.scenarioPathPackageReceiptId
    )
    if missingPathPackages:
        raise ScenarioCompositionError("conditional experiment receipt needs scenario path package receipts")
    pathPackageReceipts = _experimentScenarioPathPackageReceiptIds(experiment)
    if not pathPackageReceipts:
        raise ScenarioCompositionError("conditional experiment receipt needs composed path package parents")
    initialStateReceipts = _experimentInitialStateAdmissionReceiptIds(experiment)
    coefficientReceipts = _dedupe(
        tuple(receiptId for ledger in experiment.caseLedgers for receiptId in ledger.coefficientAdmissionReceiptIds)
    )
    return _dedupe((*initialStateReceipts, *pathPackageReceipts, *coefficientReceipts))


def conditionalScenarioExperimentPayload(experiment: ConditionalScenarioExperiment) -> dict:
    """Build the canonical artifact payload for a documented experiment result.

    Args:
        experiment: Conditional scenario experiment to seal as a replayable result table.

    Returns:
        Canonical payload dictionary binding inputs, strategies, scores, blockers, and provenance.

    Raises:
        ScenarioCompositionError: If required path package parent receipts are missing.

    Example:
        ``payload = conditionalScenarioExperimentPayload(experiment)``
    """

    parentReceiptIds = conditionalScenarioExperimentParentReceiptIds(experiment)
    leaderboardHash = canonicalPayloadHash(experiment.strategySummaries)
    fragilitySummaryHash = canonicalPayloadHash(experiment.fragilityCells)
    blockerSummaryHash = canonicalPayloadHash(experiment.blockedReasons)
    return {
        "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_VERSION,
        "kind": CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND,
        "status": "documented",
        "decisionStatus": experiment.decisionStatus,
        "recommendationStatus": "disabled" if experiment.recommendation is None else "enabled",
        "experiment": {
            "experimentHash": experiment.experimentHash,
            "schemaVersion": experiment.schemaVersion,
            "entityId": experiment.entityId,
            "comparisonReplayHash": _conditionalExperimentComparisonReplayHash(experiment),
            "simulationSpecHash": experiment.simulationSpecHash,
            "resultSetHash": experiment.resultSetHash,
            "scenarioCount": experiment.scenarioCount,
            "strategyCount": experiment.strategyCount,
            "cellCount": experiment.cellCount,
            "objectiveIndex": experiment.objectiveIndex,
        },
        "inputs": {
            "initialStateAdmissionReceiptIds": _experimentInitialStateAdmissionReceiptIds(experiment),
            "composedPathPackageReceiptIds": _experimentScenarioPathPackageReceiptIds(experiment),
            "composedPathPackageSubjectHashes": tuple(
                ledger.scenarioPathPackageSubjectHash for ledger in experiment.caseLedgers
            ),
            "providerObservationBatchRefs": experiment.providerObservationBatchRefs,
            "explicitAssumptionIds": experiment.explicitAssumptionIds,
            "overlayHashes": tuple(ledger.pathOverlayHash for ledger in experiment.caseLedgers),
            "pathHistoryInputHashes": experiment.pathHistoryInputHashes,
            "pathAssumptionHashes": experiment.pathAssumptionHashes,
            "pathAssumptionStepHashes": experiment.pathAssumptionStepHashes,
            "providerLaneLineageHashes": experiment.providerLaneLineageHashes,
            "providerLineageStatuses": experiment.providerLineageStatuses,
            "providerObservationBatchReceiptIds": experiment.providerObservationBatchReceiptIds,
            "providerObservationBatchIds": experiment.providerObservationBatchIds,
            "providerObservationBatchSourceReceiptIds": experiment.providerObservationBatchSourceReceiptIds,
            "priceSourceLegReceiptIds": experiment.priceSourceLegReceiptIds,
            "derivedReturnReceiptIds": experiment.derivedReturnReceiptIds,
            "adjustmentPolicyHashes": experiment.adjustmentPolicyHashes,
            "normalizationContractHashes": experiment.normalizationContractHashes,
            "returnTransformHashes": experiment.returnTransformHashes,
            "rawSourceRefs": experiment.rawSourceRefs,
            "revisedHistoryRefs": experiment.revisedHistoryRefs,
            "driverRegistryHashes": experiment.driverRegistryHashes,
            "driverRegistryLaneIds": experiment.driverRegistryLaneIds,
            "driverRegistrySemanticRefs": experiment.driverRegistrySemanticRefs,
            "driverRegistrySourceRefs": experiment.driverRegistrySourceRefs,
            "driverRegistryWarnings": experiment.driverRegistryWarnings,
        },
        "strategies": {
            "strategySetHash": experiment.strategySetHash,
            "strategyIds": experiment.strategyIds,
            "strategyContractHashes": experiment.strategyContractHashes,
        },
        "metrics": {
            "metricDefinitionHash": CONDITIONAL_SCENARIO_EXPERIMENT_METRIC_DEFINITION_HASH,
            "comparisonRuleHash": CONDITIONAL_SCENARIO_EXPERIMENT_COMPARISON_RULE_HASH,
            "fragilityDefinitionHash": CONDITIONAL_SCENARIO_EXPERIMENT_FRAGILITY_RULE_HASH,
            "blockerRuleHash": CONDITIONAL_SCENARIO_EXPERIMENT_BLOCKER_RULE_HASH,
        },
        "cases": tuple(
            {
                "caseId": ledger.caseId,
                "label": ledger.label,
                "caseLedgerHash": caseLedgerHash,
                "caseResultHash": ledger.resultHash,
                "runHash": ledger.runHash,
                "scenarioPathPackageHash": ledger.scenarioPathPackageHash,
                "scenarioPathPackageReceiptId": ledger.scenarioPathPackageReceiptId,
                "scenarioPathPackageReceiptStatus": ledger.scenarioPathPackageReceiptStatus,
                "assumptionSetId": assumptionSetId,
                "assumptionSetHash": assumptionSetHash,
                "scoreLeaderStrategies": ledger.scoreLeaderStrategies,
                "blockedReasons": ledger.blockedReasons,
                "conditionRefs": ledger.conditionRefs,
                "pathSourceRefs": ledger.pathSourceRefs,
                "providerLaneLineageHash": ledger.providerLaneLineageHash,
                "providerLineageStatus": ledger.providerLineageStatus,
                "providerObservationBatchReceiptIds": ledger.providerObservationBatchReceiptIds,
                "providerObservationBatchIds": ledger.providerObservationBatchIds,
                "providerObservationBatchSourceReceiptIds": ledger.providerObservationBatchSourceReceiptIds,
                "priceSourceLegReceiptIds": ledger.priceSourceLegReceiptIds,
                "derivedReturnReceiptIds": ledger.derivedReturnReceiptIds,
                "rawSourceRefs": ledger.rawSourceRefs,
                "revisedHistoryRefs": ledger.revisedHistoryRefs,
            }
            for ledger, caseLedgerHash, assumptionSetId, assumptionSetHash in zip(
                experiment.caseLedgers,
                experiment.caseLedgerHashes,
                experiment.assumptionSetIds,
                experiment.assumptionSetHashes,
                strict=True,
            )
        ),
        "results": {
            "resultSetHash": experiment.resultSetHash,
            "caseResultHashes": _experimentCaseResultHashes(experiment),
            "runHashes": _experimentRunHashes(experiment),
            "tracePanelHash": canonicalPayloadHash(experiment.traceRows),
            "traceRows": experiment.traceRows,
            "leaderStrategyIds": _experimentLeaderStrategyIds(experiment),
            "leaderboardHash": leaderboardHash,
            "fragilitySummaryHash": fragilitySummaryHash,
            "blockerSummaryHash": blockerSummaryHash,
            "strategySummaries": experiment.strategySummaries,
            "cells": experiment.cells,
            "fragilityCells": experiment.fragilityCells,
        },
        "recommendationCeiling": experiment.recommendationCeiling,
        "recommendation": experiment.recommendation,
        "blockedReasons": experiment.blockedReasons,
        "warnings": experiment.warnings,
        "parentReceiptIds": parentReceiptIds,
    }


def conditionalScenarioExperimentArtifact(experiment: ConditionalScenarioExperiment) -> bytes:
    """Return canonical bytes for a documented conditional experiment result.

    Args:
        experiment: Conditional scenario experiment to serialize.

    Returns:
        Canonical JSON bytes whose digest is signed by the result receipt.

    Raises:
        ScenarioCompositionError: If required path package parent receipts are missing.

    Example:
        ``artifact = conditionalScenarioExperimentArtifact(experiment)``
    """

    return canonicalPayloadBytes(conditionalScenarioExperimentPayload(experiment))


def conditionalScenarioExperimentSubjectHash(experiment: ConditionalScenarioExperiment) -> str:
    """Return the subject hash signed by a conditional experiment result receipt.

    Args:
        experiment: Conditional scenario experiment to bind.

    Returns:
        SHA-256 digest of the canonical experiment result artifact.

    Raises:
        ScenarioCompositionError: If required path package parent receipts are missing.

    Example:
        ``subjectHash = conditionalScenarioExperimentSubjectHash(experiment)``
    """

    return canonicalPayloadHash(conditionalScenarioExperimentPayload(experiment))


def _playReplayProvenanceIndex(experiment: ConditionalScenarioExperiment) -> dict:
    return {
        "caseLedgerHashes": experiment.caseLedgerHashes,
        "providerLaneLineageHashes": experiment.providerLaneLineageHashes,
        "providerLineageStatuses": experiment.providerLineageStatuses,
        "providerObservationBatchRefs": experiment.providerObservationBatchRefs,
        "providerObservationBatchReceiptIds": experiment.providerObservationBatchReceiptIds,
        "providerObservationBatchIds": experiment.providerObservationBatchIds,
        "providerObservationBatchSourceReceiptIds": experiment.providerObservationBatchSourceReceiptIds,
        "priceSourceLegReceiptIds": experiment.priceSourceLegReceiptIds,
        "derivedReturnReceiptIds": experiment.derivedReturnReceiptIds,
        "adjustmentPolicyHashes": experiment.adjustmentPolicyHashes,
        "normalizationContractHashes": experiment.normalizationContractHashes,
        "returnTransformHashes": experiment.returnTransformHashes,
        "rawSourceRefs": experiment.rawSourceRefs,
        "revisedHistoryRefs": experiment.revisedHistoryRefs,
        "explicitAssumptionIds": experiment.explicitAssumptionIds,
        "scenarioPathPackageReceiptIds": _experimentScenarioPathPackageReceiptIds(experiment),
        "initialStateAdmissionReceiptIds": _experimentInitialStateAdmissionReceiptIds(experiment),
        "conditionalReceiptIdsExcludedFromPolicy": _dedupe(
            tuple(
                receiptId
                for ledger in experiment.caseLedgers
                for receiptId in ledger.conditionalReceiptIdsExcludedFromPolicy
            )
        ),
    }


def conditionalPlayReplayPayload(report: ConditionalPlayReplayReport) -> dict:
    """Build a canonical payload for the conditional play replay projection."""

    return {
        "schemaVersion": report.schemaVersion,
        "kind": report.kind,
        "lineageMode": report.lineageMode,
        "contractHash": CONDITIONAL_PLAY_REPLAY_CONTRACT_HASH,
        "entityId": report.entityId,
        "decisionStatus": report.decisionStatus,
        "recommendationStatus": report.recommendationStatus,
        "recommendationCeiling": report.recommendationCeiling,
        "recommendation": report.recommendation,
        "shape": {
            "scenarioCount": report.scenarioCount,
            "strategyCount": report.strategyCount,
            "cellCount": report.cellCount,
            "horizon": report.horizon,
            "frequency": report.frequency,
            "traceRetention": report.traceRetention,
        },
        "sourceSeals": {
            "experimentHash": report.experimentHash,
            "comparisonHash": report.comparisonHash,
            "simulationSpecHash": report.simulationSpecHash,
            "resultSetHash": report.resultSetHash,
            "strategySetHash": report.strategySetHash,
            "caseLedgerHashes": report.caseLedgerHashes,
            "providerLaneLineageHashes": report.providerLaneLineageHashes,
        },
        "sectionHashes": {
            "conditionPanelHash": report.conditionPanelHash,
            "strategyPanelHash": report.strategyPanelHash,
            "cellPanelHash": report.cellPanelHash,
            "tracePanelHash": report.tracePanelHash,
            "leaderPanelHash": report.leaderPanelHash,
            "fragileCasePanelHash": report.fragileCasePanelHash,
            "blockerPanelHash": report.blockerPanelHash,
            "controlPanelHash": report.controlPanelHash,
            "provenanceIndexHash": report.provenanceIndexHash,
        },
        "controls": {
            "schemaVersion": report.controlSurface.schemaVersion,
            "kind": report.controlSurface.kind,
            "controlSurfaceHash": report.controlSurfaceHash,
            "controlPanelHash": report.controlPanelHash,
            "rowHashes": report.controlSurface.rowHashes,
            "adjustableControlIds": report.controlSurface.adjustableControlIds,
            "overlayControlIds": report.controlSurface.overlayControlIds,
            "lockedControlIds": report.controlSurface.lockedControlIds,
            "blockedReasons": report.controlSurface.blockedReasons,
            "surface": report.controlSurface,
        },
        "conditions": report.conditionRows,
        "strategies": report.strategyRows,
        "cells": report.cellRows,
        "traces": report.traceRows,
        "leaderTransitions": report.leaderTransitions,
        "fragilityRows": report.fragilityRows,
        "blockerRows": report.blockerRows,
        "blockedReasons": report.blockedReasons,
        "warnings": report.warnings,
    }


def conditionalPlayReplaySubjectHash(report: ConditionalPlayReplayReport) -> str:
    """Return the content hash for the conditional play replay projection."""

    return canonicalPayloadHash(conditionalPlayReplayPayload(report))


def conditionalPlayReplayArtifact(report: ConditionalPlayReplayReport) -> bytes:
    """Return canonical bytes for the conditional play replay projection."""

    return canonicalPayloadBytes(conditionalPlayReplayPayload(report))


def _buildConditionalPlayReplayReport(
    experiment: ConditionalScenarioExperiment,
    conditionRows: tuple[ConditionalPlayConditionRow, ...],
    strategyRows: tuple[ConditionalPlayStrategyRow, ...],
    cellRows: tuple[ConditionalPlayCellRow, ...],
    leaderTransitions: tuple[ConditionalPlayLeaderTransition, ...],
    blockerRows: tuple[ConditionalPlayBlockerRow, ...],
    controlSurface: ConditionalPlayControlSurface,
) -> ConditionalPlayReplayReport:
    if experiment.decisionStatus != "conditionalOnly" or experiment.recommendation is not None:
        raise ScenarioCompositionError("conditional play replay cannot promote a policy recommendation")
    if any(ledger.policyEvaluationCertificateId for ledger in experiment.caseLedgers):
        raise ScenarioCompositionError("conditional play replay cannot carry policy certificates")
    if not experiment.traceRows:
        raise ScenarioCompositionError("conditional play replay needs retained trace rows")
    if any(ledger.retainedTraceCount != ledger.traceCount for ledger in experiment.caseLedgers):
        raise ScenarioCompositionError("conditional play replay needs full retained traces")
    expectedTraceRows = sum(ledger.retainedTraceCount * ledger.pathHorizon for ledger in experiment.caseLedgers)
    if len(experiment.traceRows) != expectedTraceRows:
        raise ScenarioCompositionError("conditional play replay trace row count mismatch")
    frequencies = tuple(dict.fromkeys(ledger.pathFrequency for ledger in experiment.caseLedgers))
    horizons = tuple(dict.fromkeys(ledger.pathHorizon for ledger in experiment.caseLedgers))
    if len(frequencies) != 1 or len(horizons) != 1:
        raise ScenarioCompositionError("conditional play replay needs one frequency and horizon")
    if (
        not controlSurface.rows
        or controlSurface.caseLedgerHashes != experiment.caseLedgerHashes
        or controlSurface.providerLaneLineageHashes != experiment.providerLaneLineageHashes
        or controlSurface.surfaceHash != conditionalPlayControlSurfaceSubjectHash(controlSurface)
    ):
        raise ScenarioCompositionError("conditional play replay control surface mismatch")
    conditionPanelHash = canonicalPayloadHash(conditionRows)
    strategyPanelHash = canonicalPayloadHash(strategyRows)
    cellPanelHash = canonicalPayloadHash(cellRows)
    tracePanelHash = canonicalPayloadHash(experiment.traceRows)
    leaderPanelHash = canonicalPayloadHash(leaderTransitions)
    fragileCasePanelHash = canonicalPayloadHash(experiment.fragilityCells)
    blockerPanelHash = canonicalPayloadHash(blockerRows)
    controlPanelHash = canonicalPayloadHash(controlSurface.rows)
    provenanceIndexHash = canonicalPayloadHash(_playReplayProvenanceIndex(experiment))
    draft = ConditionalPlayReplayReport(
        playReplayHash="",
        schemaVersion=CONDITIONAL_PLAY_REPLAY_VERSION,
        kind=CONDITIONAL_PLAY_REPLAY_KIND,
        lineageMode="conditionalWarGameProjection",
        entityId=experiment.entityId,
        decisionStatus=experiment.decisionStatus,
        recommendationStatus="disabled",
        recommendationCeiling=experiment.recommendationCeiling,
        recommendation=experiment.recommendation,
        scenarioCount=experiment.scenarioCount,
        strategyCount=experiment.strategyCount,
        cellCount=experiment.cellCount,
        horizon=horizons[0],
        frequency=frequencies[0],
        traceRetention="full",
        experimentHash=experiment.experimentHash,
        comparisonHash=experiment.comparisonHash,
        simulationSpecHash=experiment.simulationSpecHash,
        resultSetHash=experiment.resultSetHash,
        strategySetHash=experiment.strategySetHash,
        caseLedgerHashes=experiment.caseLedgerHashes,
        providerLaneLineageHashes=experiment.providerLaneLineageHashes,
        conditionPanelHash=conditionPanelHash,
        strategyPanelHash=strategyPanelHash,
        cellPanelHash=cellPanelHash,
        tracePanelHash=tracePanelHash,
        leaderPanelHash=leaderPanelHash,
        fragileCasePanelHash=fragileCasePanelHash,
        blockerPanelHash=blockerPanelHash,
        controlPanelHash=controlPanelHash,
        provenanceIndexHash=provenanceIndexHash,
        controlSurfaceHash=controlSurface.surfaceHash,
        conditionRows=conditionRows,
        strategyRows=strategyRows,
        cellRows=cellRows,
        traceRows=experiment.traceRows,
        leaderTransitions=leaderTransitions,
        fragilityRows=experiment.fragilityCells,
        blockerRows=blockerRows,
        controlSurface=controlSurface,
        blockedReasons=experiment.blockedReasons,
        warnings=experiment.warnings,
    )
    return replace(draft, playReplayHash=conditionalPlayReplaySubjectHash(draft))


def validateConditionalScenarioExperimentReceipt(
    experiment: ConditionalScenarioExperiment,
    receiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> "AdmissionReceipt":
    """Verify a documented conditional experiment result receipt.

    Args:
        experiment: Conditional scenario experiment whose result artifact is checked.
        receiptId: Signed receipt identifier to verify.
        admissionVerifier: Runtime verifier with trusted issuer keys and artifact root.

    Returns:
        Verified admission registry receipt for the documented experiment result.

    Raises:
        ScenarioCompositionError: If the receipt, artifact, parents, or recommendation boundary do not match.

    Example:
        ``receipt = validateConditionalScenarioExperimentReceipt(experiment, receiptId, verifier)``
    """

    if not _validDigest(receiptId):
        raise ScenarioCompositionError("conditional experiment receipt identifier is invalid")
    subjectHash = conditionalScenarioExperimentSubjectHash(experiment)
    try:
        from dartlab.simulate.admissionRegistry import artifactPath

        receipt = admissionVerifier.verify(
            receiptId,
            expectedSubjectHash=subjectHash,
            expectedKind=CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND,
        )
        parentReceipts = tuple(admissionVerifier.verify(parentId) for parentId in receipt.parentReceiptIds)
        artifactBytes = artifactPath(admissionVerifier.artifactRoot, subjectHash).read_bytes()
    except (OSError, RuntimeError, ValueError) as error:
        raise ScenarioCompositionError(f"conditional experiment receipt verification failed: {error}") from error
    if artifactBytes != conditionalScenarioExperimentArtifact(experiment):
        raise ScenarioCompositionError("conditional experiment artifact content mismatch")
    expectedParents = conditionalScenarioExperimentParentReceiptIds(experiment)
    if receipt.parentReceiptIds != expectedParents:
        raise ScenarioCompositionError("conditional experiment receipt parent mismatch")
    if (
        receipt.status != "documented"
        or receipt.artifactHash != subjectHash
        or receipt.ruleId != CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_ID
        or receipt.ruleVersion != CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_VERSION
        or receipt.ruleHash != CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_HASH
        or receipt.revisionPolicy != "explicitAssumption"
        or receipt.coverage != "synthetic"
        or receipt.frequency != "scenario"
        or receipt.stepSpan != 1
        or receipt.maxAdmittedStep != 0
    ):
        raise ScenarioCompositionError("conditional experiment receipt contract mismatch")
    if any(parent.kind in {"policyEvaluation", "policyEpisodeBatch"} for parent in parentReceipts):
        raise ScenarioCompositionError("conditional experiment cannot depend on policy evaluation receipts")
    if any(parent.status == "policyAdmitted" for parent in parentReceipts):
        raise ScenarioCompositionError("conditional experiment cannot inherit policy admitted parents")
    if experiment.recommendation is not None:
        raise ScenarioCompositionError("conditional experiment receipt cannot carry recommendation")
    if "conditionalExperimentNotPolicyRecommendation" not in experiment.blockedReasons:
        raise ScenarioCompositionError("conditional experiment receipt needs recommendation blocker")
    if any(ledger.policyEvaluationCertificateId for ledger in experiment.caseLedgers):
        raise ScenarioCompositionError("conditional experiment receipt cannot carry policy certificate ids")
    if any(ledger.pathAdmissionReceiptId for ledger in experiment.caseLedgers):
        raise ScenarioCompositionError("conditional experiment receipt cannot carry path admission ids")
    return receipt


def bindConditionalScenarioExperimentReceipt(
    experiment: ConditionalScenarioExperiment,
    receiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> ConditionalScenarioExperiment:
    """Attach a verified documented receipt to a conditional experiment ledger.

    Args:
        experiment: Conditional scenario experiment to annotate.
        receiptId: Signed documented experiment receipt identifier.
        admissionVerifier: Runtime verifier used to validate the receipt and artifact.

    Returns:
        Copy of the experiment carrying receipt id, kind, status, subject hash, and parents.

    Raises:
        ScenarioCompositionError: If receipt verification fails.

    Example:
        ``sealed = bindConditionalScenarioExperimentReceipt(experiment, receiptId, verifier)``
    """

    receipt = validateConditionalScenarioExperimentReceipt(experiment, receiptId, admissionVerifier)
    return replace(
        experiment,
        experimentReceiptSubjectHash=conditionalScenarioExperimentSubjectHash(experiment),
        experimentReceiptId=receipt.receiptId,
        experimentReceiptKind=receipt.kind,
        experimentReceiptStatus=receipt.status,
        experimentReceiptParentReceiptIds=receipt.parentReceiptIds,
    )


def _strategyEvaluationRobustnessClass(
    summary: ConditionalStrategySummary,
    conditionalLeaderIds: tuple[str, ...],
) -> str:
    if summary.strategyId in conditionalLeaderIds and abs(summary.leaderFrequency - 1.0) <= 1e-12:
        return "allScenarioConditionalLeader"
    if summary.strategyId in conditionalLeaderIds:
        return "scenarioDependentConditionalLeader"
    if summary.leaderCellCount:
        return "scenarioLocalLeader"
    return "neverLeader"


def _strategyEvaluationRows(experiment: ConditionalScenarioExperiment) -> tuple[ConditionalStrategyEvaluationRow, ...]:
    conditionalLeaderIds = _experimentLeaderStrategyIds(experiment)
    rows: list[ConditionalStrategyEvaluationRow] = []
    for summary in experiment.strategySummaries:
        rowReasons: list[str] = []
        if summary.feasibleCellCount < summary.totalCellCount:
            rowReasons.append("strategyInfeasibleInSomeCases")
        if summary.breachCount:
            rowReasons.append("strategyConstraintBreachPresent")
        rows.append(
            ConditionalStrategyEvaluationRow(
                strategyId=summary.strategyId,
                conditionalLeader=summary.strategyId in conditionalLeaderIds,
                robustnessClass=_strategyEvaluationRobustnessClass(summary, conditionalLeaderIds),
                leaderFrequency=summary.leaderFrequency,
                leaderCellCount=summary.leaderCellCount,
                totalCellCount=summary.totalCellCount,
                feasibleCellCount=summary.feasibleCellCount,
                breachCount=summary.breachCount,
                scoreMedian=summary.scoreMedian,
                scoreWorst=summary.scoreWorst,
                scoreBest=summary.scoreBest,
                regretMedian=summary.regretMedian,
                regretWorst=summary.regretWorst,
                blockedReasons=_dedupe(tuple(rowReasons)),
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.leaderFrequency,
                -row.scoreWorst,
                row.regretWorst,
                row.breachCount,
                row.strategyId,
            ),
        )
    )


def _strategyEvaluationFragileCases(
    experiment: ConditionalScenarioExperiment,
) -> tuple[ConditionalStrategyFragileCase, ...]:
    if not experiment.fragilityCells:
        return ()
    smallestMargin = min(row.leaderMargin for row in experiment.fragilityCells)
    return tuple(
        ConditionalStrategyFragileCase(
            caseId=row.caseId,
            label=row.label,
            assumptionSetHash=row.assumptionSetHash,
            scenarioPathPackageHash=row.scenarioPathPackageHash,
            leaderStrategies=row.leaderStrategies,
            runnerUpStrategies=row.runnerUpStrategies,
            leaderMargin=row.leaderMargin,
            scoreSpread=row.scoreSpread,
            breachStrategies=row.breachStrategies,
            blockedReasons=row.blockedReasons,
        )
        for row in experiment.fragilityCells
        if abs(row.leaderMargin - smallestMargin) <= 1e-12
    )


def _strategyEvaluationBlockedReasons(experiment: ConditionalScenarioExperiment) -> tuple[str, ...]:
    reasons = [
        "conditionalStrategyEvaluationDocumentedOnly",
        "strategyEvaluationReceiptNotPolicyCertificate",
    ]
    reasons.extend(experiment.blockedReasons)
    if experiment.explicitAssumptionIds or any(ledger.pathAssumptionHash for ledger in experiment.caseLedgers):
        reasons.append("explicitFutureOverlayPresent")
    if any(ledger.composedPathAdmissionStatus != "admitted" for ledger in experiment.caseLedgers):
        reasons.append("composedPathNotAdmitted")
    if any(not ledger.pathAdmissionReceiptId for ledger in experiment.caseLedgers):
        reasons.append("pathAdmissionMissing")
    if any(not ledger.policyEvaluationCertificateId for ledger in experiment.caseLedgers):
        reasons.append("policyEvaluationCertificateMissing")
    if experiment.recommendation is None:
        reasons.append("automaticRecommendationDisabled")
    if any(ledger.scoreLeaderStrategies for ledger in experiment.caseLedgers):
        reasons.append("scoreLeaderNotRecommendation")
    return _dedupe(tuple(reasons))


def _validateSealedConditionalExperiment(experiment: ConditionalScenarioExperiment) -> None:
    if not experiment.experimentReceiptId:
        raise ScenarioCompositionError("conditional strategy evaluation needs sealed conditional experiment receipt")
    if (
        experiment.experimentReceiptKind != CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND
        or experiment.experimentReceiptStatus != "documented"
        or experiment.experimentReceiptSubjectHash != conditionalScenarioExperimentSubjectHash(experiment)
    ):
        raise ScenarioCompositionError("conditional experiment receipt annotation is invalid")
    if experiment.recommendation is not None:
        raise ScenarioCompositionError("conditional strategy evaluation cannot carry recommendation")
    if experiment.decisionStatus != "conditionalOnly" or experiment.recommendationCeiling != "conditionalOnly":
        raise ScenarioCompositionError("conditional strategy evaluation needs conditionalOnly experiment")
    if any(ledger.policyEvaluationCertificateId for ledger in experiment.caseLedgers):
        raise ScenarioCompositionError("conditional strategy evaluation cannot carry policy certificate ids")
    if any(ledger.pathAdmissionReceiptId for ledger in experiment.caseLedgers):
        raise ScenarioCompositionError("conditional strategy evaluation cannot carry path admission ids")
    if "conditionalExperimentNotPolicyRecommendation" not in experiment.blockedReasons:
        raise ScenarioCompositionError("conditional strategy evaluation needs experiment recommendation blocker")


def _conditionalStrategyEvaluationReplayPayload(evaluation: ConditionalStrategyEvaluation) -> dict:
    return {
        "schemaVersion": evaluation.schemaVersion,
        "kind": evaluation.kind,
        "status": "documented",
        "lineageMode": "conditionalComposedPath",
        "decisionStatus": evaluation.decisionStatus,
        "recommendationStatus": evaluation.recommendationStatus,
        "recommendation": evaluation.recommendation,
        "entityId": evaluation.entityId,
        "experimentReceiptId": evaluation.experimentReceiptId,
        "experimentReceiptSubjectHash": evaluation.experimentReceiptSubjectHash,
        "experimentHash": evaluation.experimentHash,
        "comparisonReplayHash": evaluation.comparisonReplayHash,
        "simulationSpecHash": evaluation.simulationSpecHash,
        "resultSetHash": evaluation.resultSetHash,
        "strategySetHash": evaluation.strategySetHash,
        "strategyIds": evaluation.strategyIds,
        "strategyContractHashes": evaluation.strategyContractHashes,
        "caseLedgerHashes": evaluation.caseLedgerHashes,
        "caseResultHashes": evaluation.caseResultHashes,
        "objectiveIndex": evaluation.objectiveIndex,
        "contractHash": evaluation.contractHash,
        "metricDefinitionHash": evaluation.metricDefinitionHash,
        "comparisonRuleHash": evaluation.comparisonRuleHash,
        "fragilityDefinitionHash": evaluation.fragilityDefinitionHash,
        "blockerRuleHash": evaluation.blockerRuleHash,
        "selectionRuleHash": evaluation.selectionRuleHash,
        "robustnessRuleHash": evaluation.robustnessRuleHash,
        "conditionalLeaderStrategyIds": evaluation.conditionalLeaderStrategyIds,
        "strategyRows": evaluation.strategyRows,
        "fragileCases": evaluation.fragileCases,
        "pathAdmissionReceiptIds": evaluation.pathAdmissionReceiptIds,
        "policyEvaluationCertificateIds": evaluation.policyEvaluationCertificateIds,
        "blockedReasons": evaluation.blockedReasons,
        "warnings": evaluation.warnings,
        "parentReceiptIds": evaluation.parentReceiptIds,
    }


def buildConditionalStrategyEvaluation(experiment: ConditionalScenarioExperiment) -> ConditionalStrategyEvaluation:
    """Build a documented conditional strategy judgement from a sealed experiment.

    Args:
        experiment: Conditional experiment already sealed by a documented experiment result receipt.

    Returns:
        ``ConditionalStrategyEvaluation`` with leader, fragility, blocker, and receipt parent hashes.

    Raises:
        ScenarioCompositionError: If the experiment is unsealed or already carries recommendation artifacts.

    Example:
        ``evaluation = buildConditionalStrategyEvaluation(sealedExperiment)``
    """

    _validateSealedConditionalExperiment(experiment)
    strategyRows = _strategyEvaluationRows(experiment)
    if not strategyRows:
        raise ScenarioCompositionError("conditional strategy evaluation needs strategy rows")
    fragileCases = _strategyEvaluationFragileCases(experiment)
    blockedReasons = _strategyEvaluationBlockedReasons(experiment)
    evaluationTableHash = canonicalPayloadHash(strategyRows)
    leaderboardHash = canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_STRATEGY_EVALUATION_VERSION,
            "selectionRuleHash": CONDITIONAL_STRATEGY_EVALUATION_SELECTION_RULE_HASH,
            "conditionalLeaderStrategyIds": _experimentLeaderStrategyIds(experiment),
            "strategyRows": strategyRows,
        }
    )
    fragilitySummaryHash = canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_STRATEGY_EVALUATION_VERSION,
            "fragilityDefinitionHash": CONDITIONAL_SCENARIO_EXPERIMENT_FRAGILITY_RULE_HASH,
            "fragileCases": fragileCases,
            "allFragilityCellsHash": canonicalPayloadHash(experiment.fragilityCells),
        }
    )
    blockerSummaryHash = canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_STRATEGY_EVALUATION_VERSION,
            "blockerRuleHash": CONDITIONAL_SCENARIO_EXPERIMENT_BLOCKER_RULE_HASH,
            "blockedReasons": blockedReasons,
        }
    )
    draft = ConditionalStrategyEvaluation(
        evaluationHash="",
        schemaVersion=CONDITIONAL_STRATEGY_EVALUATION_VERSION,
        kind=CONDITIONAL_STRATEGY_EVALUATION_KIND,
        entityId=experiment.entityId,
        experimentReceiptId=experiment.experimentReceiptId,
        experimentReceiptSubjectHash=experiment.experimentReceiptSubjectHash,
        experimentHash=experiment.experimentHash,
        comparisonReplayHash=_conditionalExperimentComparisonReplayHash(experiment),
        simulationSpecHash=experiment.simulationSpecHash,
        resultSetHash=experiment.resultSetHash,
        strategySetHash=experiment.strategySetHash,
        strategyIds=experiment.strategyIds,
        strategyContractHashes=experiment.strategyContractHashes,
        caseLedgerHashes=experiment.caseLedgerHashes,
        caseResultHashes=_experimentCaseResultHashes(experiment),
        objectiveIndex=experiment.objectiveIndex,
        decisionStatus=experiment.decisionStatus,
        recommendationCeiling=experiment.recommendationCeiling,
        recommendation=None,
        recommendationStatus="disabled",
        contractHash=CONDITIONAL_STRATEGY_EVALUATION_CONTRACT_HASH,
        metricDefinitionHash=CONDITIONAL_SCENARIO_EXPERIMENT_METRIC_DEFINITION_HASH,
        comparisonRuleHash=CONDITIONAL_SCENARIO_EXPERIMENT_COMPARISON_RULE_HASH,
        fragilityDefinitionHash=CONDITIONAL_SCENARIO_EXPERIMENT_FRAGILITY_RULE_HASH,
        blockerRuleHash=CONDITIONAL_SCENARIO_EXPERIMENT_BLOCKER_RULE_HASH,
        selectionRuleHash=CONDITIONAL_STRATEGY_EVALUATION_SELECTION_RULE_HASH,
        robustnessRuleHash=CONDITIONAL_STRATEGY_EVALUATION_ROBUSTNESS_RULE_HASH,
        evaluationTableHash=evaluationTableHash,
        leaderboardHash=leaderboardHash,
        fragilitySummaryHash=fragilitySummaryHash,
        blockerSummaryHash=blockerSummaryHash,
        conditionalLeaderStrategyIds=_experimentLeaderStrategyIds(experiment),
        strategyRows=strategyRows,
        fragileCases=fragileCases,
        parentReceiptIds=(experiment.experimentReceiptId,),
        pathAdmissionReceiptIds=_dedupe(tuple(ledger.pathAdmissionReceiptId for ledger in experiment.caseLedgers)),
        policyEvaluationCertificateIds=_dedupe(
            tuple(ledger.policyEvaluationCertificateId for ledger in experiment.caseLedgers)
        ),
        blockedReasons=blockedReasons,
        warnings=experiment.warnings,
    )
    return replace(draft, evaluationHash=canonicalPayloadHash(_conditionalStrategyEvaluationReplayPayload(draft)))


def conditionalStrategyEvaluationParentReceiptIds(
    evaluation: ConditionalStrategyEvaluation,
) -> tuple[str, ...]:
    """Return receipt parents required to document conditional strategy evaluation.

    Args:
        evaluation: Conditional strategy evaluation to seal.

    Returns:
        Ordered parent receipt identifiers. The first parent is the sealed conditional experiment result.

    Raises:
        ScenarioCompositionError: If the evaluation lacks its experiment result parent.

    Example:
        ``parents = conditionalStrategyEvaluationParentReceiptIds(evaluation)``
    """

    if not evaluation.experimentReceiptId:
        raise ScenarioCompositionError("conditional strategy evaluation needs experiment result parent")
    return (evaluation.experimentReceiptId,)


def conditionalStrategyEvaluationPayload(evaluation: ConditionalStrategyEvaluation) -> dict:
    """Build the canonical artifact payload for a documented strategy evaluation.

    Args:
        evaluation: Conditional strategy evaluation returned by the simulator.

    Returns:
        Canonical payload binding the sealed experiment, strategy table, fragility, and blockers.

    Raises:
        ScenarioCompositionError: If parent receipt lineage or policy boundary fields are invalid.

    Example:
        ``payload = conditionalStrategyEvaluationPayload(evaluation)``
    """

    parentReceiptIds = conditionalStrategyEvaluationParentReceiptIds(evaluation)
    if evaluation.parentReceiptIds != parentReceiptIds:
        raise ScenarioCompositionError("conditional strategy evaluation parent mismatch")
    if evaluation.evaluationHash != canonicalPayloadHash(_conditionalStrategyEvaluationReplayPayload(evaluation)):
        raise ScenarioCompositionError("conditional strategy evaluation hash mismatch")
    if evaluation.recommendation is not None or evaluation.recommendationStatus != "disabled":
        raise ScenarioCompositionError("conditional strategy evaluation cannot carry recommendation")
    return {
        "schemaVersion": CONDITIONAL_STRATEGY_EVALUATION_VERSION,
        "kind": CONDITIONAL_STRATEGY_EVALUATION_KIND,
        "status": "documented",
        "lineageMode": "conditionalComposedPath",
        "decisionStatus": evaluation.decisionStatus,
        "recommendationStatus": evaluation.recommendationStatus,
        "evaluationHash": evaluation.evaluationHash,
        "evaluation": _conditionalStrategyEvaluationReplayPayload(evaluation),
        "hashes": {
            "evaluationTableHash": evaluation.evaluationTableHash,
            "leaderboardHash": evaluation.leaderboardHash,
            "fragilitySummaryHash": evaluation.fragilitySummaryHash,
            "blockerSummaryHash": evaluation.blockerSummaryHash,
        },
        "rules": {
            "contractHash": evaluation.contractHash,
            "metricDefinitionHash": evaluation.metricDefinitionHash,
            "comparisonRuleHash": evaluation.comparisonRuleHash,
            "fragilityDefinitionHash": evaluation.fragilityDefinitionHash,
            "blockerRuleHash": evaluation.blockerRuleHash,
            "selectionRuleHash": evaluation.selectionRuleHash,
            "robustnessRuleHash": evaluation.robustnessRuleHash,
        },
        "experimentResult": {
            "experimentReceiptId": evaluation.experimentReceiptId,
            "experimentReceiptSubjectHash": evaluation.experimentReceiptSubjectHash,
            "experimentHash": evaluation.experimentHash,
            "comparisonReplayHash": evaluation.comparisonReplayHash,
            "simulationSpecHash": evaluation.simulationSpecHash,
            "resultSetHash": evaluation.resultSetHash,
        },
        "strategyJudgement": {
            "strategySetHash": evaluation.strategySetHash,
            "strategyIds": evaluation.strategyIds,
            "strategyContractHashes": evaluation.strategyContractHashes,
            "conditionalLeaderStrategyIds": evaluation.conditionalLeaderStrategyIds,
            "strategyRows": evaluation.strategyRows,
            "fragileCases": evaluation.fragileCases,
        },
        "recommendationCeiling": evaluation.recommendationCeiling,
        "recommendation": evaluation.recommendation,
        "blockedReasons": evaluation.blockedReasons,
        "warnings": evaluation.warnings,
        "refs": {
            "conditionalExperimentResult": f"conditionalExperimentResult:{evaluation.experimentReceiptId}",
            "conditionalExperimentResultSubject": (
                f"conditionalExperimentResultSubject:{evaluation.experimentReceiptSubjectHash}"
            ),
            "conditionalStrategyEvaluationReplay": f"conditionalStrategyEvaluationReplay:{evaluation.evaluationHash}",
            "strategySet": f"strategySet:{evaluation.strategySetHash}",
            "strategies": tuple(f"strategy:{strategyId}" for strategyId in evaluation.strategyIds),
            "leaderboard": f"leaderboard:{evaluation.leaderboardHash}",
            "fragilitySummary": f"fragilitySummary:{evaluation.fragilitySummaryHash}",
            "blockerSummary": f"blockerSummary:{evaluation.blockerSummaryHash}",
            "caseLedgers": tuple(f"caseLedger:{ledgerHash}" for ledgerHash in evaluation.caseLedgerHashes),
            "caseResults": tuple(f"caseResult:{resultHash}" for resultHash in evaluation.caseResultHashes),
        },
        "parentReceiptIds": parentReceiptIds,
    }


def conditionalStrategyEvaluationArtifact(evaluation: ConditionalStrategyEvaluation) -> bytes:
    """Return canonical bytes for a documented conditional strategy evaluation.

    Args:
        evaluation: Conditional strategy evaluation to serialize.

    Returns:
        Canonical JSON bytes whose digest is signed by the strategy evaluation receipt.

    Raises:
        ScenarioCompositionError: If the evaluation payload is invalid.

    Example:
        ``artifact = conditionalStrategyEvaluationArtifact(evaluation)``
    """

    return canonicalPayloadBytes(conditionalStrategyEvaluationPayload(evaluation))


def conditionalStrategyEvaluationSubjectHash(evaluation: ConditionalStrategyEvaluation) -> str:
    """Return the subject hash signed by a conditional strategy evaluation receipt.

    Args:
        evaluation: Conditional strategy evaluation to bind.

    Returns:
        SHA-256 digest of the canonical evaluation artifact.

    Raises:
        ScenarioCompositionError: If the evaluation payload is invalid.

    Example:
        ``subjectHash = conditionalStrategyEvaluationSubjectHash(evaluation)``
    """

    return canonicalPayloadHash(conditionalStrategyEvaluationPayload(evaluation))


def validateConditionalStrategyEvaluationReceipt(
    evaluation: ConditionalStrategyEvaluation,
    receiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> "AdmissionReceipt":
    """Verify a documented conditional strategy evaluation receipt.

    Args:
        evaluation: Strategy evaluation whose artifact is checked.
        receiptId: Signed receipt identifier to verify.
        admissionVerifier: Runtime verifier with trusted issuer keys and artifact root.

    Returns:
        Verified admission registry receipt for the documented strategy evaluation.

    Raises:
        ScenarioCompositionError: If receipt contract, parent lineage, artifact bytes, or recommendation boundary drift.

    Example:
        ``receipt = validateConditionalStrategyEvaluationReceipt(evaluation, receiptId, verifier)``
    """

    if not _validDigest(receiptId):
        raise ScenarioCompositionError("conditional strategy evaluation receipt identifier is invalid")
    subjectHash = conditionalStrategyEvaluationSubjectHash(evaluation)
    try:
        from dartlab.simulate.admissionRegistry import artifactPath

        receipt = admissionVerifier.verify(
            receiptId,
            expectedSubjectHash=subjectHash,
            expectedKind=CONDITIONAL_STRATEGY_EVALUATION_KIND,
        )
        parentReceipts = tuple(admissionVerifier.verify(parentId) for parentId in receipt.parentReceiptIds)
        artifactBytes = artifactPath(admissionVerifier.artifactRoot, subjectHash).read_bytes()
    except (OSError, RuntimeError, ValueError) as error:
        raise ScenarioCompositionError(
            f"conditional strategy evaluation receipt verification failed: {error}"
        ) from error
    if artifactBytes != conditionalStrategyEvaluationArtifact(evaluation):
        raise ScenarioCompositionError("conditional strategy evaluation artifact content mismatch")
    expectedParents = conditionalStrategyEvaluationParentReceiptIds(evaluation)
    if receipt.parentReceiptIds != expectedParents or len(parentReceipts) != 1:
        raise ScenarioCompositionError("conditional strategy evaluation receipt parent mismatch")
    experimentReceipt = parentReceipts[0]
    if (
        experimentReceipt.kind != CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND
        or experimentReceipt.status != "documented"
        or experimentReceipt.receiptId != evaluation.experimentReceiptId
        or experimentReceipt.subjectHash != evaluation.experimentReceiptSubjectHash
        or experimentReceipt.artifactHash != evaluation.experimentReceiptSubjectHash
        or experimentReceipt.revisionPolicy != "explicitAssumption"
        or experimentReceipt.coverage != "synthetic"
    ):
        raise ScenarioCompositionError("conditional strategy evaluation experiment parent is invalid")
    if (
        receipt.status != "documented"
        or receipt.artifactHash != subjectHash
        or receipt.ruleId != CONDITIONAL_STRATEGY_EVALUATION_RULE_ID
        or receipt.ruleVersion != CONDITIONAL_STRATEGY_EVALUATION_RULE_VERSION
        or receipt.ruleHash != CONDITIONAL_STRATEGY_EVALUATION_RULE_HASH
        or receipt.revisionPolicy != "explicitAssumption"
        or receipt.coverage != "synthetic"
        or receipt.frequency != "scenario"
        or receipt.stepSpan != 1
        or receipt.maxAdmittedStep != 0
    ):
        raise ScenarioCompositionError("conditional strategy evaluation receipt contract mismatch")
    if any(parent.kind in {"policyEvaluation", "policyEpisodeBatch"} for parent in parentReceipts):
        raise ScenarioCompositionError("conditional strategy evaluation cannot depend on policy evaluation receipts")
    if any(parent.status == "policyAdmitted" for parent in parentReceipts):
        raise ScenarioCompositionError("conditional strategy evaluation cannot inherit policy admitted parents")
    requiredReasons = {
        "conditionalStrategyEvaluationDocumentedOnly",
        "strategyEvaluationReceiptNotPolicyCertificate",
        "conditionalExperimentNotPolicyRecommendation",
        "automaticRecommendationDisabled",
        "scoreLeaderNotRecommendation",
    }
    if evaluation.recommendation is not None or evaluation.recommendationStatus != "disabled":
        raise ScenarioCompositionError("conditional strategy evaluation cannot carry recommendation")
    if evaluation.pathAdmissionReceiptIds or evaluation.policyEvaluationCertificateIds:
        raise ScenarioCompositionError("conditional strategy evaluation cannot carry admission or policy ids")
    if not requiredReasons.issubset(set(evaluation.blockedReasons)):
        raise ScenarioCompositionError("conditional strategy evaluation needs recommendation blockers")
    if evaluation.decisionStatus != "conditionalOnly" or evaluation.recommendationCeiling != "conditionalOnly":
        raise ScenarioCompositionError("conditional strategy evaluation must stay conditionalOnly")
    return receipt


def bindConditionalStrategyEvaluationReceipt(
    evaluation: ConditionalStrategyEvaluation,
    receiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> ConditionalStrategyEvaluation:
    """Attach a verified documented receipt to a conditional strategy evaluation.

    Args:
        evaluation: Conditional strategy evaluation to annotate.
        receiptId: Signed documented strategy evaluation receipt identifier.
        admissionVerifier: Runtime verifier used to validate the receipt and artifact.

    Returns:
        Copy of the evaluation carrying receipt id, kind, status, subject hash, and parents.

    Raises:
        ScenarioCompositionError: If receipt verification fails.

    Example:
        ``sealed = bindConditionalStrategyEvaluationReceipt(evaluation, receiptId, verifier)``
    """

    receipt = validateConditionalStrategyEvaluationReceipt(evaluation, receiptId, admissionVerifier)
    return replace(
        evaluation,
        evaluationReceiptSubjectHash=conditionalStrategyEvaluationSubjectHash(evaluation),
        evaluationReceiptId=receipt.receiptId,
        evaluationReceiptKind=receipt.kind,
        evaluationReceiptStatus=receipt.status,
        evaluationReceiptParentReceiptIds=receipt.parentReceiptIds,
    )


def _validateOneCompanyLoop(
    entityId: str,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
) -> None:
    if not entityId:
        raise ScenarioCompositionError("one-company scenario loop needs entityId")
    if len(cases) != 2:
        raise ScenarioCompositionError("one-company scenario loop needs exactly two scenario cases")
    if len(strategies) != 2:
        raise ScenarioCompositionError("one-company scenario loop needs exactly two strategies")


def _validateConditionalExperiment(
    entityId: str,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    objectiveIndex: int,
) -> None:
    if not entityId:
        raise ScenarioCompositionError("conditional scenario experiment needs entityId")
    if len(cases) < 2:
        raise ScenarioCompositionError("conditional scenario experiment needs at least two assumption sets")
    if len(strategies) < 2:
        raise ScenarioCompositionError("conditional scenario experiment needs at least two strategies")
    if objectiveIndex < 0:
        raise ScenarioCompositionError("objective index must be nonnegative")


def _runCase(
    inputs: OperatingWorldInputs,
    case: OperatingScenarioCase,
    strategies: tuple[StrategySpec, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    traceLimit: int | None,
    policyObjectiveIndex: int,
) -> OperatingScenarioCaseResult:
    scenarioReceipt = _verifyScenarioPathPackageReceipt(case)
    scenarioPathPackageReceiptId = scenarioReceipt.receiptId if scenarioReceipt is not None else ""
    scenarioPathPackageReceiptKind = scenarioReceipt.kind if scenarioReceipt is not None else ""
    scenarioPathPackageReceiptStatus = scenarioReceipt.status if scenarioReceipt is not None else ""
    factorSpecs = driverFactorsToOperatingSpecs(case.pathSet.factorSpecs)
    bridgeResults = tuple(
        bridgeOperatingPath(
            path,
            case.exposures,
            factorSpecs=factorSpecs,
            baselines=case.baselines,
            compiledState=case.compiledState,
            statePrimitives=case.statePrimitives,
            stateRef=case.stateRef,
            admissionVerifier=case.admissionVerifier,
            pathId=f"{case.caseId}:{path.pathId}",
        )
        for path in case.pathSet.paths
    )
    paths = _bindOperatingPathAdmission(
        case,
        tuple(item.path for item in bridgeResults),
    )
    run = runOperatingStrategies(
        inputs,
        paths,
        strategies,
        debtLimit=debtLimit,
        maxFinancing=maxFinancing,
        maxInvestment=maxInvestment,
        traceLimit=traceLimit,
        admissionVerifier=case.admissionVerifier,
        policyAdmissionEvidence=case.policyAdmissionEvidence,
        policyObjectiveIndex=policyObjectiveIndex,
    )
    bridgeHashes = tuple(item.audit.bridgeHash for item in bridgeResults)
    bridgeWarnings = tuple(warning for item in bridgeResults for warning in item.audit.warnings)
    refs = _dedupe(
        (
            *case.refs,
            *_driverRegistryRefs(case.driverRegistryAudit),
            *_coefficientBindingRefs(case.coefficientBindings),
            *case.pathSet.audit.sourceRefs,
            *_scenarioPathPackageRefs(case.pathSet, scenarioPathPackageReceiptId),
            *(ref for item in bridgeResults for ref in item.audit.sourceRefs),
            f"driverPathSet:{case.pathSet.audit.pathSetHash}",
            f"scenarioPathPackage:{_scenarioPathPackageHash(case.pathSet)}",
            f"scenarioCase:{case.caseId}",
            (f"pathAdmission:{run.pathAdmissionReceiptId}" if run.pathAdmissionReceiptId else ""),
            (f"pathAdmissionContent:{_pathAdmissionContentHash(paths, run)}" if run.pathAdmissionReceiptId else ""),
            (f"policyEvaluation:{run.policyEvaluationCertificateId}" if run.policyEvaluationCertificateId else ""),
            (
                f"policyCertificate:{_policyCertificateReceiptId(case, run)}"
                if _policyCertificateReceiptId(case, run)
                else ""
            ),
            (f"recommendationSource:{_recommendationSource(case, run)}" if _recommendationSource(case, run) else ""),
        )
    )
    warnings = tuple(sorted(set((*case.pathSet.audit.warnings, *bridgeWarnings, *run.warnings))))
    scenarioPathPackageHash = _scenarioPathPackageHash(case.pathSet)
    composedPathAdmissionStatus = _composedPathAdmissionStatus(run)
    pathAdmissionTransferStatus = _pathAdmissionTransferStatus(case.pathSet, run)
    pathAdmissionTransferBlockedBy = _pathAdmissionTransferBlockedBy(case.pathSet, run)
    return OperatingScenarioCaseResult(
        caseId=case.caseId,
        label=case.label,
        pathSetHash=case.pathSet.audit.pathSetHash,
        scenarioPathPackageHash=scenarioPathPackageHash,
        scenarioPathPackageSubjectHash=scenarioPathPackageHash,
        scenarioPathPackageReceiptId=scenarioPathPackageReceiptId,
        scenarioPathPackageReceiptKind=scenarioPathPackageReceiptKind,
        scenarioPathPackageReceiptStatus=scenarioPathPackageReceiptStatus,
        pathHistoryInputHash=case.pathSet.audit.historyInputHash,
        pathAssumptionHash=case.pathSet.audit.assumptionHash,
        pathAssumptionStepHashes=case.pathSet.audit.assumptionStepHashes,
        basePathSetHash=case.pathSet.audit.basePathSetHash,
        pathOverlayHash=case.pathSet.audit.overlayHash,
        pathFrequency=case.pathSet.audit.frequency,
        pathHorizon=case.pathSet.audit.horizon,
        observedHistoryStatus=case.pathSet.audit.observedHistoryStatus,
        futureAdjustmentStatus=_futureAdjustmentStatus(case.pathSet),
        composedPathAdmissionStatus=composedPathAdmissionStatus,
        pathAdmissionTransferStatus=pathAdmissionTransferStatus,
        pathAdmissionTransferBlockedBy=pathAdmissionTransferBlockedBy,
        policyEvaluationEligibility=_policyEvaluationEligibility(run),
        bridgeHashes=bridgeHashes,
        runHash=run.runHash,
        resultHash=run.resultHash,
        executableHash=run.executableHash,
        parameterHash=run.parameterHash,
        dataVintageHash=run.dataVintageHash,
        traceRoot=run.traceRoot,
        traceCount=run.traceCount,
        retainedTraceCount=run.retainedTraceCount,
        retainedTraces=run.traces,
        initialStateAdmissionReceiptId=run.initialStateAdmissionReceiptId,
        pathAdmissionReceiptId=run.pathAdmissionReceiptId,
        pathAdmissionContentHash=_pathAdmissionContentHash(paths, run),
        pathCertificateIds=_pathCertificateIds(paths, run),
        policyEvaluationCertificateId=run.policyEvaluationCertificateId,
        policyEvaluationCertificateReceiptId=_policyCertificateReceiptId(case, run),
        policyEvaluationCertificateStatus=_policyCertificateStatus(case, run),
        policyEvaluationParentReceiptIds=_policyEvaluationParentReceiptIds(case, run),
        recommendationSource=_recommendationSource(case, run),
        recommendationEvidenceKind=_recommendationEvidenceKind(case, run),
        recommendationEvidenceReceiptId=_recommendationEvidenceReceiptId(case, run),
        conditionalReceiptIdsExcludedFromPolicy=_conditionalReceiptIdsExcludedFromPolicy(case),
        decisionStatus=run.decisionStatus,
        status=run.status,
        weightLabel=run.weightLabel,
        recommendation=run.recommendation,
        paretoStrategies=run.paretoStrategies,
        strategyScores=_strategyScores(run),
        counts=_boundaryCounts(case, run, bridgeHashes, warnings, strategies),
        refs=refs,
        warnings=warnings,
    )


def _comparisonStatus(results: tuple[OperatingScenarioCaseResult, ...]) -> str:
    statuses = {result.decisionStatus for result in results}
    if "conditionalOnly" in statuses:
        return "conditionalOnly"
    if "abstain" in statuses:
        return "abstain"
    if "paretoOnly" in statuses:
        return "paretoOnly"
    return "comparable"


def compareOperatingScenarioCases(
    inputs: OperatingWorldInputs,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    traceLimit: int | None = None,
    policyObjectiveIndex: int = 0,
) -> OperatingScenarioComparison:
    """Run the same operating strategies across multiple named scenario cases.

    Args:
        inputs: Initial operating world state and its provenance.
        cases: Named path sets plus bridge contracts to evaluate.
        strategies: Shared baseline and candidate strategy set. Cases cannot supply
            strategy-specific paths.
        debtLimit: Hard debt constraint passed to the operating world.
        maxFinancing: Per-step borrow and repay bound.
        maxInvestment: Per-step capacity investment bound.
        traceLimit: Optional retained trace cap per case.
        policyObjectiveIndex: Objective index used when a scalar policy certificate is supplied.

    Returns:
        ``OperatingScenarioComparison`` with per-case run hashes, scores, warnings, and
        a comparison-level decision ceiling.

    Raises:
        ScenarioCompositionError: If case identity, action/path separation, or state
        bridge inputs are unsafe.

    Example:
        ``comparison = compareOperatingScenarioCases(inputs, (base, stress), strategies, debtLimit=1000, maxFinancing=100, maxInvestment=100)``
    """

    caseTuple = tuple(cases)
    strategyTuple = tuple(strategies)
    _validateCases(caseTuple, strategyTuple)
    results = tuple(
        _runCase(
            inputs,
            case,
            strategyTuple,
            debtLimit=debtLimit,
            maxFinancing=maxFinancing,
            maxInvestment=maxInvestment,
            traceLimit=traceLimit,
            policyObjectiveIndex=policyObjectiveIndex,
        )
        for case in caseTuple
    )
    decisionStatus = _comparisonStatus(results)
    warnings = []
    if decisionStatus != "comparable":
        warnings.append("scenario comparison is conditional; automatic recommendation disabled")
    recommendations = {result.recommendation for result in results}
    recommendation = None
    if decisionStatus == "comparable":
        if len(recommendations) == 1:
            recommendation = next(iter(recommendations))
        else:
            warnings.append("scenario case recommendations diverge")
    strategyContracts = tuple(strategyContractHash(strategy) for strategy in strategyTuple)
    warnings.extend(warning for result in results for warning in result.warnings)
    cleanWarnings = tuple(sorted(set(warnings)))
    comparisonHash = canonicalPayloadHash(
        {
            "schemaVersion": SCENARIO_COMPOSITION_VERSION,
            "decisionStatus": decisionStatus,
            "recommendation": recommendation,
            "strategyIds": tuple(strategy.strategyId for strategy in strategyTuple),
            "strategyContractHashes": strategyContracts,
            "caseResults": results,
            "warnings": cleanWarnings,
        }
    )
    return OperatingScenarioComparison(
        comparisonHash=comparisonHash,
        decisionStatus=decisionStatus,
        recommendation=recommendation,
        caseResults=results,
        strategyIds=tuple(strategy.strategyId for strategy in strategyTuple),
        strategyContractHashes=strategyContracts,
        warnings=cleanWarnings,
    )


def runConditionalScenarioExperiment(
    entityId: str,
    inputs: OperatingWorldInputs,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    objectiveIndex: int = 0,
    traceLimit: int | None = None,
) -> ConditionalScenarioExperiment:
    """Run an assumption sweep and summarize conditional strategy robustness.

    Args:
        entityId: Company or security identifier for the experiment subject.
        inputs: Initial operating state and state lineage refs.
        cases: Two or more scenario cases. Each case is one assumption set.
        strategies: Two or more shared strategies evaluated in every assumption set.
        debtLimit: Hard debt constraint passed to the operating world.
        maxFinancing: Per-step borrow and repay bound.
        maxInvestment: Per-step capacity investment bound.
        objectiveIndex: Objective score column used for scalar sweep summaries.
        traceLimit: Optional retained trace cap per case.

    Returns:
        ``ConditionalScenarioExperiment`` with case ledgers, cell regrets, strategy
        robustness summaries, fragility rows, hashes, and recommendation blockers.

    Raises:
        ScenarioCompositionError: If the experiment lacks enough assumption sets,
        enough strategies, safe case contracts, or a valid objective index.

    Example:
        ``experiment = runConditionalScenarioExperiment("005930", inputs, cases, strategies, debtLimit=1000, maxFinancing=100, maxInvestment=100)``
    """

    caseTuple = tuple(cases)
    strategyTuple = tuple(strategies)
    _validateConditionalExperiment(entityId, caseTuple, strategyTuple, objectiveIndex)
    comparison = compareOperatingScenarioCases(
        inputs,
        caseTuple,
        strategyTuple,
        debtLimit=debtLimit,
        maxFinancing=maxFinancing,
        maxInvestment=maxInvestment,
        traceLimit=traceLimit,
        policyObjectiveIndex=objectiveIndex,
    )
    initialRefs = _initialStateRefs(inputs)
    caseLedgers = tuple(
        _caseLedger(case, result, initialStateRefs=initialRefs)
        for case, result in zip(caseTuple, comparison.caseResults, strict=True)
    )
    caseLedgerHashes = _caseLedgerHashes(caseLedgers)
    caseParameterHashes = tuple(_caseParameterBoundaryHash(ledger) for ledger in caseLedgers)
    caseLawInputHashes = tuple(_caseLawInputHash(ledger) for ledger in caseLedgers)
    driverRegistryHashes = _experimentDriverRegistryHashes(caseLedgers)
    driverRegistryLaneIds = _experimentDriverRegistryLaneIds(caseLedgers)
    driverRegistrySemanticRefs = _experimentDriverRegistrySemanticRefs(caseLedgers)
    driverRegistrySourceRefs = _experimentDriverRegistrySourceRefs(caseLedgers)
    driverRegistryWarnings = _experimentDriverRegistryWarnings(caseLedgers)
    providerObservationBatchRefs = _experimentProviderObservationBatchRefs(caseLedgers)
    providerLaneLineageHashes = _experimentProviderLaneLineageHashes(caseLedgers)
    providerLineageStatuses = _experimentProviderLineageStatuses(caseLedgers)
    providerObservationBatchReceiptIds = _experimentProviderObservationBatchReceiptIds(caseLedgers)
    providerObservationBatchIds = _experimentProviderObservationBatchIds(caseLedgers)
    providerObservationBatchSourceReceiptIds = _experimentProviderObservationBatchSourceReceiptIds(caseLedgers)
    priceSourceLegReceiptIds = _experimentPriceSourceLegReceiptIds(caseLedgers)
    derivedReturnReceiptIds = _experimentDerivedReturnReceiptIds(caseLedgers)
    adjustmentPolicyHashes = _experimentAdjustmentPolicyHashes(caseLedgers)
    normalizationContractHashes = _experimentNormalizationContractHashes(caseLedgers)
    returnTransformHashes = _experimentReturnTransformHashes(caseLedgers)
    rawSourceRefs = _experimentRawSourceRefs(caseLedgers)
    revisedHistoryRefs = _experimentRevisedHistoryRefs(caseLedgers)
    explicitAssumptionIds = _experimentExplicitAssumptionIds(caseLedgers)
    pathHistoryInputHashes = _experimentPathHistoryInputHashes(caseLedgers)
    pathAssumptionHashes = _experimentPathAssumptionHashes(caseLedgers)
    pathAssumptionStepHashes = _experimentPathAssumptionStepHashes(caseLedgers)
    assumptionSetHashes = tuple(
        _assumptionSetHash(case, result) for case, result in zip(caseTuple, comparison.caseResults, strict=True)
    )
    strategyRefs = _strategyRefs(strategyTuple)
    strategySetHash = _strategySetHash(strategyTuple, comparison.strategyContractHashes, strategyRefs)
    cells = _experimentCells(caseLedgers, assumptionSetHashes, objectiveIndex)
    strategySummaries = _strategySummaries(cells, comparison.strategyIds)
    fragilityRows = _fragilityCells(caseLedgers, assumptionSetHashes, objectiveIndex)
    blockedReasons = _experimentBlockedReasons(comparison, caseLedgers)
    warnings = tuple(sorted(set((*comparison.warnings, *blockedReasons))))
    traceRows = _traceRows(comparison, caseLedgers, caseLedgerHashes, comparison.strategyContractHashes)
    playConditionRows = _conditionRows(caseLedgers, caseLedgerHashes, assumptionSetHashes)
    playStrategyRows = _playStrategyRows(strategyTuple, comparison.strategyContractHashes, strategySummaries)
    playCellRows = _playCellRows(cells)
    leaderTransitions = _leaderTransitions(caseLedgers, assumptionSetHashes)
    playBlockerRows = _blockerRows(blockedReasons, caseLedgers)
    controlSurface = _buildConditionalPlayControlSurface(
        entityId=entityId,
        inputs=inputs,
        cases=caseTuple,
        strategies=strategyTuple,
        caseLedgers=caseLedgers,
        caseLedgerHashes=caseLedgerHashes,
        assumptionSetHashes=assumptionSetHashes,
        strategyContractHashes=comparison.strategyContractHashes,
        warnings=warnings,
    )
    resultSetHash = canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_VERSION,
            "caseResultHashes": tuple(result.resultHash for result in comparison.caseResults),
            "runHashes": tuple(result.runHash for result in comparison.caseResults),
            "cells": cells,
            "strategySummaries": strategySummaries,
            "fragilityCells": fragilityRows,
        }
    )
    simulationSpecHash = canonicalPayloadHash(
        {
            "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_VERSION,
            "entityId": entityId,
            "initialStateRefs": initialRefs,
            "driverRegistryHashes": driverRegistryHashes,
            "driverRegistryLaneIds": driverRegistryLaneIds,
            "driverRegistrySemanticRefs": driverRegistrySemanticRefs,
            "driverRegistrySourceRefs": driverRegistrySourceRefs,
            "driverRegistryWarnings": driverRegistryWarnings,
            "providerObservationBatchRefs": providerObservationBatchRefs,
            "providerLaneLineageHashes": providerLaneLineageHashes,
            "providerLineageStatuses": providerLineageStatuses,
            "providerObservationBatchReceiptIds": providerObservationBatchReceiptIds,
            "providerObservationBatchIds": providerObservationBatchIds,
            "providerObservationBatchSourceReceiptIds": providerObservationBatchSourceReceiptIds,
            "priceSourceLegReceiptIds": priceSourceLegReceiptIds,
            "derivedReturnReceiptIds": derivedReturnReceiptIds,
            "adjustmentPolicyHashes": adjustmentPolicyHashes,
            "normalizationContractHashes": normalizationContractHashes,
            "returnTransformHashes": returnTransformHashes,
            "rawSourceRefs": rawSourceRefs,
            "revisedHistoryRefs": revisedHistoryRefs,
            "explicitAssumptionIds": explicitAssumptionIds,
            "pathHistoryInputHashes": pathHistoryInputHashes,
            "pathAssumptionHashes": pathAssumptionHashes,
            "pathAssumptionStepHashes": pathAssumptionStepHashes,
            "caseParameterHashes": caseParameterHashes,
            "caseLawInputHashes": caseLawInputHashes,
            "assumptionSetHashes": assumptionSetHashes,
            "strategySetHash": strategySetHash,
            "debtLimit": float(debtLimit),
            "maxFinancing": float(maxFinancing),
            "maxInvestment": float(maxInvestment),
            "objectiveIndex": objectiveIndex,
            "traceLimit": traceLimit,
        }
    )
    experimentPayload = {
        "schemaVersion": CONDITIONAL_SCENARIO_EXPERIMENT_VERSION,
        "entityId": entityId,
        "strategySetHash": strategySetHash,
        "simulationSpecHash": simulationSpecHash,
        "resultSetHash": resultSetHash,
        "decisionStatus": comparison.decisionStatus,
        "recommendationCeiling": comparison.decisionStatus,
        "recommendation": None,
        "strategyIds": comparison.strategyIds,
        "strategyContractHashes": comparison.strategyContractHashes,
        "initialStateRefs": initialRefs,
        "caseLedgerHashes": caseLedgerHashes,
        "caseParameterHashes": caseParameterHashes,
        "caseLawInputHashes": caseLawInputHashes,
        "driverRegistryHashes": driverRegistryHashes,
        "driverRegistryLaneIds": driverRegistryLaneIds,
        "driverRegistrySemanticRefs": driverRegistrySemanticRefs,
        "driverRegistrySourceRefs": driverRegistrySourceRefs,
        "driverRegistryWarnings": driverRegistryWarnings,
        "providerObservationBatchRefs": providerObservationBatchRefs,
        "providerLaneLineageHashes": providerLaneLineageHashes,
        "providerLineageStatuses": providerLineageStatuses,
        "providerObservationBatchReceiptIds": providerObservationBatchReceiptIds,
        "providerObservationBatchIds": providerObservationBatchIds,
        "providerObservationBatchSourceReceiptIds": providerObservationBatchSourceReceiptIds,
        "priceSourceLegReceiptIds": priceSourceLegReceiptIds,
        "derivedReturnReceiptIds": derivedReturnReceiptIds,
        "adjustmentPolicyHashes": adjustmentPolicyHashes,
        "normalizationContractHashes": normalizationContractHashes,
        "returnTransformHashes": returnTransformHashes,
        "rawSourceRefs": rawSourceRefs,
        "revisedHistoryRefs": revisedHistoryRefs,
        "explicitAssumptionIds": explicitAssumptionIds,
        "pathHistoryInputHashes": pathHistoryInputHashes,
        "pathAssumptionHashes": pathAssumptionHashes,
        "pathAssumptionStepHashes": pathAssumptionStepHashes,
        "assumptionSetIds": tuple(case.caseId for case in caseTuple),
        "assumptionSetHashes": assumptionSetHashes,
        "strategySummaries": strategySummaries,
        "cells": cells,
        "traceRows": traceRows,
        "fragilityCells": fragilityRows,
        "blockedReasons": blockedReasons,
        "warnings": warnings,
    }
    experiment = ConditionalScenarioExperiment(
        experimentHash=canonicalPayloadHash(experimentPayload),
        schemaVersion=CONDITIONAL_SCENARIO_EXPERIMENT_VERSION,
        entityId=entityId,
        comparisonHash=comparison.comparisonHash,
        strategySetHash=strategySetHash,
        simulationSpecHash=simulationSpecHash,
        resultSetHash=resultSetHash,
        decisionStatus=comparison.decisionStatus,
        recommendationCeiling=comparison.decisionStatus,
        recommendation=None,
        scenarioCount=len(caseLedgers),
        strategyCount=len(strategyTuple),
        cellCount=len(cells),
        objectiveIndex=objectiveIndex,
        strategyIds=comparison.strategyIds,
        strategyContractHashes=comparison.strategyContractHashes,
        initialStateRefs=initialRefs,
        caseLedgerHashes=caseLedgerHashes,
        driverRegistryHashes=driverRegistryHashes,
        driverRegistryLaneIds=driverRegistryLaneIds,
        driverRegistrySemanticRefs=driverRegistrySemanticRefs,
        driverRegistrySourceRefs=driverRegistrySourceRefs,
        driverRegistryWarnings=driverRegistryWarnings,
        providerObservationBatchRefs=providerObservationBatchRefs,
        providerLaneLineageHashes=providerLaneLineageHashes,
        providerLineageStatuses=providerLineageStatuses,
        providerObservationBatchReceiptIds=providerObservationBatchReceiptIds,
        providerObservationBatchIds=providerObservationBatchIds,
        providerObservationBatchSourceReceiptIds=providerObservationBatchSourceReceiptIds,
        priceSourceLegReceiptIds=priceSourceLegReceiptIds,
        derivedReturnReceiptIds=derivedReturnReceiptIds,
        adjustmentPolicyHashes=adjustmentPolicyHashes,
        normalizationContractHashes=normalizationContractHashes,
        returnTransformHashes=returnTransformHashes,
        rawSourceRefs=rawSourceRefs,
        revisedHistoryRefs=revisedHistoryRefs,
        explicitAssumptionIds=explicitAssumptionIds,
        pathHistoryInputHashes=pathHistoryInputHashes,
        pathAssumptionHashes=pathAssumptionHashes,
        pathAssumptionStepHashes=pathAssumptionStepHashes,
        assumptionSetIds=tuple(case.caseId for case in caseTuple),
        assumptionSetHashes=assumptionSetHashes,
        caseLedgers=caseLedgers,
        strategySummaries=strategySummaries,
        cells=cells,
        traceRows=traceRows,
        fragilityCells=fragilityRows,
        blockedReasons=blockedReasons,
        warnings=warnings,
    )
    playReplayReport = _buildConditionalPlayReplayReport(
        experiment,
        playConditionRows,
        playStrategyRows,
        playCellRows,
        leaderTransitions,
        playBlockerRows,
        controlSurface,
    )
    return replace(experiment, playReplayReport=playReplayReport)


def compareOneCompanyTwoScenarioStrategies(
    entityId: str,
    inputs: OperatingWorldInputs,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    traceLimit: int | None = None,
    policyObjectiveIndex: int = 0,
) -> OneCompanyScenarioLoop:
    """Run the minimal PRD vertical loop for one company.

    Args:
        entityId: Company or security identifier for the experiment subject.
        inputs: Initial operating state and state lineage refs.
        cases: Exactly two named scenario cases.
        strategies: Exactly two shared strategies to compare in every case.
        debtLimit: Hard debt constraint passed to the operating world.
        maxFinancing: Per-step borrow and repay bound.
        maxInvestment: Per-step capacity investment bound.
        traceLimit: Optional retained trace cap per case.
        policyObjectiveIndex: Objective index used when a scalar policy certificate is supplied.

    Returns:
        ``OneCompanyScenarioLoop`` containing conditions, assumptions, state refs,
        strategy scores, and recommendation blocking reasons in one object.

    Raises:
        ScenarioCompositionError: If the loop is not one entity, two cases, and
        two strategies, or if the underlying composition is unsafe.

    Example:
        ``loop = compareOneCompanyTwoScenarioStrategies("005930", inputs, cases, strategies, debtLimit=1000, maxFinancing=100, maxInvestment=100)``
    """

    caseTuple = tuple(cases)
    strategyTuple = tuple(strategies)
    _validateOneCompanyLoop(entityId, caseTuple, strategyTuple)
    comparison = compareOperatingScenarioCases(
        inputs,
        caseTuple,
        strategyTuple,
        debtLimit=debtLimit,
        maxFinancing=maxFinancing,
        maxInvestment=maxInvestment,
        traceLimit=traceLimit,
        policyObjectiveIndex=policyObjectiveIndex,
    )
    initialRefs = _initialStateRefs(inputs)
    caseLedgers = tuple(
        _caseLedger(case, result, initialStateRefs=initialRefs)
        for case, result in zip(caseTuple, comparison.caseResults, strict=True)
    )
    strategyRefs = _strategyRefs(strategyTuple)
    blockedReasons = _loopBlockedReasons(comparison, caseLedgers)
    warnings = tuple(sorted(set((*comparison.warnings, *blockedReasons))))
    loopPayload = {
        "schemaVersion": ONE_COMPANY_SCENARIO_LOOP_VERSION,
        "entityId": entityId,
        "comparisonHash": comparison.comparisonHash,
        "decisionStatus": comparison.decisionStatus,
        "recommendationCeiling": comparison.decisionStatus,
        "recommendation": comparison.recommendation,
        "strategyIds": comparison.strategyIds,
        "strategyContractHashes": comparison.strategyContractHashes,
        "strategyRefs": strategyRefs,
        "initialStateRefs": initialRefs,
        "caseLedgers": caseLedgers,
        "blockedReasons": blockedReasons,
        "warnings": warnings,
    }
    return OneCompanyScenarioLoop(
        loopHash=canonicalPayloadHash(loopPayload),
        schemaVersion=ONE_COMPANY_SCENARIO_LOOP_VERSION,
        entityId=entityId,
        comparisonHash=comparison.comparisonHash,
        decisionStatus=comparison.decisionStatus,
        recommendationCeiling=comparison.decisionStatus,
        recommendation=comparison.recommendation,
        scenarioCount=len(caseLedgers),
        strategyCount=len(strategyTuple),
        strategyIds=comparison.strategyIds,
        strategyContractHashes=comparison.strategyContractHashes,
        strategyRefs=strategyRefs,
        initialStateRefs=initialRefs,
        caseLedgers=caseLedgers,
        blockedReasons=blockedReasons,
        warnings=warnings,
    )
