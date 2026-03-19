"""OpenAI function calling 스키마 → MCP Tool 변환 브릿지."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MCPToolDef:
    """MCP Tool 정의."""

    name: str
    description: str
    inputSchema: dict


@dataclass
class MCPResource:
    """MCP Resource 정의."""

    uri: str
    name: str
    description: str
    mimeType: str = "application/json"


def openai_schema_to_mcp_tool(schema: dict) -> MCPToolDef:
    """OpenAI function calling 스키마 → MCP Tool 변환."""
    func = schema.get("function", {})
    return MCPToolDef(
        name=func.get("name", ""),
        description=func.get("description", ""),
        inputSchema=func.get("parameters", {"type": "object", "properties": {}}),
    )


def build_mcp_tools(runtime) -> list[MCPToolDef]:
    """ToolRuntime의 모든 도구를 MCP Tool 목록으로 변환."""
    return [openai_schema_to_mcp_tool(s) for s in runtime.get_tool_schemas()]


def build_company_resources(stock_code: str) -> list[MCPResource]:
    """회사별 MCP Resource 목록 생성."""
    base = f"dartlab://company/{stock_code}"
    return [
        MCPResource(
            uri=f"{base}/sections",
            name=f"{stock_code} sections",
            description="공시 섹션 지도",
        ),
        MCPResource(
            uri=f"{base}/ratios",
            name=f"{stock_code} ratios",
            description="재무비율",
        ),
        MCPResource(
            uri=f"{base}/topics",
            name=f"{stock_code} topics",
            description="조회 가능 topic 목록",
        ),
    ]
