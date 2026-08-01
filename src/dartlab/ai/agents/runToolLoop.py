"""Provider-driven multi-turn tool loop with a neutral message schema.

신규 LLM 어댑터가 늘어날 때 본 함수는 변하지 않는다. 어댑터가 자기 conversation
형식으로 변환할 책임은 `provider.complete` 안쪽에 있다.

Neutral message schema (Anthropic 친화):
    {"role": "system",    "content": str}
    {"role": "user",      "content": str | list[block]}
    {"role": "assistant", "content": list[block]}    # text, tool_use 블록
    {"role": "tool",      "content": list[block]}    # tool_result 블록

block 종류:
    {"type": "text",        "text": str}
    {"type": "tool_use",    "id": str, "name": str, "input": dict}
    {"type": "tool_result", "tool_use_id": str, "content": str | dict, "is_error": bool}
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

from dartlab.ai.contracts import Ref
from dartlab.ai.providers.base import LLMEvent, Msg
from dartlab.ai.toolAdmission import executeAllowedTool
from dartlab.ai.tools.types import ToolSpec


class ToolLoopProvider(Protocol):
    """중립 tool loop가 소비하는 provider의 최소 streaming 계약."""

    def complete(
        self,
        messages: list[Msg],
        tools: list[ToolSpec],
        *,
        stream: bool,
    ) -> Iterable[LLMEvent]:
        """중립 메시지와 도구 계약으로 모델 이벤트를 생성한다."""
        ...


@dataclass
class AgentResult:
    """agent loop 종료 시 누적 결과 — text + refs + toolCalls + stopReason + steps."""

    text: str = ""
    refs: list[Ref] = field(default_factory=list)
    toolCalls: list[dict[str, Any]] = field(default_factory=list)
    stopReason: str = ""
    steps: int = 0


def runToolLoop(
    provider: ToolLoopProvider,
    *,
    system: str,
    messages: list[Msg],
    tools: list[ToolSpec],
    executeTool: Callable[[str, dict[str, Any]], dict[str, Any]],
    onEvent: Callable[[LLMEvent], None] | None = None,
    maxSteps: int = 10,
) -> AgentResult:
    """Run a ReAct loop until the provider stops without requesting a tool.

    `executeTool` 시그니처는 `(name, args) -> ToolResult.to_dict()` 형식의
    `dartlab.ai.tools.registry.executeTool` 호환이다.
    """

    convo: list[Msg] = []
    if system:
        convo.append({"role": "system", "content": system})
    convo.extend(_clone(messages))

    result = AgentResult()
    refs: list[Ref] = []
    allowed_tool_names = frozenset(tool.name for tool in tools)

    for step in range(maxSteps):
        result.steps = step + 1
        text_buf: list[str] = []
        tool_uses: list[dict[str, Any]] = []
        stop_reason = ""

        for ev in provider.complete(convo, tools, stream=True):
            if onEvent is not None:
                onEvent(ev)
            if ev.kind == "text":
                text_buf.append(str(ev.data.get("delta", "")))
            elif ev.kind == "tool_use":
                tool_uses.append(
                    {
                        "id": str(ev.data.get("id") or f"tu_{step}_{len(tool_uses)}"),
                        "name": str(ev.data.get("name") or ""),
                        "input": dict(ev.data.get("input") or {}),
                    }
                )
            elif ev.kind == "stop":
                stop_reason = str(ev.data.get("reason") or "")

        text = "".join(text_buf)
        result.text += text
        result.stopReason = stop_reason

        if not tool_uses:
            break

        # Append assistant turn with text + tool_use blocks
        assistant_blocks: list[dict[str, Any]] = []
        if text:
            assistant_blocks.append({"type": "text", "text": text})
        for tu in tool_uses:
            assistant_blocks.append({"type": "tool_use", "id": tu["id"], "name": tu["name"], "input": tu["input"]})
        convo.append({"role": "assistant", "content": assistant_blocks})

        # Execute each tool and collect tool_result blocks
        tool_results: list[dict[str, Any]] = []
        for tu in tool_uses:
            outcome = executeAllowedTool(
                executeTool,
                tu["name"],
                tu["input"],
                allowed_tool_names,
            )
            ok = bool(outcome.get("ok", True))
            for ref_dict in outcome.get("refs") or []:
                refs.append(_refFromDict(ref_dict))
            result.toolCalls.append(
                {
                    "id": tu["id"],
                    "tool": tu["name"],
                    "input": tu["input"],
                    "ok": ok,
                    "summary": outcome.get("summary", ""),
                    "error": outcome.get("error"),
                }
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": outcome.get("summary") or outcome.get("data") or "",
                    "is_error": not ok,
                }
            )

        convo.append({"role": "tool", "content": tool_results})

    result.refs = refs
    return result


def _clone(messages: list[Msg]) -> list[Msg]:
    return [dict(m) for m in messages]


def _refFromDict(payload: dict[str, Any]) -> Ref:
    return Ref(
        id=str(payload.get("id") or ""),
        kind=str(payload.get("kind") or ""),
        title=str(payload.get("title") or ""),
        source=str(payload.get("source") or ""),
        payload=dict(payload.get("payload") or {}),
    )


__all__ = ["AgentResult", "runToolLoop"]
