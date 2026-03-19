"""DartLab MCP 서버 — Claude Desktop / Cursor 연동.

사용법::

        # stdio 모드로 서버 실행
        dartlab mcp

        # 또는 직접 실행
        python -m dartlab.mcp

Claude Desktop config.json 예시::

        {
            "mcpServers": {
                "dartlab": {
                    "command": "uv",
                    "args": ["run", "dartlab", "mcp"]
                }
            }
        }
"""

from __future__ import annotations

from typing import Any

# 회사 세션 캐시
_company_cache: dict[str, Any] = {}


def _get_or_create_company(stock_code: str | None) -> Any | None:
    """종목코드로 Company 인스턴스 가져오기 (캐싱)."""
    if not stock_code:
        return None
    if stock_code in _company_cache:
        return _company_cache[stock_code]

    from dartlab import Company

    c = Company(stock_code)
    _company_cache[stock_code] = c
    return c


def create_server():
    """MCP 서버 인스턴스 생성."""
    try:
        from mcp.server import Server
        from mcp.types import TextContent, Tool
    except ImportError:
        raise ImportError("MCP SDK가 필요합니다.\n  uv add 'mcp[cli]>=1.0'\n또는: pip install 'mcp[cli]>=1.0'")

    from dartlab.engines.ai.tools_registry import build_tool_runtime

    from .bridge import build_mcp_tools

    app = Server("dartlab")

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        runtime = build_tool_runtime(None, name="mcp-list")
        mcp_tools = build_mcp_tools(runtime)
        return [
            Tool(
                name=t.name,
                description=t.description,
                inputSchema=t.inputSchema,
            )
            for t in mcp_tools
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        args = dict(arguments)
        stock_code = args.pop("stock_code", None)
        company = _get_or_create_company(stock_code)
        runtime = build_tool_runtime(company, name="mcp-call")
        result = runtime.execute_tool(name, args)
        return [TextContent(type="text", text=result)]

    return app


def run_stdio():
    """stdio 모드로 MCP 서버 실행."""
    import asyncio

    try:
        from mcp.server.stdio import stdio_server
    except ImportError:
        raise ImportError("MCP SDK가 필요합니다.\n  uv add 'mcp[cli]>=1.0'\n또는: pip install 'mcp[cli]>=1.0'")

    app = create_server()

    async def _main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_main())


if __name__ == "__main__":
    run_stdio()
