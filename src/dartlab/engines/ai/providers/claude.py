"""Claude / Anthropic provider."""

from __future__ import annotations

from typing import Generator

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.types import LLMConfig, LLMResponse, ToolCall, ToolResponse

_CLAUDE_PROVIDER_ERRORS = (ImportError, OSError, RuntimeError, TypeError, ValueError)


class ClaudeProvider(BaseProvider):
    """Anthropic SDK 기반 provider.

    base_url 있으면 OpenAI 호환 모드 (프록시/CLIProxyAPI).
    없으면 anthropic SDK 네이티브 모드.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._use_openai_compat = False

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-6"

    def _get_client(self):
        if self._client is not None:
            return self._client

        if self.config.base_url:
            # OpenAI 호환 모드 (프록시)
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai 패키지가 필요합니다 (프록시 모드).\n  uv add dartlab[llm]")
            self._client = OpenAI(
                api_key=self.config.api_key or "proxy",
                base_url=self.config.base_url,
            )
            self._use_openai_compat = True
        else:
            # Anthropic 네이티브 모드
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError(
                    "anthropic 패키지가 필요합니다.\n"
                    "  uv add dartlab[llm-anthropic]\n\n"
                    "프록시를 사용하려면 base_url을 설정하세요:\n"
                    "  dartlab.llm.configure(provider='claude', base_url='http://...')"
                )
            kwargs = {}
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            self._client = Anthropic(**kwargs)
            self._use_openai_compat = False

        return self._client

    def check_available(self) -> bool:
        try:
            self._get_client()
            return True
        except _CLAUDE_PROVIDER_ERRORS:
            return False

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        client = self._get_client()

        if self._use_openai_compat:
            response = client.chat.completions.create(
                model=self.resolved_model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return LLMResponse(
                answer=response.choices[0].message.content or "",
                provider="claude",
                model=response.model,
                usage=usage,
            )
        else:
            # Anthropic 네이티브
            system_msg = ""
            user_messages = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    user_messages.append(m)

            response = client.messages.create(
                model=self.resolved_model,
                system=system_msg,
                messages=user_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            return LLMResponse(
                answer=response.content[0].text,
                provider="claude",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
            )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        client = self._get_client()

        if self._use_openai_compat:
            stream = client.chat.completions.create(
                model=self.resolved_model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            # Anthropic 네이티브 스트리밍
            system_msg = ""
            user_messages = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    user_messages.append(m)

            with client.messages.stream(
                model=self.resolved_model,
                system=system_msg,
                messages=user_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            ) as stream:
                for text in stream.text_stream:
                    yield text

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> ToolResponse:
        """Claude tool calling — OpenAI 호환 모드일 때만 지원."""
        import json

        client = self._get_client()

        if self._use_openai_compat:
            kwargs: dict = {
                "model": self.resolved_model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
            if tools:
                kwargs["tools"] = tools

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]

            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            tool_calls = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            name=tc.function.name,
                            arguments=json.loads(tc.function.arguments),
                        )
                    )

            return ToolResponse(
                answer=choice.message.content or "",
                provider="claude",
                model=response.model,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
                usage=usage,
            )
        else:
            # Anthropic 네이티브: BaseProvider fallback
            return super().complete_with_tools(messages, tools)
