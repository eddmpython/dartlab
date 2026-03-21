"""Provider 레지스트리 및 팩토리."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dartlab.engines.ai.providers.base import BaseProvider
    from dartlab.engines.ai.types import LLMConfig

_PROVIDER_MAP: dict[str, str] = {
    "openai": "dartlab.engines.ai.providers.openai_compat.OpenAICompatProvider",
    "ollama": "dartlab.engines.ai.providers.ollama.OllamaProvider",
    "custom": "dartlab.engines.ai.providers.openai_compat.OpenAICompatProvider",
    "codex": "dartlab.engines.ai.providers.codex.CodexProvider",
    "oauth-codex": "dartlab.engines.ai.providers.oauth_codex.OAuthCodexProvider",
}


def create_provider(config: "LLMConfig") -> "BaseProvider":
    """LLMConfig로부터 적절한 provider 인스턴스 생성."""
    class_path = _PROVIDER_MAP.get(config.provider)
    if class_path is None:
        raise ValueError(f"지원하지 않는 provider: '{config.provider}'. 지원: {list(_PROVIDER_MAP.keys())}")
    module_path, class_name = class_path.rsplit(".", 1)
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls(config)


def register_provider(name: str, class_path: str) -> None:
    """새 provider 등록 (확장용)."""
    _PROVIDER_MAP[name] = class_path


def available_providers() -> list[str]:
    """등록된 provider 이름 목록."""
    return list(_PROVIDER_MAP.keys())
