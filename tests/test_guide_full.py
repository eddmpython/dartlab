"""guide 패키지 단위 테스트 — desk, messaging, hints, capabilities, readiness.

외부 API/데이터 의존 없음. mock/합성 데이터 전용.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


# ── 1. readiness (ReadinessResult, ReadyStatus) ──


class TestReadiness:
    def test_ready_status_ok(self):
        from dartlab.guide.readiness import ReadinessResult, ReadyStatus

        result = ReadinessResult(feature="test", status=ReadyStatus.READY)
        assert result.ok is True

    def test_partial_is_ok(self):
        from dartlab.guide.readiness import ReadinessResult, ReadyStatus

        result = ReadinessResult(feature="test", status=ReadyStatus.PARTIAL)
        assert result.ok is True

    def test_not_ready_is_not_ok(self):
        from dartlab.guide.readiness import ReadinessIssue, ReadinessResult, ReadyStatus

        issue = ReadinessIssue(
            kind="missing_data",
            message="finance 데이터 없음",
            fixAction="dartlab.downloadAll('finance')",
        )
        result = ReadinessResult(
            feature="finance",
            status=ReadyStatus.NOT_READY,
            issues=[issue],
        )
        assert result.ok is False

    def test_guide_text_for_not_ready(self):
        from dartlab.guide.readiness import ReadinessIssue, ReadinessResult, ReadyStatus

        issue = ReadinessIssue(
            kind="missing",
            message="데이터 없음",
            fixAction="collect 실행",
        )
        result = ReadinessResult(
            feature="data",
            status=ReadyStatus.NOT_READY,
            issues=[issue],
        )
        text = result.guideText()
        assert "[data]" in text
        assert "사용 불가" in text
        assert "데이터 없음" in text
        assert "collect 실행" in text

    def test_guide_text_for_ready(self):
        from dartlab.guide.readiness import ReadinessResult, ReadyStatus

        result = ReadinessResult(feature="ai", status=ReadyStatus.READY)
        text = result.guideText()
        assert "사용 가능" in text

    def test_unknown_status_is_not_ok(self):
        from dartlab.guide.readiness import ReadinessResult, ReadyStatus

        result = ReadinessResult(feature="x", status=ReadyStatus.UNKNOWN)
        assert result.ok is False

    def test_list_features(self):
        from dartlab.guide.readiness import listFeatures

        features = listFeatures()
        assert isinstance(features, list)
        # Built-in checkers registered
        assert "data" in features

    def test_get_checker_returns_callable(self):
        from dartlab.guide.readiness import getChecker

        checker = getChecker("data")
        assert checker is not None
        assert callable(checker)

    def test_get_checker_returns_none_for_unknown(self):
        from dartlab.guide.readiness import getChecker

        assert getChecker("nonexistent_feature_xyz") is None


# ── 2. messaging (emit, format, progress) ──


class TestMessaging:
    def test_format_simple_message(self):
        from dartlab.guide.messaging import format

        text = format("download:start", stockCode="005930", label="DART 공시 문서 데이터")
        assert "005930" in text
        assert "자동 다운로드" in text

    def test_format_done_message(self):
        from dartlab.guide.messaging import format

        text = format("download:done", label="finance", sizeStr="12MB")
        assert "완료" in text
        assert "12MB" in text

    def test_format_structured_message(self):
        from dartlab.guide.messaging import format

        text = format("error:no_data", stockCode="005930")
        assert "005930" in text
        assert "찾을 수 없습니다" in text

    def test_emit_prints_hint(self, capsys):
        from dartlab.guide.messaging import emit

        emit("hint:no_finance", stockCode="005930", prop="BS")
        captured = capsys.readouterr()
        assert "[dartlab]" in captured.out
        assert "005930" in captured.out

    def test_emit_raises_when_requested(self):
        from dartlab.guide.messaging import emit

        with pytest.raises(ValueError, match="005930"):
            emit("error:no_data", stockCode="005930", raise_as=ValueError)

    def test_progress_silent_when_not_verbose(self, capsys):
        from dartlab.guide.messaging import _ctx, progress

        # Ensure verbose is off
        original = _ctx._verbose
        _ctx._verbose = False
        try:
            progress("테스트 메시지")
            captured = capsys.readouterr()
            assert captured.out == ""
        finally:
            _ctx._verbose = original

    def test_context_reset(self):
        from dartlab.guide.messaging import _ctx

        _ctx._dart_key = True
        _ctx._verbose = True
        _ctx.reset()
        assert _ctx._dart_key is None
        assert _ctx._verbose is None


# ── 3. hints (onCompanyCreated, nextSteps, onAnalysisRequested) ──


class TestHints:
    def test_on_company_created_no_hints(self):
        from dartlab.guide.hints import onCompanyCreated

        company = MagicMock()
        company._hasDocs = True
        company._hasFinanceParquet = True
        company._hasReport = True
        company.stockCode = "005930"
        company._freshnessResult = None

        hints = onCompanyCreated(company)
        assert hints == []

    def test_on_company_created_missing_finance(self):
        from dartlab.guide.hints import onCompanyCreated

        company = MagicMock()
        company._hasDocs = True
        company._hasFinanceParquet = False
        company._hasReport = True
        company.stockCode = "005930"
        company._freshnessResult = None

        hints = onCompanyCreated(company)
        assert any("finance" in h for h in hints)

    def test_on_company_created_stale_data(self):
        from dartlab.guide.hints import onCompanyCreated

        company = MagicMock()
        company._hasDocs = True
        company._hasFinanceParquet = True
        company._hasReport = True
        company.stockCode = "005930"

        freshness = MagicMock()
        freshness.ageInDays = 120
        company._freshnessResult = freshness

        hints = onCompanyCreated(company)
        assert any("120일" in h for h in hints)

    def test_next_steps_with_finance(self):
        from dartlab.guide.hints import nextSteps

        company = MagicMock()
        company._hasFinanceParquet = True
        company._hasDocs = True

        steps = nextSteps(company)
        assert any("BS" in s for s in steps)
        assert any("show" in s for s in steps)

    def test_next_steps_without_finance(self):
        from dartlab.guide.hints import nextSteps

        company = MagicMock()
        company._hasFinanceParquet = False
        company._hasDocs = True

        steps = nextSteps(company)
        # No BS/IS/CF/ratios steps
        assert not any("c.BS" in s for s in steps)
        assert any("show" in s for s in steps)

    def test_on_analysis_requested_with_axis(self):
        from dartlab.guide.hints import onAnalysisRequested

        result = onAnalysisRequested("수익성")
        assert result is None

    def test_on_analysis_requested_without_axis(self):
        from dartlab.guide.hints import onAnalysisRequested

        result = onAnalysisRequested(None)
        assert result is not None
        assert "수익구조" in result


# ── 4. capabilities (CapabilityKind, WidgetSpec, ViewSpec, UiAction) ──


class TestCapabilities:
    def test_capability_kind_constants(self):
        from dartlab.guide.capabilities import CapabilityKind

        assert CapabilityKind.DATA == "data"
        assert CapabilityKind.ANALYSIS == "analysis"
        assert CapabilityKind.WORKFLOW == "workflow"

    def test_widget_spec_to_payload(self):
        from dartlab.guide.capabilities import WidgetSpec

        ws = WidgetSpec(widget="chart", props={"type": "line"}, key="c1", title="매출")
        payload = ws.to_payload()
        assert payload["widget"] == "chart"
        assert payload["props"]["type"] == "line"
        assert payload["key"] == "c1"
        assert payload["title"] == "매출"

    def test_widget_spec_minimal(self):
        from dartlab.guide.capabilities import WidgetSpec

        ws = WidgetSpec(widget="table")
        payload = ws.to_payload()
        assert "key" not in payload
        assert payload["widget"] == "table"

    def test_view_spec_to_payload(self):
        from dartlab.guide.capabilities import ViewSpec, WidgetSpec

        vs = ViewSpec(
            layout="grid",
            widgets=[WidgetSpec(widget="chart")],
            title="테스트",
        )
        payload = vs.to_payload()
        assert payload["layout"] == "grid"
        assert len(payload["widgets"]) == 1
        assert payload["title"] == "테스트"

    def test_view_spec_single_widget(self):
        from dartlab.guide.capabilities import ViewSpec

        vs = ViewSpec.single_widget("table", {"data": []}, key="t1", view_title="뷰")
        payload = vs.to_payload()
        assert len(payload["widgets"]) == 1
        assert payload["widgets"][0]["widget"] == "table"
        assert payload["title"] == "뷰"

    def test_ui_action_navigate(self):
        from dartlab.guide.capabilities import UiAction

        action = UiAction.navigate(view="viewer", topic="IS", period="2023")
        payload = action.to_payload()
        assert payload["action"] == "navigate"
        assert payload["view"] == "viewer"
        assert payload["topic"] == "IS"

    def test_ui_action_toast(self):
        from dartlab.guide.capabilities import UiAction

        action = UiAction.toast("테스트 알림", level="warning")
        payload = action.to_payload()
        assert payload["action"] == "toast"
        assert payload["message"] == "테스트 알림"
        assert payload["level"] == "warning"

    def test_ui_action_select_company(self):
        from dartlab.guide.capabilities import UiAction

        action = UiAction.select_company("005930", "삼성전자", "KOSPI")
        payload = action.to_payload()
        assert payload["action"] == "select_company"
        assert payload["stockCode"] == "005930"
        assert payload["corpName"] == "삼성전자"

    def test_ui_action_layout(self):
        from dartlab.guide.capabilities import UiAction

        action = UiAction.layout("sidebar", "open")
        payload = action.to_payload()
        assert payload["action"] == "layout"
        assert payload["target"] == "sidebar"

    def test_capability_spec_to_dict(self):
        from dartlab.guide.capabilities import CapabilitySpec

        spec = CapabilitySpec(
            id="test",
            label="테스트",
            description="테스트 설명",
            input_schema={"type": "object"},
        )
        d = spec.to_dict()
        assert d["id"] == "test"
        assert d["label"] == "테스트"

    def test_build_capability_summary(self):
        from dartlab.guide.capabilities import CapabilitySpec, build_capability_summary

        specs = [
            CapabilitySpec(id="a", label="A", description="", input_schema={}, kind="data"),
            CapabilitySpec(id="b", label="B", description="", input_schema={}, kind="analysis"),
        ]
        summary = build_capability_summary(specs)
        assert summary["total"] == 2
        assert summary["byKind"]["data"] == 1
        assert summary["byKind"]["analysis"] == 1


# ── 5. desk (GuideDesk) ──


class TestGuideDesk:
    def test_check_ready_unknown_feature(self):
        from dartlab.guide.desk import GuideDesk
        from dartlab.guide.readiness import ReadyStatus

        desk = GuideDesk()
        result = desk.checkReady("nonexistent_feature_xyz")
        assert result.status == ReadyStatus.UNKNOWN

    def test_check_ready_all(self):
        from dartlab.guide.desk import GuideDesk

        desk = GuideDesk()
        results = desk.checkReadyAll(["data", "nonexistent"])
        assert "data" in results
        assert "nonexistent" in results

    def test_require_raises_on_not_ready(self):
        from dartlab.guide.desk import GuideDesk

        desk = GuideDesk()
        # "data" checker exists; with no data dir, it should fail
        # but we just test the plumbing -- if it doesn't raise, it means ready
        # We mock instead
        with patch.object(desk, "checkReady") as mock_check:
            from dartlab.guide.readiness import ReadinessIssue, ReadinessResult, ReadyStatus

            mock_check.return_value = ReadinessResult(
                feature="test",
                status=ReadyStatus.NOT_READY,
                issues=[ReadinessIssue(kind="x", message="msg", fixAction="fix")],
            )
            with pytest.raises(RuntimeError, match="사용 불가"):
                desk.require("test")

    def test_what_can_i_do_with_question(self):
        from dartlab.guide.desk import GuideDesk

        desk = GuideDesk()
        result = desk.whatCanIDo("재무 분석")
        assert isinstance(result, str)
