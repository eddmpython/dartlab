"""show() 타입 계약 테스트 + 성능 회귀 테스트.

모든 topic에 대해 show()가 DataFrame | None만 반환하는지 검증.
"""

import time

import polars as pl
import pytest

from tests.conftest import SAMSUNG, requires_samsung

pytestmark = pytest.mark.integration


@requires_samsung
class TestShowTypeContract:
    """show() → DataFrame | None 계약 검증."""

    def test_finance_topics_return_dataframe(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        for topic in ("BS", "IS", "CF", "CIS", "SCE"):
            result = c.show(topic)
            assert result is None or isinstance(result, pl.DataFrame), (
                f"show('{topic}') returned {type(result).__name__}, expected DataFrame | None"
            )

    def test_ratios_returns_dataframe(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        result = c.show("ratios")
        assert result is None or isinstance(result, pl.DataFrame)

    def test_report_topics_return_dataframe(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        for topic in ("dividend", "employee", "majorHolder", "audit"):
            result = c.show(topic)
            assert result is None or isinstance(result, pl.DataFrame), (
                f"show('{topic}') returned {type(result).__name__}, expected DataFrame | None"
            )

    def test_subtopic_topics_return_dataframe(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        for topic in ("salesOrder", "riskDerivative", "rawMaterial", "segments", "costByNature"):
            result = c.show(topic)
            assert result is None or isinstance(result, pl.DataFrame), (
                f"show('{topic}') returned {type(result).__name__}, expected DataFrame | None"
            )

    def test_docs_topics_return_dataframe(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        for topic in ("companyOverview", "businessOverview"):
            result = c.show(topic)
            assert result is None or isinstance(result, pl.DataFrame), (
                f"show('{topic}') returned {type(result).__name__}, expected DataFrame | None"
            )

    def test_nonexistent_topic_returns_none(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert c.show("completelyFakeTopicXyz") is None

    def test_all_topics_satisfy_contract(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        for topic in c.topics["topic"].to_list():
            result = c.show(topic)
            assert result is None or isinstance(result, pl.DataFrame), (
                f"show('{topic}') returned {type(result).__name__}, expected DataFrame | None"
            )


@requires_samsung
class TestPerformanceRegression:
    """성능 회귀 테스트."""

    def test_company_init_under_3s(self):
        from dartlab.providers.dart.company import Company

        start = time.perf_counter()
        Company(SAMSUNG)
        assert time.perf_counter() - start < 3.0

    def test_show_bs_under_5s(self):
        from dartlab.providers.dart.company import Company

        c = Company(SAMSUNG)
        start = time.perf_counter()
        c.show("BS")
        assert time.perf_counter() - start < 5.0


@requires_samsung
class TestSelectRegression:
    """select() 회귀 테스트 — GitHub Issue #14, #15."""

    def test_select_pretax_not_confused_with_tax(self):
        """Regression for #15: 법인세비용차감전순이익 → profit_before_tax."""
        from dartlab import Company

        c = Company("014580")
        r = c.select("IS", ["법인세비용차감전순이익"])
        assert r is not None and len(r) >= 1
        sid = r[0, "snakeId"]
        assert sid in ("profit_before_tax", "pretax_income"), (
            f"법인세비용차감전순이익 → {sid} (income_taxes면 #15 재발)"
        )

    def test_select_shortname_pretax(self):
        """Regression for #15: 줄임말 세전순이익도 profit_before_tax."""
        from dartlab import Company

        c = Company("014580")
        r = c.select("IS", ["세전순이익"])
        assert r is not None and len(r) >= 1
        sid = r[0, "snakeId"]
        assert sid in ("profit_before_tax", "pretax_income"), (
            f"세전순이익 → {sid}"
        )

    def test_select_multiple_pretax_and_tax(self):
        """Regression for #14: 복합 조회 시 세전순이익 + 법인세비용 2건 반환."""
        from dartlab import Company

        c = Company("014580")
        r = c.select("IS", ["세전순이익", "법인세비용"])
        assert r is not None, "결과가 None"
        assert len(r) == 2, f"2행 기대, {len(r)}행 반환 (#14 재발)"
        sids = set(r["snakeId"].to_list())
        assert "income_taxes" in sids, "법인세비용 누락"

    def test_select_basic_accounts_unchanged(self):
        """기본 계정 매칭이 깨지지 않았는지 검증."""
        from dartlab import Company

        c = Company(SAMSUNG)
        for name, expected_sid in [
            ("매출액", "sales"),
            ("영업이익", "operating_profit"),
            ("당기순이익", "net_profit"),
        ]:
            r = c.select("IS", [name])
            assert r is not None and len(r) >= 1, f"{name} 매칭 실패"
            assert r[0, "snakeId"] == expected_sid, (
                f"{name} → {r[0, 'snakeId']} (기대: {expected_sid})"
            )
