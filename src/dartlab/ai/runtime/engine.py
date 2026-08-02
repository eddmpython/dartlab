"""DartLab 설치형 에이전트 런타임의 단일 진실 원천."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
from collections import OrderedDict
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any

from dartlab.productOutcome import advanceOutcome, registerOutcomeEvidence, startOutcome

from .analysisCapsule import buildAnalysisCapsule, buildTurnQuestion
from .answerQuality import evaluateAnswerQuality
from .contracts import AgentEvent, RuntimeSession, nowIso
from .discovery import probeAllRuntimes, probeRuntime
from .drivers import AcpDriver, ClaudeStreamJsonDriver, CodexAppServerDriver
from .drivers.base import AgentRuntimeDriver
from .eventBuffer import EventBuffer
from .evidenceStore import EvidenceStore
from .mcpBootstrap import probeMcpConnection
from .registry import loadRuntimeRegistry
from .sessionManager import ManagedSession, SessionManager
from .sessionStore import SessionStore

logger = logging.getLogger(__name__)

_GROUNDING_TOOL_NAMES = frozenset(
    {
        "EngineCall",
        "InspectDataset",
        "RunPython",
        "PeerCompareN",
        "DCFValuation",
        "CompileFinancialDashboard",
        "RegressionForecast",
        "SensitivityAnalysis",
        "CreditScorecard",
        "ScenarioCompareN",
        "ScenarioOverlay",
    }
)


class RuntimeUnavailableError(RuntimeError):
    """사용 가능한 설치형 에이전트 CLI가 없을 때 발생한다."""


@dataclass
class _OutcomeTracker:
    """한 runtime turn의 content-free 결과 전이만 추적한다."""

    outcomeId: str | None
    question: str
    scoped: bool = False
    grounded: bool = False
    answerText: str = ""
    completed: bool = False
    completionSucceeded: bool = False
    failed: bool = False
    registeredRefIds: set[str] = field(default_factory=set)
    registeredRefs: dict[str, dict[str, Any]] = field(default_factory=dict)
    toolNames: dict[str, str] = field(default_factory=dict)

    @classmethod
    def start(cls, question: str) -> _OutcomeTracker:
        """결과 원장 오류가 실제 에이전트 턴을 막지 않는 tracker를 만든다."""
        try:
            return cls(startOutcome(feature="ask").outcomeId, question)
        except Exception:  # noqa: BLE001
            logger.exception("product outcome 시작 기록 실패")
            return cls(None, question)

    def enrich(self, event: AgentEvent) -> dict[str, Any]:
        """tool 상관관계와 evidence receipt를 반영한 공개 payload를 만든다."""
        payload = dict(event.payload)
        toolId = _toolCallId(payload)
        if event.kind == "toolStarted":
            toolName = _toolName(payload)
            if toolId and toolName:
                self.toolNames[toolId] = toolName
        elif event.kind == "toolCompleted":
            self._groundToolResult(payload, toolId=toolId)
        if self.outcomeId:
            payload["outcomeId"] = self.outcomeId
        return payload

    def _groundToolResult(self, payload: dict[str, Any], *, toolId: str) -> None:
        """허용된 grounding tool의 정형 ref만 원장에 등록한다."""
        toolName = _toolName(payload) or self.toolNames.get(toolId, "")
        if toolName:
            payload["toolName"] = toolName
        refDetails = _evidenceDetails(payload)
        refIds = [str(item["id"]) for item in refDetails]
        if not self._canGround(toolName, refIds, payload):
            return
        try:
            if not self.scoped:
                advanceOutcome(str(self.outcomeId), "scoped")
                self.scoped = True
            if not self.grounded:
                advanceOutcome(str(self.outcomeId), "grounded")
                self.grounded = True
            registerOutcomeEvidence(str(self.outcomeId), refIds)
            self.registeredRefIds.update(refIds)
            self.registeredRefs.update({str(item["id"]): dict(item) for item in refDetails})
            payload["evidenceRefs"] = refIds
            payload["refDetails"] = [{**item, "outcomeId": self.outcomeId} for item in refDetails]
        except Exception:  # noqa: BLE001
            logger.exception("product outcome 근거 기록 실패")

    def _canGround(self, toolName: str, refIds: list[str], payload: dict[str, Any]) -> bool:
        """현재 completion이 실제 DartLab grounding receipt인지 판정한다."""
        return bool(
            self.outcomeId
            and _canonicalToolName(toolName) in _GROUNDING_TOOL_NAMES
            and refIds
            and not _toolFailed(payload)
        )

    def observe(self, event: AgentEvent) -> None:
        """전달, 완료, 실패 표식만 누적한다."""
        if event.kind == "messageDelta" and event.payload.get("text"):
            self.answerText += str(event.payload["text"])
        elif event.kind == "turnCompleted":
            self.completed = True
            self.completionSucceeded = _turnCompletedSuccessfully(event.payload)
        elif event.kind == "runtimeError":
            self.failed = True

    def finalize(self) -> None:
        """근거와 답변이 모두 완주한 턴만 delivered로 전진시킨다."""
        if not (
            self.outcomeId
            and self.grounded
            and self.answerText.strip()
            and self.completed
            and self.completionSucceeded
            and self.registeredRefIds
            and self._qualityPassed()
            and not self.failed
        ):
            return
        try:
            advanceOutcome(self.outcomeId, "delivered")
        except Exception:  # noqa: BLE001
            logger.exception("product outcome 전달 기록 실패")

    def _qualityPassed(self) -> bool:
        """질문 유형별 evidence와 값·시점 binding이 모두 통과했는지 확인한다."""
        report = evaluateAnswerQuality(
            self.question,
            self.answerText,
            list(self.registeredRefs.values()),
            completionSucceeded=self.completed and self.completionSucceeded,
            failed=self.failed,
        )
        return report.passed


def _runtimeStorePath() -> Path:
    """Sig: _runtimeStorePath() -> Path.

    Args: 없음.
    Returns: 런타임 세션 매핑 DB 경로다.
    Example: `path = _runtimeStorePath()`.
    """
    configured = os.environ.get("DARTLAB_RUNTIME_DB")
    return Path(configured) if configured else Path.home() / ".dartlab" / "agentRuntime.sqlite3"


class AgentRuntimeEngine:
    """발견, 세션, 드라이버, 이벤트, 결과 지표를 한 경계에서 조정한다.

    Capabilities: CLI 자동 발견, 세션 재개, 턴 스트림, 승인, 취소, 재생을 제공한다.
    Args: sessionStore와 sessionManager는 테스트에서 대체할 수 있다.
    Returns: 공개 메서드가 RuntimeSession, AgentEvent, 상태 dict를 반환한다.
    Example: `engine.stream("질문")`.
    Guide: AI 역할은 모델을 소유하지 않고 사용자의 설치형 에이전트를 DartLab MCP에 연결하는 것이다.
    SeeAlso: `runtime.drivers`, `runtime.mcpBootstrap`.
    Requires: 지원 런타임 중 하나가 로컬 PATH에 설치되어 있어야 한다.
    AIContext: provider 키, OAuth 토큰, transcript를 DartLab이 복제하지 않는다.
    LLM Specifications: AntiPatterns=direct model SDK and fixed graph;
        OutputSchema=AgentEvent v1; Prerequisites=local CLI; Freshness=15s probe;
        Dataflow=CLI native to semantic event; TargetMarkets=all.
    """

    def __init__(
        self,
        sessionStore: SessionStore | None = None,
        sessionManager: SessionManager | None = None,
        evidenceStore: EvidenceStore | None = None,
    ):
        self.registry = loadRuntimeRegistry()
        self.sessionStore = sessionStore or SessionStore(_runtimeStorePath())
        self.sessionManager = sessionManager or SessionManager()
        self.evidenceStore = evidenceStore or EvidenceStore(self.sessionStore.path)
        self.drivers: dict[str, AgentRuntimeDriver] = {
            "codexAppServer": CodexAppServerDriver(),
            "claudeStreamJson": ClaudeStreamJsonDriver(),
            "acp": AcpDriver(),
        }
        self._evidenceJournal: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()
        self._evidenceLock = RLock()

    def status(self, *, refresh: bool = False) -> dict[str, Any]:
        """Sig: status(*, refresh=False) -> dict[str, Any].

        Args: refresh는 probe 캐시 무시 여부다.
        Returns: 설치 상태, MCP 상태, hot session 목록이다.
        Example: `engine.status(refresh=True)`.
        """
        runtimes = []
        for probe in probeAllRuntimes(refresh=refresh):
            descriptor = self.registry[probe.runtimeId]
            mcp = (
                probeMcpConnection(probe.runtimeId, refresh=refresh) if probe.state == "ready" else {"connected": False}
            )
            groundedReady = probe.state == "ready" and descriptor.embeddedGrounding and bool(mcp.get("connected"))
            if not descriptor.embeddedGrounding:
                blockingReason = "현재 CLI 프로토콜이 DartLab 근거 도구를 세션에 노출하지 않습니다"
                recommendedAction = "공식 프로토콜 지원을 기다리거나 다른 런타임을 선택하세요"
            elif probe.state != "ready":
                blockingReason = "CLI가 설치되지 않았거나 실행할 수 없습니다"
                recommendedAction = "검증된 설치 계획을 확인하세요"
            elif not mcp.get("connected"):
                blockingReason = "DartLab MCP 연결이 확인되지 않았습니다"
                recommendedAction = "검증된 MCP 연결 계획을 확인하세요"
            else:
                blockingReason = None
                recommendedAction = None
            runtimes.append(
                {
                    **descriptor.toDict(),
                    **probe.toDict(),
                    "mcp": mcp,
                    "groundedReady": groundedReady,
                    "canInstall": descriptor.embeddedGrounding and probe.state != "ready",
                    "canConnect": descriptor.embeddedGrounding and probe.state == "ready" and not mcp.get("connected"),
                    "blockingReason": blockingReason,
                    "recommendedAction": recommendedAction,
                }
            )
        return {"runtimes": runtimes, "sessions": self.sessionManager.status()}

    def selectRuntime(self, preferredRuntimeId: str | None = None) -> str:
        """Sig: selectRuntime(preferredRuntimeId=None) -> str.

        Args: preferredRuntimeId는 사용자가 고른 런타임이다.
        Returns: ready 상태의 runtimeId다.
        Raises: RuntimeUnavailableError if none is ready.
        Example: `runtimeId = engine.selectRuntime()`.
        """
        if preferredRuntimeId:
            if preferredRuntimeId not in self.registry:
                raise KeyError(preferredRuntimeId)
            if probeRuntime(self.registry[preferredRuntimeId]).state != "ready":
                raise RuntimeUnavailableError(f"{preferredRuntimeId} CLI를 사용할 수 없습니다")
            if not self.registry[preferredRuntimeId].embeddedGrounding:
                raise RuntimeUnavailableError(
                    f"{preferredRuntimeId}의 현재 ACP 구현은 embedded DartLab MCP를 노출하지 않습니다"
                )
            if not probeMcpConnection(preferredRuntimeId).get("connected"):
                raise RuntimeUnavailableError(
                    f"{preferredRuntimeId}에 DartLab MCP가 연결되지 않았습니다. "
                    f"`dartlab agent connect {preferredRuntimeId}`로 승인 계획을 확인하세요"
                )
            return preferredRuntimeId
        for runtimeId, descriptor in self.registry.items():
            if (
                descriptor.embeddedGrounding
                and probeRuntime(descriptor).state == "ready"
                and probeMcpConnection(runtimeId).get("connected")
            ):
                return runtimeId
        raise RuntimeUnavailableError(
            "DartLab MCP까지 준비된 로컬 에이전트를 찾지 못했습니다. "
            "`dartlab agent status --refresh`에서 설치와 연결 상태를 확인하세요"
        )

    def openSession(
        self,
        *,
        runtimeId: str | None = None,
        sessionId: str | None = None,
        cwd: Path | None = None,
    ) -> RuntimeSession:
        """Sig: openSession(*, runtimeId=None, sessionId=None, cwd=None) -> RuntimeSession.

        Args: 선택 런타임, 재개 ID, 작업공간이다.
        Returns: 열렸거나 재개된 세션 매핑이다.
        Raises: RuntimeUnavailableError if the selected CLI is unavailable.
        Example: `session = engine.openSession(runtimeId="cline")`.
        """
        resolvedSessionId = sessionId or uuid.uuid4().hex
        hot = self.sessionManager.get(resolvedSessionId)
        if hot:
            if runtimeId and runtimeId != hot.handle.descriptor.runtimeId:
                raise ValueError("기존 세션의 런타임은 변경할 수 없습니다")
            if cwd and cwd.resolve() != hot.handle.cwd.resolve():
                raise ValueError("기존 세션의 작업공간은 변경할 수 없습니다")
            storedHot = self.sessionStore.get(resolvedSessionId)
            return RuntimeSession(
                resolvedSessionId,
                hot.handle.descriptor.runtimeId,
                hot.handle.nativeSessionId,
                str(hot.handle.cwd),
                storedHot.createdAt if storedHot else nowIso(),
                nowIso(),
            )
        existing = self.sessionStore.get(resolvedSessionId)
        if existing:
            if runtimeId and runtimeId != existing.runtimeId:
                raise ValueError("기존 세션의 런타임은 변경할 수 없습니다")
            storedCwd = Path(existing.cwd).resolve()
            if cwd and cwd.resolve() != storedCwd:
                raise ValueError("기존 세션의 작업공간은 변경할 수 없습니다")
            runtimeId = existing.runtimeId
            resolvedCwd = storedCwd
        else:
            resolvedCwd = (cwd or Path.cwd()).resolve()
        resolvedRuntimeId = self.selectRuntime(runtimeId)
        descriptor = self.registry[resolvedRuntimeId]
        probe = probeRuntime(descriptor)
        if probe.executable is None:
            raise RuntimeUnavailableError(f"{resolvedRuntimeId} 실행 파일을 찾지 못했습니다")
        driver = self.drivers[descriptor.driver]
        instructions = buildAnalysisCapsule(cwd=resolvedCwd, mcpConnected=True)
        handle = driver.open(
            descriptor,
            probe.executable,
            resolvedSessionId,
            resolvedCwd,
            existing.nativeSessionId if existing else None,
            instructions=instructions,
        )
        managed = ManagedSession(driver, handle, EventBuffer())
        self.sessionManager.put(resolvedSessionId, managed)
        session = RuntimeSession(
            resolvedSessionId,
            resolvedRuntimeId,
            handle.nativeSessionId,
            str(resolvedCwd),
            existing.createdAt if existing else nowIso(),
            nowIso(),
        )
        return self.sessionStore.save(session)

    def _managed(self, sessionId: str) -> ManagedSession:
        """Sig: _managed(sessionId) -> ManagedSession.

        Args: DartLab 세션 ID다.
        Returns: hot session이며 필요하면 저장 매핑에서 재개한다.
        Raises: KeyError if the session does not exist.
        Example: `managed = engine._managed(sessionId)`.
        """
        managed = self.sessionManager.get(sessionId)
        if managed:
            return managed
        stored = self.sessionStore.get(sessionId)
        if stored is None:
            raise KeyError(sessionId)
        self.openSession(runtimeId=stored.runtimeId, sessionId=sessionId, cwd=Path(stored.cwd))
        resumed = self.sessionManager.get(sessionId)
        if resumed is None:
            raise RuntimeError("세션을 재개하지 못했습니다")
        return resumed

    def streamTurn(
        self,
        sessionId: str,
        question: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> Iterator[AgentEvent]:
        """Sig: streamTurn(sessionId, question) -> Iterator[AgentEvent].

        Args: 열린 sessionId와 사용자 질문이다.
        Returns: 런타임 의미 이벤트 스트림이다.
        Raises: ValueError if question is empty; runtime errors become events.
        Example: `for event in engine.streamTurn(session.sessionId, "질문"): ...`.
        """
        if not question.strip():
            raise ValueError("question은 비어 있을 수 없습니다")
        managed = self._managed(sessionId)
        if not managed.turnLock.acquire(blocking=False):
            raise RuntimeError("같은 세션에서 이미 다른 턴이 실행 중입니다")
        try:
            tracker = _OutcomeTracker.start(question)
            mcp = probeMcpConnection(managed.handle.descriptor.runtimeId)
            instructions = buildAnalysisCapsule(cwd=managed.handle.cwd, mcpConnected=bool(mcp.get("connected")))
            turnQuestion = buildTurnQuestion(question, context)
            try:
                for event in managed.driver.streamTurn(managed.handle, turnQuestion, instructions=instructions):
                    payload = tracker.enrich(event)
                    self._rememberEvidence(payload)
                    publicEvent = AgentEvent(
                        event.schemaVersion,
                        event.sessionId,
                        event.turnId,
                        event.eventId,
                        event.sequence,
                        event.runtimeId,
                        event.kind,
                        event.timestamp,
                        payload,
                        event.nativeType,
                    )
                    managed.buffer.append(publicEvent)
                    tracker.observe(event)
                    yield publicEvent
                tracker.finalize()
                self.sessionStore.touch(sessionId, managed.handle.nativeSessionId)
            except Exception as exc:  # noqa: BLE001
                turnId = managed.handle.activeTurnId or uuid.uuid4().hex
                errorEvent = managed.handle.projector.event(
                    "runtimeError", turnId=turnId, payload={"error": str(exc), "outcomeId": tracker.outcomeId}
                )
                managed.buffer.append(errorEvent)
                yield errorEvent
        finally:
            managed.turnLock.release()

    def _rememberEvidence(self, payload: dict[str, Any]) -> None:
        """한 프로세스 수명 동안 exact ref의 작은 공개 projection을 bounded 보관한다."""
        outcomeId = str(payload.get("outcomeId") or "")
        details = payload.get("refDetails")
        if not outcomeId or not isinstance(details, list):
            return
        with self._evidenceLock:
            for item in details[:100]:
                if not isinstance(item, dict) or not item.get("id"):
                    continue
                key = (outcomeId, str(item["id"]))
                self._evidenceJournal[key] = dict(item)
                self._evidenceJournal.move_to_end(key)
                try:
                    self.evidenceStore.save(outcomeId, dict(item))
                except (OSError, ValueError, sqlite3.Error):
                    logger.exception("runtime evidence projection 저장 실패")
            while len(self._evidenceJournal) > 512:
                self._evidenceJournal.popitem(last=False)

    def resolveEvidence(self, outcomeId: str, refId: str) -> dict[str, Any]:
        """현재 엔진이 실제 도구 완료에서 관측한 exact evidence만 해석한다."""
        key = (outcomeId, refId)
        with self._evidenceLock:
            detail = self._evidenceJournal.get(key)
            if detail is None:
                try:
                    detail = self.evidenceStore.get(outcomeId, refId)
                except (OSError, ValueError, sqlite3.Error):
                    logger.exception("runtime evidence projection 조회 실패")
                    detail = None
                if detail is None:
                    raise KeyError("evidence detail not found for the exact outcome")
                self._evidenceJournal[key] = dict(detail)
            self._evidenceJournal.move_to_end(key)
            return dict(detail)

    def stream(
        self,
        question: str,
        *,
        runtimeId: str | None = None,
        sessionId: str | None = None,
        cwd: Path | None = None,
        context: dict[str, Any] | None = None,
    ) -> Iterator[AgentEvent]:
        """Sig: stream(question, *, runtimeId=None, sessionId=None, cwd=None) -> Iterator[AgentEvent].

        Args: 질문과 선택적 런타임, 세션, 작업공간이다.
        Returns: 세션을 자동 개방한 의미 이벤트 스트림이다.
        Example: `events = engine.stream("삼성전자 분석")`.
        """
        session = self.openSession(runtimeId=runtimeId, sessionId=sessionId, cwd=cwd)
        managed = self._managed(session.sessionId)
        started = managed.handle.projector.event(
            "sessionResumed" if sessionId else "sessionStarted",
            turnId="",
            payload={"nativeSessionId": session.nativeSessionId},
        )
        managed.buffer.append(started)
        yield started
        yield from self.streamTurn(session.sessionId, question, context=context)

    def replay(self, sessionId: str, *, afterSequence: int = 0) -> list[AgentEvent]:
        """Sig: replay(sessionId, *, afterSequence=0) -> list[AgentEvent].

        Args: sessionId와 마지막 수신 sequence다.
        Returns: hot buffer에 남은 후속 이벤트다.
        Example: `events = engine.replay("s", afterSequence=10)`.
        """
        return self._managed(sessionId).buffer.after(afterSequence)

    def cancel(self, sessionId: str) -> None:
        """Sig: cancel(sessionId) -> None.

        Args: 취소할 세션 ID다.
        Returns: None.
        Example: `engine.cancel("s")`.
        """
        managed = self._managed(sessionId)
        managed.driver.cancel(managed.handle)

    def approve(self, sessionId: str, approvalId: str, *, allow: bool) -> None:
        """Sig: approve(sessionId, approvalId, *, allow) -> None.

        Args: 세션, pending approval, 허용 여부다.
        Returns: None.
        Example: `engine.approve("s", "a", allow=True)`.
        """
        managed = self._managed(sessionId)
        managed.driver.approve(managed.handle, approvalId, allow=allow)

    def close(self) -> None:
        """Sig: close() -> None.

        Args: 없음.
        Returns: None.
        Example: 서버 lifespan 종료에서 `engine.close()`를 호출한다.
        """
        self.sessionManager.closeAll()


_RUNTIME_ENGINE: AgentRuntimeEngine | None = None


def getRuntimeEngine() -> AgentRuntimeEngine:
    """Sig: getRuntimeEngine() -> AgentRuntimeEngine.

    Args: 없음.
    Returns: 프로세스 공유 런타임 엔진이다.
    Example: `engine = getRuntimeEngine()`.
    """
    global _RUNTIME_ENGINE
    if _RUNTIME_ENGINE is None:
        _RUNTIME_ENGINE = AgentRuntimeEngine()
    return _RUNTIME_ENGINE


def _toolCallId(payload: dict[str, Any]) -> str:
    """Sig: _toolCallId(payload) -> str.

    Args: 네이티브 tool event payload다.
    Returns: 드라이버 간 상관관계에 쓸 tool call ID다.
    Example: `_toolCallId({"item": {"id": "t1"}})`.
    """
    item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
    return str(item.get("id") or item.get("toolCallId") or item.get("tool_call_id") or item.get("tool_use_id") or "")


def _toolName(payload: dict[str, Any]) -> str:
    """Sig: _toolName(payload) -> str.

    Args: 네이티브 tool event payload다.
    Returns: 가능한 경우 실제 MCP tool 이름이다.
    Example: `_toolName({"item": {"name": "EngineCall"}})`.
    """
    item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
    return str(payload.get("toolName") or item.get("tool") or item.get("name") or item.get("title") or "")


def _canonicalToolName(name: str) -> str:
    """Sig: _canonicalToolName(name) -> str.

    Args: runtime별 MCP prefix가 붙을 수 있는 tool 이름이다.
    Returns: DartLab canonical PascalCase 이름이다.
    Example: `_canonicalToolName("mcp__dartlab__EngineCall") == "EngineCall"`.
    """
    value = name.rsplit("__", 1)[-1].rsplit("/", 1)[-1]
    aliases = {
        "engine_call": "EngineCall",
        "inspect_dataset": "InspectDataset",
        "run_python": "RunPython",
    }
    return aliases.get(value, value)


def _toolFailed(payload: dict[str, Any]) -> bool:
    """Sig: _toolFailed(payload) -> bool.

    Args: tool completion payload다.
    Returns: 명시적인 실패 표식이 하나라도 있으면 True다.
    Example: `_toolFailed({"item": {"status": "failed"}})`.
    """
    item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
    status = str(item.get("status") or "").lower()
    if status in {"failed", "error", "cancelled", "canceled"} or item.get("is_error") is True:
        return True
    return _containsFalseOk(item)


def _containsFalseOk(value: Any, *, depth: int = 0) -> bool:
    """Sig: _containsFalseOk(value, *, depth=0) -> bool.

    Args: bounded tool result 구조다.
    Returns: `ok: false`를 발견하면 True다.
    Example: `_containsFalseOk({"ok": False})`.
    """
    if depth > 6:
        return False
    if isinstance(value, dict):
        if value.get("ok") is False:
            return True
        return any(_containsFalseOk(item, depth=depth + 1) for item in value.values())
    if isinstance(value, list):
        return any(_containsFalseOk(item, depth=depth + 1) for item in value[:200])
    return False


def _turnCompletedSuccessfully(payload: dict[str, Any]) -> bool:
    """Sig: _turnCompletedSuccessfully(payload) -> bool.

    Args: runtime별 terminal turn payload다.
    Returns: failed, interrupted, cancelled가 아닌 정상 완료면 True다.
    Example: `_turnCompletedSuccessfully({"status": "completed"})`.
    """
    turn = payload.get("turn") if isinstance(payload.get("turn"), dict) else {}
    status = str(payload.get("status") or turn.get("status") or payload.get("stopReason") or "completed").lower()
    return status not in {"failed", "error", "interrupted", "cancelled", "canceled", "refused"}


def _evidenceDetails(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Sig: _evidenceDetails(payload) -> list[dict[str, Any]].

    Args: bounded native tool completion payload다.
    Returns: tool 결과 속 정형 evidence ref의 공개 가능한 작은 projection이다.
    Example: `_evidenceDetails({"refs": [{"id": "r", "kind": "tableRef"}]})`.
    """
    found: dict[str, dict[str, Any]] = {}

    def visit(value: Any, *, depth: int = 0, inRefs: bool = False) -> None:
        """제한된 깊이와 개수 안에서 evidence ref 후보를 순회한다."""
        if depth > 8 or len(found) >= 100:
            return
        if isinstance(value, str):
            stripped = value.strip()
            if len(stripped) <= 262_144 and stripped[:1] in {"{", "["}:
                try:
                    visit(json.loads(stripped), depth=depth + 1, inRefs=inRefs)
                except (TypeError, ValueError, json.JSONDecodeError):
                    return
            return
        if isinstance(value, list):
            for item in value[:200]:
                visit(item, depth=depth + 1, inRefs=inRefs)
            return
        if not isinstance(value, dict):
            return
        refId = value.get("id")
        kind = str(value.get("kind") or "")
        if isinstance(refId, str) and refId and (inRefs or kind.endswith("Ref")):
            found.setdefault(
                refId,
                {
                    "id": refId,
                    "kind": kind or "evidenceRef",
                    "title": str(value.get("title") or refId)[:500],
                    "source": str(value.get("source") or "")[:1000],
                    "sourceType": str(value.get("sourceType") or "internal")[:100],
                    "payload": _publicEvidencePayload(value.get("payload")),
                },
            )
        for key, item in value.items():
            visit(item, depth=depth + 1, inRefs=inRefs or key in {"refs", "evidence", "refDetails"})

    visit(payload)
    return list(found.values())


def _publicEvidencePayload(value: Any) -> dict[str, Any]:
    """근거 드로어에 필요한 값만 크기 제한해 공개한다."""
    if not isinstance(value, dict):
        return {}
    allowed = ("stockCode", "period", "metric", "value", "unit", "dataAsOf", "page")
    result: dict[str, Any] = {}
    for key in allowed:
        item = value.get(key)
        if isinstance(item, (str, int, float, bool)) or item is None:
            result[key] = item
    return result
