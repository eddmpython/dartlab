"""AI provider 설정 안내 메시지 중앙 모듈.

노트북, CLI, 서버 에러 응답 등 모든 환경에서 재사용.
"""

from __future__ import annotations

from dartlab.core.ai.providers import _PROVIDERS

_PROVIDER_ALIAS: dict[str, str] = {
    "chatgpt": "oauth-codex",
    "gpt": "oauth-codex",
}

_SETUP_GUIDES: dict[str, dict[str, str]] = {
    "oauth-codex": {
        "name": "ChatGPT 구독 계정",
        "short": "브라우저 로그인 (ChatGPT Plus/Pro)",
        "setup_notebook": 'dartlab.setup("chatgpt")',
        "setup_cli": "dartlab setup oauth-codex",
        "detail": (
            "ChatGPT Plus 또는 Pro 구독자는 API 키 없이 사용할 수 있습니다.\n"
            "브라우저에서 ChatGPT 계정으로 로그인하면 자동 인증됩니다."
        ),
    },
    "openai": {
        "name": "OpenAI API",
        "short": "API 키 필요 (GPT-5.4, o4 등)",
        "setup_notebook": 'dartlab.llm.configure(provider="openai", api_key="sk-...")',
        "setup_cli": "dartlab setup openai",
        "detail": (
            "OpenAI API 키가 필요합니다.\n"
            "https://platform.openai.com/api-keys 에서 발급받으세요."
        ),
    },
    "ollama": {
        "name": "로컬 LLM (무료)",
        "short": "오프라인, 프라이빗 — 설치 필요",
        "setup_notebook": 'dartlab.setup("ollama")',
        "setup_cli": "dartlab setup ollama",
        "detail": (
            "무료, 오프라인으로 사용 가능한 로컬 LLM입니다.\n"
            "https://ollama.com/download 에서 설치 후 `ollama serve` 실행."
        ),
    },
    "codex": {
        "name": "Codex CLI",
        "short": "코딩 에이전트용",
        "setup_notebook": 'dartlab.setup("codex")',
        "setup_cli": "dartlab setup codex",
        "detail": (
            "코딩 에이전트 전용 provider입니다.\n"
            "`npm install -g @openai/codex` 설치 후 `codex login`."
        ),
    },
}

# provider 표시 순서 (사용자 권장 순)
_DISPLAY_ORDER = ("oauth-codex", "openai", "ollama", "codex")


def resolve_alias(provider: str) -> str:
    """사용자 편의 alias를 정식 provider id로 변환."""
    return _PROVIDER_ALIAS.get(provider.lower(), provider)


def provider_guide(provider: str) -> str:
    """특정 provider의 설정 안내 반환."""
    provider = resolve_alias(provider)
    guide = _SETUP_GUIDES.get(provider)
    if guide is None:
        return f"  알 수 없는 provider: {provider}"

    detail_lines = "\n".join(f"  {line}" for line in guide["detail"].split("\n"))
    lines = [
        f"  [ {guide['name']} ]",
        "",
        detail_lines,
        "",
        f"  노트북:  {guide['setup_notebook']}",
        f"  CLI:     {guide['setup_cli']}",
    ]
    return "\n".join(lines)


def _check_provider_available(provider_id: str) -> bool:
    """provider 사용 가능 여부를 빠르게 체크 (네트워크 최소화)."""
    try:
        from dartlab.engines.ai.providers import create_provider
        from dartlab.engines.ai.types import LLMConfig

        config = LLMConfig(provider=provider_id)
        prov = create_provider(config)
        return prov.check_available()
    except (ImportError, RuntimeError, ConnectionError, OSError, ValueError):
        return False


def providers_status() -> str:
    """전체 provider 현황 테이블 반환."""
    lines = ["", "  AI Provider 현황", ""]

    for pid in _DISPLAY_ORDER:
        spec = _PROVIDERS.get(pid)
        guide = _SETUP_GUIDES.get(pid)
        if spec is None or guide is None:
            continue

        available = _check_provider_available(pid)
        marker = "●" if available else "○"
        status = "✓ 사용 가능" if available else "✗ 설정 필요"
        name = guide["name"]
        # 한글은 2칸, ASCII는 1칸으로 계산하여 고정폭 정렬
        display_width = sum(2 if ord(c) > 127 else 1 for c in name)
        padded_name = name + " " * max(0, 20 - display_width)
        lines.append(f"  {marker} {pid:<15s} {padded_name} {status}")

    lines.append("")
    lines.append('  설정: dartlab.setup("provider이름")')
    lines.append('  예시: dartlab.setup("chatgpt")')
    lines.append("")
    return "\n".join(lines)


def no_provider_message() -> str:
    """provider 미설정 시 안내 메시지."""
    lines = [
        "",
        "  AI provider가 설정되지 않았습니다.",
        "",
        "  아래 중 하나를 설정하세요:",
        "",
        '  1. ChatGPT (권장)  — dartlab.setup("chatgpt")',
        '  2. OpenAI API      — dartlab.llm.configure(provider="openai", api_key="sk-...")',
        '  3. 로컬 LLM (무료) — dartlab.setup("ollama")',
        "",
        '  설정 후: dartlab.ask("삼성전자 재무건전성 분석해줘")',
        "",
    ]
    return "\n".join(lines)
