"""Assemble driver paths, operating bridges, and strategies into scenario comparisons.

This module is an internal experiment envelope. It does not create a new public
verb, admit evidence, fit coefficients, or promote a conditional run to a
recommendation. Its job is to keep future assumptions in paths, company
interventions in strategies, and run every strategy over the same path ensemble
inside each named scenario case.
"""

from __future__ import annotations

from dataclasses import dataclass
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
from dartlab.simulate.driverPaths import DriverPathSet, driverFactorsToOperatingSpecs
from dartlab.simulate.operatingBridge import (
    OperatingShockBaseline,
    OperatingTransmissionExposure,
    bridgeOperatingPath,
)
from dartlab.simulate.operatingWorld import OperatingWorldInputs, runOperatingStrategies
from dartlab.simulate.stateSupport import StatePrimitive
from dartlab.simulate.vintage import canonicalPayloadHash
from dartlab.simulate.world import SimulationRun, StrategySpec, strategyContractHash

if TYPE_CHECKING:
    from dartlab.simulate.admissionRegistry import AdmissionVerifier
    from dartlab.simulate.stateCompiler import CompiledPointInTimeState

SCENARIO_COMPOSITION_VERSION = "scenario-composition-v1"
ONE_COMPANY_SCENARIO_LOOP_VERSION = "one-company-scenario-loop-v1"
SCENARIO_COEFFICIENT_BINDING_VERSION = "scenario-coefficient-binding-v1"
SCENARIO_EXPOSURE_CONTRACT_VERSION = "scenario-coefficient-exposure-contract-v1"
_OPERATING_ACTION_IDS = {"priceChange", "capacityInvestment", "borrow", "repay"}
_ASSUMPTION_REF_PREFIXES = ("assumption:", "assumption://")
_DRIVER_COEFFICIENT_ADMISSION_REF_PREFIX = "driverCoefficientAdmission:"
_PROVIDER_OBSERVATION_REF_PREFIXES = ("providerObservationBatch:", "providerObservationBatchId:")
_STATE_REF_PREFIXES = (
    "compiledState:",
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
class OperatingScenarioCaseResult:
    """Run output and audit envelope for one scenario case."""

    caseId: str
    label: str
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
    policyEvaluationCertificateId: str
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
        object.__setattr__(self, "bridgeHashes", tuple(self.bridgeHashes))
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
    explicitAssumptionIds: tuple[str, ...]
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
    policyEvaluationCertificateId: str
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
        object.__setattr__(self, "explicitAssumptionIds", tuple(self.explicitAssumptionIds))
        object.__setattr__(self, "exposureLedgers", tuple(self.exposureLedgers))
        object.__setattr__(self, "coefficientAdmissionReceiptIds", tuple(self.coefficientAdmissionReceiptIds))
        object.__setattr__(self, "coefficientBindingHashes", tuple(self.coefficientBindingHashes))
        object.__setattr__(self, "coefficientParentReceiptIds", tuple(self.coefficientParentReceiptIds))
        object.__setattr__(self, "bridgeHashes", tuple(self.bridgeHashes))
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


def _explicitAssumptionIds(warnings: tuple[str, ...]) -> tuple[str, ...]:
    prefix = "explicitAssumption:"
    return _dedupe(tuple(warning[len(prefix) :] for warning in warnings if warning.startswith(prefix)))


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


def _caseBlockedReasons(result: OperatingScenarioCaseResult) -> tuple[str, ...]:
    reasons = []
    if result.decisionStatus != "comparable":
        reasons.append(f"decisionStatus:{result.decisionStatus}")
    if result.recommendation is None:
        reasons.append("caseRecommendationClosed")
    if result.counts.explicitAssumptionCount:
        reasons.append("explicitAssumptionPresent")
    if result.counts.unvalidatedPathCount:
        reasons.append("unvalidatedPathPresent")
    if result.counts.retrospectivePathCount:
        reasons.append("retrospectiveOnlyPathPresent")
    if result.counts.admittedPathCount < result.counts.pathCount:
        reasons.append("pathAdmissionIncomplete")
    if result.counts.conditionalWarningCount:
        reasons.append("conditionalWarningPresent")
    if not result.initialStateAdmissionReceiptId:
        reasons.append("initialStateAdmissionMissing")
    if not result.pathAdmissionReceiptId:
        reasons.append("pathAdmissionMissing")
    if not result.policyEvaluationCertificateId:
        reasons.append("policyEvaluationCertificateMissing")
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


def _caseLedger(
    case: OperatingScenarioCase,
    result: OperatingScenarioCaseResult,
    *,
    initialStateRefs: tuple[str, ...],
) -> OneCompanyScenarioCaseLedger:
    conditionRefs = _dedupe(result.refs)
    assumptionRefs = _filterRefs(conditionRefs, _ASSUMPTION_REF_PREFIXES)
    stateRefs = _dedupe((*initialStateRefs, *_filterRefs(conditionRefs, _STATE_REF_PREFIXES)))
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
        pathSourceRefs=case.pathSet.audit.sourceRefs,
        providerObservationBatchRefs=_filterRefs(case.pathSet.audit.sourceRefs, _PROVIDER_OBSERVATION_REF_PREFIXES),
        explicitAssumptionIds=_explicitAssumptionIds(case.pathSet.audit.warnings),
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
        policyEvaluationCertificateId=result.policyEvaluationCertificateId,
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


def _runCase(
    inputs: OperatingWorldInputs,
    case: OperatingScenarioCase,
    strategies: tuple[StrategySpec, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    traceLimit: int | None,
) -> OperatingScenarioCaseResult:
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
    run = runOperatingStrategies(
        inputs,
        tuple(item.path for item in bridgeResults),
        strategies,
        debtLimit=debtLimit,
        maxFinancing=maxFinancing,
        maxInvestment=maxInvestment,
        traceLimit=traceLimit,
    )
    bridgeHashes = tuple(item.audit.bridgeHash for item in bridgeResults)
    bridgeWarnings = tuple(warning for item in bridgeResults for warning in item.audit.warnings)
    refs = _dedupe(
        (
            *case.refs,
            *_coefficientBindingRefs(case.coefficientBindings),
            *case.pathSet.audit.sourceRefs,
            *(ref for item in bridgeResults for ref in item.audit.sourceRefs),
            f"driverPathSet:{case.pathSet.audit.pathSetHash}",
            f"scenarioCase:{case.caseId}",
        )
    )
    warnings = tuple(sorted(set((*case.pathSet.audit.warnings, *bridgeWarnings, *run.warnings))))
    return OperatingScenarioCaseResult(
        caseId=case.caseId,
        label=case.label,
        pathSetHash=case.pathSet.audit.pathSetHash,
        bridgeHashes=bridgeHashes,
        runHash=run.runHash,
        resultHash=run.resultHash,
        executableHash=run.executableHash,
        parameterHash=run.parameterHash,
        dataVintageHash=run.dataVintageHash,
        traceRoot=run.traceRoot,
        traceCount=run.traceCount,
        retainedTraceCount=run.retainedTraceCount,
        initialStateAdmissionReceiptId=run.initialStateAdmissionReceiptId,
        pathAdmissionReceiptId=run.pathAdmissionReceiptId,
        policyEvaluationCertificateId=run.policyEvaluationCertificateId,
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
