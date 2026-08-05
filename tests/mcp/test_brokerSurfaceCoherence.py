"""설치된 AI 에게 건네는 표면이 실제 광고 목록과 어긋나지 않는지 고정한다.

DartLab 은 사용자 PC 의 agent CLI 를 통제하지 않고 중개한다. 그 AI 가 DartLab 을 아는
경로는 셋뿐이다. MCP instructions, tools/list 의 도구 설명과 스키마, 런타임이 주입하는
분석 캡슐. 이 셋이 광고 목록과 어긋나면 AI 는 존재하지 않는 도구의 사용법을 배운다.

실측 회귀(2026-08-05): 실서비스 `agent` 프로필이 18 개를 광고하는데 정적 지침이
`RunPython` 을 9 회, `SaveArtifact` 를 1 회 가르치고 있었다. 도구 설명 안에도 5 회 더
남아 있었다. 라이브 핸드셰이크로 호출하면 `tool_not_advertised` 로 실패하는 절차였다.
"""

from __future__ import annotations

import re

import pytest

from dartlab.ai.tools.registry import listToolNames, toolSpecs
from dartlab.mcp.protocol import mcpAdvertisedToolNames, mcpInstructions

pytestmark = pytest.mark.unit

_PROFILES = ("agent", "full")


def _ghosts(text: str, advertised: set[str]) -> list[str]:
    """광고 목록 밖 도구 이름이 본문에 등장하면 그 이름을 모아 돌려준다."""
    unadvertised = set(listToolNames()) - advertised
    return sorted(name for name in unadvertised if re.search(rf"\b{re.escape(name)}\b", text))


@pytest.mark.parametrize("profile", _PROFILES)
def testInstructionsNameOnlyAdvertisedTools(profile: str) -> None:
    """지침은 그 프로필이 실제로 광고하는 도구만 가르친다."""
    advertised = set(mcpAdvertisedToolNames(profile))
    ghosts = _ghosts(mcpInstructions(profile), advertised)
    assert not ghosts, f"{profile} 지침이 광고되지 않은 도구를 가르친다: {ghosts}"


@pytest.mark.parametrize("profile", _PROFILES)
def testEveryAdvertisedToolIsNamedInInstructions(profile: str) -> None:
    """광고하면서 한 번도 언급하지 않는 도구를 남기지 않는다.

    이름이 안 나오면 AI 는 그 도구가 있는 줄 모른다. 광고는 했는데 쓰이지 않는 표면이 된다.
    """
    advertised = mcpAdvertisedToolNames(profile)
    text = mcpInstructions(profile)
    missing = [name for name in advertised if not re.search(rf"\b{re.escape(name)}\b", text)]
    assert not missing, f"{profile} 지침이 광고 도구를 언급하지 않는다: {missing}"


@pytest.mark.parametrize("profile", _PROFILES)
def testAdvertisedToolDescriptionsDoNotTeachGhostTools(profile: str) -> None:
    """도구 설명과 스키마도 tools/list 로 그대로 전달되므로 같은 규칙을 받는다."""
    advertised = set(mcpAdvertisedToolNames(profile))
    specs = {str(spec.get("name") or ""): spec for spec in toolSpecs()}
    offenders: dict[str, list[str]] = {}
    for name in sorted(advertised):
        spec = specs.get(name)
        if spec is None:
            continue
        body = f"{spec.get('description') or ''} {spec.get('input_schema') or spec.get('inputSchema') or ''}"
        ghosts = _ghosts(body, advertised)
        if ghosts:
            offenders[name] = ghosts
    assert not offenders, f"{profile} 광고 도구 설명이 없는 도구를 가르친다: {offenders}"


def testAnalysisCapsuleDoesNotNameGhostTools() -> None:
    """런타임이 주입하는 분석 캡슐도 실서비스 프로필 기준으로 검사한다.

    캡슐은 중개 세션마다 주입되므로 여기에 남은 유령 이름이 가장 자주 읽힌다.
    """
    from pathlib import Path

    from dartlab.ai.runtime.analysisCapsule import buildAnalysisCapsule

    advertised = set(mcpAdvertisedToolNames("agent"))
    capsule = buildAnalysisCapsule(cwd=Path.cwd(), mcpConnected=True)
    ghosts = _ghosts(capsule, advertised)
    assert not ghosts, f"분석 캡슐이 광고되지 않은 도구를 가르친다: {ghosts}"
