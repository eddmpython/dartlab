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


def _wrapRateLimit(provider: str, e: Exception) -> Exception:
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
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._defaults = _COMPAT_DEFAULTS.get(config.provider, {})
        if self._defaults and not config.baseUrl:
            self.config.baseUrl = self._defaults["base_url"]

    def _getClient(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai 패키지가 필요합니다.\n  pip install --upgrade dartlab")
            kwargs = {}
            apiKey = self.config.apiKey
            if not apiKey:
                import os

                from dartlab.ai.settings.providerCatalog import getProviderSpec

                spec = getProviderSpec(self.config.provider)
                if spec and spec.env_key:
                    apiKey = os.environ.get(spec.env_key)
            if apiKey:
                kwargs["api_key"] = apiKey
            if self.config.baseUrl:
                kwargs["base_url"] = self.config.baseUrl
            self._client = OpenAI(**kwargs)
        return self._client

    @property
    def defaultModel(self) -> str:
        """provider-specific default_model 또는 gpt-4o 폴백."""
        return self._defaults.get("default_model", "gpt-4o")

    @property
    def supportsNativeTools(self) -> bool:
        """OpenAI 호환 API 는 native tool calling 표준 지원."""
        return True

    def checkAvailable(self) -> bool:
        """provider 키 + openai SDK 클라이언트 생성 가능 여부."""
        try:
            self._getClient()
            return True
        except _OPENAI_COMPAT_ERRORS:
            return False

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        """OpenAI 호환 chat.completions 동기 호출 + rate-limit wrap."""
        client = self._getClient()
        try:
            response = client.chat.completions.create(
                model=self.resolvedModel,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.maxTokens,
            )
        except Exception as e:  # noqa: BLE001
            raise _wrapRateLimit(self.config.provider, e) from e
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
        """OpenAI 호환 chat.completions 스트리밍 — delta.content 만 yield."""
        client = self._getClient()
        try:
            response = client.chat.completions.create(
                model=self.resolvedModel,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.maxTokens,
                stream=True,
            )
        except Exception as e:  # noqa: BLE001
            raise _wrapRateLimit(self.config.provider, e) from e
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def completeWithTools(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        toolChoice: str | None = None,
    ) -> ToolResponse:
        """OpenAI 호환 tool calling — toolChoice + parallel_tool_calls=False."""
        client = self._getClient()
        kwargs: dict = {
            "model": self.resolvedModel,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.maxTokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["parallel_tool_calls"] = False
            if toolChoice == "any":
                kwargs["tool_choice"] = "required"
            elif toolChoice == "none":
                kwargs["tool_choice"] = "none"

        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            raise _wrapRateLimit(self.config.provider, e) from e
        choice = response.choices[0]

        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        toolCalls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                toolCalls.append(
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
            toolCalls=toolCalls,
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
        )
