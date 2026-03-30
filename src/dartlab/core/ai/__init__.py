"""core/ai 패키지 — guide 패키지에서 re-import."""

from dartlab.guide.profile import AiProfileManager, get_profile_manager
from dartlab.guide.providers import (
    build_provider_catalog,
    cli_provider_choices,
    get_provider_spec,
    normalize_provider,
    provider_choices,
    public_provider_ids,
)
from dartlab.guide.routing import AI_ROLES, DEFAULT_ROLE, normalize_role
from dartlab.guide.secrets import SecretStore, get_secret_store

__all__ = [
    "AI_ROLES",
    "AiProfileManager",
    "DEFAULT_ROLE",
    "SecretStore",
    "build_provider_catalog",
    "cli_provider_choices",
    "get_profile_manager",
    "get_provider_spec",
    "get_secret_store",
    "normalize_provider",
    "normalize_role",
    "provider_choices",
    "public_provider_ids",
]
