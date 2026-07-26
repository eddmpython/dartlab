"""Feature registry, observation, PIT query 의 공통 계약 계층.

simulator 와 외부 작업대가 같은 feature 의미와 시점 선택 규칙을 공유한다.
"""

from __future__ import annotations

from dartlab.dataHub.feature.observation import (
    FeatureObservationError,
    VariableObservation,
    makeVariableObservation,
    validateVariableObservation,
)
from dartlab.dataHub.feature.query import (
    FeatureObservationSet,
    FeatureQueryError,
    FeatureReadQuery,
    FeatureReadResult,
    FeatureSelection,
    buildFeatureObservationSet,
    featureObservationSetFromValue,
    readFeatures,
)
from dartlab.dataHub.feature.registry import (
    StateVariableError,
    StateVariableRegistry,
    StateVariableSpec,
    buildStateVariableRegistry,
    stateVariableContractHash,
)

__all__ = [
    "FeatureObservationError",
    "FeatureObservationSet",
    "FeatureQueryError",
    "FeatureReadQuery",
    "FeatureReadResult",
    "FeatureSelection",
    "StateVariableError",
    "StateVariableRegistry",
    "StateVariableSpec",
    "VariableObservation",
    "buildFeatureObservationSet",
    "buildStateVariableRegistry",
    "featureObservationSetFromValue",
    "makeVariableObservation",
    "readFeatures",
    "stateVariableContractHash",
    "validateVariableObservation",
]
