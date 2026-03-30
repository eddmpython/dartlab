"""AI provider 카탈로그 — 메타데이터, 정규화, 카탈로그 빌드."""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.guide.routing import AI_ROLES


@dataclass(frozen=True)
class ProviderSpec:
    """AI provider 메타데이터 — 인증 방식, 프로빙 정책, 지원 역할."""

    id: str
    label: str
    description: str
    auth_kind: str
    public: bool = True
    setup_kind: str = "runtime"
    env_key: str | None = None
    probe_policy: str = "on_demand"
    supported_roles: tuple[str, ...] = AI_ROLES
    signupUrl: str | None = None
    freeTierHint: str | None = None


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
        label="Google Gemini (무료)",
        description="Gemini 2.5 Pro/Flash, AI Studio 무료 API key",
        auth_kind="api_key",
        setup_kind="api_key",
        env_key="GEMINI_API_KEY",
        probe_policy="credentialed",
        signupUrl="https://aistudio.google.com/apikey",
        freeTierHint="무료 — Gemini 2.5 Pro/Flash",
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
        signupUrl="https://platform.openai.com/api-keys",
    ),
    "custom": ProviderSpec(
        id="custom",
        label="Custom OpenAI-Compatible",
        description="OpenAI 호환 API 엔드포인트",
        auth_kind="api_key",
        setup_kind="api_key",
        probe_policy="credentialed",
    ),
    "groq": ProviderSpec(
        id="groq",
        label="Groq (무료)",
        description="Groq Cloud — 초고속 추론, LLaMA 3.3 70B 무료",
        auth_kind="api_key",
        setup_kind="api_key",
        env_key="GROQ_API_KEY",
        probe_policy="credentialed",
        signupUrl="https://console.groq.com/keys",
        freeTierHint="무료 — 초고속 추론, LLaMA 3.3 70B",
    ),
    "cerebras": ProviderSpec(
        id="cerebras",
        label="Cerebras (무료)",
        description="Cerebras Inference — 1M tokens/day 무료, 함수호출 벤치마크 1위",
        auth_kind="api_key",
        setup_kind="api_key",
        env_key="CEREBRAS_API_KEY",
        probe_policy="credentialed",
        signupUrl="https://cloud.cerebras.ai/",
        freeTierHint="무료 — 1M tokens/day 영구",
    ),
    "mistral": ProviderSpec(
        id="mistral",
        label="Mistral AI (무료)",
        description="Mistral AI — 1B tokens/month 무료, 다양한 모델",
        auth_kind="api_key",
        setup_kind="api_key",
        env_key="MISTRAL_API_KEY",
        probe_policy="credentialed",
        signupUrl="https://console.mistral.ai/api-keys",
        freeTierHint="무료 — 1B tokens/month",
    ),
}


def normalize_provider(provider: str | None) -> str | None:
    """provider 문자열 정규화. 알려진 provider면 그대로, 아니면 원본 반환."""
    if provider is None:
        return None
    normalized = provider.strip()
    return normalized if normalized in _PROVIDERS else provider


def get_provider_spec(provider: str) -> ProviderSpec | None:
    """provider id로 ProviderSpec 조회. 미등록이면 None."""
    normalized = normalize_provider(provider)
    if normalized is None:
        return None
    return _PROVIDERS.get(normalized)


def public_provider_ids() -> tuple[str, ...]:
    """공개(public=True) provider id 튜플."""
    return tuple(spec.id for spec in _PROVIDERS.values() if spec.public)


def provider_choices(*, include_hidden: bool = False) -> list[str]:
    """선택 가능한 provider id 목록."""
    return [spec.id for spec in _PROVIDERS.values() if include_hidden or spec.public]


def cli_provider_choices() -> list[str]:
    """CLI에서 사용 가능한 provider id 목록."""
    return provider_choices()


def build_provider_catalog(*, include_hidden: bool = False) -> list[dict[str, str | list[str]]]:
    """전체 provider 카탈로그를 JSON-safe list[dict]로 반환."""
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
        if spec.signupUrl:
            item["signupUrl"] = spec.signupUrl
        if spec.freeTierHint:
            item["freeTierHint"] = spec.freeTierHint
        items.append(item)
    return items


def api_key_secret_name(provider: str) -> str:
    """provider의 API 키 SecretStore 키 이름."""
    normalized = normalize_provider(provider) or provider
    return f"provider:{normalized}:api_key"


def oauth_secret_name(provider: str) -> str:
    """provider의 OAuth 토큰 SecretStore 키 이름."""
    normalized = normalize_provider(provider) or provider
    return f"provider:{normalized}:oauth"
