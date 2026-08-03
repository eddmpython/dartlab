"""로컬 UI 검수 API의 보안 경계와 세션·명령 왕복 회귀 테스트."""

from __future__ import annotations

from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from dartlab.server import app
from dartlab.server.api.uiQa import uiQaEnabled
from dartlab.server.security import _routeScope
from dartlab.server.services.uiQa import uiQaBroker


@pytest.fixture(autouse=True)
def _resetUiQa(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DARTLAB_HOST", "127.0.0.1")
    monkeypatch.setenv("DARTLAB_UI_QA", "1")
    monkeypatch.delenv("DARTLAB_CHANNEL", raising=False)
    monkeypatch.delenv("DARTLAB_TUNNEL", raising=False)
    monkeypatch.delenv("DARTLAB_MCP_HTTP", raising=False)
    monkeypatch.delenv("SPACE_ID", raising=False)
    uiQaBroker.reset()
    yield
    uiQaBroker.reset()


def _snapshot() -> dict:
    return {
        "route": "/chat?secret=drop-this",
        "title": "챗 · dartlab local",
        "viewport": {"x": 0, "y": 0, "width": 1280, "height": 720},
        "document": {"x": 0, "y": 0, "width": 1280, "height": 900},
        "activeQaId": "chat-input",
        "elements": [
            {
                "qaId": "chat-input",
                "tag": "textarea",
                "role": None,
                "label": "질문",
                "text": None,
                "disabled": False,
                "visible": True,
                "checked": None,
                "safeValue": "삼성전자 투자 분석",
                "rect": {"x": 200, "y": 650, "width": 700, "height": 48},
                "style": {
                    "display": "block",
                    "position": "static",
                    "color": "rgb(255, 255, 255)",
                    "backgroundColor": "rgba(0, 0, 0, 0)",
                    "fontSize": "15px",
                },
            }
        ],
        "diagnostics": [],
        "capturedAt": "2026-08-03T00:00:00.000Z",
    }


def testUiQaRoutesAreAlwaysAdminProtected():
    for method, path in (
        ("GET", "/api/ui-qa/config"),
        ("POST", "/api/ui-qa/sessions/register"),
        ("GET", "/api/ui-qa/sessions/example"),
        ("DELETE", "/api/ui-qa/sessions/example"),
    ):
        assert _routeScope(method, path) == "admin"


def testUiQaIsExplicitDevOnlyAndNeverExposed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DARTLAB_UI_QA")
    assert uiQaEnabled() is False
    monkeypatch.setenv("DARTLAB_UI_QA", "1")
    assert uiQaEnabled() is True
    monkeypatch.setenv("DARTLAB_HOST", "0.0.0.0")
    assert uiQaEnabled() is False


def testUiQaSessionSnapshotAndCommandRoundTrip():
    sessionId = str(uuid4())
    with TestClient(app) as client:
        config = client.get("/api/ui-qa/config")
        assert config.status_code == 200
        assert config.json()["enabled"] is True

        registered = client.post(
            "/api/ui-qa/sessions/register",
            json={
                "sessionId": sessionId,
                "clientName": "test-ui",
                "capabilities": ["semantic-snapshot", "fill", "arbitrary-script"],
            },
        )
        assert registered.status_code == 201
        assert registered.json()["capabilities"] == ["semantic-snapshot", "fill"]

        snapshot = client.post(f"/api/ui-qa/sessions/{sessionId}/snapshot", json=_snapshot())
        assert snapshot.status_code == 202

        created = client.post(
            f"/api/ui-qa/sessions/{sessionId}/commands",
            json={"action": "fill", "targetQaId": "chat-input", "value": "005930 투자 분석"},
        )
        assert created.status_code == 202
        commandId = created.json()["commandId"]

        delivered = client.get(f"/api/ui-qa/sessions/{sessionId}/commands/next")
        assert delivered.status_code == 200
        assert delivered.json()["commandId"] == commandId
        assert delivered.json()["status"] == "delivered"

        completed = client.post(
            f"/api/ui-qa/sessions/{sessionId}/commands/{commandId}/result",
            json={"ok": True, "detail": {"activeQaId": "chat-input"}},
        )
        assert completed.status_code == 200
        assert completed.json()["status"] == "succeeded"

        state = client.get(f"/api/ui-qa/sessions/{sessionId}")
        assert state.status_code == 200
        body = state.json()
        assert body["snapshot"]["route"] == "/chat"
        assert body["snapshot"]["elements"][0]["safeValue"] == "삼성전자 투자 분석"
        assert body["commands"][0]["status"] == "succeeded"


def testUiQaVisualPlanAndAuditReceipt():
    sessionId = str(uuid4())
    with TestClient(app) as client:
        plan = client.get("/api/ui-qa/audit-plan")
        assert plan.status_code == 200
        assert {item["viewportId"] for item in plan.json()["viewports"]} == {"desktop", "tablet", "mobile"}
        assert {item["scenarioId"] for item in plan.json()["scenarios"]} >= {
            "chat-core",
            "runtime-center",
            "terminal-shell",
        }
        chatScenario = next(item for item in plan.json()["scenarios"] if item["scenarioId"] == "chat-core")
        assert chatScenario["steps"][0]["assertQaIds"] == ["chat-welcome", "analysis-promise"]

        client.post(
            "/api/ui-qa/sessions/register",
            json={"sessionId": sessionId, "clientName": "visual-browser", "capabilities": []},
        )
        recorded = client.post(
            f"/api/ui-qa/sessions/{sessionId}/visual-audits",
            json={
                "scenarioId": "chat-core",
                "viewportId": "mobile",
                "result": "passed",
                "screenshotCaptured": True,
                "screenshotLabel": "chat-empty-mobile",
                "findings": [],
                "capturedAt": "2026-08-03T00:00:00.000Z",
            },
        )
        assert recorded.status_code == 201
        assert recorded.json()["auditId"]
        assert recorded.json()["recordedAt"]
        state = client.get(f"/api/ui-qa/sessions/{sessionId}").json()
        assert state["visualAuditCount"] == 1
        assert state["visualAudits"][0]["screenshotCaptured"] is True


def testUiQaRejectsUnknownOrUnexplainedFailedVisualAudit():
    sessionId = str(uuid4())
    with TestClient(app) as client:
        client.post(
            "/api/ui-qa/sessions/register",
            json={"sessionId": sessionId, "clientName": "visual-browser", "capabilities": []},
        )
        unknown = client.post(
            f"/api/ui-qa/sessions/{sessionId}/visual-audits",
            json={
                "scenarioId": "invented",
                "viewportId": "desktop",
                "result": "passed",
                "screenshotCaptured": False,
                "findings": [],
                "capturedAt": "2026-08-03T00:00:00.000Z",
            },
        )
        unexplained = client.post(
            f"/api/ui-qa/sessions/{sessionId}/visual-audits",
            json={
                "scenarioId": "chat-core",
                "viewportId": "desktop",
                "result": "failed",
                "screenshotCaptured": True,
                "findings": [],
                "capturedAt": "2026-08-03T00:00:00.000Z",
            },
        )
    assert unknown.status_code == 422
    assert unexplained.status_code == 422


@pytest.mark.parametrize(
    "command",
    [
        {"action": "fill", "targetQaId": "input[name=password]", "value": "secret"},
        {"action": "key", "targetQaId": "chat-input", "key": "F12"},
        {"action": "navigate", "path": "https://example.com"},
        {"action": "navigate", "path": "/chat?token=secret"},
        {"action": "navigate", "path": "/\\example.com"},
        {"action": "snapshot", "targetQaId": "chat-shell"},
    ],
)
def testUiQaRejectsSelectorsUnsafeKeysAndExternalNavigation(command: dict):
    sessionId = str(uuid4())
    with TestClient(app) as client:
        client.post(
            "/api/ui-qa/sessions/register",
            json={"sessionId": sessionId, "clientName": "test-ui", "capabilities": []},
        )
        response = client.post(f"/api/ui-qa/sessions/{sessionId}/commands", json=command)
    assert response.status_code == 422


def testUiQaCanBeDisabledLocally(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DARTLAB_UI_QA", "0")
    with TestClient(app) as client:
        assert client.get("/api/ui-qa/config").json()["enabled"] is False
        response = client.get("/api/ui-qa/sessions")
    assert response.status_code == 403
