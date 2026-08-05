from __future__ import annotations

import json
import subprocess
import sys
import time
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

    # 반환은 레지스트리 순서를 유지한다(화면 카드 순서가 실행 순서에 흔들리면 안 된다).
    assert [probe.runtimeId for probe in probes] == ["one", "two"]
    # probe 는 병렬 실행이라 호출 도착 순서는 보장하지 않는다. 계약은 "전부 1회씩, 요청한
    # refresh 로" 다. 순서를 못박으면 스케줄링에 따라 깨지는 flaky 가 된다.
    assert sorted(calls) == [("one", True), ("two", True)]


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


def testRuntimeAuthProbeUsesTtlCacheLikeSiblingProbes(monkeypatch: pytest.MonkeyPatch):
    """인증 probe 도 형제 probe 와 같은 TTL 캐시를 쓴다.

    실측 회귀(2026-08-04): 버전·MCP probe 는 캐시가 있는데 인증만 없어서 상태 조회마다
    CLI 를 재실행했다(캐시 경로 상태 API 1.01초). 인증 상태는 사용자가 CLI 에서
    로그인할 때만 바뀌므로 매번 부를 이유가 없다.
    """
    from dartlab.ai.runtime import discovery

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
        authProbeArgs=("login", "status"),
        authSuccessPattern="logged in",
    )
    runs: list[list[str]] = []

    def fakeRun(argv, **kwargs):
        runs.append(list(argv))
        return subprocess.CompletedProcess(list(argv), 0, "logged in", "")

    monkeypatch.setattr(discovery.subprocess, "run", fakeRun)
    monkeypatch.setattr(discovery, "discoverExecutable", lambda _descriptor: "/bin/fake")
    with discovery._AUTH_CACHE_LOCK:
        discovery._AUTH_CACHE.clear()

    first = discovery.probeRuntimeAuth(descriptor, refresh=True)
    second = discovery.probeRuntimeAuth(descriptor)

    assert first["state"] == "authenticated"
    assert second == first
    assert len(runs) == 1, "두 번째 조회는 캐시가 답해야 한다"

    # refresh 는 캐시를 무시하고 다시 확인한다
    discovery.probeRuntimeAuth(descriptor, refresh=True)
    assert len(runs) == 2


def testProbeCacheServesLastMeasurementAfterTtlExpiryInsteadOfDroppingIt():
    """TTL 이 지나도 마지막 실측값을 버리지 않는다.

    실측 회귀(2026-08-05): 상태 조회 1 회가 12~15 초인데 TTL 이 15 초였다. 만료 즉시
    폐기하는 캐시는 채우는 데 TTL 보다 오래 걸리면 사실상 늘 비어 있다. 사람 속도로
    화면을 다시 열면 매번 전량 재측정을 기다렸다(15.5초 / 7.5초 / 12.8초).
    """
    from dartlab.ai.runtime.probeCache import SwrCache

    cache = SwrCache(ttlSeconds=0.01)
    cache.put("claude", {"connected": True})
    fresh = cache.peek("claude")
    assert fresh is not None and fresh.fresh is True

    time.sleep(0.05)
    stale = cache.peek("claude")

    assert stale is not None, "만료가 값을 지우면 안 된다"
    assert stale.fresh is False, "만료된 값은 stale 로 표시해야 한다"
    assert stale.value == {"connected": True}
    assert cache.get("claude") is None, "fresh 전용 조회는 만료를 감춰서는 안 된다"
    assert "claude" in cache


def testNonBlockingProbeReportsUnknownAndSchedulesMeasurementInsteadOfWaiting():
    """표시 경로는 CLI 실행을 기다리지 않고, 모르는 것을 안다고 말하지도 않는다."""
    from dartlab.ai.runtime import discovery
    from dartlab.ai.runtime.probeCache import backgroundRefresher

    descriptor = RuntimeDescriptor(
        "swrfake",
        "Fake",
        "fake",
        "ndjson",
        ("swrfake-not-on-path",),
        ("--version",),
        (),
        (),
        "https://example.invalid",
    )
    discovery._PROBE_CACHE.clear("swrfake")

    probe = discovery.probeRuntime(descriptor, blocking=False)

    assert probe.state == "unknown", "측정 전에는 ready 도 missing 도 단정하지 않는다"
    assert probe.executable is None, "PATH 발견은 CLI 를 띄우지 않는 즉시 판정이라 그대로 반영한다"
    assert backgroundRefresher().wait(10.0), "예약한 실측이 끝나야 한다"
    assert discovery.probeRuntime(descriptor, blocking=False).state == "missing"


def testNonBlockingStatusAnswersWithoutRunningAnyCliAndNeverClaimsUnknownIsReady(monkeypatch):
    """비차단 상태 조회는 CLI 를 한 번도 띄우지 않고 준비 완료를 주장하지 않는다."""
    from dartlab.ai.runtime import discovery, mcpBootstrap
    from dartlab.ai.runtime import readiness as engineModule
    from dartlab.ai.runtime.engine import AgentRuntimeEngine
    from dartlab.ai.runtime.sessionManager import SessionManager

    def _forbidden(*args, **kwargs):
        raise AssertionError("비차단 경로에서 CLI 를 실행하면 안 된다")

    discovery._PROBE_CACHE.clear()
    discovery._AUTH_CACHE.clear()
    mcpBootstrap._MCP_CACHE.clear()
    engineModule._SEMANTIC_CACHE.clear()
    monkeypatch.setattr(engineModule.backgroundRefresher(), "submit", lambda key, work: True)
    monkeypatch.setattr(discovery.subprocess, "run", _forbidden)
    monkeypatch.setattr(mcpBootstrap.subprocess, "run", _forbidden)

    engine = AgentRuntimeEngine(sessionManager=SessionManager())
    status = engine.status(blocking=False)

    assert status["probing"] is True and status["settled"] is False
    for row in status["runtimes"]:
        assert row["state"] == "unknown"
        assert row["groundedReady"] is False and row["investmentReady"] is False
        assert row["canInstall"] is False, "확인도 안 하고 설치를 권하면 안 된다"
        assert row["pending"] is True
        assert row["probing"]["install"] is True


def testProbeTimeoutIsUndeterminedAndNeverOverwritesAKnownGoodMeasurement(monkeypatch):
    """상한 초과는 "동작 안 함" 이 아니라 "확인 못 함" 이고, 아는 사실을 지우지 않는다.

    실측 회귀(2026-08-05): 상태 조회를 병렬로 펼치자 CPU 경쟁으로 `cline --version` 이
    상한을 넘겼고, 멀쩡히 설치된 CLI 가 unavailable 로 화면에 떴다. 이미 설치된 것을
    다시 설치하라고 권하는 화면은 느린 화면보다 나쁘다.
    """
    from dartlab.ai.runtime import discovery

    descriptor = RuntimeDescriptor(
        "timeoutfake",
        "Fake",
        "fake",
        "ndjson",
        ("fake",),
        ("--version",),
        (),
        (),
        "https://example.invalid",
    )
    monkeypatch.setattr(discovery, "discoverExecutable", lambda _descriptor: "/bin/fake")
    monkeypatch.setattr(
        discovery.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, "9.9.9", ""),
    )
    discovery._PROBE_CACHE.clear("timeoutfake")

    good = discovery.probeRuntime(descriptor, refresh=True)
    assert good.state == "ready" and good.version == "9.9.9"

    def _timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=8)

    monkeypatch.setattr(discovery.subprocess, "run", _timeout)
    afterTimeout = discovery.probeRuntime(descriptor, refresh=True)

    assert afterTimeout.state == "ready", "확인 실패가 아는 사실을 지우면 안 된다"
    assert afterTimeout.version == "9.9.9"

    # 아는 값이 아예 없을 때는 미판정으로 남기되 unavailable 이라고 단정하지 않는다.
    discovery._PROBE_CACHE.clear("timeoutfake")
    blind = discovery.probeRuntime(descriptor, refresh=True)
    assert blind.state == "unknown"
    assert blind.executable == "/bin/fake", "실행 파일을 찾은 사실은 그대로 남는다"
    assert blind.detail and "끝나지 않았습니다" in blind.detail


def testUndeterminedRuntimeAsksForRecheckInsteadOfRecommendingInstall():
    """판정하지 못한 런타임에 설치를 권하지 않는다. 진행 중으로도 표시하지 않는다."""
    from dartlab.ai.runtime.engine import _runtimeStatusEntry

    descriptor = loadRuntimeRegistry()["codex"]
    probe = RuntimeProbe("codex", "unknown", "/bin/codex", detail="버전 확인이 8초 안에 끝나지 않았습니다")
    entry = _runtimeStatusEntry(
        descriptor,
        probe,
        {"state": "unknown", "authenticated": None, "undetermined": True},
        {"connected": False, "undetermined": True},
        {"ready": True, "checks": {"readSkill": True, "engineCall": True}},
    )

    assert entry["installed"] is True, "실행 파일을 찾은 사실은 판정 실패와 무관하다"
    assert entry["undetermined"] is True
    assert entry["pending"] is False, "기다려도 안 바뀌는 상태를 진행 중으로 두면 화면이 영원히 폴링한다"
    assert entry["primaryAction"] == "recheck"
    assert entry["canInstall"] is False and entry["canConnect"] is False and entry["canLogin"] is False
    assert entry["blockingReason"] == "설치 상태를 확인하지 못했습니다"
    assert entry["groundedReady"] is False and entry["investmentReady"] is False


def testBackgroundProbeRetriesUndeterminedInsteadOfFreezingAFailure():
    """백그라운드 실측은 판정 실패를 결론으로 굳히기 전에 한 번 더 잰다.

    실측 회귀(2026-08-06): 서버 기동과 겹친 첫 실측에서 CLI 두 개가 상한을 넘겼고,
    첫 진입 화면이 멀쩡한 런타임에 "확인 실패" 를 띄웠다. 아무도 기다리지 않는
    경로라 재시도 비용은 사용자에게 보이지 않는다.
    """
    from dartlab.ai.runtime.probeCache import retryUntilDetermined

    attempts: list[int] = []

    def flaky():
        attempts.append(len(attempts))
        return {"undetermined": len(attempts) < 2}

    result = retryUntilDetermined(flaky, lambda value: not value["undetermined"], delaySeconds=0.0)

    assert result == {"undetermined": False}
    assert len(attempts) == 2, "첫 실패 뒤 한 번 더 재야 한다"

    # 계속 실패해도 무한히 매달리지 않는다.
    attempts.clear()
    stuck = retryUntilDetermined(
        lambda: (attempts.append(1), {"undetermined": True})[1],
        lambda value: not value["undetermined"],
        attempts=3,
        delaySeconds=0.0,
    )
    assert stuck == {"undetermined": True}
    assert len(attempts) == 3


def testCodexRuntimeErrorSurfacesRealReasonExactlyOnce():
    """Codex 실패는 사유와 함께 runtimeError 로 올라오고 중복 보고되지 않는다.

    실측(2026-08-06): DartLab 이 연 codex 세션 19 건 전부가 사용량 한도 소진으로
    죽었는데 `error` 알림도 `turn.error` 도 투영되지 않아 화면에는 사유 없는
    "런타임이 정상 완료되지 않았습니다" 만 남았다. 사용자는 자기 계정 한도가 끝난
    것을 알 방법이 없었다.
    """
    projector = EventProjector("codex", "session-1")
    limitMessage = "You've hit your usage limit. Try again at Aug 8th."

    reported = projector.project(
        {
            "method": "error",
            "params": {
                "error": {"message": limitMessage, "codexErrorInfo": "usageLimitExceeded"},
                "willRetry": False,
            },
        },
        turnId="turn-1",
    )
    assert [event.kind for event in reported] == ["runtimeError"]
    assert reported[0].payload["error"] == limitMessage
    assert reported[0].payload["errorCode"] == "usageLimitExceeded"

    # 같은 실패를 turn/completed 가 다시 실어 보내도 두 번 올리지 않는다.
    terminal = projector.project(
        {
            "method": "turn/completed",
            "params": {"turn": {"status": "failed", "error": {"message": limitMessage}}},
        },
        turnId="turn-1",
    )
    assert [event.kind for event in terminal] == ["turnCompleted"]


def testCodexFailedTurnWithoutErrorNotificationStillReportsReason():
    """`error` 알림 없이 turn/completed 만 실패로 오는 경우도 사유를 잃지 않는다."""
    projector = EventProjector("codex", "session-1")

    events = projector.project(
        {
            "method": "turn/completed",
            "params": {"turn": {"status": "failed", "error": {"message": "model stream disconnected"}}},
        },
        turnId="turn-1",
    )

    assert [event.kind for event in events] == ["runtimeError", "turnCompleted"]
    assert events[0].payload["error"] == "model stream disconnected"


def testCodexRetryableErrorIsNotReportedAsTurnFailure():
    """재시도 예정 오류를 실패로 올리면 곧 회복될 턴의 답변이 미전달 처리된다."""
    projector = EventProjector("codex", "session-1")

    events = projector.project(
        {"method": "error", "params": {"error": {"message": "transient"}, "willRetry": True}},
        turnId="turn-1",
    )

    assert [event.kind for event in events] == []


def testCodexNonToolItemsAreNotProjectedAsToolCalls():
    """사용자 메시지와 사고 항목은 도구가 아니다.

    실측(2026-08-06): `userMessage` 가 도구 호출로 기록돼 도달성 측정에 "도구 1 회" 로
    잡혔지만 실제 DartLab 도구 도달은 0 이었다.
    """
    projector = EventProjector("codex", "session-1")

    for itemType in ("userMessage", "agentMessage", "reasoning", "contextCompaction"):
        started = projector.project(
            {"method": "item/started", "params": {"item": {"type": itemType, "id": "x"}}}, turnId="turn-1"
        )
        assert started == [], f"{itemType} 은 도구가 아니다"

    tool = projector.project(
        {
            "method": "item/started",
            "params": {"item": {"type": "mcpToolCall", "id": "m", "server": "dartlab", "tool": "EngineCall"}},
        },
        turnId="turn-1",
    )
    assert [event.kind for event in tool] == ["toolStarted"]
    assert tool[0].payload["item"]["tool"] == "EngineCall"


def testCodexReasoningSummaryDeltaBecomesVisibleThinking():
    """gpt-5 계열은 원문 대신 요약 reasoning 을 흘린다. 버리면 화면 사고 과정이 빈다."""
    projector = EventProjector("codex", "session-1")

    events = projector.project(
        {"method": "item/reasoning/summaryTextDelta", "params": {"delta": "재무 표를 먼저 확인한다"}},
        turnId="turn-1",
    )

    assert [event.kind for event in events] == ["reasoningDelta"]
    assert events[0].payload["text"] == "재무 표를 먼저 확인한다"


def testCodexMcpToolResultIsReadFromContentItems():
    """Codex 는 namespace 로 묶은 MCP 결과를 contentItems 로 준다."""
    from dartlab.ai.agent import _runtimeToolData

    data = _runtimeToolData(
        {"item": {"type": "dynamicToolCall", "id": "d", "tool": "EngineCall", "contentItems": {"ok": True}}},
        status="done",
    )

    assert data["data"] == {"ok": True}


def testRuntimeDeliveryRecordSurvivesRestartAndClears(tmp_path):
    """도달 판정은 프로세스가 죽어도 남고 명시적 초기화로만 지워진다."""
    store = SessionStore(tmp_path / "sessions.sqlite3")
    store.recordDelivery("codex", "blocked", "사용량 한도 소진")

    reopened = SessionStore(tmp_path / "sessions.sqlite3")
    record = reopened.getDelivery("codex")
    assert record is not None
    assert record["state"] == "blocked"
    assert record["detail"] == "사용량 한도 소진"

    reopened.clearDelivery("codex")
    assert reopened.getDelivery("codex") is None


def testSameFailureInLaterTurnStillReportsReason():
    """중복 억제는 한 턴 안에서만이다. 같은 사유로 두 턴이 연속 실패해도 둘 다 보고한다."""
    projector = EventProjector("codex", "session-1")
    failure = {"method": "error", "params": {"error": {"message": "한도 소진"}, "willRetry": False}}

    first = projector.project(failure, turnId="turn-1")
    repeatSameTurn = projector.project(failure, turnId="turn-1")
    second = projector.project(failure, turnId="turn-2")

    assert [event.kind for event in first] == ["runtimeError"]
    assert repeatSameTurn == []
    assert [event.kind for event in second] == ["runtimeError"]
