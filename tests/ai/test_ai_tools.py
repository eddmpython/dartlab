from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_canonical_tool_registry_exposes_expected_tools():
    from dartlab.ai.tools import CANONICAL_TOOL_NAMES, toolSpecs

    names = set(CANONICAL_TOOL_NAMES)
    specs = {spec["name"] for spec in toolSpecs()}

    # PascalCase canonical (snake_case alias 는 _LEGACY_NAME_MAP 에만, CANONICAL_TOOL_NAMES 미포함).
    assert {"RunPython", "ReadSkill", "ReadCapability", "WebSearch", "SaveArtifact", "CompileVisual"}.issubset(names)
    assert names == specs


def test_deprecated_tools_not_in_registry():
    """P-revised — legacy 도구는 registry 에서 제거되어야 한다."""
    from dartlab.ai.tools import CANONICAL_TOOL_NAMES

    deprecated = {"skill_search", "generated_spec_search", "engine_call", "verify_answer", "read", "write"}
    assert deprecated.isdisjoint(set(CANONICAL_TOOL_NAMES))


def test_read_capability_uses_capability_ssot():
    """후속 도구 read_capability 가 dartlab.reference.capability.search 를 그대로 활용."""
    from dartlab.ai.tools.readCapability import readCapability

    result = readCapability("scan growth")

    assert result.ok is True
    assert any(ref.payload.get("apiRef") in {"dartlab.scan", "scan"} for ref in result.refs)


def test_engine_call_internal_helper_blocks_unknown_api():
    """engineCall 은 휴리스틱 helper 로 보존 (registry 미노출). plan 검증 동작 유지 확인."""
    from dartlab.ai.tools.engineCall import engineCall

    result = engineCall({"apiRef": "Nope.missing"})

    assert result.ok is False
    assert result.error == "unknown_api_ref"


def test_installable_runtime_package_is_importable():
    import importlib.util

    assert importlib.util.find_spec("dartlab.ai.runtime") is not None
