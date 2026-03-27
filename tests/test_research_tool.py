"""research Super Tool 등록/dispatch 테스트."""

import pytest

pytestmark = pytest.mark.unit


def test_research_tool_registers():
    """research Super Tool이 정상 등록되는지 확인."""
    registered = {}

    def fakeRegister(name, func, description, schema, **kwargs):
        registered[name] = {
            "func": func,
            "description": description,
            "schema": schema,
            "kwargs": kwargs,
        }

    from dartlab.ai.tools.superTools.research import registerResearchTool

    registerResearchTool(fakeRegister)

    assert "research" in registered
    tool = registered["research"]
    assert "search" in tool["description"]
    assert tool["schema"]["properties"]["action"]["enum"] == ["search", "news", "read_url", "industry"]
    assert tool["kwargs"]["category"] == "global"


def test_research_dispatch_unknown_action():
    """알 수 없는 action에 대한 에러 메시지."""
    registered = {}

    def fakeRegister(name, func, *args, **kwargs):
        registered[name] = func

    from dartlab.ai.tools.superTools.research import registerResearchTool

    registerResearchTool(fakeRegister)

    result = registered["research"](action="invalid")
    assert "알 수 없는 action" in result


def test_research_search_no_query():
    """query 없이 search 호출 시 안내 메시지."""
    registered = {}

    def fakeRegister(name, func, *args, **kwargs):
        registered[name] = func

    from dartlab.ai.tools.superTools.research import registerResearchTool

    registerResearchTool(fakeRegister)

    result = registered["research"](action="search")
    assert "query" in result


def test_research_read_url_no_url():
    """url 없이 read_url 호출 시 안내 메시지."""
    registered = {}

    def fakeRegister(name, func, *args, **kwargs):
        registered[name] = func

    from dartlab.ai.tools.superTools.research import registerResearchTool

    registerResearchTool(fakeRegister)

    result = registered["research"](action="read_url")
    assert "url" in result


def test_research_search_no_backend_available(monkeypatch):
    """검색 패키지 미설치 시 안내 메시지."""
    from dartlab.gather import search

    monkeypatch.setattr(search, "_tavilyAvailable", lambda: False)
    monkeypatch.setattr(search, "_ddgAvailable", lambda: False)

    registered = {}

    def fakeRegister(name, func, *args, **kwargs):
        registered[name] = func

    from dartlab.ai.tools.superTools.research import registerResearchTool

    registerResearchTool(fakeRegister)

    result = registered["research"](action="search", query="test")
    assert "설치" in result


def test_superTools_init_includes_research():
    """registerSuperTools가 research를 포함하는지 확인."""
    registered = set()

    def fakeRegister(name, func, *args, **kwargs):
        registered.add(name)

    from dartlab.ai.tools.superTools import registerSuperTools

    registerSuperTools(company=None, registerTool=fakeRegister)

    assert "research" in registered
    assert "system" in registered
    assert "market" in registered
