"""회귀 가드 — registry 가 canonical 도구 보호 + V2 6 종 등록 확인."""

from __future__ import annotations

import pytest

from dartlab.ai.tools.registry import (
    CANONICAL_TOOL_NAMES,
    CANONICAL_V2,
    registerTool,
    unregisterTool,
)


@pytest.mark.unit
def test_canonical_v2_six_tools_registered() -> None:
    for name in CANONICAL_V2:
        assert name in CANONICAL_TOOL_NAMES, f"{name} 미등록"


@pytest.mark.unit
def test_canonical_tool_cannot_be_overridden_by_plugin() -> None:
    def _evil(**kwargs):  # noqa: ANN
        return None

    with pytest.raises(ValueError, match="canonical"):
        registerTool("run_python", _evil)


@pytest.mark.unit
def test_canonical_tool_cannot_be_unregistered() -> None:
    with pytest.raises(ValueError, match="canonical"):
        unregisterTool("read_skill")


@pytest.mark.unit
def test_plugin_tool_register_unregister_round_trip() -> None:
    def _hello(**kwargs):  # noqa: ANN
        return None

    registerTool("plugin_hello", _hello, description="hello plugin")
    try:
        from dartlab.ai.tools.registry import listToolNames

        assert "plugin_hello" in listToolNames()
    finally:
        unregisterTool("plugin_hello")


@pytest.mark.unit
def test_agent_default_tool_names_equals_canonical_v2() -> None:
    """agent.py _DEFAULT_TOOL_NAMES 와 CANONICAL_V2 가 같은 단일 SSOT 인지 확인.

    agent-MCP 드리프트 회귀 가드: agent 가 CANONICAL_V2 대신 자체 하드코딩 목록을
    사용하면 LLM 이 MCP 와 다른 도구 집합을 보게 된다 (2026-08-02 발견·수정).
    """
    import dartlab.ai.agent as _agent

    agent_names = set(_agent._DEFAULT_TOOL_NAMES)
    v2_names = set(CANONICAL_V2)
    assert agent_names == v2_names, (
        f"agent._DEFAULT_TOOL_NAMES != CANONICAL_V2. "
        f"agent-only: {sorted(agent_names - v2_names)}, "
        f"V2-only: {sorted(v2_names - agent_names)}"
    )
