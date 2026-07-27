"""Shared AI profile / provider status helpers for server adapters."""

from __future__ import annotations

import os
import shutil
from typing import Any

from dartlab.ai.settings import DEFAULT_ROLE, getProfileManager, normalizeProvider, normalizeRole
from dartlab.server.models import ConfigureRequest

_TRUTHY = {"1", "true", "yes", "on"}


def selectedProvider(role: str | None = None) -> str | None:
    """Resolve selected provider from shared profile."""
    profile = getProfileManager().load()
    normalized_role = normalizeRole(role)
    if normalized_role:
        binding = profile.roles.get(normalized_role)
        if binding and binding.provider:
            return normalizeProvider(binding.provider) or binding.provider
    return normalizeProvider(profile.default_provider) or profile.default_provider


def shouldPreloadOllama() -> bool:
    """Only preload Ollama when explicitly enabled and currently selected."""
    raw = os.environ.get("DARTLAB_PRELOAD_OLLAMA", "")
    if raw.strip().lower() not in _TRUTHY:
        return False
    profile = getProfileManager().load()
    if selectedProvider() == "ollama":
        return True
    return any(
        (normalizeProvider(binding.provider) or binding.provider) == "ollama" for binding in profile.roles.values()
    )


def probeProviderAvailability(prov: str) -> tuple[bool | None, str | None, bool]:
    """provider 사용 가능 여부와 모델을 실제로 점검한다."""
    from dartlab.ai import getConfig
    from dartlab.ai.providers import createProvider

    try:
        config = getConfig(prov)
        provider = createProvider(config)
        available = provider.checkAvailable()
        return available, provider.resolvedModel, True
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


def buildOllamaDetail(*, probe: bool) -> dict[str, Any]:
    """Ollama 설치/실행/GPU 상태를 조회한다."""
    if probe:
        try:
            from dartlab.ai.providers.support.ollamaSetup import detectOllama, getInstallGuide

            ollama_info = detectOllama()
            detail = {
                "installed": ollama_info.get("installed", False),
                "running": ollama_info.get("running", False),
                "gpu": ollama_info.get("gpu", None),
                "checked": True,
            }
            if not ollama_info.get("installed"):
                detail["installGuide"] = getInstallGuide()
            return detail
        except (FileNotFoundError, ImportError, OSError, PermissionError, RuntimeError, ValueError):
            return {"installed": False, "running": False, "gpu": None, "checked": True}

    return {
        "installed": bool(shutil.which("ollama")),
        "running": None,
        "gpu": None,
        "checked": False,
    }


def buildCodexDetail(*, probe: bool) -> dict[str, Any]:
    """Codex CLI 상태. probe=False 면 subprocess 없이 PATH 존재만 확인.

    detect_codex() 는 codex CLI 5 회 직렬 호출 (Windows Node 콜드 스타트 회당 0.3~0.7s)
    + OAuth 토큰 만료 시 refresh 네트워크 호출. 화면 첫 로드 (probe=0) 에서는 회피.
    """
    if not probe:
        return {
            "installed": bool(shutil.which("codex")),
            "authenticated": False,
            "authMode": None,
            "loginStatus": None,
            "version": None,
            "checked": False,
        }
    try:
        from dartlab.ai.providers.support.cliSetup import detectCodex

        return detectCodex()
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
        return {
            "installed": False,
            "authenticated": False,
            "authMode": None,
            "loginStatus": None,
            "version": None,
            "checked": True,
        }


def buildOauthCodexDetail(*, probe: bool) -> dict[str, Any]:
    """OAuth Codex 인증/토큰 상태를 조회한다."""
    try:
        from dartlab.ai.providers.support import oauthToken
    except (ImportError, OSError, RuntimeError):
        return {"authenticated": False, "tokenStored": False, "accountId": None, "checked": probe}

    token_stored = False
    try:
        token_stored = oauthToken.loadToken() is not None
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
        authenticated = oauthToken.isAuthenticated()
        account_id = oauthToken.getAccountId() if authenticated else None
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


def validateProviderConnection(req: ConfigureRequest) -> dict[str, Any]:
    """LLM provider 연결 가능 여부만 검증한다."""
    from dartlab.ai import getConfig
    from dartlab.ai.providers import createProvider
    from dartlab.ai.settings.types import LLMConfig

    effective_provider = normalizeProvider(req.provider) or req.provider
    current = getConfig(effective_provider, role=normalizeRole(req.role) or DEFAULT_ROLE)
    kwargs: dict[str, Any] = {
        "provider": effective_provider,
        "model": req.model or current.model,
        "apiKey": req.apiKey if req.apiKey is not None else current.apiKey,
        "baseUrl": req.baseUrl or current.baseUrl,
        "temperature": current.temperature,
        "maxTokens": current.maxTokens,
        "systemPrompt": current.systemPrompt,
    }

    available = False
    model = None
    try:
        config = LLMConfig(**kwargs)
        provider = createProvider(config)
        available = provider.checkAvailable()
        model = provider.resolvedModel
    except (FileNotFoundError, ImportError, OSError, PermissionError, RuntimeError, ValueError):
        available = False
        model = None

    return {"ok": True, "provider": effective_provider, "available": available, "model": model}
