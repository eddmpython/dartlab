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


def agent_loop(
    provider: BaseProvider,
    messages: list[dict],
    company: Any,
    *,
    max_turns: int = 5,
    runtime: ToolRuntime | None = None,
    on_tool_call: Callable[[str, dict], None] | None = None,
    on_tool_result: Callable[[str, str], None] | None = None,
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
            on_tool_call: 도구 호출 시 콜백 (UI용)
            on_tool_result: 도구 결과 시 콜백 (UI용)

    Returns:
            LLM의 최종 답변 텍스트
    """
    tool_runtime = runtime or build_tool_runtime(company, name="agent-loop")
    tools = tool_runtime.get_tool_schemas()

    last_answer = ""

    for _turn in range(max_turns):
        response = provider.complete_with_tools(messages, tools)
        last_answer = response.answer

        if not response.tool_calls:
            return response.answer

        # assistant 메시지 추가 (tool_calls 포함)
        assistant_msg: dict[str, Any] = {"role": "assistant"}
        if response.answer:
            assistant_msg["content"] = response.answer
        else:
            assistant_msg["content"] = None

        assistant_msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                },
            }
            for tc in response.tool_calls
        ]
        messages.append(assistant_msg)

        # 도구 실행 + 결과 추가
        for tc in response.tool_calls:
            if on_tool_call:
                on_tool_call(tc.name, tc.arguments)

            result = tool_runtime.execute_tool(tc.name, tc.arguments)

            if on_tool_result:
                on_tool_result(tc.name, result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    return last_answer


def agent_loop_stream(
    provider: BaseProvider,
    messages: list[dict],
    company: Any,
    *,
    max_turns: int = 5,
    runtime: ToolRuntime | None = None,
    on_tool_call: Callable[[str, dict], None] | None = None,
    on_tool_result: Callable[[str, str], None] | None = None,
) -> Generator[str, None, None]:
    """스트리밍 에이전트 루프: tool 실행 후 최종 답변을 청크로 yield.

    tool_call/tool_result 단계는 콜백으로 알리고,
    최종 답변은 llm.stream()으로 실시간 청크 전달.
    """
    tool_runtime = runtime or build_tool_runtime(company, name="agent-stream")
    tools = tool_runtime.get_tool_schemas()

    for _turn in range(max_turns):
        response = provider.complete_with_tools(messages, tools)

        if not response.tool_calls:
            if _turn == 0:
                yield from provider.stream(messages)
                return
            messages.append({"role": "assistant", "content": response.answer or ""})
            final_messages = [m for m in messages if m.get("role") != "tool" or True]
            yield from provider.stream(final_messages)
            return

        assistant_msg: dict[str, Any] = {"role": "assistant"}
        assistant_msg["content"] = response.answer if response.answer else None
        assistant_msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                },
            }
            for tc in response.tool_calls
        ]
        messages.append(assistant_msg)

        for tc in response.tool_calls:
            if on_tool_call:
                on_tool_call(tc.name, tc.arguments)

            result = tool_runtime.execute_tool(tc.name, tc.arguments)

            if on_tool_result:
                on_tool_result(tc.name, result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

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
