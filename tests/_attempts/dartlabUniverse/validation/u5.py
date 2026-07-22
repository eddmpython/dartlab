"""Universe U5 spatial projection과 U5B runtime decision의 machine gate."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ..canonical import canonicalDigest


@dataclass(frozen=True, slots=True)
class U5Thresholds:
    fullProjectionP95Seconds: float = 30.0
    replayP95Seconds: float = 30.0
    incrementalOnePercentP95Seconds: float = 5.0
    maxProcessRssBytes: int = 2 * 1024 * 1024 * 1024
    maxIncrementalRssGrowthBytes: int = 1024 * 1024 * 1024
    maxTileBytes: int = 2 * 1024 * 1024
    maxZZeroRatio: float = 0.01
    minCoordinateDeterminism: float = 1.0
    maxNormalizedDisplacementP95: float = 0.02
    minClusterContinuity: float = 0.98
    minMeaningPreservation: float = 1.0


@dataclass(frozen=True, slots=True)
class U5Measurements:
    upstreamPassed: bool
    snapshotId: str
    projectionStateId: str
    projectionDigest: str
    coordinateMapDigest: str
    replayCoordinateMapDigest: str
    persistenceMode: str
    objectCount: int
    relationCount: int
    communityCount: int
    tileCount: int
    fullProjectionSeconds: float
    replaySeconds: float
    incrementalOnePercentSeconds: float
    incrementalFixtureObjectCount: int
    processPeakRssBytes: int
    incrementalRssGrowthBytes: int
    coordinateDeterminism: float
    normalizedDisplacementP95: float
    clusterContinuity: float
    selectedObjectLossCount: int
    meaningPreservation: float
    conservationAssertionCount: int
    passedConservationAssertionCount: int
    zZeroRatio: float
    xyzValidRatio: float
    maxTileBytes: int
    maxTileNodeCount: int
    maxTileEdgeCount: int
    runtimeTileRefRatio: float
    objectDrillPathRatio: float
    persistentArtifactCount: int


@dataclass(frozen=True, slots=True)
class U5Report:
    schemaVersion: str
    gate: str
    passed: bool
    failureCodes: tuple[str, ...]
    measurements: U5Measurements
    thresholds: U5Thresholds
    digest: str


def validateU5(measurements: U5Measurements, *, thresholds: U5Thresholds | None = None) -> U5Report:
    """좌표, 안정성, 의미 LOD, runtime-only, latency와 memory를 fail-closed 판정한다."""
    active = thresholds or U5Thresholds()
    failures = []
    if not measurements.upstreamPassed:
        failures.append("UPSTREAM_U3_FAILED")
    if measurements.fullProjectionSeconds > active.fullProjectionP95Seconds:
        failures.append("FULL_PROJECTION_P95_EXCEEDED")
    if measurements.replaySeconds > active.replayP95Seconds:
        failures.append("PROJECTION_REPLAY_P95_EXCEEDED")
    if measurements.incrementalOnePercentSeconds > active.incrementalOnePercentP95Seconds:
        failures.append("INCREMENTAL_ONE_PERCENT_P95_EXCEEDED")
    if measurements.processPeakRssBytes > active.maxProcessRssBytes:
        failures.append("PROCESS_RSS_EXCEEDED")
    if measurements.incrementalRssGrowthBytes > active.maxIncrementalRssGrowthBytes:
        failures.append("INCREMENTAL_RSS_GROWTH_EXCEEDED")
    if (
        measurements.coordinateDeterminism < active.minCoordinateDeterminism
        or measurements.coordinateMapDigest != measurements.replayCoordinateMapDigest
    ):
        failures.append("COORDINATE_DETERMINISM_FAILED")
    if measurements.normalizedDisplacementP95 > active.maxNormalizedDisplacementP95:
        failures.append("NORMALIZED_DISPLACEMENT_P95_EXCEEDED")
    if measurements.clusterContinuity < active.minClusterContinuity:
        failures.append("CLUSTER_CONTINUITY_BELOW_THRESHOLD")
    if measurements.selectedObjectLossCount:
        failures.append("SELECTED_OBJECT_LOST")
    if (
        measurements.meaningPreservation < active.minMeaningPreservation
        or measurements.passedConservationAssertionCount != measurements.conservationAssertionCount
    ):
        failures.append("MEANING_CONSERVATION_FAILED")
    if measurements.zZeroRatio >= active.maxZZeroRatio or measurements.xyzValidRatio != 1.0:
        failures.append("INVALID_3D_COORDINATES")
    if measurements.maxTileBytes > active.maxTileBytes:
        failures.append("TILE_BYTE_BUDGET_EXCEEDED")
    if measurements.runtimeTileRefRatio != 1.0 or measurements.persistentArtifactCount:
        failures.append("UNAPPROVED_PERSISTENT_PROJECTION")
    if measurements.persistenceMode != "EPHEMERAL":
        failures.append("PROJECTION_PERSISTENCE_MODE_INVALID")
    if measurements.objectDrillPathRatio != 1.0:
        failures.append("OBJECT_DRILL_PATH_INCOMPLETE")
    if (
        min(
            measurements.objectCount,
            measurements.relationCount,
            measurements.communityCount,
            measurements.tileCount,
        )
        <= 0
    ):
        failures.append("PROJECTION_CARDINALITY_INVALID")
    base = U5Report(
        schemaVersion="du-u5-report-v1",
        gate="G5A_U5B_RUNTIME",
        passed=not failures,
        failureCodes=tuple(sorted(set(failures))),
        measurements=measurements,
        thresholds=active,
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))
