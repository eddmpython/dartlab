"""`dartlab setup` command."""

from __future__ import annotations

from dartlab.cli.context import CLI_PROVIDERS
from dartlab.cli.services.errors import CLIError


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("setup", help="LLM provider 설치 및 인증 안내")
    parser.add_argument("provider", nargs="?", default=None, choices=CLI_PROVIDERS, help="설정할 provider")
    parser.add_argument("--login", action="store_true", help="oauth-codex 브라우저 로그인 강제 실행")
    parser.set_defaults(handler=run)


def run(args) -> int:
    try:
        from dartlab.engines.ai.providers.support.cli_setup import detect_codex
    except (ImportError, ModuleNotFoundError) as exc:
        raise CLIError(f"setup 정보를 불러오지 못했습니다: {exc}") from exc

    if args.provider is None:
        print("\n사용 가능한 provider:\n")
        print("  dartlab setup oauth-codex  ChatGPT 구독 계정 — 브라우저 OAuth (권장)")
        print("  dartlab setup codex        Codex CLI — 코딩 에이전트용")
        print("  dartlab setup ollama       로컬 LLM (무료, 오프라인)")
        print("  dartlab setup openai       OpenAI API — GPT-4o 등 (API 키 필요)")
        print("  dartlab setup custom       OpenAI 호환 API — vLLM, Together 등\n")
        return 0

    if args.provider == "oauth-codex" and getattr(args, "login", False):
        handler = _do_oauth_login
    else:
        handler = {
            "oauth-codex": _setup_oauth_codex,
            "codex": lambda: _setup_codex(detect_codex()),
            "ollama": _setup_ollama,
            "openai": _setup_openai,
            "custom": _setup_custom,
        }.get(args.provider)
    if handler:
        handler()
    else:
        print(f"\n  알 수 없는 provider: {args.provider}\n")
    return 0


def _setup_oauth_codex() -> None:
    print("\n[ ChatGPT OAuth 설정 — 브라우저 로그인 (권장) ]\n")
    print("  ChatGPT Plus/Pro 구독자는 API 키 없이 사용할 수 있습니다.\n")

    # 이미 인증됐는지 확인
    try:
        from dartlab.engines.ai.providers.support.oauth_token import is_authenticated
        if is_authenticated():
            print("  ✓ 이미 인증되어 있습니다.\n")
            print("  재인증하려면 아래를 입력하세요:")
            print("     dartlab setup oauth-codex --login\n")
            return
    except ImportError:
        pass

    _do_oauth_login()


def _do_oauth_login() -> None:
    """브라우저에서 ChatGPT OAuth 로그인 실행."""
    import sys
    import threading
    import time
    import webbrowser
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs, urlparse

    try:
        from dartlab.engines.ai.providers.support.oauth_token import (
            OAUTH_REDIRECT_PORT,
            build_auth_url,
            exchange_code,
        )
    except ImportError:
        print("  OAuth 모듈을 불러올 수 없습니다.")
        print("  dartlab[ai] 설치가 필요합니다: uv add \"dartlab[ai]\"\n")
        return

    auth_url, verifier, state = build_auth_url()
    result: dict = {"done": False, "error": None}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path != "/auth/callback":
                self.send_response(404)
                self.end_headers()
                return

            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            cb_state = params.get("state", [None])[0]
            error = params.get("error", [None])[0]

            if error:
                result["error"] = error
                result["done"] = True
                self._respond("인증 실패", f"오류: {error}")
                return
            if cb_state != state:
                result["error"] = "state_mismatch"
                result["done"] = True
                self._respond("인증 실패", "보안 검증 실패")
                return
            if not code:
                result["error"] = "no_code"
                result["done"] = True
                self._respond("인증 실패", "인증 코드 없음")
                return

            try:
                exchange_code(code, verifier)
                result["done"] = True
                self._respond("인증 성공", "DartLab 인증이 완료되었습니다. 이 창을 닫아주세요.")
            except (ConnectionError, OSError, RuntimeError, ValueError) as exc:
                result["error"] = str(exc)
                result["done"] = True
                self._respond("인증 실패", f"토큰 교환 실패: {exc}")

        def _respond(self, title: str, message: str):
            markup = (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title>"
                "<style>body{font-family:system-ui;display:flex;align-items:center;"
                "justify-content:center;min-height:100vh;margin:0;background:#050811;color:#e5e5e5}"
                "div{text-align:center;padding:2rem}h1{font-size:1.5rem;margin-bottom:1rem}"
                "</style></head><body>"
                f"<div><h1>{title}</h1><p>{message}</p></div>"
                "<script>setTimeout(()=>window.close(),3000)</script>"
                "</body></html>"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(markup.encode("utf-8"))

        def log_message(self, fmt, *args):
            pass

    server = HTTPServer(("127.0.0.1", OAUTH_REDIRECT_PORT), CallbackHandler)
    server.timeout = 120

    def serve():
        server.handle_request()
        server.server_close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()

    print("  브라우저에서 ChatGPT 로그인 페이지를 엽니다...")
    print("  (120초 안에 로그인을 완료하세요)\n")
    webbrowser.open(auth_url)

    # 완료 대기
    for _ in range(120):
        if result["done"]:
            break
        time.sleep(1)
        sys.stdout.write(".")
        sys.stdout.flush()
    print()

    if result.get("error"):
        print(f"\n  ✗ 인증 실패: {result['error']}\n")
    elif result["done"]:
        print("\n  ✓ ChatGPT OAuth 인증 완료!\n")
        print("  확인:")
        print("     dartlab status -p oauth-codex\n")
        print("  사용:")
        print('     dartlab ask 005930 "재무 건전성 분석"\n')
    else:
        print("\n  ✗ 시간 초과 — 120초 안에 로그인하지 못했습니다.\n")
        print("  다시 시도: dartlab setup oauth-codex\n")


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


def _setup_openai() -> None:
    print("\n[ OpenAI API 설정 — GPT-4o 등 ]\n")

    print("  1. API 키 발급")
    print("     https://platform.openai.com/api-keys\n")

    print("  2. 환경변수 설정")
    print("     export OPENAI_API_KEY=sk-...\n")
    print("     PowerShell:")
    print("     $env:OPENAI_API_KEY = 'sk-...'\n")

    print("  3. 확인")
    print("     dartlab status -p openai\n")

    print("  4. 사용")
    print('     dartlab ask 005930 "재무 건전성 분석" -p openai')
    print('     dartlab ask 005930 "분석" -p openai -m gpt-4o')
    print()


def _setup_custom() -> None:
    print("\n[ Custom OpenAI-Compatible API 설정 ]\n")
    print("  vLLM, Together, Groq 등 OpenAI 호환 API를 사용합니다.\n")

    print("  사용 예시:")
    print('     dartlab ask 005930 "분석" -p custom \\')
    print("       --base-url http://localhost:8000/v1 \\")
    print("       --api-key YOUR_KEY \\")
    print("       -m my-model\n")

    print("  환경변수로 기본값 설정:")
    print("     export CUSTOM_BASE_URL=http://localhost:8000/v1")
    print("     export CUSTOM_API_KEY=YOUR_KEY")
    print()
