"""밸류에이션 + 예측 엔진 단위 테스트.

순수 dict 기반 테스트 . Company 로딩 없이 실행 가능.
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
def sectorParams():
    from dartlab.frame.sector.types import SectorParams

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
    def test_dcf_basic(self, sectorParams):
        from dartlab.analysis.valuation.dcf import dcfValuation as dcf_valuation

        result = dcf_valuation(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sectorParams,
            currentPrice=50_000,
        )
        assert result.enterpriseValue > 0
        assert result.equityValue > 0
        assert result.perShareValue is not None
        assert result.perShareValue > 0
        assert result.marginOfSafety is not None
        assert result.marginOfSafety == pytest.approx((result.perShareValue - 50_000) / 50_000 * 100)
        assert result.status == "usable"
        assert len(result.fcfProjections) == 5
        assert result.discountRate == 10.0

    def test_dcf_no_shares(self, sectorParams):
        from dartlab.analysis.valuation.dcf import dcfValuation as dcf_valuation

        result = dcf_valuation(HEALTHY_SERIES, sectorParams=sectorParams)
        assert result.enterpriseValue > 0
        assert result.perShareValue is None

    def test_dcf_empty_series(self, sectorParams):
        from dartlab.analysis.valuation.dcf import dcfValuation as dcf_valuation

        result = dcf_valuation({"IS": {}, "BS": {}, "CF": {}}, sectorParams=sectorParams)
        assert len(result.warnings) > 0
        assert result.enterpriseValue is None
        assert result.equityValue is None
        assert result.status == "unavailable"

    def test_dcf_missing_capex_does_not_treat_it_as_zero(self, sectorParams):
        from dartlab.analysis.valuation.dcf import dcfValuation as dcf_valuation

        series = _make_series(
            revenue=[1e9, 1.1e9, 1.2e9],
            operating_profit=[1e8, 1.1e8, 1.2e8],
            net_profit=[8e7, 9e7, 1e8],
            operating_cashflow=[1.2e8, 1.3e8, 1.4e8],
            total_assets=[2e9, 2.1e9, 2.2e9],
            total_equity=[1e9, 1.1e9, 1.2e9],
        )

        result = dcf_valuation(series, shares=1_000_000, sectorParams=sectorParams)

        assert result.status == "unavailable"
        assert result.enterpriseValue is None
        assert result.perShareValue is None
        assert any("CAPEX" in warning for warning in result.warnings)

    def test_dcf_missing_net_debt_blocks_equity_value(self, sectorParams):
        from copy import deepcopy

        from dartlab.analysis.valuation.dcf import dcfValuation as dcf_valuation

        series = deepcopy(HEALTHY_SERIES)
        series["BS"].pop("cash_and_cash_equivalents", None)
        result = dcf_valuation(series, shares=1_000_000, sectorParams=sectorParams)

        assert result.enterpriseValue is not None
        assert result.equityValue is None
        assert result.perShareValue is None
        assert result.status == "partial"

    def test_dcf_repr(self, sectorParams):
        from dartlab.analysis.valuation.dcf import dcfValuation as dcf_valuation

        result = dcf_valuation(HEALTHY_SERIES, shares=1_000_000, sectorParams=sectorParams)
        text = repr(result)
        assert "DCF" in text
        assert "투자 권유" in text


# ══════════════════════════════════════
# DDM 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestDDM:
    def test_ddm_with_dividends(self, sectorParams):
        from dartlab.analysis.valuation.dcf import ddmValuation as ddm_valuation

        result = ddm_valuation(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sectorParams,
            currentPrice=50_000,
        )
        assert result.modelUsed == "gordon"
        assert result.intrinsicValue is not None
        assert result.intrinsicValue > 0
        assert result.dividendPerShare is not None

    def test_ddm_no_dividends(self, sectorParams):
        from dartlab.analysis.valuation.dcf import ddmValuation as ddm_valuation

        result = ddm_valuation(
            NO_DIVIDEND_SERIES,
            shares=1_000_000,
            sectorParams=sectorParams,
        )
        assert result.modelUsed == "N/A"
        assert result.intrinsicValue is None

    def test_ddm_repr(self, sectorParams):
        from dartlab.analysis.valuation.dcf import ddmValuation as ddm_valuation

        result = ddm_valuation(HEALTHY_SERIES, shares=1_000_000, sectorParams=sectorParams)
        text = repr(result)
        assert "DDM" in text


# ══════════════════════════════════════
# 상대가치 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestRelativeValuation:
    def test_relative_basic(self, sectorParams):
        from dartlab.analysis.valuation.dcf import relativeValuation as relative_valuation

        result = relative_valuation(
            HEALTHY_SERIES,
            sectorParams=sectorParams,
            marketCap=500e8,
            shares=1_000_000,
            currentPrice=50_000,
        )
        assert result.sectorMultiples["PER"] == 15
        assert result.sectorMultiples["PBR"] == 1.5
        assert result.impliedValues["PER"] is not None
        assert result.consensusValue is not None

    def test_relative_no_market_cap(self, sectorParams):
        from dartlab.analysis.valuation.dcf import relativeValuation as relative_valuation

        result = relative_valuation(
            HEALTHY_SERIES,
            sectorParams=sectorParams,
            shares=1_000_000,
        )
        assert result.currentMultiples["PER"] is None  # 시가총액 없으면 현재 PER 없음

    def test_relative_missing_net_debt_blocks_ev_ebitda_value(self, sectorParams):
        from copy import deepcopy

        from dartlab.analysis.valuation.dcf import relativeValuation as relative_valuation

        series = deepcopy(HEALTHY_SERIES)
        series["BS"].pop("cash_and_cash_equivalents", None)
        result = relative_valuation(series, sectorParams=sectorParams, shares=1_000_000)

        assert result.impliedValues["EV/EBITDA"] is None
        assert any("EV/EBITDA" in warning for warning in result.warnings)


# ══════════════════════════════════════
# 종합 밸류에이션 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestFullValuation:
    def test_full_valuation(self, sectorParams):
        from dartlab.analysis.valuation.dcf import fullValuation as full_valuation

        result = full_valuation(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sectorParams,
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
    def test_forecast_revenue(self, sectorParams):
        from dartlab.analysis.forecast.forecast import forecastMetric as forecast_metric

        result = forecast_metric(HEALTHY_SERIES, metric="revenue", horizon=3, sectorParams=sectorParams)
        assert result.metric == "revenue"
        assert len(result.projected) == 3
        assert result.confidence in ("high", "medium", "low")
        assert result.rSquared >= 0

    def test_forecast_insufficient_data(self, sectorParams):
        from dartlab.analysis.forecast.forecast import forecastMetric as forecast_metric

        short = _make_series(revenue=[100e8, 120e8])
        result = forecast_metric(short, metric="revenue", sectorParams=sectorParams)
        assert len(result.projected) == 0
        assert len(result.warnings) > 0

    def test_forecast_all(self, sectorParams):
        from dartlab.analysis.forecast.forecast import forecastAll as forecast_all

        results = forecast_all(HEALTHY_SERIES, sectorParams=sectorParams)
        assert "revenue" in results
        assert "operating_income" in results
        assert "net_income" in results

    def test_forecast_unknown_metric(self, sectorParams):
        from dartlab.analysis.forecast.forecast import forecastMetric as forecast_metric

        result = forecast_metric(HEALTHY_SERIES, metric="unknown_metric", sectorParams=sectorParams)
        assert len(result.warnings) > 0


# ══════════════════════════════════════
# 시나리오 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestScenario:
    def test_scenario_basic(self, sectorParams):
        from dartlab.analysis.forecast.forecast import scenarioAnalysis as scenario_analysis

        result = scenario_analysis(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sectorParams,
            currentPrice=50_000,
        )
        assert result.base["perShareValue"] > 0
        assert result.bull["perShareValue"] >= result.base["perShareValue"]
        assert result.bear["perShareValue"] <= result.base["perShareValue"]
        assert result.weightedValue is not None
        assert result.probability["base"] == 50

    def test_scenario_repr(self, sectorParams):
        from dartlab.analysis.forecast.forecast import scenarioAnalysis as scenario_analysis

        result = scenario_analysis(HEALTHY_SERIES, shares=1_000_000, sectorParams=sectorParams)
        text = repr(result)
        assert "시나리오" in text
        assert "Bull" in text
        assert "Bear" in text


# ══════════════════════════════════════
# 민감도 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestSensitivity:
    def test_sensitivity_basic(self, sectorParams):
        from dartlab.analysis.forecast.forecast import sensitivityAnalysis as sensitivity_analysis

        result = sensitivity_analysis(
            HEALTHY_SERIES,
            shares=1_000_000,
            sectorParams=sectorParams,
        )
        assert len(result.waccValues) == 5
        assert len(result.growthValues) == 5
        assert len(result.matrix) == 5
        assert len(result.matrix[0]) == 5

    def test_sensitivity_repr(self, sectorParams):
        from dartlab.analysis.forecast.forecast import sensitivityAnalysis as sensitivity_analysis

        result = sensitivity_analysis(HEALTHY_SERIES, shares=1_000_000, sectorParams=sectorParams)
        text = repr(result)
        assert "민감도" in text
        assert "WACC" in text


# ══════════════════════════════════════
# OLS 단위 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestOLS:
    def test_perfect_linear(self):
        from dartlab.analysis.forecast.forecast import _ols

        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        slope, intercept, r2 = _ols(x, y)
        assert abs(slope - 2.0) < 0.01
        assert abs(intercept - 0.0) < 0.01
        assert abs(r2 - 1.0) < 0.01

    def test_constant(self):
        from dartlab.analysis.forecast.forecast import _ols

        x = [1.0, 2.0, 3.0]
        y = [5.0, 5.0, 5.0]
        slope, intercept, r2 = _ols(x, y)
        assert abs(slope) < 0.01
        assert abs(intercept - 5.0) < 0.01

    def test_single_point(self):
        from dartlab.analysis.forecast.forecast import _ols

        slope, intercept, r2 = _ols([1.0], [5.0])
        assert r2 == 0.0


# ══════════════════════════════════════
# EPS/BPS/DPS 테스트
# ══════════════════════════════════════


@pytest.mark.unit
class TestPerShareMetrics:
    def test_eps_bps_dps(self):
        from dartlab.analysis.financial.ratios import calcRatios

        result = calcRatios(HEALTHY_SERIES, annual=False, shares=1_000_000)
        assert result.eps is not None
        assert result.bps is not None
        assert result.dps is not None
        assert result.sharesOutstanding == 1_000_000

    def test_no_shares(self):
        from dartlab.analysis.financial.ratios import calcRatios

        result = calcRatios(HEALTHY_SERIES, annual=False)
        assert result.eps is None
        assert result.bps is None
        assert result.dps is None


# ══════════════════════════════════════
# USD 통화 포맷 테스트
# ══════════════════════════════════════


# US 기업 스케일 시계열 (달러 기준)
US_SERIES = _make_series(
    revenue=[50e9, 55e9, 60e9, 65e9, 70e9],
    operating_profit=[10e9, 12e9, 14e9, 16e9, 18e9],
    net_profit=[8e9, 9e9, 10e9, 12e9, 14e9],
    operating_cashflow=[12e9, 14e9, 16e9, 18e9, 20e9],
    capex=[-3e9, -4e9, -5e9, -6e9, -7e9],
    dividends_paid=[-2e9, -2.2e9, -2.4e9, -2.6e9, -2.8e9],
    total_assets=[200e9, 220e9, 250e9, 280e9, 310e9],
    total_equity=[120e9, 135e9, 150e9, 170e9, 190e9],
    owners_equity=[110e9, 125e9, 140e9, 160e9, 180e9],
    total_liabilities=[80e9, 85e9, 100e9, 110e9, 120e9],
    cash=[30e9, 35e9, 40e9, 45e9, 50e9],
    stb=[10e9, 10e9, 12e9, 12e9, 15e9],
    ltb=[20e9, 20e9, 25e9, 25e9, 30e9],
    debentures=[5e9, 5e9, 5e9, 5e9, 5e9],
)


@pytest.mark.unit
class TestUSDCurrency:
    def test_dcf_usd_repr(self, sectorParams):
        from dartlab.analysis.valuation.dcf import dcfValuation

        result = dcfValuation(US_SERIES, shares=1_000_000_000, sectorParams=sectorParams)
        result.currency = "USD"
        text = repr(result)
        assert "$" in text
        assert "M" in text
        assert "억" not in text

    def test_full_valuation_usd(self, sectorParams):
        from dartlab.analysis.valuation.dcf import fullValuation

        result = fullValuation(US_SERIES, shares=1_000_000_000, sectorParams=sectorParams, currency="USD")
        assert result.currency == "USD"
        assert result.dcf.currency == "USD"
        assert result.ddm.currency == "USD"
        assert result.relative.currency == "USD"
        text = repr(result)
        assert "$" in text
        assert "억" not in text

    def test_forecast_usd_repr(self, sectorParams):
        from dartlab.analysis.forecast.forecast import forecastMetric

        result = forecastMetric(US_SERIES, metric="revenue", horizon=3, sectorParams=sectorParams)
        result.currency = "USD"
        text = repr(result)
        assert "$" in text
        assert "억" not in text

    def test_revenue_forecast_usd(self):
        from dartlab.analysis.forecast.revenueForecast import forecastRevenue

        result = forecastRevenue(US_SERIES, market="US", currency="USD")
        assert result.currency == "USD"
        text = repr(result)
        assert "$" in text

    def test_krw_default(self, sectorParams):
        from dartlab.analysis.valuation.dcf import fullValuation

        result = fullValuation(HEALTHY_SERIES, shares=1_000_000, sectorParams=sectorParams)
        assert result.currency == "KRW"
        text = repr(result)
        assert "원" in text


@pytest.mark.unit
class TestFmtHelpers:
    def test_fmtBig(self):
        from dartlab.core.utils.fmt import fmtBig

        assert fmtBig(100e8, "KRW") == "100억"
        assert fmtBig(50e6, "USD") == "$50M"

    def test_fmtPrice(self):
        from dartlab.core.utils.fmt import fmtPrice

        assert fmtPrice(50000, "KRW") == "50,000원"
        assert fmtPrice(150.5, "USD") == "$150.50"


# ---------------------------------------------------------------------------
# _fetchPriceContext 네트워크 격리·강등 계약 (이슈 #105: CI 42분 스톨 재발 방지)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fetch_price_context_cache_seed_short_circuits(monkeypatch):
    """_cache 에 _priceContext 시드가 있으면 네트워크 진입 없이 즉시 반환한다."""
    import dartlab.gather.sources.price as priceMod
    from dartlab.analysis.financial._valuationInputs import _fetchPriceContext

    def trap(*_a, **_k):
        raise AssertionError("cache seed 가 있으면 fetch 호출 금지")

    monkeypatch.setattr(priceMod, "fetch", trap)

    class SeededCompany:
        stockCode = "005930"
        _cache = {"_priceContext": None}

    assert _fetchPriceContext(SeededCompany()) is None


@pytest.mark.unit
def test_fetch_price_context_gather_error_degrades_to_none(monkeypatch):
    """gather 커스텀 예외(GatherError 계열)도 None 강등으로 흡수한다 (스톨·전파 금지)."""
    import dartlab.gather.sources.price as priceMod
    from dartlab.analysis.financial._valuationInputs import _fetchPriceContext
    from dartlab.gather.types import GatherError

    def boom(*_a, **_k):
        raise GatherError("all sources exhausted")

    monkeypatch.setattr(priceMod, "fetch", boom)

    class C:
        stockCode = "005930"
        _cache: dict = {}

    company = C()
    assert _fetchPriceContext(company) is None
    assert company._cache["_priceContext"] is None, "실패 결과도 세션 캐시로 고정 (재시도 폭주 방지)"


@pytest.mark.unit
def test_fetch_price_context_offline_exception_group_degrades_to_none(monkeypatch):
    """Linux AnyIO가 묶은 offline 오류도 가격 보조 입력 실패로 강등한다."""
    import dartlab.gather.sources.price as priceMod
    from dartlab.analysis.financial._valuationInputs import _fetchPriceContext
    from dartlab.core.offlineGuard import OfflineViolation

    async def boom(*_a, **_k):
        raise ExceptionGroup("network candidates failed", [OfflineViolation("network blocked")])

    monkeypatch.setattr(priceMod, "fetch", boom)

    class C:
        stockCode = "005930"
        _cache: dict = {}

    company = C()
    assert _fetchPriceContext(company) is None
    assert company._cache["_priceContext"] is None


@pytest.mark.unit
def test_mock_company_fixture_never_touches_network(monkeypatch, mock_company):
    """conftest MockCompany 는 price 컨텍스트가 시드되어 실네트워크 진입이 불가능하다."""
    import dartlab.gather.sources.price as priceMod
    from dartlab.analysis.financial._valuationInputs import _fetchPriceContext

    def trap(*_a, **_k):
        raise AssertionError("MockCompany 경로에서 fetch 호출 금지")

    monkeypatch.setattr(priceMod, "fetch", trap)
    assert _fetchPriceContext(mock_company) is None
