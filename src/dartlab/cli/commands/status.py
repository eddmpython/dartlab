"""`dartlab status` command."""

from __future__ import annotations

from dartlab.cli.context import PROVIDERS
from dartlab.cli.services.runtime import configure_dartlab

_SETUP_HINTS = {
    "oauth-codex": "dartlab setup oauth-codex",
    "codex": "dartlab setup codex",
    "ollama": "dartlab setup ollama",
    "openai": "dartlab setup openai",
    "custom": "dartlab setup custom",
}


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("status", help="LLM 연결 상태 확인")
    parser.add_argument("--provider", "-p", default=None, choices=PROVIDERS, help="확인할 provider")
    parser.set_defaults(handler=run)


def run(args) -> int:
    dartlab = configure_dartlab()

    providers = [args.provider] if args.provider else PROVIDERS
    single = len(providers) == 1

    if not single:
        # 요약 테이블
        print("\n  Provider          │ 상태   │ 모델             │ 설정 방법")
        print("  ──────────────────┼────────┼──────────────────┼─────────────────────")

    for provider_name in providers:
        status = dartlab.llm.status(provider=provider_name)
        available = status["available"]

        if single:
            _print_detail(provider_name, status)
        else:
            marker = "✓" if available else "✗"
            model = status.get("model", "-") or "-"
            hint = "" if available else _SETUP_HINTS.get(provider_name, "")
            print(f"  {provider_name:<18s} │ {marker:<5s}  │ {model:<16s} │ {hint}")

    if not single:
        avail = sum(1 for p in providers if dartlab.llm.status(provider=p)["available"])
        print(f"\n  {avail}/{len(providers)} provider 사용 가능")
        if avail == 0:
            print("  시작하려면: dartlab setup\n")
        else:
            print()
    return 0


def _print_detail(provider_name: str, status: dict) -> None:
    """단일 provider 상세 출력."""
    available = status["available"]
    marker = "●" if available else "○"
    print(f"\n{marker} {provider_name}")
    print(f"  model:     {status['model']}")
    print(f"  available: {available}")

    if provider_name == "ollama" and "ollama" in status:
        info = status["ollama"]
        print(f"  installed: {info['installed']}")
        print(f"  running:   {info['running']}")
        if info.get("models"):
            print(f"  models:    {', '.join(info['models'])}")
        if not info["installed"]:
            print("  setup:     dartlab setup ollama")
        elif not info["running"]:
            print("  setup:     ollama serve")

    elif provider_name == "codex" and "codex" in status:
        info = status["codex"]
        print(f"  installed: {info['installed']}")
        if info.get("version"):
            print(f"  version:   {info['version']}")
        if not info["installed"]:
            print("  setup:     dartlab setup codex")

    elif provider_name == "oauth-codex" and "oauth-codex" in status:
        info = status["oauth-codex"]
        print(f"  token:     {info['tokenStored']}")
        print(f"  auth:      {info['authenticated']}")
        if info.get("accountId"):
            print(f"  account:   {info['accountId']}")
        if not info["authenticated"]:
            print("  setup:     dartlab setup oauth-codex")

    elif provider_name in ("openai", "custom") and not available:
        print(f"  setup:     dartlab setup {provider_name}")

    print()
