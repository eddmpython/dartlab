"""Tool-use 에이전트 루프.

LLM이 필요한 도구를 직접 선택하여 반복적으로 분석을 수행한다.
OpenAI function calling 프로토콜을 사용.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Generator

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.tool_runtime import ToolRuntime
from dartlab.engines.ai.tools_registry import (
    build_tool_runtime,
    get_coding_runtime_policy,
)

# 소형 모델용 핵심 도구 우선순위 (max_tools 적용 시 이 순서로 선택)
_CORE_TOOL_PRIORITY = [
    "show_topic",
    "get_data",
    "compute_ratios",
    "get_company_info",
    "get_insight",
    "list_topics",
    "get_report_data",
    "trace_topic",
    "diff_topic",
    "get_rank",
]

# 질문 유형별 도구 라우팅 — 관련 도구만 노출하여 선택 정확도 향상
_TOOL_ROUTING: dict[str, list[str]] = {
    "건전성": [
        "get_data",
        "compute_ratios",
        "get_insight",
        "show_topic",
        "get_company_info",
        "get_sector_info",
        "detect_anomalies",
    ],
    "수익성": [
        "get_data",
        "compute_ratios",
        "get_insight",
        "show_topic",
        "yoy_analysis",
        "compute_growth",
        "get_sector_info",
    ],
    "성장성": [
        "get_data",
        "compute_growth",
        "yoy_analysis",
        "get_rank",
        "get_insight",
        "show_topic",
        "get_sector_info",
    ],
    "배당": [
        "get_data",
        "get_report_data",
        "show_topic",
        "compute_ratios",
        "get_insight",
        "yoy_analysis",
    ],
    "리스크": [
        "show_topic",
        "diff_topic",
        "detect_anomalies",
        "get_insight",
        "get_data",
        "list_topics",
        "trace_topic",
    ],
    "지배구조": [
        "show_topic",
        "get_report_data",
        "diff_topic",
        "get_insight",
        "list_topics",
        "trace_topic",
    ],
    "공시": [
        "show_topic",
        "list_topics",
        "diff_topic",
        "trace_topic",
        "get_data",
        "get_report_data",
    ],
    "사업": [
        "show_topic",
        "list_topics",
        "diff_topic",
        "trace_topic",
        "get_data",
        "get_insight",
    ],
}

# 모든 유형에 공통으로 추가되는 메타 도구
_COMMON_TOOLS = ["get_system_spec", "search_company", "get_company_info"]


def _select_tools(
    tools: list[dict],
    max_tools: int | None,
    *,
    question_type: str | None = None,
) -> list[dict]:
    """질문 유형 기반 도구 라우팅 + max_tools 제한.

    question_type이 주어지면 해당 유형에 맞는 도구만 우선 선택.
    max_tools가 지정되면 그 수만큼만 반환.
    """
    by_name: dict[str, dict] = {}
    for t in tools:
        name = t.get("function", {}).get("name", "")
        by_name[name] = t

    # 질문 유형별 라우팅 적용
    if question_type and question_type in _TOOL_ROUTING:
        routed_names = _TOOL_ROUTING[question_type] + _COMMON_TOOLS
        routed = [by_name[n] for n in routed_names if n in by_name]
        # 라우팅 도구 + 나머지 (라우팅 도구 우선)
        remaining = [t for t in tools if t not in routed]
        ordered = routed + remaining
    else:
        ordered = tools

    if max_tools is None or len(ordered) <= max_tools:
        return ordered

    # max_tools 제한: 우선순위 기반 선택
    selected = []
    priority_names = (_TOOL_ROUTING.get(question_type, []) + _COMMON_TOOLS) if question_type else _CORE_TOOL_PRIORITY
    for name in priority_names:
        if name in by_name and by_name[name] not in selected and len(selected) < max_tools:
            selected.append(by_name[name])

    for t in ordered:
        if len(selected) >= max_tools:
            break
        if t not in selected:
            selected.append(t)

    return selected


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
    tools = _select_tools(tool_runtime.get_tool_schemas(), max_tools, question_type=question_type)

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
    tools = _select_tools(tool_runtime.get_tool_schemas(), max_tools, question_type=question_type)

    for _turn in range(max_turns):
        response = provider.complete_with_tools(messages, tools)

        if not response.tool_calls:
            if _turn == 0:
                yield from provider.stream(messages)
                return
            messages.append({"role": "assistant", "content": response.answer or ""})
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
    """현재 runtime에 맞는 도구 안내 프롬프트를 생성한다."""
    tool_names = {
        schema.get("function", {}).get("name", "")
        for schema in (runtime.get_tool_schemas() if runtime is not None else [])
    }
    coding_runtime_enabled, coding_runtime_reason = get_coding_runtime_policy()
    has_runtime_coding_tools = (
        {"run_coding_task", "run_codex_task"}.issubset(tool_names) if tool_names else coding_runtime_enabled
    )

    lines = [
        "",
        "## 도구 사용 안내",
        "",
        "당신은 DartLab 분석 도구를 사용할 수 있습니다.",
        "필요한 데이터를 도구를 통해 조회하고, 분석 결과를 종합하여 답변하세요.",
        "",
        "### 핵심 공시 탐색 도구 (가장 먼저 사용):",
        "- `list_topics`: 이 기업의 전체 공시 topic 목록 조회 → **어떤 공시 내용이 있는지 먼저 확인**",
        "- `show_topic`: topic의 데이터 조회 (block 없으면 목차, block=N이면 실제 텍스트/테이블) → **공시 원문 읽기의 핵심 도구**",
        "- `trace_topic`: topic 데이터의 출처 추적 (docs/finance/report 중 어디서 왔는지)",
        "- `diff_topic`: 기간간 변화 분석 (어떤 공시 내용이 바뀌었는지)",
        "",
        "### 데이터 조회 도구:",
        "- `list_modules`: 사용 가능한 데이터 모듈 목록 조회",
        "- `search_data`: 키워드로 전체 모듈 검색 → 특정 계정과목이나 지표를 찾을 때",
        "- `get_data`: 특정 모듈의 데이터 조회 (BS, IS, CF, dividend 등)",
        "- `get_report_data`: 정기보고서 API 데이터 조회 (배당, 직원, 임원 등)",
        "- `get_company_info`: 기업 기본 정보",
        "",
        "### 분석 도구:",
        "- `compute_ratios`: 재무비율 자동 계산 (부채비율, ROE 등)",
        "- `detect_anomalies`: 이상치 탐지 (급격한 변동, 부호 반전)",
        "- `compute_growth`: 성장률 매트릭스 (1Y/2Y/3Y/5Y CAGR)",
        "- `yoy_analysis`: 전년 대비 변동 분석",
        "- `get_summary`: 요약 통계 (평균, 추세, CAGR)",
        "",
        "### L2 분석 엔진 도구:",
        "- `get_insight`: 기업 7영역 인사이트 등급(A~F) + 이상치 + 프로파일 분류",
        "- `get_sector_info`: WICS 섹터 분류 + 섹터 파라미터(PER, PBR, 할인율)",
        "- `get_rank`: 전체 시장 및 섹터 내 규모 순위",
        "",
        "### 메타 도구 (시스템 정보):",
        '- `get_system_spec`: DartLab 전체 스펙 (엔진, 데이터, 기능 목록) → **"어떤 데이터가 있어?" 질문에 사용**',
        "- `get_engine_spec`: 특정 엔진의 상세 스펙 (insight, sector, rank, dart.finance, dart.report)",
        "- `get_runtime_capabilities`: UI 대화에서 실제 가능한 기능 범위 → **EDGAR 추가 수집, OpenAPI, GPT/Codex 코딩 가능 범위 질문에 우선 사용**",
        "- `get_tool_catalog`: 현재 등록된 도구 목록/파라미터 조회 → **새 도구가 추가됐는지 확인할 때 사용**",
        "- `get_coding_runtime_status`: 현재 coding runtime의 backend 목록/상태 조회",
        "",
        "### 전역 도구 (회사 없어도 사용 가능):",
        "- `search_company`: 종목명/종목코드 검색",
        "- `download_data`: docs/finance/report/edgarDocs 다운로드",
        "- `data_status`: 로컬 데이터 보유 현황 확인",
        "- `get_openapi_capabilities`: OpenDart/OpenEdgar surface 요약",
        "- `call_dart_openapi`: DART 공개 API 직접 호출",
        "- `call_edgar_openapi`: EDGAR 공개 API 직접 호출",
        "- `openapi_save`: OpenAPI saver로 parquet 생성",
    ]

    if has_runtime_coding_tools:
        lines.extend(
            [
                "- `run_coding_task`: 표준 coding runtime으로 실제 코드 작업 위임 → **명시적 코드 수정/리팩터링 요청에서 우선 사용**",
                "- `run_codex_task`: Codex compatibility alias",
            ]
        )
    else:
        lines.append(f"- 현재 세션에서는 coding runtime 도구가 등록되지 않았습니다. ({coding_runtime_reason})")

    lines.extend(
        [
            "",
            "### 분석 절차:",
            "1. 질문을 이해하고 이것이 `기능 탐색`인지 `회사 분석`인지 먼저 구분",
            "2. 기능 탐색 질문이면 `get_runtime_capabilities`, `get_system_spec`, `get_openapi_capabilities`, `get_tool_catalog`, `get_coding_runtime_status` 중 적절한 것을 먼저 호출",
            "3. 회사 분석이면 `list_topics`로 사용 가능한 공시 topic을 먼저 확인",
            "4. 공시 원문이 필요하면 `show_topic`으로 조회, 변화가 궁금하면 `diff_topic` 사용",
            "5. 재무 수치가 필요하면 `get_data`로 BS/IS/CF 조회, 정기보고서는 `get_report_data`",
            "5b. OpenAPI 원문/추가 수집 질문이면 `call_dart_openapi`, `call_edgar_openapi`, `openapi_save`를 사용",
        ]
    )

    if has_runtime_coding_tools:
        lines.append(
            "6. 명시적 코드 수정/리팩터링 요청이면 `run_coding_task` 사용을 우선 검토하고, Codex 고정 지시일 때만 `run_codex_task`를 사용"
        )
    else:
        lines.append(
            "6. 코드 작업 요청이라도 현재 세션에서 coding runtime이 닫혀 있으면 실제 수정 대신 수정안과 활성화 조건만 안내"
        )

    lines.extend(
        [
            "7. 필요 시 `get_insight`, `get_sector_info`, `get_rank` 등으로 심층 분석",
            "8. 결과를 종합하여 구조화된 답변 작성 (테이블 활용)",
            "9. 모든 수치에 출처(테이블명, 연도)를 반드시 인용",
            "",
            "### 답변 방식:",
            '- 사용자가 "뭘 할 수 있어?", "EDGAR에서 더 받을 수 있어?", "OpenAPI로 뭐가 돼?", "GPT 연결하면 코딩도 돼?"처럼 범위를 물으면',
            "  가능한 것 / 바로 할 수 있는 것 / 아직 안 되는 것을 먼저 짧게 정리한 뒤 다음 액션을 제안하세요.",
            "- 도구와 기능 목록은 고정 문구를 외우지 말고 현재 등록된 tool registry 결과를 우선 신뢰하세요.",
        ]
    )
    return "\n".join(lines)


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
    tools = _select_tools(tool_runtime.get_tool_schemas(), max_tools)
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
