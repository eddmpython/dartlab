"""외부 서버 관리자 인증과 요청 본문 예산 회귀 테스트."""

from __future__ import annotations

import asyncio
import json
import time

import pytest

pytestmark = pytest.mark.unit


def _adminApp():
    from fastapi import FastAPI

    from dartlab.server.security import AdminBoundaryMiddleware

    app = FastAPI()
    app.add_middleware(AdminBoundaryMiddleware)

    @app.put("/api/ai/profile")
    async def updateProfile():
        return {"ok": True}

    @app.get("/api/status")
    async def status():
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app


def test_localAdminMutationRemainsAvailable(monkeypatch) -> None:
    from starlette.testclient import TestClient

    for name in ("SPACE_ID", "DARTLAB_CHANNEL", "DARTLAB_TUNNEL", "DARTLAB_MCP_HTTP", "DARTLAB_ADMIN_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DARTLAB_HOST", "127.0.0.1")

    with TestClient(_adminApp()) as client:
        response = client.put("/api/ai/profile")

    assert response.status_code == 200


def test_localCrossOriginAdminMutationIsBlocked(monkeypatch) -> None:
    from starlette.testclient import TestClient

    monkeypatch.setenv("DARTLAB_HOST", "127.0.0.1")
    with TestClient(_adminApp()) as client:
        response = client.put("/api/ai/profile", headers={"Origin": "https://evil.example"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_origin_blocked"


def test_exposedAdminMutationFailsClosedWithoutToken(monkeypatch) -> None:
    from starlette.testclient import TestClient

    monkeypatch.setenv("DARTLAB_TUNNEL", "1")
    monkeypatch.delenv("DARTLAB_ADMIN_TOKEN", raising=False)
    with TestClient(_adminApp(), base_url="https://public.example") as client:
        response = client.put("/api/ai/profile")

    assert response.status_code == 503
    assert response.json()["status"] == "blocked"
    assert response.json()["error"]["code"] == "admin_auth_not_configured"


def test_exposedModeCannotTrustLoopbackProxyHop(monkeypatch) -> None:
    from starlette.testclient import TestClient

    monkeypatch.setenv("DARTLAB_TUNNEL", "1")
    monkeypatch.delenv("DARTLAB_ADMIN_TOKEN", raising=False)
    with TestClient(_adminApp()) as client:
        response = client.get("/api/status")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "execution_auth_not_configured"


def test_exposedAdminMutationRequiresMatchingBearer(monkeypatch) -> None:
    from starlette.testclient import TestClient

    token = "a" * 32
    monkeypatch.setenv("DARTLAB_TUNNEL", "1")
    monkeypatch.setenv("DARTLAB_ADMIN_TOKEN", token)
    with TestClient(_adminApp(), base_url="https://public.example") as client:
        missing = client.put("/api/ai/profile")
        wrong = client.put("/api/ai/profile", headers={"Authorization": f"Bearer {'b' * 32}"})
        accepted = client.put("/api/ai/profile", headers={"Authorization": f"Bearer {token}"})

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert accepted.status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/agent/runs"),
        ("POST", "/api/ask"),
        ("GET", "/api/ask/artifacts/2026-08-01/result.csv"),
        ("POST", "/api/company/005930/copilot"),
        ("GET", "/api/company/005930/summary/BS"),
        ("POST", "/api/company/005930/show/BS/0/parse"),
        ("POST", "/api/dl/call"),
        ("GET", "/mcp/sse"),
        ("POST", "/api/configure"),
        ("POST", "/api/provider/validate"),
        ("GET", "/api/export/excel/005930"),
        ("GET", "/api/status"),
        ("GET", "/api/ai/profile"),
        ("GET", "/api/ai/profile/events"),
        ("GET", "/api/channel"),
        ("GET", "/api/oauth/status"),
        ("GET", "/api/models/openai"),
    ],
)
def test_exposedExecutionAndResultRoutesFailClosed(monkeypatch, method: str, path: str) -> None:
    from starlette.testclient import TestClient

    monkeypatch.setenv("DARTLAB_TUNNEL", "1")
    monkeypatch.delenv("DARTLAB_ADMIN_TOKEN", raising=False)
    with TestClient(_adminApp(), base_url="https://public.example") as client:
        response = client.request(method, path)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "execution_auth_not_configured"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/export/templates"),
        ("DELETE", "/api/export/templates/custom"),
        ("PUT", "/api/openapi/dart-key"),
        ("POST", "/api/oauth/authorize"),
    ],
)
def test_exposedFilesystemMutationsFailClosed(monkeypatch, method: str, path: str) -> None:
    from starlette.testclient import TestClient

    monkeypatch.setenv("DARTLAB_TUNNEL", "1")
    monkeypatch.delenv("DARTLAB_ADMIN_TOKEN", raising=False)
    with TestClient(_adminApp(), base_url="https://public.example") as client:
        response = client.request(method, path)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "admin_auth_not_configured"


def test_oauthAuthorizeIsPostOnly() -> None:
    from dartlab.server import app

    oauthRoutes = [route for route in app.routes if getattr(route, "path", None) == "/api/oauth/authorize"]

    assert len(oauthRoutes) == 1
    assert oauthRoutes[0].methods == {"POST"}


def test_publicNonSensitiveReadDoesNotRequireAdminToken(monkeypatch) -> None:
    from starlette.testclient import TestClient

    monkeypatch.setenv("DARTLAB_TUNNEL", "1")
    monkeypatch.delenv("DARTLAB_ADMIN_TOKEN", raising=False)
    with TestClient(_adminApp(), base_url="https://public.example") as client:
        response = client.get("/health")

    assert response.status_code == 200


def test_tunnelCorsDefaultIsNotWildcard(monkeypatch) -> None:
    monkeypatch.delenv("DARTLAB_CORS_ORIGINS", raising=False)
    monkeypatch.setenv("DARTLAB_TUNNEL", "1")

    from dartlab.server import _corsOrigins

    assert _corsOrigins() != ["*"]


def test_requestBudgetRejectsOversizedJson(monkeypatch) -> None:
    from fastapi import FastAPI, Request
    from starlette.testclient import TestClient

    from dartlab.server.security import RequestBudgetMiddleware

    monkeypatch.setenv("DARTLAB_MAX_REQUEST_BYTES", "65536")
    app = FastAPI()
    app.add_middleware(RequestBudgetMiddleware)

    @app.post("/echo")
    async def echo(request: Request):
        return await request.json()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/echo", json={"value": "x" * 70_000})

    assert response.status_code == 413
    assert response.json()["status"] == "blocked"
    assert response.json()["error"]["code"] == "request_too_large"


def test_roomStateNeverPublishesMemberBearer() -> None:
    from dartlab.server.room import Room

    room = Room("fixture-room")
    host = room.getMember(room.host_member_id)
    assert host is not None

    state = room.getState()

    assert len(host.memberId) >= 32
    assert state["members"][0]["memberId"] == host.publicId
    assert state["members"][0]["memberId"] != host.memberId


def test_dlEnvelopePreservesPartialStatus(monkeypatch) -> None:
    from dartlab.server.api import dl

    monkeypatch.setattr(
        dl, "_dispatch", lambda *_args, **_kwargs: {"status": "partial", "gaps": [{"status": "missing"}]}
    )

    result = asyncio.run(dl.apiDlCall(dl.DlCallRequest(apiRef="analysis")))

    assert result["status"] == "partial"
    assert result["data"]["status"] == "partial"
    assert result["ok"] is True
    assert result["serialization"]["bytes"] == len(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def test_dlDispatchDoesNotBlockEventLoop(monkeypatch) -> None:
    from dartlab.server.api import dl

    monkeypatch.setattr(dl, "_dispatch", lambda *_args, **_kwargs: time.sleep(0.2) or {"status": "partial"})

    async def _scenario() -> float:
        started = time.perf_counter()
        task = asyncio.create_task(dl.apiDlCall(dl.DlCallRequest(apiRef="analysis")))
        await asyncio.sleep(0.02)
        elapsed = time.perf_counter() - started
        await task
        return elapsed

    assert asyncio.run(_scenario()) < 0.12


def test_serverSerializerPreservesLowerStatusAndMarksTruncation() -> None:
    from dartlab.server.api.common import serializePayload

    payload = {
        "status": "partial",
        "gaps": [{"status": "missing", "sourceRef": "fixture://gap"}],
        "items": list(range(505)),
    }

    result = serializePayload(payload)

    assert result["data"]["status"] == "partial"
    assert result["data"]["gaps"][0]["status"] == "missing"
    assert result["serialization"]["status"] == "partial"
    assert "maxItems" in result["serialization"]["reasons"]
    assert result["serialization"]["bytes"] == len(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def test_serverSerializerFailsClosedOnCycle() -> None:
    from dartlab.server.api.common import serializePayload

    payload: dict = {}
    payload["self"] = payload

    result = serializePayload(payload)

    assert result["data"]["self"]["status"] == "blocked"
    assert result["serialization"]["status"] == "blocked"
    assert "cyclicPayload" in result["serialization"]["reasons"]


def test_ollamaPullIsRemovedFromProductRuntime() -> None:
    from fastapi import HTTPException

    from dartlab.server.api.ai import apiOllamaPull

    with pytest.raises(HTTPException) as caught:
        apiOllamaPull({"model": "qwen3"})

    assert caught.value.status_code == 410
    assert "설치형 agent CLI" in str(caught.value.detail)
