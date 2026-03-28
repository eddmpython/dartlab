"""OpenAI / GPT / OpenAI-compatible provider."""

from __future__ import annotations

import json
from typing import Generator

from dartlab.ai.providers.base import BaseProvider, RateLimitError
from dartlab.ai.types import LLMConfig, LLMResponse, ToolCall, ToolResponse

try:
    from openai import OpenAIError as _OpenAIError
    from openai import RateLimitError as _OpenAIRateLimitError

    _OPENAI_COMPAT_ERRORS = (ImportError, OSError, RuntimeError, TypeError, ValueError, _OpenAIError)
    _HAS_OPENAI = True
except ImportError:
    _OPENAI_COMPAT_ERRORS = (ImportError, OSError, RuntimeError, TypeError, ValueError)
    _HAS_OPENAI = False


def _wrap_rate_limit(provider: str, e: Exception) -> Exception:
    """OpenAI SDK의 RateLimitError를 dartlab RateLimitError로 래핑."""
    if _HAS_OPENAI and isinstance(e, _OpenAIRateLimitError):
        retryAfter = None
        if hasattr(e, "response") and e.response is not None:
            ra = e.response.headers.get("retry-after")
            if ra:
                try:
                    retryAfter = float(ra)
                except ValueError:
                    pass
        return RateLimitError(provider, str(e), retryAfter=retryAfter)
    return e


_COMPAT_DEFAULTS: dict[str, dict[str, str]] = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "default_model": "llama-3.3-70b",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-small-latest",
    },
}


class OpenAICompatProvider(BaseProvider):
    """OpenAI SDK 기반 provider.

    GPT 직접 호출, CLIProxyAPI, 기타 OpenAI-compatible API 모두 지원.
    base_url 설정으로 프록시/커스텀 엔드포인트 전환.
    groq/cerebras/mistral 등 OpenAI 호환 프로바이더는 자동으로 base_url 설정.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._defaults = _COMPAT_DEFAULTS.get(config.provider, {})
        if self._defaults and not config.base_url:
            self.config.base_url = self._defaults["base_url"]

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai 패키지가 필요합니다.\n  uv add dartlab[llm]")
            kwargs = {}
            apiKey = self.config.api_key
            if not apiKey:
                import os

                from dartlab.core.ai.providers import get_provider_spec

                spec = get_provider_spec(self.config.provider)
                if spec and spec.env_key:
                    apiKey = os.environ.get(spec.env_key)
            if apiKey:
                kwargs["api_key"] = apiKey
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    @property
    def default_model(self) -> str:
        """기본 모델명."""
        return self._defaults.get("default_model", "gpt-4o")

    @property
    def supports_native_tools(self) -> bool:
        """네이티브 tool calling 지원 여부."""
        return True

    def check_available(self) -> bool:
        """provider 사용 가능 여부 확인."""
        try:
            self._get_client()
            return True
        except _OPENAI_COMPAT_ERRORS:
            return False

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        """동기 완료 요청."""
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.resolved_model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        except Exception as e:
            raise _wrap_rate_limit(self.config.provider, e) from e
        choice = response.choices[0]
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return LLMResponse(
            answer=choice.message.content or "",
            provider=self.config.provider,
            model=response.model,
            usage=usage,
        )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        """스트리밍 응답 생성."""
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.resolved_model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
            )
        except Exception as e:
            raise _wrap_rate_limit(self.config.provider, e) from e
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        tool_choice: str | None = None,
    ) -> ToolResponse:
        """OpenAI tool calling 지원."""
        client = self._get_client()
        kwargs: dict = {
            "model": self.resolved_model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["parallel_tool_calls"] = False
            if tool_choice == "any":
                kwargs["tool_choice"] = "required"
            elif tool_choice == "none":
                kwargs["tool_choice"] = "none"

        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as e:
            raise _wrap_rate_limit(self.config.provider, e) from e
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
            provider=self.config.provider,
            model=response.model,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
        )
