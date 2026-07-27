"""AG-UI compatible Agent Gateway for DartLab."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from dartlab.ai.agent import runAgent
from dartlab.ai.contracts import TraceEvent
from dartlab.ai.tools.registry import _LEGACY_NAME_MAP, CANONICAL_TOOL_NAMES
from dartlab.ai.workbench import WorkbenchLoop

from . import agentMetrics
from .models import AgentRunRequest
from .streaming import _syncGenToAsync

logger = logging.getLogger(__name__)


def _displayName(tool: str) -> str:
    """도구 이름을 UI 표시용으로 정규화 — registry _LEGACY_NAME_MAP SSOT 위 wrapping."""
    canonical = _LEGACY_NAME_MAP.get(tool, tool)
    if canonical in CANONICAL_TOOL_NAMES:
        return canonical
    if tool == "verify":  # Workbench GATE 패스의 별칭 — registry canonical 외 display only.
        return "Verify"
    return str(tool).replace("_", " ")


# UI 가 ToolBlock 카드로 표현할 도구 화이트리스트. registry SSOT 에서 derive — PascalCase canonical
# + snake_case legacy alias 가 동시에 화이트리스트에 들어간다.
_PUBLIC_TOOL_NAMES = set(CANONICAL_TOOL_NAMES) | set(_LEGACY_NAME_MAP.keys()) | {"verify"}

_ALLOWED_EVENTS = {
    "TEXT_MESSAGE_START",
    "TEXT_MESSAGE_CONTENT",
    "TEXT_MESSAGE_END",
    "THINKING_DELTA",
    "TOOL_CALL_START",
    "TOOL_CALL_ARGS",
    "TOOL_CALL_END",
    "TOOL_CALL_RESULT",
    "STATE_SNAPSHOT",
    "STATE_DELTA",
    "MESSAGES_SNAPSHOT",
    "ACTIVITY_SNAPSHOT",
    "ACTIVITY_DELTA",
    "VIEW_SPEC",
    "RUN_FINISHED",
    "RUN_ERROR",
}


async def streamAgentRun(req: AgentRunRequest) -> AsyncIterator[dict[str, str]]:
    """Stream one DartLab run using the public AG-UI event contract.

    분기:
    - 명시적 mode="analyze" / "research" / 종목 컨텍스트 / 분석 키워드 → WorkbenchLoop (5 패스)
    - 그 외 (메타 / chitchat / 일반 대화) → runAgent (LLM 자율 + tool calling)

    회귀 방지: memory/feedback_no_graph_regression.md — runAgent 가 본체. WorkbenchLoop 는 옵션.
    """
    question = _lastUserMessage(req)
    runId = req.threadId or "dartlab-thread"
    messageId = f"msg-{runId}"
    text_started = False

    kernelKwargs = _kernelKwargs(req)
    use_workbench = _shouldUseWorkbench(req, question, kernelKwargs)

    if use_workbench:
        graph = WorkbenchLoop()
        agentMetrics.record("workbench")
        yield _event(
            "STATE_SNAPSHOT",
            {
                "runId": runId,
                "agentId": req.agentId or "dartlab-research",
                "status": "running",
                "graph": {"name": "DartLabWorkbench", "nodes": list(graph.nodes)},
                "mode": "workbench",
            },
        )
        yield _activity("계획을 세우고 필요한 근거를 확인합니다.", status="done")
        producer = lambda: graph.stream(question, **kernelKwargs)  # noqa: E731
    else:
        provider_obj = _resolveProvider(kernelKwargs)
        if provider_obj is None or not _isLLMProvider(provider_obj):
            # provider 미해결 — workbench 휴리스틱 fallback
            graph = WorkbenchLoop()
            agentMetrics.record("workbench-heuristic")
            yield _event(
                "STATE_SNAPSHOT",
                {
                    "runId": runId,
                    "agentId": req.agentId or "dartlab-research",
                    "status": "running",
                    "graph": {"name": "DartLabWorkbench", "nodes": list(graph.nodes)},
                    "mode": "workbench-heuristic",
                },
            )
            producer = lambda: graph.stream(question, **kernelKwargs)  # noqa: E731
        else:
            agentMetrics.record("agent")
            yield _event(
                "STATE_SNAPSHOT",
                {
                    "runId": runId,
                    "agentId": req.agentId or "dartlab-agent",
                    "status": "running",
                    "graph": {"name": "DartLabAgent", "nodes": ["agent"]},
                    "mode": "agent",
                },
            )
            agent_kwargs = {**kernelKwargs, "provider": provider_obj}
            producer = lambda: runAgent(question, **agent_kwargs)  # noqa: E731

    try:
        async for internal in _syncGenToAsync(producer):
            for public in _publicEvents(internal, runId=runId, messageId=messageId):
                if public["event"] == "TEXT_MESSAGE_CONTENT" and not text_started:
                    text_started = True
                    yield _event("TEXT_MESSAGE_START", {"messageId": messageId, "role": "assistant"})
                yield public
        if text_started:
            yield _event("TEXT_MESSAGE_END", {"messageId": messageId})
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent run failed (runId=%s)", runId)
        yield _event(
            "RUN_ERROR",
            {"runId": runId, "message": _publicFailure(str(exc)), "code": "agent_run_failed"},
        )


def _shouldUseWorkbench(req: AgentRunRequest, question: str, kernelKwargs: dict[str, Any]) -> bool:
    """명시적 분석 모드 → workbench. 그 외 → agent (모델이 자율로 run_workbench 호출 가능).

    P-revised: intent regex 키워드 / 종목코드 자동 추출로 암묵 elevate 안 한다.
    feedback_no_graph_regression.md SSOT — 정당 활성 경로 2 가지: (1) 사용자 명시 모드,
    (2) 모델 자율 run_workbench 도구 호출 (agent.runAgent 안에서).
    """
    context = req.workspaceContext if isinstance(req.workspaceContext, dict) else {}
    if isinstance(context, dict):
        mode = str(context.get("mode") or context.get("dialogueMode") or "").lower()
        if mode in {"analyze", "analysis", "research", "workbench"}:
            return True
    return False


def _resolveProvider(kernelKwargs: dict[str, Any]) -> Any:
    try:
        from dartlab.ai.providers import createProvider

        return createProvider(
            provider=kernelKwargs.get("provider"),
            model=kernelKwargs.get("model"),
        )
    except Exception:  # noqa: BLE001
        logger.exception("provider resolve failed (provider=%s)", kernelKwargs.get("provider"))
        return None


def _isLLMProvider(obj: Any) -> bool:
    """provider 가 LLM 어댑터인지 — workbench/loop 의 _isLLMProvider 와 동일 룰."""
    if obj is None or not callable(getattr(obj, "generate", None)):
        return False
    config = getattr(obj, "config", None)
    providerId = (getattr(config, "provider", None) or "").lower()
    # 리터럴 목록을 두면 새 provider 를 등록해도 여기서만 조용히 탈락한다 (anthropic 사고).
    # kernel.py / workbench/loop.py 와 같은 SSOT (wiredProviderIds) 를 쓴다.
    from dartlab.ai.settings.providerCatalog import wiredProviderIds

    if providerId not in wiredProviderIds():
        return False
    try:
        return bool(obj.checkAvailable())
    except Exception:  # noqa: BLE001
        logger.exception("provider check_available failed (provider=%s)", providerId)
        return False


def _graphNodeEvents(data: dict, *, runId: str) -> list[dict[str, str]]:
    """단계 진행 상태를 상태 델타와 진행 줄 둘로 내보낸다."""
    state = data.get("state") if isinstance(data.get("state"), dict) else {}
    return [
        _event(
            "STATE_DELTA",
            {
                "runId": runId,
                "status": data.get("status") or "running",
                "currentNode": data.get("node"),
                "state": _publicGraphState(state),
            },
        ),
        _activity(str(data.get("summary") or "분석 단계를 진행합니다."), status="done"),
    ]


def _planEvents(data: dict) -> list[dict[str, str]]:
    """고른 분석 경로를 한 줄로. 스킬이 많아도 앞 셋만 보인다."""
    skills = data.get("selectedSkillIds") if isinstance(data.get("selectedSkillIds"), list) else []
    target = ", ".join(str(item) for item in skills[:3])
    return [_activity(f"분석 경로를 정했습니다{': ' + target if target else ''}", refs=[], passLabel=_passLabel(data))]


def _viewSpecEvents(data: dict, *, runId: str, messageId: str) -> list[dict[str, str]]:
    """차트 spec. spec 이 없으면 빈 카드를 만들지 않는다."""
    spec = data.get("spec")
    if not spec:
        return []
    return [
        _event(
            "VIEW_SPEC",
            {
                "runId": runId,
                "messageId": messageId,
                "id": data.get("id"),
                "spec": spec,
                "title": data.get("title"),
                "source": data.get("source"),
            },
        )
    ]


def _referenceEvents(data: dict) -> list[dict[str, str]]:
    """확인한 근거 개수. 하나도 없으면 말하지 않는다."""
    refs = data.get("refs") if isinstance(data.get("refs"), list) else []
    if not refs:
        return []
    return [_activity(f"근거 {len(refs)}개를 확인했습니다.", refs=_refIds(refs), passLabel=_passLabel(data))]


def _verifyEvents(data: dict) -> list[dict[str, str]]:
    """검증 결과. 통과가 아니면 다시 검증한다고 알린다."""
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    passLabel = _passLabel(data)
    if result.get("ok") is True:
        return [
            _activity(
                "근거 검증을 통과했습니다.",
                refs=[str(data.get("refId"))] if data.get("refId") else [],
                passLabel=passLabel,
            )
        ]
    return [_activity("답변 초안을 다시 검증합니다.", status="running", passLabel=passLabel)]


def _toolStartEvents(data: dict, *, runId: str, messageId: str) -> list[dict[str, str]]:
    """도구 호출 시작을 공개 이벤트로. 비공개 도구는 아무 것도 내보내지 않는다.

    ToolBlock 카드(TOOL_CALL_START)가 진행 표현을 전담하므로 activity 줄을 겹쳐 내지 않는다.
    인자를 함께 실어 UI 가 펼칠 때 RunPython 코드나 EngineCall 인자 같은 핵심 입력을 보인다.
    """
    tool = _toolName(data)
    if tool not in _PUBLIC_TOOL_NAMES:
        return []
    payload: dict[str, Any] = {
        "runId": runId,
        "messageId": messageId,
        "toolCallId": str(data.get("id") or tool),
        "toolName": _displayTool(tool),
        "args": data.get("input") if isinstance(data.get("input"), dict) else {},
        "status": "running",
    }
    passLabel = _passLabel(data)
    if passLabel:
        payload["passLabel"] = passLabel
    return [_event("TOOL_CALL_START", payload)]


def _toolResultEvents(data: dict, *, runId: str, messageId: str) -> list[dict[str, str]]:
    """도구 결과를 결과 이벤트와 종료 이벤트 둘로. 비공개 도구는 침묵한다.

    두 이벤트가 같은 toolCallId 와 상태를 공유해야 UI 가 카드를 닫는다. 한 자리에 두는 이유다.
    """
    tool = _toolName(data)
    if tool not in _PUBLIC_TOOL_NAMES:
        return []
    status = "error" if data.get("status") == "error" else "done"
    toolCallId = str(data.get("id") or tool)
    displayName = _displayTool(tool)
    resultEvent: dict[str, Any] = {
        "runId": runId,
        "messageId": messageId,
        "toolCallId": toolCallId,
        "toolName": displayName,
        "status": status,
        "summary": str(data.get("outputSummary") or data.get("summary") or ""),
        "refs": [str(v) for v in data.get("evidenceRefs") or []],
        # UI evidence chip preview 용. payload 가 큰 경우 미리보기로 절단.
        "refDetails": _publicRefDetails(data.get("refDetails")),
        "artifacts": [a for a in data.get("artifacts") or [] if isinstance(a, dict)],
        "result": _publicResultPayload(data),
        "error": str(data.get("error") or "") if status == "error" else None,
    }
    endEvent: dict[str, Any] = {
        "runId": runId,
        "messageId": messageId,
        "toolCallId": toolCallId,
        "toolName": displayName,
        "status": status,
    }
    passLabel = _passLabel(data)
    if passLabel:
        resultEvent["passLabel"] = passLabel
        endEvent["passLabel"] = passLabel
    return [_event("TOOL_CALL_RESULT", resultEvent), _event("TOOL_CALL_END", endEvent)]


def _doneEvents(data: dict, *, runId: str) -> list[dict[str, str]]:
    """실행 종료. 실패면 사유를 먼저 내보내고 종료 이벤트를 뒤에 둔다.

    순서가 뜻을 만든다. UI 가 종료를 먼저 받으면 사유가 도착하기 전에 카드를 닫는다.
    """
    status = "ok" if (data.get("responseMeta") or {}).get("finalEvent") == "answer" else "failed"
    finished = _event(
        "RUN_FINISHED",
        {
            "runId": runId,
            "status": status,
            "refs": _refIds(data.get("refs") if isinstance(data.get("refs"), list) else []),
            "artifacts": [a for a in data.get("artifacts") or [] if isinstance(a, dict)],
            "responseMeta": _publicResponseMeta(data.get("responseMeta") or {}),
            "suggestedQuestions": _suggestFollowups(data) if status == "ok" else [],
        },
    )
    if status == "ok":
        return [finished]
    reason = str((data.get("responseMeta") or {}).get("failureReason") or "")
    return [_event("RUN_ERROR", {"runId": runId, "message": _publicFailure(reason)}), finished]


def _publicEvents(event: TraceEvent, *, runId: str, messageId: str) -> list[dict[str, str]]:
    kind = event.kind
    data = event.data
    if kind == "graph_node":
        return _graphNodeEvents(data, runId=runId)
    if kind == "plan":
        return _planEvents(data)
    if kind in {"tool_start", "tool_call"}:
        return _toolStartEvents(data, runId=runId, messageId=messageId)
    if kind == "view_spec":
        return _viewSpecEvents(data, runId=runId, messageId=messageId)
    if kind == "tool_result":
        return _toolResultEvents(data, runId=runId, messageId=messageId)
    if kind == "reference":
        return _referenceEvents(data)
    if kind == "verify":
        return _verifyEvents(data)
    if kind == "chunk":
        text = str(data.get("text") or "")
        return [_event("TEXT_MESSAGE_CONTENT", {"messageId": messageId, "delta": text})] if text else []
    if kind == "thinking":
        # 추론(사고) 델타. reasoning 모델(qwen3 등)의 사고 흐름을 답변과 분리 스트림.
        text = str(data.get("text") or "")
        return [_event("THINKING_DELTA", {"messageId": messageId, "delta": text})] if text else []
    if kind == "answer":
        refs = [str(v) for v in data.get("evidenceRefs") or []]
        return [_activity(f"근거 {len(refs)}개로 답변을 작성했습니다.", refs=refs, passLabel=_passLabel(data))]
    if kind == "unable":
        message = str(data.get("message") or "") or _publicFailure(str(data.get("reason") or ""))
        return [_event("RUN_ERROR", {"runId": runId, "message": message})]
    if kind == "done":
        return _doneEvents(data, runId=runId)
    if kind == "error":
        return [_event("RUN_ERROR", {"runId": runId, "message": _publicFailure(str(data.get("error") or ""))})]
    return []


def _kernelKwargs(req: AgentRunRequest) -> dict[str, Any]:
    context = req.workspaceContext or {}
    kwargs: dict[str, Any] = {
        "provider": req.provider,
        "role": req.role,
        "model": req.model,
    }
    # history: 마지막 user message (= 현재 question) 제외, 이전 대화만.
    messages = list(req.messages or [])
    history: list[dict[str, Any]] = []
    last_user_index = -1
    for idx, msg in enumerate(messages):
        if msg.role == "user" and msg.content.strip():
            last_user_index = idx
    for idx, msg in enumerate(messages):
        if idx == last_user_index:
            continue
        if msg.role in {"user", "assistant"} and msg.content:
            history.append({"role": msg.role, "content": msg.content})
    if history:
        kwargs["history"] = history
    company = context.get("company") if isinstance(context, dict) else None
    if isinstance(company, dict):
        hint = company.get("stockCode") or company.get("corpName") or company.get("company")
        if hint:
            kwargs["stockCode"] = hint
    # Dashboard snapshot artifact (Phase 8 — "보면서 질문" bridge).
    # 사용자가 dashboard 에서 "AI 에게 첨부" 누르면 frontend 가 보내는 dict.
    snapshot = context.get("dashboardSnapshot") if isinstance(context, dict) else None
    if isinstance(snapshot, dict):
        kwargs["dashboardSnapshot"] = snapshot
    return {k: v for k, v in kwargs.items() if v is not None}


def _lastUserMessage(req: AgentRunRequest) -> str:
    for message in reversed(req.messages):
        if message.role == "user" and message.content.strip():
            return message.content.strip()
    return ""


def _event(eventType: str, data: dict[str, Any]) -> dict[str, str]:
    if eventType not in _ALLOWED_EVENTS:
        raise ValueError(f"unsupported AG-UI event: {eventType}")
    payload = {"type": eventType, **_publicEventData(data)}
    return {"event": eventType, "data": json.dumps(payload, ensure_ascii=False, default=str)}


def _publicEventData(value):
    if isinstance(value, dict):
        return {key: _publicEventData(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_publicEventData(item) for item in value]
    if isinstance(value, str):
        return (
            value.replace("search_reference", "search reference")
            .replace("read_context", "read context")
            .replace("generated_spec_search", "generated spec search")
            .replace("engine_call", "engine call")
            .replace("run_python", "run python")
            .replace("verify_answer", "verify answer")
        )
    return value


def _suggestFollowups(doneData: dict[str, Any]) -> list[str]:
    """답변 종료 시점 follow-up 추천 — 종목/topic 컨텍스트 있을 때만.

    종목·topic 없는 일반 답변엔 generic 휴리스틱 박지 않는다 (답변과 무관한
    "표·차트로 정리" 같은 옛 fallback 이 어색했음). 향후 LLM 이 답변 끝에
    직접 followup 작성하는 구조로 발전 예정.
    """
    meta = doneData.get("responseMeta") if isinstance(doneData.get("responseMeta"), dict) else {}
    stock = meta.get("stockCode") or meta.get("company") or ""
    if stock:
        return [
            f"{stock}의 수익성·안정성·성장성 축으로 비교해줘",
            f"{stock}의 최근 공시에서 의미 있는 변화는?",
            "같은 산업의 다른 회사와 비교해줘",
        ]
    topic = meta.get("topic") or ""
    if topic:
        return [
            f"{topic} 관련 주요 종목 후보를 추려줘",
            f"{topic} 의 최근 추세는 어떤가?",
            f"{topic} 와 가장 연관 있는 매크로 지표는?",
        ]
    return []


def _activity(
    summary: str,
    *,
    status: str = "done",
    refs: list[str] | None = None,
    passLabel: str | None = None,
) -> dict[str, str]:
    payload: dict[str, Any] = {
        "status": status,
        "summary": summary,
        "refs": refs or [],
    }
    if passLabel:
        payload["passLabel"] = passLabel
    return _event("ACTIVITY_DELTA", payload)


def _passLabel(data: dict[str, Any]) -> str | None:
    """TraceEvent.data 의 pass 키를 SSE 페이로드용 라벨로 정규화. brief → BRIEF."""
    raw = data.get("pass")
    if not raw:
        return None
    return str(raw).upper()


def _viewSpec(
    spec: dict[str, Any],
    *,
    runId: str,
    messageId: str,
    source: str | None = None,
    title: str | None = None,
) -> dict[str, str]:
    """View-spec part — 차트/표/대시보드 같은 시각 답변을 메시지 흐름에 인라인.

    spec 형식: viewSpec.normalizeViewSpec 가 받는 모양 (widgets[]/charts[]/component).
    분석 워크벤치 정체성의 주체. tool/activity 보다 시각적 위계가 높다.
    """
    payload: dict[str, Any] = {
        "runId": runId,
        "messageId": messageId,
        "spec": spec,
    }
    if source:
        payload["source"] = source
    if title:
        payload["title"] = title
    return _event("VIEW_SPEC", payload)


def _toolName(data: dict[str, Any]) -> str:
    return str(data.get("name") or data.get("tool") or "tool")


def _displayTool(tool: str) -> str:
    return _displayName(tool)


def _refIds(refs: list[Any]) -> list[str]:
    out: list[str] = []
    for ref in refs:
        if isinstance(ref, dict) and ref.get("id"):
            out.append(str(ref["id"]))
        elif isinstance(ref, str):
            out.append(ref)
    return out


_RESULT_PREVIEW_CHARS = 4000

# evidence chip preview 용 ref payload preview 한도 (한 ref 당 chars).
_REF_PREVIEW_CHARS = 2000


def _publicRefDetails(refs: Any) -> list[dict[str, Any]]:
    """UI evidence chip 용 ref dict 정제 — id/kind/title/sourceType 통과 + payload 미리보기 절단.

    payload 가 크면 (>_REF_PREVIEW_CHARS) `bodyPreview` 한 키로 절단 + `hasMore: True` 표식.
    UI 는 hasMore 면 `/api/ask/refs/{id}` 로 풀 fetch (v2 endpoint, 미구현 시 미리보기만).
    """
    if not isinstance(refs, list):
        return []
    out: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        rid = ref.get("id")
        if not isinstance(rid, str) or not rid:
            continue
        item: dict[str, Any] = {
            "id": rid,
            "kind": str(ref.get("kind") or ""),
            "title": str(ref.get("title") or ""),
            "source": str(ref.get("source") or ""),
            "sourceType": str(ref.get("sourceType") or "internal"),
        }
        payload = ref.get("payload")
        if isinstance(payload, dict) and payload:
            # body / markdown / text 류 텍스트 키 절단. 그 외는 그대로 통과 (작은 dict 가정).
            preview_payload: dict[str, Any] = {}
            has_more = False
            for k, v in payload.items():
                if isinstance(v, str) and len(v) > _REF_PREVIEW_CHARS:
                    preview_payload[k] = v[:_REF_PREVIEW_CHARS]
                    has_more = True
                else:
                    preview_payload[k] = v
            item["payload"] = preview_payload
            if has_more:
                item["hasMore"] = True
        out.append(item)
    return out


def _publicResultPayload(data: dict[str, Any]) -> dict[str, Any] | None:
    """tool_result 의 핵심 일부를 UI 가 expand 시 보여줄 수 있게 정제.

    inline 표시는 짧게, 너무 길면 UI 가 모달 / "전체 보기" 로 위임.
    UI 는 `markdown` 키를 우선 렌더 — 도구 작성자가 채우거나, dispatch (format_engine_result)
    가 자동 채움. 기존 stdout / stderr / values / tableHead 는 markdown 부재 시 fallback.
    """
    raw = data.get("data") if isinstance(data.get("data"), dict) else {}
    if not raw:
        return None
    out: dict[str, Any] = {}
    # markdown 1 차 표면 — 도구 작성자가 직접 채운 키 우선 통과.
    if isinstance(raw.get("markdown"), str) and raw["markdown"].strip():
        out["markdown"] = raw["markdown"][: _RESULT_PREVIEW_CHARS * 4]
    # RunPython: stdout / stderr / values / table preview / durationMs
    if "stdout" in raw or "stderr" in raw or "result" in raw:
        stdout = str(raw.get("stdout") or "")
        stderr = str(raw.get("stderr") or "")
        if stdout:
            out["stdout"] = stdout[:_RESULT_PREVIEW_CHARS]
            out["stdoutTruncated"] = len(stdout) > _RESULT_PREVIEW_CHARS
        if stderr:
            out["stderr"] = stderr[:_RESULT_PREVIEW_CHARS]
            out["stderrTruncated"] = len(stderr) > _RESULT_PREVIEW_CHARS
        if "durationMs" in raw:
            out["durationMs"] = raw.get("durationMs")
        result = raw.get("result") if isinstance(raw.get("result"), dict) else {}
        if isinstance(result.get("values"), dict):
            out["values"] = result.get("values")
        if isinstance(result.get("table"), list):
            out["tableHead"] = result["table"][:10]
            out["tableRows"] = len(result["table"])
        if "date" in result:
            out["date"] = result.get("date")
    # Read: body preview
    if "body" in raw and "stdout" not in raw:
        body = str(raw.get("body") or "")
        out["body"] = body[:_RESULT_PREVIEW_CHARS]
        out["bodyTruncated"] = len(body) > _RESULT_PREVIEW_CHARS
        if "path" in raw:
            out["path"] = raw.get("path")
    # markdown 부재 + 위 핸드롤 분기 모두 적용 안 됐으면 dispatch 로 자동 변환 시도.
    if not out.get("markdown") and not any(k in out for k in ("stdout", "tableHead", "body", "values")):
        try:
            from dartlab.ai.tools.formatting import formatEngineResult

            md = formatEngineResult(raw)
        except Exception:  # noqa: BLE001 — 마크다운 변환 실패가 도구 결과 흐름을 막지 않게
            md = None
        if md:
            out["markdown"] = md[: _RESULT_PREVIEW_CHARS * 4]
    return out or None


def _publicResponseMeta(meta: dict[str, Any]) -> dict[str, Any]:
    allowed = {"refCount", "verificationOk", "artifactCount", "activityCount", "responseStatus"}
    return {key: meta.get(key) for key in allowed if key in meta}


def _publicGraphState(state: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "currentNode",
        "selectedSkills",
        "evidenceRefs",
        "toolCallCount",
        "finalAnswerSeen",
        "failure",
    }
    return {key: state.get(key) for key in allowed if key in state}


_FAILURE_LABELS = {
    "verification": "근거 검증 실패",
    "direct_answer": "최종 답변 생성 실패",
    "ref_only": "근거 기반 답변 생성 실패",
    "prose_without_finalize": "최종 답변을 생성하지 못했습니다.",
}
_FAILURE_MAX = 200


def _publicFailure(reason: str) -> str:
    """workbench 내부 reason 코드는 라벨링, 그 외 (provider/스택 메시지) 는 원문 보존."""
    text = reason.strip()
    if not text:
        return "최종 답변을 생성하지 못했습니다."
    for needle, label in _FAILURE_LABELS.items():
        if needle in text:
            return label
    return text[:_FAILURE_MAX]
