"""Pro-Forma 3-Statement 엔진 테스트.

extract_historical_ratios, compute_company_wacc, build_proforma 검증.
"""

from __future__ import annotations

import pytest

from dartlab.analysis.forecast.simulation import SectorElasticity
from dartlab.core.finance.proforma import (
    ProFormaResult,
    _extract_base_year,
    _median,
    _remove_outliers_iqr,
    _safe_ratio_list,
    _weighted_ratio,
    build_proforma,
    compute_company_wacc,
    extract_historical_ratios,
)

# ── Mock 시계열 ──────────────────────────────────────────

# 8분기 = 2년치 (가장 최근 4분기가 TTM)
SERIES: dict = {
    "IS": {
        "sales": [250, 250, 250, 250, 300, 300, 300, 300],
        "gross_profit": [75, 75, 75, 75, 90, 90, 90, 90],
        "selling_and_administrative_expenses": [25, 25, 25, 25, 30, 30, 30, 30],
        "profit_before_tax": [40, 40, 40, 40, 48, 48, 48, 48],
        "income_tax_expense": [8, 8, 8, 8, 10, 10, 10, 10],
        "finance_costs": [2, 2, 2, 2, 3, 3, 3, 3],
        "net_profit": [32, 32, 32, 32, 38, 38, 38, 38],
    },
    "CF": {
        "depreciation_and_amortization": [10, 10, 10, 10, 12, 12, 12, 12],
        "purchase_of_property_plant_and_equipment": [-15, -15, -15, -15, -18, -18, -18, -18],
        "dividends_paid": [-8, -8, -8, -8, -10, -10, -10, -10],
    },
    "BS": {
        "current_assets": [None, None, None, 500, None, None, None, 600],
        "current_liabilities": [None, None, None, 200, None, None, None, 240],
        "cash_and_cash_equivalents": [None, None, None, 100, None, None, None, 120],
        "shortterm_borrowings": [None, None, None, 50, None, None, None, 60],
        "longterm_borrowings": [None, None, None, 100, None, None, None, 120],
        "debentures": [None, None, None, 0, None, None, None, 0],
        "trade_receivables": [None, None, None, 150, None, None, None, 180],
        "inventories": [None, None, None, 120, None, None, None, 140],
        "trade_payables": [None, None, None, 80, None, None, None, 90],
        "tangible_assets": [None, None, None, 400, None, None, None, 450],
        "total_assets": [None, None, None, 1000, None, None, None, 1200],
        "total_liabilities": [None, None, None, 400, None, None, None, 480],
        "total_stockholders_equity": [None, None, None, 600, None, None, None, 720],
    },
}

# 매출 0인 시계열
EMPTY_SERIES: dict = {
    "IS": {"sales": [0, 0, 0, 0]},
    "CF": {},
    "BS": {},
}


# ── _median ──────────────────────────────────────────────


class TestMedian:
    def test_empty(self):
        assert _median([]) == 0.0

    def test_odd(self):
        assert _median([3, 1, 2]) == 2

    def test_even(self):
        assert _median([1, 2, 3, 4]) == 2.5

    def test_single(self):
        assert _median([7]) == 7


# ── _safe_ratio_list ─────────────────────────────────────


class TestSafeRatioList:
    def test_basic(self):
        result = _safe_ratio_list([30, 60], [100, 200])
        assert result == [30.0, 30.0]

    def test_zero_denominator(self):
        result = _safe_ratio_list([30, 60], [0, 200])
        assert len(result) == 1
        assert result[0] == 30.0

    def test_no_pct(self):
        result = _safe_ratio_list([10], [100], pct=False)
        assert result == [0.1]


# ── extract_historical_ratios ────────────────────────────


class TestExtractHistoricalRatios:
    @pytest.mark.unit
    def test_basic_extraction(self):
        ratios = extract_historical_ratios(SERIES, years=5)

        # 매출총이익률 = 75/250=30%, 90/300=30% → 중위 30%
        assert 29 < ratios.gross_margin < 31

        # 판관비율 = 25/250=10%, 30/300=10% → 10%
        assert 9 < ratios.sga_ratio < 11

        # 유효세율 = 8*4/40*4 = 32/160=20%, 10*4/48*4=40/192≈20.8%
        assert 15 < ratios.effective_tax_rate < 25

        # 감가상각/매출 = 40/1000=4%, 48/1200=4%
        assert 3 < ratios.depreciation_ratio < 5

        # CAPEX/매출 = 60/1000=6%, 72/1200=6%
        assert 5 < ratios.capex_to_revenue < 7

        assert ratios.years_used >= 2
        assert ratios.confidence in ("high", "medium")

    @pytest.mark.unit
    def test_missing_data_uses_defaults(self):
        empty = {"IS": {}, "CF": {}, "BS": {}}
        ratios = extract_historical_ratios(empty, years=5)
        # 기본값 사용
        assert ratios.gross_margin == 30.0
        assert ratios.sga_ratio == 15.0
        # D&A = CAPEX(5%) × 80% = 4% (CAPEX 기본값 있으면 CAPEX 연동)
        assert ratios.depreciation_ratio == 4.0
        assert ratios.capex_to_revenue == 5.0
        assert ratios.confidence == "low"
        assert len(ratios.warnings) > 0

    @pytest.mark.unit
    def test_repr(self):
        ratios = extract_historical_ratios(SERIES)
        text = repr(ratios)
        assert "과거 비율 분석" in text
        assert "매출총이익률" in text


# ── compute_company_wacc ─────────────────────────────────


class TestComputeWACC:
    @pytest.mark.unit
    def test_basic_wacc(self):
        wacc, details = compute_company_wacc(SERIES)
        # WACC = 5~20% 범위 내
        assert 5.0 <= wacc <= 20.0
        assert "ke" in details
        assert "kd" in details
        assert "equity_weight" in details
        assert "debt_weight" in details
        # 가중치 합 = 100%
        assert abs(details["equity_weight"] + details["debt_weight"] - 100) < 0.1

    @pytest.mark.unit
    def test_no_debt(self):
        no_debt = {
            "IS": SERIES["IS"],
            "CF": SERIES["CF"],
            "BS": {
                "shortterm_borrowings": [None, None, None, 0, None, None, None, 0],
                "longterm_borrowings": [None, None, None, 0, None, None, None, 0],
                "debentures": [None, None, None, 0, None, None, None, 0],
                "total_stockholders_equity": SERIES["BS"]["total_stockholders_equity"],
            },
        }
        wacc, details = compute_company_wacc(no_debt)
        # 부채 없으면 equity 100%, WACC ≈ Ke
        assert details["debt_weight"] < 1.0
        assert details["equity_weight"] > 99.0

    @pytest.mark.unit
    def test_with_market_cap(self):
        wacc1, _ = compute_company_wacc(SERIES)
        wacc2, details2 = compute_company_wacc(SERIES, market_cap=5000)
        # 시가총액이 장부가보다 크면 equity weight 증가 → WACC 변화
        assert isinstance(wacc2, float)
        assert details2["equity_value"] == 5000


# ── _extract_base_year ───────────────────────────────────


class TestExtractBaseYear:
    @pytest.mark.unit
    def test_basic(self):
        base = _extract_base_year(SERIES)
        # TTM 매출 = 300*4 = 1200
        assert base["revenue"] == 1200
        # 최신 현금 = 120
        assert base["cash"] == 120
        assert base["ppe_net"] == 450
        assert base["receivables"] == 180
        assert base["inventories"] == 140
        assert base["payables"] == 90

    @pytest.mark.unit
    def test_empty_series(self):
        base = _extract_base_year(EMPTY_SERIES)
        assert base["revenue"] == 0


# ── build_proforma ───────────────────────────────────────


class TestBuildProforma:
    @pytest.mark.unit
    def test_basic_build(self):
        result = build_proforma(SERIES, revenue_growth_path=[5.0, 4.0, 3.0])
        assert isinstance(result, ProFormaResult)
        assert len(result.projections) == 3
        assert result.scenario_name == "base"

    @pytest.mark.unit
    def test_revenue_growth(self):
        result = build_proforma(SERIES, revenue_growth_path=[10.0, 10.0])
        p1, p2 = result.projections
        base_rev = result.base_year["revenue"]
        assert abs(p1.revenue - base_rev * 1.1) < 1
        assert abs(p2.revenue - base_rev * 1.1 * 1.1) < 1

    @pytest.mark.unit
    def test_zero_growth(self):
        result = build_proforma(SERIES, revenue_growth_path=[0.0, 0.0])
        p1, p2 = result.projections
        base_rev = result.base_year["revenue"]
        assert abs(p1.revenue - base_rev) < 1
        assert abs(p2.revenue - base_rev) < 1

    @pytest.mark.unit
    def test_bs_balance(self):
        """BS 항등식: 총자산 = 총부채 + 총자본."""
        result = build_proforma(SERIES, revenue_growth_path=[5.0, 4.0, 3.0, 2.0, 1.0])
        for p in result.projections:
            assert p.bs_balanced, (
                f"+{p.year_offset}년 BS 불균형: {p.total_assets} != {p.total_liabilities} + {p.total_equity}"
            )
            diff = abs(p.total_assets - p.total_liabilities - p.total_equity)
            assert diff < 1, f"+{p.year_offset}년 BS 차이: {diff}"

    @pytest.mark.unit
    def test_cf_consistency(self):
        """CF: delta_cash ≈ OCF + ICF + FinCF (plug 방식이라 정확하지 않을 수 있지만 방향 확인)."""
        result = build_proforma(SERIES, revenue_growth_path=[5.0, 3.0])
        for p in result.projections:
            # OCF + CAPEX + FinCF = net_cash_change
            computed = p.ocf + p.capex + p.financing_cf
            assert abs(computed - p.net_cash_change) < 1, (
                f"+{p.year_offset}년 CF 불일치: {computed} != {p.net_cash_change}"
            )

    @pytest.mark.unit
    def test_is_consistency(self):
        """IS 항등식: gross_profit = revenue - cogs, ebt = oi - interest."""
        result = build_proforma(SERIES, revenue_growth_path=[5.0])
        p = result.projections[0]
        assert abs(p.gross_profit - (p.revenue - p.cogs)) < 1
        assert abs(p.ebt - (p.operating_income - p.interest_expense)) < 1
        assert abs(p.net_income - (p.ebt - p.tax)) < 1
        assert abs(p.ebitda - (p.operating_income + p.depreciation)) < 1

    @pytest.mark.unit
    def test_zero_revenue_returns_empty(self):
        result = build_proforma(EMPTY_SERIES, revenue_growth_path=[5.0])
        assert len(result.projections) == 0
        assert any("매출이 0" in w for w in result.warnings)

    @pytest.mark.unit
    def test_negative_growth(self):
        result = build_proforma(SERIES, revenue_growth_path=[-10.0, -5.0])
        p1 = result.projections[0]
        base_rev = result.base_year["revenue"]
        assert p1.revenue < base_rev

    @pytest.mark.unit
    def test_overrides(self):
        result = build_proforma(
            SERIES,
            revenue_growth_path=[5.0],
            overrides={"gross_margin": 50.0},
        )
        p = result.projections[0]
        expected_gp = p.revenue * 0.5
        assert abs(p.gross_profit - expected_gp) < 1

    @pytest.mark.unit
    def test_repr(self):
        result = build_proforma(SERIES, revenue_growth_path=[5.0, 4.0])
        text = repr(result)
        assert "Pro-Forma" in text
        assert "손익계산서" in text
        assert "대차대조표" in text
        assert "현금흐름표" in text

    @pytest.mark.unit
    def test_fcf_sign(self):
        """FCF = OCF + CAPEX (CAPEX 음수) → OCF > |CAPEX| 이면 FCF 양수."""
        result = build_proforma(SERIES, revenue_growth_path=[5.0])
        p = result.projections[0]
        assert p.capex < 0  # CAPEX는 음수
        assert p.fcf == p.ocf + p.capex

    @pytest.mark.unit
    def test_wacc_in_result(self):
        result = build_proforma(SERIES, revenue_growth_path=[5.0])
        assert 5.0 <= result.wacc <= 20.0
        assert "ke" in result.wacc_details


# ── v2: _remove_outliers_iqr ──────────────────────────────


class TestRemoveOutliersIQR:
    def test_no_outliers(self):
        data = [10.0, 11.0, 12.0, 13.0, 14.0]
        assert _remove_outliers_iqr(data) == data

    def test_with_outlier(self):
        data = [10.0, 11.0, 12.0, 13.0, 100.0]
        cleaned = _remove_outliers_iqr(data)
        assert 100.0 not in cleaned
        assert len(cleaned) < len(data)

    def test_small_list_untouched(self):
        data = [1.0, 2.0, 3.0]
        assert _remove_outliers_iqr(data) == data


# ── v2: _weighted_ratio ───────────────────────────────────


class TestWeightedRatio:
    def test_empty(self):
        val, trend = _weighted_ratio([])
        assert val == 0.0
        assert trend == 0.0

    def test_single(self):
        val, trend = _weighted_ratio([42.0])
        assert val == 42.0
        assert trend == 0.0

    def test_constant_no_trend(self):
        val, trend = _weighted_ratio([30.0, 30.0, 30.0, 30.0])
        assert abs(val - 30.0) < 1.0
        assert abs(trend) < 0.1

    def test_upward_trend(self):
        val, trend = _weighted_ratio([20.0, 22.0, 24.0, 26.0, 28.0])
        # 최근 가중 → 28에 가까움
        assert val > 24.0
        # 상승 트렌드
        assert trend > 0

    def test_recent_weighted_higher(self):
        """최근 값이 높으면 가중 평균이 단순 중위값보다 높아야 함."""
        vals = [20.0, 22.0, 25.0, 28.0, 30.0]
        weighted_val, _ = _weighted_ratio(vals)
        simple_median = sorted(vals)[len(vals) // 2]
        assert weighted_val > simple_median


# ── v2: 트렌드 반영 확인 ──────────────────────────────────


class TestTrendInHistoricalRatios:
    @pytest.mark.unit
    def test_trends_populated(self):
        ratios = extract_historical_ratios(SERIES)
        assert isinstance(ratios.trends, dict)
        # 최소한 gross_margin 트렌드가 있어야 함
        assert "gross_margin" in ratios.trends

    @pytest.mark.unit
    def test_trends_in_repr(self):
        ratios = extract_historical_ratios(SERIES)
        # SERIES는 비율 변동이 없으므로 트렌드 == 0 → repr에 안 나올 수 있음
        text = repr(ratios)
        assert "과거 비율 분석" in text


# ── v2: 자동 차입 ─────────────────────────────────────────


class TestAutoBorrowing:
    @pytest.mark.unit
    def test_auto_borrow_triggers(self):
        """극단적 CAPEX ratio 오버라이드 → 현금 음수 → 자동 차입."""
        result = build_proforma(
            SERIES,
            revenue_growth_path=[5.0, 5.0],
            overrides={"capex_to_revenue": 80.0},  # 매출의 80% CAPEX → 현금 부족 유발
        )
        # 자동 차입 경고가 있어야 함
        auto_borrow_warnings = [w for w in result.warnings if "자동 차입" in w]
        assert len(auto_borrow_warnings) > 0
        # BS는 여전히 균형
        for p in result.projections:
            assert p.bs_balanced
            assert p.cash >= 0
            # 자동 차입으로 부채가 증가했어야 함
            assert p.short_term_debt >= 0
            assert p.long_term_debt >= 0

    @pytest.mark.unit
    def test_no_borrow_when_cash_positive(self):
        """정상 CAPEX면 자동 차입 없음."""
        result = build_proforma(SERIES, revenue_growth_path=[5.0, 5.0])
        auto_borrow_warnings = [w for w in result.warnings if "자동 차입" in w]
        assert len(auto_borrow_warnings) == 0


# ── v2: β WACC ────────────────────────────────────────────


class TestBetaWACC:
    @pytest.mark.unit
    def test_elasticity_affects_wacc(self):
        """GDP β가 다르면 WACC도 달라야 함."""
        low_beta = SectorElasticity(0.3, 0.1, 10, 0, "defensive")
        high_beta = SectorElasticity(1.8, 0.8, 50, 0, "high")

        wacc_low, _ = compute_company_wacc(SERIES, sector_elasticity=low_beta)
        wacc_high, _ = compute_company_wacc(SERIES, sector_elasticity=high_beta)
        assert wacc_high > wacc_low

    @pytest.mark.unit
    def test_sector_params_overrides_elasticity(self):
        """sector_params.beta가 있으면 elasticity보다 우선."""

        class MockParams:
            discountRate = 15.0
            beta = 2.0

        wacc, details = compute_company_wacc(
            SERIES,
            sector_params=MockParams(),
            sector_elasticity=SectorElasticity(0.3, 0.1, 10, 0, "defensive"),
        )
        # Ke = Rf(3.5) + beta(2.0) * totalErp(6.4) = 16.3
        assert details["beta"] == 2.0
        assert details["ke"] > 15.0


# ── v3: IS 구조 감지 (dep_in_sga) ───────────────────────


# SGA 포함형 시계열: GP - SGA = OP (D&A가 SGA 안에 포함)
SERIES_DEP_IN_SGA: dict = {
    "IS": {
        "sales": [250, 250, 250, 250, 300, 300, 300, 300],
        "gross_profit": [75, 75, 75, 75, 90, 90, 90, 90],
        # SGA = 25 → GP(75) - SGA(25) = OP(50), D&A가 SGA에 포함
        "selling_and_administrative_expenses": [25, 25, 25, 25, 30, 30, 30, 30],
        # OP = GP - SGA (D&A 별도 없음)
        "operating_profit": [50, 50, 50, 50, 60, 60, 60, 60],
        "profit_before_tax": [40, 40, 40, 40, 48, 48, 48, 48],
        "income_tax_expense": [8, 8, 8, 8, 10, 10, 10, 10],
        "finance_costs": [2, 2, 2, 2, 3, 3, 3, 3],
        "net_profit": [32, 32, 32, 32, 38, 38, 38, 38],
    },
    "CF": {
        "depreciation_and_amortization": [10, 10, 10, 10, 12, 12, 12, 12],
        "purchase_of_property_plant_and_equipment": [-15, -15, -15, -15, -18, -18, -18, -18],
        "dividends_paid": [-8, -8, -8, -8, -10, -10, -10, -10],
    },
    "BS": {
        "current_assets": [None, None, None, 500, None, None, None, 600],
        "current_liabilities": [None, None, None, 200, None, None, None, 240],
        "cash_and_cash_equivalents": [None, None, None, 100, None, None, None, 120],
        "shortterm_borrowings": [None, None, None, 50, None, None, None, 60],
        "longterm_borrowings": [None, None, None, 100, None, None, None, 120],
        "debentures": [None, None, None, 0, None, None, None, 0],
        "trade_receivables": [None, None, None, 150, None, None, None, 180],
        "inventories": [None, None, None, 120, None, None, None, 140],
        "trade_payables": [None, None, None, 80, None, None, None, 90],
        "tangible_assets": [None, None, None, 400, None, None, None, 450],
        "total_assets": [None, None, None, 1000, None, None, None, 1200],
        "total_liabilities": [None, None, None, 400, None, None, None, 480],
        "total_stockholders_equity": [None, None, None, 600, None, None, None, 720],
    },
}

# D&A 별도형 시계열: GP - SGA - D&A = OP
SERIES_DEP_SEPARATE: dict = {
    "IS": {
        "sales": [250, 250, 250, 250, 300, 300, 300, 300],
        "gross_profit": [75, 75, 75, 75, 90, 90, 90, 90],
        "selling_and_administrative_expenses": [15, 15, 15, 15, 18, 18, 18, 18],
        # OP = GP(75) - SGA(15) - D&A(10) = 50 (가정: IS에 dep 있음)
        "operating_profit": [50, 50, 50, 50, 60, 60, 60, 60],
        "depreciation_and_amortization": [10, 10, 10, 10, 12, 12, 12, 12],
        "profit_before_tax": [40, 40, 40, 40, 48, 48, 48, 48],
        "income_tax_expense": [8, 8, 8, 8, 10, 10, 10, 10],
        "finance_costs": [2, 2, 2, 2, 3, 3, 3, 3],
        "net_profit": [32, 32, 32, 32, 38, 38, 38, 38],
    },
    "CF": {
        "depreciation_and_amortization": [10, 10, 10, 10, 12, 12, 12, 12],
        "purchase_of_property_plant_and_equipment": [-15, -15, -15, -15, -18, -18, -18, -18],
        "dividends_paid": [-8, -8, -8, -8, -10, -10, -10, -10],
    },
    "BS": {
        "current_assets": [None, None, None, 500, None, None, None, 600],
        "current_liabilities": [None, None, None, 200, None, None, None, 240],
        "cash_and_cash_equivalents": [None, None, None, 100, None, None, None, 120],
        "shortterm_borrowings": [None, None, None, 50, None, None, None, 60],
        "longterm_borrowings": [None, None, None, 100, None, None, None, 120],
        "debentures": [None, None, None, 0, None, None, None, 0],
        "trade_receivables": [None, None, None, 150, None, None, None, 180],
        "inventories": [None, None, None, 120, None, None, None, 140],
        "trade_payables": [None, None, None, 80, None, None, None, 90],
        "tangible_assets": [None, None, None, 400, None, None, None, 450],
        "total_assets": [None, None, None, 1000, None, None, None, 1200],
        "total_liabilities": [None, None, None, 400, None, None, None, 480],
        "total_stockholders_equity": [None, None, None, 600, None, None, None, 720],
    },
}


class TestDepInSgaDetection:
    @pytest.mark.unit
    def test_dep_in_sga_detected(self):
        """GP - SGA ≈ OP → dep_in_sga = True."""
        ratios = extract_historical_ratios(SERIES_DEP_IN_SGA)
        assert ratios.dep_in_sga is True

    @pytest.mark.unit
    def test_dep_separate_detected(self):
        """GP - SGA ≠ OP (차이 큼) → dep_in_sga = False."""
        ratios = extract_historical_ratios(SERIES_DEP_SEPARATE)
        assert ratios.dep_in_sga is False

    @pytest.mark.unit
    def test_no_op_data_defaults_false(self):
        """operating_profit 데이터 없으면 dep_in_sga = False."""
        ratios = extract_historical_ratios(SERIES)  # 기존 SERIES는 OP 없음
        assert ratios.dep_in_sga is False

    @pytest.mark.unit
    def test_dep_in_sga_warning(self):
        """dep_in_sga=True이면 경고 메시지 포함."""
        ratios = extract_historical_ratios(SERIES_DEP_IN_SGA)
        has_warning = any("D&A가 SGA에 포함" in w for w in ratios.warnings)
        assert has_warning

    @pytest.mark.unit
    def test_dep_in_sga_repr(self):
        """dep_in_sga=True이면 repr에 '(D&A 포함)' 표시."""
        ratios = extract_historical_ratios(SERIES_DEP_IN_SGA)
        text = repr(ratios)
        assert "D&A 포함" in text


class TestDepInSgaProforma:
    @pytest.mark.unit
    def test_dep_in_sga_higher_operating_income(self):
        """dep_in_sga=True이면 D&A를 별도 차감하지 않아 영업이익이 더 높음."""
        result_sga = build_proforma(SERIES_DEP_IN_SGA, revenue_growth_path=[5.0, 5.0])
        result_sep = build_proforma(SERIES_DEP_SEPARATE, revenue_growth_path=[5.0, 5.0])

        assert result_sga.historical_ratios.dep_in_sga is True
        assert result_sep.historical_ratios.dep_in_sga is False

        # SGA 포함형은 SGA가 더 크지만, D&A를 빼지 않으므로 영업이익이 비슷하거나 높을 수 있음
        # 핵심: SGA 포함형에서 operating_income = GP - SGA (depreciation 미차감)
        for p in result_sga.projections:
            assert abs(p.operating_income - (p.gross_profit - p.sga)) < 1

    @pytest.mark.unit
    def test_dep_separate_deducts_depreciation(self):
        """dep_in_sga=False이면 D&A를 별도 차감."""
        result = build_proforma(SERIES_DEP_SEPARATE, revenue_growth_path=[5.0, 5.0])
        for p in result.projections:
            expected_oi = p.gross_profit - p.sga - p.depreciation
            assert abs(p.operating_income - expected_oi) < 1

    @pytest.mark.unit
    def test_ebitda_consistent_both_modes(self):
        """두 모드 모두 EBITDA = OP + D&A."""
        for series in [SERIES_DEP_IN_SGA, SERIES_DEP_SEPARATE]:
            result = build_proforma(series, revenue_growth_path=[5.0])
            for p in result.projections:
                assert abs(p.ebitda - (p.operating_income + p.depreciation)) < 1

    @pytest.mark.unit
    def test_bs_balanced_both_modes(self):
        """두 모드 모두 BS 균형 유지."""
        for series in [SERIES_DEP_IN_SGA, SERIES_DEP_SEPARATE]:
            result = build_proforma(series, revenue_growth_path=[5.0, 5.0])
            for p in result.projections:
                assert p.bs_balanced
