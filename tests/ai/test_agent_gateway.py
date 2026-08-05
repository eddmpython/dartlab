from __future__ import annotations

import asyncio
import json

import pytest

from dartlab.ai.contracts import TraceEvent
from dartlab.server.models import AgentRunMessage, AgentRunRequest

pytestmark = pytest.mark.unit


def _payload(event: dict[str, str]) -> dict:
    return json.loads(event["data"])


def test_display_name_uses_registry_legacy_map() -> None:
    """_displayName 은 registry._LEGACY_NAME_MAP SSOT 위에서 동작 — _TOOL_DISPLAY 중복 dict 폐기."""
    from dartlab.server.agentGateway import _PUBLIC_TOOL_NAMES, _displayName

    # canonical PascalCase 그대로
    assert _displayName("RunPython") == "RunPython"
    assert _displayName("ReadSkill") == "ReadSkill"
    # legacy snake → Pascal (registry SSOT)
    assert _displayName("run_python") == "RunPython"
    assert _displayName("engine_call") == "EngineCall"
    assert _displayName("read_skill") == "ReadSkill"
    # workbench GATE 별칭 (registry canonical 외 display only)
    assert _displayName("verify") == "Verify"
    # 미지 도구는 snake → space split fallback
    assert _displayName("unknown_thing") == "unknown thing"
    # whitelist 는 registry SSOT 에서 derive
    assert "RunPython" in _PUBLIC_TOOL_NAMES
    assert "run_python" in _PUBLIC_TOOL_NAMES
    assert "verify" in _PUBLIC_TOOL_NAMES


def testPrefixedNativeMcpToolIsProjectedAsCanonicalPublicTool() -> None:
    from dartlab.server.agentGateway import _publicEvents

    events = _publicEvents(
        TraceEvent(
            "tool_start",
            {
                "name": "mcp__dartlab__EngineCall",
                "nativeName": "mcp__dartlab__EngineCall",
                "canonicalName": "EngineCall",
                "toolCallId": "call-1",
                "input": {"apiRef": "Company.panel"},
            },
        ),
        runId="run-1",
        messageId="message-1",
    )

    assert len(events) == 1
    payload = _payload(events[0])
    assert payload["toolName"] == "EngineCall"
    assert payload["toolCallId"] == "call-1"


def test_agent_gateway_public_events_hide_internal_kernel_names(monkeypatch) -> None:
    import dartlab.server.agentGateway as agent_gateway

    def fake_runtime(question: str, **kwargs):
        assert question == "너 뭐 할 수 있니"
        assert kwargs["runtimeId"] == "codex"
        yield TraceEvent("plan", {"selectedSkillIds": ["start.useSkillsCatalog"]})
        yield TraceEvent("reference", {"refs": [{"id": "skill:start"}], "source": "search_reference"})
        yield TraceEvent("tool_start", {"name": "search_reference", "id": "hidden-search"})
        yield TraceEvent("tool_start", {"name": "run_python", "id": "code-1"})
        yield TraceEvent("tool_result", {"name": "run_python", "id": "code-1", "outputSummary": "계산 완료"})
        yield TraceEvent("chunk", {"text": "DartLab은 재무/공시/시장 데이터를 근거로 분석합니다."})
        yield TraceEvent("answer", {"evidenceRefs": ["skill:start"]})
        yield TraceEvent(
            "done",
            {
                "refs": [{"id": "skill:start"}],
                "responseMeta": {"finalEvent": "answer", "refCount": 1, "verificationOk": True},
            },
        )

    monkeypatch.setattr(agent_gateway, "runRuntimeAgent", fake_runtime)
    req = AgentRunRequest(
        messages=[AgentRunMessage(role="user", content="너 뭐 할 수 있니")],
        runtimeId="codex",
        workspaceContext={"mode": "analyze"},
    )

    async def collect():
        return [event async for event in agent_gateway.streamAgentRun(req)]

    events = asyncio.run(collect())
    public_text = "\n".join(event["event"] + " " + event["data"] for event in events)

    assert "search_reference" not in public_text
    assert "hidden-search" not in public_text
    assert "prose_without_finalize" not in public_text
    assert "draft_rejected" not in public_text
    assert "TEXT_MESSAGE_CONTENT" in {event["event"] for event in events}
    assert "TOOL_CALL_START" in {event["event"] for event in events}
    assert "RUN_FINISHED" in {event["event"] for event in events}
    assert any(_payload(event).get("toolName") == "RunPython" for event in events)


def testAgentGatewayPublishesInvestmentConversationAndUsefulFollowups(monkeypatch) -> None:
    import dartlab.server.agentGateway as agentGateway

    def fakeRuntime(question: str, **kwargs):
        yield TraceEvent("chunk", {"text": "검증된 투자 판단"})
        yield TraceEvent(
            "done",
            {
                "refs": [{"id": "table:005930:investment"}],
                "responseMeta": {"finalEvent": "answer", "verificationOk": True},
            },
        )

    monkeypatch.setattr(agentGateway, "runRuntimeAgent", fakeRuntime)
    request = AgentRunRequest(
        messages=[AgentRunMessage(role="user", content="삼성전자 005930 지금 투자할 만해?")],
        runtimeId="codex",
    )

    async def collect():
        return [event async for event in agentGateway.streamAgentRun(request)]

    events = asyncio.run(collect())
    state = next(_payload(event) for event in events if event["event"] == "STATE_DELTA")
    finished = next(_payload(event) for event in events if event["event"] == "RUN_FINISHED")

    assert state["analysisConversation"]["mode"] == "investmentDecision"
    assert finished["responseMeta"]["analysisConversation"]["label"] == "투자 판단"
    assert len(finished["suggestedQuestions"]) == 3
    assert any("반대논지" in value for value in finished["suggestedQuestions"])


def test_agent_gateway_uses_unique_turn_ids_and_keeps_structured_context(monkeypatch) -> None:
    import dartlab.server.agentGateway as agent_gateway

    received = []

    def fake_runtime(question: str, **kwargs):
        received.append(kwargs)
        yield TraceEvent(
            "done",
            {"refs": [], "responseMeta": {"finalEvent": "runtime_error", "failureReason": "missing evidence"}},
        )

    monkeypatch.setattr(agent_gateway, "runRuntimeAgent", fake_runtime)
    req = AgentRunRequest(
        threadId="stable-session",
        messages=[AgentRunMessage(role="user", content="이 회사 매출은?")],
        workspaceContext={"stockCode": "005930", "period": "2026Q1", "reportMode": True},
    )

    async def collect():
        first = [event async for event in agent_gateway.streamAgentRun(req)]
        second = [event async for event in agent_gateway.streamAgentRun(req)]
        return first, second

    first, second = asyncio.run(collect())
    firstState = _payload(first[0])
    secondState = _payload(second[0])
    assert firstState["runId"] != secondState["runId"]
    assert firstState["threadId"] == "stable-session"
    assert received[0]["sessionId"] == "stable-session"
    assert received[0]["stockCode"] == "005930"
    assert received[0]["period"] == "2026Q1"
    assert received[0]["reportMode"] is True


def test_agent_gateway_failure_reason_is_public(monkeypatch) -> None:
    import dartlab.server.agentGateway as agent_gateway

    def fake_runtime(question: str, **kwargs):
        yield TraceEvent("unable", {"reason": "prose_without_finalize"})

    monkeypatch.setattr(agent_gateway, "runRuntimeAgent", fake_runtime)
    req = AgentRunRequest(
        messages=[AgentRunMessage(role="user", content="질문")],
        workspaceContext={"mode": "analyze"},
    )

    async def collect():
        return [event async for event in agent_gateway.streamAgentRun(req)]

    events = asyncio.run(collect())
    errors = [_payload(event) for event in events if event["event"] == "RUN_ERROR"]

    assert errors
    assert errors[0]["message"] == "최종 답변을 생성하지 못했습니다."
    assert "prose_without_finalize" not in json.dumps(errors, ensure_ascii=False)


def test_agent_gateway_failed_done_emits_public_error_without_internal_meta(monkeypatch) -> None:
    import dartlab.server.agentGateway as agent_gateway

    def fake_runtime(question: str, **kwargs):
        yield TraceEvent(
            "done",
            {
                "refs": [],
                "responseMeta": {
                    "finalEvent": "prose_without_finalize",
                    "failureReason": "prose_without_finalize",
                    "refCount": 0,
                },
            },
        )

    monkeypatch.setattr(agent_gateway, "runRuntimeAgent", fake_runtime)
    req = AgentRunRequest(
        messages=[AgentRunMessage(role="user", content="질문")],
        workspaceContext={"mode": "analyze"},
    )

    async def collect():
        return [event async for event in agent_gateway.streamAgentRun(req)]

    events = asyncio.run(collect())
    public_text = json.dumps([_payload(event) for event in events], ensure_ascii=False)

    assert any(event["event"] == "RUN_ERROR" for event in events)
    assert any(_payload(event).get("status") == "failed" for event in events if event["event"] == "RUN_FINISHED")
    assert "prose_without_finalize" not in public_text


def test_agent_runs_endpoint_streams_only_public_events(monkeypatch) -> None:
    from starlette.testclient import TestClient

    import dartlab.server.api.agent as agent_api
    from dartlab.server import app

    async def fake_stream(req):
        yield {"event": "ACTIVITY_DELTA", "data": json.dumps({"summary": "근거 확인", "status": "done"})}
        yield {"event": "RUN_FINISHED", "data": json.dumps({"status": "ok", "refs": ["skill:start"]})}

    monkeypatch.setattr(agent_api, "streamAgentRun", fake_stream)
    with TestClient(app, raise_server_exceptions=False) as client:
        with client.stream(
            "POST",
            "/api/agent/runs",
            json={"messages": [{"role": "user", "content": "너 뭐 할 수 있니"}], "stream": True},
        ) as response:
            body = response.read().decode("utf-8")

    assert response.status_code == 200
    assert "event: ACTIVITY_DELTA" in body
    assert "event: RUN_FINISHED" in body
    assert "search_reference" not in body


def test_api_ask_stream_uses_public_agent_events(monkeypatch) -> None:
    import dartlab.server.api.ask as ask_api
    from dartlab.server.models import AskRequest

    async def fake_stream(req):
        yield {"event": "TEXT_MESSAGE_CONTENT", "data": json.dumps({"delta": "답변"})}
        yield {"event": "RUN_FINISHED", "data": json.dumps({"status": "ok"})}

    monkeypatch.setattr(ask_api, "streamAgentRun", fake_stream)

    async def collect():
        return [event async for event in ask_api._streamPublicAsk(AskRequest(question="너 뭐 할 수 있니", stream=True))]

    events = asyncio.run(collect())
    body = "\n".join(event["event"] for event in events)

    assert "TEXT_MESSAGE_CONTENT" in body
    assert "RUN_FINISHED" in body
    assert "graph_node" not in body
    assert "tool_start" not in body


def test_research_graph_emits_ordered_node_state(monkeypatch) -> None:
    from dartlab.ai.workbench import WorkbenchLoop

    events = list(WorkbenchLoop().stream("너 뭐 할 수 있니"))
    nodes = [event.data["node"] for event in events if event.kind == "graph_node"]

    # 5 패스 SSOT — workbench loop 의 GRAPH_NODES 와 일치.
    # 휴리스틱 path 는 brief→work→compose→gate 순으로 발행 (HARVEST 는 LLM 전용 no-op).
    # GATE 는 결과 + 실패 분기에서 두 번 발행될 수 있다.
    assert nodes[:4] == ["brief", "work", "compose", "gate"]
    assert events[-1].kind == "done"


def test_delta_streams_and_final_chunk_does_not_duplicate() -> None:
    """과정 중계: delta 는 실시간으로 흐르고, 같은 본문의 최종 chunk 는 중복 발행하지 않는다.

    delta 를 이미 보낸 뒤 chunk 를 그대로 내보내면 화면에 본문이 두 번 그려진다.
    """
    from dartlab.server.agentGateway import _publicEvents

    delta = _publicEvents(
        TraceEvent("delta", {"text": "매출은"}),
        runId="run-1",
        messageId="msg-1",
    )
    assert [event["event"] for event in delta] == ["TEXT_MESSAGE_CONTENT"]
    assert _payload(delta[0])["delta"] == "매출은"

    # delta 를 흘린 뒤의 chunk 는 억제된다
    assert (
        _publicEvents(
            TraceEvent("chunk", {"text": "매출은 398조다"}),
            runId="run-1",
            messageId="msg-1",
            streamedDelta=True,
        )
        == []
    )

    # delta 가 없던 런타임(비스트리밍)에서는 chunk 가 본문을 낸다
    fallback = _publicEvents(
        TraceEvent("chunk", {"text": "매출은 398조다"}),
        runId="run-1",
        messageId="msg-1",
        streamedDelta=False,
    )
    assert [event["event"] for event in fallback] == ["TEXT_MESSAGE_CONTENT"]


def test_verification_badge_fields_reach_public_meta() -> None:
    """검증 뱃지 3필드가 공개 responseMeta allowlist 를 통과한다."""
    from dartlab.server.agentGateway import _publicResponseMeta

    public = _publicResponseMeta(
        {
            "verificationStatus": "unverified",
            "evidenceCount": 37,
            "verificationNotes": ["기준시점 근거가 답변에 인용되지 않았습니다"],
            "internalSecret": "노출 금지",
        }
    )

    assert public["verificationStatus"] == "unverified"
    assert public["evidenceCount"] == 37
    assert public["verificationNotes"] == ["기준시점 근거가 답변에 인용되지 않았습니다"]
    assert "internalSecret" not in public
