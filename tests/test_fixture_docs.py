"""CI용 fixture 기반 docs 파서 테스트.

tests/fixtures/005930.docs.parquet 사용.
로컬 데이터 불필요 — CI에서 항상 실행.
"""

from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.integration

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_DOCS = FIXTURE_DIR / "005930.docs.parquet"


@pytest.fixture
def docsDf():
    return pl.read_parquet(FIXTURE_DOCS)


class TestDocsStructure:
    def test_fixtureLoads(self, docsDf):
        assert docsDf.height > 0
        assert "section_title" in docsDf.columns
        assert "section_content" in docsDf.columns

    def test_hasRequiredColumns(self, docsDf):
        required = ["corp_code", "corp_name", "year", "rcept_no", "report_type", "section_title", "section_content"]
        for col in required:
            assert col in docsDf.columns, f"missing column: {col}"

    def test_corpNameConsistent(self, docsDf):
        names = docsDf["corp_name"].unique().to_list()
        assert len(names) == 1
        assert "삼성" in names[0]


class TestReportSelector:
    def test_selectReportAnnual(self, docsDf):
        from dartlab.core.reportSelector import selectReport

        result = selectReport(docsDf, "2024", "annual")
        assert result is not None
        assert result.height > 0

    def test_parsePeriodKey(self):
        from dartlab.core.reportSelector import parsePeriodKey

        assert parsePeriodKey("사업보고서 (2024.12)") == "2024Q4"
        assert parsePeriodKey("분기보고서 (2024.03)") == "2024Q1"
        assert parsePeriodKey("반기보고서 (2024.06)") == "2024Q2"
        assert parsePeriodKey("invalid") is None

    def test_extractReportYear(self):
        from dartlab.core.reportSelector import extractReportYear

        assert extractReportYear("사업보고서 (2024.12)") == 2024
        assert extractReportYear("no year") is None


class TestTableParser:
    def test_parseAmount(self):
        from dartlab.core.tableParser import parseAmount

        assert parseAmount("1,234,567") == 1234567
        assert parseAmount("△1,000") == -1000
        assert parseAmount("-") is None
        assert parseAmount("") is None

    def test_extractTables(self):
        from dartlab.core.tableParser import extractTables

        md = "| A | B |\n| --- | --- |\n| 1 | 2 |\n| 3 | 4 |"
        tables = extractTables(md)
        assert len(tables) >= 1
        assert len(tables[0]["rows"]) >= 2
