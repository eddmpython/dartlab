"""`dartlab agent` Runtime Center CLI."""

from __future__ import annotations

import json

from dartlab.ai.runtime import getRuntimeEngine
from dartlab.ai.runtime.installManager import buildInstallPlan, executeInstallPlan
from dartlab.ai.runtime.mcpBootstrap import buildMcpConnectPlan, executeMcpConnectPlan


def configureParser(subparsers) -> None:
    """agent status/install/connect/sessions 서브커맨드를 등록한다."""
    parser = subparsers.add_parser("agent", help="설치형 agent runtime 관리")
    actions = parser.add_subparsers(dest="agentAction", required=True)
    status = actions.add_parser("status", help="runtime과 MCP 상태")
    status.add_argument("runtimeId", nargs="?", choices=["codex", "claude", "cline"])
    status.add_argument("--refresh", action="store_true")
    install = actions.add_parser("install", help="공식 CLI 설치 계획")
    install.add_argument("runtimeId", choices=["codex", "claude", "cline"])
    install.add_argument("--approve-digest", default=None)
    connect = actions.add_parser("connect", help="DartLab MCP 연결 계획")
    connect.add_argument("runtimeId", choices=["codex", "claude"])
    connect.add_argument("--approve-digest", default=None)
    sessions = actions.add_parser("sessions", help="저장된 세션 매핑")
    sessions.add_argument("--limit", type=int, default=20)
    parser.set_defaults(handler=run)


def run(args) -> int:
    """선택한 Runtime Center 작업을 실행한다."""
    if args.agentAction == "status":
        return _status(args.runtimeId, refresh=args.refresh)
    if args.agentAction == "install":
        plan = buildInstallPlan(args.runtimeId)
        return _applyOrPrint(plan, args.approve_digest, executeInstallPlan)
    if args.agentAction == "connect":
        plan = buildMcpConnectPlan(args.runtimeId)
        return _applyOrPrint(plan, args.approve_digest, executeMcpConnectPlan)
    if args.agentAction == "sessions":
        sessions = getRuntimeEngine().sessionStore.list(limit=max(1, min(args.limit, 1000)))
        print(json.dumps([item.toDict() for item in sessions], ensure_ascii=False, indent=2))
        return 0
    return 2


def _status(runtimeId: str | None, *, refresh: bool) -> int:
    """Sig: _status(runtimeId, *, refresh) -> int.

    Args: 선택적 runtimeId와 probe 캐시 무시 여부다.
    Returns: CLI 성공 코드 0이다.
    Example: `_status(None, refresh=True)`.
    """
    values = getRuntimeEngine().status(refresh=refresh)["runtimes"]
    if runtimeId:
        values = [item for item in values if item["runtimeId"] == runtimeId]
    print(json.dumps(values, ensure_ascii=False, indent=2))
    return 0


def _applyOrPrint(plan, approvedDigest: str | None, executor) -> int:
    """Sig: _applyOrPrint(plan, approvedDigest, executor) -> int.

    Args: digest 계획, 선택적 승인 digest, 실행 함수다.
    Returns: 출력만 하거나 성공 실행하면 0이다.
    Raises: 하위 공식 CLI 실행 오류를 그대로 전파한다.
    Example: `_applyOrPrint(plan, None, executor)`.
    """
    if not approvedDigest:
        print(json.dumps(plan.toDict(), ensure_ascii=False, indent=2))
        print("\n  검토 후 같은 명령에 --approve-digest <digest>를 붙여 실행하세요.\n")
        return 0
    result = executor(plan, approvedDigest=approvedDigest)
    print(result.stdout or result.stderr)
    return 0
