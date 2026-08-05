"""DartLab MCP 연결 상태와 명시적 설정 계획."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from .discovery import discoverExecutable
from .drivers.base import runtimeExecutableArgv
from .probeCache import SwrCache, backgroundRefresher, mcpProbeKey, retryUntilDetermined
from .registry import loadRuntimeRegistry

_MCP_PROBE_TTL_SECONDS = 15.0
# 형제 probe 와 같은 stale-while-revalidate 계약. TTL 은 신선도 표시일 뿐이고 만료돼도
# 마지막 실측값을 버리지 않는다. `claude mcp get` 이 7~8초라 만료 즉시 폐기하면 화면이
# 재방문마다 전량 재측정을 기다린다(실측 2026-08-05).
_MCP_CACHE = SwrCache(_MCP_PROBE_TTL_SECONDS)
_MCP_CACHE_LOCK = _MCP_CACHE.lock


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
        "args": ["-X", "utf8", "-m", "dartlab.mcp", "--profile", "agent"],
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
    if not descriptor.embeddedGrounding:
        raise ValueError(f"{runtimeId}의 현재 프로토콜은 DartLab MCP 도구를 런타임 세션에 노출하지 않습니다")
    executable = discoverExecutable(descriptor)
    if executable is None:
        raise FileNotFoundError(runtimeId)
    serverArgs = (sys.executable, "-X", "utf8", "-m", "dartlab.mcp", "--profile", "agent")
    launch = runtimeExecutableArgv(descriptor, executable)
    if runtimeId == "codex":
        argv = (*launch, "mcp", "add", "dartlab", "--", *serverArgs)
    elif runtimeId == "claude":
        argv = (*launch, "mcp", "add", "--scope", "user", "dartlab", "--", *serverArgs)
    else:
        raise ValueError(f"{runtimeId}의 MCP 연결 방식을 지원하지 않습니다")
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
    _MCP_CACHE.clear(plan.runtimeId)
    return completed


def _measureMcpConnection(runtimeId: str) -> dict[str, object]:
    """공식 CLI 설정을 실제로 읽어 DartLab MCP 연결 여부를 측정한다."""
    descriptor = loadRuntimeRegistry()[runtimeId]
    executable = discoverExecutable(descriptor)
    if executable is None:
        return {"connected": False, "mode": "global-cli", "detail": "runtime_missing"}
    if runtimeId == "cline":
        connected = _clineMcpConfigured()
        return {
            "connected": connected,
            "mode": "global-cli",
            "detail": "official_settings" if connected else "not_configured",
        }
    # probe 실패가 상태 화면을 죽이지 않는다. 형제 probe(discovery.probeRuntime·
    # probeAuth)는 전부 이 계약인데 여기만 맨몸이라, `claude mcp get` 이 10 초를 넘기면
    # TimeoutExpired 가 /api/status 까지 올라가 Runtime Center 전체가 500 이 됐다
    # (실측 2026-08-04). CLI 콜드스타트가 느린 환경에서 재현된다. 상한도 형제 중
    # 최댓값(8초)보다 넉넉한 20 초로 두되, 넘으면 미상 상태로 degrade 한다.
    try:
        completed = subprocess.run(
            [*runtimeExecutableArgv(descriptor, executable), "mcp", "get", "dartlab"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired:
        # 상한 초과는 미연결이 아니라 미판정이다. 판정으로 적으면 기기가 바쁠 때 이미 연결된
        # MCP 가 끊긴 것으로 화면에 뜬다(실측 2026-08-05).
        return {
            "connected": False,
            "mode": "global-cli",
            "detail": "probe_undetermined: timeout",
            "undetermined": True,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {"connected": False, "mode": "global-cli", "detail": f"probe_unavailable: {type(exc).__name__}"}
    detail = (completed.stdout or completed.stderr).strip()
    profileMatches = all(token in detail for token in ("dartlab.mcp", "--profile", "agent"))
    if runtimeId == "claude" and completed.returncode == 0 and "Project config" in detail:
        profileMatches = _claudeProjectMcpConfigured()
    return {
        "connected": completed.returncode == 0 and profileMatches,
        "mode": "global-cli",
        "detail": (detail[:1000] or None) if profileMatches else "agent_profile_missing",
    }


def probeMcpConnection(runtimeId: str, *, refresh: bool = False, blocking: bool = True) -> dict[str, object]:
    """Sig: probeMcpConnection(runtimeId, *, refresh=False, blocking=True) -> dict[str, object].

    Args: runtimeId는 확인할 런타임, refresh는 재측정 여부, blocking은 측정 대기 여부다.
    Returns: connected, mode, detail을 가진 상태다.
    Example: `probeMcpConnection("cline")`.

    ``blocking=False`` 는 표시 경로용이다. 마지막 실측값이 있으면 만료됐어도 즉시 주고
    갱신만 백그라운드로 보낸다. 기록이 없으면 연결됐다고 추정하지 않고 확인 중임을
    알리는 pending 상태를 돌려준다.
    """

    def _remember() -> dict[str, object]:
        """연결을 실제로 측정하고 판정에 성공했을 때만 기존 값을 갱신한다."""
        measured = _measureMcpConnection(runtimeId)
        return dict(_MCP_CACHE.put(runtimeId, measured, determined=not measured.get("undetermined")))

    if refresh:
        return _remember()
    entry = _MCP_CACHE.peek(runtimeId)
    if entry is not None and entry.fresh:
        return dict(entry.value)
    if blocking:
        return _remember()
    backgroundRefresher().submit(
        mcpProbeKey(runtimeId),
        lambda: retryUntilDetermined(_remember, lambda value: not value.get("undetermined")),
    )
    if entry is not None:
        return dict(entry.value)
    return {"connected": False, "mode": "global-cli", "detail": "probe_pending", "pending": True}


def _claudeProjectMcpConfigured(projectRoot: Path | None = None) -> bool:
    """Claude project MCP 설정이 agent read-only profile을 명시하는지 확인한다."""
    path = (projectRoot or Path.cwd()) / ".mcp.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False
    servers = value.get("mcpServers") if isinstance(value, dict) else None
    server = servers.get("dartlab") if isinstance(servers, dict) else None
    args = server.get("args") if isinstance(server, dict) else None
    return isinstance(args, list) and all(token in args for token in ("dartlab.mcp", "--profile", "agent"))


def _clineMcpConfigured(configRoot: Path | None = None) -> bool:
    """Cline 공식 설정에서 DartLab MCP 항목의 존재만 확인한다."""
    root = configRoot or Path.home() / ".cline"
    try:
        value = json.loads((root / "data" / "settings" / "cline_mcp_settings.json").read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False
    servers = value.get("mcpServers") if isinstance(value, dict) else None
    return isinstance(servers, dict) and isinstance(servers.get("dartlab"), dict)
