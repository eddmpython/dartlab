"""python -m dartlab.mcp → MCP 서버 실행.

기본 stdio (Claude Desktop / Codex CLI 호환). ``--transport`` 로 sse / http 선택.

마스터 플랜 v2 트랙 7 PR-M4 — Streamable HTTP (MCP 2024-11 표준) 추가.
"""

from __future__ import annotations

import argparse
import os
import sys


def _parseArgs(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="dartlab.mcp", description="DartLab MCP server entry point.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "http"),
        default="stdio",
        help="MCP transport (기본 stdio).",
    )
    parser.add_argument("--host", default="0.0.0.0", help="HTTP/SSE bind host.")
    parser.add_argument("--port", type=int, default=None, help="HTTP/SSE bind port (sse=8001 / http=8002 기본).")
    parser.add_argument("--json-response", action="store_true", help="Streamable HTTP 의 batch JSON 응답 모드.")
    parser.add_argument(
        "--profile",
        choices=("full", "agent"),
        default="full",
        help="도구 노출 프로필. agent는 read-only 도구만 광고하고 실행한다.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """argv parse 후 선택된 transport 의 run 함수를 호출한다.

    Args:
        argv: CLI 인자 리스트. None 이면 ``sys.argv[1:]`` 사용.

    Returns:
        None: 서버 event loop 가 종료될 때까지 block 한다.
    """
    args = _parseArgs(argv if argv is not None else sys.argv[1:])
    os.environ["DARTLAB_MCP_PROFILE"] = args.profile
    if args.transport == "stdio":
        from dartlab.mcp import runStdio

        runStdio()
    elif args.transport == "sse":
        from dartlab.mcp import runSse

        runSse(host=args.host, port=args.port or 8001)
    elif args.transport == "http":
        from dartlab.mcp import runStreamableHttp

        runStreamableHttp(host=args.host, port=args.port or 8002, jsonResponse=args.json_response)


if __name__ == "__main__":
    main()
