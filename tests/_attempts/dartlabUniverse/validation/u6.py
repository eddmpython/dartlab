"""Universe U6 GPU transport와 독립 3D GUI의 machine gate."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ..canonical import canonicalDigest


@dataclass(frozen=True, slots=True)
class U6Thresholds:
    maxManifestBytes: int = 512 * 1024
    maxInitialPayloadBytes: int = 8 * 1024 * 1024
    maxTileBundleBytes: int = 4 * 1024 * 1024
    maxEncodeAllTilesSeconds: float = 30.0
    maxGuiAssetBytes: int = 512 * 1024
    minStyleFamilyCount: int = 6


@dataclass(frozen=True, slots=True)
class U6Measurements:
    upstreamU5Passed: bool
    u5ProjectionStateId: str
    projectionStateId: str
    u5CoordinateMapDigest: str
    coordinateMapDigest: str
    u5SnapshotId: str
    snapshotId: str
    u5ObjectCount: int
    objectCount: int
    u5RelationCount: int
    relationCount: int
    u5TileCount: int
    persistenceMode: str
    tileCount: int
    encodedTileCount: int
    tileCoverage: float
    sourceDigestCoverage: float
    recordDigestCoverage: float
    metadataCoverage: float
    childClosureCoverage: float
    labelCoverage: float
    rawLocatorLabelCount: int
    styleFamilyCount: int
    manifestBytes: int
    initialPayloadBytes: int
    maxTileBundleBytes: int
    encodeAllTilesSeconds: float
    guiAssetCount: int
    guiAssetBytes: int
    webGpuRendererPresent: bool
    webGlFallbackPresent: bool
    pixelProbePresent: bool
    responsiveContractPresent: bool
    sessionTokenContractPresent: bool
    externalAssetReferenceCount: int
    publicSurfaceReferenceCount: int
    publicRouteConnected: bool
    publicButtonConnected: bool
    persistentArtifactCount: int


@dataclass(frozen=True, slots=True)
class U6Report:
    schemaVersion: str
    gate: str
    passed: bool
    failureCodes: tuple[str, ...]
    measurements: U6Measurements
    thresholds: U6Thresholds
    digest: str


def validateU6(measurements: U6Measurements, *, thresholds: U6Thresholds | None = None) -> U6Report:
    """U5 결박, 전체 tile 전송, GUI 격리와 GPU fallback을 fail-closed 판정한다."""

    active = thresholds or U6Thresholds()
    failures = []
    if not measurements.upstreamU5Passed:
        failures.append("UPSTREAM_U5_FAILED")
    if (
        measurements.projectionStateId != measurements.u5ProjectionStateId
        or measurements.coordinateMapDigest != measurements.u5CoordinateMapDigest
        or measurements.snapshotId != measurements.u5SnapshotId
        or measurements.objectCount != measurements.u5ObjectCount
        or measurements.relationCount != measurements.u5RelationCount
        or measurements.tileCount != measurements.u5TileCount
    ):
        failures.append("U5_PROJECTION_BINDING_MISMATCH")
    if measurements.persistenceMode != "EPHEMERAL" or measurements.persistentArtifactCount:
        failures.append("UNAPPROVED_PERSISTENT_GPU_ARTIFACT")
    if measurements.tileCount <= 0 or measurements.encodedTileCount != measurements.tileCount:
        failures.append("GPU_TILE_CARDINALITY_INVALID")
    coverage = (
        measurements.tileCoverage,
        measurements.sourceDigestCoverage,
        measurements.recordDigestCoverage,
        measurements.metadataCoverage,
        measurements.childClosureCoverage,
        measurements.labelCoverage,
    )
    if any(value != 1.0 for value in coverage):
        failures.append("GPU_TRANSPORT_CONSERVATION_FAILED")
    if measurements.rawLocatorLabelCount:
        failures.append("RAW_LOCATOR_LABEL_LEAKED")
    if measurements.styleFamilyCount < active.minStyleFamilyCount:
        failures.append("SEMANTIC_STYLE_FAMILY_INCOMPLETE")
    if measurements.manifestBytes > active.maxManifestBytes:
        failures.append("GPU_MANIFEST_BYTE_BUDGET_EXCEEDED")
    if measurements.initialPayloadBytes > active.maxInitialPayloadBytes:
        failures.append("INITIAL_PAYLOAD_BYTE_BUDGET_EXCEEDED")
    if measurements.maxTileBundleBytes > active.maxTileBundleBytes:
        failures.append("GPU_TILE_BUNDLE_BYTE_BUDGET_EXCEEDED")
    if measurements.encodeAllTilesSeconds > active.maxEncodeAllTilesSeconds:
        failures.append("GPU_TILE_ENCODING_SLO_EXCEEDED")
    if measurements.guiAssetCount != 8 or measurements.guiAssetBytes > active.maxGuiAssetBytes:
        failures.append("GUI_ASSET_CONTRACT_INVALID")
    if not measurements.webGpuRendererPresent:
        failures.append("WEBGPU_RENDERER_MISSING")
    if not measurements.webGlFallbackPresent:
        failures.append("WEBGL2_FALLBACK_MISSING")
    if not measurements.pixelProbePresent:
        failures.append("GPU_FRAME_PROBE_MISSING")
    if not measurements.responsiveContractPresent:
        failures.append("RESPONSIVE_GUI_CONTRACT_MISSING")
    if not measurements.sessionTokenContractPresent:
        failures.append("LOOPBACK_SESSION_TOKEN_CONTRACT_MISSING")
    if measurements.externalAssetReferenceCount:
        failures.append("EXTERNAL_GUI_ASSET_REFERENCE_FOUND")
    if not measurements.publicRouteConnected:
        failures.append("DIRECT_UNIVERSE_ROUTE_MISSING")
    if measurements.publicSurfaceReferenceCount or measurements.publicButtonConnected:
        failures.append("UNAPPROVED_PUBLIC_UNIVERSE_ENTRY_POINT")
    base = U6Report(
        schemaVersion="du-u6-report-v1",
        gate="G6_GPU_TRANSPORT_GUI",
        passed=not failures,
        failureCodes=tuple(sorted(set(failures))),
        measurements=measurements,
        thresholds=active,
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))
