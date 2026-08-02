from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from dartlab.ai.runtime.analysisCapsule import buildAnalysisCapsule, buildTurnQuestion
from dartlab.ai.runtime.contracts import ProcessSpec, RuntimeDescriptor, RuntimeProbe
from dartlab.ai.runtime.drivers.base import (
    remainingTurnSeconds,
    runtimeExecutableArgv,
    runtimeLaunchArgv,
    runtimeTurnTimeoutSeconds,
)
from dartlab.ai.runtime.drivers.claudeStreamJson import _claudeToolArgs
from dartlab.ai.runtime.drivers.codexAppServer import CodexAppServerDriver
from dartlab.ai.runtime.eventBuffer import EventBuffer
from dartlab.ai.runtime.eventProjection import EventProjector
from dartlab.ai.runtime.evidenceStore import EvidenceStore
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
    assert loadRuntimeRegistry()["cline"].launchArgs == ("--acp", "--auto-approve", "false")
    assert loadRuntimeRegistry()["cline"].embeddedGrounding is False
    assert loadRuntimeRegistry()["codex"].embeddedGrounding is True


def testRuntimeExecutablePrefixDoesNotIncludeDefaultLaunchArgs(monkeypatch):
    descriptor = RuntimeDescriptor(
        "fake", "Fake", "fake", "jsonrpc", ("fake",), (), ("app-server",), (), "https://example.invalid"
    )
    monkeypatch.setattr("dartlab.ai.runtime.drivers.base.os.name", "posix")

    assert runtimeExecutableArgv(descriptor, "/bin/fake") == ("/bin/fake",)
    assert runtimeLaunchArgv(descriptor, "/bin/fake") == ("/bin/fake", "app-server")


def testRuntimeTurnTimeoutIsBoundedAndInvalidValuesUseDefault(monkeypatch):
    monkeypatch.setenv("DARTLAB_AGENT_TURN_TIMEOUT_SECONDS", "5")
    assert runtimeTurnTimeoutSeconds() == 30
    monkeypatch.setenv("DARTLAB_AGENT_TURN_TIMEOUT_SECONDS", "1200")
    assert runtimeTurnTimeoutSeconds() == 900
    monkeypatch.setenv("DARTLAB_AGENT_TURN_TIMEOUT_SECONDS", "invalid")
    assert runtimeTurnTimeoutSeconds() == 300
    monkeypatch.setenv("DARTLAB_AGENT_TURN_TIMEOUT_SECONDS", "nan")
    assert runtimeTurnTimeoutSeconds() == 300


def testExpiredTurnDeadlineFailsClosed():
    with pytest.raises(TimeoutError, match="300초 제한"):
        remainingTurnSeconds(0, 300)


def testAnalysisCapsuleHasFiniteToolRoutingContract(tmp_path):
    capsule = buildAnalysisCapsule(cwd=tmp_path, mcpConnected=True)

    assert "턴당 정확히 한 번" in capsule
    assert "전체 도구 호출 8회 이내" in capsule
    assert "DartLab 외 다른 MCP 서버의 도구는 사용하지 마라" in capsule
    assert "필요한 근거가 확보되면 더 탐색하지 말고 즉시 답변" in capsule
    assert "start.dartlabSkillOs" in capsule
    assert "period와 freq를 누락하지 말고" in capsule


def testTurnQuestionPromotesExplicitPeriodToStructuredContext():
    question = buildTurnQuestion(
        "삼성전자 2024년 연간 매출액은?",
        {"stockCode": "005930"},
    )

    assert '"period":"2024"' in question
    assert '"stockCode":"005930"' in question
    assert '"informationCoverage"' in question
    assert '"Company.panel"' in question


def testTurnQuestionIncludesCoverageWithoutScreenContext():
    question = buildTurnQuestion("ROE가 높은 종목을 스크리닝해줘")

    assert '"informationCoverage"' in question
    assert '"scan"' in question


def testAnalysisCapsuleExplainsCoverageAsCompletionContract(tmp_path):
    capsule = buildAnalysisCapsule(cwd=tmp_path, mcpConnected=True)

    assert "informationCoverage" in capsule
    assert "강제 실행 순서가 아니라" in capsule
    assert "requiredEvidence가 빠지면" in capsule


def testCodexUsesThreadInstructionsAndReadOnlyTurn(monkeypatch, tmp_path):
    calls: list[tuple[str, dict]] = []

    class FakeSupervisor:
        def __init__(self, _spec):
            self.stopped = False

        def start(self):
            return None

        def stop(self):
            self.stopped = True

    class FakeChannel:
        def __init__(self, _supervisor):
            self.messages = [{"method": "turn/completed", "params": {"turn": {"status": "completed"}}}]

        def request(self, method, params, *, timeout):
            calls.append((method, params))
            if method == "thread/start":
                return {"thread": {"id": "thread-1"}}
            if method == "turn/start":
                return {"turn": {"id": "turn-1"}}
            return {}

        def notify(self, method, params):
            calls.append((method, params))

        def nextMessage(self, *, timeout):
            return self.messages.pop(0)

    monkeypatch.setattr("dartlab.ai.runtime.drivers.codexAppServer.ProcessSupervisor", FakeSupervisor)
    monkeypatch.setattr("dartlab.ai.runtime.drivers.codexAppServer.JsonRpcChannel", FakeChannel)
    descriptor = RuntimeDescriptor(
        "codex",
        "Codex",
        "codexAppServer",
        "jsonrpc-ndjson",
        ("codex",),
        ("--version",),
        ("app-server",),
        (),
        "https://example.invalid",
    )
    driver = CodexAppServerDriver()
    handle = driver.open(descriptor, "codex", "session-1", tmp_path, instructions="DartLab capsule")

    list(driver.streamTurn(handle, "질문", instructions="DartLab capsule"))

    threadParams = next(params for method, params in calls if method == "thread/start")
    turnParams = next(params for method, params in calls if method == "turn/start")
    assert threadParams["developerInstructions"] == "DartLab capsule"
    assert threadParams["sandbox"] == "read-only"
    assert threadParams["approvalPolicy"] == "never"
    assert "developerInstructions" not in turnParams
    assert turnParams["sandboxPolicy"] == {"type": "readOnly", "networkAccess": False}


def testCodexHandshakeFailureStopsChild(monkeypatch, tmp_path):
    holder = {}

    class FakeSupervisor:
        def __init__(self, _spec):
            self.stopped = False
            holder["supervisor"] = self

        def start(self):
            return None

        def stop(self):
            self.stopped = True

    class FailingChannel:
        def __init__(self, _supervisor):
            pass

        def request(self, method, params, *, timeout):
            raise RuntimeError("handshake failed")

    monkeypatch.setattr("dartlab.ai.runtime.drivers.codexAppServer.ProcessSupervisor", FakeSupervisor)
    monkeypatch.setattr("dartlab.ai.runtime.drivers.codexAppServer.JsonRpcChannel", FailingChannel)
    descriptor = RuntimeDescriptor(
        "codex", "Codex", "codexAppServer", "jsonrpc", ("codex",), (), ("app-server",), (), "https://example.invalid"
    )

    with pytest.raises(RuntimeError, match="handshake failed"):
        CodexAppServerDriver().open(descriptor, "codex", "session-1", tmp_path, instructions="capsule")
    assert holder["supervisor"].stopped is True


def testCodexTurnTimeoutInterruptsNativeTurn(monkeypatch, tmp_path):
    interrupted: list[tuple[str, dict]] = []

    class FakeSupervisor:
        def __init__(self, _spec):
            pass

        def start(self):
            return None

        def stop(self):
            return None

    class TimeoutChannel:
        def __init__(self, _supervisor):
            pass

        def request(self, method, params, *, timeout):
            if method == "thread/start":
                return {"thread": {"id": "thread-1"}}
            if method == "turn/start":
                return {"turn": {"id": "turn-1"}}
            return {}

        def notify(self, method, params):
            return None

        def nextMessage(self, *, timeout):
            raise TimeoutError("deadline")

        def startRequest(self, method, params):
            interrupted.append((method, params))
            return 3

    monkeypatch.setattr("dartlab.ai.runtime.drivers.codexAppServer.ProcessSupervisor", FakeSupervisor)
    monkeypatch.setattr("dartlab.ai.runtime.drivers.codexAppServer.JsonRpcChannel", TimeoutChannel)
    descriptor = RuntimeDescriptor(
        "codex", "Codex", "codexAppServer", "jsonrpc", ("codex",), (), ("app-server",), (), "https://example.invalid"
    )
    driver = CodexAppServerDriver()
    handle = driver.open(descriptor, "codex", "session-1", tmp_path, instructions="capsule")

    with pytest.raises(TimeoutError, match="300초 제한"):
        list(driver.streamTurn(handle, "질문", instructions="capsule"))

    assert interrupted == [("turn/interrupt", {"threadId": "thread-1", "turnId": "turn-1"})]
    assert handle.activeTurnId is None


def testCodexConsumerDisconnectInterruptsNativeTurn(monkeypatch, tmp_path):
    interrupted: list[tuple[str, dict]] = []

    class FakeSupervisor:
        def __init__(self, _spec):
            pass

        def start(self):
            return None

        def stop(self):
            return None

    class StreamingChannel:
        def __init__(self, _supervisor):
            pass

        def request(self, method, params, *, timeout):
            if method == "thread/start":
                return {"thread": {"id": "thread-1"}}
            if method == "turn/start":
                return {"turn": {"id": "turn-1"}}
            return {}

        def notify(self, method, params):
            return None

        def nextMessage(self, *, timeout):
            return {
                "method": "item/started",
                "params": {"item": {"id": "tool-1", "type": "mcpToolCall", "name": "ReadSkill"}},
            }

        def startRequest(self, method, params):
            interrupted.append((method, params))
            return 4

    monkeypatch.setattr("dartlab.ai.runtime.drivers.codexAppServer.ProcessSupervisor", FakeSupervisor)
    monkeypatch.setattr("dartlab.ai.runtime.drivers.codexAppServer.JsonRpcChannel", StreamingChannel)
    descriptor = RuntimeDescriptor(
        "codex",
        "Codex",
        "codexAppServer",
        "jsonrpc",
        ("codex",),
        (),
        ("app-server",),
        (),
        "https://example.invalid",
    )
    driver = CodexAppServerDriver()
    handle = driver.open(descriptor, "codex", "session-1", tmp_path, instructions="capsule")
    stream = driver.streamTurn(handle, "질문", instructions="capsule")

    assert next(stream).kind == "toolStarted"
    stream.close()

    assert interrupted == [("turn/interrupt", {"threadId": "thread-1", "turnId": "turn-1"})]
    assert handle.activeTurnId is None


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


def testJsonRpcStartRequestUsesAnIdWithoutWaiting(tmp_path):
    from dartlab.ai.runtime.processSupervisor import JsonRpcChannel

    script = tmp_path / "echoRequest.py"
    script.write_text(
        "import json, sys\nfor line in sys.stdin:\n print(json.dumps(json.loads(line)), flush=True)\n",
        encoding="utf-8",
    )
    supervisor = ProcessSupervisor(ProcessSpec((sys.executable, "-u", str(script)), tmp_path))
    supervisor.start()
    try:
        channel = JsonRpcChannel(supervisor)
        requestId = channel.startRequest("turn/interrupt", {"turnId": "turn-1"})
        message = supervisor.readJson(timeout=5)
        assert message == {
            "jsonrpc": "2.0",
            "id": requestId,
            "method": "turn/interrupt",
            "params": {"turnId": "turn-1"},
        }
    finally:
        supervisor.stop()


def testInstallPlanRequiresExactDigest():
    plan = buildInstallPlan("cline")
    with pytest.raises(PermissionError):
        executeInstallPlan(plan, approvedDigest="wrong")


def testClineMcpPlanFailsClosedWhileAcpDoesNotExposeEmbeddedTools(monkeypatch):
    monkeypatch.setattr("dartlab.ai.runtime.mcpBootstrap.discoverExecutable", lambda _descriptor: "cline")

    with pytest.raises(ValueError, match="MCP 도구를 런타임 세션에 노출하지 않습니다"):
        buildMcpConnectPlan("cline")


def testCodexMcpPlanUsesExecutablePrefixWithoutAppServer(monkeypatch):
    monkeypatch.setattr("dartlab.ai.runtime.mcpBootstrap.discoverExecutable", lambda _descriptor: "codex")
    monkeypatch.setattr(
        "dartlab.ai.runtime.mcpBootstrap.runtimeExecutableArgv",
        lambda _descriptor, _executable: ("native-codex",),
    )

    plan = buildMcpConnectPlan("codex")

    assert plan.argv[:5] == ("native-codex", "mcp", "add", "dartlab", "--")
    assert "app-server" not in plan.argv


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


def testEvidenceStorePersistsBoundedExactPayloadAndRejectsOversize(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite3")
    detail = {"id": "table:bounded", "kind": "tableRef", "payload": {"excerpt": "x" * 20_000}}

    store.save("outcome", detail)

    assert store.get("outcome", "table:bounded") == detail
    with pytest.raises(ValueError, match="64 KiB"):
        store.save(
            "outcome",
            {"id": "table:oversize", "kind": "tableRef", "payload": {"excerpt": "x" * 70_000}},
        )


def testTypeScriptContractIsGeneratedFromPythonSource():
    path = Path("ui/apps/local/src/lib/generated/agentRuntime.ts")
    assert path.read_text(encoding="utf-8") == generateTypeScriptContracts()


def testEveryRuntimeManifestIsJsonSerializable():
    encoded = json.dumps([item.toDict() for item in loadRuntimeRegistry().values()])
    assert "codexAppServer" in encoded
