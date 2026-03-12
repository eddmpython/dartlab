"""Provider helpers shared across CLI commands."""

from __future__ import annotations

from dartlab.engines.ai.providers import create_provider
from dartlab.engines.ai.types import LLMConfig


def detect_provider() -> str:
    """Return the first available local-first provider."""
    for provider_name in ["codex", "claude-code", "ollama"]:
        config = LLMConfig(provider=provider_name)
        try:
            provider = create_provider(config)
            if provider.check_available():
                return provider_name
        except Exception:
            continue
    return "ollama"
