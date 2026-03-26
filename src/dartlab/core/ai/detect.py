"""스마트 AI provider auto-detection.

우선순위: 프리미엄 → 무료 API → 로컬/CLI
각 provider별 가벼운 체크로 사용 가능한 첫 번째를 반환.
"""

from __future__ import annotations

# 감지 우선순위: 프리미엄(이미 인증) → 무료(env key) → 로컬/CLI
_DETECT_ORDER = (
    "oauth-codex", "openai",
    "gemini", "groq", "cerebras", "mistral",
    "ollama", "codex",
)


def _quick_check(provider_id: str) -> bool:
    """provider 사용 가능 여부를 빠르게 체크."""
    try:
        from dartlab.ai.providers import create_provider
        from dartlab.ai.types import LLMConfig

        config = LLMConfig(provider=provider_id)
        prov = create_provider(config)
        return prov.check_available()
    except (ImportError, RuntimeError, ConnectionError, OSError, ValueError):
        return False


def auto_detect_provider(*, verbose: bool = False) -> str | None:
    """사용 가능한 provider를 우선순위 순으로 탐색.

    Args:
        verbose: True면 감지 실패 시 안내 메시지 출력.

    Returns:
        사용 가능한 provider id. 모두 실패 시 None.
    """
    for provider_id in _DETECT_ORDER:
        if _quick_check(provider_id):
            return provider_id

    if verbose:
        from dartlab.core.ai.guide import no_provider_message

        print(no_provider_message())

    return None
