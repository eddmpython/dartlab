"""DartLab MCP 연결 상태와 명시적 설정 계획."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass

from .discovery import discoverExecutable
from .registry import loadRuntimeRegistry

_MCP_PROBE_TTL_SECONDS = 15.0
_MCP_CACHE: dict[str, tuple[float, dict[str, object]]] = {}
_MCP_CACHE_LOCK = threading.Lock()


@dataclass(frozen=True)
class McpConnectPlan:
    """사용자 승인 전에는 실행되지 않는 MCP 설정 계획."""

    runtimeId: str
    argv: tuple[str, ...]
    digest: str

    def toDict(self) -> dict[str, object]:
        """Sig: toDict() -> dict[str, object].

        Args: 없음.
        Returns: UI와 CLI에 표시할 연결 계획이다.
        Example: `plan.toDict()["argv"]`.
        """
        return asdict(self)


def embeddedMcpServerSpec() -> dict[str, object]:
    """Sig: embeddedMcpServerSpec() -> dict[str, object].

    Args: 없음.
    Returns: ACP session/new에 넣을 stdio MCP 명세다.
    Example: `servers = [embeddedMcpServerSpec()]`.
    """
    return {
        "name": "dartlab",
        "command": sys.executable,
        "args": ["-X", "utf8", "-m", "dartlab.mcp"],
        "env": [{"name": "PYTHONUNBUFFERED", "value": "1"}],
    }


def claudeReadOnlyMcpTools() -> tuple[str, ...]:
    """Sig: claudeReadOnlyMcpTools() -> tuple[str, ...].

    Args: 없음.
    Returns: 레지스트리가 read-only로 보증한 Claude MCP tool 이름이다.
    Example: `allowed = claudeReadOnlyMcpTools()`.
    """
    from dartlab.ai.tools.registry import isToolReadOnly, listToolNames

    return tuple(f"mcp__dartlab__{name}" for name in listToolNames() if isToolReadOnly(name))


def buildMcpConnectPlan(runtimeId: str) -> McpConnectPlan:
    """Sig: buildMcpConnectPlan(runtimeId) -> McpConnectPlan.

    Args: runtimeId는 연결할 설치형 에이전트다.
    Returns: 공식 CLI를 사용하는 digest 고정 계획이다.
    Raises: KeyError or ValueError if runtime is unknown or embedded-only.
    Example: `plan = buildMcpConnectPlan("codex")`.
    """
    descriptor = loadRuntimeRegistry()[runtimeId]
    executable = discoverExecutable(descriptor)
    if executable is None:
        raise FileNotFoundError(runtimeId)
    serverArgs = (sys.executable, "-X", "utf8", "-m", "dartlab.mcp")
    if runtimeId == "codex":
        argv = (executable, "mcp", "add", "dartlab", "--", *serverArgs)
    elif runtimeId == "claude":
        argv = (executable, "mcp", "add", "--scope", "user", "dartlab", "--", *serverArgs)
    else:
        raise ValueError(f"{runtimeId}는 ACP 세션에 MCP를 내장하므로 전역 설정이 필요하지 않습니다")
    canonical = json.dumps({"runtimeId": runtimeId, "argv": argv}, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return McpConnectPlan(runtimeId, argv, digest)


def executeMcpConnectPlan(plan: McpConnectPlan, *, approvedDigest: str) -> subprocess.CompletedProcess[str]:
    """Sig: executeMcpConnectPlan(plan, *, approvedDigest) -> CompletedProcess[str].

    Args: 계획과 사용자가 확인한 digest다.
    Returns: 공식 CLI 설정 명령 결과다.
    Raises: PermissionError if plan changed; CalledProcessError on CLI failure.
    Example: `executeMcpConnectPlan(plan, approvedDigest=plan.digest)`.
    """
    current = buildMcpConnectPlan(plan.runtimeId)
    if approvedDigest != plan.digest or current != plan:
        raise PermissionError("MCP 연결 계획 digest가 현재 계획과 다릅니다")
    completed = subprocess.run(
        list(plan.argv),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        shell=False,
        check=True,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    with _MCP_CACHE_LOCK:
        _MCP_CACHE.pop(plan.runtimeId, None)
    return completed


def probeMcpConnection(runtimeId: str, *, refresh: bool = False) -> dict[str, object]:
    """Sig: probeMcpConnection(runtimeId, *, refresh=False) -> dict[str, object].

    Args: runtimeId는 확인할 런타임이고 refresh는 15초 캐시 무시 여부다.
    Returns: connected, mode, detail을 가진 상태다.
    Example: `probeMcpConnection("cline")`.
    """
    if runtimeId == "cline":
        return {"connected": True, "mode": "embedded-acp", "detail": None}
    if not refresh:
        with _MCP_CACHE_LOCK:
            cached = _MCP_CACHE.get(runtimeId)
            if cached and time.monotonic() - cached[0] <= _MCP_PROBE_TTL_SECONDS:
                return dict(cached[1])
    descriptor = loadRuntimeRegistry()[runtimeId]
    executable = discoverExecutable(descriptor)
    if executable is None:
        result: dict[str, object] = {
            "connected": False,
            "mode": "global-cli",
            "detail": "runtime_missing",
        }
        with _MCP_CACHE_LOCK:
            _MCP_CACHE[runtimeId] = (time.monotonic(), result)
        return dict(result)
    completed = subprocess.run(
        [executable, "mcp", "get", "dartlab"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        shell=False,
        check=False,
    )
    detail = (completed.stdout or completed.stderr).strip()
    result = {
        "connected": completed.returncode == 0,
        "mode": "global-cli",
        "detail": detail[:1000] or None,
    }
    with _MCP_CACHE_LOCK:
        _MCP_CACHE[runtimeId] = (time.monotonic(), result)
    return dict(result)
