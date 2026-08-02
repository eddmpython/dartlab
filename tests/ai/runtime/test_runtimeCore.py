from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from dartlab.ai.runtime.contracts import ProcessSpec, RuntimeDescriptor, RuntimeProbe
from dartlab.ai.runtime.drivers.claudeStreamJson import _claudeToolArgs
from dartlab.ai.runtime.eventBuffer import EventBuffer
from dartlab.ai.runtime.eventProjection import EventProjector
from dartlab.ai.runtime.installManager import buildInstallPlan, executeInstallPlan
from dartlab.ai.runtime.mcpBootstrap import _clineMcpConfigured, buildMcpConnectPlan
from dartlab.ai.runtime.processSupervisor import ProcessSupervisor
from dartlab.ai.runtime.registry import loadRuntimeRegistry
from dartlab.ai.runtime.schema import generateTypeScriptContracts
from dartlab.ai.runtime.sessionStore import SessionStore


def testClaudeRuntimeExposesOnlyToolSearchAndReadOnlyMcp():
    args = _claudeToolArgs()
    assert args[:2] == ("--tools", "ToolSearch")
    assert "--disable-slash-commands" in args
    allowed = args[args.index("--allowedTools") + 1]
    assert allowed.startswith("ToolSearch,")
    assert "mcp__dartlab__ReadSkill" in allowed
    assert "mcp__dartlab__EngineCall" in allowed
    assert "Bash" not in allowed
    assert "PowerShell" not in allowed


def testRuntimeRegistryHasThreeNativeDrivers():
    registry = loadRuntimeRegistry()
    assert set(registry) == {"codex", "claude", "cline"}
    assert {item.driver for item in registry.values()} == {"codexAppServer", "claudeStreamJson", "acp"}
    assert all("model" not in item.toDict() for item in registry.values())


def testEventProjectionKeepsStableSemanticKinds():
    projector = EventProjector("codex", "session-1")
    first = projector.project({"method": "item/agentMessage/delta", "params": {"delta": "안녕"}}, turnId="turn-1")[0]
    second = projector.project({"method": "turn/completed", "params": {}}, turnId="turn-1")[0]
    assert (first.kind, first.payload["text"], first.sequence) == ("messageDelta", "안녕", 1)
    assert (second.kind, second.sequence) == ("turnCompleted", 2)


def testNativeSessionInitDoesNotDuplicateEngineOwnedSessionEvent():
    codex = EventProjector("codex", "session-1")
    claude = EventProjector("claude", "session-2")

    codexEvent = codex.project({"method": "thread/started", "params": {}}, turnId="turn-1")[0]
    claudeEvent = claude.project(
        {"type": "system", "subtype": "init", "session_id": "native-2"},
        turnId="turn-2",
    )[0]

    assert codexEvent.kind == "native"
    assert claudeEvent.kind == "native"


def testEventBufferEnforcesCountAndReplayBoundary():
    projector = EventProjector("cline", "session-1")
    buffer = EventBuffer(maxEvents=2, maxBytes=100_000)
    for index in range(3):
        buffer.append(projector.event("native", turnId="turn", payload={"index": index}))
    assert [event.sequence for event in buffer.after(0)] == [2, 3]
    assert [event.sequence for event in buffer.after(2)] == [3]


def testProcessSupervisorUsesNdjsonWithoutShell(tmp_path):
    script = tmp_path / "echoRuntime.py"
    script.write_text(
        "import json, sys\nfor line in sys.stdin:\n print(json.dumps(json.loads(line)), flush=True)\n",
        encoding="utf-8",
    )
    supervisor = ProcessSupervisor(ProcessSpec((sys.executable, "-u", str(script)), tmp_path))
    supervisor.start()
    try:
        supervisor.sendJson({"hello": "dartlab"})
        assert supervisor.readJson(timeout=5) == {"hello": "dartlab"}
    finally:
        supervisor.stop()


def testInstallPlanRequiresExactDigest():
    plan = buildInstallPlan("cline")
    with pytest.raises(PermissionError):
        executeInstallPlan(plan, approvedDigest="wrong")


def testClineMcpPlanUsesOfficialNonInteractiveInstaller(monkeypatch):
    monkeypatch.setattr("dartlab.ai.runtime.mcpBootstrap.discoverExecutable", lambda _descriptor: "cline")

    plan = buildMcpConnectPlan("cline")

    assert plan.argv[:7] == ("cline", "mcp", "install", "dartlab", "--yes", "--json", "--")
    assert plan.argv[-2:] == ("-m", "dartlab.mcp")


def testClineMcpProbeUsesOfficialSettingsFile(tmp_path):
    settings = tmp_path / "data" / "settings"
    settings.mkdir(parents=True)
    (settings / "cline_mcp_settings.json").write_text(
        json.dumps({"mcpServers": {"dartlab": {"transport": {"type": "stdio"}}}}),
        encoding="utf-8",
    )

    assert _clineMcpConfigured(tmp_path)
    assert not _clineMcpConfigured(tmp_path / "missing")


def testSessionStorePersistsOnlySessionMapping(tmp_path):
    from dartlab.ai.runtime.contracts import RuntimeSession

    store = SessionStore(tmp_path / "sessions.sqlite3")
    value = RuntimeSession("s", "codex", "native", str(tmp_path))
    store.save(value)
    assert store.get("s") == value
    assert store.list(limit=1) == [value]


def testTypeScriptContractIsGeneratedFromPythonSource():
    path = Path("ui/apps/local/src/lib/generated/agentRuntime.ts")
    assert path.read_text(encoding="utf-8") == generateTypeScriptContracts()


def testEveryRuntimeManifestIsJsonSerializable():
    encoded = json.dumps([item.toDict() for item in loadRuntimeRegistry().values()])
    assert "codexAppServer" in encoded
