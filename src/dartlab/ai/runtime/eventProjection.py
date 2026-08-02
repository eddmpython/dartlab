"""네이티브 CLI 이벤트를 DartLab 의미 이벤트로 투영한다."""

from __future__ import annotations

import uuid
from typing import Any

from .contracts import AgentEvent, EventKind, nowIso


class EventProjector:
    """세션별 단조 sequence와 안정 event kind를 만든다."""

    def __init__(self, runtimeId: str, sessionId: str):
        self.runtimeId = runtimeId
        self.sessionId = sessionId
        self.sequence = 0

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
        """
        nativeType = _nativeType(message)
        params = _dict(message.get("params"))
        mapping: dict[str, EventKind] = {
            "turn/started": "turnStarted",
            "item/agentMessage/delta": "messageDelta",
            "item/reasoning/textDelta": "reasoningDelta",
            "item/started": "toolStarted",
            "item/completed": "toolCompleted",
            "turn/completed": "turnCompleted",
        }
        if nativeType.endswith("/requestApproval"):
            return [self.event("approvalRequested", turnId=turnId, payload=params, nativeType=nativeType)]
        kind = mapping.get(nativeType, "native")
        if kind == "messageDelta":
            return [
                self.event(kind, turnId=turnId, payload={"text": str(params.get("delta") or "")}, nativeType=nativeType)
            ]
        if kind == "reasoningDelta":
            return [
                self.event(kind, turnId=turnId, payload={"text": str(params.get("delta") or "")}, nativeType=nativeType)
            ]
        if kind in {"toolStarted", "toolCompleted"}:
            item = _dict(params.get("item"))
            itemType = str(item.get("type") or "")
            if itemType in {"agentMessage", "reasoning"}:
                return []
            return [self.event(kind, turnId=turnId, payload={"item": item}, nativeType=nativeType)]
        return [self.event(kind, turnId=turnId, payload=params, nativeType=nativeType)]

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
