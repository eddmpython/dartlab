"""Universe U5 machine gate 임계값과 fail-closed 회귀."""

from __future__ import annotations

from dataclasses import replace

from tests._attempts.dartlabUniverse.validation.u5 import U5Measurements, validateU5


def _passingMeasurements() -> U5Measurements:
    return U5Measurements(
        upstreamPassed=True,
        snapshotId="du:v1:snapshot:" + "a" * 64,
        projectionStateId="du:v1:projection-state:" + "b" * 64,
        projectionDigest="c" * 64,
        coordinateMapDigest="d" * 64,
        replayCoordinateMapDigest="d" * 64,
        persistenceMode="EPHEMERAL",
        objectCount=212_164,
        relationCount=291_828,
        communityCount=1_809,
        tileCount=1_814,
        fullProjectionSeconds=29.0,
        replaySeconds=29.0,
        incrementalOnePercentSeconds=4.0,
        incrementalFixtureObjectCount=10_396,
        processPeakRssBytes=1_900_000_000,
        incrementalRssGrowthBytes=100_000_000,
        coordinateDeterminism=1.0,
        normalizedDisplacementP95=0.0,
        clusterContinuity=0.99,
        selectedObjectLossCount=0,
        meaningPreservation=1.0,
        conservationAssertionCount=70,
        passedConservationAssertionCount=70,
        zZeroRatio=0.001,
        xyzValidRatio=1.0,
        maxTileBytes=1_200_000,
        maxTileNodeCount=1_000,
        maxTileEdgeCount=8_000,
        runtimeTileRefRatio=1.0,
        objectDrillPathRatio=1.0,
        persistentArtifactCount=0,
    )


def testU5GateAcceptsCompleteRuntimeProjection() -> None:
    report = validateU5(_passingMeasurements())
    assert report.passed
    assert report.failureCodes == ()
    assert report.digest


def testU5GateRejectsLatencyMeaningAndPersistentTileFailures() -> None:
    measurements = replace(
        _passingMeasurements(),
        fullProjectionSeconds=30.001,
        meaningPreservation=0.99,
        passedConservationAssertionCount=69,
        runtimeTileRefRatio=0.999,
        persistentArtifactCount=1,
    )
    report = validateU5(measurements)
    assert not report.passed
    assert {
        "FULL_PROJECTION_P95_EXCEEDED",
        "MEANING_CONSERVATION_FAILED",
        "UNAPPROVED_PERSISTENT_PROJECTION",
    } <= set(report.failureCodes)


def testU5GateRejectsCoordinateAndIncrementalRegression() -> None:
    measurements = replace(
        _passingMeasurements(),
        replayCoordinateMapDigest="e" * 64,
        coordinateDeterminism=0.999,
        incrementalOnePercentSeconds=5.001,
        normalizedDisplacementP95=0.021,
        clusterContinuity=0.97,
        selectedObjectLossCount=1,
    )
    report = validateU5(measurements)
    assert not report.passed
    assert {
        "COORDINATE_DETERMINISM_FAILED",
        "INCREMENTAL_ONE_PERCENT_P95_EXCEEDED",
        "NORMALIZED_DISPLACEMENT_P95_EXCEEDED",
        "CLUSTER_CONTINUITY_BELOW_THRESHOLD",
        "SELECTED_OBJECT_LOST",
    } <= set(report.failureCodes)
