"""Claude Code stream-json 드라이버."""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..contracts import AgentEvent, ProcessSpec, RuntimeDescriptor
from ..eventProjection import EventProjector
from ..mcpBootstrap import claudeReadOnlyMcpTools
from ..processSupervisor import ProcessClosedError, ProcessSupervisor
from .base import DriverHandle, remainingTurnSeconds, runtimeLaunchArgv, runtimeTurnTimeoutSeconds

# 세션이 노출하는 내장 도구 전수(2026-08-04 init tools 실측)에서, 로컬 실행·파일 변조·
# 외부 부작용·하위 에이전트 스폰이 가능한 것을 차단한다. 중개 세션은 DartLab MCP 근거
# 도구만 써야 한다. 실측: allowedTools 만으로는 못 막는다. dontAsk 는 "허용 외 거절" 이
# 아니라 "묻지 않고 실행" 이라, ReadSkill 만 허용해도 모델이 Bash·PowerShell 을 프롬프트
# 없이 실행했다(배터리 세션에서 echo PWNED 출력 재현). disallowedTools 로 완전 차단된다.
#
# ToolSearch 와 MCP 리소스 3종은 차단하지 않는다: DartLab MCP 도구는 세션에 deferred 로
# 실려서 ToolSearch 가 스키마 로드 관문이다(배터리 8/8 세션이 ToolSearch 를 첫 도구로 사용).
# 이들을 막으면 모델이 dartlab 도구에 아예 접근하지 못해 분석이 불가능해진다(실측: 차단 시
# dartlab 도구 사용 0, 답변 실패). 셋 다 로컬 실행이 아니라 도구·리소스 발견 표면이라
# 보안 위험이 없다.
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
    """읽기 전용 DartLab MCP 도구만 노출하고 내장 실행 도구를 차단한다.

    `--tools` 는 쓰지 않는다. 실측(2026-08-04): spawn 시점에 MCP 서버가 `pending` 이라
    MCP 도구명이 아직 존재하지 않는데 `--tools` 가 그 시점 집합을 하드 제한해 세션이
    도구 0개로 시작했고(init tools []), 이후 MCP 가 붙어도 못 들어와 모델이 근거 도구
    없이 기억으로 답했다.

    허용은 `--allowedTools`(read-only MCP), 차단은 `--disallowedTools`(내장 실행 도구)로
    나눈다. `dontAsk` 는 허용 목록 밖 도구를 거절하지 않고 무프롬프트 실행하므로,
    `--allowedTools` 만으로는 Bash/PowerShell/파일 쓰기가 뚫린다. 차단은 disallow 가
    소유한다. 실측: disallow 적용 시 "이 세션에는 Bash 도구가 없다" 로 완전 차단.
    """
    allowed = ",".join(claudeReadOnlyMcpTools())
    denied = ",".join(_CLAUDE_DENIED_BUILTINS)
    return (
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
            *_claudeToolArgs(),
            "--append-system-prompt",
            instructions,
            *sessionArgs,
            question,
        )
        supervisor = ProcessSupervisor(ProcessSpec(argv, handle.cwd))
        handle.supervisor = supervisor
        supervisor.start()
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
                for event in handle.projector.project(message, turnId=turnId):
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
