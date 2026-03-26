"""Rate limit 자동 fallback 체인."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Generator

from dartlab.ai.providers.base import RateLimitError

if TYPE_CHECKING:
    from dartlab.ai.types import LLMConfig, LLMResponse, ToolResponse

log = logging.getLogger(__name__)

DEFAULT_FREE_CHAIN: tuple[str, ...] = ("groq", "cerebras", "mistral", "gemini")


def buildFreeChain() -> list[str]:
    """API 키가 등록된 무료 프로바이더만 포함한 체인을 구성한다."""
    import os

    from dartlab.core.ai.providers import get_provider_spec

    chain: list[str] = []
    for name in DEFAULT_FREE_CHAIN:
        spec = get_provider_spec(name)
        if spec is None:
            continue
        if spec.env_key and os.environ.get(spec.env_key):
            chain.append(name)
            continue
        try:
            from dartlab.core.ai.providers import api_key_secret_name
            from dartlab.core.ai.secrets import get_secret_store

            store = get_secret_store()
            if store.get(api_key_secret_name(name)):
                chain.append(name)
        except (ImportError, RuntimeError, KeyError):
            pass
    return chain


class FallbackChain:
    """Rate limit 시 자동 프로바이더 전환.

    429/503 에러가 발생하면 다음 프로바이더로 자동 전환한다.
    모든 프로바이더가 실패하면 마지막 에러를 전파한다.
    """

    def __init__(self, chain: list[str] | None = None):
        self._chain = chain if chain is not None else buildFreeChain()

    @property
    def providers(self) -> list[str]:
        return list(self._chain)

    @property
    def empty(self) -> bool:
        return len(self._chain) == 0

    def _resolve(self, providerName: str) -> "LLMConfig":
        """프로바이더 이름으로 LLMConfig를 생성한다."""
        from dartlab.ai import get_config

        config = get_config()
        return config.merge({"provider": providerName})

    def _create(self, providerName: str):
        """프로바이더 인스턴스를 생성한다."""
        from dartlab.ai.providers import create_provider

        return create_provider(self._resolve(providerName))

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> "LLMResponse | ToolResponse":
        """순서대로 시도, 429/503이면 다음 프로바이더로."""
        lastError: Exception | None = None
        for name in self._chain:
            try:
                provider = self._create(name)
                if tools and provider.supports_native_tools:
                    return provider.complete_with_tools(messages, tools)
                return provider.complete(messages)
            except RateLimitError as e:
                log.info("fallback: %s rate limit, 다음 프로바이더로 전환", name)
                lastError = e
                continue
        if lastError:
            raise lastError
        raise RuntimeError("fallback 체인에 사용 가능한 프로바이더가 없습니다")

    def stream(self, messages: list[dict]) -> Generator[str, None, None]:
        """스트리밍 fallback — 첫 성공 프로바이더의 스트림을 반환."""
        lastError: Exception | None = None
        for name in self._chain:
            try:
                provider = self._create(name)
                yield from provider.stream(messages)
                return
            except RateLimitError as e:
                log.info("fallback stream: %s rate limit, 다음 프로바이더로 전환", name)
                lastError = e
                continue
        if lastError:
            raise lastError
        raise RuntimeError("fallback 체인에 사용 가능한 프로바이더가 없습니다")
