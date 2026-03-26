"""EDGAR finance 엔진 테스트.

데이터 의존: config.dataDir/edgar/finance/{CIK}.parquet
로컬 데이터 없으면 skip.
"""

from datetime import date
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

from dartlab import config

EDGAR_DIR = Path(config.dataDir) / "edgar" / "finance"
AAPL_CIK = "0000320193"
MSFT_CIK = "0000789019"
NVDA_CIK = "0001045810"

HAS_EDGAR_DATA = (EDGAR_DIR / f"{AAPL_CIK}.parquet").exists()

_skipNoData = pytest.mark.skipif(
    not HAS_EDGAR_DATA,
    reason="EDGAR parquet 데이터 없음",
)


def _factsDf(rows: list[dict]) -> pl.DataFrame:
    defaults = {
        "cik": "0000000000",
        "entityName": "Test Corp",
        "namespace": "us-gaap",
        "label": None,
        "unit": "USD",
        "val": None,
        "fy": None,
        "fp": None,
        "form": "10-K",
        "filed": date(2025, 2, 1),
        "frame": None,
        "start": None,
        "end": None,
        "accn": "0000000000-25-000001",
    }
    normalized = [{**defaults, **row} for row in rows]
    return pl.DataFrame(normalized)


class TestEdgarMapper:
    def test_commonTagMapping(self):
        from dartlab.providers.edgar.finance.mapper import EdgarMapper

        assert EdgarMapper.mapToDart("Assets", "BS") == "total_assets"
        assert EdgarMapper.mapToDart("Liabilities", "BS") == "total_liabilities"

    def test_aliasConversion(self):
        from dartlab.providers.edgar.finance.mapper import EdgarMapper

        assert EdgarMapper.mapToDart("CashAndCashEquivalentsAtCarryingValue", "BS") == "cash_and_cash_equivalents"

    def test_stmtOverride_netIncome(self):
        from dartlab.providers.edgar.finance.mapper import EdgarMapper

        assert EdgarMapper.mapToDart("NetIncomeLoss", "IS") == "net_profit"
        assert EdgarMapper.mapToDart("NetIncomeLoss", "CF") == "net_income_cf"

    def test_learnedSynonym(self):
        from dartlab.providers.edgar.finance.mapper import EdgarMapper

        result = EdgarMapper.mapToDart("accountsreceivablenetcurrent", "BS")
        assert result is not None

    def test_unknownTag(self):
        from dartlab.providers.edgar.finance.mapper import EdgarMapper

        assert EdgarMapper.mapToDart("CompletelyFakeTag12345", "BS") is None

    def test_isCommonTag(self):
        from dartlab.providers.edgar.finance.mapper import EdgarMapper

        assert EdgarMapper.isCommonTag("Assets") is True
        assert EdgarMapper.isCommonTag("completelyfaketag") is False

    def test_classifyTagsByStmt(self):
        from dartlab.providers.edgar.finance.mapper import EdgarMapper

        stmtTags = EdgarMapper.classifyTagsByStmt()
        assert "IS" in stmtTags
        assert "BS" in stmtTags
        assert "CF" in stmtTags
        assert len(stmtTags["IS"]) > 0
        assert len(stmtTags["BS"]) > 0
        assert len(stmtTags["CF"]) > 0

    def test_getTagsForSnakeIds_revenue_includes_extended_tags(self):
        from dartlab.providers.edgar.finance.mapper import EdgarMapper

        tags = EdgarMapper.getTagsForSnakeIds(["sales", "revenue"])
        assert {
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
            "SalesRevenueGoodsNet",
        }.issubset(tags)


@_skipNoData
class TestBuildTimeseries:
    def test_aaplRevenue(self):
        from dartlab.providers.edgar.finance.pivot import buildTimeseries

        result = buildTimeseries(AAPL_CIK, edgarDir=EDGAR_DIR)
        assert result is not None

        series, periods = result
        rev = series["IS"]["sales"]
        idx = periods.index("2024-Q1")
        assert rev[idx] == pytest.approx(119_575_000_000, rel=1e-6)

    def test_aaplNetIncome(self):
        from dartlab.providers.edgar.finance.pivot import buildTimeseries

        result = buildTimeseries(AAPL_CIK, edgarDir=EDGAR_DIR)
        series, periods = result
        ni = series["IS"]["net_profit"]
        idx = periods.index("2024-Q4")
        assert ni[idx] == pytest.approx(14_736_000_000, rel=1e-6)

    def test_msftRevenue(self):
        from dartlab.providers.edgar.finance.pivot import buildTimeseries

        result = buildTimeseries(MSFT_CIK, edgarDir=EDGAR_DIR)
        series, periods = result
        rev = series["IS"]["sales"]
        idx = periods.index("2024-Q2")
        assert rev[idx] == pytest.approx(62_020_000_000, rel=1e-6)

    def test_nvdaRevenue(self):
        from dartlab.providers.edgar.finance.pivot import buildTimeseries

        result = buildTimeseries(NVDA_CIK, edgarDir=EDGAR_DIR)
        series, periods = result
        rev = series["IS"]["sales"]
        idx = periods.index("2025-Q4")
        assert rev[idx] == pytest.approx(39_331_000_000, rel=1e-6)

    def test_l2Coverage(self):
        from dartlab.providers.edgar.finance.pivot import buildTimeseries

        result = buildTimeseries(AAPL_CIK, edgarDir=EDGAR_DIR)
        series, periods = result

        allSids = set()
        for stmt in series:
            allSids.update(series[stmt].keys())

        l2Used = {
            "sales",
            "operating_profit",
            "net_profit",
            "total_assets",
            "current_assets",
            "noncurrent_assets",
            "total_liabilities",
            "current_liabilities",
            "noncurrent_liabilities",
            "owners_of_parent_equity",
            "total_stockholders_equity",
            "cash_and_cash_equivalents",
            "inventories",
            "trade_and_other_receivables",
            "shortterm_borrowings",
            "longterm_borrowings",
            "operating_cashflow",
            "investing_cashflow",
            "cash_flows_from_financing_activities",
            "cost_of_sales",
            "gross_profit",
            "profit_before_tax",
            "income_taxes",
            "basic_earnings_per_share",
            "diluted_earnings_per_share",
            "tangible_assets",
        }
        covered = allSids & l2Used
        assert len(covered) >= 24

    def test_nonexistentCik(self):
        from dartlab.providers.edgar.finance.pivot import buildTimeseries

        result = buildTimeseries("9999999999", edgarDir=EDGAR_DIR)
        assert result is None

    def test_seriesStructure(self):
        from dartlab.providers.edgar.finance.pivot import buildTimeseries

        result = buildTimeseries(AAPL_CIK, edgarDir=EDGAR_DIR)
        series, periods = result

        assert "BS" in series
        assert "IS" in series
        assert "CF" in series
        assert len(periods) > 0

        for stmt in series:
            for sid, vals in series[stmt].items():
                assert len(vals) == len(periods)


@_skipNoData
class TestBuildAnnual:
    def test_aaplFY2024(self):
        from dartlab.providers.edgar.finance.pivot import buildAnnual

        result = buildAnnual(AAPL_CIK, edgarDir=EDGAR_DIR)
        assert result is not None

        series, years = result
        idx = years.index("2024")
        rev = series["IS"]["sales"][idx]
        ni = series["IS"]["net_profit"][idx]
        assert rev == pytest.approx(391_035_000_000, rel=1e-6)
        assert ni == pytest.approx(93_736_000_000, rel=1e-6)

    def test_msftFY2024(self):
        from dartlab.providers.edgar.finance.pivot import buildAnnual

        result = buildAnnual(MSFT_CIK, edgarDir=EDGAR_DIR)
        series, years = result
        idx = years.index("2024")
        assert series["IS"]["sales"][idx] == pytest.approx(245_122_000_000, rel=1e-6)

    def test_nvdaFY2025(self):
        from dartlab.providers.edgar.finance.pivot import buildAnnual

        result = buildAnnual(NVDA_CIK, edgarDir=EDGAR_DIR)
        series, years = result
        idx = years.index("2025")
        assert series["IS"]["sales"][idx] == pytest.approx(130_497_000_000, rel=1e-6)
        assert series["IS"]["net_profit"][idx] == pytest.approx(72_880_000_000, rel=1e-6)

    def test_annual_falls_back_to_fy_value_for_is_only_year(self, monkeypatch):
        from dartlab.providers.edgar.finance import pivot as pivotMod

        monkeypatch.setattr(
            pivotMod,
            "_loadFacts",
            lambda edgarDir, cik: _factsDf(
                [
                    {
                        "tag": "Revenues",
                        "val": 100.0,
                        "fy": 2024,
                        "fp": "FY",
                        "start": date(2024, 1, 1),
                        "end": date(2024, 12, 31),
                    }
                ]
            ),
        )

        result = pivotMod.buildAnnual("0000000000", edgarDir=Path("."))
        assert result is not None

        series, years = result
        assert years == ["2024"]
        assert series["IS"]["sales"] == [100.0]

    def test_annual_falls_back_to_fy_value_for_cf_only_year(self, monkeypatch):
        from dartlab.providers.edgar.finance import pivot as pivotMod

        monkeypatch.setattr(
            pivotMod,
            "_loadFacts",
            lambda edgarDir, cik: _factsDf(
                [
                    {
                        "tag": "NetCashProvidedByUsedInOperatingActivities",
                        "val": 40.0,
                        "fy": 2024,
                        "fp": "FY",
                        "start": date(2024, 1, 1),
                        "end": date(2024, 12, 31),
                    }
                ]
            ),
        )

        result = pivotMod.buildAnnual("0000000000", edgarDir=Path("."))
        assert result is not None

        series, years = result
        assert years == ["2024"]
        assert series["CF"]["operating_cashflow"] == [40.0]


class TestEdgarPivotEdgeCases:
    def test_deaccumulate_cf_skips_negative_revenue_quarters(self):
        from dartlab.providers.edgar.finance.pivot import _deaccumulateCF

        fyQ1Result = pl.DataFrame(
            {
                "tag": ["SalesRevenueGoodsNet"],
                "period": ["2024-Q1"],
                "val": [100.0],
            }
        )
        q2q3Ytd = pl.DataFrame(
            {
                "tag": ["SalesRevenueGoodsNet", "SalesRevenueGoodsNet"],
                "fy": [2024, 2024],
                "fp": ["Q2", "Q3"],
                "ytd_val": [80.0, 70.0],
            }
        )

        result = _deaccumulateCF(fyQ1Result, q2q3Ytd)
        assert result.is_empty()

    def test_sanitize_q4_nulls_negative_revenue_tag(self):
        from dartlab.providers.edgar.finance.pivot import _sanitizeQ4

        pivoted = pl.DataFrame(
            {
                "tag": ["SalesRevenueGoodsNet", "Assets"],
                "2024-Q1": [100.0, 100.0],
                "2024-Q2": [100.0, 100.0],
                "2024-Q3": [100.0, 100.0],
                "2024-Q4": [-50.0, -50.0],
            }
        )

        result = _sanitizeQ4(pivoted, ["2024"])
        rows = result.to_dicts()
        assert rows[0]["2024-Q4"] is None
        assert rows[1]["2024-Q4"] == -50.0

    def test_compute_equity_skips_implausible_redeemable_nci_merge(self):
        from dartlab.providers.edgar.finance.pivot import _computeEquity

        result = {
            "BS": {
                "total_stockholders_equity": [100.0],
                "owners_of_parent_equity": [100.0],
                "redeemable_noncontrolling_interest": [150.0],
                "total_assets": [400.0],
            },
            "IS": {},
            "CF": {},
            "CI": {},
        }

        _computeEquity(result, ["2024-Q4"])
        assert result["BS"]["total_stockholders_equity"] == [100.0]


@_skipNoData
class TestCalcRatiosCompat:
    def test_ratiosWithEdgarData(self):
        from dartlab.core.finance.ratios import calcRatios
        from dartlab.providers.edgar.finance.pivot import buildAnnual

        result = buildAnnual(NVDA_CIK, edgarDir=EDGAR_DIR)
        series, years = result

        ratios = calcRatios(series, annual=True)
        assert ratios.operatingMargin is not None
        assert ratios.netMargin is not None
        assert ratios.revenueGrowth3Y is not None
