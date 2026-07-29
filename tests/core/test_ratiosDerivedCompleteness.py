"""파생 재무비율의 결측과 0 구분 계약 회귀."""

from copy import deepcopy

import pytest

from dartlab.core.ratios import calcRatios, calcRatioSeries

pytestmark = pytest.mark.unit


_COMPLETE_SERIES = {
    "IS": {
        "sales": [100.0],
        "operating_profit": [10.0],
        "net_profit": [8.0],
    },
    "BS": {
        "total_assets": [200.0],
        "total_liabilities": [100.0],
        "total_stockholders_equity": [100.0],
        "owners_of_parent_equity": [100.0],
        "current_assets": [80.0],
        "current_liabilities": [40.0],
        "cash_and_cash_equivalents": [20.0],
        "shortterm_borrowings": [10.0],
        "longterm_borrowings": [30.0],
        "debentures": [10.0],
    },
    "CF": {
        "operating_cashflow": [15.0],
        "purchase_of_property_plant_and_equipment": [-5.0],
        "dividends_paid": [0.0],
        "depreciation_and_amortization": [5.0],
    },
}


def test_complete_inputs_keep_point_and_series_derived_values_aligned():
    point = calcRatios(_COMPLETE_SERIES, annual=True, marketCap=300.0)
    series = calcRatioSeries(_COMPLETE_SERIES, ["2024"], yoyLag=1)

    assert point.netDebt == 30.0
    assert point.netDebtRatio == 30.0
    assert point.ebitdaMargin == 15.0
    assert point.debtToEbitda == 3.33
    assert point.evEbitda == 22.0
    assert point.fcf == 10.0
    assert point.capexRatio == 5.0
    assert point.dividendPayoutRatio == 0.0
    assert point.ebitdaEstimated is False

    assert series.netDebtRatio == [30.0]
    assert series.ebitdaMargin == [15.0]
    assert series.debtToEbitda == [3.33]
    assert series.fcf == [10.0]
    assert series.capexRatio == [5.0]
    assert series.dividendPayoutRatio == [0.0]


@pytest.mark.parametrize(
    ("statement", "field"),
    [
        ("BS", "cash_and_cash_equivalents"),
        ("BS", "shortterm_borrowings"),
        ("BS", "longterm_borrowings"),
        ("BS", "debentures"),
    ],
)
def test_incomplete_debt_inputs_do_not_become_zero(statement, field):
    incomplete = deepcopy(_COMPLETE_SERIES)
    incomplete[statement].pop(field)

    point = calcRatios(incomplete, annual=True, marketCap=300.0)
    series = calcRatioSeries(incomplete, ["2024"], yoyLag=1)

    assert point.netDebt is None
    assert point.netDebtRatio is None
    assert point.evEbitda is None
    assert series.netDebtRatio == [None]
    if field != "cash_and_cash_equivalents":
        assert point.debtToEbitda is None
        assert series.debtToEbitda == [None]


def test_missing_depreciation_does_not_turn_ebitda_into_ebit():
    incomplete = deepcopy(_COMPLETE_SERIES)
    incomplete["CF"].pop("depreciation_and_amortization")

    point = calcRatios(incomplete, annual=True, marketCap=300.0)
    series = calcRatioSeries(incomplete, ["2024"], yoyLag=1)

    assert point.ebitdaMargin is None
    assert point.debtToEbitda is None
    assert point.evEbitda is None
    assert point.ebitdaEstimated is None
    assert series.ebitdaMargin == [None]
    assert series.debtToEbitda == [None]


def test_missing_capex_does_not_turn_fcf_into_operating_cashflow():
    incomplete = deepcopy(_COMPLETE_SERIES)
    incomplete["CF"].pop("purchase_of_property_plant_and_equipment")

    point = calcRatios(incomplete, annual=True)
    series = calcRatioSeries(incomplete, ["2024"], yoyLag=1)

    assert point.fcf is None
    assert point.capexRatio is None
    assert series.fcf == [None]
    assert series.capexRatio == [None]


def test_explicit_zero_is_data_not_missing():
    zero = deepcopy(_COMPLETE_SERIES)
    zero["BS"]["cash_and_cash_equivalents"] = [0.0]
    zero["BS"]["shortterm_borrowings"] = [0.0]
    zero["BS"]["longterm_borrowings"] = [0.0]
    zero["BS"]["debentures"] = [0.0]
    zero["CF"]["purchase_of_property_plant_and_equipment"] = [0.0]
    zero["CF"]["depreciation_and_amortization"] = [0.0]

    point = calcRatios(zero, annual=True)
    series = calcRatioSeries(zero, ["2024"], yoyLag=1)

    assert point.netDebt == 0.0
    assert point.netDebtRatio == 0.0
    assert point.debtToEbitda == 0.0
    assert point.fcf == 15.0
    assert point.capexRatio == 0.0
    assert series.netDebtRatio == [0.0]
    assert series.debtToEbitda == [0.0]
    assert series.fcf == [15.0]
    assert series.capexRatio == [0.0]
