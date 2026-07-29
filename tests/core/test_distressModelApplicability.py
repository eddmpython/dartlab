"""원식 입력을 보장할 수 없는 부실·조작 모델의 비발행 계약 회귀."""

import pytest

from dartlab.core.ratios import calcRatios, calcRatioSeries

pytestmark = pytest.mark.unit


_ANNUAL_SERIES = {
    "IS": {
        "sales": [90.0, 100.0],
        "operating_profit": [12.0, 15.0],
        "net_profit": [8.0, 10.0],
        "cost_of_sales": [55.0, 60.0],
        "selling_and_administrative_expenses": [10.0, 11.0],
    },
    "BS": {
        "total_assets": [180.0, 200.0],
        "total_liabilities": [80.0, 90.0],
        "total_stockholders_equity": [100.0, 110.0],
        "current_assets": [70.0, 80.0],
        "current_liabilities": [35.0, 40.0],
        "tangible_assets": [60.0, 65.0],
        "trade_and_other_receivables": [15.0, 18.0],
    },
    "CF": {
        "operating_cashflow": [9.0, 12.0],
        "depreciation_and_amortization": [5.0, 6.0],
    },
}


def test_generic_provider_series_does_not_publish_noncanonical_beneish():
    annualPoint = calcRatios(_ANNUAL_SERIES, annual=True)
    annualSeries = calcRatioSeries(_ANNUAL_SERIES, ["2023", "2024"], yoyLag=1)

    quarterly = {
        statement: {field: values * 4 for field, values in rows.items()} for statement, rows in _ANNUAL_SERIES.items()
    }
    quarterlyPoint = calcRatios(quarterly, annual=False)
    quarterlySeries = calcRatioSeries(quarterly, [f"Q{index}" for index in range(8)], yoyLag=4)

    assert annualPoint.beneishMScore is None
    assert annualSeries.beneishMScore == [None, None]
    assert quarterlyPoint.beneishMScore is None
    assert quarterlySeries.beneishMScore == [None] * 8


@pytest.mark.parametrize("currency", ["KRW", "USD"])
def test_generic_multicurrency_engine_does_not_publish_uncalibrated_ohlson(currency):
    result = calcRatios(_ANNUAL_SERIES, annual=True, currency=currency)

    assert result.ohlsonOScore is None
    assert result.ohlsonProbability is None
