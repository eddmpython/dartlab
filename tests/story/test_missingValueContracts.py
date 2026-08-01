"""Story 렌더러가 결측 입력을 관측값 0으로 발행하지 않는지 검증한다."""

from __future__ import annotations

import pytest

from dartlab.story.blocks import MetricBlock, TableBlock, TextBlock
from dartlab.story.builders import (
    creditScenarioBlock,
    dcfValuationBlock,
    historicalRatiosBlock,
    priceTargetBlock,
    proFormaHighlightsBlock,
    reverseImpliedBlock,
    scenarioImpactBlock,
)
from dartlab.story.narrate import (
    narrateAccruals,
    narrateAltman,
    narrateBeneish,
    narrateDFV,
    narrateMacroEnvironment,
    narratePiotroski,
    narrateStoryPrecedents,
    narrateTechnicalAction,
)

pytestmark = [pytest.mark.unit]


def _metricLabels(blocks: list) -> set[str]:
    return {label for block in blocks if isinstance(block, MetricBlock) for label, _ in block.metrics}


def test_forecast_renderers_do_not_launder_missing_values_to_zero() -> None:
    proforma = proFormaHighlightsBlock({"years": [{"yearOffset": 1}]})
    assert "WACC" not in _metricLabels(proforma)

    scenario = scenarioImpactBlock({"scenarios": {"base": {"label": "기준"}}})
    table = next(block for block in scenario if isinstance(block, TableBlock))
    assert table.df["매출변화"].to_list() == ["-"]
    assert table.df["마진변화"].to_list() == ["-"]


def test_credit_scenario_does_not_compute_a_difference_without_scores() -> None:
    blocks = creditScenarioBlock({"grade": "A"}, {"grade": "BBB"}, None)
    note = next(block.text for block in blocks if isinstance(block, TextBlock))
    assert "계산하지 않았습니다" in note
    assert "0.0" not in note


def test_financial_builders_omit_missing_assumptions() -> None:
    assert _metricLabels(dcfValuationBlock({"perShareValue": 10_000})) == {"적정가"}
    assert "가중 목표가" not in _metricLabels(priceTargetBlock({"signal": "중립"}))
    assert _metricLabels(reverseImpliedBlock({"signal": "중립"})) == {"신호"}
    historical = historicalRatiosBlock({"warnings": ["입력 부족"]})
    assert not any(isinstance(block, MetricBlock) for block in historical)


def test_narratives_fail_closed_when_required_numeric_evidence_is_missing() -> None:
    assert narrateMacroEnvironment({"overallLabel": "중립"}) is None
    assert narrateStoryPrecedents({"confidence": "low"}) is None
    assert narrateAltman({"status": "ok", "zones": {}}) is None
    assert narratePiotroski({"grades": {}}) is None
    assert narrateBeneish({"status": "ok", "flags": {}}) is None
    assert narrateAccruals({"groups": {}}) is None


def test_technical_and_dfv_narratives_do_not_invent_missing_counterparts() -> None:
    technical = narrateTechnicalAction({"currentPrice": 10_000, "technicalVerdict": "관망", "support": 9_000})
    assert technical is not None
    assert "저항선" not in technical
    assert "저항선 0원" not in technical

    dfv = narrateDFV(
        {
            "dFV": 12_000,
            "opinion": "중립",
            "confidence": "낮음",
            "qualityWACC": {"totalSpread": 1.0},
            "scenarios": {"bull": 15_000},
        }
    )
    assert dfv is not None
    assert "Quality WACC" not in dfv
    assert "시나리오:" not in dfv
