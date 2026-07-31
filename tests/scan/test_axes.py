"""scan 축 (company 4축 + market network) import + 기본 구조 테스트."""

from __future__ import annotations

import polars as pl
import pytest

from tests.conftest import requires_report

pytestmark = pytest.mark.integration

# ── import 테스트 (데이터 불필요) ─────────────────────────────


def test_available_scans():
    from dartlab.scan import availableScans

    scans = availableScans()
    assert isinstance(scans, list)
    assert set(scans) >= {"network", "governance", "workforce", "capital", "debt"}


def test_governance_imports():
    from dartlab.scan.governance import scanGovernance
    from dartlab.scan.governance.scorer import grade, scoreOwnership

    assert callable(scanGovernance)
    assert grade(90) == "A"
    assert grade(75) == "B"
    assert grade(60) == "C"
    assert grade(45) == "D"
    assert grade(30) == "E"
    assert scoreOwnership(40) == 20


def test_capital_imports():
    from dartlab.scan.capital import scanCapital
    from dartlab.scan.capital.classifier import classifyReturn

    assert callable(scanCapital)
    cat, contra = classifyReturn(True, True, False)
    assert cat == "적극환원"
    assert contra is False
    cat2, contra2 = classifyReturn(True, False, True)
    assert cat2 == "중립"
    assert contra2 is True


def test_workforce_imports():
    from dartlab.scan.workforce import scanWorkforce

    assert callable(scanWorkforce)


def test_debt_imports():
    from dartlab.scan.debt import scanDebt
    from dartlab.scan.debt.risk import classifyRisk

    assert callable(scanDebt)
    assert classifyRisk(0.5, 60) == "고위험"
    assert classifyRisk(0.5, 30) == "주의"
    assert classifyRisk(2, 60) == "주의"
    assert classifyRisk(5, 30) == "안전"
    assert classifyRisk(2, 30) == "관찰"
    assert classifyRisk(None, 60) == "주의"
    # ICR 결측이고 단기 리파이낸싱 상향 신호도 없으면 판정하지 않는다. 예전에는 이 자리에서
    # "관찰" 을 냈는데, 그것은 측정하지 못한 것을 등급으로 바꿔 내보내는 조작이었다.
    assert classifyRisk(None, 30) == "자료부족"


def test_helpers_parse_num():
    from dartlab.scan.io.parquet import parseNumStr

    assert parseNumStr("1,234") == 1234.0
    assert parseNumStr("-") is None
    assert parseNumStr("") is None
    assert parseNumStr(None) is None
    assert parseNumStr(42) == 42.0
    assert parseNumStr("3.14") == pytest.approx(3.14)


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
