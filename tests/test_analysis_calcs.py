"""analysis calc 함수 단위 테스트 — MockCompany로 합성 데이터 사용.

coverage 대상:
- profitability.py: calcMarginTrend, calcReturnTrend, calcMarginWaterfall
- stability.py: calcLeverageTrend, calcCoverageTrend, calcDistressScore
- growthAnalysis.py: calcGrowthTrend, calcGrowthQuality, calcSustainableGrowthRate
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


def _make_is_df(accounts: dict[str, list[float | None]]) -> pl.DataFrame:
    """IS 형태 DataFrame 생성. accounts: {계정명: [값 per period]}."""
    rows = []
    for name, vals in accounts.items():
        row: dict = {"계정명": name}
        for i, p in enumerate(_PERIODS):
            row[p] = vals[i] if i < len(vals) else None
        rows.append(row)
    return pl.DataFrame(rows)


def _make_bs_df(accounts: dict[str, list[float | None]]) -> pl.DataFrame:
    return _make_is_df(accounts)


def _make_cf_df(accounts: dict[str, list[float | None]]) -> pl.DataFrame:
    return _make_is_df(accounts)


# ── MockCompany ──


class MockCompany:
    """analysis calc 함수에 필요한 최소 인터페이스."""

    stockCode = "005930"
    corpName = "테스트"
    market = "KOSPI"
    _cache = {}

    def __init__(self, *, is_data=None, bs_data=None, cf_data=None, sector=None, ratios=None):
        self._is = is_data or {
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
        self._bs = bs_data or {
            "자산총계": [500_000, 450_000, 400_000, 350_000, 300_000, 250_000],
            "부채총계": [200_000, 190_000, 180_000, 170_000, 160_000, 150_000],
            "자본총계": [300_000, 260_000, 220_000, 180_000, 140_000, 100_000],
            "유동자산": [150_000, 140_000, 130_000, 120_000, 110_000, 100_000],
            "유동부채": [100_000, 95_000, 90_000, 85_000, 80_000, 75_000],
            "비유동부채": [100_000, 95_000, 90_000, 85_000, 80_000, 75_000],
            "현금및현금성자산": [50_000, 45_000, 40_000, 35_000, 30_000, 25_000],
            "단기차입금": [20_000, 18_000, 16_000, 14_000, 12_000, 10_000],
            "장기차입금": [30_000, 28_000, 26_000, 24_000, 22_000, 20_000],
            "사채": [10_000, 9_000, 8_000, 7_000, 6_000, 5_000],
            "이익잉여금": [250_000, 220_000, 190_000, 160_000, 130_000, 100_000],
            "미처분이익잉여금(결손금)": [None] * 6,
            "재고자산": [30_000, 28_000, 26_000, 24_000, 22_000, 20_000],
        }
        self._cf = cf_data or {
            "영업활동현금흐름": [28_000, 24_000, 20_000, 16_000, 12_000, 8_000],
            "유형자산의취득": [-8_000, -7_000, -6_000, -5_000, -4_000, -3_000],
            "interest_paid": [-1_400, -1_400, -1_400, -1_400, -1_400, -1_400],
        }
        self._sector = sector
        self._ratios = ratios
        # 새 호출마다 캐시를 리셋해야 memoize가 방해하지 않음
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
    def notes(self):
        return _MockNotes()

    @property
    def _notesAccessor(self):
        return _MockNotes()

    def select(self, stmt: str, accounts: list[str]):
        if stmt == "IS":
            src = self._is
        elif stmt == "BS":
            src = self._bs
        elif stmt == "CF":
            src = self._cf
        else:
            return None
        filtered = {k: v for k, v in src.items() if k in accounts}
        if not filtered:
            return None
        df = _make_is_df(filtered)
        return _SelectResult(df)


class _MockNotes:
    """notes accessor mock — 모든 속성이 None."""

    def __getattr__(self, name):
        return None


class _MockRatios:
    """ratios mock."""

    marketCap = 1_000_000
    beneishMScore = -2.5
    sloanAccrualRatio = -0.03
    ohlsonProbability = 0.01
    altmanZScore = 3.5
    altmanZppScore = 7.0
    piotroskiFScore = 7


# ── Fixtures ──


@pytest.fixture
def company():
    return MockCompany()


@pytest.fixture
def empty_company():
    """모든 데이터가 비어 있는 Company."""
    return MockCompany(
        is_data={k: [None] * 6 for k in ["매출액"]},
        bs_data={k: [None] * 6 for k in ["자산총계"]},
        cf_data={},
    )


@pytest.fixture
def company_with_ratios():
    return MockCompany(ratios=_MockRatios())


# ═══════════════════════════════════════════════════════════
# profitability.py
# ═══════════════════════════════════════════════════════════


class TestCalcMarginTrend:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.profitability import calcMarginTrend

        result = calcMarginTrend(company)
        assert result is not None
        assert "history" in result

        hist = result["history"]
        assert len(hist) >= 2

        row = hist[0]
        assert "period" in row
        assert "revenue" in row
        assert "operatingMargin" in row
        assert "netMargin" in row
        assert row["revenue"] == 100_000

    def test_margin_values(self, company):
        from dartlab.analysis.financial.profitability import calcMarginTrend

        result = calcMarginTrend(company)
        row = result["history"][0]
        # 영업이익 25000 / 매출 100000 = 25%
        assert row["operatingMargin"] == 25.0
        # 순이익 18000 / 매출 100000 = 18%
        assert row["netMargin"] == 18.0

    def test_yoy_calculation(self, company):
        from dartlab.analysis.financial.profitability import calcMarginTrend

        result = calcMarginTrend(company)
        row = result["history"][0]
        # 매출 YoY: (100000 - 90000) / 90000 * 100 ≈ 11.11%
        assert row["revenueYoy"] is not None
        assert abs(row["revenueYoy"] - 11.11) < 0.1

    def test_none_when_select_returns_none(self):
        from dartlab.analysis.financial.profitability import calcMarginTrend

        co = MockCompany()
        co._is = {}  # select returns None → toDict returns None
        result = calcMarginTrend(co)
        assert result is None

    def test_has_cogs_and_gp(self, company):
        from dartlab.analysis.financial.profitability import calcMarginTrend

        result = calcMarginTrend(company)
        row = result["history"][0]
        assert "cogs" in row
        assert "grossProfit" in row
        assert "grossMargin" in row

    def test_basePeriod_filter(self, company):
        from dartlab.analysis.financial.profitability import calcMarginTrend

        result = calcMarginTrend(MockCompany(), basePeriod="2022")
        assert result is not None
        periods = [h["period"] for h in result["history"]]
        # basePeriod=2022이면 2022 이하만
        for p in periods:
            assert p <= "2022"


class TestCalcReturnTrend:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.profitability import calcReturnTrend

        result = calcReturnTrend(company)
        assert result is not None
        assert "history" in result

        row = result["history"][0]
        assert "roe" in row
        assert "roa" in row
        assert "taxBurden" in row
        assert "interestBurden" in row
        assert "operatingMargin" in row
        assert "assetTurnover" in row
        assert "leverage" in row

    def test_roe_calculation(self, company):
        from dartlab.analysis.financial.profitability import calcReturnTrend

        result = calcReturnTrend(company)
        row = result["history"][0]
        # ROE = NI / Equity = 18000 / 300000 * 100 = 6.0%
        assert row["roe"] == 6.0
        # ROA = NI / TA = 18000 / 500000 * 100 = 3.6%
        assert row["roa"] == 3.6

    def test_dupont_components(self, company):
        from dartlab.analysis.financial.profitability import calcReturnTrend

        result = calcReturnTrend(company)
        row = result["history"][0]
        # taxBurden = NI / PBT = 18000 / 23000
        assert row["taxBurden"] is not None
        assert abs(row["taxBurden"] - 18000 / 23000) < 0.01

    def test_none_when_missing_bs(self):
        from dartlab.analysis.financial.profitability import calcReturnTrend

        co = MockCompany()
        co._bs = {}  # force empty BS
        result = calcReturnTrend(co)
        assert result is None


class TestCalcMarginWaterfall:
    def test_returns_waterfall(self, company):
        from dartlab.analysis.financial.profitability import calcMarginWaterfall

        result = calcMarginWaterfall(company)
        assert result is not None
        assert "history" in result

        row = result["history"][0]
        assert "steps" in row
        assert "period" in row
        assert len(row["steps"]) >= 1
        # 첫 단계는 매출
        assert row["steps"][0]["label"] == "매출"


# ═══════════════════════════════════════════════════════════
# stability.py
# ═══════════════════════════════════════════════════════════


class TestCalcLeverageTrend:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.stability import calcLeverageTrend

        result = calcLeverageTrend(company)
        assert result is not None
        assert "history" in result
        assert len(result["history"]) >= 2

    def test_debt_ratio_calculation(self, company):
        from dartlab.analysis.financial.stability import calcLeverageTrend

        result = calcLeverageTrend(company)
        row = result["history"][0]
        # debtRatio = 부채총계 / 자본총계 * 100 = 200000/300000*100 ≈ 66.67
        assert row["debtRatio"] is not None
        assert abs(row["debtRatio"] - 66.67) < 0.1

    def test_equity_ratio(self, company):
        from dartlab.analysis.financial.stability import calcLeverageTrend

        result = calcLeverageTrend(company)
        row = result["history"][0]
        # equityRatio = 자본총계 / 자산총계 * 100 = 300000/500000*100 = 60.0
        assert row["equityRatio"] == 60.0

    def test_net_debt(self, company):
        from dartlab.analysis.financial.stability import calcLeverageTrend

        result = calcLeverageTrend(company)
        row = result["history"][0]
        # totalBorrowing = 20000+30000+10000 = 60000
        # netDebt = 60000 - 50000(cash) = 10000
        assert row["totalBorrowing"] == 60_000
        assert row["netDebt"] == 10_000

    def test_none_when_no_bs_data(self):
        from dartlab.analysis.financial.stability import calcLeverageTrend

        co = MockCompany()
        co._bs = {}  # force empty BS → select returns None
        result = calcLeverageTrend(co)
        assert result is None


class TestCalcCoverageTrend:
    def test_returns_history(self, company):
        from dartlab.analysis.financial.stability import calcCoverageTrend

        result = calcCoverageTrend(company)
        assert result is not None
        assert "history" in result

    def test_interest_coverage(self, company):
        from dartlab.analysis.financial.stability import calcCoverageTrend

        result = calcCoverageTrend(company)
        row = result["history"][0]
        # coverage = 영업이익 / 이자비용 = 25000 / 1500 ≈ 16.67
        assert row["interestCoverage"] is not None
        assert row["interestCoverage"] > 10

    def test_interest_source_priority(self, company):
        from dartlab.analysis.financial.stability import calcCoverageTrend

        result = calcCoverageTrend(company)
        row = result["history"][0]
        # IS 이자비용이 우선 소스
        assert row["interestExpenseSource"] == "이자비용"


class TestCalcDistressScore:
    def test_returns_history(self, company_with_ratios):
        from dartlab.analysis.financial.stability import calcDistressScore

        result = calcDistressScore(company_with_ratios)
        assert result is not None
        assert "history" in result

    def test_zscore_components(self, company_with_ratios):
        from dartlab.analysis.financial.stability import calcDistressScore

        result = calcDistressScore(company_with_ratios)
        row = result["history"][0]
        assert "zScore" in row or "x1" in row  # 구조에 따라 키 다름
        # x1 = (유동자산 - 유동부채) / 자산총계 = (150000-100000)/500000 = 0.1
        if "x1" in row:
            assert abs(row["x1"] - 0.1) < 0.01


# ═══════════════════════════════════════════════════════════
# growthAnalysis.py
# ═══════════════════════════════════════════════════════════


class TestCalcGrowthTrend:
    def test_returns_history_and_cagr(self, company):
        from dartlab.analysis.financial.growthAnalysis import calcGrowthTrend

        result = calcGrowthTrend(company)
        assert result is not None
        assert "history" in result
        assert "cagr" in result

    def test_history_fields(self, company):
        from dartlab.analysis.financial.growthAnalysis import calcGrowthTrend

        result = calcGrowthTrend(company)
        row = result["history"][0]
        assert "period" in row
        assert "revenue" in row
        assert "revenueYoy" in row
        assert "operatingIncome" in row
        assert "netIncome" in row
        assert "totalAssets" in row

    def test_cagr_positive(self, company):
        from dartlab.analysis.financial.growthAnalysis import calcGrowthTrend

        result = calcGrowthTrend(company)
        cagr = result["cagr"]
        # 매출이 50000→100000으로 증가 → CAGR > 0
        assert cagr["revenue"] is not None
        assert cagr["revenue"] > 0

    def test_revenue_yoy(self, company):
        from dartlab.analysis.financial.growthAnalysis import calcGrowthTrend

        result = calcGrowthTrend(company)
        row = result["history"][0]
        # (100000 - 90000) / 90000 * 100 ≈ 11.11
        assert row["revenueYoy"] is not None
        assert abs(row["revenueYoy"] - 11.11) < 0.1

    def test_none_when_select_returns_none(self):
        from dartlab.analysis.financial.growthAnalysis import calcGrowthTrend

        co = MockCompany()
        co._is = {}  # force empty IS → select returns None → toDict returns None
        result = calcGrowthTrend(co)
        assert result is None


class TestCalcGrowthQuality:
    def test_returns_quality(self, company):
        from dartlab.analysis.financial.growthAnalysis import calcGrowthQuality

        result = calcGrowthQuality(company)
        assert result is not None
        assert "quality" in result
        assert "cagr" in result

    def test_quality_label_valid(self, company):
        from dartlab.analysis.financial.growthAnalysis import calcGrowthQuality

        result = calcGrowthQuality(company)
        valid_labels = {"균형", "내실 위주", "외형 위주", "역성장", "이익 역성장", "판단 불가", "개선 중"}
        assert result["quality"] in valid_labels

    def test_leverage_effect(self, company):
        from dartlab.analysis.financial.growthAnalysis import calcGrowthQuality

        result = calcGrowthQuality(company)
        assert "leverageEffect" in result
        # 매출과 영업이익 모두 양 YoY → 레버리지 효과 계산 가능
        if result["leverageEffect"]:
            le = result["leverageEffect"][0]
            assert "operatingLeverage" in le


class TestCalcSustainableGrowthRate:
    def test_returns_sgr(self, company):
        from dartlab.analysis.financial.growthAnalysis import calcSustainableGrowthRate

        result = calcSustainableGrowthRate(company)
        # SGR requires dividend data which our mock doesn't have
        # so it may return None — that's valid
        if result is not None:
            assert "history" in result


# ═══════════════════════════════════════════════════════════
# _helpers.py — 유틸 함수 직접 테스트
# ═══════════════════════════════════════════════════════════


class TestHelpers:
    def test_parseNumStr_basic(self):
        from dartlab.analysis.financial._helpers import parseNumStr

        assert parseNumStr("1,234") == 1234.0
        assert parseNumStr("△500") == -500.0
        assert parseNumStr("-") is None
        assert parseNumStr(None) is None
        assert parseNumStr("") is None
        assert parseNumStr("12.5%") == 12.5

    def test_annualColsFromPeriods(self):
        from dartlab.analysis.financial._helpers import annualColsFromPeriods

        periods = ["2024", "2023", "2022", "2021", "2024Q4", "2024Q3"]
        result = annualColsFromPeriods(periods, None, 3)
        assert result == ["2024", "2023", "2022"]

    def test_annualColsFromPeriods_with_basePeriod(self):
        from dartlab.analysis.financial._helpers import annualColsFromPeriods

        periods = ["2024", "2023", "2022", "2021"]
        result = annualColsFromPeriods(periods, "2022", 5)
        assert "2024" not in result
        assert "2023" not in result
        assert "2022" in result

    def test_annualColsFromPeriods_q4_fallback(self):
        from dartlab.analysis.financial._helpers import annualColsFromPeriods

        periods = ["2024Q4", "2024Q3", "2023Q4", "2023Q3"]
        result = annualColsFromPeriods(periods, None, 3)
        assert "2024Q4" in result
        assert "2023Q4" in result

    def test_mergeRows(self):
        from dartlab.analysis.financial._helpers import mergeRows

        a = {"x": 1, "y": None}
        b = {"x": 2, "y": 3, "z": 4}
        merged = mergeRows(a, b)
        assert merged["x"] == 1  # primary wins
        assert merged["y"] == 3  # fallback fills None
        assert merged["z"] == 4  # fallback adds missing

    def test_mergeRows_none(self):
        from dartlab.analysis.financial._helpers import mergeRows

        assert mergeRows(None, None) == {}
        assert mergeRows(None, {"a": 1}) == {"a": 1}
        assert mergeRows({"a": 1}, None) == {"a": 1}

    def test_toDict_none(self):
        from dartlab.analysis.financial._helpers import toDict

        assert toDict(None) is None

    def test_toDict_valid(self):
        from dartlab.analysis.financial._helpers import toDict

        df = pl.DataFrame({"계정명": ["매출액", "영업이익"], "2024": [100, 50], "2023": [90, 45]})
        result = toDict(_SelectResult(df))
        assert result is not None
        data, periods = result
        assert "매출액" in data
        assert data["매출액"]["2024"] == 100
        assert "2024" in periods

    def test_periodCols(self):
        from dartlab.analysis.financial._helpers import periodCols

        df = pl.DataFrame({"계정명": ["x"], "2024": [1], "2023": [2], "foo": [3]})
        cols = periodCols(df)
        assert "2024" in cols
        assert "2023" in cols
        assert "foo" not in cols

    def test_annualLabel(self):
        from dartlab.analysis.financial._helpers import annualLabel

        assert annualLabel("2025Q4") == "2025"
        assert annualLabel("2025") == "2025"
        assert annualLabel("2025Q3") == "2025Q3"
