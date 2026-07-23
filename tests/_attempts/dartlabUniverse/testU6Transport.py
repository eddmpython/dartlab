"""U6 local-only 3D transport와 loopback 보안 경계를 검증한다."""

from __future__ import annotations

import hashlib
import json
import struct
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from tests._attempts.dartlabUniverse.spatialTestSupport import spatialFixture
from tests._attempts.dartlabUniverse.u6Harness import (
    _DEFAULT_ROUTE_ORIGINS,
    _displayObjectLabels,
    _handlerFactory,
    _launchUrl,
    buildArgumentParser,
    buildFixtureTransport,
)
from tests._attempts.dartlabUniverse.u6Transport import (
    EDGE_RECORD,
    GPU_TILE_MAGIC,
    NODE_RECORD,
)


@pytest.fixture(scope="module")
def transport():
    return buildFixtureTransport()


def _decodeHeader(payload: bytes):
    assert payload[:8] == GPU_TILE_MAGIC
    headerLength = struct.unpack_from("<I", payload, 8)[0]
    header = json.loads(payload[12 : 12 + headerLength])
    return header, payload[12 + headerLength :]


def testGpuTilePreservesEnvelopeBindingAndFixedRecordCardinality(transport):
    manifest = json.loads(transport.manifestPayload())
    payload = transport.encodeTile(manifest["rootTileId"])
    header, records = _decodeHeader(payload)

    assert manifest["schemaVersion"] == "du-gpu-manifest-v1"
    assert manifest["meaningPreservation"] == 1.0
    assert manifest["transport"]["persistenceMode"] == "EPHEMERAL"
    assert header["projectionDigest"] == manifest["scene"]["projectionDigest"]
    assert header["sourceContentDigest"]
    assert header["nodeStride"] == NODE_RECORD.size == 28
    assert header["edgeStride"] == EDGE_RECORD.size == 32
    assert len(records) == header["nodeBytes"] + header["edgeBytes"]
    assert hashlib.sha256(records).hexdigest() == header["recordDigest"]
    assert len(header["nodeMetadata"]) == header["nodeCount"]


def testGpuTransportRejectsUnknownTileWithoutLeakingFallback(transport):
    with pytest.raises(KeyError):
        transport.encodeTile("du:v1:scene-tile:" + "0" * 64)


def testDisplayAdapterReplacesOpaqueIdsWithoutChangingCatalogTruth():
    transport = buildFixtureTransport()
    catalog = spatialFixture().catalog
    labels = _displayObjectLabels(catalog)

    assert labels.keys() == {item.objectId for item in catalog.objects}
    assert all(not label.startswith("du:v1:") for label in labels.values())
    assert all("/sha256/" not in label.casefold() for label in labels.values())
    assert transport.objectLabels


def testLoopbackHandlerRequiresSessionTokenForPrivateRuntimeData(transport):
    token = "fixture-local-session-token-that-is-long-enough"
    staticRoot = Path(__file__).with_name("gui")
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handlerFactory(transport, token, staticRoot))
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urllib.request.urlopen(base + "/", timeout=5) as response:
            assert response.status == 200
            assert b"universe-canvas" in response.read()
            assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]

        with pytest.raises(urllib.error.HTTPError) as captured:
            urllib.request.urlopen(base + "/api/manifest", timeout=5)
        assert captured.value.code == 401

        request = urllib.request.Request(
            base + "/api/manifest",
            headers={"X-DartLab-Universe-Token": token},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            manifest = json.loads(response.read())
            assert response.headers["Cache-Control"] == "no-store"
            assert manifest["scene"]["objectCount"] == len(transport.projection.state.coordinates)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def testRouteSessionCorsAllowsOnlyPinnedOrigin(transport):
    token = "fixture-local-session-token-that-is-long-enough"
    staticRoot = Path(__file__).with_name("gui")
    routeOrigin = "https://eddmpython.github.io"
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        _handlerFactory(transport, token, staticRoot, routeOrigin),
    )
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        preflight = urllib.request.Request(
            f"{base}/api/manifest",
            method="OPTIONS",
            headers={
                "Origin": routeOrigin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-DartLab-Universe-Token",
                "Access-Control-Request-Private-Network": "true",
            },
        )
        with urllib.request.urlopen(preflight) as response:
            assert response.status == 204
            assert response.headers["Access-Control-Allow-Origin"] == routeOrigin
            assert response.headers["Access-Control-Allow-Private-Network"] == "true"

        session = urllib.request.Request(
            f"{base}/api/session",
            headers={"Origin": routeOrigin},
        )
        with urllib.request.urlopen(session) as response:
            payload = json.loads(response.read())
            assert response.status == 200
            assert payload == {
                "schemaVersion": "du-u6-route-session-v1",
                "token": token,
            }
            assert response.headers["Access-Control-Allow-Origin"] == routeOrigin

        for deniedOrigin in (None, "https://example.com"):
            headers = {"Origin": deniedOrigin} if deniedOrigin else {}
            deniedSession = urllib.request.Request(f"{base}/api/session", headers=headers)
            with pytest.raises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(deniedSession)
            assert error.value.code == 403

        unauthenticatedManifest = urllib.request.Request(
            f"{base}/api/manifest",
            headers={"Origin": routeOrigin},
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(unauthenticatedManifest)
        assert error.value.code == 401

        manifest = urllib.request.Request(
            f"{base}/api/manifest",
            headers={
                "Origin": routeOrigin,
                "X-DartLab-Universe-Token": token,
            },
        )
        with urllib.request.urlopen(manifest) as response:
            assert response.status == 200
            assert response.headers["Access-Control-Allow-Origin"] == routeOrigin
            assert response.headers["Cross-Origin-Resource-Policy"] == "cross-origin"

        denied = urllib.request.Request(
            f"{base}/api/manifest",
            method="OPTIONS",
            headers={"Origin": "https://example.com"},
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(denied)
        assert error.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def testRouteSessionCorsSupportsExactProductAndDevelopmentOrigins(transport):
    token = "fixture-local-session-token-that-is-long-enough"
    staticRoot = Path(__file__).with_name("gui")
    routeOrigins = (
        "https://eddmpython.github.io",
        "http://127.0.0.1:5173",
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        _handlerFactory(transport, token, staticRoot, routeOrigins),
    )
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        for routeOrigin in routeOrigins:
            request = urllib.request.Request(
                f"{base}/api/session",
                headers={"Origin": routeOrigin},
            )
            with urllib.request.urlopen(request) as response:
                assert response.status == 200
                assert response.headers["Access-Control-Allow-Origin"] == routeOrigin

        standalone = urllib.request.Request(
            f"{base}/api/session",
            headers={
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
            },
        )
        with urllib.request.urlopen(standalone) as response:
            assert response.status == 200
            assert response.headers.get("Access-Control-Allow-Origin") is None

        denied = urllib.request.Request(
            f"{base}/api/session",
            headers={"Origin": "https://eddmpython.github.io.attacker.example"},
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(denied)
        assert error.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def testLaunchUrlNeverContainsSessionToken():
    routeUrl = "https://eddmpython.github.io/dartlab/universe"
    direct = _launchUrl(routeUrl=routeUrl, runtimeUrl="http://127.0.0.1:8765")
    custom = _launchUrl(routeUrl=routeUrl, runtimeUrl="http://127.0.0.1:9876")
    standalone = _launchUrl(routeUrl=None, runtimeUrl="http://127.0.0.1:8765")

    assert direct == routeUrl
    assert custom == routeUrl + "/#api=http%3A%2F%2F127.0.0.1%3A9876"
    assert standalone == "http://127.0.0.1:8765"
    assert all("token" not in url.casefold() for url in (direct, custom, standalone))


def testHarnessAssetsRemainIndependentFromPublicUi():
    guiRoot = Path(__file__).with_name("gui")
    expected = {
        "index.html",
        "universe.css",
        "math.js",
        "camera.js",
        "tile-codec.js",
        "webgl2-renderer.js",
        "webgpu-renderer.js",
        "app.js",
    }

    assert expected == {item.name for item in guiRoot.iterdir() if item.is_file()}
    assert "http://127.0.0.1:8765" in (guiRoot / "app.js").read_text(encoding="utf-8")
    assert all("http://" not in (guiRoot / item).read_text(encoding="utf-8") for item in expected - {"app.js"})
    assert all("https://" not in (guiRoot / item).read_text(encoding="utf-8") for item in expected)


def testHarnessDefaultPortMatchesDirectRouteDiscoveryPort():
    args = buildArgumentParser().parse_args([])
    assert args.host == "127.0.0.1"
    assert args.port == 8765
    assert args.route_url == "http://127.0.0.1:5173/universe"
    assert tuple(args.allowed_origin) == _DEFAULT_ROUTE_ORIGINS
