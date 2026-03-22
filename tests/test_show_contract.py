"""show() 타입 계약 테스트 + 성능 회귀 테스트.

모든 topic에 대해 show()가 DataFrame | None만 반환하는지 검증.
"""

import time

import polars as pl

from tests.conftest import SAMSUNG, requires_samsung


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
        from dartlab.engines.company.dart.company import Company

        start = time.perf_counter()
        Company(SAMSUNG)
        assert time.perf_counter() - start < 3.0

    def test_show_bs_under_5s(self):
        from dartlab.engines.company.dart.company import Company

        c = Company(SAMSUNG)
        start = time.perf_counter()
        c.show("BS")
        assert time.perf_counter() - start < 5.0
