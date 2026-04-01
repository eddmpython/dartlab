"""`dartlab ai` command — AI 분석 웹 인터페이스."""

from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.output import print_warning


def configure_parser(subparsers) -> None:
    """ai 서브커맨드 등록 — FastAPI + SPA 웹 인터페이스."""
    parser = subparsers.add_parser("ai", help="AI 분석 웹 인터페이스 실행")
    _add_shared_arguments(parser)
    parser.set_defaults(handler=run)


def _add_shared_arguments(parser) -> None:
    parser.add_argument("--port", type=int, default=8400, help="포트 번호 (기본: 8400)")
    parser.add_argument("--host", default="127.0.0.1", help="호스트 (기본: 127.0.0.1)")
    parser.add_argument("--dev", action="store_true", help="개발 모드 (Svelte dev 서버 동시 실행)")
    parser.add_argument("--no-browser", action="store_true", help="브라우저 자동 열기 비활성화")


def run(args) -> int:
    """FastAPI 서버 + SPA를 시작하고 브라우저를 연다."""
    port = args.port
    host = args.host
    url = f"http://localhost:{port}"

    if args.dev:
        _run_dev_mode(url)
    else:
        if not _check_built_ui():
            return 0
        print("\n  DartLab AI")
        print(f"  {url}")
        print()

    from dartlab.server import ensure_port, run_server

    should_open = not args.no_browser and not os.environ.get("DARTLAB_NO_BROWSER")
    target = "http://localhost:5400" if args.dev else url

    status = ensure_port(port)
    if status == "already_running":
        if should_open:
            webbrowser.open(target)
        return 0
    if status == "failed":
        return 1

    if should_open:
        import threading
        import time

        def open_browser() -> None:
            time.sleep(1.5)
            webbrowser.open(target)

        threading.Thread(target=open_browser, daemon=True).start()

    run_server(host=host, port=port)
    return 0


def _run_dev_mode(url: str) -> None:
    import threading

    ui_dir = Path(__file__).resolve().parents[2] / "ui"
    if not (ui_dir / "node_modules").exists():
        print("npm install 실행 중...")
        result = subprocess.run(["npm", "install"], cwd=str(ui_dir), timeout=300)  # noqa: S603, S607 — hardcoded constant args
        if result.returncode != 0:
            raise CLIError("UI 의존성 설치에 실패했습니다.")

    def run_vite() -> None:
        result = subprocess.run(["npm", "run", "dev"], cwd=str(ui_dir))  # noqa: S603, S607 — hardcoded constant args
        if result.returncode != 0:
            print_warning("Svelte dev 서버가 비정상 종료되었습니다.")

    print("\n  DartLab AI (개발 모드)")
    print(f"  API:     {url}")
    print("  Svelte:  http://localhost:5400")
    print()

    threading.Thread(target=run_vite, daemon=True).start()


def _check_built_ui() -> bool:
    ui_dir = Path(__file__).resolve().parents[2] / "ui" / "build"
    if ui_dir.exists():
        return True

    print("\n  UI가 빌드되지 않았습니다.")
    print("  개발 모드로 실행하세요:\n")
    print("    dartlab ai --dev\n")
    print("  또는 빌드 후 실행:")
    print("    cd ui && npm install && npm run build")
    print("    dartlab ai\n")
    return False
