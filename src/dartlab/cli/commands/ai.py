"""`dartlab ai` command — AI 분석 웹 인터페이스."""

from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.output import print_warning

# web.py 와 동일한 로직으로 UI 디렉토리 결정
_UI_DIR = (
    Path(os.environ["DARTLAB_UI_DIR"])
    if os.environ.get("DARTLAB_UI_DIR")
    else Path(__file__).resolve().parents[4] / "ui"
)


def configure_parser(subparsers) -> None:
    """ai 서브커맨드 등록 — FastAPI + SPA 웹 인터페이스."""
    parser = subparsers.add_parser("ai", help="AI 분석 웹 인터페이스 실행")
    parser.add_argument("--port", type=int, default=8400, help="포트 번호 (기본: 8400)")
    parser.add_argument("--host", default="127.0.0.1", help="호스트 (기본: 127.0.0.1)")
    parser.add_argument("--dev", action="store_true", help="개발 모드 (Svelte dev 서버 동시 실행)")
    parser.add_argument("--no-browser", action="store_true", help="브라우저 자동 열기 비활성화")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """FastAPI 서버 + SPA를 시작하고 브라우저를 연다."""
    port = args.port
    host = args.host
    url = f"http://localhost:{port}"

    if args.dev:
        _runDevMode(url)
    else:
        if not _checkBuiltUi():
            return 0
        print("\n  DartLab AI")
        print(f"  {url}")
        print()

    from dartlab.server import ensure_port, run_server

    shouldOpen = not args.no_browser and not os.environ.get("DARTLAB_NO_BROWSER")
    target = "http://localhost:5400" if args.dev else url

    status = ensure_port(port)
    if status == "already_running":
        if shouldOpen:
            webbrowser.open(target)
        return 0
    if status == "failed":
        return 1

    if shouldOpen:
        import threading
        import time

        def _open() -> None:
            time.sleep(1.5)
            webbrowser.open(target)

        threading.Thread(target=_open, daemon=True).start()

    run_server(host=host, port=port)
    return 0


def _runDevMode(url: str) -> None:
    import threading

    if not (_UI_DIR / "node_modules").exists():
        print("npm install 실행 중...")
        result = subprocess.run(["npm", "install"], cwd=str(_UI_DIR), timeout=300)  # noqa: S603, S607
        if result.returncode != 0:
            raise CLIError("UI 의존성 설치에 실패했습니다.")

    def _vite() -> None:
        result = subprocess.run(["npm", "run", "dev"], cwd=str(_UI_DIR))  # noqa: S603, S607
        if result.returncode != 0:
            print_warning("Svelte dev 서버가 비정상 종료되었습니다.")

    print("\n  DartLab AI (개발 모드)")
    print(f"  API:     {url}")
    print("  Svelte:  http://localhost:5400")
    print()

    threading.Thread(target=_vite, daemon=True).start()


def _checkBuiltUi() -> bool:
    buildDir = _UI_DIR / "build"
    if buildDir.exists():
        return True

    print("\n  UI가 빌드되지 않았습니다.")
    print("  개발 모드로 실행하세요:\n")
    print("    dartlab ai --dev\n")
    print("  또는 빌드 후 실행:")
    print("    cd ui && npm install && npm run build")
    print("    dartlab ai\n")
    return False
