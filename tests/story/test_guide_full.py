"""guide 패키지 단위 테스트 — desk, messaging, hints, capabilities, readiness.

외부 API/데이터 의존 없음. mock/합성 데이터 전용.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit


# ── 1. readiness — 삭제됨 (Phase 20: readiness.py 제거) ──

# ── 2. messaging (emit, format, progress) ──


class TestMessaging:
    def test_format_simple_message(self):
        from dartlab.core.messaging import format

        text = format("download:start", stockCode="005930", label="DART 공시 문서 데이터")
        assert "005930" in text
        assert "자동 다운로드" in text

    def test_format_done_message(self):
        from dartlab.core.messaging import format

        text = format("download:done", label="finance", sizeStr="12MB")
        assert "완료" in text
        assert "12MB" in text

    def test_format_structured_message(self):
        from dartlab.core.messaging import format

        text = format("error:no_data", stockCode="005930")
        assert "005930" in text
        assert "찾을 수 없습니다" in text

    def test_emit_prints_hint(self, capsys, caplog):
        """emit() 는 logger 경유 — stdout 깨끗, 메시지는 caplog 로 캡처."""
        import logging

        from dartlab.core.messaging import emit

        with caplog.at_level(logging.INFO, logger="dartlab.core.messaging"):
            emit("hint:no_finance", stockCode="005930", prop="BS")
        captured = capsys.readouterr()
        # A1: emit() 는 logger.info 경유 → stdout 오염 금지.
        assert captured.out == ""
        assert "[dartlab]" in caplog.text
        assert "005930" in caplog.text

    def test_emit_raises_when_requested(self):
        from dartlab.core.messaging import emit

        with pytest.raises(ValueError, match="005930"):
            emit("error:no_data", stockCode="005930", raiseAs=ValueError)

    def test_progress_silent_when_not_verbose(self, capsys):
        from dartlab.core.messaging import progress
        from dartlab.core.messagingContext import ctx

        # Ensure verbose is off
        original = ctx._verbose
        ctx._verbose = False
        try:
            progress("테스트 메시지")
            captured = capsys.readouterr()
            # stdout/stderr 모두 조용해야 함
            assert captured.out == ""
            assert captured.err == ""
        finally:
            ctx._verbose = original

    def test_context_reset(self):
        from dartlab.core.messagingContext import ctx

        ctx._dart_key = True
        ctx._verbose = True
        ctx.reset()
        assert ctx._dart_key is None
        assert ctx._verbose is None


# ── 3. hints (onCompanyCreated, nextSteps, onAnalysisRequested) ──


class TestHints:
    def test_on_company_created_no_hints(self):
        from dartlab.core.messagingHandlers import onCompanyCreated

        company = MagicMock()
        company._hasPanel = True
        company._hasFinanceParquet = True
        company._hasReport = True
        company.stockCode = "005930"
        company._freshnessResult = None

        hints = onCompanyCreated(company)
        assert hints == []

    def test_on_company_created_missing_finance(self):
        from dartlab.core.messagingHandlers import onCompanyCreated

        company = MagicMock()
        company._hasPanel = True
        company._hasFinanceParquet = False
        company._hasReport = True
        company.stockCode = "005930"
        company._freshnessResult = None

        hints = onCompanyCreated(company)
        assert any("finance" in h for h in hints)

    def test_on_company_created_stale_data(self):
        from dartlab.core.messagingHandlers import onCompanyCreated

        company = MagicMock()
        company._hasPanel = True
        company._hasFinanceParquet = True
        company._hasReport = True
        company.stockCode = "005930"

        freshness = MagicMock()
        freshness.ageInDays = 120
        company._freshnessResult = freshness

        hints = onCompanyCreated(company)
        assert any("120일" in h for h in hints)

    def test_next_steps_with_finance(self):
        from dartlab.core.messagingHandlers import nextSteps

        company = MagicMock()
        company._hasFinanceParquet = True
        company._hasPanel = True

        steps = nextSteps(company)
        assert any("BS" in s for s in steps)
        assert any("panel" in s for s in steps)

    def test_next_steps_without_finance(self):
        from dartlab.core.messagingHandlers import nextSteps

        company = MagicMock()
        company._hasFinanceParquet = False
        company._hasPanel = True

        steps = nextSteps(company)
        # No BS/IS/CF/ratios steps
        assert not any("c.BS" in s for s in steps)
        assert any("panel" in s for s in steps)

    def test_on_analysis_requested_with_axis(self):
        from dartlab.core.messagingHandlers import onAnalysisRequested

        result = onAnalysisRequested("수익성")
        assert result is None

    def test_on_analysis_requested_without_axis(self):
        from dartlab.core.messagingHandlers import onAnalysisRequested

        result = onAnalysisRequested(None)
        assert result is not None
        assert "수익구조" in result


# ── 4. capabilities (CapabilityKind, WidgetSpec, ViewSpec, UiAction) ──


class TestCapabilities:
    def test_capability_kind_constants(self):
        from dartlab.reference.capability.registry import CapabilityKind

        assert CapabilityKind.DATA == "data"
        assert CapabilityKind.ANALYSIS == "analysis"
        assert CapabilityKind.WORKFLOW == "workflow"

    def test_widget_spec_to_payload(self):
        from dartlab.reference.capability.registry import WidgetSpec

        ws = WidgetSpec(widget="chart", props={"type": "line"}, key="c1", title="매출")
        payload = ws.toPayload()
        assert payload["widget"] == "chart"
        assert payload["props"]["type"] == "line"
        assert payload["key"] == "c1"
        assert payload["title"] == "매출"

    def test_widget_spec_minimal(self):
        from dartlab.reference.capability.registry import WidgetSpec

        ws = WidgetSpec(widget="table")
        payload = ws.toPayload()
        assert "key" not in payload
        assert payload["widget"] == "table"

    def test_view_spec_to_payload(self):
        from dartlab.reference.capability.registry import ViewSpec, WidgetSpec

        vs = ViewSpec(
            layout="grid",
            widgets=[WidgetSpec(widget="chart")],
            title="테스트",
        )
        payload = vs.toPayload()
        assert payload["layout"] == "grid"
        assert len(payload["widgets"]) == 1
        assert payload["title"] == "테스트"

    def test_view_spec_single_widget(self):
        from dartlab.reference.capability.registry import ViewSpec

        vs = ViewSpec.singleWidget("table", {"data": []}, key="t1", viewTitle="뷰")
        payload = vs.toPayload()
        assert len(payload["widgets"]) == 1
        assert payload["widgets"][0]["widget"] == "table"
        assert payload["title"] == "뷰"

    def test_ui_action_navigate(self):
        from dartlab.reference.capability.registry import UiAction

        action = UiAction.navigate(view="viewer", topic="IS", period="2023")
        payload = action.toPayload()
        assert payload["action"] == "navigate"
        assert payload["view"] == "viewer"
        assert payload["topic"] == "IS"

    def test_ui_action_toast(self):
        from dartlab.reference.capability.registry import UiAction

        action = UiAction.toast("테스트 알림", level="warning")
        payload = action.toPayload()
        assert payload["action"] == "toast"
        assert payload["message"] == "테스트 알림"
        assert payload["level"] == "warning"

    def test_ui_action_select_company(self):
        from dartlab.reference.capability.registry import UiAction

        action = UiAction.selectCompany("005930", "삼성전자", "KOSPI")
        payload = action.toPayload()
        assert payload["action"] == "select_company"
        assert payload["stockCode"] == "005930"
        assert payload["corpName"] == "삼성전자"

    def test_ui_action_layout(self):
        from dartlab.reference.capability.registry import UiAction

        action = UiAction.layout("sidebar", "open")
        payload = action.toPayload()
        assert payload["action"] == "layout"
        assert payload["target"] == "sidebar"

    def test_capability_spec_to_dict(self):
        from dartlab.reference.capability.registry import CapabilitySpec

        spec = CapabilitySpec(
            id="test",
            label="테스트",
            description="테스트 설명",
            input_schema={"type": "object"},
        )
        d = spec.toDict()
        assert d["id"] == "test"
        assert d["label"] == "테스트"

    def test_build_capability_summary(self):
        from dartlab.reference.capability.registry import CapabilitySpec, buildCapabilitySummary

        specs = [
            CapabilitySpec(id="a", label="A", description="", input_schema={}, kind="data"),
            CapabilitySpec(id="b", label="B", description="", input_schema={}, kind="analysis"),
        ]
        summary = buildCapabilitySummary(specs)
        assert summary["total"] == 2
        assert summary["byKind"]["data"] == 1
        assert summary["byKind"]["analysis"] == 1


# ── 5. capability search (capabilities() 의 search 모드) ──
#
# 옛 GuideDesk.whatCanIDo 는 dartlab.capabilities(search=...) 으로 흡수됨.


class TestCapabilitySearch:
    def test_search_returns_dict(self):
        import dartlab

        result = dartlab.capabilities(search="재무 분석")
        assert isinstance(result, dict)
