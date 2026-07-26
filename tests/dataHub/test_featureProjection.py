"""FeatureObservationSet의 public FactorProjection과 PIT gate tests."""

from __future__ import annotations

from hashlib import sha256

import polars as pl
import pytest

from dartlab.dataHub.contracts import (
    DataAssetDescriptor,
    DataQuery,
    FactorProjection,
    TimeContext,
)
from dartlab.dataHub.execution import _temporalGap
from dartlab.dataHub.featureObservation import makeVariableObservation
from dartlab.dataHub.featureQuery import buildFeatureObservationSet
from dartlab.dataHub.featureRegistry import StateVariableSpec, buildStateVariableRegistry
from dartlab.dataHub.projections import projectOutput
from dartlab.dataHub.vintage import VintageRef

_SOURCE_HASH = sha256(b"edgar-source").hexdigest()
_NORMALIZATION_HASH = sha256(b"edgar-normalization").hexdigest()


def _descriptor(*, observationPit: bool = True) -> DataAssetDescriptor:
    return DataAssetDescriptor(
        assetId="analysis.edgarFinancialFeatures",
        assetVersionId="asset:" + "a" * 64,
        owner="analysis",
        layer="L2",
        kind="featureSet",
        label="EDGAR financial features",
        description="EDGAR financial features",
        sourceRef="python:analysis:edgarFinancialFeatures",
        queryable=True,
        temporalSupport=("latest", "validAt", "knownAt"),
        executorKind="callable",
        executorModule="dartlab.analysis.financial.dataAssets",
        executorAttribute="edgarFinancialFeatures",
        subjectParam="subject",
        validTimeParam="validAt",
        knowledgeTimeParam="knownAt",
        selectorKind="subject",
        selectorRequired=True,
        executionMode="subjectFanout",
        universeMarkets=("US",),
        metadata=(("knownAtRequired", True), ("market", "US"), ("observationPIT", observationPit)),
    )


def _dataset(*, entityId: str = "US:AAPL"):
    registry = buildStateVariableRegistry(
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
            ),
        )
    )

    def observation(value: float, availableAt: str, revisionId: str):
        return makeVariableObservation(
            providerId="edgar",
            datasetId="companyfacts",
            entityId=entityId,
            signalId="revenue",
            value=value,
            unit="USD",
            frequency="quarter",
            timing="flow",
            transformId="standalone-quarter-v1",
            evidenceRole="observed",
            eventAt="20241231",
            availableAt=availableAt,
            knowledgeAsOf=availableAt,
            availabilityPrecision="date",
            revisionId=revisionId,
            vintage=VintageRef(
                artifactKind="companyfacts",
                provider="edgar",
                artifactId=f"{entityId}:{revisionId}",
                artifactHash=_SOURCE_HASH,
                payloadHash=_SOURCE_HASH,
                knowledgeAsOf=availableAt,
                availableAt=availableAt,
                revisionPolicy="asKnown",
                coverage="asOfExact",
                fiscalThrough="20241231",
            ),
            normalizationRuleHash=_NORMALIZATION_HASH,
        )

    return buildFeatureObservationSet(
        registry,
        (
            observation(100.0, "20250115", "original"),
            observation(120.0, "20250301", "amended"),
        ),
    )


def testDeclaredObservationPitBypassesGenericMetadataBlockOnly() -> None:
    query = DataQuery(
        subjects=("AAPL",),
        projection=FactorProjection(measures=("financial.revenue",)),
        time=TimeContext(knownAt="20250201"),
    )

    assert _temporalGap(_descriptor(), query) is None
    gap = _temporalGap(_descriptor(observationPit=False), query)
    assert gap is not None
    assert gap.code == "OBSERVATION_PIT_METADATA_REQUIRED"

    missingCutoff = _temporalGap(
        _descriptor(),
        DataQuery(subjects=("AAPL",), projection=FactorProjection(measures=("financial.revenue",))),
    )
    assert missingCutoff is not None
    assert missingCutoff.code == "FEATURE_KNOWN_AT_REQUIRED"


def testFactorProjectionUsesActualObservationKnowledgeTimeAndRevision() -> None:
    query = DataQuery(
        subjects=("AAPL",),
        projection=FactorProjection(measures=("financial.revenue",)),
        time=TimeContext(knownAt="20250201"),
    )
    partition, gaps = projectOutput(
        _dataset(),
        _descriptor(),
        query,
        selector={"subject": "AAPL"},
        receiptRef="data-request:" + "b" * 64,
        requestId="aaplRevenue",
    )

    assert gaps == ()
    assert partition is not None
    assert partition.temporalStatus == "POINT_IN_TIME"
    assert partition.contentHash is not None
    assert partition.data.to_dicts() == [
        {
            **partition.data.to_dicts()[0],
            "measureId": "financial.revenue",
            "entityId": "US:AAPL",
            "sourceEntityId": "AAPL",
            "eventAt": "20241231",
            "availableAt": "20250115",
            "knownAt": "20250115",
            "value": 100.0,
            "revisionId": "original",
            "temporalStatus": "POINT_IN_TIME",
            "revisionPolicy": "asKnown",
            "coverage": "asOfExact",
        }
    ]
    assert query.time is not None
    assert partition.data["knownAt"].item() != query.time.knownAt
    assert partition.data["featureRegistryHash"].item() == _dataset().registry.registryHash
    assert partition.data["evidenceRef"].item().startswith("data-execution:")


def testFeatureHistoryPreservesBothRevisionsAndMeaningCannotBeOverridden() -> None:
    history, gaps = projectOutput(
        _dataset(),
        _descriptor(),
        DataQuery(subjects=("AAPL",), projection=FactorProjection(measures=("financial.revenue",))),
        selector={"subject": "AAPL"},
        receiptRef="data-request:" + "c" * 64,
    )

    assert gaps == ()
    assert history is not None
    assert history.temporalStatus == "OBSERVATION_HISTORY"
    assert history.data["value"].to_list() == [100.0, 120.0]

    mismatch, mismatchGaps = projectOutput(
        _dataset(),
        _descriptor(),
        DataQuery(
            subjects=("AAPL",),
            projection=FactorProjection(measures=("financial.revenue",), unit="KRW"),
        ),
        selector={"subject": "AAPL"},
        receiptRef="data-request:" + "d" * 64,
    )
    assert mismatch is None
    assert [gap.code for gap in mismatchGaps] == ["FACTOR_UNIT_MISMATCH"]


def testDeclaredPitOwnerMustReturnVerifiedEnvelopeAtRuntime() -> None:
    partition, gaps = projectOutput(
        pl.DataFrame({"entity": ["AAPL"], "period": ["20241231"], "value": [100.0]}),
        _descriptor(),
        DataQuery(
            subjects=("AAPL",),
            projection=FactorProjection(measures=("financial.revenue",)),
            time=TimeContext(knownAt="20250201"),
        ),
        selector={"subject": "AAPL"},
        receiptRef="data-request:" + "e" * 64,
    )

    assert partition is None
    assert [gap.code for gap in gaps] == ["FEATURE_OBSERVATION_ENVELOPE_REQUIRED"]


def testCanonicalObservationMarketCannotCrossDescriptorMarket() -> None:
    partition, gaps = projectOutput(
        _dataset(entityId="KR:AAPL"),
        _descriptor(),
        DataQuery(
            subjects=("KR:AAPL",),
            projection=FactorProjection(measures=("financial.revenue",)),
            time=TimeContext(knownAt="20250201"),
        ),
        selector={"subject": "KR:AAPL"},
        receiptRef="data-request:" + "f" * 64,
    )

    assert partition is None
    assert [gap.code for gap in gaps] == ["FEATURE_MARKET_MISMATCH"]


@pytest.mark.parametrize("subject", ("aapl", "Apple Inc."))
def testSubjectFanoutUsesTheSingleCanonicalOwnerEntity(subject: str) -> None:
    partition, gaps = projectOutput(
        _dataset(entityId="US:AAPL"),
        _descriptor(),
        DataQuery(
            subjects=(subject,),
            projection=FactorProjection(measures=("financial.revenue",)),
            time=TimeContext(knownAt="20250201"),
        ),
        selector={"subject": subject},
        receiptRef="data-request:" + "f" * 64,
    )

    assert gaps == ()
    assert partition is not None
    assert partition.data["entityId"].unique().to_list() == ["US:AAPL"]
