"""AI 분석 실행 모드 — light / guided_json / stream / agent.

core.py의 _analyze_inner()에서 디스패치하는 4가지 실행 경로.
"""

from __future__ import annotations

import json
from typing import Any, Generator

from dartlab.engines.ai.runtime.events import AnalysisEvent, EventKind

# ── Light mode ────────────────────────────────────────────


def _run_light_mode(
    company: Any,
    question: str,
    config_: Any,
    state: Any,
    *,
    focus_context: str | None,
    history_messages: list[dict] | None,
    dialogue_policy: str | None,
    emit_system_prompt: bool,
    _full_response_parts: list[str],
) -> Generator[AnalysisEvent, None, None]:
    """분석 의도 없을 때 — 간략 회사 컨텍스트 + 대화 프롬프트."""
    from dartlab.engines.ai.conversation.prompts import build_dynamic_chat_prompt
    from dartlab.engines.ai.providers import create_provider

    if focus_context:
        yield AnalysisEvent(
            "context",
            {
                "module": "_focus_topic",
                "label": f"현재 섹션: {getattr(state, 'topic_label', '') or getattr(state, 'topic', '')}",
                "text": focus_context,
            },
        )

    # 간략 회사 컨텍스트
    light_company_ctx = "\n\n## 현재 대화 종목\n"
    light_company_ctx += f"사용자가 **{company.corpName}** ({getattr(company, 'stockCode', getattr(company, 'ticker', ''))})에 대해 이야기하고 있습니다.\n"

    # insights 등급 1줄 요약
    try:
        from dartlab.engines.analysis.insight.pipeline import analyze as _light_analyze

        _light_result = _light_analyze(
            getattr(company, "stockCode", getattr(company, "ticker", "")),
            company=company,
        )
        if _light_result is not None:
            _grades = _light_result.grades()
            _grade_str = " / ".join(
                f"{lbl}:{_grades.get(k, 'N')}"
                for k, lbl in [
                    ("performance", "실적"),
                    ("profitability", "수익성"),
                    ("health", "건전성"),
                    ("cashflow", "CF"),
                    ("governance", "지배구조"),
                    ("risk", "리스크"),
                    ("opportunity", "기회"),
                ]
                if _grades.get(k)
            )
            light_company_ctx += f"- 인사이트 등급: {_grade_str}\n"
            if _light_result.profile:
                light_company_ctx += f"- 프로파일: {_light_result.profile}\n"
    except (ImportError, AttributeError, FileNotFoundError, OSError, RuntimeError, TypeError, ValueError):
        pass

    # topics 상위 10개
    try:
        _topics = list(getattr(company, "topics", None) or [])[:10]
        if _topics:
            light_company_ctx += f"- 조회 가능 topic(일부): {', '.join(_topics)}\n"
    except (AttributeError, TypeError):
        pass

    light_company_ctx += (
        "\n아직 구체적 분석 요청은 아닙니다. 가볍게 대화하되, "
        "분석이 필요하면 어떤 분석을 원하는지 물어보세요.\n"
        "예: '어떤 분석을 원하시나요? 재무 건전성, 수익성, 배당, 종합 분석 등을 해드릴 수 있습니다.'"
    )

    light_prompt = build_dynamic_chat_prompt(state) + light_company_ctx

    if emit_system_prompt:
        yield AnalysisEvent("system_prompt", {"text": light_prompt})

    messages: list[dict[str, str]] = [{"role": "system", "content": light_prompt}]
    if history_messages:
        messages.extend(history_messages)

    user_text = question
    if focus_context:
        user_text = f"{focus_context}\n\n---\n\n질문: {question}"
    messages.append({"role": "user", "content": user_text})

    llm = create_provider(config_)
    for chunk in llm.stream(messages):
        _full_response_parts.append(chunk)
        yield AnalysisEvent("chunk", {"text": chunk})


# ── Guided JSON ───────────────────────────────────────────


def _run_guided_json(
    llm,
    messages: list[dict],
    _full_response_parts: list[str],
    _done_payload: dict[str, Any],
) -> Generator[AnalysisEvent, None, None]:
    """Compact provider용 guided JSON → markdown 변환."""
    from dartlab.engines.ai.conversation.prompts import guided_json_to_markdown
    from dartlab.engines.ai.conversation.templates.self_critique import GUIDED_SCHEMA

    resp = llm.complete_json(messages, GUIDED_SCHEMA)
    raw_json = resp.answer
    try:
        parsed = json.loads(raw_json)
        md_text = guided_json_to_markdown(parsed)
        _done_payload["guidedRaw"] = parsed
        if parsed.get("grade"):
            _done_payload["responseMeta"] = {
                "grade": parsed["grade"],
                "has_conclusion": bool(parsed.get("conclusion")),
                "signals": {
                    "positive": [p[:20] for p in parsed.get("positives", [])[:3]],
                    "negative": [
                        r.get("description", "")[:20] for r in parsed.get("risks", [])[:3] if isinstance(r, dict)
                    ],
                },
                "tables_count": 1,
            }
    except (json.JSONDecodeError, ValueError):
        md_text = raw_json

    _full_response_parts.append(md_text)
    # 단락별 yield
    paragraphs = md_text.split("\n\n")
    for i, para in enumerate(paragraphs):
        chunk_text = para if i == len(paragraphs) - 1 else para + "\n\n"
        yield AnalysisEvent("chunk", {"text": chunk_text})


# ── Stream mode ──────────────────────────────────────────


def _run_stream(
    llm,
    messages: list[dict],
    _full_response_parts: list[str],
) -> Generator[AnalysisEvent, None, None]:
    """직접 스트리밍 — 도구 없이 LLM 응답 chunk를 yield."""
    for chunk in llm.stream(messages):
        _full_response_parts.append(chunk)
        yield AnalysisEvent("chunk", {"text": chunk})


# ── Agent mode ───────────────────────────────────────────


def _run_agent(
    llm,
    messages: list[dict],
    company: Any,
    question: str,
    *,
    max_turns: int = 5,
    max_tools: int | None = None,
    q_type: str | None = None,
    useSuperTools: bool = False,
    _full_response_parts: list[str],
) -> Generator[AnalysisEvent, None, None]:
    """에이전트 모드 — 도구 호출 + 스트리밍 응답."""
    from dartlab.engines.ai.runtime.agent import agent_loop_stream, build_agent_system_addition
    from dartlab.engines.ai.tools.registry import build_tool_runtime

    runtime = build_tool_runtime(company, name="core-agent", useSuperTools=useSuperTools)

    system_addition = build_agent_system_addition(runtime)
    messages[0]["content"] += system_addition

    tool_calls_log: list[dict] = []
    tool_results_log: list[dict] = []
    chart_events: list[dict] = []
    ui_events: list[AnalysisEvent] = []

    def _on_tool_call(name: str, arguments: dict) -> None:
        tool_calls_log.append({"name": name, "arguments": arguments})

    def _on_tool_result(name: str, result: str) -> None:
        tool_results_log.append({"name": name, "result": result})
        # create_chart 도구 결과에서 ChartSpec 추출
        if name == "create_chart":
            try:
                parsed = json.loads(result)
                charts = parsed.get("charts")
                if charts:
                    chart_events.append({"charts": charts})
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        # UI 도구 결과는 canonical ui_action만 전달한다.
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict) and parsed.get("action"):
                ui_events.append(AnalysisEvent(EventKind.UI_ACTION, parsed))
        except (json.JSONDecodeError, TypeError):
            pass

    for chunk in agent_loop_stream(
        llm,
        messages,
        company,
        max_turns=max_turns,
        max_tools=max_tools,
        runtime=runtime,
        on_tool_call=_on_tool_call,
        on_tool_result=_on_tool_result,
        question_type=q_type,
    ):
        # tool call/result/chart/ui 이벤트를 먼저 flush
        while tool_calls_log:
            tc = tool_calls_log.pop(0)
            yield AnalysisEvent("tool_call", tc)
        while tool_results_log:
            tr = tool_results_log.pop(0)
            yield AnalysisEvent("tool_result", tr)
        while chart_events:
            ce = chart_events.pop(0)
            yield AnalysisEvent("chart", ce)
        while ui_events:
            yield ui_events.pop(0)

        _full_response_parts.append(chunk)
        yield AnalysisEvent("chunk", {"text": chunk})

    # 남은 이벤트 flush
    while tool_calls_log:
        yield AnalysisEvent("tool_call", tool_calls_log.pop(0))
    while tool_results_log:
        yield AnalysisEvent("tool_result", tool_results_log.pop(0))
    while chart_events:
        yield AnalysisEvent("chart", chart_events.pop(0))
    while ui_events:
        yield ui_events.pop(0)
