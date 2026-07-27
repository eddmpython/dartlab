"""DartLab AI public entry points."""

from __future__ import annotations

from typing import Any

from dartlab.ai.settings.types import LLMConfig

from .kernel import ask

ProviderConfig = LLMConfig

_CONFIG = LLMConfig()
_ROLE_CONFIGS: dict[str, LLMConfig] = {}


def configure(provider: str = "dartlab", **kwargs: Any) -> ProviderConfig:
    """Configure provider settings for compatibility callers."""

    global _CONFIG
    role = kwargs.pop("role", None)
    values = {"provider": provider, **{k: v for k, v in kwargs.items() if k in ProviderConfig.__dataclass_fields__}}
    config = ProviderConfig(**values)
    if role:
        _ROLE_CONFIGS[str(role)] = config
    else:
        _CONFIG = config
    try:
        from dartlab.ai.settings import getProfileManager, getProviderSpec, normalizeProvider, normalizeRole

        normalized = normalizeProvider(provider) or provider
        if getProviderSpec(normalized) is not None:
            getProfileManager().update(
                provider=normalized,
                role=normalizeRole(str(role)) if role else None,
                model=config.model,
                baseUrl=config.baseUrl,
                temperature=config.temperature,
                maxTokens=config.maxTokens,
                systemPrompt=config.systemPrompt,
                updatedBy="compat",
            )
    except (OSError, RuntimeError, ValueError):
        pass
    return config


def getConfig(provider: str | None = None, role: str | None = None, **kwargs: Any) -> ProviderConfig:
    """Return provider settings without owning the AI workbench loop."""

    base = (_ROLE_CONFIGS.get(str(role)) if role else None) or _CONFIG
    resolved: dict[str, Any] = {}
    if provider is not None or base.provider != "dartlab":
        try:
            from dartlab.ai.settings import getProfileManager

            resolved = getProfileManager().resolve(provider, role=role)
        except (OSError, RuntimeError, ValueError):
            resolved = {}
    resolved_provider = provider or resolved.get("provider") or base.provider
    # 모델 우선순위:
    #   1. 호출자 explicit kwarg (아래 for-loop 에서 마지막 덮어씀)
    #   2. configure() 로 저장한 base.model — 사용자 명시 선택, 보존
    #   3. OpenAI family + base.model 미설정 → latest_openai_model()
    #   4. profile_manager 저장 model (server 자동 저장)
    profile_model = resolved.get("model")
    if base.model:
        resolvedModel = base.model
    else:
        try:
            from dartlab.ai.settings.modelResolver import isOpenaiFamilyProvider, latestOpenaiModel

            if isOpenaiFamilyProvider(resolved_provider):
                resolvedModel = latestOpenaiModel()
            else:
                resolvedModel = profile_model
        except (ImportError, OSError, RuntimeError, ValueError):
            resolvedModel = profile_model
    values = {
        "provider": resolved_provider,
        "model": resolvedModel,
        "apiKey": resolved.get("api_key") or resolved.get("apiKey") or base.apiKey,
        "baseUrl": resolved.get("base_url") or resolved.get("baseUrl") or base.baseUrl,
        "temperature": resolved.get("temperature") if resolved.get("temperature") is not None else base.temperature,
        "maxTokens": resolved.get("max_tokens") if resolved.get("maxTokens") is not None else base.maxTokens,
        "systemPrompt": resolved.get("system_prompt") or resolved.get("systemPrompt") or base.systemPrompt,
    }
    for key, value in kwargs.items():
        if key in values and value is not None:
            values[key] = value
    return ProviderConfig(**values)


def templates(name: str | None = None):
    """Return available analysis templates."""

    items = {"dartlab-research": "Skill OS 근거 기반 DartLab research graph"}
    return items.get(name) if name else items


def saveTemplate(name: str, *, content: str | None = None, file: str | None = None) -> dict[str, str | None]:
    """Acknowledge template save requests until the new template store lands."""

    return {"name": name, "content": content, "file": file}


__all__ = ["ask", "configure", "getConfig", "templates", "saveTemplate"]
