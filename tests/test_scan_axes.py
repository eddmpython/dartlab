"""scan 축 (company 4축 + market network) import + 기본 구조 테스트."""

from __future__ import annotations

import polars as pl
import pytest

from tests.conftest import requires_report

pytestmark = pytest.mark.integration

# ── import 테스트 (데이터 불필요) ─────────────────────────────


def test_available_scans():
    from dartlab.scan import available_scans

    scans = available_scans()
    assert isinstance(scans, list)
    assert set(scans) >= {"network", "governance", "workforce", "capital", "debt"}


def test_governance_imports():
    from dartlab.scan.governance import scan_governance
    from dartlab.scan.governance.scorer import grade, score_ownership

    assert callable(scan_governance)
    assert grade(90) == "A"
    assert grade(75) == "B"
    assert grade(60) == "C"
    assert grade(45) == "D"
    assert grade(30) == "E"
    assert score_ownership(40) == 20


def test_capital_imports():
    from dartlab.scan.capital import scan_capital
    from dartlab.scan.capital.classifier import classify_return

    assert callable(scan_capital)
    cat, contra = classify_return(True, True, False)
    assert cat == "적극환원"
    assert contra is False
    cat2, contra2 = classify_return(True, False, True)
    assert cat2 == "중립"
    assert contra2 is True


def test_workforce_imports():
    from dartlab.scan.workforce import scan_workforce

    assert callable(scan_workforce)


def test_debt_imports():
    from dartlab.scan.debt import scan_debt
    from dartlab.scan.debt.risk import classify_risk

    assert callable(scan_debt)
    assert classify_risk(0.5, 60) == "고위험"
    assert classify_risk(0.5, 30) == "주의"
    assert classify_risk(2, 60) == "주의"
    assert classify_risk(5, 30) == "안전"
    assert classify_risk(2, 30) == "관찰"
    assert classify_risk(None, 60) == "주의"
    assert classify_risk(None, 30) == "관찰"


def test_helpers_parse_num():
    from dartlab.scan._helpers import parse_num

    assert parse_num("1,234") == 1234.0
    assert parse_num("-") is None
    assert parse_num("") is None
    assert parse_num(None) is None
    assert parse_num(42) == 42.0
    assert parse_num("3.14") == pytest.approx(3.14)


# ── 데이터 의존 테스트 ────────────────────────────────────


@requires_report
class TestWithData:
    """report 데이터가 있을 때만 실행되는 테스트."""

    def test_market_view_has_no_blank_market_label(self):
        import dartlab

        c = dartlab.Company("005930")
        df = c.governance("market")

        assert df is not None
        assert "시장" in df.columns
        assert df.filter(pl.col("시장").is_null() | (pl.col("시장") == "")).is_empty()


# ── scan 통합 테스트 (spec + tool + pipeline) ────────────────


def test_scan_spec_registered():
    """scan spec이 AI 엔진 총괄에 등록되어 있는지."""
    from dartlab.ai.spec import buildSpec

    spec = buildSpec()
    assert "dart.scan" in spec["engines"]
    summary = spec["engines"]["dart.scan"]["summary"]
    assert "governance" in summary
    assert "workforce" in summary
    assert "capital" in summary
    assert "debt" in summary


@requires_report
def test_scan_tool_registered_with_company():
    """Company가 있을 때 get_scan_data tool이 등록되는지."""
    import dartlab
    from dartlab.ai.tools.registry import register_defaults

    c = dartlab.Company("005930")
    rt = register_defaults(c)
    names = [s["function"]["name"] for s in rt.get_tool_schemas()]
    assert "get_scan_data" in names


def test_scan_tool_not_registered_without_company():
    """Company가 없을 때 get_scan_data tool이 없는지."""
    from dartlab.ai.tools.registry import register_defaults

    rt = register_defaults(None)
    names = [s["function"]["name"] for s in rt.get_tool_schemas()]
    assert "get_scan_data" not in names


def test_pipeline_classify_governance():
    """거버넌스 질문이 '지배구조'로 분류되는지."""
    from dartlab.ai.runtime.pipeline import classify_question

    assert classify_question("이 회사의 거버넌스는 어때?") == "지배구조"
    assert classify_question("지배구조 현황을 알려줘") == "지배구조"


def test_pipeline_scan_axes_mapping():
    """질문 유형별 scan 축 매핑이 정의되어 있는지."""
    from dartlab.ai.runtime.pipeline import _SCAN_AXES_BY_QTYPE

    assert "지배구조" in _SCAN_AXES_BY_QTYPE
    assert "governance" in _SCAN_AXES_BY_QTYPE["지배구조"]
    assert "리스크" in _SCAN_AXES_BY_QTYPE
    assert "debt" in _SCAN_AXES_BY_QTYPE["리스크"]


@requires_report
class TestScanIntegration:
    """scan 통합 테스트 — 데이터 필요."""

    @classmethod
    def setup_class(cls):
        import dartlab

        cls.c = dartlab.Company("005930")

    def test_scan_tool_execution(self):
        """get_scan_data tool이 실제로 결과를 반환하는지."""
        from dartlab.ai.tools.registry import register_defaults

        rt = register_defaults(self.c)
        result = rt.execute_tool("get_scan_data", {"axis": "governance"})
        assert "종목코드" in result
        assert "005930" in result

    def test_pipeline_scan_injection(self):
        """pipeline이 지배구조 질문에 scan context를 주입하는지."""
        from dartlab.ai.runtime.pipeline import _run_scan

        result = _run_scan(self.c, "지배구조")
        assert result is not None
        assert "지배구조 스캔" in result

    def test_scan_all_axes(self):
        """get_scan_data(axis='all')이 4축 모두 반환하는지."""
        from dartlab.ai.tools.registry import register_defaults

        rt = register_defaults(self.c)
        result = rt.execute_tool("get_scan_data", {"axis": "all"})
        for key in ("governance", "workforce", "capital", "debt"):
            assert key in result
