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

    # stock_code 파라미터 정의 — company 필요 도구에 주입
    _STOCK_CODE_PROP = {
        "stock_code": {
            "type": "string",
            "description": "종목코드 (예: 005930) 또는 티커 (예: AAPL). 기업별 도구 호출 시 필수.",
        }
    }

    # company=None 일 때만 노출되는 도구 (stock_code 불필요)
    _runtime_no_company = build_tool_runtime(None, name="mcp-schema-base")
    _base_tool_names = {s["function"]["name"] for s in _runtime_no_company.get_tool_schemas()}

    # dummy object로 전체 도구 스키마 수집 (실제 Company 로딩 없이)
    _runtime_full = build_tool_runtime(object(), name="mcp-schema-full")

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        mcp_tools = build_mcp_tools(_runtime_full)
        result = []
        for t in mcp_tools:
            schema = dict(t.inputSchema)
            # company 필요 도구에 stock_code 파라미터 주입
            if t.name not in _base_tool_names:
                props = dict(schema.get("properties", {}))
                props.update(_STOCK_CODE_PROP)
                schema["properties"] = props
                req = list(schema.get("required", []))
                if "stock_code" not in req:
                    req.insert(0, "stock_code")
                schema["required"] = req
            result.append(
                Tool(
                    name=t.name,
                    description=t.description,
                    inputSchema=schema,
                )
            )
        return result

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
