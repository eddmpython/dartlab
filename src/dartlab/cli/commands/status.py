"""`dartlab status` 설치형 agent runtime 상태."""

from __future__ import annotations

from dartlab.ai.runtime import getRuntimeEngine


def configureParser(subparsers) -> None:
    """status 서브커맨드에 runtime probe 옵션을 등록한다."""
    parser = subparsers.add_parser("status", help="설치형 agent CLI 연결 상태 확인")
    parser.add_argument("--runtime", "-r", choices=["codex", "claude", "cline"], default=None)
    parser.add_argument("--refresh", action="store_true", help="15초 캐시를 무시하고 다시 확인")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """설치, 버전, MCP 연결 상태를 표로 출력한다."""
    status = getRuntimeEngine().status(refresh=args.refresh)
    runtimes = status["runtimes"]
    if args.runtime:
        runtimes = [item for item in runtimes if item["runtimeId"] == args.runtime]
    print("\n  Agent runtime  │ 상태         │ 버전                         │ DartLab MCP")
    print("  ───────────────┼──────────────┼──────────────────────────────┼────────────")
    for item in runtimes:
        connected = bool((item.get("mcp") or {}).get("connected"))
        version = str(item.get("version") or "-")[:28]
        print(
            f"  {item['runtimeId']:<14s} │ {item['state']:<12s} │ {version:<28s} │ {'연결' if connected else '미연결'}"
        )
    ready = [item for item in runtimes if item["state"] == "ready"]
    print(f"\n  {len(ready)}/{len(runtimes)} runtime 사용 가능")
    if not ready:
        print("  설치 계획: dartlab agent install <runtime>\n")
    else:
        print("  상세 설정: dartlab agent status\n")
    return 0
