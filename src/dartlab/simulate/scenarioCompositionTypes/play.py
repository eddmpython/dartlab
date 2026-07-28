"""Conditional play control surface, replay, and deck shapes.

The rows a replayed play produces and the control patches that steer it.
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
    from dartlab.simulate.scenarioCompositionTypes.experiment import (
        ConditionalScenarioExperiment,
    )
    from dartlab.simulate.stateCompiler import CompiledPointInTimeState


from dartlab.simulate.scenarioCompositionTypes.paths import (
    ScenarioCompositionError,
    scenarioPathPackageSubjectHash,
)

if TYPE_CHECKING:
    from dartlab.simulate.scenarioCompositionTypes.experiment import (
        ConditionalAssumptionFragility,
        OperatingScenarioCase,
    )


CONDITIONAL_PLAY_CONTROL_SURFACE_PLANES = (
    "currentState",
    "conditionFactor",
    "assumptionDelta",
    "lawParameter",
    "strategyAction",
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
