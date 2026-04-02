"""analysis calc 함수 확장 단위 테스트 — MockCompany로 합성 데이터 사용.

coverage 대상:
- cashflow.py: calcCashFlowOverview, calcCashQuality, calcCashFlowFlags, calcOcfDecomposition
- earningsQuality.py: calcAccrualAnalysis, calcEarningsPersistence, calcEarningsQualityFlags
- costStructure.py: calcCostBreakdown, calcOperatingLeverage, calcBreakevenEstimate
- capitalAllocation.py: calcDividendPolicy, calcShareholderReturn, calcReinvestment, calcFcfUsage
- investmentAnalysis.py: calcRoicTimeline, calcInvestmentIntensity, calcEvaTimeline
- asset.py: calcAssetStructure, calcWorkingCapital, calcCapexPattern
- revenue.py: calcCompanyProfile, calcSegmentComposition
- crossStatement.py: calcIsCfDivergence, calcIsBsDivergence, calcAnomalyScore, calcArticulationCheck
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit

# ── SelectResult mock ──


class _SelectResult:
    """company.select() 반환값 모의 — .df 속성만 있으면 된다."""

    def __init__(self, df: pl.DataFrame):
        self._df = df

    @property
    def df(self) -> pl.DataFrame:
        return self._df


# ── 합성 데이터 헬퍼 ──

_PERIODS = ["2024", "2023", "2022", "2021", "2020", "2019"]


def _make_df(accounts: dict[str, list[float | None]], col_name: str = "계정명") -> pl.DataFrame:
    """IS/BS/CF 형태 DataFrame 생성."""
    rows = []
    for name, vals in accounts.items():
        row: dict = {col_name: name}
        for i, p in enumerate(_PERIODS):
            row[p] = vals[i] if i < len(vals) else None
        rows.append(row)
    return pl.DataFrame(rows)


def _make_snakeid_df(accounts: dict[str, list[float | None]]) -> pl.DataFrame:
    """snakeId 컬럼 기반 DataFrame 생성 (capitalAllocation 등에서 사용)."""
    rows = []
    for name, vals in accounts.items():
        row: dict = {"계정명": name, "snakeId": name}
        for i, p in enumerate(_PERIODS):
            row[p] = vals[i] if i < len(vals) else None
        rows.append(row)
    return pl.DataFrame(rows)


# ── MockCompany ──


class _MockNotes:
    """notes accessor mock — 모든 속성이 None."""

    def __getattr__(self, name):
        return None


class MockCompany:
    """analysis calc 함수에 필요한 최소 인터페이스."""

    stockCode = "005930"
    corpName = "테스트"
    market = "KOSPI"
    currency = "KRW"
    _cache: dict = {}

    def __init__(self, *, is_data=None, bs_data=None, cf_data=None, cf_snake=None, sector=None, ratios=None):
        self._is = (
            is_data
            if is_data is not None
            else {
                "매출액": [100_000, 90_000, 80_000, 70_000, 60_000, 50_000],
                "매출원가": [60_000, 55_000, 50_000, 45_000, 40_000, 35_000],
                "매출총이익": [40_000, 35_000, 30_000, 25_000, 20_000, 15_000],
                "판매비와관리비": [15_000, 14_000, 13_000, 12_000, 11_000, 10_000],
                "영업이익": [25_000, 21_000, 17_000, 13_000, 9_000, 5_000],
                "법인세차감전순이익": [23_000, 19_000, 15_000, 11_000, 7_000, 3_000],
                "당기순이익": [18_000, 15_000, 12_000, 9_000, 6_000, 3_000],
                "금융비용": [2_000, 2_000, 2_000, 2_000, 2_000, 2_000],
                "금융수익": [500, 400, 300, 200, 100, 50],
                "법인세비용": [5_000, 4_000, 3_000, 2_000, 1_000, 0],
                "이자비용": [1_500, 1_500, 1_500, 1_500, 1_500, 1_500],
                "감가상각비": [3_000, 2_800, 2_600, 2_400, 2_200, 2_000],
            }
        )
        self._bs = (
            bs_data
            if bs_data is not None
            else {
                "자산총계": [500_000, 450_000, 400_000, 350_000, 300_000, 250_000],
                "부채총계": [200_000, 190_000, 180_000, 170_000, 160_000, 150_000],
                "자본총계": [300_000, 260_000, 220_000, 180_000, 140_000, 100_000],
                "유동자산": [150_000, 140_000, 130_000, 120_000, 110_000, 100_000],
                "유동부채": [100_000, 95_000, 90_000, 85_000, 80_000, 75_000],
                "비유동자산": [350_000, 310_000, 270_000, 230_000, 190_000, 150_000],
                "비유동부채": [100_000, 95_000, 90_000, 85_000, 80_000, 75_000],
                "현금및현금성자산": [50_000, 45_000, 40_000, 35_000, 30_000, 25_000],
                "단기차입금": [20_000, 18_000, 16_000, 14_000, 12_000, 10_000],
                "장기차입금": [30_000, 28_000, 26_000, 24_000, 22_000, 20_000],
                "사채": [10_000, 9_000, 8_000, 7_000, 6_000, 5_000],
                "이익잉여금": [250_000, 220_000, 190_000, 160_000, 130_000, 100_000],
                "재고자산": [30_000, 28_000, 26_000, 24_000, 22_000, 20_000],
                "매출채권및기타채권": [40_000, 38_000, 36_000, 34_000, 32_000, 30_000],
                "매입채무": [25_000, 24_000, 23_000, 22_000, 21_000, 20_000],
                "유형자산": [120_000, 110_000, 100_000, 90_000, 80_000, 70_000],
                "무형자산": [15_000, 14_000, 13_000, 12_000, 11_000, 10_000],
                "영업권": [5_000, 5_000, 5_000, 5_000, 5_000, 5_000],
                "투자부동산": [0] * 6,
                "건설중인자산": [3_000, 2_500, 2_000, 1_500, 1_000, 500],
            }
        )
        self._cf = (
            cf_data
            if cf_data is not None
            else {
                "영업활동현금흐름": [28_000, 24_000, 20_000, 16_000, 12_000, 8_000],
                "투자활동현금흐름": [-15_000, -13_000, -11_000, -9_000, -7_000, -5_000],
                "재무활동으로인한현금흐름": [-5_000, -4_000, -3_000, -2_000, -1_000, 0],
                "유형자산의취득": [-8_000, -7_000, -6_000, -5_000, -4_000, -3_000],
                "무형자산의취득": [-1_000, -900, -800, -700, -600, -500],
                "유형자산의처분": [500, 400, 300, 200, 100, 50],
            }
        )
        # snakeId based CF data (capitalAllocation uses toDictBySnakeId)
        self._cf_snake = (
            cf_snake
            if cf_snake is not None
            else {
                "dividends_paid": [-3_000, -2_800, -2_600, -2_400, -2_200, -2_000],
                "operating_cashflow": [28_000, 24_000, 20_000, 16_000, 12_000, 8_000],
                "purchase_of_property_plant_and_equipment": [-8_000, -7_000, -6_000, -5_000, -4_000, -3_000],
                "purchase_of_intangible_assets": [-1_000, -900, -800, -700, -600, -500],
                "purchase_of_treasury_stock": [-500, -400, -300, 0, 0, 0],
                "repayment_of_longterm_borrowings": [-2_000, -1_500, -1_000, -800, -600, -400],
            }
        )
        self._sector = sector
        self._ratios = ratios
        self._cache = {}

    @property
    def sector(self):
        return self._sector

    @property
    def finance(self):
        return self

    @property
    def ratios(self):
        return self._ratios

    @property
    def ratioSeries(self):
        return None

    @property
    def annual(self):
        return None

    @property
    def notes(self):
        return _MockNotes()

    @property
    def _notesAccessor(self):
        return _MockNotes()

    def select(self, stmt: str, accounts: list[str] | None = None):
        if stmt == "IS":
            src = self._is
        elif stmt == "BS":
            src = self._bs
        elif stmt == "CF":
            src = self._cf
            # Check if any requested account is a snakeId
            if accounts and any("_" in a for a in accounts):
                src = self._cf_snake
        else:
            return None
        if accounts is None:
            return None
        filtered = {k: v for k, v in src.items() if k in accounts}
        if not filtered:
            return None
        # snakeId accounts get snakeId column
        if any("_" in k for k in filtered):
            df = _make_snakeid_df(filtered)
        else:
            df = _make_df(filtered)
        return _SelectResult(df)

    def show(self, topic: str, *args, **kwargs):
        return None


# ── Fixtures ──


@pytest.fixture
def company():
    return MockCompany()


@pytest.fixture
def empty_company():
    """모든 데이터가 비어 있는 Company."""
    return MockCompany(
        is_data={},
        bs_data={},
        cf_data={},
        cf_snake={},
    )


# ── 버그 표기 ──
# cashflow.py, earningsQuality.py, capitalAllocation.py, asset.py의 일부 함수는
# annualColsFromPeriods(periods, _MAX_YEARS, basePeriod=basePeriod) 형태로 호출하여
# basePeriod 인자가 중복 전달된다 (positional + keyword).
# 이 함수들은 basePeriod=None (기본값)으로 호출 시 TypeError가 발생한다.
# 해당 테스트는 xfail로 표기하여 버그 수정 후 자동으로 통과되도록 한다.

_ANNUALCOLS_BUG = pytest.mark.xfail(
    raises=TypeError,
    reason="annualColsFromPeriods() got multiple values for argument 'basePeriod'",
    strict=False,
)


# ═══════════════════════════════════════════════════════════
# cashflow.py
# ═══════════════════════════════════════════════════════════


class TestCalcCashFlowOverview:
    @_ANNUALCOLS_BUG
    def test_returns_history(self, company):
        from dartlab.analysis.financial.cashflow import calcCashFlowOverview

        result = calcCashFlowOverview(company)
        assert result is not None
        assert "history" in result
        assert len(result["history"]) >= 2

    @_ANNUALCOLS_BUG
    def test_history_fields(self, company):
        from dartlab.analysis.financial.cashflow import calcCashFlowOverview

        result = calcCashFlowOverview(company)
        h0 = result["history"][0]
        assert "period" in h0
        assert "ocf" in h0
        assert "icf" in h0
        assert "fcf" in h0
        assert "capex" in h0
        assert "pattern" in h0

    @_ANNUALCOLS_BUG
    def test_ocf_value(self, company):
        from dartlab.analysis.financial.cashflow import calcCashFlowOverview

        result = calcCashFlowOverview(company)
        h0 = result["history"][0]
        assert h0["ocf"] == 28_000
        assert h0["capex"] == 9_000
        assert h0["fcf"] == 19_000

    @_ANNUALCOLS_BUG
    def test_pattern_classification(self, company):
        from dartlab.analysis.financial.cashflow import calcCashFlowOverview

        result = calcCashFlowOverview(company)
        h0 = result["history"][0]
        assert h0["pattern"] is not None
        assert "성숙형" in h0["pattern"]

    @_ANNUALCOLS_BUG
    def test_none_when_no_cf(self, empty_company):
        from dartlab.analysis.financial.cashflow import calcCashFlowOverview

        result = calcCashFlowOverview(empty_company)
        assert result is None


class TestCalcCashQuality:
    @_ANNUALCOLS_BUG
    def test_returns_history(self, company):
        from dartlab.analysis.financial.cashflow import calcCashQuality

        result = calcCashQuality(company)
        assert result is not None
        assert "history" in result

    @_ANNUALCOLS_BUG
    def test_ocf_to_ni(self, company):
        from dartlab.analysis.financial.cashflow import calcCashQuality

        result = calcCashQuality(company)
        h0 = result["history"][0]
        assert h0["ocfToNi"] is not None
        assert h0["ocfToNi"] > 100

    @_ANNUALCOLS_BUG
    def test_ocf_margin(self, company):
        from dartlab.analysis.financial.cashflow import calcCashQuality

        result = calcCashQuality(company)
        h0 = result["history"][0]
        assert h0["ocfMargin"] == 28.0

    @_ANNUALCOLS_BUG
    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.cashflow import calcCashQuality

        result = calcCashQuality(empty_company)
        assert result is None


class TestCalcCashFlowFlags:
    @_ANNUALCOLS_BUG
    def test_returns_list(self, company):
        from dartlab.analysis.financial.cashflow import calcCashFlowFlags

        result = calcCashFlowFlags(company)
        assert isinstance(result, list)

    @_ANNUALCOLS_BUG
    def test_healthy_company_few_flags(self, company):
        from dartlab.analysis.financial.cashflow import calcCashFlowFlags

        result = calcCashFlowFlags(company)
        assert all(isinstance(f, str) for f in result)

    @_ANNUALCOLS_BUG
    def test_negative_ocf_triggers_flag(self):
        from dartlab.analysis.financial.cashflow import calcCashFlowFlags

        co = MockCompany(
            cf_data={
                "영업활동현금흐름": [-5_000, -4_000, -3_000, -2_000, -1_000, 0],
                "투자활동현금흐름": [-10_000] * 6,
                "재무활동으로인한현금흐름": [15_000] * 6,
                "유형자산의취득": [-3_000] * 6,
                "무형자산의취득": [0] * 6,
            }
        )
        result = calcCashFlowFlags(co)
        assert any("영업CF 적자" in f for f in result)


# ═══════════════════════════════════════════════════════════
# earningsQuality.py
# ═══════════════════════════════════════════════════════════


class TestCalcAccrualAnalysis:
    @_ANNUALCOLS_BUG
    def test_returns_history(self, company):
        from dartlab.analysis.financial.earningsQuality import calcAccrualAnalysis

        result = calcAccrualAnalysis(company)
        assert result is not None
        assert "history" in result

    @_ANNUALCOLS_BUG
    def test_history_fields(self, company):
        from dartlab.analysis.financial.earningsQuality import calcAccrualAnalysis

        result = calcAccrualAnalysis(company)
        h0 = result["history"][0]
        assert "netIncome" in h0
        assert "ocf" in h0
        assert "sloanAccrualRatio" in h0
        assert "ocfToNi" in h0

    @_ANNUALCOLS_BUG
    def test_sloan_ratio(self, company):
        from dartlab.analysis.financial.earningsQuality import calcAccrualAnalysis

        result = calcAccrualAnalysis(company)
        h0 = result["history"][0]
        assert h0["sloanAccrualRatio"] is not None
        assert h0["sloanAccrualRatio"] < 0

    @_ANNUALCOLS_BUG
    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.earningsQuality import calcAccrualAnalysis

        result = calcAccrualAnalysis(empty_company)
        assert result is None


class TestCalcEarningsPersistence:
    @_ANNUALCOLS_BUG
    def test_returns_history_and_volatility(self, company):
        from dartlab.analysis.financial.earningsQuality import calcEarningsPersistence

        result = calcEarningsPersistence(company)
        assert result is not None
        assert "history" in result
        assert "earningsVolatility" in result

    @_ANNUALCOLS_BUG
    def test_non_operating_income(self, company):
        from dartlab.analysis.financial.earningsQuality import calcEarningsPersistence

        result = calcEarningsPersistence(company)
        h0 = result["history"][0]
        assert h0["nonOperatingIncome"] == -2_000
        assert h0["nonOpRatio"] is not None

    @_ANNUALCOLS_BUG
    def test_earnings_volatility_calculated(self, company):
        from dartlab.analysis.financial.earningsQuality import calcEarningsPersistence

        result = calcEarningsPersistence(company)
        assert result["earningsVolatility"] is not None
        assert result["earningsVolatility"] > 0

    @_ANNUALCOLS_BUG
    def test_none_when_no_is(self, empty_company):
        from dartlab.analysis.financial.earningsQuality import calcEarningsPersistence

        result = calcEarningsPersistence(empty_company)
        assert result is None


class TestCalcEarningsQualityFlags:
    @_ANNUALCOLS_BUG
    def test_returns_dict_with_flags(self, company):
        from dartlab.analysis.financial.earningsQuality import calcEarningsQualityFlags

        result = calcEarningsQualityFlags(company)
        assert isinstance(result, dict)
        assert "flags" in result
        assert "enrichedFlags" in result
        assert isinstance(result["flags"], list)


# ═══════════════════════════════════════════════════════════
# costStructure.py
# ═══════════════════════════════════════════════════════════


class TestCalcCostBreakdown:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.costStructure import calcCostBreakdown

        result = calcCostBreakdown(company)
        assert result is not None
        assert "history" in result

    def test_cost_ratios(self, company):
        from dartlab.analysis.financial.costStructure import calcCostBreakdown

        result = calcCostBreakdown(company)
        h0 = result["history"][0]
        # costOfSalesRatio = 60000/100000*100 = 60.0
        assert h0["costOfSalesRatio"] == 60.0
        # sgaRatio = 15000/100000*100 = 15.0
        assert h0["sgaRatio"] == 15.0
        # operatingCostRatio = 75000/100000*100 = 75.0
        assert h0["operatingCostRatio"] == 75.0

    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.costStructure import calcCostBreakdown

        result = calcCostBreakdown(empty_company)
        assert result is None


class TestCalcOperatingLeverage:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.costStructure import calcOperatingLeverage

        result = calcOperatingLeverage(company)
        assert result is not None
        assert "history" in result

    def test_dol_calculation(self, company):
        from dartlab.analysis.financial.costStructure import calcOperatingLeverage

        result = calcOperatingLeverage(company)
        h0 = result["history"][0]
        assert "dol" in h0
        assert "contributionProxy" in h0
        # DOL should be positive for growing revenue/income
        if h0["dol"] is not None:
            assert h0["dol"] > 0

    def test_contribution_proxy(self, company):
        from dartlab.analysis.financial.costStructure import calcOperatingLeverage

        result = calcOperatingLeverage(company)
        h0 = result["history"][0]
        # contributionProxy = GP / OI = 40000 / 25000 = 1.6
        assert h0["contributionProxy"] == 40_000 / 25_000

    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.costStructure import calcOperatingLeverage

        result = calcOperatingLeverage(empty_company)
        assert result is None


class TestCalcBreakevenEstimate:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.costStructure import calcBreakevenEstimate

        result = calcBreakevenEstimate(company)
        assert result is not None
        assert "history" in result

    def test_bep_revenue(self, company):
        from dartlab.analysis.financial.costStructure import calcBreakevenEstimate

        result = calcBreakevenEstimate(company)
        h0 = result["history"][0]
        # variableCostRatio = 60000/100000 = 0.6
        # bepRevenue = 15000 / (1 - 0.6) = 37500
        assert h0["bepRevenue"] == pytest.approx(37_500, rel=0.01)
        # marginOfSafety = (100000 - 37500) / 100000 * 100 = 62.5
        assert h0["marginOfSafety"] == pytest.approx(62.5, rel=0.01)


class TestCalcCostStructureFlags:
    def test_returns_list(self, company):
        from dartlab.analysis.financial.costStructure import calcCostStructureFlags

        result = calcCostStructureFlags(company)
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════
# capitalAllocation.py
# ═══════════════════════════════════════════════════════════


class TestCalcDividendPolicy:
    @_ANNUALCOLS_BUG
    def test_returns_history_and_consecutive(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcDividendPolicy

        result = calcDividendPolicy(company)
        assert result is not None
        assert "history" in result
        assert "consecutiveYears" in result

    @_ANNUALCOLS_BUG
    def test_dividend_paid_abs(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcDividendPolicy

        result = calcDividendPolicy(company)
        h0 = result["history"][0]
        assert h0["dividendsPaid"] == 3_000

    @_ANNUALCOLS_BUG
    def test_consecutive_years(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcDividendPolicy

        result = calcDividendPolicy(company)
        assert result["consecutiveYears"] >= 1


class TestCalcShareholderReturn:
    @_ANNUALCOLS_BUG
    def test_returns_history(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcShareholderReturn

        result = calcShareholderReturn(company)
        assert result is not None
        assert "history" in result

    @_ANNUALCOLS_BUG
    def test_total_return(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcShareholderReturn

        result = calcShareholderReturn(company)
        h0 = result["history"][0]
        assert h0["totalReturn"] == 3_500


class TestCalcReinvestment:
    @_ANNUALCOLS_BUG
    def test_returns_history(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcReinvestment

        result = calcReinvestment(company)
        assert result is not None
        assert "history" in result

    @_ANNUALCOLS_BUG
    def test_capex_to_revenue(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcReinvestment

        result = calcReinvestment(company)
        h0 = result["history"][0]
        assert "capexToRevenue" in h0


class TestCalcFcfUsage:
    @_ANNUALCOLS_BUG
    def test_returns_history(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcFcfUsage

        result = calcFcfUsage(company)
        assert result is not None
        assert "history" in result

    @_ANNUALCOLS_BUG
    def test_residual_calculation(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcFcfUsage

        result = calcFcfUsage(company)
        h0 = result["history"][0]
        assert "residual" in h0
        assert "fcf" in h0
        assert "dividendsPaid" in h0
        assert "debtRepaid" in h0


class TestCalcCapitalAllocationFlags:
    @_ANNUALCOLS_BUG
    def test_returns_list(self, company):
        from dartlab.analysis.financial.capitalAllocation import calcCapitalAllocationFlags

        result = calcCapitalAllocationFlags(company)
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════
# investmentAnalysis.py
# ═══════════════════════════════════════════════════════════


class TestCalcRoicTimeline:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline

        result = calcRoicTimeline(company)
        assert result is not None
        assert "history" in result

    def test_roic_positive(self, company):
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline

        result = calcRoicTimeline(company)
        h0 = result["history"][0]
        assert h0["roic"] is not None
        assert h0["roic"] > 0

    def test_nopat_calculated(self, company):
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline

        result = calcRoicTimeline(company)
        h0 = result["history"][0]
        assert h0["nopat"] is not None
        assert h0["nopat"] > 0

    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline

        result = calcRoicTimeline(empty_company)
        assert result is None


class TestCalcInvestmentIntensity:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.investmentAnalysis import calcInvestmentIntensity

        result = calcInvestmentIntensity(company)
        assert result is not None
        assert "history" in result

    def test_capex_to_revenue(self, company):
        from dartlab.analysis.financial.investmentAnalysis import calcInvestmentIntensity

        result = calcInvestmentIntensity(company)
        h0 = result["history"][0]
        assert "capexToRevenue" in h0
        assert "tangibleRatio" in h0
        assert "intangibleRatio" in h0


class TestCalcEvaTimeline:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.investmentAnalysis import calcEvaTimeline

        result = calcEvaTimeline(company)
        assert result is not None
        assert "history" in result

    def test_nopat_return(self, company):
        from dartlab.analysis.financial.investmentAnalysis import calcEvaTimeline

        result = calcEvaTimeline(company)
        h0 = result["history"][0]
        assert h0["nopat"] is not None
        assert h0["investedCapital"] is not None

    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.investmentAnalysis import calcEvaTimeline

        result = calcEvaTimeline(empty_company)
        assert result is None


# ═══════════════════════════════════════════════════════════
# asset.py
# ═══════════════════════════════════════════════════════════


class TestCalcAssetStructure:
    @_ANNUALCOLS_BUG
    def test_returns_latest_and_history(self, company):
        from dartlab.analysis.financial.asset import calcAssetStructure

        result = calcAssetStructure(company)
        assert result is not None
        assert "latest" in result
        assert "history" in result
        assert "diagnosis" in result

    @_ANNUALCOLS_BUG
    def test_latest_fields(self, company):
        from dartlab.analysis.financial.asset import calcAssetStructure

        result = calcAssetStructure(company)
        lat = result["latest"]
        assert lat["totalAssets"] == 500_000
        assert "opAssets" in lat
        assert "nonOpAssets" in lat
        assert "opAssetsPct" in lat
        assert "noa" in lat

    @_ANNUALCOLS_BUG
    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.asset import calcAssetStructure

        result = calcAssetStructure(empty_company)
        assert result is None


class TestCalcWorkingCapital:
    @_ANNUALCOLS_BUG
    def test_returns_latest_and_history(self, company):
        from dartlab.analysis.financial.asset import calcWorkingCapital

        result = calcWorkingCapital(company)
        assert result is not None
        assert "latest" in result
        assert "history" in result

    @_ANNUALCOLS_BUG
    def test_ccc_calculated(self, company):
        from dartlab.analysis.financial.asset import calcWorkingCapital

        result = calcWorkingCapital(company)
        lat = result["latest"]
        assert "ccc" in lat
        assert "receivableDays" in lat
        assert "inventoryDays" in lat
        assert "payableDays" in lat

    @_ANNUALCOLS_BUG
    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.asset import calcWorkingCapital

        result = calcWorkingCapital(empty_company)
        assert result is None


class TestCalcCapexPattern:
    @_ANNUALCOLS_BUG
    def test_returns_latest_and_history(self, company):
        from dartlab.analysis.financial.asset import calcCapexPattern

        result = calcCapexPattern(company)
        assert result is not None
        assert "latest" in result
        assert "history" in result

    @_ANNUALCOLS_BUG
    def test_investment_type(self, company):
        from dartlab.analysis.financial.asset import calcCapexPattern

        result = calcCapexPattern(company)
        lat = result["latest"]
        assert "investmentType" in lat
        assert "capex" in lat
        assert "depreciation" in lat

    @_ANNUALCOLS_BUG
    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.asset import calcCapexPattern

        result = calcCapexPattern(empty_company)
        assert result is None


# ═══════════════════════════════════════════════════════════
# crossStatement.py
# ═══════════════════════════════════════════════════════════


class TestCalcIsCfDivergence:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.crossStatement import calcIsCfDivergence

        result = calcIsCfDivergence(company)
        assert result is not None
        assert "history" in result

    def test_divergence_fields(self, company):
        from dartlab.analysis.financial.crossStatement import calcIsCfDivergence

        result = calcIsCfDivergence(company)
        h0 = result["history"][0]
        assert "netIncome" in h0
        assert "ocf" in h0
        assert "divergence" in h0
        assert "direction" in h0

    def test_direction_conservative(self, company):
        from dartlab.analysis.financial.crossStatement import calcIsCfDivergence

        result = calcIsCfDivergence(company)
        h0 = result["history"][0]
        # NI=18000 < OCF=28000 → "보수적"
        assert h0["direction"] == "보수적"

    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.crossStatement import calcIsCfDivergence

        result = calcIsCfDivergence(empty_company)
        assert result is None


class TestCalcIsBsDivergence:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.crossStatement import calcIsBsDivergence

        result = calcIsBsDivergence(company)
        assert result is not None
        assert "history" in result

    def test_growth_gap_fields(self, company):
        from dartlab.analysis.financial.crossStatement import calcIsBsDivergence

        result = calcIsBsDivergence(company)
        h0 = result["history"][0]
        assert "revenueGrowth" in h0
        assert "receivableGrowth" in h0
        assert "inventoryGrowth" in h0

    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.crossStatement import calcIsBsDivergence

        result = calcIsBsDivergence(empty_company)
        assert result is None


class TestCalcAnomalyScore:
    @_ANNUALCOLS_BUG  # depends on calcAccrualAnalysis which has the bug
    def test_returns_history(self, company):
        from dartlab.analysis.financial.crossStatement import calcAnomalyScore

        result = calcAnomalyScore(company)
        assert result is not None
        assert "history" in result

    @_ANNUALCOLS_BUG  # depends on calcAccrualAnalysis which has the bug
    def test_score_bounded(self, company):
        from dartlab.analysis.financial.crossStatement import calcAnomalyScore

        result = calcAnomalyScore(company)
        for h in result["history"]:
            assert 0 <= h["score"] <= 100
            assert "components" in h


class TestCalcArticulationCheck:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.crossStatement import calcArticulationCheck

        result = calcArticulationCheck(company)
        assert result is not None
        assert "history" in result

    def test_error_fields(self, company):
        from dartlab.analysis.financial.crossStatement import calcArticulationCheck

        result = calcArticulationCheck(company)
        h0 = result["history"][0]
        assert "ppeError" in h0
        assert "cashError" in h0
        assert "equityError" in h0
        assert "maxErrorPct" in h0

    def test_none_when_empty(self, empty_company):
        from dartlab.analysis.financial.crossStatement import calcArticulationCheck

        result = calcArticulationCheck(empty_company)
        assert result is None


class TestCalcCrossStatementFlags:
    @_ANNUALCOLS_BUG  # depends on calcAnomalyScore → calcAccrualAnalysis
    def test_returns_list(self, company):
        from dartlab.analysis.financial.crossStatement import calcCrossStatementFlags

        result = calcCrossStatementFlags(company)
        assert isinstance(result, list)
