"""Server runtime helpers.

Process/port management lives here so ``dartlab.server`` can focus on the
FastAPI app surface.
"""

from __future__ import annotations

import os


def default_host() -> str:
    """환경변수 또는 기본값에서 바인딩 호스트를 반환한다."""
    return os.environ.get("DARTLAB_HOST", "127.0.0.1")


def _is_dartlab_alive(port: int) -> bool:
    """DartLab 서버가 살아있는지 health check."""
    import urllib.request

    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status?probe=0", timeout=2)
        return resp.status == 200
    except (OSError, urllib.error.URLError):
        return False


def _kill_port(port: int) -> bool:
    """포트를 점유 중인 좀비 프로세스를 종료한다. 성공 시 True."""
    import platform
    import subprocess
    import time

    system = platform.system()
    pids: set[int] = set()

    if system == "Windows":
        result = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5 and f":{port}" in parts[1] and parts[3] == "LISTENING":
                pid = int(parts[4])
                if pid > 0:
                    pids.add(pid)
    else:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.strip().splitlines():
            if line.strip().isdigit():
                pids.add(int(line.strip()))

    if not pids:
        return False

    import logging as _logging

    _log = _logging.getLogger(__name__)
    my_pid = os.getpid()
    for pid in pids:
        if pid == my_pid:
            continue
        _log.info("Killing PID %d on port %d", pid, port)
        if system == "Windows":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10)
        else:
            import signal

            os.kill(pid, signal.SIGTERM)

    time.sleep(0.5)
    return True


def ensure_port(port: int) -> str:
    """포트 확보. "ok" | "already_running" | "failed" 반환."""
    import socket
    import sys

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
        return "ok"
    except OSError:
        pass

    if _is_dartlab_alive(port):
        print(f"\n  기존 서버 종료 중 (포트 {port})...")
    else:
        print(f"\n  포트 {port} 사용 중 (좀비) — 기존 프로세스 종료 중...")
    if _kill_port(port):
        print("  종료 완료. 재시작합니다.\n")
        return "ok"

    print(f"\n  오류: 포트 {port}을 해제할 수 없습니다.", file=sys.stderr)
    print(f"  다른 포트를 사용하세요: dartlab ai --port {port + 1}\n", file=sys.stderr)
    return "failed"


def run_server(host: str | None = None, port: int = 8400):
    """서버 실행 (blocking)."""
    import uvicorn

    resolved_host = host or default_host()
    os.environ["DARTLAB_HOST"] = resolved_host
    uvicorn.run("dartlab.server:app", host=resolved_host, port=port, log_level="info")
