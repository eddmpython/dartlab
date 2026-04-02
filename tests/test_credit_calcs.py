"""credit 엔진 단위 테스트 — MockCompany로 합성 데이터 사용.

coverage 대상:
- credit/metrics.py: calcAllMetrics, _div, _cv, _toDict, _annualCols
- credit/engine.py: evaluateCompany, _isFinancial, _isHolding, _isCaptiveFinance
- credit/calcs.py: calcCreditMetrics, calcCreditScore
- core/finance/creditScorecard.py: scoreMetric, weightedScore, mapTo20Grade,
    isInvestmentGrade, gradeCategory, cashFlowGrade, creditOutlook, axisScore, notchGrade
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit

# ── SelectResult mock ──


class _SelectResult:
    def __init__(self, df: pl.DataFrame):
        self._df = df

    @property
    def df(self) -> pl.DataFrame:
        return self._df


# ── 합성 데이터 ──

_PERIODS = ["2024", "2023", "2022", "2021", "2020", "2019"]


def _make_df(accounts: dict[str, list[float | None]]) -> pl.DataFrame:
    rows = []
    for name, vals in accounts.items():
        row: dict = {"계정명": name}
        for i, p in enumerate(_PERIODS):
            row[p] = vals[i] if i < len(vals) else None
        rows.append(row)
    return pl.DataFrame(rows)


class _MockNotes:
    def __getattr__(self, name):
        return None


class _MockRatios:
    marketCap = 1_000_000
    beneishMScore = -2.5
    sloanAccrualRatio = -0.03
    ohlsonProbability = 0.01
    altmanZScore = 3.5
    altmanZppScore = 7.0
    piotroskiFScore = 7


class _MockFinance:
    def __init__(self, ratios=None):
        self._ratios = ratios

    @property
    def ratios(self):
        return self._ratios

    @property
    def ratioSeries(self):
        return None


class CreditMockCompany:
    stockCode = "005930"
    corpName = "테스트"
    market = "KOSPI"

    def __init__(self, *, ratios=None, sector=None, corp_name="테스트"):
        self.corpName = corp_name
        self._sector = sector
        self._finance = _MockFinance(ratios)
        self._cache = {}

    @property
    def sector(self):
        return self._sector

    @property
    def finance(self):
        return self._finance

    @property
    def notes(self):
        return _MockNotes()

    @property
    def _notesAccessor(self):
        return _MockNotes()

    def select(self, stmt: str, accounts: list[str]):
        data = _BS if stmt == "BS" else (_IS if stmt == "IS" else _CF)
        filtered = {k: v for k, v in data.items() if k in accounts}
        if not filtered:
            return None
        return _SelectResult(_make_df(filtered))

    def show(self, *args, **kwargs):
        return None

    def governance(self, *args, **kwargs):
        return None


_BS = {
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
    "재고자산": [30_000, 28_000, 26_000, 24_000, 22_000, 20_000],
}

_IS = {
    "매출액": [100_000, 90_000, 80_000, 70_000, 60_000, 50_000],
    "영업이익": [25_000, 21_000, 17_000, 13_000, 9_000, 5_000],
    "당기순이익": [18_000, 15_000, 12_000, 9_000, 6_000, 3_000],
    "금융비용": [2_000, 2_000, 2_000, 2_000, 2_000, 2_000],
    "이자비용": [1_500, 1_500, 1_500, 1_500, 1_500, 1_500],
    "감가상각비": [3_000, 2_800, 2_600, 2_400, 2_200, 2_000],
    "매출총이익": [40_000, 35_000, 30_000, 25_000, 20_000, 15_000],
}

_CF = {
    "영업활동현금흐름": [28_000, 24_000, 20_000, 16_000, 12_000, 8_000],
    "유형자산의취득": [-8_000, -7_000, -6_000, -5_000, -4_000, -3_000],
}


# ── Fixtures ──


@pytest.fixture
def company():
    return CreditMockCompany(ratios=_MockRatios())


@pytest.fixture
def company_no_ratios():
    return CreditMockCompany()


# ═══════════════════════════════════════════════════════════
# core/finance/creditScorecard.py — 순수 함수 테스트
# ═══════════════════════════════════════════════════════════


class TestScoreMetric:
    def test_none_value(self):
        from dartlab.core.finance.creditScorecard import scoreMetric

        bp = {"lower_is_better": True, "breakpoints": [(0, 0), (100, 100)]}
        assert scoreMetric(None, bp) is None

    def test_lower_is_better(self):
        from dartlab.core.finance.creditScorecard import scoreMetric

        bp = {"lower_is_better": True, "breakpoints": [(0, 0), (50, 50), (100, 100)]}
        # 값 0 이하 → 0점(최저 위험)
        assert scoreMetric(-5, bp) == 0
        # 값 100 이상 → 100점(최고 위험)
        assert scoreMetric(150, bp) == 100
        # 중간: 25 → 선형보간 = 25
        result = scoreMetric(25, bp)
        assert result is not None
        assert abs(result - 25) < 1

    def test_higher_is_better(self):
        from dartlab.core.finance.creditScorecard import scoreMetric

        bp = {
            "lower_is_better": False,
            "breakpoints": [(100, 0), (50, 50), (0, 100)],
        }
        # 높은 값 → 낮은 점수(좋음)
        result = scoreMetric(100, bp)
        assert result is not None
        assert result <= 10
        # 낮은 값 → 높은 점수(나쁨)
        result2 = scoreMetric(0, bp)
        assert result2 is not None
        assert result2 >= 90


class TestWeightedScore:
    def test_basic(self):
        from dartlab.core.finance.creditScorecard import weightedScore

        axes = [
            {"score": 20, "weight": 0.5},
            {"score": 40, "weight": 0.5},
        ]
        result = weightedScore(axes)
        assert result == 30.0

    def test_none_axes_excluded(self):
        from dartlab.core.finance.creditScorecard import weightedScore

        axes = [
            {"score": 20, "weight": 0.5},
            {"score": None, "weight": 0.5},
        ]
        # None 축 제외 → weight 재분배 → 20점
        result = weightedScore(axes)
        assert result == 20.0

    def test_all_none(self):
        from dartlab.core.finance.creditScorecard import weightedScore

        axes = [{"score": None, "weight": 0.5}]
        assert weightedScore(axes) == 50.0  # 중립


class TestMapTo20Grade:
    def test_aaa(self):
        from dartlab.core.finance.creditScorecard import mapTo20Grade

        grade, desc, pd = mapTo20Grade(1.0)
        assert grade == "AAA"
        assert pd == 0.0

    def test_d(self):
        from dartlab.core.finance.creditScorecard import mapTo20Grade

        grade, desc, pd = mapTo20Grade(100.0)
        assert grade == "D"
        assert pd == 100.0

    def test_mid_range(self):
        from dartlab.core.finance.creditScorecard import mapTo20Grade

        grade, desc, pd = mapTo20Grade(25.0)
        # 22~27 → BBB
        assert grade == "BBB"

    def test_clamp_negative(self):
        from dartlab.core.finance.creditScorecard import mapTo20Grade

        grade, _, _ = mapTo20Grade(-10.0)
        assert grade == "AAA"


class TestIsInvestmentGrade:
    def test_investment_grades(self):
        from dartlab.core.finance.creditScorecard import isInvestmentGrade

        assert isInvestmentGrade("AAA") is True
        assert isInvestmentGrade("BBB-") is True
        assert isInvestmentGrade("BB+") is False
        assert isInvestmentGrade("D") is False

    def test_unknown_grade(self):
        from dartlab.core.finance.creditScorecard import isInvestmentGrade

        assert isInvestmentGrade("UNKNOWN") is False


class TestGradeCategory:
    def test_categories(self):
        from dartlab.core.finance.creditScorecard import gradeCategory

        assert gradeCategory("AAA") == "최우량"
        assert gradeCategory("A") == "우량"
        assert gradeCategory("BBB") == "적격"
        assert gradeCategory("BB") == "투기"
        assert gradeCategory("B") == "고위험"
        assert gradeCategory("CCC") == "부실"
        assert gradeCategory("D") == "부실"


class TestNotchGrade:
    def test_upgrade(self):
        from dartlab.core.finance.creditScorecard import notchGrade

        # A (index 5) +2 notches 하향 = A- → BBB+ (위험 증가)
        result = notchGrade("A", 2)
        assert result == "BBB+"

    def test_downgrade(self):
        from dartlab.core.finance.creditScorecard import notchGrade

        # A (index 5) -2 notches 상향 = AA → AA- (위험 감소)
        result = notchGrade("A", -2)
        assert result == "AA-"

    def test_clamp_top(self):
        from dartlab.core.finance.creditScorecard import notchGrade

        result = notchGrade("AAA", -5)
        assert result == "AAA"

    def test_clamp_bottom(self):
        from dartlab.core.finance.creditScorecard import notchGrade

        result = notchGrade("D", 5)
        assert result == "D"

    def test_unknown(self):
        from dartlab.core.finance.creditScorecard import notchGrade

        assert notchGrade("UNKNOWN", 1) == "UNKNOWN"


class TestCashFlowGrade:
    def test_ecr1(self):
        from dartlab.core.finance.creditScorecard import cashFlowGrade

        result = cashFlowGrade(20.0, True, 35.0, True)
        assert result == "eCR-1"

    def test_ecr2(self):
        from dartlab.core.finance.creditScorecard import cashFlowGrade

        result = cashFlowGrade(12.0, False, 25.0, True)
        assert result == "eCR-2"

    def test_ecr3(self):
        from dartlab.core.finance.creditScorecard import cashFlowGrade

        result = cashFlowGrade(7.0, False, 5.0, True)
        assert result == "eCR-3"

    def test_ecr4(self):
        from dartlab.core.finance.creditScorecard import cashFlowGrade

        result = cashFlowGrade(2.0, False, 5.0, False)
        assert result == "eCR-4"

    def test_ecr5(self):
        from dartlab.core.finance.creditScorecard import cashFlowGrade

        result = cashFlowGrade(-3.0, False, None, None)
        assert result == "eCR-5"

    def test_ecr6(self):
        from dartlab.core.finance.creditScorecard import cashFlowGrade

        result = cashFlowGrade(-10.0, False, None, None)
        assert result == "eCR-6"

    def test_unknown(self):
        from dartlab.core.finance.creditScorecard import cashFlowGrade

        assert cashFlowGrade(None, None, None) == "eCR-?"


class TestCreditOutlook:
    def test_positive(self):
        from dartlab.core.finance.creditScorecard import creditOutlook

        # 점수 하락 = 개선 = 긍정적
        assert creditOutlook([20, 30]) == "긍정적"

    def test_negative(self):
        from dartlab.core.finance.creditScorecard import creditOutlook

        # 점수 상승 = 악화 = 부정적
        assert creditOutlook([40, 30]) == "부정적"

    def test_stable(self):
        from dartlab.core.finance.creditScorecard import creditOutlook

        assert creditOutlook([30, 32]) == "안정적"

    def test_insufficient(self):
        from dartlab.core.finance.creditScorecard import creditOutlook

        assert creditOutlook([30]) == "N/A"
        assert creditOutlook([]) == "N/A"


class TestAxisScore:
    def test_basic(self):
        from dartlab.core.finance.creditScorecard import axisScore

        scores = [("a", 20.0), ("b", 40.0), ("c", 60.0)]
        assert axisScore(scores) == 40.0

    def test_none_excluded(self):
        from dartlab.core.finance.creditScorecard import axisScore

        scores = [("a", 20.0), ("b", None), ("c", 40.0)]
        assert axisScore(scores) == 30.0

    def test_all_none(self):
        from dartlab.core.finance.creditScorecard import axisScore

        assert axisScore([("a", None)]) is None


class TestEstimatePD:
    def test_known_grade(self):
        from dartlab.core.finance.creditScorecard import estimatePD

        assert estimatePD("AAA") == 0.0
        assert estimatePD("D") == 100.0
        assert estimatePD("BBB") == 0.25

    def test_unknown_grade(self):
        from dartlab.core.finance.creditScorecard import estimatePD

        assert estimatePD("UNKNOWN") == 50.0


# ═══════════════════════════════════════════════════════════
# credit/metrics.py — 내부 함수 테스트
# ═══════════════════════════════════════════════════════════


class TestMetricsHelpers:
    def test_div_basic(self):
        from dartlab.credit.metrics import _div

        assert _div(100, 200) == 0.5
        assert _div(100, 200, pct=True) == 50.0
        assert _div(None, 200) is None
        assert _div(100, 0) is None
        assert _div(100, None) is None

    def test_div_negative_denominator(self):
        from dartlab.credit.metrics import _div

        # abs(b) 사용
        result = _div(100, -200)
        assert result == 0.5

    def test_cv_basic(self):
        from dartlab.credit.metrics import _cv

        # CV of [10, 20, 30] = std/mean*100
        result = _cv([10, 20, 30])
        assert result is not None
        assert result > 0

    def test_cv_insufficient(self):
        from dartlab.credit.metrics import _cv

        assert _cv([10, 20]) is None
        assert _cv([]) is None

    def test_cv_zero_mean(self):
        from dartlab.credit.metrics import _cv

        assert _cv([1, -1, 0]) is None

    def test_annualCols(self):
        from dartlab.credit.metrics import _annualCols

        periods = ["2024", "2023", "2022", "2021", "2024Q4"]
        result = _annualCols(periods, None, 3)
        assert result == ["2024", "2023", "2022"]

    def test_annualCols_basePeriod(self):
        from dartlab.credit.metrics import _annualCols

        periods = ["2024", "2023", "2022"]
        result = _annualCols(periods, "2023", 5)
        assert "2024" not in result
        assert "2023" in result


class TestCalcAllMetrics:
    def test_returns_history(self, company):
        from dartlab.credit.metrics import calcAllMetrics

        result = calcAllMetrics(company)
        assert result is not None
        assert "history" in result
        assert len(result["history"]) >= 2

    def test_metric_keys(self, company):
        from dartlab.credit.metrics import calcAllMetrics

        result = calcAllMetrics(company)
        row = result["history"][0]
        # 축1 지표
        assert "ffoToDebt" in row
        assert "debtToEbitda" in row
        # 축2 지표
        assert "debtRatio" in row
        # 축3 지표
        assert "currentRatio" in row
        # 축4 지표
        assert "ocfToSales" in row

    def test_ebitda_calculation(self, company):
        from dartlab.credit.metrics import calcAllMetrics

        result = calcAllMetrics(company)
        row = result["history"][0]
        # EBITDA = 영업이익 + 감가상각비 = 25000 + 3000 = 28000
        assert row["ebitda"] == 28_000

    def test_total_borrowing(self, company):
        from dartlab.credit.metrics import calcAllMetrics

        result = calcAllMetrics(company)
        row = result["history"][0]
        # 20000 + 30000 + 10000 = 60000
        assert row["totalBorrowing"] == 60_000

    def test_business_stability(self, company):
        from dartlab.credit.metrics import calcAllMetrics

        result = calcAllMetrics(company)
        assert "businessStability" in result


# ═══════════════════════════════════════════════════════════
# credit/engine.py — evaluateCompany 테스트
# ═══════════════════════════════════════════════════════════


class TestEvaluateCompany:
    def test_returns_grade(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        assert result is not None
        assert "grade" in result
        assert result["grade"].startswith("dCR-")

    def test_grade_in_valid_range(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        valid_grades = [
            "AAA",
            "AA+",
            "AA",
            "AA-",
            "A+",
            "A",
            "A-",
            "BBB+",
            "BBB",
            "BBB-",
            "BB+",
            "BB",
            "BB-",
            "B+",
            "B",
            "B-",
            "CCC",
            "CC",
            "C",
            "D",
        ]
        raw = result["gradeRaw"]
        assert raw in valid_grades

    def test_health_score(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        assert "healthScore" in result
        assert "score" in result
        assert abs(result["healthScore"] - (100 - result["score"])) < 0.1

    def test_axes_count(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        assert "axes" in result
        assert len(result["axes"]) == 7

    def test_axes_structure(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        for axis in result["axes"]:
            assert "name" in axis
            assert "score" in axis
            assert "weight" in axis
            assert "metrics" in axis

    def test_ecr_grade(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        assert "eCR" in result
        assert result["eCR"].startswith("eCR-")

    def test_outlook(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        assert "outlook" in result
        assert result["outlook"] in {"긍정적", "부정적", "안정적", "N/A"}

    def test_investment_grade_bool(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        assert "investmentGrade" in result
        assert isinstance(result["investmentGrade"], bool)

    def test_grade_category(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company)
        assert "gradeCategory" in result
        valid = {"최우량", "우량", "적격", "투기", "고위험", "부실"}
        assert result["gradeCategory"] in valid

    def test_detail_mode(self, company):
        from dartlab.credit.engine import evaluateCompany

        result = evaluateCompany(company, detail=True)
        assert result is not None
        assert "metricsHistory" in result
        assert "narratives" in result

    def test_holding_company(self):
        from dartlab.credit.engine import evaluateCompany

        co = CreditMockCompany(corp_name="테스트홀딩스", ratios=_MockRatios())
        result = evaluateCompany(co)
        if result is not None:
            assert result["holding"] is True


# ═══════════════════════════════════════════════════════════
# credit/engine.py — 내부 함수 직접 테스트
# ═══════════════════════════════════════════════════════════


class TestEngineHelpers:
    def test_isHolding(self):
        from dartlab.credit.engine import _isHolding

        class _Co:
            corpName = "삼성홀딩스"

        assert _isHolding(_Co()) is True

        class _Co2:
            corpName = "삼성전자"

        assert _isHolding(_Co2()) is False

    def test_isFinancial_no_sector(self):
        from dartlab.credit.engine import _isFinancial

        class _Co:
            sector = None

        assert _isFinancial(_Co()) is False

    def test_isCaptiveFinance(self):
        from dartlab.credit.engine import _isCaptiveFinance

        # totalBorrowing/ebitda > 15 → captive
        assert _isCaptiveFinance(160_000, 10_000, False) is True
        assert _isCaptiveFinance(100_000, 10_000, False) is False
        # 금융업은 대상 아님
        assert _isCaptiveFinance(160_000, 10_000, True) is False
        # ebitda 0 이하
        assert _isCaptiveFinance(160_000, 0, False) is False
        assert _isCaptiveFinance(160_000, -100, False) is False
