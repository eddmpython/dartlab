"""ScenarioOverlay 전용 도구의 공개 입력 실패 계약."""

from __future__ import annotations

import pytest

from dartlab.ai.tools.scenarioOverlay import scenarioOverlay

pytestmark = pytest.mark.unit


def testScenarioOverlayRejectsMissingScenarioBeforeDataResolution() -> None:
    result = scenarioOverlay("")

    assert result.ok is False
    assert result.error == "missing_scenario"
    assert result.refs == []
