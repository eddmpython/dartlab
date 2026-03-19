"""dartlab mcp — MCP 서버 실행."""

from __future__ import annotations


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("mcp", help="MCP 서버 실행 (stdio)")
    parser.set_defaults(func=_run)


def _run(args) -> None:
    from dartlab.mcp import run_stdio

    run_stdio()
