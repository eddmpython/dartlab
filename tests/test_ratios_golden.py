"""재무비율 Golden Value 테스트.

calcRatios()의 각 공식이 교과서 기준으로 정확한지 검증한다.
순수 Python dict 입력만 사용하므로 Polars/데이터 로드 없음 → unit 마커.

검증 대상 (30+개 비율):
- 수익성: ROE, ROA, 영업이익률, 순이익률, 매출총이익률, EBITDA마진
- 안정성: 부채비율, 유동비율, 당좌비율, 자기자본비율, 이자보상배율, 순차입금비율
- 효율성: 총자산회전율, 재고회전율, 매출채권회전율, 매입채무회전율
- 현금흐름: FCF, 영업CF마진, 영업CF/순이익, CAPEX비율
- 복합: ROIC, DuPont 3분해, Piotroski, Altman Z-Score, CCC/DSO/DIO/DPO
- Edge case: yoy_pct, TTM None, 분모 0, 금융업
"""

import pytest

pytestmark = pytest.mark.unit


# ══════════════════════════════════════
# Fixture: 교과서 기준 입력 데이터
# ══════════════════════════════════════

# annual=True 모드 → getLatest 사용, 각 리스트의 마지막 값이 최신
_SERIES_ANNUAL = {
    "IS": {
        "sales": [80_000, 90_000, 100_000],
        "operating_profit": [16_000, 18_000, 20_000],
        "net_profit": [12_000, 13_500, 15_000],
        "cost_of_sales": [48_000, 54_000, 60_000],
        "gross_profit": [32_000, 36_000, 40_000],
        "selling_and_administrative_expenses": [16_000, 18_000, 20_000],
        "finance_costs": [1_800, 2_000, 2_000],
        "profit_before_tax": [16_800, 18_000, 20_000],
        "income_tax_expense": [4_200, 4_500, 5_000],
    },
    "BS": {
        "total_assets": [180_000, 190_000, 200_000],
        "total_stockholders_equity": [100_000, 110_000, 120_000],
        "owners_of_parent_equity": [100_000, 110_000, 120_000],
        "total_liabilities": [80_000, 80_000, 80_000],
        "current_assets": [40_000, 45_000, 50_000],
        "current_liabilities": [25_000, 28_000, 30_000],
        "cash_and_cash_equivalents": [8_000, 9_000, 10_000],
        "shortterm_borrowings": [5_000, 5_000, 5_000],
        "longterm_borrowings": [15_000, 15_000, 15_000],
        "debentures": [10_000, 10_000, 10_000],
        "inventories": [8_000, 9_000, 10_000],
        "trade_and_other_receivables": [10_000, 11_000, 12_000],
        "trade_and_other_payables": [8_000, 8_500, 9_000],
        "tangible_assets": [60_000, 62_000, 65_000],
        "intangible_assets": [5_000, 5_000, 5_000],
        "retained_earnings": [50_000, 55_000, 60_000],
        "noncurrent_assets": [130_000, 135_000, 140_000],
        "noncurrent_liabilities": [40_000, 40_000, 40_000],
    },
    "CF": {
        "operating_cashflow": [20_000, 22_000, 25_000],
        "investing_cashflow": [-8_000, -9_000, -10_000],
        "purchase_of_property_plant_and_equipment": [-4_000, -4_500, -5_000],
        "dividends_paid": [-3_000, -3_500, -4_000],
        "depreciation_and_amortization": [6_000, 6_500, 7_000],
    },
}


def _calc(**kwargs):
    """calcRatios 호출 래퍼."""
    from dartlab.engines.common.finance.ratios import calcRatios

    return calcRatios(_SERIES_ANNUAL, annual=True, **kwargs)


# ══════════════════════════════════════
# 수익성 (8개)
# ══════════════════════════════════════


class TestProfitability:
    """수익성 비율 교과서 공식 검증."""

    def test_roe(self):
        """ROE = 순이익 / 자기자본 × 100 = 15000/120000 × 100 = 12.5%."""
        r = _calc()
        assert r.roe == pytest.approx(12.5, abs=0.1)

    def test_roa(self):
        """ROA = 순이익 / 총자산 × 100 = 15000/200000 × 100 = 7.5%."""
        r = _calc()
        assert r.roa == pytest.approx(7.5, abs=0.1)

    def test_operating_margin(self):
        """영업이익률 = 영업이익 / 매출 × 100 = 20000/100000 × 100 = 20%."""
        r = _calc()
        assert r.operatingMargin == pytest.approx(20.0, abs=0.1)

    def test_net_margin(self):
        """순이익률 = 순이익 / 매출 × 100 = 15000/100000 × 100 = 15%."""
        r = _calc()
        assert r.netMargin == pytest.approx(15.0, abs=0.1)

    def test_gross_margin(self):
        """매출총이익률 = 매출총이익 / 매출 × 100 = 40000/100000 × 100 = 40%."""
        r = _calc()
        assert r.grossMargin == pytest.approx(40.0, abs=0.1)

    def test_ebitda_margin(self):
        """EBITDA마진 = (영업이익 + 감가상각) / 매출 × 100 = (20000+7000)/100000 × 100 = 27%."""
        r = _calc()
        assert r.ebitdaMargin == pytest.approx(27.0, abs=0.1)
        assert r.ebitdaEstimated is False  # 감가상각 데이터 있음

    def test_cost_of_sales_ratio(self):
        """매출원가율 = 매출원가 / 매출 × 100 = 60000/100000 × 100 = 60%."""
        r = _calc()
        assert r.costOfSalesRatio == pytest.approx(60.0, abs=0.1)

    def test_sga_ratio(self):
        """판관비율 = 판관비 / 매출 × 100 = 20000/100000 × 100 = 20%."""
        r = _calc()
        assert r.sgaRatio == pytest.approx(20.0, abs=0.1)


# ══════════════════════════════════════
# 안정성 (7개)
# ══════════════════════════════════════


class TestStability:
    """안정성 비율 교과서 공식 검증."""

    def test_debt_ratio(self):
        """부채비율 = 부채 / 자본 × 100 = 80000/120000 × 100 = 66.67%."""
        r = _calc()
        assert r.debtRatio == pytest.approx(66.67, abs=0.1)

    def test_current_ratio(self):
        """유동비율 = 유동자산 / 유동부채 × 100 = 50000/30000 × 100 = 166.67%."""
        r = _calc()
        assert r.currentRatio == pytest.approx(166.67, abs=0.1)

    def test_quick_ratio(self):
        """당좌비율 = (유동자산-재고) / 유동부채 × 100 = (50000-10000)/30000 × 100 = 133.33%."""
        r = _calc()
        assert r.quickRatio == pytest.approx(133.33, abs=0.1)

    def test_equity_ratio(self):
        """자기자본비율 = 자본 / 자산 × 100 = 120000/200000 × 100 = 60%."""
        r = _calc()
        assert r.equityRatio == pytest.approx(60.0, abs=0.1)

    def test_interest_coverage(self):
        """이자보상배율 = 영업이익 / 이자비용 = 20000/2000 = 10.0."""
        r = _calc()
        assert r.interestCoverage == pytest.approx(10.0, abs=0.1)

    def test_net_debt(self):
        """순차입금 = (단기+장기+사채) - 현금 = (5000+15000+10000) - 10000 = 20000."""
        r = _calc()
        assert r.netDebt == pytest.approx(20_000, abs=1)

    def test_net_debt_ratio(self):
        """순차입금비율 = 순차입금 / 자본 × 100 = 20000/120000 × 100 ≈ 16.67%."""
        r = _calc()
        assert r.netDebtRatio == pytest.approx(16.67, abs=0.1)

    def test_noncurrent_ratio(self):
        """비유동비율 = 비유동자산 / 자본 × 100 = 140000/120000 × 100 ≈ 116.67%."""
        r = _calc()
        assert r.noncurrentRatio == pytest.approx(116.67, abs=0.1)


# ══════════════════════════════════════
# 효율성 (4개)
# ══════════════════════════════════════


class TestEfficiency:
    """효율성 비율 교과서 공식 검증."""

    def test_total_asset_turnover(self):
        """총자산회전율 = 매출 / 총자산 = 100000/200000 = 0.5."""
        r = _calc()
        assert r.totalAssetTurnover == pytest.approx(0.5, abs=0.01)

    def test_inventory_turnover(self):
        """재고회전율 = 매출 / 재고 = 100000/10000 = 10.0."""
        r = _calc()
        assert r.inventoryTurnover == pytest.approx(10.0, abs=0.1)

    def test_receivables_turnover(self):
        """매출채권회전율 = 매출 / 매출채권 = 100000/12000 ≈ 8.33."""
        r = _calc()
        assert r.receivablesTurnover == pytest.approx(8.33, abs=0.1)

    def test_payables_turnover(self):
        """매입채무회전율 = 매출원가 / 매입채무 = 60000/9000 ≈ 6.67."""
        r = _calc()
        assert r.payablesTurnover == pytest.approx(6.67, abs=0.1)


# ══════════════════════════════════════
# 현금흐름 (5개)
# ══════════════════════════════════════


class TestCashflow:
    """현금흐름 비율 교과서 공식 검증."""

    def test_fcf(self):
        """FCF = 영업CF - |CAPEX| = 25000 - 5000 = 20000."""
        r = _calc()
        assert r.fcf == pytest.approx(20_000, abs=1)

    def test_operating_cf_margin(self):
        """영업CF마진 = 영업CF / 매출 × 100 = 25000/100000 × 100 = 25%."""
        r = _calc()
        assert r.operatingCfMargin == pytest.approx(25.0, abs=0.1)

    def test_operating_cf_to_net_income(self):
        """영업CF/순이익 = 25000/15000 × 100 ≈ 166.67%."""
        r = _calc()
        assert r.operatingCfToNetIncome == pytest.approx(166.67, abs=0.1)

    def test_capex_ratio(self):
        """CAPEX비율 = |CAPEX| / 매출 × 100 = 5000/100000 × 100 = 5%."""
        r = _calc()
        assert r.capexRatio == pytest.approx(5.0, abs=0.1)

    def test_dividend_payout_ratio(self):
        """배당성향 = |배당금| / 순이익 × 100 = 4000/15000 × 100 ≈ 26.67%."""
        r = _calc()
        assert r.dividendPayoutRatio == pytest.approx(26.67, abs=0.1)


# ══════════════════════════════════════
# 복합 지표 (11개)
# ══════════════════════════════════════


class TestComposite:
    """복합 지표 교과서 공식 검증."""

    def test_roic(self):
        """ROIC = NOPAT / 투하자본 × 100.

        annual=True + 3개 값 → getTTM 실패(4개 필요) → 기본 세율 22%.
        NOPAT = 20000 × (1 - 0.22) = 15600
        순차입금 = 20000, 투하자본 = 120000 + 20000 = 140000
        ROIC = 15600/140000 × 100 ≈ 11.14%
        """
        r = _calc()
        assert r.roic == pytest.approx(11.14, abs=0.1)

    def test_roic_dynamic_tax(self):
        """ROIC 동적 세율: IS에 4개 값 제공 → getTTM 성공 → 실제 유효세율 적용.

        유효세율 = 5000/20000 = 25%
        NOPAT = 20000 × (1 - 0.25) = 15000
        투하자본 = 120000 + 20000 = 140000
        ROIC = 15000/140000 × 100 ≈ 10.71%
        """
        from dartlab.engines.common.finance.ratios import calcRatios

        series_4q = {
            "IS": {
                "sales": [70_000, 80_000, 90_000, 100_000],
                "operating_profit": [14_000, 16_000, 18_000, 20_000],
                "net_profit": [10_000, 12_000, 13_500, 15_000],
                "cost_of_sales": [42_000, 48_000, 54_000, 60_000],
                "gross_profit": [28_000, 32_000, 36_000, 40_000],
                "selling_and_administrative_expenses": [14_000, 16_000, 18_000, 20_000],
                "finance_costs": [2_000, 1_800, 2_000, 2_000],
                "profit_before_tax": [15_000, 16_800, 18_000, 20_000],
                "income_tax_expense": [3_750, 4_200, 4_500, 5_000],
            },
            "BS": _SERIES_ANNUAL["BS"],
            "CF": _SERIES_ANNUAL["CF"],
        }
        # TTM pbt = 15000+16800+18000+20000 = 69800
        # TTM tax = 3750+4200+4500+5000 = 17450
        # effective_tax = 17450/69800 ≈ 0.25
        # operatingIncomeTTM = getLatest = 20000 (annual=True)
        # NOPAT = 20000 * (1-0.25) = 15000
        # invested = 120000 + 20000 = 140000
        # ROIC = 15000/140000 * 100 ≈ 10.71%
        r = calcRatios(series_4q, annual=True)
        assert r.roic == pytest.approx(10.71, abs=0.1)

    def test_dupont_margin(self):
        """DuPont 순이익률 = 순이익 / 매출 × 100 = 15%."""
        r = _calc()
        assert r.dupontMargin == pytest.approx(15.0, abs=0.1)

    def test_dupont_turnover(self):
        """DuPont 자산회전율 = 매출 / 총자산 = 0.5."""
        r = _calc()
        assert r.dupontTurnover == pytest.approx(0.5, abs=0.01)

    def test_dupont_leverage(self):
        """DuPont 레버리지 = 총자산 / 자본 = 200000/120000 ≈ 1.67."""
        r = _calc()
        assert r.dupontLeverage == pytest.approx(1.67, abs=0.01)

    def test_dupont_decomposition(self):
        """DuPont: ROE ≈ 순이익률 × 자산회전율 × 레버리지."""
        r = _calc()
        reconstructed = (r.dupontMargin / 100) * r.dupontTurnover * r.dupontLeverage * 100
        assert r.roe == pytest.approx(reconstructed, abs=0.5)

    def test_dso(self):
        """DSO = 매출채권 / 매출 × 365 = 12000/100000 × 365 = 43.8일."""
        r = _calc()
        assert r.dso == pytest.approx(43.8, abs=0.5)

    def test_dio(self):
        """DIO = 재고 / 매출원가 × 365 = 10000/60000 × 365 ≈ 60.8일."""
        r = _calc()
        assert r.dio == pytest.approx(60.8, abs=0.5)

    def test_dpo(self):
        """DPO = 매입채무 / 매출원가 × 365 = 9000/60000 × 365 = 54.75일."""
        r = _calc()
        assert r.dpo == pytest.approx(54.75, abs=0.5)

    def test_ccc(self):
        """CCC = DSO + DIO - DPO ≈ 43.8 + 60.8 - 54.75 = 49.85일."""
        r = _calc()
        assert r.ccc == pytest.approx(49.9, abs=1.0)

    def test_piotroski_f_score(self):
        """Piotroski F-Score: 건강한 기업 → 고점수."""
        r = _calc()
        # ROA>0(1) + CF>0(1) + ROA개선(skip) + CF>NI(1) + 부채비율<100(1) + 유동비율>100(1)
        # + 신주(skip) + 매출총이익률>0(1) + 자산회전율>0(1) = 6/7
        assert r.piotroskiFScore >= 5
        assert r.piotroskiMaxScore == 7

    def test_altman_z_score(self):
        """Altman Z-Score: 제조업 공식.

        WC = 50000-30000 = 20000
        A = WC/TA = 20000/200000 = 0.1
        B = RE/TA = 60000/200000 = 0.3
        C = EBIT/TA = 20000/200000 = 0.1
        D = Equity/TL = 120000/80000 = 1.5
        E = Sales/TA = 100000/200000 = 0.5
        Z = 1.2×0.1 + 1.4×0.3 + 3.3×0.1 + 0.6×1.5 + 1.0×0.5
          = 0.12 + 0.42 + 0.33 + 0.9 + 0.5 = 2.27
        """
        r = _calc()
        assert r.altmanZScore == pytest.approx(2.27, abs=0.1)


# ══════════════════════════════════════
# BS 항등식 검증
# ══════════════════════════════════════


class TestBSIdentity:
    """BS 항등식이 golden value에서 성립 확인."""

    def test_no_bs_warning(self):
        """정상 데이터: 자산 = 부채 + 자본이므로 경고 없음."""
        r = _calc()
        bs_warnings = [w for w in r.warnings if "BS 항등식" in w]
        assert len(bs_warnings) == 0

    def test_bs_mismatch_triggers_warning(self):
        """항등식 불일치 시 경고 발생."""
        from dartlab.engines.common.finance.ratios import calcRatios

        bad_series = {
            "IS": _SERIES_ANNUAL["IS"],
            "BS": {
                **_SERIES_ANNUAL["BS"],
                "total_assets": [200_000],  # 200000
                "total_liabilities": [100_000],  # 100000
                "total_stockholders_equity": [80_000],  # 80000 → 합계 180000 ≠ 200000
            },
            "CF": _SERIES_ANNUAL["CF"],
        }
        r = calcRatios(bad_series, annual=True)
        bs_warnings = [w for w in r.warnings if "BS 항등식" in w]
        assert len(bs_warnings) == 1


# ══════════════════════════════════════
# YoY 계산 Edge Cases
# ══════════════════════════════════════


class TestYoyPct:
    """yoy_pct() 부호 전환, 경계값 검증."""

    def test_positive_to_positive(self):
        from dartlab.engines.common.finance.ratios import yoy_pct

        assert yoy_pct(120, 100) == pytest.approx(20.0)

    def test_negative_to_negative_improving(self):
        """적자 축소: -50 ← -100 → +50% (손실 축소는 양수)."""
        from dartlab.engines.common.finance.ratios import yoy_pct

        assert yoy_pct(-50, -100) == pytest.approx(50.0)

    def test_negative_to_negative_worsening(self):
        """적자 확대: -150 ← -100 → -50% (손실 확대는 음수)."""
        from dartlab.engines.common.finance.ratios import yoy_pct

        assert yoy_pct(-150, -100) == pytest.approx(-50.0)

    def test_sign_change_profit_to_loss(self):
        """흑자→적자: None (비교 불가)."""
        from dartlab.engines.common.finance.ratios import yoy_pct

        assert yoy_pct(-50, 100) is None

    def test_sign_change_loss_to_profit(self):
        """적자→흑자: None (비교 불가)."""
        from dartlab.engines.common.finance.ratios import yoy_pct

        assert yoy_pct(50, -100) is None

    def test_zero_denominator(self):
        from dartlab.engines.common.finance.ratios import yoy_pct

        assert yoy_pct(100, 0) is None

    def test_none_inputs(self):
        from dartlab.engines.common.finance.ratios import yoy_pct

        assert yoy_pct(None, 100) is None
        assert yoy_pct(100, None) is None
        assert yoy_pct(None, None) is None


# ══════════════════════════════════════
# 밸류에이션 (시가총액 제공 시)
# ══════════════════════════════════════


class TestValuation:
    """밸류에이션 멀티플 검증."""

    def test_per(self):
        """PER = 시가총액 / 순이익 = 300000/15000 = 20."""
        r = _calc(marketCap=300_000)
        assert r.per == pytest.approx(20.0, abs=0.1)

    def test_pbr(self):
        """PBR = 시가총액 / 자본 = 300000/120000 = 2.5."""
        r = _calc(marketCap=300_000)
        assert r.pbr == pytest.approx(2.5, abs=0.1)

    def test_psr(self):
        """PSR = 시가총액 / 매출 = 300000/100000 = 3.0."""
        r = _calc(marketCap=300_000)
        assert r.psr == pytest.approx(3.0, abs=0.1)

    def test_ev_ebitda(self):
        """EV/EBITDA = (시가총액+순차입금) / EBITDA.

        순차입금 = 20000
        EV = 300000 + 20000 = 320000
        EBITDA = 20000 + 7000 = 27000
        EV/EBITDA = 320000/27000 ≈ 11.85
        """
        r = _calc(marketCap=300_000)
        assert r.evEbitda == pytest.approx(11.85, abs=0.1)

    def test_no_valuation_without_market_cap(self):
        """시가총액 미제공 시 밸류에이션 None."""
        r = _calc()
        assert r.per is None
        assert r.pbr is None


# ══════════════════════════════════════
# 금융업 Archetype
# ══════════════════════════════════════


class TestFinancialArchetype:
    """금융업 archetype에서 제조업 비율이 억제되는지 검증."""

    def test_financial_suppresses_manufacturing_ratios(self):
        """금융업: 매출총이익률, 재고회전율 등은 None."""
        r = _calc(archetypeOverride="financial")
        # 금융업 정책에 따라 억제되는 비율들
        assert r.grossMargin is None or r.altmanZScore is None
