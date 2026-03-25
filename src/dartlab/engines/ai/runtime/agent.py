"""Tool-use 에이전트 루프.

LLM이 필요한 도구를 직접 선택하여 반복적으로 분석을 수행한다.
OpenAI function calling 프로토콜을 사용.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Generator

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.tools.registry import (
    build_tool_runtime,
)
from dartlab.engines.ai.tools.runtime import ToolRuntime
from dartlab.engines.ai.tools.selector import selectTools


def agent_loop(
    provider: BaseProvider,
    messages: list[dict],
    company: Any,
    *,
    max_turns: int = 5,
    max_tools: int | None = None,
    runtime: ToolRuntime | None = None,
    on_tool_call: Callable[[str, dict], None] | None = None,
    on_tool_result: Callable[[str, str], None] | None = None,
    question_type: str | None = None,
) -> str:
    """에이전트 루프: LLM ↔ 도구 반복 실행.

    1. LLM에 tools 스키마와 함께 호출
    2. tool_calls가 있으면 실행 후 결과를 messages에 추가
    3. tool_calls가 없으면 최종 답변 반환
    4. max_turns까지 반복

    Args:
            provider: LLM provider 인스턴스
            messages: 초기 메시지 (system + user)
            company: Company 인스턴스 (도구 바인딩용)
            max_turns: 최대 반복 횟수
            max_tools: 도구 개수 제한 (None이면 전체). 소형 모델은 10개 권장.
            on_tool_call: 도구 호출 시 콜백 (UI용)
            on_tool_result: 도구 결과 시 콜백 (UI용)
            question_type: 질문 유형 (Tool Routing용). None이면 전체 도구 노출.

    Returns:
            LLM의 최종 답변 텍스트
    """
    tool_runtime = runtime or build_tool_runtime(company, name="agent-loop")
    tools = selectTools(tool_runtime, questionType=question_type, maxTools=max_tools)

    last_answer = ""

    for _turn in range(max_turns):
        response = provider.complete_with_tools(messages, tools)
        last_answer = response.answer

        if not response.tool_calls:
            return response.answer

        # assistant 메시지 추가 (provider 형식에 맞게)
        messages.append(provider.format_assistant_tool_calls(response.answer, response.tool_calls))

        # 도구 실행 + 결과 추가
        for tc in response.tool_calls:
            if on_tool_call:
                on_tool_call(tc.name, tc.arguments)

            result = tool_runtime.execute_tool(tc.name, tc.arguments)

            if on_tool_result:
                on_tool_result(tc.name, result)

            messages.append(provider.format_tool_result(tc.id, result))

    return last_answer


# ══════════════════════════════════════
# Reflection — 답변 자체 검증
# ══════════════════════════════════════

_REFLECTION_PROMPT = (
    "당신의 이전 답변을 검토하세요. 다음 기준으로 평가하고 개선하세요:\n"
    "1. **수치 근거**: 인용한 모든 수치에 출처(테이블명, 연도)가 있는가?\n"
    "2. **완전성**: 사용자 질문에 완전히 답했는가? 빠진 관점은?\n"
    "3. **근거 없는 주장**: 제공된 데이터로 뒷받침할 수 없는 주장이 있는가?\n\n"
    "문제가 있으면 수정된 답변을 작성하세요. 문제가 없으면 원본 답변을 그대로 반환하세요."
)


def _reflect_on_answer(provider: BaseProvider, messages: list[dict], answer: str) -> str:
    """답변 자체 검증 — 1회 reflection으로 품질 보완."""
    reflect_messages = [
        *messages,
        {"role": "assistant", "content": answer},
        {"role": "user", "content": _REFLECTION_PROMPT},
    ]
    response = provider.complete(reflect_messages)
    return response.answer if response.answer.strip() else answer


def agent_loop_stream(
    provider: BaseProvider,
    messages: list[dict],
    company: Any,
    *,
    max_turns: int = 5,
    max_tools: int | None = None,
    runtime: ToolRuntime | None = None,
    on_tool_call: Callable[[str, dict], None] | None = None,
    on_tool_result: Callable[[str, str], None] | None = None,
    question_type: str | None = None,
) -> Generator[str, None, None]:
    """스트리밍 에이전트 루프: tool 실행 후 최종 답변을 청크로 yield.

    tool_call/tool_result 단계는 콜백으로 알리고,
    최종 답변은 llm.stream()으로 실시간 청크 전달.
    """
    tool_runtime = runtime or build_tool_runtime(company, name="agent-stream")
    tools = selectTools(tool_runtime, questionType=question_type, maxTools=max_tools)

    for _turn in range(max_turns):
        response = provider.complete_with_tools(messages, tools)

        if not response.tool_calls:
            if _turn == 0:
                # 첫 턴에서 tool 호출 없이 바로 답변 → stream으로 재생성
                yield from provider.stream(messages)
                return
            # tool 결과를 받은 후 최종 답변: complete_with_tools 결과를 직접 사용
            if response.answer:
                yield response.answer
                return
            # answer가 비어있으면 stream으로 재생성 시도
            yield from provider.stream(messages)
            return

        # assistant 메시지 추가 (provider 형식에 맞게)
        messages.append(provider.format_assistant_tool_calls(response.answer, response.tool_calls))

        for tc in response.tool_calls:
            if on_tool_call:
                on_tool_call(tc.name, tc.arguments)

            result = tool_runtime.execute_tool(tc.name, tc.arguments)

            if on_tool_result:
                on_tool_result(tc.name, result)

            messages.append(provider.format_tool_result(tc.id, result))

    yield from provider.stream(messages)


def build_agent_system_addition(runtime: ToolRuntime | None = None) -> str:
    """현재 runtime에 맞는 도구 안내 프롬프트를 생성한다.

    CapabilitySpec 메타데이터에서 자동 생성.
    """
    from dartlab.engines.ai.tools.selector import buildToolPrompt

    return buildToolPrompt(runtime)


AGENT_SYSTEM_ADDITION = build_agent_system_addition()

# ══════════════════════════════════════
# Plan-Execute 에이전트 (소형 모델용)
# ══════════════════════════════════════

PLANNING_PROMPT = """당신은 DartLab 기업 분석 플래너입니다.
사용자 질문을 분석하고, 필요한 도구 호출 계획을 JSON으로 출력하세요.

사용 가능한 도구:
{tool_list}

반드시 아래 JSON 형식으로만 답변하세요:
{{
  "question_analysis": "질문 의도 요약",
  "steps": [
    {{"step": 1, "tool": "도구명", "args": {{"key": "value"}}, "reason": "이유"}}
  ],
  "final_synthesis": "최종 답변에서 종합할 내용"
}}"""


def agent_loop_planning(
    provider: BaseProvider,
    messages: list[dict],
    company: Any,
    *,
    max_steps: int = 5,
    max_tools: int | None = 10,
    runtime: ToolRuntime | None = None,
    on_plan: Callable[[dict], None] | None = None,
    on_tool_call: Callable[[str, dict], None] | None = None,
    on_tool_result: Callable[[str, str], None] | None = None,
) -> str:
    """Plan-Execute 에이전트: 1단계 계획 → 2단계 실행 → 3단계 종합.

    소형 모델(Ollama qwen3 등)에서 복합 질문을 다단계로 분해하여 처리.
    """
    tool_runtime = runtime or build_tool_runtime(company, name="plan-execute")
    tools = selectTools(tool_runtime, maxTools=max_tools)
    tool_names = [t.get("function", {}).get("name", "") for t in tools]

    # 1단계: 계획 생성 (JSON 구조)
    question = messages[-1].get("content", "") if messages else ""
    plan_prompt = PLANNING_PROMPT.format(tool_list=", ".join(tool_names))
    plan_messages = [
        {"role": "system", "content": plan_prompt},
        {"role": "user", "content": question},
    ]

    if hasattr(provider, "complete_json"):
        plan_resp = provider.complete_json(plan_messages)
    else:
        plan_resp = provider.complete(plan_messages)

    try:
        plan = json.loads(plan_resp.answer)
    except (json.JSONDecodeError, ValueError):
        # JSON 파싱 실패 → fallback to agent_loop
        return agent_loop(
            provider,
            messages,
            company,
            max_tools=max_tools,
            runtime=tool_runtime,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        )

    if on_plan:
        on_plan(plan)

    steps = plan.get("steps", [])[:max_steps]

    # 2단계: 계획 순차 실행
    results: list[dict[str, str]] = []
    for step in steps:
        tool_name = step.get("tool", "")
        args = step.get("args", {})

        if on_tool_call:
            on_tool_call(tool_name, args)

        result = tool_runtime.execute_tool(tool_name, args)

        if on_tool_result:
            on_tool_result(tool_name, result)

        results.append({"tool": tool_name, "result": result[:3000]})

    # 3단계: 종합 답변 생성
    synthesis_parts = [f"질문: {question}", "", "## 수집된 데이터:"]
    for r in results:
        synthesis_parts.append(f"\n### {r['tool']}")
        synthesis_parts.append(r["result"])
    synthesis_parts.append("\n## 지시사항:")
    synthesis_parts.append(
        "위 데이터를 종합하여 사용자 질문에 대한 구조화된 답변을 작성하세요. "
        "테이블을 활용하고, 모든 수치에 출처를 인용하세요."
    )

    synth_messages = [
        {"role": "system", "content": messages[0].get("content", "") if messages else ""},
        {"role": "user", "content": "\n".join(synthesis_parts)},
    ]
    final_resp = provider.complete(synth_messages)
    return final_resp.answer
