"""dartlab mcp — MCP 서버 실행."""

from __future__ import annotations

import json
import sys


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("mcp", help="MCP 서버 실행 (stdio)")
    parser.add_argument(
        "--config",
        choices=["claude-desktop", "claude-code", "cursor"],
        help="지정한 클라이언트의 설정 예시를 출력합니다.",
    )
    parser.set_defaults(handler=_run)


def _print_config(client: str) -> None:
    """MCP 클라이언트 설정 예시 출력."""
    import shutil

    uv_path = shutil.which("uv") or "uv"

    if client == "claude-desktop":
        # Claude Desktop: ~/AppData/Roaming/Claude/claude_desktop_config.json (Windows)
        #                  ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
        config = {
            "mcpServers": {
                "dartlab": {
                    "command": uv_path,
                    "args": ["run", "dartlab", "mcp"],
                }
            }
        }
        if sys.platform == "win32":
            path = r"%APPDATA%\Claude\claude_desktop_config.json"
        else:
            path = "~/Library/Application Support/Claude/claude_desktop_config.json"
        print(f"# Claude Desktop 설정 파일: {path}")
        print("# 아래 내용을 mcpServers에 추가하세요.\n")
        print(json.dumps(config, indent=2, ensure_ascii=False))

    elif client == "claude-code":
        # Claude Code: ~/.claude/settings.json 또는 프로젝트 .claude/settings.json
        config = {
            "mcpServers": {
                "dartlab": {
                    "command": uv_path,
                    "args": ["run", "dartlab", "mcp"],
                }
            }
        }
        print("# Claude Code 설정")
        print("# 방법 1: 글로벌 설정 (~/.claude/settings.json)")
        print("# 방법 2: 프로젝트 설정 (.claude/settings.json)")
        print("# 아래 내용을 mcpServers에 추가하세요.\n")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        print()
        print("# 또는 CLI에서 직접 추가:")
        print(f"#   claude mcp add dartlab -- {uv_path} run dartlab mcp")

    elif client == "cursor":
        config = {
            "mcpServers": {
                "dartlab": {
                    "command": uv_path,
                    "args": ["run", "dartlab", "mcp"],
                }
            }
        }
        print("# Cursor 설정: .cursor/mcp.json")
        print("# 아래 내용을 추가하세요.\n")
        print(json.dumps(config, indent=2, ensure_ascii=False))


def _run(args) -> None:
    if args.config:
        _print_config(args.config)
        return

    from dartlab.mcp import run_stdio

    run_stdio()
