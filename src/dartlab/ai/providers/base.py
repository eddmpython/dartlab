"""LLM provider 추상 베이스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator

from dartlab.ai.types import LLMConfig, LLMResponse, ToolResponse


class RateLimitError(Exception):
    """429 rate limit 에러. fallback 체인에서 다음 프로바이더로 전환 트리거."""

    def __init__(self, provider: str, message: str = "", retryAfter: float | None = None):
        self.provider = provider
        self.retryAfter = retryAfter
        super().__init__(message or f"{provider}: rate limit 초과")


class BaseProvider(ABC):
    """모든 LLM provider의 추상 기반."""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        """동기 completion 호출."""
        ...

    @abstractmethod
    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        """스트리밍 completion (generator)."""
        ...

    @abstractmethod
    def check_available(self) -> bool:
        """provider 접근 가능 여부 확인."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """provider 기본 모델명."""
        ...

    @property
    def resolved_model(self) -> str:
        """사용자 설정 모델 또는 기본 모델명 반환."""
        return self.config.model or self.default_model

    @property
    def supports_native_tools(self) -> bool:
        """이 provider가 네이티브 tool calling을 지원하는지."""
        return False

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> ToolResponse:
        """도구 사용 가능한 completion. 미지원 provider는 fallback."""
        response = self.complete(messages)
        return ToolResponse(
            answer=response.answer,
            provider=response.provider,
            model=response.model,
            usage=response.usage,
            context_tables=response.context_tables,
        )

    def format_tool_result(self, tool_call_id: str, result: str) -> dict:
        """도구 실행 결과를 메시지로 변환 (OpenAI 형식 기본)."""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result,
        }

    def format_assistant_tool_calls(
        self,
        answer: str | None,
        tool_calls: list,
    ) -> dict:
        """assistant 메시지에 tool_calls를 포함 (OpenAI 형식 기본)."""
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
