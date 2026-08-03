"""HTTP 요청 예산과 관리자 상태 변경 경계를 강제한다."""

from __future__ import annotations

import json
import os
import re
import secrets
from ipaddress import ip_address
from urllib.parse import urlsplit

DEFAULT_REQUEST_BYTES = 1_048_576
MIN_ADMIN_TOKEN_LENGTH = 32

_ADMIN_ROUTES = {
    ("PUT", "/api/ai/profile"),
    ("POST", "/api/ai/profile/secrets"),
    ("PUT", "/api/openapi/dart-key"),
    ("DELETE", "/api/openapi/dart-key"),
    ("POST", "/api/oauth/authorize"),
    ("POST", "/api/oauth/logout"),
    ("POST", "/api/codex/logout"),
    ("POST", "/api/channel/start"),
    ("POST", "/api/channel/stop"),
    ("POST", "/api/ollama/pull"),
    ("POST", "/api/export/templates"),
    ("POST", "/api/agent/runtimes/install/apply"),
    ("POST", "/api/agent/runtimes/mcp/apply"),
}

_EXECUTION_ROUTES = {
    ("GET", "/api/status"),
    ("GET", "/api/ai/profile"),
    ("GET", "/api/ai/profile/events"),
    ("GET", "/api/channel"),
    ("GET", "/api/oauth/status"),
    ("POST", "/api/agent/runs"),
    ("POST", "/api/ask"),
    ("POST", "/api/configure"),
    ("POST", "/api/provider/validate"),
    ("POST", "/api/openapi/dart-key/validate"),
    ("POST", "/api/dl/call"),
    ("POST", "/api/room/ask"),
}

_KNOWN_PUBLIC_EXACT_PATHS = frozenset(
    {
        "/api/status",
        "/api/suggest",
        "/api/search",
        "/api/spec",
        "/api/data/stats",
        "/api/export/templates",
        "/api/room/state",
        "/api/room/stream",
    }
)
_KNOWN_PUBLIC_PATHS = re.compile(
    r"^/api/company/[A-Za-z0-9]+(?:$|/(?:meta|lenses|index|panel(?:/.*)?|viewer2/.*|show/.*|trace/.*|summary/.*|insights(?:/.*)?|network|scan/.*|diff(?:/.*)?|bridge/.*|topics/graph|search|searchIndex|modules|copilot))$"
)


def _isWhitelisted(path: str) -> bool:
    """옛 R36 진단 소비자를 위한 현재 공개 Company/API 경로 판정 helper."""
    return path in _KNOWN_PUBLIC_EXACT_PATHS or bool(_KNOWN_PUBLIC_PATHS.fullmatch(path))


_is_whitelisted = _isWhitelisted


def _errorBody(code: str, message: str, *, retryable: bool = False) -> bytes:
    payload = {
        "schemaVersion": "dartlab.http.error.v1",
        "status": "blocked",
        "error": {"code": code, "message": message, "retryable": retryable},
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


async def _sendError(send, statusCode: int, code: str, message: str, *, authenticate: bool = False) -> None:
    body = _errorBody(code, message)
    headers = [
        (b"content-type", b"application/json; charset=utf-8"),
        (b"content-length", str(len(body)).encode("ascii")),
        (b"cache-control", b"no-store"),
        (b"x-content-type-options", b"nosniff"),
    ]
    if authenticate:
        headers.append((b"www-authenticate", b"Bearer"))
    await send({"type": "http.response.start", "status": statusCode, "headers": headers})
    await send({"type": "http.response.body", "body": body})


def _header(scope, name: bytes) -> str:
    for key, value in scope.get("headers", []):
        if key.lower() == name:
            return value.decode("latin-1")
    return ""


def _isLoopback(value: str) -> bool:
    candidate = value.strip().strip("[]")
    if not candidate:
        return False
    try:
        return ip_address(candidate).is_loopback
    except ValueError:
        return candidate.lower() == "localhost"


def _hostName(hostHeader: str) -> str:
    if hostHeader.startswith("["):
        return hostHeader.split("]", 1)[0] + "]"
    return hostHeader.split(":", 1)[0]


def _originIsLocal(origin: str) -> bool:
    if not origin:
        return True
    try:
        parsed = urlsplit(origin)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and _isLoopback(parsed.hostname or "")


def _isExposedMode() -> bool:
    if os.environ.get("SPACE_ID"):
        return True
    if any(os.environ.get(name) == "1" for name in ("DARTLAB_CHANNEL", "DARTLAB_TUNNEL", "DARTLAB_MCP_HTTP")):
        return True
    host = os.environ.get("DARTLAB_HOST", "127.0.0.1")
    return not _isLoopback(host)


def _isLocalTransport(scope) -> bool:
    host = _hostName(_header(scope, b"host"))
    client = scope.get("client") or ("", 0)
    clientHost = str(client[0]) if client else ""

    if host in {"testclient", "testserver"} and clientHost == "testclient" and not _isExposedMode():
        return True
    return _isLoopback(host) and _isLoopback(clientHost)


def _routeScope(method: str, path: str) -> str | None:
    if (method, path) in _ADMIN_ROUTES:
        return "admin"
    if method == "POST" and path.startswith("/api/channels/") and path.endswith(("/start", "/stop")):
        return "admin"
    if method == "DELETE" and path.startswith("/api/export/templates/"):
        return "admin"
    if (method, path) in _EXECUTION_ROUTES:
        return "execution"
    if path.startswith("/api/agent/runtimes/") and path.endswith(("/install/plan", "/login/plan", "/mcp/plan")):
        return "admin"
    if path.startswith("/api/agent/"):
        return "execution"
    if path == "/mcp" or path.startswith("/mcp/"):
        return "execution"
    if method == "GET" and path.startswith("/api/models/"):
        return "execution"
    if path == "/api/ask" or path.startswith("/api/ask/"):
        return "execution"
    if path == "/api/export/excel" or path.startswith("/api/export/excel/"):
        return "execution"
    if path.startswith("/api/company/"):
        if path.endswith("/copilot") or "/summary/" in path:
            return "execution"
        if method == "POST" and "/show/" in path and path.endswith("/parse"):
            return "execution"
    return None


def _bearerToken(scope) -> str:
    authorization = _header(scope, b"authorization")
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer":
        return ""
    return token.strip()


class AdminBoundaryMiddleware:
    """로컬 실행만 무인증으로 허용하고 외부 관리자와 코드 실행은 bearer를 요구한다."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method", "GET")).upper()
        path = str(scope.get("path", ""))
        routeScope = _routeScope(method, path)
        if routeScope is None:
            await self.app(scope, receive, send)
            return

        if not _isExposedMode() and _isLocalTransport(scope):
            if _originIsLocal(_header(scope, b"origin")):
                await self.app(scope, receive, send)
                return
            await _sendError(
                send, 403, f"{routeScope}_origin_blocked", "로컬 보호 호출의 Origin이 허용되지 않았습니다."
            )
            return

        configured = os.environ.get("DARTLAB_ADMIN_TOKEN", "")
        if len(configured) < MIN_ADMIN_TOKEN_LENGTH:
            await _sendError(
                send,
                503,
                f"{routeScope}_auth_not_configured",
                "외부 보호 호출이 비활성화되었습니다. DARTLAB_ADMIN_TOKEN을 32자 이상으로 설정하세요.",
            )
            return

        supplied = _bearerToken(scope)
        if not supplied or not secrets.compare_digest(supplied, configured):
            await _sendError(
                send,
                401,
                f"{routeScope}_auth_required",
                "유효한 관리자 bearer token이 필요합니다.",
                authenticate=True,
            )
            return

        await self.app(scope, receive, send)


class _RequestPayloadTooLarge(Exception):
    pass


def _requestByteLimit() -> int:
    raw = os.environ.get("DARTLAB_MAX_REQUEST_BYTES", "")
    if not raw:
        return DEFAULT_REQUEST_BYTES
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_REQUEST_BYTES
    return max(65_536, min(value, 16_777_216))


class RequestBudgetMiddleware:
    """Content-Length 유무와 관계없이 HTTP 요청 본문 크기를 제한한다."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        limit = _requestByteLimit()
        contentLength = _header(scope, b"content-length")
        if contentLength:
            try:
                if int(contentLength) > limit:
                    await _sendError(send, 413, "request_too_large", f"요청 본문은 최대 {limit}바이트입니다.")
                    return
            except ValueError:
                await _sendError(send, 400, "invalid_content_length", "Content-Length가 올바르지 않습니다.")
                return

        consumed = 0

        async def _receive():
            nonlocal consumed
            message = await receive()
            if message.get("type") == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > limit:
                    raise _RequestPayloadTooLarge
            return message

        try:
            await self.app(scope, _receive, send)
        except _RequestPayloadTooLarge:
            await _sendError(send, 413, "request_too_large", f"요청 본문은 최대 {limit}바이트입니다.")
