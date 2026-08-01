"""LLM이 광고되지 않은 도구 이름을 만들어도 실행되지 않는 계약."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest

from dartlab.ai.agent import runAgent
from dartlab.ai.agents.runToolLoop import runToolLoop
from dartlab.ai.providers import ProviderTurn, ToolCall
from dartlab.ai.providers.base import LLMEvent
from dartlab.ai.tools.types import ToolSpec
from dartlab.ai.workbench.runner import runLLMPass
from dartlab.ai.workbench.state import WorkbenchState

pytestmark = pytest.mark.unit


class _WorkbenchProvider:
    class _Config:
        provider = "test"

    config = _Config()

    def __init__(self, turns: list[ProviderTurn]) -> None:
        self.turns = list(turns)

    def generate(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ProviderTurn:
        del messages, tools
        return self.turns.pop(0)


class _StreamProvider:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, messages, tools, stream=True):  # noqa: ANN001, ANN201
        del messages, tools, stream
        self.calls += 1
        if self.calls == 1:
            yield LLMEvent("tool_use", {"id": "t1", "name": "WebSearch", "input": {"query": "x"}})
            yield LLMEvent("stop", {"reason": "tool_use"})
        else:
            yield LLMEvent("text", {"delta": "done"})
            yield LLMEvent("stop", {"reason": "end"})


def _turns() -> list[ProviderTurn]:
    return [
        ProviderTurn(
            content="",
            toolCalls=[ToolCall(id="t1", name="WebSearch", args={"query": "x"})],
            raw=None,
        ),
        ProviderTurn(content="done", toolCalls=[], raw=None),
    ]


def _collect(stream: Iterable[Any]) -> list[Any]:
    return list(stream)


def test_chat_agent_rejects_tool_outside_session_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    executed: list[str] = []

    def fake_execute(name: str, args: dict[str, Any]) -> dict[str, Any]:
        del args
        executed.append(name)
        return {"ok": True, "summary": "unexpected", "refs": [], "data": {}, "error": None}

    monkeypatch.setattr("dartlab.ai.agent.executeTool", fake_execute)
    events = _collect(runAgent("test", provider=_WorkbenchProvider(_turns()), toolNames=("ReadSkill",)))

    assert executed == []
    result = next(event for event in events if event.kind == "tool_result")
    assert result.data["error"] == "tool_not_allowed"


def test_workbench_pass_rejects_tool_outside_pass_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    executed: list[str] = []

    def fake_execute(name: str, args: dict[str, Any]) -> dict[str, Any]:
        del args
        executed.append(name)
        return {"ok": True, "summary": "unexpected", "refs": [], "data": {}, "error": None}

    monkeypatch.setattr("dartlab.ai.workbench.runner.executeTool", fake_execute)
    state = WorkbenchState(question="test")
    events = _collect(
        runLLMPass(
            state,
            _WorkbenchProvider(_turns()),
            passName="test",
            systemPrompt="system",
            userContext="user",
            allowedTools=["ReadSkill"],
        )
    )

    assert executed == []
    result = next(event for event in events if event.kind == "tool_result")
    assert result.data["error"] == "tool_not_allowed"


def test_neutral_tool_loop_rejects_tool_outside_supplied_specs() -> None:
    executed: list[str] = []

    def fake_execute(name: str, args: dict[str, Any]) -> dict[str, Any]:
        del args
        executed.append(name)
        return {"ok": True, "summary": "unexpected", "refs": [], "data": {}, "error": None}

    result = runToolLoop(
        _StreamProvider(),
        system="system",
        messages=[{"role": "user", "content": "test"}],
        tools=[ToolSpec("ReadSkill", "read", {"type": "object"})],
        executeTool=fake_execute,
    )

    assert executed == []
    assert result.toolCalls[0]["error"] == "tool_not_allowed"
