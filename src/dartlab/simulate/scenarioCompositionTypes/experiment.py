"""Scenario experiment and operating case shapes.

One named case, the strategies run over it, and what the run concluded.
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
    from dartlab.simulate.scenarioCompositionTypes.paths import (
        ScenarioCoefficientBinding,
    )
    from dartlab.simulate.stateCompiler import CompiledPointInTimeState


from dartlab.simulate.scenarioCompositionTypes.paths import (
    ScenarioBoundaryCounts,
    ScenarioDriverRegistryLedger,
    ScenarioExposureLedger,
    ScenarioProviderLineageLedger,
    ScenarioStrategyScore,
    scenarioPathPackageParentReceiptIds,
    scenarioPathPackageSubjectHash,
)

if TYPE_CHECKING:
    from dartlab.simulate.scenarioCompositionTypes.play import (
        ConditionalPlayReplayReport,
        ConditionalPlayTraceRow,
    )


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
