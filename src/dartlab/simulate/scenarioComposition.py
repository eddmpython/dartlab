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
_OPERATING_ACTION_IDS = {"priceChange", "capacityInvestment", "borrow", "repay"}


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
    admissionVerifier: AdmissionVerifier | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "exposures", tuple(self.exposures))
        object.__setattr__(self, "baselines", tuple(self.baselines))
        object.__setattr__(self, "refs", tuple(self.refs))
        object.__setattr__(self, "statePrimitives", tuple(self.statePrimitives))


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
class OperatingScenarioCaseResult:
    """Run output and audit envelope for one scenario case."""

    caseId: str
    label: str
    pathSetHash: str
    bridgeHashes: tuple[str, ...]
    runHash: str
    resultHash: str
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


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


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
