"""`dartlab ai` command — AI 분석 웹 인터페이스."""

from __future__ import annotations

import json
import os
import subprocess
import webbrowser
from pathlib import Path

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.output import printWarning
from dartlab.server._ui_path import resolveUiBuildDir, resolveUiSourceDir


def configureParser(subparsers) -> None:
    """ai 서브커맨드 등록 — FastAPI + SPA 웹 인터페이스."""
    parser = subparsers.add_parser("ai", help="AI 분석 웹 인터페이스 실행")
    parser.add_argument("--port", type=int, default=8400, help="포트 번호 (기본: 8400)")
    parser.add_argument("--host", default="127.0.0.1", help="호스트 (기본: 127.0.0.1)")
    parser.add_argument("--dev", action="store_true", help="개발 모드 (Svelte dev 서버 동시 실행)")
    parser.add_argument("--no-browser", action="store_true", help="브라우저 자동 열기 비활성화")
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="포트를 점유 중인 dartlab 이 있으면 종료하지 않고 그대로 사용 (기본: 종료 후 재시작)",
    )
    parser.set_defaults(handler=run)


def _devUiPort() -> int:
    """dev 모드에서 띄우는 UI dev 서버 포트 — SvelteKit(ui/apps/local) 5174.
    (옛 React ui/web 5400 escape 는 debt-honesty P2-2 에서 ui/web 회수와 함께 제거.)"""
    return 5174


def _npmCommand(*, platform: str | None = None) -> str:
    """Windows의 npm.cmd와 POSIX의 npm을 shell 없이 선택한다."""
    return "npm.cmd" if (platform or os.name) == "nt" else "npm"


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

    from dartlab.server import ensurePort, runServer

    shouldOpen = not args.no_browser and not os.environ.get("DARTLAB_NO_BROWSER")
    # dev 모드는 UI dev 서버(_runDevMode 가 띄움)를 열고, 그 외엔 API(SPA 서빙) url 을 연다.
    target = f"http://localhost:{_devUiPort()}" if args.dev else url

    status = ensurePort(port, keepExisting=args.keep_existing)
    if status == "already_running":
        print()
        print(f"  이미 실행 중인 서버를 사용합니다 → {target}")
        if shouldOpen:
            print("  브라우저를 엽니다...")
            webbrowser.open(target)
        else:
            print("  브라우저에서 위 주소를 여세요.")
        print()
        return 0
    if status == "failed":
        return 1

    if shouldOpen:
        import threading
        import time
        import urllib.error
        import urllib.request

        probe = f"http://127.0.0.1:{port}/api/status?probe=0"

        def _waitAndOpen() -> None:
            for _ in range(40):
                time.sleep(0.5)
                try:
                    resp = urllib.request.urlopen(probe, timeout=1)
                    if resp.status == 200:
                        opened = webbrowser.open(target)
                        if not opened:
                            print(f"\n  브라우저 자동 열기 실패 — 직접 여세요: {target}\n", flush=True)
                        return
                except (OSError, urllib.error.URLError):
                    continue
            print(f"\n  서버 준비 확인 실패 — 직접 여세요: {target}\n", flush=True)

        threading.Thread(target=_waitAndOpen, daemon=True).start()
        print(f"  서버 준비 후 브라우저를 엽니다. 안 열리면 직접: {target}")
        print("  종료: Ctrl+C")
        print()

    runServer(host=host, port=port)
    return 0


def _runDevMode(url: str) -> None:
    import threading

    ui_src = resolveUiSourceDir()
    workspaceRoot = _npmWorkspaceRoot(ui_src)
    viteBin = workspaceRoot / "node_modules" / ".bin" / ("vite.cmd" if os.name == "nt" else "vite")
    if not viteBin.is_file():
        print("npm install 실행 중...")
        result = subprocess.run(  # noqa: S603, S607
            [_npmCommand(), "install"], cwd=str(workspaceRoot), timeout=300
        )
        if result.returncode != 0:
            raise CLIError("UI 의존성 설치에 실패했습니다.")

    def _vite() -> None:
        command = [_npmCommand(), "run", "dev"]
        if workspaceRoot != ui_src:
            command.extend(["--workspace", "@dartlab/ui-local"])
        result = subprocess.run(command, cwd=str(workspaceRoot))  # noqa: S603, S607
        if result.returncode != 0:
            printWarning("Svelte dev 서버가 비정상 종료되었습니다.")

    ui_label = "Svelte"
    print("\n  DartLab AI (개발 모드)")
    print(f"  API:     {url}")
    print(f"  {ui_label}:  http://localhost:{_devUiPort()}")
    print()

    threading.Thread(target=_vite, daemon=True).start()


def _npmWorkspaceRoot(uiSource: Path) -> Path:
    """Svelte 앱에서 가장 가까운 npm workspaces 루트를 찾는다."""
    for candidate in (uiSource, *uiSource.parents):
        packagePath = candidate / "package.json"
        try:
            package = json.loads(packagePath.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if isinstance(package, dict) and package.get("workspaces"):
            return candidate
    return uiSource


def _checkBuiltUi() -> bool:
    build_dir = resolveUiBuildDir()
    if build_dir.is_dir() and (build_dir / "index.html").exists():
        return True

    print("\n  UI를 사용할 수 없습니다.")
    print("  dartlab을 최신 버전으로 업그레이드하세요:\n")
    print("    pip install --upgrade dartlab\n")
    print("  또는 CLI에서 바로 사용하세요:")
    print("    dartlab ask '삼성전자 분석해줘'\n")
    return False
