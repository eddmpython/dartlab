"""Tool-use 에이전트 루프.

LLM이 필요한 도구를 직접 선택하여 반복적으로 분석을 수행한다.
OpenAI function calling 프로토콜을 사용.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Generator

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.tools_registry import (
    execute_tool,
    get_tool_schemas,
    register_defaults,
)


def agent_loop(
    provider: BaseProvider,
    messages: list[dict],
    company: Any,
    *,
    max_turns: int = 5,
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
    register_defaults(company)
    tools = get_tool_schemas()

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

            result = execute_tool(tc.name, tc.arguments)

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
    on_tool_call: Callable[[str, dict], None] | None = None,
    on_tool_result: Callable[[str, str], None] | None = None,
) -> Generator[str, None, None]:
    """스트리밍 에이전트 루프: tool 실행 후 최종 답변을 청크로 yield.

    tool_call/tool_result 단계는 콜백으로 알리고,
    최종 답변은 llm.stream()으로 실시간 청크 전달.
    """
    register_defaults(company)
    tools = get_tool_schemas()

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

            result = execute_tool(tc.name, tc.arguments)

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


AGENT_SYSTEM_ADDITION = """

## 도구 사용 안내

당신은 DartLab 분석 도구를 사용할 수 있습니다.
필요한 데이터를 도구를 통해 조회하고, 분석 결과를 종합하여 답변하세요.

### 데이터 조회 도구:
- `list_modules`: 사용 가능한 데이터 모듈 목록 조회 → **데이터를 모를 때 먼저 호출**
- `search_data`: 키워드로 전체 모듈 검색 → 특정 계정과목이나 지표를 찾을 때
- `get_data`: 특정 모듈의 데이터 조회 (BS, IS, CF, dividend 등)
- `get_report_data`: 정기보고서 API 데이터 조회 (배당, 직원, 임원 등)
- `get_company_info`: 기업 기본 정보

### 분석 도구:
- `compute_ratios`: 재무비율 자동 계산 (부채비율, ROE 등)
- `detect_anomalies`: 이상치 탐지 (급격한 변동, 부호 반전)
- `compute_growth`: 성장률 매트릭스 (1Y/2Y/3Y/5Y CAGR)
- `yoy_analysis`: 전년 대비 변동 분석
- `get_summary`: 요약 통계 (평균, 추세, CAGR)

### L2 분석 엔진 도구:
- `get_insight`: 기업 7영역 인사이트 등급(A~F) + 이상치 + 프로파일 분류
- `get_sector_info`: WICS 섹터 분류 + 섹터 파라미터(PER, PBR, 할인율)
- `get_rank`: 전체 시장 및 섹터 내 규모 순위

### 메타 도구 (시스템 정보):
- `get_system_spec`: DartLab 전체 스펙 (엔진, 데이터, 기능 목록) → **"어떤 데이터가 있어?" 질문에 사용**
- `get_engine_spec`: 특정 엔진의 상세 스펙 (insight, sector, rank, dart.finance, dart.report)

### 분석 절차:
1. 질문을 이해하고 필요한 데이터를 파악
2. 어떤 데이터가 있는지 모르면 `list_modules` 또는 `get_system_spec`을 먼저 호출
3. 구체적 모듈 데이터를 `get_data`로 조회
4. 필요 시 `get_insight`, `get_sector_info`, `get_rank` 등으로 심층 분석
5. 결과를 종합하여 구조화된 답변 작성 (테이블 활용)
6. 모든 수치에 출처(테이블명, 연도)를 반드시 인용
"""
