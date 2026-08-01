"""mcpAdvertisedToolNames SSOT 단위 — 마스터 플랜 v2 트랙 7 PR-M1.

registry CANONICAL_V2 자동 추종 + advertise 도구 spec 일관성 검증. 외부 호출 0.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_mcpAdvertisedToolNames_returns_ask_plus_canonical_v2() -> None:
    """ask + CANONICAL_V2 = 23 종 (PR-M1 목표 21+ ask)."""
    from dartlab.ai.tools.registry import CANONICAL_V2
    from dartlab.mcp.protocol import mcpAdvertisedToolNames

    names = mcpAdvertisedToolNames()
    assert names[0] == "ask"
    assert len(names) == 1 + len(CANONICAL_V2)
    assert names[1:] == CANONICAL_V2


def test_mcpAdvertisedToolNames_expands_beyond_legacy() -> None:
    """advertised 가 옛 정적 12-tuple legacy 보다 많은 도구 노출 (마이그레이션 완료)."""
    from dartlab.mcp.protocol import mcpAdvertisedToolNames

    # 옛 MCP_WORKSPACE_AGENT_TOOL_NAMES (12 종, LookAheadGuard/RequestUserInput stub 포함) 는
    # ask_kernel_status leak 경로와 함께 폐기 (debt-honesty P2-6).
    assert len(mcpAdvertisedToolNames()) > 12


def test_mcpAdvertisedToolNames_includes_finance_primitives() -> None:
    """트랙 1 PR-1~PR-7 금융 primitive 모두 MCP 외부에 노출."""
    from dartlab.mcp.protocol import mcpAdvertisedToolNames

    names = set(mcpAdvertisedToolNames())
    required = {
        "DCFValuation",
        "PeerCompareN",
        "CompileFinancialDashboard",
        "RegressionForecast",
        "SensitivityAnalysis",
        "CreditScorecard",
        "ScenarioCompareN",
        "ScenarioOverlay",
    }
    missing = required - names
    assert not missing, f"finance primitive MCP advertise 누락: {missing}"


def test_mcpAdvertisedToolNames_excludes_workbench_internals() -> None:
    """RunWorkbench / EvidenceGate / PickStoryTemplate 같은 workbench 내부 도구는 advertise X."""
    from dartlab.mcp.protocol import mcpAdvertisedToolNames

    names = set(mcpAdvertisedToolNames())
    excluded = {"RunWorkbench", "EvidenceGate", "PickStoryTemplate"}
    leaked = excluded & names
    assert not leaked, f"workbench 내부 도구 MCP 외부 누출: {leaked}"


def test_advertisedTools_specs_count_matches_names() -> None:
    """advertisedTools() spec 갯수가 advertise names 갯수와 일치 (registry 누락 0)."""
    from dartlab.mcp.protocol import advertisedTools, mcpAdvertisedToolNames

    names = mcpAdvertisedToolNames()
    tools = advertisedTools()
    assert len(tools) == len(names), f"advertise spec 누락: names={len(names)} specs={len(tools)}"


def test_advertisedTools_spec_fields_present() -> None:
    """각 advertise tool spec 의 name / description / params / annotations 필드 검증."""
    from dartlab.mcp.protocol import advertisedTools

    tools = advertisedTools()
    assert len(tools) >= 20
    for tool in tools:
        assert "name" in tool and tool["name"]
        assert "description" in tool
        assert "params" in tool
        assert "annotations" in tool


def test_advertisedTools_no_duplicates() -> None:
    from dartlab.mcp.protocol import advertisedTools

    names = [t["name"] for t in advertisedTools()]
    assert len(names) == len(set(names))


def test_advertised_registry_tools_all_have_executors() -> None:
    """ask 외 tools/list 항목은 같은 AI registry에 executor가 반드시 존재한다."""
    from dartlab.ai.tools.registry import _TOOLS
    from dartlab.mcp.protocol import mcpAdvertisedToolNames

    assert set(mcpAdvertisedToolNames()[1:]) <= set(_TOOLS)


def test_advertisedTools_fails_closed_when_spec_is_missing(monkeypatch) -> None:
    """광고 이름의 schema 누락을 조용히 숨기지 않는다."""
    from dartlab.mcp import protocol

    monkeypatch.setattr(protocol, "mcpAdvertisedToolNames", lambda: ("ask", "MissingTool"))
    with pytest.raises(KeyError, match="MissingTool"):
        protocol.advertisedTools()
