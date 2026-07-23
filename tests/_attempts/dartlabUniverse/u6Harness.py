"""공개 UI와 분리된 loopback-only DartLab Universe 3D 검수 harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlencode, urlparse

from .catalog.models import CatalogResource, CatalogState
from .catalog.recoveryStore import defaultRecoveryRoot
from .spatial.contracts import ProjectionRequest
from .spatial.projectionState import compileSpatialProjection
from .spatialTestSupport import spatialFixture, spatialRequest
from .u3C2 import defaultCheckpointPath
from .u3Gate import buildLiveU3Artifacts, defaultControlRoot
from .u6Transport import UniverseGpuTransport

_STATIC_TYPES = {
    "index.html": "text/html; charset=utf-8",
    "universe.css": "text/css; charset=utf-8",
    "math.js": "text/javascript; charset=utf-8",
    "camera.js": "text/javascript; charset=utf-8",
    "tile-codec.js": "text/javascript; charset=utf-8",
    "webgl2-renderer.js": "text/javascript; charset=utf-8",
    "webgpu-renderer.js": "text/javascript; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
}

_OPAQUE_LABEL = re.compile(r"[0-9a-f]{32,}", re.IGNORECASE)
_GENERIC_LABELS = {
    "media_catalog_record",
    "objects",
    "object",
    "record",
}
_OBJECT_KIND_LABELS = {
    "BLOG_POST": "블로그 글",
    "CAPABILITY": "분석 기능",
    "DATASET": "데이터셋",
    "DOCUMENT": "문서",
    "MEDIA": "미디어 객체",
    "MEDIA_ASSET": "미디어 객체",
    "ORGANIZATION": "법인",
    "TABLE": "데이터 테이블",
}


def _isOpaqueLabel(value: str) -> bool:
    compact = value.strip()
    return (
        not compact
        or compact.casefold() in _GENERIC_LABELS
        or compact.startswith("du:v1:")
        or "/sha256/" in compact.casefold()
        or bool(_OPAQUE_LABEL.fullmatch(compact))
    )


def _resourceDisplayLabel(resource: CatalogResource) -> str:
    locator = dict(resource.locator)
    candidates = (
        locator.get("title", ""),
        locator.get("name", ""),
        locator.get("path", ""),
        resource.label,
    )
    for value in candidates:
        value = str(value).strip()
        if not value:
            continue
        name = PurePosixPath(value.replace("\\", "/")).name or value
        if not _isOpaqueLabel(name):
            return name
    return ""


def _displayObjectLabels(catalog: CatalogState) -> dict[str, str]:
    """원본 ID는 유지하고 브라우저에만 사람 친화적인 이름을 제공한다."""

    resources = {item.resourceVersionId: item for item in catalog.resources}
    labels: dict[str, str] = {}
    for item in catalog.objects:
        label = item.canonicalLabel.strip()
        if _isOpaqueLabel(label):
            resource = next((resources.get(ref) for ref in item.resourceRefs if ref in resources), None)
            replacement = _resourceDisplayLabel(resource) if resource is not None else ""
            if replacement:
                label = replacement
            else:
                kindLabel = _OBJECT_KIND_LABELS.get(item.objectKind.upper(), "지식 객체")
                suffix = item.objectId.rsplit(":", 1)[-1][:8]
                label = f"{kindLabel} {suffix}"
        labels[item.objectId] = label
    return labels


def _liveRequest(snapshotId: str) -> ProjectionRequest:
    from .contracts import Visibility

    return ProjectionRequest(
        snapshotId=snapshotId,
        projectionVersion="du-projection-live-v1",
        objectScope=(),
        relationScope=(),
        validAt="9999-12-30T00:00:00Z",
        knownAt="9999-12-30T00:00:00Z",
        activeLens="overview",
        allowedVisibility=(Visibility.PUBLIC, Visibility.LOCAL, Visibility.PRIVATE, Visibility.RESTRICTED),
        seed=20260722,
    )


def buildFixtureTransport() -> UniverseGpuTransport:
    fixture = spatialFixture()
    request = spatialRequest(fixture, count=len(fixture.catalog.objects))
    projection = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=request,
        statements=fixture.statements,
    )
    labels = _displayObjectLabels(fixture.catalog)
    return UniverseGpuTransport(projection, objectLabels=labels)


def buildLiveTransport(
    *,
    checkpointPath: Path,
    recoveryRoot: Path,
    u3ControlRoot: Path,
) -> UniverseGpuTransport:
    artifacts = buildLiveU3Artifacts(
        checkpointPath=checkpointPath,
        recoveryRoot=recoveryRoot,
        controlRoot=u3ControlRoot,
    )
    if not artifacts.report.passed:
        raise RuntimeError(f"U6 live harness가 실패한 U3를 거부함: {artifacts.report.failureCodes}")
    projection = compileSpatialProjection(
        artifacts.catalog,
        artifacts.snapshot,
        artifacts.relations,
        request=_liveRequest(artifacts.snapshot.snapshotId),
    )
    labels = _displayObjectLabels(artifacts.catalog)
    return UniverseGpuTransport(projection, objectLabels=labels)


def _handlerFactory(
    transport: UniverseGpuTransport,
    token: str,
    staticRoot: Path,
    allowedOrigin: str | None = None,
):
    class UniverseHandler(BaseHTTPRequestHandler):
        server_version = "DartLabUniverseHarness/1"

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _securityHeaders(self) -> None:
            self.send_header("Cache-Control", "no-store")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'",
            )
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            routeSession = self.headers.get("Origin") == allowedOrigin
            self.send_header(
                "Cross-Origin-Resource-Policy",
                "cross-origin" if routeSession else "same-origin",
            )
            if routeSession:
                self.send_header("Access-Control-Allow-Origin", allowedOrigin)
                self.send_header("Access-Control-Allow-Private-Network", "true")
                self.send_header("Access-Control-Expose-Headers", "ETag")
                self.send_header("Vary", "Origin")

        def _send(self, payload: bytes, contentType: str, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            self.send_response(status)
            self._securityHeaders()
            self.send_header("Content-Type", contentType)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("ETag", f'"{hashlib.sha256(payload).hexdigest()}"')
            self.end_headers()
            self.wfile.write(payload)

        def _authorized(self) -> bool:
            provided = self.headers.get("X-DartLab-Universe-Token", "")
            return secrets.compare_digest(provided, token)

        def do_OPTIONS(self) -> None:  # noqa: N802
            if allowedOrigin is None or self.headers.get("Origin") != allowedOrigin:
                self._send(b"", "text/plain; charset=utf-8", status=HTTPStatus.FORBIDDEN)
                return
            self.send_response(HTTPStatus.NO_CONTENT)
            self._securityHeaders()
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "X-DartLab-Universe-Token")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/") and not self._authorized():
                self._send(b'{"error":"unauthorized"}', "application/json", status=HTTPStatus.UNAUTHORIZED)
                return
            if parsed.path == "/api/manifest":
                self._send(transport.manifestPayload(), "application/json; charset=utf-8")
                return
            if parsed.path.startswith("/api/tile/"):
                tileId = unquote(parsed.path.removeprefix("/api/tile/"))
                try:
                    payload = transport.encodeTile(tileId)
                except KeyError:
                    self._send(b'{"error":"tile_not_found"}', "application/json", status=HTTPStatus.NOT_FOUND)
                    return
                self._send(payload, "application/vnd.dartlab.universe-gpu-tile")
                return
            staticName = "index.html" if parsed.path in {"", "/"} else parsed.path.removeprefix("/")
            contentType = _STATIC_TYPES.get(staticName)
            if contentType is None:
                self._send(b"not found", "text/plain; charset=utf-8", status=HTTPStatus.NOT_FOUND)
                return
            self._send((staticRoot / staticName).read_bytes(), contentType)

    return UniverseHandler


def serveTransport(
    transport: UniverseGpuTransport,
    *,
    host: str,
    port: int,
    openBrowser: bool,
    routeUrl: str | None = None,
) -> None:
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("U6 harness는 loopback host만 허용함")
    token = secrets.token_urlsafe(32)
    staticRoot = Path(__file__).with_name("gui")
    parsedRoute = urlparse(routeUrl) if routeUrl else None
    if parsedRoute and (
        parsedRoute.scheme not in {"http", "https"}
        or not parsedRoute.netloc
        or parsedRoute.query
        or parsedRoute.fragment
    ):
        raise ValueError("route URL은 query와 fragment가 없는 http(s) 절대주소여야 함")
    allowedOrigin = f"{parsedRoute.scheme}://{parsedRoute.netloc}" if parsedRoute else None
    server = ThreadingHTTPServer(
        (host, port),
        _handlerFactory(transport, token, staticRoot, allowedOrigin),
    )
    server.daemon_threads = True
    actualPort = int(server.server_address[1])
    runtimeUrl = f"http://{host}:{actualPort}"
    standaloneUrl = f"{runtimeUrl}/#token={token}"
    url = f"{routeUrl.rstrip('/')}/#{urlencode({'api': runtimeUrl, 'token': token})}" if routeUrl else standaloneUrl
    summary = {
        "schemaVersion": "du-u6-harness-session-v1",
        "url": url,
        "runtimeUrl": runtimeUrl,
        "sceneId": transport.projection.manifest.sceneId,
        "snapshotId": transport.projection.manifest.snapshotId,
        "objectCount": transport.projection.manifest.objectCount,
        "relationCount": transport.projection.manifest.relationCount,
        "tileCount": transport.projection.manifest.tileCount,
        "persistenceMode": "EPHEMERAL",
        "publicRouteConnected": bool(routeUrl),
        "publicButtonConnected": False,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
    if openBrowser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def buildArgumentParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DartLab Universe 독립 3D 검수 harness")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="현재 통과한 U3 pin으로 전체 Universe를 구성")
    mode.add_argument("--fixture", action="store_true", help="결정적 대형 fixture로 빠르게 검수")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--open", action="store_true")
    parser.add_argument(
        "--route-url",
        default=os.getenv("DARTLAB_UNIVERSE_ROUTE_URL", "http://127.0.0.1:5173/universe"),
        help="직접 검수할 /universe 화면 주소. 지정하면 해당 화면에 loopback 세션을 연결",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="landing route 대신 harness 자체 화면을 사용",
    )
    parser.add_argument("--checkpoint", type=Path, default=defaultCheckpointPath())
    parser.add_argument("--recovery-root", type=Path, default=defaultRecoveryRoot())
    parser.add_argument("--u3-control-root", type=Path, default=defaultControlRoot())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = buildArgumentParser().parse_args(argv)
    if args.port < 0 or args.port > 65535:
        raise ValueError("port 범위가 잘못됨")
    transport = (
        buildLiveTransport(
            checkpointPath=args.checkpoint,
            recoveryRoot=args.recovery_root,
            u3ControlRoot=args.u3_control_root,
        )
        if args.live
        else buildFixtureTransport()
    )
    serveTransport(
        transport,
        host=args.host,
        port=args.port,
        openBrowser=args.open,
        routeUrl=None if args.standalone else args.route_url,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
