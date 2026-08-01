"""Feature observation set의 offline history와 point-in-time query tests."""

from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256

import pytest

from dartlab.dataHub.feature.observation import FeatureObservationError, makeVariableObservation
from dartlab.dataHub.feature.query import (
    FeatureQueryError,
    FeatureReadQuery,
    buildFeatureObservationSet,
    featureObservationSetFromValue,
    readFeatures,
)
from dartlab.dataHub.feature.registry import StateVariableSpec, buildStateVariableRegistry
from dartlab.dataHub.identity.vintage import VintageRef

_SOURCE_HASH = sha256(b"source").hexdigest()
_NORMALIZATION_HASH = sha256(b"normalization").hexdigest()


def _registry():
    return buildStateVariableRegistry(
        (
            StateVariableSpec(
                variableId="financial.revenue",
                signalId="revenue",
                providerId="edgar",
                datasetId="companyfacts",
                unit="USD",
                role="observedFeature",
                evidenceRole="observed",
                frequency="quarter",
                timing="flow",
                transformId="standalone-quarter-v1",
                maxStalenessDays=400,
                lower=0.0,
            ),
            StateVariableSpec(
                variableId="financial.cash",
                signalId="cash",
                providerId="edgar",
                datasetId="companyfacts",
                unit="USD",
                role="observedFeature",
                evidenceRole="observed",
                frequency="quarter",
                timing="stock",
                transformId="instant-v1",
                maxStalenessDays=400,
                lower=0.0,
            ),
        )
    )


def _observation(
    *,
    signalId: str = "revenue",
    value: float = 100.0,
    eventAt: str = "20241231",
    availableAt: str = "20250115",
    knowledgeAsOf: str | None = None,
    revisionId: str = "original",
    entityId: str = "US:AAPL",
    exact: bool = True,
):
    knowledge = knowledgeAsOf or availableAt
    timing = "flow" if signalId == "revenue" else "stock"
    transformId = "standalone-quarter-v1" if signalId == "revenue" else "instant-v1"
    return makeVariableObservation(
        providerId="edgar",
        datasetId="companyfacts",
        entityId=entityId,
        signalId=signalId,
        value=value,
        unit="USD",
        frequency="quarter",
        timing=timing,
        transformId=transformId,
        evidenceRole="observed",
        eventAt=eventAt,
        availableAt=availableAt,
        knowledgeAsOf=knowledge,
        availabilityPrecision="date",
        revisionId=revisionId,
        vintage=VintageRef(
            artifactKind="companyfacts",
            provider="edgar",
            artifactId=f"{entityId}:{revisionId}:{knowledge.replace('-', '')}",
            artifactHash=_SOURCE_HASH,
            payloadHash=_SOURCE_HASH,
            knowledgeAsOf=knowledge,
            availableAt=availableAt,
            revisionPolicy="asKnown" if exact else "latestRetained",
            coverage="asOfExact" if exact else "periodOnly",
            fiscalThrough=eventAt,
        ),
        normalizationRuleHash=_NORMALIZATION_HASH,
    )


def testObservationSetIsOrderIndependentAndContentAddressed() -> None:
    registry = _registry()
    first = _observation()
    second = _observation(signalId="cash", value=55.0)

    left = buildFeatureObservationSet(registry, (first, second))
    right = buildFeatureObservationSet(registry, (second, first))

    assert left == right
    assert left.observationSetHash == right.observationSetHash
    assert {item.observationId for item in left.observations} == {first.observationId, second.observationId}


def testLowerOwnerPlainMappingBuildsTheSameCanonicalDataset() -> None:
    registry = _registry()
    observation = _observation()
    expected = buildFeatureObservationSet(registry, (observation,))
    payload = {
        "schemaVersion": "feature-observation-input-v1",
        "specs": [asdict(item) for item in registry.specs],
        "observations": [asdict(observation)],
    }

    assert featureObservationSetFromValue(payload) == expected
    assert featureObservationSetFromValue({"ordinary": "mapping"}) is None

    payload["observations"][0]["observationId"] = "0" * 64
    with pytest.raises(FeatureQueryError) as invalid:
        featureObservationSetFromValue(payload)
    assert invalid.value.code == "FEATURE_OBSERVATION_INVALID"


def testPointInTimeQueryBlocksFutureRevisionAndSwitchesAfterKnowledgeCutoff() -> None:
    original = _observation(value=100.0, availableAt="20250115", revisionId="original")
    amended = _observation(
        value=120.0,
        availableAt="20250301",
        knowledgeAsOf="20250301",
        revisionId="amended",
    )
    dataset = buildFeatureObservationSet(_registry(), (amended, original))

    before = readFeatures(
        dataset,
        FeatureReadQuery(
            featureIds=("financial.revenue",),
            entityIds=("US:AAPL",),
            knownAt="2025-02-01",
            mode="pointInTime",
        ),
    )
    after = readFeatures(
        dataset,
        FeatureReadQuery(
            featureIds=("financial.revenue",),
            entityIds=("US:AAPL",),
            knownAt="2025-03-02",
            mode="pointInTime",
        ),
    )

    assert [item.observation.value for item in before.selections] == [100.0]
    assert [item.observation.value for item in after.selections] == [120.0]
    assert before.queryHash != after.queryHash


def testSameTimestampDifferentRevisionIdsAreAmbiguousNotLexicallyOrdered() -> None:
    first = _observation(value=100.0, revisionId="a")
    second = _observation(value=999.0, revisionId="z")
    dataset = buildFeatureObservationSet(_registry(), (first, second))

    with pytest.raises(FeatureQueryError) as ambiguous:
        readFeatures(
            dataset,
            FeatureReadQuery(
                featureIds=("financial.revenue",),
                entityIds=("US:AAPL",),
                knownAt="20250201",
                mode="pointInTime",
            ),
        )
    assert ambiguous.value.code == "FEATURE_REVISION_AMBIGUOUS"


def testHistoryUsesSameBitemporalCutoffsAndPreservesRevisions() -> None:
    oldQuarter = _observation(value=80.0, eventAt="20240930", availableAt="20241101", revisionId="q3")
    original = _observation(value=100.0, revisionId="q4")
    future = _observation(value=120.0, availableAt="20250301", revisionId="q4-amended")
    dataset = buildFeatureObservationSet(_registry(), (future, original, oldQuarter))

    result = readFeatures(
        dataset,
        FeatureReadQuery(
            featureIds=("financial.revenue",),
            entityIds=("US:AAPL",),
            validAt="2024-12-31",
            knownAt="2025-02-01",
            mode="history",
        ),
    )

    assert [(item.observation.eventAt, item.observation.value) for item in result.selections] == [
        ("20240930", 80.0),
        ("20241231", 100.0),
    ]


def testExplicitEntityFeatureMatrixReportsMissingWithoutInventingZero() -> None:
    dataset = buildFeatureObservationSet(_registry(), (_observation(),))

    result = readFeatures(
        dataset,
        FeatureReadQuery(
            entityIds=("US:AAPL", "US:MSFT"),
            knownAt="20250201",
            mode="pointInTime",
        ),
    )

    assert {(item.featureId, item.observation.entityId) for item in result.selections} == {
        ("financial.revenue", "US:AAPL")
    }
    assert result.missing == (
        ("financial.cash", "US:AAPL"),
        ("financial.cash", "US:MSFT"),
        ("financial.revenue", "US:MSFT"),
    )
    assert result.exactAsKnown is False

    inferredMatrix = readFeatures(
        dataset,
        FeatureReadQuery(knownAt="20250201", mode="pointInTime"),
    )
    assert inferredMatrix.missing == (("financial.cash", "US:AAPL"),)
    assert inferredMatrix.exactAsKnown is False


def testExactRequirementAndPointInTimeCutoffFailClosed() -> None:
    conditional = _observation(exact=False)
    dataset = buildFeatureObservationSet(_registry(), (conditional,))

    with pytest.raises(FeatureQueryError) as missingCutoff:
        readFeatures(dataset, FeatureReadQuery(mode="pointInTime"))
    assert missingCutoff.value.code == "FEATURE_KNOWN_AT_REQUIRED"

    with pytest.raises(FeatureQueryError) as notExact:
        readFeatures(
            dataset,
            FeatureReadQuery(
                featureIds=("financial.revenue",),
                entityIds=("US:AAPL",),
                knownAt="20250201",
                mode="pointInTime",
                requireExact=True,
            ),
        )
    assert notExact.value.code == "FEATURE_EXACT_REQUIRED"

    exact = buildFeatureObservationSet(_registry(), (_observation(),))
    with pytest.raises(FeatureQueryError) as selfDeclaredExact:
        readFeatures(
            exact,
            FeatureReadQuery(
                featureIds=("financial.revenue",),
                entityIds=("US:AAPL",),
                knownAt="20250201",
                mode="pointInTime",
                requireExact=True,
            ),
        )
    assert selfDeclaredExact.value.code == "FEATURE_EXACT_REQUIRED"

    with pytest.raises(FeatureQueryError) as missingScope:
        readFeatures(
            exact,
            FeatureReadQuery(
                featureIds=("financial.revenue",),
                knownAt="20250201",
                mode="pointInTime",
                requireExact=True,
            ),
        )
    assert missingScope.value.code == "FEATURE_EXACT_SCOPE_REQUIRED"


def testBoundsStalenessAndDatePrecisionUseTheSameSimulatorSemantics() -> None:
    belowBound = buildFeatureObservationSet(_registry(), (_observation(value=-1.0),))
    with pytest.raises(FeatureQueryError) as bound:
        readFeatures(
            belowBound,
            FeatureReadQuery(
                featureIds=("financial.revenue",),
                knownAt="20250201",
                mode="pointInTime",
            ),
        )
    assert bound.value.code == "FEATURE_VALUE_BELOW_BOUND"

    stale = buildFeatureObservationSet(_registry(), (_observation(),))
    with pytest.raises(FeatureQueryError) as tooOld:
        readFeatures(
            stale,
            FeatureReadQuery(
                featureIds=("financial.revenue",),
                knownAt="20270101",
                mode="pointInTime",
            ),
        )
    assert tooOld.value.code == "FEATURE_OBSERVATION_STALE"

    sameDay = readFeatures(
        stale,
        FeatureReadQuery(
            featureIds=("financial.revenue",),
            knownAt="20250115",
            mode="pointInTime",
        ),
    )
    assert sameDay.selections[0].exactAsKnown is False
    assert sameDay.exactAsKnown is False

    knowledgeSameDay = buildFeatureObservationSet(
        _registry(),
        (_observation(availableAt="20250114", knowledgeAsOf="20250115"),),
    )
    sameKnowledgeDay = readFeatures(
        knowledgeSameDay,
        FeatureReadQuery(
            featureIds=("financial.revenue",),
            knownAt="20250115",
            mode="pointInTime",
        ),
    )
    assert sameKnowledgeDay.selections[0].exactAsKnown is False
    assert sameKnowledgeDay.exactAsKnown is False


def testUnknownSourceDuplicatePrimaryKeyAndDatasetDriftFailClosed() -> None:
    registry = _registry()
    observation = _observation()

    with pytest.raises(FeatureQueryError) as duplicate:
        buildFeatureObservationSet(registry, (observation, observation))
    assert duplicate.value.code == "FEATURE_PRIMARY_KEY_DUPLICATE"

    unknown = _observation(signalId="unknown")
    with pytest.raises(FeatureQueryError) as invalid:
        buildFeatureObservationSet(registry, (unknown,))
    assert invalid.value.code == "FEATURE_SOURCE_UNKNOWN"

    dataset = buildFeatureObservationSet(registry, (observation,))
    with pytest.raises(FeatureQueryError) as drift:
        readFeatures(replace(dataset, observationSetHash="0" * 64), FeatureReadQuery())
    assert drift.value.code == "FEATURE_DATASET_DRIFT"


def testDatesAndObservedFeatureEntityIdentityAreCanonicalAtBuildTime() -> None:
    compact = _observation()
    iso = _observation(eventAt="2024-12-31", availableAt="2025-01-15")
    assert iso == compact

    with pytest.raises(FeatureObservationError, match="invalid eventAt"):
        _observation(eventAt="20250231")
    with pytest.raises(FeatureObservationError, match="invalid availableAt"):
        _observation(availableAt="20250115-extra")

    rawEntity = _observation(entityId="AAPL")
    with pytest.raises(FeatureQueryError) as invalidEntity:
        buildFeatureObservationSet(_registry(), (rawEntity,))
    assert invalidEntity.value.code == "FEATURE_ENTITY_INVALID"


def testEnvelopeRejectsStringSourceRefsInsteadOfSplittingCharacters() -> None:
    registry = _registry()
    observation = _observation()
    payload = {
        "schemaVersion": "feature-observation-input-v1",
        "specs": [asdict(item) for item in registry.specs],
        "observations": [asdict(observation)],
    }
    payload["observations"][0]["vintage"]["sourceRefs"] = "not-a-sequence"

    with pytest.raises(FeatureQueryError) as invalid:
        featureObservationSetFromValue(payload)
    assert invalid.value.code == "FEATURE_INPUT_INVALID"
