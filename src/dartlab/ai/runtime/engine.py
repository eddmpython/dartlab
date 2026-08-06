"""DartLab 설치형 에이전트 런타임의 단일 진실 원천."""

from __future__ import annotations

import logging
import os
import sqlite3
import uuid
from collections import OrderedDict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from threading import RLock
from typing import Any

from .analysisCapsule import buildAnalysisCapsule, buildTurnQuestion
from .contracts import AgentEvent, RuntimeSession, nowIso
from .discovery import probeRuntime, probeRuntimeAuth
from .drivers import AcpDriver, ClaudeStreamJsonDriver, CodexAppServerDriver
from .drivers.base import AgentRuntimeDriver
from .eventBuffer import EventBuffer
from .evidenceStore import EvidenceStore
from .mcpBootstrap import probeMcpConnection
from .outcomeTracking import _OutcomeTracker, _publicEvidencePayload, _turnCompletedSuccessfully
from .probeCache import (
    PROBE_CONCURRENCY,
    SwrCache,
    authProbeKey,
    backgroundRefresher,
    mcpProbeKey,
    versionProbeKey,
)
from .readiness import (
    _DELIVERY_BLOCK_TTL_SECONDS,
    _DELIVERY_CACHE,
    _PENDING_STATES,
    _deliveryRecord,
    _measuredProbes,
    _reachedDartlabTool,
    _runtimeStatusEntry,
    _scheduledProbes,
    _semanticReadiness,
)
from .registry import loadRuntimeRegistry
from .sessionManager import ManagedSession, SessionManager
from .sessionStore import SessionStore

logger = logging.getLogger(__name__)
_DEFAULT_RUNTIME_PREFERENCE = "defaultRuntimeId"


class RuntimeUnavailableError(RuntimeError):
    """사용 가능한 설치형 에이전트 CLI가 없을 때 발생한다."""


def _runtimeStorePath() -> Path:
    """Sig: _runtimeStorePath() -> Path.

    Args: 없음.
    Returns: 런타임 세션 매핑과 도달 판정 DB 경로다.
    Example: `path = _runtimeStorePath()`.

    형제 사용자 상태 저장소와 같은 `DARTLAB_HOME` 규약을 따른다. 여기만 사용자 home 을
    직접 잡고 있어서 격리된 실행이 운영자의 실제 DB 를 건드렸다. 실측 2026-08-06:
    격리 없이 도는 실행이 도달 판정 원장을 통째로 지워 화면이 다시 거짓 준비 완료로
    돌아갔다.
    """
    from dartlab.core.providers.secrets import dartlabHome

    configured = os.environ.get("DARTLAB_RUNTIME_DB")
    return Path(configured) if configured else dartlabHome() / "agentRuntime.sqlite3"


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

    def status(self, *, refresh: bool = False, blocking: bool = True) -> dict[str, Any]:
        """Sig: status(*, refresh=False, blocking=True) -> dict[str, Any].

        Args: refresh는 probe 재측정 여부, blocking은 측정 완료를 기다릴지 여부다.
        Returns: 설치 상태, MCP 상태, hot session 목록, 측정 진행 표시다.
        Example: `engine.status(refresh=True)`.

        ``blocking=False`` 는 화면 진입용 스냅샷이다. 이미 아는 것은 즉시 돌려주고
        모르는 것은 ``probing`` 으로 표시한 뒤 실측을 백그라운드로 예약한다. 표시용
        스냅샷과 실행 직전 판정은 다른 요구라, 세션 개방·기본 런타임 선택은 계속
        측정을 기다리는 blocking 경로를 쓴다.
        """
        semanticReadiness = _semanticReadiness(blocking=blocking or refresh)
        if refresh:
            # 다시 확인은 전 단계 재측정이다. 도달 판정만은 턴 없이 다시 잴 수 없으므로
            # 준비됨으로 되돌리지 않고 미상으로 비운다.
            self._clearDeliveryRecords()
        probes, mcpResults, authResults = (
            _measuredProbes(refresh=refresh) if blocking else _scheduledProbes(self.registry)
        )
        runtimes = []
        for probe in probes:
            # 설치되지 않았다고 확정된 런타임은 하위 단계를 판정하지 않는다.
            resolvable = probe.state in {"ready", *_PENDING_STATES}
            mcp = mcpResults.get(probe.runtimeId, {"connected": False}) if resolvable else {"connected": False}
            missingAuth = {"state": "missing", "authenticated": False, "checkedAt": probe.checkedAt}
            auth = authResults.get(probe.runtimeId, missingAuth) if resolvable else missingAuth
            runtimes.append(
                _runtimeStatusEntry(
                    self.registry[probe.runtimeId],
                    probe,
                    auth,
                    mcp,
                    semanticReadiness,
                    _deliveryRecord(self.sessionStore, probe.runtimeId),
                )
            )
        defaultRuntimeId = self.sessionStore.getPreference(_DEFAULT_RUNTIME_PREFERENCE)
        if defaultRuntimeId not in self.registry:
            defaultRuntimeId = None
        groundedIds = [str(item["runtimeId"]) for item in runtimes if item.get("groundedReady")]
        if defaultRuntimeId is None and len(groundedIds) == 1:
            defaultRuntimeId = groundedIds[0]
        probing = any(bool(item.get("pending")) for item in runtimes)
        return {
            "runtimes": runtimes,
            "sessions": self.sessionManager.status(),
            "defaultRuntimeId": defaultRuntimeId,
            "probing": probing,
            "settled": not probing,
        }

    def setDefaultRuntime(self, runtimeId: str) -> str:
        """준비가 끝난 런타임만 새 대화의 서버 기본값으로 저장한다."""
        selected = self.selectRuntime(runtimeId)
        self.sessionStore.setPreference(_DEFAULT_RUNTIME_PREFERENCE, selected)
        return selected

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
            probe = probeRuntime(self.registry[preferredRuntimeId])
            if probeRuntimeAuth(self.registry[preferredRuntimeId], executable=probe.executable).get("state") not in {
                "authenticated",
                "unsupported",
            }:
                raise RuntimeUnavailableError(f"{preferredRuntimeId} CLI 로그인이 필요합니다")
            if not self.registry[preferredRuntimeId].embeddedGrounding:
                raise RuntimeUnavailableError(
                    f"{preferredRuntimeId}의 현재 ACP 구현은 embedded DartLab MCP를 노출하지 않습니다"
                )
            connection = probeMcpConnection(preferredRuntimeId)
            if connection.get("undetermined"):
                # 상한 초과는 미연결이 아니라 미판정이다. 측정층은 이미 둘을 구분하는데
                # 이 문에서 하나로 뭉개고 있었다. 실측(2026-08-06): 기기가 바쁜 동안
                # 13 개 질문이 전부 "연결되지 않았습니다" 로 막혔고, 같은 시점에
                # `claude mcp list` 는 연결됨이었다. 잠시 뒤에는 성립하므로 한 번 더 잰다.
                connection = probeMcpConnection(preferredRuntimeId, refresh=True)
            if connection.get("undetermined"):
                raise RuntimeUnavailableError(
                    f"{preferredRuntimeId}의 DartLab MCP 연결을 확인하지 못했습니다(측정 상한 초과). "
                    f"기기가 바쁘면 잠시 뒤 다시 시도하세요"
                )
            if not connection.get("connected"):
                raise RuntimeUnavailableError(
                    f"{preferredRuntimeId}에 DartLab MCP가 연결되지 않았습니다. "
                    f"`dartlab agent connect {preferredRuntimeId}`로 승인 계획을 확인하세요"
                )
            delivery = _deliveryRecord(self.sessionStore, preferredRuntimeId)
            if delivery.get("state") == "blocked":
                # 마지막 턴이 런타임 층에서 죽은 경로로 사용자를 다시 보내면 같은 침묵이
                # 반복된다. 여기서 실제 사유를 들고 멈추는 편이 정직하다.
                raise RuntimeUnavailableError(
                    f"{preferredRuntimeId}의 마지막 분석 턴이 런타임 오류로 끝났습니다: "
                    f"{delivery.get('detail') or '사유 미상'}"
                )
            return preferredRuntimeId
        stored = self.sessionStore.getPreference(_DEFAULT_RUNTIME_PREFERENCE)
        if stored:
            try:
                return self.selectRuntime(stored)
            except (KeyError, RuntimeUnavailableError):
                pass
        ready = [
            runtimeId
            for runtimeId, descriptor in self.registry.items()
            if descriptor.embeddedGrounding
            and probeRuntime(descriptor).state == "ready"
            and probeRuntimeAuth(descriptor).get("state") in {"authenticated", "unsupported"}
            and probeMcpConnection(runtimeId).get("connected")
            and _deliveryRecord(self.sessionStore, runtimeId).get("state") != "blocked"
        ]
        if len(ready) == 1:
            return ready[0]
        if len(ready) > 1:
            raise RuntimeUnavailableError(
                "사용 가능한 런타임이 여러 개입니다. Runtime Center에서 새 대화의 기본 런타임을 선택하세요"
            )
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
        outcomeId: str | None = None,
        priorRefs: list[dict[str, Any]] | None = None,
        priorReadSkillCalls: int = 0,
        qualityQuestion: str | None = None,
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
            tracker = (
                _OutcomeTracker.resume(
                    qualityQuestion or question,
                    outcomeId=outcomeId,
                    refs=priorRefs or [],
                    readSkillCalls=priorReadSkillCalls,
                )
                if outcomeId
                else _OutcomeTracker.start(qualityQuestion or question)
            )
            mcp = probeMcpConnection(managed.handle.descriptor.runtimeId)
            instructions = buildAnalysisCapsule(cwd=managed.handle.cwd, mcpConnected=bool(mcp.get("connected")))
            turnQuestion = buildTurnQuestion(question, context, contractQuestion=qualityQuestion)
            runtimeId = managed.handle.descriptor.runtimeId
            toolReached = False
            errorReason = ""
            try:
                for event in managed.driver.streamTurn(managed.handle, turnQuestion, instructions=instructions):
                    payload = tracker.enrich(event)
                    self._rememberEvidence(payload)
                    if event.kind == "toolStarted" and _reachedDartlabTool(payload):
                        toolReached = True
                    elif event.kind == "runtimeError":
                        errorReason = str(payload.get("error") or "")
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
                errorReason = errorReason or str(exc)
                errorEvent = managed.handle.projector.event(
                    "runtimeError", turnId=turnId, payload={"error": str(exc), "outcomeId": tracker.outcomeId}
                )
                managed.buffer.append(errorEvent)
                yield errorEvent
            finally:
                self._recordDelivery(runtimeId, toolReached=toolReached, errorReason=errorReason)
        finally:
            managed.turnLock.release()

    def _recordDelivery(self, runtimeId: str, *, toolReached: bool, errorReason: str) -> None:
        """이번 턴이 실제 도달을 증명했는지 또는 런타임 층에서 죽었는지만 남긴다.

        도구에 닿았으면 그 런타임은 증명된 것이고 옛 실패 기록을 지운다. 도구를 하나도
        부르지 못한 채 런타임 오류로 끝났으면 다음 조회가 그 사실을 알아야 한다. 도구는
        못 불렀지만 오류도 없는 턴은 답변 품질 문제이지 도달 문제가 아니라 기록하지 않는다.
        """
        if not toolReached and not errorReason:
            return
        state = "verified" if toolReached else "blocked"
        detail = "" if toolReached else errorReason
        try:
            self.sessionStore.recordDelivery(runtimeId, state, detail)
        except (OSError, sqlite3.Error):
            logger.exception("런타임 도달 판정 기록 실패")
        finally:
            _DELIVERY_CACHE.clear(runtimeId)

    def _clearDeliveryRecords(self) -> None:
        """사용자가 다시 확인을 눌렀을 때 도달 판정을 미상으로 되돌린다."""
        try:
            self.sessionStore.clearDelivery()
        except (OSError, sqlite3.Error):
            logger.exception("런타임 도달 판정 초기화 실패")
        finally:
            _DELIVERY_CACHE.clear()

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
