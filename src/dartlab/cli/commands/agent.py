"""`dartlab agent` Runtime Center CLI."""

from __future__ import annotations

import json
from typing import Any

from dartlab.ai.runtime import getRuntimeEngine
from dartlab.ai.runtime.installManager import buildInstallPlan, executeInstallPlan
from dartlab.ai.runtime.mcpBootstrap import buildMcpConnectPlan, executeMcpConnectPlan


def configureParser(subparsers) -> None:
    """agent setup/status/install/connect/sessions 서브커맨드를 등록한다."""
    parser = subparsers.add_parser("agent", help="설치형 agent runtime 관리")
    actions = parser.add_subparsers(dest="agentAction", required=True)
    status = actions.add_parser("status", help="runtime과 MCP 상태")
    status.add_argument("runtimeId", nargs="?", choices=["codex", "claude", "cline"])
    status.add_argument("--refresh", action="store_true")
    status.add_argument("--json", action="store_true", dest="asJson", help="내부 상세 상태를 JSON으로 출력")
    setup = actions.add_parser("setup", help="설치·로그인·DartLab 연결을 한 흐름으로 완료")
    setup.add_argument("runtimeId", nargs="?", choices=["codex", "claude"])
    setup.add_argument("--yes", "-y", action="store_true", help="표시된 setup 변경을 한 번에 승인")
    install = actions.add_parser("install", help="공식 CLI 설치 계획")
    install.add_argument("runtimeId", choices=["codex", "claude", "cline"])
    install.add_argument("--approve-digest", default=None)
    connect = actions.add_parser("connect", help="DartLab MCP 연결 계획")
    connect.add_argument("runtimeId", choices=["codex", "claude", "cline"])
    connect.add_argument("--approve-digest", default=None)
    sessions = actions.add_parser("sessions", help="저장된 세션 매핑")
    sessions.add_argument("--limit", type=int, default=20)
    parser.set_defaults(handler=run)


def run(args) -> int:
    """선택한 Runtime Center 작업을 실행한다."""
    if args.agentAction == "status":
        return _status(args.runtimeId, refresh=args.refresh, asJson=getattr(args, "asJson", False))
    if args.agentAction == "setup":
        return runSetup(args.runtimeId, yes=getattr(args, "yes", False))
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


def _status(runtimeId: str | None, *, refresh: bool, asJson: bool = False) -> int:
    """Sig: _status(runtimeId, *, refresh) -> int.

    Args: 선택적 runtimeId와 probe 캐시 무시 여부다.
    Returns: CLI 성공 코드 0이다.
    Example: `_status(None, refresh=True)`.
    """
    values = getRuntimeEngine().status(refresh=refresh)["runtimes"]
    if runtimeId:
        values = [item for item in values if item["runtimeId"] == runtimeId]
    if asJson:
        print(json.dumps(values, ensure_ascii=False, indent=2))
        return 0
    for item in values:
        name = str(item.get("displayName") or item.get("runtimeId"))
        if item.get("investmentReady"):
            print(f"  {name}: 투자 분석 준비 완료")
            print("    지금 바로 자연어 투자 브리프를 요청할 수 있습니다.")
        elif item.get("state") != "ready":
            print(f"  {name}: 설치 필요")
            print("    dartlab setup 한 번으로 설치부터 연결까지 진행합니다.")
        elif str((item.get("auth") or {}).get("state")) not in {"authenticated", "unsupported"}:
            print(f"  {name}: 공식 로그인 필요")
            print("    dartlab setup이 로그인 화면을 열고 완료 후 자동으로 계속합니다.")
        elif not bool((item.get("mcp") or {}).get("connected")):
            print(f"  {name}: DartLab 연결 필요")
            print("    dartlab setup이 남은 연결 단계만 수행합니다.")
        else:
            print(f"  {name}: 투자 분석 계약 점검 필요")
            print("    dartlab setup을 다시 실행해 준비 상태를 복구하세요.")
    return 0


def runSetup(runtimeId: str | None, *, yes: bool) -> int:
    """설치부터 첫 투자 질문 준비까지 같은 CLI 프로세스에서 끝낸다."""
    from dartlab.ai.runtime.setupCoordinator import prepareRuntime, previewRuntimeSetup

    plan = previewRuntimeSetup(runtimeId)
    if plan.alreadyReady:
        print(f"\n  {plan.displayName}: 이미 투자 분석 준비가 완료돼 변경하지 않습니다.\n")
        result = prepareRuntime(plan.runtimeId, approved=True)
        return 0 if result.investmentReady else 1
    _printSetupPlan(plan)
    approved = yes or _confirmSetup()
    result = prepareRuntime(
        plan.runtimeId,
        approved=approved,
        observer=lambda step: print(f"  [{_stepMark(step.status)}] {step.detail}"),
    )
    print()
    if result.investmentReady:
        print("  투자 분석 준비 완료")
        print("  바로 시작: dartlab invest 005930")
        print('  자연어 질문: dartlab ask "삼성전자 005930 투자 분석해줘"\n')
        return 0
    print(f"  준비 상태: {result.state}")
    if result.nextAction:
        print(f"  다음 조치: {result.nextAction}")
    print()
    return 1


def _printSetupPlan(plan: Any) -> None:
    print(f"\n  {plan.displayName}을 투자 분석 엔진으로 준비합니다.")
    for change in plan.changes:
        print(f"  - {change}")
    if plan.prerequisitePlan is not None:
        print(f"\n  선행 설치 명령: {' '.join(plan.prerequisitePlan.argv)}")
    if plan.installPlan is not None:
        print(f"\n  설치 명령: {' '.join(plan.installPlan.argv)}")
    if plan.mcpPlan is not None:
        print(f"  연결 명령: {' '.join(plan.mcpPlan.argv)}")
    print("  인증 정보는 DartLab이 읽거나 저장하지 않습니다.\n")


def _confirmSetup() -> bool:
    try:
        return input("  위 변경을 한 번 승인하고 계속할까요? [y/N] ").strip().casefold() in {"y", "yes", "예"}
    except EOFError:
        return False


def _stepMark(status: str) -> str:
    return {"completed": "완료", "skipped": "유지", "running": "진행", "failed": "실패"}.get(status, status)


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
