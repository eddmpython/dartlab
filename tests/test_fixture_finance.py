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

    def test_q1_cf_stays_standalone(self):
        from dartlab.engines.dart.finance.pivot import buildTimeseries

        df = pl.DataFrame(
            {
                "bsns_year": ["2025", "2025"],
                "reprt_nm": ["1분기", "2분기"],
                "sj_div": ["CF", "CF"],
                "account_id": [
                    "ifrs-full_CashFlowsFromUsedInOperatingActivities",
                    "ifrs-full_CashFlowsFromUsedInOperatingActivities",
                ],
                "account_nm": ["영업활동현금흐름", "영업활동현금흐름"],
                "fs_div": ["CFS", "CFS"],
                "thstrm_amount": ["10", "30"],
                "thstrm_add_amount": ["", ""],
            }
        )

        with patch("dartlab.core.dataLoader.loadData", return_value=df):
            result = buildTimeseries("005930")

        assert result is not None
        series, periods = result
        assert periods == ["2025-Q1", "2025-Q2"]
        assert series["CF"]["operating_cashflow"] == [10.0, 20.0]


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


class TestRatioQuality:
    def test_ratio_result_has_headline_signal(self):
        from types import SimpleNamespace

        from dartlab.engines.dart.company import _ratioResultHasHeadlineSignal, _shouldFallbackToAnnualRatios

        assert _ratioResultHasHeadlineSignal(None) is False
        assert (
            _ratioResultHasHeadlineSignal(
                SimpleNamespace(
                    roe=None,
                    roa=None,
                    operatingMargin=None,
                    netMargin=None,
                    debtRatio=None,
                    currentRatio=None,
                    equityRatio=None,
                    revenueTTM=None,
                    netIncomeTTM=None,
                )
            )
            is False
        )
        assert (
            _ratioResultHasHeadlineSignal(
                SimpleNamespace(
                    roe=None,
                    roa=0.6,
                    operatingMargin=None,
                    netMargin=None,
                    debtRatio=None,
                    currentRatio=None,
                    equityRatio=None,
                    revenueTTM=None,
                    netIncomeTTM=None,
                )
            )
            is True
        )
        assert (
            _shouldFallbackToAnnualRatios(
                SimpleNamespace(
                    roe=None,
                    roa=None,
                    operatingMargin=None,
                    netMargin=None,
                    debtRatio=None,
                    currentRatio=None,
                    equityRatio=8.0,
                    revenueTTM=None,
                    netIncomeTTM=None,
                ),
                "insurance",
            )
            is True
        )
        assert (
            _shouldFallbackToAnnualRatios(
                SimpleNamespace(
                    roe=None,
                    roa=None,
                    operatingMargin=None,
                    netMargin=None,
                    debtRatio=None,
                    currentRatio=None,
                    equityRatio=8.0,
                    revenueTTM=None,
                    netIncomeTTM=None,
                ),
                None,
            )
            is False
        )

    def test_ratio_template_fields_by_financial_industry(self):
        from dartlab.engines.dart.company import _RATIO_TEMPLATE_FIELDS, _ratioTemplateKeyForIndustryGroup
        from dartlab.engines.sector.types import IndustryGroup

        assert _ratioTemplateKeyForIndustryGroup(IndustryGroup.BANK) == "bank"
        assert _ratioTemplateKeyForIndustryGroup(IndustryGroup.INSURANCE) == "insurance"
        assert _ratioTemplateKeyForIndustryGroup(IndustryGroup.DIVERSIFIED_FINANCIALS) == "diversified_financials"
        assert "debtRatio" not in _RATIO_TEMPLATE_FIELDS["bank"]
        assert "currentRatio" not in _RATIO_TEMPLATE_FIELDS["bank"]
        assert "operatingMargin" not in _RATIO_TEMPLATE_FIELDS["bank"]
        assert "operatingMargin" in _RATIO_TEMPLATE_FIELDS["diversified_financials"]
        assert "roe" in _RATIO_TEMPLATE_FIELDS["insurance"]

    def test_ratio_series_to_dataframe_can_apply_field_template(self):
        from dartlab.engines.dart.company import _ratioSeriesToDataFrame

        series = {
            "RATIO": {
                "roe": [10.0, 12.0],
                "roa": [1.0, 1.2],
                "debtRatio": [300.0, 320.0],
                "currentRatio": [90.0, 95.0],
                "operatingMargin": [12.0, 14.0],
            }
        }
        years = ["2024", "2025"]

        df = _ratioSeriesToDataFrame(series, years, fieldNames=("roe", "roa"))

        assert df is not None
        assert df["항목"].to_list() == ["ROE (%)", "ROA (%)"]

    def test_yoy_sign_change_returns_none(self):
        from dartlab.engines.common.finance.ratios import _yoy

        assert _yoy([100, -50], 1) is None
        assert _yoy([-50, 100], 1) is None
        assert _yoy([-100, -50], 1) == 50.0
        assert _yoy([-50, -100], 1) == -100.0

    def test_total_equity_uses_consolidated_and_roe_uses_owners(self):
        from dartlab.engines.common.finance.ratios import calcRatios

        series = {
            "IS": {"sales": [1000], "operating_profit": [100], "net_profit": [80]},
            "BS": {
                "total_assets": [2000],
                "total_stockholders_equity": [1000],
                "owners_of_parent_equity": [800],
                "total_liabilities": [1000],
            },
            "CF": {},
        }

        ratios = calcRatios(series, annual=True)

        assert ratios.totalEquity == 1000
        assert ratios.ownersEquity == 800
        assert ratios.roe == 10.0
        assert ratios.debtRatio == 100.0

    def test_ebitda_prefers_cf_depreciation(self):
        from dartlab.engines.common.finance.ratios import calcRatios

        series = {
            "IS": {"sales": [1000], "operating_profit": [100], "net_profit": [80]},
            "BS": {
                "total_assets": [2000],
                "total_stockholders_equity": [1000],
                "owners_of_parent_equity": [800],
                "total_liabilities": [1000],
                "tangible_assets": [10_000],
                "intangible_assets": [5_000],
            },
            "CF": {"depreciation_cf": [20]},
        }

        ratios = calcRatios(series, annual=True)

        assert ratios.ebitdaEstimated is False
        assert ratios.ebitdaMargin == 12.0

    def test_financial_alias_accounts_are_used_for_ratio_calculation(self):
        from dartlab.engines.common.finance.ratios import calcRatios, calcRatioSeries

        series = {
            "IS": {
                "revenue": [1000, 1100, 1200],
                "operating_income": [120, 132, 144],
                "net_income": [80, 88, 96],
                "interest_expense": [10, 11, 12],
            },
            "BS": {
                "total_assets": [5000, 5200, 5400],
                "total_stockholders_equity": [1000, 1050, 1100],
                "total_liabilities": [4000, 4150, 4300],
            },
            "CF": {},
        }

        latest = calcRatios(series, annual=True)
        ratioSeries = calcRatioSeries(series, ["2023", "2024", "2025"])

        assert latest.operatingIncomeTTM == 144
        assert latest.netIncomeTTM == 96
        assert latest.revenueTTM == 1200
        assert latest.roe == 8.73
        assert latest.roa == 1.78
        assert ratioSeries.operatingMargin[-1] == 12.0
        assert ratioSeries.netMargin[-1] == 8.0

    def test_bank_like_series_nulls_misleading_liquidity_ratios(self):
        from dartlab.engines.common.finance.ratios import calcRatios, calcRatioSeries

        series = {
            "IS": {
                "interest_income": [1000, 1100, 1200],
                "operating_income": [500, 550, 600],
                "operating_profit": [300, 330, 360],
                "net_profit": [150, 160, 170],
                "finance_costs": [600, 620, 640],
            },
            "BS": {
                "total_assets": [10000, 11000, 12000],
                "total_stockholders_equity": [900, 950, 1000],
                "owners_of_parent_equity": [850, 900, 950],
                "total_liabilities": [9100, 10050, 11000],
                "loans": [3000, 3200, 3400],
                "cash_and_deposits": [500, 550, 600],
                "current_assets": [2000, 2100, 2200],
                "current_liabilities": [1800, 1900, 2000],
            },
            "CF": {
                "operating_cashflow": [400, 420, 440],
                "dividends_paid": [-20, -25, -30],
            },
        }

        latest = calcRatios(series, annual=True)
        ratioSeries = calcRatioSeries(series, ["2023", "2024", "2025"])

        assert latest.roe is not None
        assert latest.roa is not None
        assert latest.debtRatio is None
        assert latest.currentRatio is None
        assert latest.interestCoverage is None
        assert latest.fcf is None
        assert latest.operatingMargin is None
        assert all(v is None for v in ratioSeries.debtRatio)
        assert all(v is None for v in ratioSeries.currentRatio)
        assert all(v is None for v in ratioSeries.operatingMargin)

    def test_archetype_override_can_force_bank_policy(self):
        from dartlab.engines.common.finance.ratios import calcRatios, calcRatioSeries

        series = {
            "IS": {
                "sales": [1000, 1100, 1200],
                "operating_profit": [100, 110, 120],
                "net_profit": [70, 75, 80],
                "finance_costs": [20, 22, 24],
            },
            "BS": {
                "total_assets": [10000, 10500, 11000],
                "total_stockholders_equity": [1000, 1020, 1040],
                "owners_of_parent_equity": [980, 1000, 1020],
                "total_liabilities": [9000, 9480, 9960],
                "current_assets": [2000, 2100, 2200],
                "current_liabilities": [1500, 1600, 1700],
            },
            "CF": {
                "operating_cashflow": [150, 160, 170],
            },
        }

        latest = calcRatios(series, annual=True, archetypeOverride="bank")
        ratioSeries = calcRatioSeries(series, ["2023", "2024", "2025"], archetypeOverride="bank")

        assert latest.roe is not None
        assert latest.debtRatio is None
        assert latest.currentRatio is None
        assert latest.operatingMargin is None
        assert all(v is None for v in ratioSeries.debtRatio)
        assert all(v is None for v in ratioSeries.currentRatio)
        assert all(v is None for v in ratioSeries.operatingMargin)

    def test_securities_like_series_keeps_margins_but_drops_debt_metrics(self):
        from dartlab.engines.common.finance.ratios import calcRatios

        series = {
            "IS": {
                "sales": [1000, 1100, 1200, 1300],
                "commission_income": [200, 220, 240, 260],
                "operating_profit": [100, 110, 120, 130],
                "net_profit": [80, 88, 96, 104],
                "finance_costs": [10, 11, 12, 13],
            },
            "BS": {
                "total_assets": [10000, 10100, 10200, 10300],
                "total_stockholders_equity": [1500, 1520, 1540, 1560],
                "owners_of_parent_equity": [1450, 1470, 1490, 1510],
                "total_liabilities": [8500, 8580, 8660, 8740],
                "financial_assets_at_fv_through_profit": [3000, 3050, 3100, 3150],
            },
            "CF": {
                "operating_cashflow": [100, 120, 140, 160],
                "depreciation_cf": [10, 10, 10, 10],
            },
        }

        ratios = calcRatios(series, annual=True)

        assert ratios.roe is not None
        assert ratios.roa is not None
        assert ratios.operatingMargin == 10.0
        assert ratios.netMargin == 8.0
        assert ratios.debtRatio is None
        assert ratios.currentRatio is None
