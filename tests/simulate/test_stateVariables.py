from __future__ import annotations

from dataclasses import replace

import pytest

from dartlab.simulate.stateVariables import (
    StateVariableError,
    StateVariableSpec,
    buildStateVariableRegistry,
    stateVariableContractHash,
)


def _spec(variableId: str = "financial.revenue") -> StateVariableSpec:
    return StateVariableSpec(
        variableId=variableId,
        signalId=variableId,
        providerId="edgar",
        datasetId="quarterly-financial",
        unit="USD",
        role="state",
        evidenceRole="observed",
        frequency="quarter",
        timing="flow" if variableId.endswith("revenue") else "stock",
        transformId="level-v1",
        maxStalenessDays=400,
    )


def testStateVariableRegistryIsOrderIndependentAndMeaningSensitive() -> None:
    revenue = _spec()
    cash = _spec("financial.cash")
    assert buildStateVariableRegistry((revenue, cash)) == buildStateVariableRegistry((cash, revenue))
    assert (
        buildStateVariableRegistry((replace(revenue, frequency="year"),)).registryHash
        != buildStateVariableRegistry((revenue,)).registryHash
    )
    assert stateVariableContractHash(
        (replace(revenue, evidenceRole="explicitAssumption"),)
    ) != stateVariableContractHash((revenue,))


def testStateVariableRegistryRejectsDuplicateAndInvalidMeaning() -> None:
    revenue = _spec()
    with pytest.raises(StateVariableError, match="unique"):
        buildStateVariableRegistry((revenue, revenue))
    with pytest.raises(StateVariableError, match="meaning"):
        buildStateVariableRegistry((replace(revenue, role="shock"),))
    with pytest.raises(StateVariableError, match="bounds"):
        buildStateVariableRegistry((replace(revenue, lower=1.0, upper=0.0),))


def testStateVariableContractSeparatesFlowStockAndTransform() -> None:
    revenue = _spec()
    base = stateVariableContractHash((revenue,))
    assert stateVariableContractHash((replace(revenue, timing="stock"),)) != base
    assert stateVariableContractHash((replace(revenue, transformId="ttm-level-v1"),)) != base
