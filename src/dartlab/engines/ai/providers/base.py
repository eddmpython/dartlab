"""LLM provider 추상 베이스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator

from dartlab.engines.ai.types import LLMConfig, LLMResponse, ToolResponse


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
        return self.config.model or self.default_model

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
