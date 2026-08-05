"""DartLab 설치형 에이전트 런타임의 단일 진실 원천."""

from __future__ import annotations

import logging
import os
import sqlite3
import uuid
from collections import OrderedDict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import RLock
from typing import Any

from .analysisCapsule import buildAnalysisCapsule, buildTurnQuestion
from .contracts import AgentEvent, RuntimeSession, nowIso
from .discovery import probeAllRuntimes, probeRuntime, probeRuntimeAuth
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
from .registry import loadRuntimeRegistry
from .sessionManager import ManagedSession, SessionManager
from .sessionStore import SessionStore

logger = logging.getLogger(__name__)
_DEFAULT_RUNTIME_PREFERENCE = "defaultRuntimeId"
# 투자 계약 점검은 로컬 카탈로그 조회라 런타임 CLI 와 무관하지만 첫 호출이 0.8 초다
# (실측 2026-08-05). 1 초 예산의 대부분을 여기서 쓰면 화면이 늦으므로 형제 probe 와
# 같은 stale-while-revalidate 계약에 넣는다. 값은 dartlab 자체가 바뀔 때만 달라진다.
_SEMANTIC_CACHE = SwrCache(600.0)
_SEMANTIC_KEY = "investmentSemanticReadiness"
_PENDING_STATES = {"unknown"}


class RuntimeUnavailableError(RuntimeError):
    """사용 가능한 설치형 에이전트 CLI가 없을 때 발생한다."""


def _runtimeStorePath() -> Path:
    """Sig: _runtimeStorePath() -> Path.

    Args: 없음.
    Returns: 런타임 세션 매핑 DB 경로다.
    Example: `path = _runtimeStorePath()`.
    """
    configured = os.environ.get("DARTLAB_RUNTIME_DB")
    return Path(configured) if configured else Path.home() / ".dartlab" / "agentRuntime.sqlite3"


def _runtimeProbingStages(
    probe: Any, auth: dict[str, Any], mcp: dict[str, Any], semanticReadiness: dict[str, Any]
) -> dict[str, bool]:
    """아직 측정 중이라 결론을 낼 수 없는 단계를 표시한다.

    측정 전 상태를 "미설치"·"미연결" 로 적으면 화면이 거짓말을 한다. 모르는 것은
    모른다고 적고 화면이 그 문구를 쓰게 한다. 단 "아직 재는 중" 과 "재 봤지만 판정하지
    못했다" 는 다르다. 후자를 계속 진행 중으로 두면 화면이 영원히 폴링하므로, 실측이
    실제로 돌고 있는 동안만 진행 중이다. 백그라운드 재시도도 진행 중에 포함한다.
    """
    refresher = backgroundRefresher()
    runtimeId = probe.runtimeId
    return {
        "install": probe.state in _PENDING_STATES
        and (not probe.detail or refresher.isPending(versionProbeKey(runtimeId))),
        "auth": str(auth.get("state") or "") in _PENDING_STATES
        and (not auth.get("undetermined") or refresher.isPending(authProbeKey(runtimeId))),
        "grounding": bool(mcp.get("pending"))
        or bool(mcp.get("undetermined") and refresher.isPending(mcpProbeKey(runtimeId))),
        "contract": bool(semanticReadiness.get("pending")),
    }


def _runtimeUndetermined(probe: Any, auth: dict[str, Any], mcp: dict[str, Any]) -> bool:
    """실측을 시도했으나 판정하지 못한 단계가 있는지 알린다."""
    return bool(
        (probe.state in _PENDING_STATES and probe.detail) or auth.get("undetermined") or mcp.get("undetermined")
    )


def _runtimeGroundingState(
    descriptor: Any,
    probe: Any,
    auth: dict[str, Any],
    mcp: dict[str, Any],
    probing: dict[str, bool] | None = None,
) -> tuple[bool, str | None, str | None]:
    """런타임 probe를 준비 여부와 사용자 조치 문구로 정규화한다."""
    stages = probing or {}
    groundedReady = (
        probe.state == "ready"
        and auth.get("state") in {"authenticated", "unsupported"}
        and descriptor.embeddedGrounding
        and bool(mcp.get("connected"))
    )
    if not descriptor.embeddedGrounding:
        return (
            groundedReady,
            "현재 CLI 프로토콜이 DartLab 근거 도구를 세션에 노출하지 않습니다",
            "공식 프로토콜 지원을 기다리거나 다른 런타임을 선택하세요",
        )
    if stages.get("install"):
        return groundedReady, "설치 여부를 확인하는 중입니다", "확인이 끝나면 다음 단계를 안내합니다"
    if probe.state in _PENDING_STATES:
        # 재 봤지만 판정하지 못한 경우다. 설치돼 있는데 "미설치" 라고 적으면 이미 있는 것을
        # 다시 설치하라고 권하게 된다.
        return groundedReady, "설치 상태를 확인하지 못했습니다", "다시 확인을 눌러 주세요"
    if probe.state != "ready":
        return groundedReady, "CLI가 설치되지 않았거나 실행할 수 없습니다", "검증된 설치 계획을 확인하세요"
    if stages.get("auth"):
        return groundedReady, "로그인 상태를 확인하는 중입니다", "확인이 끝나면 다음 단계를 안내합니다"
    if auth.get("undetermined"):
        return groundedReady, "로그인 상태를 확인하지 못했습니다", "다시 확인을 눌러 주세요"
    if auth.get("state") not in {"authenticated", "unsupported"}:
        return groundedReady, "CLI 로그인이 확인되지 않았습니다", "공식 CLI 로그인 명령을 실행한 뒤 다시 확인하세요"
    if stages.get("grounding"):
        return groundedReady, "DartLab 연결 상태를 확인하는 중입니다", "확인이 끝나면 다음 단계를 안내합니다"
    if mcp.get("undetermined"):
        return groundedReady, "DartLab 연결 상태를 확인하지 못했습니다", "다시 확인을 눌러 주세요"
    if not mcp.get("connected"):
        return groundedReady, "DartLab MCP 연결이 확인되지 않았습니다", "검증된 MCP 연결 계획을 확인하세요"
    if stages.get("contract"):
        return groundedReady, "투자 분석 계약을 확인하는 중입니다", "확인이 끝나면 다음 단계를 안내합니다"
    return groundedReady, None, None


def _runtimePrimaryAction(
    descriptor: Any,
    probe: Any,
    auth: dict[str, Any],
    mcp: dict[str, Any],
    groundedReady: bool,
    probing: dict[str, bool] | None = None,
) -> str:
    """현재 상태에서 Runtime Center가 실행할 단일 기본 동작을 고른다."""
    stages = probing or {}
    if stages.get("install"):
        return "probing"
    if descriptor.embeddedGrounding and any(stages.get(key) for key in ("auth", "grounding", "contract")):
        return "probing"
    if _runtimeUndetermined(probe, auth, mcp):
        # 판정하지 못한 상태에서 설치·연결을 권하면 이미 된 것을 또 하라고 말하게 된다.
        return "recheck"
    if probe.state != "ready":
        return "install"
    if auth.get("state") != "authenticated" and descriptor.loginArgs:
        return "login"
    if descriptor.embeddedGrounding and not mcp.get("connected"):
        return "connect"
    if groundedReady:
        return "select"
    return "unsupported"


def _runtimeStatusEntry(
    descriptor: Any,
    probe: Any,
    auth: dict[str, Any],
    mcp: dict[str, Any],
    semanticReadiness: dict[str, Any],
) -> dict[str, Any]:
    """한 런타임의 기술 준비와 투자 계약 준비 상태를 공개 행으로 만든다."""
    probing = _runtimeProbingStages(probe, auth, mcp, semanticReadiness)
    pending = any(probing.values())
    undetermined = _runtimeUndetermined(probe, auth, mcp)
    groundedReady, blockingReason, recommendedAction = _runtimeGroundingState(descriptor, probe, auth, mcp, probing)
    checks = semanticReadiness.get("checks", {})
    return {
        **descriptor.toDict(),
        **probe.toDict(),
        "mcp": mcp,
        "auth": auth,
        # 실행 파일 발견은 CLI 를 띄우지 않는 즉시 판정이라 측정 중에도 사실이다.
        "installed": probe.executable is not None,
        "probing": probing,
        "pending": pending,
        # 실측을 시도했지만 판정하지 못했다. 기다려도 바뀌지 않으니 다시 확인이 답이다.
        "undetermined": undetermined,
        "groundedReady": groundedReady,
        "semanticToolsReady": bool(checks.get("readSkill")) and bool(checks.get("engineCall")),
        "investmentContractReady": bool(checks.get("investmentContract")) and bool(checks.get("reportModel")),
        "investmentReady": groundedReady and bool(semanticReadiness.get("ready")),
        "canInstall": (
            descriptor.embeddedGrounding and not probing["install"] and not undetermined and probe.state != "ready"
        ),
        "canConnect": (
            descriptor.embeddedGrounding
            and not probing["grounding"]
            and not undetermined
            and probe.state == "ready"
            and not mcp.get("connected")
        ),
        "canLogin": (
            probe.state == "ready"
            and not probing["auth"]
            and not undetermined
            and bool(descriptor.loginArgs)
            and auth.get("state") != "authenticated"
        ),
        "readiness": {
            "install": "ready" if probe.state == "ready" else probe.state,
            "auth": auth.get("state"),
            "protocol": "supported" if descriptor.embeddedGrounding else "unsupported",
            "grounding": "probing"
            if probing["grounding"]
            else ("connected" if mcp.get("connected") else "disconnected"),
            "ready": groundedReady,
        },
        "primaryAction": _runtimePrimaryAction(descriptor, probe, auth, mcp, groundedReady, probing),
        "blockingReason": blockingReason,
        "recommendedAction": recommendedAction,
    }


ProbeBundle = tuple[list[Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]


def _measuredProbes(*, refresh: bool) -> ProbeBundle:
    """버전·MCP·인증을 한 번에 펼쳐 실제로 측정하고 가장 느린 한 건까지만 기다린다.

    세 단계는 서로 의존하지 않는 별개 CLI 실행인데 버전 확인이 전부 끝난 뒤에야 나머지를
    시작했다. 그래서 대기가 단계 합이 됐다(실측 2026-08-05: 12.0초 = 버전 3.3초 + MCP
    7.3초 + 인증 1.1초). 축을 함께 펼치면 같은 측정을 하고도 가장 느린 한 건에서 끝난다.
    설치되지 않은 런타임의 MCP·인증 probe 는 CLI 를 띄우지 않고 즉시 판정되므로 낭비가 없다.

    동시 실행 수는 ``probeCache.PROBE_CONCURRENCY`` 가 묶는다. 전부 한꺼번에 띄우면
    Node CLI 콜드스타트가 서로 CPU 를 뺏어 멀쩡한 CLI 가 자기 상한을 넘긴다(실측
    2026-08-05: 9 건 동시 실행에서 `cline --version` 이 5 초 상한 초과로 unavailable
    오판). 겹치기의 목적은 대기 시간을 포개는 것이지 동시 기동 수를 늘리는 게 아니다.
    """
    registry = loadRuntimeRegistry()
    if not registry:
        return [], {}, {}
    with ThreadPoolExecutor(max_workers=PROBE_CONCURRENCY, thread_name_prefix="dartlab-runtime-status") as pool:
        # 가장 느린 probe(MCP)를 먼저 큐에 넣어야 짧은 probe 뒤에서 대기하지 않는다.
        mcpJobs = {runtimeId: pool.submit(probeMcpConnection, runtimeId, refresh=refresh) for runtimeId in registry}
        versionJobs = {
            runtimeId: pool.submit(probeRuntime, descriptor, refresh=refresh)
            for runtimeId, descriptor in registry.items()
        }
        authJobs = {
            runtimeId: pool.submit(probeRuntimeAuth, descriptor, refresh=refresh)
            for runtimeId, descriptor in registry.items()
        }
        probes = [versionJobs[runtimeId].result() for runtimeId in registry]
        mcpResults = {runtimeId: job.result() for runtimeId, job in mcpJobs.items()}
        authResults = {runtimeId: job.result() for runtimeId, job in authJobs.items()}
    return probes, mcpResults, authResults


def _scheduledProbes(registry: dict[str, Any]) -> ProbeBundle:
    """캐시에 있는 것만 즉시 읽고 없는 것은 백그라운드 실측으로 예약한다."""
    probes = probeAllRuntimes(blocking=False)
    resolvable = [probe for probe in probes if probe.state in {"ready", *_PENDING_STATES}]
    mcpResults = {probe.runtimeId: probeMcpConnection(probe.runtimeId, blocking=False) for probe in resolvable}
    authResults = {
        probe.runtimeId: probeRuntimeAuth(registry[probe.runtimeId], executable=probe.executable, blocking=False)
        for probe in resolvable
    }
    return probes, mcpResults, authResults


def _semanticReadiness(*, blocking: bool) -> dict[str, Any]:
    """투자 계약 점검을 캐시에서 읽고 없으면 blocking 여부에 따라 측정하거나 예약한다."""
    from .setupCoordinator import investmentSemanticReadiness

    entry = _SEMANTIC_CACHE.peek(_SEMANTIC_KEY)
    if entry is not None and entry.fresh:
        return dict(entry.value)
    if blocking:
        return dict(_SEMANTIC_CACHE.put(_SEMANTIC_KEY, investmentSemanticReadiness()))
    backgroundRefresher().submit(
        _SEMANTIC_KEY,
        lambda: _SEMANTIC_CACHE.put(_SEMANTIC_KEY, investmentSemanticReadiness()),
    )
    if entry is not None:
        return dict(entry.value)
    return {"ready": False, "checks": {}, "pending": True}


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
            runtimes.append(_runtimeStatusEntry(self.registry[probe.runtimeId], probe, auth, mcp, semanticReadiness))
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
            if not probeMcpConnection(preferredRuntimeId).get("connected"):
                raise RuntimeUnavailableError(
                    f"{preferredRuntimeId}에 DartLab MCP가 연결되지 않았습니다. "
                    f"`dartlab agent connect {preferredRuntimeId}`로 승인 계획을 확인하세요"
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
