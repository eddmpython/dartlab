"""통합 runtime setup API가 관리자 경계와 coordinator를 공유하는지 검증한다."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dartlab.server.security import _routeScope

pytestmark = pytest.mark.unit


def test_setup_plan_and_apply_are_admin_mutations() -> None:
    assert _routeScope("POST", "/api/agent/runtimes/setup/plan") == "admin"
    assert _routeScope("POST", "/api/agent/runtimes/setup/apply") == "admin"


def test_setup_plan_returns_one_operation(monkeypatch) -> None:
    from dartlab.server.api import runtime

    plan = SimpleNamespace(toDict=lambda: {"runtimeId": "codex", "changes": ["install", "login", "mcp"]})
    monkeypatch.setattr(runtime, "previewRuntimeSetup", lambda runtimeId: plan)

    result = runtime.planRuntimeSetup(runtime.RuntimeSetupRequest(runtimeId="codex"))

    assert result == {"runtimeId": "codex", "changes": ["install", "login", "mcp"]}


@pytest.mark.asyncio
async def test_setup_apply_uses_visible_official_login_and_returns_investment_readiness(monkeypatch) -> None:
    from dartlab.server.api import runtime

    calls = []
    receipt = SimpleNamespace(toDict=lambda: {"state": "ready", "investmentReady": True})

    def prepare(runtimeId, *, approved, loginExecutor):
        calls.append((runtimeId, approved, loginExecutor))
        return receipt

    monkeypatch.setattr(runtime, "prepareRuntime", prepare)
    result = await runtime.applyRuntimeSetup(runtime.RuntimeSetupRequest(runtimeId="codex", approved=True))

    assert result["investmentReady"] is True
    assert calls == [("codex", True, runtime.executeVisibleLogin)]


@pytest.mark.asyncio
async def test_setup_apply_rejects_unapproved_request() -> None:
    from fastapi import HTTPException

    from dartlab.server.api import runtime

    with pytest.raises(HTTPException, match="명시적 승인"):
        await runtime.applyRuntimeSetup(runtime.RuntimeSetupRequest(runtimeId="codex", approved=False))
