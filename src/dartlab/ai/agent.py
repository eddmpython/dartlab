"""DartLab AI 본체 — chat-native + LLM 자율 tool calling. Cursor/Aider 패턴.

agent_gateway 가 호출. 흐름:

```
loop (max 8 iter):
    turn = stream_provider(provider, messages, tools)   # text 델타 streaming
    if turn.tool_calls:
        for tc: execute(tc); messages.append(tool_result)
        continue
    final text → done
```

5 패스 graph 와 다른 점:
- 흐름 강제 X. LLM 이 *언제 어떤 도구* 자율 결정.
- workbench 5 패스는 *옵션 sub-agent*. 본 모듈이 본체.

회귀 방지: memory/feedback_no_graph_regression.md 참조. BRIEF/WORK/CRITIQUE/COMPOSE/GATE/HARVEST
같은 *고정 노드 강제* 패턴을 본 모듈에 추가 금지. 새 능력은 ai/tools/ 안에서.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .contracts import TraceEvent
from .providers import streamProvider
from .tools.formatting import wrapExternalInResult
from .tools.registry import executeTool, isToolReadOnly, toolSpecs
from .toolStorage import buildPersistedContent, exceedsSizeCap, persistLargeResult
from .workbench.prompts import DARTLAB_CHAT_SYSTEM

logger = logging.getLogger(__name__)

# 한 turn 에 LLM 이 동시에 emit 한 read-only 도구들을 thread pool 로 fan-out.
# 같은 turn 안 호출은 LLM 이 의존성 없음을 보증 (의존 있으면 다른 turn 으로 분리). 즉
# ReadSkill + ReadCapability + InspectDataset + EngineCall(scan='roe') + EngineCall(scan='debt')
# 같은 묶음은 모두 동시 실행 가능. write 도구 (RunPython · SaveArtifact) 는 시퀀셜.
#
# 워커 수 4 — polars/Rust 가 GIL 풀어 CPU bound 도 진짜 병렬, 네트워크 외부 호출 (WebSearch) 도
# 함께 묶임. 8 까지 늘려도 안전하나 LLM provider rate-limit 측면에서 보수적.
_PARALLEL_READ_WORKERS = 4

# 마스터 플랜 v2 트랙 6 PR-L4 — lazy tool spec.
# turn 1 은 _DEFAULT_TOOL_NAMES 전체 (LLM 첫 자율 선택), turn 2+ 는 _CORE_TOOL_NAMES ∪ 본 세션
# 실제 호출된 도구들로 좁혀 전송 → 매 turn input token 감소. _CORE_TOOL_NAMES 가 항상 포함되어
# 직전 turn 에 호출 안 한 *새* 도구 필요 시도 cover (LLM 자율 행동 회귀 가드).
# 환경변수 ``DARTLAB_LAZY_TOOL_SPEC=0`` 으로 비활성화 가능 (기본 ON).
_CORE_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "ReadSkill",
        "GetSkillBody",
        "ReadCapability",
        "EngineCall",
        "RunPython",
        "Read",
        "SaveArtifact",
        "WebSearch",
    }
)


def _lazyToolSpecEnabled() -> bool:
    return os.getenv("DARTLAB_LAZY_TOOL_SPEC", "1").lower() in ("1", "true", "yes")


# LLM 노출 도구 set — PascalCase (Claude 도구 체계 호환). Skill 우선 → Capability → 실행 → 시각화.
# EngineCall = 단일 capability 1 회. RunPython = 다단 계산. Read = 파일 직접 인용.
# RunWorkbench 는 5 패스 elevate 명시 경로 — feedback_no_graph_regression.md 정당 활성 경로 (2).
_DEFAULT_TOOL_NAMES: tuple[str, ...] = (
    "ReadSkill",
    "GetSkillBody",
    "ReadCapability",
    "EngineCall",
    "RunPython",
    "Read",
    "WebSearch",
    "SaveArtifact",
    "CreateUserSkill",
    "CompileVisual",
    # 마스터 플랜 트랙 1 PR-1 — Damodaran DCF wrap (bear/base/bull 3 시나리오).
    # 직전 회귀: LLM 이 매번 RunPython 으로 ad-hoc DCF 코드 작성 → token 30% 낭비.
    # default 노출 누락 시 LLM 호출 0 회 회귀 (2026-05-17 default 미노출 패턴).
    "DCFValuation",
    # 마스터 플랜 트랙 1 PR-2 — N(2~12) 종목 단일 비교 도구 + percentile rank.
    # 옛 max 3 한계 확장 + peer-internal ranking. 2~3 종목 비교도 본 도구가 흡수.
    "PeerCompareN",
    # 마스터 플랜 트랙 1 PR-5 — N(2~5) macro 시나리오 baseline 대비 동시 비교.
    # ScenarioOverlay 1 회 + RunPython loop 우회 → 1 회 호출.
    "ScenarioCompareN",
    # 마스터 플랜 트랙 1 PR-6 — dCR 신용등급 + 1Y PD + 7 축 분석.
    # credit.engine.evaluateCompany wrap, RunPython 으로 ad-hoc credit 계산 우회.
    "CreditScorecard",
    # 마스터 플랜 트랙 1 PR-4 — DCF parameter grid (WACC × growth) 민감도 매트릭스.
    # multiStageDcf 반복 호출 grid loop wrap.
    "SensitivityAnalysis",
    # 마스터 플랜 트랙 1 PR-3 — 단일 종목 한 화면 dashboard (3 template).
    # companyMetrics + CompileVisual + RunPython 다단 우회 회귀 차단.
    "CompileFinancialDashboard",
    # 마스터 플랜 트랙 1 PR-7 — 매출 성장률 회귀 예측 (cross/panel cache load).
    # crossRegression.fit* + loadModel/loadPanelModel wrap.
    "RegressionForecast",
    "PickStoryTemplate",
    "EvidenceGate",
    "GroundingCheck",
    "RunWorkbench",
    # 과거 세션 transcript cross-session 검색 — "이 회사 분석한 적 있나" / "이 매핑 결정
    # 어디서 했지" 류 질문에서 LLM 자율 호출. BM25 + FTS5 (sessionIndex.db ~/.dartlab/).
    "SearchPastSessions",
)


def runAgent(
    question: str,
    *,
    provider: Any,
    history: list[dict[str, Any]] | None = None,
    toolNames: tuple[str, ...] = _DEFAULT_TOOL_NAMES,
    maxIterations: int = 30,
    **_unused: Any,
) -> Iterator[TraceEvent]:
    """본체 — chat-native autonomous tool-calling 루프. agent_gateway 가 본 함수의 TraceEvent 를 SSE 로 변환.

    마스터 플랜 트랙 2 PR-O4 — 환경변수 ``DARTLAB_AI_TRACE_DUMP=1`` 활성 시 본
    함수의 TraceEvent 시퀀스를 ``~/.dartlab/ai_trace/{sessionId}.json`` 으로 자동
    저장 (7 일 retention). KPI digest (PR-O5) 의 입력. 기본 OFF — production
    영향 0.
    """
    raw_iter = _runAgentImpl(
        question,
        provider=provider,
        history=history,
        toolNames=toolNames,
        maxIterations=maxIterations,
        **_unused,
    )
    if _traceDumpEnabled():
        yield from _wrapWithAuditDump(question=question, provider=provider, rawIter=raw_iter)
    else:
        yield from raw_iter


def _runAgentImpl(
    question: str,
    *,
    provider: Any,
    history: list[dict[str, Any]] | None = None,
    toolNames: tuple[str, ...] = _DEFAULT_TOOL_NAMES,
    maxIterations: int = 30,
    **_unused: Any,
) -> Iterator[TraceEvent]:
    """runAgent 본체 — public alias 는 ``runAgent``."""
    history = history or []
    # ⚠ question 을 반드시 실어 보낸다. 예전엔 `_unused` 만 넘겨서 intent block 이 항상
    # 빈 문자열이었고 (kwargs 에 question 키가 없다), 그 결과 DCFValuation·PeerCompareN 등
    # 금융 primitive 8 종의 라우팅 힌트가 프로덕션에서 100% 죽어 있었다.
    # 시스템 프롬프트의 static 매핑 표를 dynamic inline 으로 대체한 뒤라 순증 소실이었다.
    intentKwargs = {**_unused, "question": str(question or "").strip()}
    systemPrompt = _injectPastContextIfAvailable(DARTLAB_CHAT_SYSTEM, intentKwargs, history=history)
    messages: list[dict[str, Any]] = [{"role": "system", "content": systemPrompt}]
    for entry in history:
        if not isinstance(entry, dict):
            continue
        role = entry.get("role")
        content = entry.get("content") or entry.get("text") or ""
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": str(content)})
    userText = str(question or "").strip()
    if userText:
        messages.append({"role": "user", "content": userText})

    tools = _selectTools(toolNames)
    # PR-L4 — turn 2+ tool spec narrowing 용 누적 (LLM 이 본 세션에 실제 호출한 도구 names).
    recently_used_tools: set[str] = set()
    lazy_tool_spec_enabled = _lazyToolSpecEnabled()

    # chat-native 흐름은 phase (단계) 가 없다. 도구 카드 + 텍스트 streaming 이 모든 진행 표현.
    # 무의미한 graph_node 1 회 emit 은 UI groupActivities 가 잘못된 phase ("작성") 라벨 붙이게 만들어 제거.
    # 회귀 가드: memory/feedback_no_graph_regression.md.
    refs: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    text_emitted = ""
    # 도구 호출 상태 SSOT — cache / blocked / cacheHit / failureStreak 4 종 통합. 옛 inline
    # 4 변수 (failure_streak/blocked_calls/call_cache/cache_hit_count) 가 매 회 manual 동기화.
    # 실패 streak partition (name, error, args) — 같은 도구의 valid 호출까지 차단되던 회귀
    # (2026-05-17 EngineCall macro.rates → unknown → gather.macro → unknown → macro valid 차단)
    # 방지. _CACHE_HIT_BLOCK_LIMIT=1 = cache hit 1회에 즉시 영구 차단 (2026-05-20 사용자 audit
    # scan.ratio 4 회 연속 cached 회귀 가드).
    tracker = _ToolCallTracker(failureStreakLimit=2, cacheHitBlockLimit=1)

    # 마스터 플랜 트랙 2 PR-O2 — 첫 chunk 까지 ms 측정용. session 전체 1 회만 emit.
    session_start_ms = time.monotonic()
    first_chunk_emitted = False

    for iteration in range(maxIterations):
        # 옛 assistant reasoning 트리밍 (마지막 2 개 외 content → None). tool_calls 보존.
        # 회귀 가드: 노드 추가 아님. 기계적 메모리 관리만.
        _microcompact(messages, keepLast=2)

        # PR-L4 — turn 2+ 부터 lazy tool spec (recently used + _CORE 만). turn 1 은 전체 유지.
        if lazy_tool_spec_enabled and iteration >= 1 and recently_used_tools:
            narrowed = _selectTools(toolNames, recentlyUsed=recently_used_tools)
            if len(narrowed) < len(tools):
                yield TraceEvent(
                    "tool_spec_narrowed",
                    {
                        "iter": iteration,
                        "before": len(tools),
                        "after": len(narrowed),
                        "kept": sorted({t["function"]["name"] for t in narrowed}),
                    },
                )
                tools = narrowed

        # PR-O2 — turn timing. stream 진입/종료 ms 분리 측정.
        turn_start_ms = time.monotonic()
        stream_first_chunk_ms: float | None = None

        # lazy 소비 — provider 가 토큰 yield 하는 즉시 SSE chunk emit (typing 효과).
        # 회귀 가드: list(streamProvider(...)) 로 한 번에 모은 뒤 풀면 LLM 응답 끝까지 블록 →
        # UI 가 "분석중..." 만 길게 보이다 한 방에 답이 나타남. iterator 그대로 돌려야 한다.
        final_chunk = None
        try:
            for chunk in streamProvider(provider, messages, tools):
                if chunk.final:
                    final_chunk = chunk
                    continue
                # 추론(사고) 델타. 답변 본문과 분리 스트림, UI 가 접이식 추론 패널로 표시.
                if getattr(chunk, "thinking", ""):
                    yield TraceEvent("thinking", {"text": chunk.thinking})
                if chunk.text:
                    if stream_first_chunk_ms is None:
                        stream_first_chunk_ms = (time.monotonic() - turn_start_ms) * 1000.0
                    if not first_chunk_emitted:
                        first_chunk_emitted = True
                        yield TraceEvent(
                            "first_chunk_ms",
                            {"ms": round((time.monotonic() - session_start_ms) * 1000.0, 2), "iter": iteration},
                        )
                    text_emitted += chunk.text
                    yield TraceEvent("chunk", {"text": chunk.text})
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "stream_provider failed (provider=%s, iter=%d)",
                getattr(getattr(provider, "config", None), "provider", "?"),
                iteration,
            )
            # 이미 모은 tool 결과 (refs) 가 있으면 _finalize 한 round 시도. OAuth timeout 한 번에
            # 41 분기 시계열 받아놓고도 사용자에게 한 글자 안 보여주던 회귀 가드.
            if refs or text_emitted:
                yield TraceEvent("error", {"error": f"{type(exc).__name__}: {exc}", "recoverable": True})
                yield from _finalize(provider, messages, refs, artifacts, reason="provider_error", originalExc=exc)
                _wireChatNativeMemory(question=userText, answerText=text_emitted, refs=refs, kwargs=_unused)
                return
            yield TraceEvent("error", {"error": f"{type(exc).__name__}: {exc}"})
            return

        turn = final_chunk.turn if final_chunk else None
        if turn is None:
            yield TraceEvent("error", {"error": "no_final_turn"})
            return

        if turn.toolCalls:
            # streaming 미지원 provider 가 final 만 emit 하면 turn.content 가 그대로 텍스트일 수 있음.
            # 단 tool_calls 가 있으면 사용자에게 텍스트보다 도구 결과가 본체 — 텍스트는 일단 보존.
            if turn.content and not text_emitted:
                text_emitted = turn.content
                for piece in _chunks(turn.content, size=64):
                    yield TraceEvent("chunk", {"text": piece})

            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": turn.content or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.args, ensure_ascii=False),
                        },
                    }
                    for tc in turn.toolCalls
                ],
            }
            messages.append(assistant_msg)

            # ── 2 단 fan-out: read-only 병렬 + write 시퀀셜 ──
            # turn 안 toolCalls 는 호출자가 의존성 없음 보증 (의존 있으면 다른 turn 분리).
            # blocked / cached path 는 외부 호출 0 ms 라 분류 후 즉시 emit. 새 실행만 partition.
            fresh_read: list[tuple[Any, tuple[str, str]]] = []
            fresh_write: list[tuple[Any, tuple[str, str]]] = []
            blocked_or_cached_in_turn = 0
            for tc in turn.toolCalls:
                cache_key = _ToolCallTracker.keyOf(tc.name, tc.args)
                if tracker.isBlocked(cache_key):
                    yield from _emitBlocked(tc, messages)
                    blocked_or_cached_in_turn += 1
                    continue
                cached = tracker.cachedResult(cache_key)
                if cached is not None:
                    hits = tracker.recordCacheHit(cache_key)
                    yield from _emitCached(tc, cached, hits, tracker.hitLimit, messages)
                    blocked_or_cached_in_turn += 1
                    continue
                (fresh_read if isToolReadOnly(tc.name) else fresh_write).append((tc, cache_key))
                recently_used_tools.add(tc.name)

            # 한 turn 의 모든 tool_calls 가 blocked/cached (새 실행 0 건) → 호출자 헛돌이.
            # 사용자 화면 회귀: EngineCall 한 번 차단 → 또 같은 args → 또 차단 → turn 무한 → OAuth
            # timeout 으로 대화 종료. 도구 한 번 막힌 게 대화 종료까지 가던 흐름의 진짜 원인.
            dead_loop = blocked_or_cached_in_turn > 0 and not fresh_read and not fresh_write
            if dead_loop:
                logger.info("dead-loop: all %d tool_calls blocked/cached → finalize", blocked_or_cached_in_turn)
                yield from _finalize(provider, messages, refs, artifacts, reason="dead_loop")
                _wireChatNativeMemory(question=userText, answerText=text_emitted, refs=refs, kwargs=_unused)
                return

            # Phase 2: read-only 병렬 — tool_start 모두 즉시 + as_completed 로 결과 도착순 emit.
            if fresh_read:
                for tc, _ in fresh_read:
                    yield TraceEvent(
                        "tool_start",
                        {"id": tc.id, "tool": tc.name, "input": tc.args, "summary": f"{tc.name} 호출"},
                    )
                # 작업 단위 함수 (thread 안에서 호출). registry.executeTool 자체는 thread-safe —
                # 각 도구가 자체 캐시/IO 만 건드리고 agent.py 의 mutable state 는 메인 thread 만 변경.
                with ThreadPoolExecutor(max_workers=_PARALLEL_READ_WORKERS) as ex:
                    fut_to_meta = {
                        ex.submit(executeTool, tc.name, tc.args): (tc, cache_key) for tc, cache_key in fresh_read
                    }
                    for fut in as_completed(fut_to_meta):
                        tc, cache_key = fut_to_meta[fut]
                        resultDict = _runOrFallback(fut.result, tc.name, parallel=True)
                        tracker.recordResult(cache_key, tc.name, resultDict)
                        yield from _finalizeResult(tc, resultDict, refs, artifacts, messages)

            # Phase 3: write 시퀀셜 — 순서 의존 가능 (SaveArtifact 덮어쓰기 등).
            for tc, cache_key in fresh_write:
                yield TraceEvent(
                    "tool_start",
                    {"id": tc.id, "tool": tc.name, "input": tc.args, "summary": f"{tc.name} 호출"},
                )
                resultDict = _runOrFallback(lambda tc=tc: executeTool(tc.name, tc.args), tc.name, parallel=False)
                tracker.recordResult(cache_key, tc.name, resultDict)
                yield from _finalizeResult(tc, resultDict, refs, artifacts, messages)

            # PR-O2 — turn 종료 timing emit. stream_first_chunk_ms 는 None 가능 (tool_calls only turn).
            yield TraceEvent(
                "turn_timing",
                {
                    "iter": iteration,
                    "elapsedMs": round((time.monotonic() - turn_start_ms) * 1000.0, 2),
                    "firstChunkMs": (round(stream_first_chunk_ms, 2) if stream_first_chunk_ms is not None else None),
                    "toolCallCount": len(turn.toolCalls),
                },
            )
            continue  # 다시 호출

        # tool_calls 없음 → 정상 종료 (LLM 이 답안 작성 완료)
        if not text_emitted and turn.content:
            # streaming 미지원 provider 가 final.turn.content 에 전체 텍스트
            text_emitted = turn.content
            for piece in _chunks(turn.content, size=64):
                yield TraceEvent("chunk", {"text": piece})
        # PR-O2 — 정상 종료 turn timing.
        yield TraceEvent(
            "turn_timing",
            {
                "iter": iteration,
                "elapsedMs": round((time.monotonic() - turn_start_ms) * 1000.0, 2),
                "firstChunkMs": (round(stream_first_chunk_ms, 2) if stream_first_chunk_ms is not None else None),
                "toolCallCount": 0,
                "final": True,
            },
        )
        _wireChatNativeMemory(question=userText, answerText=text_emitted, refs=refs, kwargs=_unused)
        yield TraceEvent(
            "done",
            {
                "refs": refs,
                "artifacts": artifacts,
                # chat-native 경로는 GATE 를 돌리지 않는다. 검증을 안 했는데 통과했다고
                # 적으면 이 값을 읽는 쪽이 검증된 답으로 오해한다. 안 했으면 안 했다고 쓴다.
                "verification": {"ok": None, "issues": [], "note": "chat-native 경로는 GATE 미실행"},
                "responseMeta": {
                    "finalEvent": "answer",
                    "responseStatus": "ok",
                    "refCount": len(refs),
                    "passes": ["agent", "memory"],
                    "mode": "agent",
                },
            },
        )
        return

    # for-loop 가 break 없이 끝난 경로 = max_iterations 도달.
    yield from _finalize(provider, messages, refs, artifacts, reason="max_iter")
    _wireChatNativeMemory(question=userText, answerText=text_emitted, refs=refs, kwargs=_unused)


def _emitBlocked(tc: Any, messages: list[dict[str, Any]]) -> Iterator[TraceEvent]:
    """차단된 도구 호출 — tool_start + tool_result(error) + tool message 한 묶음 emit."""
    yield TraceEvent(
        "tool_start",
        {"id": tc.id, "tool": tc.name, "input": tc.args, "summary": f"{tc.name} 차단됨"},
    )
    yield TraceEvent(
        "tool_result",
        {
            "id": tc.id,
            "tool": tc.name,
            "status": "error",
            "outputSummary": f"{tc.name} 반복 실패 — 호출 차단",
            "evidenceRefs": [],
            "artifacts": [],
            "error": "tool_blocked_after_repeated_failures",
            "data": None,
        },
    )
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(
                {
                    "ok": False,
                    "summary": f"{tc.name} 가 직전 turn 에서 반복 실패해 차단됨. 본 도구 다시 호출 금지. 지금까지 모은 정보로 답변 작성하거나 다른 도구 사용.",
                    "data": None,
                    "error": "tool_blocked_after_repeated_failures",
                },
                ensure_ascii=False,
            ),
        }
    )


# Finalize SSOT — 답안 작성 한 round 강제하는 모든 종료 경로의 단일 진입점.
# 3 reason 지원: provider_error / dead_loop / max_iter. 호출자는 reason 만 결정.
# 옛 회귀: 같은 패턴 (_forceFinalize · _emitGracefulFinalize · _buildRefSummaryFallback) 3 helper
# 가 80% 중복이라 instruction/done 분기를 manual 동기화. SSOT 위반 → 통합.

_FINALIZE_INSTRUCTIONS: dict[str, str] = {
    "provider_error": (
        "분석 중 일시 오류가 발생했습니다. 추가 도구 호출 없이, 지금까지 받은 "
        "도구 결과만으로 사용자 질문에 부분 답안을 작성하세요. 못 받은 정보는 "
        "솔직히 한계로 명시하세요."
    ),
    "dead_loop": (
        "직전 turn 의 모든 도구 호출이 차단/캐시 hit 으로 새 결과 0 건이었습니다. "
        "추가 도구 호출 없이 지금까지 모은 결과로 사용자 질문에 답을 작성하세요. "
        "근거 부족은 솔직히 한계로 명시하세요."
    ),
    "max_iter": (
        "도구 호출 한도에 도달했습니다. 추가 도구 호출 없이 지금까지 "
        "수집한 결과로 사용자 질문에 답을 작성하세요. 근거 부족 부분은 "
        "솔직히 한계로 명시하고, 가능한 범위에서 답을 정리하세요."
    ),
}
_FINALIZE_STATUS: dict[str, str] = {
    "provider_error": "partial",
    "dead_loop": "partial",
    "max_iter": "ok",
}


def _finalize(
    provider: Any,
    messages: list[dict[str, Any]],
    refs: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    *,
    reason: str,
    originalExc: Exception | None = None,
) -> Iterator[TraceEvent]:
    """답안 작성 한 round + done event. 모든 종료 경로의 SSOT.

    흐름:
      1. reason 별 instruction messages 에 append
      2. tools=[] 로 streamProvider 한 round (LLM 답안 작성)
      3. 그 round 도 실패 → _refSummaryText fallback 텍스트 emit (LLM 0 호출)
      4. done event emit (reason → responseStatus 매핑)
    """
    instruction = _FINALIZE_INSTRUCTIONS.get(reason, _FINALIZE_INSTRUCTIONS["max_iter"])
    messages.append({"role": "user", "content": instruction})

    text_added = ""
    try:
        final_chunk = None
        for chunk in streamProvider(provider, messages, []):
            if chunk.final:
                final_chunk = chunk
                continue
            if chunk.text:
                text_added += chunk.text
                yield TraceEvent("chunk", {"text": chunk.text})
        if final_chunk and not text_added and getattr(final_chunk, "turn", None) and final_chunk.turn.content:
            for piece in _chunks(final_chunk.turn.content, size=64):
                yield TraceEvent("chunk", {"text": piece})
    except Exception as exc:  # noqa: BLE001
        logger.exception("finalize round failed (reason=%s)", reason)
        yield TraceEvent("error", {"error": f"{type(exc).__name__}: {exc}", "recoverable": True})
        fallback = _refSummaryText(refs, originalExc or exc)
        for piece in _chunks(fallback, size=64):
            yield TraceEvent("chunk", {"text": piece})

    yield TraceEvent(
        "done",
        {
            "refs": refs,
            "artifacts": artifacts,
            "verification": {"ok": None, "issues": [reason], "note": "chat-native 경로는 GATE 미실행"},
            "responseMeta": {
                "finalEvent": "answer",
                "responseStatus": _FINALIZE_STATUS.get(reason, "ok"),
                "refCount": len(refs),
                "passes": ["agent", "finalize", reason],
                "mode": "agent",
            },
        },
    )


def _refSummaryText(refs: list[dict[str, Any]], cause: Exception) -> str:
    """LLM 0 호출 fallback 텍스트 — 모든 LLM 경로 실패 시 마지막 보루."""
    lines = [f"⚠ 분석 도중 오류 발생 ({type(cause).__name__}). 모은 자료만 정리합니다.", ""]
    if not refs:
        lines.append("아직 받은 자료가 없습니다. 잠시 후 다시 시도하세요.")
        return "\n".join(lines)
    table_refs = [r for r in refs if r.get("kind") == "tableRef"]
    value_refs = [r for r in refs if r.get("kind") == "valueRef"]
    lines.append(f"확보 근거: tableRef {len(table_refs)} · valueRef {len(value_refs)} · 전체 {len(refs)} 건")
    lines.append("")
    for r in table_refs[:5]:
        lines.append(f"- {r.get('title') or r.get('id')}")
    if len(table_refs) > 5:
        lines.append(f"- ... (외 {len(table_refs) - 5} 건)")
    lines.append("")
    lines.append("재시도하면 같은 근거를 활용해 답을 다시 작성합니다.")
    return "\n".join(lines)


def _emitCached(
    tc: Any,
    cached: dict[str, Any],
    hitN: int,
    hitBlockLimit: int,
    messages: list[dict[str, Any]],
) -> Iterator[TraceEvent]:
    """cached 호출 — 동일 (name, args) 재호출 시 즉시 응답. hitBlockLimit 초과 시 강제 차단."""
    yield TraceEvent(
        "tool_start",
        {"id": tc.id, "tool": tc.name, "input": tc.args, "summary": f"{tc.name} 호출"},
    )
    is_blocked = hitN >= hitBlockLimit
    cached_summary = str(cached.get("summary") or "")
    if is_blocked:
        llmGuardNote = (
            f"{tc.name} 가 같은 인자로 {hitN} 회 반복 호출됨 — 본 인자 재호출 영구 차단. "
            f"다른 도구나 답변 작성으로 진행."
        )
    else:
        llmGuardNote = f"(cached) 같은 인자로 이미 호출됨 — 다시 부르지 마라. 직전 결과: {cached_summary[:120]}"
    uiSummary = f"(반복 차단) 같은 인자 {hitN} 회 — 더 부르지 않음" if is_blocked else f"(캐시됨) {cached_summary[:80]}"
    yield TraceEvent(
        "tool_result",
        {
            "id": tc.id,
            "tool": tc.name,
            "status": "done" if cached.get("ok") and not is_blocked else "error",
            "outputSummary": uiSummary,
            "evidenceRefs": [ref.get("id") for ref in cached.get("refs") or [] if ref.get("id")],
            "artifacts": [r for r in cached.get("refs") or [] if r.get("kind") == "artifactRef"],
            "error": cached.get("error") if not is_blocked else "duplicate_cache_call_blocked",
            "data": cached.get("data") if not is_blocked else None,
            "cached": True,
        },
    )
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(
                {
                    "ok": cached.get("ok") if not is_blocked else False,
                    "cached": True,
                    "summary": llmGuardNote,
                    "data": None,
                    "error": cached.get("error") if not is_blocked else "duplicate_cache_call_blocked",
                },
                ensure_ascii=False,
            ),
        }
    )


class _ToolCallTracker:
    """도구 호출 상태 SSOT — cache / blocked / cacheHit / failureStreak 통합.

    옛 4 변수 (failure_streak / blocked_calls / call_cache / cache_hit_count) 가 runAgent 본문
    inline + 매 회 manual 동기화. 호출자는 keyOf / isBlocked / cachedResult / recordCacheHit /
    recordResult 5 메서드만 안다. state mutation 은 모두 내부.
    """

    def __init__(self, *, failureStreakLimit: int, cacheHitBlockLimit: int) -> None:
        self._cache: dict[tuple[str, str], dict[str, Any]] = {}
        self._blocked: set[tuple[str, str]] = set()
        self._cacheHits: dict[tuple[str, str], int] = {}
        self._failStreak: dict[tuple[str, str, str], int] = {}
        self._failLimit = failureStreakLimit
        self._hitLimit = cacheHitBlockLimit

    @staticmethod
    def keyOf(name: str, args: Any) -> tuple[str, str]:
        """(도구명, args JSON-serialized) — 동일 호출 동등성 키."""
        return (name, json.dumps(args or {}, ensure_ascii=False, sort_keys=True, default=str))

    @property
    def hitLimit(self) -> int:
        """cache hit block limit — _emitCached UI 메시지 분기용으로 노출."""
        return self._hitLimit

    def isBlocked(self, key: tuple[str, str]) -> bool:
        """영구 차단 set 검사."""
        return key in self._blocked

    def cachedResult(self, key: tuple[str, str]) -> dict[str, Any] | None:
        """캐시된 결과 (없으면 None)."""
        return self._cache.get(key)

    def recordCacheHit(self, key: tuple[str, str]) -> int:
        """cache hit 카운트 + limit 도달 시 자동 blocked 등록. 현재 hit 수 반환."""
        self._cacheHits[key] = self._cacheHits.get(key, 0) + 1
        if self._cacheHits[key] >= self._hitLimit:
            self._blocked.add(key)
        return self._cacheHits[key]

    def recordResult(self, key: tuple[str, str], name: str, result: dict[str, Any]) -> None:
        """새 실행 결과 저장 + failure streak 갱신. limit 도달 시 자동 blocked 등록.

        실패한 결과는 캐시에 넣지 않는다. 넣으면 같은 인자로 다시 부를 때 실행 대신 cache hit
        으로 가로채이고, hit 한 번이면 곧바로 영구 차단이라 failure streak 이 둘까지 갈 일이
        없다. 한 번의 일시적 실패가 그 세션 내내 그 도구를 막았다. streak 이 재시도를 맡는다.
        """
        argsHash = key[1]
        if result.get("ok"):
            self._cache[key] = result
        if not result.get("ok"):
            errKey = str(result.get("error") or "unknown")
            streakKey = (name, errKey, argsHash)
            self._failStreak[streakKey] = self._failStreak.get(streakKey, 0) + 1
            if self._failStreak[streakKey] >= self._failLimit:
                self._blocked.add(key)
        else:
            # 같은 도구 + 같은 args 성공 → 그 args 의 모든 error streak 리셋.
            for k in [k for k in self._failStreak if k[0] == name and k[2] == argsHash]:
                self._failStreak.pop(k, None)


def _runOrFallback(executor: Any, toolName: str, *, parallel: bool) -> dict[str, Any]:
    """도구 실행 + uncaught 예외를 표준 error result dict 로 변환. 병렬/순차 공통 패턴 SSOT."""
    try:
        return executor()
    except Exception as exc:  # noqa: BLE001
        logger.exception("tool %s threw uncaught (%s)", toolName, "parallel" if parallel else "sequential")
        return {
            "ok": False,
            "summary": f"{toolName} 실행 오류: {type(exc).__name__}",
            "data": None,
            "error": type(exc).__name__,
            "refs": [],
        }


def _finalizeResult(
    tc: Any,
    resultDict: dict[str, Any],
    refs: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    messages: list[dict[str, Any]],
) -> Iterator[TraceEvent]:
    """새 실행 결과 후처리 — tool_result emit + visualRef view_spec + tool message append.

    state mutation (failure streak / blocked set) 은 호출 직전 _ToolCallTracker.recordResult 가
    이미 처리. 본 함수는 순수 emit + messages.append.
    """
    tool_refs = list(resultDict.get("refs") or [])
    refs.extend(tool_refs)
    tool_artifacts = [ref for ref in tool_refs if ref.get("kind") == "artifactRef"]
    artifacts.extend(tool_artifacts)
    yield TraceEvent(
        "tool_result",
        {
            "id": tc.id,
            "tool": tc.name,
            "status": "done" if resultDict.get("ok") else "error",
            "outputSummary": resultDict.get("summary", ""),
            "evidenceRefs": [ref.get("id") for ref in tool_refs if ref.get("id")],
            "refDetails": tool_refs,
            "artifacts": tool_artifacts,
            "error": resultDict.get("error"),
            "data": resultDict.get("data"),
        },
    )
    for ref in tool_refs:
        if ref.get("kind") != "visualRef":
            continue
        payload = ref.get("payload") or {}
        spec = payload.get("spec") if isinstance(payload, dict) else None
        if not spec:
            continue
        yield TraceEvent(
            "view_spec",
            {
                "id": ref.get("id"),
                "spec": spec,
                "title": ref.get("title"),
                "source": ref.get("source"),
            },
        )
    wrapped = wrapExternalInResult(resultDict)
    # refs 는 ref id + kind + title + source + payload 핵심 키만 직렬화 — token 절약하면서
    # 답변 inline 인용에 필요한 최소 정보 (id, source 식별자) 는 보존.
    # 회귀 가드: refs 누락 시 LLM 이 답변 본문에 [ref:...] 박을 수 없어 refs=0 답변.
    wrapped_refs = wrapped.get("refs") or []
    refs_for_llm = [
        {
            "id": r.get("id"),
            "kind": r.get("kind"),
            "title": r.get("title"),
            "source": r.get("source"),
            "sourceType": r.get("sourceType", "internal"),
            **({"payload": _trimRefPayload(r.get("payload") or {})} if r.get("payload") else {}),
        }
        for r in wrapped_refs
        if isinstance(r, dict) and r.get("id")
    ]
    content_str = json.dumps(
        {
            "ok": wrapped.get("ok"),
            "summary": wrapped.get("summary", ""),
            "data": wrapped.get("data"),
            "refs": refs_for_llm,
            "error": wrapped.get("error"),
        },
        ensure_ascii=False,
        default=str,
    )
    if exceedsSizeCap(content_str):
        preview, file_path = persistLargeResult(tc.name, tc.id, content_str)
        content_str = buildPersistedContent(file_path, preview, len(content_str))
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tc.id,
            "content": content_str,
        }
    )


_REF_PAYLOAD_KEYS = (
    "stockCode",
    "period",
    "metric",
    "value",
    "unit",
    "docId",
    "page",
    "lineStart",
    "lineEnd",
    "confidence",
    "dataAsOf",
    "axis",
    "axisKr",
    "stmt",
    # 외부 본문 키. 이것이 빠져 있어서 `wrapExternalInResult` 가 감싼 값이 세 줄 뒤에
    # 통째로 잘려 나갔다. 결과가 두 가지였다. untrusted 마커가 모델에 한 번도 닿지 않았고,
    # webSearch 는 제목과 URL 만 보내는 셈이라 본문이 아예 전달되지 않았다.
    # 아래 키는 `tools.formatting._EXTERNAL_TEXT_KEYS` 와 같은 자리를 가리킨다.
    "snippet",
    "text",
    "abstract",
    "body",
    "content",
    "excerpt",
    "headline",
)


def _trimRefPayload(payload: dict[str, Any]) -> dict[str, Any]:
    """ref.payload 에서 LLM 인용에 필요한 핵심 키만 유지. token 절약.

    핵심 키 (`stockCode` · `period` · `metric` · `value` · `docId` · `page` · `confidence` 등)
    와 외부 본문 키만 유지. 나머지 (예: 5MB raw DataFrame 직렬화) 는 drop. LLM 은 ref id 로
    inline 인용, 상세 본문은 UI 가 별도 fetch.
    """
    return {k: payload[k] for k in _REF_PAYLOAD_KEYS if k in payload}


def _injectPastContextIfAvailable(
    systemPrompt: str,
    kwargs: dict[str, Any],
    *,
    history: list[dict[str, Any]] | None = None,
) -> str:
    """kwargs 의 보조 컨텍스트를 system prompt 에 부착.

    블록:
        1. dashboardSnapshot 이 있으면 "현재 화면" 블록 (Phase 8 bridge)
        2. 운영자 톤 (feedback_*.md 합성기, 7 일 TTL 캐시)
        3. dialectic user context (장기 interest profile + 본 세션 intent, history 결정론 통계)

    빈 문자열이면 섹션 헤더 자체 부재 — 환각 가드.
    """
    snapshot = kwargs.get("dashboardSnapshot")
    if isinstance(snapshot, dict):
        block = _formatDashboardSnapshotBlock(snapshot)
        if block:
            systemPrompt = f"{systemPrompt}\n\n## 현재 대시보드 화면 (사용자 시야, 신뢰)\n{block}\n"

    # 운영자 톤 메타 블록 — feedback_*.md 합성기가 7 일 TTL 또는 memory mtime 변경 시
    # 재계산. 답변 톤 일관성 확보 (자동 sweep 회피·운영자 명시 트리거·측정 후 박기).
    # 캐시 hit 시 디스크 1 회 read 만 — turn 추가 비용 최소.
    try:
        from .memory.synthesizer import buildToneBlock

        tone_block = buildToneBlock()
    except Exception:  # noqa: BLE001
        tone_block = ""
    if tone_block:
        systemPrompt = f"{systemPrompt}\n\n{tone_block}"

    # dialectic user context — 장기 누적 interest (sessionIndex.db) + 본 세션 의도
    # (history 결정론 분석). 매 turn 호출이지만 profile 은 7 일 TTL 캐시 + intent 는
    # in-memory 빠른 통계라 비용 작다. 답변 톤·우선순위를 사용자 패턴에 맞추는 핵심.
    try:
        from .memory.dialectic import buildFeedbackSignalsBlock, buildUserContextBlock

        user_block = buildUserContextBlock(history)
        feedback_block = buildFeedbackSignalsBlock()
    except Exception:  # noqa: BLE001
        user_block = ""
        feedback_block = ""
    if user_block:
        systemPrompt = f"{systemPrompt}\n\n{user_block}"
    if feedback_block:
        # 피드백 시그널은 컨텍스트 *끝* — 가장 최근 학습 신호라 LLM 우선 활용.
        systemPrompt = f"{systemPrompt}\n\n{feedback_block}"

    # 마스터 플랜 트랙 3 PR-W3 — workbench/targets._buildQuestionProfile 본체 흡수.
    # 사용자 질문에서 taskType / targets / comparison / showTopic 추정 → tool 선택 가이드.
    # workbench 의 옵션 sub-agent 도 동일 helper 를 사용 — 본 호출은 *읽기만*, graph 회귀 0.
    intent_block = _formatIntentProfileBlock(kwargs)
    if intent_block:
        systemPrompt = f"{systemPrompt}\n\n{intent_block}"

    return systemPrompt


def _formatIntentProfileBlock(kwargs: dict[str, Any]) -> str:
    """workbench/targets._buildQuestionProfile 결과 → system prompt markdown 블록.

    질문 의도 추정으로 LLM 의 tool 선택 가이드 — 예: comparison=True 면 PeerCompareN
    먼저, showTopic='IS' 면 EngineCall(Company.panel, topic='IS') 우선 등.
    """
    # 질문은 caller (server/agent_gateway) 가 history 마지막 user msg 또는 kwargs.question
    # 으로 전달. 본 helper 는 정보 없으면 빈 문자열 반환 (안전).
    question = str(kwargs.get("question") or "").strip()
    stockCode = kwargs.get("stockCode")
    if not question and not stockCode:
        return ""
    try:
        from .workbench.targets import _buildQuestionProfile

        profile = _buildQuestionProfile(question, stockCode=stockCode)
    except Exception:  # noqa: BLE001
        return ""

    targets = profile.get("targets") or []
    comparison = profile.get("comparison")
    show_topic = profile.get("showTopic")
    task_type = profile.get("taskType")
    if not targets and not show_topic and task_type == "research":
        return ""

    lines: list[str] = ["## 질문 의도 추정 (참고 — LLM 자율 도구 선택 가이드)"]
    if task_type:
        lines.append(f"- 작업 유형: `{task_type}`")
    if targets:
        lines.append(f"- 추정 종목: {', '.join(f'`{t}`' for t in targets[:5])}")
    if comparison:
        lines.append("- 비교형 질문 — `PeerCompareN` (2~12 종목) 1 회 호출 우선.")
    if show_topic:
        lines.append(f"- 추정 토픽: `{show_topic}` — `EngineCall(Company.panel, topic='{show_topic}')` 우선.")
    # 마스터 플랜 v2 트랙 6 PR-L2 — trigger 표 dynamic inline (system prompt 압축 대체).
    # 기존 §"분석 의도 → 금융 primitive 도구 매핑" 9 row 평면 표 (~1500 자) 가 매 turn
    # 송신 → trigger 매칭된 도구만 표시 (평균 1~2 row, ~150 자). 매 turn token ~290 절감.
    try:
        from .workbench.prompts import matchTriggerHints

        hints = matchTriggerHints(question)
    except Exception:  # noqa: BLE001
        hints = []
    if hints:
        lines.append("- 권장 금융 primitive 도구 (질문 trigger 매칭):")
        for toolSig, hint in hints[:3]:
            lines.append(f"  - `{toolSig}` — {hint}")
    return "\n".join(lines)


def _formatDashboardSnapshotBlock(snapshot: dict[str, Any]) -> str:
    """dashboardStore.snapshot() 페이로드를 markdown bullet 으로 변환.

    페이로드 shape: {dashboardView, stockCode, axis, period, visibleKpis: [...]}
    사용자 시야 데이터라 외부 untrusted 마커 없이 trusted block 으로 삽입.
    """
    lines: list[str] = []
    view = snapshot.get("dashboardView")
    if view:
        lines.append(f"- 탭: `{view}`")
    code = snapshot.get("stockCode")
    if code:
        lines.append(f"- 회사: `{code}`")
    axis = snapshot.get("axis")
    if axis:
        lines.append(f"- 분석 axis: `{axis}`")
    period = snapshot.get("period")
    if period:
        lines.append(f"- 기간: `{period}`")
    kpis = snapshot.get("visibleKpis")
    if isinstance(kpis, list) and kpis:
        kpi_strs = []
        for kpi in kpis:
            if isinstance(kpi, dict) and "name" in kpi and "value" in kpi:
                kpi_strs.append(f"{kpi['name']}={kpi['value']}")
            else:
                kpi_strs.append(str(kpi))
        if kpi_strs:
            lines.append(f"- 보이는 KPI: {', '.join(kpi_strs)}")
    return "\n".join(lines)


def _wireChatNativeMemory(
    *, question: str, answerText: str, refs: list[dict[str, Any]], kwargs: dict[str, Any]
) -> None:
    """agent.py 종료 시 memory wiring — workbench/harvest.py 와 동일 helper 사용."""
    from .contracts import Ref
    from .memory.wiring import inferStockCodeContext, wireSessionMemory

    ref_objects: list[Ref] = []
    for raw in refs:
        if not isinstance(raw, dict):
            continue
        ref_objects.append(
            Ref(
                id=str(raw.get("id") or ""),
                kind=str(raw.get("kind") or ""),
                title=str(raw.get("title") or ""),
                source=str(raw.get("source") or ""),
                payload=raw.get("payload") if isinstance(raw.get("payload"), dict) else {},
            )
        )

    extra_tags: list[str] = []
    stockCode, market = inferStockCodeContext(ref_objects, kwargs=kwargs)
    if stockCode:
        extra_tags.append(f"target:{stockCode}")
    if market:
        extra_tags.append(f"market:{market}")

    wireSessionMemory(
        question=question,
        answerText=answerText,
        refs=ref_objects,
        selectedSkillRefs=(r for r in ref_objects if r.kind == "skillRef"),
        ok=True,
        extraTags=extra_tags,
    )


def _selectTools(
    toolNames: tuple[str, ...],
    *,
    recentlyUsed: set[str] | None = None,
) -> list[dict[str, Any]]:
    """toolSpecs() raw dict ({name, description, inputSchema}) → OpenAI function calling 형식.

    각 provider 가 자체 toolSchema 변환 가지면 호출자가 별도 처리. 본 helper 는 OpenAI 호환만.

    ``recentlyUsed`` 가 None (turn 1) → ``toolNames`` 전체.
    ``recentlyUsed`` 가 set (turn 2+) → ``_CORE_TOOL_NAMES ∪ recentlyUsed`` 와의 교집합.
    회귀 가드: ``recentlyUsed`` 가 비어 있어도 ``_CORE_TOOL_NAMES`` 가 항상 포함되어 turn 2+ 에
    새 도구 호출 가능. ``feedback_no_graph_regression.md`` 의 강박 노드 추가 아님.
    """
    if recentlyUsed is not None:
        narrow_allow = _CORE_TOOL_NAMES | recentlyUsed
        allowed = set(toolNames) & narrow_allow
    else:
        allowed = set(toolNames)
    out: list[dict[str, Any]] = []
    for spec in toolSpecs():
        if not isinstance(spec, dict):
            continue
        name = spec.get("name")
        if name not in allowed:
            continue
        out.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": spec.get("description", ""),
                    "parameters": spec.get("inputSchema", {"type": "object", "properties": {}}),
                },
            }
        )
    return out


def _chunks(text: str, *, size: int = 240) -> Iterator[str]:
    for index in range(0, len(text), size):
        yield text[index : index + size]


def _microcompact(messages: list[dict[str, Any]], *, keepLast: int = 2) -> None:
    """오래된 assistant message 의 reasoning content 를 None 으로 (in-place).

    tool_calls 구조는 보존 — provider 들이 tool result 매칭에 필요. 마지막 keep_last 개의
    assistant message 는 reasoning 유지 (직전 추론 흐름 단절 방지).

    회귀 가드: graph 노드 추가 아님. messages 배열 트리밍만.
    memory/feedback_no_graph_regression.md 6 패턴과 무관.
    """
    ai_indices = [i for i, msg in enumerate(messages) if isinstance(msg, dict) and msg.get("role") == "assistant"]
    if len(ai_indices) <= keepLast:
        return
    for idx in ai_indices[:-keepLast]:
        msg = messages[idx]
        if msg.get("tool_calls") and msg.get("content"):
            msg["content"] = None


def _traceDumpEnabled() -> bool:
    """환경변수 ``DARTLAB_AI_TRACE_DUMP`` 활성 검사 — 기본 OFF."""
    return os.getenv("DARTLAB_AI_TRACE_DUMP", "").lower() in ("1", "true", "yes")


def _resolveTraceDir() -> Path:
    """trace dump 디렉토리 — ``~/.dartlab/ai_trace/``.

    환경변수 ``DARTLAB_AI_TRACE_DIR`` override 가능 (PII 우려 시 사용자 명시 경로).
    """
    custom = os.getenv("DARTLAB_AI_TRACE_DIR")
    if custom:
        return Path(custom)
    return Path.home() / ".dartlab" / "ai_trace"


def _pruneOldTraces(directory: Path, *, retentionDays: int = 7) -> None:
    """7 일 retention rotate — 오래된 trace 파일 정리. 디스크 비대 가드."""
    if not directory.is_dir():
        return
    cutoff = time.time() - retentionDays * 86400
    for path in directory.glob("*.json"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            continue


def _wrapWithAuditDump(*, question: str, provider: Any, rawIter: Iterator[TraceEvent]) -> Iterator[TraceEvent]:
    """runAgent 의 TraceEvent stream 을 가로채 AuditCollector 누적 + 종료 시 dump.

    환경변수 ``DARTLAB_AI_TRACE_DUMP=1`` 활성 시만 호출. 모든 TraceEvent 가 pass-through
    + collector 동행. 본 wrapper 자체는 yield 흐름 변경 0 — SSE 소비자 영향 0.
    """
    from .trace import AuditCollector

    cfg = getattr(provider, "config", None)
    collector = AuditCollector(
        question=question,
        provider=getattr(cfg, "provider", None),
        model=getattr(cfg, "model", None),
    )
    try:
        for ev in rawIter:
            try:
                collector.observe(ev.kind, ev.data)
            except Exception:  # noqa: BLE001
                logger.exception("audit observe failed (kind=%s)", ev.kind)
            yield ev
    finally:
        try:
            trace_dir = _resolveTraceDir()
            trace_dir.mkdir(parents=True, exist_ok=True)
            _pruneOldTraces(trace_dir, retentionDays=7)
            collector.dumpToJson(trace_dir / f"{collector.sessionId}.json")
        except Exception:  # noqa: BLE001
            logger.exception("ai trace dump failed")


__all__ = ["runAgent"]
