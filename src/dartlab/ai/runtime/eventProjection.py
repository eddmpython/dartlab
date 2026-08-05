"""네이티브 CLI 이벤트를 DartLab 의미 이벤트로 투영한다."""

from __future__ import annotations

import uuid
from typing import Any

from .contracts import AgentEvent, EventKind, nowIso

# 도구가 아닌 Codex thread item. 이것들을 도구로 투영하면 화면 타임라인과 도달성 측정이
# 동시에 오염된다. 실측 2026-08-06: `userMessage` 가 도구 호출로 기록돼 "도구 1 회 사용"
# 처럼 보였지만 실제 DartLab 도구 도달은 0 이었다.
_CODEX_NON_TOOL_ITEMS = frozenset(
    {
        "agentMessage",
        "reasoning",
        "userMessage",
        "hookPrompt",
        "contextCompaction",
        "enteredReviewMode",
        "exitedReviewMode",
    }
)
# 실패로 끝난 네이티브 턴 상태.
_FAILED_TURN_STATUSES = frozenset({"failed", "error", "interrupted", "cancelled", "canceled", "refused"})


class EventProjector:
    """세션별 단조 sequence와 안정 event kind를 만든다."""

    def __init__(self, runtimeId: str, sessionId: str):
        self.runtimeId = runtimeId
        self.sessionId = sessionId
        self.sequence = 0
        # 같은 실패를 `error` 알림과 `turn/completed` 가 함께 실어 보내므로 한 턴에 한
        # 번만 올린다. 턴이 바뀌면 비운다. 같은 사유로 두 턴이 연속 실패하는 것은 흔한
        # 일이라 세션 단위로 기억하면 두 번째 턴이 사유를 잃는다.
        self._reportedErrors: set[str] = set()
        self._errorTurnId = ""

    def event(
        self,
        kind: EventKind,
        *,
        turnId: str,
        payload: dict[str, Any] | None = None,
        nativeType: str | None = None,
    ) -> AgentEvent:
        """Sig: event(kind, *, turnId, payload=None, nativeType=None) -> AgentEvent.

        Args: 의미 종류, 턴 ID, 공개 payload, 네이티브 종류다.
        Returns: 다음 sequence의 표준 이벤트다.
        Example: `projector.event("turnStarted", turnId="t")`.
        """
        self.sequence += 1
        return AgentEvent(
            schemaVersion="1.0",
            sessionId=self.sessionId,
            turnId=turnId,
            eventId=uuid.uuid4().hex,
            sequence=self.sequence,
            runtimeId=self.runtimeId,
            kind=kind,
            timestamp=nowIso(),
            payload=payload or {},
            nativeType=nativeType,
        )

    def project(self, message: dict[str, Any], *, turnId: str) -> list[AgentEvent]:
        """Sig: project(message, *, turnId) -> list[AgentEvent].

        Args: 드라이버의 네이티브 JSON 객체와 현재 turnId다.
        Returns: 0개 이상의 표준 이벤트다.
        Example: `events = projector.project(message, turnId="t")`.
        """
        if self.runtimeId == "codex":
            return self._projectCodex(message, turnId=turnId)
        if self.runtimeId == "claude":
            return self._projectClaude(message, turnId=turnId)
        if self.runtimeId == "cline":
            return self._projectAcp(message, turnId=turnId)
        return [self.event("native", turnId=turnId, payload=message, nativeType=_nativeType(message))]

    def _projectCodex(self, message: dict[str, Any], *, turnId: str) -> list[AgentEvent]:
        """Sig: _projectCodex(message, *, turnId) -> list[AgentEvent].

        Args: Codex app-server 메시지와 turnId다.
        Returns: Codex 의미 이벤트다.
        Example: 내부 Codex 드라이버가 호출한다.

        Codex 는 실패를 `error` 알림과 `turn/completed` 의 `turn.error` 두 곳으로 보낸다.
        둘 다 알아보지 못하면 턴이 사유 없이 끝난 것처럼 보인다. 실측 2026-08-06: 사용량
        한도 소진으로 죽은 19 개 세션 전부가 `runtimeError` 없이 조용히 종료됐고 화면에는
        "런타임이 정상 완료되지 않았습니다" 만 남았다.
        """
        nativeType = _nativeType(message)
        params = _dict(message.get("params"))
        mapping: dict[str, EventKind] = {
            "turn/started": "turnStarted",
            "item/agentMessage/delta": "messageDelta",
            "item/reasoning/textDelta": "reasoningDelta",
            # gpt-5 계열은 원문 reasoning 대신 요약본을 흘린다. 이것을 버리면 화면의 사고
            # 과정이 통째로 빈다.
            "item/reasoning/summaryTextDelta": "reasoningDelta",
            "item/started": "toolStarted",
            "item/completed": "toolCompleted",
        }
        if nativeType.endswith("/requestApproval"):
            return [self.event("approvalRequested", turnId=turnId, payload=params, nativeType=nativeType)]
        if nativeType == "error":
            return self._codexErrorEvents(params, turnId=turnId, nativeType=nativeType)
        if nativeType == "turn/completed":
            turn = _dict(params.get("turn"))
            events: list[AgentEvent] = []
            if str(turn.get("status") or "").casefold() in _FAILED_TURN_STATUSES:
                events += self._codexErrorEvents(turn, turnId=turnId, nativeType=nativeType)
            events.append(self.event("turnCompleted", turnId=turnId, payload=params, nativeType=nativeType))
            return events
        kind = mapping.get(nativeType, "native")
        if kind in {"messageDelta", "reasoningDelta"}:
            return [
                self.event(kind, turnId=turnId, payload={"text": str(params.get("delta") or "")}, nativeType=nativeType)
            ]
        if kind in {"toolStarted", "toolCompleted"}:
            item = _dict(params.get("item"))
            if str(item.get("type") or "") in _CODEX_NON_TOOL_ITEMS:
                return []
            return [self.event(kind, turnId=turnId, payload={"item": item}, nativeType=nativeType)]
        return [self.event(kind, turnId=turnId, payload=params, nativeType=nativeType)]

    def _codexErrorEvents(self, source: dict[str, Any], *, turnId: str, nativeType: str) -> list[AgentEvent]:
        """Codex 실패 payload를 사용자가 읽을 수 있는 runtimeError 하나로 만든다.

        재시도 예정(`willRetry`)은 실패가 아니다. 이것을 실패로 올리면 곧 회복될 턴의
        답변이 미전달 처리된다.
        """
        error = _dict(source.get("error"))
        message = str(error.get("message") or "").strip()
        if not message or source.get("willRetry") is True:
            return []
        if turnId != self._errorTurnId:
            self._errorTurnId = turnId
            self._reportedErrors.clear()
        if message in self._reportedErrors:
            return []
        self._reportedErrors.add(message)
        payload = {"error": message, "errorCode": str(error.get("codexErrorInfo") or "") or None}
        return [self.event("runtimeError", turnId=turnId, payload=payload, nativeType=nativeType)]

    def _projectClaude(self, message: dict[str, Any], *, turnId: str) -> list[AgentEvent]:
        """Sig: _projectClaude(message, *, turnId) -> list[AgentEvent].

        Args: Claude stream-json 메시지와 turnId다.
        Returns: Claude 의미 이벤트다.
        Example: 내부 Claude 드라이버가 호출한다.
        """
        nativeType = _nativeType(message)
        if nativeType == "system" and message.get("subtype") == "init":
            return [
                self.event(
                    "native",
                    turnId=turnId,
                    payload={"sessionId": message.get("session_id")},
                    nativeType="system/init",
                )
            ]
        if nativeType == "stream_event":
            streamEvent = _dict(message.get("event"))
            streamType = str(streamEvent.get("type") or "")
            delta = _dict(streamEvent.get("delta"))
            if streamType == "content_block_delta" and delta.get("type") == "text_delta":
                return [
                    self.event(
                        "messageDelta",
                        turnId=turnId,
                        payload={"text": str(delta.get("text") or "")},
                        nativeType=streamType,
                    )
                ]
            if streamType == "content_block_delta" and delta.get("type") == "thinking_delta":
                return [
                    self.event(
                        "reasoningDelta",
                        turnId=turnId,
                        payload={"text": str(delta.get("thinking") or "")},
                        nativeType=streamType,
                    )
                ]
        if nativeType == "assistant":
            output: list[AgentEvent] = []
            body = _dict(message.get("message"))
            for block in body.get("content") or []:
                item = _dict(block)
                if item.get("type") == "tool_use":
                    output.append(
                        self.event("toolStarted", turnId=turnId, payload={"item": item}, nativeType="tool_use")
                    )
            return output
        if nativeType == "user":
            output = []
            body = _dict(message.get("message"))
            for block in body.get("content") or []:
                item = _dict(block)
                if item.get("type") == "tool_result":
                    output.append(
                        self.event("toolCompleted", turnId=turnId, payload={"item": item}, nativeType="tool_result")
                    )
            return output
        if nativeType == "result":
            return [
                self.event(
                    "turnCompleted",
                    turnId=turnId,
                    payload={"status": message.get("subtype") or "completed"},
                    nativeType=nativeType,
                )
            ]
        return [self.event("native", turnId=turnId, payload=message, nativeType=nativeType)]

    def _projectAcp(self, message: dict[str, Any], *, turnId: str) -> list[AgentEvent]:
        """Sig: _projectAcp(message, *, turnId) -> list[AgentEvent].

        Args: ACP v1 메시지와 turnId다.
        Returns: ACP 의미 이벤트다.
        Example: 내부 ACP 드라이버가 호출한다.
        """
        nativeType = _nativeType(message)
        params = _dict(message.get("params"))
        update = _dict(params.get("update"))
        updateType = str(update.get("sessionUpdate") or update.get("type") or "")
        mapping: dict[str, EventKind] = {
            "agent_message_chunk": "messageDelta",
            "agent_thought_chunk": "reasoningDelta",
            "tool_call": "toolStarted",
            "tool_call_update": "toolCompleted",
        }
        if nativeType == "session/update" and updateType in mapping:
            kind = mapping[updateType]
            content = _dict(update.get("content"))
            payload = (
                {"text": str(content.get("text") or "")}
                if kind in {"messageDelta", "reasoningDelta"}
                else {"item": update}
            )
            return [self.event(kind, turnId=turnId, payload=payload, nativeType=updateType)]
        if nativeType in {"session/request_permission", "session/requestPermission"}:
            return [self.event("approvalRequested", turnId=turnId, payload=params, nativeType=nativeType)]
        return [self.event("native", turnId=turnId, payload=message, nativeType=nativeType)]


def _dict(value: Any) -> dict[str, Any]:
    """Sig: _dict(value) -> dict[str, Any].

    Args: 임의 값을 받는다.
    Returns: dict면 그대로, 아니면 빈 dict다.
    Example: `_dict(None) == {}`.
    """
    return value if isinstance(value, dict) else {}


def _nativeType(message: dict[str, Any]) -> str:
    """Sig: _nativeType(message) -> str.

    Args: 네이티브 JSON 메시지다.
    Returns: method 또는 type 식별자다.
    Example: `_nativeType({"method": "turn/started"})`.
    """
    return str(message.get("method") or message.get("type") or "native")
