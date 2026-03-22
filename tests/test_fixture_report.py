"""CI용 fixture 기반 report 파서 테스트.

tests/fixtures/005930.report.parquet 사용.
로컬 데이터 불필요 — CI에서 항상 실행.
"""

from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_REPORT = FIXTURE_DIR / "005930.report.parquet"


@pytest.fixture
def reportDf():
    return pl.read_parquet(FIXTURE_REPORT)


def _patchLoadData(reportDf):
    return patch(
        "dartlab.core.dataLoader.loadData",
        return_value=reportDf,
    )


class TestReportStructure:
    def test_fixtureLoads(self, reportDf):
        assert reportDf.height > 0
        assert "apiType" in reportDf.columns

    def test_hasKeyApiTypes(self, reportDf):
        types = reportDf["apiType"].unique().to_list()
        assert "dividend" in types
        assert "employee" in types
        assert "majorHolder" in types


class TestReportPivots:
    def test_pivotDividend(self, reportDf):
        from dartlab.engines.company.dart.report import pivotDividend

        with _patchLoadData(reportDf):
            result = pivotDividend("005930")
        if result is None:
            pytest.skip("배당 데이터 부족")
        assert hasattr(result, "years")
        assert hasattr(result, "dps")
        assert len(result.years) > 0

    def test_pivotEmployee(self, reportDf):
        from dartlab.engines.company.dart.report import pivotEmployee

        with _patchLoadData(reportDf):
            result = pivotEmployee("005930")
        if result is None:
            pytest.skip("직원 데이터 부족")
        assert hasattr(result, "years")
        assert hasattr(result, "totalEmployee")

    def test_pivotMajorHolder(self, reportDf):
        from dartlab.engines.company.dart.report import pivotMajorHolder

        with _patchLoadData(reportDf):
            result = pivotMajorHolder("005930")
        if result is None:
            pytest.skip("최대주주 데이터 부족")
        assert hasattr(result, "years")
        assert hasattr(result, "totalShareRatio")

    def test_pivotAudit(self, reportDf):
        from dartlab.engines.company.dart.report import pivotAudit

        with _patchLoadData(reportDf):
            result = pivotAudit("005930")
        if result is None:
            pytest.skip("감사 데이터 부족")
        assert hasattr(result, "years")
        assert hasattr(result, "opinions")
