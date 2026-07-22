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
    _displayObjectLabels,
    _handlerFactory,
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
    assert all("http://" not in (guiRoot / item).read_text(encoding="utf-8") for item in expected)
    assert all("https://" not in (guiRoot / item).read_text(encoding="utf-8") for item in expected)
