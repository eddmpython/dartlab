"""Provider-neutral feature observation 정본과 simulate 호환성 tests."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

import dartlab.dataHub.feature.observation as canonical
import dartlab.simulate.stateCompiler as compatibility
from dartlab.dataHub.identity.vintage import VintageRef, canonicalPayloadHash

_OBSERVATION_HASH = "685b9e6500e7d03ff7a3a265063c3d5be54071bface56c7d563a59dadf000d81"


def _values() -> dict[str, object]:
    sourceHash = sha256(b"source").hexdigest()
    return {
        "providerId": "edgar",
        "datasetId": "quarterly-financial",
        "entityId": "AAPL",
        "signalId": "financial.revenue",
        "value": 100.0,
        "unit": "USD",
        "frequency": "quarter",
        "timing": "flow",
        "transformId": "level-v1",
        "evidenceRole": "observed",
        "eventAt": "20241231",
        "availableAt": "20250102",
        "knowledgeAsOf": "20250102",
        "availabilityPrecision": "date",
        "revisionId": "original",
        "vintage": VintageRef(
            artifactKind="providerObservation",
            provider="edgar",
            artifactId="aapl-revenue-original",
            artifactHash=sourceHash,
            payloadHash=sourceHash,
            knowledgeAsOf="20250102",
            availableAt="20250102",
            revisionPolicy="asKnown",
            coverage="asOfExact",
            fiscalThrough="20241231",
        ),
        "normalizationRuleHash": sha256(b"edgar-quarterly-financial-v1").hexdigest(),
    }


def _observation(**overrides: object) -> canonical.VariableObservation:
    values = _values()
    values.update(overrides)
    return canonical.makeVariableObservation(**values)


def _buildBatch(observation: canonical.VariableObservation):
    return compatibility.buildProviderObservationBatch(
        (observation,),
        providerId="edgar",
        datasetId="quarterly-financial",
        entityId="AAPL",
        signalIds=("financial.revenue",),
        cutoffAsOf="20250201",
    )


def testSimulateCompatibilityPathReexportsCanonicalObjects() -> None:
    assert compatibility.VariableObservation is canonical.VariableObservation
    assert compatibility.makeVariableObservation is canonical.makeVariableObservation
    assert compatibility.observationPayload is canonical.observationPayload
    assert compatibility.validateVariableObservation is canonical.validateVariableObservation
    assert compatibility._observationPayload is canonical.observationPayload
    assert compatibility.VARIABLE_OBSERVATION_SCHEMA == canonical.VARIABLE_OBSERVATION_SCHEMA
    assert canonical.VariableObservation.__module__ == "dartlab.dataHub.feature.observation"
    assert canonical.__all__ == [
        "FeatureObservationError",
        "VARIABLE_OBSERVATION_SCHEMA",
        "VariableObservation",
        "makeVariableObservation",
        "observationPayload",
        "validateVariableObservation",
    ]


def testFactoryAndPayloadRemainContentAddressCompatible() -> None:
    observation = _observation()
    payload = canonical.observationPayload(observation)

    assert "observationId" not in payload
    assert payload["vintage"] is observation.vintage
    assert observation.observationId == _OBSERVATION_HASH
    assert observation.observationId == canonicalPayloadHash(payload)
    assert canonical.validateVariableObservation(observation) is observation
    assert compatibility.makeVariableObservation(**_values()) == observation


def testFactoryBindsEveryObservationFieldAndRequiresCompleteInput() -> None:
    baseline = _observation()

    assert _observation(value=101.0).observationId != baseline.observationId
    assert _observation(timing="stock").observationId != baseline.observationId
    assert _observation(revisionId="amended").observationId != baseline.observationId

    incomplete = _values()
    del incomplete["signalId"]
    with pytest.raises(TypeError, match="signalId"):
        canonical.makeVariableObservation(**incomplete)


def testCompileValidationKeepsStateCompilerErrorBoundary() -> None:
    invalid = _observation(timing="unexpected")
    with pytest.raises(canonical.FeatureObservationError, match="contract is incomplete"):
        canonical.validateVariableObservation(invalid)

    with pytest.raises(compatibility.StateCompilerError, match="contract is incomplete"):
        _buildBatch(invalid)

    tampered = replace(_observation(), value=101.0)
    with pytest.raises(compatibility.StateCompilerError, match="content hash mismatch"):
        _buildBatch(tampered)
