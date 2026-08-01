"""dFV 재무 기간 제한과 입력 provenance 회귀 테스트."""

from __future__ import annotations

from datetime import date

import polars as pl
import pytest

pytestmark = pytest.mark.unit


class _SelectCompany:
    def select(self, _statement, _accounts):
        return object()


def test_frozen_dcf_formula_fixture_has_exact_value():
    """동결 입력의 명시 구간과 terminal PV 합계는 정확히 1,000이다."""
    from dartlab.analysis.valuation.dcf import multiStageDcf

    result = multiStageDcf(
        baseFcf=100.0,
        growthYears=1,
        growthRates=0.0,
        terminalGrowthRate=0.0,
        wacc=10.0,
        netDebt=0.0,
        shares=1,
    )

    assert result["enterpriseValue"] == pytest.approx(1_000.0)
    assert result["equityValue"] == pytest.approx(1_000.0)
    assert result["perShare"] == pytest.approx(1_000.0)


def test_reported_shares_excludes_rows_after_base_period():
    """기준 기간 뒤의 주식수 공시는 과거 계산에 섞이지 않는다."""
    from dartlab.analysis.financial._companyLookup import _getSharesOutstandingInput

    class _Report:
        def extract(self, _topic):
            return pl.DataFrame(
                {
                    "se": ["보통주", "보통주", "보통주"],
                    "stlm_dt": ["2023-12-31", "2024-06-30", "2024-12-31"],
                    "istc_totqy": [10.0, 20.0, 999.0],
                }
            )

    company = type("Company", (), {"_report": _Report()})()
    resolved = _getSharesOutstandingInput(company, basePeriod="2024Q2")

    assert resolved == {"value": 20, "period": "2024-06-30", "source": "report.stockTotal"}
    assert _getSharesOutstandingInput(company, basePeriod="2024-H1") is None


def test_base_fcf_is_invariant_to_future_financial_rows(monkeypatch):
    """기준 기간 뒤 CF를 추가해도 선택된 기준 FCF는 변하지 않는다."""
    from dartlab.analysis.valuation._dFVTsd import _tsdExtractBaseFcfInput
    from dartlab.core.utils import helpers

    historical = {
        "operating_cashflow": {"2023": 300.0, "2022": 200.0},
        "purchase_of_property_plant_and_equipment": {"2023": 100.0, "2022": 100.0},
    }
    with_future = {
        "operating_cashflow": {"2025": 50_000.0, "2024": 40_000.0, **historical["operating_cashflow"]},
        "purchase_of_property_plant_and_equipment": {
            "2025": 1.0,
            "2024": 1.0,
            **historical["purchase_of_property_plant_and_equipment"],
        },
    }

    monkeypatch.setattr(
        helpers,
        "toDictBySnakeId",
        lambda _selected: (with_future, ["2025", "2024", "2023", "2022"]),
    )
    future_result = _tsdExtractBaseFcfInput(_SelectCompany(), basePeriod="2024Q4")
    monkeypatch.setattr(
        helpers,
        "toDictBySnakeId",
        lambda _selected: (historical, ["2023", "2022"]),
    )
    historical_result = _tsdExtractBaseFcfInput(_SelectCompany(), basePeriod="2024Q4")

    assert future_result == historical_result
    assert future_result == {
        "value": 200.0,
        "periods": ["2023", "2022"],
        "source": "CF.operatingCashflow-capex.medianPositive",
    }


def test_net_debt_and_shares_use_period_matched_inputs(monkeypatch):
    """순차입금과 주식수 모두 동일한 기준 기간 정책을 사용한다."""
    from dartlab.analysis.valuation import _valuationInputAccess
    from dartlab.analysis.valuation._dFVTsd import _tsdExtractNetDebtSharesInput
    from dartlab.core.utils import helpers

    data = {
        "shortterm_borrowings": {"2025": 900.0, "2023": 30.0},
        "longterm_borrowings": {"2025": 800.0, "2023": 20.0},
        "cash_and_cash_equivalents": {"2025": 1.0, "2023": 10.0},
    }
    monkeypatch.setattr(
        helpers,
        "toDictBySnakeId",
        lambda _selected: (data, ["2025", "2024", "2023"]),
    )
    monkeypatch.setattr(
        _valuationInputAccess,
        "_inferSharesInput",
        lambda _company, basePeriod=None: {
            "value": 100,
            "period": "2024-06-30",
            "source": "report.stockTotal",
        },
    )

    resolved = _tsdExtractNetDebtSharesInput(_SelectCompany(), basePeriod="2024Q4")

    assert resolved == {
        "netDebt": 40.0,
        "shares": 100,
        "balancePeriod": "2023",
        "sharesPeriod": "2024-06-30",
        "sharesSource": "report.stockTotal",
    }


def test_wacc_resolver_threads_base_period(monkeypatch):
    """WACC fallback도 요청한 재무 기준 기간으로 ROIC를 조회한다."""
    from dartlab.analysis.financial import investmentAnalysis
    from dartlab.analysis.valuation._dFVTsd import _tsdResolveWacc

    seen = []

    def _roic(_company, *, basePeriod=None):
        seen.append(basePeriod)
        return {"history": [{"waccEstimate": 7.25}]}

    monkeypatch.setattr(investmentAnalysis, "calcRoicTimeline", _roic)

    assert _tsdResolveWacc(object(), {}, basePeriod="2022Q4") == 7.25
    assert seen == ["2022Q4"]


def test_historical_price_does_not_fall_forward_to_latest(monkeypatch):
    """기준 기간 가격이 없으면 최신 가격을 쓰지 않고 None을 반환한다."""
    import dartlab
    from dartlab.analysis.valuation._dFVCalcs import _getCurrentPrice

    prices = pl.DataFrame(
        {
            "date": [date(2025, 1, 2), date(2026, 1, 2)],
            "close": [100.0, 999.0],
        }
    )
    monkeypatch.setattr(dartlab, "gather", lambda *_args: prices)
    company = type("Company", (), {"stockCode": "000000"})()

    assert _getCurrentPrice(company, basePeriod="2025Q1") == 100.0
    assert _getCurrentPrice(company, basePeriod="2024Q4") is None


def test_two_stage_exposes_actual_inputs_and_accounting_identities(monkeypatch):
    """twoStage 결과는 실제 사용 입력과 EV, equity, 주당가치 항등식을 노출한다."""
    from dartlab.analysis.valuation import _dFVCalcs

    monkeypatch.setattr(_dFVCalcs, "_tsdResolveTerminalGrowth", lambda *_args: 2.0)
    monkeypatch.setattr(
        _dFVCalcs,
        "_tsdExtractBaseFcfInput",
        lambda *_args, **_kwargs: {"value": 100.0, "periods": ["2023"], "source": "fixture"},
    )
    monkeypatch.setattr(
        _dFVCalcs,
        "_tsdMaybeNormalizeFcf",
        lambda value, *_args, **_kwargs: value,
    )
    monkeypatch.setattr(
        _dFVCalcs,
        "_tsdExtractNetDebtSharesInput",
        lambda *_args, **_kwargs: {
            "netDebt": 50.0,
            "shares": 10,
            "balancePeriod": "2023",
            "sharesPeriod": "2023-12-31",
            "sharesSource": "fixture",
        },
    )

    result = _dFVCalcs._calcTwoStageDcf(
        object(),
        "matureStable",
        {"growthRates": [5.0]},
        basePeriod="2024Q4",
        wacc=8.5,
    )

    assert result is not None
    assert result["wacc"] == 8.5
    assert result["assumptions"]["financialBasePeriod"] == "2024Q4"
    assert result["assumptions"]["fcfPeriods"] == ["2023"]
    assert result["pvExplicit"] + result["pvTerminal"] == pytest.approx(result["enterpriseValue"])
    assert result["enterpriseValue"] - result["netDebt"] == pytest.approx(result["equityValue"])
    assert result["equityValue"] / result["shares"] == pytest.approx(result["perShare"])
