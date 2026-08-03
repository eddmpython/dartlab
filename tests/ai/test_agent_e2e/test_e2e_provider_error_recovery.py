"""E2E 시나리오 10: provider stream error 후 refs 보존 partial 답안.

마스터 플랜 트랙 4 (cryptic-discovering-kettle.md). turn 1 에서 tool 호출 성공 후 refs
누적, turn 2 streamProvider 가 RuntimeError, recoverable=True + done event 보존.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

import pytest

from dartlab.ai.agent import runAgent
from dartlab.ai.contracts import TraceEvent
from dartlab.ai.providers import ProviderTurn, StreamChunk, ToolCall

pytestmark = pytest.mark.unit


class _ScriptedProvider:
    class _Cfg:
        provider = "scripted"
        model = "scripted-model"

    def __init__(self, turns: list[ProviderTurn]) -> None:
        self.config = self._Cfg()
        self._turns = list(turns)
        self._index = 0

    def generate(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ProviderTurn:
        if self._index >= len(self._turns):
            return ProviderTurn(content="", toolCalls=[], raw=None)
        t = self._turns[self._index]
        self._index += 1
        return t


def _collect(stream: Iterable[TraceEvent]) -> list[TraceEvent]:
    return list(stream)


def test_provider_error_after_refs_finalizes(monkeypatch: pytest.MonkeyPatch) -> None:
    """1 turn tool 성공 후 2 turn streamProvider 실패 시 finalize 한 round 시도."""

    def fake_execute(name: str, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "summary": "ok",
            "refs": [
                {
                    "id": "p:1",
                    "kind": "valueRef",
                    "title": "v",
                    "source": "x",
                    "payload": {"value": 1, "confidence": 50},
                }
            ],
            "data": {},
            "error": None,
        }

    monkeypatch.setattr("dartlab.ai.agent.executeTool", fake_execute)

    turn1 = ProviderTurn(
        content="",
        toolCalls=[ToolCall(id="t1", name="ReadSkill", args={"q": "a"})],
        raw=None,
    )
    # finalize 가 retry 한 round (turn.toolCalls=[] + content)
    turn_finalize = ProviderTurn(content="부분 답안: 진행 중 오류", toolCalls=[], raw=None)
    call_count = {"n": 0}

    def flaky_stream(
        provider: Any, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> Iterator[StreamChunk]:
        call_count["n"] += 1
        if call_count["n"] == 1:
            yield StreamChunk(text="", final=True, turn=turn1)
            return
        if call_count["n"] == 2:
            raise RuntimeError("stream timeout")
        # finalize 호출: 정상 stream
        for piece in turn_finalize.content or "":
            yield StreamChunk(text=piece)
        yield StreamChunk(text="", final=True, turn=turn_finalize)

    monkeypatch.setattr("dartlab.ai.providers.streamProvider", flaky_stream)

    provider = _ScriptedProvider([])
    events = _collect(runAgent("provider error test", provider=provider, toolNames=("ReadSkill",)))
    kinds = [e.kind for e in events]
    assert "error" in kinds
    # recoverable=True flag
    err = next(e for e in events if e.kind == "error")
    assert err.data.get("recoverable") is True
    # 그래도 done emit + refs 보존
    assert "done" in kinds
    done = next(e for e in events if e.kind == "done")
    assert len(done.data["refs"]) >= 1
