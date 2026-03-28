"""Shared AI profile / provider status helpers for server adapters."""

from __future__ import annotations

import os
import shutil
from typing import Any

from dartlab.core.ai import DEFAULT_ROLE, get_profile_manager, normalize_provider, normalize_role
from dartlab.server.models import ConfigureRequest

_TRUTHY = {"1", "true", "yes", "on"}


def selected_provider(role: str | None = None) -> str | None:
    """Resolve selected provider from shared profile."""
    profile = get_profile_manager().load()
    normalized_role = normalize_role(role)
    if normalized_role:
        binding = profile.roles.get(normalized_role)
        if binding and binding.provider:
            return normalize_provider(binding.provider) or binding.provider
    return normalize_provider(profile.default_provider) or profile.default_provider


def should_preload_ollama() -> bool:
    """Only preload Ollama when explicitly enabled and currently selected."""
    raw = os.environ.get("DARTLAB_PRELOAD_OLLAMA", "")
    if raw.strip().lower() not in _TRUTHY:
        return False
    profile = get_profile_manager().load()
    if selected_provider() == "ollama":
        return True
    return any(
        (normalize_provider(binding.provider) or binding.provider) == "ollama" for binding in profile.roles.values()
    )


def probe_provider_availability(prov: str) -> tuple[bool | None, str | None, bool]:
    """provider 사용 가능 여부와 모델을 실제로 점검한다."""
    from dartlab.ai import get_config
    from dartlab.ai.providers import create_provider

    try:
        config = get_config(prov)
        provider = create_provider(config)
        available = provider.check_available()
        return available, provider.resolved_model, True
    except (
        AttributeError,
        FileNotFoundError,
        ImportError,
        OSError,
        PermissionError,
        RuntimeError,
        TypeError,
        ValueError,
    ):
        return False, None, True


def build_ollama_detail(*, probe: bool) -> dict[str, Any]:
    """Ollama 설치/실행/GPU 상태를 조회한다."""
    if probe:
        try:
            from dartlab.ai.providers.support.ollama_setup import detect_ollama, get_install_guide

            ollama_info = detect_ollama()
            detail = {
                "installed": ollama_info.get("installed", False),
                "running": ollama_info.get("running", False),
                "gpu": ollama_info.get("gpu", None),
                "checked": True,
            }
            if not ollama_info.get("installed"):
                detail["installGuide"] = get_install_guide()
            return detail
        except (FileNotFoundError, ImportError, OSError, PermissionError, RuntimeError, ValueError):
            return {"installed": False, "running": False, "gpu": None, "checked": True}

    return {
        "installed": bool(shutil.which("ollama")),
        "running": None,
        "gpu": None,
        "checked": False,
    }


def build_oauth_codex_detail(*, probe: bool) -> dict[str, Any]:
    """OAuth Codex 인증/토큰 상태를 조회한다."""
    try:
        from dartlab.ai.providers.support import oauth_token as oauthToken
    except (ImportError, OSError, RuntimeError):
        return {"authenticated": False, "tokenStored": False, "accountId": None, "checked": probe}

    token_stored = False
    try:
        token_stored = oauthToken.load_token() is not None
    except (OSError, ValueError):
        token_stored = False

    if not probe:
        return {
            "authenticated": False,
            "tokenStored": token_stored,
            "accountId": None,
            "checked": False,
        }

    try:
        authenticated = oauthToken.is_authenticated()
        account_id = oauthToken.get_account_id() if authenticated else None
        return {
            "authenticated": authenticated,
            "tokenStored": token_stored,
            "accountId": account_id,
            "checked": True,
        }
    except (
        AttributeError,
        OSError,
        RuntimeError,
        ValueError,
        oauthToken.TokenRefreshError,
    ):
        return {
            "authenticated": False,
            "tokenStored": token_stored,
            "accountId": None,
            "checked": True,
        }


def validate_provider_connection(req: ConfigureRequest) -> dict[str, Any]:
    """LLM provider 연결 가능 여부만 검증한다."""
    from dartlab.ai import get_config
    from dartlab.ai.providers import create_provider
    from dartlab.ai.types import LLMConfig

    effective_provider = normalize_provider(req.provider) or req.provider
    current = get_config(effective_provider, role=normalize_role(req.role) or DEFAULT_ROLE)
    kwargs: dict[str, Any] = {
        "provider": effective_provider,
        "model": req.model or current.model,
        "api_key": req.api_key if req.api_key is not None else current.api_key,
        "base_url": req.base_url or current.base_url,
        "temperature": current.temperature,
        "max_tokens": current.max_tokens,
        "system_prompt": current.system_prompt,
    }

    available = False
    model = None
    try:
        config = LLMConfig(**kwargs)
        provider = create_provider(config)
        available = provider.check_available()
        model = provider.resolved_model
    except (FileNotFoundError, ImportError, OSError, PermissionError, RuntimeError, ValueError):
        available = False
        model = None

    return {"ok": True, "provider": effective_provider, "available": available, "model": model}
