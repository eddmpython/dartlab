"""LLM 기반 적극적 분석가. dartlab을 도구로 삼아 주체적으로 분석하고, 사용자의 분석 학습을 돕는다."""

from __future__ import annotations

from dartlab.ai.types import LLMConfig, LLMResponse
from dartlab.core.ai import (
    AI_ROLES,
    DEFAULT_ROLE,
    get_profile_manager,
    get_provider_spec,
    normalize_provider,
    normalize_role,
)


def configure(
    provider: str = "codex",
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    role: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    system_prompt: str | None = None,
) -> None:
    """공통 AI profile을 갱신한다."""
    normalized = normalize_provider(provider) or provider
    if get_provider_spec(normalized) is None:
        raise ValueError(f"지원하지 않는 provider: {provider}")
    normalized_role = normalize_role(role)
    if role is not None and normalized_role is None:
        raise ValueError(f"지원하지 않는 role: {role}. 지원: {AI_ROLES}")
    manager = get_profile_manager()
    manager.update(
        provider=normalized,
        model=model,
        role=normalized_role,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        updated_by="code",
    )
    if api_key:
        spec = get_provider_spec(normalized)
        if spec and spec.auth_kind == "api_key":
            manager.save_api_key(normalized, api_key, updated_by="code")


def get_config(provider: str | None = None, *, role: str | None = None) -> LLMConfig:
    """현재 글로벌 LLM 설정 반환."""
    normalized_role = normalize_role(role)
    resolved = get_profile_manager().resolve(provider=provider, role=normalized_role)
    return LLMConfig(**resolved)


def status(provider: str | None = None, *, role: str | None = None) -> dict:
    """LLM 설정 및 provider 상태 확인."""
    from dartlab.ai.providers import create_provider

    normalized_role = normalize_role(role)
    config = get_config(provider, role=normalized_role)
    selected_provider = config.provider
    llm = create_provider(config)
    available = llm.check_available()

    result = {
        "provider": selected_provider,
        "role": normalized_role or DEFAULT_ROLE,
        "model": llm.resolved_model,
        "available": available,
        "defaultProvider": get_profile_manager().load().default_provider,
    }

    if selected_provider == "ollama":
        from dartlab.ai.providers.support.ollama_setup import detect_ollama

        result["ollama"] = detect_ollama()

    if selected_provider == "codex":
        from dartlab.ai.providers.support.cli_setup import detect_codex

        result["codex"] = detect_codex()

    if selected_provider == "oauth-codex":
        from dartlab.ai.providers.support import oauth_token as oauthToken

        token_stored = False
        try:
            token_stored = oauthToken.load_token() is not None
        except (OSError, ValueError):
            token_stored = False

        try:
            authenticated = oauthToken.is_authenticated()
            account_id = oauthToken.get_account_id() if authenticated else None
        except (
            AttributeError,
            OSError,
            RuntimeError,
            ValueError,
            oauthToken.TokenRefreshError,
        ):
            authenticated = False
            account_id = None

        result["oauth-codex"] = {
            "authenticated": authenticated,
            "tokenStored": token_stored,
            "accountId": account_id,
        }

    return result


from dartlab.ai.tools.plugin import get_plugin_registry, tool


def templates(name: str | None = None):
    """분석 템플릿 목록 또는 특정 템플릿 내용 반환.

    Args:
        name: None이면 전체 목록, 지정하면 해당 템플릿 내용.

    Returns:
        list[dict] (목록) 또는 str (내용) 또는 None.
    """
    from dartlab.ai.patterns import get_template, list_templates

    if name is None:
        return list_templates()
    return get_template(name)


def saveTemplate(name: str, *, content: str | None = None, file: str | None = None):
    """사용자 분석 템플릿 저장. ~/.dartlab/templates/{name}.md

    Args:
        name: 템플릿 이름.
        content: 마크다운 내용.
        file: 파일 경로 (content 대신).

    Returns:
        Path — 저장된 파일 경로.
    """
    from dartlab.ai.patterns import save_template

    return save_template(name, content=content, file=file)


__all__ = [
    "configure",
    "get_config",
    "status",
    "LLMConfig",
    "LLMResponse",
    "tool",
    "get_plugin_registry",
    "templates",
    "saveTemplate",
]
