from __future__ import annotations

import pytest

from dartlab.story import narrative

pytestmark = pytest.mark.unit


def test_narrative_annual_columns_respect_base_period() -> None:
    periods = ["2025", "2024", "2023", "2022"]

    assert narrative._annualCols(periods, basePeriod="2023") == ["2023", "2022"]


def test_detect_threads_forwards_base_period(monkeypatch) -> None:
    received = []

    def detector(company, blockMap, *, basePeriod=None):
        received.append(basePeriod)
        return None

    monkeypatch.setattr(narrative, "_DETECTORS", [(detector, {"수익성"})])

    class VerifiedInputs(dict):
        verifiedNarrativeInputs = True

    assert narrative.detectThreads(object(), VerifiedInputs(), basePeriod="2024Q3") == []
    assert received == ["2024Q3"]


def test_current_narrative_blocks_self_calculated_claims() -> None:
    class Company:
        def select(self, *args, **kwargs):
            raise AssertionError("L3 self-calculated narrative must not read raw finance")

    assert narrative.detectThreads(Company(), {}, basePeriod=None) == []


def test_historical_act_transitions_do_not_read_latest_private_ratios() -> None:
    class Company:
        @property
        def _finance(self):
            raise AssertionError("historical path must not read latest ratios")

    assert narrative.buildActTransitions(Company(), basePeriod="2024") == {}


def test_historical_thesis_blocks_latest_ai_and_records_gap() -> None:
    from dartlab.story.registry import buildStory

    class Company:
        stockCode = "005930"
        corpName = "테스트"
        market = "KR"

        @property
        def ask(self):
            raise AssertionError("historical thesis must not call latest AI")

    story = buildStory(Company(), type="thesis", basePeriod="2024", hypothesis="과거 가설")

    assert any(gap.get("code") == "HISTORICAL_THESIS_UNSUPPORTED" for gap in story.lensGaps)
    assert "과거 시점에 고정된 AI 논제 검증 경로가 없어" in story.toMarkdown()
