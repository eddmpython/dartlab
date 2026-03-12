"""`dartlab status` command."""

from __future__ import annotations

from dartlab.cli.context import PROVIDERS
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("status", help="LLM 연결 상태 확인")
    parser.add_argument("--provider", "-p", default=None, choices=PROVIDERS, help="확인할 provider")
    parser.set_defaults(handler=run)


def run(args) -> int:
    dartlab = configure_dartlab()

    providers = [args.provider] if args.provider else PROVIDERS

    for provider_name in providers:
        dartlab.llm.configure(provider=provider_name)
        status = dartlab.llm.status()

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

        elif provider_name == "claude-code" and "claude-code" in status:
            info = status["claude-code"]
            print(f"  installed: {info['installed']}")
            print(f"  authenticated: {info['authenticated']}")
            if info.get("version"):
                print(f"  version:   {info['version']}")
            if not info["installed"] or not info["authenticated"]:
                print("  setup:     dartlab setup claude-code")

        elif provider_name == "codex" and "codex" in status:
            info = status["codex"]
            print(f"  installed: {info['installed']}")
            if info.get("version"):
                print(f"  version:   {info['version']}")
            if not info["installed"]:
                print("  setup:     dartlab setup codex")

        elif provider_name in ("openai", "claude", "custom") and not available:
            print(f"  setup:     dartlab ask ... -p {provider_name} --api-key YOUR_KEY")

    print()
    return 0
