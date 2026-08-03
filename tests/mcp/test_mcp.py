"""MCP 서버의 canonical tool surface, resources, alias 계약을 검증한다."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


def test_mcp_tools_defined():
    from dartlab.mcp import _advertisedTools

    names = {tool["name"] for tool in _advertisedTools()}
    # 설치형 에이전트가 답변 루프를 소유하므로 MCP는 재귀 ask 없이 분석 도구만 광고한다.
    expected = {
        "ReadSkill",
        "ReadCapability",
        "EngineCall",
        "RunPython",
        "WebSearch",
        "SaveArtifact",
        "CompileVisual",
    }
    assert expected.issubset(names)
    assert "ask" not in names
    # 0.10 제거된 옛 33 generated 도구 + Discovery + Analysis Graph 도구는 advertised 에서 빠짐.
    deprecated = {
        "skill_search",
        "generated_spec_search",
        "engine_call",
        "verify_answer",
        "propose_skill",
        "companyInsights",
        "companyStory",
        "marketScan",
        "macroAnalysis",
        "listDartlabApi",
        "searchDartlabApi",
        "verifyDartlabApi",
    }
    assert deprecated.isdisjoint(names)


def test_mcp_tool_schema_valid():
    from dartlab.mcp import _advertisedTools

    for tool in _advertisedTools():
        assert "name" in tool
        assert "description" in tool
        assert "params" in tool
        assert "required" in tool
        assert isinstance(tool["params"], dict)
        assert isinstance(tool["required"], list)


def test_mcp_canonical_tools_execute():
    """canonical tool dispatch (registry SSOT 경유). 0.11 부터 dict 직접 반환 (structuredContent 활용)."""
    from dartlab.mcp import _executeWorkspaceAgentTool

    found = _executeWorkspaceAgentTool("ReadSkill", {"query": "테스트 규칙", "limit": 3})
    assert found["refs"][0]["id"] == "skill:operation.testing"

    spec = _executeWorkspaceAgentTool("ReadCapability", {"query": "재무상태표", "limit": 5})
    assert spec["refs"]

    executed = _executeWorkspaceAgentTool("RunPython", {"code": "emit_result(values={'x': 1})"})
    assert executed["ok"] is True
    assert any(ref["kind"] == "executionRef" for ref in executed["refs"])


def test_mcp_non_advertised_legacy_alias_is_blocked():
    """tools/list 밖 alias는 내부 registry 호환 여부와 무관하게 MCP에서 실행하지 않는다."""
    from dartlab.mcp import _executeWorkspaceAgentTool

    via_alias = _executeWorkspaceAgentTool("skill_search", {"query": "테스트 규칙", "limit": 3})
    assert via_alias["ok"] is False
    assert via_alias["error"] == "tool_not_advertised"
    assert "ReadSkill" in via_alias["data"]["advertisedTools"]


def test_mcp_unknown_tool_is_blocked_by_advertise_ssot():
    """폐기된 generated 도구도 광고 SSOT 밖에서는 동일한 오류 계약으로 거부한다."""
    from dartlab.mcp import _executeWorkspaceAgentTool

    payload = _executeWorkspaceAgentTool("companyInsights", {"stockCode": "005930"})
    assert payload["ok"] is False
    assert payload["error"] == "tool_not_advertised"
    assert payload["refs"] == []


def test_mcp_hidden_canonical_registry_tool_is_not_callable():
    """AI 내부 canonical 도구라도 tools/list 밖이면 MCP call 권한이 아니다."""
    from dartlab.mcp import _executeWorkspaceAgentTool

    payload = _executeWorkspaceAgentTool("EvidenceGate", {"skillId": "x", "refs": []})
    assert payload["ok"] is False
    assert payload["error"] == "tool_not_advertised"


def test_mcp_payload_budget_preserves_contract_fields():
    import json

    from dartlab.mcp.protocol import boundMcpPayload

    payload = {
        "ok": True,
        "summary": "큰 결과",
        "refs": [],
        "data": {
            "status": "partial",
            "gaps": [{"id": "missing.price", "status": "missing", "reason": "가격 없음"}],
            "provenance": ["source:filing"],
            "asOf": "2025-12-31",
            "blob": "x" * 100_000,
        },
        "error": None,
    }

    bounded = boundMcpPayload(payload, maxBytes=4096)

    assert len(json.dumps(bounded, ensure_ascii=False).encode("utf-8")) <= 4096
    assert bounded["data"]["status"] == "partial"
    assert bounded["data"]["gaps"][0]["id"] == "missing.price"
    assert bounded["data"]["provenance"] == ["source:filing"]
    assert bounded["data"]["asOf"] == "2025-12-31"
    assert bounded["payloadBudget"]["gap"]["status"] == "partial"


def test_mcp_advertised_tools_carry_annotations():
    """0.11의 모든 advertise 도구가 readOnly/destructive/idempotent/openWorld hint를 노출한다.

    마스터 플랜 v2 트랙 7 PR-M1에서 advertise SSOT가 CANONICAL_V2 추종으로 전환되며 옛 workbench-
    internal 3 종 (LookAheadGuard / GroundingCheck / RequestUserInput) 은 advertise 에서 제외.
    """
    from dartlab.mcp import _advertisedTools

    tools = {t["name"]: t for t in _advertisedTools()}
    # CANONICAL_V2 21종 모두 annotations 키를 보유하는지 핵심 도구 표본으로 검증한다.
    for name in (
        "ReadSkill",
        "ReadCapability",
        "RunPython",
        "WebSearch",
        "SaveArtifact",
        "CompileVisual",
        "DCFValuation",
        "PeerCompareN",
        "CreditScorecard",
    ):
        ann = tools[name]["annotations"]
        for key in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"):
            assert key in ann, f"{name} 의 annotations 에 {key} 누락"
            assert isinstance(ann[key], bool)
    # 핵심 분류 검증
    assert tools["ReadSkill"]["annotations"]["readOnlyHint"] is True
    assert tools["WebSearch"]["annotations"]["openWorldHint"] is True
    assert tools["SaveArtifact"]["annotations"]["readOnlyHint"] is False
    assert tools["RunPython"]["annotations"]["idempotentHint"] is False


def test_recipe_skills_all_exposed_as_prompts():
    """엔진 흡수 contract의 silent drift를 막는다.

    `list_prompts()` 는 `kind == "recipe"` 만 필터한다. 새 Skill OS 카테고리 (예: `playbook`,
    `scenario`) 가 도입되면 prompts 에서 조용히 누락 + 외부 LLM 이 알아챌 수 없음. 이 invariant
    가 깨지면 `_recipeSkillsForPrompts()` 의 필터를 갱신해야 한다는 신호.
    """
    from dartlab.mcp import _recipeSkillsForPrompts
    from dartlab.skills import listSkills

    recipe_files = {s.id for s in listSkills(includeUser=False) if s.kind == "recipe"}
    exposed = {s.id for s in _recipeSkillsForPrompts()}

    assert recipe_files == exposed, (
        f"recipe 파일 ↔ prompts 노출 불일치. 파일에만: {recipe_files - exposed}. prompts 에만: {exposed - recipe_files}"
    )
    assert recipe_files, "recipe 카테고리 skill 이 최소 1 개 이상 있어야 (현재 0)"


def test_mcp_skill_resources_are_readable():
    from dartlab.mcp import _resourcePayload

    listing, listing_mime = _resourcePayload("dartlab://skills")
    detail, detail_mime = _resourcePayload("dartlab://skills/start.dartlabSkillOs")

    listing_payload = json.loads(listing)
    detail_payload = json.loads(detail)

    assert listing_mime == "application/json"
    assert detail_mime == "application/json"
    assert any(item["id"] == "start.dartlabSkillOs" for item in listing_payload["skills"])
    assert detail_payload["id"] == "start.dartlabSkillOs"
    assert detail_payload["source"]["path"].replace("\\", "/").endswith("/skills/specs/start/dartlabSkillOs.md")


def test_mcp_logger_handler_no_duplicate():
    """stream identity 비교로 stderr logger handler를 하나만 유지한다."""
    import logging
    import sys

    import dartlab.mcp  # noqa: F401, 모듈 로드

    log = logging.getLogger("dartlab.mcp")
    stderr_handlers = [
        h for h in log.handlers if isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stderr
    ]
    assert len(stderr_handlers) == 1
    assert log.propagate is False


def test_create_server_requires_mcp_sdk(monkeypatch):
    import dartlab.mcp as mcp_mod

    original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def mock_import(name, *args, **kwargs):
        if name == "mcp.server":
            raise ImportError("no mcp")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)

    with pytest.raises(ImportError, match="MCP SDK"):
        mcp_mod.createServer()
