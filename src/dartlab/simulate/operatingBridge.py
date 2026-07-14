"""Compile typed factor paths into auditable operating-world shock paths.

The bridge is the law boundary between exogenous conditions and the operating
world. It does not forecast factor paths or certify causal effects. It applies
documented baselines, unit-checked transmission exposures, optional PIT state
modifiers, and explicit lag kernels to produce a path that ``operatingWorld``
can execute.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

from dartlab.simulate.stateCompiler import CompiledPointInTimeState
from dartlab.simulate.stateSupport import StatePrimitive, stateContractHash
from dartlab.simulate.vintage import VintageError, canonicalPayloadHash, isExactAsKnown, validateVintageRef
from dartlab.simulate.world import PATH_VALIDATION_SET, WEIGHT_KIND_SET, ScenarioPath

OPERATING_TARGET_UNITS = {
    "marketPriceChange": "ratioChangePerStep",
    "demandChange": "ratioChangePerStep",
    "unitCostChange": "ratioChangePerStep",
    "fixedCostChange": "ratioChangePerStep",
    "capacityChange": "ratioChangePerStep",
    "debtRate": "effectiveRatePerStep",
}
OPERATING_TARGET_SHOCKS = set(OPERATING_TARGET_UNITS)
_RATIO_TARGETS = OPERATING_TARGET_SHOCKS - {"debtRate"}
_FACTOR_TIMINGS = {"innovation", "change", "level", "rate"}
_LAW_EVIDENCE_KINDS = {"measuredAssociation", "identifiedIntervention", "explicitAssumption"}
_BASELINE_EVIDENCE_ROLES = {
    "observed",
    "deterministicDerived",
    "admittedEstimate",
    "explicitAssumption",
    "derivedFromAssumption",
}
_EXECUTABLE_STATE_EVIDENCE = _BASELINE_EVIDENCE_ROLES
_EXECUTABLE_MODIFIER_ROLES = {"state", "observedFeature"}


class OperatingBridgeError(ValueError):
    """팩터 경로, 상태 modifier 또는 운영 shock 변환 계약이 잘못되면 발생한다."""


@dataclass(frozen=True)
class OperatingFactorSpec:
    """Meaning contract for one variable carried by a source path.

    Args:
        variableId: Identifier present in every source path step.
        unit: Source value unit used to validate exposure coefficients.
        frequency: Source time grid, which must match the path frequency.
        timing: Level, rate, change, or innovation interpretation.
        transformId: Stable transform that produced the path value.

    Returns:
        Dataclass consumed by ``bridgeOperatingPath``.

    Raises:
        Errors are raised by the bridge compiler, not this plain container.

    Example:
        ``OperatingFactorSpec("fxChange", "simpleReturn", "quarter", "innovation", "simple-return-v1")``
    """

    variableId: str
    unit: str
    frequency: str
    timing: str
    transformId: str


@dataclass(frozen=True)
class OperatingShockBaseline:
    """Explicit additive baseline for one operating shock channel.

    Args:
        targetShock: Operating shock consumed by ``operatingWorld``.
        value: Baseline value before factor transmission is added.
        unit: Exact unit declared by ``OPERATING_TARGET_UNITS``.
        evidenceRole: Observation, derivation, estimate, or explicit assumption role.
        sourceRef: Filing, state, model, or assumption reference.

    Returns:
        Dataclass that prevents silent zero defaults in the bridge.

    Raises:
        Errors are raised by the bridge compiler, not this plain container.

    Example:
        ``OperatingShockBaseline("debtRate", 0.04, "effectiveRatePerStep", "observed", "filing://debt-rate")``
    """

    targetShock: str
    value: float
    unit: str
    evidenceRole: str
    sourceRef: str


@dataclass(frozen=True)
class OperatingTransmissionExposure:
    """One directed factor to operating-shock transmission contract.

    Args:
        exposureId: Stable exposure identifier.
        sourceVariableId: Factor variable expected in every source path step.
        targetShock: Operating shock target consumed by ``operatingWorld``.
        coefficient: Linear pass-through coefficient before the response kernel.
        coefficientUnit: Exact ``targetUnit/sourceUnit`` dimension label.
        evidenceKind: Association, identified intervention, or explicit assumption boundary.
        sourceRef: Filing, fitted-law, receipt, or assumption reference.
        modifierVariableId: Optional PIT state primitive that scales the coefficient.
        modifierUnit: Required unit for the modifier primitive when present.
        lagSteps: Whole source-path steps before the first response.
        responseKernel: Ordered response weights starting at ``lagSteps``.
        aggregationGroup: Required unique group when one source-target pair is repeated.
        status: Exposure status, currently only ``active`` executes.

    Returns:
        Dataclass used by ``bridgeOperatingPath``.

    Raises:
        Errors are raised by the bridge compiler, not this plain container.

    Example:
        ``OperatingTransmissionExposure("fx-price", "fxChange", "marketPriceChange", 0.5, "ratioChangePerStep/simpleReturn", "explicitAssumption", "assumption://fx")``
    """

    exposureId: str
    sourceVariableId: str
    targetShock: str
    coefficient: float
    coefficientUnit: str
    evidenceKind: str
    sourceRef: str
    modifierVariableId: str = ""
    modifierUnit: str = ""
    lagSteps: int = 0
    responseKernel: tuple[float, ...] = (1.0,)
    aggregationGroup: str = ""
    status: str = "active"

    def __post_init__(self) -> None:
        object.__setattr__(self, "responseKernel", tuple(self.responseKernel))


@dataclass(frozen=True)
class OperatingBridgeAudit:
    """Audit record for one factor to operating shock compilation.

    Args:
        bridgeHash: Content hash over inputs, contracts, state, and produced steps.
        sourcePathId: Input path identifier.
        sourcePathContentHash: Recomputed content hash of the complete source path.
        sourceAdmissionContentHash: Optional independently admitted source content hash.
        sourcePathCertificateId: Optional source path-measure certificate identifier.
        sourceAdmissionReceiptId: Optional source path-set admission receipt identifier.
        sourcePathValidationStatus: Validation status before bridge compilation.
        sourceParameterDrawReceiptId: Source draw receipt retained in audit but not transferred.
        factorContractHash: Ordered factor meaning contract hash.
        stateRef: PIT state or explicit primitive reference used by modifiers.
        stateContractHash: Typed state contract hash without values.
        stateContentHash: Typed state content hash including values.
        exposureIds: Ordered exposure identifiers.
        baselineTargets: Ordered explicitly covered operating channels.
        targetShocks: Operating shock targets produced by the bridge.
        ignoredSourceFactors: Typed factors with no operating exposure.
        validationStatus: Honest output status after the unadmitted bridge law.
        warnings: Assumption, truncation, and honest-gap labels.
        sourceRefs: Full input and compiler reference set carried into the output.
        knowledgeAsOf: Source path knowledge cutoff.
        historyStatus: Source path history status.

    Returns:
        Dataclass attached to ``OperatingBridgeResult``.

    Raises:
        Errors are raised by the bridge compiler, not this plain container.

    Example:
        ``audit.validationStatus == "retrospectiveOnly"``
    """

    bridgeHash: str
    sourcePathId: str
    sourcePathContentHash: str
    sourceAdmissionContentHash: str
    sourcePathCertificateId: str
    sourceAdmissionReceiptId: str
    sourcePathValidationStatus: str
    sourceParameterDrawReceiptId: str
    factorContractHash: str
    stateRef: str
    stateContractHash: str
    stateContentHash: str
    exposureIds: tuple[str, ...]
    baselineTargets: tuple[str, ...]
    targetShocks: tuple[str, ...]
    ignoredSourceFactors: tuple[str, ...]
    validationStatus: str
    warnings: tuple[str, ...]
    sourceRefs: tuple[str, ...]
    knowledgeAsOf: str
    historyStatus: str


@dataclass(frozen=True)
class OperatingBridgeResult:
    """Produced operating path and its audit ledger.

    Args:
        path: Operating scenario path ready for ``runOperatingStrategies``.
        audit: Bridge contract, warning, and lineage record.

    Returns:
        Dataclass returned by ``bridgeOperatingPath``.

    Raises:
        Errors are raised by the bridge compiler, not this plain container.

    Example:
        ``result.path.steps[0]["demandChange"]``
    """

    path: ScenarioPath
    audit: OperatingBridgeAudit


def _finite(value: float | None, label: str) -> float:
    if value is None:
        raise OperatingBridgeError(f"{label} is missing")
    number = float(value)
    if not math.isfinite(number):
        raise OperatingBridgeError(f"{label} must be finite")
    return number


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise OperatingBridgeError(f"invalid {label}: {value}")
    return text


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _compiledPrimitiveState(
    compiledState: CompiledPointInTimeState | None,
    statePrimitives: tuple[StatePrimitive, ...],
    stateRef: str,
) -> tuple[tuple[StatePrimitive, ...], str, tuple[str, ...], tuple[str, ...]]:
    if compiledState is not None:
        if statePrimitives or stateRef:
            raise OperatingBridgeError("compiled state cannot be mixed with manual bridge state")
        effectiveRef = compiledState.stateReceiptId or compiledState.manifestHash or compiledState.stateId
        refs = _dedupe(
            (
                f"compiledState:{compiledState.stateId}",
                f"stateManifest:{compiledState.manifestHash}",
                f"stateReceipt:{compiledState.stateReceiptId}" if compiledState.stateReceiptId else "",
                *(f"providerBatchReceipt:{item}" for item in compiledState.providerBatchReceiptIds),
                *(f"providerBatch:{item}" for item in compiledState.providerBatchIds),
                *(f"stateObservation:{item}" for item in compiledState.selectedObservationIds),
            )
        )
        warnings = tuple(f"compiledStateLimitation:{item}" for item in compiledState.limitations)
        if compiledState.historyStatus != "exact":
            warnings += (f"compiledStateHistory:{compiledState.historyStatus}",)
        if compiledState.admissionStatus != "admitted":
            warnings += (f"compiledStateAdmission:{compiledState.admissionStatus}",)
        else:
            warnings += ("compiledStateAdmission:admittedUnverifiedByBridge",)
        return compiledState.statePrimitives, effectiveRef, refs, warnings
    primitives = tuple(statePrimitives)
    if bool(primitives) != bool(stateRef):
        raise OperatingBridgeError("manual bridge state needs both primitives and stateRef")
    refs = (stateRef,) if stateRef else ()
    return primitives, stateRef, refs, ()


def _stateById(primitives: tuple[StatePrimitive, ...]) -> Mapping[str, StatePrimitive]:
    if len({item.variableId for item in primitives}) != len(primitives):
        raise OperatingBridgeError("operating bridge state modifiers need unique variableIds")
    return {item.variableId: item for item in primitives}


def _validateFactorSpecs(
    sourcePath: ScenarioPath, factorSpecs: tuple[OperatingFactorSpec, ...]
) -> dict[str, OperatingFactorSpec]:
    specs = tuple(factorSpecs)
    if not specs or len({item.variableId for item in specs}) != len(specs):
        raise OperatingBridgeError("operating bridge needs unique factor specs")
    for item in specs:
        if (
            not item.variableId
            or not item.unit
            or not item.frequency
            or item.timing not in _FACTOR_TIMINGS
            or not item.transformId
        ):
            raise OperatingBridgeError(f"operating factor contract is incomplete: {item.variableId}")
        if item.frequency != sourcePath.frequency:
            raise OperatingBridgeError(f"operating factor frequency drift: {item.variableId}")
    return {item.variableId: item for item in specs}


def _validateSourcePath(sourcePath: ScenarioPath, factors: Mapping[str, OperatingFactorSpec]) -> str:
    if not sourcePath.pathId:
        raise OperatingBridgeError("operating bridge source path needs pathId")
    if not sourcePath.steps:
        raise OperatingBridgeError("operating bridge needs at least one source step")
    if sourcePath.validationStatus not in PATH_VALIDATION_SET:
        raise OperatingBridgeError("operating bridge source validation status is invalid")
    if sourcePath.validationStatus == "rejected":
        raise OperatingBridgeError("rejected source path cannot enter operating bridge")
    if not sourcePath.refs:
        raise OperatingBridgeError("operating bridge source path needs refs")
    if not sourcePath.frequency or sourcePath.stepSpan < 1:
        raise OperatingBridgeError("operating bridge source path needs a step contract")
    if sourcePath.weightKind not in WEIGHT_KIND_SET:
        raise OperatingBridgeError("operating bridge source weight kind is invalid")
    if sourcePath.weightKind == "unweighted" and sourcePath.weight is not None:
        raise OperatingBridgeError("unweighted operating source path cannot carry a weight")
    if sourcePath.weightKind != "unweighted":
        if sourcePath.weight is None or _finite(sourcePath.weight, "source weight") <= 0.0:
            raise OperatingBridgeError("weighted operating source path needs a positive weight")
    knowledgeAsOf = _dateText(sourcePath.knowledgeAsOf, "source knowledgeAsOf")
    if not sourcePath.historyStatus:
        raise OperatingBridgeError("operating bridge source path needs historyStatus")
    if sourcePath.vintage is not None:
        try:
            validateVintageRef(sourcePath.vintage, decisionAsOf=knowledgeAsOf)
        except VintageError as error:
            raise OperatingBridgeError(str(error)) from error
        if sourcePath.vintage.knowledgeAsOf != knowledgeAsOf:
            raise OperatingBridgeError("operating bridge source vintage cutoff drift")
    expected = set(factors)
    for stepIndex, step in enumerate(sourcePath.steps):
        if set(step) != expected:
            raise OperatingBridgeError(f"operating source factor coverage drift at step {stepIndex}")
        for variableId, value in step.items():
            _finite(value, f"source.{variableId}.{stepIndex}")
    if sourcePath.validationStatus == "admitted":
        if (
            not _validDigest(sourcePath.certificateId)
            or not _validDigest(sourcePath.admissionContentHash)
            or not _validDigest(sourcePath.admissionReceiptId)
            or sourcePath.maxAdmittedStep < len(sourcePath.steps)
            or sourcePath.historyStatus != "asKnown"
            or sourcePath.vintage is None
            or not isExactAsKnown(sourcePath.vintage)
            or not _validDigest(sourcePath.vintage.receiptId)
        ):
            raise OperatingBridgeError("admitted source path contract is incomplete")
    if sourcePath.weightKind == "calibrated" and sourcePath.validationStatus != "admitted":
        raise OperatingBridgeError("calibrated operating source path must be admitted")
    return canonicalPayloadHash(
        {
            "pathId": sourcePath.pathId,
            "steps": sourcePath.steps,
            "weight": sourcePath.weight,
            "weightKind": sourcePath.weightKind,
            "refs": sourcePath.refs,
            "frequency": sourcePath.frequency,
            "stepSpan": sourcePath.stepSpan,
            "certificateId": sourcePath.certificateId,
            "validationStatus": sourcePath.validationStatus,
            "maxAdmittedStep": sourcePath.maxAdmittedStep,
            "admissionContentHash": sourcePath.admissionContentHash,
            "parameterDraws": sourcePath.parameterDraws,
            "parameterDrawReceipt": sourcePath.parameterDrawReceipt,
            "knowledgeAsOf": sourcePath.knowledgeAsOf,
            "historyStatus": sourcePath.historyStatus,
            "vintage": sourcePath.vintage,
            "admissionReceiptId": sourcePath.admissionReceiptId,
        }
    )


def _validateBaselines(baselines: tuple[OperatingShockBaseline, ...]) -> dict[str, OperatingShockBaseline]:
    byTarget = {item.targetShock: item for item in baselines}
    if len(byTarget) != len(baselines) or set(byTarget) != OPERATING_TARGET_SHOCKS:
        raise OperatingBridgeError("operating shock baseline coverage must be exact")
    for targetShock, item in byTarget.items():
        expectedUnit = OPERATING_TARGET_UNITS[targetShock]
        if item.unit != expectedUnit:
            raise OperatingBridgeError(f"operating baseline unit drift: {targetShock}")
        if item.evidenceRole not in _BASELINE_EVIDENCE_ROLES or not item.sourceRef:
            raise OperatingBridgeError(f"operating baseline evidence is incomplete: {targetShock}")
        _validateTargetValue(targetShock, item.value, -1)
    return byTarget


def _validateExposure(
    exposure: OperatingTransmissionExposure,
    factors: Mapping[str, OperatingFactorSpec],
) -> None:
    if (
        not exposure.exposureId
        or exposure.sourceVariableId not in factors
        or exposure.targetShock not in OPERATING_TARGET_SHOCKS
        or exposure.evidenceKind not in _LAW_EVIDENCE_KINDS
        or not exposure.sourceRef
        or exposure.status != "active"
    ):
        raise OperatingBridgeError("operating transmission exposure contract is incomplete")
    _finite(exposure.coefficient, f"exposure.{exposure.exposureId}.coefficient")
    expectedUnit = f"{OPERATING_TARGET_UNITS[exposure.targetShock]}/{factors[exposure.sourceVariableId].unit}"
    if exposure.coefficientUnit != expectedUnit:
        raise OperatingBridgeError(f"operating exposure coefficient unit drift: {exposure.exposureId}")
    if bool(exposure.modifierVariableId) != bool(exposure.modifierUnit):
        raise OperatingBridgeError("modifier exposure needs both variableId and unit")
    if not isinstance(exposure.lagSteps, int) or exposure.lagSteps < 0:
        raise OperatingBridgeError(f"operating exposure lag is invalid: {exposure.exposureId}")
    if not exposure.responseKernel:
        raise OperatingBridgeError(f"operating exposure response kernel is empty: {exposure.exposureId}")
    kernel = tuple(
        _finite(value, f"exposure.{exposure.exposureId}.responseKernel") for value in exposure.responseKernel
    )
    if all(abs(value) <= 1e-15 for value in kernel):
        raise OperatingBridgeError(f"operating exposure response kernel is zero: {exposure.exposureId}")


def _validateExposureSet(exposures: tuple[OperatingTransmissionExposure, ...]) -> None:
    if not exposures or len({item.exposureId for item in exposures}) != len(exposures):
        raise OperatingBridgeError("operating bridge exposure ids must be unique")
    byPair: dict[tuple[str, str], list[OperatingTransmissionExposure]] = {}
    for item in exposures:
        byPair.setdefault((item.sourceVariableId, item.targetShock), []).append(item)
    for pair, group in byPair.items():
        if len(group) == 1:
            continue
        aggregationGroups = [item.aggregationGroup for item in group]
        if not all(aggregationGroups) or len(set(aggregationGroups)) != len(aggregationGroups):
            raise OperatingBridgeError(f"duplicate operating exposure needs unique aggregation groups: {pair}")


def _modifierValue(
    exposure: OperatingTransmissionExposure,
    state: Mapping[str, StatePrimitive],
    warnings: list[str],
) -> float:
    if not exposure.modifierVariableId:
        return 1.0
    primitive = state.get(exposure.modifierVariableId)
    if primitive is None:
        raise OperatingBridgeError(f"operating bridge modifier is missing: {exposure.modifierVariableId}")
    if primitive.unit != exposure.modifierUnit:
        raise OperatingBridgeError(f"operating bridge modifier unit drift: {exposure.modifierVariableId}")
    if primitive.role not in _EXECUTABLE_MODIFIER_ROLES:
        raise OperatingBridgeError(f"operating bridge modifier role drift: {exposure.modifierVariableId}")
    if primitive.evidenceRole not in _EXECUTABLE_STATE_EVIDENCE:
        raise OperatingBridgeError(
            f"operating bridge modifier evidence is not executable: {exposure.modifierVariableId}"
        )
    if primitive.evidenceRole in {"explicitAssumption", "derivedFromAssumption"}:
        warnings.append(f"modifierAssumption:{primitive.variableId}")
    if primitive.evidenceRole == "admittedEstimate":
        warnings.append(f"modifierEstimate:{primitive.variableId}")
    return _finite(primitive.value, f"modifier.{primitive.variableId}")


def _validateTargetValue(targetShock: str, value: float, stepIndex: int) -> float:
    number = _finite(value, f"operatingTarget.{targetShock}.{stepIndex}")
    if targetShock in _RATIO_TARGETS and number < -1.0:
        raise OperatingBridgeError(f"operating bridge target below physical floor: {targetShock}")
    if targetShock == "debtRate" and (number < 0.0 or number > 1.0):
        raise OperatingBridgeError("operating bridge debtRate is outside [0, 1]")
    return number


def _responseAt(
    sourcePath: ScenarioPath,
    exposure: OperatingTransmissionExposure,
    stepIndex: int,
) -> float:
    response = 0.0
    for kernelIndex, kernelWeight in enumerate(exposure.responseKernel):
        sourceIndex = stepIndex - exposure.lagSteps - kernelIndex
        if sourceIndex < 0:
            continue
        sourceValue = _finite(
            sourcePath.steps[sourceIndex][exposure.sourceVariableId],
            f"source.{exposure.sourceVariableId}.{sourceIndex}",
        )
        response += sourceValue * float(kernelWeight)
    return response


def bridgeOperatingPath(
    sourcePath: ScenarioPath,
    exposures: tuple[OperatingTransmissionExposure, ...],
    *,
    factorSpecs: tuple[OperatingFactorSpec, ...],
    baselines: tuple[OperatingShockBaseline, ...],
    compiledState: CompiledPointInTimeState | None = None,
    statePrimitives: tuple[StatePrimitive, ...] = (),
    stateRef: str = "",
    pathId: str | None = None,
) -> OperatingBridgeResult:
    """Translate a typed factor path into an executable operating shock path.

    Args:
        sourcePath: Complete factor path with refs, cutoff, history, and validation status.
        exposures: Unit-checked directed factor transmission contracts.
        factorSpecs: Exact meaning contract for every variable in every source step.
        baselines: Exact baseline coverage for all six operating shock channels.
        compiledState: Optional PIT state manifest for modifier primitives.
        statePrimitives: Optional explicit primitive tuple when no compiled state is available.
        stateRef: Required reference when passing explicit primitives.
        pathId: Optional output path id. Defaults to ``operating-{sourcePath.pathId}``.

    Returns:
        ``OperatingBridgeResult`` with a path consumable by the operating world.

    Raises:
        OperatingBridgeError: If source status, factor meaning, state, or physical bounds fail.

    Example:
        ``result = bridgeOperatingPath(path, exposures, factorSpecs=factors, baselines=baselines)``
    """

    factors = _validateFactorSpecs(sourcePath, factorSpecs)
    sourcePathContentHash = _validateSourcePath(sourcePath, factors)
    baselineByTarget = _validateBaselines(tuple(baselines))
    exposures = tuple(exposures)
    primitives, effectiveStateRef, stateRefs, stateWarnings = _compiledPrimitiveState(
        compiledState,
        tuple(statePrimitives),
        stateRef,
    )
    state = _stateById(primitives)
    warnings = list(stateWarnings)
    for exposure in exposures:
        _validateExposure(exposure, factors)
        warnings.append(f"bridgeEvidence:{exposure.evidenceKind}")
        if exposure.lagSteps or len(exposure.responseKernel) > 1:
            warnings.append(f"truncatedResponseTail:{exposure.exposureId}")
    _validateExposureSet(exposures)
    baselineTargets = tuple(sorted(baselineByTarget))
    for baseline in baselineByTarget.values():
        if baseline.evidenceRole in {"explicitAssumption", "derivedFromAssumption"}:
            warnings.append(f"baselineAssumption:{baseline.targetShock}")
        elif baseline.evidenceRole == "admittedEstimate":
            warnings.append(f"baselineEstimate:{baseline.targetShock}")
    exposureScales = {exposure.exposureId: _modifierValue(exposure, state, warnings) for exposure in exposures}
    usedFactors = {item.sourceVariableId for item in exposures}
    ignoredSourceFactors = tuple(sorted(set(factors) - usedFactors))
    warnings.extend(f"unusedSourceFactor:{item}" for item in ignoredSourceFactors)
    if sourcePath.validationStatus == "unvalidated":
        validationStatus = "unvalidated"
        warnings.append("sourceValidation:unvalidated")
    else:
        validationStatus = "retrospectiveOnly"
        warnings.append(f"sourceValidation:{sourcePath.validationStatus}")
    if sourcePath.validationStatus == "admitted":
        warnings.append("sourceAdmissionNotTransferredAcrossBridge")
    sourceParameterDrawReceiptId = (
        sourcePath.parameterDrawReceipt.receiptId if sourcePath.parameterDrawReceipt is not None else ""
    )
    if sourcePath.parameterDraws or sourcePath.parameterDrawReceipt is not None:
        warnings.append("sourceParameterDrawsNotTransferred")
    steps = []
    for stepIndex in range(len(sourcePath.steps)):
        targetValues = {targetShock: float(baseline.value) for targetShock, baseline in baselineByTarget.items()}
        for exposure in exposures:
            targetValues[exposure.targetShock] += (
                _responseAt(sourcePath, exposure, stepIndex)
                * float(exposure.coefficient)
                * exposureScales[exposure.exposureId]
            )
        steps.append(
            {
                targetShock: _validateTargetValue(targetShock, value, stepIndex)
                for targetShock, value in targetValues.items()
            }
        )
    factorContractHash = canonicalPayloadHash(tuple(sorted(factorSpecs, key=lambda item: item.variableId)))
    stateContract = stateContractHash(primitives) if primitives else ""
    stateContentHash = (
        canonicalPayloadHash(tuple(sorted(primitives, key=lambda item: item.variableId))) if primitives else ""
    )
    bridgeHash = canonicalPayloadHash(
        {
            "sourcePath": sourcePathContentHash,
            "factorSpecs": factorSpecs,
            "baselines": baselines,
            "exposures": exposures,
            "stateRef": effectiveStateRef,
            "statePrimitives": primitives,
            "outputSteps": tuple(steps),
            "validationStatus": validationStatus,
        }
    )
    refs = _dedupe(
        (
            *sourcePath.refs,
            *(item.sourceRef for item in baselines),
            *(item.sourceRef for item in exposures),
            *stateRefs,
            f"sourcePathContent:{sourcePathContentHash}",
            f"sourcePathCertificate:{sourcePath.certificateId}" if sourcePath.certificateId else "",
            f"sourcePathAdmissionReceipt:{sourcePath.admissionReceiptId}" if sourcePath.admissionReceiptId else "",
            f"sourceParameterDrawReceipt:{sourceParameterDrawReceiptId}" if sourceParameterDrawReceiptId else "",
            f"factorContract:{factorContractHash}",
            f"stateContract:{stateContract}" if stateContract else "",
            f"stateContent:{stateContentHash}" if stateContentHash else "",
            f"operatingBridge:{bridgeHash}",
        )
    )
    cleanWarnings = tuple(sorted(set(warnings)))
    outputPath = ScenarioPath(
        pathId=pathId or f"operating-{sourcePath.pathId}",
        steps=tuple(steps),
        weight=sourcePath.weight,
        weightKind=sourcePath.weightKind,
        refs=refs,
        frequency=sourcePath.frequency,
        stepSpan=sourcePath.stepSpan,
        validationStatus=validationStatus,
        maxAdmittedStep=0,
        parameterDraws={},
        parameterDrawReceipt=None,
        knowledgeAsOf=_dateText(sourcePath.knowledgeAsOf, "source knowledgeAsOf"),
        historyStatus=sourcePath.historyStatus,
        vintage=sourcePath.vintage,
    )
    audit = OperatingBridgeAudit(
        bridgeHash=bridgeHash,
        sourcePathId=sourcePath.pathId,
        sourcePathContentHash=sourcePathContentHash,
        sourceAdmissionContentHash=sourcePath.admissionContentHash,
        sourcePathCertificateId=sourcePath.certificateId,
        sourceAdmissionReceiptId=sourcePath.admissionReceiptId,
        sourcePathValidationStatus=sourcePath.validationStatus,
        sourceParameterDrawReceiptId=sourceParameterDrawReceiptId,
        factorContractHash=factorContractHash,
        stateRef=effectiveStateRef,
        stateContractHash=stateContract,
        stateContentHash=stateContentHash,
        exposureIds=tuple(item.exposureId for item in exposures),
        baselineTargets=baselineTargets,
        targetShocks=baselineTargets,
        ignoredSourceFactors=ignoredSourceFactors,
        validationStatus=validationStatus,
        warnings=cleanWarnings,
        sourceRefs=refs,
        knowledgeAsOf=outputPath.knowledgeAsOf,
        historyStatus=sourcePath.historyStatus,
    )
    return OperatingBridgeResult(outputPath, audit)
