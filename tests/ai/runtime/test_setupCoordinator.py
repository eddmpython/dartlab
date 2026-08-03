"""agent setup coordinator의 단일 승인·재개·멱등 계약."""

from __future__ import annotations

import subprocess

import pytest

from dartlab.ai.runtime.installManager import InstallPlan
from dartlab.ai.runtime.mcpBootstrap import McpConnectPlan
from dartlab.ai.runtime.setupCoordinator import prepareRuntime, previewRuntimeSetup

pytestmark = pytest.mark.unit


class _FakeEngine:
    def __init__(self, *, installed: bool = False, authenticated: bool = False, connected: bool = False) -> None:
        self.installed = installed
        self.authenticated = authenticated
        self.connected = connected
        self.default: str | None = None

    def status(self, *, refresh: bool = False) -> dict:
        del refresh
        ready = self.installed and self.authenticated and self.connected
        return {
            "defaultRuntimeId": self.default,
            "runtimes": [
                {
                    "runtimeId": "codex",
                    "displayName": "Codex CLI",
                    "state": "ready" if self.installed else "missing",
                    "embeddedGrounding": True,
                    "auth": {"state": "authenticated" if self.authenticated else "authRequired"},
                    "mcp": {"connected": self.connected},
                    "groundedReady": ready,
                },
                {
                    "runtimeId": "cline",
                    "displayName": "Cline",
                    "state": "ready",
                    "embeddedGrounding": False,
                    "auth": {"state": "unsupported"},
                    "mcp": {"connected": False},
                    "groundedReady": False,
                },
            ],
        }

    def setDefaultRuntime(self, runtimeId: str) -> str:
        self.default = runtimeId
        return runtimeId


def _patchSetup(monkeypatch, engine: _FakeEngine, calls: list[str]) -> None:
    import dartlab.ai.runtime.setupCoordinator as setup

    installPlan = InstallPlan("codex", ("npm", "install", "-g", "pkg@1"), "https://official", "install")
    mcpPlan = McpConnectPlan("codex", ("codex", "mcp", "add", "dartlab"), "mcp")
    monkeypatch.setattr(setup, "buildInstallPlan", lambda _runtime: installPlan)
    monkeypatch.setattr(setup, "buildMcpConnectPlan", lambda _runtime: mcpPlan)
    monkeypatch.setattr(setup, "_checkInstallPrerequisite", lambda _plan: None)
    monkeypatch.setattr(
        setup,
        "investmentSemanticReadiness",
        lambda: {
            "ready": True,
            "checks": {
                "readSkill": True,
                "engineCall": True,
                "investmentContract": True,
                "reportModel": True,
            },
        },
    )

    def install(_plan, *, approvedDigest):
        assert approvedDigest == "install"
        calls.append("install")
        engine.installed = True
        return subprocess.CompletedProcess([], 0)

    def login(_runtime):
        calls.append("login")
        engine.authenticated = True
        return subprocess.CompletedProcess([], 0)

    def connect(_plan, *, approvedDigest):
        assert approvedDigest == "mcp"
        calls.append("connect")
        engine.connected = True
        return subprocess.CompletedProcess([], 0)

    monkeypatch.setattr(setup, "executeInstallPlan", install)
    monkeypatch.setattr(setup, "executeInteractiveLogin", login)
    monkeypatch.setattr(setup, "executeMcpConnectPlan", connect)


def test_setup_finishes_in_one_approval_and_is_idempotent(monkeypatch) -> None:
    engine = _FakeEngine()
    calls: list[str] = []
    _patchSetup(monkeypatch, engine, calls)

    first = prepareRuntime(approved=True, engine=engine)
    second = prepareRuntime(approved=True, engine=engine)

    assert first.state == "ready" and first.investmentReady is True
    assert first.approvalCount == 1
    assert second.mutationCount == 0
    assert second.approvalCount == 0
    assert calls == ["install", "login", "connect"]


def test_setup_reuses_installed_runtime_and_runs_only_missing_steps(monkeypatch) -> None:
    engine = _FakeEngine(installed=True, authenticated=True, connected=False)
    calls: list[str] = []
    _patchSetup(monkeypatch, engine, calls)

    result = prepareRuntime("codex", approved=True, engine=engine)

    assert result.investmentReady is True
    assert calls == ["connect"]
    assert any(step.key == "install" and step.status == "skipped" for step in result.steps)
    assert any(step.key == "login" and step.status == "skipped" for step in result.steps)


def test_setup_does_not_offer_ungrounded_runtime(monkeypatch) -> None:
    engine = _FakeEngine()
    calls: list[str] = []
    _patchSetup(monkeypatch, engine, calls)

    with pytest.raises(ValueError, match="자동 setup 대상이 아닙니다"):
        previewRuntimeSetup("cline", engine=engine)


def test_setup_plan_includes_node_prerequisite_in_same_approval(monkeypatch) -> None:
    import dartlab.ai.runtime.setupCoordinator as setup

    engine = _FakeEngine()
    calls: list[str] = []
    _patchSetup(monkeypatch, engine, calls)
    monkeypatch.setattr(
        setup.shutil,
        "which",
        lambda executable: "C:\\Windows\\winget.exe" if executable == "winget" else None,
    )

    plan = previewRuntimeSetup("codex", engine=engine)

    assert plan.approvalRequired is True
    assert plan.prerequisitePlan is not None
    assert plan.prerequisitePlan.key == "nodejs"
    assert "Node.js LTS 자동 설치" in plan.changes
    assert plan.toDict()["prerequisitePlan"]["argv"][0] == "winget"
