"""`dartlab plugin` command — 플러그인 관리."""

from __future__ import annotations


def configure_parser(subparsers) -> None:
    """plugin 서브커맨드 등록 — 플러그인 조회/생성."""
    parser = subparsers.add_parser("plugin", help="플러그인 관리 (list, create)")
    sub = parser.add_subparsers(dest="plugin_command")

    # dartlab plugin list
    sub.add_parser("list", help="설치된 플러그인 목록")

    # dartlab plugin create <name>
    create_parser = sub.add_parser("create", help="새 플러그인 패키지 생성")
    create_parser.add_argument("name", help="플러그인 이름 (예: esg-scores)")
    create_parser.add_argument("-d", "--description", default="", help="플러그인 설명")
    create_parser.add_argument("-t", "--type", default="data", choices=["data", "tool", "engine"], help="플러그인 유형")

    parser.set_defaults(handler=run)


def run(args) -> int:
    """서브커맨드(list/create) 분기 후 실행."""
    subcmd = getattr(args, "plugin_command", None)
    if subcmd == "list":
        return _list_plugins()
    if subcmd == "create":
        return _create_plugin(args)

    # 서브커맨드 없이 호출 시 list 기본
    return _list_plugins()


def _list_plugins() -> int:
    from dartlab.core.plugins import discover, get_loaded_plugins

    discover()
    plugins = get_loaded_plugins()

    if not plugins:
        print("\n  설치된 플러그인이 없습니다.\n")
        print("  시작하기:")
        print("    dartlab plugin create my-analysis   # 패키지 생성")
        print("    dartlab.ask('ESG 플러그인 만들어줘')  # AI 자동 생성")
        print()
        return 0

    print(f"\n  설치된 플러그인 ({len(plugins)}개):\n")
    for p in plugins:
        stability = f" [{p.stability}]" if p.stability != "stable" else ""
        print(f"    {p.name} v{p.version} ({p.plugin_type}){stability}")
        print(f"      {p.description}")
    print()
    return 0


def _create_plugin(args) -> int:
    from dartlab.ai.tools.plugin_creator import create_plugin

    result = create_plugin(
        name=args.name,
        description=args.description or f"{args.name} 플러그인",
        plugin_type=args.type,
    )
    print(result)
    return 0
