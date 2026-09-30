"""Claude Code stream-json 드라이버."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..contracts import AgentEvent, ProcessSpec, RuntimeDescriptor
from ..eventProjection import EventProjector
from ..processSupervisor import ProcessClosedError, ProcessSupervisor
from ..sessionTools import callSessionTool, sessionToolSpecs
from .base import DriverHandle, remainingTurnSeconds, runtimeLaunchArgv, runtimeTurnTimeoutSeconds

# SDK 제어 채널로 제공하는 read-only DartLab 도구만 사용한다. --tools ""는
# 내장 도구를 비우고 --strict-mcp-config는 전역 서버 설정의 유입을 막는다.
# allowedTools만으로 내장 실행을 막지 못했던 기존 실측에 따라 deny 목록도 유지한다.
# SDK 내부 요청은 MCP 형식이지만 별도 MCP 서버나 사용자 전역 설정은 필요 없다.
_CLAUDE_DENIED_BUILTINS = (
    "Task",
    "Artifact",
    "Bash",
    "BashOutput",
    "KillShell",
    "CronCreate",
    "CronDelete",
    "CronList",
    "DesignSync",
    "Edit",
    "EnterWorktree",
    "ExitWorktree",
    "Glob",
    "Grep",
    "Monitor",
    "NotebookEdit",
    "PowerShell",
    "PushNotification",
    "Read",
    "RemoteTrigger",
    "ReportFindings",
    "ScheduleWakeup",
    "SendMessage",
    "Skill",
    "TaskOutput",
    "TaskStop",
    "TodoWrite",
    "WebFetch",
    "WebSearch",
    "Workflow",
    "Write",
)


def _claudeToolArgs() -> tuple[str, ...]:
    """CLI의 SDK 도구 채널을 연결하고 내장 실행 및 외부 MCP 서버를 차단한다."""
    allowed = ",".join(f"mcp__dartlab__{spec['name']}" for spec in sessionToolSpecs())
    denied = ",".join(_CLAUDE_DENIED_BUILTINS)
    return (
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        json.dumps({"mcpServers": {"dartlab": {"type": "sdk", "name": "dartlab"}}}),
        "--restricted",
        "--disable-slash-commands",
        "--permission-mode",
        "dontAsk",
        "--allowedTools",
        allowed,
        "--disallowedTools",
        denied,
    )


class ClaudeStreamJsonDriver:
    """Claude CLI가 소유한 세션을 턴별 stream-json 프로세스로 연결한다."""

    def open(
        self,
        descriptor: RuntimeDescriptor,
        executable: str,
        sessionId: str,
        cwd: Path,
        nativeSessionId: str | None = None,
        instructions: str = "",
    ) -> DriverHandle:
        """Sig: open(descriptor, executable, sessionId, cwd, nativeSessionId=None) -> DriverHandle.

        Args: 런타임 설명, 실행 파일, DartLab 세션 ID, 작업공간이다.
        Returns: 아직 모델 호출을 시작하지 않은 세션 handle이다.
        Example: 엔진의 `openSession`에서 호출한다.
        """
        return DriverHandle(
            descriptor=descriptor,
            executable=executable,
            sessionId=sessionId,
            nativeSessionId=nativeSessionId or str(uuid.uuid4()),
            cwd=cwd,
            projector=EventProjector(descriptor.runtimeId, sessionId),
            metadata={"hasRun": bool(nativeSessionId)},
        )

    def streamTurn(self, handle: DriverHandle, question: str, *, instructions: str) -> Iterator[AgentEvent]:
        """Sig: streamTurn(handle, question, *, instructions) -> Iterator[AgentEvent].

        Args: handle, 질문, 분석 캡슐이다.
        Returns: stream-json을 실시간 투영하는 iterator다.
        Raises: RuntimeError if another turn is active.
        Example: `driver.streamTurn(handle, "질문", instructions=capsule)`.
        """
        if handle.activeTurnId is not None:
            raise RuntimeError("세션에 이미 활성 턴이 있습니다")
        turnId = uuid.uuid4().hex
        handle.activeTurnId = turnId
        hasRun = bool(handle.metadata.get("hasRun"))
        sessionArgs = ("--resume", handle.nativeSessionId) if hasRun else ("--session-id", handle.nativeSessionId)
        argv = (
            *runtimeLaunchArgv(handle.descriptor, handle.executable),
            "--verbose",
            "--input-format",
            "stream-json",
            *_claudeToolArgs(),
            "--append-system-prompt",
            instructions,
            *sessionArgs,
        )
        supervisor = ProcessSupervisor(ProcessSpec(argv, handle.cwd))
        handle.supervisor = supervisor
        supervisor.start()
        initializeId = uuid.uuid4().hex
        supervisor.sendJson(
            {
                "type": "control_request",
                "request_id": initializeId,
                "request": {"subtype": "initialize", "hooks": None},
            }
        )
        completed = False
        timeoutSeconds = runtimeTurnTimeoutSeconds()
        deadline = time.monotonic() + timeoutSeconds
        try:
            yield handle.projector.event("turnStarted", turnId=turnId)
            while True:
                try:
                    message = supervisor.readJson(timeout=remainingTurnSeconds(deadline, timeoutSeconds))
                except TimeoutError as exc:
                    self.cancel(handle)
                    raise TimeoutError(f"에이전트 턴이 {timeoutSeconds:g}초 제한을 초과했습니다") from exc
                except ProcessClosedError:
                    break
                if (
                    message.get("type") == "control_response"
                    and message.get("response", {}).get("request_id") == initializeId
                ):
                    response = message["response"]
                    if response.get("subtype") == "error":
                        raise RuntimeError(str(response.get("error") or "Claude initialization failed"))
                    supervisor.sendJson(
                        {
                            "type": "user",
                            "message": {"role": "user", "content": question},
                            "parent_tool_use_id": None,
                            "session_id": handle.nativeSessionId,
                        }
                    )
                    continue
                if message.get("type") == "control_request":
                    yield from self._hostRequest(handle, message, turnId)
                    continue
                for event in handle.projector.project(message, turnId=turnId):
                    if event.kind not in {"toolStarted", "toolCompleted"}:
                        yield event
                if message.get("type") == "result":
                    nativeId = message.get("session_id")
                    if nativeId:
                        handle.nativeSessionId = str(nativeId)
                    handle.metadata["hasRun"] = True
                    completed = True
                    break
            if not completed:
                yield handle.projector.event(
                    "runtimeError",
                    turnId=turnId,
                    payload={"error": supervisor.stderrText() or "Claude stream ended without a result"},
                )
        finally:
            supervisor.stop()
            handle.supervisor = None
            handle.activeTurnId = None

    def _hostRequest(self, handle: DriverHandle, message: dict[str, Any], turnId: str) -> Iterator[AgentEvent]:
        """별도 서버 없이 CLI의 SDK 도구 제어 요청에 응답한다."""
        request = message.get("request") or {}
        rpc = request.get("message") or {}
        params = rpc.get("params") or {}
        method = rpc.get("method")
        if request.get("subtype") != "mcp_message" or request.get("server_name") != "dartlab":
            response = {
                "subtype": "error",
                "request_id": message.get("request_id"),
                "error": "unsupported host request",
            }
        else:
            if method == "initialize":
                result = {
                    "protocolVersion": params.get("protocolVersion") or "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "dartlab", "version": "1"},
                }
            elif method == "tools/list":
                result = {"tools": sessionToolSpecs()}
            elif method == "tools/call":
                toolResult = yield from callSessionTool(
                    handle.projector,
                    turnId,
                    str(message.get("request_id") or uuid.uuid4().hex),
                    str(params.get("name") or ""),
                    params.get("arguments"),
                )
                result = {
                    "content": [{"type": "text", "text": json.dumps(toolResult, ensure_ascii=False, default=str)}],
                    "isError": not toolResult.get("ok"),
                }
            elif "id" not in rpc:
                result = {}
            else:
                result = None
            answer = (
                {"result": result} if result is not None else {"error": {"code": -32601, "message": "unknown method"}}
            )
            response = {
                "subtype": "success",
                "request_id": message.get("request_id"),
                "response": {"mcp_response": {"jsonrpc": "2.0", "id": rpc.get("id"), **answer}},
            }
        if handle.supervisor:
            handle.supervisor.sendJson({"type": "control_response", "response": response})

    def cancel(self, handle: DriverHandle) -> None:
        """Sig: cancel(handle) -> None.

        Args: 실행 중인 handle이다.
        Returns: None.
        Example: `driver.cancel(handle)`.
        """
        if handle.supervisor:
            handle.supervisor.stop()

    def approve(self, handle: DriverHandle, approvalId: str, *, allow: bool) -> None:
        """Sig: approve(handle, approvalId, *, allow) -> None.

        Args: handle, approvalId, 허용 여부다.
        Returns: None.
        Raises: NotImplementedError because print mode owns its permission UI.
        Example: 이 드라이버는 호출하지 않는다.
        """
        raise NotImplementedError("Claude print mode approval은 CLI permission mode가 관리합니다")

    def close(self, handle: DriverHandle) -> None:
        """Sig: close(handle) -> None.

        Args: 닫을 handle이다.
        Returns: None.
        Example: `driver.close(handle)`.
        """
        if handle.supervisor:
            handle.supervisor.stop()

    def models(self, handle: DriverHandle) -> list[dict[str, Any]]:
        """Sig: models(handle) -> list[dict[str, Any]].

        Args: Claude handle이다.
        Returns: 빈 목록이다. 모델 선택은 CLI 계정 설정이 소유한다.
        Example: `driver.models(handle) == []`.
        """
        return []
