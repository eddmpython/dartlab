from __future__ import annotations

from dataclasses import dataclass

from dartlab.core.ai.routing import AI_ROLES


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    description: str
    auth_kind: str
    public: bool = True
    setup_kind: str = "runtime"
    env_key: str | None = None
    probe_policy: str = "on_demand"
    supported_roles: tuple[str, ...] = AI_ROLES


_PROVIDERS: dict[str, ProviderSpec] = {
    "oauth-codex": ProviderSpec(
        id="oauth-codex",
        label="GPT (ChatGPT 구독 계정)",
        description="브라우저 OAuth 로그인, GUI 대화/분석 권장",
        auth_kind="oauth",
        setup_kind="oauth",
        probe_policy="selected_only",
    ),
    "gemini": ProviderSpec(
        id="gemini",
        label="Google Gemini (구독/무료)",
        description="Gemini 2.5 Pro/Flash, 브라우저 OAuth 로그인",
        auth_kind="oauth",
        setup_kind="oauth",
        probe_policy="credentialed",
    ),
    "codex": ProviderSpec(
        id="codex",
        label="Codex CLI (코딩용)",
        description="Codex CLI 로그인 기반 에이전트. GUI 일반 대화/분석용으로는 비권장",
        auth_kind="cli",
        setup_kind="cli",
        probe_policy="selected_only",
        supported_roles=("coding",),
    ),
    "ollama": ProviderSpec(
        id="ollama",
        label="Ollama (로컬)",
        description="무료, 오프라인, 프라이빗",
        auth_kind="none",
        setup_kind="local",
        probe_policy="selected_only",
    ),
    "openai": ProviderSpec(
        id="openai",
        label="OpenAI API",
        description="GPT-5.4, o4 등 전체 모델",
        auth_kind="api_key",
        setup_kind="api_key",
        env_key="OPENAI_API_KEY",
        probe_policy="credentialed",
    ),
    "custom": ProviderSpec(
        id="custom",
        label="Custom OpenAI-Compatible",
        description="OpenAI 호환 API 엔드포인트",
        auth_kind="api_key",
        setup_kind="api_key",
        probe_policy="credentialed",
    ),
}


def normalize_provider(provider: str | None) -> str | None:
    if provider is None:
        return None
    normalized = provider.strip()
    return normalized if normalized in _PROVIDERS else provider


def get_provider_spec(provider: str) -> ProviderSpec | None:
    normalized = normalize_provider(provider)
    if normalized is None:
        return None
    return _PROVIDERS.get(normalized)


def public_provider_ids() -> tuple[str, ...]:
    return tuple(spec.id for spec in _PROVIDERS.values() if spec.public)


def provider_choices(*, include_hidden: bool = False) -> list[str]:
    return [spec.id for spec in _PROVIDERS.values() if include_hidden or spec.public]


def cli_provider_choices() -> list[str]:
    return provider_choices()


def build_provider_catalog(*, include_hidden: bool = False) -> list[dict[str, str | list[str]]]:
    items: list[dict[str, str | list[str]]] = []
    for spec in _PROVIDERS.values():
        if not include_hidden and not spec.public:
            continue
        item: dict[str, str | list[str]] = {
            "id": spec.id,
            "label": spec.label,
            "description": spec.description,
            "authKind": spec.auth_kind,
            "setupKind": spec.setup_kind,
            "probePolicy": spec.probe_policy,
            "supportedRoles": list(spec.supported_roles),
        }
        if spec.env_key:
            item["envKey"] = spec.env_key
        items.append(item)
    return items


def api_key_secret_name(provider: str) -> str:
    normalized = normalize_provider(provider) or provider
    return f"provider:{normalized}:api_key"


def oauth_secret_name(provider: str) -> str:
    normalized = normalize_provider(provider) or provider
    return f"provider:{normalized}:oauth"
