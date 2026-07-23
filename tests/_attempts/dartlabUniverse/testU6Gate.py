"""Universe U6 GPU transport와 독립 3D GUI gate 회귀."""

from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

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
        publicRouteConnected=True,
        brandChromeConnected=True,
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


def testU6GateRejectsGpuGuiAndPublicEntryPointRegression() -> None:
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
        publicRouteConnected=False,
        brandChromeConnected=False,
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
        "DIRECT_UNIVERSE_ROUTE_MISSING",
        "BRAND_CHROME_SSOT_MISSING",
        "UNAPPROVED_PUBLIC_UNIVERSE_ENTRY_POINT",
    } <= set(report.failureCodes)


def testDirectRouteExistsWithoutAnyPublicEntryPoint() -> None:
    from tests._attempts.dartlabUniverse.u6Gate import (
        _brandChromeConnected,
        _directRouteConnected,
        _publicSurfaceReferenceCount,
    )

    repoRoot = Path(__file__).resolve().parents[3]
    assert _directRouteConnected(repoRoot)
    assert _brandChromeConnected(repoRoot)
    assert _publicSurfaceReferenceCount(repoRoot) == 0


def testRouteFragmentOnlySelectsLoopbackApiAndNeverAcceptsToken() -> None:
    guiRoot = Path(__file__).with_name("gui")
    app = (guiRoot / "app.js").read_text(encoding="utf-8")

    assert "ALLOWED_FRAGMENT_KEYS = new Set(['api'])" in app
    assert "params.get('token')" not in app
    assert "sessionFromFragment" not in app
    assert "window.history.replaceState" in app
    assert "payload.token" in app
    assert "/api/session" in app


def testSpaLifecycleAndCssRemainRouteScoped() -> None:
    repoRoot = Path(__file__).resolve().parents[3]
    guiRoot = Path(__file__).with_name("gui")
    app = (guiRoot / "app.js").read_text(encoding="utf-8")
    codec = (guiRoot / "tile-codec.js").read_text(encoding="utf-8")
    css = (guiRoot / "universe.css").read_text(encoding="utf-8")
    webgl = (guiRoot / "webgl2-renderer.js").read_text(encoding="utf-8")
    webgpu = (guiRoot / "webgpu-renderer.js").read_text(encoding="utf-8")
    page = (repoRoot / "landing" / "src" / "routes" / "universe" / "+page.svelte").read_text(encoding="utf-8")

    assert "function bindElements()" in app
    assert "function releaseElements()" in app
    assert "cancelAnimationFrame(frameRequestId)" in app
    assert "bootController?.abort()" in app
    assert "for (const cleanup of cleanupCallbacks.splice(0)) cleanup()" in app
    assert "loadManifest(token, apiBase, signal)" in app
    assert "loadTile(tileId, token, manifest.scene.projectionDigest, apiBase, signal)" in app
    assert "signal" in codec
    assert "dispose = module.disposeUniverse" in page
    assert "dispose?.();" in page
    assert "delete document.body.dataset.universeRoute" in page

    assert ":root" not in css
    assert "prefers-color-scheme: light" not in css
    assert "body[data-universe-route='true']" in css
    assert "body[data-universe-standalone='true']" in css
    assert "#universe-shell [hidden]" in css
    assert "\nhtml," not in css
    assert "\nbody {" not in css
    assert "\nbutton {" not in css
    assert "\n* {" not in css
    assert "getComputedStyle(document.documentElement)" not in webgl
    assert "getComputedStyle(document.documentElement)" not in webgpu
    assert "palette(this.canvas)" in webgl
    assert "palette(this.canvas)" in webgpu


def testRouteLifecycleRebindAndAbortBehaviorInNode() -> None:
    appUri = (Path(__file__).with_name("gui") / "app.js").resolve().as_uri()
    script = """
import assert from 'node:assert/strict';

const ids = [
  'universe-canvas', 'label-layer', 'loading-state', 'loading-title',
  'loading-detail', 'error-state', 'error-title', 'error-detail',
  'backend-label', 'visible-count', 'scope-label', 'selection-panel',
  'selection-kicker', 'selection-title', 'selection-facts', 'drill-button',
  'back-button', 'labels-button', 'edges-button'
];
const makeSurface = () => new Map(ids.map((id) => [id, {
  id, dataset: {}, hidden: false, textContent: '',
  addEventListener() {}, removeEventListener() {}
}]));
let elements = makeSurface();
const fetches = [];
let replacedUrl = '';
globalThis.location = {
  hash: '#api=http%3A%2F%2F127.0.0.1%3A9876&token=secret&backend=webgl2',
  pathname: '/universe', search: '', origin: 'https://eddmpython.github.io'
};
globalThis.window = { history: {
  state: null,
  replaceState(_state, _title, url) { replacedUrl = url; }
}};
globalThis.document = {
  body: { dataset: { universeRoute: 'true' } }, hidden: false,
  getElementById(id) { return elements.get(id) ?? null; },
  addEventListener() {}, removeEventListener() {}
};
globalThis.fetch = (url, options) => {
  fetches.push({ url, signal: options.signal });
  return new Promise((_resolve, reject) => options.signal.addEventListener(
    'abort', () => reject(new DOMException('aborted', 'AbortError')), { once: true }
  ));
};
const universe = await import('__APP_URI__');
const firstBoot = universe.bootUniverse();
await Promise.resolve();
assert.equal(fetches[0].url, 'http://127.0.0.1:9876/api/session');
assert.equal(replacedUrl, '/universe#api=http%3A%2F%2F127.0.0.1%3A9876');
universe.disposeUniverse();
await firstBoot;
assert.equal(fetches[0].signal.aborted, true);

const secondSurface = makeSurface();
elements = secondSurface;
location.hash = '';
const secondBoot = universe.bootUniverse();
await Promise.resolve();
assert.equal(fetches[1].url, 'http://127.0.0.1:8765/api/session');
assert.equal(
  secondSurface.get('loading-title').textContent,
  '로컬 지식 엔진에 연결하고 있습니다'
);
universe.disposeUniverse();
await secondBoot;
assert.equal(fetches[1].signal.aborted, true);
""".replace("__APP_URI__", appUri)
    subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        cwd=Path(__file__).resolve().parents[3],
        check=True,
        capture_output=True,
        text=True,
    )
