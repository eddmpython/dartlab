"""AG-UI compatible Agent Gateway for DartLab."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

from dartlab.ai.agent import runRuntimeAgent
from dartlab.ai.contracts import TraceEvent
from dartlab.ai.runtime.contracts import PUBLIC_AGENT_EVENT_KINDS
from dartlab.ai.runtime.conversationPolicy import buildConversationGuide, followUpQuestions
from dartlab.ai.tools.registry import _LEGACY_NAME_MAP, CANONICAL_TOOL_NAMES

from . import agentMetrics
from .models import AgentRunRequest
from .streaming import _syncGenToAsync

logger = logging.getLogger(__name__)


def _displayName(tool: str) -> str:
    """도구 이름을 UI 표시용으로 정규화 — registry _LEGACY_NAME_MAP SSOT 위 wrapping."""
    canonical = _canonicalToolName(tool)
    if canonical in CANONICAL_TOOL_NAMES:
        return canonical
    if tool == "verify":  # Workbench GATE 패스의 별칭 — registry canonical 외 display only.
        return "Verify"
    return str(tool).replace("_", " ")


# UI 가 ToolBlock 카드로 표현할 도구 화이트리스트. registry SSOT 에서 derive — PascalCase canonical
# + snake_case legacy alias 가 동시에 화이트리스트에 들어간다.
_PUBLIC_TOOL_NAMES = set(CANONICAL_TOOL_NAMES) | set(_LEGACY_NAME_MAP.keys()) | {"verify"}

_ALLOWED_EVENTS = set(PUBLIC_AGENT_EVENT_KINDS)


async def streamAgentRun(req: AgentRunRequest) -> AsyncIterator[dict[str, str]]:
    """Stream one DartLab run using the public AG-UI event contract.

    모든 모드는 사용자의 설치형 agent CLI를 사용하며 인증, 모델, transcript는
    해당 CLI가 소유한다. DartLab은 MCP와 분석 capsule만 제공한다.
    """
    question = _lastUserMessage(req)
    runId = uuid.uuid4().hex
    messageId = f"msg-{uuid.uuid4().hex}"
    text_started = False
    terminal_seen = False
    error_sent = False

    kernelKwargs = _kernelKwargs(req)
    conversationGuide = buildConversationGuide(
        question,
        stockCode=str(kernelKwargs.get("stockCode") or "") or None,
    )
    agentMetrics.record("agent-runtime")
    yield _event(
        "STATE_SNAPSHOT",
        {
            "runId": runId,
            "agentId": req.agentId or "dartlab-agent-runtime",
            "status": "running",
            "mode": "agent-runtime",
            "threadId": req.threadId,
        },
    )
    yield _event(
        "STATE_DELTA",
        {
            "runId": runId,
            "status": "running",
            "analysisConversation": conversationGuide,
        },
    )
    runtimeKwargs = {**kernelKwargs, "sessionId": req.threadId} if req.threadId else kernelKwargs
    producer = lambda: runRuntimeAgent(question, **runtimeKwargs)  # noqa: E731

    streamed_delta = False
    try:
        async for internal in _syncGenToAsync(producer):
            if internal.kind == "delta" and str(internal.data.get("text") or ""):
                streamed_delta = True
            for public in _publicEvents(
                internal,
                runId=runId,
                messageId=messageId,
                conversationGuide=conversationGuide,
                streamedDelta=streamed_delta,
            ):
                if public["event"] == "TEXT_MESSAGE_CONTENT" and not text_started:
                    text_started = True
                    yield _event("TEXT_MESSAGE_START", {"messageId": messageId, "role": "assistant"})
                if public["event"] == "RUN_ERROR":
                    if error_sent:
                        continue
                    error_sent = True
                if public["event"] == "RUN_FINISHED":
                    if text_started:
                        yield _event("TEXT_MESSAGE_END", {"messageId": messageId})
                        text_started = False
                    terminal_seen = True
                yield public
        if not terminal_seen:
            if text_started:
                yield _event("TEXT_MESSAGE_END", {"messageId": messageId})
                text_started = False
            if not error_sent:
                error_sent = True
                yield _event(
                    "RUN_ERROR",
                    {
                        "runId": runId,
                        "message": "에이전트 스트림이 완료 이벤트 없이 종료되었습니다.",
                        "code": "stream_interrupted",
                    },
                )
            yield _event(
                "RUN_FINISHED",
                {"runId": runId, "status": "failed", "refs": [], "suggestedQuestions": []},
            )
            terminal_seen = True
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent run failed (runId=%s)", runId)
        if text_started:
            yield _event("TEXT_MESSAGE_END", {"messageId": messageId})
        if not error_sent:
            yield _event(
                "RUN_ERROR",
                {"runId": runId, "message": _publicFailure(str(exc)), "code": "agent_run_failed"},
            )
        if not terminal_seen:
            yield _event(
                "RUN_FINISHED",
                {"runId": runId, "status": "failed", "refs": [], "suggestedQuestions": []},
            )
    finally:
        if not terminal_seen and req.threadId:
            try:
                from dartlab.ai.runtime import getRuntimeEngine

                getRuntimeEngine().cancel(req.threadId)
            except Exception:  # noqa: BLE001
                logger.debug("이미 종료된 agent runtime session 취소 생략", exc_info=True)


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
    return [
        _activity(
            f"분석 경로를 정했습니다{': ' + target if target else ''}",
            refs=[],
            passLabel=_passLabel(data) or "질문 구조화",
        )
    ]


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
    return [
        _activity(
            f"근거 {len(refs)}개를 확인했습니다.",
            refs=_refIds(refs),
            passLabel=_passLabel(data) or "근거 수집",
        )
    ]


def _verifyEvents(data: dict) -> list[dict[str, str]]:
    """검증 결과. 통과가 아니면 다시 검증한다고 알린다."""
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    passLabel = _passLabel(data) or "답변 검산"
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
        "toolCallId": str(data.get("toolCallId") or data.get("id") or tool),
        "toolName": _displayTool(tool),
        "nativeToolName": str(data.get("nativeName") or tool),
        "args": data.get("input") if isinstance(data.get("input"), dict) else {},
        "status": "running",
    }
    passLabel = _passLabel(data) or _analysisStageForTool(tool)
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
    toolCallId = str(data.get("toolCallId") or data.get("id") or tool)
    displayName = _displayTool(tool)
    resultEvent: dict[str, Any] = {
        "runId": runId,
        "messageId": messageId,
        "toolCallId": toolCallId,
        "toolName": displayName,
        "nativeToolName": str(data.get("nativeName") or tool),
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
        "nativeToolName": str(data.get("nativeName") or tool),
        "status": status,
    }
    passLabel = _passLabel(data) or _analysisStageForTool(tool)
    if passLabel:
        resultEvent["passLabel"] = passLabel
        endEvent["passLabel"] = passLabel
    return [_event("TOOL_CALL_RESULT", resultEvent), _event("TOOL_CALL_END", endEvent)]


def _doneEvents(
    data: dict,
    *,
    runId: str,
    conversationGuide: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """실행 종료. 실패면 사유를 먼저 내보내고 종료 이벤트를 뒤에 둔다.

    순서가 뜻을 만든다. UI 가 종료를 먼저 받으면 사유가 도착하기 전에 카드를 닫는다.
    """
    status = "ok" if (data.get("responseMeta") or {}).get("finalEvent") == "answer" else "failed"
    responseMeta = _publicResponseMeta(data.get("responseMeta") or {})
    if conversationGuide:
        responseMeta["analysisConversation"] = dict(conversationGuide)
    finished = _event(
        "RUN_FINISHED",
        {
            "runId": runId,
            "status": status,
            "refs": _refIds(data.get("refs") if isinstance(data.get("refs"), list) else []),
            "candidateRefs": _refIds(data.get("candidateRefs") if isinstance(data.get("candidateRefs"), list) else []),
            "candidateRefDetails": _publicRefDetails(data.get("candidateRefs")),
            "artifacts": [a for a in data.get("artifacts") or [] if isinstance(a, dict)],
            "responseMeta": responseMeta,
            "suggestedQuestions": _suggestFollowups(data, conversationGuide=conversationGuide)
            if status == "ok"
            else [],
        },
    )
    if status == "ok":
        return [finished]
    reason = str((data.get("responseMeta") or {}).get("failureReason") or "")
    return [_event("RUN_ERROR", {"runId": runId, "message": _publicFailure(reason)}), finished]


def _publicEvents(
    event: TraceEvent,
    *,
    runId: str,
    messageId: str,
    conversationGuide: dict[str, Any] | None = None,
    streamedDelta: bool = False,
) -> list[dict[str, str]]:
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
    if kind == "delta":
        # 과정 중계: 모델이 써 내려가는 본문을 실시간으로 흘린다. 최종 `chunk` 는
        # 같은 본문의 완성본이라 그대로 내보내면 화면에 두 번 그려진다. 실시간 delta 를
        # 이미 보냈다면 chunk 는 흘리지 않는다(아래 chunk 분기의 streamedDelta 확인).
        text = str(data.get("text") or "")
        return [_event("TEXT_MESSAGE_CONTENT", {"messageId": messageId, "delta": text})] if text else []
    if kind == "chunk":
        text = str(data.get("text") or "")
        if not text or streamedDelta:
            return []
        return [_event("TEXT_MESSAGE_CONTENT", {"messageId": messageId, "delta": text})]
    if kind == "thinking":
        # 추론(사고) 델타. reasoning 모델(qwen3 등)의 사고 흐름을 답변과 분리 스트림.
        text = str(data.get("text") or "")
        return [_event("THINKING_DELTA", {"messageId": messageId, "delta": text})] if text else []
    if kind == "answer":
        refs = [str(v) for v in data.get("evidenceRefs") or []]
        return [
            _activity(
                f"근거 {len(refs)}개로 답변을 작성했습니다.",
                refs=refs,
                passLabel=_passLabel(data) or "결론",
            )
        ]
    if kind == "unable":
        message = str(data.get("message") or "") or _publicFailure(str(data.get("reason") or ""))
        return [_event("RUN_ERROR", {"runId": runId, "message": message})]
    if kind == "done":
        return _doneEvents(data, runId=runId, conversationGuide=conversationGuide)
    if kind == "error":
        return [_event("RUN_ERROR", {"runId": runId, "message": _publicFailure(str(data.get("error") or ""))})]
    if kind == "runtime_session":
        return [
            _event(
                "STATE_DELTA",
                {
                    "runId": runId,
                    "status": "running",
                    "sessionId": data.get("sessionId"),
                    "runtimeId": data.get("runtimeId"),
                    "resumed": bool(data.get("resumed")),
                },
            )
        ]
    if kind == "runtime_turn":
        return [_activity("질문을 투자 판단 구조로 정리하고 있습니다.", status="running", passLabel="질문 구조화")]
    if kind == "approval_requested":
        return [
            _event(
                "APPROVAL_REQUESTED",
                {
                    "runId": runId,
                    "sessionId": data.get("sessionId"),
                    "turnId": data.get("turnId"),
                    "approvalId": data.get("approvalId"),
                    "request": data.get("request") or {},
                },
            )
        ]
    if kind == "event_gap":
        return [_activity("재연결 구간의 일부 이벤트를 재생할 수 없습니다.", status="error")]
    return []


def _kernelKwargs(req: AgentRunRequest) -> dict[str, Any]:
    context = req.workspaceContext or {}
    kwargs: dict[str, Any] = {
        "runtimeId": req.runtimeId or req.provider,
        "role": req.role,
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
    elif isinstance(context, dict) and context.get("stockCode"):
        kwargs["stockCode"] = context["stockCode"]
    if isinstance(context, dict):
        for sourceKey, targetKey in (
            ("period", "period"),
            ("reportMode", "reportMode"),
            ("include", "include"),
            ("exclude", "exclude"),
        ):
            if context.get(sourceKey) not in (None, "", [], {}):
                kwargs[targetKey] = context[sourceKey]
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


def _suggestFollowups(
    doneData: dict[str, Any],
    *,
    conversationGuide: dict[str, Any] | None = None,
) -> list[str]:
    """답변 종료 시점 follow-up 추천 — 종목/topic 컨텍스트 있을 때만.

    종목·topic 없는 일반 답변엔 generic 휴리스틱 박지 않는다 (답변과 무관한
    "표·차트로 정리" 같은 옛 fallback 이 어색했음). 향후 LLM 이 답변 끝에
    직접 followup 작성하는 구조로 발전 예정.
    """
    if conversationGuide:
        suggested = followUpQuestions(conversationGuide)
        if suggested:
            return suggested

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
    raw = str(data.get("canonicalName") or data.get("name") or data.get("tool") or "tool")
    return _canonicalToolName(raw)


def _canonicalToolName(tool: str) -> str:
    """runtime별 MCP prefix와 legacy alias를 공개 canonical 이름으로 정규화한다."""
    value = str(tool).rsplit("__", 1)[-1].rsplit("/", 1)[-1]
    return _LEGACY_NAME_MAP.get(value, value)


def _displayTool(tool: str) -> str:
    return _displayName(tool)


def _analysisStageForTool(tool: str) -> str:
    """공개 도구 이름을 투자자용 진행 단계로 바꾼다."""
    canonical = _canonicalToolName(tool)
    if canonical in {"ReadSkill", "ReadCapability", "Read"}:
        return "질문 구조화"
    if canonical == "Verify":
        return "답변 검산"
    return "근거 수집"


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
        if ref.get("outcomeId"):
            item["outcomeId"] = str(ref["outcomeId"])
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
        # 다른 미리보기와 달리 절단 사실을 알리지 않아 UI 가 잘린 결과를 완전한 결과로
        # 보여주고 있었다. 같은 규약으로 맞춘다.
        markdownLimit = _RESULT_PREVIEW_CHARS * 4
        out["markdown"] = raw["markdown"][:markdownLimit]
        out["markdownTruncated"] = len(raw["markdown"]) > markdownLimit
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
    allowed = {
        "refCount",
        "verificationOk",
        "artifactCount",
        "activityCount",
        "responseStatus",
        "answerQuality",
        "runtimeCoverage",
        "runtimeId",
        "sessionId",
        "outcomeId",
        "verificationStatus",
        # 검증 뱃지 표시용. verificationStatus(verified/unverified/failed)와 함께
        # UI 가 "근거 N개 인용 · 수치 대조 일치" 또는 미검증 사유를 그린다.
        "evidenceCount",
        "verificationNotes",
        "repairAttempt",
        "failureCode",
        "initialQualityIssues",
    }
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
