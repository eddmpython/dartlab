"""Provider 카탈로그 + WorkbenchProvider 진입점 회귀."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_available_providers_lists_catalog_excluding_anthropic():
    from dartlab.ai.providers import availableProviders

    names = set(availableProviders())
    # 정식 1 순위
    assert "oauth-codex" in names
    # OpenAI 호환 군
    assert {"openai", "ollama", "custom", "groq", "cerebras", "mistral", "gemini", "codex"}.issubset(names)
    # ToS 회피
    assert "anthropic" not in names
    assert "claude" not in names


def test_create_provider_dartlab_returns_unavailable():
    """provider='dartlab' 은 카탈로그에 없으므로 UnavailableProvider 반환."""
    from dartlab.ai.providers import UnavailableProvider, createProvider
    from dartlab.ai.settings.types import LLMConfig

    provider = createProvider(LLMConfig(provider="dartlab", model="research"))
    assert isinstance(provider, UnavailableProvider)
    assert provider.checkAvailable() is False


def test_create_provider_chatgpt_alias_blocked():
    from dartlab.ai.providers import createProvider

    with pytest.raises(ValueError):
        createProvider(provider="chatgpt")


def test_direct_provider_configuration_is_rejected():
    from dartlab.ai import configure

    with pytest.raises(ValueError, match="agent runtime"):
        configure(provider="ollama", model="base")


def test_provider_config_round_trip_preserves_model():
    from dartlab.ai.providers import OpenAICompatibleProvider, ProviderConfig, createProvider

    provider = createProvider(ProviderConfig(provider="ollama", model="custom-model"))
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.resolvedModel == "custom-model"
