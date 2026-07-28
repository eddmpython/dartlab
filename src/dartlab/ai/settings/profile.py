"""AI 프로필 로드/저장/업데이트 관리자."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dartlab.ai.settings.modelResolver import resolveDefaultModel
from dartlab.ai.settings.providerCatalog import (
    apiKeySecretName,
    buildProviderCatalog,
    getProviderSpec,
    normalizeProvider,
    oauthSecretName,
    publicProviderIds,
)
from dartlab.ai.settings.routing import AI_ROLES, DEFAULT_ROLE, normalizeRole
from dartlab.ai.settings.secrets import SecretStore, getSecretStore
from dartlab.core.providers.secrets import dartlabHome


def _utcNow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ProviderProfile:
    """AI provider별 설정 (모델, base URL)."""

    model: str | None = None
    baseUrl: str | None = None


@dataclass
class RoleBinding:
    """역할별 provider/모델 바인딩."""

    provider: str | None = None
    model: str | None = None


@dataclass
class AiProfile:
    """AI 설정 프로필 — provider/role/temperature/max_tokens 통합 관리."""

    version: int = 2
    revision: int = 0
    default_provider: str = "oauth-codex"
    providers: dict[str, ProviderProfile] = field(default_factory=dict)
    roles: dict[str, RoleBinding] = field(default_factory=dict)
    temperature: float = 0.3
    maxTokens: int = 4096
    systemPrompt: str | None = None
    updated_at: str | None = None
    updatedBy: str | None = None


def _defaultRoles(provider: str, providers: dict[str, ProviderProfile]) -> dict[str, RoleBinding]:
    defaultModel = providers.get(provider).model if provider in providers else None
    return {role: RoleBinding(provider=provider, model=defaultModel) for role in AI_ROLES}


class AiProfileManager:
    """AI 프로필 로드/저장/업데이트 관리자."""

    def __init__(self, path: Path | None = None, secretStore: SecretStore | None = None) -> None:
        self.path = path or (dartlabHome() / "ai_profile.json")
        self.secretStore = secretStore or getSecretStore()

    def _bootstrap(self) -> AiProfile:
        return AiProfile(
            default_provider="oauth-codex",
            roles=_defaultRoles("oauth-codex", {}),
            updated_at=_utcNow(),
            updatedBy="bootstrap",
        )

    def load(self) -> AiProfile:
        """JSON 파일에서 프로필 로드. 없으면 기본값 반환."""
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
                normalized = normalizeProvider(name) or name
                if getProviderSpec(normalized) is None or not isinstance(item, dict):
                    continue
                providers[normalized] = ProviderProfile(
                    model=item.get("model"),
                    baseUrl=item.get("base_url") or item.get("baseUrl"),
                )

        default_provider = (
            normalizeProvider(data.get("defaultProvider")) or normalizeProvider(data.get("provider")) or "oauth-codex"
        )
        default_spec = getProviderSpec(default_provider)
        if default_spec is None or DEFAULT_ROLE not in default_spec.supported_roles:
            default_provider = "oauth-codex"

        roles: dict[str, RoleBinding] = {}
        roles_raw = data.get("roles", {})
        if isinstance(roles_raw, dict):
            for role_name, binding in roles_raw.items():
                normalized_role = normalizeRole(role_name)
                if normalized_role is None or not isinstance(binding, dict):
                    continue
                bound_provider = normalizeProvider(binding.get("provider")) or default_provider
                bound_spec = getProviderSpec(bound_provider)
                if bound_spec is None or normalized_role not in bound_spec.supported_roles:
                    bound_provider = default_provider
                roles[normalized_role] = RoleBinding(
                    provider=bound_provider,
                    model=binding.get("model"),
                )

        for role_name, binding in _defaultRoles(default_provider, providers).items():
            roles.setdefault(role_name, binding)

        return AiProfile(
            version=2,
            revision=int(data.get("revision", 0)),
            default_provider=default_provider,
            providers=providers,
            roles=roles,
            temperature=float(data.get("temperature", 0.3)),
            maxTokens=int(data.get("max_tokens", data.get("maxTokens", 4096))),
            systemPrompt=data.get("system_prompt") or data.get("systemPrompt"),
            updated_at=data.get("updated_at") or data.get("updatedAt") or _utcNow(),
            updatedBy=data.get("updated_by") or data.get("updatedBy") or "unknown",
        )

    def save(self, profile: AiProfile) -> AiProfile:
        """프로필을 JSON 파일로 원자적 저장."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 2,
            "revision": profile.revision,
            "defaultProvider": profile.default_provider,
            "providers": {
                name: {
                    "model": item.model,
                    "base_url": item.baseUrl,
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
            "max_tokens": profile.maxTokens,
            "system_prompt": profile.systemPrompt,
            "updated_at": profile.updated_at,
            "updated_by": profile.updatedBy,
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

    def ensureProvider(self, profile: AiProfile, provider: str) -> ProviderProfile:
        """provider가 프로필에 없으면 기본 ProviderProfile로 생성."""
        normalized = normalizeProvider(provider) or provider
        if normalized not in profile.providers:
            profile.providers[normalized] = ProviderProfile()
        return profile.providers[normalized]

    def ensureRole(self, profile: AiProfile, role: str) -> RoleBinding:
        """role이 프로필에 없으면 기본 RoleBinding으로 생성."""
        normalized = normalizeRole(role)
        if normalized is None:
            raise ValueError(f"지원하지 않는 role: {role}")
        if normalized not in profile.roles:
            defaultModel = (
                profile.providers.get(profile.default_provider).model
                if profile.default_provider in profile.providers
                else None
            )
            profile.roles[normalized] = RoleBinding(provider=profile.default_provider, model=defaultModel)
        return profile.roles[normalized]

    def update(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        role: str | None = None,
        baseUrl: str | None = None,
        temperature: float | None = None,
        maxTokens: int | None = None,
        systemPrompt: str | None = None,
        updatedBy: str = "code",
    ) -> AiProfile:
        """프로필 부분 업데이트 후 저장. revision 자동 증가."""
        profile = self.load()
        normalized_role = normalizeRole(role)
        if role is not None and normalized_role is None:
            raise ValueError(f"지원하지 않는 role: {role}")

        target_provider = normalizeProvider(provider) if provider is not None else None
        if target_provider is not None and getProviderSpec(target_provider) is None:
            raise ValueError(f"지원하지 않는 provider: {target_provider}")

        old_default = profile.default_provider

        if normalized_role is None:
            effective_provider = target_provider or profile.default_provider
            if target_provider is not None:
                profile.default_provider = target_provider
            target = self.ensureProvider(profile, effective_provider)
            if model is not None:
                target.model = model
            if baseUrl is not None:
                target.baseUrl = baseUrl
            if target_provider is not None:
                for binding in profile.roles.values():
                    if binding.provider in (None, old_default):
                        binding.provider = target_provider
                        if model is not None:
                            binding.model = model
                        elif binding.model is None:
                            binding.model = target.model
        else:
            binding = self.ensureRole(profile, normalized_role)
            effective_provider = target_provider or binding.provider or profile.default_provider
            if getProviderSpec(effective_provider) is None:
                effective_provider = profile.default_provider
            binding.provider = effective_provider
            if model is not None:
                binding.model = model
            elif binding.model is None:
                binding.model = self.ensureProvider(profile, effective_provider).model
            if target_provider is not None:
                target = self.ensureProvider(profile, target_provider)
                if baseUrl is not None:
                    target.baseUrl = baseUrl
                if model is not None and target.model is None:
                    target.model = model

        if temperature is not None:
            profile.temperature = temperature
        if maxTokens is not None:
            profile.maxTokens = maxTokens
        if systemPrompt is not None:
            profile.systemPrompt = systemPrompt
        profile.revision += 1
        profile.updated_at = _utcNow()
        profile.updatedBy = updatedBy
        return self.save(profile)

    def resolve(self, provider: str | None = None, *, role: str | None = None) -> dict[str, Any]:
        """provider/role 기반으로 최종 설정(model, api_key 등) 해석."""
        profile = self.load()
        normalized_role = normalizeRole(role)
        explicit_provider = normalizeProvider(provider) if provider is not None else None

        if explicit_provider is not None and getProviderSpec(explicit_provider) is not None:
            target_provider = explicit_provider
            role_model = None
        else:
            binding = profile.roles.get(normalized_role or DEFAULT_ROLE)
            target_provider = binding.provider if binding and binding.provider else profile.default_provider
            role_model = binding.model if binding else None

        if getProviderSpec(target_provider) is None:
            target_provider = profile.default_provider

        settings = profile.providers.get(target_provider) or ProviderProfile()
        spec = getProviderSpec(target_provider)
        apiKey = None
        if spec and spec.auth_kind == "api_key":
            apiKey = self.secretStore.get(apiKeySecretName(target_provider))
        return {
            "provider": target_provider,
            "model": role_model or settings.model,
            "api_key": apiKey,
            "base_url": settings.baseUrl,
            "temperature": profile.temperature,
            "max_tokens": profile.maxTokens,
            "system_prompt": profile.systemPrompt,
        }

    def saveApiKey(self, provider: str, apiKey: str, *, updatedBy: str = "ui") -> AiProfile:
        """provider API 키를 SecretStore에 저장하고 프로필 갱신."""
        normalized = normalizeProvider(provider) or provider
        if getProviderSpec(normalized) is None:
            raise ValueError(f"지원하지 않는 provider: {normalized}")
        self.secretStore.set(apiKeySecretName(normalized), apiKey)
        return self.update(provider=normalized, updatedBy=updatedBy)

    def clearApiKey(self, provider: str, *, updatedBy: str = "ui") -> AiProfile:
        """provider API 키를 SecretStore에서 삭제하고 프로필 갱신."""
        normalized = normalizeProvider(provider) or provider
        if getProviderSpec(normalized) is None:
            raise ValueError(f"지원하지 않는 provider: {normalized}")
        self.secretStore.delete(apiKeySecretName(normalized))
        return self.update(provider=normalized, updatedBy=updatedBy)

    def serialize(self) -> dict[str, Any]:
        """프로필 + provider 카탈로그를 JSON-safe dict로 직렬화.

        allow_fetch=False — profile 화면 표시는 cold network HTTP (DNS/TLS cold
        ~40s) 를 절대 감당 못한다. cache 있으면 backend latest, 없으면 정적 fallback.
        실제 chat 호출은 별도 경로에서 평소대로 backend latest 사용.
        """
        profile = self.load()
        # secret 존재 판정은 _load() 1 회로 일괄 — provider 별 has() 호출 (9x file IO) 회피.
        secret_keys = self.secretStore.keys()
        provider_settings: dict[str, dict[str, Any]] = {}
        for providerId in publicProviderIds():
            settings = profile.providers.get(providerId) or ProviderProfile()
            spec = getProviderSpec(providerId)
            secret_configured = False
            if spec and spec.auth_kind == "api_key":
                secret_configured = apiKeySecretName(providerId) in secret_keys
            elif spec and spec.auth_kind == "oauth":
                secret_configured = oauthSecretName(providerId) in secret_keys
            effective_model = resolveDefaultModel(providerId, configuredModel=settings.model, allowFetch=False)
            provider_settings[providerId] = {
                "model": effective_model,
                "baseUrl": settings.baseUrl,
                "secretConfigured": secret_configured,
            }
        return {
            "defaultProvider": profile.default_provider,
            "temperature": profile.temperature,
            "maxTokens": profile.maxTokens,
            "systemPrompt": profile.systemPrompt,
            "updatedAt": profile.updated_at,
            "updatedBy": profile.updatedBy,
            "revision": profile.revision,
            "providers": provider_settings,
            "roles": {
                role: {
                    "provider": binding.provider,
                    "model": resolveDefaultModel(binding.provider, configuredModel=binding.model, allowFetch=False),
                }
                for role, binding in profile.roles.items()
            },
            "catalog": buildProviderCatalog(),
        }

    def fingerprint(self) -> str:
        """프로필 변경 감지용 fingerprint 문자열."""
        profile = self.load()
        role_fingerprint = ",".join(
            f"{role}:{binding.provider}:{binding.model or ''}" for role, binding in sorted(profile.roles.items())
        )
        return (
            f"{profile.revision}:{profile.updated_at}:{profile.updatedBy}:{profile.default_provider}:{role_fingerprint}"
        )


def getProfileManager() -> AiProfileManager:
    """기본 SecretStore를 사용하는 AiProfileManager 반환."""
    return AiProfileManager(secretStore=getSecretStore())
