"""MCP stdio cold-start smoke test — initialize 왕복 + duplicate logger 가드 회귀."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time

import pytest

pytestmark = pytest.mark.unit

_BOOT_MARKERS = ("MCP 서버 초기화 완료", "DartLab MCP 서버 시작 (stdio)")

# 표식이 다 나올 때까지 기다리는 한도. 여유롭게 두어도 표식이 나오는 즉시 빠져나온다.
_BOOT_TIMEOUT_SEC = 30.0
# 표식을 본 뒤 중복이 뒤늦게 오는지 더 지켜보는 시간. 이 테스트의 목적이 중복 검출이다.
_SETTLE_SEC = 1.0


def _collectStderr(proc: subprocess.Popen) -> str:
    """부팅 표식이 다 나올 때까지 stderr 를 모아 돌려준다.

    예전에는 4 초를 무턱대고 자고 한 번 읽었다. 병렬 워커 여덟이 CPU 를 물고 있으면 그
    안에 flush 가 안 끝나 stderr 가 빈 채로 읽히고, 개수 0 으로 헛되이 붉어졌다. 부하에
    따라 붙었다 떨어졌다 하는 테스트는 신호가 아니라 잡음이다. 표식이 나오면 곧바로,
    안 나오면 한도까지 기다린다.
    """
    chunks: list[bytes] = []

    def _drain() -> None:
        if proc.stderr is None:
            return
        for line in iter(proc.stderr.readline, b""):
            chunks.append(line)

    threading.Thread(target=_drain, daemon=True).start()

    def _text() -> str:
        return b"".join(chunks).decode("utf-8", errors="replace")

    deadline = time.monotonic() + _BOOT_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if all(marker in _text() for marker in _BOOT_MARKERS):
            time.sleep(_SETTLE_SEC)  # 중복이 뒤늦게 오는지 더 본다
            break
        time.sleep(0.1)
    return _text()


def _spawn_mcp_stdio() -> subprocess.Popen:
    """`python -X utf8 -m dartlab.mcp` 를 stdio 서버로 spawn."""
    import tempfile

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"
    # cwd 를 tests/ 또는 tests/mcp/ 가 아닌 곳으로 명시 — subprocess sys.path[0]
    # 이 'tests/' 가 되면 'tests/mcp/__init__.py' 가 'import mcp' 로 잡혀
    # standalone mcp SDK 와 namespace collision (CI 회귀 원인, 2026-05-17).
    return subprocess.Popen(
        [sys.executable, "-X", "utf8", "-m", "dartlab.mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        bufsize=0,
        cwd=tempfile.gettempdir(),
    )


def test_mcp_stdio_starts_and_logs_each_message_once():
    """서버 부팅 stderr 가드 — '초기화' / '시작' 메시지가 정확히 1 회씩 출력.

    duplicate logger handler 회귀를 잡는다 (이슈 #28 의 ② 가설).
    """
    proc = _spawn_mcp_stdio()
    try:
        stderr_text = _collectStderr(proc)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)

    # 메시지 갯수 검증. 각 정확히 1 회.
    init_count = stderr_text.count(_BOOT_MARKERS[0])
    start_count = stderr_text.count(_BOOT_MARKERS[1])
    assert init_count == 1, f"기대 1, 실제 {init_count} — duplicate logger handler 회귀? stderr={stderr_text!r}"
    assert start_count == 1, f"기대 1, 실제 {start_count} — duplicate logger handler 회귀? stderr={stderr_text!r}"


def test_mcp_create_server_cold_path_under_threshold():
    """create_server() 가 timeout 임계 안에 끝나는지 — Claude Desktop attach 가드.

    측정 대상: import dartlab.mcp + create_server() 합계.
    임계: 5 초 (Claude Desktop ~23 초 timeout 대비 충분히 여유).
    회귀 시 PEP 562 lazy 이탈 또는 module-top eager import 추가 가능성.
    """
    code = (
        "import time, sys\n"
        "t0 = time.perf_counter()\n"
        "from dartlab.mcp import createServer\n"
        "createServer()\n"
        "t1 = time.perf_counter()\n"
        "sys.stdout.write(f'{(t1-t0)*1000:.0f}\\n')\n"
    )
    import tempfile

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", code],
        capture_output=True,
        text=True,
        # text=True 만 두면 로케일 인코딩으로 디코드한다. 한국어 Windows 는 cp949 라,
        # UTF-8 로 쓰는 자식의 한글 로그에서 UnicodeDecodeError 가 나고 읽기 스레드가
        # 죽어 출력이 통째로 비었다. 자식이 무엇으로 쓰는지 여기서 명시한다.
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
        cwd=tempfile.gettempdir(),  # tests/ namespace collision 차단
    )
    assert result.returncode == 0, f"create_server() 부팅 실패: {result.stderr}"
    elapsed_ms = float(result.stdout.strip().splitlines()[-1])
    assert elapsed_ms < 5000, (
        f"create_server() cold path {elapsed_ms:.0f} ms — 5000 ms 임계 초과. "
        "PEP 562 lazy 이탈 또는 module-top eager import 회귀 가능성."
    )
