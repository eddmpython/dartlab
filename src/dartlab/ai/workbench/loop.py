"""Ask Workbench loop — 분석 모드 sub-agent (5 패스 또는 휴리스틱).

본체 아님. 본체는 `ai/agent.py` (chat-native + LLM 자율 tool calling).
WorkbenchLoop 는 *명시적 분석 의도* 시 `agent_gateway` / `kernel.ask()` 가 호출.

분기 룰 (`stream()` 기준):
- provider 가 LLM 이 아님 → `streamHeuristic` (휴리스틱 path, 5 패스 노드명 발행)
- LLM provider → `streamLLMPasses` (5 패스: brief/work/critique/compose/gate/harvest)

chat-native 는 본 모듈에서 분기하지 않는다 — agent.py 가 본체. 회귀 방지:
memory/engineering.md 7절.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from dartlab.ai.contracts import TraceEvent
from dartlab.ai.settings.providerCatalog import wiredProviderIds

from .heuristic import streamHeuristic
from .passes import streamLLMPasses

# 호환 re-export — tests/test_intent_category.py 와 tests/ai/test_workbench_loop.py 가
# `from dartlab.ai.workbench.loop import _buildQuestionProfile, _injectStepDependency`
# 형태로 import. 점진 마이그레이션 시 직접 경로 (`.targets`) 로 전환.
from .targets import _buildQuestionProfile, _injectStepDependency  # noqa: F401

# 5 패스 단일 SSOT — runtime.workbenchEvidenceFlow 와 일치.
GRAPH_NODES: tuple[str, ...] = (
    "brief",
    "work",
    "critique",
    "compose",
    "gate",
    "harvest",
)


class WorkbenchLoop:
    """Production ask loop — chat-native + 5 패스 + 휴리스틱 분기점.

    routeIntent / selectSkill / searchCapability / planEvidence 는 BRIEF 안에 흡수,
    executeTool / observeResult 는 WORK 안의 도구 루프, verifyClaims 는 GATE 의
    programmatic 검증, composeAnswer 는 COMPOSE, repairOrFail 은 GATE 회귀 + 종료
    분기로 통합되었다.
    """

    nodes = GRAPH_NODES

    def stream(self, question: str, **kwargs: Any) -> Iterator[TraceEvent]:
        """분석 모드 sub-agent. chat-native 는 ai/agent.py 가 처리 — 본 모듈 호출 X."""
        provider_obj = kwargs.pop("provider", None)
        if provider_obj is None:
            provider_obj = _resolveProvider(kwargs.get("config"))
        if not _isLLMProvider(provider_obj):
            yield from streamHeuristic(question, graphNodes=GRAPH_NODES, **kwargs)
            return
        yield from streamLLMPasses(question, provider_obj, graphNodes=GRAPH_NODES, **kwargs)


# ── Provider 해상도 ──


def _resolveProvider(config: Any = None) -> Any:
    """config 으로부터 provider 객체 시도. 실패 시 None."""
    try:
        from dartlab.ai.providers import createProvider

        return createProvider(config)
    except Exception:  # noqa: BLE001
        return None


def _isLLMProvider(obj: Any) -> bool:
    """5 패스 LLM-driven path 사용 여부.

    WorkbenchProvider Protocol (generate) 만족 + check_available True + provider id 가
    `provider_catalog.wiredProviderIds()` 에 등록된 어댑터일 때 True. 미해결 /
    dartlab stub 등은 휴리스틱 path.
    """
    if obj is None:
        return False
    if not callable(getattr(obj, "generate", None)):
        return False
    config = getattr(obj, "config", None)
    providerId = (getattr(config, "provider", None) or "").lower()
    if providerId not in wiredProviderIds():
        return False
    try:
        return bool(obj.checkAvailable())
    except Exception:  # noqa: BLE001
        return False
