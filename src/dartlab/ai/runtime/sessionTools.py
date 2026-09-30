"""네이티브 세션의 도구 실행과 근거 이벤트. 업무 처리는 기존 도구 registry가 소유한다."""

from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any

from .contracts import AgentEvent
from .eventProjection import EventProjector

_MAX_RESULT_BYTES = 512_000


def sessionToolSpecs() -> list[dict[str, Any]]:
    """세션이 직접 광고할 도구를 canonical registry에서 읽는다."""
    from dartlab.ai.tools.registry import agentToolSpecs

    return [{key: spec[key] for key in ("name", "description", "inputSchema")} for spec in agentToolSpecs()]


def callSessionTool(
    projector: EventProjector,
    turnId: str,
    callId: str,
    name: str,
    arguments: Any,
) -> Generator[AgentEvent, None, dict[str, Any]]:
    """호스트가 실제 실행한 결과로만 시작·완료 이벤트와 evidence를 발급한다."""
    from dartlab.ai.tools.registry import executeAgentTool

    item = {"id": callId, "type": "dynamicToolCall", "tool": name, "arguments": arguments}
    yield projector.event("toolStarted", turnId=turnId, payload={"item": item}, nativeType="host/tool/start")
    result = executeAgentTool(name, arguments)
    encoded = json.dumps(result, ensure_ascii=False, default=str)
    if len(encoded.encode("utf-8")) > _MAX_RESULT_BYTES:
        result = {
            "ok": False,
            "error": "result_too_large",
            "summary": "결과가 세션 한도를 넘었습니다. 기간, 대상, limit을 좁혀 다시 호출하세요.",
        }
    completed = {**item, "status": "completed" if result.get("ok") else "failed", "result": result}
    yield projector.event("toolCompleted", turnId=turnId, payload={"item": completed}, nativeType="host/tool/end")
    return result
