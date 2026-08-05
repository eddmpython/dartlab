from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from dartlab.ai.runtime.analysisCapsule import buildAnalysisCapsule, buildTurnQuestion
from dartlab.ai.runtime.contracts import ProcessSpec, RuntimeDescriptor, RuntimeProbe, nowIso
from dartlab.ai.runtime.discovery import probeAllRuntimes, runtimeLoginArgv
from dartlab.ai.runtime.drivers.base import (
    remainingTurnSeconds,
    runtimeExecutableArgv,
    runtimeLaunchArgv,
    runtimeTurnTimeoutSeconds,
)
from dartlab.ai.runtime.drivers.claudeStreamJson import _claudeToolArgs
from dartlab.ai.runtime.drivers.codexAppServer import CodexAppServerDriver, codexReasoningEffort
from dartlab.ai.runtime.eventBuffer import EventBuffer
from dartlab.ai.runtime.eventProjection import EventProjector
from dartlab.ai.runtime.evidenceStore import EvidenceStore
from dartlab.ai.runtime.installManager import buildInstallPlan, executeInstallPlan
from dartlab.ai.runtime.mcpBootstrap import (
    McpConnectPlan,
    _claudeProjectMcpConfigured,
    _clineMcpConfigured,
    buildMcpConnectPlan,
    claudeReadOnlyMcpTools,
    embeddedMcpServerSpec,
    executeMcpConnectPlan,
)
from dartlab.ai.runtime.processSupervisor import ProcessSupervisor
from dartlab.ai.runtime.registry import loadRuntimeRegistry, manifestRoot
from dartlab.ai.runtime.schema import generateTypeScriptContracts, runtimeJsonSchemas
from dartlab.ai.runtime.sessionStore import SessionStore


def testClaudeRuntimeAllowsReadOnlyMcpAndBlocksBuiltinExecution():
    """허용은 --allowedTools(read-only MCP), 차단은 --disallowedTools(내장 실행)로 나눈다.

    실측(2026-08-04): dontAsk 는 "허용 외 거절" 이 아니라 "묻지 않고 실행" 이라
    allowedTools 만으로는 Bash·PowerShell 이 프롬프트 없이 실행됐다(주입 마커 출력 재현).
    차단은 disallowedTools 가 소유한다. ToolSearch·MCP 리소스 도구는 dartlab MCP 도구가
    deferred 라 발견 관문이라서 차단하지 않는다(막으면 분석 자체가 불가).
    """
    args = _claudeToolArgs()
    assert "--tools" not in args
    assert "--disable-slash-commands" in args
    assert args[args.index("--permission-mode") + 1] == "dontAsk"
    allowed = args[args.index("--allowedTools") + 1]
    assert "mcp__dartlab__ReadSkill" in allowed
    assert "mcp__dartlab__EngineCall" in allowed
    assert "RunPython" not in allowed

    denied = args[args.index("--disallowedTools") + 1].split(",")
    # 로컬 실행·파일 변조·하위 스폰은 전부 차단
    for blocked in ("Bash", "PowerShell", "Read", "Write", "Edit", "Grep", "Task", "Workflow"):
        assert blocked in denied, f"{blocked} 미차단"
    # dartlab 도구 발견 관문은 차단하지 않는다
    assert "ToolSearch" not in denied


def testAgentMcpProfileExcludesMutatingTools(monkeypatch):
    from dartlab.mcp.protocol import mcpAdvertisedToolNames

    monkeypatch.setenv("DARTLAB_MCP_PROFILE", "agent")
    names = set(mcpAdvertisedToolNames())

    assert {"ReadSkill", "ReadCapability", "EngineCall"} <= names
    assert "RunPython" not in names
    assert "SaveArtifact" not in names


def testRuntimeRegistryHasThreeNativeDrivers():
    registry = loadRuntimeRegistry()
    assert set(registry) == {"codex", "claude", "cline"}
    assert {item.driver for item in registry.values()} == {"codexAppServer", "claudeStreamJson", "acp"}
    assert all("model" not in item.toDict() for item in registry.values())
    assert loadRuntimeRegistry()["cline"].launchArgs == ("--acp", "--auto-approve", "false")
    assert loadRuntimeRegistry()["cline"].embeddedGrounding is False
    assert loadRuntimeRegistry()["codex"].embeddedGrounding is True
    assert loadRuntimeRegistry()["codex"].authProbeArgs == ("login", "status")
    assert loadRuntimeRegistry()["claude"].loginArgs == ("auth", "login")


def testRuntimePublicContractHelpersAreDirectlyUsable(monkeypatch):
    timestamp = nowIso()
    assert datetime.fromisoformat(timestamp).utcoffset().total_seconds() == 0

    root = manifestRoot()
    assert root.is_dir()
    assert {path.stem for path in root.glob("*.toml")} == {"codex", "claude", "cline"}

    schemas = runtimeJsonSchemas()
    assert set(schemas) == {"AgentEvent", "RuntimeProbe", "ProductOutcomeReceipt"}
    assert schemas["AgentEvent"]["properties"]["sequence"]["minimum"] == 1

    server = embeddedMcpServerSpec()
    assert server["name"] == "dartlab"
    assert server["args"][-2:] == ["--profile", "agent"]

    tools = claudeReadOnlyMcpTools()
    assert "mcp__dartlab__ReadSkill" in tools
    assert "mcp__dartlab__EngineCall" in tools
    assert "mcp__dartlab__RunPython" not in tools


def testProbeAllRuntimesUsesRegistryOrderAndRefresh(monkeypatch):
    descriptors = {
        runtimeId: RuntimeDescriptor(
            runtimeId,
            runtimeId,
            "fake",
            "ndjson",
            (runtimeId,),
            ("--version",),
            (),
            (),
            "https://example.invalid",
        )
        for runtimeId in ("one", "two")
    }
    calls: list[tuple[str, bool]] = []
    monkeypatch.setattr("dartlab.ai.runtime.discovery.loadRuntimeRegistry", lambda: descriptors)
    monkeypatch.setattr(
        "dartlab.ai.runtime.discovery.probeRuntime",
        lambda descriptor, refresh=False: (
            calls.append((descriptor.runtimeId, refresh))
            or RuntimeProbe(descriptor.runtimeId, "ready", f"/{descriptor.runtimeId}")
        ),
    )

    probes = probeAllRuntimes(refresh=True)

    assert [probe.runtimeId for probe in probes] == ["one", "two"]
    assert calls == [("one", True), ("two", True)]


def testRuntimeLoginArgvUsesOfficialManifestCommand(monkeypatch):
    descriptor = RuntimeDescriptor(
        "fake",
        "Fake",
        "fake",
        "ndjson",
        ("fake",),
        ("--version",),
        (),
        (),
        "https://example.invalid",
        loginArgs=("auth", "login"),
    )
    monkeypatch.setattr("dartlab.ai.runtime.discovery.loadRuntimeRegistry", lambda: {"fake": descriptor})
    monkeypatch.setattr("dartlab.ai.runtime.discovery.discoverExecutable", lambda _descriptor: "/bin/fake")
    monkeypatch.setattr(
        "dartlab.ai.runtime.drivers.base.runtimeExecutableArgv",
        lambda _descriptor, executable: (executable,),
    )

    assert runtimeLoginArgv("fake") == ("/bin/fake", "auth", "login")


def testExecuteMcpConnectPlanRequiresExactPlanAndRunsArgv(monkeypatch):
    plan = McpConnectPlan("fake", ("fake", "mcp", "add"), "digest")
    completed = subprocess.CompletedProcess(list(plan.argv), 0, "ok", "")
    calls: list[dict] = []
    monkeypatch.setattr("dartlab.ai.runtime.mcpBootstrap.buildMcpConnectPlan", lambda runtimeId: plan)

    def fakeRun(argv, **kwargs):
        calls.append({"argv": argv, **kwargs})
        return completed

    monkeypatch.setattr("dartlab.ai.runtime.mcpBootstrap.subprocess.run", fakeRun)

    result = executeMcpConnectPlan(plan, approvedDigest="digest")

    assert result is completed
    assert calls[0]["argv"] == list(plan.argv)
    assert calls[0]["shell"] is False
    assert calls[0]["check"] is True


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
    assert runtimeTurnTimeoutSeconds() == 600


def testCodexReasoningEffortBalancesLatencyAndAllowsExplicitOverride(monkeypatch):
    monkeypatch.delenv("DARTLAB_CODEX_REASONING_EFFORT", raising=False)
    assert codexReasoningEffort() == "high"
    monkeypatch.setenv("DARTLAB_CODEX_REASONING_EFFORT", "xhigh")
    assert codexReasoningEffort() == "xhigh"
    monkeypatch.setenv("DARTLAB_CODEX_REASONING_EFFORT", "invalid")
    assert codexReasoningEffort() == "high"
    monkeypatch.setenv("DARTLAB_AGENT_TURN_TIMEOUT_SECONDS", "nan")
    assert runtimeTurnTimeoutSeconds() == 600


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
    assert "사용자가 실제로 판단하려는 결정" in capsule
    assert "가설을 지지하는 자료만 모으지 말고" in capsule
    assert "관측 사실과 해석을 구분" in capsule
    assert "실제 사용하지 않은 valueRef나 dateRef" in capsule


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


def testTurnQuestionIncludesDeterministicClaimCellContract():
    question = buildTurnQuestion("삼성전자 005930 최근 5년 매출과 영업이익 추이")

    assert '"claimCellContract"' in question
    assert '"metrics":["revenue","operating_profit"]' in question
    assert '"requiredCells":10' in question
    assert '"targetCount":1' in question
    assert '"unit":"fiscal_year"' in question
    assert '"analysisConversation"' in question
    assert '"mode":"performanceTrend"' in question


def testRepairTurnReusesOriginalQuestionContract():
    question = buildTurnQuestion(
        "답변 품질을 다시 교정하라",
        contractQuestion="삼성전자 005930 최근 5년 매출과 영업이익 추이",
    )

    assert '"period":"recent:5Y"' in question
    assert '"requiredCells":10' in question
    assert question.endswith("[사용자 질문]\n답변 품질을 다시 교정하라")


def testAnalysisCapsuleExplainsCoverageAsCompletionContract(tmp_path):
    capsule = buildAnalysisCapsule(cwd=tmp_path, mcpConnected=True)

    assert "informationCoverage" in capsule
    assert "강제 실행 순서가 아니라" in capsule
    assert "requiredEvidence가 빠지면" in capsule
    assert "claimCellContract" in capsule
    assert "requiredCells를 완료 조건" in capsule


def testAnalysisCapsuleUsesInvestmentDecisionProductBeforeGapFilling(tmp_path):
    capsule = buildAnalysisCapsule(cwd=tmp_path, mcpConnected=True)

    assert "Company.reportModel을 perspective=investment로 먼저" in capsule
    assert "investmentDecision 9차원" in capsule
    assert "usable, partial, blocked, notObserved" in capsule
    assert "개인화 매수·매도 지시" in capsule


def testTurnQuestionCarriesInvestmentAcceptanceContract():
    question = buildTurnQuestion(
        "삼성전자 005930 지금 투자할 만한지 종합 분석해줘",
        {"stockCode": "005930", "reportMode": "investment"},
    )

    assert '"reportMode":"investment"' in question
    assert '"investment.decision_memo"' in question
    assert '"minUsableDimensions":7' in question
    assert '"monitoringTripwires"' in question


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
    assert turnParams["effort"] == "high"
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

    with pytest.raises(TimeoutError, match="600초 제한"):
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


def testClaudeProjectMcpRequiresAgentProfile(tmp_path):
    (tmp_path / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "dartlab": {
                        "command": "uv",
                        "args": ["run", "python", "-m", "dartlab.mcp", "--profile", "agent"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    assert _claudeProjectMcpConfigured(tmp_path) is True
    assert _claudeProjectMcpConfigured(tmp_path / "missing") is False


def testSessionStorePersistsOnlySessionMapping(tmp_path):
    from dartlab.ai.runtime.contracts import RuntimeSession

    store = SessionStore(tmp_path / "sessions.sqlite3")
    value = RuntimeSession("s", "codex", "native", str(tmp_path))
    store.save(value)
    assert store.get("s") == value
    assert store.list(limit=1) == [value]


def testSessionStorePersistsServerOwnedDefaultRuntime(tmp_path):
    store = SessionStore(tmp_path / "sessions.sqlite3")

    assert store.getPreference("defaultRuntimeId") is None
    store.setPreference("defaultRuntimeId", "codex")

    assert store.getPreference("defaultRuntimeId") == "codex"


def testRuntimeAuthProbeDoesNotExposeAccountOutput(monkeypatch):
    from subprocess import CompletedProcess

    from dartlab.ai.runtime.discovery import probeRuntimeAuth

    descriptor = loadRuntimeRegistry()["claude"]
    monkeypatch.setattr(
        "dartlab.ai.runtime.discovery.subprocess.run",
        lambda *args, **kwargs: CompletedProcess(args[0], 0, '{"loggedIn":true,"email":"private@example.com"}', ""),
    )

    result = probeRuntimeAuth(descriptor, executable="claude")

    assert result["authenticated"] is True
    assert "email" not in result
    assert "detail" not in result


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
    paths = (
        Path("ui/apps/local/src/lib/generated/agentRuntime.ts"),
        Path("ui/packages/contracts/src/generated/agentRuntime.ts"),
    )
    assert all(path.read_text(encoding="utf-8") == generateTypeScriptContracts() for path in paths)


def testEveryRuntimeManifestIsJsonSerializable():
    encoded = json.dumps([item.toDict() for item in loadRuntimeRegistry().values()])
    assert "codexAppServer" in encoded


def testMcpProbeTimeoutDegradesInsteadOfCrashingStatus(monkeypatch: pytest.MonkeyPatch):
    """probe subprocess 실패가 상태 화면을 500 으로 죽이지 않는다.

    실측 회귀(2026-08-04): `claude mcp get dartlab` 이 상한을 넘기자 TimeoutExpired 가
    /api/status 까지 올라가 Runtime Center 전체가 무너졌다. 형제 probe(discovery)는
    전부 OSError·SubprocessError 를 typed 상태로 바꾸는데 여기만 맨몸이었다.
    """
    import subprocess

    from dartlab.ai.runtime import mcpBootstrap

    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["claude", "mcp", "get", "dartlab"], timeout=20)

    monkeypatch.setattr(mcpBootstrap.subprocess, "run", _timeout)
    monkeypatch.setattr(mcpBootstrap, "discoverExecutable", lambda descriptor: "claude.exe")
    with mcpBootstrap._MCP_CACHE_LOCK:
        mcpBootstrap._MCP_CACHE.clear()

    result = mcpBootstrap.probeMcpConnection("claude", refresh=True)

    assert result["connected"] is False
    assert "probe_unavailable" in str(result["detail"])
    # 실패도 캐시해 매 요청마다 느린 probe 를 재시도하지 않는다
    assert "claude" in mcpBootstrap._MCP_CACHE
