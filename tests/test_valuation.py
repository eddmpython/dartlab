"""밸류에이션 + 예측 엔진 단위 테스트.

순수 dict 기반 테스트 — Company 로딩 없이 실행 가능.
"""

from __future__ import annotations

import pytest

# ── 테스트용 mock 시계열 ──────────────────────────────────


def _make_series(
    revenue: list = None,
    operating_profit: list = None,
    net_profit: list = None,
    operating_cashflow: list = None,
    capex: list = None,
    dividends_paid: list = None,
    total_assets: list = None,
    total_equity: list = None,
    owners_equity: list = None,
    total_liabilities: list = None,
    cash: list = None,
    stb: list = None,
    ltb: list = None,
    debentures: list = None,
    tangible_assets: list = None,
    intangible_assets: list = None,
) -> dict:
    """테스트용 간이 시계열 dict 생성."""
    series = {"IS": {}, "BS": {}, "CF": {}}

    if revenue is not None:
        series["IS"]["sales"] = revenue
    if operating_profit is not None:
        series["IS"]["operating_profit"] = operating_profit
    if net_profit is not None:
        series["IS"]["net_profit"] = net_profit

    if operating_cashflow is not None:
        series["CF"]["operating_cashflow"] = operating_cashflow
    if capex is not None:
        series["CF"]["purchase_of_property_plant_and_equipment"] = capex
    if dividends_paid is not None:
        series["CF"]["dividends_paid"] = dividends_paid

    if total_assets is not None:
        series["BS"]["total_assets"] = total_assets
    if total_equity is not None:
        series["BS"]["total_stockholders_equity"] = total_equity
    if owners_equity is not None:
        series["BS"]["owners_of_parent_equity"] = owners_equity
    if total_liabilities is not None:
        series["BS"]["total_liabilities"] = total_liabilities
    if cash is not None:
        series["BS"]["cash_and_cash_equivalents"] = cash
    if stb is not None:
        series["BS"]["shortterm_borrowings"] = stb
    if ltb is not None:
        series["BS"]["longterm_borrowings"] = ltb
    if debentures is not None:
        series["BS"]["debentures"] = debentures
    if tangible_assets is not None:
        series["BS"]["tangible_assets"] = tangible_assets
    if intangible_assets is not None:
        series["BS"]["intangible_assets"] = intangible_assets

    return series


# 정상 기업 시계열 (매출 성장, FCF 양수, 배당 있음)
HEALTHY_SERIES = _make_series(
    revenue=[100e8, 120e8, 140e8, 160e8, 180e8],
    operating_profit=[10e8, 14e8, 18e8, 22e8, 25e8],
    net_profit=[8e8, 11e8, 14e8, 17e8, 20e8],
    operating_cashflow=[12e8, 15e8, 18e8, 22e8, 26e8],
    capex=[-3e8, -4e8, -5e8, -6e8, -7e8],
    dividends_paid=[-3e8, -3.1e8, -3.2e8, -3.3e8, -3.5e8],
    total_assets=[200e8, 220e8, 250e8, 280e8, 310e8],
    total_equity=[120e8, 135e8, 150e8, 170e8, 190e8],
    owners_equity=[110e8, 125e8, 140e8, 160e8, 180e8],
    total_liabilities=[80e8, 85e8, 100e8, 110e8, 120e8],
    cash=[30e8, 35e8, 40e8, 45e8, 50e8],
    stb=[10e8, 10e8, 12e8, 12e8, 15e8],
    ltb=[20e8, 20e8, 25e8, 25e8, 30e8],
    debentures=[5e8, 5e8, 5e8, 5e8, 5e8],
    tangible_assets=[60e8, 65e8, 70e8, 75e8, 80e8],
    intangible_assets=[10e8, 12e8, 14e8, 16e8, 18e8],
)

# 무배당 기업
NO_DIVIDEND_SERIES = _make_series(
    revenue=[50e8, 55e8, 60e8, 65e8],
    operating_profit=[5e8, 6e8, 7e8, 8e8],
    net_profit=[3e8, 4e8, 5e8, 6e8],
    operating_cashflow=[4e8, 5e8, 6e8, 7e8],
    capex=[-1e8, -1.5e8, -2e8, -2.5e8],
    total_assets=[100e8, 110e8, 120e8, 130e8],
    total_equity=[60e8, 65e8, 70e8, 75e8],
    total_liabilities=[40e8, 45e8, 50e8, 55e8],
    cash=[15e8, 18e8, 20e8, 22e8],
)


@pytest.fixture
def sector_params():
    from dartlab.engines.analysis.sector.types import SectorParams

    return SectorParams(
        discountRate=10.0,
        growthRate=4.0,
        perMultiple=15,
        pbrMultiple=1.5,
        evEbitdaMultiple=8,
        label="테스트업종",
    )


# ══════════════════════════════════════
# DCF 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestDCF:
    def test_dcf_basic(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import dcfValuation as dcf_valuation

        result = dcf_valuation(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sector_params,
            currentPrice=50_000,
        )
        assert result.enterpriseValue > 0
        assert result.equityValue > 0
        assert result.perShareValue is not None
        assert result.perShareValue > 0
        assert result.marginOfSafety is not None
        assert len(result.fcfProjections) == 5
        assert result.discountRate == 10.0

    def test_dcf_no_shares(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import dcfValuation as dcf_valuation

        result = dcf_valuation(HEALTHY_SERIES, sectorParams=sector_params)
        assert result.enterpriseValue > 0
        assert result.perShareValue is None

    def test_dcf_empty_series(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import dcfValuation as dcf_valuation

        result = dcf_valuation({"IS": {}, "BS": {}, "CF": {}}, sectorParams=sector_params)
        assert len(result.warnings) > 0
        assert result.enterpriseValue == 0

    def test_dcf_repr(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import dcfValuation as dcf_valuation

        result = dcf_valuation(HEALTHY_SERIES, shares=1_000_000, sectorParams=sector_params)
        text = repr(result)
        assert "DCF" in text
        assert "투자 권유" in text


# ══════════════════════════════════════
# DDM 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestDDM:
    def test_ddm_with_dividends(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import ddmValuation as ddm_valuation

        result = ddm_valuation(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sector_params,
            currentPrice=50_000,
        )
        assert result.modelUsed == "gordon"
        assert result.intrinsicValue is not None
        assert result.intrinsicValue > 0
        assert result.dividendPerShare is not None

    def test_ddm_no_dividends(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import ddmValuation as ddm_valuation

        result = ddm_valuation(
            NO_DIVIDEND_SERIES,
            shares=1_000_000,
            sectorParams=sector_params,
        )
        assert result.modelUsed == "N/A"
        assert result.intrinsicValue is None

    def test_ddm_repr(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import ddmValuation as ddm_valuation

        result = ddm_valuation(HEALTHY_SERIES, shares=1_000_000, sectorParams=sector_params)
        text = repr(result)
        assert "DDM" in text


# ══════════════════════════════════════
# 상대가치 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestRelativeValuation:
    def test_relative_basic(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import relativeValuation as relative_valuation

        result = relative_valuation(
            HEALTHY_SERIES,
            sectorParams=sector_params,
            marketCap=500e8,
            shares=1_000_000,
            currentPrice=50_000,
        )
        assert result.sectorMultiples["PER"] == 15
        assert result.sectorMultiples["PBR"] == 1.5
        assert result.impliedValues["PER"] is not None
        assert result.consensusValue is not None

    def test_relative_no_market_cap(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import relativeValuation as relative_valuation

        result = relative_valuation(
            HEALTHY_SERIES,
            sectorParams=sector_params,
            shares=1_000_000,
        )
        assert result.currentMultiples["PER"] is None  # 시가총액 없으면 현재 PER 없음


# ══════════════════════════════════════
# 종합 밸류에이션 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestFullValuation:
    def test_full_valuation(self, sector_params):
        from dartlab.engines.analysis.analyst.valuation import fullValuation as full_valuation

        result = full_valuation(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sector_params,
            marketCap=500e8,
            currentPrice=50_000,
        )
        assert result.dcf is not None
        assert result.ddm is not None
        assert result.relative is not None
        assert result.fairValueRange is not None
        assert result.verdict in ("저평가", "적정", "고평가", "판단불가")


# ══════════════════════════════════════
# 예측 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestForecast:
    def test_forecast_revenue(self, sector_params):
        from dartlab.engines.analysis.analyst.forecast import forecastMetric as forecast_metric

        result = forecast_metric(HEALTHY_SERIES, metric="revenue", horizon=3, sectorParams=sector_params)
        assert result.metric == "revenue"
        assert len(result.projected) == 3
        assert result.confidence in ("high", "medium", "low")
        assert result.rSquared >= 0

    def test_forecast_insufficient_data(self, sector_params):
        from dartlab.engines.analysis.analyst.forecast import forecastMetric as forecast_metric

        short = _make_series(revenue=[100e8, 120e8])
        result = forecast_metric(short, metric="revenue", sectorParams=sector_params)
        assert len(result.projected) == 0
        assert len(result.warnings) > 0

    def test_forecast_all(self, sector_params):
        from dartlab.engines.analysis.analyst.forecast import forecastAll as forecast_all

        results = forecast_all(HEALTHY_SERIES, sectorParams=sector_params)
        assert "revenue" in results
        assert "operating_income" in results
        assert "net_income" in results

    def test_forecast_unknown_metric(self, sector_params):
        from dartlab.engines.analysis.analyst.forecast import forecastMetric as forecast_metric

        result = forecast_metric(HEALTHY_SERIES, metric="unknown_metric", sectorParams=sector_params)
        assert len(result.warnings) > 0


# ══════════════════════════════════════
# 시나리오 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestScenario:
    def test_scenario_basic(self, sector_params):
        from dartlab.engines.analysis.analyst.forecast import scenarioAnalysis as scenario_analysis

        result = scenario_analysis(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sector_params,
            currentPrice=50_000,
        )
        assert result.base["perShareValue"] > 0
        assert result.bull["perShareValue"] >= result.base["perShareValue"]
        assert result.bear["perShareValue"] <= result.base["perShareValue"]
        assert result.weightedValue is not None
        assert result.probability["base"] == 50

    def test_scenario_repr(self, sector_params):
        from dartlab.engines.analysis.analyst.forecast import scenarioAnalysis as scenario_analysis

        result = scenario_analysis(HEALTHY_SERIES, shares=1_000_000, sectorParams=sector_params)
        text = repr(result)
        assert "시나리오" in text
        assert "Bull" in text
        assert "Bear" in text


# ══════════════════════════════════════
# 민감도 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestSensitivity:
    def test_sensitivity_basic(self, sector_params):
        from dartlab.engines.analysis.analyst.forecast import sensitivityAnalysis as sensitivity_analysis

        result = sensitivity_analysis(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sector_params,
        )
        assert len(result.waccValues) == 5
        assert len(result.growthValues) == 5
        assert len(result.matrix) == 5
        assert len(result.matrix[0]) == 5

    def test_sensitivity_repr(self, sector_params):
        from dartlab.engines.analysis.analyst.forecast import sensitivityAnalysis as sensitivity_analysis

        result = sensitivity_analysis(HEALTHY_SERIES, shares=1_000_000, sectorParams=sector_params)
        text = repr(result)
        assert "민감도" in text
        assert "WACC" in text


# ══════════════════════════════════════
# OLS 단위 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestOLS:
    def test_perfect_linear(self):
        from dartlab.engines.analysis.analyst.forecast import _ols

        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        slope, intercept, r2 = _ols(x, y)
        assert abs(slope - 2.0) < 0.01
        assert abs(intercept - 0.0) < 0.01
        assert abs(r2 - 1.0) < 0.01

    def test_constant(self):
        from dartlab.engines.analysis.analyst.forecast import _ols

        x = [1.0, 2.0, 3.0]
        y = [5.0, 5.0, 5.0]
        slope, intercept, r2 = _ols(x, y)
        assert abs(slope) < 0.01
        assert abs(intercept - 5.0) < 0.01

    def test_single_point(self):
        from dartlab.engines.analysis.analyst.forecast import _ols

        slope, intercept, r2 = _ols([1.0], [5.0])
        assert r2 == 0.0


# ══════════════════════════════════════
# EPS/BPS/DPS 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestPerShareMetrics:
    def test_eps_bps_dps(self):
        from dartlab.engines.common.finance.ratios import calcRatios

        result = calcRatios(HEALTHY_SERIES, shares=1_000_000)
        assert result.eps is not None
        assert result.bps is not None
        assert result.dps is not None
        assert result.sharesOutstanding == 1_000_000

    def test_no_shares(self):
        from dartlab.engines.common.finance.ratios import calcRatios

        result = calcRatios(HEALTHY_SERIES)
        assert result.eps is None
        assert result.bps is None
        assert result.dps is None
