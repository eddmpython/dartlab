"""Scenario composition value types.

`scenarioComposition` held both the record shapes and the orchestration that fills them
in one 7,434 line file. The shapes moved here and split three ways: `paths` is the leaf
receipt layer, `experiment` is one named case and its strategies, `play` is the control
surface a replayed play produces.

Import direction is one way. This package never imports `scenarioComposition`.
"""

from __future__ import annotations

from dartlab.simulate.scenarioCompositionTypes.experiment import (
    ConditionalAssumptionFragility as ConditionalAssumptionFragility,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    ConditionalScenarioExperiment as ConditionalScenarioExperiment,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    ConditionalScenarioExperimentCell as ConditionalScenarioExperimentCell,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    ConditionalStrategyEvaluation as ConditionalStrategyEvaluation,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    ConditionalStrategyEvaluationRow as ConditionalStrategyEvaluationRow,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    ConditionalStrategyFragileCase as ConditionalStrategyFragileCase,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    ConditionalStrategySummary as ConditionalStrategySummary,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    OneCompanyScenarioCaseLedger as OneCompanyScenarioCaseLedger,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    OneCompanyScenarioLoop as OneCompanyScenarioLoop,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    OperatingScenarioCase as OperatingScenarioCase,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    OperatingScenarioCaseResult as OperatingScenarioCaseResult,
)
from dartlab.simulate.scenarioCompositionTypes.experiment import (
    OperatingScenarioComparison as OperatingScenarioComparison,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    _PROVIDER_OBSERVATION_BATCH_ID_REF_PREFIX as _PROVIDER_OBSERVATION_BATCH_ID_REF_PREFIX,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    _PROVIDER_OBSERVATION_BATCH_REF_PREFIX as _PROVIDER_OBSERVATION_BATCH_REF_PREFIX,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    _PROVIDER_OBSERVATION_REF_PREFIXES as _PROVIDER_OBSERVATION_REF_PREFIXES,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND as COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    SCENARIO_PATH_PACKAGE_VERSION as SCENARIO_PATH_PACKAGE_VERSION,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    ScenarioBoundaryCounts as ScenarioBoundaryCounts,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    ScenarioCoefficientBinding as ScenarioCoefficientBinding,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    ScenarioCompositionError as ScenarioCompositionError,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    ScenarioDriverRegistryLedger as ScenarioDriverRegistryLedger,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    ScenarioExposureLedger as ScenarioExposureLedger,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    ScenarioProviderLineageLedger as ScenarioProviderLineageLedger,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    ScenarioStrategyScore as ScenarioStrategyScore,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    _dedupe as _dedupe,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    _explicitAssumptionIds as _explicitAssumptionIds,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    _filterRefs as _filterRefs,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    _scenarioPathCompositionContractHash as _scenarioPathCompositionContractHash,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    _scenarioPathRows as _scenarioPathRows,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    scenarioPathPackageParentReceiptIds as scenarioPathPackageParentReceiptIds,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    scenarioPathPackagePayload as scenarioPathPackagePayload,
)
from dartlab.simulate.scenarioCompositionTypes.paths import (
    scenarioPathPackageSubjectHash as scenarioPathPackageSubjectHash,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    CONDITIONAL_PLAY_CONTROL_SURFACE_PLANES as CONDITIONAL_PLAY_CONTROL_SURFACE_PLANES,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayBlockerRow as ConditionalPlayBlockerRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayCaseLeaderDeltaRow as ConditionalPlayCaseLeaderDeltaRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayCellRow as ConditionalPlayCellRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayConditionRow as ConditionalPlayConditionRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayControlExecutionReport as ConditionalPlayControlExecutionReport,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayControlImpactRow as ConditionalPlayControlImpactRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayControlPatch as ConditionalPlayControlPatch,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayControlRebaseRow as ConditionalPlayControlRebaseRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayControlRow as ConditionalPlayControlRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayControlSurface as ConditionalPlayControlSurface,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayLeaderTransition as ConditionalPlayLeaderTransition,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayReplayReport as ConditionalPlayReplayReport,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayScenarioDeckReport as ConditionalPlayScenarioDeckReport,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayStrategyDeltaRow as ConditionalPlayStrategyDeltaRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayStrategyRow as ConditionalPlayStrategyRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    ConditionalPlayTraceRow as ConditionalPlayTraceRow,
)
from dartlab.simulate.scenarioCompositionTypes.play import (
    _ConditionalPlayPatchedBundle as _ConditionalPlayPatchedBundle,
)

__all__ = [
    "COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND",
    "CONDITIONAL_PLAY_CONTROL_SURFACE_PLANES",
    "ConditionalAssumptionFragility",
    "ConditionalPlayBlockerRow",
    "ConditionalPlayCaseLeaderDeltaRow",
    "ConditionalPlayCellRow",
    "ConditionalPlayConditionRow",
    "ConditionalPlayControlExecutionReport",
    "ConditionalPlayControlImpactRow",
    "ConditionalPlayControlPatch",
    "ConditionalPlayControlRebaseRow",
    "ConditionalPlayControlRow",
    "ConditionalPlayControlSurface",
    "ConditionalPlayLeaderTransition",
    "ConditionalPlayReplayReport",
    "ConditionalPlayScenarioDeckReport",
    "ConditionalPlayStrategyDeltaRow",
    "ConditionalPlayStrategyRow",
    "ConditionalPlayTraceRow",
    "ConditionalScenarioExperiment",
    "ConditionalScenarioExperimentCell",
    "ConditionalStrategyEvaluation",
    "ConditionalStrategyEvaluationRow",
    "ConditionalStrategyFragileCase",
    "ConditionalStrategySummary",
    "OneCompanyScenarioCaseLedger",
    "OneCompanyScenarioLoop",
    "OperatingScenarioCase",
    "OperatingScenarioCaseResult",
    "OperatingScenarioComparison",
    "SCENARIO_PATH_PACKAGE_VERSION",
    "ScenarioBoundaryCounts",
    "ScenarioCoefficientBinding",
    "ScenarioCompositionError",
    "ScenarioDriverRegistryLedger",
    "ScenarioExposureLedger",
    "ScenarioProviderLineageLedger",
    "ScenarioStrategyScore",
    "_ConditionalPlayPatchedBundle",
    "_PROVIDER_OBSERVATION_BATCH_ID_REF_PREFIX",
    "_PROVIDER_OBSERVATION_BATCH_REF_PREFIX",
    "_PROVIDER_OBSERVATION_REF_PREFIXES",
    "_dedupe",
    "_explicitAssumptionIds",
    "_filterRefs",
    "_scenarioPathCompositionContractHash",
    "_scenarioPathRows",
    "scenarioPathPackageParentReceiptIds",
    "scenarioPathPackagePayload",
    "scenarioPathPackageSubjectHash",
]
