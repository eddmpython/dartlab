"""MCP 출시 자동 smoke의 마스터 플랜 v2 트랙 7 PR-M5 검증.

stdio + Streamable HTTP 양쪽 통합 dispatch 검증. CI Fast 등록 (mcpDogfood marker) →
배포 직전 release 가드. 외부 client (Cursor/Cline) 가 본 surface 호출 시 회귀 0 보장.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.mcpDogfood]


def _spawnStdioServer() -> subprocess.Popen:
    """namespace collision을 피하도록 임시 경로에서 stdio 서버를 실행한다."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"
    return subprocess.Popen(
        [sys.executable, "-X", "utf8", "-m", "dartlab.mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        bufsize=0,
        cwd=tempfile.gettempdir(),
    )


def _sendJsonRpc(proc: subprocess.Popen, payload: dict) -> None:
    """JSON-RPC 라인 1 줄 송신 (MCP stdio 표준)."""
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    proc.stdin.write(line.encode("utf-8"))
    proc.stdin.flush()


def _readJsonRpc(proc: subprocess.Popen, timeoutSec: float = 5.0) -> dict | None:
    """제한 시간 안에 stdout의 한 줄 JSON-RPC 응답을 읽는다."""
    deadline = time.monotonic() + timeoutSec
    buf = b""
    while time.monotonic() < deadline:
        chunk = proc.stdout.read(1)
        if not chunk:
            time.sleep(0.05)
            continue
        buf += chunk
        if chunk == b"\n":
            try:
                return json.loads(buf.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                buf = b""
    return None


def test_release_smoke_stdio_initialize_and_listTools() -> None:
    """stdio 서버 initialize 왕복과 tools/list canonical 도구 광고를 검증한다."""
    proc = _spawnStdioServer()
    try:
        # initialize
        _sendJsonRpc(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "release-smoke", "version": "1.0"},
                },
            },
        )
        init_resp = _readJsonRpc(proc, timeoutSec=10.0)
        assert init_resp is not None, "initialize 응답 없음 (stdio 서버 부팅 실패)"
        assert init_resp.get("id") == 1
        assert "result" in init_resp

        # initialized notification (no response)
        _sendJsonRpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        # tools/list
        _sendJsonRpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools_resp = _readJsonRpc(proc, timeoutSec=10.0)
        assert tools_resp is not None
        tools = tools_resp.get("result", {}).get("tools") or []
        names = {t.get("name") for t in tools}
        # CANONICAL_V2 21종을 따르며 답변 루프를 재귀 호출하는 ask는 제외한다.
        assert len(names) >= 20, f"advertise tool 갯수 회귀: {len(names)} (기대 ≥ 20)"
        # 핵심 도구 sample
        assert "ask" not in names
        assert "EngineCall" in names
        assert "DCFValuation" in names
        assert "ReadSkill" in names
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def test_release_smoke_streamable_http_app_factory() -> None:
    """Streamable HTTP transport app 생성 가능 + Starlette routes 정상."""
    pytest.importorskip("mcp.server.streamable_http_manager")
    from dartlab.mcp import createStreamableHttpApp

    app = createStreamableHttpApp()
    assert app is not None
    assert hasattr(app, "routes")


def test_release_smoke_advertise_count_meets_target() -> None:
    """advertisedTools의 갯수가 PR-M1 목표인 20종 이상인지 검증한다."""
    from dartlab.mcp.protocol import advertisedTools, mcpAdvertisedToolNames

    names = mcpAdvertisedToolNames()
    assert len(names) >= 20, f"PR-M1 advertise SSOT 회귀: {len(names)}"
    tools = advertisedTools()
    assert len(tools) == len(names)


def test_release_smoke_finance_primitives_dispatch() -> None:
    """finance primitive 8 종 모두 registry dispatch 가능 (executeAskWorkbenchTool 등록 확인)."""
    from dartlab.ai.tools.registry import _SPECS, CANONICAL_V2

    finance_primitives = (
        "DCFValuation",
        "PeerCompareN",
        "CompileFinancialDashboard",
        "RegressionForecast",
        "SensitivityAnalysis",
        "CreditScorecard",
        "ScenarioCompareN",
        "ScenarioOverlay",
    )
    for name in finance_primitives:
        assert name in CANONICAL_V2, f"{name} CANONICAL_V2 누락"
        assert name in _SPECS, f"{name} registry _SPECS 누락"


def test_release_smoke_canonical_v2_no_workbench_internal() -> None:
    """CANONICAL_V2 에 workbench-internal 노출 회귀 0 (PR-M1 가드)."""
    from dartlab.ai.tools.registry import CANONICAL_V2

    workbench_internal = {"RunWorkbench", "EvidenceGate", "PickStoryTemplate"}
    leaked = set(CANONICAL_V2) & workbench_internal
    assert not leaked, f"workbench-internal 회귀 누출: {leaked}"
