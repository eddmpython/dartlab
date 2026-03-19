"""LLM 기반 기업분석 엔진.

사용법::

        import dartlab

        # 설정
        dartlab.llm.configure(provider="claude", api_key="sk-...")
        dartlab.llm.configure(provider="ollama", model="llama3.1")

        # 분석
        c = dartlab.Company("005930")
        c.ask("이 기업의 재무 건전성은?")
        c.ask("배당 추세를 분석해줘", include=["dividend", "IS"])
"""

from __future__ import annotations

from dartlab.engines.ai.types import LLMConfig, LLMResponse

_global_config: LLMConfig = LLMConfig()


def configure(
    provider: str = "openai",
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    system_prompt: str | None = None,
) -> None:
    """LLM 글로벌 설정.

    Example::

            import dartlab

            # OpenAI / GPT
            dartlab.llm.configure(provider="openai", api_key="sk-...")

            # Claude (API 키)
            dartlab.llm.configure(provider="claude", api_key="sk-ant-...")

            # Claude (프록시 / CLIProxyAPI)
            dartlab.llm.configure(provider="claude", base_url="http://localhost:8317/v1")

            # Ollama (로컬, 무료)
            dartlab.llm.configure(provider="ollama", model="llama3.1")

            # 커스텀 OpenAI 호환 엔드포인트
            dartlab.llm.configure(provider="custom", base_url="https://my-api.com/v1", api_key="key")

            # Claude Code CLI (Claude Pro/Max 구독, API 키 불필요)
            dartlab.llm.configure(provider="claude-code")
            dartlab.llm.configure(provider="claude-code", model="opus")

            # OpenAI Codex CLI (ChatGPT Plus/Pro 구독, API 키 불필요)
            dartlab.llm.configure(provider="codex")
    """
    global _global_config
    _global_config = LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
    )


def get_config() -> LLMConfig:
    """현재 글로벌 LLM 설정 반환."""
    return _global_config


def status() -> dict:
    """LLM 설정 및 provider 상태 확인.

    Returns:
            {
                    "provider": "ollama",
                    "model": "llama3.1",
                    "available": True,
                    "ollama": {...}  # ollama provider인 경우에만
            }
    """
    from dartlab.engines.ai.providers import create_provider

    provider = create_provider(_global_config)
    available = provider.check_available()

    result = {
        "provider": _global_config.provider,
        "model": provider.resolved_model,
        "available": available,
    }

    if _global_config.provider == "ollama":
        from dartlab.engines.ai.ollama_setup import detect_ollama

        result["ollama"] = detect_ollama()

    if _global_config.provider == "claude-code":
        from dartlab.engines.ai.cli_setup import detect_claude_code

        result["claude-code"] = detect_claude_code()

    if _global_config.provider == "codex":
        from dartlab.engines.ai.cli_setup import detect_codex

        result["codex"] = detect_codex()

    return result


from dartlab.engines.ai import aiParser as ai
from dartlab.engines.ai.tool_plugin import get_plugin_registry, tool

__all__ = ["configure", "get_config", "status", "LLMConfig", "LLMResponse", "ai", "tool", "get_plugin_registry"]
