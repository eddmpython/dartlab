"""Kill tests for typed initial-state artifacts and policy applicability support."""

from dataclasses import replace

import pytest

from dartlab.simulate.stateSupport import (
    StatePrimitive,
    StateSupportError,
    buildEmpiricalStateSupport,
    stateAdmissionArtifact,
    stateAdmissionSubjectHash,
    validateEmpiricalStateSupport,
)


def _state(first: float, second: float, *, unit: str = "ratio") -> tuple[StatePrimitive, ...]:
    return (
        StatePrimitive("financial.leverage", unit, "state", first),
        StatePrimitive("market.stress", "index", "metric", second),
    )


def testStateSupportIsOrderIndependentAndAcceptsKnownOrigin() -> None:
    origins = tuple(_state(index / 39, index / 39) for index in range(40))
    first = buildEmpiricalStateSupport(origins)
    second = buildEmpiricalStateSupport(tuple(reversed(origins)))
    assert first == second
    assert validateEmpiricalStateSupport(origins[20], origins, first) == 0.0


def testMarginalAndJointExtrapolationFailClosed() -> None:
    origins = tuple(_state(index / 39, index / 39) for index in range(40))
    support = buildEmpiricalStateSupport(origins)
    with pytest.raises(StateSupportError, match="marginal"):
        validateEmpiricalStateSupport(_state(1.01, 1.01), origins, support)
    with pytest.raises(StateSupportError, match="joint"):
        validateEmpiricalStateSupport(_state(0.5, 0.9), origins, support)


def testUnitDriftAndCallerEditedRadiusFailClosed() -> None:
    origins = tuple(_state(index / 39, index / 39) for index in range(40))
    support = buildEmpiricalStateSupport(origins)
    with pytest.raises(StateSupportError, match="contract"):
        validateEmpiricalStateSupport(_state(0.5, 0.5, unit="percent"), origins, support)
    meaningDrift = (
        replace(origins[20][0], timing="flow", evidenceRole="explicitAssumption"),
        origins[20][1],
    )
    with pytest.raises(StateSupportError, match="contract"):
        validateEmpiricalStateSupport(meaningDrift, origins, support)
    with pytest.raises(StateSupportError, match="artifact"):
        validateEmpiricalStateSupport(
            _state(0.5, 0.5),
            origins,
            replace(support, neighborDistanceLimit=1.0),
        )


def testInitialStateArtifactBindsValueAndDecisionCutoff() -> None:
    state = _state(0.5, 0.5)
    artifact = stateAdmissionArtifact(
        state,
        asOf="2024Q4",
        knowledgeAsOf="20250301",
        decisionAsOf="20250302",
    )
    subject = stateAdmissionSubjectHash(
        state,
        asOf="2024Q4",
        knowledgeAsOf="20250301",
        decisionAsOf="20250302",
    )
    assert len(artifact) > 0
    assert len(subject) == 64
    assert subject != stateAdmissionSubjectHash(
        _state(0.6, 0.5),
        asOf="2024Q4",
        knowledgeAsOf="20250301",
        decisionAsOf="20250302",
    )
    assert subject != stateAdmissionSubjectHash(
        state,
        asOf="2024Q4",
        knowledgeAsOf="20250301",
        decisionAsOf="20250303",
    )
