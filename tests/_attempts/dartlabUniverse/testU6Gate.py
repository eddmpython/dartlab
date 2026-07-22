"""Universe U6 GPU transport와 독립 3D GUI gate 회귀."""

from __future__ import annotations

from dataclasses import replace

from tests._attempts.dartlabUniverse.validation.u6 import U6Measurements, validateU6


def _passingMeasurements() -> U6Measurements:
    return U6Measurements(
        upstreamU5Passed=True,
        u5ProjectionStateId="du:v1:projection-state:" + "a" * 64,
        projectionStateId="du:v1:projection-state:" + "a" * 64,
        u5CoordinateMapDigest="b" * 64,
        coordinateMapDigest="b" * 64,
        u5SnapshotId="du:v1:catalog-snapshot:" + "c" * 64,
        snapshotId="du:v1:catalog-snapshot:" + "c" * 64,
        u5ObjectCount=212_394,
        objectCount=212_394,
        u5RelationCount=292_315,
        relationCount=292_315,
        u5TileCount=1_818,
        persistenceMode="EPHEMERAL",
        tileCount=1_818,
        encodedTileCount=1_818,
        tileCoverage=1.0,
        sourceDigestCoverage=1.0,
        recordDigestCoverage=1.0,
        metadataCoverage=1.0,
        childClosureCoverage=1.0,
        labelCoverage=1.0,
        rawLocatorLabelCount=0,
        styleFamilyCount=6,
        manifestBytes=12_000,
        initialPayloadBytes=1_500_000,
        maxTileBundleBytes=1_800_000,
        encodeAllTilesSeconds=9.0,
        guiAssetCount=8,
        guiAssetBytes=80_000,
        webGpuRendererPresent=True,
        webGlFallbackPresent=True,
        pixelProbePresent=True,
        responsiveContractPresent=True,
        sessionTokenContractPresent=True,
        externalAssetReferenceCount=0,
        publicSurfaceReferenceCount=0,
        publicRouteConnected=False,
        publicButtonConnected=False,
        persistentArtifactCount=0,
    )


def testU6GateAcceptsCompleteRuntimeOnlyGpuTransportAndGui() -> None:
    report = validateU6(_passingMeasurements())
    assert report.passed
    assert report.failureCodes == ()
    assert report.digest


def testU6GateRejectsTransportConservationAndU5BindingRegression() -> None:
    measurements = replace(
        _passingMeasurements(),
        upstreamU5Passed=False,
        projectionStateId="du:v1:projection-state:" + "d" * 64,
        encodedTileCount=1_817,
        recordDigestCoverage=0.999,
        childClosureCoverage=0.999,
        rawLocatorLabelCount=1,
    )
    report = validateU6(measurements)
    assert not report.passed
    assert {
        "UPSTREAM_U5_FAILED",
        "U5_PROJECTION_BINDING_MISMATCH",
        "GPU_TILE_CARDINALITY_INVALID",
        "GPU_TRANSPORT_CONSERVATION_FAILED",
        "RAW_LOCATOR_LABEL_LEAKED",
    } <= set(report.failureCodes)


def testU6GateRejectsGpuGuiAndPublicSurfaceRegression() -> None:
    measurements = replace(
        _passingMeasurements(),
        persistenceMode="PERSISTENT",
        persistentArtifactCount=1,
        webGpuRendererPresent=False,
        webGlFallbackPresent=False,
        pixelProbePresent=False,
        responsiveContractPresent=False,
        sessionTokenContractPresent=False,
        externalAssetReferenceCount=1,
        publicSurfaceReferenceCount=1,
        publicRouteConnected=True,
        publicButtonConnected=True,
    )
    report = validateU6(measurements)
    assert not report.passed
    assert {
        "UNAPPROVED_PERSISTENT_GPU_ARTIFACT",
        "WEBGPU_RENDERER_MISSING",
        "WEBGL2_FALLBACK_MISSING",
        "GPU_FRAME_PROBE_MISSING",
        "RESPONSIVE_GUI_CONTRACT_MISSING",
        "LOOPBACK_SESSION_TOKEN_CONTRACT_MISSING",
        "EXTERNAL_GUI_ASSET_REFERENCE_FOUND",
        "UNAPPROVED_PUBLIC_UNIVERSE_SURFACE",
    } <= set(report.failureCodes)
