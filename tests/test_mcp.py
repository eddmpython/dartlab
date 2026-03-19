"""MCP 서버 기본 테스트 — bridge, tool 변환, 캐싱."""

from __future__ import annotations

import pytest

from dartlab.mcp import _company_cache, _get_or_create_company
from dartlab.mcp.bridge import MCPToolDef, build_mcp_tools, openai_schema_to_mcp_tool

# ── bridge 변환 ──


def test_openai_schema_to_mcp_tool():
    schema = {
        "type": "function",
        "function": {
            "name": "search_company",
            "description": "회사를 검색한다.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }
    tool = openai_schema_to_mcp_tool(schema)

    assert isinstance(tool, MCPToolDef)
    assert tool.name == "search_company"
    assert tool.description == "회사를 검색한다."
    assert "query" in tool.inputSchema["properties"]


def test_openai_schema_empty_function():
    tool = openai_schema_to_mcp_tool({})

    assert tool.name == ""
    assert tool.description == ""
    assert tool.inputSchema == {"type": "object", "properties": {}}


def test_build_mcp_tools_from_runtime():
    class FakeRuntime:
        def get_tool_schemas(self):
            return [
                {
                    "type": "function",
                    "function": {
                        "name": "tool_a",
                        "description": "A",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "tool_b",
                        "description": "B",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
            ]

    tools = build_mcp_tools(FakeRuntime())

    assert len(tools) == 2
    assert tools[0].name == "tool_a"
    assert tools[1].name == "tool_b"


# ── 캐시 ──


def test_get_or_create_company_none():
    assert _get_or_create_company(None) is None
    assert _get_or_create_company("") is None


def test_company_cache_reuses(monkeypatch):
    sentinel = object()
    _company_cache.clear()
    _company_cache["TEST"] = sentinel

    result = _get_or_create_company("TEST")

    assert result is sentinel
    _company_cache.clear()


# ── MCP SDK 없이도 bridge 모듈은 임포트 가능 ──


def test_bridge_importable_without_mcp_sdk():
    from dartlab.mcp.bridge import MCPResource, build_company_resources

    resources = build_company_resources("005930")

    assert len(resources) == 3
    assert any("sections" in r.uri for r in resources)
    assert all(isinstance(r, MCPResource) for r in resources)


# ── create_server는 MCP SDK가 없으면 ImportError ──


def test_create_server_requires_mcp_sdk(monkeypatch):
    import dartlab.mcp as mcp_mod

    original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def mock_import(name, *args, **kwargs):
        if name == "mcp.server":
            raise ImportError("no mcp")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)

    with pytest.raises(ImportError, match="MCP SDK"):
        mcp_mod.create_server()
