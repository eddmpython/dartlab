"""Company 클래스 기본 테스트."""

import polars as pl
import pytest

from tests.conftest import SAMSUNG, requires_samsung


def _topicBlocksFrame(topic: str, rows: list[dict[str, object]]) -> pl.DataFrame:
    records: list[dict[str, object]] = []
    for idx, row in enumerate(rows):
        records.append(
            {
                "stockCode": "TEST",
                "period": row["period"],
                "periodOrder": row["periodOrder"],
                "sectionOrder": row.get("sectionOrder", 1),
                "rawTitle": row.get("rawTitle", topic),
                "topic": topic,
                "sourceTopic": row.get("sourceTopic", topic),
                "cellKey": f"TEST:{row['period']}:{topic}",
                "blockIdx": idx,
                "blockType": row.get("blockType", "text"),
                "blockLabel": row.get("blockLabel", "(root)"),
                "blockText": row.get("blockText", ""),
                "chars": len(str(row.get("blockText", ""))),
                "tableLines": row.get("tableLines", 0),
                "semanticTopic": row.get("semanticTopic"),
                "detailTopic": row.get("detailTopic"),
                "isBoilerplate": False,
                "isPlaceholder": row.get("isPlaceholder", False),
                "blockPriority": row.get("blockPriority", 3),
            }
        )
    return pl.DataFrame(records, strict=False)


class TestProfileChangeLedgerHelpers:
    def test_change_point_collapses_repeated_periods(self):
        from dartlab.engines.dart.company import _buildTopicChangeLedger

        blocks = _topicBlocksFrame(
            "companyOverview",
            [
                {"period": "2024Q1", "periodOrder": 20241, "blockText": "회사는 반도체를 생산한다."},
                {"period": "2024Q2", "periodOrder": 20242, "blockText": "회사는 반도체를 생산한다."},
                {"period": "2024Q3", "periodOrder": 20243, "blockText": "회사는 반도체와 모바일 기기를 생산한다."},
            ],
        )

        ledger = _buildTopicChangeLedger(blocks)

        assert ledger.height == 2
        assert set(ledger["period"].to_list()) == {"2024Q1", "2024Q3"}

    def test_restated_text_is_separated_from_edited_text(self):
        from dartlab.engines.dart.company import _buildTopicChangeLedger

        blocks = _topicBlocksFrame(
            "companyOverview",
            [
                {"period": "2024Q1", "periodOrder": 20241, "blockText": "회사는 반도체를 생산한다."},
                {"period": "2024Q2", "periodOrder": 20242, "blockText": "회사는 반도체를 생산한다"},
            ],
        )

        ledger = _buildTopicChangeLedger(blocks)

        assert ledger.height == 2
        latest = ledger.filter(pl.col("period") == "2024Q2")
        assert latest.item(0, "changeType") == "restated"

    def test_table_structure_change_is_not_treated_as_value_edit(self):
        from dartlab.engines.dart.company import _buildTopicChangeLedger

        blocks = _topicBlocksFrame(
            "salesOrder",
            [
                {
                    "period": "2024Q1",
                    "periodOrder": 20241,
                    "blockType": "table",
                    "blockLabel": "(root)",
                    "blockText": "| 항목 | 값 |\n| --- | --- |\n| A | 1 |\n| B | 2 |",
                    "tableLines": 4,
                },
                {
                    "period": "2024Q2",
                    "periodOrder": 20242,
                    "blockType": "table",
                    "blockLabel": "(root)",
                    "blockText": "| 항목 | 값 |\n| --- | --- |\n| A | 1 |\n| B | 2 |\n| C | 3 |",
                    "tableLines": 5,
                },
            ],
        )

        ledger = _buildTopicChangeLedger(blocks)

        latest = ledger.filter(pl.col("period") == "2024Q2")
        assert latest.item(0, "changeType") == "added"

    def test_placeholder_is_tracked_with_own_change_type(self):
        from dartlab.engines.dart.company import _buildTopicChangeLedger

        blocks = _topicBlocksFrame(
            "companyOverview",
            [
                {"period": "2024Q1", "periodOrder": 20241, "blockText": "회사는 반도체를 생산한다."},
                {
                    "period": "2024Q2",
                    "periodOrder": 20242,
                    "blockText": "기업공시서식 작성기준에 따라 분기보고서에 기재하지 않습니다.",
                    "isPlaceholder": True,
                },
            ],
        )

        ledger = _buildTopicChangeLedger(blocks)

        latest = ledger.filter(pl.col("period") == "2024Q2")
        assert latest.item(0, "changeType") == "placeholder"


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

    def test_alphanumeric_dart_codes_are_routed_and_resolved(self):
        from dartlab import Company
        from dartlab.engines.dart.company import Company as DartCompany

        c = Company("0009K0")
        assert isinstance(c, DartCompany)
        assert c.stockCode == "0009K0"
        assert DartCompany.resolve("0009K0") == "0009K0"
        payload = c.show("rawMaterial")
        assert payload is None or isinstance(payload, pl.DataFrame)

    def test_source_namespaces(self):
        from dartlab import Company
        from dartlab.engines.dart.report.types import PREFERRED_QUARTER

        c = Company(SAMSUNG)
        assert c.docs is not None
        assert c.finance is not None
        assert c.report is not None
        assert c.index is not None
        assert c.profile is not None
        assert isinstance(c.index, pl.DataFrame)
        assert len(c.report.apiTypes) == 28
        status = c.report.status()
        assert isinstance(status, pl.DataFrame)
        assert set(["apiType", "label", "preferredQuarter", "isPivot", "available"]).issubset(status.columns)
        assert (
            status.filter(pl.col("apiType") == "dividend").item(0, "preferredQuarter") == PREFERRED_QUARTER["dividend"]
        )

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
        ratioTrace = c.trace("ratios")
        assert ratioTrace["primarySource"] == "finance"
        assert ratioTrace["template"] == "general"
        assert ratioTrace["coverage"] in {"full", "partial"}
        assert ratioTrace["rowCount"] is not None
        assert ratioTrace["yearCount"] is not None

    def test_index_and_profile_accessor(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert c.index.height > 0
        assert set(["chapter", "topic", "kind", "source", "periods", "shape", "preview"]).issubset(set(c.index.columns))
        assert c.profile.sections is not None
        assert isinstance(c.profile.sections, pl.DataFrame)
        assert c.profile.facts is not None
        assert isinstance(c.profile.facts, pl.DataFrame)

    def test_profile_trace_returns_provenance(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        traced = c.profile.trace("BS")
        assert traced is not None
        assert traced["primarySource"] == "finance"
        traced_docs = c.profile.trace("companyOverview")
        assert traced_docs is not None
        assert traced_docs["primarySource"] == "docs"

    def test_open_and_topics_surface_company_payloads(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        assert "BS" in c.topics
        assert "ratios" in c.topics
        assert isinstance(c.show("BS"), pl.DataFrame)
        assert isinstance(c.show("BS", raw=True), pl.DataFrame)
        assert isinstance(c.show("ratios"), pl.DataFrame)
        assert isinstance(c.show("dividend"), pl.DataFrame)
        assert isinstance(c.show("riskDerivative", raw=False), pl.DataFrame)

    def test_sections_based_table_topics_are_exposed_as_dataframes(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        sales = c.show("salesOrder")
        risk = c.show("riskDerivative")
        raw_material = c.show("rawMaterial")
        assert isinstance(sales, pl.DataFrame)
        assert isinstance(risk, pl.DataFrame)
        assert isinstance(raw_material, pl.DataFrame)
        assert "subtopic" in sales.columns or "항목" in sales.columns
        assert "subtopic" in risk.columns or "항목" in risk.columns
        assert "subtopic" in raw_material.columns or "항목" in raw_material.columns
        # segments, costByNature는 데이터 의존적 — None일 수 있음
        segments = c.show("segments")
        cost_by_nature = c.show("costByNature")
        if segments is not None:
            assert isinstance(segments, pl.DataFrame)
        if cost_by_nature is not None:
            assert isinstance(cost_by_nature, pl.DataFrame)

    def test_sections_based_table_topics_support_raw_long_view_and_docs_subtables(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        sales_raw = c.show("salesOrder", raw=True)
        sales_docs = c.docs.subtables("salesOrder")
        risk_raw = c.docs.subtables("riskDerivative", raw=True)
        cost_docs = c.docs.subtables("costByNature")

        assert isinstance(sales_raw, pl.DataFrame)
        assert isinstance(sales_docs, pl.DataFrame)
        assert isinstance(risk_raw, pl.DataFrame)
        assert cost_docs is None or isinstance(cost_docs, pl.DataFrame)
        assert "subtopic" in sales_raw.columns
        assert "tableText" in sales_raw.columns
        assert "subtopic" in sales_docs.columns
        assert "subtopic" in risk_raw.columns

    def test_report_result_surface_is_unified(self):
        from dartlab import Company
        from dartlab.engines.dart.report.types import ReportResult

        c = Company(SAMSUNG)
        dividend = c.report.result("dividend")
        treasury = c.report.result("treasuryStock")

        assert dividend is not None
        assert hasattr(dividend, "df")
        assert isinstance(dividend.df, pl.DataFrame)

        assert treasury is None or isinstance(treasury, ReportResult)
        if treasury is not None:
            assert isinstance(treasury.df, pl.DataFrame)

    def test_index_includes_finance_ratio_series(self):
        import dartlab

        c = dartlab.Company(SAMSUNG)
        ratios = c.index.filter(pl.col("topic") == "ratios")
        assert ratios.height == 1
        assert ratios.item(0, "chapter") == "III. 재무에 관한 사항"
        assert ratios.item(0, "source") == "finance"
        assert ratios.item(0, "label") == "재무비율"

    def test_public_index_show_trace_surface(self):
        import dartlab

        c = dartlab.Company(SAMSUNG)
        assert isinstance(c.index, pl.DataFrame)
        assert c.index.height > 0
        overview = c.show("companyOverview")
        assert overview is None or isinstance(overview, pl.DataFrame)
        traced = c.trace("dividend")
        assert traced is not None
        assert traced["primarySource"] == "report"
