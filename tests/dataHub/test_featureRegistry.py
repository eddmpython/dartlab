"""Provider-neutral feature registry 정본과 simulate 호환성 tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

import dartlab.dataHub.featureRegistry as canonical
import dartlab.simulate.stateVariables as compatibility

_REGISTRY_HASH = "b43ec06ed53833cac036a5bf3fd44d061dce5daa3913ca66e44712bc9db096c6"
_CONTRACT_HASH = "c30f140ee59040a6d352ba328ab8cc9cc21c80dfbcedbdae0cf0ceb4d92a60ec"


def _spec(variableId: str = "financial.revenue") -> canonical.StateVariableSpec:
    return canonical.StateVariableSpec(
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


def testSimulateCompatibilityPathReexportsCanonicalObjects() -> None:
    assert compatibility.StateVariableError is canonical.StateVariableError
    assert compatibility.StateVariableSpec is canonical.StateVariableSpec
    assert compatibility.StateVariableRegistry is canonical.StateVariableRegistry
    assert compatibility.buildStateVariableRegistry is canonical.buildStateVariableRegistry
    assert compatibility.stateVariableContractHash is canonical.stateVariableContractHash
    assert compatibility.STATE_VARIABLE_ROLES is canonical.STATE_VARIABLE_ROLES
    assert compatibility.STATE_EVIDENCE_ROLES is canonical.STATE_EVIDENCE_ROLES
    assert compatibility.STATE_TIMINGS is canonical.STATE_TIMINGS
    assert canonical.StateVariableSpec.__module__ == "dartlab.dataHub.featureRegistry"


def testRegistryAndContractHashesRemainByteCompatible() -> None:
    revenue = _spec()
    cash = _spec("financial.cash")

    registry = canonical.buildStateVariableRegistry((revenue, cash))

    assert registry.specs == (cash, revenue)
    assert registry.registryHash == _REGISTRY_HASH
    assert canonical.stateVariableContractHash((revenue, cash)) == _CONTRACT_HASH
    assert compatibility.buildStateVariableRegistry((cash, revenue)) == registry
    assert compatibility.stateVariableContractHash((cash, revenue)) == _CONTRACT_HASH


@pytest.mark.parametrize(
    ("specs", "message"),
    [
        ((), "state registry needs unique variables"),
        ((_spec(), _spec()), "state registry needs unique variables"),
        ((replace(_spec(), schemaVersion="v2"),), "state variable protocol mismatch"),
        ((replace(_spec(), datasetId=""),), "state variable contract is incomplete"),
        ((replace(_spec(), role="shock"),), "state variable meaning is invalid: financial.revenue"),
        ((replace(_spec(), maxStalenessDays=-1),), "state variable staleness must be nonnegative"),
        ((replace(_spec(), lower=1.0, upper=0.0),), "state variable bounds are inverted"),
    ],
)
def testRegistryErrorTypeAndMessagesRemainCompatible(
    specs: tuple[canonical.StateVariableSpec, ...],
    message: str,
) -> None:
    with pytest.raises(canonical.StateVariableError, match=f"^{message}$") as canonicalError:
        canonical.buildStateVariableRegistry(specs)
    with pytest.raises(compatibility.StateVariableError, match=f"^{message}$") as compatibilityError:
        compatibility.buildStateVariableRegistry(specs)

    assert type(canonicalError.value) is type(compatibilityError.value) is canonical.StateVariableError


def testDataclassShapeAndMeaningSensitivityRemainCompatible() -> None:
    revenue = _spec()

    assert repr(revenue) == (
        "StateVariableSpec(variableId='financial.revenue', signalId='financial.revenue', "
        "providerId='edgar', datasetId='quarterly-financial', unit='USD', role='state', "
        "evidenceRole='observed', frequency='quarter', timing='flow', transformId='level-v1', "
        "maxStalenessDays=400, lower=None, upper=None, schemaVersion='state-variable-spec-v1')"
    )
    assert (
        canonical.buildStateVariableRegistry((replace(revenue, frequency="year"),)).registryHash
        != canonical.buildStateVariableRegistry((revenue,)).registryHash
    )
    assert canonical.stateVariableContractHash((replace(revenue, timing="stock"),)) != (
        canonical.stateVariableContractHash((revenue,))
    )
