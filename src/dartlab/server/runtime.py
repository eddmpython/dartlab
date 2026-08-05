"""Server runtime helpers.

Process/port management lives here so ``dartlab.server`` can focus on the
FastAPI app surface.
"""

from __future__ import annotations

import os


def defaultHost() -> str:
    """환경변수 또는 기본값에서 바인딩 호스트를 반환한다."""
    return os.environ.get("DARTLAB_HOST", "127.0.0.1")


def _isDartlabAlive(port: int) -> bool:
    """DartLab 서버가 살아있는지 health check."""
    import urllib.request

    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status?probe=0", timeout=2)
        return resp.status == 200
    except (OSError, urllib.error.URLError):
        return False


def _killPort(port: int) -> bool:
    """포트를 점유 중인 좀비 프로세스를 종료한다. 성공 시 True."""
    import platform
    import subprocess
    import time

    system = platform.system()
    pids: set[int] = set()

    if system == "Windows":
        # netstat 출력은 OEM 코드페이지 (한국어 Windows = cp949). text=True 의 기본
        # UTF-8 디코드 시 UnicodeDecodeError → result.stdout=None → 좀비 정리 전면
        # 실패. bytes 로 받고 errors='ignore' 로 안전 디코드 (PID 라인은 ASCII).
        result = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True,
            timeout=10,
        )
        stdout_text = (result.stdout or b"").decode("ascii", errors="ignore")
        for line in stdout_text.splitlines():
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


def ensurePort(port: int, *, keepExisting: bool = False) -> str:
    """포트 확보. "ok" | "already_running" | "failed" 반환.

    기본 동작 — 포트가 점유돼 있으면 종료 후 재사용한다 (살아있는 dartlab 이든
    좀비든). 매번 명확히 어떤 PID 를 죽이는지 로그로 남긴다 — silent kill 회귀를
    *피하지 않고 가시화* 하는 방향. ``keepExisting=True`` 일 때만 살아있는
    dartlab 을 그대로 두고 ``already_running`` 을 돌려준다.
    """
    import socket

    from dartlab.core.logger import getLogger

    _log = getLogger(__name__)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
        return "ok"
    except OSError:
        pass

    alive = _isDartlabAlive(port)
    if alive and keepExisting:
        _log.info("기존 dartlab 서버가 포트 %d 에서 실행 중입니다 — 그대로 사용합니다.", port)
        return "already_running"

    if alive:
        _log.info("기존 dartlab 서버 종료 후 재시작 (포트 %d)...", port)
    else:
        _log.info("포트 %d 점유 중 — 기존 프로세스 종료 후 재시작...", port)
    if _killPort(port):
        _log.info("종료 완료. 재시작합니다.")
        return "ok"

    _log.error("포트 %d 을 해제할 수 없습니다.", port)
    _log.error("다른 포트를 사용하세요: dartlab ai --port %d", port + 1)
    return "failed"


def runServer(host: str | None = None, port: int = 8400):
    """서버 실행 (blocking)."""
    import uvicorn

    resolved_host = host or defaultHost()
    os.environ["DARTLAB_HOST"] = resolved_host
    # 제품 서버로 뜬 실행이라는 표식. lifespan 이 이걸 보고 Runtime Center 실측을 미리 시작한다.
    os.environ["DARTLAB_SERVER_ENTRY"] = "1"
    uvicorn.run("dartlab.server:app", host=resolved_host, port=port, log_level="info")
