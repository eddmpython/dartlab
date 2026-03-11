"""CI용 fixture 기반 finance 파서 테스트.

tests/fixtures/005930.finance.parquet 사용.
로컬 데이터 불필요 — CI에서 항상 실행.
"""

from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_FINANCE = FIXTURE_DIR / "005930.finance.parquet"


@pytest.fixture
def financeDf():
    return pl.read_parquet(FIXTURE_FINANCE)


class TestMapperWithFixture:
    def _mapper(self):
        from dartlab.engines.dart.finance.mapper import AccountMapper
        return AccountMapper.get()

    def test_mapRevenueId(self):
        result = self._mapper().map("ifrs-full_Revenue", "매출액")
        assert result == "sales"

    def test_mapOperatingProfit(self):
        result = self._mapper().map("dart_OperatingIncomeLoss", "영업이익")
        assert result == "operating_profit"

    def test_mapAssets(self):
        result = self._mapper().map("ifrs-full_Assets", "자산총계")
        assert result == "total_assets"

    def test_mapCashflow(self):
        result = self._mapper().map(
            "ifrs-full_CashFlowsFromUsedInOperatingActivities",
            "영업활동현금흐름",
        )
        assert result == "operating_cashflow"

    def test_mapEquity(self):
        result = self._mapper().map(
            "ifrs-full_EquityAttributableToOwnersOfParent",
            "지배기업의 소유주에게 귀속되는 자본",
        )
        assert result == "owners_of_parent_equity"

    def test_unmappedReturnsNone(self):
        result = self._mapper().map("some_unknown_id_xyz", "알수없는계정")
        assert result is None


class TestPivotWithFixture:
    def test_buildTimeseriesFromDf(self, financeDf):
        from dartlab.engines.dart.finance.pivot import buildTimeseries

        with patch("dartlab.core.dataLoader.loadData", return_value=financeDf):
            result = buildTimeseries("005930")

        assert result is not None
        series, periods = result
        assert "IS" in series
        assert "BS" in series
        assert "CF" in series
        assert len(periods) > 0

    def test_timeseriesHasRevenue(self, financeDf):
        from dartlab.engines.dart.finance.pivot import buildTimeseries

        with patch("dartlab.core.dataLoader.loadData", return_value=financeDf):
            series, periods = buildTimeseries("005930")

        assert "sales" in series["IS"]
        vals = series["IS"]["sales"]
        nonNull = [v for v in vals if v is not None]
        assert len(nonNull) > 0

    def test_timeseriesHasAssets(self, financeDf):
        from dartlab.engines.dart.finance.pivot import buildTimeseries

        with patch("dartlab.core.dataLoader.loadData", return_value=financeDf):
            series, periods = buildTimeseries("005930")

        assert "total_assets" in series["BS"]

    def test_buildAnnualFromDf(self, financeDf):
        from dartlab.engines.dart.finance.pivot import buildAnnual

        with patch("dartlab.core.dataLoader.loadData", return_value=financeDf):
            result = buildAnnual("005930")

        assert result is not None
        aSeries, years = result
        assert len(years) > 0
        assert "IS" in aSeries

    def test_ratiosFromFixture(self, financeDf):
        from dartlab.engines.common.finance.ratios import calcRatios
        from dartlab.engines.dart.finance.pivot import buildAnnual

        with patch("dartlab.core.dataLoader.loadData", return_value=financeDf):
            result = buildAnnual("005930")

        assert result is not None
        aSeries, _ = result
        ratios = calcRatios(aSeries, annual=True)
        assert ratios is not None
        assert ratios.roe is not None or ratios.operatingMargin is not None


class TestExtractUtils:
    def test_getTTM(self):
        from dartlab.engines.common.finance.extract import getTTM

        series = {"IS": {"sales": [100, 200, 300, 400, 500]}}
        assert getTTM(series, "IS", "sales") == 200 + 300 + 400 + 500

    def test_getTTM_insufficientData(self):
        from dartlab.engines.common.finance.extract import getTTM

        series = {"IS": {"sales": [100, None, 300]}}
        assert getTTM(series, "IS", "sales") is None

    def test_getLatest(self):
        from dartlab.engines.common.finance.extract import getLatest

        series = {"BS": {"total_assets": [100, 200, None, 400]}}
        assert getLatest(series, "BS", "total_assets") == 400

    def test_getLatest_allNone(self):
        from dartlab.engines.common.finance.extract import getLatest

        series = {"BS": {"total_assets": [None, None]}}
        assert getLatest(series, "BS", "total_assets") is None

    def test_getAnnualValues(self):
        from dartlab.engines.common.finance.extract import getAnnualValues

        series = {"IS": {"sales": [1, 2, 3]}}
        assert getAnnualValues(series, "IS", "sales") == [1, 2, 3]

    def test_getAnnualValues_missing(self):
        from dartlab.engines.common.finance.extract import getAnnualValues

        series = {"IS": {}}
        assert getAnnualValues(series, "IS", "sales") == []

    def test_revenueGrowth3Y(self):
        from dartlab.engines.common.finance.extract import getRevenueGrowth3Y

        series = {"IS": {"sales": [100, 110, 120, 130]}}
        growth = getRevenueGrowth3Y(series)
        assert growth is not None
        assert 8 < growth < 12

    def test_revenueGrowth3Y_insufficient(self):
        from dartlab.engines.common.finance.extract import getRevenueGrowth3Y

        series = {"IS": {"sales": [100, 200]}}
        assert getRevenueGrowth3Y(series) is None
