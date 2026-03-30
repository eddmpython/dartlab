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


# ── scan spec/tool 통합 테스트는 ai.spec/ai.tools.registry 제거로 삭제됨 ──
