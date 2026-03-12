"""Company 클래스 기본 테스트."""

import polars as pl
import pytest

from tests.conftest import SAMSUNG, requires_samsung


@requires_samsung
class TestCompany:
    def test_init_by_code(self):
        from dartlab import Company
        c = Company(SAMSUNG)
        assert c.stockCode == SAMSUNG
        assert c.corpName == "삼성전자"

    def test_repr(self):
        import dartlab
        dartlab.verbose = False
        c = dartlab.Company(SAMSUNG)
        assert "005930" in repr(c)
        assert "삼성전자" in repr(c)
        dartlab.verbose = True

    def test_filings(self):
        from dartlab import Company
        c = Company(SAMSUNG)
        filings = c.filings()
        assert isinstance(filings, pl.DataFrame)
        assert len(filings) > 0
        assert "dartUrl" in filings.columns

    def test_invalid_name_raises(self):
        from dartlab import Company
        with pytest.raises(ValueError):
            Company("존재하지않는회사명zzz")

    def test_source_namespaces(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert c.docs is not None
        assert c.finance is not None
        assert c.report is not None
        assert c.index is not None
        assert c.profile is not None
        assert isinstance(c.index, pl.DataFrame)
        assert len(c.report.apiTypes) == 28

    def test_profile_sections_matches_company_sections(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert c.sections is not None
        assert c.profile.sections is not None
        assert c.sections.shape == c.profile.sections.shape

    def test_first_layer_dataframe_contracts(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert isinstance(c.filings(), pl.DataFrame)
        assert isinstance(c.docs.sections, pl.DataFrame)
        assert isinstance(c.profile.sections, pl.DataFrame)
        assert isinstance(c.sources, pl.DataFrame)
        assert isinstance(c.finance.BS, pl.DataFrame)
        assert isinstance(c.finance.IS, pl.DataFrame)
        assert isinstance(c.finance.CIS, pl.DataFrame)
        assert isinstance(c.finance.CF, pl.DataFrame)
        assert isinstance(c.finance.SCE, pl.DataFrame)

    def test_profile_facts_include_docs_source(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        facts = c.profile.facts
        assert facts is not None
        assert "source" in facts.columns
        assert "docs" in set(facts["source"].unique().to_list())

    def test_profile_trace_for_docs_topic(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        traced = c.profile.trace("riskDerivative")
        assert traced is not None
        assert traced["primarySource"] == "docs"

    def test_finance_cis_and_sce_are_exposed(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert isinstance(c.finance.CIS, pl.DataFrame)
        assert isinstance(c.CIS, pl.DataFrame)
        assert isinstance(c.finance.SCE, pl.DataFrame)
        assert isinstance(c.SCE, pl.DataFrame)

    def test_profile_sections_include_finance_and_report_topics(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        sections = c.profile.sections
        assert sections is not None
        topics = sections["topic"].to_list()
        for topic in ["BS", "IS", "CIS", "CF", "SCE", "dividend", "employee", "majorHolder", "audit"]:
            assert topic in topics

    def test_profile_sections_hide_raw_source_topics(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        sections = c.profile.sections
        assert sections is not None
        topics = set(sections["topic"].to_list())
        assert "주요제품및원재료등" not in topics
        assert "파생상품등에관한사항" not in topics
        assert "I.회사의개황" not in topics

    def test_profile_trace_for_finance_and_report_topics(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert c.profile.trace("dividend")["primarySource"] == "report"
        assert c.profile.trace("BS")["primarySource"] == "finance"
        assert c.profile.trace("CIS")["primarySource"] == "finance"

    def test_board_and_profile_are_ordered_topic_views(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert c.index.height > 0
        assert len(c.profile) > 0
        assert set(["chapter", "topic", "kind", "source", "periods", "shape", "preview"]).issubset(set(c.index.columns))
        firstProfileChapter = next(iter(c.profile.values()))
        assert len(firstProfileChapter) > 0
        assert isinstance(next(iter(firstProfileChapter.values())), pl.DataFrame)

    def test_open_and_topics_surface_company_payloads(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert "BS" in c.topics
        assert isinstance(c.show("BS"), pl.DataFrame)
        assert isinstance(c.show("BS", raw=True), pl.DataFrame)
        assert isinstance(c.show("dividend"), pl.DataFrame)
        assert isinstance(c.show("riskDerivative", raw=False), pl.DataFrame)

    def test_public_index_show_trace_surface(self):
        import dartlab

        c = dartlab.Company(SAMSUNG)
        assert isinstance(c.index, pl.DataFrame)
        assert c.index.height > 0
        assert isinstance(c.show("companyOverview"), pl.DataFrame)
        traced = c.trace("dividend")
        assert traced is not None
        assert traced["primarySource"] == "report"
