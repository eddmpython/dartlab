from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dartlab.core.ai.providers import (
    api_key_secret_name,
    build_provider_catalog,
    get_provider_spec,
    normalize_provider,
    oauth_secret_name,
    public_provider_ids,
)
from dartlab.core.ai.routing import AI_ROLES, DEFAULT_ROLE, normalize_role
from dartlab.core.ai.secrets import SecretStore, get_secret_store


def _dartlab_home() -> Path:
    raw = os.environ.get("DARTLAB_HOME")
    if raw:
        return Path(raw)
    return Path.home() / ".dartlab"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ProviderProfile:
    model: str | None = None
    base_url: str | None = None


@dataclass
class RoleBinding:
    provider: str | None = None
    model: str | None = None


@dataclass
class AiProfile:
    version: int = 2
    revision: int = 0
    default_provider: str = "codex"
    providers: dict[str, ProviderProfile] = field(default_factory=dict)
    roles: dict[str, RoleBinding] = field(default_factory=dict)
    temperature: float = 0.3
    max_tokens: int = 4096
    system_prompt: str | None = None
    updated_at: str | None = None
    updated_by: str | None = None


def _default_roles(provider: str, providers: dict[str, ProviderProfile]) -> dict[str, RoleBinding]:
    default_model = providers.get(provider).model if provider in providers else None
    return {
        role: RoleBinding(provider=provider, model=default_model)
        for role in AI_ROLES
    }


class AiProfileManager:
    def __init__(self, path: Path | None = None, secret_store: SecretStore | None = None) -> None:
        self.path = path or (_dartlab_home() / "ai_profile.json")
        self.secret_store = secret_store or get_secret_store()

    def _bootstrap(self) -> AiProfile:
        return AiProfile(
            default_provider="codex",
            roles=_default_roles("codex", {}),
            updated_at=_utc_now(),
            updated_by="bootstrap",
        )

    def load(self) -> AiProfile:
        if not self.path.exists():
            return self._bootstrap()
        raw = self.path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return self._bootstrap()

        providers_raw = data.get("providers", {})
        providers: dict[str, ProviderProfile] = {}
        if isinstance(providers_raw, dict):
            for name, item in providers_raw.items():
                normalized = normalize_provider(name) or name
                if get_provider_spec(normalized) is None or not isinstance(item, dict):
                    continue
                providers[normalized] = ProviderProfile(
                    model=item.get("model"),
                    base_url=item.get("base_url") or item.get("baseUrl"),
                )

        default_provider = normalize_provider(data.get("defaultProvider")) or normalize_provider(data.get("provider")) or "codex"
        if get_provider_spec(default_provider) is None:
            default_provider = "codex"

        roles: dict[str, RoleBinding] = {}
        roles_raw = data.get("roles", {})
        if isinstance(roles_raw, dict):
            for role_name, binding in roles_raw.items():
                normalized_role = normalize_role(role_name)
                if normalized_role is None or not isinstance(binding, dict):
                    continue
                bound_provider = normalize_provider(binding.get("provider")) or default_provider
                if get_provider_spec(bound_provider) is None:
                    bound_provider = default_provider
                roles[normalized_role] = RoleBinding(
                    provider=bound_provider,
                    model=binding.get("model"),
                )

        for role_name, binding in _default_roles(default_provider, providers).items():
            roles.setdefault(role_name, binding)

        return AiProfile(
            version=2,
            revision=int(data.get("revision", 0)),
            default_provider=default_provider,
            providers=providers,
            roles=roles,
            temperature=float(data.get("temperature", 0.3)),
            max_tokens=int(data.get("max_tokens", data.get("maxTokens", 4096))),
            system_prompt=data.get("system_prompt") or data.get("systemPrompt"),
            updated_at=data.get("updated_at") or data.get("updatedAt") or _utc_now(),
            updated_by=data.get("updated_by") or data.get("updatedBy") or "unknown",
        )

    def save(self, profile: AiProfile) -> AiProfile:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 2,
            "revision": profile.revision,
            "defaultProvider": profile.default_provider,
            "providers": {
                name: {
                    "model": item.model,
                    "base_url": item.base_url,
                }
                for name, item in profile.providers.items()
            },
            "roles": {
                role: {
                    "provider": binding.provider,
                    "model": binding.model,
                }
                for role, binding in profile.roles.items()
            },
            "temperature": profile.temperature,
            "max_tokens": profile.max_tokens,
            "system_prompt": profile.system_prompt,
            "updated_at": profile.updated_at,
            "updated_by": profile.updated_by,
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        fd, tmp_path = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            fd = -1
            tmp = Path(tmp_path)
            if os.name != "nt":
                tmp.chmod(0o600)
            tmp.replace(self.path)
        finally:
            if fd >= 0:
                os.close(fd)
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        return profile

    def ensure_provider(self, profile: AiProfile, provider: str) -> ProviderProfile:
        normalized = normalize_provider(provider) or provider
        if normalized not in profile.providers:
            profile.providers[normalized] = ProviderProfile()
        return profile.providers[normalized]

    def ensure_role(self, profile: AiProfile, role: str) -> RoleBinding:
        normalized = normalize_role(role)
        if normalized is None:
            raise ValueError(f"지원하지 않는 role: {role}")
        if normalized not in profile.roles:
            default_model = profile.providers.get(profile.default_provider).model if profile.default_provider in profile.providers else None
            profile.roles[normalized] = RoleBinding(provider=profile.default_provider, model=default_model)
        return profile.roles[normalized]

    def update(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        role: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        updated_by: str = "code",
    ) -> AiProfile:
        profile = self.load()
        normalized_role = normalize_role(role)
        if role is not None and normalized_role is None:
            raise ValueError(f"지원하지 않는 role: {role}")

        target_provider = normalize_provider(provider) if provider is not None else None
        if target_provider is not None and get_provider_spec(target_provider) is None:
            raise ValueError(f"지원하지 않는 provider: {target_provider}")

        old_default = profile.default_provider

        if normalized_role is None:
            effective_provider = target_provider or profile.default_provider
            if target_provider is not None:
                profile.default_provider = target_provider
            target = self.ensure_provider(profile, effective_provider)
            if model is not None:
                target.model = model
            if base_url is not None:
                target.base_url = base_url
            if target_provider is not None:
                for binding in profile.roles.values():
                    if binding.provider in (None, old_default):
                        binding.provider = target_provider
                        if model is not None:
                            binding.model = model
                        elif binding.model is None:
                            binding.model = target.model
        else:
            binding = self.ensure_role(profile, normalized_role)
            effective_provider = target_provider or binding.provider or profile.default_provider
            if get_provider_spec(effective_provider) is None:
                effective_provider = profile.default_provider
            binding.provider = effective_provider
            if model is not None:
                binding.model = model
            elif binding.model is None:
                binding.model = self.ensure_provider(profile, effective_provider).model
            if target_provider is not None:
                target = self.ensure_provider(profile, target_provider)
                if base_url is not None:
                    target.base_url = base_url
                if model is not None and target.model is None:
                    target.model = model

        if temperature is not None:
            profile.temperature = temperature
        if max_tokens is not None:
            profile.max_tokens = max_tokens
        if system_prompt is not None:
            profile.system_prompt = system_prompt
        profile.revision += 1
        profile.updated_at = _utc_now()
        profile.updated_by = updated_by
        return self.save(profile)

    def resolve(self, provider: str | None = None, *, role: str | None = None) -> dict[str, Any]:
        profile = self.load()
        normalized_role = normalize_role(role)
        explicit_provider = normalize_provider(provider) if provider is not None else None

        if explicit_provider is not None and get_provider_spec(explicit_provider) is not None:
            target_provider = explicit_provider
            role_model = None
        else:
            binding = profile.roles.get(normalized_role or DEFAULT_ROLE)
            target_provider = binding.provider if binding and binding.provider else profile.default_provider
            role_model = binding.model if binding else None

        if get_provider_spec(target_provider) is None:
            target_provider = profile.default_provider

        settings = profile.providers.get(target_provider) or ProviderProfile()
        spec = get_provider_spec(target_provider)
        api_key = None
        if spec and spec.auth_kind == "api_key":
            api_key = self.secret_store.get(api_key_secret_name(target_provider))
        return {
            "provider": target_provider,
            "model": role_model or settings.model,
            "api_key": api_key,
            "base_url": settings.base_url,
            "temperature": profile.temperature,
            "max_tokens": profile.max_tokens,
            "system_prompt": profile.system_prompt,
        }

    def save_api_key(self, provider: str, api_key: str, *, updated_by: str = "ui") -> AiProfile:
        normalized = normalize_provider(provider) or provider
        if get_provider_spec(normalized) is None:
            raise ValueError(f"지원하지 않는 provider: {normalized}")
        self.secret_store.set(api_key_secret_name(normalized), api_key)
        return self.update(provider=normalized, updated_by=updated_by)

    def clear_api_key(self, provider: str, *, updated_by: str = "ui") -> AiProfile:
        normalized = normalize_provider(provider) or provider
        if get_provider_spec(normalized) is None:
            raise ValueError(f"지원하지 않는 provider: {normalized}")
        self.secret_store.delete(api_key_secret_name(normalized))
        return self.update(provider=normalized, updated_by=updated_by)

    def serialize(self) -> dict[str, Any]:
        profile = self.load()
        provider_settings: dict[str, dict[str, Any]] = {}
        for provider_id in public_provider_ids():
            settings = profile.providers.get(provider_id) or ProviderProfile()
            spec = get_provider_spec(provider_id)
            secret_configured = False
            if spec and spec.auth_kind == "api_key":
                secret_configured = self.secret_store.has(api_key_secret_name(provider_id))
            elif spec and spec.auth_kind == "oauth":
                secret_configured = self.secret_store.has(oauth_secret_name(provider_id))
            provider_settings[provider_id] = {
                "model": settings.model,
                "baseUrl": settings.base_url,
                "secretConfigured": secret_configured,
            }
        return {
            "defaultProvider": profile.default_provider,
            "temperature": profile.temperature,
            "maxTokens": profile.max_tokens,
            "systemPrompt": profile.system_prompt,
            "updatedAt": profile.updated_at,
            "updatedBy": profile.updated_by,
            "revision": profile.revision,
            "providers": provider_settings,
            "roles": {
                role: {
                    "provider": binding.provider,
                    "model": binding.model,
                }
                for role, binding in profile.roles.items()
            },
            "catalog": build_provider_catalog(),
        }

    def fingerprint(self) -> str:
        profile = self.load()
        role_fingerprint = ",".join(
            f"{role}:{binding.provider}:{binding.model or ''}"
            for role, binding in sorted(profile.roles.items())
        )
        return f"{profile.revision}:{profile.updated_at}:{profile.updated_by}:{profile.default_provider}:{role_fingerprint}"


def get_profile_manager() -> AiProfileManager:
    return AiProfileManager(secret_store=get_secret_store())
