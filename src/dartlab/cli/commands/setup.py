"""`dartlab setup` command."""

from __future__ import annotations

from dartlab.cli.context import CLI_PROVIDERS
from dartlab.cli.services.errors import CLIError


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("setup", help="LLM provider 설치 및 인증 안내")
    parser.add_argument("provider", nargs="?", default=None, choices=CLI_PROVIDERS, help="설정할 provider")
    parser.set_defaults(handler=run)


def run(args) -> int:
    try:
        from dartlab.engines.ai.cli_setup import detect_claude_code, detect_codex
    except Exception as exc:
        raise CLIError(f"setup 정보를 불러오지 못했습니다: {exc}") from exc

    if args.provider is None:
        print("\n사용 가능한 provider:\n")
        print("  dartlab setup codex        ChatGPT Plus/Pro 구독 (API 키 불필요)")
        print("  dartlab setup claude-code  Claude Pro/Max 구독 (API 키 불필요)")
        print("  dartlab setup ollama       로컬 LLM (무료)\n")
        return 0

    if args.provider == "codex":
        _setup_codex(detect_codex())
    elif args.provider == "claude-code":
        _setup_claude_code(detect_claude_code())
    elif args.provider == "ollama":
        _setup_ollama()
    return 0


def _setup_codex(info: dict) -> None:
    print("\n[ Codex CLI 설정 — ChatGPT Plus/Pro 구독 ]\n")

    if info["installed"]:
        print(f"  1. 설치  ✓  ({info.get('version', 'installed')})")
    else:
        print("  1. 설치")
        print("     npm install -g @openai/codex\n")
        print("     Node.js가 필요합니다: https://nodejs.org/\n")

    print("  2. 인증")
    if info["installed"]:
        print("     터미널에서 codex 를 실행하면 브라우저가 열립니다.")
        print("     ChatGPT 계정으로 로그인하세요.\n")
    else:
        print("     설치 후 codex 를 실행하면 브라우저에서 로그인됩니다.\n")

    print("  3. 확인")
    print("     dartlab status -p codex\n")

    print("  4. 사용")
    print('     dartlab ask 005930 "재무 건전성 분석" -p codex')
    print()


def _setup_claude_code(info: dict) -> None:
    print("\n[ Claude Code CLI 설정 — Claude Pro/Max 구독 ]\n")

    if info["installed"]:
        print(f"  1. 설치  ✓  ({info.get('version', 'installed')})")
    else:
        print("  1. 설치")
        print("     npm install -g @anthropic-ai/claude-code\n")
        print("     Node.js가 필요합니다: https://nodejs.org/\n")

    if info.get("authenticated"):
        print("  2. 인증  ✓")
    else:
        print("  2. 인증")
        print("     claude auth login\n")
        print("     브라우저가 열리면 Claude 계정으로 로그인하세요.\n")

    print("  3. 확인")
    print("     dartlab status -p claude-code\n")

    print("  4. 사용")
    print('     dartlab ask 005930 "재무 건전성 분석" -p claude-code')
    print('     dartlab ask 삼성전자 "배당 분석" -p claude-code -m opus')
    print()


def _setup_ollama() -> None:
    print("\n[ Ollama 설정 — 로컬 LLM (무료) ]\n")

    print("  1. 설치")
    print("     https://ollama.com/download\n")

    print("  2. 모델 다운로드")
    print("     ollama pull llama3.2\n")

    print("  3. 서버 시작")
    print("     ollama serve\n")

    print("  4. 확인")
    print("     dartlab status -p ollama\n")

    print("  5. 사용")
    print('     dartlab ask 005930 "재무 건전성 분석" -p ollama')
    print()
