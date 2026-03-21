"""agent 모듈 테스트 — mock provider로 LLM 불필요."""

import pytest

pytestmark = pytest.mark.unit

import polars as pl

from dartlab.engines.ai.agent import agent_loop, build_agent_system_addition
from dartlab.engines.ai.tools.registry import build_tool_runtime
from dartlab.engines.ai.types import ToolCall, ToolResponse

# ══════════════════════════════════════
# Mocks
# ══════════════════════════════════════


class MockCompany:
    """테스트용 가짜 Company."""

    def __init__(self):
        self.corpName = "테스트기업"
        self.stockCode = "000000"
        self.BS = pl.DataFrame(
            {
                "계정명": ["자산총계", "부채총계", "자본총계"],
                "2023": [15000, 5000, 10000],
                "2022": [13000, 4000, 9000],
            }
        )
        self.IS = pl.DataFrame(
            {
                "계정명": ["매출액", "영업이익", "당기순이익"],
                "2023": [20000, 3000, 2000],
                "2022": [18000, 2500, 1800],
            }
        )


class MockProvider:
    """테스트용 mock LLM provider."""

    def __init__(self, responses: list[ToolResponse]):
        self._responses = responses
        self._call_count = 0

    def complete_with_tools(self, messages, tools):
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        return self._responses[idx]

    def format_tool_result(self, tool_call_id: str, result: str) -> dict:
        return {"role": "tool", "tool_call_id": tool_call_id, "content": result}

    def format_assistant_tool_calls(self, answer: str | None, tool_calls: list) -> dict:
        import json

        msg: dict = {"role": "assistant", "content": answer}
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                },
            }
            for tc in tool_calls
        ]
        return msg


# ══════════════════════════════════════
# agent_loop
# ══════════════════════════════════════


class TestAgentLoop:
    def test_direct_answer(self):
        """도구 호출 없이 바로 답변."""
        provider = MockProvider(
            [
                ToolResponse(
                    answer="분석 결과입니다.",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[],
                    finish_reason="stop",
                )
            ]
        )
        company = MockCompany()
        messages = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "분석해줘"},
        ]
        result = agent_loop(provider, messages, company)
        assert result == "분석 결과입니다."

    def test_tool_call_then_answer(self):
        """도구 호출 → 결과 → 최종 답변."""
        provider = MockProvider(
            [
                # 1단계: tool call 요청
                ToolResponse(
                    answer="",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[
                        ToolCall(id="call_1", name="get_company_info", arguments={}),
                    ],
                    finish_reason="tool_calls",
                ),
                # 2단계: 최종 답변
                ToolResponse(
                    answer="테스트기업의 분석 결과입니다.",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[],
                    finish_reason="stop",
                ),
            ]
        )
        company = MockCompany()
        messages = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "기업 정보 알려줘"},
        ]
        result = agent_loop(provider, messages, company)
        assert "테스트기업의 분석 결과" in result

    def test_max_turns(self):
        """max_turns 도달 시 마지막 답변 반환."""
        # 계속 tool call만 하는 provider
        always_call = ToolResponse(
            answer="아직 분석 중...",
            provider="mock",
            model="mock-1",
            tool_calls=[
                ToolCall(id="call_x", name="get_company_info", arguments={}),
            ],
            finish_reason="tool_calls",
        )
        provider = MockProvider([always_call] * 10)
        company = MockCompany()
        messages = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "분석해줘"},
        ]
        result = agent_loop(provider, messages, company, max_turns=2)
        assert isinstance(result, str)

    def test_callbacks(self):
        """on_tool_call, on_tool_result 콜백."""
        calls = []
        results = []

        provider = MockProvider(
            [
                ToolResponse(
                    answer="",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[
                        ToolCall(id="call_1", name="get_company_info", arguments={}),
                    ],
                    finish_reason="tool_calls",
                ),
                ToolResponse(
                    answer="완료",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[],
                    finish_reason="stop",
                ),
            ]
        )
        company = MockCompany()
        messages = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "정보"},
        ]

        agent_loop(
            provider,
            messages,
            company,
            on_tool_call=lambda name, args: calls.append(name),
            on_tool_result=lambda name, result: results.append(name),
        )

        assert "get_company_info" in calls
        assert "get_company_info" in results

    def test_messages_accumulate(self):
        """메시지가 누적되는지 확인."""
        provider = MockProvider(
            [
                ToolResponse(
                    answer="",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[
                        ToolCall(id="call_1", name="get_company_info", arguments={}),
                    ],
                    finish_reason="tool_calls",
                ),
                ToolResponse(
                    answer="최종 답변",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[],
                    finish_reason="stop",
                ),
            ]
        )
        company = MockCompany()
        messages = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "정보"},
        ]
        agent_loop(provider, messages, company)

        # messages에 assistant + tool 메시지가 추가되어야 함
        roles = [m["role"] for m in messages]
        assert "assistant" in roles
        assert "tool" in roles

    def test_unknown_tool(self):
        """등록되지 않은 도구 호출 시 에러 메시지."""
        provider = MockProvider(
            [
                ToolResponse(
                    answer="",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[
                        ToolCall(id="call_1", name="nonexistent_tool", arguments={}),
                    ],
                    finish_reason="tool_calls",
                ),
                ToolResponse(
                    answer="완료",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[],
                    finish_reason="stop",
                ),
            ]
        )
        company = MockCompany()
        messages = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "정보"},
        ]
        # 에러 없이 실행되어야 함
        result = agent_loop(provider, messages, company)
        assert isinstance(result, str)

    def test_runtime_injection(self):
        """커스텀 ToolRuntime을 주입해도 정상 동작."""
        provider = MockProvider(
            [
                ToolResponse(
                    answer="",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[
                        ToolCall(id="call_1", name="get_company_info", arguments={}),
                    ],
                    finish_reason="tool_calls",
                ),
                ToolResponse(
                    answer="완료",
                    provider="mock",
                    model="mock-1",
                    tool_calls=[],
                    finish_reason="stop",
                ),
            ]
        )
        company = MockCompany()
        runtime = build_tool_runtime(company, name="agent-test")
        messages = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "정보"},
        ]
        result = agent_loop(provider, messages, company, runtime=runtime)
        assert result == "완료"


# ══════════════════════════════════════
# AGENT_SYSTEM_ADDITION
# ══════════════════════════════════════


class TestAgentSystemAddition:
    def test_contains_tool_descriptions(self):
        prompt = build_agent_system_addition(build_tool_runtime(MockCompany(), name="agent-system-test"))
        assert "get_data" in prompt
        assert "compute_ratios" in prompt
        assert "detect_anomalies" in prompt
        assert "get_runtime_capabilities" in prompt
        assert "get_tool_catalog" in prompt
        assert "get_coding_runtime_status" in prompt
        assert "call_dart_openapi" in prompt
        assert "call_edgar_openapi" in prompt
        assert "run_coding_task" in prompt
        assert "run_codex_task" in prompt
        assert "AGENT_SYSTEM_ADDITION" not in prompt

    def test_contains_procedure(self):
        prompt = build_agent_system_addition(build_tool_runtime(MockCompany(), name="agent-system-test"))
        assert "분석 절차" in prompt
        assert "run_coding_task" in prompt

    def test_hides_coding_tools_when_runtime_disabled(self, monkeypatch):
        monkeypatch.setenv("DARTLAB_HOST", "0.0.0.0")
        monkeypatch.delenv("DARTLAB_ENABLE_CODING_RUNTIME", raising=False)
        prompt = build_agent_system_addition(build_tool_runtime(MockCompany(), name="agent-system-disabled"))
        assert "coding runtime 도구가 등록되지 않았습니다" in prompt
        assert "run_coding_task" not in prompt
        assert "run_codex_task" not in prompt
