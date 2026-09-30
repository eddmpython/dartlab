"""인텔리전스 팩은 레거시 runtime 대신 Skill/capability 검색으로 흡수된다."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_read_capability_replaces_runtime_intelligence_pack():
    from dartlab.ai.tools.readCapability import readCapability

    result = readCapability("재무상태표 Company panel")

    assert result.ok is True
    assert any(ref.payload.get("apiRef") == "Company.panel" for ref in result.refs)


def test_read_skill_replaces_runtime_pack_summary():
    from dartlab.ai.tools.readSkill import readSkill

    result = readSkill("처음 온 외부 시작점", audience="all")

    assert result.ok is True
    assert any(ref.id == "skill:start.dartlabSkillOs" for ref in result.refs)
