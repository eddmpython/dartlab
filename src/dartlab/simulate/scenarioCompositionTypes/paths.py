"""Scenario path package receipts and the constants that bound them.

The leaf layer. Nothing here reaches back into experiment or play shapes.
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


SCENARIO_PATH_PACKAGE_VERSION = "scenario-path-package-v1"

COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND = "composedConditionalPathPackage"

_PROVIDER_OBSERVATION_BATCH_REF_PREFIX = "providerObservationBatch:"

_PROVIDER_OBSERVATION_BATCH_ID_REF_PREFIX = "providerObservationBatchId:"

_PROVIDER_OBSERVATION_REF_PREFIXES = (
    _PROVIDER_OBSERVATION_BATCH_REF_PREFIX,
    _PROVIDER_OBSERVATION_BATCH_ID_REF_PREFIX,
)


class ScenarioCompositionError(ValueError):
    """시나리오 case, path, bridge, strategy 역할 경계가 깨지면 발생한다."""


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


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _filterRefs(refs: tuple[str, ...], prefixes: tuple[str, ...]) -> tuple[str, ...]:
    return _dedupe(tuple(ref for ref in refs if ref.startswith(prefixes)))


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
