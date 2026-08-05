"""설치형 런타임의 준비 상태 판정.

engine.py 가 소유하던 것을 떼어 냈다. 세션 수명과 스트리밍을 다루는 본체와, "이 런타임이
지금 쓸 수 있는가" 를 판정하는 일은 바뀌는 이유가 다르다. 한 파일에 두면 본체를 읽을 때마다
판정 규칙을 지나쳐야 한다.

판정의 핵심은 정직성이다. 아직 재지 못한 것을 미설치라고 적지 않고, 도달에 실패한 런타임을
준비 완료라고 적지 않는다. 상한을 넘긴 결과는 미판정으로 구분하고 기존 값을 덮지 않는다.
"""

from __future__ import annotations

import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any

from .contracts import nowIso
from .discovery import probeAllRuntimes, probeRuntime, probeRuntimeAuth
from .mcpBootstrap import probeMcpConnection
from .probeCache import (
    PROBE_CONCURRENCY,
    SwrCache,
    authProbeKey,
    backgroundRefresher,
    mcpProbeKey,
    versionProbeKey,
)
from .registry import loadRuntimeRegistry

logger = logging.getLogger(__name__)

# 투자 계약 점검은 로컬 카탈로그 조회라 런타임 CLI 와 무관하지만 첫 호출이 0.8 초다
# (실측 2026-08-05). 1 초 예산의 대부분을 여기서 쓰면 화면이 늦으므로 형제 probe 와
# 같은 stale-while-revalidate 계약에 넣는다. 값은 dartlab 자체가 바뀔 때만 달라진다.
_SEMANTIC_CACHE = SwrCache(600.0)
_SEMANTIC_KEY = "investmentSemanticReadiness"
_PENDING_STATES = {"unknown"}
# 도달 실패 기록의 유효 기간. 사용량 한도나 계정 제한은 시간이 지나면 풀리므로 영구
# 차단으로 굳히면 안 된다. 반대로 즉시 잊으면 화면이 다시 거짓 준비 완료를 말한다.
_DELIVERY_BLOCK_TTL_SECONDS = 6 * 3600.0
# 도달 판정 읽기 캐시. 값은 턴이 끝날 때와 다시 확인을 누를 때만 바뀌고 둘 다 여기서
# 무효화한다. TTL 은 다른 프로세스가 쓴 값을 따라잡는 상한일 뿐이다. 캐시가 없으면 상태
# 조회 한 번이 sqlite 연결 3 회가 되어 표시 경로가 30ms 를 더 쓴다(실측 2026-08-06).
_DELIVERY_CACHE = SwrCache(5.0)


def _deliveryRecord(store: Any, runtimeId: str) -> dict[str, Any]:
    """마지막 턴이 실제로 DartLab 도구에 닿았는지의 캐시된 판정을 읽는다.

    설치·로그인·MCP 등록은 CLI 에게 물어보면 알 수 있지만 도달 가능성은 아니다. 실측
    2026-08-06: codex 는 세 항목 전부 통과하면서도 사용량 한도 소진으로 모델 토큰을 한 개도
    만들지 못했고, 그 사이 화면은 근거 기반 분석 준비 완료를 표시했다. 여기서는 실호출을
    새로 하지 않고 마지막 턴이 남긴 판정만 읽는다.
    """
    entry = _DELIVERY_CACHE.peek(runtimeId)
    if entry is not None and entry.fresh:
        return _agedDelivery(dict(entry.value))
    try:
        record = store.getDelivery(runtimeId) or {"state": "unknown"}
    except (OSError, sqlite3.Error):
        logger.exception("런타임 도달 판정 조회 실패")
        return {"state": "unknown"}
    _DELIVERY_CACHE.put(runtimeId, record)
    return _agedDelivery(record)


def _agedDelivery(record: dict[str, Any]) -> dict[str, Any]:
    """유효 기간이 지난 실패 기록을 판정이 아닌 옛 기록으로 낮춘다."""
    if record.get("state") == "blocked" and _isStaleIso(record.get("updatedAt"), _DELIVERY_BLOCK_TTL_SECONDS):
        # 오래된 실패는 판정이 아니라 옛 기록이다. 다시 미상으로 돌린다.
        return {"state": "unknown", "detail": record.get("detail"), "expired": True}
    return dict(record)


@lru_cache(maxsize=1)
def _dartlabToolNames() -> frozenset[str]:
    """DartLab MCP 가 광고하는 도구 이름 집합이다. 프로세스 수명 동안 바뀌지 않는다."""
    from dartlab.ai.tools.registry import listToolNames

    return frozenset(listToolNames())


def _reachedDartlabTool(payload: dict[str, Any]) -> bool:
    """이번 도구 호출이 런타임 내장 도구가 아니라 DartLab 도구였는지 판정한다."""
    canonical = str(payload.get("canonicalName") or "")
    if not canonical:
        return False
    if "dartlab" in str(payload.get("nativeName") or "").casefold():
        return True
    try:
        return canonical in _dartlabToolNames()
    except Exception:  # noqa: BLE001 - 카탈로그 조회 실패가 턴을 죽이면 안 된다.
        logger.exception("DartLab 도구 목록 조회 실패")
        return False


def _isStaleIso(timestamp: Any, ttlSeconds: float) -> bool:
    """ISO 시각이 주어진 유효 기간을 지났는지 판정한다."""
    from datetime import datetime, timezone

    try:
        moment = datetime.fromisoformat(str(timestamp))
    except (TypeError, ValueError):
        return True
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - moment).total_seconds() > ttlSeconds


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
    delivery: dict[str, Any] | None = None,
) -> tuple[bool, str | None, str | None]:
    """런타임 probe를 준비 여부와 사용자 조치 문구로 정규화한다."""
    stages = probing or {}
    groundedReady = (
        probe.state == "ready"
        and auth.get("state") in {"authenticated", "unsupported"}
        and descriptor.embeddedGrounding
        and bool(mcp.get("connected"))
    )
    if groundedReady and (delivery or {}).get("state") == "blocked":
        # 설치·로그인·MCP 는 통과했는데 마지막 실제 턴이 런타임 층에서 죽었다. 이 상태를
        # 준비 완료로 표시하면 사용자를 답이 나오지 않는 경로로 보낸다.
        detail = str((delivery or {}).get("detail") or "").strip()
        return (
            False,
            detail or "마지막 분석 턴이 런타임 오류로 끝났습니다",
            "런타임 CLI 자체를 실행해 오류를 해소한 뒤 다시 확인을 눌러 주세요",
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
    delivery: dict[str, Any] | None = None,
) -> str:
    """현재 상태에서 Runtime Center가 실행할 단일 기본 동작을 고른다."""
    stages = probing or {}
    if stages.get("install"):
        return "probing"
    if (delivery or {}).get("state") == "blocked":
        # 설치·연결은 이미 됐으므로 다시 설치하거나 연결하라고 권하면 안 된다. 사용자가
        # 런타임 쪽 문제를 푼 뒤 다시 확인하는 것이 유일한 진행 경로다.
        return "recheck"
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
    delivery: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """한 런타임의 기술 준비와 투자 계약 준비 상태를 공개 행으로 만든다."""
    probing = _runtimeProbingStages(probe, auth, mcp, semanticReadiness)
    pending = any(probing.values())
    undetermined = _runtimeUndetermined(probe, auth, mcp)
    delivery = delivery or {"state": "unknown"}
    groundedReady, blockingReason, recommendedAction = _runtimeGroundingState(
        descriptor, probe, auth, mcp, probing, delivery
    )
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
        # 마지막 실제 턴이 DartLab 도구에 닿았는지의 판정이다. verified 는 닿았음,
        # blocked 는 런타임 층에서 죽었음, unknown 은 아직 모름이다. 모르는 것은
        # 준비됨으로도 미준비로도 적지 않는다.
        "delivery": delivery,
        "readiness": {
            "install": "ready" if probe.state == "ready" else probe.state,
            "auth": auth.get("state"),
            "protocol": "supported" if descriptor.embeddedGrounding else "unsupported",
            "grounding": "probing"
            if probing["grounding"]
            else ("connected" if mcp.get("connected") else "disconnected"),
            # 설치·로그인·MCP 와 달리 이 축만이 "질문하면 답이 나오는가" 를 말한다.
            "delivery": delivery.get("state"),
            "ready": groundedReady,
        },
        "primaryAction": _runtimePrimaryAction(descriptor, probe, auth, mcp, groundedReady, probing, delivery),
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
