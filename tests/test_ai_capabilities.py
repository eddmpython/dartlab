from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

from types import SimpleNamespace

import polars as pl

from dartlab.ai.context import build_context_skeleton
from dartlab.ai.context.company_adapter import get_headline_ratios, get_ratio_series
from dartlab.ai.runtime.events import EventKind
from dartlab.ai.spec import buildSpec
from dartlab.ai.tools.registry import build_tool_runtime
from dartlab.core.capabilities import CapabilityKind, UiAction, get_capability_specs


class FakeRatioResult:
    def __init__(self):
        self.revenueTTM = 125000
        self.operatingIncomeTTM = 21000
        self.netIncomeTTM = 18000
        self.operatingMargin = 16.8
        self.roe = 11.2
        self.roa = 6.1
        self.debtRatio = 58.4
        self.currentRatio = 142.0
        self.fcf = 9000
        self.revenueGrowth3Y = 7.5
        self.netMargin = 14.4
        self.equityRatio = 63.1
        self.netDebt = -1200
        self.netDebtRatio = -3.2
        self.roic = 12.5
        self.interestCoverage = 8.3
        self.piotroskiFScore = 7
        self.altmanZScore = 3.45
        self.warnings = []


class FakeCompany:
    def __init__(self):
        self.corpName = "테스트기업"
        self.stockCode = "000000"
        self.ratios = pl.DataFrame(
            {
                "분류": ["수익성"],
                "항목": ["ROE"],
                "2024Q4": [11.2],
            }
        )
        self.ratioSeries = (
            {
                "RATIO": {
                    "roe": [8.2, 9.4, 11.2],
                    "operatingMargin": [11.0, 13.4, 16.8],
                    "debtRatio": [71.0, 64.2, 58.4],
                }
            },
            ["2022Q4", "2023Q4", "2024Q4"],
        )
        self.annual = None
        self.sector = SimpleNamespace(sector=None)

    def getRatios(self):
        return FakeRatioResult()


def test_build_tool_runtime_registers_capability_metadata():
    build_tool_runtime(None, name="capability-test")
    specs = get_capability_specs()
    by_id = {spec.id: spec for spec in specs}

    assert "execute_code" in by_id
    assert by_id["execute_code"].kind == CapabilityKind.WORKFLOW
    assert "create_plugin" in by_id
    assert by_id["create_plugin"].kind == CapabilityKind.WORKFLOW


def test_build_spec_includes_capability_summary():
    build_tool_runtime(object(), name="capability-spec")
    spec = buildSpec(depth="summary")

    assert "capabilities" in spec
    assert spec["capabilities"]["summary"]["total"] > 0
    assert "workflow" in spec["capabilities"]["summary"]["byKind"]


def test_ratio_adapter_prefers_get_ratios_over_dataframe_surface():
    company = FakeCompany()

    ratios = get_headline_ratios(company)
    ratio_series = get_ratio_series(company)
    context_text, included = build_context_skeleton(company)

    assert ratios is not None
    assert ratios.roe == 11.2
    assert ratio_series is not None
    assert ratio_series.roe[-1] == 11.2
    assert "ROE: 11.2%" in context_text
    assert "ratios" in included


def test_event_kind_exposes_canonical_ui_action_only():
    assert EventKind.UI_ACTION == "ui_action"


def test_ui_action_render_widget_embeds_view_spec():
    action = UiAction.render_widget(
        "chart",
        {"spec": {"chartType": "bar"}},
        title="매출 추이",
    )
    payload = action.to_payload()

    assert payload["action"] == "render"
    assert payload["view"]["widgets"][0]["widget"] == "chart"
    assert payload["view"]["widgets"][0]["title"] == "매출 추이"
    assert payload["view"]["widgets"][0]["props"]["spec"]["chartType"] == "bar"


def test_ui_action_render_comparison_widget_embeds_view_spec():
    payload = UiAction.render_widget(
        "comparison",
        {"stockCode": "005930", "topics": ["BS"]},
        title="기간 비교",
    ).to_payload()

    assert payload["action"] == "render"
    assert payload["view"]["widgets"][0]["widget"] == "comparison"
