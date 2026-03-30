"""MCP 서버 기본 테스트 — 도구 정의, 실행, 캐싱."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_mcp_tools_defined():
    from dartlab.mcp import _TOOLS

    assert len(_TOOLS) > 10
    names = {t["name"] for t in _TOOLS}
    assert "companyInsights" in names
    assert "searchCompany" in names
    assert "companyReview" in names
    assert "marketScan" in names


def test_mcp_tool_schema_valid():
    from dartlab.mcp import _TOOLS

    for tool in _TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "params" in tool
        assert "required" in tool
        assert isinstance(tool["params"], dict)
        assert isinstance(tool["required"], list)


def test_fmt_none():
    from dartlab.mcp import _fmt

    assert _fmt(None) == "데이터 없음"


def test_fmt_dict():
    from dartlab.mcp import _fmt

    result = _fmt({"key": "value"})
    assert "key" in result
    assert "value" in result


def test_fmt_list():
    from dartlab.mcp import _fmt

    result = _fmt(["a", "b"])
    assert "a" in result
    assert "b" in result


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
